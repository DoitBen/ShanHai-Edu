import re
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from .store import ProjectStore


class RuleExecutionError(ValueError):
    def __init__(self, result: dict[str, Any]):
        super().__init__(result["message"])
        self.result = result

    @property
    def rule_id(self) -> str:
        return str(self.result["rule_id"])

    @property
    def code(self) -> str:
        return f"RULE_VIOLATION_{self.rule_id}"

    @property
    def details(self) -> dict[str, Any]:
        return self.result


class RuleHardBlockError(RuleExecutionError):
    pass


class RuleWarningError(ValueError):
    def __init__(self, warnings: list[dict[str, Any]]):
        super().__init__("规则 warning 需要用户确认后才能继续")
        self.warnings = warnings

    @property
    def details(self) -> dict[str, Any]:
        return {"warnings": self.warnings}


class RuleExecutor:
    def __init__(self, rules_dir: Path | None):
        self.rules_dir = rules_dir
        self.rules = self._load_rules(rules_dir) if rules_dir else []

    def run_for_event(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        node_id: str,
        trigger_event: str,
        content: dict[str, Any] | None,
        *,
        version_id: str | None = None,
        override_warning_rule_ids: list[str] | None = None,
        override_reason: str | None = None,
    ) -> list[dict[str, Any]]:
        override_ids = set(override_warning_rule_ids or [])
        event_rules = self._rules_for(node_id, trigger_event)
        results: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for severity in ["hard_block", "warning", "info"]:
            for rule in [item for item in event_rules if item.get("severity") == severity]:
                check = self._builtin_check(rule, content or {})
                if check is None:
                    continue
                passed, details = check
                if severity == "warning" and not passed and rule["rule_id"] in override_ids:
                    details = {**details, "override": True, "override_reason": override_reason}
                    result = self._record(store, conn, project_id, node_id, version_id, rule, trigger_event, True, details)
                    results.append(result)
                    continue
                result = self._record(store, conn, project_id, node_id, version_id, rule, trigger_event, passed, details)
                results.append(result)
                if severity == "hard_block" and not passed:
                    if trigger_event in {"on_save", "on_generate"}:
                        state = store.node_state(conn, project_id, node_id)
                        store.update_node_state(conn, project_id, node_id, "blocked", state.get("current_version_id"))
                        store.record_state_transition(
                            conn,
                            project_id=project_id,
                            node_id=node_id,
                            from_status=state.get("status"),
                            to_status="blocked",
                            trigger="hard_block",
                            version_id_before=state.get("current_version_id"),
                            version_id_after=state.get("current_version_id"),
                            reason=result["message"],
                        )
                    conn.commit()
                    raise RuleHardBlockError(result)
                if severity == "warning" and not passed:
                    warnings.append(result)
        if warnings:
            conn.commit()
            raise RuleWarningError(warnings)
        return results

    def record_r010_result(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        node_id: str,
        passed: bool,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        rule = self._rule_by_id("R010") or {
            "rule_id": "R010",
            "severity": "hard_block",
            "trigger_event": "on_generate",
            "action_message": "上游依赖节点必须 approved 或 skipped",
        }
        result = self._record(store, conn, project_id, node_id, None, rule, "on_generate", passed, details)
        if not passed:
            conn.commit()
        return result

    def _record(
        self,
        store: ProjectStore,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        version_id: str | None,
        rule: dict[str, Any],
        trigger_event: str,
        passed: bool,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        message = rule.get("action_message") or rule.get("title") or rule["rule_id"]
        record = store.record_rule_result(
            conn,
            project_id=project_id,
            node_id=node_id,
            version_id=version_id,
            rule_id=rule["rule_id"],
            trigger_event=trigger_event,
            severity=rule["severity"],
            passed=passed,
            message=message,
            details={
                "rule_id": rule["rule_id"],
                "trigger_event": trigger_event,
                "severity": rule["severity"],
                **details,
            },
        )
        return {
            "rule_id": rule["rule_id"],
            "trigger_event": trigger_event,
            "severity": rule["severity"],
            "passed": passed,
            "message": message,
            "details": record["details"],
        }

    def _builtin_check(self, rule: dict[str, Any], content: dict[str, Any]) -> tuple[bool, dict[str, Any]] | None:
        checks = {
            "R001": self._check_r001,
            "R004": self._check_r004,
            "R006": self._check_r006,
            "R023": self._check_r023,
            "R024": self._check_r024,
            "R026": self._check_r026,
            "R030": self._check_r030,
        }
        check = checks.get(rule["rule_id"])
        return check(content) if check else None

    @staticmethod
    def _check_r001(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        exemption = content.get("voice_exemption") if isinstance(content.get("voice_exemption"), dict) else {}
        passed = (content.get("voice_gender") == "male" and content.get("voice_language") == "zh-CN") or bool(exemption.get("approved"))
        return passed, {
            "voice_gender": content.get("voice_gender"),
            "voice_language": content.get("voice_language"),
            "voice_exemption_approved": bool(exemption.get("approved")),
        }

    @staticmethod
    def _check_r004(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        allowed_styles = {"cartoon", "silhouette", "3d_non_realistic"}
        required_keywords = {"真人", "photorealistic", "real child"}
        broken = []
        for index, character in enumerate(content.get("characters") or []):
            if not isinstance(character, dict):
                broken.append({"index": index, "reason": "character must be object"})
                continue
            style = character.get("style_constraint")
            keywords = set(character.get("banned_keywords") or [])
            if style not in allowed_styles or not required_keywords.issubset(keywords):
                broken.append(
                    {
                        "index": index,
                        "character_id": character.get("character_id"),
                        "style_constraint": style,
                        "missing_banned_keywords": sorted(required_keywords - keywords),
                    }
                )
        return not broken, {"violations": broken}

    @staticmethod
    def _check_r006(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        allowed_layers = {"ppt_text", "ppt_shape", "ppt_chart"}
        broken = []
        for page_index, page in enumerate(content.get("pages") or []):
            if not isinstance(page, dict):
                continue
            for assertion_index, assertion in enumerate(page.get("math_assertions") or []):
                if not isinstance(assertion, dict):
                    continue
                layer = assertion.get("editable_layer")
                if layer not in allowed_layers:
                    broken.append(
                        {
                            "page_index": page.get("page_index", page_index + 1),
                            "assertion_index": assertion_index,
                            "editable_layer": layer,
                            "allowed_layers": sorted(allowed_layers),
                        }
                    )
        return not broken, {"violations": broken}

    @staticmethod
    def _check_r023(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        quota = content.get("page_type_quota") if isinstance(content.get("page_type_quota"), dict) else {}
        value = quota.get("blackboard_summary", 0)
        passed = isinstance(value, (int, float)) and value >= 1
        return passed, {"blackboard_summary": value}

    @staticmethod
    def _check_r024(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        quota = content.get("page_type_quota") if isinstance(content.get("page_type_quota"), dict) else {}
        active_types = [key for key, value in quota.items() if isinstance(value, (int, float)) and value >= 1]
        return len(active_types) >= 5, {"active_page_type_count": len(active_types), "active_page_types": active_types}

    @staticmethod
    def _check_r026(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        forbidden_patterns = [
            "准确性提醒",
            "QA 检查点",
            r"阶段[1-9]",
            "工作流",
            "task_id",
            "file_id",
            "jobs.jsonl",
            "blocked",
            "needs_review",
            "draft",
            "candidate",
        ]
        text_values = RuleExecutor._collect_strings(content)
        hits = []
        for value in text_values:
            for pattern in forbidden_patterns:
                if re.search(pattern, value, flags=re.IGNORECASE):
                    hits.append({"pattern": pattern, "text": value[:120]})
        return not hits, {"violations": hits}

    @staticmethod
    def _check_r030(content: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        media_count = content.get("media_count")
        passed = isinstance(media_count, int) and media_count > 0
        return passed, {"media_count": media_count}

    @staticmethod
    def _collect_strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            values = []
            for key, item in value.items():
                if key == "notes_text":
                    continue
                values.extend(RuleExecutor._collect_strings(item))
            return values
        if isinstance(value, list):
            values = []
            for item in value:
                values.extend(RuleExecutor._collect_strings(item))
            return values
        return []

    def _rules_for(self, node_id: str, trigger_event: str) -> list[dict[str, Any]]:
        return [
            rule
            for rule in self.rules
            if rule.get("trigger_event") == trigger_event and self._node_matches(rule.get("trigger_node"), node_id)
        ]

    def _rule_by_id(self, rule_id: str) -> dict[str, Any] | None:
        return next((rule for rule in self.rules if rule.get("rule_id") == rule_id), None)

    @staticmethod
    def _node_matches(trigger_node: str | None, node_id: str) -> bool:
        if trigger_node in {None, "", "所有"}:
            return True
        candidates = [part.strip() for part in str(trigger_node).split("/") if part.strip()]
        return node_id in candidates

    @staticmethod
    def _load_rules(rules_dir: Path) -> list[dict[str, Any]]:
        index_path = rules_dir / "index.yaml"
        if not index_path.exists():
            return []
        index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        rules = []
        for item in index.get("rules", []):
            rule_path = rules_dir / item["file"]
            if not rule_path.exists():
                continue
            rule = yaml.safe_load(rule_path.read_text(encoding="utf-8")) or {}
            rule.setdefault("severity", item.get("severity"))
            rules.append(rule)
        return rules
