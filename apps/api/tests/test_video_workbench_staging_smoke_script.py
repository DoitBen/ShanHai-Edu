from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "apps" / "api" / "scripts" / "video_workbench_staging_smoke.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("video_workbench_staging_smoke", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_video_workbench_staging_smoke_defaults_to_non_paid_mode(monkeypatch):
    smoke = load_script_module()
    monkeypatch.setattr(sys, "argv", ["video_workbench_staging_smoke.py"])

    args = smoke.parse_args()

    assert args.run_real_provider is False
    assert args.required_proxy == "/api/backend"
    assert args.env_name == "local"


def test_video_workbench_staging_smoke_redacts_sensitive_values():
    smoke = load_script_module()

    redacted = smoke.redact_sensitive(
        {
            "provider_task_id": "remote_should_not_be_saved",
            "video_url": "https://provider.example/signed.mp4?token=secret",
            "nested": ["Authorization: Bearer should-not-leak", "octo-secretvalue123456"],
            "safe": "completed",
        }
    )

    assert redacted["provider_task_id"] == "<redacted>"
    assert redacted["video_url"] == "<redacted>"
    assert redacted["safe"] == "completed"
    assert "should-not-leak" not in str(redacted)
    assert "secretvalue123456" not in str(redacted)


def test_video_workbench_staging_smoke_report_contains_only_sanitized_run_fields():
    smoke = load_script_module()
    report = smoke.render_markdown_report(
        {
            "status": "passed",
            "mode": "fake_provider",
            "started_at": "2026-06-29T00:00:00+00:00",
            "completed_at": "2026-06-29T00:01:00+00:00",
            "runs": [
                {
                    "scenario": "OMNI_TEXT_TO_VIDEO",
                    "run_id": "task_safe",
                    "status": "completed",
                    "reference_count": 0,
                    "download": {"byte_size": 32},
                }
            ],
        },
        "local-fake",
    )

    assert "task_safe" in report
    assert "provider_task_id" not in report
    assert "Authorization" not in report
