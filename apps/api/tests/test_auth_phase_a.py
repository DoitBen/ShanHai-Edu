import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import assert_request_origin_allowed, verify_csrf_token


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "cors_origins": "http://localhost:3000,http://127.0.0.1:3000",
            **(overrides or {}),
        }
    )
    return TestClient(app)


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def unwrap_error(response, expected_status: int, expected_code: str):
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert payload["ok"] is False, payload
    assert payload["error"]["code"] == expected_code
    return payload["error"]


def auth_db(client: TestClient) -> Path:
    return Path(client.app.state.settings.storage_root) / "auth.db"


def create_user(
    client: TestClient,
    *,
    email: str = "teacher@example.com",
    password: str = "CorrectHorse123!",
    role: str = "teacher",
    display_name: str = "Teacher One",
) -> dict[str, Any]:
    return client.app.state.auth_service.create_user(
        email=email,
        display_name=display_name,
        role=role,
        password=password,
    )


def session_cookie(response) -> str:
    cookie = response.cookies.get("shanhai_session")
    assert cookie
    return cookie


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_auth_db_initializes_phase_a_tables_and_indexes(tmp_path: Path):
    client = make_client(tmp_path)

    with sqlite3.connect(auth_db(client)) as conn:
        table_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        index_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert {"users", "sessions", "auth_audit_events", "login_attempts"} <= table_names
    assert {
        "idx_sessions_token_hash",
        "idx_sessions_user_id",
        "idx_sessions_expires_at",
        "idx_login_attempts_email_hash_created_at",
        "idx_login_attempts_ip_hash_created_at",
    } <= index_names


def test_password_hash_uses_argon2id_and_never_stores_plaintext(tmp_path: Path):
    client = make_client(tmp_path)
    user = create_user(client, password="CorrectHorse123!")

    with sqlite3.connect(auth_db(client)) as conn:
        row = conn.execute(
            "SELECT email, password_hash FROM users WHERE user_id = ?",
            (user["user_id"],),
        ).fetchone()

    assert row[0] == "teacher@example.com"
    assert "CorrectHorse123!" not in row[1]
    assert row[1].startswith("$argon2id$")
    assert client.app.state.auth_service.verify_user_password(
        "teacher@example.com",
        "CorrectHorse123!",
    )


def test_login_success_sets_http_only_cookie_and_hashes_session_and_csrf(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)

    response = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000", "User-Agent": "pytest-agent"},
    )
    data = unwrap_ok(response)
    raw_session_token = session_cookie(response)

    assert data["user"] == {
        "user_id": data["user"]["user_id"],
        "email": "teacher@example.com",
        "display_name": "Teacher One",
        "role": "teacher",
        "status": "active",
    }
    assert data["csrf_token"]
    set_cookie = response.headers["set-cookie"]
    assert "shanhai_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Path=/" in set_cookie
    assert "Max-Age=" in set_cookie
    assert "Secure" not in set_cookie

    with sqlite3.connect(auth_db(client)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT token_hash, csrf_token_hash, user_agent FROM sessions"
        ).fetchone()

    assert row is not None
    assert row["token_hash"] == sha256_hex(raw_session_token)
    assert row["csrf_token_hash"] == sha256_hex(data["csrf_token"])
    assert raw_session_token not in row["token_hash"]
    assert data["csrf_token"] not in row["csrf_token_hash"]
    assert row["user_agent"] == "pytest-agent"


def test_login_can_set_secure_cookie_when_configured(tmp_path: Path):
    client = make_client(tmp_path, {"auth_cookie_secure": True})
    create_user(client)

    response = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )

    unwrap_ok(response)
    assert "Secure" in response.headers["set-cookie"]


def test_login_failure_paths_use_same_error_and_audit_without_account_enumeration(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)
    client.app.state.auth_service.disable_user("teacher@example.com")

    cases = [
        {"email": "missing@example.com", "password": "WrongPassword123!"},
        {"email": "teacher@example.com", "password": "WrongPassword123!"},
        {"email": "teacher@example.com", "password": "CorrectHorse123!"},
    ]
    for payload in cases:
        error = unwrap_error(
            client.post(
                "/auth/login",
                json=payload,
                headers={"Origin": "http://localhost:3000"},
            ),
            401,
            "AUTH_INVALID_CREDENTIALS",
        )
        assert "不存在" not in error["message"]
        assert "禁用" not in error["message"]

    with sqlite3.connect(auth_db(client)) as conn:
        failures = conn.execute(
            """
            SELECT event_type, result, metadata_json
            FROM auth_audit_events
            WHERE event_type = 'auth.login'
            ORDER BY created_at
            """
        ).fetchall()

    assert len(failures) == 3
    assert all(row[1] == "failed" for row in failures)
    serialized = "\n".join(row[2] for row in failures)
    assert "WrongPassword123!" not in serialized
    assert "CorrectHorse123!" not in serialized


def test_login_failure_paths_all_execute_argon2_verify_to_reduce_timing_enumeration(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    create_user(client, email="wrong@example.com", password="CorrectHorse123!")
    create_user(client, email="disabled@example.com", password="CorrectHorse123!")
    client.app.state.auth_service.disable_user("disabled@example.com")

    calls: list[tuple[str, str]] = []

    class FakePasswordHasher:
        def verify(self, password_hash: str, password: str) -> bool:
            calls.append((password_hash, password))
            return False

    monkeypatch.setattr(client.app.state.auth_service, "password_hasher", FakePasswordHasher())

    cases = [
        {"email": "missing@example.com", "password": "WrongPassword123!"},
        {"email": "disabled@example.com", "password": "WrongPassword123!"},
        {"email": "wrong@example.com", "password": "WrongPassword123!"},
    ]
    for payload in cases:
        error = unwrap_error(
            client.post(
                "/auth/login",
                json=payload,
                headers={"Origin": "http://localhost:3000"},
            ),
            401,
            "AUTH_INVALID_CREDENTIALS",
        )
        assert error["message"] == "邮箱或密码不正确"

    assert len(calls) == len(cases)
    assert all(password == "WrongPassword123!" for _hash, password in calls)
    assert all(password_hash.startswith("$argon2id$") for password_hash, _password in calls)
    assert len({password_hash for password_hash, _password in calls}) >= 2


def test_login_rate_limit_uses_email_and_ip_hash_without_plaintext_storage(tmp_path: Path):
    client = make_client(
        tmp_path,
        {
            "auth_login_rate_limit_max_failures": 5,
            "auth_login_rate_limit_window_seconds": 900,
        },
    )
    create_user(client)

    for _ in range(5):
        unwrap_error(
            client.post(
                "/auth/login",
                json={"email": "teacher@example.com", "password": "WrongPassword123!"},
                headers={"Origin": "http://localhost:3000"},
            ),
            401,
            "AUTH_INVALID_CREDENTIALS",
        )
    limited = unwrap_error(
        client.post(
            "/auth/login",
            json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
            headers={"Origin": "http://localhost:3000"},
        ),
        429,
        "AUTH_RATE_LIMITED",
    )

    assert limited["details"]["retry_after_seconds"] > 0
    with sqlite3.connect(auth_db(client)) as conn:
        rows = conn.execute(
            "SELECT email_hash, ip_hash FROM login_attempts"
        ).fetchall()
    assert len(rows) == 5
    assert all(row[0] != "teacher@example.com" for row in rows)
    assert all(row[1] not in {"127.0.0.1", "testclient"} for row in rows)


def test_login_rate_limit_blocks_same_ip_across_different_emails_by_design(tmp_path: Path):
    client = make_client(
        tmp_path,
        {
            "auth_login_rate_limit_max_failures": 2,
            "auth_login_rate_limit_window_seconds": 900,
        },
    )
    create_user(client, email="one@example.com")
    create_user(client, email="two@example.com")
    create_user(client, email="three@example.com")

    for email in ["one@example.com", "two@example.com"]:
        unwrap_error(
            client.post(
                "/auth/login",
                json={"email": email, "password": "WrongPassword123!"},
                headers={"Origin": "http://localhost:3000"},
            ),
            401,
            "AUTH_INVALID_CREDENTIALS",
        )

    limited = unwrap_error(
        client.post(
            "/auth/login",
            json={"email": "three@example.com", "password": "CorrectHorse123!"},
            headers={"Origin": "http://localhost:3000"},
        ),
        429,
        "AUTH_RATE_LIMITED",
    )

    assert limited["details"]["retry_after_seconds"] == 900


def test_successful_login_clears_email_failure_count(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)

    unwrap_error(
        client.post(
            "/auth/login",
            json={"email": "teacher@example.com", "password": "WrongPassword123!"},
            headers={"Origin": "http://localhost:3000"},
        ),
        401,
        "AUTH_INVALID_CREDENTIALS",
    )
    unwrap_ok(
        client.post(
            "/auth/login",
            json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
            headers={"Origin": "http://localhost:3000"},
        )
    )

    with sqlite3.connect(auth_db(client)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM login_attempts").fetchone()[0]
    assert count == 0


def test_auth_me_recovers_user_from_cookie_and_rotates_csrf_token(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)
    login = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    first = unwrap_ok(login)

    me = unwrap_ok(client.get("/auth/me"))

    assert me["user"] == first["user"]
    assert me["user"]["status"] == "active"
    assert "password_hash" not in me["user"]
    assert "token" not in me["user"]
    assert "token_hash" not in me["user"]
    assert me["expires_at"] == first["expires_at"]
    assert me["csrf_token"]
    assert me["csrf_token"] != first["csrf_token"]
    with sqlite3.connect(auth_db(client)) as conn:
        csrf_hash = conn.execute("SELECT csrf_token_hash FROM sessions").fetchone()[0]
    assert csrf_hash == sha256_hex(me["csrf_token"])


def test_auth_me_rejects_expired_revoked_and_disabled_sessions(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)
    response = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    unwrap_ok(response)

    with sqlite3.connect(auth_db(client)) as conn:
        expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        conn.execute("UPDATE sessions SET expires_at = ?", (expired,))
    unwrap_error(client.get("/auth/me"), 401, "AUTH_REQUIRED")

    client = make_client(tmp_path)
    create_user(client, email="second@example.com")
    second = client.post(
        "/auth/login",
        json={"email": "second@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    unwrap_ok(second)
    client.app.state.auth_service.revoke_user_sessions("second@example.com")
    unwrap_error(client.get("/auth/me"), 401, "AUTH_REQUIRED")

    client = make_client(tmp_path)
    create_user(client, email="third@example.com")
    third = client.post(
        "/auth/login",
        json={"email": "third@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    unwrap_ok(third)
    client.app.state.auth_service.disable_user("third@example.com")
    unwrap_error(client.get("/auth/me"), 401, "AUTH_REQUIRED")


def test_logout_requires_origin_and_csrf_for_valid_session_then_revokes_session_and_clears_cookie(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)
    login = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    data = unwrap_ok(login)

    unwrap_error(
        client.post("/auth/logout", headers={"Origin": "http://localhost:3000"}),
        403,
        "CSRF_TOKEN_REQUIRED",
    )
    unwrap_error(
        client.post(
            "/auth/logout",
            headers={"Origin": "http://evil.example", "X-CSRF-Token": data["csrf_token"]},
        ),
        403,
        "AUTH_ORIGIN_FORBIDDEN",
    )
    logout = client.post(
        "/auth/logout",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": data["csrf_token"]},
    )
    unwrap_ok(logout)
    assert "shanhai_session=" in logout.headers["set-cookie"]
    assert "Max-Age=0" in logout.headers["set-cookie"]
    with sqlite3.connect(auth_db(client)) as conn:
        revoked_at = conn.execute("SELECT revoked_at FROM sessions").fetchone()[0]
    assert revoked_at
    unwrap_error(client.get("/auth/me"), 401, "AUTH_REQUIRED")


def test_logout_is_idempotent_for_second_missing_and_revoked_sessions(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)

    no_cookie = client.post("/auth/logout")
    unwrap_ok(no_cookie)
    assert "shanhai_session=" in no_cookie.headers["set-cookie"]
    assert "Max-Age=0" in no_cookie.headers["set-cookie"]

    login = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    data = unwrap_ok(login)
    first_logout = client.post(
        "/auth/logout",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": data["csrf_token"]},
    )
    unwrap_ok(first_logout)

    second_logout = client.post("/auth/logout")
    unwrap_ok(second_logout)
    assert "Max-Age=0" in second_logout.headers["set-cookie"]

    stale_cookie_client = make_client(tmp_path)
    stale_cookie_client.cookies.set("shanhai_session", session_cookie(login))
    revoked_logout = stale_cookie_client.post("/auth/logout")
    unwrap_ok(revoked_logout)
    assert "Max-Age=0" in revoked_logout.headers["set-cookie"]


def test_csrf_tool_accepts_matching_hash_and_rejects_missing_wrong_and_cross_session_tokens():
    token = "csrf-token-one"
    other = "csrf-token-two"
    stored_hash = sha256_hex(token)

    verify_csrf_token(token, stored_hash)

    for candidate in [None, "", "wrong-token", other]:
        try:
            verify_csrf_token(candidate, stored_hash)
        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail["code"] in {"CSRF_TOKEN_REQUIRED", "CSRF_TOKEN_INVALID"}
        else:
            raise AssertionError("expected CSRF rejection")


def test_origin_tool_accepts_configured_origin_and_rejects_missing_or_untrusted_origin():
    assert_request_origin_allowed("http://localhost:3000", ["http://localhost:3000"])

    for origin in [None, "", "http://evil.example"]:
        try:
            assert_request_origin_allowed(origin, ["http://localhost:3000"])
        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail["code"] == "AUTH_ORIGIN_FORBIDDEN"
        else:
            raise AssertionError("expected origin rejection")


def test_audit_events_record_login_success_failure_and_logout_without_secrets(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)

    unwrap_error(
        client.post(
            "/auth/login",
            json={"email": "teacher@example.com", "password": "WrongPassword123!"},
            headers={"Origin": "http://localhost:3000"},
        ),
        401,
        "AUTH_INVALID_CREDENTIALS",
    )
    login = client.post(
        "/auth/login",
        json={"email": "teacher@example.com", "password": "CorrectHorse123!"},
        headers={"Origin": "http://localhost:3000"},
    )
    data = unwrap_ok(login)
    unwrap_ok(
        client.post(
            "/auth/logout",
            headers={"Origin": "http://localhost:3000", "X-CSRF-Token": data["csrf_token"]},
        )
    )

    with sqlite3.connect(auth_db(client)) as conn:
        rows = conn.execute(
            "SELECT event_type, result, metadata_json FROM auth_audit_events ORDER BY created_at"
        ).fetchall()

    assert [(row[0], row[1]) for row in rows] == [
        ("auth.login", "failed"),
        ("auth.login", "success"),
        ("auth.logout", "success"),
    ]
    serialized = "\n".join(row[2] for row in rows)
    assert "WrongPassword123!" not in serialized
    assert "CorrectHorse123!" not in serialized
    assert "shanhai_session" not in serialized
    assert data["csrf_token"] not in serialized
