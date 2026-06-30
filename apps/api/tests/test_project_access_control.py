import sqlite3
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from conftest import TEST_ORIGIN, create_auth_user, login_as


WORKFLOW_ROOT = Path(__file__).resolve().parents[3] / "workflow"
PROJECT_CREATE_TOKEN = "phase-c-project-token"
MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


class RecordingVideoProvider:
    def __init__(self):
        self.submitted: list[dict[str, Any]] = []

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append(payload)
        return {
            "provider_task_id": f"provider_{len(self.submitted)}",
            "status": "queued",
            "progress": 0,
            "video_url": None,
        }


def make_app(tmp_path: Path, overrides: dict[str, Any] | None = None):
    return create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(WORKFLOW_ROOT),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "backend_api_token": PROJECT_CREATE_TOKEN,
            "cors_origins": TEST_ORIGIN,
            **(overrides or {}),
        }
    )


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


def project_payload(name: str) -> dict[str, str]:
    return {
        "name": name,
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }


def logged_client(app, email: str) -> TestClient:
    client = TestClient(app)
    login_as(client, email=email)
    return client


def create_project(client: TestClient, name: str) -> dict[str, Any]:
    return unwrap_ok(client.post("/projects", json=project_payload(name)))


def set_project_owner(project: dict[str, Any], owner_id: str | None) -> None:
    with sqlite3.connect(Path(project["project_dir"]) / "project.db") as conn:
        conn.execute(
            "UPDATE project_meta SET owner_id = ? WHERE project_id = ?",
            (owner_id, project["project_id"]),
        )


def image_bytes() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (64, 48), (24, 110, 180)).save(stream, format="PNG")
    return stream.getvalue()


def create_two_teacher_projects(tmp_path: Path):
    app = make_app(tmp_path)
    app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    create_auth_user(TestClient(app), email="teacher-a@example.com", display_name="Teacher A")
    create_auth_user(TestClient(app), email="teacher-b@example.com", display_name="Teacher B")
    teacher_a = logged_client(app, "teacher-a@example.com")
    teacher_b = logged_client(app, "teacher-b@example.com")
    project_a = create_project(teacher_a, "A 的项目")
    project_b = create_project(teacher_b, "B 的项目")
    return app, teacher_a, teacher_b, project_a, project_b


def test_teacher_project_list_and_project_reads_are_scoped_by_owner(tmp_path: Path):
    app = make_app(tmp_path)
    create_auth_user(TestClient(app), email="teacher-a@example.com", display_name="Teacher A")
    create_auth_user(TestClient(app), email="teacher-b@example.com", display_name="Teacher B")
    create_auth_user(TestClient(app), email="admin@example.com", role="admin", display_name="Admin")
    teacher_a = logged_client(app, "teacher-a@example.com")
    teacher_b = logged_client(app, "teacher-b@example.com")
    admin = logged_client(app, "admin@example.com")

    project_a = create_project(teacher_a, "A 的项目")
    project_b = create_project(teacher_b, "B 的项目")

    teacher_a_projects = unwrap_ok(teacher_a.get("/projects"))
    assert {project["project_id"] for project in teacher_a_projects} == {project_a["project_id"]}
    assert unwrap_ok(teacher_a.get(f"/projects/{project_a['project_id']}"))["project_id"] == project_a["project_id"]
    unwrap_error(teacher_a.get(f"/projects/{project_b['project_id']}"), 404, "PROJECT_NOT_FOUND")
    unwrap_error(teacher_a.get(f"/projects/{project_b['project_id']}/manifest"), 404, "PROJECT_NOT_FOUND")
    unwrap_error(teacher_a.get(f"/projects/{project_b['project_id']}/workspace"), 404, "PROJECT_NOT_FOUND")

    admin_projects = unwrap_ok(admin.get("/projects"))
    assert {project["project_id"] for project in admin_projects} == {project_a["project_id"], project_b["project_id"]}
    assert unwrap_ok(admin.get(f"/projects/{project_a['project_id']}"))["project_id"] == project_a["project_id"]
    assert unwrap_ok(admin.get(f"/projects/{project_b['project_id']}"))["project_id"] == project_b["project_id"]


def test_unauthenticated_and_token_only_requests_cannot_read_project_resources(tmp_path: Path):
    app = make_app(tmp_path)
    owner = create_auth_user(TestClient(app), email="owner@example.com")
    app.state.settings.project_creation_default_owner_user_id = owner["user_id"]
    token_client = TestClient(app)
    project = unwrap_ok(
        token_client.post(
            "/projects",
            headers={"Authorization": f"Bearer {PROJECT_CREATE_TOKEN}"},
            json=project_payload("兼容创建项目"),
        )
    )

    anonymous = TestClient(app)
    unwrap_error(anonymous.get(f"/projects/{project['project_id']}"), 401, "AUTH_REQUIRED")

    token_only = TestClient(app)
    token_only.headers.update({"Authorization": f"Bearer {PROJECT_CREATE_TOKEN}"})
    unwrap_error(token_only.get(f"/projects/{project['project_id']}"), 401, "AUTH_REQUIRED")
    unwrap_error(token_only.get(f"/projects/{project['project_id']}/manifest"), 401, "AUTH_REQUIRED")


def test_missing_or_orphan_project_owner_is_not_accessible_even_to_admin(tmp_path: Path):
    app = make_app(tmp_path)
    create_auth_user(TestClient(app), email="teacher@example.com")
    create_auth_user(TestClient(app), email="admin@example.com", role="admin")
    teacher = logged_client(app, "teacher@example.com")
    admin = logged_client(app, "admin@example.com")

    missing_owner = create_project(teacher, "缺 owner 项目")
    orphaned_owner = create_project(teacher, "孤儿 owner 项目")
    set_project_owner(missing_owner, None)
    set_project_owner(orphaned_owner, "user_missing")

    unwrap_error(admin.get(f"/projects/{missing_owner['project_id']}"), 404, "PROJECT_NOT_FOUND")
    unwrap_error(admin.get(f"/projects/{orphaned_owner['project_id']}"), 404, "PROJECT_NOT_FOUND")
    assert unwrap_ok(admin.get("/projects")) == []


def test_every_project_route_declares_project_access_dependency(tmp_path: Path):
    app = make_app(tmp_path)

    from app.auth_dependencies import require_project_access

    uncovered: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or "{project_id}" not in route.path:
            continue
        calls = {dependency.call for dependency in route.dependant.dependencies}
        if require_project_access not in calls:
            methods = ",".join(sorted(route.methods or []))
            uncovered.append(f"{methods} {route.path}")

    assert uncovered == []


def test_teacher_cannot_download_other_teacher_project_files(tmp_path: Path):
    _app, teacher_a, teacher_b, _project_a, project_b = create_two_teacher_projects(tmp_path)
    project_dir = Path(project_b["project_dir"])
    (project_dir / "uploads" / "secret.txt").write_text("private", encoding="utf-8")
    (project_dir / "exports").mkdir(exist_ok=True)
    (project_dir / "exports" / "deck.pptx").write_bytes(b"pptx")
    (project_dir / "outputs").mkdir(exist_ok=True)
    (project_dir / "outputs" / "final_video.mp4").write_bytes(MP4_BYTES)
    (project_dir / "clips" / "clip.mp4").write_bytes(MP4_BYTES)
    (project_dir / "assets" / "generated_images").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "generated_images" / "image.png").write_bytes(image_bytes())

    textbook = unwrap_ok(
        teacher_b.post(
            f"/projects/{project_b['project_id']}/textbook",
            files={"file": ("textbook.txt", "B project textbook", "text/plain")},
        )
    )
    asset_id = unwrap_ok(teacher_b.get(f"/projects/{project_b['project_id']}/assets"))[0]["asset_id"]
    assert asset_id == textbook["asset_id"]

    blocked_paths = [
        f"/projects/{project_b['project_id']}/files/uploads/secret.txt",
        f"/projects/{project_b['project_id']}/exports/deck.pptx",
        f"/projects/{project_b['project_id']}/outputs/final_video.mp4",
        f"/projects/{project_b['project_id']}/clips/clip.mp4",
        f"/projects/{project_b['project_id']}/images/image.png",
        f"/projects/{project_b['project_id']}/assets",
        f"/projects/{project_b['project_id']}/assets/{asset_id}",
    ]
    for path in blocked_paths:
        unwrap_error(teacher_a.get(path), 404, "PROJECT_NOT_FOUND")


def test_teacher_cannot_operate_other_teacher_video_workflow_or_guess_ids(tmp_path: Path):
    _app, teacher_a, teacher_b, project_a, project_b = create_two_teacher_projects(tmp_path)
    uploaded = unwrap_ok(
        teacher_b.post(
            f"/projects/{project_b['project_id']}/video-workflow/assets",
            files={"files": ("reference.png", image_bytes(), "image/png")},
        )
    )
    asset_id = uploaded["uploaded"][0]["asset_id"]
    run = unwrap_ok(
        teacher_b.post(
            f"/projects/{project_b['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "generate a private video",
                "reference_asset_ids": [asset_id],
            },
        )
    )
    run_id = run["run_id"]

    blocked_project_b_operations = [
        ("get", f"/projects/{project_b['project_id']}/video-workflow"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/storage"),
        ("post", f"/projects/{project_b['project_id']}/video-workflow/storage/cleanup"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/assets/{asset_id}/content"),
        ("delete", f"/projects/{project_b['project_id']}/video-workflow/assets/{asset_id}"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/runs"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/runs/{run_id}"),
        ("post", f"/projects/{project_b['project_id']}/video-workflow/runs/{run_id}/sync"),
        ("post", f"/projects/{project_b['project_id']}/video-workflow/runs/{run_id}/retry"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/runs/{run_id}/download"),
        ("get", f"/projects/{project_b['project_id']}/video-workflow/runs/{run_id}/content"),
    ]
    for method, path in blocked_project_b_operations:
        if method == "post":
            response = teacher_a.post(path, json={"client_request_id": str(uuid.uuid4())})
        elif method == "delete":
            response = teacher_a.delete(path)
        else:
            response = teacher_a.get(path)
        unwrap_error(response, 404, "PROJECT_NOT_FOUND")

    unwrap_error(
        teacher_a.get(f"/projects/{project_a['project_id']}/video-workflow/assets/{asset_id}/content"),
        404,
        "VIDEO_REFERENCE_NOT_FOUND",
    )
    unwrap_error(
        teacher_a.get(f"/projects/{project_a['project_id']}/video-workflow/runs/{run_id}"),
        404,
        "VIDEO_WORKFLOW_RUN_NOT_FOUND",
    )
