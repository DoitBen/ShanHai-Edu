import argparse
import getpass
import sys
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Callable

from .auth_service import AuthService
from .auth_store import AuthStore
from .settings import Settings


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

    args = parser.parse_args(argv)
    storage_root = Path(args.storage_root)
    service = AuthService(
        AuthStore(storage_root / "auth.db"),
        Settings.from_overrides({"storage_root": str(storage_root)}),
    )

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


if __name__ == "__main__":
    raise SystemExit(main())
