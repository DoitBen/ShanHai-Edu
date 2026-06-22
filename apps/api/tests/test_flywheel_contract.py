import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app


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
    return TestClient(app)


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def create_project(client: TestClient, name: str = "Flywheel 契约") -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": name,
                "subject": "math",
                "grade": "2",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def write_current_version(
    client: TestClient,
    project: dict[str, Any],
    node_id: str,
    content: dict[str, Any],
    status: str = "needs_review",
) -> dict[str, Any]:
    project_id = project["project_id"]
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        return client.app.state.store.write_version(conn, project_id, node_id, content, "fixture", "fixture", status)


def table_rows(project: dict[str, Any], table: str) -> list[dict[str, Any]]:
    with sqlite3.connect(Path(project["project_dir"]) / "project.db") as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]


def test_approve_records_approved_sample_and_debug_endpoint_returns_events(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    version = write_current_version(
        client,
        project,
        "lesson_plan",
        {"lesson_plan_markdown": "## 教学目标\n理解一次进位。", "teaching_objectives": "理解一次进位"},
    )

    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/approve", json={}))

    assert approved == {"node_id": "lesson_plan", "status": "approved"}
    rows = table_rows(project, "approved_samples")
    assert len(rows) == 1
    assert rows[0]["project_id"] == project_id
    assert rows[0]["node_id"] == "lesson_plan"
    assert rows[0]["version_id"] == version["version_id"]
    assert "一次进位" in rows[0]["content_excerpt"]
    assert json.loads(rows[0]["content_json"])["teaching_objectives"] == "理解一次进位"

    flywheel = unwrap_ok(client.get(f"/projects/{project_id}/flywheel"))
    assert [sample["sample_id"] for sample in flywheel["approved_samples"]] == [rows[0]["sample_id"]]
    assert flywheel["post_approve_edits"] == []
    assert flywheel["rule_override_events"] == []
    assert flywheel["feedback_log"] == []


def test_edit_after_approved_records_post_approve_edit(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    first = write_current_version(
        client,
        project,
        "textbook_parse",
        {"lesson_title": "旧版解析", "teaching_goal_summary": "旧目标"},
    )
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    edited = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/textbook_parse/edit",
            json={"content": {"lesson_title": "新版解析", "teaching_goal_summary": "新目标"}},
        )
    )

    rows = table_rows(project, "post_approve_edits")
    assert len(rows) == 1
    assert rows[0]["project_id"] == project_id
    assert rows[0]["node_id"] == "textbook_parse"
    assert rows[0]["before_version_id"] == first["version_id"]
    assert rows[0]["after_version_id"] == edited["version_id"]
    diff = json.loads(rows[0]["diff_json"])
    assert diff["changed_fields"] == ["lesson_title", "teaching_goal_summary"]
    assert diff["before_excerpt"] == "旧版解析 旧目标"
    assert diff["after_excerpt"] == "新版解析 新目标"


def test_warning_override_records_rule_override_event(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    warning_content = {
        "page_count_target": 6,
        "page_type_quota": {
            "life_observation": 1,
            "role_task": 1,
            "inquiry_operation": 1,
            "step_reveal": 1,
            "practice_challenge": 1,
            "blackboard_summary": 0,
        },
    }
    write_current_version(client, project, "ppt_assembly_plan", warning_content)

    warning = client.post(f"/projects/{project_id}/nodes/ppt_assembly_plan/approve", json={})
    assert warning.status_code == 409
    approved = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/ppt_assembly_plan/approve",
            json={"override_warning_rule_ids": ["R023"], "override_reason": "内测保留 6 页"},
        )
    )

    assert approved == {"node_id": "ppt_assembly_plan", "status": "approved"}
    rows = table_rows(project, "rule_override_events")
    assert len(rows) == 1
    assert rows[0]["project_id"] == project_id
    assert rows[0]["node_id"] == "ppt_assembly_plan"
    assert rows[0]["rule_id"] == "R023"
    assert rows[0]["reason"] == "内测保留 6 页"


def test_feedback_api_records_feedback_log(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    feedback = unwrap_ok(
        client.post(
            f"/projects/{project_id}/feedback",
            json={
                "feedback_type": "delivery",
                "payload": {
                    "rating": 4,
                    "comment": "课件可以直接试用，但导入动画还想更短。",
                    "next_session_hint": "下次优先减少动画时长",
                },
            },
        )
    )

    rows = table_rows(project, "feedback_log")
    assert len(rows) == 1
    assert rows[0]["feedback_id"] == feedback["feedback_id"]
    assert rows[0]["feedback_type"] == "delivery"
    payload = json.loads(rows[0]["payload_json"])
    assert payload["rating"] == 4
    assert "动画" in payload["comment"]

    flywheel = unwrap_ok(client.get(f"/projects/{project_id}/flywheel"))
    assert flywheel["feedback_log"][0]["payload"]["next_session_hint"] == "下次优先减少动画时长"


def test_feedback_api_rejects_unknown_feedback_type(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)

    response = client.post(
        f"/projects/{project['project_id']}/feedback",
        json={"feedback_type": "random", "payload": {"comment": "bad"}},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "FEEDBACK_TYPE_INVALID"
