from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .providers import FakeProvider, ProviderError, sanitize_provider_excerpt
from .store import ProjectStore, now_iso
from .video_outputs import FINAL_VIDEO_REL_PATH, compose_final_video_from_clips, compose_final_video_with_audio, write_concat_manifest, write_placeholder_narration_audio, write_subtitle_srt


class VideoOrchestrator:
    def __init__(
        self,
        *,
        store: ProjectStore,
        text_provider: Any,
        video_provider: Any | None,
        tts_provider: Any | None,
        video_model: str,
        reference_url_resolver: Callable[[str], dict[str, str]],
    ):
        self.store = store
        self.text_provider = text_provider
        self.video_provider = video_provider
        self.tts_provider = tts_provider
        self.video_model = video_model
        self.reference_url_resolver = reference_url_resolver

    def generate(self, conn, project_id: str, project_dir: Path, options: dict[str, Any]) -> dict[str, Any]:
        storyboard = self.store.current_content(conn, project_id, "storyboard")
        if not storyboard:
            raise PermissionError("Storyboard is not ready")
        tasks = []
        clips = []
        is_fake_video = isinstance(self.text_provider, FakeProvider) or self.video_provider is None
        shots = storyboard["shots"] if is_fake_video or self.video_provider is not None or options.get("full_run") else storyboard["shots"][:1]
        video_shot_limit = _positive_int_option(options.get("video_shot_limit") or options.get("clip_limit"))
        if video_shot_limit is not None:
            shots = shots[:video_shot_limit]
        model = options.get("model") or self.video_model
        size = options.get("size", "1280x720")
        mode = options.get("mode", "reference")
        reference_urls = self.reference_url_resolver(project_id)
        for shot in shots:
            clip_name = f"clips/{shot['shot_id']}.mp4"
            shot_reference_urls = [
                reference_urls[reference_id]
                for reference_id in shot.get("reference_image_ids", [])
                if reference_id in reference_urls
            ]
            payload = {
                "shot_id": shot["shot_id"],
                "model": model,
                "size": size,
                "mode": mode,
                "prompt": shot["model_prompt"],
                "reference_image_ids": shot["reference_image_ids"],
            }
            if shot_reference_urls:
                payload["reference_image_urls"] = shot_reference_urls
            if is_fake_video:
                task = self.store.create_task(
                    conn,
                    project_id,
                    "final_video",
                    "video_clip_generation",
                    {**payload, "model_prompt": shot["model_prompt"]},
                    status="generated",
                    result={"download_path": clip_name},
                )
            else:
                task = self._submit_real_video_task(conn, project_id, shot, payload, clip_name, shot_reference_urls, model, size)
            tasks.append(task)
            clips.append(
                {
                    "shot_id": shot["shot_id"],
                    "api_task_id": task["task_id"],
                    "download_path": clip_name,
                    "status": task["status"],
                    "reference_image_ids": shot["reference_image_ids"],
                }
            )
        content = {
            "clip_count": len(clips),
            "clips": clips,
            "video_path": FINAL_VIDEO_REL_PATH,
            "model_audio_policy": "discarded_or_mute_later",
            "english_audio_detected": False,
        }
        if is_fake_video:
            content = self.finalize_artifacts(conn, project_id, project_dir, tasks, content)
        final_status = "needs_review" if is_fake_video else "drafted"
        self.store.write_version(conn, project_id, "final_video", content, "ai", self.text_provider.name, final_status)
        return {"node_id": "final_video", "status": final_status, "content": content, "tasks": tasks, "video_path": FINAL_VIDEO_REL_PATH}

    def _submit_real_video_task(
        self,
        conn,
        project_id: str,
        shot: dict[str, Any],
        payload: dict[str, Any],
        clip_name: str,
        shot_reference_urls: list[str],
        model: str,
        size: str,
    ) -> dict[str, Any]:
        task = self.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            payload,
            status="submitting",
            result={"download_path": clip_name, "provider_phase": "submit"},
        )
        try:
            submit_payload = {"model": model, "prompt": shot["model_prompt"], "size": size}
            if shot_reference_urls:
                submit_payload["images"] = shot_reference_urls
            submitted = self.video_provider.submit_video(submit_payload)
        except ProviderError as exc:
            result = {
                "download_path": clip_name,
                "clip_path": clip_name,
                "provider_phase": "submit",
                **provider_error_result(exc),
            }
            task = self.store.update_task(conn, task["task_id"], "failed", result, str(exc))
            self.store.record_error(conn, project_id, "final_video", exc.code, str(exc))
            failure_content = {
                "clip_count": 1,
                "clips": [
                    {
                        "shot_id": shot["shot_id"],
                        "api_task_id": task["task_id"],
                        "download_path": clip_name,
                        "status": "failed",
                        "reference_image_ids": shot["reference_image_ids"],
                    }
                ],
                "video_path": FINAL_VIDEO_REL_PATH,
                "error_code": exc.code,
                "error_message": str(exc),
                "model_audio_policy": "discarded_or_mute_later",
                "english_audio_detected": False,
            }
            self.store.write_version(conn, project_id, "final_video", failure_content, "ai", self.text_provider.name, "blocked")
            conn.commit()
            raise
        return self.store.update_task(
            conn,
            task["task_id"],
            submitted["status"] or "queued",
            {**submitted, "download_path": clip_name, "provider_phase": "submit"},
        )

    def compose_if_ready(self, conn, project_id: str, project_dir: Path) -> dict[str, Any] | None:
        tasks = self.store.tasks(project_id)
        video_tasks = [task for task in tasks if task["node_id"] == "final_video" and task["task_type"] == "video_clip_generation"]
        if not video_tasks or any(task["status"] != "completed" or task["result"].get("download_status") != "downloaded" for task in video_tasks):
            return None
        clip_paths = [task["download_path"] for task in video_tasks if task.get("download_path")]
        if len(clip_paths) != len(video_tasks):
            return None
        try:
            has_narration_context = bool(self.store.current_content(conn, project_id, "storyboard")) or bool(
                self.store.current_content(conn, project_id, "intro_video_script")
            )
            output_path = None if has_narration_context else compose_final_video_from_clips(project_dir, clip_paths)
        except RuntimeError as exc:
            message = sanitize_provider_excerpt(str(exc), 240)
            self.store.record_error(conn, project_id, "final_video", "FINAL_VIDEO_COMPOSE_FAILED", message)
            failure_content = {
                "clip_count": len(video_tasks),
                "clips": [
                    {
                        "shot_id": task["payload"].get("shot_id"),
                        "api_task_id": task["task_id"],
                        "download_path": task["download_path"],
                        "status": "downloaded",
                        "reference_image_ids": task["payload"].get("reference_image_ids", []),
                    }
                    for task in video_tasks
                ],
                "video_path": FINAL_VIDEO_REL_PATH,
                "error_code": "FINAL_VIDEO_COMPOSE_FAILED",
                "error_message": message,
                "model_audio_policy": "discarded_or_mute_later",
                "english_audio_detected": False,
            }
            self.store.write_version(conn, project_id, "final_video", failure_content, "ai", self.text_provider.name, "blocked")
            return {
                "compose_status": "failed",
                "compose_error": message,
                "error_code": "FINAL_VIDEO_COMPOSE_FAILED",
                "retryable": False,
            }
        base_content = {
            "clip_count": len(video_tasks),
            "clips": [
                {
                    "shot_id": task["payload"].get("shot_id"),
                    "api_task_id": task["task_id"],
                    "download_path": task["download_path"],
                    "status": "downloaded",
                    "reference_image_ids": task["payload"].get("reference_image_ids", []),
                }
                for task in video_tasks
            ],
            "video_path": FINAL_VIDEO_REL_PATH,
            "model_audio_policy": "discarded_or_mute_later",
            "english_audio_detected": False,
        }
        if output_path is not None:
            content = {**base_content, "output_size_bytes": output_path.stat().st_size}
        else:
            content = self.finalize_artifacts(conn, project_id, project_dir, video_tasks, base_content)
        self.store.write_version(conn, project_id, "final_video", content, "ai", self.text_provider.name, "needs_review")
        return {"compose_status": "completed", "final_video_path": FINAL_VIDEO_REL_PATH}

    def finalize_artifacts(
        self,
        conn,
        project_id: str,
        project_dir: Path,
        video_tasks: list[dict[str, Any]],
        content: dict[str, Any],
    ) -> dict[str, Any]:
        narration = self._narration_text_for_final_video(conn, project_id)
        audio_rel_path = self._ensure_narration_audio(project_dir, narration)
        storyboard = self.store.current_content(conn, project_id, "storyboard") or {}
        shots = storyboard.get("shots") if isinstance(storyboard, dict) else []
        narration_slices = [str(shot.get("narration_slice") or shot.get("subtitle") or "") for shot in shots if isinstance(shot, dict)]
        durations = [int(shot.get("duration_sec") or 10) for shot in shots if isinstance(shot, dict)]
        subtitle_path = write_subtitle_srt(project_dir, narration_slices or [narration], durations or [max(10, len(narration) // 4)])
        clip_paths = [task.get("download_path") or task.get("result", {}).get("download_path") for task in video_tasks]
        clip_paths = [str(path) for path in clip_paths if path]
        output_path = compose_final_video_with_audio(project_dir, clip_paths, audio_rel_path)
        manifest = write_concat_manifest(
            project_dir,
            clip_paths,
            {
                "task_id": video_tasks[0]["task_id"] if video_tasks else None,
                "download_path": FINAL_VIDEO_REL_PATH,
                "reference_images": [clip.get("reference_image_ids", []) for clip in content.get("clips", [])],
                "final_video_seconds": sum(durations) if durations else None,
                "audio_streams": 1,
                "audio_verified": True,
                "voice_gender": "unknown",
                "voice_language": "zh-CN",
            },
        )
        subtitle_rel_path = str(subtitle_path.relative_to(project_dir)).replace("\\", "/")
        provider_task_ids = [str(task.get("result", {}).get("provider_task_id") or task["task_id"]) for task in video_tasks]
        return {
            **content,
            "video_path": FINAL_VIDEO_REL_PATH,
            "output_size_bytes": output_path.stat().st_size,
            "total_duration_sec": sum(durations) if durations else max(10, len(narration) // 4),
            "duration_sec": sum(durations) if durations else max(10, len(narration) // 4),
            "audio_streams_count": 1,
            "audio_verified": True,
            "voice_gender": "unknown",
            "voice_language": "zh-CN",
            "narration_audio_path": audio_rel_path,
            "audio_path": audio_rel_path,
            "subtitle_srt_path": subtitle_rel_path,
            "subtitle_path": subtitle_rel_path,
            "model_audio_policy": "discarded_or_muted",
            "english_audio_detected": False,
            "concat_manifest_path": str(manifest.relative_to(project_dir)).replace("\\", "/"),
            "provider_task_ids": provider_task_ids,
            "source_versions": self._source_versions(conn, project_id, ["storyboard", "intro_video_script"]),
            "generated_at": now_iso(),
        }

    def _narration_text_for_final_video(self, conn, project_id: str) -> str:
        script = self.store.current_content(conn, project_id, "intro_video_script") or {}
        narration = script.get("narration_full_text") if isinstance(script, dict) else ""
        return str(narration or "欢迎来到山海教育导入视频。")

    def _ensure_narration_audio(self, project_dir: Path, narration: str) -> str:
        audio_path = project_dir / "audio" / "narration.mp3"
        if self.tts_provider is None:
            write_placeholder_narration_audio(project_dir)
        else:
            self.tts_provider.synthesize(narration, audio_path)
        return str(audio_path.relative_to(project_dir)).replace("\\", "/")

    def _source_versions(self, conn, project_id: str, node_ids: list[str]) -> dict[str, str]:
        versions: dict[str, str] = {}
        for node_id in node_ids:
            try:
                state = self.store.node_state(conn, project_id, node_id)
            except KeyError:
                continue
            version_id = state.get("current_version_id")
            if version_id:
                versions[node_id] = str(version_id)
        return versions


def provider_error_result(exc: ProviderError) -> dict[str, Any]:
    result: dict[str, Any] = {
        "error_code": exc.code,
        "retryable": exc.retryable,
    }
    status_code = getattr(exc, "status_code", None)
    response_excerpt = getattr(exc, "response_excerpt", "")
    if status_code is not None:
        result["http_status"] = status_code
    if response_excerpt:
        result["response_excerpt"] = sanitize_provider_excerpt(response_excerpt)
    return result


def _positive_int_option(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
