from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "capabilities_path": str(
                Path(__file__).resolve().parents[3]
                / "docs"
                / "api-research"
                / "octo-video"
                / "capabilities.json"
            ),
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


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "视频画布契约测试",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )


def test_video_workflow_defaults_to_omni_text_canvas(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert data["graph"]["selected_model"] == "omni_flash-10s"
    assert data["graph"]["mode"] == "text"
    assert data["graph"]["duration_sec"] == 10
    assert data["graph"]["size"] == "1280x720"
    assert [node["type"] for node in data["graph"]["nodes"]] == [
        "prompt_input",
        "reference_input",
        "omni_model",
        "video_output",
    ]
    omni = next(item for item in data["capabilities"]["models"] if item["model"] == "omni_flash-10s")
    assert omni["max_seconds"] == 10
    assert omni["max_reference_images"] == 7
    assert data["latest_run"] is None


def test_video_workflow_rejects_reference_upload_over_model_limit(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    files = [
        ("files", (f"ref_{index}.png", b"\x89PNG\r\n\x1a\nfake", "image/png"))
        for index in range(8)
    ]

    error = unwrap_error(
        client.post(f"/projects/{project['project_id']}/video-workflow/assets", files=files),
        400,
        "VIDEO_REFERENCE_LIMIT_EXCEEDED",
    )

    assert "最多 7 张" in error["message"]


def test_video_workflow_rejects_non_image_reference_upload(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("note.txt", b"not an image", "text/plain"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )

    assert "图片" in error["message"]


def test_video_workflow_text_run_does_not_send_reference_fields(tmp_path: Path):
    submitted_payloads: list[dict[str, Any]] = []

    class RecordingVideoProvider:
        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            submitted_payloads.append(payload)
            return {
                "provider_task_id": "remote_video_1",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)

    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "prompt": "一个温暖的课堂导入镜头。",
                "model": "omni_flash-10s",
                "mode": "text",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [],
            },
        )
    )

    assert run["task_type"] == "video_workflow_generation"
    assert submitted_payloads == [
        {
            "model": "omni_flash-10s",
            "prompt": "一个温暖的课堂导入镜头。",
            "size": "1280x720",
        }
    ]
    assert "images" not in submitted_payloads[0]
    assert "reference_image_paths" not in submitted_payloads[0]


def test_video_workflow_reference_run_uses_multipart_paths(tmp_path: Path):
    submitted_payloads: list[dict[str, Any]] = []

    class RecordingVideoProvider:
        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            submitted_payloads.append(payload)
            return {
                "provider_task_id": "remote_video_2",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    upload = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("ref.png", b"\x89PNG\r\n\x1a\nfake", "image/png"))],
        )
    )

    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "prompt": "参考图延展成课堂导入视频。",
                "model": "omni_flash-10s",
                "mode": "reference",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [upload["assets"][0]["asset_id"]],
            },
        )
    )

    assert run["status"] == "queued"
    assert submitted_payloads[0]["model"] == "omni_flash-10s"
    assert "images" not in submitted_payloads[0]
    assert len(submitted_payloads[0]["reference_image_paths"]) == 1
    assert submitted_payloads[0]["reference_image_paths"][0].endswith("ref.png")
