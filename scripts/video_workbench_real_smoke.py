from __future__ import annotations

import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx


def unwrap(response: httpx.Response) -> Any:
    response.raise_for_status()
    payload = response.json()
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload.get("error") or payload, ensure_ascii=False))
    return payload["data"]


def main() -> int:
    base_url = os.environ["SHANHAI_API_BASE_URL"].rstrip("/")
    api_token = os.environ["BACKEND_API_TOKEN"]
    project_id = os.environ["VIDEO_SMOKE_PROJECT_ID"]
    image_paths = [Path(item) for item in os.environ["VIDEO_SMOKE_IMAGES"].split(os.pathsep)]
    prompt = os.getenv(
        "VIDEO_SMOKE_PROMPT",
        "卡通三角形积木逐渐组合成一座桥，固定镜头，温暖课堂插画风格。",
    )
    headers = {"Authorization": f"Bearer {api_token}"}
    files = [
        ("files", (path.name, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "image/png"))
        for path in image_paths
    ]
    uploaded = unwrap(httpx.post(
        f"{base_url}/projects/{project_id}/video-workflow/assets",
        headers=headers,
        files=files,
        timeout=60,
    ))
    run = unwrap(httpx.post(
        f"{base_url}/projects/{project_id}/video-workflow/runs",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "client_request_id": str(uuid.uuid4()),
            "prompt": prompt,
            "reference_asset_ids": [item["asset_id"] for item in uploaded["assets"][-len(files):]],
        },
        timeout=60,
    ))
    deadline = time.monotonic() + 20 * 60
    while time.monotonic() < deadline:
        run = unwrap(httpx.post(
            f"{base_url}/projects/{project_id}/video-workflow/runs/{run['run_id']}/sync",
            headers=headers,
            json={},
            timeout=180,
        ))
        print(json.dumps({
            "run_id": run["run_id"],
            "status": run["status"],
            "progress": run["progress"],
            "video_ready": run["video_ready"],
        }, ensure_ascii=False))
        if run["status"] in {"completed", "failed", "submission_unknown"}:
            return 0 if run["status"] == "completed" and run["video_ready"] else 1
        time.sleep(5)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
