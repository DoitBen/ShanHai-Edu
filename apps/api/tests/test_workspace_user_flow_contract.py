from pathlib import Path
from typing import Any

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


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "T129 用户态工作区",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
                "textbook_id": "renjiao-grade1-volume1-2024",
                "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
                "knowledge_point_id": "kp_001",
            },
        )
    )


def create_direct_lesson_project(client: TestClient) -> dict[str, Any]:
    uploaded = unwrap_ok(
        client.post(
            "/lesson-plan-library/uploads",
            files={
                "file": (
                    "direct-lesson.md",
                    "# 直接教案\n\n## 教学目标\n直接从教案推进。",
                    "text/markdown",
                )
            },
        )
    )
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "T direct lesson 用户态工作区",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
                "reference_lesson_plan_id": uploaded["lesson_plan_id"],
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
                    "一年级数学《5以内数的认识》，学生需要会数数、比大小、认识第几。",
                    "text/plain",
                )
            },
        )
    )


def generate_and_approve(client: TestClient, project_id: str, node_id: str) -> dict[str, Any]:
    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    return generated["content"]


def write_approved_node(client: TestClient, project: dict[str, Any], node_id: str, content: dict[str, Any]) -> dict[str, Any]:
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        result = client.app.state.store.write_version(conn, project["project_id"], node_id, content, "fixture", "fixture", "approved")
        client.app.state.store.update_current_version_status(conn, result["version_id"], "approved", approved=True)
        return result["content"]


def write_needs_review_node(client: TestClient, project: dict[str, Any], node_id: str, content: dict[str, Any]) -> dict[str, Any]:
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        result = client.app.state.store.write_version(conn, project["project_id"], node_id, content, "fixture", "fixture", "needs_review")
        return result["content"]


def steps_by_id(workspace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["step_id"]: step for step in workspace["steps"]}


def assert_no_technical_terms(value: Any) -> None:
    text = str(value)
    forbidden = ["StateEngine", "schema", "manifest", "R010", "dependency_gate", "node_id"]
    for term in forbidden:
        assert term not in text


def test_workspace_user_flow_exposes_seven_user_steps_and_hides_diagnostics_from_main_steps(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))

    assert [step["title"] for step in workspace["steps"]] == [
        "项目信息",
        "教材内容",
        "教案生成",
        "导入视频方案",
        "PPT 草稿",
        "视频生成",
        "最终交付",
    ]
    assert workspace["current_step_id"] == "textbook_content"

    steps = steps_by_id(workspace)
    assert steps["project_info"]["state"] == "completed"
    assert steps["project_info"]["review"]["summary"]
    assert steps["textbook_content"]["state"] == "current"
    assert steps["textbook_content"]["primary_action"]["label"] == "生成草稿"
    assert steps["lesson_plan"]["state"] == "locked"
    assert steps["lesson_plan"]["lock_reason"] == "请先确认【教材内容】后，再进入【教案生成】。"
    assert steps["lesson_plan"]["primary_action"]["enabled"] is False
    assert steps["ppt_draft"]["state"] == "locked"
    assert steps["ppt_draft"]["lock_reason"] == "请先确认【导入视频方案】后，再进入【PPT 草稿】。"

    for step in workspace["steps"]:
        main_step = {key: value for key, value in step.items() if key != "sub_gates"}
        assert_no_technical_terms(main_step)
    assert "developer_diagnostics" in workspace
    assert "node_ids" in workspace["developer_diagnostics"]["steps"]["lesson_plan"]


def test_workspace_user_flow_tracks_completed_current_locked_and_review_content(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    textbook_content = write_approved_node(
        client,
        project,
        "textbook_parse",
        {
            "textbook_meta": {"title": "人教版一年级上册"},
            "selected_knowledge_point": {
                "title": "5以内数的认识",
                "textbook_pages": "14-23",
                "pdf_pages": "19-28",
                "markdown": "# 5以内数的认识\n\n教材结构化内容。",
            },
        },
    )
    lesson_content = write_needs_review_node(
        client,
        project,
        "lesson_plan",
        {
            "source_knowledge_point_id": "kp_001",
            "lesson_plan_markdown": "# 公开课教案\n\n从数数活动导入。",
        },
    )

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    steps = steps_by_id(workspace)

    assert workspace["current_step_id"] == "lesson_plan"
    assert steps["textbook_content"]["state"] == "completed"
    assert steps["textbook_content"]["review"]["markdown"] == textbook_content["selected_knowledge_point"]["markdown"]
    assert steps["lesson_plan"]["state"] == "current"
    assert steps["lesson_plan"]["primary_action"]["label"] == "确认并进入下一步"
    assert steps["lesson_plan"]["result"]["status_text"] == "已生成草稿，等待确认。"
    assert steps["lesson_plan"]["review"]["markdown"] == lesson_content["lesson_plan_markdown"]
    assert steps["intro_video_plan"]["state"] == "locked"
    assert steps["intro_video_plan"]["lock_reason"] == "请先确认【教案生成】后，再进入【导入视频方案】。"


def test_workspace_user_flow_keeps_upstream_errors_actionable_and_diagnostics_separate(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    blocked = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    steps = steps_by_id(workspace)

    assert steps["lesson_plan"]["state"] == "locked"
    assert steps["lesson_plan"]["user_action"] == "请先确认【教材内容】后再进入【教案生成】。"
    assert_no_technical_terms(steps["lesson_plan"])
    diagnostics = workspace["developer_diagnostics"]["steps"]["lesson_plan"]
    assert diagnostics["node_ids"] == ["lesson_plan"]
    assert diagnostics["nodes"][0]["latest_transition"]["trigger"] == "dependency_gate_blocked"
    assert "R010" in diagnostics["nodes"][0]["latest_transition"]["reason"]


def test_workspace_user_flow_exposes_ppt_sub_gates_without_manifest_terms(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    write_approved_node(client, project, "textbook_parse", {"selected_knowledge_point": {"title": "5以内数的认识"}})
    write_approved_node(client, project, "lesson_plan", {"lesson_plan_markdown": "# lesson"})
    write_approved_node(
        client,
        project,
        "intro_selection",
        {"selected_title": "动物数数", "selected_anchor": "接回数清物体个数的学习任务。"},
    )
    write_approved_node(client, project, "intro_video_script", {"narration_full_text": "旁白"})
    write_approved_node(client, project, "intro_video_screenplay", {"scenes": [{"scene_id": "s1"}]})
    write_approved_node(client, project, "intro_video_asset", {"assets": [{"asset_id": "asset_1"}]})
    write_approved_node(client, project, "storyboard", {"shots": [{"shot_id": "shot_01"}]})
    write_approved_node(client, project, "ppt_assembly_plan", {"page_count_target": 8, "theme": "数数探究"})
    write_needs_review_node(client, project, "ppt_page_script", {"pages": [{"page_index": 1, "page_objective": "观察"}]})
    write_approved_node(client, project, "ppt_visual_asset", {"assets": [{"asset_id": "ppt_asset_1", "status": "placeholder"}]})
    write_approved_node(
        client,
        project,
        "pptx_artifact",
        {"pptx_path": "exports/demo.pptx", "download_url": f"/projects/{project_id}/exports/demo.pptx"},
    )

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    ppt_step = steps_by_id(workspace)["ppt_draft"]

    assert ppt_step["state"] == "current"
    assert ppt_step["current_action"] == "确认 PPT 草稿是否符合公开课展示需要。"
    assert ppt_step["review_summary"]
    assert [gate["gate_id"] for gate in ppt_step["sub_gates"]] == [
        "structure_plan",
        "page_script",
        "visual_assets",
        "pptx_file",
    ]
    assert [gate["title"] for gate in ppt_step["sub_gates"]] == ["结构方案", "逐页脚本", "视觉资产", "PPTX 文件"]
    assert [gate["state"] for gate in ppt_step["sub_gates"]] == ["completed", "current", "completed", "completed"]
    assert ppt_step["sub_gates"][0]["review_summary"] == "已形成 8 页 PPT 结构方案。"
    for gate in ppt_step["sub_gates"]:
        assert set(gate.keys()) == {"gate_id", "title", "state", "status_text", "review_summary"}
    public_sub_gate_text = str(ppt_step["sub_gates"])
    for forbidden in ["ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset", "pptx_artifact", "pptx-generation"]:
        assert forbidden not in public_sub_gate_text

    public_ppt_step = {
        key: value
        for key, value in ppt_step.items()
        if key not in {"developer_diagnostics", "sub_gates"}
    }
    public_text = str(public_ppt_step)
    for forbidden in ["manifest", "node_id", "schema", "ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset", "pptx_artifact"]:
        assert forbidden not in public_text
    assert workspace["developer_diagnostics"]["steps"]["ppt_draft"]["compatibility_aliases"]["pptx_artifact"] == [
        "pptx-generation"
    ]


def test_workspace_user_flow_exposes_video_sub_gates_from_nodes_and_tasks(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    write_approved_node(client, project, "textbook_parse", {"selected_knowledge_point": {"title": "5以内数的认识"}})
    write_approved_node(client, project, "lesson_plan", {"lesson_plan_markdown": "# lesson"})
    write_approved_node(
        client,
        project,
        "intro_selection",
        {"selected_title": "动物数数", "selected_anchor": "接回数清物体个数的学习任务。"},
    )
    write_approved_node(client, project, "ppt_assembly_plan", {"page_count_target": 8})
    write_approved_node(client, project, "ppt_page_script", {"pages": [{"page_index": 1}]})
    write_approved_node(client, project, "ppt_visual_asset", {"assets": [{"asset_id": "ppt_asset_1"}]})
    write_approved_node(client, project, "pptx_artifact", {"pptx_path": "exports/demo.pptx"})
    write_approved_node(client, project, "intro_video_script", {"total_duration_sec": 70, "narration_full_text": "中文旁白"})
    write_approved_node(client, project, "intro_video_screenplay", {"scenes": [{"scene_id": "s1"}, {"scene_id": "s2"}]})
    write_approved_node(client, project, "intro_video_asset", {"assets": [{"asset_id": "asset_1", "status": "completed"}]})
    write_needs_review_node(client, project, "storyboard", {"shots": [{"shot_id": "shot_01"}, {"shot_id": "shot_02"}]})
    write_needs_review_node(client, project, "final_video", {"clip_count": 2, "video_path": "outputs/final_video.mp4"})
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"shot_id": "shot_01"},
            status="completed",
            result={"clip_path": "clips/shot_01.mp4", "download_status": "downloaded"},
        )
        client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "tts_generation",
            {"voice": "zh-CN"},
            status="completed",
            result={"audio_path": "audio/narration.mp3"},
        )

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    video_step = steps_by_id(workspace)["video_generation"]

    assert video_step["state"] == "current"
    assert [gate["gate_id"] for gate in video_step["sub_gates"]] == [
        "script",
        "screenplay",
        "assets_first_frame",
        "storyboard",
        "clip_tts_composition",
    ]
    assert [gate["title"] for gate in video_step["sub_gates"]] == ["文稿", "分场剧本", "资产与首帧", "分镜", "clip/TTS/合成"]
    assert [gate["state"] for gate in video_step["sub_gates"]] == [
        "completed",
        "completed",
        "completed",
        "current",
        "current",
    ]
    for gate in video_step["sub_gates"]:
        assert set(gate.keys()) == {"gate_id", "title", "state", "status_text", "review_summary"}
    public_sub_gate_text = str(video_step["sub_gates"])
    for forbidden in ["intro_video_script", "intro_video_screenplay", "final_video", "video-screenplay"]:
        assert forbidden not in public_sub_gate_text
    assert "2 个镜头" in video_step["sub_gates"][3]["review_summary"]
    assert "clip 1/2" in video_step["sub_gates"][4]["review_summary"]
    assert "TTS 1 项" in video_step["sub_gates"][4]["review_summary"]

    public_video_step = {
        key: value
        for key, value in video_step.items()
        if key not in {"developer_diagnostics", "sub_gates"}
    }
    public_text = str(public_video_step)
    for forbidden in ["manifest", "node_id", "schema", "intro_video_script", "intro_video_screenplay", "final_video"]:
        assert forbidden not in public_text
    assert workspace["developer_diagnostics"]["steps"]["video_generation"]["compatibility_aliases"]["intro_video_screenplay"] == [
        "video-screenplay"
    ]


def test_workspace_user_flow_separates_user_fields_from_developer_diagnostics(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    lesson_step = steps_by_id(workspace)["lesson_plan"]

    assert "current_action" in lesson_step
    assert "review_summary" in lesson_step
    assert "developer_diagnostics" not in lesson_step
    assert lesson_step["lock_reason"] == "请先确认【教材内容】后，再进入【教案生成】。"
    assert lesson_step["current_action"] == "请先确认【教材内容】后再进入【教案生成】。"
    assert lesson_step["review_summary"] == "完成后可回看本步骤结果。"
    assert lesson_step["sub_gates"] == []
    assert_no_technical_terms(lesson_step)

    diagnostics = workspace["developer_diagnostics"]["steps"]["lesson_plan"]
    assert diagnostics["node_ids"] == ["lesson_plan"]
    assert diagnostics["nodes"][0]["node_id"] == "lesson_plan"
    assert "schema" in diagnostics["nodes"][0]


def test_direct_lesson_project_starts_at_lesson_plan_and_does_not_lock_on_textbook_content(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_direct_lesson_project(client)
    project_id = project["project_id"]

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    steps = steps_by_id(workspace)

    assert workspace["current_step_id"] == "lesson_plan"
    assert steps["textbook_content"]["state"] == "completed"
    assert steps["textbook_content"]["result"]["status_text"] == "已从已有教案导入，教材内容步骤已跳过。"
    assert steps["lesson_plan"]["state"] == "current"
    assert steps["lesson_plan"]["lock_reason"] is None
    assert steps["lesson_plan"]["primary_action"]["enabled"] is True


def test_direct_lesson_source_payload_also_skips_textbook_content(tmp_path: Path):
    client = make_client(tmp_path)
    project = client.app.state.store.create_project(
        {
            "name": "T direct_lesson 字段用户态工作区",
            "subject": "math",
            "grade": "1",
            "textbook_version": "renjiao",
            "volume": "shang",
            "lesson_type": "public",
            "lesson_plan_source": "direct_lesson",
            "direct_lesson": True,
        },
        client.app.state.workflow,
        owner_id=client.app.state.settings.project_creation_default_owner_user_id,
    )

    workspace = unwrap_ok(client.get(f"/projects/{project['project_id']}/workspace"))
    steps = steps_by_id(workspace)

    assert workspace["current_step_id"] == "lesson_plan"
    assert steps["textbook_content"]["state"] == "completed"
    assert steps["textbook_content"]["result"]["status_text"] == "已从已有教案导入，教材内容步骤已跳过。"
    assert steps["lesson_plan"]["state"] == "current"
