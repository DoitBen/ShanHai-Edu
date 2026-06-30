# Google Flow Core Video Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing project-level Omni video MVP into a reliable Google Flow-style core workbench supporting ordered reference images, prompt-to-video generation, automatic progress, history, preview, download, retry, and parameter reuse.

**Architecture:** Extend `VideoWorkflowService` as the single project-level business source, keep `OctoVideoProvider` as the third-party adapter, and store immutable run snapshots in the existing project task table. Replace the decorative ReactFlow canvas with a responsive three-panel workbench backed by one Zustand project state and one polling scheduler.

**Tech Stack:** FastAPI, Python 3.11, SQLite/project task store, Pillow, pytest, Next.js 16, React 19, TypeScript, Zustand, dnd-kit, Bun, Playwright.

---

## Source of Truth

Implement against:

- `docs/superpowers/specs/2026-06-29-google-flow-core-video-workbench-design.md`
- `docs/api-research/octo-video/capabilities.json`
- `apps/api/app/video_workflow.py`
- `apps/api/app/providers.py::OctoVideoProvider`

Do not add video editing, first/last frames, voice references, multiple outputs, Extend, Remix, Agent, or Scenebuilder.

## File Map

### Backend

- Modify `apps/api/requirements.txt`: add Pillow.
- Replace most of `apps/api/app/video_workflow.py`: project assets, idempotent runs, history, retry, sync, atomic result download.
- Modify `apps/api/app/providers.py`: real MIME multipart, safer error mapping, streaming/atomic-compatible download.
- Modify `apps/api/app/main.py`: asset content/delete, run list/retry/content routes.
- Expand `apps/api/tests/test_video_workflow_canvas.py`: service and route contract.
- Expand `apps/api/tests/test_real_providers.py`: multipart and provider normalization.
- Create `scripts/video_workbench_real_smoke.py`: opt-in real Omni smoke.

### Frontend

- Modify `apps/web/src/lib/types.ts`: new config, asset and run contracts.
- Modify `apps/web/src/lib/api-client.ts`: new asset, run, retry, content APIs.
- Modify `apps/web/src/lib/store.ts`: ordered run list and immutable updates.
- Replace `apps/web/src/lib/video-workflow-contract.test.ts`: new source contract.
- Create `apps/web/src/components/video-workflow/video-workflow-utils.ts`: terminal states, ordered selection and run helpers.
- Create `apps/web/src/components/video-workflow/use-video-workflow-polling.ts`: one project poller.
- Create `apps/web/src/components/video-workflow/VideoAssetPanel.tsx`.
- Create `apps/web/src/components/video-workflow/VideoComposerPanel.tsx`.
- Create `apps/web/src/components/video-workflow/VideoRunHistoryPanel.tsx`.
- Create `apps/web/src/components/video-workflow/VideoWorkflowWorkbench.tsx`.
- Remove `apps/web/src/components/video-workflow/VideoWorkflowCanvas.tsx` after imports are migrated.
- Modify `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`: mount only the new workbench.
- Create `apps/web/e2e/video-workbench.spec.ts`.
- Modify `apps/web/package.json`: test scripts and Playwright dev dependency.

## Task 1: Lock the Backend Asset Contract

**Files:**
- Modify: `apps/api/requirements.txt`
- Modify: `apps/api/tests/test_video_workflow_canvas.py`
- Modify: `apps/api/app/video_workflow.py`

- [x] **Step 1: Add image decoding dependency**

Append this exact dependency:

```text
Pillow>=11.0,<12.0
```

- [x] **Step 2: Write failing upload and persistence tests**

Add tests using Pillow-generated in-memory images:

```python
from io import BytesIO
from PIL import Image


def image_bytes(fmt: str = "PNG", size: tuple[int, int] = (64, 48)) -> bytes:
    stream = BytesIO()
    Image.new("RGB", size, (24, 110, 180)).save(stream, format=fmt)
    return stream.getvalue()


def test_video_workflow_upload_records_real_metadata(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    response = client.post(
        f"/projects/{project['project_id']}/video-workflow/assets",
        files=[
            ("files", ("one.png", image_bytes("PNG"), "image/png")),
            ("files", ("two.jpg", image_bytes("JPEG", (80, 60)), "image/jpeg")),
        ],
    )
    data = unwrap_ok(response)
    assert [(item["mime_type"], item["width"], item["height"]) for item in data["assets"]] == [
        ("image/png", 64, 48),
        ("image/jpeg", 80, 60),
    ]
    assert all(item["byte_size"] > 0 for item in data["assets"])
    assert all(item["deleted_at"] is None for item in data["assets"])


def test_video_workflow_upload_rejects_fake_image(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("fake.png", b"not an image", "image/png"))],
        ),
        400,
        "VIDEO_REFERENCE_INVALID",
    )


def test_video_workflow_soft_delete_keeps_historical_metadata(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    uploaded = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[("files", ("one.png", image_bytes(), "image/png"))],
        )
    )
    asset_id = uploaded["assets"][0]["asset_id"]
    unwrap_ok(client.delete(f"/projects/{project['project_id']}/video-workflow/assets/{asset_id}"))
    workbench = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))
    assert workbench["assets"] == []
    manifest = json.loads(
        (Path(project["project_dir"]) / "video_workflow" / "assets.json").read_text(encoding="utf-8")
    )
    assert manifest[0]["asset_id"] == asset_id
    assert manifest[0]["deleted_at"]


def test_video_workflow_partial_upload_keeps_valid_files(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    data = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/assets",
            files=[
                ("files", ("valid.png", image_bytes(), "image/png")),
                ("files", ("bad.png", b"not-image", "image/png")),
            ],
        )
    )
    assert [item["filename"] for item in data["uploaded"]] == ["valid.png"]
    assert data["errors"][0]["filename"] == "bad.png"
    assert data["errors"][0]["code"] == "VIDEO_REFERENCE_INVALID"
```

- [x] **Step 3: Run the tests and verify failure**

Run:

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "upload_records or fake_image or soft_delete" -q
```

Expected: FAIL because width, height, byte size, soft deletion and DELETE route do not exist.

- [x] **Step 4: Add canonical limits and asset validation**

At the top of `video_workflow.py`, add:

```python
import os
from PIL import Image, UnidentifiedImageError

VIDEO_MODEL = "omni_flash-10s"
VIDEO_SIZE = "1280x720"
VIDEO_DURATION_SEC = 10
MAX_REFERENCE_IMAGES = 7
MAX_PROJECT_ASSETS = 50
MAX_ASSET_BYTES = int(os.getenv("VIDEO_REFERENCE_MAX_BYTES", str(10 * 1024 * 1024)))
POLL_INTERVAL_MS = 4000
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}
```

Replace direct `file.file.read()` handling with bounded disk streaming:

```python
def _stage_upload(file: UploadFile, temp_path: Path) -> int:
    total = 0
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with temp_path.open("wb") as output:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ASSET_BYTES:
                raise VideoWorkflowError(
                    "VIDEO_REFERENCE_TOO_LARGE",
                    f"单张参考图不能超过 {MAX_ASSET_BYTES // (1024 * 1024)}MB",
                )
            output.write(chunk)
    if total == 0:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图文件为空")
    return total


def _inspect_image(path: Path) -> tuple[str, str, int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image_format = str(image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "文件不是有效图片") from exc
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "仅支持 JPG、PNG、WebP 图片")
    mime_type, extension = ALLOWED_IMAGE_FORMATS[image_format]
    return mime_type, extension, int(width), int(height)


def _save_one_asset(self, project_dir: Path, file: UploadFile) -> dict[str, Any]:
    asset_id = f"vref_{uuid.uuid4().hex[:12]}"
    original_name = Path(file.filename or "reference").name
    upload_dir = self._workflow_dir(project_dir) / "references"
    temp = upload_dir / f".{asset_id}.upload"
    try:
        byte_size = _stage_upload(file, temp)
        mime_type, extension, width, height = _inspect_image(temp)
        filename = f"{asset_id}{extension}"
        target = upload_dir / filename
        os.replace(temp, target)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return {
        "asset_id": asset_id,
        "filename": original_name,
        "path": f"video_workflow/references/{filename}",
        "mime_type": mime_type,
        "byte_size": byte_size,
        "width": width,
        "height": height,
        "created_at": now_iso(),
        "deleted_at": None,
    }
```

- [x] **Step 5: Make manifest writes atomic and support soft delete**

Add:

```python
def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)
```

Before processing, reject an upload when the number of active assets is already `MAX_PROJECT_ASSETS`. Process files independently:

Remove the old upload-time check that limits the entire project library to 7 images. Seven is the per-run selected reference limit; the project library limit is 50.

```python
uploaded: list[dict[str, Any]] = []
errors: list[dict[str, str]] = []
for file in files:
    if len(existing) + len(uploaded) >= MAX_PROJECT_ASSETS:
        errors.append({
            "filename": file.filename or "unnamed",
            "code": "VIDEO_REFERENCE_LIMIT_EXCEEDED",
            "message": f"单项目最多保存 {MAX_PROJECT_ASSETS} 张参考图",
        })
        continue
    try:
        uploaded.append(self._save_one_asset(project_dir, file))
    except VideoWorkflowError as exc:
        errors.append({
            "filename": file.filename or "unnamed",
            "code": exc.code,
            "message": str(exc),
        })
if not uploaded and errors:
    first = errors[0]
    raise VideoWorkflowError(first["code"], first["message"])
all_assets = [*self._all_reference_assets(project_dir), *uploaded]
_write_json_atomic(self._assets_path(project_dir), all_assets)
return {
    "assets": [item for item in all_assets if not item.get("deleted_at")],
    "uploaded": uploaded,
    "errors": errors,
    "max_reference_images": MAX_REFERENCE_IMAGES,
}
```

Add service methods:

```python
def asset(self, project_id: str, asset_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
    project_dir = Path(self.store.get_project(project_id)["project_dir"])
    for item in self._all_reference_assets(project_dir):
        if item["asset_id"] == asset_id and (include_deleted or not item.get("deleted_at")):
            return item
    raise KeyError(asset_id)


def delete_asset(self, project_id: str, asset_id: str) -> dict[str, Any]:
    project_dir = Path(self.store.get_project(project_id)["project_dir"])
    assets = self._all_reference_assets(project_dir)
    found = False
    for item in assets:
        if item["asset_id"] == asset_id and not item.get("deleted_at"):
            item["deleted_at"] = now_iso()
            found = True
            break
    if not found:
        raise KeyError(asset_id)
    _write_json_atomic(self._assets_path(project_dir), assets)
    return {"asset_id": asset_id, "deleted": True}
```

Keep `_all_reference_assets()` unfiltered and make `_reference_assets()` return only entries without `deleted_at`.

- [x] **Step 6: Run asset tests**

Run:

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "upload or asset" -q
```

Expected: all upload/asset tests PASS.

- [x] **Step 7: Commit**

```bash
git add apps/api/requirements.txt apps/api/app/video_workflow.py apps/api/tests/test_video_workflow_canvas.py
git commit -m "feat(video): validate and persist project reference assets"
```

## Task 2: Correct the Omni Multipart Adapter

**Files:**
- Modify: `apps/api/tests/test_real_providers.py`
- Modify: `apps/api/app/providers.py`

- [x] **Step 1: Write failing multipart tests**

Add a recording transport test:

```python
def test_octo_video_provider_keeps_reference_order_and_mime(tmp_path: Path):
    png = tmp_path / "a.png"
    jpg = tmp_path / "b.jpg"
    png.write_bytes(b"png-bytes")
    jpg.write_bytes(b"jpg-bytes")
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any):
        calls.append({"method": method, "url": url, **kwargs})
        return {"id": "remote_1", "status": "queued"}

    provider = OctoVideoProvider("secret", "https://provider.example", transport=transport)
    provider.submit_video(
        {
            "model": "omni_flash-10s",
            "prompt": "test",
            "size": "1280x720",
            "reference_images": [
                {"path": str(png), "mime_type": "image/png"},
                {"path": str(jpg), "mime_type": "image/jpeg"},
            ],
        }
    )
    files = calls[0]["files"]
    assert [item[0] for item in files] == ["input_reference", "input_reference"]
    assert [item[1][0] for item in files] == ["a.png", "b.jpg"]
    assert [item[1][2] for item in files] == ["image/png", "image/jpeg"]
    assert calls[0]["data"] == {
        "model": "omni_flash-10s",
        "prompt": "test",
        "size": "1280x720",
    }
    assert "images" not in calls[0]["data"]


def test_octo_video_provider_text_mode_uses_json_without_references():
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any):
        calls.append(kwargs)
        return {"id": "remote_2", "status": "queued"}

    provider = OctoVideoProvider("secret", "https://provider.example", transport=transport)
    provider.submit_video({"model": "omni_flash-10s", "prompt": "test", "size": "1280x720"})
    assert calls[0]["json"] == {
        "model": "omni_flash-10s",
        "prompt": "test",
        "size": "1280x720",
    }
    assert "data" not in calls[0]
```

- [x] **Step 2: Verify failure**

Run:

```bash
python -m pytest apps/api/tests/test_real_providers.py -k "keeps_reference_order or text_mode" -q
```

Expected: multipart test FAIL because the provider only understands `reference_image_paths`, constructs one in-memory body and writes every file as PNG.

- [x] **Step 3: Change multipart input to typed streamed references**

Import:

```python
from contextlib import ExitStack

import httpx
```

Update `submit_video`:

```python
references = payload.get("reference_images") or []
if references:
    request_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"images", "reference_images", "reference_image_paths"}
    }
    with ExitStack() as stack:
        files: list[tuple[str, tuple[str, Any, str]]] = []
        for item in references:
            path = Path(str(item["path"]))
            if not path.is_file():
                raise ProviderError(
                    "OCTO_REFERENCE_FILE_MISSING",
                    f"参考图文件不存在：{path.name}",
                    retryable=False,
                )
            stream = stack.enter_context(path.open("rb"))
            files.append((
                "input_reference",
                (path.name, stream, str(item["mime_type"])),
            ))
        raw = self.transport(
            "POST",
            f"{self.base_url}/v1/videos",
            headers=self._auth_headers(),
            data=request_payload,
            files=files,
        )
else:
    request_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"images", "reference_images", "reference_image_paths"}
    }
    raw = self.transport(
        "POST",
        f"{self.base_url}/v1/videos",
        headers=self._json_headers(),
        json=request_payload,
    )
```

Remove `_multipart_video_body`; no caller should read all reference files into one bytes object.

Replace only `OctoVideoProvider._http_transport` with:

```python
def _http_transport(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
            response = client.request(
                method,
                url,
                headers=kwargs.get("headers") or {},
                json=kwargs.get("json"),
                data=kwargs.get("data"),
                files=kwargs.get("files"),
            )
        response.raise_for_status()
        if not response.content:
            raise ProviderError("OCTO_RESPONSE_INVALID", "上游服务返回空响应", retryable=True)
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(
                "OCTO_RESPONSE_INVALID",
                "上游服务返回非 JSON 响应",
                retryable=True,
                response_excerpt=response.text,
            ) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise ProviderError(
            "OCTO_REQUEST_FAILED",
            f"HTTP {status}",
            retryable=status in {408, 429, 500, 502, 503, 504},
            status_code=status,
            response_excerpt=exc.response.text,
        ) from exc
    except httpx.TimeoutException as exc:
        raise ProviderError("OCTO_REQUEST_FAILED", "视频服务请求超时", retryable=True) from exc
    except httpx.RequestError as exc:
        raise ProviderError("OCTO_REQUEST_FAILED", str(exc), retryable=True) from exc
```

Replace `download_video` so MP4 content is streamed to the service-provided temporary path:

```python
def download_video(self, video_url: str, target_path: Path) -> None:
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream(
            "GET",
            video_url,
            headers={
                "User-Agent": "ShanHai-Edu/1.0",
                "Accept": "video/mp4,video/*;q=0.9,application/octet-stream",
            },
            timeout=httpx.Timeout(180.0, connect=20.0),
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            with target_path.open("wb") as output:
                for chunk in response.iter_bytes(1024 * 1024):
                    output.write(chunk)
    except httpx.HTTPStatusError as exc:
        raise ProviderError(
            "VIDEO_DOWNLOAD_FAILED",
            f"视频下载失败：HTTP {exc.response.status_code}",
            retryable=exc.response.status_code in {408, 429, 500, 502, 503, 504},
            status_code=exc.response.status_code,
        ) from exc
    except httpx.RequestError as exc:
        raise ProviderError("VIDEO_DOWNLOAD_FAILED", str(exc), retryable=True) from exc
```

- [x] **Step 4: Run provider tests**

Run:

```bash
python -m pytest apps/api/tests/test_real_providers.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add apps/api/app/providers.py apps/api/tests/test_real_providers.py
git commit -m "fix(video): preserve Omni reference order and MIME"
```

## Task 3: Implement Idempotent Run Creation and History

**Files:**
- Modify: `apps/api/tests/test_video_workflow_canvas.py`
- Modify: `apps/api/app/video_workflow.py`
- Modify: `apps/api/app/store.py`

- [x] **Step 1: Write failing idempotency, list and fixed-config tests**

```python
def test_video_workflow_create_is_idempotent_and_server_owned(tmp_path: Path):
    submitted: list[dict[str, Any]] = []

    class Provider:
        def submit_video(self, payload):
            submitted.append(payload)
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = Provider()
    project = create_project(client)
    request = {
        "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
        "prompt": "triangle blocks form a bridge",
        "reference_asset_ids": [],
        "model": "forged-model",
        "size": "999x999",
        "duration_sec": 999,
    }
    first = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=request))
    second = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=request))
    assert first["run_id"] == second["run_id"]
    assert len(submitted) == 1
    assert first["model"] == "omni_flash-10s"
    assert first["size"] == "1280x720"
    assert first["duration_sec"] == 10


def test_video_workflow_same_id_with_different_payload_conflicts(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    base = {
        "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
        "prompt": "first",
        "reference_asset_ids": [],
    }
    unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs", json=base))
    unwrap_error(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={**base, "prompt": "different"},
        ),
        409,
        "VIDEO_REQUEST_CONFLICT",
    )


def test_video_workflow_returns_latest_fifty_runs(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    for index in range(55):
        unwrap_ok(
            client.post(
                f"/projects/{project['project_id']}/video-workflow/runs",
                json={
                    "client_request_id": str(uuid.uuid4()),
                    "prompt": f"prompt {index}",
                    "reference_asset_ids": [],
                },
            )
        )
    data = unwrap_ok(client.get(f"/projects/{project['project_id']}/video-workflow"))
    assert len(data["runs"]) == 50
    assert data["runs"][0]["prompt"] == "prompt 54"
```

Add these imports once at the top of the test module:

```python
import json
import uuid
```

Add one shared provider fixture class at module level:

```python
class RecordingVideoProvider:
    def __init__(self):
        self.submitted: list[dict[str, Any]] = []

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append(payload)
        return {
            "provider_task_id": f"remote_{len(self.submitted)}",
            "status": "queued",
            "progress": 0,
            "video_url": None,
        }
```

- [x] **Step 2: Verify failure**

Run:

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "idempotent or conflicts or latest_fifty" -q
```

Expected: FAIL because current create accepts client-owned config and only exposes `latest_run`.

- [x] **Step 3: Add canonical request helpers**

```python
def _canonical_run_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
    request_id = str(payload.get("client_request_id") or "").strip()
    try:
        uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise VideoWorkflowError("VIDEO_REQUEST_INVALID", "client_request_id 必须是 UUID") from exc
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise VideoWorkflowError("VIDEO_PROMPT_REQUIRED", "请先填写视频提示词")
    if len(prompt) > 5000:
        raise VideoWorkflowError("VIDEO_PROMPT_TOO_LONG", "视频提示词不能超过 5000 字符")
    reference_ids = [str(item) for item in payload.get("reference_asset_ids") or []]
    if len(reference_ids) > MAX_REFERENCE_IMAGES:
        raise VideoWorkflowError("VIDEO_REFERENCE_LIMIT_EXCEEDED", "Omni 最多使用 7 张参考图")
    if len(reference_ids) != len(set(reference_ids)):
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图不能重复")
    return {
        "client_request_id": request_id,
        "prompt": prompt,
        "model": VIDEO_MODEL,
        "size": VIDEO_SIZE,
        "duration_sec": VIDEO_DURATION_SEC,
        "reference_asset_ids": reference_ids,
    }


def _find_run_by_client_request_id(self, project_id: str, request_id: str) -> dict[str, Any] | None:
    for task in self.store.tasks(project_id):
        if task["task_type"] != "video_workflow_generation":
            continue
        if task.get("payload", {}).get("client_request_id") == request_id:
            return task
    return None
```

In `create_run`, resolve the ordered references and add the frozen `reference_assets` snapshot before comparing the canonical payload to an existing task. Then compare before calling the provider:

```python
canonical = self._canonical_run_payload(payload)
existing = self._find_run_by_client_request_id(project_id, canonical["client_request_id"])
if existing:
    if existing["payload"] != canonical:
        raise VideoWorkflowError(
            "VIDEO_REQUEST_CONFLICT",
            "相同 client_request_id 已用于不同的视频请求",
            status_code=409,
        )
    return self._decorate_run(existing)
```

Replace the error constructor with:

```python
class VideoWorkflowError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
```

- [x] **Step 4: Add a database-backed idempotency key**

In `ProjectStore.init_db()`, call `self._ensure_task_columns(conn)` after the schema script. Add:

```python
def _ensure_task_columns(self, conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    if "client_request_id" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN client_request_id TEXT")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_video_client_request
        ON tasks(project_id, task_type, client_request_id)
        WHERE client_request_id IS NOT NULL
        """
    )
    conn.commit()
```

Extend `create_task` with `client_request_id: str | None = None`, include it in the INSERT, and return it from task decoration. Add:

```python
def task_by_client_request_id(
    self,
    project_id: str,
    task_type: str,
    client_request_id: str,
) -> dict[str, Any] | None:
    project = self.get_project(project_id)
    with self.connect(Path(project["project_dir"])) as conn:
        row = conn.execute(
            """
            SELECT * FROM tasks
            WHERE project_id = ? AND task_type = ? AND client_request_id = ?
            """,
            (project_id, task_type, client_request_id),
        ).fetchone()
    return self._task_from_row(row) if row else None
```

Use this lookup in `_find_run_by_client_request_id`. If two requests race, catch `sqlite3.IntegrityError`, re-read by idempotency key, compare payloads, and return the existing run.

- [x] **Step 5: Submit typed reference metadata**

Resolve each ordered asset and construct:

```python
references = [self.asset(project_id, asset_id) for asset_id in canonical["reference_asset_ids"]]
canonical["reference_assets"] = [
    {
        "asset_id": asset["asset_id"],
        "filename": asset["filename"],
        "mime_type": asset["mime_type"],
        "width": asset["width"],
        "height": asset["height"],
    }
    for asset in references
]
submit_payload: dict[str, Any] = {
    "model": VIDEO_MODEL,
    "prompt": canonical["prompt"],
    "size": VIDEO_SIZE,
}
if references:
    submit_payload["reference_images"] = [
        {
            "path": str(project_dir / asset["path"]),
            "mime_type": asset["mime_type"],
        }
        for asset in references
    ]
```

When `video_provider is None`, raise `VIDEO_PROVIDER_NOT_CONFIGURED`; do not return a generated placeholder.

- [x] **Step 6: Normalize provider submission errors**

Add:

```python
from .providers import ProviderError, sanitize_provider_excerpt


def _submission_failure(exc: ProviderError) -> tuple[str, str, bool, str]:
    excerpt = (exc.response_excerpt or "").lower()
    if exc.status_code in {401, 403}:
        return "VIDEO_AUTH_FAILED", "视频服务鉴权失败", False, "failed"
    if exc.status_code == 429:
        return "VIDEO_RATE_LIMITED", "视频服务请求过于频繁", True, "failed"
    if exc.status_code in {402} or "quota" in excerpt or "resource_exhausted" in excerpt:
        return "VIDEO_QUOTA_EXHAUSTED", "视频服务额度不足", False, "failed"
    if "safety" in excerpt or "moderation" in excerpt or "content" in excerpt:
        return "VIDEO_CONTENT_REJECTED", "提示词或参考素材未通过内容审核", False, "failed"
    if exc.code == "OCTO_REQUEST_FAILED" and exc.retryable and exc.status_code is None:
        return "VIDEO_SUBMIT_UNCERTAIN", "提交超时，无法确认上游是否已创建任务", False, "submission_unknown"
    return "VIDEO_TASK_FAILED", str(exc), exc.retryable, "failed"
```

In `create_run`, persist the mapped code, retryability and terminal state, then return the decorated failed or `submission_unknown` task:

```python
except ProviderError as exc:
    error_code, message, retryable, status = _submission_failure(exc)
    with self.store.connect(project_dir) as conn:
        updated = self.store.update_task(
            conn,
            task["task_id"],
            status,
            {
                "provider_phase": "submit",
                "download_status": "not_started",
                "error_code": error_code,
                "retryable": retryable,
                "response_excerpt": sanitize_provider_excerpt(exc.response_excerpt or ""),
            },
            message,
        )
    return self._decorate_run(updated)
```

This guarantees the failed attempt appears immediately in history. Never issue a second provider submission automatically.

- [x] **Step 7: Expose config, active assets and 50 runs**

Return:

```python
{
    "project_id": project_id,
    "config": {
        "model": VIDEO_MODEL,
        "size": VIDEO_SIZE,
        "duration_sec": VIDEO_DURATION_SEC,
        "max_reference_images": MAX_REFERENCE_IMAGES,
        "max_project_assets": MAX_PROJECT_ASSETS,
        "max_asset_bytes": MAX_ASSET_BYTES,
        "poll_interval_ms": POLL_INTERVAL_MS,
        "provider_ready": self.video_provider is not None,
    },
    "graph": self._read_graph(project_dir),
    "assets": self._reference_assets(project_dir),
    "runs": self.list_runs(project_id, limit=50),
}
```

Implement:

```python
def list_runs(self, project_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    bounded = min(100, max(1, int(limit)))
    runs = [
        self._decorate_run(task)
        for task in self.store.tasks(project_id)
        if task["task_type"] == "video_workflow_generation"
    ]
    return sorted(runs, key=lambda item: item["created_at"], reverse=True)[:bounded]
```

Replace `_decorate_run` with a stable public shape:

```python
def _decorate_run(self, task: dict[str, Any]) -> dict[str, Any]:
    payload = dict(task.get("payload") or {})
    result = dict(task.get("result") or {})
    return {
        "run_id": task["task_id"],
        "client_request_id": payload.get("client_request_id"),
        "retry_of_run_id": payload.get("retry_of_run_id"),
        "project_id": task["project_id"],
        "status": task["status"],
        "download_status": result.get("download_status", "not_started"),
        "progress": int(result.get("progress") or 0),
        "prompt": payload.get("prompt", ""),
        "model": payload.get("model", VIDEO_MODEL),
        "size": payload.get("size", VIDEO_SIZE),
        "duration_sec": payload.get("duration_sec", VIDEO_DURATION_SEC),
        "reference_asset_ids": payload.get("reference_asset_ids", []),
        "reference_assets": payload.get("reference_assets", []),
        "provider_task_id": result.get("provider_task_id"),
        "error_code": result.get("error_code"),
        "error_message": task.get("error_message"),
        "retryable": bool(result.get("retryable", False)),
        "video_ready": (
            task["status"] == "completed"
            and result.get("download_status") == "downloaded"
            and bool(result.get("download_path"))
        ),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }
```

- [x] **Step 8: Run run-creation tests**

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "create or idempotent or conflicts or latest_fifty or text_run or reference_run" -q
```

Expected: PASS.

- [x] **Step 9: Commit**

```bash
git add apps/api/app/video_workflow.py apps/api/app/store.py apps/api/tests/test_video_workflow_canvas.py
git commit -m "feat(video): add idempotent project run history"
```

## Task 4: Complete Sync, Retry and Atomic Download

**Files:**
- Modify: `apps/api/tests/test_video_workflow_canvas.py`
- Modify: `apps/api/app/video_workflow.py`

- [x] **Step 1: Write failing terminal sync and retry tests**

```python
def test_completed_sync_downloads_once_atomically(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.downloads = 0

        def submit_video(self, payload):
            return {"provider_task_id": "remote_1", "status": "queued", "progress": 0}

        def query_task(self, task_id):
            return {
                "provider_task_id": task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/result.mp4",
            }

        def download_video(self, url, target):
            self.downloads += 1
            Path(target).write_bytes(b"test-mp4-bytes")

    provider = Provider()
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = provider
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "test",
                "reference_asset_ids": [],
            },
        )
    )
    first = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    second = unwrap_ok(client.post(f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/sync"))
    assert first["status"] == second["status"] == "completed"
    assert first["download_status"] == second["download_status"] == "downloaded"
    assert provider.downloads == 1


def test_retry_creates_new_run_with_original_snapshot(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    original = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "original",
                "reference_asset_ids": [],
            },
        )
    )
    retried = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs/{original['run_id']}/retry",
            json={"client_request_id": str(uuid.uuid4())},
        )
    )
    assert retried["run_id"] != original["run_id"]
    assert retried["retry_of_run_id"] == original["run_id"]
    assert retried["prompt"] == "original"
```

- [x] **Step 2: Verify failure**

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "downloads_once or retry_creates" -q
```

Expected: FAIL because sync always queries/downloads and retry route does not exist.

- [x] **Step 3: Make sync terminal-state and download aware**

Implement this ordering:

```python
TERMINAL_RUN_STATES = {"completed", "failed", "submission_unknown"}

def sync_run(self, project_id: str, run_id: str) -> dict[str, Any]:
    project_dir = Path(self.store.get_project(project_id)["project_dir"])
    task = self.store.task(project_id, run_id)
    result = dict(task.get("result") or {})
    if task["status"] == "completed" and result.get("download_status") == "downloaded":
        return self._decorate_run(task)
    provider_task_id = result.get("provider_task_id") or task.get("provider_task_id")
    if not provider_task_id:
        return self._decorate_run(task)
    remote = self.video_provider.query_task(provider_task_id)
    merged = {**result, **remote, "provider_phase": "query"}
    status = str(remote.get("status") or task["status"])
    if status == "completed" and remote.get("video_url"):
        relative = f"video_workflow/runs/{run_id}.mp4"
        target = project_dir / relative
        try:
            if not target.is_file() or target.stat().st_size == 0:
                temp = target.with_suffix(".mp4.part")
                temp.parent.mkdir(parents=True, exist_ok=True)
                self.video_provider.download_video(remote["video_url"], temp)
                if not temp.is_file() or temp.stat().st_size == 0:
                    temp.unlink(missing_ok=True)
                    raise ProviderError("VIDEO_DOWNLOAD_FAILED", "视频下载结果为空", retryable=True)
                os.replace(temp, target)
        except ProviderError as exc:
            failed_download = {
                **merged,
                "download_path": relative,
                "download_status": "download_failed",
                "error_code": "VIDEO_DOWNLOAD_FAILED",
                "retryable": True,
            }
            with self.store.connect(project_dir) as conn:
                self.store.update_task(conn, run_id, "completed", failed_download, str(exc))
            raise
        merged.update({"download_path": relative, "download_status": "downloaded"})
    with self.store.connect(project_dir) as conn:
        updated = self.store.update_task(
            conn,
            run_id,
            status,
            merged,
            remote.get("error_message"),
        )
    return self._decorate_run(updated)
```

When download fails, retain generation status `completed`, set `download_status=download_failed`, and return a retryable provider error without changing the run to generated failure.

Wrap `query_task` errors with the same public mapping used during submit. For a provider response whose normalized status is `failed`, persist `remote.error_code`, `remote.error_message`, and `remote.retryable`; do not replace them with a generic frontend-only message.

- [x] **Step 4: Add retry service**

```python
def retry_run(self, project_id: str, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    original = self.store.task(project_id, run_id)
    if original["task_type"] != "video_workflow_generation":
        raise KeyError(run_id)
    original_payload = dict(original.get("payload") or {})
    retry_payload = {
        "client_request_id": payload.get("client_request_id"),
        "prompt": original_payload.get("prompt"),
        "reference_asset_ids": original_payload.get("reference_asset_ids", []),
    }
    created = self.create_run(
        project_id,
        retry_payload,
        allow_deleted_assets=True,
        retry_of_run_id=run_id,
    )
    return created
```

Extend `create_run` to:

```python
def create_run(
    self,
    project_id: str,
    payload: dict[str, Any],
    *,
    allow_deleted_assets: bool = False,
    retry_of_run_id: str | None = None,
) -> dict[str, Any]:
```

Resolve references with `include_deleted=allow_deleted_assets` and add `retry_of_run_id` to the canonical stored payload before task creation. Public create requests always use the default `False`; only the internal retry service may use deleted historical assets.

- [x] **Step 5: Run sync/retry tests**

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "sync or retry or completed" -q
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add apps/api/app/video_workflow.py apps/api/tests/test_video_workflow_canvas.py
git commit -m "feat(video): add recoverable sync and retry lifecycle"
```

## Task 5: Expose the Complete Project API

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/tests/test_video_workflow_canvas.py`

- [x] **Step 1: Write failing route tests**

Add these route tests:

```python
def test_video_workflow_asset_content_and_delete_are_project_scoped(tmp_path: Path):
    client = make_client(tmp_path)
    first = create_project(client)
    second = create_project(client)
    asset = unwrap_ok(
        client.post(
            f"/projects/{first['project_id']}/video-workflow/assets",
            files=[("files", ("one.png", image_bytes(), "image/png"))],
        )
    )["assets"][0]
    assert client.get(
        f"/projects/{first['project_id']}/video-workflow/assets/{asset['asset_id']}/content"
    ).status_code == 200
    assert client.get(
        f"/projects/{second['project_id']}/video-workflow/assets/{asset['asset_id']}/content"
    ).status_code == 404
    assert client.delete(
        f"/projects/{first['project_id']}/video-workflow/assets/{asset['asset_id']}"
    ).status_code == 200


def test_video_workflow_content_is_inline_mp4(tmp_path: Path):
    client = make_client(tmp_path, {"video_provider_mode": "real"})
    client.app.state.service.video_workflow.video_provider = RecordingVideoProvider()
    project = create_project(client)
    run = unwrap_ok(
        client.post(
            f"/projects/{project['project_id']}/video-workflow/runs",
            json={
                "client_request_id": str(uuid.uuid4()),
                "prompt": "stream test",
                "reference_asset_ids": [],
            },
        )
    )
    project_row = client.app.state.store.get_project(project["project_id"])
    project_dir = Path(project_row["project_dir"])
    relative = f"video_workflow/runs/{run['run_id']}.mp4"
    target = project_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"0123456789abcdef")
    task = client.app.state.store.task(project["project_id"], run["run_id"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.update_task(
            conn,
            run["run_id"],
            "completed",
            {
                **task["result"],
                "download_path": relative,
                "download_status": "downloaded",
            },
        )
    response = client.get(
        f"/projects/{project['project_id']}/video-workflow/runs/{run['run_id']}/content",
        headers={"Range": "bytes=0-7"},
    )
    assert response.status_code in {200, 206}
    assert response.headers["content-type"].startswith("video/mp4")
```

- [x] **Step 2: Verify failure**

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py -k "project_scoped or inline_mp4" -q
```

Expected: FAIL with 404/405 because the routes are missing.

- [x] **Step 3: Add routes with consistent error mapping**

Add to `main.py` beside existing video-workflow routes:

```python
@app.get("/projects/{project_id}/video-workflow/assets/{asset_id}/content", dependencies=protected)
def get_video_workflow_asset(project_id: str, asset_id: str):
    try:
        asset = service.video_workflow.asset(project_id, asset_id, include_deleted=True)
        project = store.get_project(project_id)
        path = Path(project["project_dir"]) / asset["path"]
        if not path.is_file():
            raise KeyError(asset_id)
        return FileResponse(path, media_type=asset["mime_type"], filename=asset["filename"])
    except KeyError:
        return fail(404, "VIDEO_REFERENCE_NOT_FOUND", "参考图不存在", retryable=False)


@app.delete("/projects/{project_id}/video-workflow/assets/{asset_id}", dependencies=protected)
def delete_video_workflow_asset(project_id: str, asset_id: str):
    try:
        return ok(service.video_workflow.delete_asset(project_id, asset_id))
    except KeyError:
        return fail(404, "VIDEO_REFERENCE_NOT_FOUND", "参考图不存在", retryable=False)


@app.get("/projects/{project_id}/video-workflow/runs", dependencies=protected)
def list_video_workflow_runs(project_id: str, limit: int = 50):
    return ok(service.video_workflow.list_runs(project_id, limit=limit))


@app.post("/projects/{project_id}/video-workflow/runs/{run_id}/retry", dependencies=protected)
def retry_video_workflow_run(project_id: str, run_id: str, payload: dict[str, Any]):
    try:
        return ok(service.video_workflow.retry_run(project_id, run_id, payload))
    except VideoWorkflowError as exc:
        return fail(exc.status_code, exc.code, str(exc), retryable=False)
    except KeyError:
        return fail(404, "VIDEO_WORKFLOW_RUN_NOT_FOUND", "视频任务不存在", retryable=False)


@app.get("/projects/{project_id}/video-workflow/runs/{run_id}/content", dependencies=protected)
def stream_video_workflow_run(project_id: str, run_id: str):
    try:
        path = service.video_workflow.download_path(project_id, run_id)
        if not path.is_file():
            raise KeyError(run_id)
        return FileResponse(
            path,
            media_type="video/mp4",
            filename=path.name,
            content_disposition_type="inline",
        )
    except KeyError:
        return fail(404, "VIDEO_OUTPUT_NOT_FOUND", "视频输出不存在", retryable=True)
```

Use `exc.status_code` in existing create/upload handlers.

- [x] **Step 4: Run the complete backend video suite**

```bash
python -m pytest apps/api/tests/test_video_workflow_canvas.py apps/api/tests/test_real_providers.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add apps/api/app/main.py apps/api/tests/test_video_workflow_canvas.py
git commit -m "feat(video): expose project asset and run lifecycle APIs"
```

## Task 6: Replace Frontend Contracts and State

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/api-client.ts`
- Modify: `apps/web/src/lib/store.ts`
- Modify: `apps/web/src/lib/video-workflow-contract.test.ts`

- [x] **Step 1: Rewrite contract assertions first**

The contract test must assert the new surface:

```typescript
assert(types.includes("interface VideoWorkflowConfig"), "config contract is required");
assert(types.includes("byte_size: number"), "asset byte size is required");
assert(types.includes("deleted_at: string | null"), "asset soft delete is required");
assert(types.includes("client_request_id: string"), "run idempotency key is required");
assert(types.includes("download_status: VideoDownloadStatus"), "download state is required");
assert(types.includes("runs: VideoWorkflowRun[]"), "workbench must expose history");

assert(apiClient.includes("deleteVideoWorkflowAsset"), "asset delete API is required");
assert(apiClient.includes("fetchVideoWorkflowRuns"), "run list API is required");
assert(apiClient.includes("retryVideoWorkflowRun"), "retry API is required");
assert(apiClient.includes("streamVideoWorkflowRun"), "inline video API is required");

assert(store.includes("replaceVideoWorkflowRun"), "store must replace a run immutably");
assert(store.includes("removeVideoWorkflowAsset"), "store must remove soft-deleted assets");

assert(workspace.includes("VideoWorkflowWorkbench"), "workspace must mount new workbench");
assert(!workspace.includes("<VideoWorkflowCanvas"), "workspace must not mount ReactFlow canvas");
```

- [x] **Step 2: Verify contract failure**

Run:

```bash
cd apps/web
bun src/lib/video-workflow-contract.test.ts
```

Expected: FAIL on the first missing new contract.

- [x] **Step 3: Replace video types**

Use:

```typescript
export type VideoRunStatus =
  | "submitting"
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "submission_unknown";

export type VideoDownloadStatus =
  | "not_started"
  | "downloading"
  | "downloaded"
  | "download_failed";

export interface VideoWorkflowConfig {
  model: "omni_flash-10s";
  size: "1280x720";
  duration_sec: 10;
  max_reference_images: 7;
  max_project_assets: 50;
  max_asset_bytes: number;
  poll_interval_ms: number;
  provider_ready: boolean;
}

export interface VideoReferenceAsset {
  asset_id: string;
  filename: string;
  path: string;
  mime_type: "image/jpeg" | "image/png" | "image/webp";
  byte_size: number;
  width: number;
  height: number;
  created_at: string;
  deleted_at: string | null;
}

export interface VideoWorkflowRun {
  run_id: string;
  client_request_id: string;
  retry_of_run_id: string | null;
  project_id: string;
  status: VideoRunStatus;
  download_status: VideoDownloadStatus;
  progress: number;
  prompt: string;
  model: "omni_flash-10s";
  size: "1280x720";
  duration_sec: 10;
  reference_asset_ids: string[];
  reference_assets: Array<
    Pick<
      VideoReferenceAsset,
      "asset_id" | "filename" | "mime_type" | "width" | "height"
    >
  >;
  provider_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  retryable: boolean;
  video_ready: boolean;
  created_at: string;
  updated_at: string;
}

export interface VideoWorkflowRunRequest {
  client_request_id: string;
  prompt: string;
  reference_asset_ids: string[];
}

export interface VideoWorkflowUploadError {
  filename: string;
  code: string;
  message: string;
}

export interface VideoWorkflowAssetsResponse {
  assets: VideoReferenceAsset[];
  uploaded: VideoReferenceAsset[];
  errors: VideoWorkflowUploadError[];
  max_reference_images: number;
}

export interface VideoWorkflowResponse {
  project_id: string;
  config: VideoWorkflowConfig;
  assets: VideoReferenceAsset[];
  runs: VideoWorkflowRun[];
  graph?: VideoWorkflowGraph;
}
```

- [x] **Step 4: Add API functions**

```typescript
export function videoWorkflowAssetContent(projectId: string, assetId: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectId)}/video-workflow/assets/${encodeURIComponent(assetId)}/content`;
}

export async function deleteVideoWorkflowAsset(projectId: string, assetId: string) {
  return request<{ asset_id: string; deleted: boolean }>(
    `/projects/${encodeURIComponent(projectId)}/video-workflow/assets/${encodeURIComponent(assetId)}`,
    { method: "DELETE" },
  );
}

export async function fetchVideoWorkflowRuns(projectId: string, limit = 50) {
  return request<VideoWorkflowRun[]>(
    `/projects/${encodeURIComponent(projectId)}/video-workflow/runs?limit=${limit}`,
  );
}

export async function retryVideoWorkflowRun(projectId: string, runId: string) {
  return request<VideoWorkflowRun>(
    `/projects/${encodeURIComponent(projectId)}/video-workflow/runs/${encodeURIComponent(runId)}/retry`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_request_id: crypto.randomUUID() }),
    },
  );
}

export function streamVideoWorkflowRun(projectId: string, runId: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectId)}/video-workflow/runs/${encodeURIComponent(runId)}/content`;
}
```

Keep the existing download function.

- [x] **Step 5: Centralize immutable state updates**

Add helpers inside the Zustand module:

```typescript
function upsertVideoRun(
  workflow: VideoWorkflowResponse,
  run: VideoWorkflowRun,
): VideoWorkflowResponse {
  return {
    ...workflow,
    runs: [run, ...workflow.runs.filter((item) => item.run_id !== run.run_id)]
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
      .slice(0, 50),
  };
}
```

Expose actions:

```typescript
removeVideoWorkflowAsset: async (projectId, assetId) => {
  try {
    await deleteVideoWorkflowAsset(projectId, assetId);
    const current = get().videoWorkflowByProject[projectId];
    if (current) {
      set({
        videoWorkflowByProject: {
          ...get().videoWorkflowByProject,
          [projectId]: {
            ...current,
            assets: current.assets.filter((item) => item.asset_id !== assetId),
          },
        },
      });
    }
    return { ok: true };
  } catch (error) {
    return { ok: false, msg: error instanceof Error ? error.message : "参考图移除失败" };
  }
},
replaceVideoWorkflowRun: (projectId, run) => {
  const current = get().videoWorkflowByProject[projectId];
  if (!current) return;
  set({
    videoWorkflowByProject: {
      ...get().videoWorkflowByProject,
      [projectId]: upsertVideoRun(current, run),
    },
  });
},
retryVideoWorkflowRun: async (projectId, runId) => {
  try {
    const run = await retryVideoWorkflowRunRequest(projectId, runId);
    get().replaceVideoWorkflowRun(projectId, run);
    return { ok: true, run };
  } catch (error) {
    return { ok: false, msg: error instanceof Error ? error.message : "视频任务重试失败" };
  }
},
```

Change create and sync actions from `latest_run` assignment to `upsertVideoRun`.

Update the existing upload action to preserve partial errors:

```typescript
uploadVideoWorkflowReferences: async (projectId, files) => {
  try {
    const result = await uploadVideoWorkflowAssets(projectId, files);
    const current = get().videoWorkflowByProject[projectId];
    if (current) {
      set({
        videoWorkflowByProject: {
          ...get().videoWorkflowByProject,
          [projectId]: { ...current, assets: result.assets },
        },
      });
    }
    return { ok: true, assets: result.assets, errors: result.errors };
  } catch (error) {
    return {
      ok: false,
      msg: error instanceof Error ? error.message : "参考图上传失败",
    };
  }
},
```

Alias the imported retry API to avoid colliding with the store action:

```typescript
import {
  retryVideoWorkflowRun as retryVideoWorkflowRunRequest,
} from "@/lib/api-client";
```

Update the `AppState` interface to use the new request type and actions:

```typescript
createVideoWorkflowRun: (
  projectId: string,
  payload: VideoWorkflowRunRequest,
) => Promise<{ ok: boolean; msg?: string; run?: VideoWorkflowRun }>;
uploadVideoWorkflowReferences: (
  projectId: string,
  files: File[],
) => Promise<{
  ok: boolean;
  msg?: string;
  assets?: VideoReferenceAsset[];
  errors?: VideoWorkflowUploadError[];
}>;
syncVideoWorkflowRun: (
  projectId: string,
  runId: string,
) => Promise<{ ok: boolean; msg?: string; run?: VideoWorkflowRun }>;
removeVideoWorkflowAsset: (
  projectId: string,
  assetId: string,
) => Promise<{ ok: boolean; msg?: string }>;
replaceVideoWorkflowRun: (projectId: string, run: VideoWorkflowRun) => void;
retryVideoWorkflowRun: (
  projectId: string,
  runId: string,
) => Promise<{ ok: boolean; msg?: string; run?: VideoWorkflowRun }>;
```

Remove the early return from `loadVideoWorkflow`:

```typescript
// Delete this line:
if (get().dataMode === "demo") return;
```

The demo shell still uses normal project-level video APIs. Browser tests intercept those APIs, while deployed API mode uses the backend proxy.

- [x] **Step 6: Run contract and type checks**

```bash
cd apps/web
bun src/lib/video-workflow-contract.test.ts
bunx tsc --noEmit
```

Expected: both commands PASS.

- [x] **Step 7: Commit**

```bash
git add apps/web/src/lib/types.ts apps/web/src/lib/api-client.ts apps/web/src/lib/store.ts apps/web/src/lib/video-workflow-contract.test.ts
git commit -m "feat(video): define workbench frontend contracts"
```

## Task 7: Implement Selection Helpers and One Polling Scheduler

**Files:**
- Create: `apps/web/src/components/video-workflow/video-workflow-utils.ts`
- Create: `apps/web/src/components/video-workflow/use-video-workflow-polling.ts`
- Create: `apps/web/src/lib/video-workflow-utils.test.ts`

- [x] **Step 1: Write failing pure helper tests**

```typescript
import {
  addReference,
  isActiveVideoRun,
  moveReference,
  reusableReferenceIds,
} from "@/components/video-workflow/video-workflow-utils";

function assert(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}

assert(isActiveVideoRun({ status: "processing" } as never), "processing is active");
assert(!isActiveVideoRun({ status: "completed" } as never), "completed is terminal");
assert(
  JSON.stringify(addReference(["a", "b"], "c", 7)) === JSON.stringify(["a", "b", "c"]),
  "selection preserves order",
);
assert(addReference(["a", "b", "c", "d", "e", "f", "g"], "h", 7).length === 7, "limit is enforced");
assert(
  JSON.stringify(moveReference(["a", "b", "c"], 2, 0)) === JSON.stringify(["c", "a", "b"]),
  "drag reorder works",
);
assert(
  JSON.stringify(reusableReferenceIds(["a", "deleted"], new Set(["a"]))) === JSON.stringify(["a"]),
  "deleted assets are excluded from reuse",
);
```

- [x] **Step 2: Verify failure**

```bash
cd apps/web
bun src/lib/video-workflow-utils.test.ts
```

Expected: FAIL because the utility module does not exist.

- [x] **Step 3: Implement pure helpers**

```typescript
import type { VideoWorkflowRun } from "@/lib/types";

export function isActiveVideoRun(run: Pick<VideoWorkflowRun, "status">): boolean {
  return run.status === "submitting" || run.status === "queued" || run.status === "processing";
}

export function addReference(current: string[], assetId: string, limit: number): string[] {
  if (current.includes(assetId) || current.length >= limit) return current;
  return [...current, assetId];
}

export function moveReference(current: string[], from: number, to: number): string[] {
  if (from === to || from < 0 || to < 0 || from >= current.length || to >= current.length) return current;
  const next = [...current];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}

export function reusableReferenceIds(ids: string[], activeIds: Set<string>): string[] {
  return ids.filter((id) => activeIds.has(id));
}
```

- [x] **Step 4: Implement one polling hook**

```typescript
"use client";

import { useEffect, useMemo } from "react";
import type { VideoWorkflowRun } from "@/lib/types";
import { isActiveVideoRun } from "./video-workflow-utils";

export function useVideoWorkflowPolling({
  projectId,
  runs,
  intervalMs,
  syncRun,
}: {
  projectId: string;
  runs: VideoWorkflowRun[];
  intervalMs: number;
  syncRun: (projectId: string, runId: string) => Promise<unknown>;
}) {
  const activeIds = useMemo(
    () => runs.filter(isActiveVideoRun).map((run) => run.run_id).sort(),
    [runs],
  );
  const activeKey = activeIds.join(",");

  useEffect(() => {
    if (!activeIds.length) return;
    let cancelled = false;
    const syncAll = async () => {
      if (cancelled) return;
      await Promise.allSettled(activeIds.map((runId) => syncRun(projectId, runId)));
    };
    void syncAll();
    const timer = window.setInterval(() => void syncAll(), intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeKey, intervalMs, projectId, syncRun]);
}
```

The dependency on `activeKey` is intentional; suppress the exhaustive-deps warning for `activeIds` only if ESLint requires it, with a short comment.

- [x] **Step 5: Run helper tests and type check**

```bash
cd apps/web
bun src/lib/video-workflow-utils.test.ts
bunx tsc --noEmit
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add apps/web/src/components/video-workflow/video-workflow-utils.ts apps/web/src/components/video-workflow/use-video-workflow-polling.ts apps/web/src/lib/video-workflow-utils.test.ts
git commit -m "feat(video): add ordered selection and automatic polling"
```

## Task 8: Build the Three Workbench Panels

**Files:**
- Create: `apps/web/src/components/video-workflow/VideoAssetPanel.tsx`
- Create: `apps/web/src/components/video-workflow/VideoComposerPanel.tsx`
- Create: `apps/web/src/components/video-workflow/VideoRunHistoryPanel.tsx`

- [x] **Step 1: Build the asset panel with dnd-kit**

The public props must be:

```typescript
interface VideoAssetPanelProps {
  projectId: string;
  assets: VideoReferenceAsset[];
  selectedIds: string[];
  maxSelected: number;
  maxAssetBytes: number;
  busy: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onToggle: (assetId: string) => void;
  onReorder: (ids: string[]) => void;
  onDelete: (assetId: string) => Promise<void>;
}
```

Required UI behavior:

- File input accepts PNG/JPEG/WebP and multiple files.
- Pre-check each browser file against `maxAssetBytes`.
- Asset grid uses `videoWorkflowAssetContent(projectId, assetId)`.
- Selected cards show 1-based order badges.
- A selected strip uses `DndContext`, `SortableContext`, `arrayMove`.
- Delete uses an AlertDialog and calls `onDelete`.
- Clicking the eighth image shows `toast.warning("Omni 最多使用 7 张参考图")`.
- Images use fixed aspect ratio, `object-cover`, and `loading="lazy"`.

- [x] **Step 2: Build the composer/preview panel**

Props:

```typescript
interface VideoComposerPanelProps {
  projectId: string;
  config: VideoWorkflowConfig;
  prompt: string;
  selectedCount: number;
  selectedRun: VideoWorkflowRun | null;
  submitting: boolean;
  onPromptChange: (value: string) => void;
  onSubmit: () => Promise<void>;
}
```

Render:

```tsx
{selectedRun?.video_ready ? (
  <video
    key={selectedRun.run_id}
    controls
    preload="metadata"
    className="aspect-video w-full bg-black"
    src={streamVideoWorkflowRun(projectId, selectedRun.run_id)}
  />
) : (
  <VideoRunPlaceholder run={selectedRun} />
)}
```

The form must:

- Show prompt character count `${prompt.length}/5000`.
- Disable submit when provider is unavailable, prompt is empty/too long, or submit is active.
- Show read-only pills for Omni, 1280×720, 10 seconds, one output.
- Label submit “生成 10 秒视频”.
- Explain 0 references as text-to-video and 1-7 as reference-to-video only through a short status label, not instructional paragraphs.

- [x] **Step 3: Build task history**

Props:

```typescript
interface VideoRunHistoryPanelProps {
  projectId: string;
  runs: VideoWorkflowRun[];
  selectedRunId: string | null;
  busyRunId: string | null;
  onSelect: (runId: string) => void;
  onRetry: (runId: string) => Promise<void>;
  onReuse: (run: VideoWorkflowRun) => void;
}
```

Each card must show:

- Status badge and progress bar.
- Created time.
- Two-line prompt excerpt.
- Up to 4 reference thumbnails and a `+N` badge.
- Error message for failed/unknown runs.
- Retry only when `retryable` or `submission_unknown`.
- A `completed + download_failed` run labels the action “重试下载”; other retryable failures label it “重试生成”.
- “复用参数”.
- Download button only when `video_ready`.

Use `downloadVideoWorkflowRun(projectId, runId)` for downloads.
Use each run's frozen `reference_assets` snapshot for labels and `videoWorkflowAssetContent(projectId, asset_id)` for thumbnails. The content route intentionally allows same-project soft-deleted assets.

- [x] **Step 4: Add source-level contract checks**

Extend `video-workflow-contract.test.ts`:

```typescript
const assetPanel = readProjectFile("src/components/video-workflow/VideoAssetPanel.tsx");
const composer = readProjectFile("src/components/video-workflow/VideoComposerPanel.tsx");
const history = readProjectFile("src/components/video-workflow/VideoRunHistoryPanel.tsx");

assert(assetPanel.includes("DndContext"), "asset panel must support drag ordering");
assert(assetPanel.includes("maxSelected"), "asset panel must enforce reference limit");
assert(composer.includes("<video"), "composer must preview completed video");
assert(composer.includes("生成 10 秒视频"), "composer must expose fixed action");
assert(history.includes("onRetry"), "history must support retry");
assert(history.includes("onReuse"), "history must support parameter reuse");
```

- [x] **Step 5: Run frontend checks**

```bash
cd apps/web
bun src/lib/video-workflow-contract.test.ts
bunx tsc --noEmit
bun run lint
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add apps/web/src/components/video-workflow/VideoAssetPanel.tsx apps/web/src/components/video-workflow/VideoComposerPanel.tsx apps/web/src/components/video-workflow/VideoRunHistoryPanel.tsx apps/web/src/lib/video-workflow-contract.test.ts
git commit -m "feat(video): build workbench asset composer and history panels"
```

## Task 9: Assemble the Workbench and Remove the Decorative Canvas

**Files:**
- Create: `apps/web/src/components/video-workflow/VideoWorkflowWorkbench.tsx`
- Delete: `apps/web/src/components/video-workflow/VideoWorkflowCanvas.tsx`
- Modify: `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`
- Modify: `apps/web/src/lib/video-workflow-contract.test.ts`

- [x] **Step 1: Assemble workbench state**

The component owns only ephemeral UI state:

```typescript
const [prompt, setPrompt] = useState("");
const [selectedIds, setSelectedIds] = useState<string[]>([]);
const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
const [submitting, setSubmitting] = useState(false);
const [busyRunId, setBusyRunId] = useState<string | null>(null);
```

Server data remains in Zustand.

On load:

```typescript
useEffect(() => {
  if (status === "idle" || status === "error") void loadVideoWorkflow(projectId);
}, [loadVideoWorkflow, projectId, status]);

useEffect(() => {
  if (!selectedRunId && workflow?.runs[0]) setSelectedRunId(workflow.runs[0].run_id);
}, [selectedRunId, workflow?.runs]);
```

Create:

```typescript
async function submit() {
  if (!workflow || submitting) return;
  const normalized = prompt.trim();
  if (!normalized || normalized.length > 5000) return;
  setSubmitting(true);
  const result = await createVideoWorkflowRun(projectId, {
    client_request_id: crypto.randomUUID(),
    prompt: normalized,
    reference_asset_ids: selectedIds,
  });
  setSubmitting(false);
  if (!result.ok || !result.run) {
    toast.error(result.msg || "视频任务创建失败");
    return;
  }
  setSelectedRunId(result.run.run_id);
}
```

Reuse:

```typescript
function reuse(run: VideoWorkflowRun) {
  const active = new Set((workflow?.assets || []).map((asset) => asset.asset_id));
  const reusable = reusableReferenceIds(run.reference_asset_ids, active);
  setPrompt(run.prompt);
  setSelectedIds(reusable);
  if (reusable.length !== run.reference_asset_ids.length) {
    toast.warning("部分历史参考图已移除，请重新上传或替换");
  }
}
```

Add the remaining handlers:

```typescript
const selectedRun =
  workflow?.runs.find((run) => run.run_id === selectedRunId) || workflow?.runs[0] || null;

async function upload(files: File[]) {
  const result = await uploadVideoWorkflowReferences(projectId, files);
  if (!result.ok) {
    toast.error(result.msg || "参考图上传失败");
    return;
  }
  for (const error of result.errors || []) {
    toast.error(`${error.filename}：${error.message}`);
  }
}

function toggleAsset(assetId: string) {
  setSelectedIds((current) =>
    current.includes(assetId)
      ? current.filter((id) => id !== assetId)
      : addReference(current, assetId, workflow?.config.max_reference_images || 7),
  );
}

async function deleteAsset(assetId: string) {
  const result = await removeVideoWorkflowAsset(projectId, assetId);
  if (!result.ok) {
    toast.error(result.msg || "参考图移除失败");
    return;
  }
  setSelectedIds((current) => current.filter((id) => id !== assetId));
}

async function retry(runId: string) {
  setBusyRunId(runId);
  const original = workflow?.runs.find((run) => run.run_id === runId);
  const result =
    original?.status === "completed" && original.download_status === "download_failed"
      ? await syncVideoWorkflowRun(projectId, runId)
      : await retryVideoWorkflowRun(projectId, runId);
  setBusyRunId(null);
  if (!result.ok || !result.run) {
    toast.error(result.msg || "视频任务重试失败");
    return;
  }
  setSelectedRunId(result.run.run_id);
}
```

- [x] **Step 2: Wire the poller**

```typescript
useVideoWorkflowPolling({
  projectId,
  runs: workflow?.runs || [],
  intervalMs: workflow?.config.poll_interval_ms || 4000,
  syncRun: async (id, runId) => {
    await syncVideoWorkflowRun(id, runId);
  },
});
```

- [x] **Step 3: Implement responsive layout**

```tsx
const assetPanel = (
  <VideoAssetPanel
    projectId={projectId}
    assets={workflow.assets}
    selectedIds={selectedIds}
    maxSelected={workflow.config.max_reference_images}
    maxAssetBytes={workflow.config.max_asset_bytes}
    busy={status === "loading"}
    onUpload={upload}
    onToggle={toggleAsset}
    onReorder={setSelectedIds}
    onDelete={deleteAsset}
  />
);
const composerPanel = (
  <VideoComposerPanel
    projectId={projectId}
    config={workflow.config}
    prompt={prompt}
    selectedCount={selectedIds.length}
    selectedRun={selectedRun}
    submitting={submitting}
    onPromptChange={setPrompt}
    onSubmit={submit}
  />
);
const historyPanel = (
  <VideoRunHistoryPanel
    projectId={projectId}
    runs={workflow.runs}
    selectedRunId={selectedRun?.run_id || null}
    busyRunId={busyRunId}
    onSelect={setSelectedRunId}
    onRetry={retry}
    onReuse={reuse}
  />
);

return (
  <>
    <div className="hidden min-h-[640px] gap-4 xl:grid xl:grid-cols-[260px_minmax(0,1fr)_320px]">
      {assetPanel}
      {composerPanel}
      {historyPanel}
    </div>
    <Tabs defaultValue="create" className="xl:hidden">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="assets">素材</TabsTrigger>
        <TabsTrigger value="create">创作</TabsTrigger>
        <TabsTrigger value="history">历史</TabsTrigger>
      </TabsList>
      <TabsContent value="assets">{assetPanel}</TabsContent>
      <TabsContent value="create">{composerPanel}</TabsContent>
      <TabsContent value="history">{historyPanel}</TabsContent>
    </Tabs>
  </>
);
```

- [x] **Step 4: Replace project workspace integration**

Change import:

```typescript
import { VideoWorkflowWorkbench } from "@/components/video-workflow/VideoWorkflowWorkbench";
```

Replace `VideoGenerationRunTab` body with:

```tsx
function VideoGenerationRunTab({ projectId }: { projectId: string }) {
  return <VideoWorkflowWorkbench projectId={projectId} />;
}
```

Update its call site to pass only `projectId`. Remove the duplicate model, size, mode and full-run controls from this tab. Do not remove `videoOption` globally until `rg "videoOption" ProjectWorkspaceScreen.tsx` proves it is unused elsewhere.

- [x] **Step 5: Delete the old canvas and update assertions**

Remove the old file. Update contract test to assert:

```typescript
assert(!workspace.includes("VideoWorkflowCanvas"), "old canvas must be removed");
assert(!workbench.includes("@xyflow/react"), "new workbench must not use ReactFlow");
assert(workbench.includes("useVideoWorkflowPolling"), "workbench must auto-poll");
```

- [x] **Step 6: Run checks**

```bash
cd apps/web
bun src/lib/video-workflow-contract.test.ts
bun src/lib/video-workflow-utils.test.ts
bunx tsc --noEmit
bun run lint
bun run build
```

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add apps/web/src/components/video-workflow apps/web/src/components/screens/ProjectWorkspaceScreen.tsx apps/web/src/lib/video-workflow-contract.test.ts
git commit -m "feat(video): replace canvas with project Flow workbench"
```

## Task 10: Add Browser E2E and Real API Smoke

**Files:**
- Modify: `apps/web/package.json`
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/video-workbench.spec.ts`
- Create: `scripts/video_workbench_real_smoke.py`
- Modify: `apps/api/README.md`

- [x] **Step 1: Add test scripts and Playwright**

Run:

```bash
cd apps/web
bun add -d @playwright/test
```

Add scripts:

```json
{
  "test:contracts": "bun src/lib/video-workflow-contract.test.ts && bun src/lib/video-workflow-utils.test.ts",
  "test:e2e": "playwright test"
}
```

- [x] **Step 2: Configure Playwright**

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
```

- [x] **Step 3: Add workbench E2E**

Use a stateful browser API fixture so the UI test does not spend real credits:

```typescript
import { expect, type Page, test } from "@playwright/test";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+XcIYAAAAAElFTkSuQmCC",
  "base64",
);

async function mockVideoWorkflowApi(page: Page) {
  let assets: Array<Record<string, unknown>> = [];
  let runs: Array<Record<string, unknown>> = [];
  let syncCount = 0;
  await page.route("**/api/backend/projects/**/video-workflow**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const ok = (data: unknown) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data }),
    });

    if (path.endsWith("/content") && path.includes("/assets/")) {
      return route.fulfill({ status: 200, contentType: "image/png", body: PNG });
    }
    if (path.endsWith("/content") && path.includes("/runs/")) {
      return route.fulfill({ status: 200, contentType: "video/mp4", body: "test-video" });
    }
    if (path.endsWith("/download")) {
      return route.fulfill({
        status: 200,
        contentType: "video/mp4",
        headers: { "Content-Disposition": 'attachment; filename="test.mp4"' },
        body: "test-video",
      });
    }
    if (request.method() === "POST" && path.endsWith("/assets")) {
      assets = ["a", "b", "c"].map((suffix, index) => ({
        asset_id: `vref_${suffix}`,
        filename: `reference-${suffix}.png`,
        path: `video_workflow/references/reference-${suffix}.png`,
        mime_type: "image/png",
        byte_size: PNG.length,
        width: 1,
        height: 1,
        created_at: new Date(Date.now() + index).toISOString(),
        deleted_at: null,
      }));
      return ok({ assets, uploaded: assets, errors: [], max_reference_images: 7 });
    }
    if (request.method() === "POST" && path.endsWith("/runs")) {
      const payload = request.postDataJSON();
      const run = {
        run_id: "task_e2e",
        client_request_id: payload.client_request_id,
        retry_of_run_id: null,
        project_id: "demo",
        status: "queued",
        download_status: "not_started",
        progress: 0,
        prompt: payload.prompt,
        model: "omni_flash-10s",
        size: "1280x720",
        duration_sec: 10,
        reference_asset_ids: payload.reference_asset_ids,
        provider_task_id: "remote_e2e",
        error_code: null,
        error_message: null,
        retryable: false,
        video_ready: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      runs = [run];
      return ok(run);
    }
    if (request.method() === "POST" && path.endsWith("/sync")) {
      syncCount += 1;
      runs = runs.map((run) => ({
        ...run,
        status: syncCount >= 2 ? "completed" : "processing",
        progress: syncCount >= 2 ? 100 : 50,
        download_status: syncCount >= 2 ? "downloaded" : "not_started",
        video_ready: syncCount >= 2,
      }));
      return ok(runs[0]);
    }
    if (request.method() === "GET" && path.endsWith("/runs")) return ok(runs);
    if (request.method() === "GET" && path.endsWith("/video-workflow")) {
      return ok({
        project_id: "demo",
        config: {
          model: "omni_flash-10s",
          size: "1280x720",
          duration_sec: 10,
          max_reference_images: 7,
          max_project_assets: 50,
          max_asset_bytes: 10485760,
          poll_interval_ms: 50,
          provider_ready: true,
        },
        assets,
        runs,
      });
    }
    return route.fallback();
  });
}

test("project video workbench completes the core flow", async ({ page }) => {
  await mockVideoWorkflowApi(page);
  await loginAndOpenProject(page);
  await page.getByRole("tab", { name: /视频生成/ }).click();
  await expect(page.getByText("项目素材")).toBeVisible();

  await page.getByLabel("上传参考图").setInputFiles(
    ["a", "b", "c"].map((name) => ({
      name: `reference-${name}.png`,
      mimeType: "image/png",
      buffer: PNG,
    })),
  );
  await expect(page.getByText("已选 3 / 7")).toBeVisible();

  await page.getByLabel("视频提示词").fill(
    "卡通三角形积木逐渐组合成一座桥，固定镜头，温暖课堂插画风格。",
  );
  await page.getByRole("button", { name: "生成 10 秒视频" }).click();
  await expect(page.getByText(/queued|processing/)).toBeVisible();
  await expect(page.locator("video")).toBeVisible({ timeout: 30_000 });

  await page.reload();
  await expect(page.getByText("项目概览")).toBeVisible();
  await page.getByRole("button", { name: "进入工作区" }).first().click();
  await page.getByRole("tab", { name: /视频生成/ }).click();
  await expect(page.locator("video")).toBeVisible();
  await page.getByRole("button", { name: "复用参数" }).first().click();
  await expect(page.getByLabel("视频提示词")).toHaveValue(/三角形积木/);
});
```

Define the helper in the same test file:

```typescript
async function loginAndOpenProject(page: Page) {
  await page.goto("/");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill("shanhai2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByText("项目概览")).toBeVisible();
  await page.getByRole("button", { name: "进入工作区" }).first().click();
}
```

Run this E2E with `NEXT_PUBLIC_DEMO_MODE=true`. The page route above is the fake video backend; all other application requests keep their normal behavior.

- [x] **Step 4: Add opt-in real smoke**

The script must:

```python
from __future__ import annotations

import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx


def unwrap(response: httpx.Response) -> Any:
    response.raise_for_status()
    payload = response.json()
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload.get("error") or payload, ensure_ascii=False))
    return payload["data"]


def main() -> int:
    base_url = os.environ["SHANHAI_API_BASE_URL"].rstrip("/")
    api_token = os.environ["BACKEND_API_TOKEN"]
    project_id = os.environ["VIDEO_SMOKE_PROJECT_ID"]
    image_paths = [Path(item) for item in os.environ["VIDEO_SMOKE_IMAGES"].split(os.pathsep)]
    prompt = os.getenv(
        "VIDEO_SMOKE_PROMPT",
        "卡通三角形积木逐渐组合成一座桥，固定镜头，温暖课堂插画风格。",
    )
    headers = {"Authorization": f"Bearer {api_token}"}
    files = [
        ("files", (path.name, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "image/png"))
        for path in image_paths
    ]
    uploaded = unwrap(httpx.post(
        f"{base_url}/projects/{project_id}/video-workflow/assets",
        headers=headers,
        files=files,
        timeout=60,
    ))
    run = unwrap(httpx.post(
        f"{base_url}/projects/{project_id}/video-workflow/runs",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "client_request_id": str(uuid.uuid4()),
            "prompt": prompt,
            "reference_asset_ids": [item["asset_id"] for item in uploaded["assets"][-len(files):]],
        },
        timeout=60,
    ))
    deadline = time.monotonic() + 20 * 60
    while time.monotonic() < deadline:
        run = unwrap(httpx.post(
            f"{base_url}/projects/{project_id}/video-workflow/runs/{run['run_id']}/sync",
            headers=headers,
            json={},
            timeout=180,
        ))
        print(json.dumps({
            "run_id": run["run_id"],
            "status": run["status"],
            "progress": run["progress"],
            "video_ready": run["video_ready"],
        }, ensure_ascii=False))
        if run["status"] in {"completed", "failed", "submission_unknown"}:
            return 0 if run["status"] == "completed" and run["video_ready"] else 1
        time.sleep(5)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 5: Document configuration and smoke invocation**

Add:

```bash
SHANHAI_API_BASE_URL=http://127.0.0.1:8000 \
BACKEND_API_TOKEN=... \
VIDEO_SMOKE_PROJECT_ID=project_xxx \
VIDEO_SMOKE_IMAGES="/path/a.png:/path/b.png" \
python scripts/video_workbench_real_smoke.py
```

State clearly that `OCTO_API_KEY` remains server-side and the smoke script calls ShanHai API, not the provider directly.

- [x] **Step 6: Run E2E in fake-provider environment**

```bash
cd apps/web
bunx playwright install chromium
bun run test:e2e -- e2e/video-workbench.spec.ts
```

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add apps/web/package.json apps/web/bun.lock apps/web/playwright.config.ts apps/web/e2e scripts/video_workbench_real_smoke.py apps/api/README.md
git commit -m "test(video): add workbench e2e and real Omni smoke"
```

## Task 11: Full Verification and Handoff

**Files:**
- Modify only if verification reveals a defect.

- [x] **Step 1: Run backend regression**

```bash
python -m pytest apps/api/tests -q
```

Expected: all tests PASS.

- [x] **Step 2: Run frontend regression**

```bash
cd apps/web
bun run test:contracts
bunx tsc --noEmit
bun run lint
bun run build
```

Expected: all commands PASS.

- [x] **Step 3: Run browser E2E**

```bash
cd apps/web
bun run test:e2e -- e2e/video-workbench.spec.ts
```

Expected: PASS with no failed screenshots or traces.

- [x] **Step 4: Run security checks**

```bash
cd apps/web
bun run scan:client-secrets
rg -n "OCTO_API_KEY|Authorization.*Bearer" src
```

Expected: secret scan PASS; `rg` shows no embedded key or client-side provider Authorization header.

- [x] **Step 5: Run the real smoke once**

Use the documented command with a controlled account and non-sensitive reference images.

Expected:

- One provider task only.
- Terminal state `completed`.
- `video_ready=true`.
- Local MP4 exists and is non-empty.

Status: completed with one real `omni_flash-10s` provider task through the ShanHai backend API. The run reached `completed`, `video_ready=true`, and downloaded a non-empty MP4. See `docs/qa-audits/2026-06-29-google-flow-video-workbench-verification.md`.

- [x] **Step 6: Verify the 13 acceptance items**

Use the checklist in the design spec, recording pass/fail evidence for each item. Do not mark complete if any item is unverified.

Evidence recorded in `docs/qa-audits/2026-06-29-google-flow-video-workbench-verification.md`. Items that require real provider execution remain explicitly marked as pending credentials/smoke rather than passed.

- [x] **Step 7: Final commit if verification required fixes**

```bash
git add apps/api/app/video_workflow.py apps/api/app/providers.py apps/api/app/main.py apps/api/app/store.py apps/web/src/components/video-workflow apps/web/src/components/screens/ProjectWorkspaceScreen.tsx apps/web/src/lib/types.ts apps/web/src/lib/api-client.ts apps/web/src/lib/store.ts
git commit -m "fix(video): close workbench acceptance gaps"
```

## Spec Coverage Matrix

| Specification area | Implementation tasks |
|---|---|
| Project asset upload, validation, soft delete | Tasks 1 and 5 |
| Ordered 0-7 Omni references and real MIME | Tasks 2, 3, 7 and 8 |
| Fixed server-owned Omni configuration | Tasks 3 and 6 |
| Idempotency and submission uncertainty | Task 3 |
| Run states, automatic sync and atomic download | Tasks 4, 5 and 7 |
| History, preview, download, retry and reuse | Tasks 5, 8 and 9 |
| Three-panel responsive project UI | Tasks 8 and 9 |
| Project isolation and restart persistence | Tasks 1, 3, 4 and 5 |
| Backend, frontend, E2E and real smoke evidence | Tasks 1-11 |

The implementation is incomplete if a specification row has code but lacks its corresponding automated or real-smoke evidence.

## Implementation Guardrails

- Do not modify the admin media workbench except to keep compilation working.
- Do not create a second project video service.
- Do not expose API keys or provider URLs to the browser.
- Do not mark placeholder tasks as completed.
- Do not automatically retry an uncertain submission.
- Do not store provider URLs as the permanent playback source.
- Do not make model, resolution, duration or output count editable in this phase.
- Do not retain ReactFlow controls in the new user-facing workbench.
- Do not delete historical asset files when users remove them from the active library.
- Do not claim completion without the real API smoke evidence.
