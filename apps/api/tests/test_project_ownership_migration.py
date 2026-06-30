import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.auth_cli import main as auth_cli_main
from app.auth_store import AuthStore
from app.main import create_app
from app.store import ProjectStore


WORKFLOW_ROOT = Path(__file__).resolve().parents[3] / "workflow"


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(WORKFLOW_ROOT),
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


def project_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "name": "归属项目",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }
    payload.update(overrides)
    return payload


def create_user(
    client: TestClient,
    *,
    email: str = "teacher@example.com",
    password: str = "CorrectHorse123!",
    role: str = "teacher",
    display_name: str = "Teacher",
) -> dict[str, Any]:
    return client.app.state.auth_service.create_user(
        email=email,
        display_name=display_name,
        role=role,
        password=password,
    )


def login(client: TestClient, *, email: str = "teacher@example.com", password: str = "CorrectHorse123!") -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/auth/login",
            json={"email": email, "password": password},
            headers={"Origin": "http://localhost:3000"},
        )
    )


def project_db(project: dict[str, Any]) -> Path:
    return Path(project["project_dir"]) / "project.db"


def read_project_meta(project: dict[str, Any]) -> dict[str, Any]:
    with sqlite3.connect(project_db(project)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM project_meta WHERE project_id = ?", (project["project_id"],)).fetchone()
    assert row is not None
    return dict(row)


def projects_root(client: TestClient) -> Path:
    return Path(client.app.state.settings.storage_root) / "projects"


def run_cli(storage_root: Path, args: list[str]) -> int:
    return auth_cli_main(["--storage-root", str(storage_root), *args])


def auth_store(storage_root: Path) -> AuthStore:
    return AuthStore(storage_root / "auth.db")


def create_legacy_project_without_owner_column(storage_root: Path, name: str = "旧项目") -> dict[str, Any]:
    project = ProjectStore(storage_root).create_project(project_payload(name=name), None, owner_id="user_legacy_owner")
    with sqlite3.connect(project_db(project)) as conn:
        row = conn.execute("SELECT * FROM project_meta WHERE project_id = ?", (project["project_id"],)).fetchone()
        values = dict(zip([description[0] for description in conn.execute("SELECT * FROM project_meta").description], row))
        conn.execute("DROP TABLE project_meta")
        conn.execute(
            """
            CREATE TABLE project_meta (
              project_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              subject TEXT NOT NULL,
              grade TEXT NOT NULL,
              textbook_version TEXT NOT NULL,
              volume TEXT NOT NULL,
              lesson_type TEXT NOT NULL,
              created_at TEXT NOT NULL,
              status TEXT NOT NULL,
              project_dir TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO project_meta
            (project_id, name, subject, grade, textbook_version, volume, lesson_type, created_at, status, project_dir)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["project_id"],
                values["name"],
                values["subject"],
                values["grade"],
                values["textbook_version"],
                values["volume"],
                values["lesson_type"],
                values["created_at"],
                values["status"],
                values["project_dir"],
            ),
        )
    return project


def test_project_store_rejects_new_project_without_owner_id(tmp_path: Path):
    store = ProjectStore(tmp_path / "storage")

    try:
        store.create_project(project_payload(), None, owner_id=None)
    except ValueError as exc:
        assert "owner_id" in str(exc)
    else:
        raise AssertionError("ProjectStore.create_project must reject missing owner_id")


def test_cookie_user_create_project_sets_owner_id_before_store_write(tmp_path: Path):
    client = make_client(tmp_path)
    user = create_user(client)
    login(client)

    project = unwrap_ok(client.post("/projects", json=project_payload()))

    assert read_project_meta(project)["owner_id"] == user["user_id"]


def test_cookie_user_create_project_works_when_backend_token_is_configured(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    user = create_user(client)
    login(client)

    project = unwrap_ok(client.post("/projects", json=project_payload()))

    assert read_project_meta(project)["owner_id"] == user["user_id"]


def test_backend_token_create_project_uses_active_fallback_owner(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    owner = create_user(client, email="owner@example.com")
    client.app.state.settings.project_creation_default_owner_user_id = owner["user_id"]

    project = unwrap_ok(
        client.post(
            "/projects",
            json=project_payload(),
            headers={"Authorization": "Bearer dev-token"},
        )
    )

    assert read_project_meta(project)["owner_id"] == owner["user_id"]


def test_backend_token_create_project_without_fallback_fails_without_project_directory(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    root = projects_root(client)
    before = sorted(root.glob("*")) if root.exists() else []

    response = client.post(
        "/projects",
        json=project_payload(),
        headers={"Authorization": "Bearer dev-token"},
    )

    unwrap_error(response, 400, "PROJECT_OWNER_REQUIRED")
    after = sorted(root.glob("*")) if root.exists() else []
    assert after == before


def test_fallback_owner_without_backend_api_token_does_not_allow_anonymous_project_creation(tmp_path: Path):
    client = make_client(tmp_path)
    owner = create_user(client, email="owner@example.com")
    client.app.state.settings.project_creation_default_owner_user_id = owner["user_id"]
    root = projects_root(client)
    before = sorted(root.glob("*")) if root.exists() else []

    response = client.post("/projects", json=project_payload())

    unwrap_error(response, 401, "UNAUTHORIZED")
    after = sorted(root.glob("*")) if root.exists() else []
    assert after == before
    new_project_dirs = set(after) - set(before)
    assert new_project_dirs == set()
    assert not [path for path in new_project_dirs if (path / "project.db").exists()]


def test_disabled_fallback_owner_cannot_create_project(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    owner = create_user(client, email="disabled@example.com")
    client.app.state.auth_service.disable_user("disabled@example.com")
    client.app.state.settings.project_creation_default_owner_user_id = owner["user_id"]
    before = sorted(projects_root(client).glob("*"))

    response = client.post(
        "/projects",
        json=project_payload(),
        headers={"Authorization": "Bearer dev-token"},
    )

    unwrap_error(response, 400, "PROJECT_OWNER_REQUIRED")
    assert sorted(projects_root(client).glob("*")) == before


def test_create_project_rejects_owner_id_in_request_body(tmp_path: Path):
    client = make_client(tmp_path)
    create_user(client)
    login(client)

    response = client.post("/projects", json=project_payload(owner_id="user_attacker"))

    unwrap_error(response, 422, "PROJECT_OWNER_FORBIDDEN")


def test_verify_project_ownership_is_read_only_and_reports_missing_owner_column(tmp_path: Path):
    storage_root = tmp_path / "storage"
    create_legacy_project_without_owner_column(storage_root)

    assert run_cli(storage_root, ["verify-project-ownership"]) == 1

    db_path = next((storage_root / "projects").glob("*/project.db"))
    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    assert "owner_id" not in columns


def test_verify_project_ownership_distinguishes_missing_orphaned_and_owned(tmp_path: Path):
    storage_root = tmp_path / "storage"
    store = ProjectStore(storage_root)
    missing_column = create_legacy_project_without_owner_column(storage_root, "缺列")
    user = auth_store(storage_root).create_user(
        email="owner@example.com",
        display_name="Owner",
        password_hash="hash",
        role="teacher",
    )
    missing_owner = store.create_project(project_payload(name="空 owner"), None, owner_id=user["user_id"])
    orphaned = store.create_project(project_payload(name="孤儿 owner"), None, owner_id=user["user_id"])
    owned = store.create_project(project_payload(name="有 owner"), None, owner_id=user["user_id"])
    with sqlite3.connect(project_db(missing_owner)) as conn:
        conn.execute("UPDATE project_meta SET owner_id = NULL WHERE project_id = ?", (missing_owner["project_id"],))
    with sqlite3.connect(project_db(orphaned)) as conn:
        conn.execute("UPDATE project_meta SET owner_id = ? WHERE project_id = ?", ("user_missing", orphaned["project_id"]))
    with sqlite3.connect(project_db(owned)) as conn:
        conn.execute("UPDATE project_meta SET owner_id = ? WHERE project_id = ?", (user["user_id"], owned["project_id"]))

    assert run_cli(storage_root, ["verify-project-ownership", "--json"]) == 1

    # Direct module import is intentional here: tests verify the CLI and the reusable scanner contract.
    from app.project_ownership import scan_project_ownership

    result = scan_project_ownership(store, auth_store(storage_root))
    codes_by_project = {issue.project_id: issue.code for issue in result.issues}
    assert codes_by_project[missing_column["project_id"]] == "missing_owner_column"
    assert codes_by_project[missing_owner["project_id"]] == "missing_owner"
    assert codes_by_project[orphaned["project_id"]] == "orphaned_owner"
    assert owned["project_id"] not in codes_by_project


def test_mapping_preflight_owner_missing_apply_writes_nothing(tmp_path: Path):
    storage_root = tmp_path / "storage"
    project = create_legacy_project_without_owner_column(storage_root)
    mapping = tmp_path / "mapping.json"
    mapping.write_text(json.dumps({project["project_id"]: {"owner_user_id": "user_missing"}}), encoding="utf-8")

    assert run_cli(storage_root, ["assign-legacy-projects", "--mapping-file", str(mapping), "--apply"]) == 1

    db_path = project_db(project)
    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    assert "owner_id" not in columns


def test_dry_run_reports_plan_without_writing_owner_id(tmp_path: Path, capsys):
    storage_root = tmp_path / "storage"
    project = create_legacy_project_without_owner_column(storage_root)
    owner = auth_store(storage_root).create_user(
        email="owner@example.com",
        display_name="Owner",
        password_hash="hash",
        role="teacher",
    )

    assert run_cli(storage_root, ["assign-legacy-projects", "--owner-user-id", owner["user_id"]]) == 0

    output = capsys.readouterr().out
    assert "planned_count=1" in output
    assert "written_count=0" in output
    with sqlite3.connect(project_db(project)) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    assert "owner_id" not in columns


def test_mapping_file_invalid_apply_writes_nothing(tmp_path: Path):
    storage_root = tmp_path / "storage"
    project = create_legacy_project_without_owner_column(storage_root)
    mapping = tmp_path / "mapping.json"
    mapping.write_text("[not-an-object]", encoding="utf-8")

    assert run_cli(storage_root, ["assign-legacy-projects", "--mapping-file", str(mapping), "--apply"]) == 1

    with sqlite3.connect(project_db(project)) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    assert "owner_id" not in columns


def test_mapping_preflight_project_missing_apply_writes_nothing(tmp_path: Path):
    storage_root = tmp_path / "storage"
    project = create_legacy_project_without_owner_column(storage_root)
    owner = auth_store(storage_root).create_user(
        email="owner@example.com",
        display_name="Owner",
        password_hash="hash",
        role="teacher",
    )
    mapping = tmp_path / "mapping.json"
    mapping.write_text(
        json.dumps(
            {
                project["project_id"]: {"owner_user_id": owner["user_id"]},
                "proj_missing": {"owner_user_id": owner["user_id"]},
            }
        ),
        encoding="utf-8",
    )

    assert run_cli(storage_root, ["assign-legacy-projects", "--mapping-file", str(mapping), "--apply"]) == 1

    with sqlite3.connect(project_db(project)) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    assert "owner_id" not in columns


def test_apply_summary_counts_writes_and_skips_existing_owner_without_overwrite(tmp_path: Path, capsys):
    storage_root = tmp_path / "storage"
    store = ProjectStore(storage_root)
    legacy = create_legacy_project_without_owner_column(storage_root, "待迁移")
    first_owner = auth_store(storage_root).create_user(
        email="first@example.com",
        display_name="First",
        password_hash="hash",
        role="teacher",
    )
    existing = store.create_project(project_payload(name="已有 owner"), None, owner_id=first_owner["user_id"])
    second_owner = auth_store(storage_root).create_user(
        email="second@example.com",
        display_name="Second",
        password_hash="hash",
        role="teacher",
    )
    with sqlite3.connect(project_db(existing)) as conn:
        conn.execute("UPDATE project_meta SET owner_id = ? WHERE project_id = ?", (first_owner["user_id"], existing["project_id"]))
    mapping = tmp_path / "mapping.json"
    mapping.write_text(
        json.dumps(
            {
                legacy["project_id"]: {"owner_user_id": second_owner["user_id"]},
                existing["project_id"]: {"owner_user_id": second_owner["user_id"]},
            }
        ),
        encoding="utf-8",
    )

    assert run_cli(storage_root, ["assign-legacy-projects", "--mapping-file", str(mapping), "--apply"]) == 0

    output = capsys.readouterr().out
    assert "planned_count=2" in output
    assert "written_count=1" in output
    assert "skipped_existing_owner_count=1" in output
    assert "failed_count=0" in output
    assert read_project_meta(legacy)["owner_id"] == second_owner["user_id"]
    assert read_project_meta(existing)["owner_id"] == first_owner["user_id"]


def test_readiness_reports_project_ownership_non_blocking(tmp_path: Path):
    storage_root = tmp_path / "storage"
    create_legacy_project_without_owner_column(storage_root)
    client = make_client(tmp_path)

    response = client.get("/readiness")

    data = unwrap_ok(response)
    ownership = data["project_ownership"]
    assert ownership["ready_for_phase_c"] is False
    assert ownership["missing_owner_projects"] == 1
    assert ownership["orphaned_owner_projects"] == 0
    assert ownership["issues"][0]["code"] == "missing_owner_column"
