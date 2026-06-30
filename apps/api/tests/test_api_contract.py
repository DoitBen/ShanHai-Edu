from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import enable_project_creation_fallback
from app.workflow_config import WorkflowConfig
from app.settings import Settings
from app.workflow_config import WorkflowConfig


def make_client(tmp_path: Path, overrides: dict | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            **(overrides or {}),
        }
    )
    return enable_project_creation_fallback(TestClient(app))


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def project_payload(**overrides):
    return {
        "name": "契约测试项目",
        "subject": "math",
        "grade": "3",
        "textbook_version": "renjiao",
        "volume": "xia",
        "lesson_type": "public",
        **overrides,
    }


def test_cors_uses_configured_allowlist(tmp_path: Path):
    client = make_client(tmp_path, {"cors_origins": "http://allowed.local"})

    allowed = client.options(
        "/projects",
        headers={"Origin": "http://allowed.local", "Access-Control-Request-Method": "GET"},
    )
    blocked = client.options(
        "/projects",
        headers={"Origin": "http://blocked.local", "Access-Control-Request-Method": "GET"},
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://allowed.local"
    assert blocked.headers.get("access-control-allow-origin") is None


def test_project_api_requires_session_even_when_token_is_configured(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    client.cookies.clear()
    client.headers.clear()

    response = client.get("/projects")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_project_api_rejects_token_only_project_reads(tmp_path: Path):
    client = make_client(tmp_path, {"backend_api_token": "dev-token"})
    client.cookies.clear()
    client.headers.clear()

    response = client.get("/projects", headers={"Authorization": "Bearer dev-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_create_project_uses_pydantic_validation(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post("/projects", json={"name": "缺字段项目"})

    assert response.status_code == 422
    assert response.json()["ok"] is False
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_node_edit_requires_content_object(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(client.post("/projects", json=project_payload()))

    response = client.post(
        f"/projects/{project['project_id']}/nodes/project_config/edit",
        json={"bad": "payload"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_workflow_runtime_nodes_include_yaml_nodes_and_textbook_bridge():
    workflow = WorkflowConfig(Path(__file__).resolve().parents[3] / "workflow")

    runtime_ids = workflow.runtime_node_ids()
    dependencies = workflow.runtime_dependencies()

    assert "lesson_plan" in workflow.node_ids()
    assert "final_delivery" in workflow.node_ids()
    assert "textbook_parse" in runtime_ids
    assert "lesson_plan" in runtime_ids
    assert dependencies["intro_video_script"] == ["intro_selection", "lesson_plan"]
    assert dependencies["lesson_plan"] == ["textbook_parse"]


def test_workflow_runtime_nodes_are_selected_by_yaml_runtime_flags(tmp_path: Path):
    workflow_root = tmp_path / "workflow"
    shutil.copytree(Path(__file__).resolve().parents[3] / "workflow", workflow_root)
    workflow_path = workflow_root / "workflow.yaml"
    text = workflow_path.read_text(encoding="utf-8")
    text = text.replace(
        "  - id: pptx_artifact\n    runtime_enabled: true",
        "  - id: pptx_artifact\n    runtime_enabled: false",
    )
    workflow_path.write_text(text, encoding="utf-8")

    workflow = WorkflowConfig(workflow_root)

    assert "pptx_artifact" not in workflow.runtime_node_ids()
    assert "pptx_artifact" not in workflow.runtime_dependencies()
    assert "pptx_artifact" in workflow.node_ids()


def test_workflow_config_no_longer_uses_python_mvp_runtime_constants():
    source = (Path(__file__).resolve().parents[1] / "app" / "workflow_config.py").read_text(encoding="utf-8")
    forbidden_names = [
        "MVP" + "_RUNTIME_NODE_IDS",
        "MVP" + "_NODE_IDS",
        "MVP" + "_DEPENDENCIES",
    ]

    for name in forbidden_names:
        assert name not in source


def test_environment_variables_override_local_env_files(tmp_path: Path, monkeypatch):
    env_dir = tmp_path / "apps" / "api"
    env_dir.mkdir(parents=True)
    (env_dir / ".env").write_text(
        "PROVIDER_MODE=minimax\nBACKEND_API_TOKEN=file-token\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PROVIDER_MODE", "fake")
    monkeypatch.setenv("BACKEND_API_TOKEN", "")

    settings = Settings.from_overrides()

    assert settings.provider_mode == "fake"
    assert settings.backend_api_token == ""


def test_real_text_provider_with_placeholder_video_mode_does_not_initialize_octo(tmp_path: Path):
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "real",
            "video_provider_mode": "placeholder",
            "deepseek_api_key": "test-deepseek-token",
        }
    )

    assert app.state.settings.provider_mode == "real"
    assert app.state.settings.video_provider_mode == "placeholder"
    assert app.state.service.provider.name == "deepseek"
    assert app.state.service.video_provider is None
