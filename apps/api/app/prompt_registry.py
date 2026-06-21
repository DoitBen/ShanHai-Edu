from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .prompt_loader import extract_variables, load_prompt_body_from_path, render_prompt_body


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            self.init_db(conn)

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, conn) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS prompt_templates (
              template_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              provider TEXT NOT NULL,
              description TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(node_id, provider)
            );
            CREATE TABLE IF NOT EXISTS prompt_versions (
              version_id TEXT PRIMARY KEY,
              template_id TEXT NOT NULL,
              version_number INTEGER NOT NULL,
              body TEXT NOT NULL,
              variables_json TEXT NOT NULL,
              status TEXT NOT NULL,
              canary_percent INTEGER DEFAULT 0,
              source TEXT NOT NULL,
              source_file_path TEXT,
              notes TEXT,
              checksum TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              activated_at TEXT,
              FOREIGN KEY (template_id) REFERENCES prompt_templates(template_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_versions_active_unique
              ON prompt_versions(template_id)
              WHERE status='active';
            CREATE INDEX IF NOT EXISTS idx_prompt_versions_lookup
              ON prompt_versions(template_id, status);
            CREATE TABLE IF NOT EXISTS prompt_usage_log (
              log_id TEXT PRIMARY KEY,
              template_id TEXT NOT NULL,
              version_id TEXT NOT NULL,
              project_id TEXT,
              node_id TEXT NOT NULL,
              invoked_at TEXT NOT NULL,
              success INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS prompt_audit_log (
              audit_id TEXT PRIMARY KEY,
              template_id TEXT NOT NULL,
              version_id TEXT,
              action TEXT NOT NULL,
              actor TEXT NOT NULL,
              notes TEXT,
              created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

    def ensure_template(self, node_id: str, provider: str, description: str | None = None) -> dict[str, Any]:
        template_id = f"{node_id}@{provider}"
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO prompt_templates (template_id, node_id, provider, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (template_id, node_id, provider, description, now_iso()),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM prompt_templates WHERE template_id=?", (template_id,)).fetchone()
            return dict(row)

    def create_version(
        self,
        *,
        template_id: str,
        body: str,
        variables: list[str],
        status: str,
        created_by: str,
        notes: str | None = None,
        source: str = "admin_edit",
        source_file_path: str | None = None,
        canary_percent: int = 0,
    ) -> dict[str, Any]:
        checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
        with self.connect() as conn:
            current = conn.execute(
                "SELECT COALESCE(MAX(version_number), 0) AS n FROM prompt_versions WHERE template_id=?",
                (template_id,),
            ).fetchone()["n"]
            version_id = f"prv_{uuid.uuid4().hex[:12]}"
            if status == "active":
                conn.execute("UPDATE prompt_versions SET status='archived' WHERE template_id=? AND status='active'", (template_id,))
            activated_at = now_iso() if status == "active" else None
            conn.execute(
                """
                INSERT INTO prompt_versions
                (version_id, template_id, version_number, body, variables_json, status, canary_percent,
                 source, source_file_path, notes, checksum, created_by, created_at, activated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    template_id,
                    int(current) + 1,
                    body,
                    json.dumps(variables, ensure_ascii=False),
                    status,
                    canary_percent,
                    source,
                    source_file_path,
                    notes,
                    checksum,
                    created_by,
                    now_iso(),
                    activated_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO prompt_audit_log (audit_id, template_id, version_id, action, actor, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f"aud_{uuid.uuid4().hex[:12]}", template_id, version_id, f"create_{status}", created_by, notes, now_iso()),
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM prompt_versions WHERE version_id=?", (version_id,)).fetchone())

    def seed_from_file(self, node_id: str, provider: str, body: str, source_file_path: Path, created_by: str) -> bool:
        template = self.ensure_template(node_id, provider)
        with self.connect() as conn:
            existing = conn.execute("SELECT 1 FROM prompt_versions WHERE template_id=? LIMIT 1", (template["template_id"],)).fetchone()
        if existing:
            return False
        self.create_version(
            template_id=template["template_id"],
            body=body,
            variables=extract_variables(body),
            status="active",
            created_by=created_by,
            notes="file seed",
            source="file_seed",
            source_file_path=str(source_file_path),
        )
        return True

    def active_version(self, node_id: str, provider: str) -> dict[str, Any] | None:
        template_id = f"{node_id}@{provider}"
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM prompt_versions WHERE template_id=? AND status='active' ORDER BY version_number DESC LIMIT 1",
                (template_id,),
            ).fetchone()
            return dict(row) if row else None

    def canary_versions(self, node_id: str, provider: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM prompt_versions WHERE template_id=? AND status='canary' AND canary_percent > 0",
                (f"{node_id}@{provider}",),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_templates(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM prompt_templates ORDER BY template_id").fetchall()]

    def list_versions(self, template_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM prompt_versions WHERE template_id=? ORDER BY version_number",
                    (template_id,),
                ).fetchall()
            ]


class PromptRegistry:
    def __init__(self, store: PromptStore, file_root: Path, cache_ttl_seconds: int = 30):
        self.store = store
        self.file_root = file_root
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def ensure_seeded(self, created_by: str = "system") -> None:
        if not self.file_root.exists():
            return
        for path in self.file_root.glob("*/**/*.md"):
            try:
                rel = path.relative_to(self.file_root)
            except ValueError:
                continue
            if len(rel.parts) != 2:
                continue
            if rel.parts[0] in {"shared", "supervisor"}:
                continue
            node_id = _normalize_node_id(rel.parts[0])
            provider = path.stem
            self.store.seed_from_file(node_id, provider, load_prompt_body_from_path(self.file_root, path), path, created_by)

    def template(self, node_id: str, provider: str, route_key: str | None = None) -> dict[str, Any] | None:
        cache_key = f"{node_id}@{provider}@{route_key or ''}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return cached[1]
        selected = self._select_canary(node_id, provider, route_key) or self.store.active_version(node_id, provider)
        if selected:
            self._cache[cache_key] = (time.time(), selected)
        return selected

    def render(self, node_id: str, provider: str, context: dict[str, Any], route_key: str | None = None) -> str:
        template = self.template(node_id, provider, route_key)
        if not template:
            raise FileNotFoundError(f"未找到 prompt 模板：{node_id}@{provider}")
        return render_prompt_body(template["body"], context)

    def invalidate(self, node_id: str | None = None, provider: str | None = None) -> None:
        if not node_id and not provider:
            self._cache.clear()
            return
        prefix = f"{node_id or ''}@{provider or ''}"
        for key in list(self._cache):
            if key.startswith(prefix):
                self._cache.pop(key, None)

    def _select_canary(self, node_id: str, provider: str, route_key: str | None) -> dict[str, Any] | None:
        if not route_key:
            return None
        for version in self.store.canary_versions(node_id, provider):
            percent = int(version.get("canary_percent") or 0)
            bucket = int(hashlib.sha256(f"{route_key}:{node_id}".encode("utf-8")).hexdigest()[:8], 16) % 100
            if bucket < percent:
                return version
        return None


def _normalize_node_id(folder: str) -> str:
    mapping = {
        "node_01_lesson_plan": "lesson_plan",
        "node_02_ppt_assembly": "ppt_assembly",
        "node_03_ppt_page_script": "ppt_page_script",
        "node_4b_intro_video_script": "intro_video_script",
        "node_06_storyboard": "storyboard",
        "node_08_video_generation": "final_video",
    }
    return mapping.get(folder, folder)
