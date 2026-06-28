from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .providers import ProviderError
from .store import ProjectStore, now_iso


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


class VideoWorkflowError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class VideoWorkflowService:
    def __init__(self, *, store: ProjectStore, capabilities_path: Path, video_provider: Any | None):
        self.store = store
        self.capabilities_path = capabilities_path
        self.video_provider = video_provider

    def get_workflow(self, project_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        return {
            "project_id": project_id,
            "graph": self._read_graph(project_dir),
            "assets": self._reference_assets(project_dir),
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
        graph = self._read_graph(project_dir)
        limit = self._reference_limit(str(graph.get("selected_model") or "omni_flash-10s"))
        existing = self._reference_assets(project_dir)
        if len(existing) + len(files) > limit:
            raise VideoWorkflowError("VIDEO_REFERENCE_LIMIT_EXCEEDED", f"当前模型参考图最多 {limit} 张")
        if not files:
            raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "请上传至少 1 张参考图")

        upload_dir = self._workflow_dir(project_dir) / "references"
        upload_dir.mkdir(parents=True, exist_ok=True)
        assets = []
        for file in files:
            content_type = str(file.content_type or "")
            suffix = Path(file.filename or "reference.png").suffix.lower()
            if not content_type.startswith("image/") and suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "只能上传图片作为视频参考图")
            asset_id = f"vref_{uuid.uuid4().hex[:12]}"
            original_name = Path(file.filename or "reference.png").name
            safe_original = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in original_name)
            filename = f"{asset_id}_{safe_original}"
            rel_path = f"video_workflow/references/{filename}"
            target = project_dir / rel_path
            target.write_bytes(file.file.read())
            if target.stat().st_size == 0:
                raise VideoWorkflowError("VIDEO_REFERENCE_INVALID", "参考图文件为空")
            assets.append(
                {
                    "asset_id": asset_id,
                    "filename": file.filename or filename,
                    "path": rel_path.replace("\\", "/"),
                    "mime_type": content_type or "image/png",
                    "created_at": now_iso(),
                }
            )
        all_assets = existing + assets
        self._assets_path(project_dir).write_text(json.dumps(all_assets, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"assets": all_assets, "max_reference_images": limit}

    def create_run(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        graph = self._read_graph(project_dir)
        model = str(payload.get("model") or graph.get("selected_model") or "omni_flash-10s")
        mode = str(payload.get("mode") or graph.get("mode") or "text")
        prompt = str(payload.get("prompt") or "").strip()
        size = str(payload.get("size") or graph.get("size") or "1280x720")
        duration_sec = int(payload.get("duration_sec") or graph.get("duration_sec") or 10)
        reference_asset_ids = [str(item) for item in payload.get("reference_asset_ids") or []]

        if not prompt:
            raise VideoWorkflowError("VIDEO_PROMPT_REQUIRED", "请先填写视频提示词")
        limit = self._reference_limit(model)
        if len(reference_asset_ids) > limit:
            raise VideoWorkflowError("VIDEO_REFERENCE_LIMIT_EXCEEDED", f"当前模型参考图最多 {limit} 张")
        if mode == "reference" and not reference_asset_ids:
            raise VideoWorkflowError("VIDEO_REFERENCE_REQUIRED", "图生视频需要至少 1 张参考图")

        reference_paths = self._resolve_reference_paths(project_dir, reference_asset_ids)
        submit_payload: dict[str, Any] = {"model": model, "prompt": prompt, "size": size}
        if mode != "text" and reference_paths:
            submit_payload["reference_image_paths"] = [str(project_dir / item) for item in reference_paths]

        task_payload = {
            "prompt": prompt,
            "model": model,
            "mode": mode,
            "size": size,
            "duration_sec": duration_sec,
            "reference_asset_ids": reference_asset_ids,
        }
        with self.store.connect(project_dir) as conn:
            task = self.store.create_task(
                conn,
                project_id,
                "video_workflow",
                "video_workflow_generation",
                task_payload,
                status="submitting" if self.video_provider is not None else "generated",
                result={"provider_phase": "submit", "download_status": "not_started"},
            )
            if self.video_provider is None:
                updated = self.store.update_task(
                    conn,
                    task["task_id"],
                    "generated",
                    {"download_status": "placeholder", "duration_sec": duration_sec, "model": model},
                )
                return self._decorate_run(updated)
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
        return self._decorate_run(updated)

    def get_run(self, project_id: str, run_id: str) -> dict[str, Any]:
        return self._decorate_run(self.store.task(project_id, run_id))

    def sync_run(self, project_id: str, run_id: str) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        task = self.store.task(project_id, run_id)
        if self.video_provider is None:
            return self._decorate_run(task)
        provider_task_id = task.get("provider_task_id") or task.get("result", {}).get("provider_task_id")
        if not provider_task_id:
            return self._decorate_run(task)
        remote = self.video_provider.query_task(provider_task_id)
        result = {**task["result"], **remote, "provider_phase": "query"}
        download_path = task.get("download_path") or f"video_workflow/runs/{run_id}.mp4"
        if remote.get("status") == "completed" and remote.get("video_url"):
            target = project_dir / download_path
            self.video_provider.download_video(remote["video_url"], target)
            result = {**result, "download_path": download_path, "download_status": "downloaded"}
        with self.store.connect(project_dir) as conn:
            updated = self.store.update_task(conn, run_id, remote.get("status") or task["status"], result, remote.get("error_message"))
        return self._decorate_run(updated)

    def download_path(self, project_id: str, run_id: str) -> Path:
        project = self.store.get_project(project_id)
        task = self.store.task(project_id, run_id)
        rel_path = task.get("download_path") or task.get("result", {}).get("download_path")
        if not rel_path:
            raise KeyError(run_id)
        return Path(project["project_dir"]) / rel_path

    def _capabilities(self) -> dict[str, Any]:
        data = json.loads(self.capabilities_path.read_text(encoding="utf-8"))
        models = data.get("capabilities", data.get("models", []))
        return {**data, "models": models}

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

    def _reference_assets(self, project_dir: Path) -> list[dict[str, Any]]:
        path = self._assets_path(project_dir)
        if not path.is_file():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

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
        runs = [task for task in self.store.tasks(project_id) if task["task_type"] == "video_workflow_generation"]
        if not runs:
            return None
        return self._decorate_run(runs[-1])

    def _decorate_run(self, task: dict[str, Any]) -> dict[str, Any]:
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
        }
