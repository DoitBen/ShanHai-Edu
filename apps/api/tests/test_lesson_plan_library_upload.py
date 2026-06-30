from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import enable_project_creation_fallback


REPO_ROOT = Path(__file__).resolve().parents[3]


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(REPO_ROOT / "workflow"),
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


def steps_by_id(workspace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["step_id"]: step for step in workspace["steps"]}


def test_upload_markdown_lesson_plan_and_create_project_from_reference(tmp_path: Path):
    client = make_client(tmp_path)

    uploaded = unwrap_ok(
        client.post(
            "/lesson-plan-library/uploads",
            data={"created_by": "qa"},
            files={
                "file": (
                    "公开课教案.md",
                    "# 5以内数的认识公开课教案\n\n## 教学目标\n会数 1-5 个物体。\n",
                    "text/markdown",
                )
            },
        )
    )

    assert uploaded["lesson_plan_id"].startswith("lp_")
    assert uploaded["title"] == "5以内数的认识公开课教案"
    assert uploaded["source_type"] == "uploaded_file"
    assert uploaded["source_filename"] == "公开课教案.md"
    assert uploaded["extract_status"] == "text_extracted"
    assert "会数 1-5 个物体" in uploaded["markdown"]

    project = unwrap_ok(
        client.post(
            "/projects",
            json={
                "name": "直接教案创建项目",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
                "reference_lesson_plan_id": uploaded["lesson_plan_id"],
            },
        )
    )
    project_id = project["project_id"]

    assert project["reference_lesson_plan_id"] == uploaded["lesson_plan_id"]
    assert project["textbook_id"] is None
    assert project["knowledge_point_id"] is None

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    node_status = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert node_status["textbook_parse"] == "skipped"
    assert node_status["lesson_plan"] == "needs_review"

    lesson = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))
    assert lesson["content"]["reference_lesson_plan_id"] == uploaded["lesson_plan_id"]
    assert lesson["content"]["reference_lesson_plan"]["lesson_plan_id"] == uploaded["lesson_plan_id"]
    assert lesson["content"]["lesson_plan_markdown"] == uploaded["markdown"]

    workspace = unwrap_ok(client.get(f"/projects/{project_id}/workspace"))
    steps = steps_by_id(workspace)
    assert workspace["current_step_id"] == "lesson_plan"
    assert steps["textbook_content"]["state"] == "completed"
    assert steps["lesson_plan"]["state"] == "current"
    assert steps["lesson_plan"]["primary_action"]["intent"] == "approve"
    assert "5以内数的认识公开课教案" in steps["lesson_plan"]["review"]["markdown"]


def test_pdf_lesson_plan_upload_is_marked_as_conservative_placeholder(tmp_path: Path):
    client = make_client(tmp_path)

    uploaded = unwrap_ok(
        client.post(
            "/lesson-plan-library/uploads",
            files={
                "file": (
                    "教案.pdf",
                    b"%PDF-1.4\n% ShanHaiEdu fixture without OCR text\n%%EOF",
                    "application/pdf",
                )
            },
        )
    )

    assert uploaded["source_filename"] == "教案.pdf"
    assert uploaded["extract_status"] == "placeholder"
    assert uploaded["metadata"]["text_extraction"]["method"] == "placeholder"
    assert "未执行 OCR" in uploaded["markdown"]
    assert "教案.pdf" in uploaded["markdown"]


def test_lesson_plan_upload_rejects_unsupported_file_type(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post(
        "/lesson-plan-library/uploads",
        files={"file": ("lesson.png", b"not a lesson plan", "image/png")},
    )
    payload = response.json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] == "LESSON_PLAN_UPLOAD_INVALID"
