import sqlite3
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

    def assert_upstreams_passable(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> None:
        if node_id in {"project_meta", "project_config"}:
            return
        state = self.store.node_state(conn, project_id, node_id)
        if state["status"] == "skipped":
            raise NodeSkippedError(f"Node {node_id} is skipped by project configuration")
        for dep in self.dependencies.get(node_id, []):
            state = self.store.node_state(conn, project_id, dep)
            if state["status"] not in self.passable_states:
                raise PermissionError(f"Upstream node {dep} is not approved")

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
        self._assert_transition_allowed(from_status, to_status, trigger)
        self.store.record_state_transition(
            conn,
            project_id=project_id,
            node_id=node_id,
            from_status=from_status,
            to_status=to_status,
            trigger=trigger,
            triggered_by_user_id=user_id,
            version_id_before=version_id_before,
            version_id_after=version_id_after,
            reason=self._transition_reason(trigger, node_id),
        )
        if version_id_before != version_id_after:
            self.cascade_invalidate(conn, project_id, node_id, version_id_before, version_id_after, user_id)
        return self._public_version_result(version_result)

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
        self.store.update_node_state(conn, project_id, node_id, "approved", version_id)
        if version_id:
            self.store.update_current_version_status(conn, version_id, "approved", approved=True)
        self.store.record_state_transition(
            conn,
            project_id=project_id,
            node_id=node_id,
            from_status=state.get("status"),
            to_status="approved",
            trigger="user_approve",
            triggered_by_user_id=user_id,
            version_id_before=version_id,
            version_id_after=version_id,
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
            self._assert_transition_allowed("approved", "needs_review", "cascade_invalidate")
            current_version_id = state.get("current_version_id")
            self.store.update_node_state(conn, project_id, downstream_id, "needs_review", current_version_id)
            if current_version_id:
                self.store.update_current_version_status(conn, current_version_id, "needs_review", approved=False)
            transition = self.store.record_state_transition(
                conn,
                project_id=project_id,
                node_id=downstream_id,
                from_status="approved",
                to_status="needs_review",
                trigger="cascade_invalidate",
                triggered_by_user_id=user_id,
                version_id_before=current_version_id,
                version_id_after=current_version_id,
                reason=f"上游 {changed_node_id} 当前版本已变更，需要重新确认",
            )
            invalidated.append(transition)
        return invalidated

    def apply_config_change(self, conn: sqlite3.Connection, project_id: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        transitions = []
        for node_id in self._skip_when_nodes(config):
            state = self.store.node_state(conn, project_id, node_id)
            if state["status"] == "skipped":
                continue
            self._assert_transition_allowed(state["status"], "skipped", "config_change")
            self.store.update_node_state(conn, project_id, node_id, "skipped", state.get("current_version_id"))
            current_version_id = state.get("current_version_id")
            if current_version_id:
                self.store.update_current_version_status(conn, current_version_id, "skipped", approved=False)
            transitions.append(
                self.store.record_state_transition(
                    conn,
                    project_id=project_id,
                    node_id=node_id,
                    from_status=state["status"],
                    to_status="skipped",
                    trigger="config_change",
                    version_id_before=current_version_id,
                    version_id_after=current_version_id,
                    reason="项目配置关闭导入视频分支，节点按 workflow.yaml skip_when 跳过",
                )
            )
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
            self._assert_transition_allowed("skipped", "not_started", "user_cancel_skip")
            self.store.update_node_state(conn, project_id, node_id, "not_started", state.get("current_version_id"))
            current_version_id = state.get("current_version_id")
            if current_version_id:
                self.store.update_current_version_status(conn, current_version_id, "not_started", approved=False)
            transitions.append(
                self.store.record_state_transition(
                    conn,
                    project_id=project_id,
                    node_id=node_id,
                    from_status="skipped",
                    to_status="not_started",
                    trigger="config_change",
                    version_id_before=current_version_id,
                    version_id_after=current_version_id,
                    reason="项目配置重新启用导入视频分支，节点恢复为未开始",
                )
            )
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
        intermediate_trigger = "ai_generate" if trigger == "ai_generate_done" else "user_edit" if trigger == "user_save_edit" else None
        if intermediate_trigger is None:
            return False
        return self._is_direct_transition_allowed(from_status, "drafted", intermediate_trigger) and self._is_direct_transition_allowed(
            "drafted", "needs_review", trigger
        )

    @staticmethod
    def _transition_reason(trigger: str, node_id: str) -> str:
        reasons = {
            "ai_generate_done": "AI 生成完成，等待用户审查",
            "user_save_edit": "用户保存编辑，等待重新审查",
            "user_redo": "用户重做节点产物，等待重新审查",
        }
        return reasons.get(trigger, f"{node_id} 状态已更新")

    @staticmethod
    def _public_version_result(result: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in result.items() if not key.startswith("_")}
