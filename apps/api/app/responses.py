from fastapi.responses import JSONResponse


def ok(data):
    return {"ok": True, "data": data}


def fail(status_code: int, code: str, message: str, retryable: bool = False, details=None):
    error = {
        "code": code,
        "message": message,
        "retryable": retryable,
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
