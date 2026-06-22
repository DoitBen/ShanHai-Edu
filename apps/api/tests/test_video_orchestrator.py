from pathlib import Path
from typing import Any

from app.providers import FakeProvider
from app.store import ProjectStore
from app.video_orchestrator import VideoOrchestrator
from app.workflow_config import WorkflowConfig


ROOT = Path(__file__).resolve().parents[3]


def test_video_orchestrator_fake_run_creates_tasks_and_final_content(tmp_path: Path):
    store = ProjectStore(tmp_path / "storage")
    workflow = WorkflowConfig(ROOT / "workflow")
    project = store.create_project(
        {
            "name": "orchestrator fake",
            "subject": "math",
            "grade": "1",
            "textbook_version": "renjiao",
            "volume": "shang",
            "lesson_type": "public",
        },
        workflow,
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    storyboard = {
        "shots": [
            {
                "shot_id": f"shot_{index:02d}",
                "duration_sec": 10,
                "main_subject": "卡通桌面数数",
                "reference_image_ids": [f"asset_ref_{index:02d}"],
                "narration_slice": f"认识数字 {index}",
                "subtitle": f"认识数字 {index}",
                "model_prompt": f"中文旁白：认识数字 {index}。\n画面：卡通桌面数数。\n禁止英文配音。",
            }
            for index in range(1, 3)
        ]
    }
    with store.connect(project_dir) as conn:
        script_version = store.write_version(
            conn,
            project_id,
            "intro_video_script",
            {"narration_full_text": "认识 1 到 2。"},
            "fixture",
            "fixture",
            "approved",
        )
        storyboard_version = store.write_version(conn, project_id, "storyboard", storyboard, "fixture", "fixture", "approved")

        orchestrator = VideoOrchestrator(
            store=store,
            text_provider=FakeProvider(),
            video_provider=None,
            tts_provider=None,
            video_model="omni_flash-10s",
            reference_url_resolver=lambda _project_id: {},
        )
        result = orchestrator.generate(conn, project_id, project_dir, {"full_run": True})

    assert result["status"] == "needs_review"
    assert result["content"]["clip_count"] == 2
    assert result["content"]["video_path"] == "outputs/final_video.mp4"
    assert result["content"]["audio_path"] == result["content"]["narration_audio_path"]
    assert result["content"]["subtitle_path"] == result["content"]["subtitle_srt_path"]
    assert result["content"]["source_versions"] == {
        "storyboard": storyboard_version["version_id"],
        "intro_video_script": script_version["version_id"],
    }
    assert len(result["content"]["provider_task_ids"]) == 2
    assert result["content"]["generated_at"]
    assert len(result["tasks"]) == 2
    assert {task["status"] for task in result["tasks"]} == {"generated"}
    assert (project_dir / "outputs" / "final_video.mp4").exists()
