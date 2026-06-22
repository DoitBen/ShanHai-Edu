import json
import sqlite3
from typing import Any

from .store import ProjectStore


VALID_FEEDBACK_TYPES = {"delivery", "next_session", "classroom_after_use"}


class FeedbackTypeError(ValueError):
    pass


class FeedbackPayloadError(ValueError):
    pass


class FlywheelService:
    def record_approve(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        node_id: str,
        version_id: str | None,
        content: dict[str, Any] | None,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not version_id or content is None:
            return None
        return store.record_approved_sample(
            conn,
            user_id=user_id,
            project_id=project_id,
            node_id=node_id,
            version_id=version_id,
            content_excerpt=_content_excerpt(content),
            content=content,
        )

    def record_post_approve_edit(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        node_id: str,
        before_version_id: str | None,
        after_version_id: str | None,
        before_content: dict[str, Any] | None,
        after_content: dict[str, Any] | None,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not before_version_id or not after_version_id or before_content is None or after_content is None:
            return None
        return store.record_post_approve_edit(
            conn,
            user_id=user_id,
            project_id=project_id,
            node_id=node_id,
            before_version_id=before_version_id,
            after_version_id=after_version_id,
            diff=_diff_snapshot(before_content, after_content),
        )

    def record_rule_override(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        node_id: str,
        rule_id: str,
        reason: str | None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        return store.record_rule_override_event(
            conn,
            user_id=user_id,
            project_id=project_id,
            node_id=node_id,
            rule_id=rule_id,
            reason=reason,
        )

    def record_feedback(
        self,
        conn: sqlite3.Connection,
        store: ProjectStore,
        project_id: str,
        feedback_type: str,
        payload: dict[str, Any],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        if feedback_type not in VALID_FEEDBACK_TYPES:
            raise FeedbackTypeError(f"feedback_type must be one of {sorted(VALID_FEEDBACK_TYPES)}")
        _validate_feedback_payload(feedback_type, payload)
        return store.record_feedback(
            conn,
            user_id=user_id,
            project_id=project_id,
            feedback_type=feedback_type,
            payload=payload,
        )


def _diff_snapshot(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    changed_fields = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    return {
        "changed_fields": changed_fields,
        "before_excerpt": _content_excerpt(before),
        "after_excerpt": _content_excerpt(after),
    }


def _content_excerpt(content: Any, max_chars: int = 500) -> str:
    strings = _collect_strings(content)
    text = " ".join(item.strip() for item in strings if item.strip())
    if not text:
        text = json.dumps(content, ensure_ascii=False, sort_keys=True)
    return text[:max_chars]


def _validate_feedback_payload(feedback_type: str, payload: dict[str, Any]) -> None:
    if not payload:
        raise FeedbackPayloadError("feedback payload must not be empty")
    comment = payload.get("comment")
    if feedback_type == "delivery" and not _meaningful_text(comment):
        raise FeedbackPayloadError("delivery feedback requires a non-empty comment")
    text = " ".join(_collect_strings(payload)).lower()
    placeholder_markers = [
        "占位",
        "预留",
        "等待教师填写正式反馈",
        "placeholder",
        "todo",
        "mock",
    ]
    if any(marker.lower() in text for marker in placeholder_markers):
        raise FeedbackPayloadError("feedback payload contains placeholder text")


def _meaningful_text(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 2


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_collect_strings(item))
        return values
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_collect_strings(item))
        return values
    return []
