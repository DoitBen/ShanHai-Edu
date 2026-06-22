import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.state_engine import STATE_VALUES


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


def create_project(client: TestClient, name: str = "StateEngine 契约") -> dict[str, Any]:
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


def upload_textbook(client: TestClient, project_id: str) -> None:
    unwrap_ok(
        client.post(
            f"/projects/{project_id}/textbook",
            files={
                "file": (
                    "textbook.txt",
                    "二年级数学《万以内加法（一次进位）》，学生需要理解为什么要进位。",
                    "text/plain",
                )
            },
        )
    )


def generate_and_approve(client: TestClient, project_id: str, node_id: str) -> dict[str, Any]:
    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
    assert generated["status"] == "needs_review"
    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    assert approved == {"node_id": node_id, "status": "approved"}
    return generated["content"]


def transition_rows(project_dir: str, project_id: str, node_id: str | None = None) -> list[sqlite3.Row]:
    db_path = Path(project_dir) / "project.db"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        params: list[str] = [project_id]
        sql = "SELECT * FROM state_transition_log WHERE project_id = ?"
        if node_id is not None:
            sql += " AND node_id = ?"
            params.append(node_id)
        sql += " ORDER BY triggered_at"
        return conn.execute(sql, params).fetchall()


def test_state_engine_blocks_downstream_until_upstreams_passable_and_logs_transitions(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    blocked = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={})

    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    generate_and_approve(client, project_id, "textbook_parse")
    lesson_plan = unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))

    assert lesson_plan["status"] == "needs_review"
    assert lesson_plan["content"]

    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/approve", json={}))
    assert approved == {"node_id": "lesson_plan", "status": "approved"}

    lesson_plan_node = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))
    assert lesson_plan_node["latest_transition"]["trigger"] == "user_approve"
    assert lesson_plan_node["review_reason"] is None

    rows = transition_rows(project["project_dir"], project_id, "lesson_plan")
    triggers = [row["trigger"] for row in rows]
    assert "ai_generate_done" in triggers
    assert "user_approve" in triggers


def test_state_engine_cascades_approved_downstream_to_needs_review_without_losing_content(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)
    for node_id in ["textbook_parse", "lesson_plan", "ppt_assembly_plan"]:
        generate_and_approve(client, project_id, node_id)

    downstream_before = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_assembly_plan"))
    original_content = downstream_before["content"]
    original_version_id = downstream_before["current_version_id"]
    lesson_plan = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))["content"]
    lesson_plan["state_engine_marker"] = "upstream changed"

    edited = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/lesson_plan/edit",
            json={"content": lesson_plan},
        )
    )

    assert edited["status"] == "needs_review"
    downstream_after = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_assembly_plan"))
    assert downstream_after["status"] == "needs_review"
    assert downstream_after["current_version_id"] == original_version_id
    assert downstream_after["content"] == original_content
    assert downstream_after["review_reason"]["trigger"] == "cascade_invalidate"
    assert downstream_after["latest_transition"]["trigger"] == "cascade_invalidate"
    assert downstream_after["latest_transition"]["version_id_before"] == original_version_id
    assert downstream_after["latest_transition"]["version_id_after"] == original_version_id

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    manifest_nodes = {node["node_id"]: node for node in manifest["nodes"]}
    assert manifest_nodes["ppt_assembly_plan"]["review_reason"]["trigger"] == "cascade_invalidate"

    rows = transition_rows(project["project_dir"], project_id, "ppt_assembly_plan")
    cascade_rows = [row for row in rows if row["trigger"] == "cascade_invalidate"]
    assert len(cascade_rows) == 1
    assert cascade_rows[0]["from_status"] == "approved"
    assert cascade_rows[0]["to_status"] == "needs_review"


def test_cascaded_downstream_cannot_be_approved_until_upstream_is_reapproved(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)
    for node_id in ["textbook_parse", "lesson_plan", "ppt_assembly_plan"]:
        generate_and_approve(client, project_id, node_id)

    lesson_plan = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))["content"]
    lesson_plan["state_engine_marker"] = "requires upstream reapproval"
    unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/lesson_plan/edit",
            json={"content": lesson_plan},
        )
    )

    downstream = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_assembly_plan"))
    assert downstream["status"] == "needs_review"

    blocked = client.post(f"/projects/{project_id}/nodes/ppt_assembly_plan/approve", json={})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    rule_rows = client.app.state.store.rule_results(project_id, "ppt_assembly_plan")
    r010_failures = [row for row in rule_rows if row["rule_id"] == "R010" and row["passed"] == 0]
    assert r010_failures
    assert r010_failures[-1]["details"]["dependencies"] == ["lesson_plan"]

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/approve", json={}))
    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/ppt_assembly_plan/approve", json={}))
    assert approved == {"node_id": "ppt_assembly_plan", "status": "approved"}


def test_store_rejects_non_workflow_business_statuses(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    store = client.app.state.store
    project_id = project["project_id"]
    invalid_status = "fail" + "ed"

    with store.connect(Path(project["project_dir"])) as conn:
        try:
            store.write_version(conn, project_id, "lesson_plan", {"bad": True}, "fixture", "fixture", invalid_status)
        except ValueError as exc:
            assert "Invalid workflow status" in str(exc)
        else:
            raise AssertionError("write_version should reject failed as a business status")

        state = store.node_state(conn, project_id, "lesson_plan")
        assert state["status"] in STATE_VALUES


def test_store_rejects_invalid_node_state_updates(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    store = client.app.state.store
    project_id = project["project_id"]
    invalid_status = "fail" + "ed"

    with store.connect(Path(project["project_dir"])) as conn:
        try:
            store.update_node_state(conn, project_id, "lesson_plan", invalid_status, None)
        except ValueError as exc:
            assert "Invalid workflow status" in str(exc)
        else:
            raise AssertionError("update_node_state should reject failed as a business status")

        state = store.node_state(conn, project_id, "lesson_plan")
        assert state["status"] in STATE_VALUES
