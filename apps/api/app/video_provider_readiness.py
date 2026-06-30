from __future__ import annotations

from typing import Any, Mapping


PUBLIC_VIDEO_DEFAULT_MODEL = "omni_flash-10s"


def build_video_provider_readiness_report(
    *,
    env: Mapping[str, str | None],
    require_real: bool = False,
    provider_error_code: str | None = None,
    api_alive: bool | None = None,
    web_alive: bool | None = None,
    live_smoke_executed: bool | None = None,
) -> dict[str, Any]:
    video_mode = (env.get("VIDEO_PROVIDER_MODE") or "placeholder").strip() or "placeholder"
    checks = {
        "VIDEO_PROVIDER_MODE": _public_check(video_mode),
        "OCTO_API_KEY": _secret_check(env.get("OCTO_API_KEY")),
        "OCTO_BASE_URL": _public_check(env.get("OCTO_BASE_URL") or "https://otuapi.com"),
        "OCTO_VIDEO_PROVIDER": _public_check(env.get("OCTO_VIDEO_PROVIDER") or "octo"),
        "VIDEO_MODEL": _public_check(
            env.get("VIDEO_MODEL")
            or env.get("OMNI_DEFAULT_MODEL")
            or env.get("NEWAPI_DEFAULT_MODEL")
            or PUBLIC_VIDEO_DEFAULT_MODEL
        ),
    }
    blocking_issues: list[str] = []
    if require_real and video_mode != "real":
        blocking_issues.append("VIDEO_PROVIDER_MODE")
    if video_mode == "real" and not checks["OCTO_API_KEY"]["present"]:
        blocking_issues.append("OCTO_API_KEY")
    if provider_error_code == "VIDEO_QUOTA_EXHAUSTED":
        blocking_issues.append("VIDEO_QUOTA_EXHAUSTED")
    next_action = "ready_for_single_clip_real_smoke"
    if "VIDEO_QUOTA_EXHAUSTED" in blocking_issues:
        next_action = "restore_video_provider_quota_or_switch_account_pool"
    elif blocking_issues:
        next_action = "fix_video_provider_configuration"
    return {
        "ok": not blocking_issues,
        "provider": "octo",
        "checks": checks,
        "runtime": {
            "api_alive": api_alive,
            "web_alive": web_alive,
            "live_smoke_executed": live_smoke_executed,
        },
        "blocking_issues": blocking_issues,
        "next_action": next_action,
    }


def _secret_check(value: str | None) -> dict[str, Any]:
    return {"present": bool(value), "value": "<redacted>" if value else None}


def _public_check(value: str | None) -> dict[str, Any]:
    return {"present": bool(value), "value": value if value else None}
