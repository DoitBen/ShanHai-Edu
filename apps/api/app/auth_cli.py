import argparse
import getpass
import json
import sys
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Any, Callable

from .auth_service import AuthService
from .auth_store import AuthStore
from .project_ownership import apply_assignment_plan, build_assignment_plan, scan_project_ownership
from .settings import Settings
from .store import ProjectStore


MIN_PASSWORD_LENGTH = 12


def main(argv: list[str] | None = None, getpass_func: Callable[[str], str] = getpass.getpass) -> int:
    parser = argparse.ArgumentParser(prog="auth-cli")
    parser.add_argument("--storage-root", default="storage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-user")
    create.add_argument("--email", required=True)
    create.add_argument("--display-name", required=True)
    create.add_argument("--role", choices=["admin", "teacher"], required=True)

    set_password = subparsers.add_parser("set-password")
    set_password.add_argument("--email", required=True)

    disable = subparsers.add_parser("disable-user")
    disable.add_argument("--email", required=True)

    enable = subparsers.add_parser("enable-user")
    enable.add_argument("--email", required=True)

    subparsers.add_parser("list-users")

    verify_ownership = subparsers.add_parser("verify-project-ownership")
    verify_ownership.add_argument("--json", action="store_true")

    assign_legacy = subparsers.add_parser("assign-legacy-projects")
    assign_legacy.add_argument("--owner-email")
    assign_legacy.add_argument("--owner-user-id")
    assign_legacy.add_argument("--mapping-file")
    assign_legacy.add_argument("--apply", action="store_true")

    args = parser.parse_args(argv)
    storage_root = Path(args.storage_root)
    auth_store = AuthStore(storage_root / "auth.db")
    service = AuthService(
        auth_store,
        Settings.from_overrides({"storage_root": str(storage_root)}),
    )
    project_store = ProjectStore(storage_root)

    try:
        if args.command == "create-user":
            password = _read_new_password(getpass_func)
            service.create_user(
                email=args.email,
                display_name=args.display_name,
                role=args.role,
                password=password,
            )
            print(f"created {args.role}: {args.email}")
            return 0
        if args.command == "set-password":
            password = _read_new_password(getpass_func)
            service.set_password(args.email, password)
            print(f"password updated: {args.email}")
            return 0
        if args.command == "disable-user":
            service.disable_user(args.email)
            print(f"disabled: {args.email}")
            return 0
        if args.command == "enable-user":
            service.enable_user(args.email)
            print(f"enabled: {args.email}")
            return 0
        if args.command == "list-users":
            for user in service.store.list_users():
                status = "active" if int(user["is_active"]) == 1 else "disabled"
                print(f"{user['email']}\t{user['display_name']}\t{user['role']}\t{status}")
            return 0
        if args.command == "verify-project-ownership":
            result = scan_project_ownership(project_store, auth_store)
            if args.json:
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_ownership_verify(result.to_dict())
            return 0 if result.ready_for_phase_c else 1
        if args.command == "assign-legacy-projects":
            plan = build_assignment_plan(
                store=project_store,
                auth_store=auth_store,
                owner_email=args.owner_email,
                owner_user_id=args.owner_user_id,
                mapping_file=Path(args.mapping_file) if args.mapping_file else None,
            )
            if args.apply:
                result = apply_assignment_plan(plan)
            else:
                result = _dry_run_result(plan)
            for line in result.to_lines():
                print(line)
            return 0 if not result.errors and result.failed_count == 0 else 1
    except (IntegrityError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def _read_new_password(getpass_func: Callable[[str], str]) -> str:
    password = getpass_func("Password: ")
    confirm = getpass_func("Confirm password: ")
    if password != confirm:
        raise ValueError("passwords do not match")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("password must be at least 12 characters")
    return password


def _dry_run_result(plan) -> Any:
    return type("DryRunResult", (), {"to_lines": lambda _self: [
        f"planned_count={plan.planned_count}",
        "written_count=0",
        f"skipped_existing_owner_count={plan.skipped_existing_owner_count}",
        "failed_count=0",
        f"errors={json.dumps(plan.errors, ensure_ascii=False)}",
    ], "errors": plan.errors, "failed_count": 0})()


def _print_ownership_verify(result: dict) -> None:
    print(f"total_projects={result['total_projects']}")
    print(f"owned_projects={result['owned_projects']}")
    print(f"missing_owner_projects={result['missing_owner_projects']}")
    print(f"orphaned_owner_projects={result['orphaned_owner_projects']}")
    print(f"projects_missing_owner_column={result['projects_missing_owner_column']}")
    print(f"ready_for_phase_c={str(result['ready_for_phase_c']).lower()}")
    for issue in result["issues"]:
        print(f"{issue['code']}\t{issue['project_id']}\t{issue['project_dir']}")


if __name__ == "__main__":
    raise SystemExit(main())
