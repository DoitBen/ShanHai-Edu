from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from .providers import ProviderError, sanitize_provider_excerpt
from .store import ProjectStore, now_iso

logger = logging.getLogger(__name__)

VIDEO_MODEL = "omni_flash-10s"
VIDEO_SIZE = "1280x720"
VIDEO_DURATION_SEC = 10
MAX_REFERENCE_IMAGES = 7
MAX_PROJECT_ASSETS = 50
MAX_ASSET_BYTES = int(os.getenv("VIDEO_REFERENCE_MAX_BYTES", str(10 * 1024 * 1024)))
MAX_IMAGE_WIDTH = int(os.getenv("VIDEO_REFERENCE_MAX_WIDTH", "8192"))
MAX_IMAGE_HEIGHT = int(os.getenv("VIDEO_REFERENCE_MAX_HEIGHT", "8192"))
MAX_IMAGE_PIXELS = int(os.getenv("VIDEO_REFERENCE_MAX_PIXELS", str(50_000_000)))
MAX_VIDEO_DOWNLOAD_BYTES = int(os.getenv("VIDEO_WORKFLOW_MAX_VIDEO_DOWNLOAD_BYTES", str(512 * 1024 * 1024)))
PROJECT_REFERENCE_QUOTA_BYTES = int(os.getenv("VIDEO_WORKFLOW_REFERENCE_QUOTA_BYTES", str(512 * 1024 * 1024)))
SOFT_DELETE_RETENTION_DAYS = int(os.getenv("VIDEO_WORKFLOW_SOFT_DELETE_RETENTION_DAYS", "30"))
FAILED_RUN_RETENTION_DAYS = int(os.getenv("VIDEO_WORKFLOW_FAILED_RUN_RETENTION_DAYS", "30"))
TEMPORARY_FILE_RETENTION_HOURS = int(os.getenv("VIDEO_WORKFLOW_TEMP_FILE_RETENTION_HOURS", "24"))
RUN_CREATE_WINDOW_SECONDS = int(os.getenv("VIDEO_WORKFLOW_RUN_CREATE_WINDOW_SECONDS", "3600"))
RUN_CREATE_PROJECT_WINDOW_LIMIT = int(os.getenv("VIDEO_WORKFLOW_PROJECT_CREATE_LIMIT", "6"))
RUN_CREATE_GLOBAL_WINDOW_LIMIT = int(os.getenv("VIDEO_WORKFLOW_GLOBAL_CREATE_LIMIT", "20"))
POLL_INTERVAL_MS = 4000
MIN_PROVIDER_SYNC_INTERVAL_SEC = float(os.getenv("VIDEO_WORKFLOW_MIN_SYNC_INTERVAL_SEC", "3"))
SUBMISSION_LEASE_SECONDS = int(os.getenv("VIDEO_WORKFLOW_SUBMISSION_LEASE_SECONDS", "300"))
PENDING_URL_TIMEOUT_SECONDS = int(os.getenv("VIDEO_WORKFLOW_PENDING_URL_TIMEOUT_SECONDS", "1800"))
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}
TERMINAL_RUN_STATES = {"completed", "failed", "submission_unknown"}
RUN_STATUS_RANK = {
    "queued": 10,
    "submitting": 20,
    "processing": 30,
    "completed_pending_download": 40,
    "completed": 100,
    "failed": 100,
    "submission_unknown": 100,
}
PROVIDER_STATUS_ALIASES = {
    "pending": "queued",
    "submitted": "queued",
    "queued": "queued",
    "running": "processing",
    "runing": "processing",
    "in_progress": "processing",
    "processing": "processing",
    "success": "completed",
    "succeeded": "completed",
    "completed": "completed",
    "failed": "failed",
    "failure": "failed",
    "error": "failed",
}


DEFAULT_VIDEO_WORKFLOW_GRAPH: dict[str, Any] = {
    "nodes": [
        {"id": "prompt", "type": "prompt_input", "position": {"x": 40, "y": 120}, "data": {"label": "文本提示词输入"}},
        {"id": "references", "type": "reference_input", "position": {"x": 40, "y": 300}, "data": {"label": "参考图输入"}},
        {"id": "model", "type": "omni_model", "position": {"x": 360, "y": 180}, "data": {"label": "Omni 视频模型"}},
        {"id": "output", "type": "video_output", "position": {"x": 680, "y": 180}, "data": {"label": "视频输出"}},
    ],
    "edges": [
        {"id": "prompt-model", "source": "prompt", "target": "model"},
        {"id": "references-model", "source": "references", "target": "model"},
        {"id": "model-output", "source": "model", "target": "output"},
    ],
    "selected_model": "omni_flash-10s",
    "mode": "text",
    "duration_sec": 10,
    "size": "1280x720",
}


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
    except Image.DecompressionBombError as exc:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图像素过大，请压缩后重新上传") from exc
    except Image.DecompressionBombWarning as exc:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图像素过大，请压缩后重新上传") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "文件不是有效图片") from exc
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "仅支持 JPG、PNG、WebP 图片")
    if width <= 0 or height <= 0:
        raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图宽高无效")
    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise VideoWorkflowError(
            "VIDEO_REFERENCE_INVALID",
            f"参考图宽高不能超过 {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}",
            details={"max_width": MAX_IMAGE_WIDTH, "max_height": MAX_IMAGE_HEIGHT, "width": width, "height": height},
        )
    pixels = int(width) * int(height)
    if pixels > MAX_IMAGE_PIXELS:
        raise VideoWorkflowError(
            "VIDEO_REFERENCE_INVALID",
            f"参考图像素总数不能超过 {MAX_IMAGE_PIXELS}",
            details={"max_pixels": MAX_IMAGE_PIXELS, "pixels": pixels, "width": width, "height": height},
        )
    mime_type, extension = ALLOWED_IMAGE_FORMATS[image_format]
    return mime_type, extension, int(width), int(height)


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _write_json_snapshot_best_effort(path: Path, value: Any, *, operation: str) -> None:
    try:
        _write_json_atomic(path, value)
    except OSError as exc:
        logger.warning(
            "video_workflow_json_snapshot_failed operation=%s error_type=%s",
            operation,
            type(exc).__name__,
        )


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


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _future_iso(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _elapsed_ms(start: Any, end: datetime | None = None) -> int:
    started_at = _parse_iso(start)
    if started_at is None:
        return 0
    finished_at = end or datetime.now(timezone.utc)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def _duration_ms(start: datetime, end: datetime | None = None) -> int:
    finished_at = end or datetime.now(timezone.utc)
    return max(0, int((finished_at - start).total_seconds() * 1000))


def _is_timed_out(start: Any, timeout_seconds: int, *, now: datetime | None = None) -> bool:
    started_at = _parse_iso(start)
    if started_at is None:
        return False
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (current - started_at).total_seconds() >= timeout_seconds


def _percent(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0
    return round((float(numerator) / float(denominator)) * 100, 2)


def _clean_provider_result(value: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "provider_task_id",
        "progress",
        "remix_id",
        "error_code",
        "error_message",
        "response_excerpt",
        "retryable",
    }
    cleaned: dict[str, Any] = {}
    for key in allowed:
        if key in value and value[key] is not None:
            cleaned[key] = value[key]
    if "response_excerpt" in cleaned:
        cleaned["response_excerpt"] = sanitize_provider_excerpt(str(cleaned["response_excerpt"]))
    if value.get("status") is not None:
        cleaned["provider_status"] = str(value["status"])
    return cleaned


def _normalize_provider_status(status: Any, *, fallback: str) -> str:
    raw = str(status or "").strip().lower()
    if not raw:
        return fallback
    normalized = PROVIDER_STATUS_ALIASES.get(raw)
    if normalized:
        return normalized
    return "processing" if fallback in {"queued", "submitting", "processing"} else fallback


def _inspect_downloaded_mp4(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ProviderError("VIDEO_DOWNLOAD_FAILED", "视频下载结果为空", retryable=True)
    byte_size = path.stat().st_size
    if byte_size > MAX_VIDEO_DOWNLOAD_BYTES:
        raise ProviderError("VIDEO_DOWNLOAD_TOO_LARGE", "视频文件超过下载大小限制", retryable=False)
    with path.open("rb") as handle:
        header = handle.read(32)
    if len(header) < 12 or b"ftyp" not in header[4:16]:
        raise ProviderError("VIDEO_DOWNLOAD_INVALID", "下载结果不是有效 MP4 文件", retryable=True)
    return {"download_bytes": byte_size, "download_sha256": _sha256_file(path)}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class VideoWorkflowError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        action: str | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details
        self.action = action
        self.retryable = retryable


class VideoWorkflowService:
    def __init__(
        self,
        *,
        store: ProjectStore,
        capabilities_path: Path,
        video_provider: Any | None,
        provider_readiness: dict[str, Any] | None = None,
    ):
        self.store = store
        self.capabilities_path = capabilities_path
        self.video_provider = video_provider
        self.provider_readiness = provider_readiness or self._provider_readiness_from_provider()
        self._run_locks: dict[str, threading.Lock] = {}
        self._run_locks_guard = threading.Lock()
        self._create_locks: dict[str, threading.Lock] = {}
        self._create_locks_guard = threading.Lock()
        self._asset_locks: dict[str, threading.Lock] = {}
        self._asset_locks_guard = threading.Lock()
        self._observability_lock = threading.Lock()
        self._observability_events: list[dict[str, Any]] = []
        self._observability_metrics: dict[str, int | float] = {
            "provider_submit_success_count": 0,
            "provider_submit_failure_count": 0,
            "provider_submit_latency_ms_total": 0,
            "provider_submit_success_rate_percent": 0,
            "provider_query_count": 0,
            "provider_query_failure_count": 0,
            "download_success_count": 0,
            "download_failure_count": 0,
            "downloaded_video_bytes": 0,
            "duplicate_request_count": 0,
            "duplicate_request_rate_percent": 0,
            "queue_time_ms_total": 0,
            "generation_time_ms_total": 0,
            "download_time_ms_total": 0,
            "retry_count": 0,
            "retry_rate_percent": 0,
            "sync_backoff_count": 0,
            "provider_error_count": 0,
            "storage_reference_bytes": 0,
            "storage_reference_growth_bytes": 0,
        }
        self._storage_reference_baseline_bytes: dict[str, int] = {}

    def get_workflow(self, project_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        self.recover_stale_submissions(project_id)
        return {
            "project_id": project_id,
            "config": {
                "model": VIDEO_MODEL,
                "size": VIDEO_SIZE,
                "duration_sec": VIDEO_DURATION_SEC,
                "max_reference_images": MAX_REFERENCE_IMAGES,
                "max_project_assets": MAX_PROJECT_ASSETS,
                "max_asset_bytes": MAX_ASSET_BYTES,
                "poll_interval_ms": POLL_INTERVAL_MS,
                "run_create_window_seconds": RUN_CREATE_WINDOW_SECONDS,
                "run_create_project_window_limit": RUN_CREATE_PROJECT_WINDOW_LIMIT,
                "run_create_global_window_limit": RUN_CREATE_GLOBAL_WINDOW_LIMIT,
                "storage_lifecycle": self.storage_lifecycle_policy(),
                "runtime_concurrency": self.runtime_concurrency_policy(),
                **self._provider_readiness_config(),
            },
            "storage_usage": self._storage_usage_for_project_dir(project_dir),
            "graph": self._read_graph(project_dir),
            "assets": self._reference_assets(project_dir),
            "runs": self.list_runs(project_id, limit=50),
            "latest_run": self._latest_run(project_id),
            "capabilities": self._capabilities(),
        }

    def save_workflow(self, project_id: str, graph: dict[str, Any]) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        normalized = self._normalize_graph(graph)
        self._workflow_dir(project_dir).mkdir(parents=True, exist_ok=True)
        self._graph_path(project_dir).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.get_workflow(project_id)

    def upload_assets(self, project_id: str, files: list[UploadFile]) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        if not files:
            raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "请上传至少 1 张参考图")

        with self._lock_for_assets(project_id):
            all_assets = self._all_reference_assets(project_dir)
            existing = [item for item in all_assets if not item.get("deleted_at")]
            active_bytes = self._active_reference_bytes(project_dir, all_assets)
            uploaded: list[dict[str, Any]] = []
            errors: list[dict[str, str]] = []
            for file in files:
                filename = file.filename or "unnamed"
                if len(existing) + len(uploaded) >= MAX_PROJECT_ASSETS:
                    errors.append(
                        {
                            "filename": filename,
                            "code": "VIDEO_REFERENCE_LIMIT_EXCEEDED",
                            "message": f"单项目最多保存 {MAX_PROJECT_ASSETS} 张参考图",
                        }
                    )
                    continue
                try:
                    asset = self._save_one_asset(project_dir, file)
                    attempted_bytes = int(asset.get("byte_size") or 0)
                    if active_bytes + sum(int(item.get("byte_size") or 0) for item in uploaded) + attempted_bytes > PROJECT_REFERENCE_QUOTA_BYTES:
                        self._discard_asset_file(project_dir, asset)
                        raise VideoWorkflowError(
                            "VIDEO_STORAGE_QUOTA_EXCEEDED",
                            "项目视频参考图存储空间已达上限，请先清理不再使用的参考图",
                            status_code=413,
                            details={
                                "quota_bytes": PROJECT_REFERENCE_QUOTA_BYTES,
                                "current_bytes": active_bytes + sum(int(item.get("byte_size") or 0) for item in uploaded),
                                "attempted_bytes": attempted_bytes,
                            },
                        )
                    uploaded.append(asset)
                except VideoWorkflowError as exc:
                    if exc.code == "VIDEO_STORAGE_QUOTA_EXCEEDED" and not uploaded:
                        raise
                    errors.append({"filename": filename, "code": exc.code, "message": str(exc)})
            if not uploaded and errors:
                first = errors[0]
                raise VideoWorkflowError(first["code"], first["message"])
            self._upsert_asset_metadata(project_dir, project_id, uploaded)
            next_assets = self._all_reference_assets(project_dir)
            _write_json_snapshot_best_effort(self._assets_path(project_dir), next_assets, operation="upload_assets")
            return {
                "assets": [item for item in next_assets if not item.get("deleted_at")],
                "uploaded": uploaded,
                "errors": errors,
                "max_reference_images": MAX_REFERENCE_IMAGES,
                "storage_usage": self._storage_usage_for_assets(project_dir, next_assets),
            }

    def asset(self, project_id: str, asset_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        project_dir = Path(self.store.get_project(project_id)["project_dir"])
        for item in self._all_reference_assets(project_dir):
            if item["asset_id"] == asset_id and (include_deleted or not item.get("deleted_at")):
                return item
        raise KeyError(asset_id)

    def delete_asset(self, project_id: str, asset_id: str) -> dict[str, Any]:
        project_dir = Path(self.store.get_project(project_id)["project_dir"])
        with self._lock_for_assets(project_id):
            try:
                self.asset(project_id, asset_id)
            except KeyError:
                raise KeyError(asset_id)
            self._mark_asset_metadata_deleted(project_dir, asset_id)
            assets = self._all_reference_assets(project_dir)
            _write_json_snapshot_best_effort(self._assets_path(project_dir), assets, operation="delete_asset")
        return {"asset_id": asset_id, "deleted": True}

    def create_run(
        self,
        project_id: str,
        payload: dict[str, Any],
        *,
        allow_deleted_assets: bool = False,
        retry_of_run_id: str | None = None,
    ) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        canonical = self._canonical_run_payload(payload)
        if retry_of_run_id:
            canonical["retry_of_run_id"] = retry_of_run_id
        references = [
            self.asset(project_id, asset_id, include_deleted=allow_deleted_assets)
            for asset_id in canonical["reference_asset_ids"]
        ]
        self._ensure_reference_files_available(project_dir, references)
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

        if self.video_provider is None:
            raise VideoWorkflowError("VIDEO_PROVIDER_NOT_CONFIGURED", "视频生成服务未连接")

        with self._lock_for_create(project_id, canonical["client_request_id"]):
            existing = self._return_existing_run_or_conflict(
                project_id,
                canonical["client_request_id"],
                canonical,
            )
            if existing:
                self._record_observability_event(
                    "idempotency_reused",
                    project_id=project_id,
                    run_id=existing["run_id"],
                    status=existing["status"],
                )
                return existing
            active = self._active_run(project_id)
            if active:
                raise VideoWorkflowError(
                    "VIDEO_ACTIVE_RUN_EXISTS",
                    "当前项目已有视频任务正在生成，请等待完成后再创建新任务",
                    status_code=409,
                    action="wait_for_active_run",
                )
            self._enforce_create_rate_limits(project_id)
            with self.store.connect(project_dir) as conn:
                try:
                    task = self.store.create_task(
                        conn,
                        project_id,
                        "video_workflow",
                        "video_workflow_generation",
                        canonical,
                        status="submitting",
                        result={
                            "provider_phase": "submit",
                            "download_status": "not_started",
                            "submission_started_at": now_iso(),
                            "submission_attempt": 1,
                            "submission_lease_expires_at": _future_iso(SUBMISSION_LEASE_SECONDS),
                        },
                        client_request_id=canonical["client_request_id"],
                    )
                except sqlite3.IntegrityError:
                    conn.rollback()
                    existing = self._return_existing_run_or_conflict(
                        project_id,
                        canonical["client_request_id"],
                        canonical,
                    )
                    if existing:
                        return existing
                    raise
                try:
                    submit_started_at = datetime.now(timezone.utc)
                    submitted = self.video_provider.submit_video(submit_payload)
                except ProviderError as exc:
                    submit_latency_ms = _duration_ms(submit_started_at)
                    error_code, message, retryable, status = _submission_failure(exc)
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
                    self._record_observability_event(
                        "provider_submit_failed",
                        project_id=project_id,
                        run_id=task["task_id"],
                        status=status,
                        error_code=error_code,
                        retryable=retryable,
                        submit_latency_ms=submit_latency_ms,
                        queue_time_ms=_elapsed_ms(task["created_at"]),
                    )
                    return self._decorate_run(updated)
                submit_latency_ms = _duration_ms(submit_started_at)
                submitted_status = _normalize_provider_status(submitted.get("status"), fallback="queued")
                updated = self.store.update_task(
                    conn,
                    task["task_id"],
                    submitted_status,
                    {
                        **_clean_provider_result(submitted),
                        "provider_phase": "submit",
                        "download_status": "not_started",
                        "duration_sec": VIDEO_DURATION_SEC,
                        "model": VIDEO_MODEL,
                    },
                )
                self._record_observability_event(
                    "provider_submit_succeeded",
                    project_id=project_id,
                    run_id=task["task_id"],
                    status=submitted_status,
                    provider_task_id=submitted.get("provider_task_id"),
                    provider_status=submitted.get("status"),
                    progress=int(submitted.get("progress") or 0),
                    submit_latency_ms=submit_latency_ms,
                    queue_time_ms=_elapsed_ms(task["created_at"]),
                )
            return self._decorate_run(updated)

    def get_run(self, project_id: str, run_id: str) -> dict[str, Any]:
        self.recover_stale_submissions(project_id)
        return self._decorate_run(self.store.task(project_id, run_id))

    def _lock_for_create(self, project_id: str, request_id: str) -> threading.Lock:
        key = f"{project_id}:{request_id}"
        with self._create_locks_guard:
            lock = self._create_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._create_locks[key] = lock
            return lock

    def _lock_for_run(self, project_id: str, run_id: str) -> threading.Lock:
        key = f"{project_id}:{run_id}"
        with self._run_locks_guard:
            lock = self._run_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._run_locks[key] = lock
            return lock

    def _lock_for_assets(self, project_id: str) -> threading.Lock:
        with self._asset_locks_guard:
            lock = self._asset_locks.get(project_id)
            if lock is None:
                lock = threading.Lock()
                self._asset_locks[project_id] = lock
            return lock

    def _record_observability_event(self, event: str, **fields: Any) -> None:
        safe_event: dict[str, Any] = {
            "event": event,
            "trace_id": f"trace_{uuid.uuid4().hex[:12]}",
            "created_at": now_iso(),
        }
        allowed_fields = {
            "project_id",
            "run_id",
            "status",
            "provider_task_id",
            "provider_status",
            "progress",
            "error_code",
            "retryable",
            "download_bytes",
        }
        for key in allowed_fields:
            value = fields.get(key)
            if value is not None:
                safe_event[key] = value
        with self._observability_lock:
            self._observability_events.append(safe_event)
            if len(self._observability_events) > 500:
                self._observability_events = self._observability_events[-500:]
            if event == "provider_submit_succeeded":
                self._observability_metrics["provider_submit_success_count"] += 1
                self._observability_metrics["provider_submit_latency_ms_total"] += int(
                    fields.get("submit_latency_ms") or 0
                )
                self._observability_metrics["queue_time_ms_total"] += int(fields.get("queue_time_ms") or 0)
            elif event == "provider_submit_failed":
                self._observability_metrics["provider_submit_failure_count"] += 1
                self._observability_metrics["provider_submit_latency_ms_total"] += int(
                    fields.get("submit_latency_ms") or 0
                )
                self._observability_metrics["queue_time_ms_total"] += int(fields.get("queue_time_ms") or 0)
                self._observability_metrics["provider_error_count"] += 1
            elif event == "provider_query_completed":
                self._observability_metrics["provider_query_count"] += 1
                self._observability_metrics["generation_time_ms_total"] += int(
                    fields.get("generation_time_ms") or 0
                )
            elif event == "provider_query_failed":
                self._observability_metrics["provider_query_failure_count"] += 1
                self._observability_metrics["provider_error_count"] += 1
            elif event == "video_download_succeeded":
                self._observability_metrics["download_success_count"] += 1
                self._observability_metrics["downloaded_video_bytes"] += int(fields.get("download_bytes") or 0)
                self._observability_metrics["download_time_ms_total"] += int(fields.get("download_time_ms") or 0)
            elif event == "video_download_failed":
                self._observability_metrics["download_failure_count"] += 1
                self._observability_metrics["download_time_ms_total"] += int(fields.get("download_time_ms") or 0)
            elif event == "idempotency_reused":
                self._observability_metrics["duplicate_request_count"] += 1
            elif event == "video_run_retry_requested":
                self._observability_metrics["retry_count"] += 1
            elif event == "provider_sync_backoff":
                self._observability_metrics["sync_backoff_count"] += 1

    def observability_snapshot(self, project_id: str | None = None) -> dict[str, Any]:
        with self._observability_lock:
            events = list(self._observability_events)
            metrics = dict(self._observability_metrics)
        if project_id is not None:
            events = [event for event in events if event.get("project_id") == project_id]
            usage = self.storage_usage(project_id)
            reference_bytes = int(usage.get("reference_asset_bytes") or 0)
            baseline = self._storage_reference_baseline_bytes.setdefault(project_id, reference_bytes)
            metrics["storage_reference_bytes"] = reference_bytes
            metrics["storage_reference_growth_bytes"] = max(0, reference_bytes - baseline)
        provider_submit_total = int(metrics.get("provider_submit_success_count") or 0) + int(
            metrics.get("provider_submit_failure_count") or 0
        )
        total_create_attempts = provider_submit_total + int(metrics.get("duplicate_request_count") or 0)
        retry_total = int(metrics.get("retry_count") or 0)
        metrics["provider_submit_success_rate_percent"] = _percent(
            int(metrics.get("provider_submit_success_count") or 0),
            provider_submit_total,
        )
        metrics["duplicate_request_rate_percent"] = _percent(
            int(metrics.get("duplicate_request_count") or 0),
            total_create_attempts,
        )
        metrics["retry_rate_percent"] = _percent(retry_total, total_create_attempts + retry_total)
        return {
            "metrics": metrics,
            "events": events,
            "event_retention": {"type": "in_memory_ring_buffer", "max_events": 500},
            "redaction": {
                "stores_provider_raw": False,
                "stores_signed_media_locator": False,
                "stores_authorization_header": False,
            },
        }

    @staticmethod
    def _monotonic_status(current_status: str, remote_status: str) -> str:
        current_rank = RUN_STATUS_RANK.get(current_status, 0)
        remote_rank = RUN_STATUS_RANK.get(remote_status, 0)
        if current_rank >= remote_rank:
            return current_status
        return remote_status

    def sync_run(self, project_id: str, run_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        self.recover_stale_submissions(project_id)
        with self._lock_for_run(project_id, run_id):
            task = self.store.task(project_id, run_id)
            result = dict(task.get("result") or {})
            if task["status"] == "completed" and result.get("download_status") == "downloaded":
                rel_path = result.get("download_path")
                if rel_path and (not result.get("download_bytes") or not result.get("download_sha256")):
                    target = project_dir / str(rel_path)
                    metadata = _inspect_downloaded_mp4(target)
                    result = {**result, **metadata}
                    with self.store.connect(project_dir) as conn:
                        task = self.store.update_task(conn, run_id, "completed", result, task.get("error_message"))
                return self._decorate_run(task)
            if self.video_provider is None:
                return self._decorate_run(task)
            provider_task_id = result.get("provider_task_id") or task.get("provider_task_id")
            if not provider_task_id:
                return self._decorate_run(task)
            last_synced_at = _parse_iso(result.get("last_provider_sync_at"))
            if last_synced_at is not None:
                elapsed = (datetime.now(timezone.utc) - last_synced_at).total_seconds()
                if elapsed < MIN_PROVIDER_SYNC_INTERVAL_SEC:
                    self._record_observability_event(
                        "provider_sync_backoff",
                        project_id=project_id,
                        run_id=run_id,
                        status=task["status"],
                        provider_task_id=provider_task_id,
                    )
                    return self._decorate_run(task)
            try:
                remote = self.video_provider.query_task(provider_task_id)
            except ProviderError as exc:
                self._record_observability_event(
                    "provider_query_failed",
                    project_id=project_id,
                    run_id=run_id,
                    status=task["status"],
                    provider_task_id=provider_task_id,
                    error_code=exc.code,
                    retryable=exc.retryable,
                )
                raise
            raw_remote_status = remote.get("status")
            remote_status = _normalize_provider_status(raw_remote_status, fallback=task["status"])
            status = self._monotonic_status(task["status"], remote_status)
            self._record_observability_event(
                "provider_query_completed",
                project_id=project_id,
                run_id=run_id,
                status=status,
                provider_task_id=provider_task_id,
                provider_status=raw_remote_status,
                progress=int(remote.get("progress") or 0),
                generation_time_ms=_elapsed_ms(
                    result.get("submission_started_at") or task["created_at"]
                )
                if status in TERMINAL_RUN_STATES
                else 0,
            )
            merged = {
                **result,
                **_clean_provider_result(remote),
                "provider_phase": "query",
                "last_provider_sync_at": now_iso(),
            }
            if raw_remote_status and str(raw_remote_status).strip().lower() not in PROVIDER_STATUS_ALIASES:
                merged["response_excerpt"] = sanitize_provider_excerpt(
                    str(merged.get("response_excerpt") or f"unknown provider status: {raw_remote_status}")
                )
            if (
                task["status"] == "completed"
                and RUN_STATUS_RANK.get(remote_status, 0) < RUN_STATUS_RANK["completed"]
            ):
                status = "completed"
                merged["progress"] = max(int(result.get("progress") or 0), int(remote.get("progress") or 0))
                if result.get("download_path"):
                    merged["download_path"] = result["download_path"]
                if result.get("download_status"):
                    merged["download_status"] = result["download_status"]
            if (
                status == "completed"
                and remote_status == "completed"
                and not remote.get("video_url")
                and merged.get("download_status") != "downloaded"
            ):
                pending_started_at = merged.get("pending_url_started_at") or now_iso()
                merged["pending_url_started_at"] = pending_started_at
                merged["progress"] = max(int(result.get("progress") or 0), int(remote.get("progress") or 0), 100)
                if _is_timed_out(pending_started_at, PENDING_URL_TIMEOUT_SECONDS):
                    status = "failed"
                    merged.update(
                        {
                            "download_status": "download_failed",
                            "error_code": "VIDEO_URL_TIMEOUT",
                            "retryable": True,
                        }
                    )
                    with self.store.connect(project_dir) as conn:
                        updated = self.store.update_task(
                            conn,
                            run_id,
                            "failed",
                            merged,
                            "视频生成已完成，但获取视频文件超时",
                        )
                    return self._decorate_run(updated)
                status = "completed_pending_download"
                merged["download_status"] = "pending_url"
            if status == "completed" and remote.get("video_url"):
                relative = f"video_workflow/runs/{run_id}.mp4"
                target = project_dir / relative
                download_started_at = datetime.now(timezone.utc)
                try:
                    if not target.is_file() or target.stat().st_size == 0:
                        temp = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.mp4.part")
                        temp.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            self.video_provider.download_video(remote["video_url"], temp)
                            metadata = _inspect_downloaded_mp4(temp)
                        except ProviderError:
                            temp.unlink(missing_ok=True)
                            raise
                        os.replace(temp, target)
                    else:
                        metadata = _inspect_downloaded_mp4(target)
                except ProviderError as exc:
                    self._record_observability_event(
                        "video_download_failed",
                        project_id=project_id,
                        run_id=run_id,
                        status="completed",
                        provider_task_id=provider_task_id,
                        error_code=exc.code,
                        retryable=True,
                        download_time_ms=_duration_ms(download_started_at),
                    )
                    failed_download = {
                        **merged,
                        "download_path": relative,
                        "download_status": "download_failed",
                        "error_code": exc.code,
                        "retryable": True,
                    }
                    with self.store.connect(project_dir) as conn:
                        updated = self.store.update_task(conn, run_id, "completed", failed_download, str(exc))
                    return self._decorate_run(updated)
                merged.update({"download_path": relative, "download_status": "downloaded", **metadata})
                self._record_observability_event(
                    "video_download_succeeded",
                    project_id=project_id,
                    run_id=run_id,
                    status="completed",
                    provider_task_id=provider_task_id,
                    download_bytes=metadata["download_bytes"],
                    download_time_ms=_duration_ms(download_started_at),
                )
            with self.store.connect(project_dir) as conn:
                updated = self.store.update_task(
                    conn,
                    run_id,
                    status,
                    merged,
                    remote.get("error_message"),
                )
            return self._decorate_run(updated)

    def retry_run(self, project_id: str, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        original = self.store.task(project_id, run_id)
        if original["task_type"] != "video_workflow_generation":
            raise KeyError(run_id)
        result = dict(original.get("result") or {})
        status = str(original.get("status") or "")
        download_status = str(result.get("download_status") or "not_started")
        if status == "completed" and download_status == "download_failed":
            return self.sync_run(project_id, run_id)
        if status == "submission_unknown" and payload.get("confirm_possible_duplicate") is not True:
            raise VideoWorkflowError(
                "VIDEO_DUPLICATE_CONFIRMATION_REQUIRED",
                "上次提交结果未知，可能已经产生费用；请确认后再重新生成",
                status_code=409,
            )
        if status not in {"failed", "submission_unknown"}:
            if status in {"queued", "submitting", "processing", "completed_pending_download"}:
                message = "视频任务仍在生成中，不能重复生成"
            elif status == "completed":
                message = "视频任务已完成，不能重复生成"
            else:
                message = "当前视频任务状态不允许重试"
            raise VideoWorkflowError("VIDEO_RETRY_NOT_ALLOWED", message, status_code=409)
        self._record_observability_event(
            "video_run_retry_requested",
            project_id=project_id,
            run_id=run_id,
            status=status,
        )
        original_payload = dict(original.get("payload") or {})
        retry_payload = {
            "client_request_id": payload.get("client_request_id"),
            "prompt": original_payload.get("prompt"),
            "reference_asset_ids": original_payload.get("reference_asset_ids", []),
        }
        return self.create_run(
            project_id,
            retry_payload,
            allow_deleted_assets=True,
            retry_of_run_id=run_id,
        )

    def download_path(self, project_id: str, run_id: str) -> Path:
        project = self.store.get_project(project_id)
        task = self.store.task(project_id, run_id)
        rel_path = task.get("download_path") or task.get("result", {}).get("download_path")
        if not rel_path:
            raise KeyError(run_id)
        return Path(project["project_dir"]) / rel_path

    def storage_lifecycle_policy(self) -> dict[str, Any]:
        return {
            "project_reference_quota_bytes": PROJECT_REFERENCE_QUOTA_BYTES,
            "soft_delete_retention_days": SOFT_DELETE_RETENTION_DAYS,
            "failed_run_retention_days": FAILED_RUN_RETENTION_DAYS,
            "temporary_file_retention_hours": TEMPORARY_FILE_RETENTION_HOURS,
            "backup_recommendation": "backup_project_directory_before_physical_purge",
            "soft_delete_behavior": "reference_metadata_retained_after_file_purge",
        }

    def runtime_concurrency_policy(self) -> dict[str, Any]:
        return {
            "lock_scope": "single_api_process",
            "supports_multi_worker": False,
            "deployment_warning": "当前视频工作流内存锁只支持单 API 进程；多 Worker/多容器部署前必须改为数据库租约或外部队列锁。",
        }

    def storage_usage(self, project_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        return self._storage_usage_for_project_dir(project_dir)

    def cleanup_storage(self, project_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        reference_cutoff = datetime.now(timezone.utc) - timedelta(days=SOFT_DELETE_RETENTION_DAYS)
        failed_run_cutoff = datetime.now(timezone.utc) - timedelta(days=FAILED_RUN_RETENTION_DAYS)
        temp_cutoff = datetime.now(timezone.utc) - timedelta(hours=TEMPORARY_FILE_RETENTION_HOURS)
        purged_reference_assets: list[str] = []
        purged_temporary_files: list[str] = []
        expired_failed_runs: list[str] = []
        with self._lock_for_assets(project_id):
            assets = self._all_reference_assets(project_dir)
            changed = False
            for asset in assets:
                if not asset.get("deleted_at") or asset.get("purged_at"):
                    continue
                deleted_at = _parse_iso(asset.get("deleted_at"))
                if deleted_at is None or deleted_at > reference_cutoff:
                    continue
                path = project_dir / str(asset.get("path") or "")
                if path.is_file():
                    path.unlink()
                asset["purged_at"] = now_iso()
                purged_reference_assets.append(str(asset["asset_id"]))
                changed = True
            if changed:
                self._mark_asset_metadata_purged(project_dir, purged_reference_assets)
                assets = self._all_reference_assets(project_dir)
                _write_json_snapshot_best_effort(self._assets_path(project_dir), assets, operation="cleanup_storage")
        references_dir = self._workflow_dir(project_dir) / "references"
        if references_dir.is_dir():
            for temp in references_dir.glob(".*.upload"):
                try:
                    modified_at = datetime.fromtimestamp(temp.stat().st_mtime, tz=timezone.utc)
                except OSError:
                    continue
                if modified_at <= temp_cutoff:
                    temp.unlink(missing_ok=True)
                    purged_temporary_files.append(str(temp.relative_to(project_dir)).replace("\\", "/"))
        with self.store.connect(project_dir) as conn:
            for task in self.store.tasks(project_id):
                if task["task_type"] != "video_workflow_generation" or task["status"] != "failed":
                    continue
                result = dict(task.get("result") or {})
                if result.get("retention_status") == "expired":
                    continue
                updated_at = _parse_iso(task.get("updated_at"))
                if updated_at is None or updated_at > failed_run_cutoff:
                    continue
                expired = {
                    **result,
                    "retention_status": "expired",
                    "expired_at": now_iso(),
                }
                self.store.update_task(conn, task["task_id"], "failed", expired, task.get("error_message"))
                expired_failed_runs.append(task["task_id"])
        return {
            "policy": self.storage_lifecycle_policy(),
            "purged_reference_assets": purged_reference_assets,
            "purged_temporary_files": purged_temporary_files,
            "expired_failed_runs": expired_failed_runs,
            "storage_usage": self.storage_usage(project_id),
        }

    def recover_stale_submissions(self, project_id: str) -> None:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        now = datetime.now(timezone.utc)
        for task in self.store.tasks(project_id):
            if task["task_type"] != "video_workflow_generation" or task["status"] != "submitting":
                continue
            result = dict(task.get("result") or {})
            provider_task_id = result.get("provider_task_id") or task.get("provider_task_id")
            if provider_task_id:
                continue
            lease_expires_at = _parse_iso(result.get("submission_lease_expires_at"))
            if lease_expires_at is not None and lease_expires_at > now:
                continue
            recovered = {
                **result,
                "provider_phase": "submit",
                "download_status": result.get("download_status", "not_started"),
                "error_code": "VIDEO_SUBMIT_UNCERTAIN",
                "retryable": False,
                "submission_recovered_at": now_iso(),
            }
            with self.store.connect(project_dir) as conn:
                self.store.update_task(
                    conn,
                    task["task_id"],
                    "submission_unknown",
                    recovered,
                    "提交超时，无法确认上游是否已创建任务",
                )

    def list_runs(self, project_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        self.recover_stale_submissions(project_id)
        bounded = min(100, max(1, int(limit)))
        runs = [
            self._decorate_run(task)
            for task in self.store.tasks(project_id)
            if task["task_type"] == "video_workflow_generation"
        ]
        return sorted(runs, key=lambda item: item["created_at"], reverse=True)[:bounded]

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
        return self.store.task_by_client_request_id(project_id, "video_workflow_generation", request_id)

    def _active_run(self, project_id: str) -> dict[str, Any] | None:
        for task in self.store.tasks(project_id):
            if task["task_type"] == "video_workflow_generation" and task["status"] in {
                "submitting",
                "queued",
                "processing",
                "completed_pending_download",
            }:
                if task["status"] == "completed_pending_download" and self._expire_pending_url_if_timed_out(
                    project_id,
                    task,
                ):
                    continue
                return task
        return None

    def _expire_pending_url_if_timed_out(self, project_id: str, task: dict[str, Any]) -> bool:
        result = dict(task.get("result") or {})
        if not _is_timed_out(result.get("pending_url_started_at"), PENDING_URL_TIMEOUT_SECONDS):
            return False
        project_dir = Path(self.store.get_project(project_id)["project_dir"])
        expired = {
            **result,
            "download_status": "download_failed",
            "error_code": "VIDEO_URL_TIMEOUT",
            "retryable": True,
        }
        with self.store.connect(project_dir) as conn:
            self.store.update_task(
                conn,
                task["task_id"],
                "failed",
                expired,
                "视频生成已完成，但获取视频文件超时",
            )
        return True

    def _enforce_create_rate_limits(self, project_id: str) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=RUN_CREATE_WINDOW_SECONDS)
        project_count = 0
        global_count = 0
        for project in self.store.list_projects():
            try:
                tasks = self.store.tasks(project["project_id"])
            except KeyError:
                continue
            for task in tasks:
                if task["task_type"] != "video_workflow_generation":
                    continue
                created_at = _parse_iso(task.get("created_at"))
                if created_at is None:
                    continue
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at < cutoff:
                    continue
                global_count += 1
                if task["project_id"] == project_id:
                    project_count += 1
        if project_count >= RUN_CREATE_PROJECT_WINDOW_LIMIT:
            raise VideoWorkflowError(
                "VIDEO_RATE_LIMITED",
                f"当前项目视频生成请求过于频繁，请稍后再试（{RUN_CREATE_WINDOW_SECONDS // 60} 分钟内最多 {RUN_CREATE_PROJECT_WINDOW_LIMIT} 次）",
                status_code=429,
                action="wait_and_retry",
                retryable=True,
            )
        if global_count >= RUN_CREATE_GLOBAL_WINDOW_LIMIT:
            raise VideoWorkflowError(
                "VIDEO_RATE_LIMITED",
                f"视频生成请求过于频繁，请稍后再试（{RUN_CREATE_WINDOW_SECONDS // 60} 分钟内最多 {RUN_CREATE_GLOBAL_WINDOW_LIMIT} 次）",
                status_code=429,
                action="wait_and_retry",
                retryable=True,
            )

    def _return_existing_run_or_conflict(
        self,
        project_id: str,
        request_id: str,
        canonical: dict[str, Any],
    ) -> dict[str, Any] | None:
        existing = self._find_run_by_client_request_id(project_id, request_id)
        if not existing:
            return None
        if existing["payload"] != canonical:
            raise VideoWorkflowError(
                "VIDEO_REQUEST_CONFLICT",
                "相同 client_request_id 已用于不同的视频请求",
                status_code=409,
            )
        return self._decorate_run(existing)

    def _capabilities(self) -> dict[str, Any]:
        data = json.loads(self.capabilities_path.read_text(encoding="utf-8"))
        models = data.get("capabilities", data.get("models", []))
        return {**data, "models": models}

    def _provider_readiness_config(self) -> dict[str, Any]:
        ready = bool(self.provider_readiness.get("ok"))
        blocking = [str(item) for item in self.provider_readiness.get("blocking_issues") or []]
        reason_code = "VIDEO_PROVIDER_READY"
        user_message = "视频生成服务已就绪"
        if "OCTO_API_KEY" in blocking:
            reason_code = "VIDEO_PROVIDER_KEY_MISSING"
            user_message = "服务端尚未配置视频生成密钥"
        elif "VIDEO_PROVIDER_MODE" in blocking:
            reason_code = "VIDEO_PROVIDER_DISABLED"
            user_message = "服务端尚未开启真实视频生成模式"
        elif blocking:
            reason_code = "VIDEO_PROVIDER_NOT_READY"
            user_message = "视频生成服务尚未就绪"
        return {
            "provider_ready": ready,
            "provider_reason_code": reason_code,
            "provider_user_message": user_message,
        }

    def _provider_readiness_from_provider(self) -> dict[str, Any]:
        if self.video_provider is None:
            return {"ok": False, "blocking_issues": ["VIDEO_PROVIDER_MODE"]}
        if not getattr(self.video_provider, "api_key", None):
            return {"ok": False, "blocking_issues": ["OCTO_API_KEY"]}
        return {"ok": True, "blocking_issues": []}

    def _reference_limit(self, model: str) -> int:
        for item in self._capabilities()["models"]:
            if item.get("model") == model:
                return int(item.get("max_reference_images") or 0)
        return 0

    def _workflow_dir(self, project_dir: Path) -> Path:
        return project_dir / "video_workflow"

    def _graph_path(self, project_dir: Path) -> Path:
        return self._workflow_dir(project_dir) / "graph.json"

    def _assets_path(self, project_dir: Path) -> Path:
        return self._workflow_dir(project_dir) / "assets.json"

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

    def _read_graph(self, project_dir: Path) -> dict[str, Any]:
        path = self._graph_path(project_dir)
        if path.is_file():
            return self._normalize_graph(json.loads(path.read_text(encoding="utf-8")))
        return self._normalize_graph(DEFAULT_VIDEO_WORKFLOW_GRAPH)

    def _normalize_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        normalized = {**DEFAULT_VIDEO_WORKFLOW_GRAPH, **(graph or {})}
        normalized["selected_model"] = str(normalized.get("selected_model") or "omni_flash-10s")
        normalized["mode"] = str(normalized.get("mode") or "text")
        normalized["duration_sec"] = int(normalized.get("duration_sec") or 10)
        normalized["size"] = str(normalized.get("size") or "1280x720")
        normalized["nodes"] = list(normalized.get("nodes") or DEFAULT_VIDEO_WORKFLOW_GRAPH["nodes"])
        normalized["edges"] = list(normalized.get("edges") or DEFAULT_VIDEO_WORKFLOW_GRAPH["edges"])
        return normalized

    def _all_reference_assets(self, project_dir: Path) -> list[dict[str, Any]]:
        rows = self._read_reference_assets_from_db(project_dir)
        if rows:
            return rows
        if self._legacy_manifest_migration_completed(project_dir):
            return []
        legacy_assets = self._read_legacy_manifest_assets(project_dir)
        if legacy_assets:
            project_id = self._project_id_from_dir(project_dir)
            self._upsert_asset_metadata(project_dir, project_id, legacy_assets, source="legacy_manifest")
            self._mark_legacy_manifest_migration_completed(project_dir)
            return self._read_reference_assets_from_db(project_dir)
        self._mark_legacy_manifest_migration_completed(project_dir)
        return []

    def _legacy_manifest_migration_completed(self, project_dir: Path) -> bool:
        with self.store.connect(project_dir) as conn:
            self._ensure_video_workflow_meta_table(conn)
            row = conn.execute(
                "SELECT value FROM video_workflow_meta WHERE key = ?",
                ("assets_manifest_migrated",),
            ).fetchone()
        return row is not None and str(row["value"]) == "true"

    def _mark_legacy_manifest_migration_completed(self, project_dir: Path) -> None:
        with self.store.connect(project_dir) as conn:
            self._ensure_video_workflow_meta_table(conn)
            conn.execute(
                """
                INSERT INTO video_workflow_meta (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                ("assets_manifest_migrated", "true", now_iso()),
            )

    @staticmethod
    def _ensure_video_workflow_meta_table(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS video_workflow_meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )

    def _read_legacy_manifest_assets(self, project_dir: Path) -> list[dict[str, Any]]:
        path = self._assets_path(project_dir)
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [self._normalize_asset_record(item) for item in data if isinstance(item, dict)]

    def _read_reference_assets_from_db(self, project_dir: Path) -> list[dict[str, Any]]:
        with self.store.connect(project_dir) as conn:
            rows = conn.execute(
                """
                SELECT asset_id, filename, path, mime_type, byte_size, width, height,
                       source, created_at, updated_at, deleted_at, purged_at
                FROM video_workflow_assets
                ORDER BY created_at, asset_id
                """
            ).fetchall()
        return [self._normalize_asset_record(dict(row)) for row in rows]

    def _project_id_from_dir(self, project_dir: Path) -> str:
        with self.store.connect(project_dir) as conn:
            row = conn.execute("SELECT project_id FROM project_meta LIMIT 1").fetchone()
        if row is None:
            raise KeyError("PROJECT_NOT_FOUND")
        return str(row["project_id"])

    def _normalize_asset_record(self, asset: dict[str, Any]) -> dict[str, Any]:
        return {
            "asset_id": str(asset["asset_id"]),
            "filename": str(asset.get("filename") or Path(str(asset.get("path") or "")).name),
            "path": str(asset.get("path") or ""),
            "mime_type": str(asset.get("mime_type") or "application/octet-stream"),
            "byte_size": int(asset.get("byte_size") or 0),
            "width": int(asset.get("width") or 0),
            "height": int(asset.get("height") or 0),
            "created_at": str(asset.get("created_at") or now_iso()),
            "deleted_at": asset.get("deleted_at"),
            "purged_at": asset.get("purged_at"),
            "source": str(asset.get("source") or "upload"),
        }

    def _upsert_asset_metadata(
        self,
        project_dir: Path,
        project_id: str,
        assets: list[dict[str, Any]],
        *,
        source: str = "upload",
    ) -> None:
        if not assets:
            return
        with self.store.connect(project_dir) as conn:
            for asset in assets:
                normalized = self._normalize_asset_record(asset)
                timestamp = now_iso()
                conn.execute(
                    """
                    INSERT INTO video_workflow_assets
                    (
                      asset_id, project_id, filename, path, mime_type, byte_size,
                      width, height, source, created_at, updated_at, deleted_at, purged_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(asset_id) DO UPDATE SET
                      filename = excluded.filename,
                      path = excluded.path,
                      mime_type = excluded.mime_type,
                      byte_size = excluded.byte_size,
                      width = excluded.width,
                      height = excluded.height,
                      updated_at = excluded.updated_at,
                      deleted_at = excluded.deleted_at,
                      purged_at = excluded.purged_at
                    """,
                    (
                        normalized["asset_id"],
                        project_id,
                        normalized["filename"],
                        normalized["path"],
                        normalized["mime_type"],
                        int(normalized.get("byte_size") or 0),
                        int(normalized.get("width") or 0),
                        int(normalized.get("height") or 0),
                        source,
                        normalized.get("created_at") or timestamp,
                        timestamp,
                        normalized.get("deleted_at"),
                        normalized.get("purged_at"),
                    ),
                )
        self._mark_legacy_manifest_migration_completed(project_dir)

    def _mark_asset_metadata_deleted(self, project_dir: Path, asset_id: str) -> None:
        with self.store.connect(project_dir) as conn:
            timestamp = now_iso()
            conn.execute(
                """
                UPDATE video_workflow_assets
                SET deleted_at = COALESCE(deleted_at, ?), updated_at = ?
                WHERE asset_id = ?
                """,
                (timestamp, timestamp, asset_id),
            )

    def _mark_asset_metadata_purged(self, project_dir: Path, asset_ids: list[str]) -> None:
        if not asset_ids:
            return
        with self.store.connect(project_dir) as conn:
            timestamp = now_iso()
            for asset_id in asset_ids:
                conn.execute(
                    """
                    UPDATE video_workflow_assets
                    SET purged_at = COALESCE(purged_at, ?), updated_at = ?
                    WHERE asset_id = ?
                    """,
                    (timestamp, timestamp, asset_id),
                )

    def _reference_assets(self, project_dir: Path) -> list[dict[str, Any]]:
        return [item for item in self._all_reference_assets(project_dir) if not item.get("deleted_at")]

    def _storage_usage_for_project_dir(self, project_dir: Path) -> dict[str, Any]:
        return self._storage_usage_for_assets(project_dir, self._all_reference_assets(project_dir))

    def _storage_usage_for_assets(self, project_dir: Path, assets: list[dict[str, Any]]) -> dict[str, Any]:
        active = [item for item in assets if not item.get("deleted_at")]
        deleted = [item for item in assets if item.get("deleted_at") and not item.get("purged_at")]
        active_bytes = self._reference_bytes(project_dir, active)
        deleted_bytes = self._reference_bytes(project_dir, deleted)
        return {
            "reference_asset_bytes": active_bytes,
            "deleted_reference_asset_bytes": deleted_bytes,
            "total_reference_asset_bytes": active_bytes + deleted_bytes,
            "active_reference_asset_count": len(active),
            "deleted_reference_asset_count": len(deleted),
            "reference_quota_bytes": PROJECT_REFERENCE_QUOTA_BYTES,
            "reference_quota_used_percent": round((active_bytes / PROJECT_REFERENCE_QUOTA_BYTES) * 100, 2)
            if PROJECT_REFERENCE_QUOTA_BYTES > 0
            else 0,
        }

    def _active_reference_bytes(self, project_dir: Path, assets: list[dict[str, Any]]) -> int:
        return self._reference_bytes(project_dir, [item for item in assets if not item.get("deleted_at")])

    def _reference_bytes(self, project_dir: Path, assets: list[dict[str, Any]]) -> int:
        total = 0
        for asset in assets:
            path = project_dir / str(asset.get("path") or "")
            if path.is_file():
                total += path.stat().st_size
            else:
                total += int(asset.get("byte_size") or 0)
        return total

    def _discard_asset_file(self, project_dir: Path, asset: dict[str, Any]) -> None:
        path = project_dir / str(asset.get("path") or "")
        if path.is_file():
            path.unlink(missing_ok=True)

    def _ensure_reference_files_available(self, project_dir: Path, assets: list[dict[str, Any]]) -> None:
        for asset in assets:
            path = project_dir / str(asset.get("path") or "")
            if not path.is_file() or path.stat().st_size <= 0:
                raise VideoWorkflowError(
                    "VIDEO_REFERENCE_EXPIRED",
                    "参考素材已过期，请重新上传后再生成视频",
                    status_code=410,
                    action="upload_reference_again",
                    retryable=False,
                    details={"asset_id": asset.get("asset_id")},
                )

    def _resolve_reference_paths(self, project_dir: Path, reference_asset_ids: list[str]) -> list[str]:
        assets = {asset["asset_id"]: asset for asset in self._reference_assets(project_dir)}
        paths = []
        for asset_id in reference_asset_ids:
            asset = assets.get(asset_id)
            if not asset:
                raise VideoWorkflowError("VIDEO_REFERENCE_NOT_FOUND", "参考图不存在")
            paths.append(str(asset["path"]))
        return paths

    def _latest_run(self, project_id: str) -> dict[str, Any] | None:
        runs = self.list_runs(project_id, limit=1)
        return runs[0] if runs else None

    def _decorate_run(self, task: dict[str, Any]) -> dict[str, Any]:
        result = dict(task.get("result") or {})
        payload = dict(task.get("payload") or {})
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
            "mode": "reference" if payload.get("reference_asset_ids") else "text",
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
            "download_path": result.get("download_path") or task.get("download_path"),
            "download_bytes": result.get("download_bytes"),
            "download_sha256": result.get("download_sha256"),
            "video_url_present": bool(result.get("video_url")),
        }
