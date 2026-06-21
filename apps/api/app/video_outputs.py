from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


FINAL_VIDEO_REL_PATH = "outputs/final_video.mp4"

PLACEHOLDER_MP4 = bytes.fromhex(
    "000000206674797069736f6d0000020069736f6d69736f32617663316d703431"
    "0000000866726565"
    "000000086d646174"
)


def ensure_final_video_output(project_dir: Path) -> Path:
    video_path = project_dir / FINAL_VIDEO_REL_PATH
    video_path.parent.mkdir(parents=True, exist_ok=True)
    if not video_path.exists():
        video_path.write_bytes(PLACEHOLDER_MP4)
    return video_path


def compose_final_video_from_clips(project_dir: Path, clip_rel_paths: list[str]) -> Path:
    if not clip_rel_paths:
        raise RuntimeError("没有可合成的视频片段")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法合成真实 final_video.mp4")
    output_path = project_dir / FINAL_VIDEO_REL_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clip_paths = []
    for rel_path in clip_rel_paths:
        clip_path = project_dir / rel_path
        if not clip_path.exists() or clip_path.stat().st_size == 0:
            raise RuntimeError(f"视频片段不存在或为空：{rel_path}")
        clip_paths.append(clip_path)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as manifest:
        manifest_path = Path(manifest.name)
        for clip_path in clip_paths:
            escaped = str(clip_path.resolve()).replace("'", "'\\''")
            manifest.write(f"file '{escaped}'\n")
    temp_output = output_path.with_suffix(".tmp.mp4")
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                "-c",
                "copy",
                str(temp_output),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if temp_output.stat().st_size == 0:
            raise RuntimeError("ffmpeg 合成输出为空")
        temp_output.replace(output_path)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip().splitlines()[-1:] or ["ffmpeg 合成失败"]
        raise RuntimeError(detail[0]) from exc
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"ffmpeg 输出解码失败：{exc}") from exc
    finally:
        manifest_path.unlink(missing_ok=True)
        if temp_output.exists():
            temp_output.unlink(missing_ok=True)
    return output_path


def write_subtitle_srt(project_dir: Path, narration_slices: list[str], durations: list[int]) -> Path:
    subtitle_path = project_dir / "audio" / "narration.srt"
    subtitle_path.parent.mkdir(parents=True, exist_ok=True)
    cursor = 0
    lines: list[str] = []
    for index, text in enumerate(narration_slices, start=1):
        duration = max(1, int(durations[index - 1] if index - 1 < len(durations) else 10))
        start = _srt_time(cursor)
        cursor += duration
        end = _srt_time(cursor)
        lines.extend([str(index), f"{start} --> {end}", text.strip() or " ", ""])
    subtitle_path.write_text("\n".join(lines), encoding="utf-8")
    return subtitle_path


def write_concat_manifest(project_dir: Path, clip_rel_paths: list[str], metadata: dict[str, Any]) -> Path:
    manifest_path = project_dir / "outputs" / "concat_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    manifest_path.write_text(
        json.dumps(
            {
                "status": "final",
                "clips": clip_rel_paths,
                **metadata,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def write_placeholder_narration_audio(project_dir: Path) -> Path:
    audio_path = project_dir / "audio" / "narration.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if not audio_path.exists():
        audio_path.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00")
    return audio_path


def compose_final_video_with_audio(project_dir: Path, clip_rel_paths: list[str], narration_audio_rel_path: str) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return ensure_final_video_output(project_dir)
    output_path = project_dir / FINAL_VIDEO_REL_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clip_paths = [project_dir / rel_path for rel_path in clip_rel_paths if (project_dir / rel_path).exists()]
    audio_path = project_dir / narration_audio_rel_path
    if not clip_paths or not audio_path.exists() or audio_path.stat().st_size == 0:
        return ensure_final_video_output(project_dir)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as manifest:
        manifest_path = Path(manifest.name)
        for clip_path in clip_paths:
            escaped = str(clip_path.resolve()).replace("'", "'\\''")
            manifest.write(f"file '{escaped}'\n")
    temp_video = output_path.with_suffix(".video.tmp.mp4")
    temp_output = output_path.with_suffix(".tmp.mp4")
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                "-an",
                "-c:v",
                "copy",
                str(temp_video),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(temp_video),
                "-i",
                str(audio_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                str(temp_output),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if temp_output.stat().st_size > 0:
            temp_output.replace(output_path)
            return output_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ensure_final_video_output(project_dir)
    finally:
        manifest_path.unlink(missing_ok=True)
        temp_video.unlink(missing_ok=True)
        temp_output.unlink(missing_ok=True)
    return ensure_final_video_output(project_dir)


def _srt_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"
