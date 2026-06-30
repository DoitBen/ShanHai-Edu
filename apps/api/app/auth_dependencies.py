from typing import Any, Callable

from fastapi import Depends, HTTPException, Request

from .auth_store import AuthStore
from .security import assert_request_origin_allowed, verify_csrf_token
from .settings import Settings
from .store import ProjectStore


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def raise_project_not_found() -> None:
    raise HTTPException(
        status_code=404,
        detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"},
    )


def require_current_user(request: Request) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    auth_service = request.app.state.auth_service
    session_token = request.cookies.get(settings.auth_cookie_name)
    session, user = auth_service.session_from_token(session_token)
    _verify_csrf_for_unsafe_request(request, settings, session)
    return user


def require_role(*roles: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    allowed = set(roles)

    def dependency(current_user: dict[str, Any] = Depends(require_current_user)) -> dict[str, Any]:
        if str(current_user.get("role")) not in allowed:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "无权访问该资源"},
            )
        return current_user

    return dependency


def require_project_access(
    project_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> dict[str, Any]:
    store: ProjectStore = request.app.state.store
    auth_store: AuthStore = request.app.state.auth_store
    try:
        project = store.get_project(project_id)
    except KeyError:
        raise_project_not_found()
    if not _project_access_allowed(project, current_user, auth_store):
        _record_project_denied(request, current_user, project_id)
        raise_project_not_found()
    return project


def filter_projects_for_user(
    projects: list[dict[str, Any]],
    current_user: dict[str, Any],
    auth_store: AuthStore,
) -> list[dict[str, Any]]:
    return [
        project
        for project in projects
        if _project_access_allowed(project, current_user, auth_store)
    ]


def _verify_csrf_for_unsafe_request(
    request: Request,
    settings: Settings,
    session: dict[str, Any],
) -> None:
    if request.method.upper() in SAFE_METHODS:
        return
    assert_request_origin_allowed(request.headers.get("origin"), settings.cors_origin_list)
    verify_csrf_token(request.headers.get("x-csrf-token"), str(session["csrf_token_hash"]))


def _project_access_allowed(
    project: dict[str, Any],
    current_user: dict[str, Any],
    auth_store: AuthStore,
) -> bool:
    owner_id = str(project.get("owner_id") or "").strip()
    if not owner_id:
        return False
    owner = auth_store.get_user_by_id(owner_id)
    if not owner:
        return False
    role = str(current_user.get("role") or "")
    if role == "admin":
        return True
    return role == "teacher" and owner_id == str(current_user.get("user_id") or "")


def _record_project_denied(request: Request, current_user: dict[str, Any], project_id: str) -> None:
    try:
        request.app.state.auth_store.record_audit_event(
            event_type="project.access",
            result="denied",
            actor_user_id=str(current_user.get("user_id") or "") or None,
            target_type="project",
            target_id=project_id,
            metadata={"reason": "project_not_found_or_forbidden"},
        )
    except Exception:
        return
