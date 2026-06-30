import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import HTTPException, Request

from .auth_store import AuthStore, normalize_email
from .security import sha256_hex, verify_csrf_token
from .settings import Settings
from .store import now_iso


DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "UPaVfMMHMIAPMtYyWmPQkA$"
    "GKHJKYAN+5L8XeW5VmjKWDnL7UepLtifassGF94jmqc"
)


class AuthService:
    def __init__(self, store: AuthStore, settings: Settings):
        self.store = store
        self.settings = settings
        self.password_hasher = PasswordHasher()

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        role: str,
        password: str,
    ) -> dict[str, Any]:
        if role not in {"admin", "teacher"}:
            raise ValueError("role must be admin or teacher")
        password_hash = self.password_hasher.hash(password)
        user = self.store.create_user(
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            role=role,
        )
        return self.public_user(user)

    def verify_user_password(self, email: str, password: str) -> bool:
        user = self.store.get_user_by_email(email)
        if not user:
            return False
        try:
            return self.password_hasher.verify(user["password_hash"], password)
        except (VerifyMismatchError, VerificationError):
            return False

    def login(self, *, email: str, password: str, request: Request) -> dict[str, Any]:
        normalized_email = normalize_email(email)
        ip_hash = self.request_ip_hash(request)
        email_hash = sha256_hex(normalized_email)
        self._enforce_login_rate_limit(email_hash=email_hash, ip_hash=ip_hash)

        user = self.store.get_user_by_email(normalized_email)
        password_hash = user["password_hash"] if user else DUMMY_PASSWORD_HASH
        try:
            password_ok = self.password_hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError):
            password_ok = False
        if not user or not password_ok or int(user.get("is_active") or 0) != 1:
            self.store.record_login_attempt(email_hash=email_hash, ip_hash=ip_hash)
            self.store.record_audit_event(
                event_type="auth.login",
                result="failed",
                actor_user_id=user["user_id"] if user else None,
                target_type="user" if user else None,
                target_id=user["user_id"] if user else None,
                metadata={"email_hash": email_hash, "ip_hash": ip_hash},
            )
            raise HTTPException(
                status_code=401,
                detail={"code": "AUTH_INVALID_CREDENTIALS", "message": "邮箱或密码不正确"},
            )

        self.store.clear_attempts_for_email(email_hash)
        session_token = generate_secret_token()
        csrf_token = generate_secret_token()
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(self.settings.auth_session_ttl_seconds))
        ).isoformat()
        session = self.store.create_session(
            user_id=user["user_id"],
            token_hash=sha256_hex(session_token),
            csrf_token_hash=sha256_hex(csrf_token),
            expires_at=expires_at,
            client_ip_hash=ip_hash,
            user_agent=request.headers.get("user-agent"),
        )
        self.store.record_audit_event(
            event_type="auth.login",
            result="success",
            actor_user_id=user["user_id"],
            target_type="session",
            target_id=session["session_id"],
            metadata={"email_hash": email_hash, "ip_hash": ip_hash},
        )
        return {
            "user": self.public_user(user),
            "session_token": session_token,
            "csrf_token": csrf_token,
            "expires_at": expires_at,
        }

    def session_from_token(self, session_token: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
        if not session_token:
            raise_auth_required()
        token_hash = sha256_hex(session_token)
        session = self.store.session_by_token_hash(token_hash)
        if not session:
            raise_auth_required()
        if not secrets.compare_digest(str(session["token_hash"]), token_hash):
            raise_auth_required()
        user = self.store.get_user_by_id(session["user_id"])
        if not user or int(user.get("is_active") or 0) != 1:
            raise_auth_required()
        return session, user

    def me(self, session_token: str | None) -> dict[str, Any]:
        session, user = self.session_from_token(session_token)
        csrf_token = generate_secret_token()
        self.store.update_session_seen_and_csrf(session["session_id"], sha256_hex(csrf_token))
        return {
            "user": self.public_user(user),
            "csrf_token": csrf_token,
            "expires_at": session["expires_at"],
        }

    def logout(self, *, session_token: str | None, csrf_token: str | None) -> None:
        session, user = self.optional_session_from_token(session_token)
        if not session or not user:
            return
        verify_csrf_token(csrf_token, session["csrf_token_hash"])
        self.store.revoke_session(session["session_id"])
        self.store.record_audit_event(
            event_type="auth.logout",
            result="success",
            actor_user_id=user["user_id"],
            target_type="session",
            target_id=session["session_id"],
            metadata={},
        )

    def optional_session_from_token(
        self,
        session_token: str | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if not session_token:
            return None, None
        token_hash = sha256_hex(session_token)
        session = self.store.session_by_token_hash(token_hash)
        if not session:
            return None, None
        if not secrets.compare_digest(str(session["token_hash"]), token_hash):
            return None, None
        user = self.store.get_user_by_id(session["user_id"])
        if not user or int(user.get("is_active") or 0) != 1:
            return None, None
        return session, user

    def disable_user(self, email: str) -> None:
        user = self.store.get_user_by_email(email)
        if not user:
            raise KeyError(email)
        self.store.set_user_active(email, False)
        self.store.revoke_user_sessions(user["user_id"])
        self.store.record_audit_event(
            event_type="auth.user.disable",
            result="success",
            actor_user_id=None,
            target_type="user",
            target_id=user["user_id"],
            metadata={"email_hash": sha256_hex(user["email"])},
        )

    def revoke_user_sessions(self, email: str) -> None:
        user = self.store.get_user_by_email(email)
        if not user:
            raise KeyError(email)
        self.store.revoke_user_sessions(user["user_id"])
        self.store.record_audit_event(
            event_type="auth.session.revoke",
            result="success",
            actor_user_id=None,
            target_type="user",
            target_id=user["user_id"],
            metadata={"email_hash": sha256_hex(user["email"])},
        )

    def enable_user(self, email: str) -> None:
        user = self.store.get_user_by_email(email)
        if not user:
            raise KeyError(email)
        self.store.set_user_active(email, True)
        self.store.record_audit_event(
            event_type="auth.user.enable",
            result="success",
            actor_user_id=None,
            target_type="user",
            target_id=user["user_id"],
            metadata={"email_hash": sha256_hex(user["email"])},
        )

    def set_password(self, email: str, password: str) -> None:
        user = self.store.get_user_by_email(email)
        if not user:
            raise KeyError(email)
        self.store.update_password_hash(email, self.password_hasher.hash(password))
        self.store.revoke_user_sessions(user["user_id"])
        self.store.record_audit_event(
            event_type="auth.password.set",
            result="success",
            actor_user_id=None,
            target_type="user",
            target_id=user["user_id"],
            metadata={"email_hash": sha256_hex(user["email"]), "sessions_revoked": True},
        )

    def public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": user["role"],
            "status": "active" if int(user.get("is_active") or 0) == 1 else "disabled",
        }

    def request_ip_hash(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",", 1)[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return sha256_hex(ip)

    def _enforce_login_rate_limit(self, *, email_hash: str, ip_hash: str) -> None:
        window_seconds = int(self.settings.auth_login_rate_limit_window_seconds)
        since_dt = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        since = since_dt.isoformat()
        self.store.prune_login_attempts(since)
        email_count, ip_count = self.store.count_recent_attempts(
            email_hash=email_hash,
            ip_hash=ip_hash,
            since=since,
        )
        max_failures = int(self.settings.auth_login_rate_limit_max_failures)
        if email_count >= max_failures or ip_count >= max_failures:
            self.store.record_audit_event(
                event_type="auth.login",
                result="denied",
                actor_user_id=None,
                target_type=None,
                target_id=None,
                metadata={"reason": "rate_limited", "email_hash": email_hash, "ip_hash": ip_hash},
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "AUTH_RATE_LIMITED",
                    "message": "登录失败次数过多，请稍后再试",
                    "details": {"retry_after_seconds": window_seconds},
                },
            )


def generate_secret_token() -> str:
    return secrets.token_urlsafe(48)


def raise_auth_required() -> None:
    raise HTTPException(
        status_code=401,
        detail={"code": "AUTH_REQUIRED", "message": "请先登录"},
    )
