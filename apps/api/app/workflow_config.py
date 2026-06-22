import json
from pathlib import Path
from typing import Any

import yaml


class WorkflowConfig:
    def __init__(self, root: Path):
        self.root = root
        workflow_path = root / "workflow.yaml"
        if not workflow_path.exists():
            raise FileNotFoundError(f"workflow.yaml not found: {workflow_path}")
        self.workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        self.schemas_dir = root / "schemas"

    @property
    def version(self) -> str:
        return str(self.workflow.get("version", "unknown"))

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return list(self.workflow.get("nodes", []))

    def node_ids(self) -> list[str]:
        return [node["id"] for node in self.nodes]

    def runtime_node_ids(self) -> list[str]:
        return [node["id"] for node in self.nodes if node.get("runtime_enabled", True) is not False]

    def get_node(self, node_id: str) -> dict[str, Any]:
        for node in self.nodes:
            if node.get("id") == node_id:
                return node
        raise KeyError(f"Unknown workflow node: {node_id}")

    def runtime_dependencies(self) -> dict[str, list[str]]:
        dependencies: dict[str, list[str]] = {}
        node_ids = set(self.runtime_node_ids())
        for node in self.nodes:
            node_id = node.get("id")
            if node_id not in node_ids:
                continue
            deps = [dep for dep in node.get("depends_on", []) if dep in node_ids]
            dependencies[node_id] = deps
        return dependencies

    def schema(self, schema_name: str) -> dict[str, Any]:
        path = self.schemas_dir / schema_name
        if not path.exists():
            raise FileNotFoundError(f"schema not found: {schema_name}")
        return json.loads(path.read_text(encoding="utf-8"))
