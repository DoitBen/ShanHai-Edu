from pathlib import Path

from app.auth_cli import main as auth_cli_main
from app.auth_store import AuthStore


def run_cli(storage_root: Path, args: list[str], passwords: list[str] | None = None) -> int:
    password_values = list(passwords or [])

    def fake_getpass(prompt: str = "") -> str:
        if not password_values:
            raise AssertionError(f"unexpected password prompt: {prompt}")
        return password_values.pop(0)

    return auth_cli_main(
        [
            "--storage-root",
            str(storage_root),
            *args,
        ],
        getpass_func=fake_getpass,
    )


def test_cli_creates_admin_and_teacher_without_printing_hashes(tmp_path: Path, capsys):
    storage_root = tmp_path / "storage"

    assert (
        run_cli(
            storage_root,
            [
                "create-user",
                "--email",
                "admin@example.com",
                "--display-name",
                "Admin",
                "--role",
                "admin",
            ],
            ["CorrectHorse123!", "CorrectHorse123!"],
        )
        == 0
    )
    assert (
        run_cli(
            storage_root,
            [
                "create-user",
                "--email",
                "teacher@example.com",
                "--display-name",
                "Teacher",
                "--role",
                "teacher",
            ],
            ["CorrectHorse123!", "CorrectHorse123!"],
        )
        == 0
    )
    assert run_cli(storage_root, ["list-users"]) == 0

    output = capsys.readouterr().out
    assert "admin@example.com" in output
    assert "teacher@example.com" in output
    assert "$argon2id$" not in output
    assert "session" not in output.lower()

    users = AuthStore(storage_root / "auth.db").list_users()
    assert {user["role"] for user in users} == {"admin", "teacher"}


def test_cli_rejects_duplicate_email_and_weak_or_mismatched_passwords(tmp_path: Path):
    storage_root = tmp_path / "storage"
    assert (
        run_cli(
            storage_root,
            ["create-user", "--email", "teacher@example.com", "--display-name", "Teacher", "--role", "teacher"],
            ["CorrectHorse123!", "CorrectHorse123!"],
        )
        == 0
    )

    assert (
        run_cli(
            storage_root,
            ["create-user", "--email", "teacher@example.com", "--display-name", "Teacher", "--role", "teacher"],
            ["CorrectHorse123!", "CorrectHorse123!"],
        )
        == 1
    )
    assert (
        run_cli(
            storage_root,
            ["create-user", "--email", "weak@example.com", "--display-name", "Weak", "--role", "teacher"],
            ["short", "short"],
        )
        == 1
    )
    assert (
        run_cli(
            storage_root,
            ["create-user", "--email", "mismatch@example.com", "--display-name", "Mismatch", "--role", "teacher"],
            ["CorrectHorse123!", "DifferentHorse123!"],
        )
        == 1
    )


def test_cli_disable_enable_and_set_password_revoke_sessions(tmp_path: Path):
    storage_root = tmp_path / "storage"
    assert (
        run_cli(
            storage_root,
            ["create-user", "--email", "teacher@example.com", "--display-name", "Teacher", "--role", "teacher"],
            ["CorrectHorse123!", "CorrectHorse123!"],
        )
        == 0
    )
    store = AuthStore(storage_root / "auth.db")
    user = store.get_user_by_email("teacher@example.com")
    store.create_session(
        user_id=user["user_id"],
        token_hash="token-hash",
        csrf_token_hash="csrf-hash",
        expires_at="2999-01-01T00:00:00+00:00",
        client_ip_hash="ip-hash",
        user_agent="pytest",
    )

    assert run_cli(storage_root, ["disable-user", "--email", "teacher@example.com"]) == 0
    assert AuthStore(storage_root / "auth.db").get_user_by_email("teacher@example.com")["is_active"] == 0
    assert AuthStore(storage_root / "auth.db").session_by_token_hash("token-hash") is None

    assert run_cli(storage_root, ["enable-user", "--email", "teacher@example.com"]) == 0
    assert AuthStore(storage_root / "auth.db").get_user_by_email("teacher@example.com")["is_active"] == 1

    user = AuthStore(storage_root / "auth.db").get_user_by_email("teacher@example.com")
    AuthStore(storage_root / "auth.db").create_session(
        user_id=user["user_id"],
        token_hash="token-hash-2",
        csrf_token_hash="csrf-hash-2",
        expires_at="2999-01-01T00:00:00+00:00",
        client_ip_hash="ip-hash",
        user_agent="pytest",
    )
    assert (
        run_cli(
            storage_root,
            ["set-password", "--email", "teacher@example.com"],
            ["NewCorrectHorse123!", "NewCorrectHorse123!"],
        )
        == 0
    )
    assert AuthStore(storage_root / "auth.db").session_by_token_hash("token-hash-2") is None
