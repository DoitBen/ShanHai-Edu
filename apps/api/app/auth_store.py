import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .store import now_iso


class AuthStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            self.init_db(conn)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              user_id TEXT PRIMARY KEY,
              email TEXT UNIQUE NOT NULL,
              display_name TEXT NOT NULL,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('admin', 'teacher')),
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              password_changed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
              session_id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              token_hash TEXT UNIQUE NOT NULL,
              csrf_token_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              revoked_at TEXT,
              client_ip_hash TEXT,
              user_agent TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
            CREATE TABLE IF NOT EXISTS login_attempts (
              attempt_id TEXT PRIMARY KEY,
              email_hash TEXT NOT NULL,
              ip_hash TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_login_attempts_email_hash_created_at
              ON login_attempts(email_hash, created_at);
            CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_hash_created_at
              ON login_attempts(ip_hash, created_at);
            CREATE TABLE IF NOT EXISTS auth_audit_events (
              event_id TEXT PRIMARY KEY,
              event_type TEXT NOT NULL,
              actor_user_id TEXT,
              target_type TEXT,
              target_id TEXT,
              result TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        password_hash: str,
        role: str,
    ) -> dict[str, Any]:
        timestamp = now_iso()
        user = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": normalize_email(email),
            "display_name": display_name.strip(),
            "password_hash": password_hash,
            "role": role,
            "is_active": 1,
            "created_at": timestamp,
            "updated_at": timestamp,
            "password_changed_at": timestamp,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users
                (user_id, email, display_name, password_hash, role, is_active, created_at, updated_at, password_changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["user_id"],
                    user["email"],
                    user["display_name"],
                    user["password_hash"],
                    user["role"],
                    user["is_active"],
                    user["created_at"],
                    user["updated_at"],
                    user["password_changed_at"],
                ),
            )
        return user

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (normalize_email(email),),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def list_users(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, email, display_name, role, is_active, created_at, updated_at, password_changed_at
                FROM users ORDER BY email
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def set_user_active(self, email: str, active: bool) -> None:
        with self.connect() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = ?, updated_at = ? WHERE email = ?",
                (1 if active else 0, now_iso(), normalize_email(email)),
            )
            if cursor.rowcount == 0:
                raise KeyError(email)

    def update_password_hash(self, email: str, password_hash: str) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET password_hash = ?, password_changed_at = ?, updated_at = ?
                WHERE email = ?
                """,
                (password_hash, timestamp, timestamp, normalize_email(email)),
            )
            if cursor.rowcount == 0:
                raise KeyError(email)

    def create_session(
        self,
        *,
        user_id: str,
        token_hash: str,
        csrf_token_hash: str,
        expires_at: str,
        client_ip_hash: str | None,
        user_agent: str | None,
    ) -> dict[str, Any]:
        timestamp = now_iso()
        session = {
            "session_id": f"sess_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "token_hash": token_hash,
            "csrf_token_hash": csrf_token_hash,
            "created_at": timestamp,
            "expires_at": expires_at,
            "last_seen_at": timestamp,
            "revoked_at": None,
            "client_ip_hash": client_ip_hash,
            "user_agent": (user_agent or "")[:256] or None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                (session_id, user_id, token_hash, csrf_token_hash, created_at, expires_at, last_seen_at, revoked_at, client_ip_hash, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["session_id"],
                    session["user_id"],
                    session["token_hash"],
                    session["csrf_token_hash"],
                    session["created_at"],
                    session["expires_at"],
                    session["last_seen_at"],
                    session["revoked_at"],
                    session["client_ip_hash"],
                    session["user_agent"],
                ),
            )
        return session

    def session_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sessions
                WHERE token_hash = ? AND revoked_at IS NULL AND expires_at > ?
                """,
                (token_hash, now_iso()),
            ).fetchone()
        return dict(row) if row else None

    def update_session_seen_and_csrf(self, session_id: str, csrf_token_hash: str | None = None) -> None:
        with self.connect() as conn:
            if csrf_token_hash is None:
                conn.execute(
                    "UPDATE sessions SET last_seen_at = ? WHERE session_id = ?",
                    (now_iso(), session_id),
                )
            else:
                conn.execute(
                    "UPDATE sessions SET last_seen_at = ?, csrf_token_hash = ? WHERE session_id = ?",
                    (now_iso(), csrf_token_hash, session_id),
                )

    def revoke_session(self, session_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE session_id = ? AND revoked_at IS NULL",
                (now_iso(), session_id),
            )

    def revoke_user_sessions(self, user_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                (now_iso(), user_id),
            )

    def record_login_attempt(self, *, email_hash: str, ip_hash: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO login_attempts (attempt_id, email_hash, ip_hash, created_at) VALUES (?, ?, ?, ?)",
                (f"attempt_{uuid.uuid4().hex[:12]}", email_hash, ip_hash, now_iso()),
            )

    def count_recent_attempts(self, *, email_hash: str, ip_hash: str, since: str) -> tuple[int, int]:
        with self.connect() as conn:
            email_count = conn.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE email_hash = ? AND created_at >= ?",
                (email_hash, since),
            ).fetchone()[0]
            ip_count = conn.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE ip_hash = ? AND created_at >= ?",
                (ip_hash, since),
            ).fetchone()[0]
        return int(email_count), int(ip_count)

    def clear_attempts_for_email(self, email_hash: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM login_attempts WHERE email_hash = ?", (email_hash,))

    def prune_login_attempts(self, before: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM login_attempts WHERE created_at < ?", (before,))

    def record_audit_event(
        self,
        *,
        event_type: str,
        result: str,
        actor_user_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_audit_events
                (event_id, event_type, actor_user_id, target_type, target_id, result, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"audit_{uuid.uuid4().hex[:12]}",
                    event_type,
                    actor_user_id,
                    target_type,
                    target_id,
                    result,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now_iso(),
                ),
            )


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()
