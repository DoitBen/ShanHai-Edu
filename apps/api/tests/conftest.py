import sys
from pathlib import Path

from fastapi.testclient import TestClient


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

TEST_ORIGIN = "http://localhost:3000"


def allowed_origin(client: TestClient) -> str:
    settings = client.app.state.settings
    origins = getattr(settings, "cors_origin_list", None) or []
    return origins[0] if origins else TEST_ORIGIN


def enable_project_creation_fallback(client: TestClient) -> TestClient:
    """Test-only explicit fallback owner for legacy token/no-cookie project creation paths."""
    settings = client.app.state.settings
    if settings.project_creation_default_owner_user_id:
        user = client.app.state.auth_store.get_user_by_id(settings.project_creation_default_owner_user_id)
    else:
        user = client.app.state.auth_service.create_user(
            email="project-owner@example.com",
            display_name="Project Owner",
            role="admin",
            password="CorrectHorse123!",
        )
        settings.project_creation_default_owner_user_id = user["user_id"]
    if user:
        login_as(client, email=user["email"])
    return client


def create_auth_user(
    client: TestClient,
    *,
    email: str,
    password: str = "CorrectHorse123!",
    role: str = "teacher",
    display_name: str | None = None,
) -> dict:
    return client.app.state.auth_service.create_user(
        email=email,
        display_name=display_name or email.split("@", 1)[0],
        role=role,
        password=password,
    )


def login_as(
    client: TestClient,
    *,
    email: str,
    password: str = "CorrectHorse123!",
) -> dict:
    origin = allowed_origin(client)
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"Origin": origin},
    )
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    data = payload["data"]
    client.headers.update({"Origin": origin, "X-CSRF-Token": data["csrf_token"]})
    return data
