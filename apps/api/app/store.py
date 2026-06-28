import json
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .workflow_config import WorkflowConfig


WORKFLOW_STATUS_VALUES = {"not_started", "drafted", "needs_review", "approved", "blocked", "skipped"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    normalized = normalized.strip("-_")
    return normalized or "project"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _split_user_list(value: str | None) -> list[str]:
    text = _clean_text(value)
    if not text:
        return []
    parts = re.split(r"[、,，;；\n]+", text)
    return [part.strip() for part in parts if part.strip()]


class ProjectStore:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self.projects_root = storage_root / "projects"
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def create_project(self, payload: dict[str, Any], workflow: WorkflowConfig | None = None) -> dict[str, Any]:
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        name = payload["name"]
        project_dir = self.projects_root / f"{slugify(name)}_{project_id}"
        for folder in ["uploads", "assets", "clips", "audio", "exports", "logs"]:
            (project_dir / folder).mkdir(parents=True, exist_ok=True)

        db_path = project_dir / "project.db"
        with self.connect(project_dir) as conn:
            self.init_db(conn)
            created_at = now_iso()
            conn.execute(
                """
                INSERT INTO project_meta
                (
                  project_id, name, subject, grade, textbook_version, volume, lesson_type,
                  textbook_id, textbook_version_id, knowledge_point_id, reference_lesson_plan_id,
                  lesson_plan_source, direct_lesson,
                  created_at, status, project_dir
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    name,
                    payload.get("subject", "math"),
                    payload.get("grade", "3"),
                    payload.get("textbook_version", "renjiao"),
                    payload.get("volume", "xia"),
                    payload.get("lesson_type", "public"),
                    payload.get("textbook_id"),
                    payload.get("textbook_version_id"),
                    payload.get("knowledge_point_id"),
                    payload.get("reference_lesson_plan_id"),
                    self._lesson_plan_source(payload),
                    1 if self._is_direct_lesson_project(payload) else 0,
                    created_at,
                    "active",
                    str(project_dir),
                ),
            )
            node_ids = workflow.runtime_node_ids() if workflow else []
            for node_id in node_ids:
                status = "approved" if node_id in {"project_meta", "project_config"} else "not_started"
                if node_id == "textbook_parse" and self._is_direct_lesson_project(payload):
                    status = "skipped"
                conn.execute(
                    """
                    INSERT INTO node_state (project_id, node_id, status, current_version_id, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (project_id, node_id, status, None, created_at),
                )
            self._seed_create_project_runtime_nodes(conn, project_id, payload, node_ids)
            if workflow:
                from .state_engine import StateEngine

                project_config = self.current_content(conn, project_id, "project_config") or {}
                StateEngine(self, workflow.runtime_dependencies(), workflow).apply_config_change(conn, project_id, project_config)
            self._seed_reference_lesson_plan_start(conn, project_id, payload, node_ids)
            self.record_event(conn, project_id, "project_meta", "project_created", payload)
        return self.get_project(project_id)

    def update_project(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.get_project(project_id)
        allowed_fields = {
            "name",
            "subject",
            "grade",
            "textbook_version",
            "volume",
            "lesson_type",
            "textbook_id",
            "textbook_version_id",
            "knowledge_point_id",
            "reference_lesson_plan_id",
            "lesson_plan_source",
            "direct_lesson",
        }
        updates = {
            key: _clean_text(value)
            for key, value in payload.items()
            if key in allowed_fields and value is not None and _clean_text(value)
        }
        with self.connect(Path(project["project_dir"])) as conn:
            if updates:
                assignments = ", ".join(f"{key} = ?" for key in updates)
                conn.execute(
                    f"UPDATE project_meta SET {assignments} WHERE project_id = ?",
                    (*updates.values(), project_id),
                )
            node_ids = [
                row["node_id"]
                for row in conn.execute(
                    "SELECT node_id FROM node_state WHERE project_id = ?",
                    (project_id,),
                )
            ]
            self._seed_create_project_runtime_nodes(conn, project_id, {**project, **payload}, node_ids)
            self.record_event(conn, project_id, "project_meta", "project_updated", payload)
        return self.get_project(project_id)

    def _seed_create_project_runtime_nodes(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        payload: dict[str, Any],
        node_ids: list[str],
    ) -> None:
        seeded_nodes = {
            "project_config": self._project_config_from_create_payload(payload),
            "visual_contract": self._visual_contract_from_create_payload(payload),
            "character_dict": self._character_dict_from_create_payload(payload),
        }
        for node_id, content in seeded_nodes.items():
            if node_id not in node_ids or content is None:
                continue
            written = self.write_version(conn, project_id, node_id, content, "user_create_project", None, "approved")
            self.update_current_version_status(conn, written["version_id"], "approved", approved=True)
            self.record_state_transition(
                conn,
                project_id,
                node_id,
                written.get("_previous_status"),
                "approved",
                "user_create_project",
                version_id_before=written.get("_previous_version_id"),
                version_id_after=written["version_id"],
                reason="seeded_from_create_project_payload",
            )
            self.record_event(
                conn,
                project_id,
                node_id,
                "runtime_node_seeded",
                {"version_id": written["version_id"], "generated_by": "user_create_project"},
            )

    def _seed_reference_lesson_plan_start(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        payload: dict[str, Any],
        node_ids: list[str],
    ) -> None:
        reference = payload.get("_reference_lesson_plan") if isinstance(payload.get("_reference_lesson_plan"), dict) else None
        reference_id = _clean_text(payload.get("reference_lesson_plan_id"))
        if not reference or not reference_id or "lesson_plan" not in node_ids:
            return
        if "textbook_parse" in node_ids and not payload.get("textbook_id") and not payload.get("knowledge_point_id"):
            state = self.node_state(conn, project_id, "textbook_parse")
            if state["status"] != "skipped":
                self.update_node_state(conn, project_id, "textbook_parse", "skipped", state.get("current_version_id"))
                self.record_state_transition(
                    conn,
                    project_id,
                    "textbook_parse",
                    state.get("status"),
                    "skipped",
                    "config_change",
                    version_id_before=state.get("current_version_id"),
                    version_id_after=state.get("current_version_id"),
                    reason="项目直接引用教案文件创建，教材解析步骤跳过",
                )
        markdown = str(reference.get("markdown") or "").strip()
        if not markdown:
            return
        content = {
            "lesson_plan_markdown": markdown,
            "reference_lesson_plan_id": reference_id,
            "reference_lesson_plan": {
                "lesson_plan_id": reference.get("lesson_plan_id"),
                "title": reference.get("title"),
                "source_type": reference.get("source_type"),
                "source_filename": reference.get("source_filename"),
                "extract_status": reference.get("extract_status"),
            },
            "textbook_anchor": "基于教师提供的教案文件创建项目，待教师核对后继续。",
        }
        written = self.write_version(conn, project_id, "lesson_plan", content, "user_create_project", None, "needs_review")
        self.record_state_transition(
            conn,
            project_id,
            "lesson_plan",
            written.get("_previous_status"),
            "drafted",
            "user_edit",
            version_id_before=written.get("_previous_version_id"),
            version_id_after=written.get("_previous_version_id"),
            reason="项目创建时写入引用教案草稿",
        )
        self.record_state_transition(
            conn,
            project_id,
            "lesson_plan",
            "drafted",
            "needs_review",
            "user_save_edit",
            version_id_before=written.get("_previous_version_id"),
            version_id_after=written["version_id"],
            reason="项目创建时从引用教案文件生成待确认教案草稿",
        )
        self.record_event(
            conn,
            project_id,
            "lesson_plan",
            "runtime_node_seeded",
            {"version_id": written["version_id"], "generated_by": "user_create_project"},
        )

    def _project_config_from_create_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        needs_intro_video = payload.get("needs_intro_video")
        if needs_intro_video is None:
            needs_intro_video = True
        embed_video_in_ppt = payload.get("embed_video_in_ppt")
        if embed_video_in_ppt is None:
            embed_video_in_ppt = False
        return {
            "needs_intro_video": bool(needs_intro_video),
            "intro_video_type": payload.get("intro_video_type") or "full_60_120s",
            "ppt_page_range": payload.get("ppt_page_range") or [12, 16],
            "visual_richness": payload.get("visual_richness") or "mid",
            "embed_video_in_ppt": bool(embed_video_in_ppt),
            "intro_design_types": payload.get("intro_design_types") or ["science", "application", "story"],
            "designs_per_type": int(payload.get("designs_per_type") or 3),
            "source_input": {
                "needs_intro_video": needs_intro_video,
                "embed_video_in_ppt": embed_video_in_ppt,
            },
        }

    @staticmethod
    def _lesson_plan_source(payload: dict[str, Any]) -> str | None:
        source = str(payload.get("lesson_plan_source") or "").strip()
        if source:
            return source
        if ProjectStore._is_direct_lesson_project(payload):
            return "direct_lesson"
        return None

    @staticmethod
    def _is_direct_lesson_project(payload: dict[str, Any]) -> bool:
        source = str(payload.get("lesson_plan_source") or "").strip().lower()
        if source in {"direct_lesson", "lesson_plan", "reference_lesson_plan", "existing_lesson_plan"}:
            return True
        direct_flag = payload.get("direct_lesson")
        if isinstance(direct_flag, bool):
            return direct_flag
        if isinstance(direct_flag, str) and direct_flag.strip().lower() in {"1", "true", "yes", "direct_lesson"}:
            return True
        return bool(str(payload.get("reference_lesson_plan_id") or "").strip())

    def _visual_contract_from_create_payload(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        source = {
            "visual_palette": _clean_text(payload.get("visual_palette")),
            "visual_style_keywords": _clean_text(payload.get("visual_style_keywords")),
            "font_preference": _clean_text(payload.get("font_preference")),
            "compliance_notes": _clean_text(payload.get("compliance_notes")),
        }
        if not any(source.values()):
            return None
        palette = re.findall(r"#[0-9A-Fa-f]{6}", source["visual_palette"] or "")
        if len(palette) < 3:
            palette = ["#0F766E", "#F59E0B", "#F8FAFC"]
        style_keywords = _split_user_list(source["visual_style_keywords"]) or ["非写实卡通", "公开课作品感", "生活化数学情境"]
        return {
            "palette": palette[:5],
            "style_keywords": style_keywords,
            "font_preference": source["font_preference"] or "Microsoft YaHei",
            "source_input": source,
        }

    def _character_dict_from_create_payload(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        profile = _clean_text(payload.get("character_profile"))
        safety_rule = _clean_text(payload.get("character_safety_rule"))
        compliance_notes = _clean_text(payload.get("compliance_notes"))
        if not any([profile, safety_rule, compliance_notes]):
            return None
        return {
            "characters": [
                {
                    "character_id": "char_user_guide",
                    "name": "课堂引导员",
                    "identity": profile or "非写实卡通数学任务引导员",
                    "view_front": "非写实卡通正面形象，保持圆润比例和清晰课堂提示姿态。",
                    "view_side": "非写实卡通侧面形象，服装和发型与正面设定一致。",
                    "view_back": "非写实卡通背面形象，保留固定服装轮廓和简化发型。",
                    "view_half": "半身用于提示气泡旁，不出现真人儿童质感。",
                    "view_hand": "手部为简化卡通手套形态，可指向算式或物品。",
                    "outfit_lock": {"color": "teal-and-gold", "style": "cartoon"},
                    "hair_lock": "简化卡通发型，不使用真实儿童照片质感。",
                    "body_proportion": "3d_non_realistic_childlike_chibi",
                    "style_constraint": "3d_non_realistic",
                    "banned_keywords": ["真人", "photorealistic", "real child"],
                }
            ],
            "source_input": {
                "character_profile": profile,
                "character_safety_rule": safety_rule,
                "compliance_notes": compliance_notes,
            },
        }

    def init_db(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS project_meta (
              project_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              subject TEXT NOT NULL,
              grade TEXT NOT NULL,
              textbook_version TEXT NOT NULL,
              volume TEXT NOT NULL,
              lesson_type TEXT NOT NULL,
              textbook_id TEXT,
              textbook_version_id TEXT,
              knowledge_point_id TEXT,
              reference_lesson_plan_id TEXT,
              lesson_plan_source TEXT,
              direct_lesson INTEGER DEFAULT 0,
              created_at TEXT NOT NULL,
              status TEXT NOT NULL,
              project_dir TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS node_state (
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              status TEXT NOT NULL,
              current_version_id TEXT,
              updated_at TEXT NOT NULL,
              PRIMARY KEY (project_id, node_id)
            );
            CREATE TABLE IF NOT EXISTS node_versions (
              version_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              content_json TEXT NOT NULL,
              generated_by TEXT NOT NULL,
              provider TEXT,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              approved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS assets (
              asset_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              kind TEXT NOT NULL,
              path TEXT NOT NULL,
              mime_type TEXT,
              node_id TEXT,
              version_id TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              task_type TEXT NOT NULL,
              status TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              result_json TEXT,
              error_message TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT,
              event_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS errors (
              error_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT,
              code TEXT NOT NULL,
              message TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cost_log (
              cost_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT,
              provider TEXT,
              model TEXT,
              estimated_cost REAL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS state_transition_log (
              transition_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              from_status TEXT,
              to_status TEXT NOT NULL,
              trigger TEXT NOT NULL,
              triggered_at TEXT NOT NULL,
              triggered_by_user_id TEXT,
              version_id_before TEXT,
              version_id_after TEXT,
              reason TEXT
            );
            CREATE TABLE IF NOT EXISTS rule_result_log (
              result_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              version_id TEXT,
              rule_id TEXT NOT NULL,
              trigger_event TEXT NOT NULL,
              severity TEXT NOT NULL,
              passed INTEGER NOT NULL,
              message TEXT NOT NULL,
              details_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approved_samples (
              sample_id TEXT PRIMARY KEY,
              user_id TEXT,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              version_id TEXT NOT NULL,
              content_excerpt TEXT NOT NULL,
              content_json TEXT NOT NULL,
              approved_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS post_approve_edits (
              edit_id TEXT PRIMARY KEY,
              user_id TEXT,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              before_version_id TEXT NOT NULL,
              after_version_id TEXT NOT NULL,
              diff_json TEXT NOT NULL,
              edited_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rule_override_events (
              override_id TEXT PRIMARY KEY,
              user_id TEXT,
              project_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              rule_id TEXT NOT NULL,
              reason TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback_log (
              feedback_id TEXT PRIMARY KEY,
              user_id TEXT,
              project_id TEXT NOT NULL,
              feedback_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        self._ensure_project_meta_columns(conn)

    def _ensure_project_meta_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"] if isinstance(row, sqlite3.Row) else row[1])
            for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()
        }
        for column in ["textbook_id", "textbook_version_id", "knowledge_point_id", "reference_lesson_plan_id", "lesson_plan_source"]:
            if column not in existing:
                conn.execute(f"ALTER TABLE project_meta ADD COLUMN {column} TEXT")
        if "direct_lesson" not in existing:
            conn.execute("ALTER TABLE project_meta ADD COLUMN direct_lesson INTEGER DEFAULT 0")

    def connect(self, project_dir: Path) -> sqlite3.Connection:
        project_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(project_dir / "project.db", timeout=30)
        conn.row_factory = sqlite3.Row
        self.init_db(conn)
        return conn

    def find_project_dir(self, project_id: str) -> Path:
        matches = list(self.projects_root.glob(f"*_{project_id}"))
        if not matches:
            raise KeyError(f"Unknown project: {project_id}")
        return matches[0]

    def get_project(self, project_id: str) -> dict[str, Any]:
        project_dir = self.find_project_dir(project_id)
        with self.connect(project_dir) as conn:
            row = conn.execute("SELECT * FROM project_meta WHERE project_id = ?", (project_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown project: {project_id}")
            data = dict(row)
            data["project_dir"] = str(project_dir)
            return data

    def is_direct_lesson_project(self, conn: sqlite3.Connection, project_id: str) -> bool:
        row = conn.execute(
            """
            SELECT reference_lesson_plan_id, lesson_plan_source, direct_lesson
            FROM project_meta
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            return False
        return self._is_direct_lesson_project(dict(row))

    def list_projects(self) -> list[dict[str, Any]]:
        projects = []
        for db_path in self.projects_root.glob("*/project.db"):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                self.init_db(conn)
                row = conn.execute("SELECT * FROM project_meta LIMIT 1").fetchone()
                if row:
                    data = dict(row)
                    if data.get("status") == "internal":
                        continue
                    data["project_dir"] = str(db_path.parent)
                    projects.append(data)
        return sorted(projects, key=lambda p: p["created_at"], reverse=True)

    def manifest(
        self,
        project_id: str,
        workflow: WorkflowConfig | None = None,
        rule_runtime_summary: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            rows = conn.execute("SELECT * FROM node_state ORDER BY rowid").fetchall()
        return {
            "project": project,
            "nodes": [self.decorate_node_state(conn, project_id, dict(row), workflow, rule_runtime_summary) for row in rows],
        }

    def node_state(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM node_state WHERE project_id = ? AND node_id = ?",
            (project_id, node_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown node: {node_id}")
        return dict(row)

    def decorate_node_state(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        state: dict[str, Any],
        workflow: WorkflowConfig | None = None,
        rule_runtime_summary: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        latest_transition = self.latest_transition(conn, project_id, state["node_id"])
        review_reason = None
        if state.get("status") == "needs_review" and latest_transition and latest_transition.get("trigger") == "cascade_invalidate":
            review_reason = {
                "trigger": latest_transition["trigger"],
                "reason": latest_transition.get("reason"),
                "version_id_before": latest_transition.get("version_id_before"),
                "version_id_after": latest_transition.get("version_id_after"),
            }
        node_id = state["node_id"]
        node_config = self._workflow_node_config(workflow, node_id)
        content = self.current_content(conn, project_id, node_id) if state.get("current_version_id") else None
        return {
            **state,
            **self._manifest_workflow_fields(node_config),
            "capabilities": self._manifest_capabilities(conn, project_id, state, node_config),
            "artifact": self._manifest_artifact(content),
            "rule_summary": self._manifest_rule_summary(conn, project_id, node_id, (rule_runtime_summary or {}).get(node_id)),
            "latest_transition": latest_transition,
            "review_reason": review_reason,
        }

    def node_detail(
        self,
        project_id: str,
        node_id: str,
        workflow: WorkflowConfig | None = None,
        rule_runtime_summary: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            state = self.decorate_node_state(
                conn,
                project_id,
                self.node_state(conn, project_id, node_id),
                workflow,
                rule_runtime_summary,
            )
            content = self.current_content(conn, project_id, node_id)
        return {**state, "content": content}

    def _workflow_node_config(self, workflow: WorkflowConfig | None, node_id: str) -> dict[str, Any] | None:
        if workflow is None:
            return None
        try:
            return workflow.get_node(node_id)
        except KeyError:
            return None

    def _manifest_workflow_fields(self, node_config: dict[str, Any] | None) -> dict[str, Any]:
        if node_config is None:
            return {
                "title": None,
                "step": None,
                "branch": None,
                "depends_on": [],
                "schema": None,
            }
        return {
            "title": node_config.get("title"),
            "step": node_config.get("step"),
            "branch": node_config.get("branch"),
            "depends_on": list(node_config.get("depends_on") or []),
            "schema": node_config.get("schema"),
        }

    def _manifest_capabilities(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        state: dict[str, Any],
        node_config: dict[str, Any] | None,
    ) -> dict[str, bool]:
        status = state.get("status")
        node_id = state["node_id"]
        dependencies = list(node_config.get("depends_on") or []) if node_config else []
        deps_passable = True
        for dep in dependencies:
            dep_row = conn.execute(
                "SELECT status FROM node_state WHERE project_id = ? AND node_id = ?",
                (project_id, dep),
            ).fetchone()
            if dep_row is None or dep_row["status"] not in {"approved", "skipped"}:
                deps_passable = False
                break
        is_artifact = node_id in {"pptx_artifact", "final_video", "final_delivery"}
        has_version = bool(state.get("current_version_id"))
        return {
            "can_generate": deps_passable and status in {"not_started", "drafted", "needs_review", "blocked"},
            "can_edit": not is_artifact,
            "can_approve": status == "needs_review" and has_version,
            "can_redo": status in {"needs_review", "approved", "blocked"} and has_version,
            "can_skip": bool(node_config and node_config.get("optional") is True and status not in {"approved", "skipped"}),
        }

    def _manifest_artifact(self, content: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(content, dict):
            return None
        artifact_keys = [
            "download_url",
            "pptx_path",
            "video_path",
            "lesson_plan_path",
            "pptx_final_path",
            "video_final_path",
            "delivery_manifest_path",
            "gate_result_json_path",
            "time_stats_md_path",
            "error_code",
            "error_message",
        ]
        artifact = {key: content[key] for key in artifact_keys if content.get(key)}
        return artifact or None

    def _manifest_rule_summary(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        runtime_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = conn.execute(
            """
            SELECT rule_id, severity, passed FROM rule_result_log
            WHERE project_id = ? AND node_id = ?
            ORDER BY created_at
            """,
            (project_id, node_id),
        ).fetchall()
        failed_rule_ids = sorted({row["rule_id"] for row in rows if not row["passed"]})
        warning_rule_ids = sorted({row["rule_id"] for row in rows if row["severity"] == "warning" and not row["passed"]})
        hard_block_rule_ids = sorted({row["rule_id"] for row in rows if row["severity"] == "hard_block" and not row["passed"]})
        return {
            "hard_block_count": len(hard_block_rule_ids),
            "warning_count": len(warning_rule_ids),
            "failed_rule_ids": failed_rule_ids,
            "warning_rule_ids": warning_rule_ids,
            "unimplemented_hard_block_count": int((runtime_summary or {}).get("unimplemented_hard_block_count", 0)),
            "unimplemented_hard_block_rule_ids": list((runtime_summary or {}).get("unimplemented_hard_block_rule_ids", [])),
        }

    def current_content(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> dict[str, Any] | None:
        state = self.node_state(conn, project_id, node_id)
        version_id = state.get("current_version_id")
        if not version_id:
            return None
        row = conn.execute("SELECT content_json FROM node_versions WHERE version_id = ?", (version_id,)).fetchone()
        return json.loads(row["content_json"]) if row else None

    def write_version(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        content: dict[str, Any],
        generated_by: str,
        provider: str | None,
        status: str = "needs_review",
    ) -> dict[str, Any]:
        self._assert_workflow_status(status)
        previous_state = self.node_state(conn, project_id, node_id)
        version_id = f"ver_{uuid.uuid4().hex[:12]}"
        created_at = now_iso()
        conn.execute(
            """
            INSERT INTO node_versions
            (version_id, project_id, node_id, content_json, generated_by, provider, status, created_at, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (version_id, project_id, node_id, json.dumps(content, ensure_ascii=False), generated_by, provider, status, created_at, None),
        )
        conn.execute(
            "UPDATE node_state SET status = ?, current_version_id = ?, updated_at = ? WHERE project_id = ? AND node_id = ?",
            (status, version_id, created_at, project_id, node_id),
        )
        self.record_event(conn, project_id, node_id, "version_written", {"version_id": version_id, "status": status})
        return {
            "version_id": version_id,
            "node_id": node_id,
            "status": status,
            "content": content,
            "_previous_status": previous_state.get("status"),
            "_previous_version_id": previous_state.get("current_version_id"),
        }

    def update_node_state(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        status: str,
        current_version_id: str | None,
    ) -> None:
        self._assert_workflow_status(status)
        conn.execute(
            "UPDATE node_state SET status = ?, current_version_id = ?, updated_at = ? WHERE project_id = ? AND node_id = ?",
            (status, current_version_id, now_iso(), project_id, node_id),
        )

    def update_current_version_status(self, conn: sqlite3.Connection, version_id: str, status: str, approved: bool = False) -> None:
        self._assert_workflow_status(status)
        if approved:
            conn.execute(
                "UPDATE node_versions SET status = ?, approved_at = ? WHERE version_id = ?",
                (status, now_iso(), version_id),
            )
            return
        conn.execute("UPDATE node_versions SET status = ? WHERE version_id = ?", (status, version_id))

    def _assert_workflow_status(self, status: str) -> None:
        if status not in WORKFLOW_STATUS_VALUES:
            raise ValueError(f"Invalid workflow status: {status}")

    def record_state_transition(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        from_status: str | None,
        to_status: str,
        trigger: str,
        triggered_by_user_id: str | None = None,
        version_id_before: str | None = None,
        version_id_after: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        transition = {
            "transition_id": f"tr_{uuid.uuid4().hex[:12]}",
            "project_id": project_id,
            "node_id": node_id,
            "from_status": from_status,
            "to_status": to_status,
            "trigger": trigger,
            "triggered_at": now_iso(),
            "triggered_by_user_id": triggered_by_user_id,
            "version_id_before": version_id_before,
            "version_id_after": version_id_after,
            "reason": reason,
        }
        conn.execute(
            """
            INSERT INTO state_transition_log
            (transition_id, project_id, node_id, from_status, to_status, trigger, triggered_at, triggered_by_user_id,
             version_id_before, version_id_after, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transition["transition_id"],
                transition["project_id"],
                transition["node_id"],
                transition["from_status"],
                transition["to_status"],
                transition["trigger"],
                transition["triggered_at"],
                transition["triggered_by_user_id"],
                transition["version_id_before"],
                transition["version_id_after"],
                transition["reason"],
            ),
        )
        return transition

    def latest_transition(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT * FROM state_transition_log
            WHERE project_id = ? AND node_id = ?
            ORDER BY triggered_at DESC, rowid DESC
            LIMIT 1
            """,
            (project_id, node_id),
        ).fetchone()
        return dict(row) if row else None

    def transition_log(self, project_id: str, node_id: str | None = None) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            params: list[str] = [project_id]
            sql = "SELECT * FROM state_transition_log WHERE project_id = ?"
            if node_id is not None:
                sql += " AND node_id = ?"
                params.append(node_id)
            sql += " ORDER BY triggered_at"
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def record_rule_result(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        version_id: str | None,
        rule_id: str,
        trigger_event: str,
        severity: str,
        passed: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "result_id": f"rule_{uuid.uuid4().hex[:12]}",
            "project_id": project_id,
            "node_id": node_id,
            "version_id": version_id,
            "rule_id": rule_id,
            "trigger_event": trigger_event,
            "severity": severity,
            "passed": 1 if passed else 0,
            "message": message,
            "details": details or {},
            "created_at": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO rule_result_log
            (result_id, project_id, node_id, version_id, rule_id, trigger_event, severity, passed, message, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["result_id"],
                result["project_id"],
                result["node_id"],
                result["version_id"],
                result["rule_id"],
                result["trigger_event"],
                result["severity"],
                result["passed"],
                result["message"],
                json.dumps(result["details"], ensure_ascii=False),
                result["created_at"],
            ),
        )
        return result

    def rule_results(self, project_id: str, node_id: str | None = None) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            params: list[str] = [project_id]
            sql = "SELECT * FROM rule_result_log WHERE project_id = ?"
            if node_id is not None:
                sql += " AND node_id = ?"
                params.append(node_id)
            sql += " ORDER BY created_at"
            rows = conn.execute(sql, params).fetchall()
        results = []
        for row in rows:
            data = dict(row)
            data["details"] = json.loads(data.pop("details_json") or "{}")
            results.append(data)
        return results

    def record_approved_sample(
        self,
        conn: sqlite3.Connection,
        user_id: str | None,
        project_id: str,
        node_id: str,
        version_id: str,
        content_excerpt: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        sample = {
            "sample_id": f"sample_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "project_id": project_id,
            "node_id": node_id,
            "version_id": version_id,
            "content_excerpt": content_excerpt,
            "content": content,
            "approved_at": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO approved_samples
            (sample_id, user_id, project_id, node_id, version_id, content_excerpt, content_json, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample["sample_id"],
                sample["user_id"],
                sample["project_id"],
                sample["node_id"],
                sample["version_id"],
                sample["content_excerpt"],
                json.dumps(sample["content"], ensure_ascii=False),
                sample["approved_at"],
            ),
        )
        return sample

    def record_post_approve_edit(
        self,
        conn: sqlite3.Connection,
        user_id: str | None,
        project_id: str,
        node_id: str,
        before_version_id: str,
        after_version_id: str,
        diff: dict[str, Any],
    ) -> dict[str, Any]:
        edit = {
            "edit_id": f"edit_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "project_id": project_id,
            "node_id": node_id,
            "before_version_id": before_version_id,
            "after_version_id": after_version_id,
            "diff": diff,
            "edited_at": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO post_approve_edits
            (edit_id, user_id, project_id, node_id, before_version_id, after_version_id, diff_json, edited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edit["edit_id"],
                edit["user_id"],
                edit["project_id"],
                edit["node_id"],
                edit["before_version_id"],
                edit["after_version_id"],
                json.dumps(edit["diff"], ensure_ascii=False),
                edit["edited_at"],
            ),
        )
        return edit

    def record_rule_override_event(
        self,
        conn: sqlite3.Connection,
        user_id: str | None,
        project_id: str,
        node_id: str,
        rule_id: str,
        reason: str | None,
    ) -> dict[str, Any]:
        event = {
            "override_id": f"override_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "project_id": project_id,
            "node_id": node_id,
            "rule_id": rule_id,
            "reason": reason,
            "created_at": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO rule_override_events
            (override_id, user_id, project_id, node_id, rule_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["override_id"],
                event["user_id"],
                event["project_id"],
                event["node_id"],
                event["rule_id"],
                event["reason"],
                event["created_at"],
            ),
        )
        return event

    def record_feedback(
        self,
        conn: sqlite3.Connection,
        user_id: str | None,
        project_id: str,
        feedback_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        feedback = {
            "feedback_id": f"feedback_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "project_id": project_id,
            "feedback_type": feedback_type,
            "payload": payload,
            "created_at": now_iso(),
        }
        conn.execute(
            """
            INSERT INTO feedback_log
            (feedback_id, user_id, project_id, feedback_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                feedback["feedback_id"],
                feedback["user_id"],
                feedback["project_id"],
                feedback["feedback_type"],
                json.dumps(feedback["payload"], ensure_ascii=False),
                feedback["created_at"],
            ),
        )
        return feedback

    def flywheel_events(self, project_id: str) -> dict[str, list[dict[str, Any]]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            approved_samples = [dict(row) for row in conn.execute("SELECT * FROM approved_samples WHERE project_id = ? ORDER BY approved_at", (project_id,)).fetchall()]
            post_approve_edits = [dict(row) for row in conn.execute("SELECT * FROM post_approve_edits WHERE project_id = ? ORDER BY edited_at", (project_id,)).fetchall()]
            rule_override_events = [dict(row) for row in conn.execute("SELECT * FROM rule_override_events WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()]
            feedback_log = [dict(row) for row in conn.execute("SELECT * FROM feedback_log WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()]
        for row in approved_samples:
            row["content"] = json.loads(row.pop("content_json") or "{}")
        for row in post_approve_edits:
            row["diff"] = json.loads(row.pop("diff_json") or "{}")
        for row in feedback_log:
            row["payload"] = json.loads(row.pop("payload_json") or "{}")
        return {
            "approved_samples": approved_samples,
            "post_approve_edits": post_approve_edits,
            "rule_override_events": rule_override_events,
            "feedback_log": feedback_log,
        }

    def save_asset(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        kind: str,
        rel_path: str,
        mime_type: str | None,
        node_id: str | None = None,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        asset_id = f"asset_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO assets (asset_id, project_id, kind, path, mime_type, node_id, version_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, project_id, kind, rel_path, mime_type, node_id, version_id, now_iso()),
        )
        return {"asset_id": asset_id, "kind": kind, "path": rel_path, "mime_type": mime_type}

    def upload_textbook(self, project_id: str, file: UploadFile) -> dict[str, Any]:
        project = self.get_project(project_id)
        project_dir = Path(project["project_dir"])
        safe_name = Path(file.filename or "textbook.txt").name
        target = project_dir / "uploads" / safe_name
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        with self.connect(project_dir) as conn:
            asset = self.save_asset(conn, project_id, "textbook", f"uploads/{safe_name}", file.content_type, "textbook_parse")
            self.record_event(conn, project_id, "textbook_parse", "textbook_uploaded", asset)
        return {**asset, "filename": safe_name, "status": "uploaded"}

    def attach_textbook_file(self, project_id: str, source_path: Path, filename: str, mime_type: str = "application/pdf") -> dict[str, Any]:
        project = self.get_project(project_id)
        project_dir = Path(project["project_dir"])
        safe_name = Path(filename).name
        target = project_dir / "uploads" / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
        with self.connect(project_dir) as conn:
            asset = self.save_asset(conn, project_id, "textbook", f"uploads/{safe_name}", mime_type, "textbook_parse")
            self.record_event(conn, project_id, "textbook_parse", "textbook_attached_from_library", asset)
        return {**asset, "filename": safe_name, "status": "uploaded"}

    def latest_textbook_text(self, conn: sqlite3.Connection, project_dir: Path, project_id: str) -> str:
        source = self.latest_textbook_source(conn, project_dir, project_id)
        suffix = source["path"].suffix.lower()
        if suffix not in {".txt", ".md"}:
            raise ValueError(f"Unsupported textbook type for MVP: {suffix}")
        return source["path"].read_text(encoding="utf-8", errors="ignore")

    def latest_textbook_source(self, conn: sqlite3.Connection, project_dir: Path, project_id: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT path, mime_type FROM assets WHERE project_id = ? AND kind = 'textbook' ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if row is None:
            raise ValueError("No textbook uploaded")
        path = project_dir / row["path"]
        return {
            "path": path,
            "rel_path": row["path"],
            "mime_type": row["mime_type"],
            "filename": path.name,
        }

    def create_task(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        task_type: str,
        payload: dict[str, Any],
        status: str = "generated",
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        created_at = now_iso()
        conn.execute(
            """
            INSERT INTO tasks
            (task_id, project_id, node_id, task_type, status, payload_json, result_json, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                project_id,
                node_id,
                task_type,
                status,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(result or {}, ensure_ascii=False),
                error_message,
                created_at,
                created_at,
            ),
        )
        conn.commit()
        return {
            **self._decorate_task(
                {
                    "task_id": task_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "task_type": task_type,
                    "status": status,
                    "payload": payload,
                    "result": result or {},
                    "error_message": error_message,
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            )
        }

    def tasks(self, project_id: str) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            rows = conn.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()
        return [self._task_from_row(row) for row in rows]

    def task(self, project_id: str, task_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE project_id = ? AND task_id = ?",
                (project_id, task_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown task: {task_id}")
        return self._task_from_row(row)

    def update_task(
        self,
        conn: sqlite3.Connection,
        task_id: str,
        status: str,
        result: dict[str, Any],
        error_message: str | None = None,
    ) -> dict[str, Any]:
        updated_at = now_iso()
        conn.execute(
            """
            UPDATE tasks
            SET status = ?, result_json = ?, error_message = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (status, json.dumps(result, ensure_ascii=False), error_message, updated_at, task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown task: {task_id}")
        return self._task_from_row(row)

    def versions(self, project_id: str, node_id: str) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            rows = conn.execute(
                "SELECT * FROM node_versions WHERE project_id = ? AND node_id = ? ORDER BY created_at",
                (project_id, node_id),
            ).fetchall()
        versions = []
        for row in rows:
            data = dict(row)
            data["content"] = json.loads(data.pop("content_json"))
            versions.append(data)
        return versions

    def assets(self, project_id: str) -> list[dict[str, Any]]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            rows = conn.execute("SELECT * FROM assets WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()
        return [dict(row) for row in rows]

    def asset(self, project_id: str, asset_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            row = conn.execute(
                "SELECT * FROM assets WHERE project_id = ? AND asset_id = ?",
                (project_id, asset_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown asset: {asset_id}")
        return dict(row)

    def record_error(self, conn: sqlite3.Connection, project_id: str, node_id: str | None, code: str, message: str) -> None:
        created_at = now_iso()
        conn.execute(
            "INSERT INTO errors (error_id, project_id, node_id, code, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"err_{uuid.uuid4().hex[:12]}", project_id, node_id, code, message, created_at),
        )
        project_dir = self.find_project_dir(project_id)
        with (project_dir / "logs" / "errors.log").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"code": code, "message": message, "node_id": node_id, "created_at": created_at}, ensure_ascii=False) + "\n")

    def record_event(self, conn: sqlite3.Connection, project_id: str, node_id: str | None, event_type: str, payload: dict[str, Any]) -> None:
        created_at = now_iso()
        conn.execute(
            "INSERT INTO events (event_id, project_id, node_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"evt_{uuid.uuid4().hex[:12]}", project_id, node_id, event_type, json.dumps(payload, ensure_ascii=False), created_at),
        )
        project_dir = self.find_project_dir(project_id) if project_id else None
        if project_dir:
            with (project_dir / "logs" / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"event_type": event_type, "node_id": node_id, "payload": payload, "created_at": created_at}, ensure_ascii=False) + "\n")

    def _task_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json"))
        data["result"] = json.loads(data.pop("result_json") or "{}")
        return self._decorate_task(data)

    def _decorate_task(self, data: dict[str, Any]) -> dict[str, Any]:
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        video_url = result.get("video_url") or payload.get("video_url")
        image_url = result.get("image_url") or payload.get("image_url")
        data["provider_task_id"] = result.get("provider_task_id") or payload.get("provider_task_id")
        data["error_code"] = result.get("error_code")
        data["retryable"] = bool(result.get("retryable", False))
        data["download_path"] = result.get("download_path") or result.get("clip_path") or payload.get("download_path") or payload.get("clip_path")
        data["clip_path"] = result.get("clip_path") or result.get("download_path") or payload.get("clip_path") or payload.get("download_path")
        data["image_path"] = result.get("image_path") or payload.get("image_path")
        data["image_url"] = image_url
        data["download_status"] = result.get("download_status") or ("not_started" if data.get("clip_path") and data.get("status") not in {"completed", "generated"} else None)
        data["video_url_present"] = bool(video_url)
        return data
