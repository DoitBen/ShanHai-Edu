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
    assert payload["ok"] is True
    return payload["data"]


def unwrap_error(response, expected_status: int, expected_code: str) -> dict[str, Any]:
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == expected_code
    assert isinstance(payload["error"].get("details"), list)
    return payload["error"]


def create_project(client: TestClient) -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "视频生成契约测试",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
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
                    "三年级数学，分数的初步认识。学生理解平均分和二分之一。",
                    "text/plain",
                )
            },
        )
    )


def generate_and_approve(client: TestClient, project_id: str, node_id: str) -> dict[str, Any]:
    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
    content = dict(generated["content"])
    content["_contract_marker"] = f"{node_id}_edited"
    edited = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/{node_id}/edit",
            json={"content": content},
        )
    )
    assert edited["status"] == "needs_review"
    current = unwrap_ok(client.get(f"/projects/{project_id}/nodes/{node_id}"))
    assert current["content"]["_contract_marker"] == f"{node_id}_edited"
    approved = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    assert approved == {"node_id": node_id, "status": "approved"}
    return current["content"]


def generate_and_approve_shared_visual_context(client: TestClient, project_id: str) -> None:
    for node_id in ["visual_contract", "character_dict"]:
        generate_and_approve(client, project_id, node_id)


def test_intro_selection_requires_approved_lesson_plan_and_can_be_edited(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate", json={}))
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    blocked = client.post(f"/projects/{project_id}/nodes/intro_selection/generate", json={})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))
    unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/approve", json={}))

    content = generate_and_approve(client, project_id, "intro_selection")
    assert content["primary_design_id"] in content["selected_design_ids"]

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    states = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert states["intro_selection"] == "approved"
    assert states["intro_video_script"] == "not_started"


def test_intro_selection_requires_selected_anchor_for_edit_and_approve(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/intro_selection/generate", json={}))
    content = dict(generated["content"])
    lesson_plan = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))["content"]
    selected_design = next(design for design in lesson_plan["intro_designs"] if design["design_id"] == content["primary_design_id"])
    assert content["selected_anchor"] == selected_design["anchor_to_lesson"]

    missing_anchor = dict(content)
    missing_anchor.pop("selected_anchor")
    edit_response = client.post(
        f"/projects/{project_id}/nodes/intro_selection/edit",
        json={"content": missing_anchor},
    )
    edit_error = unwrap_error(edit_response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "selected_anchor" for item in edit_error["details"])

    too_short = dict(content)
    too_short["selected_anchor"] = "太短"
    edit_response = client.post(
        f"/projects/{project_id}/nodes/intro_selection/edit",
        json={"content": too_short},
    )
    edit_error = unwrap_error(edit_response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "selected_anchor" and item["code"] == "too_short" for item in edit_error["details"])

    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.write_version(conn, project_id, "intro_selection", missing_anchor, "fixture", "fixture", "needs_review")
    approve_response = client.post(f"/projects/{project_id}/nodes/intro_selection/approve", json={})
    approve_error = unwrap_error(approve_response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "selected_anchor" for item in approve_error["details"])


def test_intro_video_script_requires_and_inherits_selected_anchor(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/intro_selection/generate", json={}))
    content = dict(generated["content"])
    selected_anchor = content["selected_anchor"]
    assert content["selected_anchor"] == selected_anchor
    broken = dict(content)
    broken.pop("selected_anchor")
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.write_version(conn, project_id, "intro_selection", broken, "fixture", "fixture", "approved")

    blocked = client.post(f"/projects/{project_id}/nodes/intro_video_script/generate", json={})
    assert blocked.status_code == 400
    assert blocked.json()["error"]["code"] == "GENERATION_INPUT_INVALID"
    assert "课程锚点" in blocked.json()["error"]["message"]

    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.write_version(conn, project_id, "intro_selection", content, "fixture", "fixture", "approved")

    script = unwrap_ok(client.post(f"/projects/{project_id}/nodes/intro_video_script/generate", json={}))
    assert script["content"]["anchor_to_lesson"] == selected_anchor
    assert script["content"]["narration_full_text"].endswith(selected_anchor)


def test_storyboard_returns_anchor_warning_when_last_subtitle_misses_anchor(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan", "intro_selection"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    generate_and_approve_shared_visual_context(client, project_id)

    intro_selection = unwrap_ok(client.get(f"/projects/{project_id}/nodes/intro_selection"))["content"]
    unrelated_script = {
        "total_duration_sec": 60,
        "video_type": "application",
        "anchor_to_lesson": intro_selection["selected_anchor"],
        "narration_full_text": "这是一段完全无关的旁白，只描述云朵和风车慢慢旋转。",
        "narration_word_count": 30,
        "banned_elements": ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"],
    }
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        client.app.state.store.write_version(conn, project_id, "intro_video_script", unrelated_script, "fixture", "fixture", "approved")

    for node_id in ["intro_video_screenplay", "intro_video_asset"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    storyboard = unwrap_ok(client.post(f"/projects/{project_id}/nodes/storyboard/generate", json={}))

    warnings = storyboard["content"].get("rule_warnings", [])
    assert any(item["rule_id"] == "R049" for item in warnings)
    warning = next(item for item in warnings if item["rule_id"] == "R049")
    assert warning["field"] == "shots[-1].subtitle"
    assert "selected_anchor" in warning["details"]


def test_fake_video_generation_chain_creates_queryable_tasks(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan", "intro_selection"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    generate_and_approve_shared_visual_context(client, project_id)

    for node_id in [
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
        "storyboard",
    ]:
        content = generate_and_approve(client, project_id, node_id)
        assert content

    video = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/final_video/generate",
            json={"model": "veo_3_1-fast", "size": "1280x720", "mode": "reference", "full_run": True},
        )
    )
    assert video["status"] == "drafted"
    assert video["video_path"] == "outputs/final_video.mp4"
    assert video["content"]["clip_count"] == 6
    assert video["content"]["video_path"] == "outputs/final_video.mp4"
    assert len(video["tasks"]) == 6
    final_video_path = Path(project["project_dir"]) / video["content"]["video_path"]
    assert final_video_path.exists()
    assert final_video_path.read_bytes().startswith(b"\x00\x00\x00 ftyp")

    final_node = unwrap_ok(client.get(f"/projects/{project_id}/nodes/final_video"))
    assert final_node["status"] == "drafted"
    assert final_node["content"]["clip_count"] == 6
    assert final_node["content"]["video_path"] == "outputs/final_video.mp4"

    tasks = unwrap_ok(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 6
    assert {task["status"] for task in tasks} == {"generated"}
    assert {task["node_id"] for task in tasks} == {"final_video"}
    assert all(task["payload"]["model"] == "veo_3_1-fast" for task in tasks)

    downloaded = client.get(f"/projects/{project_id}/outputs/final_video.mp4")
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("video/mp4")
    assert downloaded.content == final_video_path.read_bytes()


def test_fake_video_generation_reuses_existing_final_video_output(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan", "intro_selection"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))
    generate_and_approve_shared_visual_context(client, project_id)

    for node_id in [
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
        "storyboard",
    ]:
        generate_and_approve(client, project_id, node_id)

    final_video_path = Path(project["project_dir"]) / "outputs" / "final_video.mp4"
    final_video_path.parent.mkdir(parents=True, exist_ok=True)
    existing_video = bytes.fromhex(
        "000000206674797069736f6d0000020069736f6d69736f32617663316d703431"
        "0000000866726565"
        "0000000c6d64617474303439"
    )
    final_video_path.write_bytes(existing_video)

    video = unwrap_ok(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={"full_run": True}))

    assert video["video_path"] == "outputs/final_video.mp4"
    assert video["content"]["video_path"] == "outputs/final_video.mp4"
    assert final_video_path.read_bytes() == existing_video
    downloaded = client.get(f"/projects/{project_id}/outputs/final_video.mp4")
    assert downloaded.status_code == 200
    assert downloaded.content == existing_video


def test_video_node_edit_accepts_valid_content_and_keeps_needs_review(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/intro_selection/generate", json={}))
    content = dict(generated["content"])
    content["selection_reason"] = "T033 合法保存"

    edited = unwrap_ok(
        client.post(
            f"/projects/{project_id}/nodes/intro_selection/edit",
            json={"content": content},
        )
    )

    assert edited["status"] == "needs_review"
    current = unwrap_ok(client.get(f"/projects/{project_id}/nodes/intro_selection"))
    assert current["status"] == "needs_review"
    assert current["content"]["selection_reason"] == "T033 合法保存"


def test_video_node_edit_rejects_missing_required_fields(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    response = client.post(
        f"/projects/{project_id}/nodes/intro_selection/edit",
        json={"content": {"selection_mode": "single_best"}},
    )

    error = unwrap_error(response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "selected_design_ids" for item in error["details"])
    assert any(item["field"] == "primary_design_id" for item in error["details"])


def test_video_node_edit_rejects_invalid_references_and_shapes(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in [
        "textbook_parse",
        "lesson_plan",
        "intro_selection",
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
    ]:
        if node_id == "intro_video_script":
            generate_and_approve_shared_visual_context(client, project_id)
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    response = client.post(
        f"/projects/{project_id}/nodes/storyboard/edit",
        json={
            "content": {
                "shots": [
                    {
                        "shot_id": "shot_bad",
                        "duration_sec": 10,
                        "main_subject": "卡通披萨平均分情境",
                        "reference_image_ids": ["missing_asset"],
                        "narration_slice": "这一份是整体的二分之一。",
                        "model_prompt": "旁白（男声，中文）：这一份是整体的二分之一。禁止英文配音。",
                    }
                ]
            }
        },
    )

    error = unwrap_error(response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "shots[0].reference_image_ids" for item in error["details"])


def test_video_node_edit_rejects_invalid_final_video_structure(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    for node_id in ["textbook_parse", "lesson_plan", "intro_selection", "intro_video_script", "intro_video_screenplay", "intro_video_asset", "storyboard"]:
        if node_id == "intro_video_script":
            generate_and_approve_shared_visual_context(client, project_id)
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    response = client.post(
        f"/projects/{project_id}/nodes/final_video/edit",
        json={"content": {"clip_count": 2, "clips": [], "english_audio_detected": False}},
    )

    error = unwrap_error(response, 400, "NODE_CONTENT_INVALID")
    assert any(item["field"] == "clips" for item in error["details"])
