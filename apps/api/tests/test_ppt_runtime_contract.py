from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app


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
