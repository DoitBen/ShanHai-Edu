from pathlib import Path
from typing import Any
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
        }
    )
    return TestClient(app)


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True
    return payload["data"]


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "PPT 导出项目",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def test_export_ppt_creates_pptx_with_placeholder_video(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))

    pptx_path = Path(project["project_dir"]) / exported["path"]
    video_path = Path(project["project_dir"]) / "outputs" / "final_video.mp4"

    assert exported["filename"].endswith(".pptx")
    assert exported["download_url"] == f"/projects/{project_id}/exports/{exported['filename']}"
    assert pptx_path.exists()
    assert video_path.exists()
    with ZipFile(pptx_path) as archive:
        names = set(archive.namelist())
        assert "ppt/slides/slide1.xml" in names
        assert "ppt/slides/slide2.xml" in names
        assert any(name.startswith("ppt/media/") and name.endswith(".mp4") for name in names)


def test_export_ppt_reuses_existing_final_video_output(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    video_path = Path(project["project_dir"]) / "outputs" / "final_video.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    existing_video = bytes.fromhex(
        "000000206674797069736f6d0000020069736f6d69736f32617663316d703431"
        "0000000866726565"
        "0000000c6d6461747368616e"
    )
    video_path.write_bytes(existing_video)

    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))

    assert exported["video_path"] == "outputs/final_video.mp4"
    assert video_path.read_bytes() == existing_video
    with ZipFile(Path(project["project_dir"]) / exported["path"]) as archive:
        media_names = [name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".mp4")]
        assert len(media_names) == 1
        assert archive.read(media_names[0]) == existing_video
