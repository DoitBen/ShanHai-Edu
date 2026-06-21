from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.settings import Settings  # noqa: E402
from app.video_provider_readiness import build_video_provider_readiness_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check video provider readiness without printing secrets.")
    parser.add_argument("--require-real", action="store_true", help="Fail unless VIDEO_PROVIDER_MODE=real.")
    parser.add_argument("--provider-error-code", default=None, help="Optional latest provider error code to classify.")
    args = parser.parse_args()

    settings = Settings.from_overrides({})
    env = {
        "VIDEO_PROVIDER_MODE": settings.video_provider_mode,
        "OCTO_API_KEY": settings.octo_api_key,
        "OCTO_BASE_URL": settings.octo_base_url,
        "OCTO_VIDEO_PROVIDER": settings.octo_video_provider,
        "VIDEO_MODEL": os.environ.get("VIDEO_MODEL"),
        "OMNI_DEFAULT_MODEL": os.environ.get("OMNI_DEFAULT_MODEL"),
        "NEWAPI_DEFAULT_MODEL": os.environ.get("NEWAPI_DEFAULT_MODEL"),
    }
    report = build_video_provider_readiness_report(
        env=env,
        require_real=args.require_real,
        provider_error_code=args.provider_error_code,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
