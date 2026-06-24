from pathlib import Path
from typing import Any
import json

from fastapi import Depends, FastAPI, Form, Header, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .models import FeedbackRequest, NodeApproveRequest, NodeEditRequest, NodeGenerateRequest, ProjectCreateRequest, ProjectUpdateRequest, dump_model
from .providers import DeepSeekTextProvider, FakeProvider, MinimaxTextProvider, MinimaxTTSProvider, NewApiImageProvider, OctoVideoProvider, ProviderError, sanitize_provider_excerpt
from .control_plane import ControlPlaneStore
from .lesson_plan_library import LessonPlanLibraryStore
from .prompt_registry import PromptRegistry, PromptStore
from .responses import fail, ok
from .rule_executor import RuleHardBlockError, RuleWarningError
from .security import require_api_token
from .services import FeedbackPayloadError, FeedbackTypeError, NodeContentValidationError, WorkflowService
from .settings import Settings
from .state_engine import NodeSkippedError
from .store import ProjectStore
from .textbook_library import TextbookAssetExtractionError, TextbookAssetNotTrustedError, TextbookLibraryStore
from .workflow_config import WorkflowConfig


def create_app(overrides: dict[str, Any] | None = None) -> FastAPI:
    settings = Settings.from_overrides(overrides)
    workflow = WorkflowConfig(Path(settings.workflow_root))
    store = ProjectStore(Path(settings.storage_root))
    textbook_library = TextbookLibraryStore(Path(settings.storage_root))
    textbook_library.ensure_seeded()
    lesson_plan_library = LessonPlanLibraryStore(Path(settings.storage_root))
    control_plane = ControlPlaneStore(Path(settings.storage_root) / "control_plane.db", Path(settings.workflow_root) / "rules")
    control_plane.ensure_seeded(actor="system")
    for existing_project in store.list_projects():
        control_plane.bind_project_to_active_rule_set(existing_project["project_id"])
    provider_mode = settings.provider_mode.lower()
    video_provider_mode = settings.video_provider_mode.lower()
    image_provider_mode = settings.image_provider_mode.lower()
    if provider_mode == "minimax":
        provider = MinimaxTextProvider(settings.minmax_api_key, settings.minmax_base_url, settings.minmax_text_model)
    elif provider_mode in {"real", "deepseek"}:
        provider = DeepSeekTextProvider(settings.deepseek_api_key, settings.deepseek_base_url, settings.deepseek_model)
    else:
        provider = FakeProvider()
    video_provider = OctoVideoProvider(settings.octo_api_key, settings.octo_base_url) if video_provider_mode == "real" else None
    image_provider = (
        NewApiImageProvider(settings.imagegen_api_key, settings.imagegen_base_url, settings.imagegen_model)
        if image_provider_mode == "real"
        else None
    )
    tts_provider = (
        MinimaxTTSProvider(
            settings.minmax_api_key,
            settings.minmax_base_url,
            settings.minmax_tts_model,
            settings.minmax_tts_voice_id,
        )
        if settings.tts_provider_mode.lower() == "real"
        else None
    )
    prompt_store = PromptStore(Path(settings.storage_root) / "prompt_registry.db")
    prompt_registry = PromptRegistry(prompt_store, Path(settings.workflow_root) / "prompts")
    prompt_registry.ensure_seeded(created_by="system")
    service = WorkflowService(
        store,
        provider,
        video_provider,
        image_provider,
        workflow,
        control_plane=control_plane,
        textbook_library=textbook_library,
        lesson_plan_library=lesson_plan_library,
        prompt_registry=prompt_registry,
        prompt_root=Path(settings.workflow_root) / "prompts",
        tts_provider=tts_provider,
        video_model=settings.video_model,
    )

    app = FastAPI(title="ShanHaiEdu Video MVP API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.state.settings = settings
    app.state.workflow = workflow
    app.state.store = store
    app.state.service = service
    app.state.control_plane = control_plane
    app.state.textbook_library = textbook_library
    app.state.lesson_plan_library = lesson_plan_library
    app.state.prompt_store = prompt_store
    app.state.prompt_registry = prompt_registry
    protected = [Depends(require_api_token(settings))]

    def require_admin(authorization: str | None = Header(default=None)) -> None:
        if not settings.backend_api_token:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "资源不存在"})
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "资源不存在"})
        token = authorization.removeprefix("Bearer ").strip()
        if token != settings.backend_api_token:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "资源不存在"})

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(_request, exc):
        return fail(
            422,
            "REQUEST_VALIDATION_FAILED",
            "请求参数不符合接口契约",
            retryable=False,
            details=exc.errors(),
        )

    @app.exception_handler(HTTPException)
    def http_exception_handler(_request, exc):
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        return fail(
            exc.status_code,
            str(detail.get("code") or "HTTP_ERROR"),
            str(detail.get("message") or "请求失败"),
            retryable=False,
        )

    @app.get("/health")
    def health():
        return ok({"status": "ok", "workflow_version": workflow.version})

    @app.get("/workflow")
    def get_workflow():
        return ok({"version": workflow.version, "nodes": workflow.nodes})

    @app.get("/textbook-library", dependencies=protected)
    def get_textbook_library():
        return ok(service.textbook_library())

    @app.post("/textbook-library/uploads", dependencies=protected)
    def upload_textbook_to_library(file: UploadFile):
        try:
            return ok(service.upload_textbook_to_library(file))
        except ValueError as exc:
            return fail(400, "TEXTBOOK_UPLOAD_INVALID", str(exc), retryable=False)

    @app.get("/textbook-library/jobs/{job_id}", dependencies=protected)
    def get_textbook_library_job(job_id: str):
        try:
            return ok(service.textbook_library_job(job_id))
        except KeyError:
            return fail(404, "TEXTBOOK_JOB_NOT_FOUND", "教材解析任务不存在", retryable=False)

    @app.get("/textbook-library/{textbook_id}/knowledge-points", dependencies=protected)
    def get_textbook_knowledge_points(textbook_id: str):
        try:
            return ok(service.textbook_library_knowledge_points(textbook_id))
        except ValueError as exc:
            return fail(404, "TEXTBOOK_NOT_FOUND", str(exc), retryable=False)

    @app.get("/textbook-library/{textbook_id}/knowledge-points/{knowledge_point_id}/assets", dependencies=protected)
    def get_textbook_knowledge_point_assets(textbook_id: str, knowledge_point_id: str):
        try:
            return ok(service.textbook_library_asset_package(textbook_id, knowledge_point_id))
        except ValueError as exc:
            return fail(404, "TEXTBOOK_ASSET_NOT_FOUND", str(exc), retryable=False)

    @app.post("/textbook-library/{textbook_id}/split", dependencies=protected)
    def split_textbook_knowledge_point_assets(textbook_id: str, payload: dict[str, Any] | None = None):
        try:
            knowledge_point_ids = (payload or {}).get("knowledge_point_ids")
            return ok(service.split_textbook_assets(textbook_id, knowledge_point_ids if isinstance(knowledge_point_ids, list) else None))
        except ValueError as exc:
            return fail(404, "TEXTBOOK_ASSET_NOT_FOUND", str(exc), retryable=False)

    @app.post("/textbook-library/{textbook_id}/assets/extract", dependencies=protected)
    def extract_textbook_knowledge_point_assets_batch(textbook_id: str, payload: dict[str, Any] | None = None):
        try:
            knowledge_point_ids = (payload or {}).get("knowledge_point_ids")
            return ok(service.extract_textbook_assets(textbook_id, knowledge_point_ids if isinstance(knowledge_point_ids, list) else None))
        except ValueError as exc:
            return fail(404, "TEXTBOOK_ASSET_NOT_FOUND", str(exc), retryable=False)

    @app.post("/textbook-library/{textbook_id}/knowledge-points/{knowledge_point_id}/assets/extract", dependencies=protected)
    def extract_textbook_knowledge_point_assets(textbook_id: str, knowledge_point_id: str):
        try:
            return ok(service.extract_textbook_asset(textbook_id, knowledge_point_id))
        except TextbookAssetExtractionError as exc:
            return fail(409, "TEXTBOOK_ASSET_EXTRACT_FAILED", str(exc), retryable=False, details=exc.asset)
        except ValueError as exc:
            return fail(404, "TEXTBOOK_ASSET_NOT_FOUND", str(exc), retryable=False)

    @app.post("/textbook-library/assets/{asset_id}/confirm", dependencies=protected)
    def confirm_textbook_asset(asset_id: str, payload: dict[str, Any] | None = None):
        try:
            return ok(service.confirm_textbook_asset(asset_id, reviewer=str((payload or {}).get("reviewer") or "")))
        except KeyError:
            return fail(404, "TEXTBOOK_ASSET_NOT_FOUND", "教材资产不存在", retryable=False)
        except TextbookAssetNotTrustedError as exc:
            return fail(409, "TEXTBOOK_ASSET_NOT_TRUSTED", str(exc), retryable=False, details=exc.asset)

    @app.get("/lesson-plan-library", dependencies=protected)
    def get_lesson_plan_library(textbook_id: str | None = None, knowledge_point_id: str | None = None):
        return ok(service.lesson_plan_library(textbook_id=textbook_id, knowledge_point_id=knowledge_point_id))

    @app.get("/lesson-plan-library/{lesson_plan_id}", dependencies=protected)
    def get_lesson_plan_library_item(lesson_plan_id: str):
        try:
            return ok(service.lesson_plan_library_item(lesson_plan_id))
        except KeyError:
            return fail(404, "LESSON_PLAN_NOT_FOUND", "教案不存在", retryable=False)

    @app.post("/lesson-plan-library/uploads", dependencies=protected)
    def upload_lesson_plan_to_library(
        file: UploadFile,
        textbook_id: str | None = Form(default=None),
        textbook_version_id: str | None = Form(default=None),
        knowledge_point_id: str | None = Form(default=None),
        created_by: str = Form(default="admin"),
    ):
        try:
            return ok(
                service.upload_lesson_plan_to_library(
                    file,
                    textbook_id=textbook_id,
                    textbook_version_id=textbook_version_id,
                    knowledge_point_id=knowledge_point_id,
                    created_by=created_by,
                )
            )
        except ValueError as exc:
            return fail(400, "LESSON_PLAN_UPLOAD_INVALID", str(exc), retryable=False)

    @app.post("/lesson-plan-library/import/from-project", dependencies=protected)
    def import_lesson_plan_from_project(payload: dict[str, Any]):
        try:
            return ok(
                service.import_lesson_plan_from_project(
                    str(payload.get("project_id") or ""),
                    created_by=str(payload.get("created_by") or "user"),
                )
            )
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在", retryable=False)
        except ValueError as exc:
            return fail(409, "LESSON_PLAN_NOT_READY", str(exc), retryable=False)

    @app.get("/admin/prompts/templates", dependencies=[Depends(require_admin)])
    def admin_prompt_templates():
        return ok(prompt_store.list_templates())

    @app.get("/admin/rules", dependencies=[Depends(require_admin)])
    def admin_rules():
        return ok(control_plane.list_rules())

    @app.get("/admin/rules/audit", dependencies=[Depends(require_admin)])
    def admin_rules_audit():
        return ok(control_plane.audit_log())

    @app.get("/admin/rules/{rule_id}", dependencies=[Depends(require_admin)])
    def admin_rule(rule_id: str):
        try:
            return ok(control_plane.get_rule(rule_id))
        except KeyError:
            return fail(404, "RULE_NOT_FOUND", "规则不存在", retryable=False)

    @app.post("/admin/rules/{rule_id}/versions", dependencies=[Depends(require_admin)])
    def admin_create_rule_version(rule_id: str, payload: dict[str, Any]):
        try:
            return ok(
                control_plane.create_rule_version(
                    rule_id,
                    severity=str(payload.get("severity") or "warning"),
                    action_message=str(payload.get("action_message") or ""),
                    check_json=payload.get("check_json") if isinstance(payload.get("check_json"), dict) else {},
                    enabled=bool(payload.get("enabled", True)),
                    created_by=str(payload.get("created_by") or "admin"),
                    notes=payload.get("notes"),
                )
            )
        except KeyError:
            return fail(404, "RULE_NOT_FOUND", "规则不存在", retryable=False)
        except ValueError as exc:
            return fail(400, "RULE_VERSION_INVALID", str(exc), retryable=False)

    @app.post("/admin/rules/{rule_id}/activate", dependencies=[Depends(require_admin)])
    def admin_activate_rule_version(rule_id: str, payload: dict[str, Any]):
        try:
            return ok(
                control_plane.activate_rule_version(
                    rule_id,
                    str(payload.get("version_id") or ""),
                    actor=str(payload.get("actor") or "admin"),
                    notes=payload.get("notes"),
                )
            )
        except KeyError:
            return fail(404, "RULE_VERSION_NOT_FOUND", "规则版本不存在", retryable=False)

    @app.post("/admin/rules/{rule_id}/rollback", dependencies=[Depends(require_admin)])
    def admin_rollback_rule_version(rule_id: str, payload: dict[str, Any]):
        try:
            return ok(
                control_plane.rollback_rule(
                    rule_id,
                    str(payload.get("version_id") or ""),
                    actor=str(payload.get("actor") or "admin"),
                    notes=payload.get("notes"),
                )
            )
        except KeyError:
            return fail(404, "RULE_VERSION_NOT_FOUND", "规则版本不存在", retryable=False)

    @app.get("/admin/workflow/graph", dependencies=[Depends(require_admin)])
    def admin_workflow_graph():
        rules_by_node: dict[str, list[dict[str, Any]]] = {}
        for item in control_plane.list_rules():
            active = item.get("active_version") or {}
            rules_by_node.setdefault(str(item.get("trigger_node")), []).append(
                {
                    "rule_id": item["rule_id"],
                    "title": item.get("title"),
                    "trigger_event": item.get("trigger_event"),
                    "severity": active.get("severity"),
                    "enabled": active.get("enabled"),
                    "version_id": active.get("version_id"),
                }
            )
        return ok(
            {
                "version": workflow.version,
                "editable": False,
                "edit_scope": "rules_and_prompts_only",
                "nodes": [
                    {
                        "id": node.get("id"),
                        "title": node.get("title"),
                        "step": node.get("step"),
                        "branch": node.get("branch"),
                        "depends_on": list(node.get("depends_on") or []),
                        "rules": rules_by_node.get(str(node.get("id")), []),
                    }
                    for node in workflow.nodes
                ],
            }
        )

    @app.get("/admin/prompts/templates/{template_id}", dependencies=[Depends(require_admin)])
    def admin_prompt_template(template_id: str):
        return ok({"template_id": template_id, "versions": prompt_store.list_versions(template_id)})

    @app.post("/admin/prompts/templates/{template_id}/versions", dependencies=[Depends(require_admin)])
    def admin_create_prompt_version(template_id: str, payload: dict[str, Any]):
        body = str(payload.get("body") or "")
        status = str(payload.get("status") or "draft")
        if status not in {"draft", "active", "canary", "archived"}:
            return fail(400, "PROMPT_STATUS_INVALID", "prompt status 不合法", retryable=False)
        variables = payload.get("variables") if isinstance(payload.get("variables"), list) else []
        version = prompt_store.create_version(
            template_id=template_id,
            body=body,
            variables=[str(item) for item in variables],
            status=status,
            canary_percent=int(payload.get("canary_percent") or 0),
            created_by=str(payload.get("created_by") or "admin"),
            notes=payload.get("notes"),
        )
        prompt_registry.invalidate()
        return ok(version)

    @app.get("/video/capabilities")
    def get_video_capabilities():
        try:
            data = json.loads(Path(settings.capabilities_path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return fail(404, "CAPABILITIES_NOT_FOUND", "未找到视频能力配置")
        models = data.get("capabilities", data.get("models", []))
        return ok({**data, "models": models})

    @app.get("/schemas/{schema_name}", dependencies=protected)
    def get_schema(schema_name: str):
        try:
            return ok(workflow.schema(schema_name))
        except FileNotFoundError:
            return fail(404, "SCHEMA_NOT_FOUND", f"未找到 schema：{schema_name}")

    @app.get("/rules/coverage", dependencies=protected)
    def get_rule_coverage():
        return ok(service.rule_executor.coverage())

    @app.post("/projects", dependencies=protected)
    def create_project(payload: ProjectCreateRequest):
        project_payload = dump_model(payload)
        reference_lesson_plan_id = project_payload.get("reference_lesson_plan_id")
        if reference_lesson_plan_id:
            try:
                project_payload["_reference_lesson_plan"] = service.lesson_plan_library_item(reference_lesson_plan_id)
            except KeyError:
                return fail(404, "LESSON_PLAN_NOT_FOUND", "引用教案不存在", retryable=False)
        project = store.create_project(project_payload, workflow)
        control_plane.bind_project_to_active_rule_set(project["project_id"])
        return ok(project)

    @app.get("/projects", dependencies=protected)
    def list_projects():
        return ok(store.list_projects())

    @app.get("/projects/{project_id}", dependencies=protected)
    def get_project(project_id: str):
        try:
            return ok(store.get_project(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.patch("/projects/{project_id}", dependencies=protected)
    def update_project(project_id: str, payload: ProjectUpdateRequest):
        try:
            return ok(store.update_project(project_id, dump_model(payload, exclude_none=True)))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/manifest", dependencies=protected)
    def get_manifest(project_id: str):
        try:
            return ok(store.manifest(project_id, workflow, service.rule_runtime_summary()))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/workspace", dependencies=protected)
    def get_workspace_user_flow(project_id: str):
        try:
            return ok(service.workspace_user_flow(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/flywheel", dependencies=protected)
    def get_flywheel(project_id: str):
        try:
            return ok(service.flywheel_events(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.post("/projects/{project_id}/feedback", dependencies=protected)
    def record_feedback(project_id: str, payload: FeedbackRequest):
        try:
            return ok(service.record_feedback(project_id, payload.feedback_type, payload.payload))
        except FeedbackTypeError as exc:
            return fail(400, "FEEDBACK_TYPE_INVALID", str(exc), retryable=False)
        except FeedbackPayloadError as exc:
            return fail(400, "FEEDBACK_PAYLOAD_INVALID", str(exc), retryable=False)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.post("/projects/{project_id}/textbook", dependencies=protected)
    def upload_textbook(project_id: str, file: UploadFile):
        try:
            return ok(store.upload_textbook(project_id, file))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.post("/projects/{project_id}/textbook/from-library/{textbook_id}", dependencies=protected)
    def attach_textbook_from_library(project_id: str, textbook_id: str):
        try:
            source_pdf = textbook_library.source_pdf_path(textbook_id)
            return ok(store.attach_textbook_file(project_id, source_pdf, source_pdf.name))
        except ValueError:
            return fail(404, "TEXTBOOK_NOT_FOUND", "教材不存在", retryable=False)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.post("/projects/{project_id}/nodes/{node_id}/generate", dependencies=protected)
    def generate_node(project_id: str, node_id: str, payload: NodeGenerateRequest | None = None):
        try:
            return ok(service.generate_node(project_id, node_id, payload.to_options() if payload else {}))
        except NodeSkippedError as exc:
            return fail(409, "NODE_SKIPPED", str(exc), retryable=False)
        except PermissionError as exc:
            return fail(409, "UPSTREAM_NOT_APPROVED", str(exc), retryable=False)
        except ProviderError as exc:
            details = {}
            if getattr(exc, "status_code", None) is not None:
                details["http_status"] = exc.status_code
            if getattr(exc, "response_excerpt", ""):
                details["response_excerpt"] = sanitize_provider_excerpt(exc.response_excerpt)
            return fail(502, exc.code, str(exc), retryable=exc.retryable, details=details or None)
        except ValueError as exc:
            return fail(400, "GENERATION_INPUT_INVALID", str(exc), retryable=False)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.post("/projects/{project_id}/nodes/{node_id}/edit", dependencies=protected)
    def edit_node(project_id: str, node_id: str, payload: NodeEditRequest):
        try:
            return ok(service.edit_node(project_id, node_id, payload.content))
        except NodeContentValidationError as exc:
            return fail(400, "NODE_CONTENT_INVALID", str(exc), retryable=False, details=exc.details)
        except RuleHardBlockError as exc:
            return fail(400, exc.code, str(exc), retryable=False, details=exc.details)
        except NodeSkippedError as exc:
            return fail(409, "NODE_SKIPPED", str(exc), retryable=False)
        except PermissionError as exc:
            return fail(409, "UPSTREAM_NOT_APPROVED", str(exc), retryable=False)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.post("/projects/{project_id}/nodes/{node_id}/approve", dependencies=protected)
    def approve_node(project_id: str, node_id: str, payload: NodeApproveRequest | None = None):
        try:
            return ok(service.approve_node(project_id, node_id, dump_model(payload, exclude_none=True) if payload else {}))
        except NodeContentValidationError as exc:
            return fail(400, "NODE_CONTENT_INVALID", str(exc), retryable=False, details=exc.details)
        except RuleWarningError as exc:
            return fail(409, "RULE_WARNING", str(exc), retryable=False, details=exc.details)
        except RuleHardBlockError as exc:
            return fail(409, exc.code, str(exc), retryable=False, details=exc.details)
        except PermissionError as exc:
            return fail(409, "UPSTREAM_NOT_APPROVED", str(exc), retryable=False)
        except ValueError as exc:
            return fail(409, "NODE_NOT_READY", str(exc), retryable=False)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.post("/projects/{project_id}/nodes/{node_id}/retry", dependencies=protected)
    def retry_node(project_id: str, node_id: str):
        try:
            return ok(service.retry_node(project_id, node_id))
        except NodeSkippedError as exc:
            return fail(409, "NODE_SKIPPED", str(exc), retryable=False)
        except PermissionError as exc:
            return fail(409, "UPSTREAM_NOT_APPROVED", str(exc), retryable=False)
        except ProviderError as exc:
            details = {}
            if getattr(exc, "status_code", None) is not None:
                details["http_status"] = exc.status_code
            if getattr(exc, "response_excerpt", ""):
                details["response_excerpt"] = sanitize_provider_excerpt(exc.response_excerpt)
            return fail(502, exc.code, str(exc), retryable=exc.retryable, details=details or None)
        except ValueError as exc:
            return fail(400, "GENERATION_INPUT_INVALID", str(exc), retryable=False)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.get("/projects/{project_id}/nodes/{node_id}", dependencies=protected)
    def get_node(project_id: str, node_id: str):
        try:
            return ok(store.node_detail(project_id, node_id, workflow, service.rule_runtime_summary()))
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.get("/projects/{project_id}/nodes/{node_id}/versions", dependencies=protected)
    def get_versions(project_id: str, node_id: str):
        try:
            return ok(store.versions(project_id, node_id))
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.get("/projects/{project_id}/tasks", dependencies=protected)
    def get_tasks(project_id: str):
        try:
            return ok(store.tasks(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/tasks/{task_id}", dependencies=protected)
    def get_task(project_id: str, task_id: str):
        try:
            return ok(service.sync_task(project_id, task_id))
        except ProviderError as exc:
            details = {}
            if getattr(exc, "status_code", None) is not None:
                details["http_status"] = exc.status_code
            if getattr(exc, "response_excerpt", ""):
                details["response_excerpt"] = sanitize_provider_excerpt(exc.response_excerpt)
            return fail(502, exc.code, str(exc), retryable=exc.retryable, details=details or None)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.post("/projects/{project_id}/export/ppt", dependencies=protected)
    def export_ppt(project_id: str):
        try:
            return ok(service.export_ppt(project_id))
        except ValueError as exc:
            return fail(409, "PPT_ARTIFACT_NOT_READY", str(exc), retryable=False)
        except RuntimeError as exc:
            return fail(500, "PPT_EXPORT_FAILED", str(exc), retryable=False)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/exports/{filename}", dependencies=protected)
    def download_export(project_id: str, filename: str):
        try:
            project = store.get_project(project_id)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")
        safe_name = Path(filename).name
        path = Path(project["project_dir"]) / "exports" / safe_name
        if not path.exists() or path.suffix.lower() != ".pptx":
            return fail(404, "EXPORT_NOT_FOUND", "导出文件不存在")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=safe_name,
        )

    @app.get("/projects/{project_id}/outputs/final_video.mp4", dependencies=protected)
    def download_final_video(project_id: str):
        try:
            project = store.get_project(project_id)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")
        path = Path(project["project_dir"]) / "outputs" / "final_video.mp4"
        if not path.exists():
            return fail(404, "OUTPUT_NOT_FOUND", "最终视频文件不存在")
        return FileResponse(path, media_type="video/mp4", filename="final_video.mp4")

    @app.get("/projects/{project_id}/clips/{filename}", dependencies=protected)
    def download_clip(project_id: str, filename: str):
        try:
            project = store.get_project(project_id)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")
        safe_name = Path(filename).name
        path = Path(project["project_dir"]) / "clips" / safe_name
        if not path.exists() or path.suffix.lower() != ".mp4":
            return fail(404, "CLIP_NOT_FOUND", "视频片段不存在")
        return FileResponse(path, media_type="video/mp4", filename=safe_name)

    @app.get("/projects/{project_id}/images/{filename}", dependencies=protected)
    def download_image(project_id: str, filename: str):
        try:
            project = store.get_project(project_id)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")
        safe_name = Path(filename).name
        path = Path(project["project_dir"]) / "assets" / "generated_images" / safe_name
        suffix = path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        if not path.exists() or suffix not in media_types:
            return fail(404, "IMAGE_NOT_FOUND", "图片文件不存在")
        return FileResponse(path, media_type=media_types[suffix], filename=safe_name)

    @app.get("/projects/{project_id}/files/{asset_path:path}", dependencies=protected)
    def download_project_asset(project_id: str, asset_path: str):
        try:
            project = store.get_project(project_id)
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")
        safe_parts = [part for part in Path(asset_path).parts if part not in {"", ".", ".."}]
        if not safe_parts:
            return fail(404, "ASSET_NOT_FOUND", "资产不存在")
        path = Path(project["project_dir"]).joinpath(*safe_parts)
        project_root = Path(project["project_dir"]).resolve()
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            return fail(404, "ASSET_NOT_FOUND", "资产不存在")
        if project_root not in [resolved, *resolved.parents] or not resolved.exists() or not resolved.is_file():
            return fail(404, "ASSET_NOT_FOUND", "资产不存在")
        media_types = {
            ".pdf": "application/pdf",
            ".md": "text/markdown; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
        }
        media_type = media_types.get(resolved.suffix.lower(), "application/octet-stream")
        return FileResponse(resolved, media_type=media_type, filename=resolved.name)

    @app.post("/projects/{project_id}/tasks/{task_id}/retry", dependencies=protected)
    def retry_task(project_id: str, task_id: str):
        try:
            return ok(service.retry_task(project_id, task_id))
        except ProviderError as exc:
            details = {}
            if getattr(exc, "status_code", None) is not None:
                details["http_status"] = exc.status_code
            if getattr(exc, "response_excerpt", ""):
                details["response_excerpt"] = sanitize_provider_excerpt(exc.response_excerpt)
            return fail(502, exc.code, str(exc), retryable=exc.retryable, details=details or None)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.get("/projects/{project_id}/assets", dependencies=protected)
    def get_assets(project_id: str):
        try:
            return ok(store.assets(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/assets/{asset_id}", dependencies=protected)
    def get_asset(project_id: str, asset_id: str):
        try:
            return ok(store.asset(project_id, asset_id))
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    return app


app = create_app()
