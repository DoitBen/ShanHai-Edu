from pathlib import Path

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


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def test_health_and_workflow_load(tmp_path: Path):
    client = make_client(tmp_path)

    health = unwrap(client.get("/health"))
    assert health["status"] == "ok"
    assert health["workflow_version"] == "1.0.0"

    workflow = unwrap(client.get("/workflow"))
    node_ids = [node["id"] for node in workflow["nodes"]]
    assert "lesson_plan" in node_ids
    assert "final_video" in node_ids


def test_create_project_persists_manifest(tmp_path: Path):
    client = make_client(tmp_path)

    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "自动化测试项目",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )

    project_dir = Path(project["project_dir"])
    assert project_dir.exists()
    assert (project_dir / "project.db").exists()

    manifest = unwrap(client.get(f"/projects/{project['project_id']}/manifest"))
    states = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert states["textbook_parse"] == "not_started"
    assert states["final_video"] == "not_started"


def test_textbook_upload_and_generation_flow(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "认识分数",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]

    uploaded = unwrap(
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
    assert uploaded["status"] == "uploaded"
    assert Path(project["project_dir"], uploaded["path"]).exists()

    parse_result = unwrap(
        client.post(f"/projects/{project_id}/nodes/textbook_parse/generate")
    )
    assert parse_result["status"] == "needs_review"
    assert parse_result["content"]["lesson_title"] == "分数的初步认识"

    blocked = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"

    approved = unwrap(
        client.post(f"/projects/{project_id}/nodes/textbook_parse/approve")
    )
    assert approved["status"] == "approved"

    lesson = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate"))
    assert lesson["status"] == "needs_review"
    assert len(lesson["content"]["intro_designs"]) >= 3


def test_video_chain_creates_tasks_without_real_provider(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "视频闭环测试",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
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
        generated = unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/generate"))
        assert generated["status"] == "needs_review"
        unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/approve"))

    video = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate"))
    assert video["status"] == "needs_review"
    assert len(video["tasks"]) == 6
    approved = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/approve"))
    assert approved == {"node_id": "final_video", "status": "approved"}

    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 6
    assert {task["status"] for task in tasks} == {"generated"}
