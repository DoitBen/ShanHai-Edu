from __future__ import annotations

import json

from app.video_provider_readiness import build_video_provider_readiness_report
from app.main import create_app
from fastapi.testclient import TestClient


def test_video_provider_readiness_report_redacts_secret_values():
    report = build_video_provider_readiness_report(
        env={
            "VIDEO_PROVIDER_MODE": "real",
            "OCTO_API_KEY": "sk-test-secret-value",
            "OCTO_BASE_URL": "https://otuapi.com",
            "OCTO_VIDEO_PROVIDER": "octo",
        },
        require_real=True,
    )
    serialized = json.dumps(report, ensure_ascii=False)

    assert report["ok"] is True
    assert report["checks"]["OCTO_API_KEY"]["present"] is True
    assert report["checks"]["OCTO_API_KEY"]["value"] == "<redacted>"
    assert "sk-test-secret-value" not in serialized
    assert report["checks"]["OCTO_BASE_URL"]["value"] == "https://otuapi.com"


def test_video_provider_readiness_report_blocks_real_mode_without_key():
    report = build_video_provider_readiness_report(
        env={
            "VIDEO_PROVIDER_MODE": "real",
            "OCTO_BASE_URL": "https://otuapi.com",
        },
        require_real=True,
    )

    assert report["ok"] is False
    assert report["checks"]["OCTO_API_KEY"]["present"] is False
    assert "OCTO_API_KEY" in report["blocking_issues"]


def test_video_provider_readiness_report_notes_quota_error_as_ops_blocker():
    report = build_video_provider_readiness_report(
        env={
            "VIDEO_PROVIDER_MODE": "real",
            "OCTO_API_KEY": "sk-test-secret-value",
            "OCTO_BASE_URL": "https://otuapi.com",
        },
        provider_error_code="VIDEO_QUOTA_EXHAUSTED",
        require_real=True,
    )

    assert report["ok"] is False
    assert "VIDEO_QUOTA_EXHAUSTED" in report["blocking_issues"]
    assert report["next_action"] == "restore_video_provider_quota_or_switch_account_pool"


def test_readiness_endpoint_returns_runtime_checks_without_secrets(tmp_path):
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": "workflow",
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
        }
    )
    payload = TestClient(app).get("/readiness")

    assert payload.status_code == 200, payload.text
    data = payload.json()["data"]
    assert data["ok"] is True
    assert data["runtime"]["api_alive"] is True
    assert data["runtime"]["live_smoke_executed"] is False
    assert data["checks"]["OCTO_API_KEY"]["value"] is None
