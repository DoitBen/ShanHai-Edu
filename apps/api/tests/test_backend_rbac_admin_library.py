from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import TEST_ORIGIN, create_auth_user, login_as


WORKFLOW_ROOT = Path(__file__).resolve().parents[3] / "workflow"


def make_app(tmp_path: Path, overrides: dict[str, Any] | None = None):
    return create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(WORKFLOW_ROOT),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
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


def logged_client(app, email: str) -> TestClient:
    client = TestClient(app)
    login_as(client, email=email)
    return client


def setup_users(app):
    create_auth_user(TestClient(app), email="teacher@example.com", role="teacher")
    create_auth_user(TestClient(app), email="admin@example.com", role="admin")
    return logged_client(app, "teacher@example.com"), logged_client(app, "admin@example.com")


def test_global_read_interfaces_require_login_and_allow_teacher_and_admin(tmp_path: Path):
    app = make_app(tmp_path)
    teacher, admin = setup_users(app)
    anonymous = TestClient(app)

    read_paths = [
        "/workflow",
        "/video/capabilities",
        "/schemas/lesson_plan.schema.json",
        "/textbook-library",
        "/lesson-plan-library",
    ]
    for path in read_paths:
        unwrap_error(anonymous.get(path), 401, "AUTH_REQUIRED")
        unwrap_ok(teacher.get(path))
        unwrap_ok(admin.get(path))


def test_readiness_stays_public_for_phase_c(tmp_path: Path):
    app = make_app(tmp_path)

    data = unwrap_ok(TestClient(app).get("/readiness"))

    assert "project_ownership" in data


def test_teacher_cannot_call_admin_or_write_library_endpoints(tmp_path: Path):
    app = make_app(tmp_path)
    teacher, _admin = setup_users(app)

    blocked_requests = [
        ("get", "/admin/rules", None),
        ("get", "/admin/media-workbench", None),
        ("get", "/rules/coverage", None),
        ("post", "/textbook-library/uploads", {"files": {"file": ("book.txt", "content", "text/plain")}}),
        ("post", "/textbook-library/missing/split", {"json": {}}),
        ("post", "/textbook-library/missing/assets/extract", {"json": {}}),
        ("post", "/textbook-library/missing/knowledge-points/kp/assets/extract", {"json": {}}),
        ("post", "/textbook-library/assets/missing/confirm", {"json": {}}),
        ("post", "/lesson-plan-library/uploads", {"files": {"file": ("plan.txt", "content", "text/plain")}}),
        ("post", "/lesson-plan-library/import/from-project", {"json": {"project_id": "proj_missing"}}),
    ]
    for method, path, kwargs in blocked_requests:
        response = getattr(teacher, method)(path, **(kwargs or {}))
        unwrap_error(response, 403, "FORBIDDEN")


def test_admin_can_enter_admin_and_write_library_handlers(tmp_path: Path):
    app = make_app(tmp_path)
    _teacher, admin = setup_users(app)

    unwrap_ok(admin.get("/admin/rules"))
    unwrap_ok(admin.get("/admin/media-workbench"))
    unwrap_ok(admin.get("/rules/coverage"))

    # These invalid-resource requests prove admin passed RBAC and reached the handler.
    assert admin.post("/textbook-library/missing/split", json={}).status_code == 404
    assert admin.post("/textbook-library/assets/missing/confirm", json={}).status_code == 404
    assert admin.post("/lesson-plan-library/import/from-project", json={"project_id": "proj_missing"}).status_code == 404
