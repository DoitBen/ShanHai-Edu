from pathlib import Path
import subprocess
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.providers import MinimaxTTSProvider, ProviderError
from app.video_outputs import FINAL_VIDEO_REL_PATH
from app.video_outputs import compose_final_video_from_clips


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "capabilities_path": str(
                Path(__file__).resolve().parents[3]
                / "docs"
                / "api-research"
                / "octo-video"
                / "capabilities.json"
            ),
            **(overrides or {}),
        }
    )
    return TestClient(app)


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def test_minimax_tts_provider_requires_key():
    provider = MinimaxTTSProvider(api_key=None, base_url="https://api.minimaxi.com", model="speech-2.8-hd")

    try:
        provider.synthesize("你好", Path("audio/out.mp3"))
    except ProviderError as exc:
        assert exc.code == "MINIMAX_TTS_KEY_MISSING"
    else:
        raise AssertionError("expected ProviderError")


def test_minimax_tts_provider_writes_audio_from_hex_response(tmp_path: Path):
    def transport(payload: dict[str, Any]) -> dict[str, Any]:
        assert payload["model"] == "speech-2.8-hd"
        assert payload["voice_setting"]["voice_id"] == "Chinese (Mandarin)_Gentleman"
        return {"data": {"audio": "49443304000000000000"}}

    provider = MinimaxTTSProvider(
        api_key="fake",
        base_url="https://api.minimaxi.com",
        model="speech-2.8-hd",
        voice_id="Chinese (Mandarin)_Gentleman",
        transport=transport,
    )
    output = tmp_path / "audio" / "narration.mp3"

    result = provider.synthesize("认识 1 到 5。", output)

    assert output.exists()
    assert output.read_bytes().startswith(b"ID3")
    assert result["audio_path"] == str(output)
    assert result["voice_gender"] == "male"
    assert result["voice_language"] == "zh-CN"


def test_final_video_generate_creates_audio_manifest_and_schema_fields(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "TTS final video",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    storyboard = {
        "shots": [
            {
                "shot_id": "shot_01",
                "duration_sec": 10,
                "main_subject": "卡通苹果",
                "character_refs": [],
                "reference_image_ids": ["asset_001"],
                "narration_slice": "先数一个苹果。",
                "subtitle": "先数一个苹果",
                "model_prompt": "中文旁白：先数一个苹果。\n禁止英文配音。",
                "first_frame_test_status": "passed",
                "first_frame_asset_id": "asset_001",
            },
            {
                "shot_id": "shot_02",
                "duration_sec": 10,
                "main_subject": "卡通铅笔",
                "character_refs": [],
                "reference_image_ids": ["asset_002"],
                "narration_slice": "再数两支铅笔。",
                "subtitle": "再数两支铅笔",
                "model_prompt": "中文旁白：再数两支铅笔。\n禁止英文配音。",
                "first_frame_test_status": "passed",
                "first_frame_asset_id": "asset_002",
            },
        ]
    }
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        client.app.state.store.write_version(
            conn,
            project_id,
            "intro_video_script",
            {"narration_full_text": "先数一个苹果。再数两支铅笔。"},
            "ai",
            "fixture",
            "approved",
        )
        client.app.state.store.write_version(conn, project_id, "storyboard", storyboard, "ai", "fixture", "approved")

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={}))
    node = unwrap(client.get(f"/projects/{project_id}/nodes/final_video"))
    content = node["content"]
    project_dir = Path(project["project_dir"])

    assert generated["video_path"] == FINAL_VIDEO_REL_PATH
    assert content["voice_gender"] == "male"
    assert content["voice_language"] == "zh-CN"
    assert content["audio_path"] == content["narration_audio_path"]
    assert content["subtitle_path"] == content["subtitle_srt_path"]
    assert content["provider_task_ids"]
    assert content["source_versions"]["storyboard"]
    assert content["generated_at"]
    assert content["audio_verified"] is True
    assert content["english_audio_detected"] is False
    assert (project_dir / content["narration_audio_path"]).exists()
    assert (project_dir / content["subtitle_srt_path"]).exists()
    assert (project_dir / content["concat_manifest_path"]).exists()
    assert (project_dir / FINAL_VIDEO_REL_PATH).exists()


def test_compose_final_video_reports_ffmpeg_decode_errors_as_runtime_error(tmp_path: Path, monkeypatch):
    clip = tmp_path / "clips" / "shot_01.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"not a real mp4")
    monkeypatch.setattr("app.video_outputs.shutil.which", lambda name: "ffmpeg")

    def broken_run(*args, **kwargs):
        raise UnicodeDecodeError("gbk", b"\xad", 0, 1, "illegal multibyte sequence")

    monkeypatch.setattr(subprocess, "run", broken_run)

    try:
        compose_final_video_from_clips(tmp_path, ["clips/shot_01.mp4"])
    except RuntimeError as exc:
        assert "ffmpeg" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
