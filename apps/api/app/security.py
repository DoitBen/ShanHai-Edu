import secrets
import hashlib

from fastapi import Header, HTTPException

from .settings import Settings


def require_api_token(settings: Settings):
    def dependency(authorization: str | None = Header(default=None)) -> None:
        if not settings.backend_api_token:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "未授权访问"})
        token = authorization.removeprefix("Bearer ").strip()
        if not secrets.compare_digest(token, settings.backend_api_token):
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "无权访问该资源"})

    return dependency


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assert_request_origin_allowed(origin: str | None, allowed_origins: list[str]) -> None:
    if not origin or origin not in allowed_origins:
        raise HTTPException(
            status_code=403,
            detail={"code": "AUTH_ORIGIN_FORBIDDEN", "message": "请求来源不受信任"},
        )


def verify_csrf_token(candidate: str | None, stored_hash: str) -> None:
    if not candidate:
        raise HTTPException(
            status_code=403,
            detail={"code": "CSRF_TOKEN_REQUIRED", "message": "缺少 CSRF Token"},
        )
    candidate_hash = sha256_hex(candidate)
    if not secrets.compare_digest(candidate_hash, stored_hash):
        raise HTTPException(
            status_code=403,
            detail={"code": "CSRF_TOKEN_INVALID", "message": "CSRF Token 无效"},
        )

