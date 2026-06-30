from typing import Any

from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel

from .auth_service import AuthService
from .responses import ok
from .security import assert_request_origin_allowed
from .settings import Settings


class LoginRequest(BaseModel):
    email: str
    password: str


def register_auth_routes(app: FastAPI, auth_service: AuthService, settings: Settings) -> None:
    @app.post("/auth/login")
    def login(payload: LoginRequest, request: Request, response: Response, origin: str | None = Header(default=None)):
        assert_request_origin_allowed(origin, settings.cors_origin_list)
        result = auth_service.login(email=payload.email, password=payload.password, request=request)
        response.set_cookie(
            settings.auth_cookie_name,
            result["session_token"],
            httponly=True,
            secure=bool(settings.auth_cookie_secure),
            samesite="Lax",
            path="/",
            max_age=int(settings.auth_session_ttl_seconds),
        )
        return ok(_auth_payload(result))

    @app.get("/auth/me")
    def me(request: Request):
        result = auth_service.me(request.cookies.get(settings.auth_cookie_name))
        return ok(result)

    @app.post("/auth/logout")
    def logout(
        request: Request,
        response: Response,
        origin: str | None = Header(default=None),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    ):
        session_token = request.cookies.get(settings.auth_cookie_name)
        session, user = auth_service.optional_session_from_token(session_token)
        if session and user:
            assert_request_origin_allowed(origin, settings.cors_origin_list)
        auth_service.logout(
            session_token=session_token,
            csrf_token=csrf_token,
        )
        response.delete_cookie(settings.auth_cookie_name, path="/", samesite="Lax")
        return ok({"logged_out": True})


def _auth_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "user": result["user"],
        "csrf_token": result["csrf_token"],
        "expires_at": result["expires_at"],
    }
