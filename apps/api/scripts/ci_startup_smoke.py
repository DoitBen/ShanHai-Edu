from __future__ import annotations

import tempfile
import sys
from pathlib import Path

from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.main import create_app


def _unwrap(response):
    if response.status_code >= 400:
        raise AssertionError(response.text)
    payload = response.json()
    if payload.get("ok") is not True:
        raise AssertionError(payload)
    return payload["data"]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="shanhai-video-workbench-ci-") as tmp:
        root = Path(__file__).resolve().parents[3]
        storage_root = Path(tmp) / "storage"
        app = create_app(
            {
                "storage_root": str(storage_root),
                "workflow_root": str(root / "workflow"),
                "provider_mode": "fake",
                "video_provider_mode": "placeholder",
                "image_provider_mode": "placeholder",
                "tts_provider_mode": "placeholder",
            }
        )
        client = TestClient(app)

        health = _unwrap(client.get("/health"))
        if health.get("status") != "ok":
            raise AssertionError(health)

        readiness = _unwrap(client.get("/readiness"))
        if readiness.get("ok") is not True:
            raise AssertionError(readiness)

        project = _unwrap(
            client.post(
                "/projects",
                json={
                    "name": "CI 视频工作台启动冒烟",
                    "subject": "math",
                    "grade": "3",
                    "textbook_version": "renjiao",
                    "volume": "xia",
                    "lesson_type": "public",
                },
            )
        )
        project_dir = Path(project["project_dir"])
        if not project_dir.is_dir():
            raise AssertionError(f"project dir missing: {project_dir}")
        if not (project_dir / "project.db").is_file():
            raise AssertionError("project db was not created")

        workflow = _unwrap(client.get(f"/projects/{project['project_id']}/video-workflow"))
        if workflow["config"]["model"] != "omni_flash-10s":
            raise AssertionError(workflow["config"])

        print("api startup smoke passed")


if __name__ == "__main__":
    main()
