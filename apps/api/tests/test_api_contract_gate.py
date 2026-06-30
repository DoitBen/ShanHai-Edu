from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            **(overrides or {}),
        }
    )
    return TestClient(app)


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert "data" in payload
    return payload["data"]


def unwrap_error(response, expected_status: int, expected_code: str):
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == expected_code
    assert isinstance(payload["error"]["message"], str)
    assert isinstance(payload["error"]["retryable"], bool)
    assert isinstance(payload["error"]["action"], str)
    assert isinstance(payload["error"]["trace_id"], str)
    assert payload["error"]["trace_id"].startswith("trace_")
    return payload["error"]


def create_project(client: TestClient, name: str = "联调门禁项目") -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": name,
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )


def upload_textbook(client: TestClient, project_id: str) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            f"/projects/{project_id}/textbook",
            files={
                "file": (
                    "textbook.txt",
                    "三年级数学，分数的初步认识。学生理解平均分和二分之一。",
                    "text/plain",
                )
            },
        )
    )


def manifest_states(client: TestClient, project_id: str) -> dict[str, str]:
    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    return {node["node_id"]: node["status"] for node in manifest["nodes"]}


def test_api_success_and_error_responses_use_stable_envelope(tmp_path: Path):
    client = make_client(tmp_path)

    health = client.get("/health")
    health_payload = health.json()

    assert health.status_code == 200
    assert health_payload["ok"] is True
    assert health_payload["data"]["status"] == "ok"

    missing = client.get("/projects/proj_missing")

    error = unwrap_error(missing, 404, "PROJECT_NOT_FOUND")
    assert error["message"] == "项目不存在"


def test_minimal_frontend_backend_flow_updates_manifest_states(tmp_path: Path):
    client = make_client(tmp_path)

    project = create_project(client)
    project_id = project["project_id"]

    states = manifest_states(client, project_id)
    assert states["textbook_parse"] == "not_started"
    assert states["lesson_plan"] == "not_started"

    uploaded = upload_textbook(client, project_id)
    assert uploaded["status"] == "uploaded"
    assert uploaded["path"] == "uploads/textbook.txt"

    parse_result = unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate"))
    assert parse_result["status"] == "needs_review"
    assert parse_result["content"]["lesson_title"] == "分数的初步认识"

    states = manifest_states(client, project_id)
    assert states["textbook_parse"] == "needs_review"
    assert states["lesson_plan"] == "not_started"

    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve"))
    assert approved == {"node_id": "textbook_parse", "status": "approved"}

    states = manifest_states(client, project_id)
    assert states["textbook_parse"] == "approved"
    assert states["lesson_plan"] == "not_started"

    lesson = unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate"))
    assert lesson["status"] == "needs_review"
    assert "intro_designs" in lesson["content"]

    states = manifest_states(client, project_id)
    assert states["textbook_parse"] == "approved"
    assert states["lesson_plan"] == "needs_review"


def test_downstream_generate_fails_when_upstream_is_not_approved(tmp_path: Path):
    client = make_client(tmp_path)

    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate"))

    blocked = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate")

    error = unwrap_error(blocked, 409, "UPSTREAM_NOT_APPROVED")
    assert "textbook_parse" in error["message"]
    assert error["retryable"] is False


def test_project_create_rejects_missing_required_fields(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects",
        json={
            "name": "缺字段项目",
            "subject": "math",
            "grade": "3",
            "textbook_version": "renjiao",
            "volume": "xia",
        },
    )

    error = unwrap_error(response, 422, "REQUEST_VALIDATION_FAILED")
    assert error["message"] == "请求参数不符合接口契约"
    assert any("lesson_type" in ".".join(str(part) for part in item["loc"]) for item in error["details"])


def test_configured_auth_blocks_unauthorized_project_create(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})

    response = client.post(
        "/projects",
        json={
            "name": "未授权创建应失败",
            "subject": "math",
            "grade": "3",
            "textbook_version": "renjiao",
            "volume": "xia",
            "lesson_type": "public",
        },
    )

    error = unwrap_error(response, 401, "UNAUTHORIZED")
    assert error["message"] == "未授权访问"


def test_video_workflow_errors_include_stable_next_actions(tmp_path: Path):
    class RecordingVideoProvider:
        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "provider_task_id": "provider_action_test",
                "status": "queued",
                "progress": 0,
                "video_url": None,
            }

    client = make_client(tmp_path)
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    project_id = project["project_id"]

    first = unwrap_ok(
        client.post(
            f"/projects/{project_id}/video-workflow/runs",
            json={
                "client_request_id": "11111111-1111-4111-8111-111111111111",
                "prompt": "create a classroom intro animation",
                "reference_asset_ids": [],
            },
        )
    )
    assert first["status"] in {"submitting", "queued", "processing"}

    active_conflict = client.post(
        f"/projects/{project_id}/video-workflow/runs",
        json={
            "client_request_id": "22222222-2222-4222-8222-222222222222",
            "prompt": "duplicate active run should be blocked",
            "reference_asset_ids": [],
        },
    )
    conflict_error = unwrap_error(active_conflict, 409, "VIDEO_ACTIVE_RUN_EXISTS")
    assert conflict_error["action"] == "wait_for_active_run"
    assert conflict_error["retryable"] is False

    missing_output = client.get(f"/projects/{project_id}/video-workflow/runs/{first['run_id']}/download")
    output_error = unwrap_error(missing_output, 404, "VIDEO_OUTPUT_NOT_FOUND")
    assert output_error["action"] == "retry"
    assert output_error["retryable"] is True


@pytest.mark.xfail(
    reason="P1: 后端当前会 normalize 缺字段内容并写入版本，尚未在服务层拒绝 schema 缺必填字段。",
    strict=True,
)
def test_provider_schema_validation_rejects_missing_required_fields(tmp_path: Path):
    class InvalidTextProvider:
        name = "invalid-test-provider"

        def complete_json(self, **kwargs):
            return {"lesson_title": "缺字段教材解析"}

    client = make_client(tmp_path)
    client.app.state.service.provider = InvalidTextProvider()

    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    response = client.post(f"/projects/{project_id}/nodes/textbook_parse/generate")

    unwrap_error(response, 400, "GENERATION_INPUT_INVALID")


@pytest.mark.xfail(
    reason="架构决策待定：当前最小鉴权仅在配置 BACKEND_API_TOKEN 后启用，本地默认仍开放以便联调。",
    strict=True,
)
def test_unauthorized_request_cannot_create_project(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post(
        "/projects",
        json={
            "name": "未授权创建应失败",
            "subject": "math",
            "grade": "3",
            "textbook_version": "renjiao",
            "volume": "xia",
            "lesson_type": "public",
        },
    )

    assert response.status_code in {401, 403}
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] in {"UNAUTHORIZED", "FORBIDDEN"}
