from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LessonPlanLibraryStore:
    SUPPORTED_UPLOAD_SUFFIXES = {".md", ".markdown", ".txt", ".pdf", ".docx", ".doc"}

    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self.db_path = storage_root / "lesson_plan_library.db"
        self.uploads_root = storage_root / "lesson_plan_library_uploads"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.uploads_root.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            self.init_db(conn)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS lesson_plans (
              lesson_plan_id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              markdown TEXT NOT NULL,
              source_project_id TEXT NOT NULL,
              source_textbook_id TEXT,
              source_textbook_version_id TEXT,
              source_knowledge_point_id TEXT,
              source_slice_pdf_path TEXT,
              source_mineru_md_path TEXT,
              metadata_json TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_lesson_plans_source
              ON lesson_plans(source_textbook_id, source_knowledge_point_id);
            """
        )
        self._ensure_columns(conn)
        conn.commit()

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"] if isinstance(row, sqlite3.Row) else row[1])
            for row in conn.execute("PRAGMA table_info(lesson_plans)").fetchall()
        }
        for column in ["source_type", "source_filename", "source_file_path", "extract_status"]:
            if column not in existing:
                conn.execute(f"ALTER TABLE lesson_plans ADD COLUMN {column} TEXT")

    def import_from_project(self, project: dict[str, Any], content: dict[str, Any], *, created_by: str = "system") -> dict[str, Any]:
        markdown = str(content.get("lesson_plan_markdown") or "").strip()
        if not markdown:
            raise ValueError("当前项目 lesson_plan 不包含可入库 Markdown")
        metadata = {
            "source_label": "项目导入",
            "project_name": project.get("name"),
            "textbook_anchor": content.get("textbook_anchor"),
            "reference_lesson_plan_id": content.get("reference_lesson_plan_id"),
            "created_by_label": created_by,
            "markdown_excerpt": markdown[:240],
        }
        return self.create_from_markdown(
            markdown,
            source_project_id=project["project_id"],
            source_textbook_id=content.get("source_textbook_id"),
            source_textbook_version_id=content.get("source_textbook_version_id"),
            source_knowledge_point_id=content.get("source_knowledge_point_id"),
            source_slice_pdf_path=content.get("source_slice_pdf_path"),
            source_mineru_md_path=content.get("source_mineru_md_path"),
            metadata=metadata,
            created_by=created_by,
        )

    def create_from_markdown(
        self,
        markdown: str,
        *,
        source_project_id: str | None = None,
        source_textbook_id: str | None = None,
        source_textbook_version_id: str | None = None,
        source_knowledge_point_id: str | None = None,
        source_slice_pdf_path: str | None = None,
        source_mineru_md_path: str | None = None,
        source_type: str | None = None,
        source_filename: str | None = None,
        source_file_path: str | None = None,
        extract_status: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str = "system",
    ) -> dict[str, Any]:
        markdown = markdown.strip()
        if not markdown:
            raise ValueError("教案 Markdown 不能为空")
        lesson_plan_id = f"lp_{uuid.uuid4().hex[:12]}"
        title = _title_from_markdown(markdown) or "未命名教案"
        now = now_iso()
        merged_metadata = {
            "source_label": "管理员上传" if source_project_id is None else "项目导入",
            "created_by_label": created_by,
            "markdown_excerpt": markdown[:240],
            **(metadata or {}),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO lesson_plans
                (lesson_plan_id, title, markdown, source_project_id, source_textbook_id,
                 source_textbook_version_id, source_knowledge_point_id, source_slice_pdf_path,
                 source_mineru_md_path, metadata_json, created_by, created_at, updated_at,
                 source_type, source_filename, source_file_path, extract_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson_plan_id,
                    title,
                    markdown,
                    source_project_id or "",
                    source_textbook_id,
                    source_textbook_version_id,
                    source_knowledge_point_id,
                    source_slice_pdf_path,
                    source_mineru_md_path,
                    json.dumps(merged_metadata, ensure_ascii=False),
                    created_by,
                    now,
                    now,
                    source_type or ("uploaded_file" if source_project_id is None else "project"),
                    source_filename,
                    source_file_path,
                    extract_status,
                ),
            )
            conn.commit()
            return self.get(lesson_plan_id)

    def upload_file(self, file: UploadFile, *, created_by: str = "user") -> dict[str, Any]:
        source_filename = Path(file.filename or "lesson-plan.md").name
        suffix = Path(source_filename).suffix.lower()
        if suffix not in self.SUPPORTED_UPLOAD_SUFFIXES:
            raise ValueError("仅支持 .md/.markdown/.txt/.pdf/.docx/.doc 教案文件")
        lesson_plan_id = f"lp_{uuid.uuid4().hex[:12]}"
        target = self.uploads_root / f"{lesson_plan_id}{suffix or '.txt'}"
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        markdown, extract_status, extraction = self._extract_markdown(target, source_filename, suffix)
        return self.create_from_markdown(
            markdown,
            source_project_id="uploaded_file",
            source_type="uploaded_file",
            source_filename=source_filename,
            source_file_path=str(target.relative_to(self.storage_root)),
            extract_status=extract_status,
            metadata={
                "source_label": "教案文件上传",
                "source_filename": source_filename,
                "content_type": file.content_type,
                "text_extraction": extraction,
            },
            created_by=created_by,
        )

    def _extract_markdown(self, path: Path, source_filename: str, suffix: str) -> tuple[str, str, dict[str, Any]]:
        if suffix in {".md", ".markdown", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                raise ValueError("教案文件内容为空")
            return text, "text_extracted", {"method": "plain_text", "trusted_text": True}
        markdown = (
            f"# {Path(source_filename).stem}\n\n"
            f"> 已保存原始教案文件：{source_filename}。\n\n"
            "当前版本未执行 OCR，也未声称完成 PDF/Word 正文解析。请在教案步骤中补充或核对正文后再继续。"
        )
        return markdown, "placeholder", {"method": "placeholder", "trusted_text": False}

    def list(self, *, textbook_id: str | None = None, knowledge_point_id: str | None = None) -> dict[str, Any]:
        query = "SELECT * FROM lesson_plans WHERE 1=1"
        params: list[Any] = []
        if textbook_id:
            query += " AND source_textbook_id = ?"
            params.append(textbook_id)
        if knowledge_point_id:
            query += " AND source_knowledge_point_id = ?"
            params.append(knowledge_point_id)
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return {"lesson_plans": [self._summary(dict(row)) for row in rows]}

    def get(self, lesson_plan_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM lesson_plans WHERE lesson_plan_id = ?", (lesson_plan_id,)).fetchone()
            if row is None:
                raise KeyError(lesson_plan_id)
            return self._payload(dict(row))

    def update_source_metadata(
        self,
        lesson_plan_id: str,
        *,
        source_textbook_id: str | None = None,
        source_textbook_version_id: str | None = None,
        source_knowledge_point_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT metadata_json FROM lesson_plans WHERE lesson_plan_id = ?", (lesson_plan_id,)).fetchone()
            if row is None:
                raise KeyError(lesson_plan_id)
            merged_metadata = {**json.loads(row["metadata_json"] or "{}"), **(metadata or {})}
            conn.execute(
                """
                UPDATE lesson_plans
                SET source_textbook_id = ?, source_textbook_version_id = ?,
                    source_knowledge_point_id = ?, metadata_json = ?, updated_at = ?
                WHERE lesson_plan_id = ?
                """,
                (
                    source_textbook_id,
                    source_textbook_version_id,
                    source_knowledge_point_id,
                    json.dumps(merged_metadata, ensure_ascii=False),
                    now_iso(),
                    lesson_plan_id,
                ),
            )
            conn.commit()
        return self.get(lesson_plan_id)

    def _summary(self, row: dict[str, Any]) -> dict[str, Any]:
        source_type = row.get("source_type") or ("uploaded_file" if row.get("source_project_id") == "uploaded_file" else "project")
        source_project_id = row["source_project_id"] or None
        if source_type == "uploaded_file":
            source_project_id = None
        return {
            "lesson_plan_id": row["lesson_plan_id"],
            "title": row["title"],
            "source_project_id": source_project_id,
            "source_textbook_id": row.get("source_textbook_id"),
            "source_textbook_version_id": row.get("source_textbook_version_id"),
            "source_knowledge_point_id": row.get("source_knowledge_point_id"),
            "source_type": source_type,
            "source_filename": row.get("source_filename"),
            "extract_status": row.get("extract_status"),
            "metadata": json.loads(row.get("metadata_json") or "{}"),
            "updated_at": row["updated_at"],
            "created_at": row["created_at"],
        }

    def _payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            **self._summary(row),
            "markdown": row["markdown"],
            "source_slice_pdf_path": row.get("source_slice_pdf_path"),
            "source_mineru_md_path": row.get("source_mineru_md_path"),
            "source_file_path": row.get("source_file_path"),
            "created_by": row["created_by"],
        }


def _title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""
