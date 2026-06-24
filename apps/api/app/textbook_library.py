from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .textbook_parser import (
    FIXTURE_TEXTBOOK_PDF,
    RENJIAO_GRADE1_VOLUME1_LESSONS,
    RENJIAO_GRADE1_VOLUME1_META,
    TEXTBOOK_ID,
    TEXTBOOK_VERSION_ID,
    TextbookParser,
    renjiao_chapter_id_for_lesson,
    renjiao_grade1_volume1_chapters,
    renjiao_textbook_display_fields,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TextbookLibraryStore:
    def __init__(self, storage_root: Path, parser: TextbookParser | None = None):
        self.storage_root = storage_root
        self.db_path = storage_root / "textbook_library.db"
        self.files_root = storage_root / "textbook-library"
        self.uploads_root = self.files_root / "uploads"
        self.assets_root = self.files_root / "assets"
        self.parser = parser or TextbookParser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.uploads_root.mkdir(parents=True, exist_ok=True)
        self.assets_root.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            self.init_db(conn)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS textbooks (
              textbook_id TEXT PRIMARY KEY,
              subject TEXT NOT NULL,
              grade TEXT NOT NULL,
              textbook_version TEXT NOT NULL,
              volume TEXT NOT NULL,
              title TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS textbook_versions (
              textbook_version_id TEXT PRIMARY KEY,
              textbook_id TEXT NOT NULL,
              source_pdf_path TEXT NOT NULL,
              source_pdf_sha256 TEXT,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id)
            );
            CREATE TABLE IF NOT EXISTS knowledge_points (
              textbook_id TEXT NOT NULL,
              textbook_version_id TEXT NOT NULL,
              knowledge_point_id TEXT NOT NULL,
              title TEXT NOT NULL,
              unit TEXT,
              page_start INTEGER,
              page_end INTEGER,
              pdf_page_start INTEGER,
              pdf_page_end INTEGER,
              keywords_json TEXT NOT NULL,
              lesson_scope TEXT,
              parse_status TEXT NOT NULL,
              review_status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              PRIMARY KEY (textbook_version_id, knowledge_point_id)
            );
            CREATE TABLE IF NOT EXISTS textbook_asset_packages (
              asset_id TEXT PRIMARY KEY,
              textbook_id TEXT NOT NULL,
              textbook_version_id TEXT NOT NULL,
              knowledge_point_id TEXT NOT NULL,
              source_pdf_path TEXT NOT NULL,
              slice_pdf_path TEXT NOT NULL,
              mineru_md_path TEXT NOT NULL,
              markdown_path TEXT NOT NULL,
              textbook_pages TEXT NOT NULL,
              pdf_pages TEXT NOT NULL,
              parse_status TEXT NOT NULL,
              review_status TEXT NOT NULL,
              mineru_job_id TEXT,
              checksum TEXT,
              diagnostics_json TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              UNIQUE(textbook_version_id, knowledge_point_id)
            );
            CREATE TABLE IF NOT EXISTS textbook_parse_jobs (
              job_id TEXT PRIMARY KEY,
              textbook_id TEXT NOT NULL,
              textbook_version_id TEXT NOT NULL,
              knowledge_point_id TEXT,
              job_type TEXT NOT NULL,
              status TEXT NOT NULL,
              provider TEXT NOT NULL,
              error_message TEXT,
              result_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        _ensure_column(conn, "textbook_asset_packages", "diagnostics_json", "TEXT")
        conn.commit()

    def ensure_seeded(self) -> None:
        fixture_hash = _sha256_file(FIXTURE_TEXTBOOK_PDF) if FIXTURE_TEXTBOOK_PDF.exists() else None
        with self.connect() as conn:
            now = now_iso()
            conn.execute(
                """
                INSERT OR IGNORE INTO textbooks
                (textbook_id, subject, grade, textbook_version, volume, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'ready', ?, ?)
                """,
                (
                    TEXTBOOK_ID,
                    RENJIAO_GRADE1_VOLUME1_META["subject"],
                    RENJIAO_GRADE1_VOLUME1_META["grade"],
                    RENJIAO_GRADE1_VOLUME1_META["textbook_version"],
                    RENJIAO_GRADE1_VOLUME1_META["volume"],
                    RENJIAO_GRADE1_VOLUME1_META["title"],
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO textbook_versions
                (textbook_version_id, textbook_id, source_pdf_path, source_pdf_sha256, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'ready', ?, ?)
                """,
                (TEXTBOOK_VERSION_ID, TEXTBOOK_ID, str(FIXTURE_TEXTBOOK_PDF), fixture_hash, now, now),
            )
            for lesson in RENJIAO_GRADE1_VOLUME1_LESSONS:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO knowledge_points
                    (textbook_id, textbook_version_id, knowledge_point_id, title, unit, page_start, page_end,
                     pdf_page_start, pdf_page_end, keywords_json, lesson_scope, parse_status, review_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        TEXTBOOK_ID,
                        TEXTBOOK_VERSION_ID,
                        lesson["id"],
                        lesson["title"],
                        lesson.get("unit"),
                        lesson.get("page_start"),
                        lesson.get("page_end"),
                        lesson.get("pdf_page_start"),
                        lesson.get("pdf_page_end"),
                        json.dumps(lesson.get("keywords") or [], ensure_ascii=False),
                        lesson.get("lesson_scope"),
                        "parsed" if lesson["id"] == "kp_001" else "indexed",
                        "needs_review",
                        now,
                        now,
                    ),
                )
            conn.commit()

    def list_library(self) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT t.*, v.textbook_version_id, v.source_pdf_path, COUNT(k.knowledge_point_id) AS knowledge_point_count
                FROM textbooks t
                JOIN textbook_versions v ON v.textbook_id = t.textbook_id
                LEFT JOIN knowledge_points k ON k.textbook_version_id = v.textbook_version_id
                GROUP BY t.textbook_id, v.textbook_version_id
                ORDER BY t.created_at
                """
            ).fetchall()
            return {
                "textbooks": [
                    {
                        "textbook_id": row["textbook_id"],
                        "textbook_version_id": row["textbook_version_id"],
                        "subject": row["subject"],
                        "grade": row["grade"],
                        "textbook_version": row["textbook_version"],
                        "volume": row["volume"],
                        "title": row["title"],
                        "source_pdf_path": row["source_pdf_path"],
                        "knowledge_point_count": row["knowledge_point_count"],
                        "status": "indexed" if row["textbook_id"] == TEXTBOOK_ID else row["status"],
                        "publisher": "人教版" if row["textbook_version"] == "renjiao" else row["textbook_version"],
                        "version": row["textbook_version"],
                        "toc_template_id": "renjiao_grade1_volume1_2024_toc" if row["textbook_id"] == TEXTBOOK_ID else "manual_toc_pending",
                        "page_mapping_strategy": "renjiao_grade1_volume1_offset_5" if row["textbook_id"] == TEXTBOOK_ID else "manual_review_required",
                        "parser_profile": "jiaocaiTojiaoan_mineru_v1" if row["textbook_id"] == TEXTBOOK_ID else "unverified_manual_profile",
                        "verification_status": "verified" if row["textbook_id"] == TEXTBOOK_ID else "unverified",
                        "review_status": "approved" if row["textbook_id"] == TEXTBOOK_ID else "needs_review",
                        **renjiao_textbook_display_fields(
                            row["subject"],
                            row["grade"],
                            row["textbook_version"],
                            row["volume"],
                        ),
                    }
                    for row in rows
                ]
            }

    def knowledge_points(self, textbook_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            textbook, version = self._textbook_and_version(conn, textbook_id)
            rows = conn.execute(
                """
                SELECT * FROM knowledge_points
                WHERE textbook_version_id = ?
                ORDER BY CAST(REPLACE(knowledge_point_id, 'kp_', '') AS INTEGER), knowledge_point_id
                """,
                (version["textbook_version_id"],),
            ).fetchall()
            return {
                "textbook": self._textbook_meta(textbook, version),
                "textbook_id": textbook_id,
                "textbook_version_id": version["textbook_version_id"],
                "chapters": renjiao_grade1_volume1_chapters(),
                "knowledge_points": [self._knowledge_point_payload(dict(row), version) for row in rows],
            }

    def asset_package(self, textbook_id: str, knowledge_point_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            textbook, version = self._textbook_and_version(conn, textbook_id)
            kp = self._knowledge_point(conn, version["textbook_version_id"], knowledge_point_id)
            asset = self._asset_for(conn, version["textbook_version_id"], knowledge_point_id)
            if asset is None:
                return self._asset_payload_from_kp(textbook, version, kp, asset=None)
            return self._asset_payload_from_kp(textbook, version, kp, asset=asset)

    def upload_textbook(self, file: UploadFile) -> dict[str, Any]:
        safe_name = Path(file.filename or "textbook.pdf").name
        upload_id = uuid.uuid4().hex[:12]
        target = self.uploads_root / f"{upload_id}-{safe_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        digest = _sha256_file(target)

        with self.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM textbook_versions WHERE source_pdf_sha256 = ? ORDER BY created_at LIMIT 1",
                (digest,),
            ).fetchone()
            if existing:
                version = dict(existing)
                textbook = dict(conn.execute("SELECT * FROM textbooks WHERE textbook_id = ?", (version["textbook_id"],)).fetchone())
            else:
                textbook_id = _uploaded_textbook_id(digest)
                version_id = f"{textbook_id}-v1"
                textbook = {
                    "textbook_id": textbook_id,
                    "subject": "math",
                    "grade": "1",
                    "textbook_version": "renjiao",
                    "volume": "shang",
                    "title": Path(safe_name).stem,
                    "status": "needs_review",
                }
                now = now_iso()
                conn.execute(
                    """
                    INSERT OR IGNORE INTO textbooks
                    (textbook_id, subject, grade, textbook_version, volume, title, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        textbook_id,
                        textbook["subject"],
                        textbook["grade"],
                        textbook["textbook_version"],
                        textbook["volume"],
                        textbook["title"],
                        textbook["status"],
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO textbook_versions
                    (textbook_version_id, textbook_id, source_pdf_path, source_pdf_sha256, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'uploaded', ?, ?)
                    """,
                    (version_id, textbook_id, str(target), digest, now, now),
                )
                version = {
                    "textbook_version_id": version_id,
                    "textbook_id": textbook_id,
                    "source_pdf_path": str(target),
                    "source_pdf_sha256": digest,
                    "status": "uploaded",
                }
                self._seed_fixture_lessons_for_uploaded(conn, textbook_id, version_id)

            job = self._create_job(
                conn,
                textbook["textbook_id"],
                version["textbook_version_id"],
                None,
                "textbook_index",
                "uploaded",
                {"filename": safe_name, "source_pdf_sha256": digest},
            )
            conn.commit()
            self._complete_index_job(job["job_id"])
            return {
                "textbook_id": textbook["textbook_id"],
                "textbook_version_id": version["textbook_version_id"],
                "job_id": job["job_id"],
                "parse_status": "uploaded",
                "filename": safe_name,
            }

    def job(self, job_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM textbook_parse_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            return self._job_payload(dict(row))

    def split_assets(self, textbook_id: str, knowledge_point_ids: list[str] | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            textbook, version = self._textbook_and_version(conn, textbook_id)
            kps = self._resolve_knowledge_points(conn, version["textbook_version_id"], knowledge_point_ids)
            job = self._create_job(
                conn,
                textbook_id,
                version["textbook_version_id"],
                None,
                "textbook_split",
                "splitting",
                {"knowledge_point_ids": [kp["knowledge_point_id"] for kp in kps]},
            )
            conn.commit()

        assets: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for kp in kps:
            try:
                assets.append(self._split_asset(textbook, version, kp, job["job_id"]))
            except Exception as exc:
                failures.append(
                    {
                        "knowledge_point_id": kp["knowledge_point_id"],
                        "message": str(exc),
                    }
                )

        status = "split_ready" if not failures else ("failed" if not assets else "partial")
        result = self._batch_result(job, status, assets, failures)
        self._finish_job(job["job_id"], status, result, failures[0]["message"] if failures and not assets else None)
        return result

    def extract_assets(self, textbook_id: str, knowledge_point_ids: list[str] | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            textbook, version = self._textbook_and_version(conn, textbook_id)
            kps = self._resolve_knowledge_points(conn, version["textbook_version_id"], knowledge_point_ids)
            job = self._create_job(
                conn,
                textbook_id,
                version["textbook_version_id"],
                None,
                "mineru_extract_batch",
                "extracting",
                {"knowledge_point_ids": [kp["knowledge_point_id"] for kp in kps]},
            )
            conn.commit()

        assets: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for kp in kps:
            try:
                assets.append(self.extract_asset(textbook_id, kp["knowledge_point_id"]))
            except TextbookAssetExtractionError as exc:
                failures.append(
                    {
                        "knowledge_point_id": kp["knowledge_point_id"],
                        "message": str(exc),
                        "asset": exc.asset,
                    }
                )
            except Exception as exc:
                failures.append(
                    {
                        "knowledge_point_id": kp["knowledge_point_id"],
                        "message": str(exc),
                    }
                )

        status = "needs_review" if not failures else ("failed" if not assets else "partial")
        result = self._batch_result(job, status, assets, failures)
        self._finish_job(job["job_id"], status, result, failures[0]["message"] if failures and not assets else None)
        return result

    def extract_asset(self, textbook_id: str, knowledge_point_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            textbook, version = self._textbook_and_version(conn, textbook_id)
            kp = self._knowledge_point(conn, version["textbook_version_id"], knowledge_point_id)
            job = self._create_job(conn, textbook_id, version["textbook_version_id"], knowledge_point_id, "mineru_extract", "extracting", {})
            conn.commit()
        try:
            source_pdf = Path(version["source_pdf_path"])
            asset_dir = self.assets_root / version["textbook_version_id"] / "knowledge-points" / knowledge_point_id
            slice_path = asset_dir / "source.pdf"
            md_path = asset_dir / "mineru.md"
            selected = self._kp_as_lesson(kp)
            self.parser._write_pdf_slice(source_pdf, slice_path, int(kp["pdf_page_start"]), int(kp["pdf_page_end"]))
            markdown = self.parser._load_fixture_markdown(selected)
            md_path.write_text(markdown, encoding="utf-8")
            checksum = f"sha256:{hashlib.sha256(markdown.encode('utf-8')).hexdigest()}"
            with self.connect() as conn:
                now = now_iso()
                existing = conn.execute(
                    "SELECT asset_id FROM textbook_asset_packages WHERE textbook_version_id = ? AND knowledge_point_id = ?",
                    (version["textbook_version_id"], knowledge_point_id),
                ).fetchone()
                asset_id = existing["asset_id"] if existing else f"ta_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO textbook_asset_packages
                    (asset_id, textbook_id, textbook_version_id, knowledge_point_id, source_pdf_path, slice_pdf_path,
                     mineru_md_path, markdown_path, textbook_pages, pdf_pages, parse_status, review_status,
                     mineru_job_id, checksum, diagnostics_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'needs_review', 'needs_review', ?, ?, NULL, ?, ?)
                    ON CONFLICT(textbook_version_id, knowledge_point_id) DO UPDATE SET
                      source_pdf_path=excluded.source_pdf_path,
                      slice_pdf_path=excluded.slice_pdf_path,
                      mineru_md_path=excluded.mineru_md_path,
                      markdown_path=excluded.markdown_path,
                      textbook_pages=excluded.textbook_pages,
                      pdf_pages=excluded.pdf_pages,
                      parse_status='needs_review',
                      review_status='needs_review',
                      mineru_job_id=excluded.mineru_job_id,
                      checksum=excluded.checksum,
                      diagnostics_json=NULL,
                      updated_at=excluded.updated_at
                    """,
                    (
                        asset_id,
                        textbook_id,
                        version["textbook_version_id"],
                        knowledge_point_id,
                        str(source_pdf),
                        str(slice_path),
                        str(md_path),
                        str(md_path),
                        f"{kp['page_start']}-{kp['page_end']}",
                        f"{kp['pdf_page_start']}-{kp['pdf_page_end']}",
                        job["job_id"],
                        checksum,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """
                    UPDATE textbook_parse_jobs
                    SET status='needs_review', result_json=?, updated_at=?
                    WHERE job_id=?
                    """,
                    (json.dumps({"asset_id": asset_id}, ensure_ascii=False), now, job["job_id"]),
                )
                conn.commit()
                asset = self._asset_for(conn, version["textbook_version_id"], knowledge_point_id)
                return self._asset_payload_from_kp(textbook, version, kp, asset=asset)
        except Exception as exc:
            diagnostics = {
                "stage": "pdf_slice",
                "message": str(exc),
                "source_pdf_path": str(version["source_pdf_path"]),
                "textbook_pages": f"{kp['page_start']}-{kp['page_end']}",
                "pdf_pages": f"{kp['pdf_page_start']}-{kp['pdf_page_end']}",
            }
            with self.connect() as conn:
                now = now_iso()
                existing = conn.execute(
                    "SELECT asset_id FROM textbook_asset_packages WHERE textbook_version_id = ? AND knowledge_point_id = ?",
                    (version["textbook_version_id"], knowledge_point_id),
                ).fetchone()
                asset_id = existing["asset_id"] if existing else f"ta_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO textbook_asset_packages
                    (asset_id, textbook_id, textbook_version_id, knowledge_point_id, source_pdf_path, slice_pdf_path,
                     mineru_md_path, markdown_path, textbook_pages, pdf_pages, parse_status, review_status,
                     mineru_job_id, checksum, diagnostics_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'failed', 'needs_review', ?, NULL, ?, ?, ?)
                    ON CONFLICT(textbook_version_id, knowledge_point_id) DO UPDATE SET
                      source_pdf_path=excluded.source_pdf_path,
                      slice_pdf_path=excluded.slice_pdf_path,
                      mineru_md_path=excluded.mineru_md_path,
                      markdown_path=excluded.markdown_path,
                      textbook_pages=excluded.textbook_pages,
                      pdf_pages=excluded.pdf_pages,
                      parse_status='failed',
                      review_status='needs_review',
                      mineru_job_id=excluded.mineru_job_id,
                      checksum=NULL,
                      diagnostics_json=excluded.diagnostics_json,
                      updated_at=excluded.updated_at
                    """,
                    (
                        asset_id,
                        textbook_id,
                        version["textbook_version_id"],
                        knowledge_point_id,
                        str(source_pdf),
                        str(slice_path),
                        str(md_path),
                        str(md_path),
                        f"{kp['page_start']}-{kp['page_end']}",
                        f"{kp['pdf_page_start']}-{kp['pdf_page_end']}",
                        job["job_id"],
                        json.dumps(diagnostics, ensure_ascii=False),
                        now,
                        now,
                    ),
                )
                conn.execute(
                    "UPDATE textbook_parse_jobs SET status='failed', error_message=?, updated_at=? WHERE job_id=?",
                    (str(exc), now, job["job_id"]),
                )
                conn.commit()
                asset = self._asset_for(conn, version["textbook_version_id"], knowledge_point_id)
                payload = self._asset_payload_from_kp(textbook, version, kp, asset=asset)
            raise TextbookAssetExtractionError(payload) from exc

    def confirm_asset(self, asset_id: str, reviewer: str | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM textbook_asset_packages WHERE asset_id = ?", (asset_id,)).fetchone()
            if row is None:
                raise KeyError(asset_id)
            textbook = dict(conn.execute("SELECT * FROM textbooks WHERE textbook_id = ?", (row["textbook_id"],)).fetchone())
            version = dict(conn.execute("SELECT * FROM textbook_versions WHERE textbook_version_id = ?", (row["textbook_version_id"],)).fetchone())
            kp = self._knowledge_point(conn, row["textbook_version_id"], row["knowledge_point_id"])
            trust_errors = self._asset_trust_errors(dict(row), kp)
            if trust_errors:
                payload = self._asset_payload_from_kp(textbook, version, kp, asset=dict(row))
                payload["trust_errors"] = trust_errors
                raise TextbookAssetNotTrustedError(payload)
            now = now_iso()
            conn.execute(
                """
                UPDATE textbook_asset_packages
                SET parse_status='approved', review_status='approved', updated_at=?
                WHERE asset_id=?
                """,
                (now, asset_id),
            )
            if row["mineru_job_id"]:
                conn.execute(
                    "UPDATE textbook_parse_jobs SET status='approved', updated_at=? WHERE job_id=?",
                    (now, row["mineru_job_id"]),
            )
            conn.commit()
            updated = dict(conn.execute("SELECT * FROM textbook_asset_packages WHERE asset_id = ?", (asset_id,)).fetchone())
            payload = self._asset_payload_from_kp(textbook, version, kp, asset=updated)
            payload["reviewer"] = reviewer
            return payload

    def source_pdf_path(self, textbook_id: str) -> Path:
        with self.connect() as conn:
            _textbook, version = self._textbook_and_version(conn, textbook_id)
            return Path(version["source_pdf_path"])

    def _seed_fixture_lessons_for_uploaded(self, conn: sqlite3.Connection, textbook_id: str, version_id: str) -> None:
        now = now_iso()
        for lesson in RENJIAO_GRADE1_VOLUME1_LESSONS:
            conn.execute(
                """
                INSERT OR IGNORE INTO knowledge_points
                (textbook_id, textbook_version_id, knowledge_point_id, title, unit, page_start, page_end,
                 pdf_page_start, pdf_page_end, keywords_json, lesson_scope, parse_status, review_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'indexed', 'needs_review', ?, ?)
                """,
                (
                    textbook_id,
                    version_id,
                    lesson["id"],
                    lesson["title"],
                    lesson.get("unit"),
                    lesson.get("page_start"),
                    lesson.get("page_end"),
                    lesson.get("pdf_page_start"),
                    lesson.get("pdf_page_end"),
                    json.dumps(lesson.get("keywords") or [], ensure_ascii=False),
                    lesson.get("lesson_scope"),
                    now,
                    now,
                ),
            )

    def _complete_index_job(self, job_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE textbook_parse_jobs SET status='indexed', updated_at=? WHERE job_id=? AND status='uploaded'",
                (now_iso(), job_id),
            )
            conn.commit()

    def _create_job(
        self,
        conn: sqlite3.Connection,
        textbook_id: str,
        textbook_version_id: str,
        knowledge_point_id: str | None,
        job_type: str,
        status: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        job_id = f"tj_{uuid.uuid4().hex[:12]}"
        now = now_iso()
        conn.execute(
            """
            INSERT INTO textbook_parse_jobs
            (job_id, textbook_id, textbook_version_id, knowledge_point_id, job_type, status, provider,
             error_message, result_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'mineru_fixture', NULL, ?, ?, ?)
            """,
            (job_id, textbook_id, textbook_version_id, knowledge_point_id, job_type, status, json.dumps(result, ensure_ascii=False), now, now),
        )
        return {
            "job_id": job_id,
            "textbook_id": textbook_id,
            "textbook_version_id": textbook_version_id,
            "knowledge_point_id": knowledge_point_id,
            "job_type": job_type,
            "status": status,
        }

    def _textbook_and_version(self, conn: sqlite3.Connection, textbook_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        textbook = conn.execute("SELECT * FROM textbooks WHERE textbook_id = ?", (textbook_id,)).fetchone()
        if textbook is None:
            raise ValueError(f"Unknown textbook: {textbook_id}")
        version = conn.execute(
            "SELECT * FROM textbook_versions WHERE textbook_id = ? ORDER BY created_at DESC LIMIT 1",
            (textbook_id,),
        ).fetchone()
        if version is None:
            raise ValueError(f"Unknown textbook version: {textbook_id}")
        return dict(textbook), dict(version)

    def _knowledge_point(self, conn: sqlite3.Connection, textbook_version_id: str, knowledge_point_id: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM knowledge_points WHERE textbook_version_id = ? AND knowledge_point_id = ?",
            (textbook_version_id, knowledge_point_id),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown knowledge point: {knowledge_point_id}")
        return dict(row)

    def _resolve_knowledge_points(
        self,
        conn: sqlite3.Connection,
        textbook_version_id: str,
        knowledge_point_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        if knowledge_point_ids:
            return [self._knowledge_point(conn, textbook_version_id, knowledge_point_id) for knowledge_point_id in knowledge_point_ids]
        rows = conn.execute(
            """
            SELECT * FROM knowledge_points
            WHERE textbook_version_id = ?
            ORDER BY CAST(REPLACE(knowledge_point_id, 'kp_', '') AS INTEGER), knowledge_point_id
            """,
            (textbook_version_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _asset_for(self, conn: sqlite3.Connection, textbook_version_id: str, knowledge_point_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM textbook_asset_packages WHERE textbook_version_id = ? AND knowledge_point_id = ?",
            (textbook_version_id, knowledge_point_id),
        ).fetchone()
        return dict(row) if row else None

    def _split_asset(
        self,
        textbook: dict[str, Any],
        version: dict[str, Any],
        kp: dict[str, Any],
        job_id: str,
    ) -> dict[str, Any]:
        source_pdf = Path(version["source_pdf_path"])
        knowledge_point_id = kp["knowledge_point_id"]
        asset_dir = self.assets_root / version["textbook_version_id"] / "knowledge-points" / knowledge_point_id
        slice_path = asset_dir / "source.pdf"
        md_path = asset_dir / "mineru.md"
        self.parser._write_pdf_slice(source_pdf, slice_path, int(kp["pdf_page_start"]), int(kp["pdf_page_end"]))
        checksum = f"sha256:{_sha256_file(slice_path)}"
        with self.connect() as conn:
            now = now_iso()
            existing = conn.execute(
                "SELECT asset_id FROM textbook_asset_packages WHERE textbook_version_id = ? AND knowledge_point_id = ?",
                (version["textbook_version_id"], knowledge_point_id),
            ).fetchone()
            asset_id = existing["asset_id"] if existing else f"ta_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO textbook_asset_packages
                (asset_id, textbook_id, textbook_version_id, knowledge_point_id, source_pdf_path, slice_pdf_path,
                 mineru_md_path, markdown_path, textbook_pages, pdf_pages, parse_status, review_status,
                 mineru_job_id, checksum, diagnostics_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'split_ready', 'unreviewed', ?, ?, NULL, ?, ?)
                ON CONFLICT(textbook_version_id, knowledge_point_id) DO UPDATE SET
                  source_pdf_path=excluded.source_pdf_path,
                  slice_pdf_path=excluded.slice_pdf_path,
                  mineru_md_path=excluded.mineru_md_path,
                  markdown_path=excluded.markdown_path,
                  textbook_pages=excluded.textbook_pages,
                  pdf_pages=excluded.pdf_pages,
                  parse_status='split_ready',
                  review_status='unreviewed',
                  mineru_job_id=excluded.mineru_job_id,
                  checksum=excluded.checksum,
                  diagnostics_json=NULL,
                  updated_at=excluded.updated_at
                """,
                (
                    asset_id,
                    textbook["textbook_id"],
                    version["textbook_version_id"],
                    knowledge_point_id,
                    str(source_pdf),
                    str(slice_path),
                    str(md_path),
                    str(md_path),
                    f"{kp['page_start']}-{kp['page_end']}",
                    f"{kp['pdf_page_start']}-{kp['pdf_page_end']}",
                    job_id,
                    checksum,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                UPDATE knowledge_points
                SET parse_status='split_ready', review_status='unreviewed', updated_at=?
                WHERE textbook_version_id=? AND knowledge_point_id=?
                """,
                (now, version["textbook_version_id"], knowledge_point_id),
            )
            conn.commit()
            asset = self._asset_for(conn, version["textbook_version_id"], knowledge_point_id)
            return self._asset_payload_from_kp(textbook, version, kp, asset=asset)

    def _knowledge_point_payload(self, row: dict[str, Any], version: dict[str, Any]) -> dict[str, Any]:
        keywords = json.loads(row.get("keywords_json") or "[]")
        return {
            "id": row["knowledge_point_id"],
            "chapter_id": renjiao_chapter_id_for_lesson(row),
            "title": row["title"],
            "unit": row.get("unit"),
            "page_start": row.get("page_start"),
            "page_end": row.get("page_end"),
            "pdf_page_start": row.get("pdf_page_start"),
            "pdf_page_end": row.get("pdf_page_end"),
            "keywords": keywords,
            "lesson_scope": row.get("lesson_scope"),
            "textbook_id": row["textbook_id"],
            "textbook_version_id": row["textbook_version_id"],
            "parse_status": row.get("parse_status"),
            "review_status": row.get("review_status"),
            "asset_package": self._asset_payload_from_kp(
                {"textbook_id": row["textbook_id"]},
                version,
                row,
                asset=None,
            ),
        }

    def _asset_payload_from_kp(
        self,
        textbook: dict[str, Any],
        version: dict[str, Any],
        kp: dict[str, Any],
        asset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        textbook_pages = f"{kp['page_start']}-{kp['page_end']}"
        pdf_pages = f"{kp['pdf_page_start']}-{kp['pdf_page_end']}"
        if asset:
            payload = dict(asset)
            diagnostics = json.loads(payload.get("diagnostics_json") or "{}")
            return {
                "asset_id": payload.get("asset_id"),
                "textbook_id": payload["textbook_id"],
                "textbook_version_id": payload["textbook_version_id"],
                "knowledge_point_id": payload["knowledge_point_id"],
                "chapter_id": renjiao_chapter_id_for_lesson(kp),
                "title": kp["title"],
                "source_pdf_path": _api_path(payload["source_pdf_path"]),
                "slice_pdf_path": _api_path(payload["slice_pdf_path"]),
                "mineru_md_path": _api_path(payload["mineru_md_path"]),
                "markdown_path": _api_path(payload["markdown_path"]),
                "textbook_pages": payload["textbook_pages"],
                "pdf_pages": payload["pdf_pages"],
                "parse_status": payload["parse_status"],
                "review_status": payload["review_status"],
                "mineru_job_id": payload.get("mineru_job_id"),
                "checksum": payload.get("checksum"),
                "preview_images": [],
                "diagnostics": diagnostics,
            }
        return {
            "textbook_id": textbook["textbook_id"],
            "textbook_version_id": version["textbook_version_id"],
            "knowledge_point_id": kp["knowledge_point_id"],
            "chapter_id": renjiao_chapter_id_for_lesson(kp),
            "title": kp["title"],
            "source_pdf_path": version["source_pdf_path"],
            "slice_pdf_path": f"knowledge-points/{kp['knowledge_point_id']}/source.pdf",
            "mineru_md_path": f"knowledge-points/{kp['knowledge_point_id']}/mineru.md",
            "markdown_path": f"knowledge-points/{kp['knowledge_point_id']}/mineru.md",
            "textbook_pages": textbook_pages,
            "pdf_pages": pdf_pages,
            "parse_status": kp.get("parse_status") or "indexed",
            "review_status": kp.get("review_status") or "needs_review",
            "preview_images": [],
            "diagnostics": {},
        }

    def _textbook_meta(self, textbook: dict[str, Any], version: dict[str, Any]) -> dict[str, Any]:
        return {
            "subject": textbook["subject"],
            "grade": textbook["grade"],
            "textbook_version": textbook["textbook_version"],
            "volume": textbook["volume"],
            "title": textbook["title"],
            "textbook_id": textbook["textbook_id"],
            "textbook_version_id": version["textbook_version_id"],
            "publisher": "人教版" if textbook["textbook_version"] == "renjiao" else textbook["textbook_version"],
            "version": textbook["textbook_version"],
            "toc_template_id": "renjiao_grade1_volume1_2024_toc" if textbook["textbook_id"] == TEXTBOOK_ID else "manual_toc_pending",
            "page_mapping_strategy": "renjiao_grade1_volume1_offset_5" if textbook["textbook_id"] == TEXTBOOK_ID else "manual_review_required",
            "parser_profile": "jiaocaiTojiaoan_mineru_v1" if textbook["textbook_id"] == TEXTBOOK_ID else "unverified_manual_profile",
            "verification_status": "verified" if textbook["textbook_id"] == TEXTBOOK_ID else "unverified",
            "review_status": "approved" if textbook["textbook_id"] == TEXTBOOK_ID else "needs_review",
            **renjiao_textbook_display_fields(
                textbook["subject"],
                textbook["grade"],
                textbook["textbook_version"],
                textbook["volume"],
            ),
        }

    def _kp_as_lesson(self, kp: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": kp["knowledge_point_id"],
            "chapter_id": renjiao_chapter_id_for_lesson(kp),
            "title": kp["title"],
            "unit": kp.get("unit"),
            "page_start": kp.get("page_start"),
            "page_end": kp.get("page_end"),
            "pdf_page_start": kp.get("pdf_page_start"),
            "pdf_page_end": kp.get("pdf_page_end"),
            "keywords": json.loads(kp.get("keywords_json") or "[]"),
            "lesson_scope": kp.get("lesson_scope") or "",
        }

    def _asset_trust_errors(self, asset: dict[str, Any], kp: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if asset.get("parse_status") not in {"needs_review", "parsed", "indexed"}:
            errors.append("parse_status_not_confirmable")
        if asset.get("review_status") != "needs_review":
            errors.append("review_status_not_pending")

        slice_path = Path(str(asset.get("slice_pdf_path") or ""))
        md_path = Path(str(asset.get("mineru_md_path") or ""))
        if not slice_path.exists():
            errors.append("slice_pdf_missing")
        if not md_path.exists():
            errors.append("mineru_markdown_missing")

        if slice_path.exists():
            try:
                expected_pages = int(kp["pdf_page_end"]) - int(kp["pdf_page_start"]) + 1
                slice_pages = _pdf_page_count(slice_path)
                if slice_pages != expected_pages:
                    errors.append("slice_pdf_page_count_mismatch")
                source_pdf = Path(str(asset.get("source_pdf_path") or ""))
                if source_pdf.exists() and slice_pages >= _pdf_page_count(source_pdf):
                    errors.append("slice_pdf_looks_like_full_book")
            except Exception:
                errors.append("slice_pdf_unreadable")

        if md_path.exists():
            try:
                markdown = md_path.read_text(encoding="utf-8")
                if _missing_markdown_contract_sections(markdown):
                    errors.append("mineru_markdown_contract_incomplete")
                if "待 MinerU 精抽" in markdown or "当前内容待" in markdown:
                    errors.append("mineru_markdown_placeholder_only")
            except Exception:
                errors.append("mineru_markdown_unreadable")

        if not str(asset.get("checksum") or "").startswith("sha256:"):
            errors.append("checksum_missing")
        return errors

    def _batch_result(
        self,
        job: dict[str, Any],
        status: str,
        assets: list[dict[str, Any]],
        failures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        requested_count = len(assets) + len(failures)
        return {
            "job_id": job["job_id"],
            "textbook_id": job["textbook_id"],
            "textbook_version_id": job["textbook_version_id"],
            "job_type": job["job_type"],
            "status": status,
            "requested_count": requested_count,
            "successful_count": len(assets),
            "failed_count": len(failures),
            "assets": assets,
            "failures": failures,
        }

    def _finish_job(self, job_id: str, status: str, result: dict[str, Any], error_message: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE textbook_parse_jobs
                SET status=?, error_message=?, result_json=?, updated_at=?
                WHERE job_id=?
                """,
                (status, error_message, json.dumps(result, ensure_ascii=False), now_iso(), job_id),
            )
            conn.commit()

    def _job_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": row["job_id"],
            "textbook_id": row["textbook_id"],
            "textbook_version_id": row["textbook_version_id"],
            "knowledge_point_id": row.get("knowledge_point_id"),
            "job_type": row["job_type"],
            "status": row["status"],
            "provider": row["provider"],
            "error_message": row.get("error_message"),
            "result": json.loads(row.get("result_json") or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _uploaded_textbook_id(digest: str) -> str:
    return f"textbook-{digest[:12]}"


def _api_path(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row["name"] == column for row in rows):
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def _pdf_page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(path)).pages)


def _missing_markdown_contract_sections(markdown: str) -> list[str]:
    required_sections = [
        "## 一、课节范围判断",
        "## 二、核心知识点",
        "## 三、图片、物体、道具清单",
        "## 四、逐页结构化内容",
        "## 五、可转成教案的课堂流程",
        "## 六、可直接形成的教学目标",
        "## 七、建议板书",
        "## 八、输出与核验说明",
    ]
    return [section for section in required_sections if section not in markdown]


class TextbookAssetExtractionError(RuntimeError):
    def __init__(self, asset: dict[str, Any]):
        super().__init__(str(asset.get("diagnostics", {}).get("message") or "教材资产提取失败"))
        self.asset = asset


class TextbookAssetNotTrustedError(RuntimeError):
    def __init__(self, asset: dict[str, Any]):
        super().__init__("教材资产未通过可信校验，不能确认")
        self.asset = asset
