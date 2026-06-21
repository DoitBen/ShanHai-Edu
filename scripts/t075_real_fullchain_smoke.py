from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.video_provider_readiness import build_video_provider_readiness_report


NODE_CHAIN = [
    "textbook_parse",
    "lesson_plan",
    "intro_selection",
    "intro_video_script",
    "intro_video_screenplay",
    "intro_video_asset",
    "storyboard",
]

FINAL_VIDEO_REL_PATH = "outputs/final_video.mp4"
DEFAULT_VIDEO_MODEL = "omni_flash-10s"


class SmokeStepError(RuntimeError):
    def __init__(self, step: str, message: str):
        super().__init__(message)
        self.step = step


def mask_text(value: str) -> str:
    if not value:
        return ""
    patterns = [
        (r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"',}]+", r"\1<redacted>"),
        (r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]{8,}", r"\1<redacted>"),
        (r"(?i)((?:api[_-]?key|token|secret|key|authorization)\s*[\"']?\s*[:=]\s*[\"']?)[^\"',}\s]+", r"\1<redacted>"),
        (r"\b(?:sk|octo|deepseek|mmx|newapi|pplx|pk)-[A-Za-z0-9._-]{6,}\b", "<redacted>"),
    ]
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_for_evidence(value), ensure_ascii=False, indent=2), encoding="utf-8")


def sanitize_for_evidence(value: Any) -> Any:
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, list):
        return [sanitize_for_evidence(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize_for_evidence(item) for key, item in value.items()}
    return value


def _non_empty_artifact(value: Any) -> bool:
    return isinstance(value, dict) and int(value.get("bytes") or 0) > 0


def _final_video_content(evidence: dict[str, Any]) -> dict[str, Any]:
    content = evidence.get("final_video_node_content")
    return content if isinstance(content, dict) else {}


def _ffprobe_result(evidence: dict[str, Any]) -> dict[str, Any]:
    result = evidence.get("ffprobe")
    return result if isinstance(result, dict) else {}


def _ppt_media_entries(evidence: dict[str, Any]) -> list[Any]:
    ppt = evidence.get("ppt_path")
    if not isinstance(ppt, dict):
        return []
    entries = ppt.get("ppt_media_mp4_entries")
    return entries if isinstance(entries, list) else []


def evaluate_success_checks(evidence: dict[str, Any], allow_placeholder_media: bool = False) -> dict[str, dict[str, Any]]:
    image_count = len(evidence.get("generated_image_paths") or [])
    clip_count = len(evidence.get("clip_download_paths") or [])
    final_video = evidence.get("final_video_path")
    ppt = evidence.get("ppt_path")
    final_content = _final_video_content(evidence)
    ffprobe = _ffprobe_result(evidence)
    ppt_media_entries = _ppt_media_entries(evidence)
    has_audio_stream = int(ffprobe.get("audio_stream_count") or 0) >= 1
    has_final_schema = (
        final_content.get("voice_gender") == "male"
        and final_content.get("voice_language") == "zh-CN"
        and final_content.get("audio_verified") is True
        and final_content.get("english_audio_detected") is False
        and bool(final_content.get("narration_audio_path"))
        and bool(final_content.get("subtitle_srt_path"))
        and bool(final_content.get("concat_manifest_path"))
        and final_content.get("video_path") == FINAL_VIDEO_REL_PATH
    )
    return {
        "has_real_image": {
            "ok": allow_placeholder_media or image_count >= 1,
            "count": image_count,
            "required": ">=1 unless --allow-placeholder-media",
        },
        "has_real_video_clip": {
            "ok": allow_placeholder_media or clip_count >= 1,
            "count": clip_count,
            "required": ">=1 unless --allow-placeholder-media",
        },
        "has_final_video": {
            "ok": _non_empty_artifact(final_video),
            "artifact": final_video,
            "required": FINAL_VIDEO_REL_PATH,
        },
        "has_ppt": {
            "ok": _non_empty_artifact(ppt),
            "artifact": ppt,
            "required": "downloaded .pptx",
        },
        "has_verified_audio": {
            "ok": allow_placeholder_media or has_audio_stream,
            "ffprobe": ffprobe,
            "required": "ffprobe audio_stream_count >= 1 unless --allow-placeholder-media",
        },
        "has_final_video_schema": {
            "ok": allow_placeholder_media or has_final_schema,
            "content": final_content,
            "required": "male zh-CN narration schema with verified audio and final video path",
        },
        "has_embedded_ppt_video": {
            "ok": allow_placeholder_media or len(ppt_media_entries) >= 1,
            "ppt_media_mp4_entries": ppt_media_entries,
            "required": ">=1 embedded ppt/media/*.mp4 unless --allow-placeholder-media",
        },
    }


def all_success_checks_passed(checks: dict[str, dict[str, Any]]) -> bool:
    return all(bool(item.get("ok")) for item in checks.values())


def probe_media(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {"ok": False, "error": mask_text(completed.stderr.strip())}
    try:
        payload = json.loads(completed.stdout or "{}")
    except ValueError as exc:
        return {"ok": False, "error": f"ffprobe returned invalid JSON: {mask_text(str(exc))}"}
    streams = payload.get("streams") if isinstance(payload.get("streams"), list) else []
    audio_streams = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "audio"]
    video_streams = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    return {
        "ok": True,
        "audio_stream_count": len(audio_streams),
        "video_stream_count": len(video_streams),
        "audio_codecs": [stream.get("codec_name") for stream in audio_streams],
    }


def extract_error_code(body_excerpt: str) -> str | None:
    try:
        payload = json.loads(body_excerpt)
    except Exception:
        return None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("code"):
            return str(error["code"])
    return None


def build_provider_error_summary(calls: list[dict[str, Any]], failed_step: str | None, failure: str | None) -> dict[str, Any]:
    failed_calls = [call for call in calls if int(call.get("http_status") or 0) >= 400]
    last = failed_calls[-1] if failed_calls else (calls[-1] if calls else {})
    body_excerpt = mask_text(str(last.get("body_excerpt") or ""))
    return {
        "failed_step": failed_step,
        "failure": mask_text(failure or ""),
        "last_error": {
            "step": last.get("step"),
            "method": last.get("method"),
            "path": last.get("path"),
            "http_status": last.get("http_status"),
            "error_code": extract_error_code(body_excerpt),
            "body_excerpt": body_excerpt[:1200],
        },
        "http_error_calls": [
            {
                "step": call.get("step"),
                "method": call.get("method"),
                "path": call.get("path"),
                "http_status": call.get("http_status"),
                "error_code": extract_error_code(mask_text(str(call.get("body_excerpt") or ""))),
                "body_excerpt": mask_text(str(call.get("body_excerpt") or ""))[:1200],
            }
            for call in failed_calls
        ],
    }


class EvidenceWriter:
    def __init__(self, evidence_dir: Path, evidence: dict[str, Any]):
        self.evidence_dir = evidence_dir
        self.evidence = evidence

    def flush(self) -> None:
        write_json(self.evidence_dir / "summary.json", self.evidence)
        write_json(self.evidence_dir / "manifest.json", self.evidence.get("manifest") or {})
        write_json(self.evidence_dir / "tasks.json", self.evidence.get("tasks") or [])
        write_json(self.evidence_dir / "generated-image-paths.json", self.evidence.get("generated_image_paths") or [])
        write_json(self.evidence_dir / "video-task-paths.json", self.evidence.get("video_task_paths") or [])
        write_json(self.evidence_dir / "final-artifact-paths.json", self.evidence.get("final_artifact_paths") or {})
        write_json(self.evidence_dir / "video-provider-readiness.json", self.evidence.get("video_provider_readiness") or {})
        write_json(
            self.evidence_dir / "provider-error-summary.json",
            build_provider_error_summary(
                self.evidence.get("calls") or [],
                self.evidence.get("failed_step"),
                self.evidence.get("failure"),
            ),
        )


class EvidenceClient:
    def __init__(self, api_base: str, evidence: dict[str, Any], api_token: str | None = None):
        self.api_base = api_base.rstrip("/")
        headers = {"Authorization": f"Bearer {api_token}"} if api_token else None
        self.client = httpx.Client(timeout=240, headers=headers)
        self.evidence = evidence

    def close(self) -> None:
        self.client.close()

    def request_json(self, step: str, method: str, path: str, json_body: Any | None = None) -> dict[str, Any]:
        try:
            response = self.client.request(method, f"{self.api_base}{path}", json=json_body)
        except Exception as exc:
            self._record(step, method, path, None, mask_text(str(exc)))
            raise SmokeStepError(step, f"{method} {path} request failed: {mask_text(str(exc))}") from exc
        body_excerpt = mask_text(response.text)[:1800]
        self._record(step, method, path, response.status_code, body_excerpt)
        if response.status_code >= 400:
            raise SmokeStepError(step, f"{method} {path} returned HTTP {response.status_code}: {body_excerpt}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise SmokeStepError(step, f"{method} {path} returned non-JSON response: {body_excerpt}") from exc
        if payload.get("ok") is not True:
            raise SmokeStepError(step, f"{method} {path} returned non-ok response: {mask_text(json.dumps(payload, ensure_ascii=False))}")
        return payload["data"]

    def upload_file(self, step: str, path: str, file_path: Path) -> dict[str, Any]:
        with file_path.open("rb") as stream:
            response = self.client.post(
                f"{self.api_base}{path}",
                files={"file": (file_path.name, stream, "application/pdf")},
            )
        body_excerpt = mask_text(response.text)[:1800]
        self._record(step, "POST", path, response.status_code, body_excerpt)
        if response.status_code >= 400:
            raise SmokeStepError(step, f"POST {path} returned HTTP {response.status_code}: {body_excerpt}")
        payload = response.json()
        if payload.get("ok") is not True:
            raise SmokeStepError(step, f"POST {path} returned non-ok response: {mask_text(json.dumps(payload, ensure_ascii=False))}")
        return payload["data"]

    def download_file(self, step: str, path: str, out_file: Path) -> dict[str, Any]:
        response = self.client.get(f"{self.api_base}{path}")
        self._record(step, "GET", path, response.status_code, f"<binary:{len(response.content)}>")
        if response.status_code >= 400:
            excerpt = mask_text(response.text)[:1800]
            raise SmokeStepError(step, f"GET {path} returned HTTP {response.status_code}: {excerpt}")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(response.content)
        return {
            "api_path": path.removeprefix(f"/projects/{self.evidence.get('project_id')}/"),
            "download_url": path,
            "local_path": str(out_file),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(response.content),
            "http_status": response.status_code,
        }

    def _record(self, step: str, method: str, path: str, status: int | None, excerpt: str) -> None:
        self.evidence["calls"].append(
            {
                "step": step,
                "method": method,
                "path": path,
                "http_status": status,
                "body_excerpt": mask_text(excerpt),
            }
        )


def safe_filename_from_rel_path(rel_path: str) -> str:
    return Path(str(rel_path).replace("\\", "/")).name


def generate_and_approve(
    client: EvidenceClient,
    writer: EvidenceWriter,
    project_id: str,
    node_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    generated = client.request_json(f"{node_id}_generate", "POST", f"/projects/{project_id}/nodes/{node_id}/generate", body or {})
    writer.evidence["node_results"][f"{node_id}_generated"] = summarize_node(generated)
    writer.flush()
    approved = client.request_json(f"{node_id}_approve", "POST", f"/projects/{project_id}/nodes/{node_id}/approve", {})
    writer.evidence["node_results"][f"{node_id}_approved"] = approved
    current = client.request_json(f"{node_id}_get", "GET", f"/projects/{project_id}/nodes/{node_id}")
    writer.evidence["node_results"][node_id] = summarize_node(current)
    writer.flush()
    return current


def build_node_generate_body(node_id: str, args: argparse.Namespace) -> dict[str, Any]:
    if node_id != "intro_video_asset":
        return {}
    return {
        "image_size": args.image_size,
        "image_limit": args.image_limit,
        "image_quality": args.image_quality,
        "min_successful_images": args.min_successful_images,
        "allow_partial_assets": args.allow_partial_assets,
    }


def build_final_video_generate_body(args: argparse.Namespace) -> dict[str, Any]:
    body = {
        "model": args.video_model,
        "size": args.video_size,
        "mode": args.video_mode,
        "full_run": True,
    }
    if args.video_shot_limit:
        body["video_shot_limit"] = args.video_shot_limit
    return body


def default_video_model_from_env() -> str:
    return (
        os.environ.get("VIDEO_MODEL")
        or os.environ.get("OMNI_DEFAULT_MODEL")
        or os.environ.get("NEWAPI_DEFAULT_MODEL")
        or DEFAULT_VIDEO_MODEL
    )


def collect_final_video_node_content(client: EvidenceClient, evidence: dict[str, Any], project_id: str) -> None:
    final_video_node = client.request_json("final_video_get", "GET", f"/projects/{project_id}/nodes/final_video")
    evidence.setdefault("node_results", {})["final_video"] = summarize_node(final_video_node)
    content = final_video_node.get("content") if isinstance(final_video_node.get("content"), dict) else {}
    evidence["final_video_node_content"] = sanitize_for_evidence(content)


def summarize_node(node: dict[str, Any]) -> dict[str, Any]:
    content = node.get("content") if isinstance(node.get("content"), dict) else {}
    summary: dict[str, Any] = {
        key: node.get(key)
        for key in ["node_id", "status", "version_id", "current_version_id", "video_path"]
        if key in node
    }
    if "selected_anchor" in content:
        summary["selected_anchor"] = content["selected_anchor"]
    if "assets" in content and isinstance(content["assets"], list):
        summary["asset_count"] = len(content["assets"])
    if "shots" in content and isinstance(content["shots"], list):
        summary["shot_count"] = len(content["shots"])
        if content["shots"]:
            summary["last_subtitle"] = content["shots"][-1].get("subtitle")
    if "rule_warnings" in content:
        summary["rule_warnings"] = content["rule_warnings"]
    if "clip_count" in content:
        summary["clip_count"] = content["clip_count"]
    return summary


def edit_and_approve_intro_selection(client: EvidenceClient, writer: EvidenceWriter, project_id: str) -> dict[str, Any]:
    generated = client.request_json("intro_selection_generate", "POST", f"/projects/{project_id}/nodes/intro_selection/generate", {})
    content = dict(generated.get("content") or {})
    selected_anchor = str(content.get("selected_anchor") or "").strip()
    if len(selected_anchor) < 10:
        selected_anchor = "视频最后用清晰数量问题回到课堂中5以内数的认识任务。"
    elif "5以内数的认识" not in selected_anchor and "1、2、3、4、5" not in selected_anchor:
        selected_anchor = f"{selected_anchor} 这个镜头最后要回到课堂中5以内数的认识任务。"
    content["selected_anchor"] = selected_anchor
    edited = client.request_json("intro_selection_edit_selected_anchor", "POST", f"/projects/{project_id}/nodes/intro_selection/edit", {"content": content})
    approved = client.request_json("intro_selection_approve", "POST", f"/projects/{project_id}/nodes/intro_selection/approve", {})
    current = client.request_json("intro_selection_get", "GET", f"/projects/{project_id}/nodes/intro_selection")
    writer.evidence["node_results"]["intro_selection_generated"] = summarize_node(generated)
    writer.evidence["node_results"]["intro_selection_edited"] = summarize_node(edited)
    writer.evidence["node_results"]["intro_selection_approved"] = approved
    writer.evidence["node_results"]["intro_selection"] = summarize_node(current)
    writer.flush()
    return current


def refresh_project_state(client: EvidenceClient, writer: EvidenceWriter, project_id: str) -> None:
    try:
        writer.evidence["manifest"] = client.request_json("manifest", "GET", f"/projects/{project_id}/manifest")
    except Exception:
        pass
    try:
        writer.evidence["tasks"] = client.request_json("tasks", "GET", f"/projects/{project_id}/tasks")
    except Exception:
        pass
    writer.flush()


def collect_generated_images(client: EvidenceClient, writer: EvidenceWriter, project_id: str) -> None:
    tasks = client.request_json("tasks_after_images", "GET", f"/projects/{project_id}/tasks")
    writer.evidence["tasks"] = tasks
    image_items = []
    for task in tasks:
        if task.get("task_type") != "image_generation":
            continue
        image_path = task.get("image_path") or task.get("download_path") or (task.get("result") or {}).get("image_path")
        if not image_path:
            continue
        filename = safe_filename_from_rel_path(image_path)
        local_path = writer.evidence_dir / "images" / filename
        try:
            download = client.download_file("download_generated_image", f"/projects/{project_id}/images/{filename}", local_path)
        except SmokeStepError:
            download = {"api_path": image_path, "local_path": str(local_path), "bytes": 0, "download_error": True}
        image_items.append(
            {
                "task_id": task.get("task_id"),
                "status": task.get("status"),
                "provider_task_id": task.get("provider_task_id"),
                "api_path": image_path,
                **download,
            }
        )
    writer.evidence["generated_image_paths"] = image_items
    writer.flush()


def sync_video_tasks(
    client: EvidenceClient,
    writer: EvidenceWriter,
    project_id: str,
    initial_tasks: list[dict[str, Any]],
    timeout_sec: int,
    poll_interval_sec: int,
    allow_placeholder_media: bool,
) -> list[dict[str, Any]]:
    task_ids = [task.get("task_id") for task in initial_tasks if task.get("task_id")]
    if not task_ids:
        writer.evidence["video_task_paths"] = []
        writer.flush()
        return []
    deadline = time.monotonic() + timeout_sec
    latest: list[dict[str, Any]] = list(initial_tasks)
    terminal = {"completed", "failed", "generated"}
    while time.monotonic() < deadline:
        latest = [
            client.request_json("sync_video_task", "GET", f"/projects/{project_id}/tasks/{task_id}")
            for task_id in task_ids
        ]
        writer.evidence["tasks"] = client.request_json("tasks_during_video_sync", "GET", f"/projects/{project_id}/tasks")
        writer.evidence["video_task_paths"] = build_video_task_paths(latest)
        writer.flush()
        statuses = {task.get("status") for task in latest}
        if all(status in terminal for status in statuses):
            if allow_placeholder_media:
                break
            downloaded = [
                task
                for task in latest
                if task.get("status") == "completed"
                and (
                    task.get("download_status")
                    or ((task.get("result") if isinstance(task.get("result"), dict) else {}) or {}).get("download_status")
                )
                == "downloaded"
            ]
            if downloaded:
                break
            failed = [task for task in latest if task.get("status") == "failed"]
            if failed:
                writer.evidence["video_task_failure_summary"] = summarize_failed_video_tasks(failed)
                writer.evidence["video_provider_readiness"] = build_video_readiness_from_failed_tasks(failed)
                writer.flush()
                raise SmokeStepError("sync_video_tasks", f"video tasks failed before any clip was downloaded: {writer.evidence['video_task_failure_summary']}")
        time.sleep(poll_interval_sec)
    else:
        raise SmokeStepError("sync_video_tasks", f"video tasks did not reach terminal state in {timeout_sec}s")
    return latest


def summarize_failed_video_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task in tasks:
        result = task.get("result") if isinstance(task.get("result"), dict) else {}
        rows.append(
            {
                "task_id": task.get("task_id"),
                "provider_task_id": task.get("provider_task_id") or result.get("provider_task_id"),
                "status": task.get("status"),
                "error_code": task.get("error_code") or result.get("error_code"),
                "retryable": task.get("retryable") if task.get("retryable") is not None else result.get("retryable"),
                "error_message": mask_text(str(task.get("error_message") or result.get("error_message") or ""))[:500],
            }
        )
    return rows


def build_video_readiness_from_failed_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    error_codes = [
        row.get("error_code")
        for row in summarize_failed_video_tasks(tasks)
        if row.get("error_code")
    ]
    provider_error_code = "VIDEO_QUOTA_EXHAUSTED" if "VIDEO_QUOTA_EXHAUSTED" in error_codes else (error_codes[0] if error_codes else None)
    return build_video_provider_readiness_report(
        env={
            "VIDEO_PROVIDER_MODE": os.environ.get("VIDEO_PROVIDER_MODE", "real"),
            "OCTO_API_KEY": os.environ.get("OCTO_API_KEY") or "<server-side-redacted>",
            "OCTO_BASE_URL": os.environ.get("OCTO_BASE_URL", "https://otuapi.com"),
            "OCTO_VIDEO_PROVIDER": os.environ.get("OCTO_VIDEO_PROVIDER", "octo"),
            "VIDEO_MODEL": default_video_model_from_env(),
        },
        require_real=False,
        provider_error_code=provider_error_code,
    )


def build_video_task_paths(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task in tasks:
        result = task.get("result") if isinstance(task.get("result"), dict) else {}
        rows.append(
            {
                "task_id": task.get("task_id"),
                "status": task.get("status"),
                "provider_task_id": task.get("provider_task_id") or result.get("provider_task_id"),
                "download_path": task.get("download_path") or result.get("download_path"),
                "clip_path": task.get("clip_path") or result.get("clip_path"),
                "download_status": task.get("download_status") or result.get("download_status"),
                "error_code": task.get("error_code") or result.get("error_code"),
                "retryable": task.get("retryable") if task.get("retryable") is not None else result.get("retryable"),
            }
        )
    return rows


def download_completed_clips(client: EvidenceClient, writer: EvidenceWriter, project_id: str, tasks: list[dict[str, Any]]) -> None:
    clips = []
    for task in tasks:
        result = task.get("result") if isinstance(task.get("result"), dict) else {}
        status = task.get("status")
        download_status = task.get("download_status") or result.get("download_status")
        rel_path = task.get("download_path") or result.get("download_path") or task.get("clip_path") or result.get("clip_path")
        if status != "completed" or download_status != "downloaded" or not rel_path:
            continue
        filename = safe_filename_from_rel_path(rel_path)
        local_path = writer.evidence_dir / "clips" / filename
        download = client.download_file("download_video_clip", f"/projects/{project_id}/clips/{filename}", local_path)
        clips.append(
            {
                "task_id": task.get("task_id"),
                "provider_task_id": task.get("provider_task_id") or result.get("provider_task_id"),
                "api_path": rel_path,
                **download,
            }
        )
    writer.evidence["clip_download_paths"] = clips
    writer.flush()


def download_final_artifacts(client: EvidenceClient, writer: EvidenceWriter, project_id: str) -> None:
    final_video = client.download_file("download_final_video", f"/projects/{project_id}/outputs/final_video.mp4", writer.evidence_dir / "final_video.mp4")
    writer.evidence["final_video_path"] = final_video
    export = client.request_json("export_ppt", "POST", f"/projects/{project_id}/export/ppt", {})
    ppt_filename = export["filename"]
    ppt = client.download_file("download_ppt", export["download_url"], writer.evidence_dir / ppt_filename)
    ppt.update({"api_path": export.get("path"), "download_url": export.get("download_url"), "video_path": export.get("video_path")})
    media_entries: list[str] = []
    with zipfile.ZipFile(writer.evidence_dir / ppt_filename) as archive:
        media_entries = [name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".mp4")]
    ppt["ppt_media_mp4_entries"] = media_entries
    writer.evidence["ppt_path"] = ppt
    writer.evidence["final_artifact_paths"] = {
        "final_video": final_video,
        "ppt": ppt,
        "ppt_media_mp4_entries": media_entries,
    }
    writer.flush()


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_pdf = Path(args.fixture_pdf)
    if not fixture_pdf.is_absolute():
        fixture_pdf = repo_root / fixture_pdf
    if not fixture_pdf.exists():
        raise SystemExit(f"fixture PDF not found: {fixture_pdf}")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    evidence_dir = (repo_root / args.evidence_root / timestamp).resolve()
    api_token = args.api_token or None
    if args.api_token_env:
        import os

        api_token = os.environ.get(args.api_token_env) or api_token

    evidence: dict[str, Any] = {
        "ok": False,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "api_base": args.api_base,
        "provider_mode": args.provider_mode,
        "image_provider_mode": args.image_provider_mode,
        "video_provider_mode": args.video_provider_mode,
        "tts_provider_mode": args.tts_provider_mode,
        "storage": args.storage,
        "fixture_pdf": str(fixture_pdf),
        "evidence_dir": str(evidence_dir),
        "allow_placeholder_media": args.allow_placeholder_media,
        "image_limit": args.image_limit,
        "image_quality": args.image_quality,
        "min_successful_images": args.min_successful_images,
        "allow_partial_assets": args.allow_partial_assets,
        "project_id": None,
        "failed_step": None,
        "failure": None,
        "calls": [],
        "node_results": {},
        "manifest": {},
        "tasks": [],
        "generated_image_paths": [],
        "video_task_paths": [],
        "clip_download_paths": [],
        "final_video_path": None,
        "ppt_path": None,
        "final_artifact_paths": {},
        "final_video_node_content": {},
        "ffprobe": {},
        "success_checks": {},
    }
    writer = EvidenceWriter(evidence_dir, evidence)
    writer.flush()
    client = EvidenceClient(args.api_base, evidence, api_token=api_token)
    try:
        evidence["health"] = client.request_json("health", "GET", "/health")
        project = client.request_json(
            "create_project",
            "POST",
            "/projects",
            {
                "name": args.project_name or f"T075 real fullchain smoke {timestamp}",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
        project_id = project["project_id"]
        evidence["project_id"] = project_id
        evidence["project"] = {k: project.get(k) for k in ["project_id", "name", "project_dir", "status"]}
        writer.flush()

        client.upload_file("upload_pdf", f"/projects/{project_id}/textbook", fixture_pdf)
        generate_and_approve(client, writer, project_id, "textbook_parse", {"knowledge_point_id": args.knowledge_point_id})
        generate_and_approve(client, writer, project_id, "lesson_plan")
        edit_and_approve_intro_selection(client, writer, project_id)
        for node_id in ["intro_video_script", "intro_video_screenplay", "intro_video_asset", "storyboard"]:
            body = build_node_generate_body(node_id, args)
            generate_and_approve(client, writer, project_id, node_id, body)
            if node_id == "intro_video_asset":
                collect_generated_images(client, writer, project_id)

        final_video = client.request_json(
            "final_video_generate",
            "POST",
            f"/projects/{project_id}/nodes/final_video/generate",
            build_final_video_generate_body(args),
        )
        evidence["node_results"]["final_video_generated"] = summarize_node(final_video)
        initial_video_tasks = list(final_video.get("tasks") or [])
        evidence["video_task_paths"] = build_video_task_paths(initial_video_tasks)
        writer.flush()

        latest_video_tasks = sync_video_tasks(
            client,
            writer,
            project_id,
            initial_video_tasks,
            timeout_sec=args.task_timeout_sec,
            poll_interval_sec=args.poll_interval_sec,
            allow_placeholder_media=args.allow_placeholder_media,
        )
        download_completed_clips(client, writer, project_id, latest_video_tasks)
        download_final_artifacts(client, writer, project_id)
        collect_final_video_node_content(client, evidence, project_id)
        final_local_path = Path((evidence.get("final_video_path") or {}).get("local_path") or "")
        if final_local_path.exists():
            evidence["ffprobe"] = sanitize_for_evidence(probe_media(final_local_path))
        writer.flush()
        refresh_project_state(client, writer, project_id)

        checks = evaluate_success_checks(evidence, allow_placeholder_media=args.allow_placeholder_media)
        evidence["success_checks"] = checks
        if not all_success_checks_passed(checks):
            raise SmokeStepError("success_checks", "T075 success checks failed")
        evidence["ok"] = True
        return evidence
    except SmokeStepError as exc:
        evidence["failed_step"] = exc.step
        evidence["failure"] = mask_text(str(exc))
        refresh_project_state(client, writer, evidence["project_id"]) if evidence.get("project_id") else writer.flush()
        return evidence
    except Exception as exc:
        evidence["failed_step"] = evidence.get("failed_step") or "unexpected"
        evidence["failure"] = mask_text(str(exc))
        refresh_project_state(client, writer, evidence["project_id"]) if evidence.get("project_id") else writer.flush()
        return evidence
    finally:
        client.close()
        evidence["finished_at"] = datetime.now().isoformat(timespec="seconds")
        evidence["success_checks"] = evaluate_success_checks(evidence, allow_placeholder_media=args.allow_placeholder_media)
        writer.flush()
        print(f"[t075] summary={evidence_dir / 'summary.json'}")
        if evidence.get("failed_step"):
            print(f"[t075] failed_step={evidence['failed_step']}")
        print(f"[t075] ok={evidence.get('ok')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T075 real fullchain PDF-to-PPT smoke with structured evidence.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--fixture-pdf", default=r"fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf")
    parser.add_argument("--storage", default="storage")
    parser.add_argument("--provider-mode", default="real", choices=["fake", "placeholder", "real", "deepseek", "minimax"])
    parser.add_argument("--image-provider-mode", default="real", choices=["fake", "placeholder", "real"])
    parser.add_argument("--video-provider-mode", default="real", choices=["fake", "placeholder", "real"])
    parser.add_argument("--tts-provider-mode", default="real", choices=["placeholder", "real"])
    parser.add_argument("--evidence-root", default=r"docs\qa-audits\t075-real-fullchain-smoke-evidence")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--knowledge-point-id", default="kp_001")
    parser.add_argument("--image-size", default="1024x1024")
    parser.add_argument("--image-limit", type=int, default=1)
    parser.add_argument("--image-quality", default="low")
    parser.add_argument("--min-successful-images", type=int, default=1)
    parser.add_argument("--allow-partial-assets", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--video-model", default=default_video_model_from_env())
    parser.add_argument("--video-size", default="1280x720")
    parser.add_argument("--video-mode", default="reference")
    parser.add_argument("--video-shot-limit", type=int, default=1)
    parser.add_argument("--task-timeout-sec", type=int, default=900)
    parser.add_argument("--poll-interval-sec", type=int, default=15)
    parser.add_argument("--allow-placeholder-media", action="store_true", help="Allow fake/placeholder runs to pass without real image and clip artifacts.")
    parser.add_argument("--api-token", default="", help="Optional API token. Do not pass provider keys here.")
    parser.add_argument("--api-token-env", default="BACKEND_API_TOKEN", help="Environment variable containing optional API token.")
    return parser.parse_args()


def main() -> None:
    evidence = run(parse_args())
    raise SystemExit(0 if evidence.get("ok") else 1)


if __name__ == "__main__":
    main()
