from pathlib import Path
from typing import Any
import http.client
import json
import threading
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.providers import DeepSeekTextProvider, MinimaxTextProvider, NewApiImageProvider, OctoVideoProvider, ProviderError
from app.services import normalize_node_content
from app.settings import Settings


def make_client(tmp_path: Path, overrides: dict[str, Any] | None = None) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(Path(__file__).resolve().parents[3] / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
            "capabilities_path": str(
                Path(__file__).resolve().parents[3]
                / "docs"
                / "api-research"
                / "octo-video"
                / "capabilities.json"
            ),
            **(overrides or {}),
        }
    )
    return TestClient(app)


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def _write_shared_visual_context(conn, project_id: str) -> None:
    conn.execute(
        "UPDATE node_state SET status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE project_id = ? AND node_id IN ('project_meta', 'project_config')",
        (project_id,),
    )
    store_content = {
        "visual_contract": {
            "palette": ["#0F766E", "#F59E0B", "#F8FAFC"],
            "style_keywords": ["非写实卡通", "生活化数学情境"],
            "font_preference": "Microsoft YaHei",
        },
        "character_dict": {
            "characters": [
                {
                    "character_id": "char_math_guide",
                    "name": "小山",
                    "identity": "非写实卡通数学引导员",
                    "view_front": "卡通正面形象",
                    "view_side": "卡通侧面形象",
                    "view_back": "卡通背面形象",
                    "outfit_lock": {"color": "teal", "style": "cartoon"},
                    "hair_lock": "简化发型",
                    "body_proportion": "3d_non_realistic_childlike_chibi",
                    "style_constraint": "3d_non_realistic",
                    "banned_keywords": ["真人", "photorealistic", "real child"],
                }
            ]
        },
    }
    for node_id, content in store_content.items():
        version_id = f"ver_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO node_versions
            (version_id, project_id, node_id, content_json, generated_by, provider, status, created_at, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (version_id, project_id, node_id, json.dumps(content, ensure_ascii=False), "fixture", "fixture", "approved"),
        )
        conn.execute(
            "UPDATE node_state SET status = 'approved', current_version_id = ?, updated_at = CURRENT_TIMESTAMP WHERE project_id = ? AND node_id = ?",
            (version_id, project_id, node_id),
        )


def test_video_capabilities_include_octo_models(tmp_path: Path):
    client = make_client(tmp_path)

    data = unwrap(client.get("/video/capabilities"))
    models = {item["model"]: item for item in data["models"]}

    assert models["sora-2-12s"]["max_seconds"] == 12
    assert models["omni_flash-10s"]["max_reference_images"] == 7
    assert models["veo_3_1-fast-fl"]["first_last_frame"] is True
    assert models["veo_3_1-fast-extend"]["extend"] is True
    assert all(item["query_requires_authorization"] for item in data["models"])


def test_settings_loads_project_imagegen_skill_env(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    skill_env = tmp_path / "skills" / "imagegen-myself" / ".env.local"
    skill_env.parent.mkdir(parents=True)
    skill_env.write_text(
        "NEWAPI_BASE_URL=https://image.example/v1\nNEWAPI_API_KEY=test-image-key\n",
        encoding="utf-8",
    )

    settings = Settings.from_overrides({})

    assert settings.imagegen_base_url == "https://image.example/v1"
    assert settings.imagegen_api_key == "test-image-key"


def test_settings_uses_imagegen_skill_primary_credentials_first(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    skill_env = tmp_path / "skills" / "imagegen-myself" / ".env.local"
    skill_env.parent.mkdir(parents=True)
    skill_env.write_text(
        "\n".join(
            [
                "NEWAPI_BASE_URL=https://newapi.example",
                "NEWAPI_API_KEY=newapi-key",
                "IMAGEGEN_MYSELF_BASE_URL=https://image.example",
                "IMAGEGEN_MYSELF_API_KEY=image-key",
                "IMAGEGEN_MYSELF_PRIMARY_BASE_URL=https://primary.example",
                "IMAGEGEN_MYSELF_PRIMARY_API_KEY=primary-key",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_overrides({})

    assert settings.imagegen_base_url == "https://primary.example"
    assert settings.imagegen_api_key == "primary-key"


def test_settings_video_model_prefers_video_model_then_legacy_defaults(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "NEWAPI_DEFAULT_MODEL=legacy-newapi-model",
                "OMNI_DEFAULT_MODEL=legacy-omni-model",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_overrides({})

    assert settings.video_model == "legacy-omni-model"

    monkeypatch.setenv("VIDEO_MODEL", "sora-2-12s")
    settings = Settings.from_overrides({})

    assert settings.video_model == "sora-2-12s"


def test_octo_video_provider_uses_authorization_for_submit_and_query():
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append({"method": method, "url": url, **kwargs})
        if method == "POST":
            return {"id": "task_remote_1", "status": "queued", "progress": 0}
        return {"id": "task_remote_1", "status": "completed", "progress": 100, "url": "https://cdn.example/test.mp4"}

    provider = OctoVideoProvider(api_key="test-token", base_url="https://otuapi.com", transport=transport)

    submitted = provider.submit_video(
        {
            "model": "veo_3_1-fast",
            "prompt": "课堂导入视频",
            "size": "1280x720",
            "images": ["https://example.com/ref.png"],
        }
    )
    queried = provider.query_task("task_remote_1")

    assert submitted["provider_task_id"] == "task_remote_1"
    assert queried["status"] == "completed"
    assert queried["video_url"] == "https://cdn.example/test.mp4"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-token"
    assert calls[1]["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.parametrize(
    ("raw", "expected_url"),
    [
        ({"status": "completed", "video_url": "https://cdn.example/a.mp4"}, "https://cdn.example/a.mp4"),
        ({"status": "completed", "url": "https://cdn.example/b.mp4"}, "https://cdn.example/b.mp4"),
        ({"status": "SUCCESS", "data": {"video_url": "https://cdn.example/c.mp4"}}, "https://cdn.example/c.mp4"),
        ({"status": "SUCCESS", "data": {"url": "https://cdn.example/d.mp4"}}, "https://cdn.example/d.mp4"),
        ({"status": "SUCCESS", "data": {"result_url": "https://cdn.example/e.mp4"}}, "https://cdn.example/e.mp4"),
        ({"status": "SUCCESS", "data": {"first_video_url": "https://cdn.example/f.mp4"}}, "https://cdn.example/f.mp4"),
        ({"status": "SUCCESS", "result": {"video_url": "https://cdn.example/g.mp4"}}, "https://cdn.example/g.mp4"),
        ({"status": "SUCCESS", "result": {"url": "https://cdn.example/h.mp4"}}, "https://cdn.example/h.mp4"),
    ],
)
def test_octo_video_provider_normalizes_video_url_fields(raw: dict[str, Any], expected_url: str):
    provider = OctoVideoProvider(api_key="test-token", base_url="https://otuapi.com", transport=lambda *args, **kwargs: raw)

    assert provider.query_task("task_remote_1")["video_url"] == expected_url


def test_octo_video_provider_classifies_quota_exhausted_query_failure():
    raw = {
        "id": "task_remote_quota",
        "status": "failed",
        "error": {
            "code": 429,
            "message": "Resource has been exhausted (e.g. check quota).",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "PUBLIC_ERROR_USER_QUOTA_REACHED",
                }
            ],
        },
    }
    provider = OctoVideoProvider(api_key="test-token", base_url="https://otuapi.com", transport=lambda *args, **kwargs: raw)

    queried = provider.query_task("task_remote_quota")

    assert queried["status"] == "failed"
    assert queried["error_code"] == "VIDEO_QUOTA_EXHAUSTED"
    assert queried["retryable"] is False
    assert "RESOURCE_EXHAUSTED" in queried["error_message"]
    assert "PUBLIC_ERROR_USER_QUOTA_REACHED" in queried["error_message"]
    assert "test-token" not in queried["error_message"]


def test_minimax_text_provider_retries_invalid_json_once():
    calls = 0

    def transport(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"choices": [{"message": {"content": "not json"}}]}
        return {"choices": [{"message": {"content": '{"lesson_title":"分数","core_knowledge_points":[]}'}}]}

    provider = MinimaxTextProvider(api_key="test-token", base_url="https://api.example", model="M3", transport=transport)

    result = provider.complete_json(
        node_id="textbook_parse",
        prompt="输出 JSON",
        schema={"required": ["lesson_title"]},
        temperature=0.2,
        max_tokens=1000,
    )

    assert result["lesson_title"] == "分数"
    assert calls == 2


@pytest.mark.parametrize(
    ("body", "expected_message"),
    [
        (b"", "返回空响应"),
        (b"not json", "返回非 JSON 响应"),
    ],
)
def test_newapi_image_provider_wraps_empty_or_non_json_http_response(monkeypatch, body: bytes, expected_message: str):
    class StubResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return body

    monkeypatch.setattr("app.providers.urllib.request.urlopen", lambda request, timeout: StubResponse())
    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda method, url, **kwargs: provider._http_transport(method, url, **kwargs),
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert exc_info.value.code == "IMAGE_RESPONSE_INVALID"
    assert expected_message in str(exc_info.value)
    assert exc_info.value.retryable is True


def test_newapi_image_provider_wraps_remote_disconnect(monkeypatch):
    def disconnect(_request, timeout):
        raise http.client.RemoteDisconnected("Remote end closed connection without response")

    monkeypatch.setattr("app.providers.urllib.request.urlopen", disconnect)
    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda method, url, **kwargs: provider._http_transport(method, url, **kwargs),
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert exc_info.value.code == "IMAGE_REQUEST_FAILED"
    assert exc_info.value.retryable is True
    assert "closed connection" in str(exc_info.value)


@pytest.mark.parametrize(
    ("raw", "expected_url"),
    [
        ({"data": [{"url": "https://cdn.example/openai.png"}]}, "https://cdn.example/openai.png"),
        ({"data": {"url": "https://cdn.example/data-url.png"}}, "https://cdn.example/data-url.png"),
        ({"data": {"image_url": "https://cdn.example/data-image-url.png"}}, "https://cdn.example/data-image-url.png"),
        ({"url": "https://cdn.example/top-url.png"}, "https://cdn.example/top-url.png"),
        ({"image_url": "https://cdn.example/top-image-url.png"}, "https://cdn.example/top-image-url.png"),
    ],
)
def test_newapi_image_provider_normalizes_sync_url_shapes(raw: dict[str, Any], expected_url: str):
    captured: dict[str, Any] = {}

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        captured["json"] = kwargs["json"]
        return raw

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=transport,
    )

    result = provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert result["image_url"] == expected_url
    assert result["status"] == "completed"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://image.example/v1/images/generations"
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["json"] == {
        "model": "gpt-image-2",
        "prompt": "小学数学参考图",
        "size": "1024x1024",
        "quality": "high",
        "response_format": "b64_json",
        "n": 1,
    }


def test_newapi_image_provider_normalizes_base_url_without_v1():
    captured: dict[str, Any] = {}

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        captured["url"] = url
        return {"data": [{"url": "https://cdn.example/image.png"}]}

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example",
        model="gpt-image-2",
        transport=transport,
    )

    provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert captured["url"] == "https://image.example/v1/images/generations"


def test_newapi_image_provider_retries_verified_profiles_after_pool_unavailable():
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs["json"])
        if len(calls) == 1:
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                "HTTP 503",
                retryable=True,
                status_code=503,
                response_excerpt='{"error":{"message":"auth_unavailable: no auth available"}}',
            )
        return {"data": [{"url": "https://cdn.example/fallback.png"}]}

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=transport,
    )

    result = provider.generate_image({"prompt": "小学数学参考图", "size": "1920x1080", "quality": "high"})

    assert result["image_url"] == "https://cdn.example/fallback.png"
    assert [call["size"] for call in calls] == ["1920x1080", "1024x1024"]
    assert [call["quality"] for call in calls] == ["high", "high"]


def test_newapi_image_provider_retries_same_profile_once_after_transient_disconnect():
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs["json"])
        if len(calls) == 1:
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                "Remote end closed connection without response",
                retryable=True,
            )
        return {"data": [{"url": "https://cdn.example/retry.png"}]}

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=transport,
    )

    result = provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024", "quality": "low"})

    assert result["image_url"] == "https://cdn.example/retry.png"
    assert [call["size"] for call in calls] == ["1024x1024", "1024x1024"]
    assert [call["quality"] for call in calls] == ["low", "low"]


def test_newapi_image_provider_retries_low_quality_when_high_profile_unavailable():
    calls: list[dict[str, Any]] = []

    def transport(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs["json"])
        if len(calls) < 3:
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                "HTTP 503",
                retryable=True,
                status_code=503,
                response_excerpt='{"error":{"message":"No available compatible accounts"}}',
            )
        return {"data": [{"url": "https://cdn.example/low.png"}]}

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=transport,
    )

    result = provider.generate_image({"prompt": "小学数学参考图", "size": "1920x1080", "quality": "high"})

    assert result["image_url"] == "https://cdn.example/low.png"
    assert [call["size"] for call in calls] == ["1920x1080", "1024x1024", "1024x1024"]
    assert [call["quality"] for call in calls] == ["high", "high", "low"]


def test_newapi_image_provider_rejects_sync_response_without_image_payload():
    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda *args, **kwargs: {"data": [{}]},
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert exc_info.value.code == "IMAGE_RESPONSE_INVALID"
    assert "url 或 b64_json" in str(exc_info.value)
    assert exc_info.value.retryable is True


def test_newapi_image_provider_marks_async_task_response_unsupported():
    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda *args, **kwargs: {"task_id": "img_task_001", "status": "queued"},
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})

    assert exc_info.value.code == "IMAGE_ASYNC_TASK_UNSUPPORTED"
    assert exc_info.value.retryable is True
    assert "img_task_001" in exc_info.value.response_excerpt


def test_newapi_image_provider_b64_json_downloads_to_file(tmp_path: Path):
    b64_png = "iVBORw0KGgppbWFnZQ=="
    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda *args, **kwargs: {"data": [{"b64_json": b64_png}]},
    )
    target = tmp_path / "asset.png"

    result = provider.generate_image({"prompt": "小学数学参考图", "size": "1024x1024"})
    provider.download_image("data:image/png;base64," + result["b64_json"], target)

    assert result["b64_json"] == b64_png
    assert target.read_bytes().startswith(b"\x89PNG")


def test_intro_video_asset_newapi_empty_response_persists_failed_task_and_node(monkeypatch, tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "图片空响应")
    project_id = project["project_id"]

    class StubResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b""

    monkeypatch.setattr("app.providers.urllib.request.urlopen", lambda request, timeout: StubResponse())
    client.app.state.service.image_provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda method, url, **kwargs: client.app.state.service.image_provider._http_transport(method, url, **kwargs),
    )

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "IMAGE_RESPONSE_INVALID"
    assert error["retryable"] is True
    assert "Expecting value" not in error["message"]
    asset_node = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_asset"))
    assert asset_node["status"] == "blocked"
    assert asset_node["content"]["error_code"] == "IMAGE_RESPONSE_INVALID"
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    assert tasks[0]["task_type"] == "image_generation"
    assert tasks[0]["status"] == "failed"
    assert tasks[0]["error_code"] == "IMAGE_RESPONSE_INVALID"


def test_minimax_text_provider_unwraps_data_payload_before_validation():
    provider = MinimaxTextProvider(
        api_key="test-token",
        base_url="https://api.example/v1",
        model="M3",
        transport=lambda payload: {"choices": [{"message": {"content": '{"data":{"lesson_title":"分数"}}'}}]},
    )

    result = provider.complete_json(
        node_id="textbook_parse",
        prompt="输出 JSON",
        schema={"required": ["lesson_title"]},
        temperature=0.2,
        max_tokens=1000,
    )

    assert result == {"lesson_title": "分数"}


def test_deepseek_text_provider_sends_openai_compatible_payload_and_auth():
    captured: dict[str, Any] = {}

    def transport(payload: dict[str, Any], headers: dict[str, str], url: str) -> dict[str, Any]:
        captured["payload"] = payload
        captured["headers"] = headers
        captured["url"] = url
        return {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"lesson_plan_markdown":"# 教案：5以内数的认识"}\n```'
                    }
                }
            ]
        }

    provider = DeepSeekTextProvider(
        api_key="deepseek-token",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        transport=transport,
    )

    result = provider.complete_json(
        node_id="lesson_plan",
        prompt="只输出 JSON",
        schema={"required": ["lesson_plan_markdown"]},
        temperature=0.2,
        max_tokens=1000,
    )

    assert result == {"lesson_plan_markdown": "# 教案：5以内数的认识"}
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer deepseek-token"
    assert captured["payload"]["model"] == "deepseek-chat"
    assert captured["payload"]["response_format"] == {"type": "json_object"}
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["payload"]["messages"][1]["content"] == "只输出 JSON"


def test_deepseek_text_provider_requires_api_key():
    provider = DeepSeekTextProvider(api_key=None, base_url="https://api.deepseek.com", model="deepseek-chat")

    with pytest.raises(ProviderError) as exc:
        provider.complete_json(
            node_id="lesson_plan",
            prompt="只输出 JSON",
            schema={"required": ["lesson_plan_markdown"]},
            temperature=0.2,
            max_tokens=1000,
        )

    assert exc.value.code == "DEEPSEEK_KEY_MISSING"
    assert exc.value.retryable is False


def test_real_provider_mode_uses_deepseek_for_lesson_plan(tmp_path: Path, monkeypatch):
    calls: list[dict[str, Any]] = []

    class StubDeepSeekProvider:
        name = "deepseek"

        def __init__(self, api_key: str | None, base_url: str, model: str):
            assert api_key == "test-deepseek-key"
            assert base_url == "https://api.deepseek.com"
            assert model == "deepseek-chat"

        def complete_json(self, **kwargs):
            calls.append(kwargs)
            if kwargs["node_id"] == "textbook_parse":
                return {
                    "lesson_title": "5以内数的认识",
                    "core_knowledge_points": ["1-5数量意义"],
                    "teaching_goal_summary": "认识 1-5 的数量意义。",
                    "key_points": ["数物对应"],
                    "difficulties": ["数量抽象"],
                    "selected_knowledge_point": {
                        "knowledge_point_id": "kp_001",
                        "title": "5以内数的认识",
                        "markdown_path": "knowledge-points/kp_001.md",
                        "markdown": "# 知识点：5以内数的认识\n\n认识 1-5，会用数量表达物品个数。",
                    },
                }
            return {
                "lesson_plan_markdown": "# 教案：5以内数的认识\n\n## 基本信息\n- 年级：小学一年级",
                "intro_designs": [
                    {
                        "design_id": "design_application_01",
                        "type": "application",
                        "title": "数一数身边的物品",
                        "hook": "用铅笔和苹果引出 1-5。",
                        "anchor_to_lesson": "贴合 5 以内数的认识。",
                        "recommend_score": 5,
                    },
                    {
                        "design_id": "design_story_01",
                        "type": "story",
                        "title": "数字寻宝",
                        "hook": "小朋友寻找数字卡。",
                        "anchor_to_lesson": "串联 1-5 的数量意义。",
                        "recommend_score": 4,
                    },
                    {
                        "design_id": "design_science_01",
                        "type": "science",
                        "title": "自然里的数字",
                        "hook": "花瓣数量引出数字。",
                        "anchor_to_lesson": "从观察到抽象。",
                        "recommend_score": 4,
                    },
                ],
            }

    monkeypatch.setattr("app.main.DeepSeekTextProvider", StubDeepSeekProvider)
    client = make_client(
        tmp_path,
        {
            "provider_mode": "real",
            "deepseek_api_key": "test-deepseek-key",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat",
        },
    )
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "DeepSeek 教案生成",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    unwrap(
        client.post(
            f"/projects/{project_id}/textbook",
            files={"file": ("textbook.txt", "一年级数学，5以内数的认识。", "text/plain")},
        )
    )
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))

    lesson_call = next(call for call in calls if call["node_id"] == "lesson_plan")
    assert "5以内数的认识" in lesson_call["prompt"]
    assert generated["content"]["lesson_plan_markdown"].startswith("# 教案")
    assert generated["content"]["textbook_anchor"] == "基于已选知识点 Markdown 生成"
    assert len(generated["content"]["intro_designs"]) == 9
    assert {item["type"] for item in generated["content"]["intro_designs"]} == {"science", "application", "story"}
    assert all("video_theme" in item for item in generated["content"]["intro_designs"])


def test_real_provider_mode_generates_video_script_chain_with_shared_llm(tmp_path: Path):
    calls: list[str] = []

    class StubTextProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            node_id = kwargs["node_id"]
            calls.append(node_id)
            if node_id == "intro_selection":
                return {
                    "selection_mode": "single_best",
                    "selected_design_ids": ["design_application_01"],
                    "primary_design_id": "design_application_01",
                    "selected_anchor": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                    "downstream_generation_mode": "three_variants_for_primary",
                    "selection_reason": "生活物品数数最贴近一年级学生经验。",
                }
            if node_id == "intro_video_script":
                return {
                    "total_duration_sec": 60,
                    "video_type": "application",
                    "anchor_to_lesson": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                    "narration_full_text": "桌面上出现一个苹果、两支铅笔、三块积木、四朵小花和五颗星星。我们一起数一数，认识 1 到 5。用苹果、铅笔等物品引出 1-5 的数量意义。",
                    "narration_word_count": 48,
                    "banned_elements": ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"],
                }
            if node_id == "intro_video_screenplay":
                return {
                    "scenes": [
                        {
                            "scene_id": "scene_01",
                            "duration_sec": 20,
                            "scene_description": "卡通桌面依次出现 1-5 个物品。",
                            "character_refs": [],
                            "narration_segment": "桌面上出现一个苹果、两支铅笔。",
                        },
                        {
                            "scene_id": "scene_02",
                            "duration_sec": 20,
                            "scene_description": "物品和数字卡片逐一对应。",
                            "character_refs": [],
                            "narration_segment": "我们一起数一数，认识 1 到 5。",
                        },
                    ]
                }
            if node_id == "intro_video_asset":
                return {
                    "assets": [
                        {
                            "asset_id": f"asset_ref_{index:02d}",
                            "source_prompt_id": f"shot_{index:02d}",
                            "storage_path": f"08B_导入视频资产/ref_{index:02d}.png",
                            "status": "approved",
                        }
                        for index in range(1, 7)
                    ]
                }
            if node_id == "storyboard":
                return {
                    "total_duration": 60,
                    "shots": [
                        {
                            "id": f"shot_{index:02d}",
                            "duration": 10,
                            "scene": "卡通桌面数数",
                            "subject": f"{index} 个数学物品",
                            "subtitle": f"认识数字 {index}",
                            "visual_type": "animation",
                        }
                        for index in range(1, 7)
                    ],
                }
            raise AssertionError(f"unexpected node {node_id}")

    client = make_client(tmp_path)
    client.app.state.service.provider = StubTextProvider()
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "视频脚本链真实 LLM",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        _write_shared_visual_context(conn, project_id)
        client.app.state.store.write_version(
            conn,
            project_id,
            "textbook_parse",
            {"lesson_title": "5以内数的认识"},
            "ai",
            "fixture",
            "approved",
        )
        client.app.state.store.write_version(
            conn,
            project_id,
            "lesson_plan",
            normalize_node_content(
                "lesson_plan",
                {
                    "lesson_plan_markdown": "# 教案：5以内数的认识",
                    "intro_designs": [
                        {
                            "design_id": "design_application_01",
                        "type": "application",
                        "title": "生活物品数一数",
                        "hook": "用苹果导入。",
                        "anchor_to_lesson": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                        "recommend_score": 5,
                    }
                ],
                },
                {
                    "grade": "1",
                    "textbook_version": "renjiao",
                    "volume": "shang",
                    "textbook_parse": {"lesson_title": "5以内数的认识"},
                },
            ),
            "ai",
            "fixture",
            "approved",
        )

    for node_id in ["intro_selection", "intro_video_script", "intro_video_screenplay", "intro_video_asset", "storyboard"]:
        generated = unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        assert generated["status"] == "needs_review"
        unwrap(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    assert calls == ["intro_selection", "intro_video_script", "intro_video_screenplay", "intro_video_asset", "storyboard"]
    storyboard = unwrap(client.get(f"/projects/{project_id}/nodes/storyboard"))
    assert len(storyboard["content"]["shots"]) == 6
    assert storyboard["content"]["shots"][0]["shot_id"] == "shot_01"
    assert "旁白（男声，中文）" in storyboard["content"]["shots"][0]["model_prompt"]
    script = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_script"))
    assert script["content"]["anchor_to_lesson"] == "用苹果、铅笔等物品引出 1-5 的数量意义。"
    assert script["content"]["narration_full_text"].endswith("用苹果、铅笔等物品引出 1-5 的数量意义。")


def test_storyboard_prompt_omits_large_data_image_payloads_but_keeps_asset_refs(tmp_path: Path):
    captured: dict[str, str] = {}

    class CapturingTextProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            captured["prompt"] = kwargs["prompt"]
            return {
                "shots": [
                    {
                        "shot_id": "shot_01",
                        "duration_sec": 10,
                        "main_subject": "卡通桌面数数",
                        "character_refs": [],
                        "reference_image_ids": ["asset_ref_01"],
                        "narration_slice": "认识数字 1。",
                        "subtitle": "认识数字 1",
                        "model_prompt": "旁白（男声，中文）：认识数字 1。\n画面：卡通桌面数数。\n禁止英文配音。",
                        "first_frame_test_status": "passed",
                        "first_frame_asset_id": "asset_ref_01",
                    }
                ]
            }

    client = make_client(tmp_path)
    client.app.state.service.provider = CapturingTextProvider()
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "storyboard prompt 清洗",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    large_data_image = "data:image/png;base64," + ("A" * 100_000)
    with client.app.state.store.connect(project_dir) as conn:
        _write_shared_visual_context(conn, project_id)
        client.app.state.store.write_version(
            conn,
            project_id,
            "intro_selection",
            {
                "selection_mode": "single_best",
                "selected_design_ids": ["design_application_01"],
                "primary_design_id": "design_application_01",
                "selected_anchor": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                "downstream_generation_mode": "three_variants_for_primary",
                "selection_reason": "生活物品数数最贴近一年级学生经验。",
            },
            "ai",
            "fixture",
            "approved",
        )
        client.app.state.store.write_version(
            conn,
            project_id,
            "intro_video_script",
            {
                "total_duration_sec": 60,
                "video_type": "application",
                "anchor_to_lesson": "用苹果、铅笔等物品引出 1-5 的数量意义。",
                "narration_full_text": "认识数字 1。用苹果、铅笔等物品引出 1-5 的数量意义。",
                "narration_word_count": 24,
                "banned_elements": ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"],
            },
            "ai",
            "fixture",
            "approved",
        )
        client.app.state.store.write_version(
            conn,
            project_id,
            "intro_video_screenplay",
            {
                "scenes": [
                    {
                        "scene_id": "scene_01",
                        "duration_sec": 10,
                        "scene_description": "卡通桌面出现一个苹果和数字 1。",
                        "character_refs": [],
                        "narration_segment": "认识数字 1。",
                    }
                ]
            },
            "ai",
            "fixture",
            "approved",
        )
        client.app.state.store.write_version(
            conn,
            project_id,
            "intro_video_asset",
            {
                "assets": [
                    {
                        "asset_id": "asset_ref_01",
                        "source_prompt_id": "scene_01",
                        "storage_path": "08B_导入视频资产/asset_ref_01.png",
                        "status": "approved",
                        "image_path": "assets/generated_images/asset_ref_01.png",
                        "image_url": large_data_image,
                        "raw": {"b64_json": "B" * 100_000},
                    }
                ]
            },
            "ai",
            "fixture",
            "approved",
        )

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/storyboard/generate", json={}))

    prompt = captured["prompt"]
    assert generated["status"] == "needs_review"
    assert "asset_ref_01" in prompt
    assert "assets/generated_images/asset_ref_01.png" in prompt
    assert "data:image" not in prompt
    assert "A" * 1000 not in prompt
    assert "B" * 1000 not in prompt


def test_textbook_parse_content_aliases_are_normalized():
    normalized = normalize_node_content(
        "textbook_parse",
        {
            "topic": "分数的初步认识",
            "key_concepts": ["平均分", "二分之一"],
            "teaching_focus": "理解部分与整体关系",
            "misconceptions": ["未平均分也用分数表示"],
        },
        {"grade": "3", "textbook_version": "renjiao", "volume": "xia"},
    )

    assert normalized["lesson_title"] == "分数的初步认识"
    assert normalized["core_knowledge_points"] == ["平均分", "二分之一"]
    assert normalized["teaching_goal_summary"] == "理解部分与整体关系"
    assert normalized["key_points"] == ["理解部分与整体关系"]
    assert normalized["difficulties"] == ["未平均分也用分数表示"]


def test_storyboard_normalization_expands_weak_model_prompt_for_video_provider():
    normalized = normalize_node_content(
        "storyboard",
        {
            "shots": [
                {
                    "id": "1",
                    "duration": 10,
                    "subject": "卡通小羊排队，结绳记录数量",
                    "subtitle": "这个结绳记录了多少只羊？",
                    "model_prompt": "旁白（男声，中文），禁止英文配音",
                }
            ]
        },
        {
            "intro_video_asset": {
                "assets": [
                    {"asset_id": "asset_001", "storage_path": "08B_导入视频资产/asset_001.png", "status": "generated"}
                ]
            }
        },
    )

    prompt = normalized["shots"][0]["model_prompt"]
    assert normalized["shots"][0]["shot_id"] == "shot_01"
    assert "旁白（男声，中文）：" in prompt
    assert "画面：" in prompt
    assert "卡通小羊排队，结绳记录数量" in prompt
    assert "禁止英文配音" in prompt
    assert len(prompt) > 40


def test_lesson_plan_normalization_produces_nine_complete_intro_designs():
    normalized = normalize_node_content(
        "lesson_plan",
        {
            "lesson_plan_markdown": "# 教案：5以内数的认识\n\n## 教学目标\n认识 1-5 的数量意义。",
            "intro_designs": [
                {
                    "design_id": "design_application_01",
                    "type": "application",
                    "title": "旧生活导入",
                    "hook": "桌上出现 5 个苹果。",
                    "anchor_to_lesson": "自然引出本课",
                    "recommend_score": 5,
                }
            ],
        },
        {
            "grade": "1",
            "textbook_version": "renjiao",
            "volume": "shang",
            "textbook_parse": {
                "lesson_title": "5以内数的认识",
                "selected_knowledge_point": {"title": "5以内数的认识"},
            },
        },
    )

    intro_designs = normalized["intro_designs"]
    assert len(intro_designs) == 9
    assert [item["type"] for item in intro_designs].count("science") == 3
    assert [item["type"] for item in intro_designs].count("application") == 3
    assert [item["type"] for item in intro_designs].count("story") == 3

    required_fields = {
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
    anchors = [item["anchor_to_lesson"] for item in intro_designs]
    assert len(set(anchors)) == 9
    for item in intro_designs:
        assert required_fields <= set(item)
        assert item["design_id"].startswith(f"design_{item['type']}_")
        assert isinstance(item["recommend_score"], int)
        assert 1 <= item["recommend_score"] <= 100
        assert len(item["anchor_to_lesson"]) >= 10
        assert not _contains_abstract_anchor_phrase(item["anchor_to_lesson"])


def test_lesson_plan_prompt_requires_nine_distinct_anchor_designs(tmp_path: Path):
    client = make_client(tmp_path)

    prompt = client.app.state.service._build_prompt(
        "lesson_plan",
        {
            "grade": "1",
            "textbook_version": "renjiao",
            "volume": "shang",
            "textbook_parse": {
                "selected_knowledge_point": {
                    "title": "5以内数的认识",
                    "markdown": "# 知识点：5以内数的认识",
                }
            },
        },
    )

    assert "9 套" in prompt
    assert "science" in prompt
    assert "application" in prompt
    assert "story" in prompt
    for field in [
        "video_theme",
        "eye_catch_tag",
        "classroom_entry_question",
        "no_pre_teach",
        "entry_position",
        "recommend_reason",
    ]:
        assert field in prompt
    assert "锚点必须各不相同" in prompt
    assert "自然引出本课" in prompt
    assert "不得" in prompt
    assert "3 个导入方案" not in prompt


def _contains_abstract_anchor_phrase(value: str) -> bool:
    return any(
        phrase in value
        for phrase in [
            "自然引出本课",
            "教学目标对应点",
            "教案关联点",
            "引出课堂探究活动",
            "服务本课核心知识点",
        ]
    )


def _create_project_with_approved_storyboard(client: TestClient, name: str = "真实视频任务"):
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": name,
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    storyboard = {
        "shots": [
            {
                "shot_id": "shot_01",
                "duration_sec": 10,
                "main_subject": "卡通桌面数数",
                "character_refs": [],
                "reference_image_ids": ["asset_ref_01"],
                "narration_slice": "认识数字 1。",
                "subtitle": "认识数字 1",
                "model_prompt": "旁白（男声，中文）：认识数字 1。\n画面：卡通桌面数数。\n禁止英文配音。",
                "first_frame_test_status": "passed",
                "first_frame_asset_id": "asset_ref_01",
            },
            {
                "shot_id": "shot_02",
                "duration_sec": 10,
                "main_subject": "卡通桌面数数",
                "character_refs": [],
                "reference_image_ids": ["asset_ref_02"],
                "narration_slice": "认识数字 2。",
                "subtitle": "认识数字 2",
                "model_prompt": "旁白（男声，中文）：认识数字 2。\n画面：卡通桌面数数。\n禁止英文配音。",
                "first_frame_test_status": "passed",
                "first_frame_asset_id": "asset_ref_02",
            },
        ]
    }
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        _write_shared_visual_context(conn, project_id)
        client.app.state.store.write_version(conn, project_id, "intro_video_script", {"narration_full_text": "认识 1 到 2。"}, "ai", "fixture", "approved")
        client.app.state.store.write_version(conn, project_id, "storyboard", storyboard, "ai", "fixture", "approved")
    return project


def _create_project_with_approved_screenplay(client: TestClient, name: str = "真实图片任务"):
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": name,
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    screenplay = {
        "scenes": [
            {
                "scene_id": "scene_01",
                "duration_sec": 10,
                "scene_description": "卡通桌面出现苹果和数字卡片。",
                "character_refs": [],
                "narration_segment": "先数一个苹果。",
            }
        ]
    }
    with client.app.state.store.connect(Path(project["project_dir"])) as conn:
        _write_shared_visual_context(conn, project_id)
        client.app.state.store.write_version(conn, project_id, "intro_video_screenplay", screenplay, "ai", "fixture", "approved")
    return project


def test_intro_video_asset_partial_image_success_continues_when_minimum_met(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "部分生图继续")
    project_id = project["project_id"]

    class AssetProvider:
        name = "deepseek"

        def complete_json(self, **kwargs: Any):
            return {
                "assets": [
                    {"asset_id": "asset_001", "source_prompt_id": "scene_01", "storage_path": "08B/a.mp4", "status": "approved"},
                    {"asset_id": "asset_002", "source_prompt_id": "scene_02", "storage_path": "08B/b.mp4", "status": "approved"},
                    {"asset_id": "asset_003", "source_prompt_id": "scene_03", "storage_path": "08B/c.mp4", "status": "approved"},
                ]
            }

    class PartiallyFailingImageProvider:
        def __init__(self):
            self.calls = 0

        def submit_image(self, payload: dict[str, Any]):
            self.calls += 1
            if self.calls == 3:
                raise ProviderError("IMAGE_REQUEST_FAILED", "Connection error.", retryable=True)
            return {"status": "completed", "image_bytes": b"\x89PNG\r\n\x1a\nfake-image"}

        def download_image(self, image_url: str, target_path: Path):
            raise AssertionError("image_bytes path should not download by url")

    client.app.state.service.provider = AssetProvider()
    client.app.state.service.image_provider = PartiallyFailingImageProvider()

    data = unwrap(
        client.post(
            f"/projects/{project_id}/nodes/intro_video_asset/generate",
            json={"min_successful_images": 1},
        )
    )

    assert data["status"] == "needs_review"
    assert data["content"]["partial_success"] is True
    assert len(data["content"]["assets"]) == 2
    assert [asset["asset_id"] for asset in data["content"]["assets"]] == ["asset_001", "asset_002"]
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert [task["status"] for task in tasks] == ["completed", "completed", "failed"]
    failed = tasks[-1]
    assert failed["error_code"] == "IMAGE_REQUEST_FAILED"
    assert failed["retryable"] is True


def test_image_task_is_committed_before_slow_real_image_provider_call(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "慢生图不锁库")
    project_id = project["project_id"]
    entered_provider = threading.Event()
    release_provider = threading.Event()

    class SlowImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            entered_provider.set()
            assert release_provider.wait(timeout=5)
            return {
                "provider_task_id": "image_remote_slow",
                "status": "completed",
                "b64_json": "iVBORw0KGgppbWFnZQ==",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nslow")

    client.app.state.service.image_provider = SlowImageProvider()
    result: dict[str, Any] = {}

    def generate_asset() -> None:
        result["response"] = client.post(
            f"/projects/{project_id}/nodes/intro_video_asset/generate",
            json={"image_limit": 1, "min_successful_images": 1, "allow_partial_assets": True},
        )

    thread = threading.Thread(target=generate_asset)
    thread.start()
    assert entered_provider.wait(timeout=5)

    tasks_response = client.get(f"/projects/{project_id}/tasks")

    release_provider.set()
    thread.join(timeout=5)

    assert tasks_response.status_code == 200, tasks_response.text
    tasks = tasks_response.json()["data"]
    assert len(tasks) == 1
    assert tasks[0]["status"] == "submitting"
    assert result["response"].status_code == 200, result["response"].text


def test_real_video_submit_failure_persists_failed_task_without_leaking_tokens(tmp_path: Path):
    client = make_client(tmp_path)
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频失败诊断")
    project_id = project["project_id"]

    class FailingVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            assert payload["model"] == "omni_flash-10s"
            exc = ProviderError("OCTO_REQUEST_FAILED", "HTTP 503", retryable=True)
            exc.status_code = 503
            exc.response_excerpt = '{"error":{"code":"model_unavailable","message":"upstream unavailable","token":"sk-test-secret"}}'
            raise exc

    client.app.state.service.video_provider = FailingVideoProvider()

    response = client.post(f"/projects/{project_id}/nodes/final_video/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "OCTO_REQUEST_FAILED"
    assert error["details"]["http_status"] == 503
    assert "sk-test-secret" not in str(error)
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    task = tasks[0]
    assert task["node_id"] == "final_video"
    assert task["status"] == "failed"
    assert task["error_code"] == "OCTO_REQUEST_FAILED"
    assert task["provider_task_id"] is None
    assert task["video_url_present"] is False
    assert task["result"]["http_status"] == 503
    assert task["result"]["retryable"] is True
    serialized_task = str(task)
    assert "sk-test-secret" not in serialized_task
    assert "OCTO_API_KEY" not in serialized_task
    final_node = unwrap(client.get(f"/projects/{project_id}/nodes/final_video"))
    assert final_node["status"] == "blocked"
    assert final_node["content"]["error_code"] == "OCTO_REQUEST_FAILED"


def test_real_video_submit_success_exposes_provider_task_id(tmp_path: Path):
    client = make_client(tmp_path)
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频提交成功")
    project_id = project["project_id"]

    class SuccessfulVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            shot_index = "001" if "数字 1" in payload["prompt"] else "002"
            return {
                "provider_task_id": f"octo_task_{shot_index}",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {"id": f"octo_task_{shot_index}", "status": "queued"},
            }

    client.app.state.service.video_provider = SuccessfulVideoProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={}))

    assert generated["status"] == "drafted"
    assert len(generated["tasks"]) == 2
    task = generated["tasks"][0]
    assert task["status"] == "queued"
    assert task["provider_task_id"] == "octo_task_001"
    assert task["payload"]["shot_id"] == "shot_01"
    assert task["download_path"] == "clips/shot_01.mp4"
    assert task["video_url_present"] is False
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert tasks[0]["provider_task_id"] == "octo_task_001"
    assert tasks[1]["provider_task_id"] == "octo_task_002"


def test_real_video_generate_respects_video_shot_limit_for_quota_safe_demo(tmp_path: Path):
    client = make_client(tmp_path)
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频单镜头演示")
    project_id = project["project_id"]
    submitted_prompts: list[str] = []

    class SuccessfulVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            submitted_prompts.append(payload["prompt"])
            return {
                "provider_task_id": "octo_task_001",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {"id": "octo_task_001", "status": "queued"},
            }

    client.app.state.service.video_provider = SuccessfulVideoProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={"video_shot_limit": 1}))

    assert generated["status"] == "drafted"
    assert len(generated["tasks"]) == 1
    assert len(submitted_prompts) == 1
    assert generated["tasks"][0]["payload"]["shot_id"] == "shot_01"
    assert generated["content"]["clip_count"] == 1


def test_real_video_generate_uses_configured_default_video_model(tmp_path: Path):
    client = make_client(tmp_path, {"video_model": "sora-2-12s"})
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频配置默认模型")
    project_id = project["project_id"]
    submitted_models: list[str] = []

    class SuccessfulVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            submitted_models.append(payload["model"])
            return {
                "provider_task_id": f"octo_task_{len(submitted_models):03d}",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client.app.state.service.video_provider = SuccessfulVideoProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={"video_shot_limit": 1}))

    assert generated["tasks"][0]["payload"]["model"] == "sora-2-12s"
    assert submitted_models == ["sora-2-12s"]


def test_real_video_generate_request_model_overrides_configured_default(tmp_path: Path):
    client = make_client(tmp_path, {"video_model": "sora-2-12s"})
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频请求覆盖模型")
    project_id = project["project_id"]
    submitted_models: list[str] = []

    class SuccessfulVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            submitted_models.append(payload["model"])
            return {
                "provider_task_id": f"octo_task_{len(submitted_models):03d}",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client.app.state.service.video_provider = SuccessfulVideoProvider()

    generated = unwrap(
        client.post(
            f"/projects/{project_id}/nodes/final_video/generate",
            json={"video_shot_limit": 1, "model": "veo_3_1-fast"},
        )
    )

    assert generated["tasks"][0]["payload"]["model"] == "veo_3_1-fast"
    assert submitted_models == ["veo_3_1-fast"]


def test_real_video_submit_creates_tasks_for_all_storyboard_shots_and_uses_reference_urls(tmp_path: Path):
    client = make_client(tmp_path)
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    project = _create_project_with_approved_storyboard(client, "真实视频多镜头提交")
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        client.app.state.store.create_task(
            conn,
            project_id,
            "intro_video_asset",
            "image_generation",
            {"asset_id": "asset_ref_01", "image_path": "assets/generated_images/asset_ref_01.png"},
            status="completed",
            result={
                "provider_task_id": "image_remote_01",
                "image_path": "assets/generated_images/asset_ref_01.png",
                "image_url": "https://cdn.example/asset_ref_01.png",
                "download_status": "downloaded",
            },
        )
        client.app.state.store.create_task(
            conn,
            project_id,
            "intro_video_asset",
            "image_generation",
            {"asset_id": "asset_ref_02", "image_path": "assets/generated_images/asset_ref_02.png"},
            status="completed",
            result={
                "provider_task_id": "image_remote_02",
                "image_path": "assets/generated_images/asset_ref_02.png",
                "image_url": "https://cdn.example/asset_ref_02.png",
                "download_status": "downloaded",
            },
        )
    submitted_payloads: list[dict[str, Any]] = []

    class SuccessfulVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            submitted_payloads.append(payload)
            index = len(submitted_payloads)
            return {
                "provider_task_id": f"octo_task_{index:03d}",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client.app.state.service.video_provider = SuccessfulVideoProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/final_video/generate", json={}))

    assert len(generated["tasks"]) == 2
    assert [task["payload"]["shot_id"] for task in generated["tasks"]] == ["shot_01", "shot_02"]
    assert [task["provider_task_id"] for task in generated["tasks"]] == ["octo_task_001", "octo_task_002"]
    assert [task["download_path"] for task in generated["tasks"]] == ["clips/shot_01.mp4", "clips/shot_02.mp4"]
    assert submitted_payloads[0]["model"] == "omni_flash-10s"
    assert submitted_payloads[0]["prompt"].startswith("旁白（男声，中文）：认识数字 1")
    assert submitted_payloads[0]["images"] == ["https://cdn.example/asset_ref_01.png"]
    assert submitted_payloads[1]["images"] == ["https://cdn.example/asset_ref_02.png"]


def test_real_image_provider_success_persists_task_and_downloadable_path(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "真实图片成功")
    project_id = project["project_id"]

    class SuccessfulImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            assert payload["asset_id"].startswith("asset_ref_")
            return {
                "provider_task_id": f"image_remote_{payload['asset_id']}",
                "status": "completed",
                "image_url": f"https://cdn.example/{payload['asset_id']}.png",
                "raw": {"id": f"image_remote_{payload['asset_id']}"},
            }

        def download_image(self, image_url: str, target_path: Path):
            assert image_url.startswith("https://cdn.example/asset_ref_")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nimage")

    client.app.state.service.image_provider = SuccessfulImageProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={}))

    assert generated["status"] == "needs_review"
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 6
    task = tasks[0]
    assert task["task_type"] == "image_generation"
    assert task["status"] == "completed"
    assert task["provider_task_id"] == "image_remote_asset_ref_01"
    assert task["image_url"] == "https://cdn.example/asset_ref_01.png"
    assert task["image_path"] == "assets/generated_images/asset_ref_01.png"
    assert task["error_code"] is None
    assert task["retryable"] is False
    downloaded = client.get(f"/projects/{project_id}/images/asset_ref_01.png")
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("image/png")
    assert downloaded.content.startswith(b"\x89PNG")


def test_intro_video_asset_generation_expands_short_source_prompt_ids_for_image_provider(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "图片 prompt 加固")
    project_id = project["project_id"]
    captured_prompts: list[str] = []

    class CaptureImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            captured_prompts.append(payload["prompt"])
            return {
                "provider_task_id": f"image_remote_{payload['asset_id']}",
                "status": "completed",
                "b64_json": "iVBORw0KGgppbWFnZQ==",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nimage")

    client.app.state.service.image_provider = CaptureImageProvider()

    unwrap(client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={}))

    assert captured_prompts
    assert captured_prompts[0] != "shot_01"
    assert "shot_01" in captured_prompts[0]
    assert "小学数学导入视频参考图" in captured_prompts[0]
    assert "卡通桌面出现苹果和数字卡片" in captured_prompts[0]


def test_intro_video_asset_generation_respects_image_limit_and_quality_option(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "图片数量限制")
    project_id = project["project_id"]
    payloads: list[dict[str, Any]] = []

    class CaptureImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            payloads.append(payload)
            return {
                "provider_task_id": f"image_remote_{payload['asset_id']}",
                "status": "completed",
                "b64_json": "iVBORw0KGgppbWFnZQ==",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nimage")

    client.app.state.service.image_provider = CaptureImageProvider()

    unwrap(
        client.post(
            f"/projects/{project_id}/nodes/intro_video_asset/generate",
            json={"image_limit": 1, "image_quality": "low"},
        )
    )

    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    assert len(payloads) == 1
    assert payloads[0]["quality"] == "low"


def test_real_image_provider_failure_persists_failed_task_node_error_and_redacts(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "真实图片失败")
    project_id = project["project_id"]

    class FailingImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                "HTTP 503",
                retryable=True,
                status_code=503,
                response_excerpt='{"error":"upstream down","api_key":"sk-image-secret"}',
            )

    client.app.state.service.image_provider = FailingImageProvider()

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "IMAGE_REQUEST_FAILED"
    assert error["retryable"] is True
    assert "sk-image-secret" not in str(error)
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    task = tasks[0]
    assert task["status"] == "failed"
    assert task["error_code"] == "IMAGE_REQUEST_FAILED"
    assert task["retryable"] is True
    assert task["image_path"] == "assets/generated_images/asset_ref_01.png"
    asset_node = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_asset"))
    assert asset_node["status"] == "blocked"
    assert asset_node["content"]["error_code"] == "IMAGE_REQUEST_FAILED"
    errors_log = Path(project["project_dir"]) / "logs" / "errors.log"
    assert "IMAGE_REQUEST_FAILED" in errors_log.read_text(encoding="utf-8")
    assert "sk-image-secret" not in errors_log.read_text(encoding="utf-8")


def test_intro_video_asset_empty_llm_response_returns_diagnostic_provider_error(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "资产空响应")
    project_id = project["project_id"]

    class EmptyAssetProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            assert kwargs["node_id"] == "intro_video_asset"
            raise ValueError("Expecting value: line 1 column 1 (char 0)")

    client.app.state.service.provider = EmptyAssetProvider()

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "INTRO_VIDEO_ASSET_JSON_EMPTY"
    assert error["retryable"] is True
    assert "Expecting value" not in error["message"]
    asset_node = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_asset"))
    assert asset_node["status"] == "blocked"
    assert asset_node["content"]["error_code"] == "INTRO_VIDEO_ASSET_JSON_EMPTY"
    assert unwrap(client.get(f"/projects/{project_id}/tasks")) == []


def test_intro_video_asset_non_json_llm_response_returns_diagnostic_provider_error(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "资产非 JSON")
    project_id = project["project_id"]

    class NonJsonAssetProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            raise ValueError("not json: bearer secret-token and sk-real-secret")

    client.app.state.service.provider = NonJsonAssetProvider()

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "INTRO_VIDEO_ASSET_JSON_INVALID"
    assert error["retryable"] is True
    assert "sk-real-secret" not in str(error)
    assert "secret-token" not in str(error)
    asset_node = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_asset"))
    assert asset_node["status"] == "blocked"
    assert asset_node["content"]["error_code"] == "INTRO_VIDEO_ASSET_JSON_INVALID"


def test_intro_video_asset_missing_assets_returns_schema_error(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "资产缺字段")
    project_id = project["project_id"]

    class MissingAssetsProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            return {"items": []}

    client.app.state.service.provider = MissingAssetsProvider()

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "INTRO_VIDEO_ASSET_SCHEMA_INVALID"
    assert "assets" in error["message"]
    asset_node = unwrap(client.get(f"/projects/{project_id}/nodes/intro_video_asset"))
    assert asset_node["status"] == "blocked"
    assert asset_node["content"]["error_code"] == "INTRO_VIDEO_ASSET_SCHEMA_INVALID"


def test_intro_video_asset_valid_llm_json_continues_to_image_generation_tasks(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "资产合法 JSON")
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])

    class ValidAssetProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            return {
                "assets": [
                    {
                        "asset_id": "asset_ref_01",
                        "source_prompt_id": "scene_01",
                        "storage_path": "08B_导入视频资产/asset_ref_01.png",
                        "status": "approved",
                    }
                ]
            }

    class SuccessfulImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            return {
                "provider_task_id": "image_remote_asset_ref_01",
                "status": "completed",
                "image_url": "https://cdn.example/asset_ref_01.png",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nasset")

    client.app.state.service.provider = ValidAssetProvider()
    client.app.state.service.image_provider = SuccessfulImageProvider()

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={}))

    assert generated["status"] == "needs_review"
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_type"] == "image_generation"
    assert task["status"] == "completed"
    assert task["provider_task_id"] == "image_remote_asset_ref_01"
    assert task["image_path"] == "assets/generated_images/asset_ref_01.png"
    assert task["error_code"] is None
    assert task["retryable"] is False
    assert (project_dir / "assets" / "generated_images" / "asset_ref_01.png").read_bytes().startswith(b"\x89PNG")


def test_intro_video_asset_b64_image_response_persists_completed_task_and_file(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "资产 b64 图片")
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])

    class ValidAssetProvider:
        name = "deepseek"

        def complete_json(self, **kwargs):
            return {
                "assets": [
                    {
                        "asset_id": "asset_ref_01",
                        "source_prompt_id": "scene_01",
                        "storage_path": "08B_导入视频资产/asset_ref_01.png",
                        "status": "approved",
                    }
                ]
            }

    provider = NewApiImageProvider(
        api_key="test-token",
        base_url="https://image.example/v1",
        model="gpt-image-2",
        transport=lambda *args, **kwargs: {"data": [{"b64_json": "iVBORw0KGgppbWFnZQ=="}]},
    )
    client.app.state.service.provider = ValidAssetProvider()
    client.app.state.service.image_provider = provider

    generated = unwrap(client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={}))

    assert generated["status"] == "needs_review"
    tasks = unwrap(client.get(f"/projects/{project_id}/tasks"))
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_type"] == "image_generation"
    assert task["status"] == "completed"
    assert task["image_path"] == "assets/generated_images/asset_ref_01.png"
    assert task["download_status"] == "downloaded"
    assert task["error_code"] is None
    assert (project_dir / "assets" / "generated_images" / "asset_ref_01.png").read_bytes().startswith(b"\x89PNG")


def test_retry_image_task_resubmits_single_image_and_updates_task(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_screenplay(client, "图片重试")
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "intro_video_asset",
            "image_generation",
            {"asset_id": "asset_ref_01", "prompt": "卡通苹果", "image_path": "assets/generated_images/asset_ref_01.png"},
            status="failed",
            result={"image_path": "assets/generated_images/asset_ref_01.png", "error_code": "IMAGE_REQUEST_FAILED", "retryable": True},
            error_message="HTTP 503",
        )

    class RetryImageProvider:
        def generate_image(self, payload: dict[str, Any]):
            assert payload["asset_id"] == "asset_ref_01"
            return {
                "provider_task_id": "image_remote_retry",
                "status": "completed",
                "image_url": "https://cdn.example/retry.png",
                "raw": {},
            }

        def download_image(self, image_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"\x89PNG\r\n\x1a\nretry")

    client.app.state.service.image_provider = RetryImageProvider()

    retried = unwrap(client.post(f"/projects/{project_id}/tasks/{task['task_id']}/retry"))

    assert retried["task_id"] == task["task_id"]
    assert retried["status"] == "completed"
    assert retried["provider_task_id"] == "image_remote_retry"
    assert retried["image_path"] == "assets/generated_images/asset_ref_01.png"
    assert retried["retryable"] is False
    assert (project_dir / "assets" / "generated_images" / "asset_ref_01.png").read_bytes().startswith(b"\x89PNG")


def test_retry_video_clip_task_resubmits_single_clip(tmp_path: Path):
    client = make_client(tmp_path)
    project = _create_project_with_approved_storyboard(client, "视频 clip 重试")
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {
                "shot_id": "shot_01",
                "model": "omni_flash-10s",
                "size": "1280x720",
                "prompt": "旁白（男声，中文）：重试镜头",
                "reference_image_ids": ["asset_ref_01"],
            },
            status="failed",
            result={"clip_path": "clips/shot_01.mp4", "error_code": "OCTO_REQUEST_FAILED", "retryable": True},
            error_message="HTTP 503",
        )

    class RetryVideoProvider:
        def submit_video(self, payload: dict[str, Any]):
            assert payload["model"] == "omni_flash-10s"
            assert payload["prompt"] == "旁白（男声，中文）：重试镜头"
            return {
                "provider_task_id": "octo_retry_001",
                "status": "queued",
                "progress": 0,
                "video_url": None,
                "raw": {},
            }

    client.app.state.service.video_provider = RetryVideoProvider()

    retried = unwrap(client.post(f"/projects/{project_id}/tasks/{task['task_id']}/retry"))

    assert retried["task_id"] == task["task_id"]
    assert retried["status"] == "queued"
    assert retried["provider_task_id"] == "octo_retry_001"
    assert retried["clip_path"] == "clips/shot_01.mp4"
    assert retried["download_status"] == "not_started"
    assert retried["retryable"] is False


def test_sync_task_queries_octo_and_downloads_completed_clip(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "同步视频任务",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_1", "shot_id": "shot_01"},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            assert provider_task_id == "task_remote_1"
            return {
                "provider_task_id": provider_task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/shot_01.mp4",
                "raw": {},
            }

        def download_video(self, video_url: str, target_path: Path):
            assert video_url == "https://cdn.example/shot_01.mp4"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"fake mp4")

    client.app.state.service.video_provider = StubVideoProvider()

    synced = unwrap(client.get(f"/projects/{project_id}/tasks/{task['task_id']}"))

    assert synced["status"] == "completed"
    assert synced["result"]["video_url"] == "https://cdn.example/shot_01.mp4"
    assert synced["download_path"] == "clips/shot_01.mp4"
    assert synced["video_url_present"] is True
    assert synced["result"]["download_status"] == "downloaded"
    assert (project_dir / "clips" / "shot_01.mp4").read_bytes() == b"fake mp4"


def test_sync_task_keeps_completed_status_when_download_fails(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "下载失败保留状态",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_2", "shot_id": "shot_01"},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            return {
                "provider_task_id": provider_task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/forbidden.mp4",
                "raw": {},
            }

        def download_video(self, video_url: str, target_path: Path):
            raise ProviderError("OCTO_DOWNLOAD_FAILED", "download forbidden", retryable=True)

    client.app.state.service.video_provider = StubVideoProvider()

    synced = unwrap(client.get(f"/projects/{project_id}/tasks/{task['task_id']}"))

    assert synced["status"] == "completed"
    assert synced["result"]["video_url"] == "https://cdn.example/forbidden.mp4"
    assert synced["result"]["download_status"] == "failed"
    assert synced["error_code"] == "VIDEO_DOWNLOAD_FAILED"
    errors_log = project_dir / "logs" / "errors.log"
    assert "VIDEO_DOWNLOAD_FAILED" in errors_log.read_text(encoding="utf-8")


def test_sync_task_persists_video_quota_exhausted_error_code(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "视频配额失败分类",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_quota", "shot_id": "shot_01"},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            return {
                "provider_task_id": provider_task_id,
                "status": "failed",
                "progress": 0,
                "video_url": None,
                "error_code": "VIDEO_QUOTA_EXHAUSTED",
                "retryable": False,
                "error_message": "RESOURCE_EXHAUSTED PUBLIC_ERROR_USER_QUOTA_REACHED",
                "response_excerpt": '{"status":"RESOURCE_EXHAUSTED","reason":"PUBLIC_ERROR_USER_QUOTA_REACHED"}',
                "raw": {},
            }

    client.app.state.service.video_provider = StubVideoProvider()

    synced = unwrap(client.get(f"/projects/{project_id}/tasks/{task['task_id']}"))

    assert synced["status"] == "failed"
    assert synced["error_code"] == "VIDEO_QUOTA_EXHAUSTED"
    assert synced["retryable"] is False
    assert synced["result"]["error_code"] == "VIDEO_QUOTA_EXHAUSTED"
    assert synced["result"]["retryable"] is False
    errors_log = project_dir / "logs" / "errors.log"
    assert "VIDEO_QUOTA_EXHAUSTED" in errors_log.read_text(encoding="utf-8")


def test_sync_task_composes_final_video_after_all_real_clips_are_downloaded(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "真实 clips 合成",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task_1 = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_1", "shot_id": "shot_01", "reference_image_ids": ["asset_ref_01"]},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )
        client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_2", "shot_id": "shot_02", "reference_image_ids": ["asset_ref_02"]},
            status="completed",
            result={"download_path": "clips/shot_02.mp4", "download_status": "downloaded", "provider_task_id": "task_remote_2"},
        )
    (project_dir / "clips").mkdir(parents=True, exist_ok=True)
    (project_dir / "clips" / "shot_02.mp4").write_bytes(b"clip-2")
    composed: dict[str, Any] = {}

    def fake_compose(project_dir_arg: Path, clip_rel_paths: list[str]) -> Path:
        composed["clips"] = clip_rel_paths
        output = project_dir_arg / "outputs" / "final_video.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"real final video")
        return output

    monkeypatch.setattr("app.services.compose_final_video_from_clips", fake_compose)

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            return {
                "provider_task_id": provider_task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/shot_01.mp4",
                "raw": {},
            }

        def download_video(self, video_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"clip-1")

    client.app.state.service.video_provider = StubVideoProvider()

    unwrap(client.get(f"/projects/{project_id}/tasks/{task_1['task_id']}"))

    assert composed["clips"] == ["clips/shot_01.mp4", "clips/shot_02.mp4"]
    assert (project_dir / "outputs" / "final_video.mp4").read_bytes() == b"real final video"
    final_node = unwrap(client.get(f"/projects/{project_id}/nodes/final_video"))
    assert final_node["status"] == "needs_review"
    assert final_node["content"]["video_path"] == "outputs/final_video.mp4"


def test_sync_task_composes_final_video_after_single_real_clip_when_limited(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "真实单 clip 合成",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task_1 = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_1", "shot_id": "shot_01", "reference_image_ids": ["asset_ref_01"]},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )
    composed: dict[str, Any] = {}

    def fake_compose(project_dir_arg: Path, clip_rel_paths: list[str]) -> Path:
        composed["clips"] = clip_rel_paths
        output = project_dir_arg / "outputs" / "final_video.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"single real final video")
        return output

    monkeypatch.setattr("app.services.compose_final_video_from_clips", fake_compose)

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            return {
                "provider_task_id": provider_task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/shot_01.mp4",
                "raw": {},
            }

        def download_video(self, video_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"clip-1")

    client.app.state.service.video_provider = StubVideoProvider()

    unwrap(client.get(f"/projects/{project_id}/tasks/{task_1['task_id']}"))

    assert composed["clips"] == ["clips/shot_01.mp4"]
    assert (project_dir / "outputs" / "final_video.mp4").read_bytes() == b"single real final video"
    final_node = unwrap(client.get(f"/projects/{project_id}/nodes/final_video"))
    assert final_node["status"] == "needs_review"
    assert final_node["content"]["clip_count"] == 1
    assert final_node["content"]["video_path"] == "outputs/final_video.mp4"


def test_sync_task_marks_compose_failure_when_ffmpeg_missing(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "真实合成失败诊断",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    with client.app.state.store.connect(project_dir) as conn:
        task_1 = client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_1", "shot_id": "shot_01", "reference_image_ids": ["asset_ref_01"]},
            status="processing",
            result={"download_path": "clips/shot_01.mp4"},
        )
        client.app.state.store.create_task(
            conn,
            project_id,
            "final_video",
            "video_clip_generation",
            {"provider_task_id": "task_remote_2", "shot_id": "shot_02", "reference_image_ids": ["asset_ref_02"]},
            status="completed",
            result={"download_path": "clips/shot_02.mp4", "download_status": "downloaded", "provider_task_id": "task_remote_2"},
        )
    (project_dir / "clips").mkdir(parents=True, exist_ok=True)
    (project_dir / "clips" / "shot_02.mp4").write_bytes(b"clip-2")

    def failing_compose(project_dir_arg: Path, clip_rel_paths: list[str]) -> Path:
        raise RuntimeError("缺少 ffmpeg，无法合成真实 final_video.mp4")

    monkeypatch.setattr("app.services.compose_final_video_from_clips", failing_compose)

    class StubVideoProvider:
        def query_task(self, provider_task_id: str):
            return {
                "provider_task_id": provider_task_id,
                "status": "completed",
                "progress": 100,
                "video_url": "https://cdn.example/shot_01.mp4",
                "raw": {},
            }

        def download_video(self, video_url: str, target_path: Path):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"clip-1")

    client.app.state.service.video_provider = StubVideoProvider()

    synced = unwrap(client.get(f"/projects/{project_id}/tasks/{task_1['task_id']}"))

    assert synced["status"] == "completed"
    assert synced["error_code"] == "FINAL_VIDEO_COMPOSE_FAILED"
    assert synced["result"]["download_status"] == "downloaded"
    assert synced["result"]["compose_status"] == "failed"
    assert "ffmpeg" in synced["result"]["compose_error"]
    final_node = unwrap(client.get(f"/projects/{project_id}/nodes/final_video"))
    assert final_node["status"] == "blocked"
    assert final_node["content"]["error_code"] == "FINAL_VIDEO_COMPOSE_FAILED"
    assert not (project_dir / "outputs" / "final_video.mp4").exists()


def test_download_clip_returns_only_project_mp4_clips(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "clip 下载",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    clip = project_dir / "clips" / "shot_01.mp4"
    clip.write_bytes(b"real clip")
    (project_dir / "clips" / "note.txt").write_text("not mp4", encoding="utf-8")

    downloaded = client.get(f"/projects/{project_id}/clips/shot_01.mp4")
    rejected = client.get(f"/projects/{project_id}/clips/note.txt")
    traversal = client.get(f"/projects/{project_id}/clips/..%2Fproject.db")

    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("video/mp4")
    assert downloaded.content == b"real clip"
    assert rejected.status_code == 404
    assert traversal.status_code == 404


def test_download_image_returns_only_project_generated_images(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "图片下载",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]
    project_dir = Path(project["project_dir"])
    image = project_dir / "assets" / "generated_images" / "asset_ref_01.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"\x89PNG\r\n\x1a\nimage")
    (project_dir / "assets" / "generated_images" / "note.txt").write_text("not image", encoding="utf-8")

    downloaded = client.get(f"/projects/{project_id}/images/asset_ref_01.png")
    rejected = client.get(f"/projects/{project_id}/images/note.txt")
    traversal = client.get(f"/projects/{project_id}/images/..%2F..%2Fproject.db")

    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("image/png")
    assert downloaded.content.startswith(b"\x89PNG")
    assert rejected.status_code == 404
    assert traversal.status_code == 404


def test_download_final_video_returns_readable_error_when_missing(tmp_path: Path):
    client = make_client(tmp_path)
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "最终视频缺失",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )

    response = client.get(f"/projects/{project['project_id']}/outputs/final_video.mp4")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "OUTPUT_NOT_FOUND"
    assert "最终视频文件不存在" in error["message"]


def test_real_video_mode_ppt_export_requires_composed_final_video(tmp_path: Path):
    client = make_client(tmp_path)
    client.app.state.service.provider = type("StubTextProvider", (), {"name": "deepseek"})()
    client.app.state.service.video_provider = type("StubVideoProvider", (), {})()
    project = unwrap(
        client.post(
            "/projects",
            json={
                "name": "真实模式 PPT",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        )
    )
    project_id = project["project_id"]

    response = client.post(f"/projects/{project_id}/export/ppt")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PPT_ARTIFACT_NOT_READY"
    final_video = Path(project["project_dir"]) / "outputs" / "final_video.mp4"
    assert not final_video.exists()


def test_octo_video_download_uses_browser_compatible_headers(monkeypatch, tmp_path: Path):
    captured = {}

    class StubResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"fake mp4"

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return StubResponse()

    monkeypatch.setattr("app.providers.urllib.request.urlopen", fake_urlopen)
    provider = OctoVideoProvider(api_key="test-token", base_url="https://otuapi.com")
    target = tmp_path / "clip.mp4"

    provider.download_video("https://cdn.example/clip.mp4", target)

    assert target.read_bytes() == b"fake mp4"
    assert captured["headers"]["User-agent"].startswith("Mozilla/5.0")
    assert "video/mp4" in captured["headers"]["Accept"]
    assert "Referer" not in captured["headers"]
