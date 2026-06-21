from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class PromptTemplateMissing(FileNotFoundError):
    pass


class PromptVariableMissing(ValueError):
    pass


INCLUDE_RE = re.compile(r"{{\s*include\s+([^}]+?)\s*}}")
VARIABLE_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


def template_path(prompt_root: Path, node_id: str, provider: str) -> Path:
    candidates = [
        prompt_root / node_id / f"{provider}.md",
        prompt_root / f"node_01_{node_id}" / f"{provider}.md",
        prompt_root / f"node_4b_{node_id}" / f"{provider}.md",
        prompt_root / f"node_06_{node_id}" / f"{provider}.md",
        prompt_root / f"node_08_{node_id}" / f"{provider}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise PromptTemplateMissing(f"未找到 prompt 模板：{node_id}@{provider}")


def render_prompt_file(prompt_root: Path, node_id: str, provider: str, context: dict[str, Any]) -> str:
    return render_prompt_body(load_prompt_body(prompt_root, node_id, provider), context)


def load_prompt_body(prompt_root: Path, node_id: str, provider: str) -> str:
    path = template_path(prompt_root, node_id, provider)
    return load_prompt_body_from_path(prompt_root, path)


def load_prompt_body_from_path(prompt_root: Path, path: Path) -> str:
    body = path.read_text(encoding="utf-8")
    return _expand_includes(prompt_root, body, seen={path.resolve()})


def render_prompt_body(body: str, context: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in context:
            raise PromptVariableMissing(f"prompt 缺少变量：{name}")
        value = context[name]
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        if value is None:
            return ""
        return str(value)

    return VARIABLE_RE.sub(replace, body)


def extract_variables(body: str) -> list[str]:
    without_includes = INCLUDE_RE.sub("", body)
    return sorted(set(VARIABLE_RE.findall(without_includes)))


def _expand_includes(prompt_root: Path, body: str, seen: set[Path]) -> str:
    def replace(match: re.Match[str]) -> str:
        rel = match.group(1).strip().replace("\\", "/")
        include_path = (prompt_root / rel).resolve()
        try:
            include_path.relative_to(prompt_root.resolve())
        except ValueError as exc:
            raise PromptTemplateMissing(f"include 路径越界：{rel}") from exc
        if include_path in seen:
            raise PromptTemplateMissing(f"include 循环引用：{rel}")
        if not include_path.exists():
            raise PromptTemplateMissing(f"include 文件不存在：{rel}")
        return _expand_includes(prompt_root, include_path.read_text(encoding="utf-8"), seen | {include_path})

    return INCLUDE_RE.sub(replace, body)
