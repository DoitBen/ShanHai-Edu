from pathlib import Path
from typing import Any
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.main import create_app


def seed_ppt_artifact_upstreams(client: TestClient, project: dict[str, Any]) -> None:
    store = client.app.state.store
    project_id = project["project_id"]
    with store.connect(Path(project["project_dir"])) as conn:
        for node_id in ["ppt_page_script", "ppt_visual_asset"]:
            result = store.write_version(conn, project_id, node_id, {"seeded": node_id}, "fixture", None, "approved")
            store.update_current_version_status(conn, result["version_id"], "approved", approved=True)


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
        }
    )
    return TestClient(app)


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True
    return payload["data"]


def create_project(client: TestClient, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "name": "PPT 导出项目",
        "subject": "math",
        "grade": "1",
        "textbook_version": "renjiao",
        "volume": "shang",
        "lesson_type": "public",
    }
    payload.update(extra or {})
    return unwrap_ok(
        client.post(
            "/projects",
            json=payload,
        )
    )


def test_export_ppt_requires_existing_pptx_artifact_version(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    response = client.post(f"/projects/{project_id}/export/ppt", json={})

    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "PPT_ARTIFACT_NOT_READY"
    assert not (Path(project["project_dir"]) / "exports" / "lesson-video-demo.pptx").exists()


def test_pptx_artifact_generate_creates_pptx_and_compat_export_reads_existing_artifact(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    seed_ppt_artifact_upstreams(client, project)
    artifact = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))
    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))

    pptx_path = Path(project["project_dir"]) / artifact["content"]["pptx_path"]

    assert exported == {
        "filename": artifact["content"]["filename"],
        "path": artifact["content"]["pptx_path"],
        "download_url": artifact["content"]["download_url"],
        "video_path": artifact["content"]["video_path"],
    }
    assert exported["download_url"] == f"/projects/{project_id}/exports/{exported['filename']}"
    assert exported["video_path"] is None
    assert pptx_path.exists()
    with ZipFile(pptx_path) as archive:
        names = set(archive.namelist())
        assert "ppt/slides/slide1.xml" in names
        assert not any(name.startswith("ppt/media/") and name.endswith(".mp4") for name in names)


def test_export_ppt_reuses_existing_final_video_output(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client, {"embed_video_in_ppt": True})
    project_id = project["project_id"]
    video_path = Path(project["project_dir"]) / "outputs" / "final_video.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    existing_video = bytes.fromhex(
        "000000206674797069736f6d0000020069736f6d69736f32617663316d703431"
        "0000000866726565"
        "0000000c6d6461747368616e"
    )
    video_path.write_bytes(existing_video)

    seed_ppt_artifact_upstreams(client, project)
    artifact = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))
    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))

    assert exported["video_path"] == "outputs/final_video.mp4"
    assert video_path.read_bytes() == existing_video
    assert exported["path"] == artifact["content"]["pptx_path"]
    with ZipFile(Path(project["project_dir"]) / artifact["content"]["pptx_path"]) as archive:
        media_names = [name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".mp4")]
        assert len(media_names) == 1
        assert archive.read(media_names[0]) == existing_video
