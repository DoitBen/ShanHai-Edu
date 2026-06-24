import sqlite3
import json
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from .store import ProjectStore
from .workflow_config import WorkflowConfig


PASSABLE_STATES = {"approved", "skipped"}
STATE_VALUES = {"not_started", "drafted", "needs_review", "approved", "blocked", "skipped"}


class StateTransitionError(ValueError):
    pass


class NodeSkippedError(PermissionError):
    pass


class StateEngine:
    def __init__(
        self,
        store: ProjectStore,
        dependencies: Mapping[str, Sequence[str]],
        workflow: WorkflowConfig | None = None,
    ):
        self.store = store
        self.dependencies = {node_id: list(deps) for node_id, deps in dependencies.items()}
        self.downstreams = self._build_downstream_graph(self.dependencies)
        self.workflow = workflow
        self.passable_states = set(workflow.passable_states if workflow else PASSABLE_STATES) or PASSABLE_STATES
        self.transitions = list(workflow.transitions if workflow else [])

    def transition(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        to_status: str,
        trigger: str,
        *,
        user_id: str | None = None,
        current_version_id: str | None = None,
        version_status: str | None = None,
        approved: bool = False,
        reason: str | None = None,
    ) -> dict[str, Any] | None:
        state = self.store.node_state(conn, project_id, node_id)
        from_status = state.get("status")
        version_id_before = state.get("current_version_id")
        version_id_after = current_version_id if current_version_id is not None else version_id_before
        self._assert_transition_allowed(from_status, to_status, trigger)
        if from_status == to_status and version_id_before == version_id_after:
            return None
        self.store.update_node_state(conn, project_id, node_id, to_status, version_id_after)
        if version_id_after and version_status:
            self.store.update_current_version_status(conn, version_id_after, version_status, approved=approved)
        return self.store.record_state_transition(
            conn,
            project_id=project_id,
            node_id=node_id,
            from_status=from_status,
            to_status=to_status,
            trigger=trigger,
            triggered_by_user_id=user_id,
            version_id_before=version_id_before,
            version_id_after=version_id_after,
            reason=reason or self._transition_reason(trigger, node_id),
        )

    def assert_upstreams_passable(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> None:
        self.assert_can_generate(conn, project_id, node_id)

    def assert_can_generate(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> None:
        if node_id in {"project_meta", "project_config"}:
            return
        state = self.store.node_state(conn, project_id, node_id)
        if state["status"] == "skipped":
            raise NodeSkippedError(f"Node {node_id} is skipped by project configuration")
        blocked = []
        for dep in self.dependencies.get(node_id, []):
            if self._dependency_satisfied_by_direct_lesson(conn, project_id, node_id, dep):
                continue
            dep_state = self.store.node_state(conn, project_id, dep)
            if dep_state["status"] not in self.passable_states:
                blocked.append(
                    {
                        "node_id": dep,
                        "status": dep_state["status"],
                        "current_version_id": dep_state.get("current_version_id"),
                    }
                )
        if not blocked:
            return
        current_status = state.get("status")
        self.store.record_state_transition(
            conn,
            project_id=project_id,
            node_id=node_id,
            from_status=current_status,
            to_status=current_status,
            trigger="dependency_gate_blocked",
            version_id_before=state.get("current_version_id"),
            version_id_after=state.get("current_version_id"),
            reason=json.dumps(
                {
                    "rule_id": "R010",
                    "handled_by": "StateEngine",
                    "blocked_dependencies": blocked,
                },
                ensure_ascii=False,
            ),
        )
        conn.commit()
        raise PermissionError(f"Upstream node {blocked[0]['node_id']} is not approved")

    def _dependency_satisfied_by_direct_lesson(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        dependency_id: str,
    ) -> bool:
        if node_id != "lesson_plan" or dependency_id != "textbook_parse":
            return False
        checker = getattr(self.store, "is_direct_lesson_project", None)
        if checker is None:
            return False
        return bool(checker(conn, project_id))

    def record_version_ready(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        version_result: dict[str, Any],
        trigger: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        from_status = version_result.get("_previous_status")
        to_status = version_result["status"]
        version_id_before = version_result.get("_previous_version_id")
        version_id_after = version_result["version_id"]
        transition_trigger = trigger
        if from_status == "drafted" and to_status == "needs_review" and trigger in {"user_redo", "ai_generate_done"}:
            transition_trigger = "ai_generate_done"
        self._assert_transition_allowed(from_status, to_status, transition_trigger)
        intermediate_trigger = self._intermediate_review_trigger(trigger)
        if from_status != "drafted" and intermediate_trigger:
            self.store.record_state_transition(
                conn,
                project_id=project_id,
                node_id=node_id,
                from_status=from_status,
                to_status="drafted",
                trigger=intermediate_trigger,
                triggered_by_user_id=user_id,
                version_id_before=version_id_before,
                version_id_after=version_id_before,
                reason=self._transition_reason(intermediate_trigger, node_id),
            )
            from_status = "drafted"
            version_id_before = version_id_before
        self.store.record_state_transition(
            conn,
            project_id=project_id,
            node_id=node_id,
            from_status=from_status,
            to_status=to_status,
            trigger=transition_trigger,
            triggered_by_user_id=user_id,
            version_id_before=version_id_before,
            version_id_after=version_id_after,
            reason=self._transition_reason(transition_trigger, node_id),
        )
        if version_id_before != version_id_after:
            self.cascade_invalidate(conn, project_id, node_id, version_id_before, version_id_after, user_id)
        return self._public_version_result(version_result)

    def record_written_version(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        version_result: dict[str, Any],
        trigger: str,
        *,
        reason: dict[str, Any] | str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        public = self.record_version_ready(conn, project_id, node_id, version_result, trigger, user_id=user_id)
        reason_text = self._state_engine_reason(reason)
        if reason_text:
            latest = self.store.latest_transition(conn, project_id, node_id)
            if latest:
                conn.execute(
                    "UPDATE state_transition_log SET reason = ? WHERE transition_id = ?",
                    (reason_text, latest["transition_id"]),
                )
        return public

    def mark_blocked(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        trigger: str,
        *,
        rule_id: str | None = None,
        error_code: str | None = None,
        message: str | None = None,
        retryable: bool | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        state = self.store.node_state(conn, project_id, node_id)
        reason = self._state_engine_reason(
            {
                "rule_id": rule_id,
                "error_code": error_code,
                "message": message,
                "retryable": retryable,
            }
        )
        return self.transition(
            conn,
            project_id,
            node_id,
            "blocked",
            trigger,
            user_id=user_id,
            current_version_id=state.get("current_version_id"),
            version_status="blocked" if state.get("current_version_id") else None,
            reason=reason,
        )

    def approve(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        node_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        state = self.store.node_state(conn, project_id, node_id)
        version_id = state.get("current_version_id")
        self._assert_transition_allowed(state.get("status"), "approved", "user_approve")
        if not version_id and node_id not in {"project_meta", "project_config"}:
            raise ValueError("node has no current version")
        self.transition(
            conn,
            project_id,
            node_id,
            "approved",
            "user_approve",
            user_id=user_id,
            current_version_id=version_id,
            version_status="approved" if version_id else None,
            approved=True,
            reason="用户确认节点产物可作为下游输入",
        )
        self.store.record_event(conn, project_id, node_id, "node_approved", {"version_id": version_id})
        return {"node_id": node_id, "status": "approved"}

    def cascade_invalidate(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        changed_node_id: str,
        version_id_before: str | None,
        version_id_after: str | None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        invalidated = []
        for downstream_id in self._downstream_closure(changed_node_id):
            state = self.store.node_state(conn, project_id, downstream_id)
            if state["status"] != "approved":
                continue
            current_version_id = state.get("current_version_id")
            transition = self.transition(
                conn,
                project_id,
                downstream_id,
                "needs_review",
                "cascade_invalidate",
                user_id=user_id,
                current_version_id=current_version_id,
                version_status="needs_review" if current_version_id else None,
                reason=f"上游 {changed_node_id} 当前版本已变更，需要重新确认",
            )
            if transition:
                invalidated.append(transition)
        return invalidated

    def apply_config_change(self, conn: sqlite3.Connection, project_id: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        transitions = []
        for node_id in self._skip_when_nodes(config):
            state = self.store.node_state(conn, project_id, node_id)
            if state["status"] == "skipped":
                continue
            current_version_id = state.get("current_version_id")
            transition = self.transition(
                conn,
                project_id,
                node_id,
                "skipped",
                "config_change",
                current_version_id=current_version_id,
                version_status="skipped" if current_version_id else None,
                reason="项目配置关闭导入视频分支，节点按 workflow.yaml skip_when 跳过",
            )
            if transition:
                transitions.append(transition)
        return transitions

    def restore_config_skips(self, conn: sqlite3.Connection, project_id: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        if config.get("needs_intro_video") is not True:
            return []
        transitions = []
        for node in self.workflow.nodes if self.workflow else []:
            expression = str(node.get("skip_when") or "")
            if expression != "project_config.needs_intro_video == false":
                continue
            node_id = str(node["id"])
            state = self.store.node_state(conn, project_id, node_id)
            if state["status"] != "skipped":
                continue
            current_version_id = state.get("current_version_id")
            transition = self.transition(
                conn,
                project_id,
                node_id,
                "not_started",
                "config_change",
                current_version_id=current_version_id,
                version_status="not_started" if current_version_id else None,
                reason="项目配置重新启用导入视频分支，节点恢复为未开始",
            )
            if transition:
                transitions.append(transition)
        return transitions

    def _skip_when_nodes(self, config: dict[str, Any]) -> list[str]:
        if not self.workflow:
            return []
        nodes = []
        for node in self.workflow.nodes:
            expression = str(node.get("skip_when") or "")
            if expression == "project_config.needs_intro_video == false" and config.get("needs_intro_video") is False:
                nodes.append(str(node["id"]))
        return nodes

    def _downstream_closure(self, node_id: str) -> list[str]:
        ordered = []
        seen = set()
        queue = deque(self.downstreams.get(node_id, []))
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            ordered.append(current)
            queue.extend(self.downstreams.get(current, []))
        return ordered

    @staticmethod
    def _build_downstream_graph(dependencies: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
        downstreams: dict[str, list[str]] = {}
        for node_id, deps in dependencies.items():
            downstreams.setdefault(node_id, [])
            for dep in deps:
                downstreams.setdefault(dep, []).append(node_id)
        return downstreams

    def _assert_transition_allowed(self, from_status: str | None, to_status: str, trigger: str) -> None:
        if from_status == to_status:
            return
        if self._is_direct_transition_allowed(from_status, to_status, trigger):
            return
        if self._is_review_version_transition_allowed(from_status, to_status, trigger):
            return
        raise StateTransitionError(f"Illegal workflow transition: {from_status} --{trigger}--> {to_status}")

    def _is_direct_transition_allowed(self, from_status: str | None, to_status: str, trigger: str) -> bool:
        effective_trigger = "user_cancel_skip" if trigger == "config_change" and from_status == "skipped" and to_status == "not_started" else trigger
        for transition in self.transitions:
            if transition.get("to") != to_status or transition.get("trigger") != effective_trigger:
                continue
            transition_from = transition.get("from")
            if transition_from == "any" or transition_from == from_status:
                return True
        return False

    def _is_review_version_transition_allowed(self, from_status: str | None, to_status: str, trigger: str) -> bool:
        if to_status != "needs_review":
            return False
        intermediate_trigger = self._intermediate_review_trigger(trigger)
        if intermediate_trigger is None:
            return False
        return self._is_direct_transition_allowed(from_status, "drafted", intermediate_trigger) and self._is_direct_transition_allowed(
            "drafted", "needs_review", trigger
        )

    @staticmethod
    def _intermediate_review_trigger(trigger: str) -> str | None:
        return {
            "ai_generate_done": "ai_generate",
            "user_save_edit": "user_edit",
        }.get(trigger)

    @staticmethod
    def _transition_reason(trigger: str, node_id: str) -> str:
        reasons = {
            "ai_generate": "AI 开始生成节点草稿",
            "ai_generate_done": "AI 生成完成，等待用户审查",
            "user_edit": "用户开始编辑节点产物",
            "user_save_edit": "用户保存编辑，等待重新审查",
            "user_redo": "用户重做节点产物，等待重新审查",
        }
        return reasons.get(trigger, f"{node_id} 状态已更新")

    @staticmethod
    def _state_engine_reason(reason: dict[str, Any] | str | None) -> str | None:
        if isinstance(reason, dict):
            cleaned = {key: value for key, value in reason.items() if value is not None}
            return json.dumps({"handled_by": "StateEngine", **cleaned}, ensure_ascii=False)
        if isinstance(reason, str) and reason.strip():
            return json.dumps({"handled_by": "StateEngine", "message": reason}, ensure_ascii=False)
        return json.dumps({"handled_by": "StateEngine"}, ensure_ascii=False)

    @staticmethod
    def _public_version_result(result: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in result.items() if not key.startswith("_")}
