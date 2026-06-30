from pathlib import Path
from typing import Any
import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import enable_project_creation_fallback


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
        }
    )
    return enable_project_creation_fallback(TestClient(app))


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def create_reference_lesson_plan(client: TestClient) -> dict[str, Any]:
    return client.app.state.lesson_plan_library.create_from_markdown(
        "# 直接教案\n\n## 教学目标\n直接从教案推进。",
        source_project_id="uploaded_file",
        source_type="uploaded_file",
        source_filename="direct-lesson.md",
        extract_status="text_extracted",
        created_by="fixture",
    )


def create_project(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "name": "直接教案入口",
        "subject": "math",
        "grade": "2",
        "textbook_version": "renjiao",
        "volume": "shang",
        "lesson_type": "public",
    }
    base.update(payload)
    return unwrap_ok(client.post("/projects", json=base))


def transition_rows(project_dir: str, project_id: str, node_id: str) -> list[sqlite3.Row]:
    db_path = Path(project_dir) / "project.db"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """
            SELECT *
            FROM state_transition_log
            WHERE project_id = ? AND node_id = ?
            ORDER BY triggered_at
            """,
            (project_id, node_id),
        ).fetchall()


def test_direct_lesson_project_can_generate_lesson_plan_without_textbook_parse_approval(tmp_path: Path):
    client = make_client(tmp_path)
    lesson_plan = create_reference_lesson_plan(client)
    project = create_project(client, {"reference_lesson_plan_id": lesson_plan["lesson_plan_id"]})
    project_id = project["project_id"]

    response = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={})

    assert response.status_code < 400, response.text
    generated = response.json()["data"]
    assert generated["node_id"] == "lesson_plan"
    assert generated["status"] == "needs_review"
    rows = transition_rows(project["project_dir"], project_id, "lesson_plan")
    assert [row for row in rows if row["trigger"] == "dependency_gate_blocked"] == []
