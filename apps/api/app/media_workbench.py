from __future__ import annotations

import json
import base64
import urllib.request
import urllib.error
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from .providers import ProviderError
from .store import ProjectStore, now_iso


ADMIN_MEDIA_PROJECT_ID = "admin_media_workbench"
ADMIN_MEDIA_PROJECT_DIR = "admin_media_workbench_admin_media_workbench"
DEFAULT_IMAGE_MODEL = "gpt-image-2"
DEFAULT_IMAGE_SIZE = "1920x1080"
DEFAULT_IMAGE_QUALITY = "high"
DEFAULT_VIDEO_MODEL = "omni_flash-10s"
DEFAULT_VIDEO_SIZE = "1280x720"
DEFAULT_VIDEO_DURATION_SEC = 10
ALLOWED_REFERENCE_IMAGE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


class MediaWorkbenchError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class MediaWorkbenchService:
    def __init__(
        self,
        *,
        store: ProjectStore,
        capabilities_path: Path,
        image_provider: Any | None,
        video_provider: Any | None,
        image_model: str = DEFAULT_IMAGE_MODEL,
    ):
        self.store = store
        self.capabilities_path = capabilities_path
        self.image_provider = image_provider
        self.video_provider = video_provider
        self.image_model = image_model or DEFAULT_IMAGE_MODEL
        self._ensure_workspace()

    def summary(self) -> dict[str, Any]:
        return {
            "capabilities": self.capabilities(),
            "assets": self.assets(),
            "reference_basket": self.reference_basket(),
            "image_runs": [self._decorate_image_run(task) for task in self._tasks("admin_image_generation")][-20:],
            "video_runs": [self._decorate_video_run(task) for task in self._tasks("admin_video_generation")][-20:],
        }

    def capabilities(self) -> dict[str, Any]:
        data = json.loads(self.capabilities_path.read_text(encoding="utf-8"))
        models = data.get("capabilities", data.get("models", []))
        return {
            "image": {
                "provider": "newapi-image",
                "provider_ready": self.image_provider is not None,
                "default_model": self.image_model,
                "default_size": DEFAULT_IMAGE_SIZE,
                "default_quality": DEFAULT_IMAGE_QUALITY,
                "models": [
                    {
                        "model": self.image_model,
                        "sizes": ["1920x1080", "1024x1024", "1080x1920"],
                        "qualities": ["high", "low"],
                        "max_count": 4,
                    }
                ],
            },
            "video": {
                "provider": "octo",
                "provider_ready": self.video_provider is not None,
                "default_model": DEFAULT_VIDEO_MODEL,
                "default_size": DEFAULT_VIDEO_SIZE,
                "default_duration_sec": DEFAULT_VIDEO_DURATION_SEC,
                "models": models,
            },
        }

    def assets(self, asset_type: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
        assets = self._read_assets()
        if asset_type:
            assets = [item for item in assets if item.get("asset_type") == asset_type]
        if source:
            assets = [item for item in assets if item.get("source") == source]
        return assets

    def create_image_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.image_provider is None:
            raise MediaWorkbenchError("IMAGE_PROVIDER_NOT_CONFIGURED", "图片生成服务未配置")
        prompt = str(payload.get("prompt") or "").strip()
        if not prompt:
            raise MediaWorkbenchError("IMAGE_PROMPT_REQUIRED", "请先填写图片提示词")
        count = int(payload.get("count") or 1)
        if count < 1 or count > 4:
            raise MediaWorkbenchError("IMAGE_COUNT_INVALID", "图片数量必须在 1 到 4 张之间")
        model = str(payload.get("model") or self.image_model)
        size = str(payload.get("size") or DEFAULT_IMAGE_SIZE)
        quality = str(payload.get("quality") or DEFAULT_IMAGE_QUALITY)
        run_payload = {"prompt": prompt, "model": model, "size": size, "quality": quality, "count": count}
        with self.store.connect(self._workspace_dir()) as conn:
            task = self.store.create_task(
                conn,
                ADMIN_MEDIA_PROJECT_ID,
                "admin_media_workbench",
                "admin_image_generation",
                run_payload,
                status="processing",
                result={"provider_phase": "submit"},
            )
            assets = []
            try:
                submissions: dict[int, dict[str, Any]] = {}
                request_payload = {
                    "prompt": prompt,
                    "model": model,
                    "size": size,
                    "quality": quality,
                    "response_format": "b64_json",
                }
                with ThreadPoolExecutor(max_workers=min(count, 4)) as executor:
                    futures = {
                        executor.submit(self.image_provider.generate_image, dict(request_payload)): index
                        for index in range(count)
                    }
                    for future in as_completed(futures):
                        submissions[futures[future]] = future.result()
                for index in range(count):
                    assets.append(self._save_image_result(task["task_id"], index, prompt, submissions[index]))
            except ProviderError as exc:
                self.store.update_task(
                    conn,
                    task["task_id"],
                    "failed",
                    {"provider_phase": "submit", "error_code": exc.code, "retryable": exc.retryable},
                    str(exc),
                )
                raise
            updated = self.store.update_task(
                conn,
                task["task_id"],
                "completed",
                {"provider_phase": "completed", "assets": assets, "model": model, "size": size, "quality": quality},
            )
        return self._decorate_image_run(updated)

    def get_image_run(self, run_id: str) -> dict[str, Any]:
        return self._decorate_image_run(self._task(run_id))

    def upload_video_references(self, files: list[UploadFile]) -> dict[str, Any]:
        limit = self._reference_limit(DEFAULT_VIDEO_MODEL)
        basket = self.reference_basket()["assets"]
        if len(basket) + len(files) > limit:
            raise MediaWorkbenchError("VIDEO_REFERENCE_LIMIT_EXCEEDED", f"当前模型参考图最多 {limit} 张")
        if not files:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "请上传至少 1 张参考图")
        assets = self._read_assets()
        created = []
        for file in files:
            content_type = str(file.content_type or "")
            suffix = Path(file.filename or "reference.png").suffix.lower()
            if not content_type.startswith("image/") and suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "只能上传图片作为视频参考图")
            content = file.file.read()
            if not content:
                raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "参考图文件为空")
            mime_type = self._validate_reference_image(content)
            asset_id = f"mref_{uuid.uuid4().hex[:12]}"
            safe_name = self._safe_filename(file.filename or "reference.png")
            rel_path = f"media_workbench/assets/references/{asset_id}_{safe_name}"
            target = self._storage_root() / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            item = {
                "asset_id": asset_id,
                "asset_type": "image",
                "source": "upload",
                "filename": file.filename or safe_name,
                "path": rel_path.replace("\\", "/"),
                "mime_type": mime_type,
                "created_at": now_iso(),
            }
            assets.append(item)
            created.append(item)
        self._write_assets(assets)
        self._set_reference_basket([*basket, *created])
        return self.reference_basket()

    def import_video_references(self, asset_ids: list[str]) -> dict[str, Any]:
        limit = self._reference_limit(DEFAULT_VIDEO_MODEL)
        known = {item["asset_id"]: item for item in self._read_assets()}
        basket = self.reference_basket()["assets"]
        next_assets = list(basket)
        existing_ids = {item["asset_id"] for item in next_assets}
        for asset_id in [str(item) for item in asset_ids]:
            asset = known.get(asset_id)
            if not asset or asset.get("asset_type") != "image":
                raise MediaWorkbenchError("MEDIA_ASSET_NOT_FOUND", "素材不存在")
            if asset_id not in existing_ids:
                next_assets.append(asset)
                existing_ids.add(asset_id)
        if len(next_assets) > limit:
            raise MediaWorkbenchError("VIDEO_REFERENCE_LIMIT_EXCEEDED", f"当前模型参考图最多 {limit} 张")
        self._set_reference_basket(next_assets)
        return self.reference_basket()

    def reference_basket(self) -> dict[str, Any]:
        path = self._basket_path()
        if path.is_file():
            basket_ids = json.loads(path.read_text(encoding="utf-8")).get("asset_ids", [])
        else:
            basket_ids = []
        assets = {item["asset_id"]: item for item in self._read_assets()}
        selected = [assets[item] for item in basket_ids if item in assets]
        return {"assets": selected, "max_reference_images": self._reference_limit(DEFAULT_VIDEO_MODEL)}

    def create_video_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.video_provider is None:
            raise MediaWorkbenchError("VIDEO_PROVIDER_NOT_CONFIGURED", "视频生成服务未配置")
        prompt = str(payload.get("prompt") or "").strip()
        if not prompt:
            raise MediaWorkbenchError("VIDEO_PROMPT_REQUIRED", "请先填写视频提示词")
        model = str(payload.get("model") or DEFAULT_VIDEO_MODEL)
        mode = str(payload.get("mode") or "text")
        size = str(payload.get("size") or DEFAULT_VIDEO_SIZE)
        duration_sec = int(payload.get("duration_sec") or DEFAULT_VIDEO_DURATION_SEC)
        reference_asset_ids = [str(item) for item in payload.get("reference_asset_ids") or []]
        limit = self._reference_limit(model)
        if len(reference_asset_ids) > limit:
            raise MediaWorkbenchError("VIDEO_REFERENCE_LIMIT_EXCEEDED", f"当前模型参考图最多 {limit} 张")
        if mode == "reference" and not reference_asset_ids:
            raise MediaWorkbenchError("VIDEO_REFERENCE_REQUIRED", "图生视频需要至少 1 张参考图")
        reference_paths = self._resolve_asset_paths(reference_asset_ids)
        submit_payload: dict[str, Any] = {"model": model, "prompt": prompt, "size": size}
        if mode != "text" and reference_paths:
            submit_payload["reference_image_paths"] = [str(path) for path in reference_paths]
        task_payload = {
            "prompt": prompt,
            "model": model,
            "mode": mode,
            "size": size,
            "duration_sec": duration_sec,
            "reference_asset_ids": reference_asset_ids,
        }
        with self.store.connect(self._workspace_dir()) as conn:
            task = self.store.create_task(
                conn,
                ADMIN_MEDIA_PROJECT_ID,
                "admin_media_workbench",
                "admin_video_generation",
                task_payload,
                status="submitting",
                result={"provider_phase": "submit", "download_status": "not_started"},
            )
            try:
                submitted = self.video_provider.submit_video(submit_payload)
            except ProviderError as exc:
                self.store.update_task(
                    conn,
                    task["task_id"],
                    "failed",
                    {"provider_phase": "submit", "error_code": exc.code, "retryable": exc.retryable},
                    str(exc),
                )
                raise
            updated = self.store.update_task(
                conn,
                task["task_id"],
                submitted.get("status") or "queued",
                {
                    **submitted,
                    "provider_phase": "submit",
                    "download_status": "not_started",
                    "duration_sec": duration_sec,
                    "model": model,
                },
            )
        return self._decorate_video_run(updated)

    def get_video_run(self, run_id: str) -> dict[str, Any]:
        return self._decorate_video_run(self._task(run_id))

    def sync_video_run(self, run_id: str) -> dict[str, Any]:
        task = self._task(run_id)
        if self.video_provider is None:
            return self._decorate_video_run(task)
        provider_task_id = task.get("provider_task_id") or task.get("result", {}).get("provider_task_id")
        if not provider_task_id:
            return self._decorate_video_run(task)
        remote = self.video_provider.query_task(provider_task_id)
        result = {**task.get("result", {}), **remote, "provider_phase": "query"}
        download_path = task.get("download_path") or f"media_workbench/assets/videos/{run_id}.mp4"
        if remote.get("status") == "completed" and remote.get("video_url"):
            target = self._storage_root() / download_path
            self.video_provider.download_video(remote["video_url"], target)
            asset = self._upsert_video_asset(run_id, download_path, task)
            result = {**result, "download_path": download_path, "download_status": "downloaded", "asset": asset}
        with self.store.connect(self._workspace_dir()) as conn:
            updated = self._update_task_with_retry(conn, run_id, remote.get("status") or task["status"], result, remote.get("error_message"))
        return self._decorate_video_run(updated)

    def asset_path(self, asset_id: str) -> Path:
        for asset in self._read_assets():
            if asset.get("asset_id") == asset_id:
                return self._storage_root() / str(asset["path"])
        raise KeyError(asset_id)

    def video_download_path(self, run_id: str) -> Path:
        task = self._task(run_id)
        rel_path = task.get("download_path") or task.get("result", {}).get("download_path")
        if not rel_path:
            raise KeyError(run_id)
        return self._storage_root() / rel_path

    def _ensure_workspace(self) -> None:
        project_dir = self._workspace_dir()
        project_dir.mkdir(parents=True, exist_ok=True)
        with self.store.connect(project_dir) as conn:
            row = conn.execute("SELECT project_id FROM project_meta WHERE project_id = ?", (ADMIN_MEDIA_PROJECT_ID,)).fetchone()
            if row is None:
                created_at = now_iso()
                conn.execute(
                    """
                    INSERT INTO project_meta
                    (
                      project_id, name, subject, grade, textbook_version, volume, lesson_type,
                      created_at, status, project_dir
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ADMIN_MEDIA_PROJECT_ID,
                        "管理员媒体生成工作台",
                        "media",
                        "admin",
                        "internal",
                        "all",
                        "admin",
                        created_at,
                        "internal",
                        str(project_dir),
                    ),
                )

    def _storage_root(self) -> Path:
        return self.store.storage_root

    def _workspace_dir(self) -> Path:
        return self.store.projects_root / ADMIN_MEDIA_PROJECT_DIR

    def _meta_dir(self) -> Path:
        path = self._storage_root() / "media_workbench"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _assets_path(self) -> Path:
        return self._meta_dir() / "assets.json"

    def _basket_path(self) -> Path:
        return self._meta_dir() / "reference_basket.json"

    def _read_assets(self) -> list[dict[str, Any]]:
        path = self._assets_path()
        if not path.is_file():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_assets(self, assets: list[dict[str, Any]]) -> None:
        self._assets_path().write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")

    def _set_reference_basket(self, assets: list[dict[str, Any]]) -> None:
        self._basket_path().write_text(
            json.dumps({"asset_ids": [item["asset_id"] for item in assets]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save_image_result(self, run_id: str, index: int, prompt: str, submitted: dict[str, Any]) -> dict[str, Any]:
        asset_id = f"mimg_{uuid.uuid4().hex[:12]}"
        rel_path = f"media_workbench/assets/images/{asset_id}.png"
        target = self._storage_root() / rel_path
        if submitted.get("b64_json"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(str(submitted["b64_json"])))
        elif submitted.get("image_url"):
            if hasattr(self.image_provider, "download_image"):
                self.image_provider.download_image(str(submitted["image_url"]), target)
            else:
                self._download_image_url(str(submitted["image_url"]), target)
        else:
            raise ProviderError("IMAGE_RESPONSE_INVALID", "图片生成未返回 url 或 b64_json", retryable=True)
        asset = {
            "asset_id": asset_id,
            "asset_type": "image",
            "source": "image_run",
            "filename": f"{asset_id}.png",
            "path": rel_path,
            "mime_type": "image/png",
            "prompt": prompt,
            "run_id": run_id,
            "provider_task_id": submitted.get("provider_task_id"),
            "created_at": now_iso(),
            "index": index,
        }
        assets = self._read_assets()
        assets.append(asset)
        self._write_assets(assets)
        return asset

    def _upsert_video_asset(self, run_id: str, rel_path: str, task: dict[str, Any]) -> dict[str, Any]:
        asset_id = f"mvid_{run_id}"
        payload = task.get("payload") or {}
        asset = {
            "asset_id": asset_id,
            "asset_type": "video",
            "source": "video_run",
            "filename": Path(rel_path).name,
            "path": rel_path,
            "mime_type": "video/mp4",
            "prompt": payload.get("prompt"),
            "run_id": run_id,
            "created_at": now_iso(),
        }
        assets = [item for item in self._read_assets() if item.get("asset_id") != asset_id]
        assets.append(asset)
        self._write_assets(assets)
        return asset

    def _reference_limit(self, model: str) -> int:
        for item in self.capabilities()["video"]["models"]:
            if item.get("model") == model:
                return int(item.get("max_reference_images") or 0)
        return 0

    def _resolve_asset_paths(self, asset_ids: list[str]) -> list[Path]:
        assets = {item["asset_id"]: item for item in self._read_assets()}
        paths = []
        for asset_id in asset_ids:
            asset = assets.get(asset_id)
            if not asset:
                raise MediaWorkbenchError("MEDIA_ASSET_NOT_FOUND", "素材不存在")
            paths.append(self._storage_root() / str(asset["path"]))
        return paths

    def _validate_reference_image(self, content: bytes) -> str:
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image_format = str(image.format or "").upper()
                width, height = image.size
        except Image.DecompressionBombError as exc:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "参考图像素过大，请压缩后重新上传") from exc
        except Image.DecompressionBombWarning as exc:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "参考图像素过大，请压缩后重新上传") from exc
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "文件不是有效图片，请上传 PNG、JPG 或 WebP 图片") from exc
        if image_format not in ALLOWED_REFERENCE_IMAGE_FORMATS:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "仅支持 PNG、JPG、WebP 图片")
        if width <= 0 or height <= 0:
            raise MediaWorkbenchError("VIDEO_REFERENCE_INVALID", "参考图宽高无效")
        return ALLOWED_REFERENCE_IMAGE_FORMATS[image_format]

    def _tasks(self, task_type: str) -> list[dict[str, Any]]:
        return [task for task in self.store.tasks(ADMIN_MEDIA_PROJECT_ID) if task["task_type"] == task_type]

    def _task(self, run_id: str) -> dict[str, Any]:
        return self.store.task(ADMIN_MEDIA_PROJECT_ID, run_id)

    def _update_task_with_retry(
        self,
        conn,
        task_id: str,
        status: str,
        result: dict[str, Any],
        error_message: str | None,
    ) -> dict[str, Any]:
        try:
            return self.store.update_task(conn, task_id, status, result, error_message)
        except sqlite3.OperationalError as exc:
            if "readonly database" not in str(exc).lower():
                raise
            with self.store.connect(self._workspace_dir()) as retry_conn:
                return self.store.update_task(retry_conn, task_id, status, result, error_message)

    def _decorate_image_run(self, task: dict[str, Any]) -> dict[str, Any]:
        result = task.get("result") or {}
        payload = task.get("payload") or {}
        return {
            **task,
            "run_id": task["task_id"],
            "prompt": payload.get("prompt"),
            "model": payload.get("model"),
            "size": payload.get("size"),
            "quality": payload.get("quality"),
            "count": payload.get("count"),
            "assets": result.get("assets", []),
        }

    def _decorate_video_run(self, task: dict[str, Any]) -> dict[str, Any]:
        result = task.get("result") or {}
        payload = task.get("payload") or {}
        return {
            **task,
            "run_id": task["task_id"],
            "prompt": payload.get("prompt"),
            "model": payload.get("model"),
            "mode": payload.get("mode"),
            "size": payload.get("size"),
            "duration_sec": payload.get("duration_sec"),
            "reference_asset_ids": payload.get("reference_asset_ids", []),
            "progress": result.get("progress", 0),
            "download_path": result.get("download_path") or task.get("download_path"),
            "video_url_present": bool(result.get("video_url")),
            "asset": result.get("asset"),
        }

    def _safe_filename(self, value: str) -> str:
        name = Path(value).name or "asset.png"
        return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in name)

    def _download_image_url(self, image_url: str, target: Path) -> None:
        request = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                ),
                "Accept": "image/png,image/*;q=0.9,application/octet-stream,*/*;q=0.5",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            raise ProviderError("IMAGE_DOWNLOAD_FAILED", f"图片下载失败：HTTP {exc.code}", retryable=True) from exc
        except urllib.error.URLError as exc:
            raise ProviderError("IMAGE_DOWNLOAD_FAILED", f"图片下载失败：{exc.reason}", retryable=True) from exc
