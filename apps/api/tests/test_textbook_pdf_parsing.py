from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "textbook-parsing" / "renjiao-grade1-volume1-2024"
TEXTBOOK_PDF = FIXTURE_DIR / "1上-人教版小学数学课本（2024新版）.pdf"


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(REPO_ROOT / "workflow"),
            "provider_mode": "fake",
        }
    )
    return TestClient(app)


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def create_project(client: TestClient) -> dict:
    return unwrap(
        client.post(
            "/projects",
            json={
                "name": "PDF教材解析链路测试",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def upload_fixture_pdf(client: TestClient, project_id: str) -> dict:
    with TEXTBOOK_PDF.open("rb") as textbook:
        return unwrap(
            client.post(
                f"/projects/{project_id}/textbook",
                files={
                    "file": (
                        TEXTBOOK_PDF.name,
                        textbook,
                        "application/pdf",
                    )
                },
            )
        )


def test_fixture_pdf_generates_textbook_outline_and_knowledge_point_markdown(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    uploaded = upload_fixture_pdf(client, project_id)
    assert uploaded["status"] == "uploaded"
    assert uploaded["filename"].endswith(".pdf")

    parse_result = unwrap(
        client.post(
            f"/projects/{project_id}/nodes/textbook_parse/generate",
            json={"knowledge_point_id": "kp_001"},
        )
    )
    content = parse_result["content"]

    assert parse_result["status"] == "needs_review"
    assert content["textbook_meta"] == {
        "subject": "math",
        "grade": "1",
        "textbook_version": "renjiao",
        "volume": "shang",
        "title": "人教版小学数学一年级上册",
    }
    assert content["subject"] == "math"
    assert content["grade"] == "1"
    assert content["textbook_version"] == "renjiao"
    assert content["volume"] == "shang"

    knowledge_points = content["knowledge_points"]
    assert any(point["title"] == "5以内数的认识" for point in knowledge_points)
    selected = content["selected_knowledge_point"]
    assert selected["knowledge_point_id"] == "kp_001"
    assert selected["title"] == "5以内数的认识"
    assert "5以内数的认识" in selected["markdown"]
    assert selected["markdown_path"].endswith("knowledge-points/kp_001.md")
    assert Path(project["project_dir"], selected["markdown_path"]).exists()


def test_lesson_plan_uses_selected_knowledge_point_markdown(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    lesson = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))
    content = lesson["content"]

    assert lesson["status"] == "needs_review"
    assert content["source_knowledge_point_id"] == "kp_001"
    assert content["source_markdown_path"].endswith("knowledge-points/kp_001.md")
    assert "5以内数的认识" in content["lesson_plan_markdown"]
    assert "5以内数的认识" in content["textbook_anchor"]
