from __future__ import annotations

import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Iterator

import uvicorn


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

PHASE_E_USERS = [
    {
        "email": "phase-e-teacher-a@example.test",
        "display_name": "Phase E Teacher A",
        "role": "teacher",
    },
    {
        "email": "phase-e-teacher-b@example.test",
        "display_name": "Phase E Teacher B",
        "role": "teacher",
    },
    {
        "email": "phase-e-admin@example.test",
        "display_name": "Phase E Admin",
        "role": "admin",
    },
]
PHASE_E_PASSWORD = "CorrectHorse123!"


@contextmanager
def _storage_root() -> Iterator[Path]:
    configured = os.environ.get("PHASE_E_FULLSTACK_STORAGE_ROOT")
    if configured:
        root = Path(configured).resolve()
        root.mkdir(parents=True, exist_ok=True)
        yield root
        return

    with tempfile.TemporaryDirectory(prefix="shanhai-phase-e-fullstack-") as tmp:
        root = Path(tmp) / "storage"
        root.mkdir(parents=True, exist_ok=True)
        yield root


def _configure_environment(storage_root: Path) -> None:
    os.environ["STORAGE_ROOT"] = str(storage_root)
    os.environ.setdefault("WORKFLOW_ROOT", str(REPO_ROOT / "workflow"))
    os.environ.setdefault("PROVIDER_MODE", "fake")
    os.environ.setdefault("VIDEO_PROVIDER_MODE", "placeholder")
    os.environ.setdefault("IMAGE_PROVIDER_MODE", "placeholder")
    os.environ.setdefault("TTS_PROVIDER_MODE", "placeholder")
    os.environ.setdefault("AUTH_COOKIE_SECURE", "false")
    os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")


def _seed_users(app) -> None:
    for user in PHASE_E_USERS:
        if app.state.auth_store.get_user_by_email(user["email"]):
            continue
        try:
            app.state.auth_service.create_user(
                email=user["email"],
                display_name=user["display_name"],
                role=user["role"],
                password=PHASE_E_PASSWORD,
            )
        except IntegrityError:
            continue


def main() -> None:
    with _storage_root() as storage_root:
        _configure_environment(storage_root)
        from app.main import create_app

        app = create_app()
        _seed_users(app)
        uvicorn.run(
            app,
            host=os.environ.get("PHASE_E_API_HOST", "127.0.0.1"),
            port=int(os.environ.get("PHASE_E_API_PORT", "8000")),
            log_level=os.environ.get("PHASE_E_API_LOG_LEVEL", "warning"),
        )


if __name__ == "__main__":
    main()
