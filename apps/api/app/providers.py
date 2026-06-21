from __future__ import annotations

import json
import re
import base64
import http.client
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class ProviderError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        status_code: int | None = None,
        response_excerpt: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status_code = status_code
        self.response_excerpt = sanitize_provider_excerpt(response_excerpt or "")


def sanitize_provider_excerpt(value: str, limit: int = 600) -> str:
    if not value:
        return ""
    redacted = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"',}]+", r"\1<redacted>", value)
    redacted = re.sub(r"(?i)(\bbearer\s+)[^\s\"',}]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"(?i)((?:api[_-]?key|token|secret|key)\s*[\"']?\s*[:=]\s*[\"']?)[^\"',}\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"\b(?:sk|octo|deepseek)-[A-Za-z0-9._-]{8,}\b", "<redacted>", redacted)
    redacted = redacted.replace("\r", " ").replace("\n", " ")
    return redacted[:limit]


def strip_json_fence(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text


def validate_required_fields(content: dict[str, Any], schema: dict[str, Any]) -> None:
    for field in schema.get("required", []):
        if field not in content:
            raise ValueError(f"Missing required JSON field: {field}")


class MinimaxTextProvider:
    name = "minimax"

    def __init__(
        self,
        api_key: str | None,
        base_url: str | None,
        model: str,
        transport=None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or "").rstrip("/")
        self.model = "MiniMax-M3" if model.upper() == "M3" else model
        self.transport = transport or self._http_transport

    def complete_json(
        self,
        *,
        node_id: str,
        prompt: str,
        schema: dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                raw = self.transport(
                    {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "thinking": {"type": "disabled"},
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                content = self._extract_content(raw)
                parsed = json.loads(strip_json_fence(content))
                if set(parsed.keys()).issuperset({"data"}) and isinstance(parsed.get("data"), dict):
                    parsed = parsed["data"]
                validate_required_fields(parsed, schema)
                return parsed
            except (json.JSONDecodeError, ValueError, ProviderError) as exc:
                last_error = exc
        raise ProviderError("MINIMAX_JSON_INVALID", f"{node_id} 输出不是合法 JSON：{last_error}", retryable=True)

    def _extract_content(self, raw: dict[str, Any]) -> str:
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("MINIMAX_RESPONSE_INVALID", "Minimax 返回格式不符合预期", retryable=True) from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("MINIMAX_EMPTY_RESPONSE", "Minimax 返回内容为空", retryable=True)
        return content

    def _http_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("MINIMAX_KEY_MISSING", "未配置 MINMAX_API_KEY", retryable=False)
        if not self.base_url:
            raise ProviderError("MINIMAX_BASE_URL_MISSING", "未配置 MINMAX_BASE_URL", retryable=False)
        url = f"{self.base_url}/chat/completions" if self.base_url.endswith("/v1") else f"{self.base_url}/v1/chat/completions"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return _request_json(request, "MINIMAX_REQUEST_FAILED")


class MinimaxTTSProvider:
    name = "minimax-tts"

    def __init__(
        self,
        api_key: str | None,
        base_url: str | None,
        model: str,
        voice_id: str = "Chinese (Mandarin)_Gentleman",
        transport=None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.minimaxi.com").rstrip("/")
        self.model = model
        self.voice_id = voice_id
        self.transport = transport or self._http_transport

    def synthesize(self, text: str, output_path: Path) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("MINIMAX_TTS_KEY_MISSING", "未配置 MINIMAX_API_KEY", retryable=False)
        payload = {
            "model": self.model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": self.voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
        }
        raw = self.transport(payload)
        audio_bytes = self._extract_audio_bytes(raw)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)
        if output_path.stat().st_size == 0:
            raise ProviderError("MINIMAX_TTS_EMPTY_AUDIO", "Minimax TTS 返回音频为空", retryable=True)
        return {
            "audio_path": str(output_path),
            "voice_id": self.voice_id,
            "voice_gender": "male",
            "voice_language": "zh-CN",
            "provider": self.name,
            "model": self.model,
        }

    def _extract_audio_bytes(self, raw: dict[str, Any]) -> bytes:
        candidates = [
            raw.get("audio"),
            raw.get("data", {}).get("audio") if isinstance(raw.get("data"), dict) else None,
            raw.get("data", {}).get("audio_base64") if isinstance(raw.get("data"), dict) else None,
            raw.get("audio_base64"),
        ]
        value = next((item for item in candidates if isinstance(item, str) and item.strip()), "")
        if not value:
            raise ProviderError("MINIMAX_TTS_RESPONSE_INVALID", "Minimax TTS 返回格式不符合预期", retryable=True)
        text = value.strip()
        try:
            if re.fullmatch(r"[0-9A-Fa-f]+", text) and len(text) % 2 == 0:
                return bytes.fromhex(text)
            return base64.b64decode(text)
        except ValueError as exc:
            raise ProviderError("MINIMAX_TTS_AUDIO_INVALID", "Minimax TTS 音频编码无法解析", retryable=True) from exc

    def _http_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("MINIMAX_TTS_KEY_MISSING", "未配置 MINIMAX_API_KEY", retryable=False)
        url = (
            self.base_url
            if self.base_url.endswith("/t2a_v2")
            else f"{self.base_url.rstrip('/')}/v1/t2a_v2"
        )
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return _request_json(request, "MINIMAX_TTS_REQUEST_FAILED")


class DeepSeekTextProvider:
    name = "deepseek"

    def __init__(
        self,
        api_key: str | None,
        base_url: str | None,
        model: str,
        transport=None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or "").rstrip("/")
        self.model = model
        self.transport = transport or self._http_transport

    def complete_json(
        self,
        *,
        node_id: str,
        prompt: str,
        schema: dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError("DEEPSEEK_KEY_MISSING", "未配置 DEEPSEEK_API_KEY", retryable=False)
        if not self.base_url:
            raise ProviderError("DEEPSEEK_BASE_URL_MISSING", "未配置 DEEPSEEK_BASE_URL", retryable=False)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是山海教育全链路生成模块。必须只输出一个合法 JSON 对象，不要解释，不要 Markdown 包裹。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        for _ in range(2):
            try:
                raw = self.transport(payload, headers, self._chat_url())
                content = self._extract_content(raw)
                parsed = json.loads(strip_json_fence(content))
                if set(parsed.keys()).issuperset({"data"}) and isinstance(parsed.get("data"), dict):
                    parsed = parsed["data"]
                validate_required_fields(parsed, schema)
                return parsed
            except (json.JSONDecodeError, ValueError, ProviderError) as exc:
                last_error = exc
        raise ProviderError("DEEPSEEK_JSON_INVALID", f"{node_id} 输出不是合法 JSON：{last_error}", retryable=True)

    def _chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def _extract_content(self, raw: dict[str, Any]) -> str:
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("DEEPSEEK_RESPONSE_INVALID", "DeepSeek 返回格式不符合预期", retryable=True) from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("DEEPSEEK_EMPTY_RESPONSE", "DeepSeek 返回内容为空", retryable=True)
        return content

    def _http_transport(self, payload: dict[str, Any], headers: dict[str, str], url: str) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        return _request_json(request, "DEEPSEEK_REQUEST_FAILED")


class OctoVideoProvider:
    name = "octo"

    def __init__(self, api_key: str | None, base_url: str, transport=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport or self._http_transport

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = self.transport("POST", f"{self.base_url}/v1/videos", headers=self._headers(), json=payload)
        task_id = raw.get("id") or raw.get("task_id") or raw.get("data", {}).get("id")
        if not task_id:
            raise ProviderError("OCTO_RESPONSE_INVALID", "章鱼哥提交视频未返回任务 ID", retryable=True)
        return {
            "provider_task_id": task_id,
            "status": self._normalize_status(raw),
            "progress": self._normalize_progress(raw),
            "video_url": self._extract_video_url(raw),
            "remix_id": self._extract_remix_id(raw),
            "raw": raw,
        }

    def query_task(self, provider_task_id: str) -> dict[str, Any]:
        raw = self.transport("GET", f"{self.base_url}/v1/videos/{urllib.parse.quote(provider_task_id)}", headers=self._headers())
        error_code, retryable = self._classify_query_error(raw)
        return {
            "provider_task_id": provider_task_id,
            "status": self._normalize_status(raw),
            "progress": self._normalize_progress(raw),
            "video_url": self._extract_video_url(raw),
            "remix_id": self._extract_remix_id(raw),
            "error_message": self._extract_error(raw),
            "error_code": error_code,
            "retryable": retryable,
            "response_excerpt": sanitize_provider_excerpt(json.dumps(raw.get("error") or raw, ensure_ascii=False)),
            "raw": raw,
        }

    def download_video(self, video_url: str, target_path) -> None:
        request = urllib.request.Request(
            video_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                ),
                "Accept": "video/mp4,video/*;q=0.9,application/octet-stream,*/*;q=0.5",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            raise ProviderError("OCTO_DOWNLOAD_FAILED", f"视频下载失败：HTTP {exc.code}", retryable=True) from exc
        except urllib.error.URLError as exc:
            raise ProviderError("OCTO_DOWNLOAD_FAILED", f"视频下载失败：{exc.reason}", retryable=True) from exc

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError("OCTO_KEY_MISSING", "未配置 OCTO_API_KEY", retryable=False)
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _http_transport(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        body = kwargs.get("json")
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, headers=kwargs.get("headers") or {}, method=method)
        return _request_json(request, "OCTO_REQUEST_FAILED")

    def _normalize_status(self, raw: dict[str, Any]) -> str:
        data = raw.get("data")
        data_status = data.get("status") if isinstance(data, dict) else None
        status = str(raw.get("status") or data_status or "").lower()
        if status == "success":
            return "completed"
        if status in {"in_progress", "processing"}:
            return "processing"
        return status or "unknown"

    def _normalize_progress(self, raw: dict[str, Any]) -> int:
        progress = raw.get("progress") or raw.get("data", {}).get("progress") or 0
        if isinstance(progress, str):
            progress = progress.strip().rstrip("%")
        try:
            return int(float(progress))
        except (TypeError, ValueError):
            return 0

    def _extract_video_url(self, raw: dict[str, Any]) -> str | None:
        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
        return (
            data.get("video_url")
            or raw.get("video_url")
            or raw.get("url")
            or raw.get("result_url")
            or data.get("url")
            or data.get("result_url")
            or data.get("first_video_url")
            or result.get("video_url")
            or result.get("url")
        )

    def _extract_remix_id(self, raw: dict[str, Any]) -> str | None:
        data = raw.get("data", {})
        value = raw.get("remix_id") or data.get("remix_id")
        if value:
            return value
        size = data.get("size") or raw.get("size")
        return size if isinstance(size, str) and size.startswith("video_") else None

    def _extract_error(self, raw: dict[str, Any]) -> str | None:
        error = raw.get("error")
        if isinstance(error, dict):
            parts = [error.get("message"), error.get("status")]
            for detail in error.get("details") or []:
                if isinstance(detail, dict):
                    parts.append(detail.get("reason"))
            return " ".join(str(part) for part in parts if part)
        if isinstance(error, str):
            return error
        return raw.get("fail_reason") or raw.get("message")

    def _classify_query_error(self, raw: dict[str, Any]) -> tuple[str | None, bool]:
        if self._normalize_status(raw) != "failed":
            return None, False
        error_text = json.dumps(raw.get("error") or raw, ensure_ascii=False)
        if "RESOURCE_EXHAUSTED" in error_text or "PUBLIC_ERROR_USER_QUOTA_REACHED" in error_text:
            return "VIDEO_QUOTA_EXHAUSTED", False
        return "VIDEO_TASK_FAILED", True


class NewApiImageProvider:
    name = "newapi-image"

    def __init__(self, api_key: str | None, base_url: str, model: str, transport=None):
        self.api_key = api_key
        self.base_url = self._normalize_base_url(base_url)
        self.model = model
        self.transport = transport or self._sdk_transport

    def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: ProviderError | None = None
        raw: dict[str, Any] | None = None
        for request_json in self._request_variants(payload):
            for attempt in range(2):
                try:
                    raw = self.transport(
                        "POST",
                        self._image_url(),
                        headers=self._headers(),
                        json=request_json,
                    )
                    break
                except ProviderError as exc:
                    last_error = exc
                    if attempt == 0 and self._should_retry_same_variant(exc):
                        continue
                    if not self._should_try_next_variant(exc):
                        raise
                    break
            if raw is not None:
                break
        else:
            assert last_error is not None
            raise last_error
        assert raw is not None
        image_url = self._extract_image_url(raw)
        b64_json = self._extract_b64_json(raw)
        provider_task_id = self._extract_task_id(raw)
        if provider_task_id and not image_url and not b64_json and self._looks_async_task_response(raw):
            raise ProviderError(
                "IMAGE_ASYNC_TASK_UNSUPPORTED",
                "图片生成接口返回异步任务 ID，当前同步生图链路尚未配置 query/download",
                retryable=True,
                response_excerpt=json.dumps(
                    {"provider_task_id": provider_task_id, "status": self._normalize_status(raw)},
                    ensure_ascii=False,
                ),
            )
        if not image_url and not b64_json:
            raise ProviderError("IMAGE_RESPONSE_INVALID", "图片生成未返回 url 或 b64_json", retryable=True)
        return {
            "provider_task_id": provider_task_id,
            "status": self._normalize_status(raw),
            "image_url": image_url,
            "b64_json": b64_json,
            "raw": raw,
        }

    def _request_variants(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        base = {
            "model": payload.get("model") or self.model,
            "prompt": payload["prompt"],
            "size": payload.get("size", "1024x1024"),
            "quality": payload.get("quality", "high"),
            "response_format": payload.get("response_format", "b64_json"),
            "n": 1,
        }
        variants = [base]
        for size, quality in [("1024x1024", "high"), ("1024x1024", "low")]:
            fallback = {**base, "size": size, "quality": quality}
            if fallback not in variants:
                variants.append(fallback)
        return variants

    def _should_try_next_variant(self, exc: ProviderError) -> bool:
        if not exc.retryable:
            return False
        text = f"{exc} {exc.response_excerpt}".lower()
        return (
            exc.status_code in {408, 429, 500, 502, 503, 504}
            or "no available compatible accounts" in text
            or "auth_unavailable" in text
            or "closed connection" in text
            or "upstream" in text
        )

    def _should_retry_same_variant(self, exc: ProviderError) -> bool:
        if not exc.retryable:
            return False
        text = f"{exc} {exc.response_excerpt}".lower()
        return (
            "closed connection" in text
            or "connection error" in text
            or "upstream" in text
        )

    def download_image(self, image_url: str, target_path: Path) -> None:
        try:
            if image_url.startswith("data:image/") and "base64," in image_url:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(base64.b64decode(image_url.split("base64,", 1)[1]))
                return
            request = urllib.request.Request(
                image_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                    ),
                    "Accept": "image/png,image/*;q=0.9,application/octet-stream,*/*;q=0.5",
                },
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            raise ProviderError("IMAGE_DOWNLOAD_FAILED", f"图片下载失败：HTTP {exc.code}", retryable=True) from exc
        except urllib.error.URLError as exc:
            raise ProviderError("IMAGE_DOWNLOAD_FAILED", f"图片下载失败：{exc.reason}", retryable=True) from exc
        except (ValueError, base64.binascii.Error) as exc:
            raise ProviderError("IMAGE_DOWNLOAD_FAILED", "图片 b64 内容无法解码", retryable=False) from exc

    def _image_url(self) -> str:
        if self.base_url.endswith("/images/generations"):
            return self.base_url
        return f"{self.base_url}/images/generations"

    def _normalize_base_url(self, value: str) -> str:
        base_url = value.rstrip("/")
        if base_url.endswith("/v1") or base_url.endswith("/images/generations"):
            return base_url
        return f"{base_url}/v1"

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError("IMAGE_KEY_MISSING", "未配置图片生成 API key", retryable=False)
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _http_transport(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        body = kwargs.get("json")
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, headers=kwargs.get("headers") or {}, method=method)
        return _request_json(request, "IMAGE_REQUEST_FAILED")

    def _sdk_transport(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError:
            return self._http_transport(method, url, **kwargs)
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.images.generate(**kwargs["json"])
            if hasattr(response, "model_dump"):
                return response.model_dump()
            if hasattr(response, "dict"):
                return response.dict()
            return json.loads(json.dumps(response, default=lambda value: getattr(value, "__dict__", str(value))))
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            body = getattr(exc, "body", None)
            message = str(exc)
            excerpt = json.dumps(body, ensure_ascii=False) if body is not None else message
            raise ProviderError(
                "IMAGE_REQUEST_FAILED",
                f"HTTP {status_code}" if status_code else message,
                retryable=status_code in {408, 429, 500, 502, 503, 504} or "connection" in message.lower(),
                status_code=status_code,
                response_excerpt=excerpt,
            ) from exc

    def _normalize_status(self, raw: dict[str, Any]) -> str:
        data = raw.get("data")
        data_status = data.get("status") if isinstance(data, dict) else None
        status = str(raw.get("status") or data_status or "").lower()
        if status in {"success", "succeeded"}:
            return "completed"
        if status in {"in_progress", "processing"}:
            return "processing"
        return status or "completed"

    def _extract_image_url(self, raw: dict[str, Any]) -> str | None:
        data = raw.get("data")
        if isinstance(data, list) and data:
            first = data[0] if isinstance(data[0], dict) else {}
            return first.get("url") or first.get("image_url")
        if isinstance(data, dict):
            nested = data.get("data")
            if isinstance(nested, list) and nested:
                first = nested[0] if isinstance(nested[0], dict) else {}
                return first.get("url") or first.get("image_url")
            return data.get("url") or data.get("image_url") or data.get("result_url")
        return raw.get("url") or raw.get("image_url") or raw.get("result_url")

    def _extract_b64_json(self, raw: dict[str, Any]) -> str | None:
        data = raw.get("data")
        if isinstance(data, list) and data:
            first = data[0] if isinstance(data[0], dict) else {}
            return first.get("b64_json")
        if isinstance(data, dict):
            nested = data.get("data")
            if isinstance(nested, list) and nested:
                first = nested[0] if isinstance(nested[0], dict) else {}
                return first.get("b64_json")
            return data.get("b64_json")
        return raw.get("b64_json")

    def _extract_task_id(self, raw: dict[str, Any]) -> str | None:
        data = raw.get("data")
        if isinstance(data, dict):
            return raw.get("id") or raw.get("task_id") or data.get("id") or data.get("task_id")
        return raw.get("id") or raw.get("task_id")

    def _looks_async_task_response(self, raw: dict[str, Any]) -> bool:
        status = self._normalize_status(raw)
        task_id = self._extract_task_id(raw)
        return bool(task_id and status in {"queued", "pending", "processing", "running", "submitted"})


def _request_json(request: urllib.request.Request, error_code: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8", errors="replace")
            if not body.strip():
                raise ProviderError(
                    _response_error_code(error_code),
                    "上游服务返回空响应",
                    retryable=True,
                )
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise ProviderError(
                    _response_error_code(error_code),
                    "上游服务返回非 JSON 响应",
                    retryable=True,
                    response_excerpt=body,
                ) from exc
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise ProviderError(
            error_code,
            f"HTTP {exc.code}",
            retryable=exc.code in {408, 429, 500, 502, 503, 504},
            status_code=exc.code,
            response_excerpt=body,
        ) from exc
    except urllib.error.URLError as exc:
        raise ProviderError(error_code, str(exc.reason), retryable=True) from exc
    except (http.client.RemoteDisconnected, TimeoutError, socket.timeout) as exc:
        raise ProviderError(error_code, str(exc), retryable=True) from exc


def _response_error_code(error_code: str) -> str:
    if error_code.endswith("_REQUEST_FAILED"):
        return error_code[: -len("_REQUEST_FAILED")] + "_RESPONSE_INVALID"
    return error_code


class FakeProvider:
    name = "fake"

    def generate(self, node_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if node_id == "textbook_parse":
            text = context.get("textbook_text", "")
            lesson_title = "分数的初步认识" if "分数" in text else "数学探究课"
            return {
                "subject": "math",
                "grade": context.get("grade", "3"),
                "textbook_version": context.get("textbook_version", "renjiao"),
                "volume": context.get("volume", "xia"),
                "lesson_title": lesson_title,
                "core_knowledge_points": ["平均分", "二分之一", "分数表示"],
                "teaching_goal_summary": "理解平均分与分数含义，能用分数描述生活中的部分与整体。",
                "key_points": ["理解分数表示部分与整体的关系"],
                "difficulties": ["把生活情境准确抽象为分数表达"],
            }
        if node_id == "lesson_plan":
            parsed = context.get("textbook_parse", {})
            lesson = parsed.get("lesson_title", "数学探究课")
            selected = parsed.get("selected_knowledge_point") or {}
            source_markdown = selected.get("markdown") if isinstance(selected, dict) else None
            source_markdown_path = selected.get("markdown_path") if isinstance(selected, dict) else None
            source_knowledge_point_id = selected.get("knowledge_point_id") if isinstance(selected, dict) else None
            if source_markdown:
                lesson = selected.get("title") or lesson
                return {
                    "source_knowledge_point_id": source_knowledge_point_id,
                    "source_markdown_path": source_markdown_path,
                    "textbook_anchor": f"人教版一年级上册，基于《{lesson}》教材 Markdown 生成。",
                    "teaching_objectives": "学生能认识 1-5 的数量意义，能比较数量大小，能区分几个和第几个，并初步理解数的分与合。",
                    "key_difficulty": "重点是建立 1-5 的数感和数量对应；难点是把教材情境中的位置、比较和分合关系说清楚。",
                    "teaching_flow": "先从教材生活情境导入数数，再用实物、点子图和数字建立对应，随后比较数量、区分第几，最后通过分与合活动巩固。",
                    "blackboard_design": "5以内数的认识：数一数、比一比、排一排、分一分。",
                    "lesson_plan_markdown": (
                        f"# 《{lesson}》公开课教案\n\n"
                        "## 教材依据\n\n"
                        f"{source_markdown[:1200]}\n\n"
                        "## 教学流程\n\n"
                        "1. 情境导入：观察教材图，数出 1-5。\n"
                        "2. 探究活动：用实物、点子图和数字卡片表示数量。\n"
                        "3. 对比提升：练习比大小和第几。\n"
                        "4. 巩固应用：完成分与合活动并表达理由。\n"
                    ),
                    "intro_designs": [
                        self._intro("science", 1, "数字 1-5 从哪里来", "从生活物体数量抽象出数字。"),
                        self._intro("application", 1, "排队和分水果里的 1-5", "用排队、比较和分合场景导入。"),
                        self._intro("story", 1, "小朋友的数字寻宝", "用寻找 1-5 的故事串起教材内容。"),
                    ],
                }
            return {
                "textbook_anchor": f"人教版三年级下册，围绕《{lesson}》展开。",
                "teaching_objectives": "学生能在平均分情境中理解分数意义，能说出二分之一和四分之一表示的部分与整体关系。",
                "key_difficulty": "重点是理解分数意义；难点是用分数准确描述真实生活中的部分与整体。",
                "teaching_flow": "从分披萨的生活情境导入，引导学生观察平均分，再通过摆一摆、说一说、比一比理解二分之一和四分之一，最后回到生活问题完成表达。",
                "blackboard_design": "分数的初步认识：平均分、整体、部分、二分之一、四分之一。",
                "intro_designs": [
                    self._intro("science", 1, "月亮为什么会变成一半", "用月相变化引出部分与整体。"),
                    self._intro("application", 1, "分披萨里的公平问题", "用分披萨引出平均分和二分之一。"),
                    self._intro("story", 1, "小明的半块巧克力", "用故事冲突引出分数表达。"),
                ],
            }
        if node_id == "intro_selection":
            designs = context.get("lesson_plan", {}).get("intro_designs", [])
            primary = designs[1]["design_id"] if len(designs) > 1 else "design_application_01"
            selected_design = next((design for design in designs if design.get("design_id") == primary), None)
            selected_anchor = (
                selected_design.get("anchor_to_lesson")
                if isinstance(selected_design, dict)
                else "通过分披萨的公平问题，引出平均分和二分之一。"
            )
            return {
                "selection_mode": "single_best",
                "selected_design_ids": [primary],
                "primary_design_id": primary,
                "downstream_generation_mode": "three_variants_for_primary",
                "selection_reason": "应用类情境贴近三年级学生生活经验，适合作为导入视频主线。",
                "selected_anchor": selected_anchor,
            }
        if node_id == "intro_video_script":
            selected_anchor = context.get("intro_selection", {}).get("selected_anchor") or "通过分披萨的公平问题，引出平均分和二分之一。"
            return {
                "total_duration_sec": 60,
                "video_type": "application",
                "anchor_to_lesson": selected_anchor,
                "narration_full_text": f"今天，小明和朋友遇到一个公平分披萨的问题。一个披萨平均分成两份，每人得到其中一份。这一份可以怎样表示？原来它就是整体的二分之一。{selected_anchor}",
                "narration_word_count": 82,
                "banned_elements": ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"],
            }
        if node_id == "intro_video_screenplay":
            narration = context.get("intro_video_script", {}).get("narration_full_text", "")
            parts = self._split_text(narration, 3)
            return {
                "scenes": [
                    {"scene_id": "scene_01", "duration_sec": 20, "scene_description": "卡通厨房桌面上出现一个完整披萨。", "character_refs": [], "narration_segment": parts[0]},
                    {"scene_id": "scene_02", "duration_sec": 20, "scene_description": "披萨被平均分成两份，其中一份被高亮。", "character_refs": [], "narration_segment": parts[1]},
                    {"scene_id": "scene_03", "duration_sec": 20, "scene_description": "画面切到分数符号和生活物品的卡通类比。", "character_refs": [], "narration_segment": parts[2]},
                ]
            }
        if node_id == "intro_video_asset":
            return {
                "assets": [
                    {
                        "asset_id": f"asset_ref_{i:02d}",
                        "source_prompt_id": f"shot_{i:02d}",
                        "storage_path": f"assets/ref_{i:02d}.txt",
                        "status": "approved",
                    }
                    for i in range(1, 7)
                ]
            }
        if node_id == "storyboard":
            script = context.get("intro_video_script", {})
            parts = self._split_text(script.get("narration_full_text", ""), 6)
            shots = []
            for index in range(1, 7):
                narration = parts[index - 1]
                shots.append(
                    {
                        "shot_id": f"shot_{index:02d}",
                        "duration_sec": 10,
                        "main_subject": "卡通披萨平均分情境",
                        "character_refs": [],
                        "reference_image_ids": [f"asset_ref_{index:02d}"],
                        "narration_slice": narration,
                        "subtitle": narration,
                        "model_prompt": f"旁白（男声，中文）：{narration}\n画面：卡通披萨平均分情境，第{index}镜头。\n风格：3d_non_realistic, warm classroom illustration\n角色：无真人儿童，使用非写实卡通物品。\n禁止英文配音；如平台自动生成英文音频，则该片段判为不合格，需要静音或重合成中文配音。",
                        "first_frame_test_status": "passed",
                        "first_frame_asset_id": f"asset_ref_{index:02d}",
                    }
                )
            return {"shots": shots}
        if node_id == "final_video":
            return {"clip_count": 6, "clips": [], "model_audio_policy": "discarded_or_mute_later", "english_audio_detected": False}
        raise KeyError(f"Unsupported fake generation node: {node_id}")

    def _intro(self, kind: str, index: int, title: str, hook: str) -> dict[str, Any]:
        return {
            "design_id": f"design_{kind}_{index:02d}",
            "type": kind,
            "title": title,
            "hook": hook,
            "anchor_to_lesson": "把生活中的部分与整体关系连接到分数学习。",
            "recommend_score": 5 if kind == "application" else 4,
            "risk_note": "需要保持非写实卡通风格。",
        }

    def _split_text(self, text: str, count: int) -> list[str]:
        text = re.sub(r"\s+", "", text) or "用分数描述生活中的部分与整体。"
        size = max(1, len(text) // count)
        parts = [text[i * size : (i + 1) * size] for i in range(count - 1)]
        parts.append(text[(count - 1) * size :])
        return [part or text for part in parts]
