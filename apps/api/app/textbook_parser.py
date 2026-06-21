from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KNOWLEDGE_POINT_MARKDOWN_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "textbook-parsing"
    / "renjiao-grade1-volume1-2024"
    / "5以内数的认识_结构化文字教案.md"
)


@dataclass(frozen=True)
class TextbookSource:
    path: Path
    rel_path: str
    mime_type: str | None
    filename: str


class TextbookParser:
    def __init__(self, *, mineru_exe: str | None = None):
        self.mineru_exe = mineru_exe or os.environ.get("MINERU_EXE")

    def parse_uploaded_textbook(
        self,
        *,
        project_dir: Path,
        project: dict[str, Any],
        source: TextbookSource,
        selected_knowledge_point_id: str | None = None,
    ) -> dict[str, Any]:
        suffix = source.path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return {
                "textbook_text": source.path.read_text(encoding="utf-8", errors="ignore"),
                "textbook_source": {
                    "filename": source.filename,
                    "path": source.rel_path,
                    "mime_type": source.mime_type,
                    "parser": "plain_text",
                },
            }
        if suffix != ".pdf":
            raise ValueError(f"Unsupported textbook type for MVP: {suffix}")

        return self._parse_pdf_fixture(
            project_dir=project_dir,
            project=project,
            source=source,
            selected_knowledge_point_id=selected_knowledge_point_id,
        )

    def _parse_pdf_fixture(
        self,
        *,
        project_dir: Path,
        project: dict[str, Any],
        source: TextbookSource,
        selected_knowledge_point_id: str | None,
    ) -> dict[str, Any]:
        selected_id = selected_knowledge_point_id or "kp_001"
        knowledge_points = [
            {
                "id": "kp_001",
                "title": "5以内数的认识",
                "unit": "5以内数的认识和加、减法",
                "page_start": 14,
                "page_end": 23,
                "pdf_page_start": 19,
                "pdf_page_end": 28,
                "keywords": ["1-5", "比大小", "第几", "分与合"],
            }
        ]
        selected = next((item for item in knowledge_points if item["id"] == selected_id), None)
        if selected is None:
            raise ValueError(f"Unknown knowledge point: {selected_id}")

        markdown = self._load_fixture_markdown(selected)
        markdown_rel_path = f"knowledge-points/{selected['id']}.md"
        markdown_path = project_dir / markdown_rel_path
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")

        outline_rel_path = "assets/textbook_parse/textbook_outline.json"
        outline_path = project_dir / outline_rel_path
        outline_path.parent.mkdir(parents=True, exist_ok=True)

        textbook_meta = {
            "subject": "math",
            "grade": "1",
            "textbook_version": "renjiao",
            "volume": "shang",
            "title": "人教版小学数学一年级上册",
        }
        parser_info = {
            "parser": "mineru_fixture",
            "skill_path": "skills/pdf",
            "mineru_exe_configured": bool(self.mineru_exe),
            "source_pdf": source.rel_path,
        }
        outline_path.write_text(
            _json_dumps(
                {
                    "textbook_meta": textbook_meta,
                    "knowledge_points": knowledge_points,
                    "parser_info": parser_info,
                }
            ),
            encoding="utf-8",
        )

        return {
            "textbook_source": {
                "filename": source.filename,
                "path": source.rel_path,
                "mime_type": source.mime_type,
                **parser_info,
            },
            "subject": textbook_meta["subject"],
            "grade": textbook_meta["grade"],
            "textbook_version": textbook_meta["textbook_version"],
            "volume": textbook_meta["volume"],
            "lesson_title": selected["title"],
            "core_knowledge_points": [point["title"] for point in knowledge_points],
            "teaching_goal_summary": "认识 1-5 的数量意义，理解比大小、第几、分与合等基础数概念。",
            "key_points": ["1-5 的认识", "比大小", "第几", "分与合"],
            "difficulties": ["区分几个和第几个", "理解 4 和 5 的分与合"],
            "textbook_meta": textbook_meta,
            "knowledge_points": knowledge_points,
            "selected_knowledge_point_id": selected["id"],
            "selected_knowledge_point": {
                "knowledge_point_id": selected["id"],
                "title": selected["title"],
                "source_pages": {
                    "textbook_pages": f"{selected['page_start']}-{selected['page_end']}",
                    "pdf_pages": f"{selected['pdf_page_start']}-{selected['pdf_page_end']}",
                },
                "markdown_path": markdown_rel_path,
                "markdown": markdown,
            },
            "parse_artifacts": {
                "outline_path": outline_rel_path,
                "markdown_path": markdown_rel_path,
            },
        }

    def _load_fixture_markdown(self, selected: dict[str, Any]) -> str:
        if KNOWLEDGE_POINT_MARKDOWN_SOURCE.exists() and selected["id"] == "kp_001":
            return KNOWLEDGE_POINT_MARKDOWN_SOURCE.read_text(encoding="utf-8")
        return f"# 《{selected['title']}》教材内容整理\n\n待补充教材 Markdown。"


def _json_dumps(data: dict[str, Any]) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)
