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
FIXTURE_TEXTBOOK_PDF = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "textbook-parsing"
    / "renjiao-grade1-volume1-2024"
    / "1上-人教版小学数学课本（2024新版）.pdf"
)
TEXTBOOK_ID = "renjiao-grade1-volume1-2024"
TEXTBOOK_VERSION_ID = "renjiao-grade1-volume1-2024-v1"

RENJIAO_GRADE1_VOLUME1_META = {
    "subject": "math",
    "grade": "1",
    "textbook_version": "renjiao",
    "volume": "shang",
    "title": "人教版小学数学一年级上册",
}

RENJIAO_GRADE1_VOLUME1_CHAPTERS: list[dict[str, Any]] = [
    {
        "chapter_id": "ch_001",
        "title": "数学游戏",
        "page_start": 1,
        "page_end": 11,
        "pdf_page_start": 6,
        "pdf_page_end": 16,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_002",
        "title": "5以内数的认识和加、减法",
        "page_start": 12,
        "page_end": 33,
        "pdf_page_start": 17,
        "pdf_page_end": 38,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_003",
        "title": "6~10的认识和加、减法",
        "page_start": 34,
        "page_end": 66,
        "pdf_page_start": 39,
        "pdf_page_end": 71,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_004",
        "title": "认识立体图形",
        "page_start": 67,
        "page_end": 72,
        "pdf_page_start": 72,
        "pdf_page_end": 77,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_005",
        "title": "11~20的认识",
        "page_start": 73,
        "page_end": 87,
        "pdf_page_start": 78,
        "pdf_page_end": 92,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_006",
        "title": "20以内的进位加法",
        "page_start": 88,
        "page_end": 102,
        "pdf_page_start": 93,
        "pdf_page_end": 107,
        "source": "toc",
        "review_status": "needs_review",
    },
    {
        "chapter_id": "ch_007",
        "title": "复习与关联",
        "page_start": 103,
        "page_end": 113,
        "pdf_page_start": 108,
        "pdf_page_end": 118,
        "source": "toc",
        "review_status": "needs_review",
    },
]

RENJIAO_GRADE1_VOLUME1_LESSONS: list[dict[str, Any]] = [
    {
        "id": "kp_001",
        "title": "5以内数的认识",
        "unit": "5以内数的认识和加、减法",
        "page_start": 14,
        "page_end": 23,
        "pdf_page_start": 19,
        "pdf_page_end": 28,
        "keywords": ["1-5", "比大小", "第几", "分与合"],
        "lesson_scope": "认识 1-5 的数量意义，理解同样多、多、少、第几，以及 4 和 5 的分与合。",
    },
    {
        "id": "kp_002",
        "title": "1-5的加、减法",
        "unit": "5以内数的认识和加、减法",
        "page_start": 24,
        "page_end": 29,
        "pdf_page_start": 29,
        "pdf_page_end": 34,
        "keywords": ["加法", "减法", "1-5", "看图列式"],
        "lesson_scope": "从生活情境理解加法和减法含义，能用 1-5 的加、减法解决简单问题。",
    },
    {
        "id": "kp_003",
        "title": "0的认识和加、减法",
        "unit": "5以内数的认识和加、减法",
        "page_start": 30,
        "page_end": 30,
        "pdf_page_start": 35,
        "pdf_page_end": 35,
        "keywords": ["0", "0的认识", "有关0的加减法"],
        "lesson_scope": "认识 0 的意义，理解有关 0 的加、减法算式。",
    },
    {
        "id": "kp_004",
        "title": "整理和复习（5以内数）",
        "unit": "5以内数的认识和加、减法",
        "page_start": 31,
        "page_end": 33,
        "pdf_page_start": 36,
        "pdf_page_end": 38,
        "keywords": ["整理和复习", "分与合", "比大小", "加减法"],
        "lesson_scope": "整理 5 以内数的认识、比大小、分与合和加减法，形成知识图。",
    },
    {
        "id": "kp_005",
        "title": "6-10的认识",
        "unit": "6-10的认识和加、减法",
        "page_start": 36,
        "page_end": 43,
        "pdf_page_start": 41,
        "pdf_page_end": 48,
        "keywords": ["6-10", "比大小", "第几", "分与合"],
        "lesson_scope": "认识 6-10 的数量意义，继续学习比大小、第几和 6-10 的分与合。",
    },
    {
        "id": "kp_006",
        "title": "6-9的加、减法",
        "unit": "6-10的认识和加、减法",
        "page_start": 44,
        "page_end": 53,
        "pdf_page_start": 49,
        "pdf_page_end": 58,
        "keywords": ["6和7", "8和9", "加法", "减法", "解决问题"],
        "lesson_scope": "学习 6、7、8、9 的加、减法，能从情境中提出并解决简单问题。",
    },
    {
        "id": "kp_007",
        "title": "10的认识和加、减法",
        "unit": "6-10的认识和加、减法",
        "page_start": 54,
        "page_end": 57,
        "pdf_page_start": 59,
        "pdf_page_end": 62,
        "keywords": ["10", "10的组成", "10的加减法"],
        "lesson_scope": "认识 10，理解 10 的组成，并学习 10 的加、减法。",
    },
    {
        "id": "kp_008",
        "title": "连加、连减",
        "unit": "6-10的认识和加、减法",
        "page_start": 58,
        "page_end": 61,
        "pdf_page_start": 63,
        "pdf_page_end": 66,
        "keywords": ["连加", "连减", "情境列式"],
        "lesson_scope": "结合连续变化情境理解连加、连减的含义和计算顺序。",
    },
    {
        "id": "kp_009",
        "title": "整理和复习（6-10）",
        "unit": "6-10的认识和加、减法",
        "page_start": 62,
        "page_end": 65,
        "pdf_page_start": 67,
        "pdf_page_end": 70,
        "keywords": ["整理和复习", "6-10", "分与合", "加减法"],
        "lesson_scope": "整理 6-10 的认识、分与合、加减法和连加连减，形成单元知识图。",
    },
]


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

    def list_library(self) -> dict[str, Any]:
        return {
            "textbooks": [
                {
                    **dict(RENJIAO_GRADE1_VOLUME1_META),
                    "textbook_id": TEXTBOOK_ID,
                    "textbook_version_id": TEXTBOOK_VERSION_ID,
                    "source_pdf_path": str(FIXTURE_TEXTBOOK_PDF),
                    "knowledge_point_count": len(RENJIAO_GRADE1_VOLUME1_LESSONS),
                    "status": "indexed",
                    **renjiao_textbook_display_fields(
                        RENJIAO_GRADE1_VOLUME1_META["subject"],
                        RENJIAO_GRADE1_VOLUME1_META["grade"],
                        RENJIAO_GRADE1_VOLUME1_META["textbook_version"],
                        RENJIAO_GRADE1_VOLUME1_META["volume"],
                    ),
                }
            ]
        }

    def library_knowledge_points(self, textbook_id: str) -> dict[str, Any]:
        self._assert_fixture_textbook(textbook_id)
        return {
            "textbook": dict(RENJIAO_GRADE1_VOLUME1_META),
            "textbook_id": TEXTBOOK_ID,
            "textbook_version_id": TEXTBOOK_VERSION_ID,
            "chapters": renjiao_grade1_volume1_chapters(),
            "knowledge_points": [self._knowledge_point_summary(item) for item in RENJIAO_GRADE1_VOLUME1_LESSONS],
        }

    def library_asset_package(self, textbook_id: str, knowledge_point_id: str) -> dict[str, Any]:
        self._assert_fixture_textbook(textbook_id)
        selected = self._find_lesson(knowledge_point_id)
        return {
            **self._asset_package_for_selected(
                project_dir=None,
                source_pdf_path=FIXTURE_TEXTBOOK_PDF,
                source_pdf_rel_path=str(FIXTURE_TEXTBOOK_PDF),
                selected=selected,
                markdown=None,
                ensure_files=False,
            ),
            "textbook_id": TEXTBOOK_ID,
            "textbook_version_id": TEXTBOOK_VERSION_ID,
            "knowledge_point_id": selected["id"],
            "title": selected["title"],
        }

    def _parse_pdf_fixture(
        self,
        *,
        project_dir: Path,
        project: dict[str, Any],
        source: TextbookSource,
        selected_knowledge_point_id: str | None,
    ) -> dict[str, Any]:
        selected_id = selected_knowledge_point_id or RENJIAO_GRADE1_VOLUME1_LESSONS[0]["id"]
        knowledge_points = [self._knowledge_point_summary(item) for item in RENJIAO_GRADE1_VOLUME1_LESSONS]
        selected = self._find_lesson(selected_id)

        markdown = self._load_fixture_markdown(selected)
        asset_package = self._asset_package_for_selected(
            project_dir=project_dir,
            source_pdf_path=source.path,
            source_pdf_rel_path=source.rel_path,
            selected=selected,
            markdown=markdown,
            ensure_files=True,
        )
        markdown_rel_path = f"knowledge-points/{selected['id']}.md"
        legacy_markdown_path = project_dir / markdown_rel_path
        legacy_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_markdown_path.write_text(markdown, encoding="utf-8")

        outline_rel_path = "assets/textbook_parse/textbook_outline.json"
        outline_path = project_dir / outline_rel_path
        outline_path.parent.mkdir(parents=True, exist_ok=True)

        textbook_meta = dict(RENJIAO_GRADE1_VOLUME1_META)
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
                    "chapters": renjiao_grade1_volume1_chapters(),
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
            "core_knowledge_points": [selected["title"], *selected["keywords"]],
            "teaching_goal_summary": selected["lesson_scope"],
            "key_points": [selected["title"], *selected["keywords"]],
            "difficulties": self._difficulties_for_selected_lesson(selected),
            "textbook_meta": textbook_meta,
            "textbook_id": TEXTBOOK_ID,
            "textbook_version_id": TEXTBOOK_VERSION_ID,
            "chapters": renjiao_grade1_volume1_chapters(),
            "knowledge_points": knowledge_points,
            "selected_knowledge_point_id": selected["id"],
            "selected_knowledge_point": {
                "knowledge_point_id": selected["id"],
                "chapter_id": renjiao_chapter_id_for_lesson(selected),
                "title": selected["title"],
                "source_pages": {
                    "textbook_pages": f"{selected['page_start']}-{selected['page_end']}",
                    "pdf_pages": f"{selected['pdf_page_start']}-{selected['pdf_page_end']}",
                },
                "markdown_path": markdown_rel_path,
                "mineru_md_path": asset_package["mineru_md_path"],
                "slice_pdf_path": asset_package["slice_pdf_path"],
                "asset_package": asset_package,
                "markdown": markdown,
            },
            "parse_artifacts": {
                "outline_path": outline_rel_path,
                "markdown_path": markdown_rel_path,
                "mineru_md_path": asset_package["mineru_md_path"],
                "slice_pdf_path": asset_package["slice_pdf_path"],
            },
        }

    def _assert_fixture_textbook(self, textbook_id: str) -> None:
        if textbook_id != TEXTBOOK_ID:
            raise ValueError(f"Unknown textbook: {textbook_id}")

    def _find_lesson(self, knowledge_point_id: str) -> dict[str, Any]:
        selected = next((item for item in RENJIAO_GRADE1_VOLUME1_LESSONS if item["id"] == knowledge_point_id), None)
        if selected is None:
            raise ValueError(f"Unknown knowledge point: {knowledge_point_id}")
        return dict(selected)

    def _knowledge_point_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            **dict(item),
            "chapter_id": renjiao_chapter_id_for_lesson(item),
            "textbook_id": TEXTBOOK_ID,
            "textbook_version_id": TEXTBOOK_VERSION_ID,
            "parse_status": "parsed" if item["id"] == "kp_001" else "indexed",
            "review_status": "needs_review",
            "asset_package": self._asset_package_for_selected(
                project_dir=None,
                source_pdf_path=FIXTURE_TEXTBOOK_PDF,
                source_pdf_rel_path=str(FIXTURE_TEXTBOOK_PDF),
                selected=item,
                markdown=None,
                ensure_files=False,
            ),
        }

    def _asset_package_for_selected(
        self,
        *,
        project_dir: Path | None,
        source_pdf_path: Path,
        source_pdf_rel_path: str,
        selected: dict[str, Any],
        markdown: str | None,
        ensure_files: bool,
    ) -> dict[str, Any]:
        base_rel = f"knowledge-points/{selected['id']}"
        slice_rel = f"{base_rel}/source.pdf"
        mineru_rel = f"{base_rel}/mineru.md"
        markdown_body = markdown or self._load_fixture_markdown(selected)
        package = {
            "chapter_id": renjiao_chapter_id_for_lesson(selected),
            "source_pdf_path": source_pdf_rel_path,
            "slice_pdf_path": slice_rel,
            "mineru_md_path": mineru_rel,
            "markdown_path": mineru_rel,
            "textbook_pages": f"{selected['page_start']}-{selected['page_end']}",
            "pdf_pages": f"{selected['pdf_page_start']}-{selected['pdf_page_end']}",
            "parse_status": "parsed" if selected["id"] == "kp_001" else "indexed",
            "review_status": "needs_review",
            "checksum": f"sha256:{_sha256_text(markdown_body)}",
            "preview_images": [],
            "download_urls": {
                "slice_pdf": f"files/{slice_rel}",
                "mineru_md": f"files/{mineru_rel}",
            },
        }
        if ensure_files and project_dir is not None:
            mineru_path = project_dir / mineru_rel
            mineru_path.parent.mkdir(parents=True, exist_ok=True)
            mineru_path.write_text(markdown_body, encoding="utf-8")
            slice_path = project_dir / slice_rel
            self._write_pdf_slice(source_pdf_path, slice_path, int(selected["pdf_page_start"]), int(selected["pdf_page_end"]))
        return package

    def _write_pdf_slice(self, source_pdf_path: Path, target_path: Path, page_start: int, page_end: int) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(str(source_pdf_path))
        if page_start < 1 or page_end < page_start:
            raise ValueError(f"invalid pdf page range: {page_start}-{page_end}")
        if page_start > len(reader.pages):
            raise ValueError(f"pdf page range starts after document end: {page_start}>{len(reader.pages)}")

        writer = PdfWriter()
        start_index = page_start - 1
        end_index = min(page_end, len(reader.pages))
        for index in range(start_index, end_index):
            writer.add_page(reader.pages[index])
        if len(writer.pages) == 0:
            raise ValueError("empty pdf slice")
        with target_path.open("wb") as output:
            writer.write(output)

    def _load_fixture_markdown(self, selected: dict[str, Any]) -> str:
        if KNOWLEDGE_POINT_MARKDOWN_SOURCE.exists() and selected["id"] == "kp_001":
            return KNOWLEDGE_POINT_MARKDOWN_SOURCE.read_text(encoding="utf-8")
        keywords = "、".join(selected.get("keywords", [])) or "待补充"
        page_range = f"{selected['page_start']}-{selected['page_end']}"
        pdf_range = f"{selected['pdf_page_start']}-{selected['pdf_page_end']}"
        mid_start = selected["page_start"] + 1
        mid_end = max(mid_start, selected["page_end"] - 1)
        return (
            f"# 《{selected['title']}》图文教材结构化整理\n\n"
            f"来源：人教版小学数学一年级上册，单元“{selected['unit']}”，教材页码 {page_range}；PDF 页码 {pdf_range}。\n"
            "处理方式：按当前知识点页码范围裁剪页段 PDF，使用本地 fixture 结构化模板整理教材图文要素。\n\n"
            "## 一、课节范围判断\n\n"
            f"本资产包只覆盖当前知识点“{selected['title']}”，教材页码 {page_range}，PDF 页码 {pdf_range}。"
            f"课节范围为：{selected['lesson_scope']}\n\n"
            "## 二、核心知识点\n\n"
            f"- 课题：{selected['title']}。\n"
            f"- 所属单元：{selected['unit']}。\n"
            f"- 核心关键词：{keywords}。\n"
            "- 学生需要把教材图、实物数量、算式或数学表达连接起来，形成可操作的课堂活动。\n\n"
            "## 三、图片、物体、道具清单\n\n"
            "- 教材页段中的情境图、练习图、数字或算式卡片。\n"
            "- 可用于课堂复现的计数器、小棒、方块、贴纸、动物或生活物图片卡。\n"
            "- 板书与投影需要保留教材页中的数量关系、操作步骤和关键表达。\n\n"
            "## 四、逐页结构化内容\n\n"
            f"- 教材页 {selected['page_start']}：进入“{selected['title']}”主题，观察教材情境并提取数量关系。\n"
            f"- 教材页 {mid_start}-{mid_end}：围绕 {keywords} 展开例题、操作和练习。\n"
            f"- 教材页 {selected['page_end']}：通过练习或整理活动回收本知识点的关键表达。\n\n"
            "## 五、可转成教案的课堂流程\n\n"
            "1. 观察教材情境图，提出本节要解决的数学问题。\n"
            "2. 用实物、图形或算式还原教材中的数量关系。\n"
            "3. 组织学生表达自己的观察、操作和计算过程。\n"
            "4. 回到教材练习，完成同类题并总结方法。\n\n"
            "## 六、可直接形成的教学目标\n\n"
            f"- 理解“{selected['title']}”涉及的核心概念和表达方式。\n"
            "- 能借助教材图文和课堂道具说明数量关系。\n"
            "- 能把教材例题方法迁移到同类练习。\n\n"
            "## 七、建议板书\n\n"
            f"{selected['title']}\n\n"
            f"- 关键词：{keywords}\n"
            "- 图文观察 -> 操作表示 -> 数学表达 -> 练习应用\n\n"
            "## 八、输出与核验说明\n\n"
            "本 Markdown 来自当前知识点页段资产包，不是历史教案替代品。"
            "人工确认前 review_status 保持 needs_review；确认时必须同时核验页段 PDF 和本结构化内容。\n"
        )

    def _difficulties_for_selected_lesson(self, selected: dict[str, Any]) -> list[str]:
        difficulty_map = {
            "kp_001": ["区分几个和第几个", "理解 4 和 5 的分与合"],
            "kp_002": ["理解加法和减法的实际含义", "根据情境正确列式"],
            "kp_003": ["理解 0 表示一个也没有", "掌握含 0 的加减法"],
            "kp_004": ["把分散知识整理成知识图", "区分数量、比较和运算关系"],
            "kp_005": ["把 6-10 的数量、顺序和分与合建立联系", "继续区分几个和第几个"],
            "kp_006": ["从图文情境中提取数量关系", "选择合适的加法或减法算式"],
            "kp_007": ["理解 10 的组成", "建立 10 的加减法互逆关系"],
            "kp_008": ["理解连续变化情境", "掌握连加连减的计算顺序"],
            "kp_009": ["综合整理 6-10 的知识结构", "把分与合、加减法和解决问题联系起来"],
        }
        return difficulty_map.get(selected["id"], ["请结合 Markdown 预览核对教学难点"])


def _json_dumps(data: dict[str, Any]) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)


def renjiao_grade1_volume1_chapters() -> list[dict[str, Any]]:
    return [dict(chapter) for chapter in RENJIAO_GRADE1_VOLUME1_CHAPTERS]


def renjiao_chapter_id_for_lesson(lesson: dict[str, Any]) -> str | None:
    page_start = lesson.get("page_start")
    if page_start is None:
        return None
    for chapter in RENJIAO_GRADE1_VOLUME1_CHAPTERS:
        if int(chapter["page_start"]) <= int(page_start) <= int(chapter["page_end"]):
            return str(chapter["chapter_id"])
    return None


def renjiao_textbook_display_fields(subject: str, grade: str, textbook_version: str, volume: str) -> dict[str, str]:
    publisher = {"renjiao": "人教版"}.get(textbook_version, textbook_version)
    subject_label = {"math": "小学数学"}.get(subject, subject)
    grade_label = {"1": "一年级"}.get(grade, grade)
    volume_label = {"shang": "上册", "xia": "下册"}.get(volume, volume)
    return {
        "publisher": publisher,
        "subject_label": subject_label,
        "grade_label": grade_label,
        "volume_label": volume_label,
        "display_name": f"{publisher} / {subject_label} / {grade_label} / {volume_label}",
    }


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
