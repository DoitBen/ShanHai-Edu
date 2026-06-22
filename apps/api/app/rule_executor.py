import re
import sqlite3
from pathlib import Path
from typing import Any

from pptx import Presentation
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
        nested_details = self.result.get("details")
        if isinstance(nested_details, dict):
            return {**self.result, **nested_details, "details": nested_details}
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
    IMPLEMENTED_RULE_IDS = {"R001", "R004", "R006", "R010", "R023", "R024", "R026", "R030"}

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
                check = self._builtin_check(rule, content or {}, conn, store, project_id)
                if check is None:
                    self._record_unimplemented_rule(store, conn, project_id, node_id, version_id, rule, trigger_event)
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
                            trigger="hard_block_rule_hit",
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

    def coverage(self) -> dict[str, Any]:
        rules = []
        for rule in self.rules:
            rule_id = str(rule.get("rule_id"))
            implemented = self._is_implemented(rule)
            rules.append(
                {
                    "rule_id": rule_id,
                    "title": rule.get("title"),
                    "trigger_node": rule.get("trigger_node"),
                    "trigger_event": rule.get("trigger_event"),
                    "severity": rule.get("severity"),
                    "declared_executor": rule.get("executor"),
                    "executor_type": "builtin" if implemented else "unimplemented",
                    "implemented": implemented,
                }
            )
        unimplemented = [rule for rule in rules if not rule["implemented"]]
        return {
            "loaded_count": len(rules),
            "implemented_count": len(rules) - len(unimplemented),
            "unimplemented_count": len(unimplemented),
            "rules": rules,
            "implemented_rule_ids": [rule["rule_id"] for rule in rules if rule["implemented"]],
            "unimplemented_rule_ids": [rule["rule_id"] for rule in unimplemented],
            "unimplemented_hard_block_rule_ids": [
                rule["rule_id"] for rule in unimplemented if rule.get("severity") == "hard_block"
            ],
        }

    def summary_for_node(self, node_id: str) -> dict[str, Any]:
        applicable = [rule for rule in self.rules if self._node_matches(rule.get("trigger_node"), node_id)]
        unimplemented_hard_blocks = sorted(
            {
                str(rule["rule_id"])
                for rule in applicable
                if rule.get("severity") == "hard_block" and not self._is_implemented(rule)
            }
        )
        return {
            "unimplemented_hard_block_count": len(unimplemented_hard_blocks),
            "unimplemented_hard_block_rule_ids": unimplemented_hard_blocks,
        }

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

    def _record_unimplemented_rule(
        self,
        store: ProjectStore,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        version_id: str | None,
        rule: dict[str, Any],
        trigger_event: str,
    ) -> dict[str, Any] | None:
        if rule.get("severity") != "hard_block":
            return None
        return self._record(
            store,
            conn,
            project_id,
            node_id,
            version_id,
            rule,
            trigger_event,
            True,
            {
                "implemented": False,
                "executor_type": "unimplemented",
                "coverage_visible": True,
            },
        )

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

    def _builtin_check(
        self,
        rule: dict[str, Any],
        content: dict[str, Any],
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
    ) -> tuple[bool, dict[str, Any]] | None:
        checks = {
            "R001": self._check_r001,
            "R004": self._check_r004,
            "R006": self._check_r006,
            "R023": self._check_r023,
            "R024": self._check_r024,
            "R030": self._check_r030,
        }
        if rule["rule_id"] == "R026":
            return self._check_r026(content, conn, store, project_id)
        check = checks.get(rule["rule_id"])
        return check(content) if check else None

    def _is_implemented(self, rule: dict[str, Any]) -> bool:
        return str(rule.get("rule_id")) in self.IMPLEMENTED_RULE_IDS

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

    def _check_r026(
        self,
        content: dict[str, Any],
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
    ) -> tuple[bool, dict[str, Any]]:
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
        pptx_path = content.get("pptx_path") if isinstance(content.get("pptx_path"), str) else None
        if not pptx_path:
            return False, {
                "pptx_path": None,
                "error_code": "PPTX_PATH_MISSING",
                "violations": [{"source": "pptx_path", "error_code": "PPTX_PATH_MISSING", "text": ""}],
            }
        pptx_probe = self._pptx_visible_text_values(conn, store, project_id, pptx_path)
        pptx_error = next((item for item in pptx_probe if "error_code" in item), None)
        if pptx_error:
            return False, {"pptx_path": pptx_path, "error_code": pptx_error["error_code"], "violations": [pptx_error]}
        text_values = [{"source": "content_json", "text": value} for value in RuleExecutor._collect_strings(content)]
        text_values.extend(pptx_probe)
        hits = []
        for item in text_values:
            value = item["text"]
            for pattern in forbidden_patterns:
                if re.search(pattern, value, flags=re.IGNORECASE):
                    hits.append({"source": item["source"], "pattern": pattern, "text": value[:120]})
        return not hits, {"pptx_path": pptx_path, "violations": hits}

    def _pptx_visible_text_values(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        rel_path: str,
    ) -> list[dict[str, str]]:
        project_dir = Path(store.get_project(project_id)["project_dir"])
        project_root = project_dir.resolve()
        pptx_path = (project_dir / rel_path).resolve()
        if not _is_within(pptx_path, project_root):
            return [{"source": "pptx_path", "error_code": "PPTX_PATH_OUTSIDE_PROJECT", "text": rel_path}]
        if pptx_path.suffix.lower() != ".pptx":
            return [{"source": "pptx_path", "error_code": "PPTX_EXTENSION_INVALID", "text": rel_path}]
        if not pptx_path.exists():
            return [{"source": "pptx_path", "error_code": "PPTX_FILE_NOT_FOUND", "text": rel_path}]
        try:
            presentation = Presentation(str(pptx_path))
        except Exception:
            return [{"source": "pptx_path", "error_code": "PPTX_PARSE_FAILED", "text": rel_path}]
        values: list[dict[str, str]] = []
        for slide_index, slide in enumerate(presentation.slides, start=1):
            for shape_index, shape in enumerate(slide.shapes, start=1):
                if not getattr(shape, "has_text_frame", False):
                    continue
                text = "\n".join(paragraph.text for paragraph in shape.text_frame.paragraphs).strip()
                if text:
                    values.append({"source": "pptx_shape_text", "text": text, "location": f"slide:{slide_index}/shape:{shape_index}"})
        return values

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
        candidates = [part.strip() for part in re.split(r"[|/]", str(trigger_node)) if part.strip()]
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


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
