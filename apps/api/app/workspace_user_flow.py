from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkspaceStepSpec:
    step_id: str
    title: str
    node_ids: tuple[str, ...]
    prerequisite_step_id: str | None
    goal: str
    user_todo: str
    result_empty: str
    result_ready: str


@dataclass(frozen=True)
class WorkspaceSubGateSpec:
    gate_id: str
    title: str
    canonical_node_id: str
    legacy_aliases: tuple[str, ...] = ()


WORKSPACE_STEPS: tuple[WorkspaceStepSpec, ...] = (
    WorkspaceStepSpec(
        "project_info",
        "项目信息",
        ("project_config",),
        None,
        "确认公开课项目的基本信息、视觉风格和角色安全要求。",
        "回看项目信息，如需调整请回到项目设置。",
        "项目信息已创建。",
        "项目信息已确认。",
    ),
    WorkspaceStepSpec(
        "textbook_content",
        "教材内容",
        ("textbook_parse",),
        "project_info",
        "确认本课使用的教材页段、知识点和教材结构化内容。",
        "生成或确认教材内容，确认后才能生成教案。",
        "还没有教材内容草稿。",
        "教材内容已生成，等待确认。",
    ),
    WorkspaceStepSpec(
        "lesson_plan",
        "教案生成",
        ("lesson_plan",),
        "textbook_content",
        "基于教材内容生成公开课教案，并确认教学目标和课堂流程。",
        "生成教案草稿，检查后确认进入导入视频方案。",
        "还没有教案草稿。",
        "已生成草稿，等待确认。",
    ),
    WorkspaceStepSpec(
        "intro_video_plan",
        "导入视频方案",
        ("intro_selection",),
        "lesson_plan",
        "选择导入视频创意，确认课程锚点和课堂接入方式。",
        "确认视频方案和课程锚点，准备进入视频文稿、剧本和分镜生成。",
        "还没有导入视频方案。",
        "导入视频方案已有草稿，等待确认。",
    ),
    WorkspaceStepSpec(
        "ppt_draft",
        "PPT 草稿",
        ("ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset", "pptx_artifact"),
        "intro_video_plan",
        "生成 PPT 结构、页面脚本、视觉资产和可下载课件草稿。",
        "确认 PPT 草稿是否符合公开课展示需要。",
        "还没有 PPT 草稿。",
        "PPT 草稿已有结果，等待确认。",
    ),
    WorkspaceStepSpec(
        "video_generation",
        "视频生成",
        ("intro_video_script", "intro_video_screenplay", "intro_video_asset", "storyboard", "final_video"),
        "ppt_draft",
        "生成导入视频文稿、分场剧本、资产首帧、分镜和最终合成结果。",
        "检查视频文稿、剧本、资产、分镜和 clip/TTS/合成状态。",
        "还没有生成视频。",
        "视频生成已有结果，等待确认。",
    ),
    WorkspaceStepSpec(
        "final_delivery",
        "最终交付",
        ("final_delivery",),
        "video_generation",
        "汇总教案、PPT 和视频，形成最终交付包。",
        "检查最终交付物并下载使用。",
        "还没有最终交付包。",
        "最终交付包已有结果，等待确认。",
    ),
)

PPT_SUB_GATES: tuple[WorkspaceSubGateSpec, ...] = (
    WorkspaceSubGateSpec("structure_plan", "结构方案", "ppt_assembly_plan"),
    WorkspaceSubGateSpec("page_script", "逐页脚本", "ppt_page_script"),
    WorkspaceSubGateSpec("visual_assets", "视觉资产", "ppt_visual_asset"),
    WorkspaceSubGateSpec("pptx_file", "PPTX 文件", "pptx_artifact", ("pptx-generation",)),
)

VIDEO_SUB_GATES: tuple[WorkspaceSubGateSpec, ...] = (
    WorkspaceSubGateSpec("script", "文稿", "intro_video_script"),
    WorkspaceSubGateSpec("screenplay", "分场剧本", "intro_video_screenplay", ("video-screenplay",)),
    WorkspaceSubGateSpec("assets_first_frame", "资产与首帧", "intro_video_asset"),
    WorkspaceSubGateSpec("storyboard", "分镜", "storyboard"),
    WorkspaceSubGateSpec("clip_tts_composition", "clip/TTS/合成", "final_video", ("video-generation", "video_clip_generation")),
)

COMPATIBILITY_ALIASES: dict[str, tuple[str, ...]] = {
    "lesson_plan": ("open-lesson-plan", "lesson-plan-final"),
    "pptx_artifact": ("pptx-generation",),
    "intro_video_screenplay": ("video-screenplay",),
    "final_video": ("video-generation", "video_clip_generation"),
    "final_delivery": ("final-delivery",),
}

PASSABLE_STATUSES = {"approved", "skipped"}
READY_STATUSES = {"needs_review", "drafted", "blocked"}


def build_workspace_user_flow(
    project: dict[str, Any],
    manifest: dict[str, Any],
    node_details: dict[str, dict[str, Any]],
    tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest_nodes = {node["node_id"]: node for node in manifest.get("nodes", [])}
    built_steps: dict[str, dict[str, Any]] = {}
    ordered_steps: list[dict[str, Any]] = []
    tasks = tasks or []
    direct_lesson = _is_direct_lesson_project(project)

    for index, spec in enumerate(WORKSPACE_STEPS, start=1):
        prerequisite = built_steps.get(spec.prerequisite_step_id or "")
        if direct_lesson and spec.step_id == "lesson_plan" and spec.prerequisite_step_id == "textbook_content":
            prerequisite = None
        locked = bool(prerequisite and prerequisite["state"] != "completed")
        node_statuses = [str((manifest_nodes.get(node_id) or {}).get("status") or "not_started") for node_id in spec.node_ids]
        has_result = any(bool((node_details.get(node_id) or {}).get("content")) for node_id in spec.node_ids)
        completed = bool(node_statuses) and all(status in PASSABLE_STATUSES for status in node_statuses)
        if direct_lesson and spec.step_id == "textbook_content":
            completed = True
        current = not locked and not completed

        if locked:
            state = "locked"
            lock_reason = _lock_reason(prerequisite, spec)
            user_action = _lock_action(prerequisite, spec)
        elif completed:
            state = "completed"
            lock_reason = None
            user_action = _completed_action(spec, direct_lesson)
        else:
            state = "current"
            lock_reason = None
            user_action = spec.user_todo

        primary_action = _primary_action(state, completed, has_result, spec)
        step = {
            "step_id": spec.step_id,
            "order": index,
            "title": spec.title,
            "state": state,
            "goal": spec.goal,
            "user_action": user_action,
            "current_action": user_action,
            "result": _result_summary(spec, node_statuses, has_result, direct_lesson),
            "primary_action": primary_action,
            "lock_reason": lock_reason,
            "review": _review_payload(spec, project, node_details) if state in {"completed", "current"} else None,
            "review_summary": _review_summary(spec, project, node_details) if state in {"completed", "current"} else "完成后可回看本步骤结果。",
            "sub_gates": _sub_gates(spec, manifest_nodes, node_details, tasks),
            "can_review": state in {"completed", "current"} and has_result,
            "can_modify": state == "current" and spec.step_id not in {"project_info", "final_delivery"},
        }
        built_steps[spec.step_id] = step
        ordered_steps.append(step)

    current_step = next((step for step in ordered_steps if step["state"] == "current"), None)
    return {
        "project": _project_summary(project),
        "steps": ordered_steps,
        "current_step_id": current_step["step_id"] if current_step else ordered_steps[-1]["step_id"],
        "developer_diagnostics": _developer_diagnostics(manifest_nodes, node_details),
    }


def _project_summary(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": project.get("project_id"),
        "name": project.get("name"),
        "subject": project.get("subject"),
        "grade": project.get("grade"),
        "textbook_version": project.get("textbook_version"),
        "volume": project.get("volume"),
        "lesson_type": project.get("lesson_type"),
        "textbook_id": project.get("textbook_id"),
        "textbook_version_id": project.get("textbook_version_id"),
        "knowledge_point_id": project.get("knowledge_point_id"),
        "reference_lesson_plan_id": project.get("reference_lesson_plan_id"),
        "lesson_plan_source": project.get("lesson_plan_source"),
    }


def _primary_action(state: str, completed: bool, has_result: bool, spec: WorkspaceStepSpec) -> dict[str, Any]:
    if state == "locked":
        return {"label": "暂未解锁", "enabled": False, "intent": "locked"}
    if completed:
        return {"label": "查看下一步", "enabled": True, "intent": "next"}
    if has_result:
        return {"label": "确认并进入下一步", "enabled": True, "intent": "approve"}
    return {"label": "生成草稿", "enabled": True, "intent": "generate"}


def _result_summary(spec: WorkspaceStepSpec, node_statuses: list[str], has_result: bool, direct_lesson: bool = False) -> dict[str, Any]:
    if direct_lesson and spec.step_id == "textbook_content":
        status_text = "已从已有教案导入，教材内容步骤已跳过。"
        has_result = True
    elif has_result:
        status_text = spec.result_ready
    elif any(status == "blocked" for status in node_statuses):
        status_text = "生成遇到问题，请按提示处理后重试。"
    else:
        status_text = spec.result_empty
    return {"status_text": status_text, "has_result": has_result}


def _completed_action(spec: WorkspaceStepSpec, direct_lesson: bool = False) -> str:
    if direct_lesson and spec.step_id == "textbook_content":
        return "本项目从教案开始，教材内容步骤已由教案导入替代。"
    return "可以回看本步骤内容，也可以继续下一步。"


def _lock_reason(prerequisite: dict[str, Any] | None, spec: WorkspaceStepSpec) -> str:
    if prerequisite:
        return f"请先确认【{prerequisite['title']}】后，再进入【{spec.title}】。"
    return "请先完成上一阶段。"


def _lock_action(prerequisite: dict[str, Any] | None, spec: WorkspaceStepSpec) -> str:
    if prerequisite:
        return f"请先确认【{prerequisite['title']}】后再进入【{spec.title}】。"
    return "请先完成上一阶段。"


def _review_payload(spec: WorkspaceStepSpec, project: dict[str, Any], node_details: dict[str, dict[str, Any]]) -> dict[str, Any]:
    contents = {node_id: (node_details.get(node_id) or {}).get("content") for node_id in spec.node_ids}
    if spec.step_id == "project_info":
        return {
            "summary": {
                "项目名称": project.get("name"),
                "年级": project.get("grade"),
                "教材版本": project.get("textbook_version"),
                "册次": project.get("volume"),
                "课型": project.get("lesson_type"),
            }
        }
    if spec.step_id == "textbook_content":
        if _is_direct_lesson_project(project):
            return {
                "summary": {
                    "来源": "已有教案",
                    "参考教案": project.get("reference_lesson_plan_id"),
                    "处理方式": "教材内容步骤已跳过",
                },
                "markdown": None,
            }
        content = contents.get("textbook_parse") or {}
        selected = content.get("selected_knowledge_point") if isinstance(content, dict) else {}
        markdown = selected.get("markdown") if isinstance(selected, dict) else None
        return {
            "summary": {
                "教材": content.get("textbook_meta", {}).get("title") if isinstance(content, dict) else None,
                "知识点": selected.get("title") if isinstance(selected, dict) else None,
                "教材页码": selected.get("textbook_pages") if isinstance(selected, dict) else None,
                "PDF页码": selected.get("pdf_pages") if isinstance(selected, dict) else None,
            },
            "markdown": markdown or content.get("textbook_markdown") if isinstance(content, dict) else None,
        }
    if spec.step_id == "lesson_plan":
        content = contents.get("lesson_plan") or {}
        return {
            "summary": {
                "来源知识点": content.get("source_knowledge_point_id") if isinstance(content, dict) else None,
                "参考教案": content.get("reference_lesson_plan_id") if isinstance(content, dict) else None,
            },
            "markdown": content.get("lesson_plan_markdown") if isinstance(content, dict) else None,
        }
    if spec.step_id == "ppt_draft":
        return {"summary": _plain_sub_gate_summary(PPT_SUB_GATES, node_details, [])}
    if spec.step_id == "video_generation":
        return {"summary": _plain_sub_gate_summary(VIDEO_SUB_GATES, node_details, [])}
    return {
        "summary": _summarize_contents(contents),
    }


def _review_summary(spec: WorkspaceStepSpec, project: dict[str, Any], node_details: dict[str, dict[str, Any]]) -> str:
    if spec.step_id == "ppt_draft":
        gates = _plain_sub_gate_summary(PPT_SUB_GATES, node_details, [])
        return "；".join(gates.values()) if gates else "完成后可回看 PPT 草稿。"
    if spec.step_id == "video_generation":
        gates = _plain_sub_gate_summary(VIDEO_SUB_GATES, node_details, [])
        return "；".join(gates.values()) if gates else "完成后可回看视频生成结果。"
    if spec.step_id == "project_info":
        return f"已创建项目《{project.get('name') or '未命名项目'}》。"
    review = _review_payload(spec, project, node_details)
    summary = review.get("summary") if isinstance(review, dict) else None
    if isinstance(summary, dict):
        values = [str(value) for value in summary.values() if value]
        if values:
            return "；".join(values[:3])
    if review.get("markdown") if isinstance(review, dict) else None:
        return "已形成可回看的 Markdown 内容。"
    return "完成后可回看本步骤结果。"


def _is_direct_lesson_project(project: dict[str, Any]) -> bool:
    source = str(project.get("lesson_plan_source") or "").strip().lower()
    if source in {"direct_lesson", "lesson_plan", "reference_lesson_plan", "existing_lesson_plan"}:
        return True
    direct_flag = project.get("direct_lesson")
    if isinstance(direct_flag, bool):
        return direct_flag
    if isinstance(direct_flag, int):
        return direct_flag == 1
    if isinstance(direct_flag, str) and direct_flag.strip().lower() in {"1", "true", "yes", "direct_lesson"}:
        return True
    return bool(str(project.get("reference_lesson_plan_id") or "").strip())


def _sub_gates(
    spec: WorkspaceStepSpec,
    manifest_nodes: dict[str, dict[str, Any]],
    node_details: dict[str, dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if spec.step_id == "ppt_draft":
        return [_build_sub_gate(gate, manifest_nodes, node_details, tasks) for gate in PPT_SUB_GATES]
    if spec.step_id == "video_generation":
        return [_build_sub_gate(gate, manifest_nodes, node_details, tasks) for gate in VIDEO_SUB_GATES]
    return []


def _plain_sub_gate_summary(
    gates: tuple[WorkspaceSubGateSpec, ...],
    node_details: dict[str, dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> dict[str, str]:
    summary: dict[str, str] = {}
    for gate in gates:
        content = (node_details.get(gate.canonical_node_id) or {}).get("content")
        text = _gate_review_summary(gate.gate_id, content, tasks)
        if text and not text.startswith("等待"):
            summary[gate.title] = text
    return summary


def _build_sub_gate(
    gate: WorkspaceSubGateSpec,
    manifest_nodes: dict[str, dict[str, Any]],
    node_details: dict[str, dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    status = str((manifest_nodes.get(gate.canonical_node_id) or {}).get("status") or "not_started")
    content = (node_details.get(gate.canonical_node_id) or {}).get("content")
    return {
        "gate_id": gate.gate_id,
        "title": gate.title,
        "state": _user_gate_state(status),
        "status_text": _gate_status_text(status),
        "review_summary": _gate_review_summary(gate.gate_id, content, tasks),
    }


def _user_gate_state(status: str) -> str:
    if status in PASSABLE_STATUSES:
        return "completed"
    if status in READY_STATUSES:
        return "current"
    return "locked"


def _gate_status_text(status: str) -> str:
    if status in PASSABLE_STATUSES:
        return "已完成"
    if status == "needs_review":
        return "待确认"
    if status == "drafted":
        return "已生成草稿"
    if status == "blocked":
        return "需要处理后重试"
    return "未开始"


def _gate_review_summary(gate_id: str, content: Any, tasks: list[dict[str, Any]]) -> str:
    content = content if isinstance(content, dict) else {}
    if gate_id == "structure_plan":
        page_count = content.get("page_count_target") or content.get("slide_count")
        if page_count:
            return f"已形成 {page_count} 页 PPT 结构方案。"
        return "等待形成 PPT 页数、结构模板和整体风格。"
    if gate_id == "page_script":
        pages = content.get("pages") if isinstance(content.get("pages"), list) else []
        if pages:
            return f"已形成 {len(pages)} 页逐页脚本。"
        return "等待形成逐页讲法、学生动作和页面内容。"
    if gate_id == "visual_assets":
        assets = content.get("assets") if isinstance(content.get("assets"), list) else []
        if assets:
            return f"已有 {len(assets)} 项视觉资产或占位素材。"
        return "等待形成 PPT 视觉资产清单。"
    if gate_id == "pptx_file":
        if content.get("pptx_path") or content.get("download_url"):
            return "已生成可下载 PPTX 文件。"
        return "等待生成可下载 PPTX 文件。"
    if gate_id == "script":
        duration = content.get("total_duration_sec")
        if duration:
            return f"已形成约 {duration} 秒导入视频文稿。"
        if content.get("narration_full_text"):
            return "已形成导入视频旁白文稿。"
        return "等待形成导入视频文稿。"
    if gate_id == "screenplay":
        scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
        if scenes:
            return f"已形成 {len(scenes)} 个分场剧本。"
        return "等待形成分场剧本。"
    if gate_id == "assets_first_frame":
        assets = content.get("assets") if isinstance(content.get("assets"), list) else []
        if assets:
            return f"已有 {len(assets)} 项视频资产或首帧素材。"
        return "等待形成视频资产与首帧素材。"
    if gate_id == "storyboard":
        shots = content.get("shots") if isinstance(content.get("shots"), list) else []
        if shots:
            return f"已形成 {len(shots)} 个镜头分镜。"
        return "等待形成镜头级分镜。"
    if gate_id == "clip_tts_composition":
        clip_tasks = [task for task in tasks if task.get("node_id") == "final_video" and task.get("task_type") == "video_clip_generation"]
        tts_tasks = [task for task in tasks if task.get("node_id") == "final_video" and "tts" in str(task.get("task_type") or "").lower()]
        completed_clips = sum(1 for task in clip_tasks if task.get("status") == "completed")
        clip_count = content.get("clip_count") if isinstance(content.get("clip_count"), int) else None
        total_clips = max(len(clip_tasks), clip_count or 0)
        parts = []
        if total_clips:
            parts.append(f"clip {completed_clips}/{total_clips}")
        if tts_tasks:
            parts.append(f"TTS {len(tts_tasks)} 项")
        if content.get("video_path"):
            parts.append("合成文件已记录")
        return "；".join(parts) if parts else "等待 clip、TTS 和最终合成。"
    return "等待形成本子门禁结果。"


def _summarize_contents(contents: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for node_id, content in contents.items():
        if not isinstance(content, dict):
            continue
        summary[node_id] = _safe_content_summary(content)
    return summary


def _safe_content_summary(content: dict[str, Any]) -> dict[str, Any]:
    preferred_keys = [
        "title",
        "selected_title",
        "selected_anchor",
        "page_count_target",
        "slide_count",
        "clip_count",
        "download_url",
        "video_path",
        "pptx_path",
        "lesson_plan_path",
        "pptx_final_path",
        "video_final_path",
    ]
    result = {key: content[key] for key in preferred_keys if content.get(key) is not None}
    if not result:
        result["状态"] = "已有内容"
    return result


def _developer_diagnostics(manifest_nodes: dict[str, dict[str, Any]], node_details: dict[str, dict[str, Any]]) -> dict[str, Any]:
    steps: dict[str, Any] = {}
    for spec in WORKSPACE_STEPS:
        nodes = []
        for node_id in spec.node_ids:
            manifest_node = manifest_nodes.get(node_id) or {}
            detail = node_details.get(node_id) or {}
            nodes.append(
                {
                    "node_id": node_id,
                    "status": manifest_node.get("status"),
                    "schema": manifest_node.get("schema"),
                    "depends_on": manifest_node.get("depends_on") or [],
                    "capabilities": manifest_node.get("capabilities") or {},
                    "rule_summary": manifest_node.get("rule_summary") or {},
                    "latest_transition": manifest_node.get("latest_transition") or detail.get("latest_transition"),
                    "review_reason": manifest_node.get("review_reason") or detail.get("review_reason"),
                    "artifact": manifest_node.get("artifact"),
                }
            )
        steps[spec.step_id] = {
            "node_ids": list(spec.node_ids),
            "compatibility_aliases": {
                node_id: list(COMPATIBILITY_ALIASES.get(node_id, ()))
                for node_id in spec.node_ids
                if COMPATIBILITY_ALIASES.get(node_id)
            },
            "nodes": nodes,
        }
    return {
        "title": "开发诊断",
        "default_collapsed": True,
        "steps": steps,
    }
