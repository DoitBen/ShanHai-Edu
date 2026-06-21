import secrets

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

