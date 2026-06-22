import re
from pathlib import Path

from app.providers import sanitize_provider_excerpt


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_frontend_source_does_not_depend_on_public_api_token():
    public_api_token_name = "NEXT_PUBLIC" + "_API_TOKEN"
    frontend_files = [
        *list((REPO_ROOT / "apps" / "web" / "src").rglob("*.ts")),
        *list((REPO_ROOT / "apps" / "web" / "src").rglob("*.tsx")),
    ]

    offenders = []
    for path in frontend_files:
        text = path.read_text(encoding="utf-8")
        if public_api_token_name in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_ops_runbook_uses_server_side_backend_proxy_token_language():
    runbook = REPO_ROOT / "docs" / "ops-runbook-draft.md"
    text = runbook.read_text(encoding="utf-8")
    public_api_token_name = "NEXT_PUBLIC" + "_API_TOKEN"

    assert public_api_token_name not in text
    assert "/api/backend" in text
    assert "BACKEND_API_TOKEN" in text


def test_frontend_source_does_not_expose_public_secret_like_env_names():
    pattern = re.compile(r"NEXT_PUBLIC_[A-Z0-9_]*(?:KEY|TOKEN|SECRET)[A-Z0-9_]*")
    frontend_files = [
        *list((REPO_ROOT / "apps" / "web" / "src").rglob("*.ts")),
        *list((REPO_ROOT / "apps" / "web" / "src").rglob("*.tsx")),
    ]

    matches = {}
    for path in frontend_files:
        found = sorted(set(pattern.findall(path.read_text(encoding="utf-8"))))
        if found:
            matches[str(path.relative_to(REPO_ROOT))] = found

    assert matches == {}


def test_provider_excerpt_redacts_authorization_and_key_material():
    raw = (
        "Authorization: Bearer sk-secret123456789 "
        "api_key=octo-secret123456789 token: deepseek-secret123456789 "
        "plain text remains"
    )

    redacted = sanitize_provider_excerpt(raw)

    assert "sk-secret123456789" not in redacted
    assert "octo-secret123456789" not in redacted
    assert "deepseek-secret123456789" not in redacted
    assert "Bearer <redacted>" in redacted
    assert "api_key=<redacted>" in redacted
    assert "token: <redacted>" in redacted
    assert "plain text remains" in redacted


def test_api_env_example_contains_only_placeholders_for_secret_like_values():
    env_example = REPO_ROOT / "apps" / "api" / ".env.example"
    text = env_example.read_text(encoding="utf-8")
    violations = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if any(marker in key.upper() for marker in ["KEY", "TOKEN", "SECRET"]):
            if value and not (value.startswith("<") and value.endswith(">")):
                violations.append(key)

    assert violations == []
