import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.providers import FakeProvider


PPT_RUNTIME_NODE_IDS = [
    "visual_contract",
    "character_dict",
    "ppt_assembly_plan",
    "ppt_page_script",
    "ppt_visual_asset",
    "pptx_artifact",
]


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


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "第0周 PPT 主链路",
                "subject": "math",
                "grade": "2",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def transition_rows(project_dir: str, project_id: str, node_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(Path(project_dir) / "project.db") as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM state_transition_log WHERE project_id = ? AND node_id = ? ORDER BY triggered_at, rowid",
            (project_id, node_id),
        ).fetchall()


def event_rows(project_dir: str, project_id: str, node_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(Path(project_dir) / "project.db") as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND node_id = ? ORDER BY created_at, rowid",
            (project_id, node_id),
        ).fetchall()


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
    content = dict(generated["content"])
    content["_phase0_marker"] = node_id
    edited = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/{node_id}/edit",
            json={"content": content},
        )
    )
    assert edited["status"] == "needs_review"
    current = unwrap_ok(client.get(f"/projects/{project_id}/nodes/{node_id}"))
    assert current["content"]["_phase0_marker"] == node_id
    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    assert approved == {"node_id": node_id, "status": "approved"}
    return current["content"]


def test_ppt_runtime_manifest_and_artifact_generation(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    states = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert "final_delivery" not in states
    for node_id in PPT_RUNTIME_NODE_IDS:
        assert states[node_id] == "not_started"

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    ppt_plan = generate_and_approve(client, project_id, "ppt_assembly_plan")
    assert ppt_plan["page_count_target"] >= 6

    blocked = client.post(f"/projects/{project_id}/nodes/ppt_page_script/generate", json={})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    for node_id in ["visual_contract", "character_dict"]:
        generate_and_approve(client, project_id, node_id)

    for node_id in ["ppt_page_script", "ppt_visual_asset"]:
        content = generate_and_approve(client, project_id, node_id)
        assert content

    artifact = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))
    assert artifact["node_id"] == "pptx_artifact"
    assert artifact["status"] == "needs_review"
    content = artifact["content"]
    assert content["pptx_path"].endswith(".pptx")
    assert content["download_url"].startswith(f"/projects/{project_id}/exports/")
    assert content["source_nodes"] == [
        "visual_contract",
        "character_dict",
        "ppt_assembly_plan",
        "ppt_page_script",
        "ppt_visual_asset",
    ]

    pptx_path = Path(project["project_dir"]) / content["pptx_path"]
    assert pptx_path.exists()
    assert content["slide_count"] >= 1
    assert content["notes_count"] >= 1
    assert content["media_count"] >= 1
    assert content["svg_quality_passed"] is True
    assert content["eight_confirmations_status"] == "fast_mode_authorized"

    downloaded = client.get(content["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert downloaded.content == pptx_path.read_bytes()

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/approve", json={}))
    final_manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    final_states = {node["node_id"]: node["status"] for node in final_manifest["nodes"]}
    assert final_states["pptx_artifact"] == "approved"
    assert "final_delivery" not in final_states


def test_manifest_exposes_workflow_contract_capabilities_and_artifacts(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    nodes = {node["node_id"]: node for node in manifest["nodes"]}

    ppt_plan = nodes["ppt_assembly_plan"]
    assert ppt_plan["title"] == "PPT 总装方案"
    assert ppt_plan["step"] == 2
    assert ppt_plan["branch"] == "ppt"
    assert ppt_plan["depends_on"] == ["lesson_plan"]
    assert ppt_plan["schema"] == "schemas/ppt_assembly_plan.schema.json"
    assert ppt_plan["capabilities"] == {
        "can_generate": False,
        "can_edit": True,
        "can_approve": False,
        "can_redo": False,
        "can_skip": False,
    }
    assert ppt_plan["artifact"] is None
    assert ppt_plan["rule_summary"] == {
        "hard_block_count": 0,
        "warning_count": 0,
        "failed_rule_ids": [],
        "warning_rule_ids": [],
    }

    upload_textbook(client, project_id)
    for node_id in ["textbook_parse", "lesson_plan", "visual_contract", "character_dict", "ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset"]:
        generate_and_approve(client, project_id, node_id)
    artifact_result = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))

    artifact_manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    artifact_node = {node["node_id"]: node for node in artifact_manifest["nodes"]}["pptx_artifact"]
    assert artifact_node["capabilities"]["can_edit"] is False
    assert artifact_node["capabilities"]["can_approve"] is True
    assert artifact_node["artifact"] == {
        "download_url": artifact_result["content"]["download_url"],
        "pptx_path": artifact_result["content"]["pptx_path"],
        "video_path": artifact_result["content"]["video_path"],
    }


def test_node_detail_uses_same_workflow_contract_as_manifest(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    manifest_node = {node["node_id"]: node for node in manifest["nodes"]}["ppt_page_script"]
    detail = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_page_script"))

    for key in ["title", "step", "branch", "depends_on", "schema"]:
        assert detail[key] == manifest_node[key]
    assert detail["title"] == "PPT 页面脚本"
    assert detail["step"] == 3
    assert detail["branch"] == "ppt"
    assert detail["depends_on"] == ["ppt_assembly_plan", "character_dict", "visual_contract"]
    assert detail["schema"] == "schemas/ppt_page_script.schema.json"
    assert detail["capabilities"]["can_generate"] is False
    assert detail["capabilities"] == manifest_node["capabilities"]
    assert detail["artifact"] == manifest_node["artifact"]
    assert detail["rule_summary"] == manifest_node["rule_summary"]


def test_create_project_promotes_visual_and_character_inputs_to_runtime_nodes(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "创建即带视觉角色契约",
                "subject": "math",
                "grade": "2",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
                "character_profile": "小山是非写实卡通数学引导员，圆润、克制、适合二年级公开课。",
                "character_safety_rule": "禁真人、photorealistic、real child，不使用真实儿童或真实课堂实拍感。",
                "visual_palette": "暖纸白 #F6F5F1、深青灰 #2D4356、古铜金 #9C7C4E",
                "visual_style_keywords": "温润、克制、真实生活情境、可编辑 PPT 视觉资产",
                "font_preference": "系统无衬线中文优先，数学内容必须可编辑",
                "compliance_notes": "所有儿童角色必须为非写实卡通或剪影风格。",
            },
        )
    )
    project_id = project["project_id"]

    visual = unwrap_ok(client.get(f"/projects/{project_id}/nodes/visual_contract"))
    character = unwrap_ok(client.get(f"/projects/{project_id}/nodes/character_dict"))

    assert visual["status"] == "approved"
    assert visual["content"]["palette"] == ["#F6F5F1", "#2D4356", "#9C7C4E"]
    assert visual["content"]["style_keywords"] == ["温润", "克制", "真实生活情境", "可编辑 PPT 视觉资产"]
    assert visual["content"]["font_preference"] == "系统无衬线中文优先，数学内容必须可编辑"
    assert visual["content"]["source_input"]["compliance_notes"] == "所有儿童角色必须为非写实卡通或剪影风格。"
    assert visual["latest_transition"]["trigger"] == "user_create_project"

    assert character["status"] == "approved"
    assert character["content"]["characters"][0]["character_id"] == "char_user_guide"
    assert character["content"]["characters"][0]["identity"] == "小山是非写实卡通数学引导员，圆润、克制、适合二年级公开课。"
    assert character["content"]["characters"][0]["banned_keywords"] == ["真人", "photorealistic", "real child"]
    assert character["content"]["source_input"]["character_safety_rule"].startswith("禁真人")
    assert character["latest_transition"]["trigger"] == "user_create_project"

    for node_id in ["visual_contract", "character_dict"]:
        versions = unwrap_ok(client.get(f"/projects/{project_id}/nodes/{node_id}/versions"))
        assert len(versions) == 1
        assert versions[0]["status"] == "approved"
        assert versions[0]["generated_by"] == "user_create_project"
        assert versions[0]["approved_at"] is not None
        transitions = transition_rows(project["project_dir"], project_id, node_id)
        assert [row["trigger"] for row in transitions] == ["user_create_project"]
        events = event_rows(project["project_dir"], project_id, node_id)
        assert "runtime_node_seeded" in [row["event_type"] for row in events]
        seeded_events = [row for row in events if row["event_type"] == "runtime_node_seeded"]
        assert json.loads(seeded_events[-1]["payload_json"])["generated_by"] == "user_create_project"


def test_create_project_seeded_visual_and_character_content_is_used_by_downstream_context(tmp_path: Path):
    class CaptureProvider(FakeProvider):
        def __init__(self):
            super().__init__()
            self.name = "capture"
            self.context_by_node: dict[str, dict[str, Any]] = {}

        def generate(self, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
            self.context_by_node[node_id] = context
            if node_id == "ppt_assembly_plan":
                return {
                    "page_count_target": 6,
                    "theme": "创建上下文消费测试",
                    "persistent_context": "使用用户创建项目时填写的视觉和角色契约。",
                    "page_outline": ["导入", "观察", "探究", "练习", "总结", "拓展"],
                    "action_chain": ["look", "count", "compare", "speak", "correct"],
                    "inquiry_path": "从生活情境到可编辑数学表达。",
                    "ppt_video_division": "PPT 负责课堂探究。",
                    "material_requirements": ["可编辑数学图形"],
                    "editable_text_rules": "数学内容必须可编辑。",
                    "accuracy_warnings": ["检查可见层"],
                }
            if node_id == "ppt_page_script":
                return {
                    "pages": [
                        {
                            "page_index": 1,
                            "core_competency": ["number_sense"],
                            "page_objective": "观察进位情境",
                            "student_action": "look",
                            "page_type": "life_observation",
                            "main_visual": {
                                "description": "校园义卖图书合并统计。",
                                "serves_purpose": "引出一次进位。",
                            },
                            "character_refs": ["char_user_guide"],
                            "image_prompts": [],
                            "math_assertions": [
                                {"content": "286 + 147 = 433", "answer": "433", "editable_layer": "ppt_text"}
                            ],
                            "zone_layout": {"task_zone": "左", "math_zone": "右", "conclusion_zone": "下"},
                            "evidence_requirement": "学生解释个位满十。",
                            "accuracy_notes": "检查进位位置。",
                            "link_to_prev_page": "承接生活情境。",
                            "density_limits": {"body_text_max": 18, "info_chunks_max": 3},
                        }
                    ]
                }
            return super().generate(node_id, context)

    provider = CaptureProvider()
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
    app.state.service.provider = provider
    client = TestClient(app)
    project = unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "下游读取创建输入",
                "subject": "math",
                "grade": "2",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
                "character_profile": "小山是用户创建时填写的数学引导员。",
                "character_safety_rule": "禁真人、photorealistic、real child。",
                "visual_palette": "#112233 #445566 #778899",
                "visual_style_keywords": "温润、可编辑、生活化",
                "font_preference": "Source Han Sans",
                "compliance_notes": "不使用真实儿童照片。",
            },
        )
    )
    project_id = project["project_id"]
    upload_textbook(client, project_id)
    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/ppt_assembly_plan/generate", json={}))
    unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/ppt_assembly_plan/approve",
            json={
                "override_warning_rule_ids": ["R023", "R024"],
                "override_reason": "contract test focuses on downstream context consumption",
            },
        )
    )

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/ppt_page_script/generate", json={}))

    context = provider.context_by_node["ppt_page_script"]
    assert context["visual_contract"]["palette"] == ["#112233", "#445566", "#778899"]
    assert context["visual_contract"]["font_preference"] == "Source Han Sans"
    assert context["character_dict"]["characters"][0]["identity"] == "小山是用户创建时填写的数学引导员。"
