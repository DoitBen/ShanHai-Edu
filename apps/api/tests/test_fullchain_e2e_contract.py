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
                        "model_prompt": f"旁白（男声，中文）：认识数字 {index}。禁止英文配音。",
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


def test_real_text_placeholder_video_fullchain_exports_ppt_with_mp4(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.app.state.settings.provider_mode == "real"
    assert client.app.state.settings.video_provider_mode == "placeholder"
    assert client.app.state.service.provider.name == "deepseek"
    assert client.app.state.service.video_provider is None

    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook_input(client, project_id)

    for node_id in [
        "textbook_parse",
        "lesson_plan",
        "visual_contract",
        "character_dict",
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
    assert final_video["status"] == "running"
    assert final_video["video_path"] == "outputs/final_video.mp4"
    assert final_video["content"]["video_path"] == "outputs/final_video.mp4"
    assert len(final_video["tasks"]) == 6

    downloaded_mp4 = client.get(f"/projects/{project_id}/outputs/final_video.mp4")
    assert downloaded_mp4.status_code == 200
    assert downloaded_mp4.headers["content-type"].startswith("video/mp4")
    assert downloaded_mp4.content.startswith(b"\x00\x00\x00 ftyp")

    exported = unwrap_ok(client.post(f"/projects/{project_id}/export/ppt", json={}))
    assert exported["filename"].endswith(".pptx")
    assert exported["download_url"] == f"/projects/{project_id}/exports/{exported['filename']}"
    assert exported["video_path"] == "outputs/final_video.mp4"

    downloaded_ppt = client.get(exported["download_url"])
    assert downloaded_ppt.status_code == 200
    assert downloaded_ppt.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    pptx_path = Path(project["project_dir"]) / exported["path"]
    with ZipFile(pptx_path) as archive:
        media_names = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/media/") and name.endswith(".mp4")
        ]
        assert media_names
        assert archive.read(media_names[0]) == downloaded_mp4.content
