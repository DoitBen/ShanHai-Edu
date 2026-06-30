from pathlib import Path
from typing import Any
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    storage_root: Path = Field(default=Path("storage"))
    workflow_root: Path = Field(default=Path("workflow"))
    capabilities_path: Path = Field(default=Path("docs/api-research/octo-video/capabilities.json"))
    provider_mode: str = Field(default="fake")
    video_provider_mode: str = Field(default="placeholder")
    video_model: str = Field(default="omni_flash-10s")
    image_provider_mode: str = Field(default="placeholder")
    tts_provider_mode: str = Field(default="placeholder")
    minmax_api_key: str | None = Field(default=None)
    minmax_base_url: str | None = Field(default=None)
    minmax_text_model: str = Field(default="M3")
    minmax_video_model: str = Field(default="minmax-video")
    minmax_tts_model: str = Field(default="speech-2.8-hd")
    minmax_tts_voice_id: str = Field(default="Chinese (Mandarin)_Gentleman")
    deepseek_api_key: str | None = Field(default=None)
    deepseek_base_url: str = Field(default="https://api.deepseek.com")
    deepseek_model: str = Field(default="deepseek-chat")
    octo_api_key: str | None = Field(default=None)
    octo_base_url: str = Field(default="https://otuapi.com")
    octo_video_provider: str = Field(default="octo")
    imagegen_api_key: str | None = Field(default=None)
    imagegen_base_url: str = Field(default="https://img.baofu.eu.cc/v1")
    imagegen_model: str = Field(default="gpt-image-2")
    backend_api_token: str | None = Field(default=None)
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    auth_cookie_name: str = Field(default="shanhai_session")
    auth_session_ttl_seconds: int = Field(default=43200)
    auth_cookie_secure: bool = Field(default=False)
    auth_login_rate_limit_max_failures: int = Field(default=5)
    auth_login_rate_limit_window_seconds: int = Field(default=900)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @classmethod
    def from_overrides(cls, overrides: dict[str, Any] | None = None) -> "Settings":
        env = _load_env_files()
        values: dict[str, Any] = {
            "storage_root": _setting_value(env, "STORAGE_ROOT", "storage"),
            "workflow_root": _setting_value(env, "WORKFLOW_ROOT", "workflow"),
            "capabilities_path": _setting_value(
                env,
                "CAPABILITIES_PATH",
                "docs/api-research/octo-video/capabilities.json",
            ),
            "provider_mode": _setting_value(env, "PROVIDER_MODE", "fake"),
            "video_provider_mode": _setting_value(env, "VIDEO_PROVIDER_MODE", "placeholder"),
            "video_model": (
                _setting_value(env, "VIDEO_MODEL")
                or _setting_value(env, "OMNI_DEFAULT_MODEL")
                or _setting_value(env, "NEWAPI_DEFAULT_MODEL")
                or "omni_flash-10s"
            ),
            "image_provider_mode": _setting_value(env, "IMAGE_PROVIDER_MODE", "placeholder"),
            "tts_provider_mode": _setting_value(env, "TTS_PROVIDER_MODE", "placeholder"),
            "minmax_api_key": _setting_value(env, "MINIMAX_API_KEY") or _setting_value(env, "MINMAX_API_KEY"),
            "minmax_base_url": _setting_value(env, "MINIMAX_BASE_URL") or _setting_value(env, "MINMAX_BASE_URL"),
            "minmax_text_model": _setting_value(env, "MINMAX_TEXT_MODEL", "M3"),
            "minmax_video_model": _setting_value(env, "MINMAX_VIDEO_MODEL", "minmax-video"),
            "minmax_tts_model": _setting_value(env, "MINIMAX_TTS_MODEL") or _setting_value(env, "MINMAX_TTS_MODEL", "speech-2.8-hd"),
            "minmax_tts_voice_id": _setting_value(env, "MINIMAX_TTS_VOICE_ID", "Chinese (Mandarin)_Gentleman"),
            "deepseek_api_key": _setting_value(env, "DEEPSEEK_API_KEY"),
            "deepseek_base_url": _setting_value(env, "DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "deepseek_model": _setting_value(env, "DEEPSEEK_MODEL", "deepseek-chat"),
            "octo_api_key": _setting_value(env, "OCTO_API_KEY"),
            "octo_base_url": _setting_value(env, "OCTO_BASE_URL", "https://otuapi.com"),
            "octo_video_provider": _setting_value(env, "OCTO_VIDEO_PROVIDER", "octo"),
            "imagegen_api_key": (
                _setting_value(env, "IMAGEGEN_MYSELF_PRIMARY_API_KEY")
                or _setting_value(env, "IMAGEGEN_MYSELF_API_KEY")
                or _setting_value(env, "NEWAPI_PRIMARY_API_KEY")
                or _setting_value(env, "IMAGEGEN_API_KEY")
                or _setting_value(env, "NEWAPI_API_KEY")
                or _setting_value(env, "PINAI_PRIMARY_API_KEY")
                or _setting_value(env, "PINAI_API_KEY")
                or _setting_value(env, "AIRCODE_PRIMARY_API_KEY")
                or _setting_value(env, "AIRCODE_API_KEY")
                or _setting_value(env, "OPENAI_API_KEY")
            ),
            "imagegen_base_url": (
                _setting_value(env, "IMAGEGEN_MYSELF_PRIMARY_BASE_URL")
                or _setting_value(env, "IMAGEGEN_MYSELF_BASE_URL")
                or _setting_value(env, "NEWAPI_PRIMARY_BASE_URL")
                or _setting_value(env, "IMAGEGEN_BASE_URL")
                or _setting_value(env, "NEWAPI_BASE_URL")
                or _setting_value(env, "PINAI_PRIMARY_BASE_URL")
                or _setting_value(env, "PINAI_BASE_URL")
                or "https://img.baofu.eu.cc/v1"
            ),
            "imagegen_model": (
                _setting_value(env, "IMAGEGEN_MYSELF_MODEL")
                or _setting_value(env, "IMAGEGEN_MODEL")
                or _setting_value(env, "NEWAPI_IMAGE_MODEL")
                or "gpt-image-2"
            ),
            "backend_api_token": _setting_value(env, "BACKEND_API_TOKEN"),
            "cors_origins": _setting_value(
                env,
                "CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            ),
            "auth_cookie_name": _setting_value(env, "AUTH_COOKIE_NAME", "shanhai_session"),
            "auth_session_ttl_seconds": int(_setting_value(env, "AUTH_SESSION_TTL_SECONDS", "43200") or "43200"),
            "auth_cookie_secure": _parse_bool(_setting_value(env, "AUTH_COOKIE_SECURE", "false")),
            "auth_login_rate_limit_max_failures": int(
                _setting_value(env, "AUTH_LOGIN_RATE_LIMIT_MAX_FAILURES", "5") or "5"
            ),
            "auth_login_rate_limit_window_seconds": int(
                _setting_value(env, "AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "900") or "900"
            ),
        }
        values.update(overrides or {})
        return cls(**values)


def _setting_value(env: dict[str, str], key: str, default: str | None = None) -> str | None:
    return os.environ[key] if key in os.environ else env.get(key, default)


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_env_files() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in [Path(".env"), Path("apps/api/.env"), Path("skills/imagegen-myself/.env.local")]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values
