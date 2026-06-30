import sys
from pathlib import Path

from fastapi.testclient import TestClient


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def enable_project_creation_fallback(client: TestClient) -> TestClient:
    """Test-only explicit fallback owner for legacy token/no-cookie project creation paths."""
    settings = client.app.state.settings
    if settings.project_creation_default_owner_user_id:
        return client
    user = client.app.state.auth_service.create_user(
        email="project-owner@example.com",
        display_name="Project Owner",
        role="teacher",
        password="CorrectHorse123!",
    )
    settings.project_creation_default_owner_user_id = user["user_id"]
    return client
