from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "t075_real_fullchain_smoke.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("t075_real_fullchain_smoke", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_t075_mask_text_redacts_provider_secrets():
    smoke = load_script_module()

    masked = smoke.mask_text(
        "Authorization: Bearer fake-token "
        "CONFIG_KEY=samplecredentialabcdef token: samplecredentialxyz"
    )

    assert "samplecredential1234567890" not in masked
    assert "samplecredentialabcdef" not in masked
    assert "samplecredentialxyz" not in masked
    assert "<redacted>" in masked


def test_t075_success_checks_require_real_media_by_default():
    smoke = load_script_module()
    evidence = {
        "generated_image_paths": [{"api_path": "assets/generated_images/a.png", "local_path": "a.png", "bytes": 12}],
        "clip_download_paths": [{"api_path": "clips/s1.mp4", "local_path": "s1.mp4", "bytes": 34}],
        "final_video_path": {"api_path": "outputs/final_video.mp4", "local_path": "final_video.mp4", "bytes": 56},
        "ppt_path": {
            "api_path": "exports/demo.pptx",
            "local_path": "demo.pptx",
            "bytes": 78,
            "ppt_media_mp4_entries": ["ppt/media/media1.mp4"],
        },
        "final_video_node_content": {
            "voice_gender": "male",
            "voice_language": "zh-CN",
            "audio_verified": True,
            "english_audio_detected": False,
            "narration_audio_path": "audio/narration.mp3",
            "subtitle_srt_path": "audio/narration.srt",
            "concat_manifest_path": "outputs/concat_manifest.json",
            "video_path": "outputs/final_video.mp4",
        },
        "ffprobe": {"audio_stream_count": 1, "video_stream_count": 1},
    }

    checks = smoke.evaluate_success_checks(evidence, allow_placeholder_media=False)

    assert checks["has_real_image"]["ok"] is True
    assert checks["has_real_video_clip"]["ok"] is True
    assert checks["has_final_video"]["ok"] is True
    assert checks["has_ppt"]["ok"] is True
    assert checks["has_verified_audio"]["ok"] is True
    assert checks["has_final_video_schema"]["ok"] is True
    assert checks["has_embedded_ppt_video"]["ok"] is True
    assert smoke.all_success_checks_passed(checks) is True


def test_t075_success_checks_reject_missing_final_audio_contract():
    smoke = load_script_module()
    evidence = {
        "generated_image_paths": [{"api_path": "assets/generated_images/a.png", "local_path": "a.png", "bytes": 12}],
        "clip_download_paths": [{"api_path": "clips/s1.mp4", "local_path": "s1.mp4", "bytes": 34}],
        "final_video_path": {"api_path": "outputs/final_video.mp4", "local_path": "final_video.mp4", "bytes": 56},
        "ppt_path": {"api_path": "exports/demo.pptx", "local_path": "demo.pptx", "bytes": 78},
        "final_video_node_content": {
            "voice_gender": "female",
            "voice_language": "en-US",
            "audio_verified": False,
            "english_audio_detected": True,
            "video_path": "outputs/final_video.mp4",
        },
        "ffprobe": {"audio_stream_count": 0, "video_stream_count": 1},
    }

    checks = smoke.evaluate_success_checks(evidence, allow_placeholder_media=False)

    assert checks["has_verified_audio"]["ok"] is False
    assert checks["has_final_video_schema"]["ok"] is False
    assert checks["has_embedded_ppt_video"]["ok"] is False
    assert smoke.all_success_checks_passed(checks) is False


def test_t075_success_checks_allow_placeholder_structure_when_requested():
    smoke = load_script_module()
    evidence = {
        "generated_image_paths": [],
        "clip_download_paths": [],
        "final_video_path": {"api_path": "outputs/final_video.mp4", "local_path": "final_video.mp4", "bytes": 56},
        "ppt_path": {"api_path": "exports/demo.pptx", "local_path": "demo.pptx", "bytes": 78},
    }

    strict_checks = smoke.evaluate_success_checks(evidence, allow_placeholder_media=False)
    placeholder_checks = smoke.evaluate_success_checks(evidence, allow_placeholder_media=True)

    assert strict_checks["has_real_image"]["ok"] is False
    assert strict_checks["has_real_video_clip"]["ok"] is False
    assert smoke.all_success_checks_passed(strict_checks) is False
    assert placeholder_checks["has_real_image"]["ok"] is True
    assert placeholder_checks["has_real_video_clip"]["ok"] is True
    assert smoke.all_success_checks_passed(placeholder_checks) is True


def test_t075_provider_error_summary_keeps_http_status_and_code():
    smoke = load_script_module()
    calls = [
        {"step": "health", "method": "GET", "path": "/health", "http_status": 200, "body_excerpt": "{}"},
        {
            "step": "intro_video_asset_generate",
            "method": "POST",
            "path": "/projects/p1/nodes/intro_video_asset/generate",
            "http_status": 502,
            "body_excerpt": '{"ok":false,"error":{"code":"IMAGE_RESPONSE_INVALID","message":"token: samplecredential123456"}}',
        },
    ]

    summary = smoke.build_provider_error_summary(calls, "intro_video_asset_generate", "failed token: samplecredential123456")

    assert summary["failed_step"] == "intro_video_asset_generate"
    assert summary["last_error"]["http_status"] == 502
    assert summary["last_error"]["error_code"] == "IMAGE_RESPONSE_INVALID"
    assert "samplecredential123456" not in summary["last_error"]["body_excerpt"]
    assert "samplecredential123456" not in summary["failure"]


def test_t075_sanitize_for_evidence_recursively_masks_strings():
    smoke = load_script_module()

    sanitized = smoke.sanitize_for_evidence(
        {
            "nested": [
                {
                    "response_excerpt": "Authorization: Bearer fake-token",
                    "safe": "outputs/final_video.mp4",
                }
            ]
        }
    )

    assert sanitized["nested"][0]["safe"] == "outputs/final_video.mp4"
    assert "samplecredential1234567890" not in sanitized["nested"][0]["response_excerpt"]


def test_t075_parse_args_records_real_tts_and_partial_asset_defaults(monkeypatch):
    smoke = load_script_module()
    monkeypatch.setattr(sys, "argv", ["t075_real_fullchain_smoke.py"])

    args = smoke.parse_args()

    assert args.tts_provider_mode == "real"
    assert args.min_successful_images == 1
    assert args.allow_partial_assets is True
    assert args.image_limit == 1
    assert args.image_quality == "low"
    assert args.video_shot_limit == 1


def test_t075_parse_args_uses_video_model_environment_default(monkeypatch):
    smoke = load_script_module()
    monkeypatch.setenv("VIDEO_MODEL", "sora-2-12s")
    monkeypatch.setattr(sys, "argv", ["t075_real_fullchain_smoke.py"])

    args = smoke.parse_args()

    assert args.video_model == "sora-2-12s"


def test_t075_parse_args_cli_video_model_overrides_environment(monkeypatch):
    smoke = load_script_module()
    monkeypatch.setenv("VIDEO_MODEL", "sora-2-12s")
    monkeypatch.setattr(sys, "argv", ["t075_real_fullchain_smoke.py", "--video-model", "veo_3_1-fast"])

    args = smoke.parse_args()

    assert args.video_model == "veo_3_1-fast"


def test_t075_build_node_generate_body_passes_partial_asset_controls():
    smoke = load_script_module()

    class Args:
        image_size = "1024x1024"
        image_limit = 1
        image_quality = "low"
        min_successful_images = 1
        allow_partial_assets = True

    assert smoke.build_node_generate_body("intro_video_asset", Args()) == {
        "image_size": "1024x1024",
        "image_limit": 1,
        "image_quality": "low",
        "min_successful_images": 1,
        "allow_partial_assets": True,
    }
    assert smoke.build_node_generate_body("storyboard", Args()) == {}


def test_t075_real_chain_generates_shared_visual_context_before_video_branch():
    smoke = load_script_module()

    assert smoke.SHARED_CONTEXT_NODE_CHAIN == ["visual_contract", "character_dict"]
    assert smoke.VIDEO_NODE_CHAIN == [
        "intro_video_script",
        "intro_video_screenplay",
        "intro_video_asset",
        "storyboard",
    ]
    assert smoke.PPT_NODE_CHAIN == ["ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset", "pptx_artifact"]


def test_t075_create_project_payload_seeds_visual_and_character_context():
    smoke = load_script_module()

    payload = smoke.build_project_create_payload("T075 real demo", "20260623-210000")

    assert payload["character_profile"]
    assert "真人" in payload["character_safety_rule"]
    assert "#0F766E" in payload["visual_palette"]
    assert payload["visual_style_keywords"]
    assert payload["font_preference"]


def test_t075_skips_generate_when_node_already_approved(tmp_path: Path):
    smoke = load_script_module()

    class Client:
        def __init__(self):
            self.calls: list[tuple[str, str, str]] = []

        def request_json(self, step: str, method: str, path: str, json_body=None):
            self.calls.append((step, method, path))
            if step == "visual_contract_get_before_generate":
                return {"node_id": "visual_contract", "status": "approved", "content": {"palette": ["#0F766E"]}}
            raise AssertionError(f"unexpected call: {step}")

    evidence = {"node_results": {}}
    writer = smoke.EvidenceWriter(tmp_path, evidence)
    current = smoke.generate_and_approve_if_needed(Client(), writer, "p1", "visual_contract")

    assert current["status"] == "approved"
    assert evidence["node_results"]["visual_contract"]["node_id"] == "visual_contract"


def test_t075_build_final_video_generate_body_passes_quota_safe_limit():
    smoke = load_script_module()

    class Args:
        video_model = "omni_flash-10s"
        video_size = "1280x720"
        video_mode = "reference"
        video_shot_limit = 1

    assert smoke.build_final_video_generate_body(Args()) == {
        "model": "omni_flash-10s",
        "size": "1280x720",
        "mode": "reference",
        "full_run": True,
        "video_shot_limit": 1,
    }


def test_t075_probe_media_counts_audio_and_video_streams(monkeypatch, tmp_path: Path):
    smoke = load_script_module()
    media_path = tmp_path / "final_video.mp4"
    media_path.write_bytes(b"fake")

    def fake_run(*args: Any, **kwargs: Any):
        return SimpleNamespace(
            returncode=0,
            stdout='{"streams":[{"codec_type":"video","codec_name":"h264"},{"codec_type":"audio","codec_name":"mp3"}]}',
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)

    result = smoke.probe_media(media_path)

    assert result == {
        "ok": True,
        "audio_stream_count": 1,
        "video_stream_count": 1,
        "audio_codecs": ["mp3"],
    }


def test_t075_collect_final_video_node_content_records_sanitized_content():
    smoke = load_script_module()

    class Client:
        def request_json(self, step: str, method: str, path: str):
            assert step == "final_video_get"
            assert method == "GET"
            assert path == "/projects/p1/nodes/final_video"
            return {
                "node_id": "final_video",
                "status": "completed",
                "content": {
                    "video_path": "outputs/final_video.mp4",
                    "narration_audio_path": "audio/narration.mp3",
                    "response_excerpt": "Authorization: Bearer fake-token",
                },
            }

    evidence = {"node_results": {}}

    smoke.collect_final_video_node_content(Client(), evidence, "p1")

    assert evidence["node_results"]["final_video"]["node_id"] == "final_video"
    assert evidence["final_video_node_content"]["video_path"] == "outputs/final_video.mp4"
    assert "samplecredential1234567890" not in evidence["final_video_node_content"]["response_excerpt"]


def test_t075_evidence_writer_flushes_video_provider_readiness_file(tmp_path: Path):
    smoke = load_script_module()
    evidence = {
        "video_provider_readiness": {
            "ok": False,
            "checks": {"OCTO_API_KEY": {"present": True, "value": "<redacted>"}},
            "blocking_issues": ["VIDEO_QUOTA_EXHAUSTED"],
            "next_action": "restore_video_provider_quota_or_switch_account_pool",
        }
    }

    smoke.EvidenceWriter(tmp_path, evidence).flush()

    readiness_path = tmp_path / "video-provider-readiness.json"
    assert readiness_path.exists()
    payload = json.loads(readiness_path.read_text(encoding="utf-8"))
    assert payload["blocking_issues"] == ["VIDEO_QUOTA_EXHAUSTED"]
    assert payload["checks"]["OCTO_API_KEY"]["value"] == "<redacted>"


def test_t075_sync_video_tasks_fails_before_final_download_when_all_real_clips_fail(tmp_path: Path):
    smoke = load_script_module()
    failed_task = {
        "task_id": "task_failed",
        "status": "failed",
        "task_type": "video_clip_generation",
        "error_code": "VIDEO_QUOTA_EXHAUSTED",
        "retryable": False,
        "result": {
            "download_path": "clips/shot_01.mp4",
            "error_message": "RESOURCE_EXHAUSTED",
            "error_code": "VIDEO_QUOTA_EXHAUSTED",
            "retryable": False,
        },
        "error_message": "RESOURCE_EXHAUSTED",
    }

    class Client:
        def request_json(self, step: str, method: str, path: str):
            if step == "sync_video_task":
                return failed_task
            if step == "tasks_during_video_sync":
                return [failed_task]
            raise AssertionError(step)

    evidence = {"tasks": [], "video_task_paths": []}
    writer = smoke.EvidenceWriter(tmp_path, evidence)

    try:
        smoke.sync_video_tasks(
            Client(),
            writer,
            "p1",
            [{"task_id": "task_failed"}],
            timeout_sec=1,
            poll_interval_sec=0,
            allow_placeholder_media=False,
        )
    except smoke.SmokeStepError as exc:
        assert exc.step == "sync_video_tasks"
        assert "video tasks failed" in str(exc)
    else:
        raise AssertionError("expected sync_video_tasks to fail")

    assert evidence["tasks"] == [failed_task]
    assert evidence["video_task_paths"][0]["status"] == "failed"
    assert evidence["video_provider_readiness"]["ok"] is False
    assert evidence["video_provider_readiness"]["blocking_issues"] == ["VIDEO_QUOTA_EXHAUSTED"]
    assert evidence["video_provider_readiness"]["next_action"] == "restore_video_provider_quota_or_switch_account_pool"
