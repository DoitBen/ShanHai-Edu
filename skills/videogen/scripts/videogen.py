#!/usr/bin/env python3
"""MiniMax/Hailuo and OTU/NewAPI video helper for ShanHaiEdu."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


OTU_NEWAPI_MODELS = [
    {
        "model": "sora-2-12s",
        "family": "sora",
        "kind": ["text_to_video", "image_to_video"],
        "endpoint": "/v1/videos",
        "duration": "12s",
        "size_required": True,
        "image_limit": 1,
        "notes": "Sora 2; landscape/portrait is controlled by size; image mode uses the first image.",
    },
    {
        "model": "omni_flash-10s",
        "family": "omni",
        "kind": ["text_to_video", "image_to_video", "video_edit"],
        "endpoint": "/v1/videos",
        "duration": "10s",
        "resolution": "720p",
        "size_required": False,
        "image_limit": 7,
        "notes": "Supports reference-image mode and video edit; current docs say no first/last-frame mode.",
    },
    {
        "model": "veo_3_1-fast",
        "family": "veo",
        "kind": ["text_to_video", "reference_image_to_video"],
        "endpoint": "/v1/videos",
        "image_limit": 3,
        "notes": "Veo fast text/reference-image mode.",
    },
    {
        "model": "veo_3_1-fast-fl",
        "family": "veo",
        "kind": ["first_last_frame_to_video"],
        "endpoint": "/v1/videos",
        "image_limit": 2,
        "notes": "Veo fast first/last-frame mode; image order is first frame, then last frame.",
    },
    {
        "model": "veo_3_1-fast-extend",
        "family": "veo",
        "kind": ["video_extend"],
        "endpoint": "/v1/videos",
        "required": ["model", "prompt", "remix_id"],
        "notes": "Extends a previous Veo video to 15s; remix_id is a video_xxx id, not task_id.",
    },
    {
        "model": "gpt-image-2",
        "family": "gpt-image",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "aspect_ratios": ["1:1", "5:4", "9:16", "21:9", "16:9", "3:2", "4:3", "4:5", "3:4", "2:3"],
        "notes": "Async image model routed through /v1/videos.",
    },
    {
        "model": "gpt-image-2-2K",
        "family": "gpt-image",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "notes": "2K async image model routed through /v1/videos.",
    },
    {
        "model": "gpt-image-2-4K",
        "family": "gpt-image",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "notes": "4K async image model routed through /v1/videos.",
    },
    {
        "model": "nano_banana_2",
        "family": "nano-banana",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "aspect_ratios": ["1:1", "9:16", "16:9", "auto"],
        "notes": "Async Nano Banana image model routed through /v1/videos.",
    },
    {
        "model": "nano_banana_pro-1K",
        "family": "nano-banana",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "aspect_ratios": ["1:1", "9:16", "16:9", "auto"],
        "notes": "1K Pro async Nano Banana image model routed through /v1/videos.",
    },
    {
        "model": "nano_banana_pro-2K",
        "family": "nano-banana",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "aspect_ratios": ["1:1", "9:16", "16:9", "auto"],
        "notes": "2K Pro async Nano Banana image model routed through /v1/videos.",
    },
    {
        "model": "nano_banana_pro-4K",
        "family": "nano-banana",
        "kind": ["async_text_to_image", "async_image_to_image"],
        "endpoint": "/v1/videos",
        "image_limit": 5,
        "aspect_ratios": ["1:1", "9:16", "16:9", "auto"],
        "notes": "4K Pro async Nano Banana image model routed through /v1/videos.",
    },
]

OTU_OTHER_IMAGE_MODELS = [
    {
        "model": "gemini-3-pro-image-preview",
        "family": "gemini-native-image",
        "kind": ["sync_text_to_image", "sync_image_to_image"],
        "endpoint": "/v1beta/models/{model}:generateContent",
        "aspect_ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "notes": "Gemini native generateContent image endpoint; model id is part of the path.",
    },
    {
        "model": "gemini-3.1-flash-image-preview",
        "family": "gemini-native-image",
        "kind": ["sync_text_to_image", "sync_image_to_image"],
        "endpoint": "/v1beta/models/{model}:generateContent",
        "aspect_ratios": [
            "1:1",
            "2:3",
            "3:2",
            "3:4",
            "4:3",
            "4:5",
            "5:4",
            "9:16",
            "16:9",
            "21:9",
            "1:4",
            "4:1",
            "1:8",
            "8:1",
        ],
        "image_sizes": ["1K", "2K", "4K"],
        "notes": "Gemini native generateContent image endpoint; supports extra aspect ratios and imageSize.",
    },
    {
        "model": "image2",
        "family": "openai-image",
        "kind": ["text_to_image", "image_edit"],
        "endpoint": "/v1/images/generations and /v1/images/edits",
        "notes": "OpenAI-compatible image generation/edit endpoint; supports JSON and multipart.",
    },
]

OTU_DEPRECATED_MODELS = [
    "sora-2-landscape-10s",
    "sora-2-portrait-10s",
    "sora-2-landscape-15s",
    "sora-2-portrait-15s",
    "sora-2-pro-landscape-25s",
    "sora-2-pro-portrait-25s",
    "sora-2-pro-landscape-hd-15s",
    "sora-2-pro-portrait-hd-15s",
    "veo_3_1-fast-remix",
    "veo_3_1-fast-fl-remix",
    "veo_3_1-fast-hd-remix",
    "veo_3_1-fast-fl-hd-remix",
    "veo_3_1-hd-remix",
    "veo_3_1-hd-fl-remix",
    "veo_3_1-remix",
    "veo_3_1-fl-remix",
]

OTU_PREFERRED_VIDEO_MODELS = ["omni_flash-10s", "sora-2-12s"]

INTERFACES = [
    {
        "name": "text_to_video",
        "method": "POST",
        "path": "/v1/video_generation",
        "required": ["model", "prompt"],
        "models": ["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-02", "T2V-01-Director", "T2V-01"],
    },
    {
        "name": "image_to_video",
        "method": "POST",
        "path": "/v1/video_generation",
        "required": ["model", "first_frame_image"],
        "models": [
            "MiniMax-Hailuo-2.3",
            "MiniMax-Hailuo-2.3-Fast",
            "MiniMax-Hailuo-02",
            "I2V-01-Director",
            "I2V-01-live",
            "I2V-01",
        ],
    },
    {
        "name": "start_end_to_video",
        "method": "POST",
        "path": "/v1/video_generation",
        "required": ["model", "last_frame_image"],
        "models": ["MiniMax-Hailuo-02"],
    },
    {
        "name": "subject_reference_to_video",
        "method": "POST",
        "path": "/v1/video_generation",
        "required": ["model", "subject_reference"],
        "models": ["S2V-01"],
    },
    {
        "name": "query_video_generation_task",
        "method": "GET",
        "path": "/v1/query/video_generation",
        "required": ["task_id"],
        "models": [],
    },
    {
        "name": "download_video_file",
        "method": "GET",
        "path": "/v1/files/retrieve",
        "required": ["file_id"],
        "models": [],
    },
    {
        "name": "otu_newapi_create_task",
        "method": "POST",
        "path": "/v1/videos",
        "required": ["model", "prompt"],
        "models": [item["model"] for item in OTU_NEWAPI_MODELS],
    },
    {
        "name": "otu_newapi_query_task",
        "method": "GET",
        "path": "/v1/videos/{task_id}",
        "required": ["task_id"],
        "models": [],
    },
]

DEFAULTS = {
    "MINIMAX_BASE_URL": "https://api.minimax.io",
    "MINIMAX_DEFAULT_MODEL": "MiniMax-Hailuo-2.3",
    "MINIMAX_DEFAULT_RESOLUTION": "768P",
    "MINIMAX_DEFAULT_DURATION": "6",
    "MINIMAX_PROMPT_OPTIMIZER": "false",
    "OMNI_DEFAULT_MODEL": "omni_flash-10s",
    "OMNI_DEFAULT_SIZE": "1280x720",
    "NEWAPI_DEFAULT_MODEL": "omni_flash-10s",
    "NEWAPI_DEFAULT_SIZE": "1280x720",
}

SECRET_KEYS = {
    "MINIMAX_API_KEY",
    "MINMAX_API_KEY",
    "NEWAPI_API_KEY",
    "MINIMAX_TOKEN",
    "NEWAPI_TOKEN",
    "OTU_API_KEY",
    "OTU_TOKEN",
    "OCTO_API_KEY",
}


def find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "skills").exists() and (parent / "scripts").exists():
            return parent
    for parent in [here, *here.parents]:
        if (parent / ".env.local").exists():
            return parent
    return Path.cwd()


def load_env(path: Path) -> dict[str, str]:
    return load_env_from_paths([path])


def load_env_from_paths(paths: list[Path]) -> dict[str, str]:
    values = DEFAULTS.copy()
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    if values.get("MINMAX_API_KEY") and not values.get("MINIMAX_API_KEY"):
        values["MINIMAX_API_KEY"] = values["MINMAX_API_KEY"]
    if values.get("OCTO_API_KEY"):
        values["NEWAPI_API_KEY"] = values["OCTO_API_KEY"]
        values["MINIMAX_API_KEY"] = values["OCTO_API_KEY"]
    if values.get("OCTO_BASE_URL"):
        values["NEWAPI_BASE_URL"] = values["OCTO_BASE_URL"]
        values["MINIMAX_BASE_URL"] = values["OCTO_BASE_URL"]
    if values.get("NEWAPI_API_KEY") and not values.get("MINIMAX_API_KEY"):
        values["MINIMAX_API_KEY"] = values["NEWAPI_API_KEY"]
    if values.get("NEWAPI_BASE_URL") and values.get("MINIMAX_BASE_URL") == DEFAULTS["MINIMAX_BASE_URL"]:
        values["MINIMAX_BASE_URL"] = values["NEWAPI_BASE_URL"]
    for key in set(values) | SECRET_KEYS:
        if os.environ.get(key):
            values[key] = os.environ[key]
    if values.get("MINMAX_API_KEY") and not values.get("MINIMAX_API_KEY"):
        values["MINIMAX_API_KEY"] = values["MINMAX_API_KEY"]
    if values.get("OCTO_API_KEY"):
        values["NEWAPI_API_KEY"] = values["OCTO_API_KEY"]
        values["MINIMAX_API_KEY"] = values["OCTO_API_KEY"]
    if values.get("OCTO_BASE_URL"):
        values["NEWAPI_BASE_URL"] = values["OCTO_BASE_URL"]
        values["MINIMAX_BASE_URL"] = values["OCTO_BASE_URL"]
    if values.get("NEWAPI_API_KEY") and not values.get("MINIMAX_API_KEY"):
        values["MINIMAX_API_KEY"] = values["NEWAPI_API_KEY"]
    if values.get("NEWAPI_BASE_URL") and values.get("MINIMAX_BASE_URL") == DEFAULTS["MINIMAX_BASE_URL"]:
        values["MINIMAX_BASE_URL"] = values["NEWAPI_BASE_URL"]
    return values


def bool_from_env(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def redact(text: str) -> str:
    for key in SECRET_KEYS:
        api_key = os.environ.get(key, "")
        if api_key:
            text = text.replace(api_key, "***")
    return text


def print_json(data: Any) -> None:
    print(json.dumps(sanitize_for_output(data), ensure_ascii=False, indent=2))


def sanitize_for_output(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: sanitize_for_output(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_for_output(value) for value in data]
    if isinstance(data, str) and data.startswith("data:image/"):
        prefix = data.split(",", 1)[0]
        return f"{prefix},<base64 omitted>"
    return data


def nested_get(data: Any, *keys: str) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def image_to_data_url(value: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    path = Path(value)
    if not path.exists():
        raise SystemExit(f"Image not found: {value}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif suffix == ".png":
            mime = "image/png"
        elif suffix == ".webp":
            mime = "image/webp"
        else:
            raise SystemExit(f"Unsupported image type: {path.suffix}")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def request_json(
    method: str,
    base_url: str,
    path: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    timeout: int = 300,
) -> Any:
    url = normalize_base_url(base_url) + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    payload = None
    headers = {"Authorization": f"Bearer {api_key}"}
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
            if "application/json" in content_type:
                return json.loads(data.decode("utf-8"))
            return data
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(redact(f"HTTP {exc.code}: {detail}")) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(redact(f"Network error: {exc.reason}")) from exc


def request_multipart(
    method: str,
    base_url: str,
    path: str,
    api_key: str,
    fields: dict[str, Any],
    references: list[str] | None = None,
    reference_field: str = "input_reference",
    timeout: int = 300,
) -> Any:
    url = normalize_base_url(base_url) + path
    boundary = f"----AIYoujiaoBoundary{int(time.time() * 1000)}"
    chunks: list[bytes] = []

    def add_text(name: str, value: Any) -> None:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    def add_file(name: str, file_path: Path) -> None:
        mime, _ = mimetypes.guess_type(file_path.name)
        mime = mime or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{name}"; filename="{file_path.name}"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(file_path.read_bytes())
        chunks.append(b"\r\n")

    for key, value in fields.items():
        if value is not None:
            add_text(key, value)
    for ref in references or []:
        path_ref = Path(ref)
        if not ref.startswith(("http://", "https://", "data:")) and path_ref.exists():
            add_file(reference_field, path_ref)
        else:
            add_text(reference_field, ref)
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request(url, data=b"".join(chunks), headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
            if "application/json" in content_type:
                return json.loads(data.decode("utf-8"))
            return data
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(redact(f"HTTP {exc.code}: {detail}")) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(redact(f"Network error: {exc.reason}")) from exc


def request_bytes(url: str, timeout: int = 300) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "video/mp4,video/*;q=0.9,image/*;q=0.8,application/octet-stream,*/*;q=0.5",
        "Referer": "https://otuapi.com/",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(redact(f"HTTP {exc.code}: {detail}")) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(redact(f"Network error: {exc.reason}")) from exc


def require_key(env: dict[str, str]) -> str:
    key = env.get("MINIMAX_API_KEY", "").strip()
    if not key:
        raise SystemExit("Video API key is missing. Configure OCTO_API_KEY in apps\\api\\.env or NEWAPI_API_KEY in .env.local.")
    return key


def extract_model_ids(data: Any) -> list[str]:
    if isinstance(data, dict):
        raw_models = data.get("data") or data.get("models") or []
    elif isinstance(data, list):
        raw_models = data
    else:
        raw_models = []
    models: list[str] = []
    for item in raw_models:
        if isinstance(item, str):
            models.append(item)
        elif isinstance(item, dict):
            model_id = item.get("id") or item.get("model") or item.get("name")
            if isinstance(model_id, str):
                models.append(model_id)
    return models


def otu_model_matrix() -> dict[str, Any]:
    video_families = {"sora", "omni", "veo"}
    return {
        "video_models": [item for item in OTU_NEWAPI_MODELS if item["family"] in video_families],
        "async_image_models": [item for item in OTU_NEWAPI_MODELS if item["family"] not in video_families],
        "other_image_models": OTU_OTHER_IMAGE_MODELS,
        "deprecated_models": OTU_DEPRECATED_MODELS,
    }


def live_models(env: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    data = request_json("GET", env["MINIMAX_BASE_URL"], "/v1/models", require_key(env), timeout=timeout)
    models = extract_model_ids(data)
    video_like = [
        model
        for model in models
        if any(token in model.lower() for token in ("video", "hailuo", "minimax", "i2v", "t2v", "s2v", "wan", "omni", "sora", "veo"))
    ]
    return {
        "base_url": env["MINIMAX_BASE_URL"],
        "count": len(models),
        "models": models,
        "video_like_models": video_like,
        "otu_doc_models": otu_model_matrix(),
        "raw": data,
    }


def encode_reference(value: str, image_mode: str = "data-uri") -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    if image_mode == "path":
        return value
    return image_to_data_url(value)


def newapi_model_family(model: str) -> str:
    for item in OTU_NEWAPI_MODELS:
        if item["model"] == model:
            return item["family"]
    if model.startswith("gpt-image-2"):
        return "gpt-image"
    if model.startswith("veo_"):
        return "veo"
    if model.startswith("sora-"):
        return "sora"
    if model.startswith("omni_"):
        return "omni"
    return ""


def newapi_allows_default_size(model: str) -> bool:
    if model == "veo_3_1-fast-extend":
        return False
    if newapi_model_family(model) in {"gpt-image", "nano-banana"}:
        return False
    return True


def newapi_body(args: argparse.Namespace, env: dict[str, str], include_images: bool = True) -> dict[str, Any]:
    model = args.model or env.get("NEWAPI_DEFAULT_MODEL") or env["OMNI_DEFAULT_MODEL"]
    body: dict[str, Any] = {
        "model": model,
    }
    if getattr(args, "prompt", None):
        body["prompt"] = args.prompt
    if getattr(args, "prompt_extend", None):
        body["prompt_extend"] = args.prompt_extend
    if getattr(args, "remix_id", None):
        body["remix_id"] = args.remix_id
    size = getattr(args, "size", None)
    if size:
        body["size"] = size
    elif newapi_allows_default_size(model) and (env.get("NEWAPI_DEFAULT_SIZE") or env.get("OMNI_DEFAULT_SIZE")):
        body["size"] = env.get("NEWAPI_DEFAULT_SIZE") or env["OMNI_DEFAULT_SIZE"]
    if getattr(args, "aspect_ratio", None):
        body["aspect_ratio"] = args.aspect_ratio
    images = getattr(args, "images", None)
    if images:
        image_mode = getattr(args, "image_mode", "data-uri")
        if include_images:
            body["images"] = [encode_reference(image, image_mode=image_mode) for image in images]
    return body


def newapi_form_fields(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    return newapi_body(args, env, include_images=False)


def omni_body(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    return newapi_body(args, env)


def submit_newapi(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    if not getattr(args, "prompt", None):
        raise SystemExit("NewAPI video generation requires --prompt.")
    model = args.model or env.get("NEWAPI_DEFAULT_MODEL") or env["OMNI_DEFAULT_MODEL"]
    if model not in OTU_PREFERRED_VIDEO_MODELS and not getattr(args, "allow_other_model", False):
        preferred = ", ".join(OTU_PREFERRED_VIDEO_MODELS)
        raise SystemExit(
            f"Model {model} is not a default-approved video model. "
            f"Default-approved models: {preferred}. "
            "Use --allow-other-model only when the user explicitly requested this model."
        )
    use_multipart = bool(getattr(args, "multipart", False))
    body = newapi_form_fields(args, env) if use_multipart else newapi_body(args, env)
    if args.dry_run:
        result = {"dry_run": True, "request": body, "path": "/v1/videos", "content_type": "multipart/form-data" if use_multipart else "application/json"}
        if use_multipart:
            result["input_reference"] = getattr(args, "images", None) or []
            result["reference_field"] = getattr(args, "reference_field", "input_reference")
        return result
    if use_multipart:
        return request_multipart(
            "POST",
            env["MINIMAX_BASE_URL"],
            "/v1/videos",
            require_key(env),
            body,
            references=getattr(args, "images", None) or [],
            reference_field=getattr(args, "reference_field", "input_reference"),
            timeout=args.timeout,
        )
    return request_json("POST", env["MINIMAX_BASE_URL"], "/v1/videos", require_key(env), body=body, timeout=args.timeout)


def submit_omni(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    return submit_newapi(args, env)


def query_newapi(task_id: str, env: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    safe_task_id = urllib.parse.quote(task_id, safe="")
    return request_json("GET", env["MINIMAX_BASE_URL"], f"/v1/videos/{safe_task_id}", require_key(env), timeout=timeout)


def query_omni(task_id: str, env: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    return query_newapi(task_id, env, timeout)


def normalize_newapi_status(data: dict[str, Any]) -> str:
    raw = data.get("status") or nested_get(data, "data", "status")
    value = str(raw or "").strip().lower()
    mapping = {
        "success": "completed",
        "succeeded": "completed",
        "completed": "completed",
        "submitted": "queued",
        "queued": "queued",
        "in_progress": "processing",
        "processing": "processing",
        "running": "processing",
        "failure": "failed",
        "fail": "failed",
        "failed": "failed",
        "error": "failed",
    }
    return mapping.get(value, value)


def extract_newapi_download_url(data: dict[str, Any]) -> str:
    candidates = [
        data.get("video_url"),
        data.get("url"),
        data.get("result_url"),
        data.get("output"),
        nested_get(data, "data", "video_url"),
        nested_get(data, "data", "url"),
        nested_get(data, "data", "result_url"),
        nested_get(data, "data", "first_video_url"),
        nested_get(data, "result", "video_url"),
        nested_get(data, "result", "url"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith("http"):
            return candidate
    raise SystemExit(f"NewAPI video response has no download URL: {json.dumps(sanitize_for_output(data), ensure_ascii=False)[:500]}")


def extract_omni_download_url(data: dict[str, Any]) -> str:
    return extract_newapi_download_url(data)


def download_newapi_task(task_id: str, out_path: Path, env: dict[str, str], timeout: int) -> None:
    data = query_newapi(task_id, env, timeout)
    url = extract_newapi_download_url(data)
    content = request_bytes(url, timeout=timeout)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(content)
    print_json({"saved": str(out_path), "bytes": out_path.stat().st_size, "source_url": url})


def download_omni_video(task_id: str, out_path: Path, env: dict[str, str], timeout: int) -> None:
    data = query_omni(task_id, env, timeout)
    url = extract_omni_download_url(data)
    content = request_bytes(url, timeout=timeout)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(content)
    print_json({"saved": str(out_path), "bytes": out_path.stat().st_size, "source_url": url})


def video_body(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": args.model or env["MINIMAX_DEFAULT_MODEL"],
    }
    if getattr(args, "prompt", None):
        body["prompt"] = args.prompt
    if getattr(args, "duration", None):
        body["duration"] = args.duration
    if getattr(args, "resolution", None):
        body["resolution"] = args.resolution
    if getattr(args, "prompt_optimizer", None) is not None:
        body["prompt_optimizer"] = args.prompt_optimizer
    elif "MINIMAX_PROMPT_OPTIMIZER" in env:
        body["prompt_optimizer"] = bool_from_env(env["MINIMAX_PROMPT_OPTIMIZER"])
    if getattr(args, "fast_pretreatment", False):
        body["fast_pretreatment"] = True
    if getattr(args, "callback_url", None):
        body["callback_url"] = args.callback_url
    return body


def submit(args: argparse.Namespace, env: dict[str, str], mode: str) -> dict[str, Any]:
    if mode == "t2v" and not getattr(args, "prompt", None):
        raise SystemExit("t2v requires --prompt.")
    body = video_body(args, env)
    if mode == "i2v":
        body["first_frame_image"] = image_to_data_url(args.first_frame)
    elif mode == "fl2v":
        body["model"] = args.model or "MiniMax-Hailuo-02"
        if args.first_frame:
            body["first_frame_image"] = image_to_data_url(args.first_frame)
        body["last_frame_image"] = image_to_data_url(args.last_frame)
    elif mode == "s2v":
        body["model"] = args.model or "S2V-01"
        body["subject_reference"] = [
            {
                "type": args.subject_type,
                "image": [image_to_data_url(args.subject_image)],
            }
        ]
    if args.dry_run:
        return {"dry_run": True, "request": body}
    api_key = require_key(env)
    return request_json("POST", env["MINIMAX_BASE_URL"], "/v1/video_generation", api_key, body=body, timeout=args.timeout)


def poll_task(task_id: str, env: dict[str, str], timeout: int, interval: int) -> dict[str, Any]:
    api_key = require_key(env)
    deadline = time.time() + timeout
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = request_json(
            "GET",
            env["MINIMAX_BASE_URL"],
            "/v1/query/video_generation",
            api_key,
            query={"task_id": task_id},
            timeout=min(60, timeout),
        )
        status = str(last.get("status", "")).lower()
        if status in {"success", "fail", "failed"}:
            return last
        time.sleep(interval)
    raise SystemExit(f"Timed out waiting for task: {task_id}")


def download_file(file_id: str, out_path: Path, env: dict[str, str], timeout: int) -> None:
    api_key = require_key(env)
    data = request_json(
        "GET",
        env["MINIMAX_BASE_URL"],
        "/v1/files/retrieve",
        api_key,
        query={"file_id": file_id},
        timeout=timeout,
    )
    if not isinstance(data, dict):
        content = data
    else:
        url = extract_download_url(data)
        content = request_bytes(url, timeout=timeout)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(content)
    print_json({"saved": str(out_path), "bytes": out_path.stat().st_size})


def extract_download_url(data: dict[str, Any]) -> str:
    candidates = [
        data.get("download_url"),
        data.get("url"),
        (data.get("file") or {}).get("download_url"),
        (data.get("file") or {}).get("url"),
        (data.get("data") or {}).get("download_url"),
        (data.get("data") or {}).get("url"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith("http"):
            return candidate
    raise SystemExit(f"MiniMax file response has no download URL: {json.dumps(sanitize_for_output(data), ensure_ascii=False)[:500]}")


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_for_output(data), ensure_ascii=False, indent=2), encoding="utf-8")


def add_common_video_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model")
    parser.add_argument("--prompt")
    parser.add_argument("--duration", type=int, default=int(DEFAULTS["MINIMAX_DEFAULT_DURATION"]))
    parser.add_argument("--resolution", default=DEFAULTS["MINIMAX_DEFAULT_RESOLUTION"])
    parser.add_argument("--prompt-optimizer", dest="prompt_optimizer", action="store_true")
    parser.add_argument("--no-prompt-optimizer", dest="prompt_optimizer", action="store_false")
    parser.set_defaults(prompt_optimizer=None)
    parser.add_argument("--fast-pretreatment", action="store_true")
    parser.add_argument("--callback-url")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest")


def add_omni_video_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--size")
    parser.add_argument("--prompt-extend", dest="prompt_extend")
    parser.add_argument("--remix-id", dest="remix_id")
    parser.add_argument("--aspect-ratio", dest="aspect_ratio")
    parser.add_argument(
        "--image-mode",
        choices=["data-uri", "url", "path"],
        default="data-uri",
        help="How to pass local --image values in JSON requests. Default encodes local files as data URI.",
    )
    parser.add_argument("--multipart", action="store_true", help="Submit as multipart/form-data with repeated input_reference fields.")
    parser.add_argument("--reference-field", default="input_reference", help="Multipart reference field name. Use input_reference for current active docs.")
    parser.add_argument("--image", dest="images", action="append", help="Optional image URL or local image path. Repeat for multiple images.")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-other-model",
        action="store_true",
        help="Allow a non-default OTU/NewAPI model only when the user explicitly requested it.",
    )
    parser.add_argument("--manifest")


def main() -> int:
    root = find_project_root()
    env = load_env_from_paths([root / ".env.local", root / ".env", root / "apps" / "api" / ".env"])

    parser = argparse.ArgumentParser(description="MiniMax/Hailuo video generation helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("interfaces", help="List supported API interfaces")
    p.set_defaults(func=lambda a: print_json({"count": len(INTERFACES), "interfaces": INTERFACES}))

    p = sub.add_parser("models", help="List known video models, or query /v1/models with --live")
    p.add_argument("--live", action="store_true")
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(func=lambda a: print_json(live_models(env, a.timeout) if a.live else {"interfaces": INTERFACES}))

    p = sub.add_parser("ping", help="Check API key and model-list connectivity without generating video")
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(func=lambda a: print_json({"ok": True, "models": live_models(env, a.timeout)}))

    p = sub.add_parser("otu-models", help="List OTU/NewAPI models documented in the bundled Apifox-derived matrix")
    p.set_defaults(func=lambda a: print_json({"preferred_video_models": OTU_PREFERRED_VIDEO_MODELS, **otu_model_matrix()}))

    p = sub.add_parser("newapi-create", help="Submit OTU/NewAPI-compatible async task via POST /v1/videos")
    add_omni_video_args(p)
    p.set_defaults(func=lambda a: handle_newapi_submit(a, env, "newapi_video"))

    p = sub.add_parser("newapi-query", help="Query OTU/NewAPI-compatible task via GET /v1/videos/{task_id}")
    p.add_argument("--task-id", required=True)
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(func=lambda a: print_json(query_newapi(a.task_id, env, a.timeout)))

    p = sub.add_parser("newapi-download", help="Download completed OTU/NewAPI task URL to a local file")
    p.add_argument("--task-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=lambda a: download_newapi_task(a.task_id, Path(a.out), env, a.timeout))

    p = sub.add_parser("omni-t2v", help="Submit NewAPI/Omni-compatible text-to-video task via POST /v1/videos")
    add_omni_video_args(p)
    p.set_defaults(func=lambda a: handle_newapi_submit(a, env, "omni_video"))

    p = sub.add_parser("omni-i2v", help="Submit NewAPI/Omni-compatible image-to-video task via POST /v1/videos")
    add_omni_video_args(p)
    p.set_defaults(func=lambda a: handle_newapi_submit(a, env, "omni_video"))

    p = sub.add_parser("omni-query", help="Query NewAPI/Omni-compatible video task via GET /v1/videos/{task_id}")
    p.add_argument("--task-id", required=True)
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(func=lambda a: print_json(query_omni(a.task_id, env, a.timeout)))

    p = sub.add_parser("omni-download", help="Download completed NewAPI/Omni video task")
    p.add_argument("--task-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=lambda a: download_omni_video(a.task_id, Path(a.out), env, a.timeout))

    p = sub.add_parser("t2v", help="Submit text-to-video task")
    add_common_video_args(p)
    p.add_argument("--out")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=5)
    p.set_defaults(func=lambda a: handle_submit(a, env, "t2v"))

    p = sub.add_parser("i2v", help="Submit image-to-video task")
    add_common_video_args(p)
    p.add_argument("--first-frame", required=True)
    p.add_argument("--out")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=5)
    p.set_defaults(func=lambda a: handle_submit(a, env, "i2v"))

    p = sub.add_parser("fl2v", help="Submit first/last-frame video task")
    add_common_video_args(p)
    p.add_argument("--first-frame")
    p.add_argument("--last-frame", required=True)
    p.add_argument("--out")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=5)
    p.set_defaults(func=lambda a: handle_submit(a, env, "fl2v"))

    p = sub.add_parser("s2v", help="Submit subject-reference video task")
    add_common_video_args(p)
    p.add_argument("--subject-image", required=True)
    p.add_argument("--subject-type", default="character")
    p.add_argument("--out")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=5)
    p.set_defaults(func=lambda a: handle_submit(a, env, "s2v"))

    p = sub.add_parser("query", help="Query task status")
    p.add_argument("--task-id", required=True)
    p.add_argument("--timeout", type=int, default=60)
    p.set_defaults(func=lambda a: print_json(request_json("GET", env["MINIMAX_BASE_URL"], "/v1/query/video_generation", require_key(env), query={"task_id": a.task_id}, timeout=a.timeout)))

    p = sub.add_parser("download", help="Download video by file ID")
    p.add_argument("--file-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=lambda a: download_file(a.file_id, Path(a.out), env, a.timeout))

    args = parser.parse_args()
    args.func(args)
    return 0


def handle_submit(args: argparse.Namespace, env: dict[str, str], mode: str) -> None:
    result = submit(args, env, mode)
    record = {
        "mode": mode,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "result": result,
    }
    if args.wait and result.get("task_id"):
        status = poll_task(result["task_id"], env, args.timeout, args.poll_interval)
        record["status"] = status
        if args.out and status.get("file_id"):
            download_file(status["file_id"], Path(args.out), env, args.timeout)
            record["downloaded_to"] = args.out
    if args.manifest:
        write_manifest(Path(args.manifest), record)
    print_json(result)


def handle_newapi_submit(args: argparse.Namespace, env: dict[str, str], mode: str) -> None:
    result = submit_newapi(args, env)
    record = {
        "mode": mode,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "result": result,
    }
    if args.manifest:
        write_manifest(Path(args.manifest), record)
    print_json(result)


def handle_omni_submit(args: argparse.Namespace, env: dict[str, str]) -> None:
    handle_newapi_submit(args, env, "omni_video")


if __name__ == "__main__":
    raise SystemExit(main())
