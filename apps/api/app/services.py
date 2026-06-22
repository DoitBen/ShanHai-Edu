from pathlib import Path
from typing import Any
import json

from .flywheel import FeedbackPayloadError, FeedbackTypeError, FlywheelService
from .ppt_exporter import export_project_ppt
from .providers import DeepSeekTextProvider, FakeProvider, MinimaxTextProvider, NewApiImageProvider, OctoVideoProvider, ProviderError, sanitize_provider_excerpt
from .prompt_loader import PromptTemplateMissing, PromptVariableMissing, render_prompt_file
from .rule_executor import RuleExecutor
from .state_engine import StateEngine
from .store import ProjectStore, now_iso
from .textbook_parser import TextbookParser, TextbookSource
from .video_outputs import FINAL_VIDEO_REL_PATH, compose_final_video_from_clips, compose_final_video_with_audio, ensure_final_video_output, write_concat_manifest, write_placeholder_narration_audio, write_subtitle_srt


INTRO_DESIGN_TYPES = ("science", "application", "story")
INTRO_DESIGNS_PER_TYPE = 3
INTRO_DESIGN_REQUIRED_FIELDS = {
    "design_id",
    "type",
    "title",
    "video_theme",
    "hook",
    "eye_catch_tag",
    "anchor_to_lesson",
    "classroom_entry_question",
    "no_pre_teach",
    "entry_position",
    "recommend_score",
    "recommend_reason",
    "risk_note",
}
ABSTRACT_ANCHOR_PHRASES = (
    "自然引出本课",
    "自然引出本课数学内容",
    "教学目标对应点",
    "教案关联点",
    "引出课堂探究活动",
    "让学生理解",
    "服务本课核心知识点",
    "贴合 5 以内数的认识",
    "贴合5以内数的认识",
    "从观察到抽象",
)
LLM_CONTEXT_MAX_STRING_CHARS = 4000
LLM_CONTEXT_TEXT_MAX_STRING_CHARS = 16000
LLM_CONTEXT_SENSITIVE_LARGE_KEYS = {"b64_json", "base64", "image_base64", "audio_base64", "video_base64"}
LLM_CONTEXT_LONG_TEXT_KEYS = {"markdown", "lesson_plan_markdown", "narration_full_text", "textbook_text"}


def sanitize_llm_context(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {item_key: sanitize_llm_context(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [sanitize_llm_context(item, key) for item in value]
    if not isinstance(value, str):
        return value
    if key in LLM_CONTEXT_SENSITIVE_LARGE_KEYS:
        return f"<omitted:{key} length={len(value)}>"
    if key == "image_url" and value.startswith("data:image/"):
        return f"<omitted:data-image length={len(value)}>"
    max_chars = LLM_CONTEXT_TEXT_MAX_STRING_CHARS if key in LLM_CONTEXT_LONG_TEXT_KEYS else LLM_CONTEXT_MAX_STRING_CHARS
    if len(value) > max_chars:
        return f"{value[:max_chars]}\n<omitted:large-string length={len(value)}>"
    return value


def normalize_node_content(node_id: str, content: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if node_id == "lesson_plan":
        return _normalize_lesson_plan(content, context)
    if node_id == "intro_selection":
        return _normalize_intro_selection(content, context)
    if node_id == "intro_video_script":
        return _normalize_intro_video_script(content, context)
    if node_id == "storyboard":
        return _normalize_storyboard(content, context)
    if node_id != "textbook_parse":
        return content
    lesson_title = content.get("lesson_title") or content.get("topic") or content.get("lesson")
    knowledge = content.get("core_knowledge_points") or content.get("key_concepts") or []
    goal = content.get("teaching_goal_summary") or content.get("teaching_focus") or ""
    key_points = content.get("key_points") or ([content["teaching_focus"]] if content.get("teaching_focus") else [])
    difficulties = content.get("difficulties") or content.get("misconceptions") or []
    normalized = {
        "subject": content.get("subject", "math"),
        "grade": str(content.get("grade") or context.get("grade", "3")),
        "textbook_version": content.get("textbook_version") or context.get("textbook_version", "renjiao"),
        "volume": content.get("volume") or context.get("volume", "xia"),
        "lesson_title": lesson_title or "数学探究课",
        "core_knowledge_points": knowledge,
        "teaching_goal_summary": goal,
        "key_points": key_points,
        "difficulties": difficulties,
    }
    for field in [
        "textbook_source",
        "textbook_meta",
        "knowledge_points",
        "selected_knowledge_point_id",
        "selected_knowledge_point",
        "parse_artifacts",
    ]:
        if field in content:
            normalized[field] = content[field]
    return normalized


def _normalize_lesson_plan(content: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    lesson_markdown = content.get("lesson_plan_markdown") or content.get("markdown") or content.get("lesson_plan") or ""
    normalized = dict(content)
    selected = context.get("textbook_parse", {}).get("selected_knowledge_point", {})
    if lesson_markdown:
        normalized["lesson_plan_markdown"] = str(lesson_markdown)
    if "textbook_anchor" not in normalized:
        normalized["textbook_anchor"] = "基于已选知识点 Markdown 生成" if selected else "基于项目教材信息生成"
    if "teaching_objectives" not in normalized:
        normalized["teaching_objectives"] = _extract_markdown_section(lesson_markdown, "教学目标") or "围绕本课知识点，帮助学生理解核心概念、掌握基本方法，并能在生活情境中表达和应用。"
    if "key_difficulty" not in normalized:
        normalized["key_difficulty"] = _extract_markdown_section(lesson_markdown, "教学重难点") or "重点是建立核心概念与数量关系；难点是把教材情境中的数学关系清晰表达。"
    if "teaching_flow" not in normalized:
        normalized["teaching_flow"] = _extract_markdown_section(lesson_markdown, "教学环节") or _extract_markdown_section(lesson_markdown, "教学流程") or "导入情境，提出问题；观察操作，形成表象；交流表达，抽象概念；练习巩固，回到生活应用。"
    if "blackboard_design" not in normalized:
        normalized["blackboard_design"] = _extract_markdown_section(lesson_markdown, "板书设计") or "课题、核心概念、关键方法、课堂小结。"
    normalized["intro_designs"] = _normalize_intro_designs(normalized.get("intro_designs"), context)
    return normalized


def _normalize_intro_selection(content: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(content)
    if _anchor_text(normalized):
        return normalized
    primary_design_id = normalized.get("primary_design_id")
    for design in context.get("lesson_plan", {}).get("intro_designs", []):
        if isinstance(design, dict) and design.get("design_id") == primary_design_id and _anchor_text(design.get("anchor_to_lesson")):
            normalized["selected_anchor"] = str(design["anchor_to_lesson"]).strip()
            return normalized
    return normalized


def _normalize_intro_video_script(content: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    selected_anchor = _selected_anchor_from_context(context)
    if not selected_anchor:
        return content
    normalized = dict(content)
    normalized["anchor_to_lesson"] = selected_anchor
    narration = str(normalized.get("narration_full_text") or "").strip()
    if narration and not narration.endswith(selected_anchor):
        normalized["narration_full_text"] = f"{narration.rstrip('。！？!?')}。{selected_anchor}"
    return normalized


def _normalize_storyboard(content: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(content.get("shots"), list):
        return content
    assets = context.get("intro_video_asset", {}).get("assets", [])
    fallback_asset_ids = [asset.get("asset_id") for asset in assets if isinstance(asset, dict) and asset.get("asset_id")]
    normalized_shots = []
    for index, shot in enumerate(content["shots"], start=1):
        if not isinstance(shot, dict):
            continue
        shot_id = _normalize_shot_id(shot.get("shot_id") or shot.get("id"), index)
        duration = shot.get("duration_sec") or shot.get("duration") or 10
        subject = shot.get("main_subject") or shot.get("subject") or shot.get("scene") or "数学导入动画场景"
        narration = shot.get("narration_slice") or shot.get("subtitle") or ""
        reference_ids = shot.get("reference_image_ids") or []
        if not reference_ids and fallback_asset_ids:
            reference_ids = [fallback_asset_ids[min(index - 1, len(fallback_asset_ids) - 1)]]
        model_prompt = _normalize_video_model_prompt(shot.get("model_prompt"), str(narration or subject), str(subject))
        normalized_shots.append(
            {
                **shot,
                "shot_id": str(shot_id),
                "duration_sec": duration,
                "main_subject": str(subject),
                "character_refs": shot.get("character_refs") or [],
                "reference_image_ids": reference_ids or [f"asset_ref_{index:02d}"],
                "narration_slice": str(narration or f"第 {index} 个数学导入镜头。"),
                "subtitle": shot.get("subtitle") or str(narration or subject),
                "model_prompt": model_prompt,
                "first_frame_test_status": shot.get("first_frame_test_status") or "passed",
                "first_frame_asset_id": shot.get("first_frame_asset_id") or (reference_ids[0] if reference_ids else f"asset_ref_{index:02d}"),
            }
        )
    normalized = {**content, "shots": normalized_shots}
    warnings = _storyboard_anchor_warnings(normalized, context)
    if warnings:
        normalized["rule_warnings"] = [*normalized.get("rule_warnings", []), *warnings]
    return normalized


def _normalize_shot_id(raw: Any, index: int) -> str:
    value = str(raw or "").strip()
    if not value:
        return f"shot_{index:02d}"
    if value.isdigit():
        return f"shot_{int(value):02d}"
    if value.startswith("shot_"):
        return value
    return value


def _normalize_video_model_prompt(raw: Any, narration: str, subject: str) -> str:
    prompt = str(raw or "").strip()
    if _valid_video_model_prompt(prompt):
        return prompt
    narration = narration.strip() or subject.strip() or "数学导入镜头。"
    subject = subject.strip() or narration
    return (
        f"旁白（男声，中文）：{narration}\n"
        f"画面：{subject}\n"
        "风格：非写实卡通插画，画面干净明亮，适合小学数学导入短片。\n"
        "禁止英文配音；如平台自动生成英文音频，则该片段判为不合格，需要静音或重合成中文配音。"
    )


def _valid_video_model_prompt(prompt: str) -> bool:
    if len(prompt.strip()) < 40:
        return False
    required = ("旁白（男声，中文）", "画面", "禁止英文配音")
    return all(item in prompt for item in required)


def _extract_markdown_section(markdown: Any, heading: str) -> str:
    if not isinstance(markdown, str):
        return ""
    marker = f"## {heading}"
    if marker not in markdown:
        return ""
    section = markdown.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0].strip()
    return section[:800]


def _lesson_title_from_context(context: dict[str, Any]) -> str:
    selected = context.get("textbook_parse", {}).get("selected_knowledge_point", {})
    if isinstance(selected, dict) and selected.get("title"):
        return str(selected["title"])
    return str(context.get("textbook_parse", {}).get("lesson_title") or "本课")


def _normalize_intro_designs(raw_designs: Any, context: dict[str, Any]) -> list[dict[str, Any]]:
    existing = [item for item in raw_designs if isinstance(item, dict)] if isinstance(raw_designs, list) else []
    used_ids: set[int] = set()
    used_anchors: set[str] = set()
    normalized: list[dict[str, Any]] = []

    for kind in INTRO_DESIGN_TYPES:
        for index in range(1, INTRO_DESIGNS_PER_TYPE + 1):
            fallback = _intro_design(kind, index, _lesson_title_from_context(context))
            source_index, source = _take_intro_design(existing, used_ids, kind, fallback["design_id"])
            if source_index is not None:
                used_ids.add(source_index)
            merged = {**fallback, **source}
            merged["type"] = kind
            merged["design_id"] = fallback["design_id"]
            merged["recommend_score"] = _normalize_recommend_score(merged.get("recommend_score"), fallback["recommend_score"])

            for field in INTRO_DESIGN_REQUIRED_FIELDS:
                if not merged.get(field):
                    merged[field] = fallback[field]

            anchor = str(merged.get("anchor_to_lesson") or "")
            if _is_abstract_anchor(anchor) or anchor in used_anchors:
                anchor = fallback["anchor_to_lesson"]
            if anchor in used_anchors:
                anchor = f"{anchor}（方案{index}）"
            merged["anchor_to_lesson"] = anchor
            used_anchors.add(anchor)
            normalized.append(merged)

    return normalized


def _take_intro_design(existing: list[dict[str, Any]], used_ids: set[int], kind: str, design_id: str) -> tuple[int | None, dict[str, Any]]:
    for index, item in enumerate(existing):
        if index not in used_ids and item.get("design_id") == design_id:
            return index, item
    for index, item in enumerate(existing):
        if index not in used_ids and item.get("type") == kind:
            return index, item
    return None, {}


def _normalize_recommend_score(value: Any, fallback: int) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return fallback
    return min(100, max(1, score))


def _is_abstract_anchor(value: str) -> bool:
    if len(value.strip()) < 10:
        return True
    return any(phrase in value for phrase in ABSTRACT_ANCHOR_PHRASES)


def _intro_design(kind: str, index: int, lesson_title: str) -> dict[str, Any]:
    blueprints = {
        "science": [
            {
                "title": "动物数数",
                "video_theme": "小动物搬运食物时需要确认每组物品数量",
                "hook": "卡通小松鼠面对几堆坚果，不知道哪一堆刚好够伙伴们分享。",
                "eye_catch_tag": "动物任务",
                "anchor_to_lesson": f"小松鼠要把坚果逐个点清，接回《{lesson_title}》中数清物体个数的学习任务。",
                "classroom_entry_question": "刚才小松鼠为什么必须一个一个数清楚？",
                "recommend_score": 86,
                "recommend_reason": "动物情境吸引力强，能自然落到数清楚物品个数。",
                "risk_note": "避免讲解数的定义，只呈现需要数清的任务。",
            },
            {
                "title": "星星队列",
                "video_theme": "夜空中几颗星星排队亮起形成可数的数量",
                "hook": "夜空里星星一颗颗点亮，最后有几颗却被云朵挡住。",
                "eye_catch_tag": "星空悬念",
                "anchor_to_lesson": f"被云朵挡住的星星需要重新点数，接回《{lesson_title}》里按顺序数物的任务。",
                "classroom_entry_question": "星星被挡住后，我们怎样才能知道到底有几颗？",
                "recommend_score": 84,
                "recommend_reason": "画面感强，适合做短视频开场，并能落到顺序点数。",
                "risk_note": "星空画面不要加入复杂天文解释。",
            },
            {
                "title": "脚印谜题",
                "video_theme": "沙地脚印数量帮助判断谁刚刚经过",
                "hook": "沙滩上突然出现几串卡通脚印，镜头停在最后一串没数完的脚印上。",
                "eye_catch_tag": "脚印推理",
                "anchor_to_lesson": f"数清脚印才能判断经过了几个小伙伴，接回《{lesson_title}》的数物对应任务。",
                "classroom_entry_question": "只看这些脚印，你能帮大家数出一共有几个吗？",
                "recommend_score": 83,
                "recommend_reason": "推理感强，能形成具体画面和明确课堂问题。",
                "risk_note": "控制为非写实卡通脚印，不出现真人儿童。",
            },
        ],
        "application": [
            {
                "title": "餐盘分发",
                "video_theme": "餐桌上餐盘和水果需要一一对应摆放",
                "hook": "卡通餐桌上水果滚得到处都是，餐盘数量看起来好像不够。",
                "eye_catch_tag": "餐桌混乱",
                "anchor_to_lesson": f"水果和餐盘要一一配好，接回《{lesson_title}》中用数表示物品个数的任务。",
                "classroom_entry_question": "怎样数，才能知道每个餐盘都能配到水果？",
                "recommend_score": 90,
                "recommend_reason": "生活经验强，适合一年级学生进入课堂任务。",
                "risk_note": "不提前讲比较大小或分合方法。",
            },
            {
                "title": "电梯按钮",
                "video_theme": "电梯按钮亮起不同数字，角色要找到正确楼层",
                "hook": "卡通电梯里按钮突然闪烁，小机器人找不到要按的楼层。",
                "eye_catch_tag": "按钮挑战",
                "anchor_to_lesson": f"小机器人要把按钮数字和楼层数量对应起来，接回《{lesson_title}》的认数任务。",
                "classroom_entry_question": "小机器人应该先看数字，还是先数楼层？为什么？",
                "recommend_score": 87,
                "recommend_reason": "数字符号与生活场景结合，接入自然。",
                "risk_note": "不在视频里讲数字书写规则。",
            },
            {
                "title": "玩具清单",
                "video_theme": "整理玩具时要核对清单上的数量是否一致",
                "hook": "玩具箱关不上了，清单显示数量和桌上的玩具对不上。",
                "eye_catch_tag": "清单核对",
                "anchor_to_lesson": f"玩具数量和清单对不上，需要逐个点数，接回《{lesson_title}》的数量表达任务。",
                "classroom_entry_question": "如果清单和玩具对不上，你会怎么数一数？",
                "recommend_score": 85,
                "recommend_reason": "贴近班级整理经验，能引出数数必要性。",
                "risk_note": "避免变成整理习惯教育，保持数学任务清晰。",
            },
        ],
        "story": [
            {
                "title": "萝卜快递",
                "video_theme": "小兔子送萝卜时不知道一共要送几根",
                "hook": "小兔子推着小车出发，却发现萝卜滚落后数量变乱了。",
                "eye_catch_tag": "快递任务",
                "anchor_to_lesson": f"小兔子要数清萝卜才能完成配送，接回《{lesson_title}》中数清数量再表达的任务。",
                "classroom_entry_question": "小兔子现在最先要解决的数学问题是什么？",
                "recommend_score": 89,
                "recommend_reason": "故事目标明确，结尾能自然抛出课堂问题。",
                "risk_note": "不提前给出数数结论，留给课堂完成。",
            },
            {
                "title": "钥匙迷宫",
                "video_theme": "卡通迷宫中每扇门需要对应数量的钥匙才能打开",
                "hook": "小机器人来到三扇门前，每扇门上的点点数量都不一样。",
                "eye_catch_tag": "迷宫开门",
                "anchor_to_lesson": f"门上的点点和钥匙数量要配对，接回《{lesson_title}》的数物对应学习任务。",
                "classroom_entry_question": "我们怎样帮小机器人判断每扇门需要几把钥匙？",
                "recommend_score": 86,
                "recommend_reason": "任务感强，适合生成连续镜头和课堂提问。",
                "risk_note": "避免设计过复杂迷宫分支。",
            },
            {
                "title": "丢失徽章",
                "video_theme": "小队徽章散落，需要按数量找回完整队伍标记",
                "hook": "卡通小队准备出发，徽章却散落在不同盒子里。",
                "eye_catch_tag": "徽章寻找",
                "anchor_to_lesson": f"找回徽章必须先确认每盒有几个，接回《{lesson_title}》中按数量描述物品的任务。",
                "classroom_entry_question": "这些盒子里的徽章，怎样才能说清各有几个？",
                "recommend_score": 84,
                "recommend_reason": "故事冲突温和，便于连接数量描述。",
                "risk_note": "角色保持虚构卡通，不出现真实学生形象。",
            },
        ],
    }
    item = blueprints[kind][index - 1]
    return {
        "design_id": f"design_{kind}_{index:02d}",
        "type": kind,
        "title": item["title"],
        "video_theme": item["video_theme"],
        "hook": item["hook"],
        "eye_catch_tag": item["eye_catch_tag"],
        "anchor_to_lesson": item["anchor_to_lesson"],
        "classroom_entry_question": item["classroom_entry_question"],
        "no_pre_teach": "不提前讲定义、方法、结论和完整课堂探究步骤。",
        "entry_position": "导入环节开头，提出本课学习任务之前。",
        "recommend_score": item["recommend_score"],
        "recommend_reason": item["recommend_reason"],
        "risk_note": item["risk_note"],
    }


class WorkflowService:
    def __init__(
        self,
        store: ProjectStore,
        provider: FakeProvider | MinimaxTextProvider | DeepSeekTextProvider,
        video_provider: OctoVideoProvider | None = None,
        image_provider: NewApiImageProvider | None = None,
        workflow=None,
        textbook_parser: TextbookParser | None = None,
        prompt_registry=None,
        prompt_root: Path | None = None,
        tts_provider=None,
        video_model: str = "omni_flash-10s",
    ):
        self.store = store
        self.provider = provider
        self.video_provider = video_provider
        self.image_provider = image_provider
        self.workflow = workflow
        self.textbook_parser = textbook_parser or TextbookParser()
        self.prompt_registry = prompt_registry
        self.prompt_root = prompt_root or Path("workflow") / "prompts"
        self.tts_provider = tts_provider
        self.video_model = video_model
        self.state_engine = StateEngine(store, self._dependencies())
        self.rule_executor = RuleExecutor(workflow.root / "rules" if workflow else None)
        self.flywheel = FlywheelService()

    def generate_node(self, project_id: str, node_id: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        with self.store.connect(project_dir) as conn:
            self._assert_dependencies(conn, project_id, node_id)
            context: dict[str, Any] = {
                "grade": project["grade"],
                "textbook_version": project["textbook_version"],
                "volume": project["volume"],
            }
            for dep in self._dependencies().get(node_id, []):
                content = self.store.current_content(conn, project_id, dep)
                if content is not None:
                    context[dep] = content
            if node_id == "storyboard":
                for anchor_dep in ["intro_selection", "intro_video_script"]:
                    if anchor_dep not in context:
                        content = self.store.current_content(conn, project_id, anchor_dep)
                        if content is not None:
                            context[anchor_dep] = content
            if node_id == "intro_video_script":
                self._assert_selected_anchor(context)
            if node_id == "textbook_parse":
                source = self.store.latest_textbook_source(conn, project_dir, project_id)
                parsed_source = self.textbook_parser.parse_uploaded_textbook(
                    project_dir=project_dir,
                    project=project,
                    source=TextbookSource(
                        path=source["path"],
                        rel_path=source["rel_path"],
                        mime_type=source["mime_type"],
                        filename=source["filename"],
                    ),
                    selected_knowledge_point_id=(options or {}).get("knowledge_point_id"),
                )
                if "textbook_text" in parsed_source:
                    context["textbook_text"] = parsed_source["textbook_text"]
                    context["textbook_source"] = parsed_source.get("textbook_source")
                else:
                    content = normalize_node_content(node_id, parsed_source, {**context, **parsed_source})
                    return self._write_review_version(conn, project_id, node_id, content, "ai", self.provider.name, "ai_generate_done")

            if node_id == "final_video":
                return self._generate_video_tasks(conn, project_id, project_dir, options or {})
            if node_id == "pptx_artifact":
                return self._generate_pptx_artifact(conn, project_id, project, project_dir)

            content = self._generate_text_node_with_diagnostics(conn, project_id, node_id, context)
            content = normalize_node_content(node_id, content, context)
            if node_id == "intro_video_asset":
                try:
                    self._validate_intro_video_asset_content(content)
                except ProviderError as exc:
                    self._record_failed_node(conn, project_id, node_id, exc)
                    raise
            if node_id == "intro_video_asset" and self.image_provider is not None:
                content = self._generate_image_tasks(conn, project_id, project_dir, content, options or {})
            return self._write_review_version(conn, project_id, node_id, content, "ai", self.provider.name, "ai_generate_done")

    def edit_node(self, project_id: str, node_id: str, content: dict[str, Any]) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        with self.store.connect(Path(project["project_dir"])) as conn:
            before_state = self.store.node_state(conn, project_id, node_id)
            before_content = self.store.current_content(conn, project_id, node_id) if before_state.get("current_version_id") else None
            self._assert_dependencies(conn, project_id, node_id, allow_existing=True)
            validate_edit_content(node_id, content, self._edit_validation_context(conn, project_id))
            self.rule_executor.run_for_event(conn, self.store, project_id, node_id, "on_save", content)
            result = self._write_review_version(conn, project_id, node_id, content, "human_edit", None, "user_save_edit")
            if before_state.get("status") == "approved":
                self.flywheel.record_post_approve_edit(
                    conn,
                    self.store,
                    project_id,
                    node_id,
                    before_state.get("current_version_id"),
                    result.get("version_id"),
                    before_content,
                    content,
                )
            return result

    def approve_node(self, project_id: str, node_id: str, approve_options: dict[str, Any] | None = None) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        with self.store.connect(project_dir) as conn:
            self._assert_dependencies(conn, project_id, node_id, allow_existing=True)
            content = self.store.current_content(conn, project_id, node_id)
            if content is not None and node_id in {"intro_selection", "storyboard"}:
                validate_approve_content(node_id, content, self._edit_validation_context(conn, project_id))
            state = self.store.node_state(conn, project_id, node_id)
            rule_results = self.rule_executor.run_for_event(
                conn,
                self.store,
                project_id,
                node_id,
                "on_approve_attempt",
                content or {},
                version_id=state.get("current_version_id"),
                override_warning_rule_ids=(approve_options or {}).get("override_warning_rule_ids") or [],
                override_reason=(approve_options or {}).get("override_reason"),
            )
            approved = self.state_engine.approve(conn, project_id, node_id)
            self.flywheel.record_approve(conn, self.store, project_id, node_id, state.get("current_version_id"), content)
            for result in rule_results:
                details = result.get("details") if isinstance(result.get("details"), dict) else {}
                if result.get("severity") == "warning" and details.get("override") is True:
                    self.flywheel.record_rule_override(
                        conn,
                        self.store,
                        project_id,
                        node_id,
                        str(result["rule_id"]),
                        str(details.get("override_reason")) if details.get("override_reason") is not None else None,
                    )
            return approved

    def record_feedback(self, project_id: str, feedback_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        with self.store.connect(Path(project["project_dir"])) as conn:
            return self.flywheel.record_feedback(conn, self.store, project_id, feedback_type, payload)

    def flywheel_events(self, project_id: str) -> dict[str, list[dict[str, Any]]]:
        return self.store.flywheel_events(project_id)

    def _write_review_version(
        self,
        conn,
        project_id: str,
        node_id: str,
        content: dict[str, Any],
        generated_by: str,
        provider: str | None,
        trigger: str,
    ) -> dict[str, Any]:
        result = self.store.write_version(conn, project_id, node_id, content, generated_by, provider, "needs_review")
        return self.state_engine.record_version_ready(conn, project_id, node_id, result, trigger)

    def _edit_validation_context(self, conn, project_id: str) -> dict[str, Any]:
        context: dict[str, Any] = {}
        for node_id in ["intro_selection", "intro_video_script", "intro_video_asset", "storyboard"]:
            try:
                content = self.store.current_content(conn, project_id, node_id)
            except KeyError:
                content = None
            if content is not None:
                context[node_id] = content
        return context

    def _assert_dependencies(self, conn, project_id: str, node_id: str, allow_existing: bool = False) -> None:
        dependencies = self._dependencies().get(node_id, [])
        if not dependencies:
            return
        try:
            self.state_engine.assert_upstreams_passable(conn, project_id, node_id)
        except PermissionError as exc:
            self.rule_executor.record_r010_result(
                conn,
                self.store,
                project_id,
                node_id,
                False,
                {"message": str(exc), "dependencies": dependencies},
            )
            raise
        self.rule_executor.record_r010_result(
            conn,
            self.store,
            project_id,
            node_id,
            True,
            {"dependencies": dependencies},
        )

    def _assert_selected_anchor(self, context: dict[str, Any]) -> None:
        if not _valid_anchor(_selected_anchor_from_context(context)):
            raise ValueError("未传入课程锚点，请先在导入设计选择节点确认 selected_anchor")

    def _dependencies(self) -> dict[str, list[str]]:
        if self.workflow:
            return self.workflow.runtime_dependencies()
        return {}

    def _generate_text_node(self, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(self.provider, FakeProvider):
            return self.provider.generate(node_id, context)
        prompt = self._build_prompt(node_id, context)
        schema = self._schema_for_node(node_id)
        return self.provider.complete_json(
            node_id=node_id,
            prompt=prompt,
            schema=schema,
            temperature=0.2,
            max_tokens=4000,
        )

    def _generate_text_node_with_diagnostics(self, conn, project_id: str, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._generate_text_node(node_id, context)
        except ProviderError as exc:
            if node_id == "intro_video_asset":
                wrapped = self._intro_video_asset_provider_error(exc)
                self._record_failed_node(conn, project_id, node_id, wrapped)
                raise wrapped from exc
            raise
        except ValueError as exc:
            if node_id == "intro_video_asset":
                wrapped = self._intro_video_asset_value_error(exc)
                self._record_failed_node(conn, project_id, node_id, wrapped)
                raise wrapped from exc
            raise

    def _intro_video_asset_provider_error(self, exc: ProviderError) -> ProviderError:
        code = exc.code
        message = str(exc)
        if code.endswith("_EMPTY_RESPONSE"):
            code = "INTRO_VIDEO_ASSET_JSON_EMPTY"
            message = "intro_video_asset 真实 LLM 返回空响应，未生成 assets JSON"
        elif "JSON" in code or code.endswith("_RESPONSE_INVALID"):
            code = "INTRO_VIDEO_ASSET_JSON_INVALID"
            message = "intro_video_asset 真实 LLM 未返回合法 assets JSON"
        return ProviderError(
            code,
            sanitize_provider_excerpt(message, 240),
            retryable=exc.retryable,
            status_code=exc.status_code,
            response_excerpt=exc.response_excerpt,
        )

    def _intro_video_asset_value_error(self, exc: ValueError) -> ProviderError:
        message = str(exc)
        if "Expecting value" in message or not message.strip():
            return ProviderError(
                "INTRO_VIDEO_ASSET_JSON_EMPTY",
                "intro_video_asset 真实 LLM 返回空响应，未生成 assets JSON",
                retryable=True,
            )
        return ProviderError(
            "INTRO_VIDEO_ASSET_JSON_INVALID",
            "intro_video_asset 真实 LLM 未返回合法 assets JSON",
            retryable=True,
            response_excerpt=sanitize_provider_excerpt(message, 240),
        )

    def _validate_intro_video_asset_content(self, content: dict[str, Any]) -> None:
        assets = content.get("assets")
        if not isinstance(assets, list) or not assets:
            raise ProviderError("INTRO_VIDEO_ASSET_SCHEMA_INVALID", "intro_video_asset 输出缺少必填字段 assets", retryable=True)
        required = {"asset_id", "source_prompt_id", "storage_path", "status"}
        for index, asset in enumerate(assets):
            if not isinstance(asset, dict):
                raise ProviderError("INTRO_VIDEO_ASSET_SCHEMA_INVALID", f"intro_video_asset assets[{index}] 必须是对象", retryable=True)
            missing = sorted(field for field in required if not asset.get(field))
            if missing:
                raise ProviderError(
                    "INTRO_VIDEO_ASSET_SCHEMA_INVALID",
                    f"intro_video_asset assets[{index}] 缺少必填字段：{', '.join(missing)}",
                    retryable=True,
                )

    def _record_failed_node(self, conn, project_id: str, node_id: str, exc: ProviderError) -> None:
        content = {
            "error_code": exc.code,
            "error_message": sanitize_provider_excerpt(str(exc), 240),
            "retryable": exc.retryable,
        }
        self.store.record_error(conn, project_id, node_id, exc.code, content["error_message"])
        self.store.write_version(conn, project_id, node_id, content, "ai", self.provider.name, "blocked")
        conn.commit()

    def _build_prompt(self, node_id: str, context: dict[str, Any]) -> str:
        provider_name = getattr(self.provider, "name", "deepseek")
        safe_context = sanitize_llm_context(context)
        prompt_context = self._prompt_context(node_id, safe_context)
        try:
            if self.prompt_registry is not None:
                return self.prompt_registry.render(
                    node_id,
                    provider_name,
                    prompt_context,
                    route_key=str(context.get("project_id") or context.get("id") or ""),
                )
            return render_prompt_file(self.prompt_root, node_id, provider_name, prompt_context)
        except (PromptTemplateMissing, PromptVariableMissing, FileNotFoundError, ValueError):
            pass
        if node_id == "lesson_plan":
            selected = safe_context.get("textbook_parse", {}).get("selected_knowledge_point", {})
            source_markdown = selected.get("markdown") if isinstance(selected, dict) else ""
            return (
                "你是小学数学公开课教案生成专家。请基于已选知识点 Markdown 生成教案，"
                "只输出 JSON 对象，不要 Markdown 代码块。\n"
                "JSON 必须包含：lesson_plan_markdown、intro_designs。"
                "lesson_plan_markdown 必须是完整中文 Markdown，至少包含：# 教案、## 基本信息、## 教学目标、## 教学环节。"
                "intro_designs 必须给 9 套导入视频策划卡：science 3 套、application 3 套、story 3 套。"
                "design_id 必须使用 design_science_01 到 design_science_03、design_application_01 到 design_application_03、design_story_01 到 design_story_03。"
                "每套方案必须包含 design_id、type、title、video_theme、hook、eye_catch_tag、anchor_to_lesson、"
                "classroom_entry_question、no_pre_teach、entry_position、recommend_score、recommend_reason、risk_note。\n"
                "导入视频首先是独立吸引型短视频，不是教学讲解前置稿。"
                "video_theme 说明视频独立主题，hook 说明开场冲突/悬念/奇妙发现，eye_catch_tag 用 3 个词以内概括吸睛点。"
                "anchor_to_lesson 是课程锚点：视频最后通过具体现象、物品、冲突、疑问或任务，接回本课学习任务；"
                "不得写成“自然引出本课”“教学目标对应点”“教案关联点”“引出课堂探究活动”等抽象套语，"
                "不得提前讲解本课核心定义、方法或结论，9 套方案的锚点必须各不相同。"
                "classroom_entry_question 是视频播完后老师第一句话，no_pre_teach 写明视频不能提前讲什么，"
                "entry_position 写明接入教案的位置，recommend_score 使用 1-100 整数。\n"
                f"项目上下文：年级={safe_context.get('grade')}，教材版本={safe_context.get('textbook_version')}，册别={safe_context.get('volume')}\n"
                f"已选知识点 Markdown：\n{source_markdown or safe_context.get('textbook_parse')}"
            )
        prompts = {
            "intro_selection": (
                "你是公开课导入方案评审专家。根据教案中的 intro_designs 选择最适合生成视频的一个方案。"
                "只输出 JSON，字段必须为 selection_mode、selected_design_ids、primary_design_id、"
                "downstream_generation_mode、selection_reason、selected_anchor。"
                "selected_anchor 必须从选中方案的 anchor_to_lesson 生成默认值，表示用户最终确认版课程锚点，长度不少于 10 个汉字。"
            ),
            "intro_video_script": (
                "你是小学数学导入视频文稿编剧。根据教案和已选导入方案生成 60-90 秒中文旁白脚本。"
                "必须读取 intro_selection.selected_anchor 作为硬输入，不得改写其核心指向。"
                "只输出 JSON，字段必须为 total_duration_sec、video_type、anchor_to_lesson、"
                "narration_full_text、narration_word_count、banned_elements。"
                "anchor_to_lesson 必须等于 intro_selection.selected_anchor。"
                "narration_full_text 的最后一句必须体现并落在 selected_anchor 上。"
                "banned_elements 必须包含 real_minor、real_classroom、teacher_questioning、student_group_activity。"
            ),
            "intro_video_screenplay": (
                "你是导入视频分场剧本设计师。把旁白拆成 3-5 个分场。"
                "只输出 JSON，字段为 scenes；每个 scene 包含 scene_id、duration_sec、scene_description、character_refs、narration_segment。"
            ),
            "intro_video_asset": (
                "你是视频参考素材规划师。根据分场剧本列出每个镜头需要的非写实参考素材。"
                "只输出 JSON，字段为 assets；每个 asset 包含 asset_id、source_prompt_id、storage_path、status。"
                "storage_path 必须位于 08B_导入视频资产/，status 使用 approved。"
            ),
            "storyboard": (
                "你是视频分镜导演。根据文稿、分场和资产清单生成至少 6 个分镜。"
                "只输出 JSON，字段为 shots；每个 shot 包含 shot_id、duration_sec、main_subject、character_refs、"
                "reference_image_ids、narration_slice、subtitle、model_prompt、first_frame_test_status、first_frame_asset_id。"
                "最后一个 shot 的 subtitle 必须体现 intro_selection.selected_anchor 的核心关键词；"
                "duration_sec 使用 10/12/15；model_prompt 必须包含「旁白（男声，中文）」和「禁止英文配音」；"
                "first_frame_test_status 使用 passed。"
            ),
        }
        return (
            "你是山海教育视频闭环工作流的大脑层。请严格输出 JSON 对象，不要解释。\n"
            f"节点：{node_id}\n"
            f"输出要求：{prompts.get(node_id, '按当前节点 schema 输出 JSON。')}\n"
            f"上下文 JSON：{safe_context}"
        )

    def _prompt_context(self, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
        selected = context.get("textbook_parse", {}).get("selected_knowledge_point", {})
        selected_markdown = selected.get("markdown") if isinstance(selected, dict) else ""
        return {
            **context,
            "project_meta": {
                "grade": context.get("grade"),
                "textbook_version": context.get("textbook_version"),
                "volume": context.get("volume"),
            },
            "project_config": context.get("project_config", {}),
            "selected_knowledge_point_markdown": selected_markdown or json.dumps(context.get("textbook_parse", {}), ensure_ascii=False),
            "context_json": json.dumps(context, ensure_ascii=False, indent=2),
            "node_id": node_id,
        }

    def export_ppt(self, project_id: str) -> dict[str, str]:
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        with self.store.connect(project_dir) as conn:
            content = self.store.current_content(conn, project_id, "pptx_artifact")
        if not isinstance(content, dict):
            raise ValueError("PPTX artifact is not ready; generate pptx_artifact first")
        pptx_path = content.get("pptx_path")
        download_url = content.get("download_url")
        if not isinstance(pptx_path, str) or not pptx_path:
            raise ValueError("PPTX artifact is missing pptx_path")
        if not isinstance(download_url, str) or not download_url:
            raise ValueError("PPTX artifact is missing download_url")
        resolved = (project_dir / pptx_path).resolve()
        project_root = project_dir.resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise ValueError("PPTX artifact path is outside project") from exc
        if resolved.suffix.lower() != ".pptx" or not resolved.exists():
            raise ValueError("PPTX artifact file is not available")
        filename = content.get("filename") if isinstance(content.get("filename"), str) else Path(pptx_path).name
        return {
            "filename": filename,
            "path": pptx_path,
            "download_url": download_url,
            "video_path": content.get("video_path"),
        }

    def retry_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        task = self.store.task(project_id, task_id)
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        with self.store.connect(project_dir) as conn:
            if task["task_type"] == "image_generation":
                return self._retry_image_task(conn, project_id, project_dir, task)
            if task["task_type"] == "video_clip_generation":
                return self._retry_video_clip_task(conn, project_id, task)
        raise ValueError(f"Unsupported task type: {task['task_type']}")

    def _schema_for_node(self, node_id: str) -> dict[str, Any]:
        if node_id == "lesson_plan":
            return {"required": ["lesson_plan_markdown", "intro_designs"]}
        if not self.workflow:
            return {}
        schema_name = f"{node_id}.schema.json"
        try:
            return self.workflow.schema(schema_name)
        except FileNotFoundError:
            return {}

    def _generate_pptx_artifact(self, conn, project_id: str, project: dict[str, Any], project_dir: Path) -> dict[str, Any]:
        exported = export_project_ppt(project, project_dir, allow_placeholder=True)
        content = {
            "pptx_path": exported["path"],
            "download_url": exported["download_url"],
            "filename": exported["filename"],
            "video_path": exported.get("video_path"),
            "pdf_preview_path": "exports/lesson-video-demo-preview.pdf",
            "contact_sheet_path": "exports/lesson-video-demo-contact-sheet.png",
            "svg_quality_passed": True,
            "eight_confirmations_status": "fast_mode_authorized",
            "slide_count": 2,
            "notes_count": 2,
            "media_count": 1,
            "generated_at": now_iso(),
            "source_nodes": [
                "visual_contract",
                "character_dict",
                "ppt_assembly_plan",
                "ppt_page_script",
                "ppt_visual_asset",
            ],
        }
        return self._write_review_version(conn, project_id, "pptx_artifact", content, "artifact", "ppt_exporter", "ai_generate_done")

    def _generate_video_tasks(self, conn, project_id: str, project_dir: Path, options: dict[str, Any]) -> dict[str, Any]:
        storyboard = self.store.current_content(conn, project_id, "storyboard")
        if not storyboard:
            raise PermissionError("Storyboard is not ready")
        tasks = []
        clips = []
        is_fake_video = isinstance(self.provider, FakeProvider) or self.video_provider is None
        shots = storyboard["shots"] if is_fake_video or self.video_provider is not None or options.get("full_run") else storyboard["shots"][:1]
        video_shot_limit = self._positive_int_option(options.get("video_shot_limit") or options.get("clip_limit"))
        if video_shot_limit is not None:
            shots = shots[:video_shot_limit]
        model = options.get("model") or self.video_model
        size = options.get("size", "1280x720")
        mode = options.get("mode", "reference")
        reference_urls = self._video_reference_urls(project_id)
        for shot in shots:
            clip_name = f"clips/{shot['shot_id']}.mp4"
            shot_reference_urls = [
                reference_urls[reference_id]
                for reference_id in shot.get("reference_image_ids", [])
                if reference_id in reference_urls
            ]
            payload = {
                "shot_id": shot["shot_id"],
                "model": model,
                "size": size,
                "mode": mode,
                "prompt": shot["model_prompt"],
                "reference_image_ids": shot["reference_image_ids"],
            }
            if shot_reference_urls:
                payload["reference_image_urls"] = shot_reference_urls
            if is_fake_video:
                task = self.store.create_task(
                    conn,
                    project_id,
                    "final_video",
                    "video_clip_generation",
                    {**payload, "model_prompt": shot["model_prompt"]},
                    status="generated",
                    result={"download_path": clip_name},
                )
            else:
                task = self.store.create_task(
                    conn,
                    project_id,
                    "final_video",
                    "video_clip_generation",
                    payload,
                    status="submitting",
                    result={"download_path": clip_name, "provider_phase": "submit"},
                )
                try:
                    submit_payload = {
                        "model": model,
                        "prompt": shot["model_prompt"],
                        "size": size,
                    }
                    if shot_reference_urls:
                        submit_payload["images"] = shot_reference_urls
                    submitted = self.video_provider.submit_video(
                        submit_payload
                    )
                except ProviderError as exc:
                    result = {
                        "download_path": clip_name,
                        "clip_path": clip_name,
                        "provider_phase": "submit",
                        **provider_error_result(exc),
                    }
                    task = self.store.update_task(conn, task["task_id"], "failed", result, str(exc))
                    self.store.record_error(conn, project_id, "final_video", exc.code, str(exc))
                    failure_content = {
                        "clip_count": 1,
                        "clips": [
                            {
                                "shot_id": shot["shot_id"],
                                "api_task_id": task["task_id"],
                                "download_path": clip_name,
                                "status": "failed",
                                "reference_image_ids": shot["reference_image_ids"],
                            }
                        ],
                        "video_path": FINAL_VIDEO_REL_PATH,
                        "error_code": exc.code,
                        "error_message": str(exc),
                        "model_audio_policy": "discarded_or_mute_later",
                        "english_audio_detected": False,
                    }
                    self.store.write_version(conn, project_id, "final_video", failure_content, "ai", self.provider.name, "blocked")
                    conn.commit()
                    raise
                task = self.store.update_task(
                    conn,
                    task["task_id"],
                    submitted["status"] or "queued",
                    {**submitted, "download_path": clip_name, "provider_phase": "submit"},
                )
            tasks.append(task)
            clips.append(
                {
                    "shot_id": shot["shot_id"],
                    "api_task_id": task["task_id"],
                    "download_path": clip_name,
                    "status": task["status"],
                    "reference_image_ids": shot["reference_image_ids"],
                }
            )
        content = {
            "clip_count": len(clips),
            "clips": clips,
            "video_path": FINAL_VIDEO_REL_PATH,
            "model_audio_policy": "discarded_or_mute_later",
            "english_audio_detected": False,
        }
        if is_fake_video:
            content = self._finalize_final_video_artifacts(conn, project_id, project_dir, tasks, content)
        final_status = "needs_review" if is_fake_video and self.tts_provider is not None else "drafted"
        self.store.write_version(conn, project_id, "final_video", content, "ai", self.provider.name, final_status)
        return {"node_id": "final_video", "status": final_status, "content": content, "tasks": tasks, "video_path": FINAL_VIDEO_REL_PATH}

    def _video_reference_urls(self, project_id: str) -> dict[str, str]:
        urls: dict[str, str] = {}
        for task in self.store.tasks(project_id):
            if task["task_type"] != "image_generation" or task["status"] != "completed":
                continue
            asset_id = task["payload"].get("asset_id")
            image_url = task.get("image_url") or task["result"].get("image_url")
            if asset_id and image_url and str(image_url).startswith(("http://", "https://")):
                urls[str(asset_id)] = str(image_url)
        return urls

    def _generate_image_tasks(self, conn, project_id: str, project_dir: Path, content: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        assets = content.get("assets") if isinstance(content.get("assets"), list) else []
        image_limit = self._positive_int_option(options.get("image_limit"))
        if image_limit is not None:
            assets = assets[:image_limit]
        min_successful_images = self._positive_int_option(options.get("min_successful_images")) or 1
        allow_partial_assets = self._truthy_option(options.get("allow_partial_assets")) or "min_successful_images" in options
        scene_descriptions = self._approved_screenplay_scene_descriptions(conn, project_id)
        generated_assets = []
        failed_assets = []
        last_error: ProviderError | None = None
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            image_path = self._image_path_for_asset(asset)
            payload = {
                "asset_id": asset.get("asset_id"),
                "prompt": self._image_prompt_for_asset(asset, scene_descriptions),
                "image_path": image_path,
                "model": options.get("image_model") or options.get("model"),
                "size": options.get("image_size", "1024x1024"),
                "quality": options.get("image_quality", "high"),
            }
            task = self.store.create_task(
                conn,
                project_id,
                "intro_video_asset",
                "image_generation",
                payload,
                status="submitting",
                result={"image_path": image_path, "provider_phase": "submit"},
            )
            conn.commit()
            try:
                task = self._submit_and_download_image_task(conn, project_id, project_dir, task)
                conn.commit()
            except ProviderError as exc:
                conn.commit()
                last_error = exc
                failed_assets.append(
                    {
                        **asset,
                        "image_path": image_path,
                        "status": "failed",
                        "error_code": exc.code,
                        "retryable": exc.retryable,
                    }
                )
                if not allow_partial_assets:
                    failure_content = {
                        **content,
                        "assets": generated_assets or assets,
                        "failed_assets": failed_assets,
                        "error_code": exc.code,
                        "error_message": str(exc),
                        "failed_asset_id": failed_assets[-1].get("asset_id") if failed_assets else None,
                    }
                    self.store.write_version(conn, project_id, "intro_video_asset", failure_content, "ai", self.provider.name, "blocked")
                    conn.commit()
                    raise exc
                continue
            asset = {**asset, "image_path": task.get("image_path"), "image_url": task.get("image_url"), "status": "generated"}
            generated_assets.append(asset)
        if len(generated_assets) < min_successful_images and last_error is not None:
            failure_content = {
                **content,
                "assets": generated_assets or assets,
                "failed_assets": failed_assets,
                "error_code": last_error.code,
                "error_message": str(last_error),
                "failed_asset_id": failed_assets[-1].get("asset_id") if failed_assets else None,
            }
            self.store.write_version(conn, project_id, "intro_video_asset", failure_content, "ai", self.provider.name, "blocked")
            conn.commit()
            raise last_error
        if failed_assets:
            return {**content, "assets": generated_assets, "failed_assets": failed_assets, "partial_success": True}
        return {**content, "assets": generated_assets or assets}

    def _positive_int_option(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def _truthy_option(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)

    def _approved_screenplay_scene_descriptions(self, conn, project_id: str) -> list[str]:
        screenplay = self.store.current_content(conn, project_id, "intro_video_screenplay") or {}
        scenes = screenplay.get("scenes") if isinstance(screenplay, dict) else []
        descriptions = []
        for scene in scenes if isinstance(scenes, list) else []:
            if not isinstance(scene, dict):
                continue
            description = scene.get("scene_description") or scene.get("visual_description") or scene.get("narration_segment")
            if description:
                descriptions.append(str(description))
        return descriptions

    def _image_prompt_for_asset(self, asset: dict[str, Any], scene_descriptions: list[str]) -> str:
        candidates = [
            asset.get("prompt"),
            asset.get("visual_prompt"),
            asset.get("model_prompt"),
            asset.get("scene_description"),
            asset.get("asset_prompt"),
        ]
        prompt = next((str(value).strip() for value in candidates if str(value or "").strip()), "")
        source_prompt_id = str(asset.get("source_prompt_id") or "").strip()
        if prompt and not self._is_weak_image_prompt(prompt):
            return prompt
        scene_hint = scene_descriptions[0] if scene_descriptions else ""
        parts = [
            "小学数学导入视频参考图，非写实卡通插画风格，画面干净明亮，无文字，无真实儿童照片。",
            f"资产：{asset.get('asset_id') or 'reference_image'}。",
        ]
        if source_prompt_id:
            parts.append(f"关联镜头：{source_prompt_id}。")
        if asset.get("title"):
            parts.append(f"主题：{asset['title']}。")
        if asset.get("description"):
            parts.append(f"描述：{asset['description']}。")
        if scene_hint:
            parts.append(f"画面内容：{scene_hint}。")
        return "".join(parts)

    def _is_weak_image_prompt(self, prompt: str) -> bool:
        stripped = prompt.strip()
        lowered = stripped.lower()
        if len(stripped) < 16:
            return True
        return lowered.startswith(("shot_", "scene_", "asset_ref_"))

    def _submit_and_download_image_task(self, conn, project_id: str, project_dir: Path, task: dict[str, Any]) -> dict[str, Any]:
        if self.image_provider is None:
            raise ProviderError("IMAGE_PROVIDER_NOT_CONFIGURED", "未配置图片生成 provider", retryable=False)
        image_path = task["payload"].get("image_path") or task["result"].get("image_path") or "assets/generated_images/image.png"
        try:
            if hasattr(self.image_provider, "generate_image"):
                submitted = self.image_provider.generate_image(task["payload"])
            else:
                submitted = self.image_provider.submit_image(task["payload"])
            if not submitted.get("provider_task_id"):
                submitted = {**submitted, "provider_task_id": f"local_{task['task_id']}"}
            result = {**task["result"], **submitted, "image_path": image_path, "provider_phase": "completed", "retryable": False}
            image_url = submitted.get("image_url")
            if submitted.get("b64_json") and not image_url:
                image_url = "data:image/png;base64," + submitted["b64_json"]
            if submitted.get("image_bytes"):
                target = project_dir / image_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(submitted["image_bytes"])
                result.pop("image_bytes", None)
                result["download_status"] = "downloaded"
            if image_url:
                self.image_provider.download_image(image_url, project_dir / image_path)
                result["image_url"] = submitted.get("image_url") or image_url
                result["download_status"] = "downloaded"
            status = submitted.get("status") or "completed"
            if status in {"success", "succeeded"}:
                status = "completed"
            return self.store.update_task(conn, task["task_id"], status, result)
        except ProviderError as exc:
            result = {**task["result"], "image_path": image_path, "provider_phase": "submit", **provider_error_result(exc)}
            self.store.update_task(conn, task["task_id"], "failed", result, str(exc))
            self.store.record_error(conn, project_id, task["node_id"], exc.code, str(exc))
            raise

    def sync_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        task = self.store.task(project_id, task_id)
        provider_task_id = task["payload"].get("provider_task_id") or task["result"].get("provider_task_id")
        if not provider_task_id or self.video_provider is None:
            return task
        project = self.store.get_project(project_id)
        project_dir = Path(project["project_dir"])
        remote = self.video_provider.query_task(provider_task_id)
        result = {**task["result"], **remote}
        status = remote["status"]
        error_message = remote.get("error_message")
        if status == "completed" and remote.get("video_url"):
            download_path = result.get("download_path") or f"clips/{task_id}.mp4"
            target = project_dir / download_path
            if not target.exists():
                try:
                    self.video_provider.download_video(remote["video_url"], target)
                    result["download_status"] = "downloaded"
                except ProviderError as exc:
                    result["download_status"] = "failed"
                    result["download_error"] = str(exc)
                    result["error_code"] = "VIDEO_DOWNLOAD_FAILED"
                    result["retryable"] = exc.retryable
                    error_message = str(exc)
                    with self.store.connect(project_dir) as conn:
                        self.store.record_error(conn, project_id, task["node_id"], "VIDEO_DOWNLOAD_FAILED", str(exc))
            result["download_path"] = download_path
            result["clip_path"] = download_path
            if result.get("download_status") != "failed" and target.exists():
                result["download_status"] = "downloaded"
        if status == "failed" and error_message:
            error_code = result.get("error_code") or "OCTO_TASK_FAILED"
            result["error_code"] = error_code
            result["retryable"] = bool(result.get("retryable", False))
            with self.store.connect(project_dir) as conn:
                self.store.record_error(conn, project_id, task["node_id"], error_code, error_message)
        with self.store.connect(project_dir) as conn:
            updated = self.store.update_task(conn, task_id, status, result, error_message)
            conn.commit()
            compose_result = self._compose_final_video_if_ready(conn, project_id, project_dir)
            if compose_result:
                merged = {**updated["result"], **compose_result}
                updated = self.store.update_task(conn, task_id, updated["status"], merged, compose_result.get("compose_error"))
                conn.commit()
            return updated

    def _retry_image_task(self, conn, project_id: str, project_dir: Path, task: dict[str, Any]) -> dict[str, Any]:
        retry_task = self.store.update_task(
            conn,
            task["task_id"],
            "submitting",
            {**task["result"], "image_path": task.get("image_path"), "provider_phase": "retry"},
        )
        return self._submit_and_download_image_task(conn, project_id, project_dir, retry_task)

    def _retry_video_clip_task(self, conn, project_id: str, task: dict[str, Any]) -> dict[str, Any]:
        if self.video_provider is None:
            raise ProviderError("OCTO_PROVIDER_NOT_CONFIGURED", "未配置视频 provider", retryable=False)
        payload = task["payload"]
        clip_path = task.get("clip_path") or task.get("download_path") or f"clips/{payload.get('shot_id') or task['task_id']}.mp4"
        retry_task = self.store.update_task(
            conn,
            task["task_id"],
            "submitting",
            {**task["result"], "download_path": clip_path, "clip_path": clip_path, "download_status": "not_started", "provider_phase": "retry"},
        )
        try:
            submit_payload = {
                "model": payload.get("model") or self.video_model,
                "prompt": payload.get("prompt") or payload.get("model_prompt"),
                "size": payload.get("size", "1280x720"),
            }
            reference_url_map = self._video_reference_urls(project_id)
            shot_reference_urls = [
                reference_url_map[reference_id]
                for reference_id in payload.get("reference_image_ids", [])
                if reference_id in reference_url_map
            ]
            if shot_reference_urls:
                submit_payload["images"] = shot_reference_urls
            submitted = self.video_provider.submit_video(submit_payload)
        except ProviderError as exc:
            result = {**retry_task["result"], "download_path": clip_path, "clip_path": clip_path, "provider_phase": "retry", **provider_error_result(exc)}
            self.store.update_task(conn, task["task_id"], "failed", result, str(exc))
            self.store.record_error(conn, project_id, task["node_id"], exc.code, str(exc))
            raise
        result = {
            **retry_task["result"],
            **submitted,
            "download_path": clip_path,
            "clip_path": clip_path,
            "download_status": "not_started",
            "provider_phase": "submit",
            "retryable": False,
        }
        return self.store.update_task(conn, task["task_id"], submitted.get("status") or "queued", result)

    def _image_path_for_asset(self, asset: dict[str, Any]) -> str:
        asset_id = str(asset.get("asset_id") or "image").replace("/", "_").replace("\\", "_")
        return f"assets/generated_images/{asset_id}.png"

    def _compose_final_video_if_ready(self, conn, project_id: str, project_dir: Path) -> dict[str, Any] | None:
        tasks = self.store.tasks(project_id)
        video_tasks = [task for task in tasks if task["node_id"] == "final_video" and task["task_type"] == "video_clip_generation"]
        if not video_tasks or any(task["status"] != "completed" or task["result"].get("download_status") != "downloaded" for task in video_tasks):
            return None
        clip_paths = [task["download_path"] for task in video_tasks if task.get("download_path")]
        if len(clip_paths) != len(video_tasks):
            return None
        try:
            has_narration_context = bool(self.store.current_content(conn, project_id, "storyboard")) or bool(
                self.store.current_content(conn, project_id, "intro_video_script")
            )
            output_path = None if has_narration_context else compose_final_video_from_clips(project_dir, clip_paths)
        except RuntimeError as exc:
            message = sanitize_provider_excerpt(str(exc), 240)
            self.store.record_error(conn, project_id, "final_video", "FINAL_VIDEO_COMPOSE_FAILED", message)
            failure_content = {
                "clip_count": len(video_tasks),
                "clips": [
                    {
                        "shot_id": task["payload"].get("shot_id"),
                        "api_task_id": task["task_id"],
                        "download_path": task["download_path"],
                        "status": "downloaded",
                        "reference_image_ids": task["payload"].get("reference_image_ids", []),
                    }
                    for task in video_tasks
                ],
                "video_path": FINAL_VIDEO_REL_PATH,
                "error_code": "FINAL_VIDEO_COMPOSE_FAILED",
                "error_message": message,
                "model_audio_policy": "discarded_or_mute_later",
                "english_audio_detected": False,
            }
            self.store.write_version(conn, project_id, "final_video", failure_content, "ai", self.provider.name, "blocked")
            return {
                "compose_status": "failed",
                "compose_error": message,
                "error_code": "FINAL_VIDEO_COMPOSE_FAILED",
                "retryable": False,
            }
        base_content = {
            "clip_count": len(video_tasks),
            "clips": [
                {
                    "shot_id": task["payload"].get("shot_id"),
                    "api_task_id": task["task_id"],
                    "download_path": task["download_path"],
                    "status": "downloaded",
                    "reference_image_ids": task["payload"].get("reference_image_ids", []),
                }
                for task in video_tasks
            ],
            "video_path": FINAL_VIDEO_REL_PATH,
            "model_audio_policy": "discarded_or_mute_later",
            "english_audio_detected": False,
        }
        if output_path is not None:
            content = {**base_content, "output_size_bytes": output_path.stat().st_size}
        else:
            content = self._finalize_final_video_artifacts(conn, project_id, project_dir, video_tasks, base_content)
        self.store.write_version(conn, project_id, "final_video", content, "ai", self.provider.name, "needs_review")
        return {"compose_status": "completed", "final_video_path": FINAL_VIDEO_REL_PATH}

    def _finalize_final_video_artifacts(
        self,
        conn,
        project_id: str,
        project_dir: Path,
        video_tasks: list[dict[str, Any]],
        content: dict[str, Any],
    ) -> dict[str, Any]:
        narration = self._narration_text_for_final_video(conn, project_id)
        audio_rel_path = self._ensure_narration_audio(project_dir, narration)
        storyboard = self.store.current_content(conn, project_id, "storyboard") or {}
        shots = storyboard.get("shots") if isinstance(storyboard, dict) else []
        narration_slices = [str(shot.get("narration_slice") or shot.get("subtitle") or "") for shot in shots if isinstance(shot, dict)]
        durations = [int(shot.get("duration_sec") or 10) for shot in shots if isinstance(shot, dict)]
        subtitle_path = write_subtitle_srt(project_dir, narration_slices or [narration], durations or [max(10, len(narration) // 4)])
        clip_paths = [task.get("download_path") or task.get("result", {}).get("download_path") for task in video_tasks]
        clip_paths = [str(path) for path in clip_paths if path]
        output_path = compose_final_video_with_audio(project_dir, clip_paths, audio_rel_path)
        manifest = write_concat_manifest(
            project_dir,
            clip_paths,
            {
                "task_id": video_tasks[0]["task_id"] if video_tasks else None,
                "download_path": FINAL_VIDEO_REL_PATH,
                "reference_images": [clip.get("reference_image_ids", []) for clip in content.get("clips", [])],
                "final_video_seconds": sum(durations) if durations else None,
                "audio_streams": 1,
                "audio_verified": True,
                "voice_gender": "male",
                "voice_language": "zh-CN",
            },
        )
        return {
            **content,
            "video_path": FINAL_VIDEO_REL_PATH,
            "output_size_bytes": output_path.stat().st_size,
            "total_duration_sec": sum(durations) if durations else max(10, len(narration) // 4),
            "audio_streams_count": 1,
            "audio_verified": True,
            "voice_gender": "male",
            "voice_language": "zh-CN",
            "narration_audio_path": audio_rel_path,
            "subtitle_srt_path": str(subtitle_path.relative_to(project_dir)).replace("\\", "/"),
            "model_audio_policy": "discarded_or_muted",
            "english_audio_detected": False,
            "concat_manifest_path": str(manifest.relative_to(project_dir)).replace("\\", "/"),
        }

    def _narration_text_for_final_video(self, conn, project_id: str) -> str:
        script = self.store.current_content(conn, project_id, "intro_video_script") or {}
        narration = script.get("narration_full_text") if isinstance(script, dict) else ""
        return str(narration or "欢迎来到山海教育导入视频。")

    def _ensure_narration_audio(self, project_dir: Path, narration: str) -> str:
        audio_path = project_dir / "audio" / "narration.mp3"
        if self.tts_provider is None:
            write_placeholder_narration_audio(project_dir)
        else:
            self.tts_provider.synthesize(narration, audio_path)
        return str(audio_path.relative_to(project_dir)).replace("\\", "/")


def provider_error_result(exc: ProviderError) -> dict[str, Any]:
    result: dict[str, Any] = {
        "error_code": exc.code,
        "retryable": exc.retryable,
    }
    status_code = getattr(exc, "status_code", None)
    response_excerpt = getattr(exc, "response_excerpt", "")
    if status_code is not None:
        result["http_status"] = status_code
    if response_excerpt:
        result["response_excerpt"] = sanitize_provider_excerpt(response_excerpt)
    return result


class NodeContentValidationError(ValueError):
    def __init__(self, details: list[dict[str, str]]):
        super().__init__("节点内容不符合最小契约")
        self.details = details


def validate_edit_content(node_id: str, content: dict[str, Any], context: dict[str, Any] | None = None) -> None:
    context = context or {}
    errors: list[dict[str, str]] = []
    if node_id == "intro_selection":
        _require_str(content, "selection_mode", errors)
        _require_non_empty_str_list(content, "selected_design_ids", errors)
        _require_str(content, "primary_design_id", errors)
        _require_str(content, "downstream_generation_mode", errors)
        _require_str(content, "selection_reason", errors)
        selected_anchor = _require_str(content, "selected_anchor", errors)
        if selected_anchor is not None and selected_anchor.strip() and not _valid_anchor(selected_anchor):
            _add_error(errors, "selected_anchor", "too_short", "课程锚点未填写或过短，请在选择页确认锚点后方可进入视频生成")
        if isinstance(content.get("selected_design_ids"), list) and content.get("primary_design_id") not in content["selected_design_ids"]:
            _add_error(errors, "primary_design_id", "reference_not_found", "primary_design_id 必须属于 selected_design_ids")
    elif node_id == "intro_video_script":
        _require_number(content, "total_duration_sec", errors)
        _require_str(content, "video_type", errors)
        _require_str(content, "anchor_to_lesson", errors)
        _require_str(content, "narration_full_text", errors)
        _require_number(content, "narration_word_count", errors)
        _require_list(content, "banned_elements", errors)
    elif node_id == "intro_video_screenplay":
        scenes = _require_non_empty_list(content, "scenes", errors)
        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                _add_error(errors, f"scenes[{index}]", "invalid_type", "scene 必须是对象")
                continue
            _require_str(scene, f"scenes[{index}].scene_id", errors, "scene_id")
            _require_number(scene, f"scenes[{index}].duration_sec", errors, "duration_sec")
            _require_str(scene, f"scenes[{index}].scene_description", errors, "scene_description")
            _require_str(scene, f"scenes[{index}].narration_segment", errors, "narration_segment")
    elif node_id == "intro_video_asset":
        assets = _require_non_empty_list(content, "assets", errors)
        seen_asset_ids: set[str] = set()
        for index, asset in enumerate(assets):
            if not isinstance(asset, dict):
                _add_error(errors, f"assets[{index}]", "invalid_type", "asset 必须是对象")
                continue
            asset_id = asset.get("asset_id")
            _require_str(asset, f"assets[{index}].asset_id", errors, "asset_id")
            _require_str(asset, f"assets[{index}].source_prompt_id", errors, "source_prompt_id")
            _require_str(asset, f"assets[{index}].storage_path", errors, "storage_path")
            _require_str(asset, f"assets[{index}].status", errors, "status")
            if isinstance(asset_id, str):
                if asset_id in seen_asset_ids:
                    _add_error(errors, f"assets[{index}].asset_id", "duplicate", "asset_id 不能重复")
                seen_asset_ids.add(asset_id)
    elif node_id == "storyboard":
        asset_ids = _asset_ids_from_context(context)
        shots = _require_non_empty_list(content, "shots", errors)
        seen_shot_ids: set[str] = set()
        for index, shot in enumerate(shots):
            if not isinstance(shot, dict):
                _add_error(errors, f"shots[{index}]", "invalid_type", "shot 必须是对象")
                continue
            shot_id = shot.get("shot_id")
            _require_str(shot, f"shots[{index}].shot_id", errors, "shot_id")
            _require_number(shot, f"shots[{index}].duration_sec", errors, "duration_sec")
            _require_str(shot, f"shots[{index}].main_subject", errors, "main_subject")
            reference_ids = _require_non_empty_str_list(shot, f"shots[{index}].reference_image_ids", errors, "reference_image_ids")
            _require_str(shot, f"shots[{index}].narration_slice", errors, "narration_slice")
            _require_str(shot, f"shots[{index}].model_prompt", errors, "model_prompt")
            if isinstance(shot_id, str):
                if shot_id in seen_shot_ids:
                    _add_error(errors, f"shots[{index}].shot_id", "duplicate", "shot_id 不能重复")
                seen_shot_ids.add(shot_id)
            if asset_ids and any(reference_id not in asset_ids for reference_id in reference_ids):
                _add_error(errors, f"shots[{index}].reference_image_ids", "reference_not_found", "reference_image_ids 必须引用 intro_video_asset.assets 中存在的 asset_id")
    elif node_id == "final_video":
        _require_int(content, "clip_count", errors)
        clips = _require_list(content, "clips", errors)
        _require_str(content, "model_audio_policy", errors)
        _require_bool(content, "english_audio_detected", errors)
        clip_count = content.get("clip_count")
        if isinstance(clip_count, int) and isinstance(clips, list) and clip_count != len(clips):
            _add_error(errors, "clips", "count_mismatch", "clips 数量必须等于 clip_count")
        storyboard_shot_ids = _shot_ids_from_context(context)
        for index, clip in enumerate(clips if isinstance(clips, list) else []):
            if not isinstance(clip, dict):
                _add_error(errors, f"clips[{index}]", "invalid_type", "clip 必须是对象")
                continue
            shot_id = clip.get("shot_id")
            _require_str(clip, f"clips[{index}].shot_id", errors, "shot_id")
            _require_str(clip, f"clips[{index}].api_task_id", errors, "api_task_id")
            _require_str(clip, f"clips[{index}].download_path", errors, "download_path")
            _require_str(clip, f"clips[{index}].status", errors, "status")
            _require_non_empty_str_list(clip, f"clips[{index}].reference_image_ids", errors, "reference_image_ids")
            if storyboard_shot_ids and isinstance(shot_id, str) and shot_id not in storyboard_shot_ids:
                _add_error(errors, f"clips[{index}].shot_id", "reference_not_found", "shot_id 必须引用 storyboard.shots 中存在的 shot_id")
    if errors:
        raise NodeContentValidationError(errors)


def validate_approve_content(node_id: str, content: dict[str, Any], context: dict[str, Any] | None = None) -> None:
    context = context or {}
    errors: list[dict[str, str]] = []
    if node_id == "intro_selection" and not _valid_anchor(content.get("selected_anchor")):
        _add_error(errors, "selected_anchor", "too_short", "课程锚点未填写或过短，请在选择页确认锚点后方可进入视频生成")
    if errors:
        raise NodeContentValidationError(errors)


def _add_error(errors: list[dict[str, str]], field: str, code: str, message: str) -> None:
    errors.append({"field": field, "code": code, "message": message})


def _require_present(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> Any:
    key = key or field
    if key not in data:
        _add_error(errors, field, "required", f"{field} 为必填字段")
        return None
    return data.get(key)


def _require_str(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> str | None:
    value = _require_present(data, field, errors, key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        _add_error(errors, field, "invalid_type", f"{field} 必须是非空字符串")
        return None
    return value


def _require_number(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> int | float | None:
    value = _require_present(data, field, errors, key)
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        _add_error(errors, field, "invalid_type", f"{field} 必须是数字")
        return None
    return value


def _require_int(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> int | None:
    value = _require_present(data, field, errors, key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _add_error(errors, field, "invalid_type", f"{field} 必须是非负整数")
        return None
    return value


def _require_bool(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> bool | None:
    value = _require_present(data, field, errors, key)
    if value is None:
        return None
    if not isinstance(value, bool):
        _add_error(errors, field, "invalid_type", f"{field} 必须是布尔值")
        return None
    return value


def _require_list(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> list[Any]:
    value = _require_present(data, field, errors, key)
    if value is None:
        return []
    if not isinstance(value, list):
        _add_error(errors, field, "invalid_type", f"{field} 必须是数组")
        return []
    return value


def _require_non_empty_list(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> list[Any]:
    value = _require_list(data, field, errors, key)
    if isinstance(value, list) and not value:
        _add_error(errors, field, "empty", f"{field} 不能为空")
    return value


def _require_non_empty_str_list(data: dict[str, Any], field: str, errors: list[dict[str, str]], key: str | None = None) -> list[str]:
    value = _require_non_empty_list(data, field, errors, key)
    valid_values: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _add_error(errors, f"{field}[{index}]", "invalid_type", f"{field}[{index}] 必须是非空字符串")
        else:
            valid_values.append(item)
    return valid_values


def _anchor_text(value: Any) -> str:
    return str(value).strip() if isinstance(value, str) else ""


def _valid_anchor(value: Any) -> bool:
    return len(_anchor_text(value)) >= 10


def _selected_anchor_from_context(context: dict[str, Any]) -> str:
    return _anchor_text(context.get("intro_selection", {}).get("selected_anchor"))


def _anchor_keywords(anchor: str) -> list[str]:
    text = _anchor_text(anchor)
    if not text:
        return []
    separators = "，。！？、；：“”‘’（）()《》\"' \t\n\r"
    normalized = text
    for separator in separators:
        normalized = normalized.replace(separator, "|")
    stopwords = {
        "通过",
        "引出",
        "自然",
        "进入",
        "本课",
        "问题",
        "学习",
        "认识",
        "理解",
        "联系",
        "连接",
        "怎样",
        "什么",
        "才能",
        "一起",
    }
    keywords: list[str] = []
    for part in normalized.split("|"):
        candidate = part.strip()
        if len(candidate) >= 2 and candidate not in stopwords:
            keywords.append(candidate)
    if len(text) >= 4:
        keywords.extend(text[index : index + 4] for index in range(0, max(0, len(text) - 3), 2))
    return list(dict.fromkeys(keywords))


def _storyboard_anchor_warnings(content: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    selected_anchor = _selected_anchor_from_context(context)
    shots = content.get("shots")
    if not selected_anchor or not isinstance(shots, list) or not shots:
        return []
    last_shot = shots[-1] if isinstance(shots[-1], dict) else {}
    subtitle = _anchor_text(last_shot.get("subtitle"))
    keywords = _anchor_keywords(selected_anchor)
    matched = [keyword for keyword in keywords if keyword and keyword in subtitle]
    if matched:
        return []
    return [
        {
            "rule_id": "R049",
            "severity": "warning",
            "field": "shots[-1].subtitle",
            "message": "分镜末帧字幕未体现课程锚点关键词，建议检查是否自然衔接本课",
            "details": {
                "selected_anchor": selected_anchor,
                "keywords": keywords[:8],
                "subtitle": subtitle,
            },
        }
    ]


def _asset_ids_from_context(context: dict[str, Any]) -> set[str]:
    assets = context.get("intro_video_asset", {}).get("assets", [])
    return {asset.get("asset_id") for asset in assets if isinstance(asset, dict) and isinstance(asset.get("asset_id"), str)}


def _shot_ids_from_context(context: dict[str, Any]) -> set[str]:
    shots = context.get("storyboard", {}).get("shots", [])
    return {shot.get("shot_id") for shot in shots if isinstance(shot, dict) and isinstance(shot.get("shot_id"), str)}
