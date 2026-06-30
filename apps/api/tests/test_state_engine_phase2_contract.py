import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import enable_project_creation_fallback
from app.providers import FakeProvider, ProviderError


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


def create_project(client: TestClient, name: str = "StateEngine Phase2 契约") -> dict[str, Any]:
    return unwrap_ok(
        client.post(
            "/projects",
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


def transition_rows(project_dir: str, project_id: str, node_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(Path(project_dir) / "project.db") as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """
            SELECT * FROM state_transition_log
            WHERE project_id = ? AND node_id = ?
            ORDER BY triggered_at, rowid
            """,
            (project_id, node_id),
        ).fetchall()


def seed_approved_node(client: TestClient, project: dict[str, Any], node_id: str, content: dict[str, Any]) -> dict[str, Any]:
    store = client.app.state.store
    project_id = project["project_id"]
    with store.connect(Path(project["project_dir"])) as conn:
        version = store.write_version(conn, project_id, node_id, content, "fixture", "fixture", "approved")
        store.update_current_version_status(conn, version["version_id"], "approved", approved=True)
        return version


def seed_final_video_upstreams_approved(client: TestClient, project: dict[str, Any]) -> None:
    seed_approved_node(
        client,
        project,
        "intro_video_script",
        {
            "total_duration_sec": 20,
            "video_type": "application",
            "anchor_to_lesson": "从分水果的一一对应问题回到课堂中的数量表达任务。",
            "narration_full_text": "小朋友正在分水果，大家想知道每个盘子能不能刚好配上一个水果。",
            "narration_word_count": 34,
            "banned_elements": ["real_minor", "teacher_questioning"],
        },
    )
    seed_approved_node(
        client,
        project,
        "storyboard",
        {
            "shots": [
                {
                    "shot_id": "shot_01",
                    "duration_sec": 10,
                    "main_subject": "卡通水果和餐盘一一对应",
                    "character_refs": [],
                    "reference_image_ids": ["asset_ref_01"],
                    "narration_slice": "先看水果和餐盘是不是一样多。",
                    "subtitle": "先看水果和餐盘是不是一样多。",
                    "model_prompt": "中文旁白：先看水果和餐盘是不是一样多。\n画面：卡通水果和餐盘一一对应。\n禁止英文配音。",
                    "first_frame_test_status": "passed",
                    "first_frame_asset_id": "asset_ref_01",
                }
            ]
        },
    )


def seed_intro_video_asset_upstreams_approved(client: TestClient, project: dict[str, Any]) -> None:
    seed_approved_node(
        client,
        project,
        "character_dict",
        {
            "characters": [
                {
                    "character_id": "char_math_guide",
                    "name": "小山",
                    "style_constraint": "3d_non_realistic",
                    "banned_keywords": ["真人", "photorealistic"],
                }
            ]
        },
    )
    seed_approved_node(
        client,
        project,
        "visual_contract",
        {
            "palette": ["#0F766E", "#F59E0B"],
            "style_keywords": ["非写实卡通", "生活化数学情境"],
            "font_preference": "Microsoft YaHei",
        },
    )
    seed_approved_node(
        client,
        project,
        "intro_video_screenplay",
        {
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "duration_sec": 10,
                    "scene_description": "卡通桌面上出现几个水果和盘子。",
                    "character_refs": [],
                    "narration_segment": "数一数水果和盘子是不是一样多。",
                }
            ]
        },
    )


class BrokenIntroVideoAssetProvider(FakeProvider):
    name = "broken-test-provider"

    def generate(self, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if node_id == "intro_video_asset":
            raise ProviderError("INTRO_VIDEO_ASSET_TEST_FAILURE", "测试 provider 失败", retryable=True)
        return super().generate(node_id, context)


def test_rule_hard_block_transition_is_owned_by_state_engine(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    response = client.post(
        f"/projects/{project_id}/nodes/character_dict/edit",
        json={
            "content": {
                "characters": [
                    {
                        "character_id": "c1",
                        "display_name": "真人学生",
                        "role": "student",
                        "style_constraint": "photorealistic",
                        "banned_keywords": [],
                    }
                ]
            }
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "RULE_VIOLATION_R004"
    rows = transition_rows(project["project_dir"], project_id, "character_dict")
    blocked_rows = [row for row in rows if row["to_status"] == "blocked"]
    assert blocked_rows
    assert blocked_rows[-1]["trigger"] == "hard_block_rule_hit"
    assert '"handled_by": "StateEngine"' in blocked_rows[-1]["reason"]
    assert '"rule_id": "R004"' in blocked_rows[-1]["reason"]


def test_final_video_generate_records_state_engine_transition(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    seed_final_video_upstreams_approved(client, project)

    response = client.post(f"/projects/{project_id}/nodes/final_video/generate", json={})

    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["node_id"] == "final_video"
    assert body["status"] in {"drafted", "needs_review"}
    rows = transition_rows(project["project_dir"], project_id, "final_video")
    assert rows
    assert rows[-1]["to_status"] == body["status"]
    assert rows[-1]["trigger"] in {"ai_generate_done", "video_tasks_submitted"}
    assert '"handled_by": "StateEngine"' in (rows[-1]["reason"] or "")


def test_provider_failure_blocked_state_is_recorded_by_state_engine(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    seed_intro_video_asset_upstreams_approved(client, project)
    client.app.state.service.provider = BrokenIntroVideoAssetProvider()

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "INTRO_VIDEO_ASSET_TEST_FAILURE"
    rows = transition_rows(project["project_dir"], project_id, "intro_video_asset")
    blocked_rows = [row for row in rows if row["to_status"] == "blocked"]
    assert blocked_rows
    assert blocked_rows[-1]["trigger"] == "provider_failed"
    assert '"handled_by": "StateEngine"' in blocked_rows[-1]["reason"]
    assert '"error_code": "INTRO_VIDEO_ASSET_TEST_FAILURE"' in blocked_rows[-1]["reason"]
