import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ControlPlaneStore:
    def __init__(self, db_path: Path, rules_dir: Path):
        self.db_path = db_path
        self.rules_dir = rules_dir
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
            CREATE TABLE IF NOT EXISTS rule_templates (
              rule_id TEXT PRIMARY KEY,
              title TEXT,
              trigger_node TEXT NOT NULL,
              trigger_event TEXT NOT NULL,
              executor TEXT,
              legacy_source TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rule_versions (
              version_id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              version_number INTEGER NOT NULL,
              status TEXT NOT NULL,
              severity TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1,
              check_json TEXT NOT NULL,
              action_message TEXT NOT NULL,
              source TEXT NOT NULL,
              source_file_path TEXT,
              notes TEXT,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              activated_at TEXT,
              FOREIGN KEY (rule_id) REFERENCES rule_templates(rule_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_rule_versions_active_unique
              ON rule_versions(rule_id)
              WHERE status='active';
            CREATE TABLE IF NOT EXISTS rule_set_versions (
              rule_set_version_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              rules_json TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              activated_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_rule_set_versions_active_unique
              ON rule_set_versions(status)
              WHERE status='active';
            CREATE TABLE IF NOT EXISTS rule_release_channels (
              channel_name TEXT PRIMARY KEY,
              rule_set_version_id TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY (rule_set_version_id) REFERENCES rule_set_versions(rule_set_version_id)
            );
            CREATE TABLE IF NOT EXISTS project_rule_binding (
              project_id TEXT PRIMARY KEY,
              rule_set_version_id TEXT NOT NULL,
              binding_mode TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rule_audit_log (
              audit_id TEXT PRIMARY KEY,
              rule_id TEXT,
              version_id TEXT,
              rule_set_version_id TEXT,
              action TEXT NOT NULL,
              actor TEXT NOT NULL,
              notes TEXT,
              created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

    def ensure_seeded(self, actor: str = "system") -> None:
        rules = self._load_file_rules()
        with self.connect() as conn:
            for rule in rules:
                rule_id = str(rule["rule_id"])
                conn.execute(
                    """
                    INSERT OR IGNORE INTO rule_templates
                    (rule_id, title, trigger_node, trigger_event, executor, legacy_source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rule_id,
                        rule.get("title"),
                        str(rule.get("trigger_node") or ""),
                        str(rule.get("trigger_event") or ""),
                        str(rule.get("executor") or ""),
                        rule.get("legacy_source"),
                        now_iso(),
                    ),
                )
                existing = conn.execute("SELECT 1 FROM rule_versions WHERE rule_id=? LIMIT 1", (rule_id,)).fetchone()
                if existing:
                    continue
                version_id = f"rv_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO rule_versions
                    (version_id, rule_id, version_number, status, severity, enabled, check_json, action_message,
                     source, source_file_path, notes, created_by, created_at, activated_at)
                    VALUES (?, ?, ?, 'active', ?, 1, ?, ?, 'file_seed', ?, 'file seed', ?, ?, ?)
                    """,
                    (
                        version_id,
                        rule_id,
                        1,
                        str(rule.get("severity") or "info"),
                        json.dumps(rule.get("check") or {}, ensure_ascii=False),
                        str(rule.get("action_message") or rule.get("title") or rule_id),
                        str(rule.get("_source_file_path") or ""),
                        actor,
                        now_iso(),
                        now_iso(),
                    ),
                )
                self._audit(conn, rule_id, version_id, None, "seed_active", actor, "file seed")
            self._rebuild_active_rule_set(conn, actor, "seed active rule set")
            conn.commit()

    def list_rules(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM rule_templates ORDER BY rule_id").fetchall()
            return [self._template_with_versions(conn, dict(row)) for row in rows]

    def get_rule(self, rule_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM rule_templates WHERE rule_id=?", (rule_id,)).fetchone()
            if row is None:
                raise KeyError(rule_id)
            return self._template_with_versions(conn, dict(row))

    def create_rule_version(
        self,
        rule_id: str,
        *,
        severity: str,
        action_message: str,
        check_json: dict[str, Any],
        enabled: bool = True,
        created_by: str = "admin",
        notes: str | None = None,
    ) -> dict[str, Any]:
        if severity not in {"hard_block", "warning", "info"}:
            raise ValueError("rule severity 不合法")
        with self.connect() as conn:
            template = conn.execute("SELECT * FROM rule_templates WHERE rule_id=?", (rule_id,)).fetchone()
            if template is None:
                raise KeyError(rule_id)
            current = conn.execute("SELECT COALESCE(MAX(version_number), 0) AS n FROM rule_versions WHERE rule_id=?", (rule_id,)).fetchone()["n"]
            version_id = f"rv_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO rule_versions
                (version_id, rule_id, version_number, status, severity, enabled, check_json, action_message,
                 source, source_file_path, notes, created_by, created_at, activated_at)
                VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, 'admin_edit', NULL, ?, ?, ?, NULL)
                """,
                (
                    version_id,
                    rule_id,
                    int(current) + 1,
                    severity,
                    1 if enabled else 0,
                    json.dumps(check_json, ensure_ascii=False),
                    action_message,
                    notes,
                    created_by,
                    now_iso(),
                ),
            )
            self._audit(conn, rule_id, version_id, None, "create_draft", created_by, notes)
            conn.commit()
            return self._version_by_id(conn, version_id)

    def activate_rule_version(self, rule_id: str, version_id: str, actor: str = "admin", notes: str | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            version = conn.execute("SELECT * FROM rule_versions WHERE rule_id=? AND version_id=?", (rule_id, version_id)).fetchone()
            if version is None:
                raise KeyError(version_id)
            conn.execute("UPDATE rule_versions SET status='archived' WHERE rule_id=? AND status='active'", (rule_id,))
            conn.execute("UPDATE rule_versions SET status='active', activated_at=? WHERE version_id=?", (now_iso(), version_id))
            self._audit(conn, rule_id, version_id, None, "activate", actor, notes)
            rule_set = self._rebuild_active_rule_set(conn, actor, f"activate {rule_id}")
            conn.commit()
            return {"active_version": self._version_by_id(conn, version_id), "rule_set_version": rule_set}

    def rollback_rule(self, rule_id: str, version_id: str, actor: str = "admin", notes: str | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            version = conn.execute("SELECT * FROM rule_versions WHERE rule_id=? AND version_id=?", (rule_id, version_id)).fetchone()
            if version is None:
                raise KeyError(version_id)
            conn.execute("UPDATE rule_versions SET status='archived' WHERE rule_id=? AND status='active'", (rule_id,))
            conn.execute("UPDATE rule_versions SET status='active', activated_at=? WHERE version_id=?", (now_iso(), version_id))
            self._audit(conn, rule_id, version_id, None, "rollback_active", actor, notes)
            rule_set = self._rebuild_active_rule_set(conn, actor, f"rollback {rule_id}")
            conn.commit()
            return {"active_version": self._version_by_id(conn, version_id), "rule_set_version": rule_set}

    def active_rule_set(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT r.*
                FROM rule_release_channels c
                JOIN rule_set_versions r ON c.rule_set_version_id = r.rule_set_version_id
                WHERE c.channel_name='default'
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                row = conn.execute("SELECT * FROM rule_set_versions WHERE status='active' ORDER BY created_at DESC LIMIT 1").fetchone()
            if row is None:
                return self._rebuild_active_rule_set(conn, "system", "create missing active rule set")
            return self._decode_rule_set(dict(row))

    def bind_project_to_active_rule_set(self, project_id: str) -> dict[str, Any]:
        active = self.active_rule_set()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO project_rule_binding
                (project_id, rule_set_version_id, binding_mode, created_at)
                VALUES (?, ?, 'pinned', ?)
                """,
                (project_id, active["rule_set_version_id"], now_iso()),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM project_rule_binding WHERE project_id=?", (project_id,)).fetchone()
            return dict(row)

    def rules_for_project(self, project_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rule_set = None
            if project_id:
                binding = conn.execute("SELECT * FROM project_rule_binding WHERE project_id=?", (project_id,)).fetchone()
                if binding:
                    row = conn.execute(
                        "SELECT * FROM rule_set_versions WHERE rule_set_version_id=?",
                        (binding["rule_set_version_id"],),
                    ).fetchone()
                    if row:
                        rule_set = self._decode_rule_set(dict(row))
            if rule_set is None:
                row = conn.execute(
                    """
                    SELECT r.*
                    FROM rule_release_channels c
                    JOIN rule_set_versions r ON c.rule_set_version_id = r.rule_set_version_id
                    WHERE c.channel_name='default'
                    LIMIT 1
                    """
                ).fetchone()
                if row is None:
                    row = conn.execute("SELECT * FROM rule_set_versions WHERE status='active' ORDER BY created_at DESC LIMIT 1").fetchone()
                if row:
                    rule_set = self._decode_rule_set(dict(row))
            return list((rule_set or {}).get("rules") or [])

    def audit_log(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM rule_audit_log ORDER BY created_at, rowid").fetchall()]

    def _template_with_versions(self, conn, template: dict[str, Any]) -> dict[str, Any]:
        versions = [self._decode_version(dict(row)) for row in conn.execute(
            "SELECT * FROM rule_versions WHERE rule_id=? ORDER BY version_number",
            (template["rule_id"],),
        ).fetchall()]
        active = next((version for version in versions if version["status"] == "active"), None)
        return {**template, "active_version": active, "versions": versions}

    def _rebuild_active_rule_set(self, conn, actor: str, notes: str | None) -> dict[str, Any]:
        rows = conn.execute(
            """
            SELECT t.rule_id, t.title, t.trigger_node, t.trigger_event, t.executor, t.legacy_source,
                   v.version_id, v.version_number, v.status, v.severity, v.enabled, v.check_json, v.action_message,
                   v.created_by, v.created_at, v.activated_at
            FROM rule_templates t
            JOIN rule_versions v ON t.rule_id = v.rule_id
            WHERE v.status='active'
            ORDER BY t.rule_id
            """
        ).fetchall()
        rules = [self._row_to_runtime_rule(dict(row)) for row in rows]
        conn.execute("UPDATE rule_set_versions SET status='archived' WHERE status='active'")
        rule_set_id = f"rset_{uuid.uuid4().hex[:12]}"
        created_at = now_iso()
        conn.execute(
            """
            INSERT INTO rule_set_versions
            (rule_set_version_id, status, rules_json, created_by, created_at, activated_at)
            VALUES (?, 'active', ?, ?, ?, ?)
            """,
            (rule_set_id, json.dumps(rules, ensure_ascii=False), actor, created_at, created_at),
        )
        conn.execute(
            """
            INSERT INTO rule_release_channels
            (channel_name, rule_set_version_id, created_by, created_at, updated_at)
            VALUES ('default', ?, ?, ?, ?)
            ON CONFLICT(channel_name) DO UPDATE SET
              rule_set_version_id=excluded.rule_set_version_id,
              updated_at=excluded.updated_at
            """,
            (rule_set_id, actor, created_at, created_at),
        )
        self._audit(conn, None, None, rule_set_id, "activate_rule_set", actor, notes)
        return {"rule_set_version_id": rule_set_id, "status": "active", "rules": rules, "created_by": actor, "created_at": created_at}

    def _load_file_rules(self) -> list[dict[str, Any]]:
        index_path = self.rules_dir / "index.yaml"
        if not index_path.exists():
            return []
        index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        rules = []
        for item in index.get("rules", []):
            path = self.rules_dir / item["file"]
            if not path.exists():
                continue
            rule = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            rule.setdefault("severity", item.get("severity"))
            rule["_source_file_path"] = str(path)
            rules.append(rule)
        return rules

    def _version_by_id(self, conn, version_id: str) -> dict[str, Any]:
        row = conn.execute("SELECT * FROM rule_versions WHERE version_id=?", (version_id,)).fetchone()
        if row is None:
            raise KeyError(version_id)
        return self._decode_version(dict(row))

    def _decode_version(self, row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "enabled": bool(row.get("enabled")), "check_json": json.loads(row.get("check_json") or "{}")}

    def _decode_rule_set(self, row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "rules": json.loads(row.get("rules_json") or "[]")}

    def _row_to_runtime_rule(self, row: dict[str, Any]) -> dict[str, Any]:
        version = self._decode_version(row)
        return {
            "rule_id": row["rule_id"],
            "title": row.get("title"),
            "trigger_node": row["trigger_node"],
            "trigger_event": row["trigger_event"],
            "executor": row.get("executor"),
            "legacy_source": row.get("legacy_source"),
            "version_id": row["version_id"],
            "version_number": row["version_number"],
            "status": row["status"],
            "severity": row["severity"],
            "enabled": version["enabled"],
            "check": version["check_json"],
            "action_message": row["action_message"],
            "created_by": row.get("created_by"),
            "created_at": row.get("created_at"),
            "activated_at": row.get("activated_at"),
        }

    def _audit(
        self,
        conn,
        rule_id: str | None,
        version_id: str | None,
        rule_set_version_id: str | None,
        action: str,
        actor: str,
        notes: str | None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO rule_audit_log
            (audit_id, rule_id, version_id, rule_set_version_id, action, actor, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (f"raud_{uuid.uuid4().hex[:12]}", rule_id, version_id, rule_set_version_id, action, actor, notes, now_iso()),
        )
