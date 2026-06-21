from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt

from .video_outputs import FINAL_VIDEO_REL_PATH, PLACEHOLDER_MP4, ensure_final_video_output


class PptExportError(RuntimeError):
    pass


def export_project_ppt(project: dict[str, Any], project_dir: Path, allow_placeholder: bool = True) -> dict[str, str]:
    exports_dir = project_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    if allow_placeholder:
        video_path = ensure_final_video_output(project_dir)
    else:
        video_path = project_dir / FINAL_VIDEO_REL_PATH
        if not video_path.exists():
            raise PptExportError("真实视频模式下缺少已合成的 final_video.mp4")
        if video_path.read_bytes() == PLACEHOLDER_MP4:
            raise PptExportError("真实视频模式下 final_video.mp4 不能是占位视频")

    filename = "lesson-video-demo.pptx"
    pptx_path = exports_dir / filename
    presentation = Presentation()
    _add_cover_slide(presentation, project)
    _add_video_slide(presentation, video_path)
    try:
        presentation.save(pptx_path)
    except Exception as exc:
        raise PptExportError(f"PPTX 保存失败：{exc}") from exc

    return {
        "filename": filename,
        "path": f"exports/{filename}",
        "download_url": f"/projects/{project['project_id']}/exports/{filename}",
        "video_path": FINAL_VIDEO_REL_PATH,
    }


def _add_cover_slide(presentation: Presentation, project: dict[str, Any]) -> None:
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    title_box = slide.shapes.add_textbox(Inches(0.9), Inches(1.6), Inches(8.2), Inches(0.9))
    title_frame = title_box.text_frame
    title_frame.clear()
    title = title_frame.paragraphs[0]
    title.text = project.get("name") or "山海教育公开课"
    title.font.size = Pt(34)
    title.font.bold = True

    meta_box = slide.shapes.add_textbox(Inches(0.95), Inches(2.75), Inches(8), Inches(0.6))
    meta = meta_box.text_frame.paragraphs[0]
    meta.text = f"数学 · {project.get('grade', '')}年级 · {project.get('textbook_version', '')} · {project.get('volume', '')}"
    meta.font.size = Pt(18)


def _add_video_slide(presentation: Presentation, video_path: Path) -> None:
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(8.5), Inches(0.5))
    title = title_box.text_frame.paragraphs[0]
    title.text = "导入视频"
    title.font.size = Pt(24)
    title.font.bold = True
    try:
        slide.shapes.add_movie(
            str(video_path),
            Inches(0.75),
            Inches(1.0),
            Inches(8.5),
            Inches(4.8),
            mime_type="video/mp4",
        )
    except Exception as exc:
        raise PptExportError(f"视频嵌入失败：{exc}") from exc
