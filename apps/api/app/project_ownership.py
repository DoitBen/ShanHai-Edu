import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import secrets

from fastapi import HTTPException, Request

from .auth_store import AuthStore, normalize_email
from .settings import Settings
from .store import ProjectStore


OWNERSHIP_ISSUE_MISSING_COLUMN = "missing_owner_column"
OWNERSHIP_ISSUE_MISSING_OWNER = "missing_owner"
OWNERSHIP_ISSUE_ORPHANED_OWNER = "orphaned_owner"


@dataclass
class OwnershipIssue:
    project_id: str
    project_dir: str
    code: str
    message: str
    owner_id: str | None = None


@dataclass
class OwnershipVerifyResult:
    total_projects: int
    owned_projects: int
    missing_owner_projects: int
    orphaned_owner_projects: int
    projects_missing_owner_column: int
    ready_for_phase_c: bool
    issues: list[OwnershipIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "owned_projects": self.owned_projects,
            "missing_owner_projects": self.missing_owner_projects,
            "orphaned_owner_projects": self.orphaned_owner_projects,
            "projects_missing_owner_column": self.projects_missing_owner_column,
            "ready_for_phase_c": self.ready_for_phase_c,
            "issues": [asdict(issue) for issue in self.issues],
        }


@dataclass
class ProjectOwnershipRecord:
    project_id: str
    project_dir: Path
    has_owner_column: bool
    owner_id: str | None


@dataclass
class MigrationAction:
    project_id: str
    project_dir: str
    owner_id: str
    skipped_existing_owner: bool = False


@dataclass
class MigrationPlan:
    actions: list[MigrationAction]
    errors: list[str]
    planned_count: int
    skipped_existing_owner_count: int


@dataclass
class MigrationResult:
    planned_count: int
    written_count: int
    skipped_existing_owner_count: int
    failed_count: int
    errors: list[str]

    def to_lines(self) -> list[str]:
        return [
            f"planned_count={self.planned_count}",
            f"written_count={self.written_count}",
            f"skipped_existing_owner_count={self.skipped_existing_owner_count}",
            f"failed_count={self.failed_count}",
            f"errors={json.dumps(self.errors, ensure_ascii=False)}",
        ]


def resolve_project_owner(request: Request, settings: Settings, auth_store: AuthStore) -> str:
    auth_service = getattr(request.app.state, "auth_service")
    session_token = request.cookies.get(settings.auth_cookie_name)
    session, user = auth_service.optional_session_from_token(session_token)
    if session and user:
        return str(user["user_id"])

    _require_legacy_backend_token_for_fallback(request, settings)

    fallback_owner_id = str(settings.project_creation_default_owner_user_id or "").strip()
    if fallback_owner_id:
        fallback_owner = auth_store.get_user_by_id(fallback_owner_id)
        if fallback_owner and int(fallback_owner.get("is_active") or 0) == 1:
            return str(fallback_owner["user_id"])

    raise HTTPException(
        status_code=400,
        detail={
            "code": "PROJECT_OWNER_REQUIRED",
            "message": "创建项目需要有效登录用户或已配置的默认项目 owner",
        },
    )


def _require_legacy_backend_token_for_fallback(request: Request, settings: Settings) -> None:
    if not settings.backend_api_token:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "未授权访问"})
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "未授权访问"})
    candidate = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(candidate, settings.backend_api_token):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "无权访问该资源"})


def reject_request_owner(payload: dict[str, Any]) -> None:
    if "owner_id" in payload:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "PROJECT_OWNER_FORBIDDEN",
                "message": "项目 owner 只能由服务端根据当前用户写入",
            },
        )


def scan_project_ownership(store: ProjectStore, auth_store: AuthStore) -> OwnershipVerifyResult:
    records = list_project_ownership_records(store)
    issues: list[OwnershipIssue] = []
    owned_projects = 0
    users_by_id = {str(user["user_id"]): user for user in auth_store.list_users()}
    for record in records:
        if not record.has_owner_column:
            issues.append(
                OwnershipIssue(
                    project_id=record.project_id,
                    project_dir=str(record.project_dir),
                    code=OWNERSHIP_ISSUE_MISSING_COLUMN,
                    message="项目数据库缺少 owner_id 列",
                )
            )
            continue
        if not record.owner_id:
            issues.append(
                OwnershipIssue(
                    project_id=record.project_id,
                    project_dir=str(record.project_dir),
                    code=OWNERSHIP_ISSUE_MISSING_OWNER,
                    message="项目缺少 owner_id",
                )
            )
            continue
        if record.owner_id not in users_by_id:
            issues.append(
                OwnershipIssue(
                    project_id=record.project_id,
                    project_dir=str(record.project_dir),
                    code=OWNERSHIP_ISSUE_ORPHANED_OWNER,
                    message="项目 owner_id 指向不存在的用户",
                    owner_id=record.owner_id,
                )
            )
            continue
        owned_projects += 1

    missing_owner_projects = sum(
        1
        for issue in issues
        if issue.code in {OWNERSHIP_ISSUE_MISSING_COLUMN, OWNERSHIP_ISSUE_MISSING_OWNER}
    )
    orphaned_owner_projects = sum(1 for issue in issues if issue.code == OWNERSHIP_ISSUE_ORPHANED_OWNER)
    projects_missing_owner_column = sum(1 for issue in issues if issue.code == OWNERSHIP_ISSUE_MISSING_COLUMN)
    return OwnershipVerifyResult(
        total_projects=len(records),
        owned_projects=owned_projects,
        missing_owner_projects=missing_owner_projects,
        orphaned_owner_projects=orphaned_owner_projects,
        projects_missing_owner_column=projects_missing_owner_column,
        ready_for_phase_c=missing_owner_projects == 0 and orphaned_owner_projects == 0,
        issues=issues,
    )


def list_project_ownership_records(store: ProjectStore) -> list[ProjectOwnershipRecord]:
    records: list[ProjectOwnershipRecord] = []
    for db_path in store.projects_root.glob("*/project.db"):
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
            row = conn.execute("SELECT * FROM project_meta LIMIT 1").fetchone()
            if row is None:
                continue
            data = dict(row)
            if data.get("status") == "internal":
                continue
        records.append(
            ProjectOwnershipRecord(
                project_id=str(data["project_id"]),
                project_dir=db_path.parent,
                has_owner_column="owner_id" in columns,
                owner_id=str(data.get("owner_id") or "").strip() if "owner_id" in columns else None,
            )
        )
    return sorted(records, key=lambda record: record.project_id)


def build_assignment_plan(
    *,
    store: ProjectStore,
    auth_store: AuthStore,
    owner_email: str | None = None,
    owner_user_id: str | None = None,
    mapping_file: Path | None = None,
) -> MigrationPlan:
    records = {record.project_id: record for record in list_project_ownership_records(store)}
    errors: list[str] = []
    actions: list[MigrationAction] = []
    assignments: dict[str, str] = {}

    if mapping_file:
        assignments.update(_load_mapping_file(mapping_file, auth_store, records, errors))
    else:
        resolved_owner = _resolve_cli_owner(auth_store, owner_email=owner_email, owner_user_id=owner_user_id, errors=errors)
        if resolved_owner:
            for record in records.values():
                if record.owner_id:
                    actions.append(
                        MigrationAction(
                            project_id=record.project_id,
                            project_dir=str(record.project_dir),
                            owner_id=record.owner_id,
                            skipped_existing_owner=True,
                        )
                    )
                else:
                    assignments[record.project_id] = resolved_owner
        elif not errors:
            errors.append("PROJECT_OWNER_REQUIRED: --owner-email, --owner-user-id or --mapping-file is required")

    if mapping_file:
        for project_id, target_owner_id in assignments.items():
            record = records.get(project_id)
            if record is None:
                continue
            if record.owner_id:
                actions.append(
                    MigrationAction(
                        project_id=project_id,
                        project_dir=str(record.project_dir),
                        owner_id=record.owner_id,
                        skipped_existing_owner=True,
                    )
                )
            else:
                actions.append(
                    MigrationAction(
                        project_id=project_id,
                        project_dir=str(record.project_dir),
                        owner_id=target_owner_id,
                    )
                )
    else:
        for project_id, target_owner_id in assignments.items():
            record = records[project_id]
            actions.append(
                MigrationAction(
                    project_id=project_id,
                    project_dir=str(record.project_dir),
                    owner_id=target_owner_id,
                )
            )

    skipped_count = sum(1 for action in actions if action.skipped_existing_owner)
    return MigrationPlan(
        actions=actions,
        errors=errors,
        planned_count=len(actions),
        skipped_existing_owner_count=skipped_count,
    )


def apply_assignment_plan(plan: MigrationPlan) -> MigrationResult:
    if plan.errors:
        return MigrationResult(
            planned_count=plan.planned_count,
            written_count=0,
            skipped_existing_owner_count=plan.skipped_existing_owner_count,
            failed_count=0,
            errors=plan.errors,
        )

    written_count = 0
    errors: list[str] = []
    for action in plan.actions:
        if action.skipped_existing_owner:
            continue
        try:
            with sqlite3.connect(Path(action.project_dir) / "project.db") as conn:
                _ensure_owner_column(conn)
                cursor = conn.execute(
                    """
                    UPDATE project_meta
                    SET owner_id = ?
                    WHERE project_id = ? AND (owner_id IS NULL OR owner_id = '')
                    """,
                    (action.owner_id, action.project_id),
                )
                if cursor.rowcount:
                    written_count += 1
        except sqlite3.Error as exc:
            errors.append(f"{action.project_id}: {exc}")

    return MigrationResult(
        planned_count=plan.planned_count,
        written_count=written_count,
        skipped_existing_owner_count=plan.skipped_existing_owner_count,
        failed_count=len(errors),
        errors=errors,
    )


def _load_mapping_file(
    mapping_file: Path,
    auth_store: AuthStore,
    records: dict[str, ProjectOwnershipRecord],
    errors: list[str],
) -> dict[str, str]:
    try:
        payload = json.loads(mapping_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"MAPPING_FILE_INVALID: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append("MAPPING_FILE_INVALID: root must be an object")
        return {}

    assignments: dict[str, str] = {}
    for project_id, owner_spec in payload.items():
        project_id = str(project_id)
        if project_id not in records:
            errors.append(f"MAPPING_PROJECT_NOT_FOUND: {project_id}")
            continue
        owner_id = _owner_id_from_mapping_spec(auth_store, owner_spec, errors, project_id)
        if owner_id:
            assignments[project_id] = owner_id
    return assignments


def _owner_id_from_mapping_spec(
    auth_store: AuthStore,
    owner_spec: Any,
    errors: list[str],
    project_id: str,
) -> str | None:
    owner_email: str | None = None
    owner_user_id: str | None = None
    if isinstance(owner_spec, str):
        if owner_spec.startswith("user_"):
            owner_user_id = owner_spec
        else:
            owner_email = owner_spec
    elif isinstance(owner_spec, dict):
        owner_email = owner_spec.get("owner_email")
        owner_user_id = owner_spec.get("owner_user_id")
    else:
        errors.append(f"MAPPING_ENTRY_INVALID: {project_id}")
        return None
    return _resolve_cli_owner(auth_store, owner_email=owner_email, owner_user_id=owner_user_id, errors=errors)


def _resolve_cli_owner(
    auth_store: AuthStore,
    *,
    owner_email: str | None,
    owner_user_id: str | None,
    errors: list[str],
) -> str | None:
    if owner_email and owner_user_id:
        errors.append("PROJECT_OWNER_AMBIGUOUS: specify owner email or owner user id, not both")
        return None
    if owner_email:
        user = auth_store.get_user_by_email(normalize_email(owner_email))
        if not user:
            errors.append(f"PROJECT_OWNER_NOT_FOUND: {owner_email}")
            return None
        return str(user["user_id"])
    if owner_user_id:
        user = auth_store.get_user_by_id(str(owner_user_id))
        if not user:
            errors.append(f"PROJECT_OWNER_NOT_FOUND: {owner_user_id}")
            return None
        return str(user["user_id"])
    return None


def _ensure_owner_column(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(project_meta)").fetchall()}
    if "owner_id" not in columns:
        conn.execute("ALTER TABLE project_meta ADD COLUMN owner_id TEXT")
