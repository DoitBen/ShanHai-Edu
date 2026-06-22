import json
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .workflow_config import MVP_NODE_IDS, WorkflowConfig


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    normalized = normalized.strip("-_")
    return normalized or "project"


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
                (project_id, name, subject, grade, textbook_version, volume, lesson_type, created_at, status, project_dir)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    name,
                    payload.get("subject", "math"),
                    payload.get("grade", "3"),
                    payload.get("textbook_version", "renjiao"),
                    payload.get("volume", "xia"),
                    payload.get("lesson_type", "public"),
                    created_at,
                    "active",
                    str(project_dir),
                ),
            )
            node_ids = workflow.runtime_node_ids() if workflow else MVP_NODE_IDS
            for node_id in node_ids:
                status = "approved" if node_id in {"project_meta", "project_config"} else "not_started"
                conn.execute(
                    """
                    INSERT INTO node_state (project_id, node_id, status, current_version_id, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (project_id, node_id, status, None, created_at),
                )
            self.record_event(conn, project_id, "project_meta", "project_created", payload)
        return self.get_project(project_id)

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
            """
        )

    def connect(self, project_dir: Path) -> sqlite3.Connection:
        project_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(project_dir / "project.db")
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

    def list_projects(self) -> list[dict[str, Any]]:
        projects = []
        for db_path in self.projects_root.glob("*/project.db"):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM project_meta LIMIT 1").fetchone()
                if row:
                    data = dict(row)
                    data["project_dir"] = str(db_path.parent)
                    projects.append(data)
        return sorted(projects, key=lambda p: p["created_at"], reverse=True)

    def manifest(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            rows = conn.execute("SELECT * FROM node_state ORDER BY rowid").fetchall()
        return {
            "project": project,
            "nodes": [self.decorate_node_state(conn, project_id, dict(row)) for row in rows],
        }

    def node_state(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM node_state WHERE project_id = ? AND node_id = ?",
            (project_id, node_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown node: {node_id}")
        return dict(row)

    def decorate_node_state(self, conn: sqlite3.Connection, project_id: str, state: dict[str, Any]) -> dict[str, Any]:
        latest_transition = self.latest_transition(conn, project_id, state["node_id"])
        review_reason = None
        if state.get("status") == "needs_review" and latest_transition and latest_transition.get("trigger") == "cascade_invalidate":
            review_reason = {
                "trigger": latest_transition["trigger"],
                "reason": latest_transition.get("reason"),
                "version_id_before": latest_transition.get("version_id_before"),
                "version_id_after": latest_transition.get("version_id_after"),
            }
        return {
            **state,
            "latest_transition": latest_transition,
            "review_reason": review_reason,
        }

    def node_detail(self, project_id: str, node_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            state = self.decorate_node_state(conn, project_id, self.node_state(conn, project_id, node_id))
            content = self.current_content(conn, project_id, node_id)
        return {**state, "content": content}

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
        conn.execute(
            "UPDATE node_state SET status = ?, current_version_id = ?, updated_at = ? WHERE project_id = ? AND node_id = ?",
            (status, current_version_id, now_iso(), project_id, node_id),
        )

    def update_current_version_status(self, conn: sqlite3.Connection, version_id: str, status: str, approved: bool = False) -> None:
        if approved:
            conn.execute(
                "UPDATE node_versions SET status = ?, approved_at = ? WHERE version_id = ?",
                (status, now_iso(), version_id),
            )
            return
        conn.execute("UPDATE node_versions SET status = ? WHERE version_id = ?", (status, version_id))

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

    def approve_node(self, project_id: str, node_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        with self.connect(Path(project["project_dir"])) as conn:
            state = self.node_state(conn, project_id, node_id)
            if not state.get("current_version_id") and node_id not in {"project_meta", "project_config"}:
                raise ValueError("node has no current version")
            updated_at = now_iso()
            conn.execute(
                "UPDATE node_state SET status = ?, updated_at = ? WHERE project_id = ? AND node_id = ?",
                ("approved", updated_at, project_id, node_id),
            )
            if state.get("current_version_id"):
                conn.execute(
                    "UPDATE node_versions SET status = ?, approved_at = ? WHERE version_id = ?",
                    ("approved", updated_at, state["current_version_id"]),
                )
            self.record_event(conn, project_id, node_id, "node_approved", {"version_id": state.get("current_version_id")})
        return {"node_id": node_id, "status": "approved"}

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
