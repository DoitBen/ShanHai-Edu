import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.main import create_app


ROOT = Path(__file__).resolve().parents[3]


class StubDeepSeekProvider:
    name = "deepseek"

    def __init__(self, api_key: str | None, base_url: str, model: str):
        assert api_key == "test-deepseek-key"
        assert base_url == "https://api.deepseek.com"
        assert model == "deepseek-chat"

    def complete_json(self, **kwargs: Any) -> dict[str, Any]:
        node_id = kwargs["node_id"]
        if node_id == "textbook_parse":
            return {
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_title": "5以内数的认识",
                "core_knowledge_points": ["1-5数量意义", "数物对应"],
                "teaching_goal_summary": "认识 1-5 的数量意义。",
                "key_points": ["数物对应"],
                "difficulties": ["数量抽象"],
            }
        if node_id == "lesson_plan":
            return {
                "lesson_plan_markdown": (
                    "# 教案：5以内数的认识\n\n"
                    "## 基本信息\n- 年级：一年级\n\n"
                    "## 教学目标\n认识 1-5 的数量意义。\n\n"
                    "## 教学环节\n从生活物品数数导入。"
                ),
                "intro_designs": [
                    {
                        "design_id": "design_application_01",
                        "type": "application",
                        "title": "生活物品数一数",
                        "hook": "用苹果和铅笔引出 1-5。",
                        "anchor_to_lesson": "贴合 5 以内数的认识。",
                        "recommend_score": 5,
                        "risk_note": "保持非写实卡通。",
                    },
                    {
                        "design_id": "design_story_01",
                        "type": "story",
                        "title": "数字寻宝",
                        "hook": "寻找数字卡。",
                        "anchor_to_lesson": "串联 1-5 的数量意义。",
                        "recommend_score": 4,
                        "risk_note": "不出现真人儿童。",
                    },
                    {
                        "design_id": "design_science_01",
                        "type": "science",
                        "title": "自然里的数字",
                        "hook": "观察花瓣数量。",
                        "anchor_to_lesson": "从观察到抽象。",
                        "recommend_score": 4,
                        "risk_note": "避免复杂科学解释。",
                    },
                ],
            }
        if node_id == "visual_contract":
            return {
                "palette": ["#0F766E", "#F59E0B", "#F8FAFC"],
                "style_keywords": ["非写实卡通", "生活化数学情境"],
                "font_preference": "Microsoft YaHei",
            }
        if node_id == "character_dict":
            return {
                "characters": [
                    {
                        "character_id": "char_math_guide",
                        "name": "小山",
                        "identity": "非写实卡通数学引导员",
                        "view_front": "卡通正面形象",
                        "view_side": "卡通侧面形象",
                        "view_back": "卡通背面形象",
                        "outfit_lock": {"color": "teal", "style": "cartoon"},
                        "hair_lock": "简化发型",
                        "body_proportion": "3d_non_realistic_childlike_chibi",
                        "style_constraint": "3d_non_realistic",
                        "banned_keywords": ["真人", "photorealistic", "real child"],
                    }
                ]
            }
        if node_id == "ppt_assembly_plan":
            return {
                "persistent_context": "围绕 5 以内数的认识，保持生活化情境和可编辑数学文本。",
                "page_count_target": 6,
                "page_type_quota": {
                    "life_observation": 1,
                    "role_task": 1,
                    "inquiry_operation": 1,
                    "step_reveal": 1,
                    "practice_challenge": 1,
                    "blackboard_summary": 1,
                },
                "action_chain": ["look", "count", "match", "speak"],
                "inquiry_path": "先观察真实物品数量，再建立数字和数量对应，最后用板书总结。",
                "ppt_video_division": "PPT 负责课堂探究和可编辑数学表达，导入视频负责吸引注意力。",
                "material_requirements": ["卡通苹果和铅笔数量图", "数字卡片", "可编辑板书文本"],
                "editable_text_rules": "数字、算式和结论必须使用 PPT 文本或形状层。",
                "accuracy_warnings": [],
            }
        if node_id == "ppt_page_script":
            return {
                "pages": [
                    {
                        "page_index": 1,
                        "core_competency": ["number_sense"],
                        "page_objective": "观察物品数量并提出数数任务",
                        "student_action": "look",
                        "page_type": "life_observation",
                        "main_visual": {
                            "description": "卡通桌面上摆放 1 到 5 个不同物品。",
                            "serves_purpose": "帮助学生观察数量并开始数数。",
                        },
                        "character_refs": ["char_math_guide"],
                        "image_prompts": [
                            {
                                "prompt_id": "ppt_prompt_01",
                                "description": "非写实卡通桌面，苹果、铅笔和星星数量清晰。",
                                "knowledge_link": "5 以内数的认识",
                                "real_life_scene": True,
                                "character_refs": ["char_math_guide"],
                                "aspect_ratio": "16:9",
                            }
                        ],
                        "math_assertions": [{"content": "1、2、3、4、5 表示不同数量", "answer": "1-5", "editable_layer": "ppt_text"}],
                        "zone_layout": {"task_zone": "左侧物品图", "math_zone": "右侧数字卡", "conclusion_zone": "底部说一说"},
                        "evidence_requirement": "学生能把物品个数和数字卡对应起来。",
                        "accuracy_notes": "数字和数量必须一一对应。",
                        "link_to_prev_page": "承接导入视频中的数数悬念。",
                        "density_limits": {"body_text_max": 18, "info_chunks_max": 3},
                    },
                    {
                        "page_index": 2,
                        "core_competency": ["number_sense"],
                        "page_objective": "总结 1 到 5 的数量意义",
                        "student_action": "speak",
                        "page_type": "blackboard_summary",
                        "main_visual": {
                            "description": "板书式数字与点子图对应表。",
                            "serves_purpose": "形成可复述的数量对应结论。",
                        },
                        "character_refs": ["char_math_guide"],
                        "image_prompts": [],
                        "math_assertions": [{"content": "数到几，就用数字几表示", "answer": "数量对应", "editable_layer": "ppt_shape"}],
                        "zone_layout": {"task_zone": "顶部回顾", "math_zone": "中间对应表", "conclusion_zone": "底部板书"},
                        "evidence_requirement": "学生能用自己的话说出数字表示数量。",
                        "accuracy_notes": "保持学生可见层简洁。",
                        "link_to_prev_page": "从观察进入总结。",
                        "density_limits": {"body_text_max": 16, "info_chunks_max": 3},
                    },
                ]
            }
        if node_id == "ppt_visual_asset":
            return {
                "assets": [
                    {
                        "asset_id": "ppt_asset_01",
                        "source_prompt_id": "ppt_prompt_01",
                        "storage_path": "08A_PPT视觉资产/ppt_asset_01.png",
                        "status": "approved",
                    }
                ]
            }
        if node_id == "intro_selection":
            return {
                "selection_mode": "single_best",
                "selected_design_ids": ["design_application_01"],
                "primary_design_id": "design_application_01",
                "downstream_generation_mode": "three_variants_for_primary",
                "selection_reason": "生活物品数数最贴近一年级学生经验。",
            }
        if node_id == "intro_video_script":
            return {
                "total_duration_sec": 60,
                "video_type": "application",
                "anchor_to_lesson": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                "narration_full_text": "桌面上出现一个苹果、两支铅笔、三块积木、四朵小花和五颗星星。我们一起数一数，认识 1 到 5。",
                "narration_word_count": 48,
                "banned_elements": ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"],
            }
        if node_id == "intro_video_screenplay":
            return {
                "scenes": [
                    {
                        "scene_id": "scene_01",
                        "duration_sec": 20,
                        "scene_description": "卡通桌面依次出现 1-5 个物品。",
                        "character_refs": [],
                        "narration_segment": "桌面上出现一个苹果、两支铅笔。",
                    },
                    {
                        "scene_id": "scene_02",
                        "duration_sec": 20,
                        "scene_description": "物品和数字卡片逐一对应。",
                        "character_refs": [],
                        "narration_segment": "我们一起数一数，认识 1 到 5。",
                    },
                    {
                        "scene_id": "scene_03",
                        "duration_sec": 20,
                        "scene_description": "五颗星星变成数字 5。",
                        "character_refs": [],
                        "narration_segment": "数量可以用数字清楚表示。",
                    },
                ]
            }
        if node_id == "intro_video_asset":
            return {
                "assets": [
                    {
                        "asset_id": f"asset_ref_{index:02d}",
                        "source_prompt_id": f"shot_{index:02d}",
                        "storage_path": f"08B_导入视频资产/ref_{index:02d}.png",
                        "status": "approved",
                    }
                    for index in range(1, 7)
                ]
            }
        if node_id == "storyboard":
            return {
                "shots": [
                    {
                        "shot_id": f"shot_{index:02d}",
                        "duration_sec": 10,
                        "main_subject": "卡通桌面数数",
                        "character_refs": [],
                        "reference_image_ids": [f"asset_ref_{index:02d}"],
                        "narration_slice": f"认识数字 {index}",
                        "subtitle": f"认识数字 {index}",
                        "model_prompt": f"中文旁白：认识数字 {index}。禁止英文配音。",
                        "first_frame_test_status": "passed",
                        "first_frame_asset_id": f"asset_ref_{index:02d}",
                    }
                    for index in range(1, 7)
                ]
            }
        raise AssertionError(f"unexpected node {node_id}")


def make_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setattr("app.main.DeepSeekTextProvider", StubDeepSeekProvider)
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(ROOT / "workflow"),
            "provider_mode": "real",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "deepseek_api_key": "test-deepseek-key",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat",
            "octo_api_key": "must-not-be-used",
        }
    )
    return TestClient(app)


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


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "Fullchain E2E 契约测试",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def upload_textbook_input(client: TestClient, project_id: str) -> None:
    unwrap_ok(
        client.post(
            f"/projects/{project_id}/textbook",
            files={
                "file": (
                    "textbook.txt",
                    "一年级数学，5以内数的认识。学生通过数苹果、铅笔和星星建立 1-5 的数量意义。",
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
    return unwrap_ok(client.get(f"/projects/{project_id}/nodes/{node_id}"))


def seed_ppt_artifact_upstreams(client: TestClient, project: dict[str, Any]) -> None:
    store = client.app.state.store
    project_id = project["project_id"]
    with store.connect(Path(project["project_dir"])) as conn:
        for node_id in ["ppt_page_script", "ppt_visual_asset"]:
            result = store.write_version(conn, project_id, node_id, {"seeded": node_id}, "fixture", "fixture", "approved")
            store.update_current_version_status(conn, result["version_id"], "approved", approved=True)


def test_real_text_placeholder_video_fullchain_exports_ppt_with_mp4(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.app.state.settings.provider_mode == "real"
    assert client.app.state.settings.video_provider_mode == "placeholder"
    assert client.app.state.service.provider.name == "deepseek"
    assert client.app.state.service.video_provider is None

    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook_input(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan", "visual_contract", "character_dict"]:
        node = generate_and_approve(client, project_id, node_id)
        assert node["status"] == "approved"

    for node_id in ["ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset"]:
        node = generate_and_approve(client, project_id, node_id)
        assert node["status"] == "approved"

    artifact = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))
    assert artifact["status"] == "needs_review"
    assert artifact["content"]["media_count"] >= 1
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/approve", json={}))
    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))
    assert exported["filename"].endswith(".pptx")
    assert exported["download_url"] == f"/projects/{project_id}/exports/{exported['filename']}"
    assert exported["path"] == artifact["content"]["pptx_path"]

    downloaded_ppt = client.get(exported["download_url"])
    assert downloaded_ppt.status_code == 200
    assert downloaded_ppt.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    pptx_path = Path(project["project_dir"]) / exported["path"]
    assert pptx_path.exists()

    for node_id in [
        "intro_selection",
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
        "storyboard",
    ]:
        node = generate_and_approve(client, project_id, node_id)
        assert node["status"] == "approved"

    storyboard = unwrap_ok(client.get(f"/projects/{project_id}/nodes/storyboard"))
    assert storyboard["status"] == "approved"
    assert len(storyboard["content"]["shots"]) == 6

    final_video = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/final_video/generate",
            json={"model": "veo_3_1-fast", "size": "1280x720", "mode": "reference", "full_run": True},
        )
    )
    assert final_video["status"] == "needs_review"
    assert final_video["video_path"] == "outputs/final_video.mp4"
    assert final_video["content"]["video_path"] == "outputs/final_video.mp4"
    assert len(final_video["tasks"]) == 6
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/final_video/approve", json={}))

    downloaded_mp4 = client.get(f"/projects/{project_id}/outputs/final_video.mp4")
    assert downloaded_mp4.status_code == 200
    assert downloaded_mp4.headers["content-type"].startswith("video/mp4")
    assert downloaded_mp4.content.startswith(b"\x00\x00\x00 ftyp")

    delivery_error = unwrap_error(
        client.post(f"/projects/{project_id}/nodes/final_delivery/generate", json={}),
        400,
        "GENERATION_INPUT_INVALID",
    )
    assert "FINAL_VIDEO_PLACEHOLDER" in delivery_error["message"]

    final_manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    final_states = {node["node_id"]: node["status"] for node in final_manifest["nodes"]}
    for node_id in [
        "lesson_plan",
        "pptx_artifact",
        "intro_selection",
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
        "storyboard",
        "final_video",
    ]:
        assert final_states[node_id] == "approved"
    assert final_states["final_delivery"] == "blocked"

    final_delivery_node = unwrap_ok(client.get(f"/projects/{project_id}/nodes/final_delivery"))
    assert final_delivery_node["status"] == "blocked"
    assert final_delivery_node["artifact"]["error_code"] == "FINAL_VIDEO_PLACEHOLDER"
