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
        ids = [node_id for node_id in self.node_ids() if node_id in MVP_RUNTIME_NODE_IDS]
        for bridge_node in MVP_BRIDGE_NODE_IDS:
            if bridge_node not in ids:
                insert_at = ids.index("lesson_plan") if "lesson_plan" in ids else len(ids)
                ids.insert(insert_at, bridge_node)
        return ids

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
        dependencies["textbook_parse"] = ["project_meta"]
        if "lesson_plan" in dependencies:
            dependencies["lesson_plan"] = ["textbook_parse"]
        return dependencies

    def schema(self, schema_name: str) -> dict[str, Any]:
        path = self.schemas_dir / schema_name
        if not path.exists():
            raise FileNotFoundError(f"schema not found: {schema_name}")
        return json.loads(path.read_text(encoding="utf-8"))


MVP_BRIDGE_NODE_IDS = ["textbook_parse"]

MVP_RUNTIME_NODE_IDS = {
    "project_meta",
    "project_config",
    "visual_contract",
    "character_dict",
    "lesson_plan",
    "intro_selection",
    "ppt_assembly_plan",
    "ppt_page_script",
    "ppt_visual_asset",
    "pptx_artifact",
    "intro_video_script",
    "intro_video_screenplay",
    "intro_video_asset",
    "storyboard",
    "final_video",
}

MVP_NODE_IDS = [
    "project_meta",
    "project_config",
    "visual_contract",
    "character_dict",
    "textbook_parse",
    "lesson_plan",
    "intro_selection",
    "ppt_assembly_plan",
    "ppt_page_script",
    "ppt_visual_asset",
    "pptx_artifact",
    "intro_video_script",
    "intro_video_screenplay",
    "intro_video_asset",
    "storyboard",
    "final_video",
]

MVP_DEPENDENCIES: dict[str, list[str]] = {
    "project_meta": [],
    "project_config": ["project_meta"],
    "visual_contract": ["project_meta"],
    "character_dict": ["project_meta"],
    "textbook_parse": ["project_meta"],
    "lesson_plan": ["textbook_parse"],
    "intro_selection": ["lesson_plan"],
    "ppt_assembly_plan": ["lesson_plan"],
    "ppt_page_script": ["ppt_assembly_plan", "character_dict", "visual_contract"],
    "ppt_visual_asset": ["ppt_page_script", "character_dict", "visual_contract"],
    "pptx_artifact": ["ppt_page_script", "ppt_visual_asset"],
    "intro_video_script": ["intro_selection", "lesson_plan"],
    "intro_video_screenplay": ["intro_video_script"],
    "intro_video_asset": ["intro_video_screenplay"],
    "storyboard": ["intro_video_asset", "intro_video_screenplay"],
    "final_video": ["storyboard", "intro_video_script"],
}
