import base64
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.providers import ProviderError


API_TOKEN = "admin-test-token"


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "backend_api_token": API_TOKEN,
            "imagegen_model": "gpt-image-2",
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


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {API_TOKEN}"}


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


def test_admin_media_workbench_capabilities_defaults_and_readiness(tmp_path: Path):
    client = make_client(tmp_path)

    data = unwrap_ok(client.get("/admin/media-workbench/capabilities", headers=auth_headers()))

    assert data["image"]["default_model"] == "gpt-image-2"
    assert data["image"]["default_size"] == "1920x1080"
    assert data["image"]["default_quality"] == "high"
    assert data["image"]["provider_ready"] is False
    assert data["video"]["default_model"] == "omni_flash-10s"
    assert data["video"]["default_size"] == "1280x720"
    assert data["video"]["default_duration_sec"] == 10
    assert data["video"]["provider_ready"] is False
    omni = next(item for item in data["video"]["models"] if item["model"] == "omni_flash-10s")
    assert omni["max_seconds"] == 10
    assert omni["max_reference_images"] == 7


def test_admin_media_workbench_requires_admin_token(tmp_path: Path):
    client = make_client(tmp_path)

    error = unwrap_error(client.get("/admin/media-workbench"), 404, "NOT_FOUND")

    assert "资源不存在" in error["message"]


def test_admin_media_workbench_image_run_saves_b64_asset_and_payload(tmp_path: Path):
    submitted_payloads: list[dict[str, Any]] = []

    class RecordingImageProvider:
        def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
            submitted_payloads.append(payload)
            return {
                "provider_task_id": "remote_img_1",
                "status": "completed",
                "b64_json": base64.b64encode(b"\x89PNG\r\n\x1a\nfake-image").decode("ascii"),
                "image_url": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"image_provider_mode": "real"})
    client.app.state.service.media_workbench.image_provider = RecordingImageProvider()

    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={
                "prompt": "明亮的小学数学课堂参考图",
                "model": "gpt-image-2",
                "size": "1920x1080",
                "quality": "high",
                "count": 1,
            },
        )
    )

    assert run["task_type"] == "admin_image_generation"
    assert run["status"] == "completed"
    assert run["assets"][0]["asset_type"] == "image"
    assert run["assets"][0]["source"] == "image_run"
    assert Path(run["assets"][0]["path"]).suffix == ".png"
    assert submitted_payloads == [
        {
            "prompt": "明亮的小学数学课堂参考图",
            "model": "gpt-image-2",
            "size": "1920x1080",
            "quality": "high",
            "response_format": "b64_json",
        }
    ]


def test_admin_media_workbench_image_run_saves_url_asset(tmp_path: Path):
    class RecordingImageProvider:
        def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "provider_task_id": "remote_img_url",
                "status": "completed",
                "b64_json": None,
                "image_url": "https://cdn.example/image.png",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path) -> None:
            assert image_url == "https://cdn.example/image.png"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nurl-image")

    client = make_client(tmp_path, {"image_provider_mode": "real"})
    client.app.state.service.media_workbench.image_provider = RecordingImageProvider()

    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={"prompt": "URL 图片保存", "count": 1},
        )
    )

    asset_path = Path(client.app.state.service.media_workbench.asset_path(run["assets"][0]["asset_id"]))
    assert asset_path.read_bytes().startswith(b"\x89PNG")


def test_admin_media_workbench_image_count_runs_concurrently(tmp_path: Path):
    lock = threading.Lock()
    active = 0
    max_active = 0

    class SlowImageProvider:
        def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.15)
            with lock:
                active -= 1
            return {
                "provider_task_id": f"remote_img_{payload['prompt']}",
                "status": "completed",
                "b64_json": base64.b64encode(b"\x89PNG\r\n\x1a\nfake-image").decode("ascii"),
                "image_url": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"image_provider_mode": "real"})
    client.app.state.service.media_workbench.image_provider = SlowImageProvider()

    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={"prompt": "并发图片测试", "count": 3},
        )
    )

    assert len(run["assets"]) == 3
    assert max_active > 1


def test_admin_media_workbench_image_run_requires_configured_provider(tmp_path: Path):
    client = make_client(tmp_path)

    error = unwrap_error(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={"prompt": "课堂图片"},
        ),
        400,
        "IMAGE_PROVIDER_NOT_CONFIGURED",
    )

    assert "图片生成服务未配置" in error["message"]


def test_admin_media_workbench_imports_image_assets_to_video_basket(tmp_path: Path):
    client = make_client(tmp_path, {"image_provider_mode": "real"})
    client.app.state.service.media_workbench.image_provider = type(
        "ImageProvider",
        (),
        {
            "generate_image": lambda self, payload: {
                "provider_task_id": "remote_img_2",
                "status": "completed",
                "b64_json": base64.b64encode(b"\x89PNG\r\n\x1a\nfake-image").decode("ascii"),
                "image_url": None,
                "raw": {},
            }
        },
    )()
    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={"prompt": "可作为视频参考图的图片", "count": 1},
        )
    )

    basket = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/references/import",
            headers=auth_headers(),
            json={"asset_ids": [run["assets"][0]["asset_id"]]},
        )
    )

    assert basket["max_reference_images"] == 7
    assert [item["asset_id"] for item in basket["assets"]] == [run["assets"][0]["asset_id"]]


def test_admin_media_workbench_rejects_reference_upload_over_omni_limit(tmp_path: Path):
    client = make_client(tmp_path)
    files = [
        ("files", (f"ref_{index}.png", b"\x89PNG\r\n\x1a\nfake", "image/png"))
        for index in range(8)
    ]

    error = unwrap_error(
        client.post("/admin/media-workbench/videos/references", headers=auth_headers(), files=files),
        400,
        "VIDEO_REFERENCE_LIMIT_EXCEEDED",
    )

    assert "最多 7 张" in error["message"]


def test_admin_media_workbench_video_text_run_does_not_send_reference_fields(tmp_path: Path):
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
    client.app.state.service.media_workbench.video_provider = RecordingVideoProvider()

    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/runs",
            headers=auth_headers(),
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

    assert run["task_type"] == "admin_video_generation"
    assert submitted_payloads == [
        {
            "model": "omni_flash-10s",
            "prompt": "一个温暖的课堂导入镜头。",
            "size": "1280x720",
        }
    ]
    assert "images" not in submitted_payloads[0]
    assert "reference_image_paths" not in submitted_payloads[0]


def test_admin_media_workbench_video_reference_run_uses_local_asset_paths(tmp_path: Path):
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
    client.app.state.service.media_workbench.video_provider = RecordingVideoProvider()
    upload = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/references",
            headers=auth_headers(),
            files=[("files", ("ref.png", b"\x89PNG\r\n\x1a\nfake", "image/png"))],
        )
    )

    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/runs",
            headers=auth_headers(),
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
    assert "images" not in submitted_payloads[0]
    assert len(submitted_payloads[0]["reference_image_paths"]) == 1
    assert submitted_payloads[0]["reference_image_paths"][0].endswith("ref.png")


def test_admin_media_workbench_sync_commits_video_run_update(tmp_path: Path):
    class RecordingVideoProvider:
        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "provider_task_id": "remote_video_commit",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

        def query_task(self, provider_task_id: str) -> dict[str, Any]:
            return {
                "provider_task_id": provider_task_id,
                "status": "processing",
                "progress": 50,
                "video_url": None,
                "error_message": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.media_workbench.video_provider = RecordingVideoProvider()
    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/runs",
            headers=auth_headers(),
            json={
                "prompt": "提交后同步状态需要持久化。",
                "model": "omni_flash-10s",
                "mode": "text",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [],
            },
        )
    )

    synced = unwrap_ok(
        client.post(
            f"/admin/media-workbench/videos/runs/{run['run_id']}/sync",
            headers=auth_headers(),
            json={},
        )
    )
    fetched = unwrap_ok(
        client.get(
            f"/admin/media-workbench/videos/runs/{run['run_id']}",
            headers=auth_headers(),
        )
    )

    assert synced["status"] == "processing"
    assert fetched["status"] == "processing"
    assert fetched["progress"] == 50


def test_admin_media_workbench_sync_retries_transient_sqlite_readonly(tmp_path: Path):
    class RecordingVideoProvider:
        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "provider_task_id": "remote_video_retry",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

        def query_task(self, provider_task_id: str) -> dict[str, Any]:
            return {
                "provider_task_id": provider_task_id,
                "status": "processing",
                "progress": 60,
                "video_url": None,
                "error_message": None,
                "raw": {},
            }

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.media_workbench.video_provider = RecordingVideoProvider()
    run = unwrap_ok(
        client.post(
            "/admin/media-workbench/videos/runs",
            headers=auth_headers(),
            json={
                "prompt": "同步遇到 SQLite 瞬态只读时需要重试。",
                "model": "omni_flash-10s",
                "mode": "text",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [],
            },
        )
    )
    store = client.app.state.service.media_workbench.store
    original_update_task = store.update_task
    calls = {"count": 0}

    def flaky_update_task(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise sqlite3.OperationalError("attempt to write a readonly database")
        return original_update_task(*args, **kwargs)

    store.update_task = flaky_update_task

    synced = unwrap_ok(
        client.post(
            f"/admin/media-workbench/videos/runs/{run['run_id']}/sync",
            headers=auth_headers(),
            json={},
        )
    )

    assert synced["status"] == "processing"
    assert synced["progress"] == 60
    assert calls["count"] == 2


def test_admin_media_workbench_provider_errors_are_sanitized(tmp_path: Path):
    class FailingImageProvider:
        def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                "HTTP 500",
                retryable=True,
                response_excerpt='{"Authorization":"Bearer secret-token","message":"bad"}',
            )

    client = make_client(tmp_path, {"image_provider_mode": "real"})
    client.app.state.service.media_workbench.image_provider = FailingImageProvider()

    error = unwrap_error(
        client.post(
            "/admin/media-workbench/images/runs",
            headers=auth_headers(),
            json={"prompt": "课堂图片"},
        ),
        502,
        "IMAGE_REQUEST_FAILED",
    )

    assert "secret-token" not in str(error)
