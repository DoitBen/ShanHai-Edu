import sqlite3
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from .store import ProjectStore


PASSABLE_STATES = {"approved", "skipped"}
STATE_VALUES = {"not_started", "drafted", "needs_review", "approved", "blocked", "skipped"}


class StateTransitionError(ValueError):
    pass


class StateEngine:
    def __init__(self, store: ProjectStore, dependencies: Mapping[str, Sequence[str]]):
        self.store = store
        self.dependencies = {node_id: list(deps) for node_id, deps in dependencies.items()}
        self.downstreams = self._build_downstream_graph(self.dependencies)

    def assert_upstreams_passable(self, conn: sqlite3.Connection, project_id: str, node_id: str) -> None:
        if node_id in {"project_meta", "project_config"}:
            return
        for dep in self.dependencies.get(node_id, []):
            state = self.store.node_state(conn, project_id, dep)
            if state["status"] not in PASSABLE_STATES:
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
