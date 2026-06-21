from pathlib import Path

import pytest

from app.prompt_loader import PromptTemplateMissing, PromptVariableMissing, render_prompt_file
from app.prompt_registry import PromptRegistry, PromptStore


def test_prompt_loader_renders_markdown_with_includes_and_variables(tmp_path: Path):
    root = tmp_path / "workflow" / "prompts"
    (root / "shared").mkdir(parents=True)
    (root / "node_01_lesson_plan").mkdir(parents=True)
    (root / "shared" / "system_role.md").write_text("系统角色：{{role}}\n", encoding="utf-8")
    (root / "node_01_lesson_plan" / "deepseek.md").write_text(
        "{{include shared/system_role.md}}\n课题：{{lesson_title}}\n",
        encoding="utf-8",
    )

    rendered = render_prompt_file(
        root,
        "node_01_lesson_plan",
        "deepseek",
        {"role": "小学数学教案专家", "lesson_title": "5以内数的认识"},
    )

    assert "系统角色：小学数学教案专家" in rendered
    assert "课题：5以内数的认识" in rendered
    assert "{{" not in rendered


def test_prompt_loader_reports_missing_variable(tmp_path: Path):
    root = tmp_path / "workflow" / "prompts"
    (root / "lesson_plan").mkdir(parents=True)
    (root / "lesson_plan" / "deepseek.md").write_text("课题：{{lesson_title}}", encoding="utf-8")

    with pytest.raises(PromptVariableMissing) as exc:
        render_prompt_file(root, "lesson_plan", "deepseek", {})

    assert "lesson_title" in str(exc.value)


def test_prompt_loader_reports_missing_template(tmp_path: Path):
    with pytest.raises(PromptTemplateMissing):
        render_prompt_file(tmp_path / "prompts", "lesson_plan", "deepseek", {})


def test_prompt_registry_seed_is_idempotent_and_active_version_is_unique(tmp_path: Path):
    prompt_root = tmp_path / "workflow" / "prompts"
    (prompt_root / "lesson_plan").mkdir(parents=True)
    (prompt_root / "lesson_plan" / "deepseek.md").write_text("版本1：{{lesson_title}}", encoding="utf-8")
    db_path = tmp_path / "prompt_registry.db"
    store = PromptStore(db_path)
    registry = PromptRegistry(store, prompt_root, cache_ttl_seconds=0)

    registry.ensure_seeded(created_by="seed")
    registry.ensure_seeded(created_by="seed")

    templates = store.list_templates()
    assert len(templates) == 1
    versions = store.list_versions("lesson_plan@deepseek")
    assert len(versions) == 1
    assert versions[0]["status"] == "active"

    version2 = store.create_version(
        template_id="lesson_plan@deepseek",
        body="版本2：{{lesson_title}}",
        variables=["lesson_title"],
        status="active",
        created_by="admin",
        notes="测试发布",
    )
    active = store.active_version("lesson_plan", "deepseek")

    assert active["version_id"] == version2["version_id"]
    assert [item["status"] for item in store.list_versions("lesson_plan@deepseek")].count("active") == 1


def test_prompt_registry_canary_routes_stably_by_project(tmp_path: Path):
    prompt_root = tmp_path / "workflow" / "prompts"
    (prompt_root / "storyboard").mkdir(parents=True)
    (prompt_root / "storyboard" / "deepseek.md").write_text("active {{project_id}}", encoding="utf-8")
    store = PromptStore(tmp_path / "prompt_registry.db")
    registry = PromptRegistry(store, prompt_root, cache_ttl_seconds=0)
    registry.ensure_seeded(created_by="seed")
    store.create_version(
        template_id="storyboard@deepseek",
        body="canary {{project_id}}",
        variables=["project_id"],
        status="canary",
        canary_percent=100,
        created_by="admin",
        notes="灰度",
    )

    first = registry.render("storyboard", "deepseek", {"project_id": "proj_a"}, route_key="proj_a")
    second = registry.render("storyboard", "deepseek", {"project_id": "proj_a"}, route_key="proj_a")

    assert first == "canary proj_a"
    assert second == first
