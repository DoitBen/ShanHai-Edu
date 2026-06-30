import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import enable_project_creation_fallback
from app.store import ProjectStore
from app.workflow_config import WorkflowConfig


ROOT = Path(__file__).resolve().parents[3]


def make_client(tmp_path: Path, token: str | None = "admin-token") -> TestClient:
    overrides = {
        "storage_root": str(tmp_path / "storage"),
        "workflow_root": str(ROOT / "workflow"),
        "provider_mode": "fake",
        "video_provider_mode": "placeholder",
        "image_provider_mode": "placeholder",
        "tts_provider_mode": "placeholder",
    }
    if token is not None:
        overrides["backend_api_token"] = token
    return enable_project_creation_fallback(TestClient(create_app(overrides)))


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def unwrap_ok(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def unwrap_error(response, status_code: int, code: str) -> dict[str, Any]:
    assert response.status_code == status_code, response.text
    payload = response.json()
    assert payload["ok"] is False, payload
    assert payload["error"]["code"] == code, payload
    return payload["error"]


def create_project(client: TestClient, name: str) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            headers=auth("admin-token"),
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


def admin_get(client: TestClient, path: str):
    return client.get(path, headers=auth("admin-token"))


def admin_post(client: TestClient, path: str, payload: dict[str, Any]):
    return client.post(path, json=payload, headers=auth("admin-token"))


def seed_approved_upstreams(client: TestClient, project: dict[str, Any], node_id: str) -> None:
    dependencies = {
        "ppt_assembly_plan": ["lesson_plan"],
    }
    store = client.app.state.store
    with store.connect(Path(project["project_dir"])) as conn:
        for dep_id in dependencies.get(node_id, []):
            state = store.node_state(conn, project["project_id"], dep_id)
            if state["status"] == "approved":
                continue
            result = store.write_version(conn, project["project_id"], dep_id, {"seeded": dep_id}, "fixture", "fixture", "approved")
            store.update_current_version_status(conn, result["version_id"], "approved", approved=True)


def write_current_version(client: TestClient, project: dict[str, Any], node_id: str, content: dict[str, Any]) -> None:
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        client.app.state.store.write_version(conn, project["project_id"], node_id, content, "fixture", "fixture", "needs_review")


def approve_ppt_assembly(client: TestClient, project: dict[str, Any]) -> Any:
    return client.post(f"/projects/{project['project_id']}/nodes/ppt_assembly_plan/approve", json={}, headers=auth("admin-token"))


def rule_result_messages(project: dict[str, Any], rule_id: str) -> list[str]:
    with sqlite3.connect(Path(project["project_dir"]) / "project.db") as conn:
        rows = conn.execute("SELECT message FROM rule_result_log WHERE rule_id=? ORDER BY rowid", (rule_id,)).fetchall()
    return [row[0] for row in rows]


def test_control_plane_seeds_rule_templates_and_active_versions(tmp_path: Path):
    client = make_client(tmp_path)

    rules = unwrap_ok(admin_get(client, "/admin/rules"))

    by_id = {rule["rule_id"]: rule for rule in rules}
    assert by_id["R023"]["active_version"]["status"] == "active"
    assert by_id["R030"]["active_version"]["check_json"]["type"] == "field_compare"
    assert by_id["R026"]["active_version"]["check_json"]["type"] == "pptx_visible_text_not_contains"
    assert by_id["R004"]["active_version"]["check_json"]["type"] == "list_each"

    with sqlite3.connect(tmp_path / "storage" / "control_plane.db") as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        channel = conn.execute(
            "SELECT channel_name, rule_set_version_id FROM rule_release_channels WHERE channel_name='default'"
        ).fetchone()
    assert "rule_release_channels" in tables
    assert channel is not None
    assert channel[1]


def test_new_projects_bind_current_active_rule_set_and_old_projects_do_not_migrate(tmp_path: Path):
    client = make_client(tmp_path)
    old_project = create_project(client, "旧规则项目")
    seed_approved_upstreams(client, old_project, "ppt_assembly_plan")
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
    write_current_version(client, old_project, "ppt_assembly_plan", warning_content)

    created = unwrap_ok(
        admin_post(
            client,
            "/admin/rules/R023/versions",
            {
                "severity": "hard_block",
                "action_message": "新规则要求板书小结页必须存在",
                "check_json": {
                    "type": "field_compare",
                    "field": "page_type_quota.blackboard_summary",
                    "op": ">=",
                    "value": 1,
                },
                "created_by": "architect",
                "notes": "promote R023 to hard block for new projects",
            },
        )
    )
    unwrap_ok(admin_post(client, "/admin/rules/R023/activate", {"version_id": created["version_id"], "actor": "architect"}))

    new_project = create_project(client, "新规则项目")
    seed_approved_upstreams(client, new_project, "ppt_assembly_plan")
    write_current_version(client, new_project, "ppt_assembly_plan", warning_content)

    old_response = approve_ppt_assembly(client, old_project)
    old_error = unwrap_error(old_response, 409, "RULE_WARNING")
    assert old_error["details"]["warnings"][0]["severity"] == "warning"
    assert "PPT 总装方案必须至少包含 1 页板书小结" in rule_result_messages(old_project, "R023")

    new_response = approve_ppt_assembly(client, new_project)
    new_error = unwrap_error(new_response, 409, "RULE_VIOLATION_R023")
    assert new_error["details"]["severity"] == "hard_block"
    assert "新规则要求板书小结页必须存在" in rule_result_messages(new_project, "R023")


def test_startup_binds_existing_unbound_projects_before_rule_changes(tmp_path: Path):
    workflow = WorkflowConfig(ROOT / "workflow")
    legacy_store = ProjectStore(tmp_path / "storage")
    legacy_project = legacy_store.create_project(
        {
            "name": "控制面前旧项目",
            "subject": "math",
            "grade": "2",
            "textbook_version": "renjiao",
            "volume": "shang",
            "lesson_type": "public",
        },
        workflow,
        owner_id="user_test_owner",
    )

    client = make_client(tmp_path)
    seed_approved_upstreams(client, legacy_project, "ppt_assembly_plan")
    write_current_version(
        client,
        legacy_project,
        "ppt_assembly_plan",
        {
            "page_count_target": 6,
            "page_type_quota": {
                "life_observation": 1,
                "role_task": 1,
                "inquiry_operation": 1,
                "step_reveal": 1,
                "practice_challenge": 1,
                "blackboard_summary": 0,
            },
        },
    )
    created = unwrap_ok(
        admin_post(
            client,
            "/admin/rules/R023/versions",
            {
                "severity": "hard_block",
                "action_message": "新规则发布后不得影响控制面前旧项目",
                "check_json": {
                    "type": "field_compare",
                    "field": "page_type_quota.blackboard_summary",
                    "op": ">=",
                    "value": 1,
                },
                "created_by": "architect",
            },
        )
    )
    unwrap_ok(admin_post(client, "/admin/rules/R023/activate", {"version_id": created["version_id"], "actor": "architect"}))

    response = approve_ppt_assembly(client, legacy_project)

    legacy_error = unwrap_error(response, 409, "RULE_WARNING")
    assert legacy_error["details"]["warnings"][0]["severity"] == "warning"
    assert "PPT 总装方案必须至少包含 1 页板书小结" in rule_result_messages(legacy_project, "R023")


def test_admin_rule_api_requires_configured_admin_token(tmp_path: Path):
    client = make_client(tmp_path, token="fake")

    no_token = client.get("/admin/rules")
    wrong_token = client.get("/admin/rules", headers=auth("bad-token"))
    ok = client.get("/admin/rules", headers=auth("fake"))

    unwrap_error(no_token, 404, "NOT_FOUND")
    unwrap_error(wrong_token, 404, "NOT_FOUND")
    assert ok.status_code == 200
    assert ok.json()["ok"] is True


def test_admin_rule_rollback_creates_audit_log_and_restores_previous_behavior(tmp_path: Path):
    client = make_client(tmp_path)
    original = unwrap_ok(admin_get(client, "/admin/rules/R023"))["active_version"]
    created = unwrap_ok(
        admin_post(
            client,
            "/admin/rules/R023/versions",
            {
                "severity": "hard_block",
                "action_message": "临时硬阻断",
                "check_json": {
                    "type": "field_compare",
                    "field": "page_type_quota.blackboard_summary",
                    "op": ">=",
                    "value": 1,
                },
                "created_by": "architect",
            },
        )
    )
    unwrap_ok(admin_post(client, "/admin/rules/R023/activate", {"version_id": created["version_id"], "actor": "architect"}))

    rolled_back = unwrap_ok(
        admin_post(
            client,
            "/admin/rules/R023/rollback",
            {"version_id": original["version_id"], "actor": "architect", "notes": "restore warning behavior"},
        )
    )
    audit = unwrap_ok(admin_get(client, "/admin/rules/audit"))
    project = create_project(client, "回滚后新项目")
    seed_approved_upstreams(client, project, "ppt_assembly_plan")
    write_current_version(
        client,
        project,
        "ppt_assembly_plan",
        {"page_count_target": 6, "page_type_quota": {"life_observation": 1, "blackboard_summary": 0}},
    )

    response = approve_ppt_assembly(client, project)

    assert rolled_back["active_version"]["version_id"] == original["version_id"]
    assert any(item["action"] == "rollback_active" and item["rule_id"] == "R023" for item in audit)
    unwrap_error(response, 409, "RULE_WARNING")


def test_admin_workflow_graph_is_read_only_and_contains_rule_bindings(tmp_path: Path):
    client = make_client(tmp_path)

    graph = unwrap_ok(admin_get(client, "/admin/workflow/graph"))

    lesson = next(node for node in graph["nodes"] if node["id"] == "lesson_plan")
    ppt_assembly = next(node for node in graph["nodes"] if node["id"] == "ppt_assembly_plan")
    assert lesson["depends_on"] == ["textbook_parse"]
    assert any(rule["rule_id"] == "R023" for rule in ppt_assembly["rules"])
    assert graph["editable"] is False
    assert graph["edit_scope"] == "rules_and_prompts_only"


def test_rule_executor_source_no_longer_hardcodes_implemented_rule_ids():
    source = (ROOT / "apps" / "api" / "app" / "rule_executor.py").read_text(encoding="utf-8")

    assert "IMPLEMENTED_RULE_IDS" not in source
    assert "\"R001\": self._check_r001" not in source
    assert "if rule_id ==" not in source
