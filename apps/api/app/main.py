from pathlib import Path
from typing import Any
import json

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .models import FeedbackRequest, NodeApproveRequest, NodeEditRequest, NodeGenerateRequest, ProjectCreateRequest, dump_model
from .providers import DeepSeekTextProvider, FakeProvider, MinimaxTextProvider, MinimaxTTSProvider, NewApiImageProvider, OctoVideoProvider, ProviderError, sanitize_provider_excerpt
from .prompt_registry import PromptRegistry, PromptStore
from .responses import fail, ok
from .rule_executor import RuleHardBlockError, RuleWarningError
from .security import require_api_token
from .services import FeedbackPayloadError, FeedbackTypeError, NodeContentValidationError, WorkflowService
from .settings import Settings
from .store import ProjectStore
from .workflow_config import WorkflowConfig


def create_app(overrides: dict[str, Any] | None = None) -> FastAPI:
    settings = Settings.from_overrides(overrides)
    workflow = WorkflowConfig(Path(settings.workflow_root))
    store = ProjectStore(Path(settings.storage_root))
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

    @app.get("/admin/prompts/templates", dependencies=[Depends(require_admin)])
    def admin_prompt_templates():
        return ok(prompt_store.list_templates())

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

    @app.post("/projects", dependencies=protected)
    def create_project(payload: ProjectCreateRequest):
        return ok(store.create_project(dump_model(payload), workflow))

    @app.get("/projects", dependencies=protected)
    def list_projects():
        return ok(store.list_projects())

    @app.get("/projects/{project_id}", dependencies=protected)
    def get_project(project_id: str):
        try:
            return ok(store.get_project(project_id))
        except KeyError:
            return fail(404, "PROJECT_NOT_FOUND", "项目不存在")

    @app.get("/projects/{project_id}/manifest", dependencies=protected)
    def get_manifest(project_id: str):
        try:
            return ok(store.manifest(project_id))
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

    @app.post("/projects/{project_id}/nodes/{node_id}/generate", dependencies=protected)
    def generate_node(project_id: str, node_id: str, payload: NodeGenerateRequest | None = None):
        try:
            return ok(service.generate_node(project_id, node_id, payload.to_options() if payload else {}))
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
        except ValueError as exc:
            return fail(409, "NODE_NOT_READY", str(exc), retryable=False)
        except KeyError as exc:
            return fail(404, "NOT_FOUND", str(exc), retryable=False)

    @app.post("/projects/{project_id}/nodes/{node_id}/retry", dependencies=protected)
    def retry_node(project_id: str, node_id: str):
        return generate_node(project_id, node_id)

    @app.get("/projects/{project_id}/nodes/{node_id}", dependencies=protected)
    def get_node(project_id: str, node_id: str):
        try:
            return ok(store.node_detail(project_id, node_id))
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
