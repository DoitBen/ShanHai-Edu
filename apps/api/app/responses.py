import uuid

from fastapi.responses import JSONResponse


def ok(data):
    return {"ok": True, "data": data}


def fail(
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
    details=None,
    action: str | None = None,
    trace_id: str | None = None,
):
    error = {
        "code": code,
        "message": message,
        "retryable": retryable,
        "action": action or _default_action(status_code, retryable),
        "trace_id": trace_id or f"trace_{uuid.uuid4().hex[:12]}",
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": error,
        },
    )


def _default_action(status_code: int, retryable: bool) -> str:
    if retryable:
        return "retry"
    if status_code in {401, 403}:
        return "login_or_check_permission"
    if status_code == 404:
        return "check_resource"
    if status_code == 409:
        return "resolve_conflict"
    if status_code == 422:
        return "fix_request"
    if status_code >= 500:
        return "contact_support"
    return "check_input"
