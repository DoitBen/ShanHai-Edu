import json
import threading
import time
import uuid
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from conftest import create_auth_user, login_as
from app.providers import ProviderError

MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
PROJECT_CREATE_TOKEN = "video-workflow-test-token"


class RecordingVideoProvider:
    def __init__(self):
        self.submitted: list[dict[str, Any]] = []

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append(payload)
        return {
            "provider_task_id": f"remote_{len(self.submitted)}",
            "status": "queued",
            "progress": 0,
            "video_url": None,
        }


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "backend_api_token": PROJECT_CREATE_TOKEN,
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
    client = TestClient(app)
    create_auth_user(client, email="video-workflow-owner@example.com")
    login_as(client, email="video-workflow-owner@example.com")
    return client


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


def project_create_headers(client: TestClient) -> dict[str, str]:
    token = client.app.state.settings.backend_api_token
    return {"Authorization": f"Bearer {token}"}


def image_bytes(fmt: str = "PNG", size: tuple[int, int] = (64, 48)) -> bytes:
    stream = BytesIO()
    Image.new("RGB", size, (24, 110, 180)).save(stream, format=fmt)
    return stream.getvalue()


def insert_legacy_manifest_asset(project_dir: Path, asset: dict[str, Any]) -> None:
    manifest = project_dir / "video_workflow" / "assets.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps([asset], ensure_ascii=False, indent=2), encoding="utf-8")


def read_asset_row(client: TestClient, project_dir: Path, asset_id: str) -> dict[str, Any]:
    with client.app.state.store.connect(project_dir) as conn:
        row = conn.execute(
            "SELECT * FROM video_workflow_assets WHERE asset_id = ?",
            (asset_id,),
        ).fetchone()
    assert row is not None
    return dict(row)


def force_db_asset_deleted_at(client: TestClient, project_dir: Path, asset_id: str, deleted_at: str) -> None:
    with client.app.state.store.connect(project_dir) as conn:
        conn.execute(
            "UPDATE video_workflow_assets SET deleted_at = ?, updated_at = ? WHERE asset_id = ?",
            (deleted_at, deleted_at, asset_id),
        )


def write_manifest_asset_snapshot(project_dir: Path, asset: dict[str, Any]) -> None:
    manifest_path = project_dir / "video_workflow" / "assets.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps([asset], ensure_ascii=False, indent=2), encoding="utf-8")


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


def test_video_workflow_provider_readiness_explains_missing_key(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real", "octo_api_key": None})
    project = create_project(client)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert data["config"]["provider_ready"] is False
    assert data["config"]["provider_reason_code"] == "VIDEO_PROVIDER_KEY_MISSING"
    assert "密钥" in data["config"]["provider_user_message"]


def test_video_workflow_config_exposes_storage_lifecycle_policy(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    lifecycle = data["config"]["storage_lifecycle"]
    assert lifecycle["project_reference_quota_bytes"] > 0
    assert lifecycle["soft_delete_retention_days"] >= 1
    assert lifecycle["failed_run_retention_days"] >= 1
    assert lifecycle["temporary_file_retention_hours"] >= 1
    assert lifecycle["backup_recommendation"] == "backup_project_directory_before_physical_purge"
    assert data["storage_usage"]["reference_asset_bytes"] == 0
    assert data["storage_usage"]["deleted_reference_asset_bytes"] == 0
    assert data["storage_usage"]["active_reference_asset_count"] == 0


def test_video_workflow_config_declares_single_process_concurrency_boundary(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    boundary = data["config"]["runtime_concurrency"]
    assert boundary["lock_scope"] == "single_api_process"
    assert boundary["supports_multi_worker"] is False
    assert "单 API 进程" in boundary["deployment_warning"]


def test_video_workflow_allows_project_asset_library_above_run_limit(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    files = [
        ("files", (f"ref_{index}.png", image_bytes("PNG"), "image/png"))
        for index in range(8)
    ]

    data = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/assets", files=files))

    assert len(data["assets"]) == 8
    assert data["max_reference_images"] == 7


def test_video_workflow_upload_records_real_metadata(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    response = client.post(
        f"/projects/{project['project_id']}/video-workflow/assets",
        files=[
            ("files", ("one.png", image_bytes("PNG"), "image/png")),
            ("files", ("two.jpg", image_bytes("JPEG", (80, 60)), "image/jpeg")),
        ],
    )
    data = unwrap_ok(response)
    assert [(item["mime_type"], item["width"], item["height"]) for item in data["assets"]] == [
        ("image/png", 64, 48),
        ("image/jpeg", 80, 60),
    ]
    assert all(item["byte_size"] > 0 for item in data["assets"])
    assert all(item["deleted_at"] is None for item in data["assets"])


def test_video_workflow_upload_delete_and_cleanup_persist_asset_metadata_to_sqlite(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("sqlite.png", image_bytes("PNG"), "image/png"))],
        )
    )
    asset = uploaded["assets"][0]

    with client.app.state.store.connect(project_dir) as conn:
        row = conn.execute(
            """
            SELECT asset_id, project_id, filename, path, mime_type, byte_size,
                   width, height, source, deleted_at, purged_at
            FROM video_workflow_assets
            WHERE asset_id = ?
            """,
            (asset["asset_id"],),
        ).fetchone()
        assert dict(row) == {
            "asset_id": asset["asset_id"],
            "project_id": project["project_id"],
            "filename": "sqlite.png",
            "path": asset["path"],
            "mime_type": "image/png",
            "byte_size": asset["byte_size"],
            "width": 64,
            "height": 48,
            "source": "upload",
            "deleted_at": None,
            "purged_at": None,
        }

    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{asset['asset_id']}"))
    with client.app.state.store.connect(project_dir) as conn:
        deleted_at = conn.execute(
            "SELECT deleted_at FROM video_workflow_assets WHERE asset_id = ?",
            (asset["asset_id"],),
        ).fetchone()["deleted_at"]
    assert deleted_at

    force_db_asset_deleted_at(client, project_dir, asset["asset_id"], "2000-01-01T00:00:00+00:00")
    unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/storage/cleanup"))

    with client.app.state.store.connect(project_dir) as conn:
        purged_at = conn.execute(
            "SELECT purged_at FROM video_workflow_assets WHERE asset_id = ?",
            (asset["asset_id"],),
        ).fetchone()["purged_at"]
    assert purged_at


def test_video_workflow_migrates_legacy_manifest_to_sqlite_runtime_source(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    reference_dir = project_dir / "video_workflow" / "references"
    reference_dir.mkdir(parents=True, exist_ok=True)
    reference_path = reference_dir / "legacy.png"
    reference_path.write_bytes(image_bytes("PNG"))
    legacy_asset = {
        "asset_id": "vref_legacy_manifest_only",
        "filename": "legacy.png",
        "path": "video_workflow/references/legacy.png",
        "mime_type": "image/png",
        "byte_size": reference_path.stat().st_size,
        "width": 64,
        "height": 48,
        "created_at": "2026-06-29T00:00:00+00:00",
        "deleted_at": None,
    }
    insert_legacy_manifest_asset(project_dir, legacy_asset)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert [asset["asset_id"] for asset in data["assets"]] == ["vref_legacy_manifest_only"]
    with client.app.state.store.connect(project_dir) as conn:
        row = conn.execute(
            "SELECT asset_id, source FROM video_workflow_assets WHERE asset_id = ?",
            ("vref_legacy_manifest_only",),
        ).fetchone()
    assert dict(row)["source"] == "legacy_manifest"


def test_video_workflow_db_asset_source_wins_when_manifest_is_inconsistent(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("db.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]
    stale_asset = {
        "asset_id": "vref_stale_manifest_only",
        "filename": "stale.png",
        "path": "video_workflow/references/stale.png",
        "mime_type": "image/png",
        "byte_size": 10,
        "width": 1,
        "height": 1,
        "created_at": "2026-06-29T00:00:00+00:00",
        "deleted_at": None,
    }
    insert_legacy_manifest_asset(project_dir, stale_asset)

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert [asset["asset_id"] for asset in data["assets"]] == [uploaded["asset_id"]]


def test_video_workflow_does_not_recover_runtime_db_row_from_manifest_after_migration_completed(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("recover.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]
    with client.app.state.store.connect(project_dir) as conn:
        conn.execute("DELETE FROM video_workflow_assets WHERE asset_id = ?", (uploaded["asset_id"],))

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert data["assets"] == []
    with client.app.state.store.connect(project_dir) as conn:
        row = conn.execute(
            "SELECT asset_id, source FROM video_workflow_assets WHERE asset_id = ?",
            (uploaded["asset_id"],),
        ).fetchone()
    assert row is None


def test_video_workflow_db_asset_stays_active_when_manifest_marks_deleted(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("active.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]
    write_manifest_asset_snapshot(project_dir, {**uploaded, "deleted_at": "2000-01-01T00:00:00+00:00"})

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert [asset["asset_id"] for asset in data["assets"]] == [uploaded["asset_id"]]
    assert read_asset_row(client, project_dir, uploaded["asset_id"])["deleted_at"] is None


def test_video_workflow_db_deleted_wins_when_manifest_still_active(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("deleted.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]
    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{uploaded['asset_id']}"))
    write_manifest_asset_snapshot(project_dir, {**uploaded, "deleted_at": None, "purged_at": None})

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert data["assets"] == []
    assert read_asset_row(client, project_dir, uploaded["asset_id"])["deleted_at"]


def test_video_workflow_upload_succeeds_when_json_snapshot_write_fails(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])

    def fail_snapshot(path: Path, value: Any) -> None:
        raise OSError("snapshot disk unavailable")

    monkeypatch.setattr("app.video_workflow._write_json_atomic", fail_snapshot)

    data = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("snapshot-fail.png", image_bytes("PNG"), "image/png"))],
        )
    )

    uploaded = data["uploaded"][0]
    assert read_asset_row(client, project_dir, uploaded["asset_id"])["asset_id"] == uploaded["asset_id"]


def test_video_workflow_delete_succeeds_when_json_snapshot_write_fails(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("delete-snapshot-fail.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]

    def fail_snapshot(path: Path, value: Any) -> None:
        raise OSError("snapshot disk unavailable")

    monkeypatch.setattr("app.video_workflow._write_json_atomic", fail_snapshot)

    deleted = unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{uploaded['asset_id']}"))

    assert deleted["deleted"] is True
    assert read_asset_row(client, project_dir, uploaded["asset_id"])["deleted_at"]


def test_video_workflow_cleanup_ignores_stale_manifest_retention_state(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("cleanup-stale.png", image_bytes("PNG"), "image/png"))],
        )
    )["uploaded"][0]
    write_manifest_asset_snapshot(project_dir, {**uploaded, "deleted_at": "2000-01-01T00:00:00+00:00"})

    cleanup = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/storage/cleanup"))

    assert cleanup["purged_reference_assets"] == []
    row = read_asset_row(client, project_dir, uploaded["asset_id"])
    assert row["deleted_at"] is None
    assert row["purged_at"] is None


def test_video_workflow_legacy_manifest_migration_runs_only_while_database_empty(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    reference_dir = project_dir / "video_workflow" / "references"
    reference_dir.mkdir(parents=True, exist_ok=True)
    reference_path = reference_dir / "legacy-once.png"
    reference_path.write_bytes(image_bytes("PNG"))
    legacy_asset = {
        "asset_id": "vref_legacy_once",
        "filename": "legacy-once.png",
        "path": "video_workflow/references/legacy-once.png",
        "mime_type": "image/png",
        "byte_size": reference_path.stat().st_size,
        "width": 64,
        "height": 48,
        "created_at": "2026-06-29T00:00:00+00:00",
        "deleted_at": None,
    }
    insert_legacy_manifest_asset(project_dir, legacy_asset)
    first = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))
    assert [asset["asset_id"] for asset in first["assets"]] == ["vref_legacy_once"]

    write_manifest_asset_snapshot(project_dir, {**legacy_asset, "deleted_at": "2000-01-01T00:00:00+00:00"})
    second = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert [asset["asset_id"] for asset in second["assets"]] == ["vref_legacy_once"]
    assert read_asset_row(client, project_dir, "vref_legacy_once")["deleted_at"] is None


def test_video_workflow_upload_enforces_project_reference_storage_quota(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = create_project(client)
    service = client.app.state.service.video_workflow
    monkeypatch.setattr("app.video_workflow.PROJECT_REFERENCE_QUOTA_BYTES", 200)

    first = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("one.png", image_bytes(), "image/png"))],
        )
    )
    assert first["storage_usage"]["reference_asset_bytes"] > 0
    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("two.png", image_bytes(), "image/png"))],
        ),
        413,
        "VIDEO_STORAGE_QUOTA_EXCEEDED",
    )
    usage = service.storage_usage(project["project_id"])
    assert error["details"]["quota_bytes"] == 200
    assert error["details"]["current_bytes"] == usage["reference_asset_bytes"]
    assert error["details"]["attempted_bytes"] > 0


def test_video_workflow_upload_rejects_fake_image(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("fake.png", b"not an image", "image/png"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )


def test_video_workflow_upload_rejects_reference_image_above_max_dimensions(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.video_workflow.MAX_IMAGE_WIDTH", 32)
    monkeypatch.setattr("app.video_workflow.MAX_IMAGE_HEIGHT", 32)
    client = make_client(tmp_path)
    project = create_project(client)

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("too-wide.png", image_bytes("PNG", (64, 48)), "image/png"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )

    assert "宽高" in error["message"]


def test_video_workflow_upload_rejects_reference_image_above_max_pixels(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.video_workflow.MAX_IMAGE_WIDTH", 128)
    monkeypatch.setattr("app.video_workflow.MAX_IMAGE_HEIGHT", 128)
    monkeypatch.setattr("app.video_workflow.MAX_IMAGE_PIXELS", 1024)
    client = make_client(tmp_path)
    project = create_project(client)

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("too-many-pixels.png", image_bytes("PNG", (64, 48)), "image/png"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )

    assert "像素" in error["message"]


def test_video_workflow_upload_handles_decompression_bomb_as_controlled_4xx(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)
    client = make_client(tmp_path)
    project = create_project(client)

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("bomb.png", image_bytes("PNG", (64, 48)), "image/png"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )

    assert "过大" in error["message"] or "像素" in error["message"]


def test_video_workflow_soft_delete_keeps_historical_metadata(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("one.png", image_bytes(), "image/png"))],
        )
    )
    asset_id = uploaded["assets"][0]["asset_id"]
    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{asset_id}"))
    workbench = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))
    assert workbench["assets"] == []
    manifest = json.loads(
        (Path(project["project_dir"]) / "video_workflow" / "assets.json").read_text(encoding="utf-8")
    )
    assert manifest[0]["asset_id"] == asset_id
    assert manifest[0]["deleted_at"]


def test_video_workflow_cleanup_purges_expired_soft_deleted_reference_files(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("old.png", image_bytes(), "image/png"))],
        )
    )
    asset_id = uploaded["assets"][0]["asset_id"]
    asset_file = Path(project["project_dir"]) / uploaded["assets"][0]["path"]
    assert asset_file.exists()
    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{asset_id}"))
    manifest_path = Path(project["project_dir"]) / "video_workflow" / "assets.json"
    force_db_asset_deleted_at(client, Path(project["project_dir"]), asset_id, "2000-01-01T00:00:00+00:00")

    cleanup = client.app.state.service.video_workflow.cleanup_storage(project["project_id"])

    assert cleanup["purged_reference_assets"] == [asset_id]
    assert not asset_file.exists()
    retained = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained[0]["asset_id"] == asset_id
    assert retained[0]["purged_at"]
    assert retained[0]["byte_size"] == uploaded["assets"][0]["byte_size"]
    usage = client.app.state.service.video_workflow.storage_usage(project["project_id"])
    assert usage["deleted_reference_asset_bytes"] == 0


def test_video_workflow_storage_endpoint_reports_usage_and_cleanup(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("old.png", image_bytes(), "image/png"))],
        )
    )
    asset_id = uploaded["assets"][0]["asset_id"]
    asset_file = Path(project["project_dir"]) / uploaded["assets"][0]["path"]
    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{asset_id}"))
    manifest_path = Path(project["project_dir"]) / "video_workflow" / "assets.json"
    force_db_asset_deleted_at(client, Path(project["project_dir"]), asset_id, "2000-01-01T00:00:00+00:00")

    before = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow/storage"))
    cleanup = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/storage/cleanup"))
    after = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow/storage"))

    assert before["policy"]["soft_delete_retention_days"] >= 1
    assert before["usage"]["deleted_reference_asset_bytes"] == uploaded["assets"][0]["byte_size"]
    assert cleanup["purged_reference_assets"] == [asset_id]
    assert cleanup["storage_usage"]["deleted_reference_asset_bytes"] == 0
    assert not asset_file.exists()
    assert after["usage"]["deleted_reference_asset_bytes"] == 0
    retained = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert retained[0]["asset_id"] == asset_id
    assert retained[0]["purged_at"]


def test_video_workflow_cleanup_marks_expired_failed_runs(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        old_task = client.app.state.store.create_task(
            conn,
            project["project_id"],
            "video_workflow",
            "video_workflow_generation",
            {"prompt": "old failed run", "reference_asset_ids": []},
            status="failed",
            result={"error_code": "VIDEO_TASK_FAILED"},
            error_message="old failure",
        )
        fresh_task = client.app.state.store.create_task(
            conn,
            project["project_id"],
            "video_workflow",
            "video_workflow_generation",
            {"prompt": "fresh failed run", "reference_asset_ids": []},
            status="failed",
            result={"error_code": "VIDEO_TASK_FAILED"},
            error_message="fresh failure",
        )
        conn.execute(
            "UPDATE tasks SET updated_at = ? WHERE task_id = ?",
            ("2000-01-01T00:00:00+00:00", old_task["task_id"]),
        )

    cleanup = client.app.state.service.video_workflow.cleanup_storage(project["project_id"])

    assert cleanup["expired_failed_runs"] == [old_task["task_id"]]
    old_after = client.app.state.store.task(project["project_id"], old_task["task_id"])
    fresh_after = client.app.state.store.task(project["project_id"], fresh_task["task_id"])
    assert old_after["status"] == "failed"
    assert old_after["result"]["retention_status"] == "expired"
    assert old_after["result"]["expired_at"]
    assert fresh_after["result"].get("retention_status") is None


def test_video_workflow_partial_upload_keeps_valid_files(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    data = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[
                ("files", ("valid.png", image_bytes(), "image/png")),
                ("files", ("bad.png", b"not-image", "image/png")),
            ],
        )
    )
    assert [item["filename"] for item in data["uploaded"]] == ["valid.png"]
    assert data["errors"][0]["filename"] == "bad.png"
    assert data["errors"][0]["code"] == "VIDEO_REFERENCE_INVALID"


def test_video_workflow_concurrent_asset_uploads_preserve_manifest(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = create_project(client)
    service = client.app.state.service.video_workflow
    original_all_assets = service._all_reference_assets
    final_read_barrier = threading.Barrier(2)
    thread_state = threading.local()
    counter_lock = threading.Lock()
    counter = {"value": 0}

    def fake_save_one_asset(project_dir: Path, file: Any) -> dict[str, Any]:
        with counter_lock:
            counter["value"] += 1
            index = counter["value"]
        thread_state.after_save = True
        return {
            "asset_id": f"vref_concurrent_{index}",
            "filename": f"ref_{index}.png",
            "path": f"video_workflow/references/ref_{index}.png",
            "mime_type": "image/png",
            "byte_size": 128,
            "width": 64,
            "height": 48,
            "created_at": "2026-06-29T00:00:00+00:00",
            "deleted_at": None,
        }

    def synchronized_final_manifest_read(project_dir: Path) -> list[dict[str, Any]]:
        if getattr(thread_state, "after_save", False):
            snapshot = original_all_assets(project_dir)
            try:
                final_read_barrier.wait(timeout=1)
            except threading.BrokenBarrierError:
                pass
            return snapshot
        return original_all_assets(project_dir)

    monkeypatch.setattr(service, "_save_one_asset", fake_save_one_asset)
    monkeypatch.setattr(service, "_all_reference_assets", synchronized_final_manifest_read)
    results: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def upload_once(name: str):
        try:
            results.append(service.upload_assets(project["project_id"], [type("Upload", (), {"filename": name})()]))
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [
        threading.Thread(target=upload_once, args=("left.png",)),
        threading.Thread(target=upload_once, args=("right.png",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    assert len(results) == 2
    manifest = json.loads(
        (Path(project["project_dir"]) / "video_workflow" / "assets.json").read_text(encoding="utf-8")
    )
    assert {item["asset_id"] for item in manifest} == {"vref_concurrent_1", "vref_concurrent_2"}


def test_video_workflow_upload_does_not_undo_concurrent_soft_delete(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = create_project(client)
    service = client.app.state.service.video_workflow
    existing = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("existing.png", image_bytes(), "image/png"))],
        )
    )["assets"][0]
    original_all_assets = service._all_reference_assets
    upload_write_barrier = threading.Barrier(2)
    thread_state = threading.local()

    def fake_save_one_asset(project_dir: Path, file: Any) -> dict[str, Any]:
        thread_state.after_save = True
        return {
            "asset_id": "vref_new_upload",
            "filename": "new.png",
            "path": "video_workflow/references/new.png",
            "mime_type": "image/png",
            "byte_size": 128,
            "width": 64,
            "height": 48,
            "created_at": "2026-06-29T00:00:00+00:00",
            "deleted_at": None,
        }

    def synchronized_upload_manifest_read(project_dir: Path) -> list[dict[str, Any]]:
        if getattr(thread_state, "after_save", False):
            snapshot = original_all_assets(project_dir)
            try:
                upload_write_barrier.wait(timeout=1)
            except threading.BrokenBarrierError:
                pass
            return snapshot
        return original_all_assets(project_dir)

    monkeypatch.setattr(service, "_save_one_asset", fake_save_one_asset)
    monkeypatch.setattr(service, "_all_reference_assets", synchronized_upload_manifest_read)
    errors: list[BaseException] = []

    def upload_new():
        try:
            service.upload_assets(project["project_id"], [type("Upload", (), {"filename": "new.png"})()])
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    upload_thread = threading.Thread(target=upload_new)
    upload_thread.start()
    upload_write_barrier.wait(timeout=1)
    service.delete_asset(project["project_id"], existing["asset_id"])
    upload_thread.join(timeout=5)

    assert not errors
    manifest = json.loads(
        (Path(project["project_dir"]) / "video_workflow" / "assets.json").read_text(encoding="utf-8")
    )
    assets = {item["asset_id"]: item for item in manifest}
    assert assets[existing["asset_id"]]["deleted_at"]
    assert "vref_new_upload" in assets


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
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    provider = RecordingVideoProvider()
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)

    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "一个温暖的课堂导入镜头。",
                "model": "omni_flash-10s",
                "mode": "text",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [],
            },
        )
    )

    assert run["status"] == "queued"
    assert provider.submitted == [
        {
            "model": "omni_flash-10s",
            "prompt": "一个温暖的课堂导入镜头。",
            "size": "1280x720",
        }
    ]
    assert "images" not in provider.submitted[0]
    assert "reference_image_paths" not in provider.submitted[0]


def test_video_workflow_reference_run_uses_multipart_paths(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    provider = RecordingVideoProvider()
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    upload = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("ref.png", image_bytes(), "image/png"))],
        )
    )

    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
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
    assert provider.submitted[0]["model"] == "omni_flash-10s"
    assert "images" not in provider.submitted[0]
    assert len(provider.submitted[0]["reference_images"]) == 1
    assert provider.submitted[0]["reference_images"][0]["path"].endswith(".png")
    assert provider.submitted[0]["reference_images"][0]["mime_type"] == "image/png"


def test_video_workflow_reference_run_rejects_purged_reference_before_provider_submit(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    provider = RecordingVideoProvider()
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    upload = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("expired.png", image_bytes(), "image/png"))],
        )
    )
    asset = upload["assets"][0]
    project_dir = Path(project["project_dir"])
    (project_dir / asset["path"]).unlink()

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "素材已被物理清理时不能继续提交付费任务。",
                "model": "omni_flash-10s",
                "mode": "reference",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": [asset["asset_id"]],
            },
        ),
        410,
        "VIDEO_REFERENCE_EXPIRED",
    )

    assert "重新上传" in error["message"]
    assert provider.submitted == []


def test_video_workflow_create_is_idempotent_and_server_owned(tmp_path: Path):
    provider = RecordingVideoProvider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    request = {
        "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
        "prompt": "triangle blocks form a bridge",
        "reference_asset_ids": [],
        "model": "forged-model",
        "size": "999x999",
        "duration_sec": 999,
    }

    first = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=request))
    second = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=request))

    assert first["run_id"] == second["run_id"]
    assert len(provider.submitted) == 1
    assert first["model"] == "omni_flash-10s"
    assert first["size"] == "1280x720"
    assert first["duration_sec"] == 10


def test_video_workflow_create_idempotency_handles_twenty_concurrent_requests(tmp_path: Path):
    class SlowProvider:
        def __init__(self):
            self.submitted: list[dict[str, Any]] = []
            self.lock = threading.Lock()

        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            time.sleep(0.05)
            with self.lock:
                self.submitted.append(payload)
                index = len(self.submitted)
            return {
                "provider_task_id": f"remote_{index}",
                "status": "queued",
                "progress": 0,
            }

    provider = SlowProvider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    request = {
        "client_request_id": "11111111-2222-4333-8444-555555555555",
        "prompt": "twenty concurrent idempotent requests",
        "reference_asset_ids": [],
    }
    results: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def create_once():
        try:
            results.append(client.app.state.service.video_workflow.create_run(project["project_id"], request))
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=create_once) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    assert len(results) == 20
    assert {item["run_id"] for item in results} == {results[0]["run_id"]}
    assert len(provider.submitted) == 1


def test_video_workflow_same_id_with_different_payload_conflicts(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    base = {
        "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
        "prompt": "first",
        "reference_asset_ids": [],
    }

    unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=base))
    unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={**base, "prompt": "different"},
        ),
        409,
        "VIDEO_REQUEST_CONFLICT",
    )


def test_video_workflow_rejects_second_active_run_per_project(tmp_path: Path):
    provider = RecordingVideoProvider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)

    first = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "first active run",
                "reference_asset_ids": [],
            },
        )
    )
    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "second active run",
                "reference_asset_ids": [],
            },
        ),
        409,
        "VIDEO_ACTIVE_RUN_EXISTS",
    )

    assert first["status"] == "queued"
    assert "正在生成" in error["message"]
    assert len(provider.submitted) == 1


def test_video_workflow_rate_limits_project_run_creation_window(tmp_path: Path, monkeypatch):
    provider = RecordingVideoProvider()
    monkeypatch.setattr("app.video_workflow.RUN_CREATE_PROJECT_WINDOW_LIMIT", 2)
    monkeypatch.setattr("app.video_workflow.RUN_CREATE_GLOBAL_WINDOW_LIMIT", 100)
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    project_dir = Path(client.app.state.store.get_project(project["project_id"])["project_dir"])

    for index in range(2):
        run = unwrap_ok(
            client.post(
                f"/projects/{project['project_id']}/video-workflow/runs",
                json={
                    "client_request_id": str(uuid.uuid4()),
                    "prompt": f"rate limited run {index}",
                    "reference_asset_ids": [],
                },
            )
        )
        task = client.app.state.store.task(project["project_id"], run["run_id"])
        with client.app.state.store.connect(project_dir) as conn:
            client.app.state.store.update_task(
                conn,
                run["run_id"],
                "failed",
                {**task["result"], "retryable": False, "error_code": "TEST_SETTLED"},
                "settled for next create",
            )

    error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "third run should be limited",
                "reference_asset_ids": [],
            },
        ),
        429,
        "VIDEO_RATE_LIMITED",
    )

    assert "过于频繁" in error["message"]
    assert error["retryable"] is True
    assert len(provider.submitted) == 2


def test_video_workflow_returns_latest_fifty_runs(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.video_workflow.RUN_CREATE_PROJECT_WINDOW_LIMIT", 100)
    monkeypatch.setattr("app.video_workflow.RUN_CREATE_GLOBAL_WINDOW_LIMIT", 100)
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    project_dir = Path(client.app.state.store.get_project(project["project_id"])["project_dir"])
    for index in range(55):
        run = unwrap_ok(
            client.post(
                f"/projects/{project['project_id']}/video-workflow/runs",
                json={
                    "client_request_id": str(uuid.uuid4()),
                    "prompt": f"prompt {index}",
                    "reference_asset_ids": [],
                },
            )
        )
        task = client.app.state.store.task(project["project_id"], run["run_id"])
        with client.app.state.store.connect(project_dir) as conn:
            client.app.state.store.update_task(
                conn,
                run["run_id"],
                "completed",
                {
                    **task["result"],
                    "download_status": "downloaded",
                    "download_path": f"video_workflow/runs/{run['run_id']}.mp4",
                },
            )

    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert len(data["runs"]) == 50
    assert data["runs"][0]["prompt"] == "prompt 54"


def test_video_workflow_uncertain_submit_is_saved_without_auto_retry(tmp_path: Path):
    class TimeoutProvider:
        def __init__(self):
            self.submitted = 0

        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.submitted += 1
            raise ProviderError("OCTO_REQUEST_FAILED", "timeout", retryable=True)

    provider = TimeoutProvider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)

    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "network timeout should not auto retry",
                "reference_asset_ids": [],
            },
        )
    )
    workbench = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))

    assert provider.submitted == 1
    assert run["status"] == "submission_unknown"
    assert run["error_code"] == "VIDEO_SUBMIT_UNCERTAIN"
    assert run["retryable"] is False
    assert workbench["runs"][0]["run_id"] == run["run_id"]


def test_stale_submitting_without_provider_id_recovers_to_submission_unknown(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.submitted = 0

        def submit_video(self, payload):
            self.submitted += 1
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    request_id = "22222222-3333-4444-8555-666666666666"
    payload = {
        "client_request_id": request_id,
        "prompt": "stale local submitting row",
        "reference_asset_ids": [],
        "reference_assets": [],
        "model": "omni_flash-10s",
        "size": "1280x720",
        "duration_sec": 10,
    }
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project["project_id"],
            "video_workflow",
            "video_workflow_generation",
            payload,
            status="submitting",
            result={
                "provider_phase": "submit",
                "download_status": "not_started",
                "submission_started_at": "2000-01-01T00:00:00+00:00",
                "submission_attempt": 1,
                "submission_lease_expires_at": "2000-01-01T00:05:00+00:00",
            },
            client_request_id=request_id,
        )

    recovered = client.app.state.service.video_workflow.get_run(project["project_id"], task["task_id"])

    assert recovered["status"] == "submission_unknown"
    assert recovered["error_code"] == "VIDEO_SUBMIT_UNCERTAIN"
    assert recovered["retryable"] is False
    assert provider.submitted == 0


def test_completed_sync_downloads_once_atomically(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.downloads = 0

        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/result.mp4",
            }

        def download_video(self, url, target):
            self.downloads += 1
            Path(target).write_bytes(MP4_BYTES)

    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "test",
                "reference_asset_ids": [],
            },
        )
    )

    first = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    second = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    assert first["status"] == second["status"] == "completed"
    assert first["download_status"] == second["download_status"] == "downloaded"
    assert provider.downloads == 1


def test_completed_without_video_url_stays_queryable_for_delayed_download(tmp_path: Path, monkeypatch):
    class Provider:
        def __init__(self):
            self.queries = 0
            self.downloads = 0

        def submit_video(self, payload):
            return {"provider_task_id": "remote_delayed_url", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            self.queries += 1
            if self.queries == 1:
                return {"provider_task_id": task_id, "status": "completed", "progress": 100}
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/delayed.mp4",
            }

        def download_video(self, url, target):
            self.downloads += 1
            Path(target).write_bytes(MP4_BYTES)

    monkeypatch.setattr("app.video_workflow.MIN_PROVIDER_SYNC_INTERVAL_SEC", 0)
    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "completed status arrives before media url",
                "reference_asset_ids": [],
            },
        )
    )

    pending = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    completed = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    assert pending["status"] == "completed_pending_download"
    assert pending["download_status"] == "pending_url"
    assert pending["video_ready"] is False
    assert completed["status"] == "completed"
    assert completed["download_status"] == "downloaded"
    assert completed["video_ready"] is True
    assert provider.downloads == 1


def test_pending_url_times_out_and_allows_new_run_and_retry(tmp_path: Path, monkeypatch):
    class Provider:
        def __init__(self):
            self.queries = 0
            self.downloads = 0
            self.submissions: list[dict[str, Any]] = []

        def submit_video(self, payload):
            self.submissions.append(payload)
            return {"provider_task_id": f"remote_{len(self.submissions)}", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            self.queries += 1
            return {"provider_task_id": task_id, "status": "completed", "progress": 100}

        def download_video(self, url, target):
            self.downloads += 1
            Path(target).write_bytes(MP4_BYTES)

    monkeypatch.setattr("app.video_workflow.MIN_PROVIDER_SYNC_INTERVAL_SEC", 0)
    monkeypatch.setattr("app.video_workflow.PENDING_URL_TIMEOUT_SECONDS", 1)
    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "provider never returns video url",
                "reference_asset_ids": [],
            },
        )
    )

    pending = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    assert pending["status"] == "completed_pending_download"
    assert pending["download_status"] == "pending_url"
    assert pending["video_ready"] is False

    project_dir = Path(project["project_dir"])
    task = client.app.state.store.task(project["project_id"], run["run_id"])
    stale_result = {
        **task["result"],
        "pending_url_started_at": "2000-01-01T00:00:00+00:00",
        "last_provider_sync_at": "2000-01-01T00:00:00+00:00",
    }
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(conn, run["run_id"], "completed_pending_download", stale_result)

    timed_out = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    assert timed_out["status"] == "failed"
    assert timed_out["download_status"] == "download_failed"
    assert timed_out["error_code"] == "VIDEO_URL_TIMEOUT"
    assert timed_out["error_message"] == "视频生成已完成，但获取视频文件超时"
    assert timed_out["retryable"] is True
    assert provider.downloads == 0

    replacement = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "new run after pending url timeout",
                "reference_asset_ids": [],
            },
        )
    )
    assert replacement["status"] == "queued"

    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(conn, replacement["run_id"], "failed", {"error_code": "test_failure"}, "test")
    retry = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        )
    )
    assert retry["retry_of_run_id"] == run["run_id"]
    assert len(provider.submissions) == 3


def test_expired_pending_url_does_not_block_new_run_without_manual_sync(tmp_path: Path, monkeypatch):
    class Provider:
        def __init__(self):
            self.submissions: list[dict[str, Any]] = []

        def submit_video(self, payload):
            self.submissions.append(payload)
            return {"provider_task_id": f"remote_{len(self.submissions)}", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {"provider_task_id": task_id, "status": "completed", "progress": 100}

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES)

    monkeypatch.setattr("app.video_workflow.MIN_PROVIDER_SYNC_INTERVAL_SEC", 0)
    monkeypatch.setattr("app.video_workflow.PENDING_URL_TIMEOUT_SECONDS", 1)
    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "stale pending url should not block next create",
                "reference_asset_ids": [],
            },
        )
    )
    pending = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    assert pending["status"] == "completed_pending_download"

    project_dir = Path(project["project_dir"])
    stale_result = {
        **client.app.state.store.task(project["project_id"], run["run_id"])["result"],
        "pending_url_started_at": "2000-01-01T00:00:00+00:00",
        "last_provider_sync_at": "2000-01-01T00:00:00+00:00",
    }
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(conn, run["run_id"], "completed_pending_download", stale_result)

    replacement = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "new run after stale pending url",
                "reference_asset_ids": [],
            },
        )
    )

    timed_out = client.app.state.store.task(project["project_id"], run["run_id"])
    assert timed_out["status"] == "failed"
    assert timed_out["result"]["error_code"] == "VIDEO_URL_TIMEOUT"
    assert replacement["status"] == "queued"
    assert len(provider.submissions) == 2


def test_completed_sync_persists_video_download_metadata(tmp_path: Path):
    class Provider:
        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/result.mp4",
            }

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES)

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "metadata required",
                "reference_asset_ids": [],
            },
        )
    )

    synced = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    stored = client.app.state.store.task(project["project_id"], run["run_id"])["result"]

    assert synced["download_bytes"] == len(MP4_BYTES)
    assert synced["download_sha256"] == hashlib.sha256(MP4_BYTES).hexdigest()
    assert stored["download_bytes"] == len(MP4_BYTES)
    assert stored["download_sha256"] == hashlib.sha256(MP4_BYTES).hexdigest()


def test_completed_sync_rejects_oversized_video_download(tmp_path: Path, monkeypatch):
    class Provider:
        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/too-large.mp4",
            }

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES + (b"x" * 8))

    monkeypatch.setattr("app.video_workflow.MAX_VIDEO_DOWNLOAD_BYTES", len(MP4_BYTES))
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "oversized downloaded video",
                "reference_asset_ids": [],
            },
        )
    )

    synced = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    project_dir = Path(client.app.state.store.get_project(project["project_id"])["project_dir"])

    assert synced["status"] == "completed"
    assert synced["download_status"] == "download_failed"
    assert synced["error_code"] == "VIDEO_DOWNLOAD_TOO_LARGE"
    assert not (project_dir / f"video_workflow/runs/{run['run_id']}.mp4").exists()


def test_completed_sync_rejects_non_mp4_download(tmp_path: Path):
    class Provider:
        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/not-video.mp4",
            }

        def download_video(self, url, target):
            Path(target).write_bytes(b"not an mp4 file")

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "invalid downloaded video",
                "reference_asset_ids": [],
            },
        )
    )

    synced = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    project_dir = Path(client.app.state.store.get_project(project["project_id"])["project_dir"])

    assert synced["status"] == "completed"
    assert synced["download_status"] == "download_failed"
    assert synced["error_code"] == "VIDEO_DOWNLOAD_INVALID"
    assert not (project_dir / f"video_workflow/runs/{run['run_id']}.mp4").exists()


def test_provider_raw_and_video_url_are_not_persisted(tmp_path: Path):
    class Provider:
        def submit_video(self, payload):
            return {
                "provider_task_id": "remote_1",
                "status": "queued",
                "progress": 0,
                "video_url": "https://transient.example/submit-ephemeral.mp4",
                "raw": {"debug_payload": "submit-provider-debug-marker"},
            }

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://transient.example/query-ephemeral.mp4",
                "raw": {"debug_payload": "query-provider-debug-marker"},
            }

        def download_video(self, url, target):
            assert url == "https://transient.example/query-ephemeral.mp4"
            Path(target).write_bytes(MP4_BYTES)

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "sanitize provider payload",
                "reference_asset_ids": [],
            },
        )
    )
    synced = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    stored = client.app.state.store.task(project["project_id"], run["run_id"])

    assert synced["video_url_present"] is False
    assert "raw" not in stored["result"]
    assert "video_url" not in stored["result"]
    assert "transient.example" not in json.dumps(stored["result"], ensure_ascii=False)
    assert "provider-debug-marker" not in json.dumps(stored["result"], ensure_ascii=False)


def test_video_workflow_observability_redacts_provider_payloads(tmp_path: Path):
    signed_url = "https://cdn.example/result.mp4?Expires=123&Signature=signed-marker&token=access-marker"

    class Provider:
        def submit_video(self, payload):
            return {
                "provider_task_id": "remote_1",
                "status": "queued",
                "progress": 0,
                "video_url": "https://submit.example/private.mp4?Signature=submit-marker",
                "raw": {"auth_header": "auth submit-marker", "debug": "submit-raw-marker"},
                "response_excerpt": "auth header submit-marker",
            }

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": signed_url,
                "raw": {"debug": "query-raw-marker", "provider_key": "query-marker"},
                "response_excerpt": "download at https://cdn.example/result.mp4?Signature=signed-marker",
            }

        def download_video(self, url, target):
            assert url == signed_url
            Path(target).write_bytes(MP4_BYTES)

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    service = client.app.state.service.video_workflow
    service.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "observable redacted provider run",
                "reference_asset_ids": [],
            },
        )
    )
    unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    snapshot = service.observability_snapshot(project["project_id"])
    serialized = json.dumps(snapshot, ensure_ascii=False)

    assert snapshot["metrics"]["provider_submit_success_count"] == 1
    assert snapshot["metrics"]["provider_query_count"] == 1
    assert snapshot["metrics"]["download_success_count"] == 1
    assert snapshot["metrics"]["downloaded_video_bytes"] == len(MP4_BYTES)
    assert snapshot["metrics"]["queue_time_ms_total"] >= 0
    assert snapshot["metrics"]["generation_time_ms_total"] >= 0
    assert snapshot["metrics"]["download_time_ms_total"] >= 0
    assert snapshot["metrics"]["retry_count"] == 0
    assert snapshot["metrics"]["retry_rate_percent"] == 0
    assert snapshot["metrics"]["duplicate_request_rate_percent"] == 0
    assert snapshot["metrics"]["storage_reference_growth_bytes"] >= 0
    assert snapshot["metrics"]["storage_reference_bytes"] >= 0
    assert {event["event"] for event in snapshot["events"]} >= {
        "provider_submit_succeeded",
        "provider_query_completed",
        "video_download_succeeded",
    }
    assert run["run_id"] in serialized
    assert project["project_id"] in serialized
    assert "trace_" in serialized
    assert "signed-marker" not in serialized
    assert "access-marker" not in serialized
    assert "submit-marker" not in serialized
    assert "query-marker" not in serialized
    assert "auth_header" not in serialized
    assert "raw-marker" not in serialized
    assert "video_url" not in serialized


def test_video_workflow_observability_endpoint_returns_redacted_project_snapshot(tmp_path: Path):
    signed_url = "https://cdn.example/result.mp4?expires_marker=123&signed_marker=endpoint-marker&temporary_marker=endpoint-private"

    class Provider:
        def submit_video(self, payload):
            return {
                "provider_task_id": "remote_endpoint",
                "status": "queued",
                "progress": 0,
                "video_url": "https://submit.example/private.mp4?signed_marker=submit-endpoint-marker",
                "raw": {"upstream_header": "private submit-endpoint-marker", "debug": "submit-endpoint-raw"},
                "response_excerpt": "private header submit-endpoint-marker",
            }

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": signed_url,
                "raw": {"debug": "query-endpoint-raw", "provider_marker": "query-endpoint-marker"},
                "response_excerpt": "download at https://cdn.example/result.mp4?signed_marker=endpoint-marker",
            }

        def download_video(self, url, target):
            assert url == signed_url
            Path(target).write_bytes(MP4_BYTES)

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "observable endpoint redacted provider run",
                "reference_asset_ids": [],
            },
        )
    )
    unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    snapshot = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow/observability"))
    serialized = json.dumps(snapshot, ensure_ascii=False)

    assert snapshot["metrics"]["provider_submit_success_count"] == 1
    assert snapshot["metrics"]["provider_query_count"] == 1
    assert snapshot["metrics"]["download_success_count"] == 1
    assert snapshot["metrics"]["downloaded_video_bytes"] == len(MP4_BYTES)
    assert {event["event"] for event in snapshot["events"]} >= {
        "provider_submit_succeeded",
        "provider_query_completed",
        "video_download_succeeded",
    }
    assert all(event["project_id"] == project["project_id"] for event in snapshot["events"])
    assert run["run_id"] in serialized
    assert "trace_" in serialized
    assert "endpoint-marker" not in serialized
    assert "endpoint-private" not in serialized
    assert "submit-endpoint-marker" not in serialized
    assert "query-endpoint-marker" not in serialized
    assert "upstream_header" not in serialized
    assert "endpoint-raw" not in serialized
    assert "video_url" not in serialized


def test_concurrent_completed_sync_downloads_once(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.downloads = 0
            self.lock = threading.Lock()

        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            time.sleep(0.05)
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/result.mp4",
            }

        def download_video(self, url, target):
            with self.lock:
                self.downloads += 1
            time.sleep(0.05)
            Path(target).write_bytes(MP4_BYTES)

    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "concurrent sync",
                "reference_asset_ids": [],
            },
        )
    )

    results: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def sync_once():
        try:
            results.append(
                client.app.state.service.video_workflow.sync_run(project["project_id"], run["run_id"])
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=sync_once), threading.Thread(target=sync_once)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    assert len(results) == 2
    assert {item["status"] for item in results} == {"completed"}
    assert {item["download_status"] for item in results} == {"downloaded"}
    assert provider.downloads == 1


def test_sync_run_does_not_regress_completed_after_stale_processing_response(tmp_path: Path):
    class Provider:
        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": "remote_1",
                "status": "processing",
                "progress": 40,
            }

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES)

    provider = Provider()
    client = make_client(
        tmp_path,
        {
            "video_provider_mode": "real",
            "VIDEO_WORKFLOW_MIN_SYNC_INTERVAL_SEC": "0",
        },
    )
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "stale provider status",
                "reference_asset_ids": [],
            },
        )
    )
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    task = client.app.state.store.task(project["project_id"], run["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            run["run_id"],
            "completed",
            {
                **task["result"],
                "download_status": "download_failed",
                "download_path": f"video_workflow/runs/{run['run_id']}.mp4",
                "progress": 100,
                "last_provider_sync_at": "2000-01-01T00:00:00+00:00",
            },
        )

    synced = client.app.state.service.video_workflow.sync_run(project["project_id"], run["run_id"])
    stored = client.app.state.service.video_workflow.get_run(project["project_id"], run["run_id"])

    assert synced["status"] == "completed"
    assert stored["status"] == "completed"
    assert stored["download_status"] == "download_failed"
    assert stored["progress"] == 100


def test_sync_run_throttles_repeated_provider_queries(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.queries = 0

        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            self.queries += 1
            return {
                "provider_task_id": task_id,
                "status": "processing",
                "progress": min(99, self.queries * 10),
            }

    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "sync throttle test",
                "reference_asset_ids": [],
            },
        )
    )

    first = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    second = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))

    assert provider.queries == 1
    assert first["progress"] == second["progress"] == 10


def test_provider_status_aliases_are_mapped_to_internal_states(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.responses = [
                {"status": "pending", "progress": 0},
                {"status": "submitted", "progress": 5},
                {"status": "running", "progress": 25},
                {"status": "in_progress", "progress": 50},
                {"status": "succeeded", "progress": 100, "video_url": "https://cdn.example/final.mp4"},
            ]

        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "pending", "progress": 0}

        def query_task(self, task_id):
            return {"provider_task_id": task_id, **self.responses.pop(0)}

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES)

    provider = Provider()
    client = make_client(
        tmp_path,
        {
            "video_provider_mode": "real",
            "VIDEO_WORKFLOW_MIN_SYNC_INTERVAL_SEC": "0",
        },
    )
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "provider status aliases",
                "reference_asset_ids": [],
            },
        )
    )

    project_dir = Path(client.app.state.store.get_project(project["project_id"])["project_dir"])
    states = []
    for _ in range(5):
        synced = client.app.state.service.video_workflow.sync_run(project["project_id"], run["run_id"])
        states.append(synced["status"])
        task = client.app.state.store.task(project["project_id"], run["run_id"])
        with client.app.state.store.connect(project_dir) as conn:
            client.app.state.store.update_task(
                conn,
                run["run_id"],
                task["status"],
                {
                    **task["result"],
                    "last_provider_sync_at": "2000-01-01T00:00:00+00:00",
                },
                task.get("error_message"),
            )

    assert states == ["queued", "queued", "processing", "processing", "completed"]


def test_unknown_provider_status_stays_processing_with_sanitized_excerpt(tmp_path: Path):
    class Provider:
        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "alien_state",
                "progress": 33,
                "response_excerpt": "unexpected alien_state provider payload",
            }

    client = make_client(
        tmp_path,
        {
            "video_provider_mode": "real",
            "VIDEO_WORKFLOW_MIN_SYNC_INTERVAL_SEC": "0",
        },
    )
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "unknown provider status",
                "reference_asset_ids": [],
            },
        )
    )

    synced = client.app.state.service.video_workflow.sync_run(project["project_id"], run["run_id"])
    stored = client.app.state.store.task(project["project_id"], run["run_id"])

    assert synced["status"] == "processing"
    assert synced["progress"] == 33
    assert stored["result"]["provider_status"] == "alien_state"
    assert "alien_state" in stored["result"]["response_excerpt"]


def test_retry_creates_new_run_with_original_snapshot(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    original = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "original",
                "reference_asset_ids": [],
            },
        )
    )
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    task = client.app.state.store.task(project["project_id"], original["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            original["run_id"],
            "failed",
            {
                **task["result"],
                "error_code": "VIDEO_TASK_FAILED",
                "retryable": True,
            },
            "provider failed",
        )

    retried = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{original['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        )
    )

    assert retried["run_id"] != original["run_id"]
    assert retried["retry_of_run_id"] == original["run_id"]
    assert retried["prompt"] == "original"


def test_retry_rejects_active_and_completed_runs(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    active = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "active run",
                "reference_asset_ids": [],
            },
        )
    )
    active_error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{active['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        ),
        409,
        "VIDEO_RETRY_NOT_ALLOWED",
    )
    assert "生成中" in active_error["message"]

    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    task = client.app.state.store.task(project["project_id"], active["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            active["run_id"],
            "completed",
            {
                **task["result"],
                "download_status": "downloaded",
                "download_path": f"video_workflow/runs/{active['run_id']}.mp4",
            },
        )

    completed_error = unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{active['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        ),
        409,
        "VIDEO_RETRY_NOT_ALLOWED",
    )
    assert "已完成" in completed_error["message"]


def test_retry_download_failed_completed_run_does_not_resubmit_provider(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.submitted = 0
            self.queries = 0

        def submit_video(self, payload):
            self.submitted += 1
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            self.queries += 1
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/result.mp4",
            }

        def download_video(self, url, target):
            Path(target).write_bytes(MP4_BYTES)

    provider = Provider()
    client = make_client(
        tmp_path,
        {
            "video_provider_mode": "real",
            "VIDEO_WORKFLOW_MIN_SYNC_INTERVAL_SEC": "0",
        },
    )
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "completed but download failed",
                "reference_asset_ids": [],
            },
        )
    )
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    task = client.app.state.store.task(project["project_id"], run["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            run["run_id"],
            "completed",
            {
                **task["result"],
                "download_status": "download_failed",
                "download_path": f"video_workflow/runs/{run['run_id']}.mp4",
                "last_provider_sync_at": "2000-01-01T00:00:00+00:00",
            },
        )

    retried = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        )
    )

    assert retried["run_id"] == run["run_id"]
    assert retried["status"] == "completed"
    assert retried["download_status"] == "downloaded"
    assert provider.submitted == 1
    assert provider.queries == 1


def test_submission_unknown_retry_requires_duplicate_confirmation(tmp_path: Path):
    class TimeoutProvider:
        def __init__(self):
            self.submitted = 0

        def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.submitted += 1
            if self.submitted == 1:
                raise ProviderError("OCTO_REQUEST_FAILED", "timeout", retryable=True)
            return {"provider_task_id": "remote_retry", "status": "queued", "progress": 0}

    provider = TimeoutProvider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    original = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "uncertain submission",
                "reference_asset_ids": [],
            },
        )
    )
    assert original["status"] == "submission_unknown"

    unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{original['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        ),
        409,
        "VIDEO_DUPLICATE_CONFIRMATION_REQUIRED",
    )

    confirmed = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{original['run_id']}/retry",
            json={
                "client_request_id": str(uuid.uuid4()),
                "confirm_possible_duplicate": True,
            },
        )
    )

    assert confirmed["run_id"] != original["run_id"]
    assert confirmed["retry_of_run_id"] == original["run_id"]
    assert provider.submitted == 2


def test_video_workflow_asset_content_and_delete_are_project_scoped(tmp_path: Path):
    client = make_client(tmp_path)
    first = create_project(client)
    second = create_project(client)
    asset = unwrap_ok(
        client.post(
            f"/projects/{first['project_id']}/video-workflow/assets",
            files=[("files", ("one.png", image_bytes(), "image/png"))],
        )
    )["assets"][0]

    assert client.get(
        f"/projects/{first['project_id']}/video-workflow/assets/{asset['asset_id']}/content"
    ).status_code == 200
    assert client.get(
        f"/projects/{second['project_id']}/video-workflow/assets/{asset['asset_id']}/content"
    ).status_code == 404
    assert client.delete(
        f"/projects/{first['project_id']}/video-workflow/assets/{asset['asset_id']}"
    ).status_code == 200


def test_video_workflow_content_is_inline_mp4(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "stream test",
                "reference_asset_ids": [],
            },
        )
    )
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    relative = f"video_workflow/runs/{run['run_id']}.mp4"
    target = project_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(MP4_BYTES)
    task = client.app.state.store.task(project["project_id"], run["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            run["run_id"],
            "completed",
            {
                **task["result"],
                "download_path": relative,
                "download_status": "downloaded",
            },
        )

    response = client.get(
        f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/content",
        headers={"Range": "bytes=0-7"},
    )

    assert response.status_code in {200, 206}
    assert response.headers["content-type"].startswith("video/mp4")
