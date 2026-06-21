# Backend Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current local MVP backend into a safer, recoverable, testable backend that can run real Minimax and OTU/NewAPI video workflows without exposing keys, accepting unsafe uploads, or corrupting workflow state.

**Architecture:** Keep the current FastAPI + SQLite + filesystem MVP shape, but add safety boundaries before expanding capability. First close external exposure risks, then make workflow state truthful, then introduce task-worker style execution and deployment reproducibility.

**Tech Stack:** FastAPI, Pydantic, SQLite, filesystem storage, pytest, JSON Schema, ffmpeg/ffprobe, OTU/NewAPI video provider, Minimax M3 text provider.

---

## Scope And Priority

### P0 Must Fix Before Any Public Or Shared Network Run

1. Backend API token authentication for project/task/asset mutation and read APIs.
2. CORS allowlist from environment.
3. Upload limits, extension validation, server-generated filenames, and failure cleanup.
4. Error response sanitization and provider error mapping.

### P1 Must Fix Before Full Real Video Runs

1. Real task retry and truthful clip/task status.
2. Downstream node invalidation when upstream content changes.
3. Full JSON Schema validation for LLM and human edited node content.
4. Safer download handling already started: keep browser-compatible direct URL download headers and add tests around it.

### P2 Production Hardening

1. Background task runner so submit/query/download do not block request handlers.
2. SQLite migrations, indexes, and optional global project registry.
3. Final video compose with TTS, mute, concat, audio verification.
4. pyproject, Dockerfile, health/readiness split, structured logs.

## Files To Touch

- Modify: `apps/api/app/settings.py`  
  Add `backend_api_token`, `cors_origins`, upload limits, and environment parsing helpers.
- Create: `apps/api/app/security.py`  
  Central API-token dependency and request id helper.
- Modify: `apps/api/app/main.py`  
  Add route dependencies, CORS allowlist, sanitized exception handling, real task retry route.
- Modify: `apps/api/app/store.py`  
  Add upload validation, server-side filenames, indexes/migration hook, downstream invalidation, asset metadata.
- Modify: `apps/api/app/services.py`  
  Add schema validation entry points, truthful video task state, retry implementation, and later background task entry points.
- Modify: `apps/api/app/providers.py`  
  Keep NewAPI query/download behavior; add stricter response/error normalization and safe messages.
- Create: `apps/api/app/schema_validation.py`  
  JSON Schema validation wrapper with consistent error messages.
- Create: `apps/api/app/task_worker.py`  
  P2 worker facade for submit/query/download execution.
- Create: `apps/api/app/video_compose.py`  
  P2 ffmpeg/ffprobe compose and verification utilities.
- Modify: `apps/api/.env.example`  
  Add safe placeholders for new server settings.
- Create: `apps/api/pyproject.toml`  
  Make Python dependencies reproducible.
- Create: `apps/api/Dockerfile`  
  Containerize API runtime.
- Modify: `apps/api/tests/test_mvp_api.py`  
  Add auth, upload, state invalidation, and retry API tests.
- Modify: `apps/api/tests/test_real_providers.py`  
  Keep provider behavior tests and add error mapping cases.
- Create: `apps/api/tests/test_security.py`  
  Authentication, CORS, and sanitized error tests.
- Create: `apps/api/tests/test_schema_validation.py`  
  JSON Schema validation positive and negative cases.
- Create: `apps/api/tests/test_video_compose.py`  
  P2 ffprobe/compose rule tests with mocked subprocess where needed.

## Task 1: Add Settings For Auth, CORS, Upload Limits

**Files:**
- Modify: `apps/api/app/settings.py`
- Modify: `apps/api/.env.example`
- Test: `apps/api/tests/test_security.py`

- [ ] **Step 1: Write failing settings test**

Add this to `apps/api/tests/test_security.py`:

```python
from app.settings import Settings


def test_settings_parses_backend_security_values():
    settings = Settings.from_overrides(
        {
            "backend_api_token": "dev-token",
            "cors_origins": "http://localhost:3000,http://127.0.0.1:3000",
            "max_upload_bytes": "1024",
            "allowed_textbook_suffixes": ".txt,.md",
        }
    )

    assert settings.backend_api_token == "dev-token"
    assert settings.cors_origin_list == ["http://localhost:3000", "http://127.0.0.1:3000"]
    assert settings.max_upload_bytes == 1024
    assert settings.allowed_textbook_suffix_set == {".txt", ".md"}
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py::test_settings_parses_backend_security_values -q
```

Expected: FAIL because `backend_api_token`, `cors_origin_list`, `max_upload_bytes`, or `allowed_textbook_suffix_set` does not exist.

- [ ] **Step 3: Implement settings fields**

In `apps/api/app/settings.py`, add fields:

```python
backend_api_token: str | None = Field(default=None)
cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
max_upload_bytes: int = Field(default=20 * 1024 * 1024)
allowed_textbook_suffixes: str = Field(default=".txt,.md,.pdf")
```

Add properties:

```python
@property
def cors_origin_list(self) -> list[str]:
    return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

@property
def allowed_textbook_suffix_set(self) -> set[str]:
    return {item.strip().lower() for item in self.allowed_textbook_suffixes.split(",") if item.strip()}
```

Add to `from_overrides()` values:

```python
"backend_api_token": env.get("BACKEND_API_TOKEN", os.getenv("BACKEND_API_TOKEN")),
"cors_origins": env.get("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")),
"max_upload_bytes": env.get("MAX_UPLOAD_BYTES", os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024))),
"allowed_textbook_suffixes": env.get("ALLOWED_TEXTBOOK_SUFFIXES", os.getenv("ALLOWED_TEXTBOOK_SUFFIXES", ".txt,.md,.pdf")),
```

Update `apps/api/.env.example`:

```env
BACKEND_API_TOKEN=
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MAX_UPLOAD_BYTES=20971520
ALLOWED_TEXTBOOK_SUFFIXES=.txt,.md,.pdf
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py::test_settings_parses_backend_security_values -q
```

Expected: PASS.

## Task 2: Add Backend API Token Authentication

**Files:**
- Create: `apps/api/app/security.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_security.py`

- [ ] **Step 1: Write failing auth tests**

Add:

```python
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import create_app


def secure_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            {
                "storage_root": str(tmp_path / "storage"),
                "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
                "provider_mode": "fake",
                "backend_api_token": "dev-token",
            }
        )
    )


def test_project_api_requires_token_when_configured(tmp_path: Path):
    client = secure_client(tmp_path)

    response = client.get("/projects")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_project_api_accepts_valid_token(tmp_path: Path):
    client = secure_client(tmp_path)

    response = client.get("/projects", headers={"Authorization": "Bearer dev-token"})

    assert response.status_code == 200
    assert response.json()["ok"] is True
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py::test_project_api_requires_token_when_configured apps\api\tests\test_security.py::test_project_api_accepts_valid_token -q
```

Expected: first test fails because endpoint is open.

- [ ] **Step 3: Implement `security.py`**

Create `apps/api/app/security.py`:

```python
import secrets
from collections.abc import Callable

from fastapi import Header

from .responses import fail
from .settings import Settings


PUBLIC_PATHS = {"/health", "/healthz", "/readyz", "/workflow", "/video/capabilities"}


def auth_dependency(settings: Settings) -> Callable:
    def require_api_token(authorization: str | None = Header(default=None)):
        if not settings.backend_api_token:
            return None
        if not authorization or not authorization.startswith("Bearer "):
            return fail(401, "UNAUTHORIZED", "未授权访问", retryable=False)
        token = authorization.removeprefix("Bearer ").strip()
        if not secrets.compare_digest(token, settings.backend_api_token):
            return fail(403, "FORBIDDEN", "无权访问该资源", retryable=False)
        return None

    return require_api_token
```

Implementation note: if returning `JSONResponse` from dependency is awkward in FastAPI, use `HTTPException` and add an exception handler that maps it to the unified response format. The final response must still be:

```json
{"ok": false, "error": {"code": "UNAUTHORIZED", "message": "未授权访问", "retryable": false}}
```

- [ ] **Step 4: Wire dependencies into protected routes**

In `apps/api/app/main.py`, define:

```python
from fastapi import Depends
from .security import auth_dependency
```

Inside `create_app()`:

```python
require_api_token = auth_dependency(settings)
protected = [Depends(require_api_token)]
```

Apply to project/task/asset/schema routes:

```python
@app.get("/projects", dependencies=protected)
@app.post("/projects", dependencies=protected)
@app.get("/projects/{project_id}", dependencies=protected)
...
```

Keep `/health`, `/workflow`, and `/video/capabilities` public for local readiness and UI model metadata unless the chief architect later decides otherwise.

- [ ] **Step 5: Run auth tests**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py -q
```

Expected: PASS.

## Task 3: Restrict CORS To Configured Origins

**Files:**
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_security.py`

- [ ] **Step 1: Write failing CORS test**

Add:

```python
def test_cors_uses_configured_allowlist(tmp_path: Path):
    client = TestClient(
        create_app(
            {
                "storage_root": str(tmp_path / "storage"),
                "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
                "cors_origins": "http://allowed.local",
            }
        )
    )

    allowed = client.options(
        "/projects",
        headers={
            "Origin": "http://allowed.local",
            "Access-Control-Request-Method": "GET",
        },
    )
    blocked = client.options(
        "/projects",
        headers={
            "Origin": "http://blocked.local",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://allowed.local"
    assert blocked.headers.get("access-control-allow-origin") is None
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py::test_cors_uses_configured_allowlist -q
```

Expected: FAIL because current middleware allows all origins.

- [ ] **Step 3: Implement CORS allowlist**

In `apps/api/app/main.py`, replace:

```python
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

with:

```python
allow_origins=settings.cors_origin_list,
allow_credentials=False,
allow_methods=["GET", "POST", "OPTIONS"],
allow_headers=["Authorization", "Content-Type"],
```

- [ ] **Step 4: Run security tests**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py -q
```

Expected: PASS.

## Task 4: Harden Textbook Upload

**Files:**
- Modify: `apps/api/app/store.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_mvp_api.py`

- [ ] **Step 1: Write failing upload tests**

Add tests:

```python
def test_textbook_upload_rejects_unsupported_suffix(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json={
        "name": "上传限制",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }))

    response = client.post(
        f"/projects/{project['project_id']}/textbook",
        files={"file": ("bad.exe", b"not a textbook", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UPLOAD_INVALID"


def test_textbook_upload_uses_server_generated_filename(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json={
        "name": "安全文件名",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }))

    uploaded = unwrap(client.post(
        f"/projects/{project['project_id']}/textbook",
        files={"file": ("same.txt", "教材内容", "text/plain")},
    ))

    assert uploaded["filename"] == "same.txt"
    assert uploaded["path"].startswith("uploads/textbook_")
    assert uploaded["path"].endswith(".txt")
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_mvp_api.py::test_textbook_upload_rejects_unsupported_suffix apps\api\tests\test_mvp_api.py::test_textbook_upload_uses_server_generated_filename -q
```

Expected: FAIL because current upload accepts any suffix and preserves filename.

- [ ] **Step 3: Change store upload signature**

Change:

```python
def upload_textbook(self, project_id: str, file: UploadFile) -> dict[str, Any]:
```

to:

```python
def upload_textbook(self, project_id: str, file: UploadFile, *, allowed_suffixes: set[str], max_bytes: int) -> dict[str, Any]:
```

Implement chunked writing:

```python
original_name = Path(file.filename or "textbook.txt").name
suffix = Path(original_name).suffix.lower()
if suffix not in allowed_suffixes:
    raise ValueError(f"Unsupported textbook suffix: {suffix}")

safe_name = f"textbook_{uuid.uuid4().hex}{suffix}"
target = project_dir / "uploads" / safe_name
written = 0
try:
    with target.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                raise ValueError("Textbook file is too large")
            out.write(chunk)
except Exception:
    target.unlink(missing_ok=True)
    raise
```

Return both:

```python
return {**asset, "filename": original_name, "status": "uploaded"}
```

- [ ] **Step 4: Pass settings from route**

In `main.py`:

```python
return ok(
    store.upload_textbook(
        project_id,
        file,
        allowed_suffixes=settings.allowed_textbook_suffix_set,
        max_bytes=settings.max_upload_bytes,
    )
)
```

Catch `ValueError` and return:

```python
return fail(400, "UPLOAD_INVALID", "教材文件不符合上传要求", retryable=False)
```

- [ ] **Step 5: Run upload tests and full API tests**

Run:

```powershell
python -m pytest apps\api\tests\test_mvp_api.py -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 5: Sanitize Error Responses

**Files:**
- Modify: `apps/api/app/responses.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_security.py`

- [ ] **Step 1: Write failing sanitized error test**

Add:

```python
def test_provider_error_response_does_not_leak_internal_detail(tmp_path: Path):
    client = TestClient(
        create_app(
            {
                "storage_root": str(tmp_path / "storage"),
                "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
                "provider_mode": "minimax",
                "minmax_api_key": None,
            }
        )
    )

    project = client.post("/projects", json={
        "name": "错误脱敏",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }).json()["data"]

    response = client.post(f"/projects/{project['project_id']}/nodes/textbook_parse/generate")

    assert response.status_code in {400, 502}
    message = response.json()["error"]["message"]
    assert "MINMAX_API_KEY" not in message
    assert "Traceback" not in message
```

- [ ] **Step 2: Run and verify current behavior**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py::test_provider_error_response_does_not_leak_internal_detail -q
```

Expected: FAIL if raw provider message leaks variable names or internal details.

- [ ] **Step 3: Add safe error catalog**

In `responses.py`:

```python
SAFE_ERROR_MESSAGES = {
    "MINIMAX_KEY_MISSING": "文本生成服务未配置",
    "MINIMAX_BASE_URL_MISSING": "文本生成服务地址未配置",
    "OCTO_KEY_MISSING": "视频生成服务未配置",
    "OCTO_REQUEST_FAILED": "视频生成服务请求失败",
    "OCTO_DOWNLOAD_FAILED": "视频下载失败，可稍后重试",
    "GENERATION_INPUT_INVALID": "生成输入不符合要求",
}


def safe_message(code: str, fallback: str) -> str:
    return SAFE_ERROR_MESSAGES.get(code, fallback)
```

In route exception handlers, use:

```python
return fail(502, exc.code, safe_message(exc.code, "外部生成服务调用失败"), retryable=exc.retryable)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest apps\api\tests\test_security.py -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 6: Implement Full JSON Schema Validation

**Files:**
- Create: `apps/api/app/schema_validation.py`
- Modify: `apps/api/app/providers.py`
- Modify: `apps/api/app/services.py`
- Test: `apps/api/tests/test_schema_validation.py`
- Modify: `apps/api/pyproject.toml` or dependency docs when dependency file exists

- [ ] **Step 1: Write failing validator tests**

Create `apps/api/tests/test_schema_validation.py`:

```python
import pytest

from app.schema_validation import SchemaValidationError, validate_json_schema


def test_validate_json_schema_rejects_wrong_type():
    schema = {
        "type": "object",
        "required": ["shots"],
        "properties": {
            "shots": {"type": "array"},
        },
    }

    with pytest.raises(SchemaValidationError) as exc:
        validate_json_schema({"shots": "not-array"}, schema)

    assert "shots" in str(exc.value)


def test_validate_json_schema_accepts_valid_content():
    schema = {
        "type": "object",
        "required": ["shots"],
        "properties": {
            "shots": {"type": "array"},
        },
    }

    validate_json_schema({"shots": []}, schema)
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_schema_validation.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement validator**

Create `apps/api/app/schema_validation.py`:

```python
from typing import Any

from jsonschema import Draft202012Validator


class SchemaValidationError(ValueError):
    pass


def validate_json_schema(content: dict[str, Any], schema: dict[str, Any]) -> None:
    if not schema:
        return
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(content), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise SchemaValidationError(f"{path}: {first.message}")
```

- [ ] **Step 4: Replace provider required-only validation**

In `providers.py`, replace `validate_required_fields(parsed, schema)` with:

```python
from .schema_validation import validate_json_schema
...
validate_json_schema(parsed, schema)
```

Keep `validate_required_fields` only if tests still need it; otherwise remove it after updating imports.

- [ ] **Step 5: Validate human edit content**

In `services.py` inside `edit_node()`:

```python
schema = self._schema_for_node(node_id)
validate_json_schema(content, schema)
return self.store.write_version(...)
```

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m pytest apps\api\tests\test_schema_validation.py -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 7: Downstream Invalidation On Upstream Change

**Files:**
- Modify: `apps/api/app/store.py`
- Modify: `apps/api/app/workflow_config.py` if helper belongs there
- Test: `apps/api/tests/test_mvp_api.py`

- [ ] **Step 1: Write failing invalidation test**

Add:

```python
def test_editing_approved_upstream_invalidates_downstream(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json={
        "name": "下游降级",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }))
    project_id = project["project_id"]
    client.post(f"/projects/{project_id}/textbook", files={
        "file": ("textbook.txt", "三年级数学，分数的初步认识。", "text/plain")
    })

    for node_id in ["textbook_parse", "lesson_plan", "intro_selection", "intro_video_script"]:
        unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/generate"))
        unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/approve"))

    unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/edit", json={
        "content": {
            "textbook_anchor": "新教案",
            "teaching_objectives": "新目标",
            "key_difficulty": "新重难点",
            "teaching_flow": "新流程",
            "blackboard_design": "新板书",
            "intro_designs": [],
        }
    }))

    manifest = unwrap(client.get(f"/projects/{project_id}/manifest"))
    states = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert states["lesson_plan"] == "needs_review"
    assert states["intro_selection"] == "needs_review"
    assert states["intro_video_script"] == "needs_review"
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_mvp_api.py::test_editing_approved_upstream_invalidates_downstream -q
```

Expected: FAIL because downstream remains approved.

- [ ] **Step 3: Implement reverse dependency traversal**

In `store.py`, add:

```python
def downstream_nodes(node_id: str) -> list[str]:
    reverse: dict[str, list[str]] = {}
    for child, deps in MVP_DEPENDENCIES.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(child)
    seen = set()
    ordered = []
    stack = list(reverse.get(node_id, []))
    while stack:
        current = stack.pop(0)
        if current in seen:
            continue
        seen.add(current)
        ordered.append(current)
        stack.extend(reverse.get(current, []))
    return ordered
```

Change `write_version()` after updating current node:

```python
for downstream in downstream_nodes(node_id):
    conn.execute(
        """
        UPDATE node_state
        SET status = ?, updated_at = ?
        WHERE project_id = ? AND node_id = ? AND status = ?
        """,
        ("needs_review", created_at, project_id, downstream, "approved"),
    )
    self.record_event(conn, project_id, downstream, "node_invalidated", {"changed_upstream": node_id})
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest apps\api\tests\test_mvp_api.py::test_editing_approved_upstream_invalidates_downstream -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 8: Make Final Video State Truthful

**Files:**
- Modify: `apps/api/app/services.py`
- Test: `apps/api/tests/test_mvp_api.py`

- [ ] **Step 1: Write failing task status test**

Add a provider stub test that submits real-provider-like queued tasks:

```python
def test_final_video_clips_reflect_task_status(tmp_path: Path):
    client = make_client(tmp_path)
    # Build project through storyboard using existing helper pattern from test_video_chain_creates_tasks_without_real_provider.
    # Then set provider_mode to minimax with a stub video provider returning queued.
```

Implementation detail for this task: if existing `make_client()` only creates fake provider, create a local app with fake text provider but injected stub `video_provider` before calling final_video. Expected assertion:

```python
assert video["content"]["clips"][0]["status"] in {"queued", "processing"}
assert video["tasks"][0]["status"] in {"queued", "processing"}
```

- [ ] **Step 2: Run and verify failure**

Expected: FAIL because current clip status is always `generated`.

- [ ] **Step 3: Implement truthful clip status**

In `_generate_video_tasks()`, replace:

```python
"status": "generated",
```

with:

```python
"status": task["status"],
```

Also ensure fake provider still returns `generated` for fake tasks.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 9: Implement Real Task Retry

**Files:**
- Modify: `apps/api/app/services.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_real_providers.py`

- [ ] **Step 1: Write failing retry test**

Add:

```python
def test_retry_task_resubmits_failed_video_task(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json={
        "name": "重试任务",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }))
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"model": "omni_flash-10s", "prompt": "课堂导入", "size": "1280x720"},
            status="failed",
            result={},
            error_message="remote failed",
        )

    class StubVideoProvider:
        def submit_video(self, payload):
            return {
                "provider_task_id": "task_remote_retry",
                "status": "queued",
                "progress": 0,
                "raw": {},
            }

    client.app.state.service.video_provider = StubVideoProvider()

    retried = unwrap(client.post(f"/projects/{project_id}/tasks/{task['task_id']}/retry"))

    assert retried["status"] == "queued"
    assert retried["payload"]["provider_task_id"] == "task_remote_retry"
    assert retried["error_message"] is None
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_real_providers.py::test_retry_task_resubmits_failed_video_task -q
```

Expected: FAIL because route returns fake generated status.

- [ ] **Step 3: Implement service retry**

In `services.py`:

```python
def retry_task(self, project_id: str, task_id: str) -> dict[str, Any]:
    task = self.store.task(project_id, task_id)
    if task["task_type"] != "video_clip_generation":
        raise ValueError("Task type is not retryable")
    if task["status"] not in {"failed", "completed"} and task.get("result", {}).get("download_status") != "failed":
        raise ValueError("Task is not retryable")
    if self.video_provider is None:
        raise ProviderError("VIDEO_PROVIDER_MISSING", "视频生成服务未配置", retryable=False)
    payload = dict(task["payload"])
    submitted = self.video_provider.submit_video(
        {
            "model": payload.get("model"),
            "prompt": payload.get("prompt") or payload.get("model_prompt"),
            "size": payload.get("size"),
        }
    )
    payload["provider_task_id"] = submitted["provider_task_id"]
    project = self.store.get_project(project_id)
    with self.store.connect(Path(project["project_dir"])) as conn:
        conn.execute(
            "UPDATE tasks SET payload_json = ?, error_message = NULL WHERE task_id = ?",
            (json.dumps(payload, ensure_ascii=False), task_id),
        )
        return self.store.update_task(conn, task_id, submitted["status"] or "queued", submitted, None)
```

- [ ] **Step 4: Route retry through service**

In `main.py`:

```python
return ok(service.retry_task(project_id, task_id))
```

Map `ValueError` to `409 TASK_NOT_RETRYABLE`.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest apps\api\tests\test_real_providers.py::test_retry_task_resubmits_failed_video_task -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 10: Add SQLite Migrations And Indexes

**Files:**
- Modify: `apps/api/app/store.py`
- Test: `apps/api/tests/test_mvp_api.py`

- [ ] **Step 1: Write failing migration test**

Add:

```python
def test_project_db_has_schema_migrations_and_indexes(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json={
        "name": "索引检查",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
    }))
    import sqlite3
    conn = sqlite3.connect(Path(project["project_dir"]) / "project.db")
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    conn.close()

    assert "schema_migrations" in tables
    assert "idx_tasks_project_status" in indexes
    assert "idx_versions_project_node" in indexes
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest apps\api\tests\test_mvp_api.py::test_project_db_has_schema_migrations_and_indexes -q
```

Expected: FAIL because migrations/indexes do not exist.

- [ ] **Step 3: Add migration table and indexes**

In `init_db()` SQL script add:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_versions_project_node ON node_versions(project_id, node_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assets_project_kind ON assets(project_id, kind, created_at);
CREATE INDEX IF NOT EXISTS idx_events_project_created ON events(project_id, created_at);
```

Record initial migration:

```python
conn.execute(
    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
    ("0001_initial_mvp_indexes", now_iso()),
)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 11: Introduce Background Task Facade

**Files:**
- Create: `apps/api/app/task_worker.py`
- Modify: `apps/api/app/services.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_real_providers.py`

- [ ] **Step 1: Write failing non-blocking generate test**

Add a test that final video generation creates pending local task and returns without calling remote provider immediately when `async_mode=true`.

Expected request:

```python
response = client.post(f"/projects/{project_id}/nodes/final_video/generate", json={"async_mode": True})
assert response.json()["data"]["status"] == "running"
assert response.json()["data"]["tasks"][0]["status"] == "pending"
```

- [ ] **Step 2: Implement `task_worker.py` facade**

Create:

```python
class TaskWorker:
    def __init__(self, service):
        self.service = service

    def run_video_task(self, project_id: str, task_id: str) -> None:
        self.service.submit_pending_video_task(project_id, task_id)
```

For MVP, FastAPI `BackgroundTasks` is acceptable. Later replace with durable worker.

- [ ] **Step 3: Split create vs submit**

In `services.py`, split `_generate_video_tasks()` into:

- create pending task rows
- submit pending task rows

Keep synchronous mode as default until frontend is ready.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 12: Final Video Compose Gate

**Files:**
- Create: `apps/api/app/video_compose.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/store.py`
- Test: `apps/api/tests/test_video_compose.py`

- [ ] **Step 1: Write ffprobe validation tests**

Create:

```python
from app.video_compose import can_approve_final_video


def test_final_video_requires_at_least_six_approved_clips():
    result = can_approve_final_video(
        {
            "clip_count": 1,
            "clips": [{"status": "approved"}],
            "audio_verified": True,
            "voice_gender": "male",
            "voice_language": "zh-CN",
            "english_audio_detected": False,
        }
    )

    assert result.ok is False
    assert result.code == "FINAL_VIDEO_TOO_FEW_CLIPS"
```

- [ ] **Step 2: Implement approval gate**

Create:

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class ComposeCheck:
    ok: bool
    code: str | None = None
    message: str | None = None


def can_approve_final_video(content: dict[str, Any]) -> ComposeCheck:
    if int(content.get("clip_count") or 0) < 6:
        return ComposeCheck(False, "FINAL_VIDEO_TOO_FEW_CLIPS", "完整视频至少需要 6 段")
    if any(clip.get("status") != "approved" for clip in content.get("clips", [])):
        return ComposeCheck(False, "FINAL_VIDEO_CLIPS_NOT_APPROVED", "存在未确认片段")
    if content.get("voice_gender") != "male" or content.get("voice_language") != "zh-CN":
        return ComposeCheck(False, "FINAL_VIDEO_VOICE_INVALID", "必须使用中文男声")
    if content.get("audio_verified") is not True:
        return ComposeCheck(False, "FINAL_VIDEO_AUDIO_NOT_VERIFIED", "音频未验证")
    if content.get("english_audio_detected") is True:
        return ComposeCheck(False, "FINAL_VIDEO_ENGLISH_AUDIO", "检测到英文音频")
    return ComposeCheck(True)
```

- [ ] **Step 3: Wire final_video approve**

In `main.py` approve route, before `store.approve_node()` when `node_id == "final_video"`:

```python
content = store.current_content(...)
check = can_approve_final_video(content or {})
if not check.ok:
    return fail(409, check.code, check.message, retryable=False)
```

- [ ] **Step 4: Add compose endpoint later**

Add endpoint:

```python
@app.post("/projects/{project_id}/nodes/final_video/compose")
def compose_final_video(project_id: str):
    return ok(service.compose_final_video(project_id))
```

Implement `compose_final_video()` only after TTS provider decision is approved by chief architect.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest apps\api\tests\test_video_compose.py -q
python -m pytest apps\api\tests -q
```

Expected: PASS.

## Task 13: Reproducible API Runtime

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/Dockerfile`
- Modify: `apps/api/README.md`

- [ ] **Step 1: Add pyproject**

Create `apps/api/pyproject.toml`:

```toml
[project]
name = "shanhai-edu-api"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic",
  "pyyaml",
  "python-multipart",
  "jsonschema",
]

[project.optional-dependencies]
test = [
  "pytest",
  "httpx",
]
```

- [ ] **Step 2: Add Dockerfile**

Create `apps/api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
RUN pip install --no-cache-dir /app/apps/api[test]

COPY apps/api /app/apps/api
COPY workflow /app/workflow
COPY docs/api-research/octo-video/capabilities.json /app/docs/api-research/octo-video/capabilities.json

ENV PYTHONPATH=/app/apps/api
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Add health/readiness routes**

In `main.py`:

```python
@app.get("/healthz")
def healthz():
    return ok({"status": "ok"})

@app.get("/readyz")
def readyz():
    return ok({"status": "ready", "workflow_version": workflow.version})
```

- [ ] **Step 4: Verify locally**

Run:

```powershell
python -m pytest apps\api\tests -q
```

Expected: PASS.

Docker build may be deferred if local Docker is unavailable; if run:

```powershell
docker build -f apps\api\Dockerfile -t shanhai-edu-api .
```

Expected: image builds.

## Global Verification Before Handoff

- [ ] Run backend tests:

```powershell
python -m pytest apps\api\tests -q
```

Expected: all tests pass.

- [ ] Run videogen local skill test:

```powershell
python -m pytest skills\videogen\tests -q
```

Expected: all tests pass.

- [ ] Run local NewAPI metadata command:

```powershell
.\scripts\videogen.ps1 otu-models
```

Expected: prints local model matrix without external project path dependency.

- [ ] Secret scan changed docs and source:

```powershell
rg -n "sk-[A-Za-z0-9_-]{10,}|Bearer [A-Za-z0-9_-]{10,}" apps\api docs scripts skills\videogen AGENTS.md
```

Expected: no real secrets. Placeholder text such as `Bearer <token>` is acceptable only in docs.

## Commit Grouping Recommendation

Use separate commits by risk area:

1. `fix: 加固后端鉴权与 CORS | v0.2.0 | 2026-06-20 HH:MM`
2. `fix: 加固教材上传与错误脱敏 | v0.2.0 | 2026-06-20 HH:MM`
3. `fix: 修正工作流状态与任务重试 | v0.2.0 | 2026-06-20 HH:MM`
4. `feat: 增加 schema 校验与数据库迁移索引 | v0.2.0 | 2026-06-20 HH:MM`
5. `feat: 增加视频合成验收门禁 | v0.2.0 | 2026-06-20 HH:MM`
6. `conf: 增加后端可复现运行配置 | v0.2.0 | 2026-06-20 HH:MM`

## Open Decisions For Chief System Architect

1. 鉴权 MVP 是否先用单一 `BACKEND_API_TOKEN`，还是立即引入用户表与项目 owner。
2. `/workflow` 和 `/schemas/{schema_name}` 是否保持公开只读，还是全部纳入鉴权。
3. 后台任务第一版使用 FastAPI `BackgroundTasks`，还是直接引入独立 worker 和 Redis/SQLite queue。
4. TTS Provider 是否继续优先 Minimax，还是先接本地可用中文男声服务。
5. Docker 目标是本机 docker-compose，还是直接按 Cloud Run 约束整理。

