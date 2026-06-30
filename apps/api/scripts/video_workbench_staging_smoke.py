from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient
from PIL import Image

API_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.main import create_app

REPORT_KIND = "video-workbench-staging-smoke"
OMNI_TEXT_TO_VIDEO = "OMNI_TEXT_TO_VIDEO"
OMNI_REFERENCE_TO_VIDEO = "OMNI_REFERENCE_TO_VIDEO"
MIN_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08free"
SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "token",
    "secret",
    "provider_task_id",
    "video_url",
    "download_url",
    "url",
    "path",
    "project_dir",
}


class SmokeError(RuntimeError):
    pass


class RecordingSmokeVideoProvider:
    def __init__(self) -> None:
        self.submitted: list[dict[str, Any]] = []
        self.query_count: dict[str, int] = {}
        self.download_count = 0

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append(payload)
        provider_task_id = f"remote_smoke_{len(self.submitted)}"
        self.query_count[provider_task_id] = 0
        return {"provider_task_id": provider_task_id, "status": "queued", "progress": 0}

    def query_task(self, provider_task_id: str) -> dict[str, Any]:
        self.query_count[provider_task_id] = self.query_count.get(provider_task_id, 0) + 1
        if self.query_count[provider_task_id] < 2:
            return {"provider_task_id": provider_task_id, "status": "processing", "progress": 60}
        return {
            "provider_task_id": provider_task_id,
            "status": "completed",
            "progress": 100,
            "video_url": "https://provider.example.invalid/signed/smoke.mp4",
        }

    def download_video(self, _video_url: str, target_path: Path) -> None:
        self.download_count += 1
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(MIN_MP4_BYTES)


@dataclass
class SmokeHttpClient:
    base_url: str | None
    token: str | None
    test_client: TestClient | None = None
    timeout: float = 30

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    ) -> tuple[int, dict[str, Any], bytes, dict[str, str], str]:
        if self.test_client is not None:
            response = self.test_client.request(method, path, json=json_body, files=files)
            return (
                response.status_code,
                self._json_or_empty(response.text),
                response.content,
                dict(response.headers),
                f"in-process:{path}",
            )
        assert self.base_url is not None
        target = f"{self.base_url.rstrip('/')}{path}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
            response = client.request(method, target, json=json_body, files=files, headers=headers)
        return (
            response.status_code,
            self._json_or_empty(response.text),
            response.content,
            dict(response.headers),
            target,
        )

    @staticmethod
    def _json_or_empty(text: str) -> dict[str, Any]:
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"_non_json": text[:200]}
        return data if isinstance(data, dict) else {"value": data}


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if any(sensitive in normalized for sensitive in SENSITIVE_KEYS):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        text = re.sub(
            r"(?i)authorization:\s*bearer\s+[a-z0-9._-]+",
            "Authorization: " + "Bearer <redacted>",
            value,
        )
        text = re.sub(r"(?i)\bbearer\s+[a-z0-9._-]+", "Bearer <redacted>", text)
        text = re.sub(r"\b(?:sk|octo|deepseek)-[A-Za-z0-9._-]{8,}\b", "<redacted>", text)
        text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "<redacted>", text)
        return text
    return value


def unwrap_ok(step: str, response: tuple[int, dict[str, Any], bytes, dict[str, str], str]) -> dict[str, Any]:
    status, payload, _content, _headers, url = response
    if status >= 400 or payload.get("ok") is not True:
        raise SmokeError(f"{step} failed: status={status} payload={redact_sensitive(payload)} url={sanitize_url(url)}")
    return payload["data"]


def sanitize_url(url: str) -> str:
    return re.sub(r"(?i)([?&](?:token|signature|expires|key|api_key)=)[^&]+", r"\1<redacted>", url)


def make_png_bytes(color: tuple[int, int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 48), color).save(buffer, format="PNG")
    return buffer.getvalue()


def make_project(client: SmokeHttpClient, label: str) -> dict[str, Any]:
    return unwrap_ok(
        "create_project",
        client.request(
            "POST",
            "/projects",
            json_body={
                "name": f"{label} {datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "subject": "math",
                "grade": "3",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "public",
            },
        ),
    )


def upload_references(client: SmokeHttpClient, project_id: str, count: int) -> list[dict[str, Any]]:
    palette = [(24, 110, 180), (240, 150, 40), (45, 160, 120)]
    files = [
        ("files", (f"reference-{index + 1}.png", make_png_bytes(palette[index % len(palette)]), "image/png"))
        for index in range(count)
    ]
    data = unwrap_ok(
        "upload_references",
        client.request("POST", f"/projects/{project_id}/video-workflow/assets", files=files),
    )
    uploaded = data.get("uploaded") or data.get("assets") or []
    if len(uploaded) < count:
        raise SmokeError(f"expected {count} uploaded references, got {len(uploaded)}")
    return uploaded[:count]


def create_run(
    client: SmokeHttpClient,
    project_id: str,
    *,
    prompt: str,
    reference_asset_ids: list[str],
) -> dict[str, Any]:
    return unwrap_ok(
        "create_run",
        client.request(
            "POST",
            f"/projects/{project_id}/video-workflow/runs",
            json_body={
                "client_request_id": str(uuid.uuid4()),
                "prompt": prompt,
                "model": "omni_flash-10s",
                "size": "1280x720",
                "duration_sec": 10,
                "reference_asset_ids": reference_asset_ids,
            },
        ),
    )


def sync_until_terminal(client: SmokeHttpClient, project_id: str, run_id: str, *, max_attempts: int) -> dict[str, Any]:
    current: dict[str, Any] = {}
    for _ in range(max_attempts):
        current = unwrap_ok(
            "sync_run",
            client.request("POST", f"/projects/{project_id}/video-workflow/runs/{run_id}/sync", json_body={}),
        )
        if current.get("status") in {"completed", "failed", "submission_unknown"}:
            return current
        time.sleep(1)
    raise SmokeError(f"run did not reach terminal state after {max_attempts} sync attempts: {redact_sensitive(current)}")


def fetch_binary(client: SmokeHttpClient, path: str, step: str) -> tuple[int, bytes, dict[str, str], str]:
    status, payload, content, headers, url = client.request("GET", path)
    if status >= 400:
        raise SmokeError(f"{step} failed: status={status} payload={redact_sensitive(payload)} url={sanitize_url(url)}")
    return status, content, headers, url


def assert_mp4(step: str, content: bytes, headers: dict[str, str]) -> dict[str, Any]:
    content_type = headers.get("content-type") or headers.get("Content-Type") or ""
    if "video/mp4" not in content_type:
        raise SmokeError(f"{step} content-type is not video/mp4: {content_type}")
    if len(content) == 0:
        raise SmokeError(f"{step} returned empty video")
    if b"ftyp" not in content[:32]:
        raise SmokeError(f"{step} returned invalid mp4 header")
    return {"byte_size": len(content), "content_type": content_type}


def verify_proxy_url(url: str, required_proxy: str, findings: list[dict[str, Any]]) -> None:
    if url.startswith("in-process:"):
        findings.append({"check": "proxy_path", "status": "skipped", "reason": "in_process_testclient"})
        return
    if required_proxy not in url:
        raise SmokeError(f"request did not use required proxy path {required_proxy}: {sanitize_url(url)}")
    findings.append({"check": "proxy_path", "status": "passed", "url": sanitize_url(url)})


def run_staging_flow(
    client: SmokeHttpClient,
    *,
    required_proxy: str,
    run_real_provider: bool,
    max_sync_attempts: int,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "kind": REPORT_KIND,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "real_provider" if run_real_provider else "fake_provider",
        "checks": [],
        "runs": [],
    }
    project = make_project(client, REPORT_KIND)
    project_id = str(project["project_id"])
    workflow_response = client.request("GET", f"/projects/{project_id}/video-workflow")
    workflow = unwrap_ok("fetch_video_workflow", workflow_response)
    verify_proxy_url(workflow_response[4], required_proxy, evidence["checks"])
    config = workflow.get("config") or {}
    evidence["checks"].append(
        {
            "check": "workflow_defaults",
            "status": "passed",
            "model": config.get("model"),
            "size": config.get("size"),
            "duration_sec": config.get("duration_sec"),
            "provider_ready": config.get("provider_ready"),
            "provider_reason_code": config.get("provider_reason_code"),
        }
    )
    if run_real_provider and config.get("provider_ready") is not True:
        raise SmokeError(f"real provider is not ready: {redact_sensitive(config)}")

    references = upload_references(client, project_id, 2)
    asset_ids = [str(item["asset_id"]) for item in references]
    delete_response = client.request(
        "DELETE",
        f"/projects/{project_id}/video-workflow/assets/{asset_ids[-1]}",
    )
    unwrap_ok("delete_reference", delete_response)
    verify_proxy_url(delete_response[4], required_proxy, evidence["checks"])
    references = upload_references(client, project_id, 1)
    asset_ids = [asset_ids[0], str(references[0]["asset_id"])]

    scenarios = [
        {
            "name": OMNI_TEXT_TO_VIDEO,
            "prompt": "卡通数学积木在课堂桌面上组合成小桥，固定镜头，温暖插画风格。",
            "reference_asset_ids": [],
        },
        {
            "name": OMNI_REFERENCE_TO_VIDEO,
            "prompt": "参考图中的颜色和构图延展为 10 秒课堂插画视频，镜头缓慢推进。",
            "reference_asset_ids": asset_ids,
        },
    ]
    for scenario in scenarios:
        run = create_run(
            client,
            project_id,
            prompt=str(scenario["prompt"]),
            reference_asset_ids=list(scenario["reference_asset_ids"]),
        )
        completed = sync_until_terminal(client, project_id, str(run["run_id"]), max_attempts=max_sync_attempts)
        if completed.get("status") != "completed" or completed.get("video_ready") is not True:
            raise SmokeError(f"{scenario['name']} did not complete: {redact_sensitive(completed)}")
        status, content, headers, content_url = fetch_binary(
            client,
            f"/projects/{project_id}/video-workflow/runs/{run['run_id']}/content",
            f"{scenario['name']}_content",
        )
        content_meta = assert_mp4(f"{scenario['name']}_content", content, headers)
        status, download, download_headers, download_url = fetch_binary(
            client,
            f"/projects/{project_id}/video-workflow/runs/{run['run_id']}/download",
            f"{scenario['name']}_download",
        )
        download_meta = assert_mp4(f"{scenario['name']}_download", download, download_headers)
        verify_proxy_url(content_url, required_proxy, evidence["checks"])
        verify_proxy_url(download_url, required_proxy, evidence["checks"])
        evidence["runs"].append(
            {
                "scenario": scenario["name"],
                "run_id": run["run_id"],
                "model": completed.get("model"),
                "size": completed.get("size"),
                "duration_sec": completed.get("duration_sec"),
                "status": completed.get("status"),
                "download_status": completed.get("download_status"),
                "progress": completed.get("progress"),
                "reference_count": len(scenario["reference_asset_ids"]),
                "content": content_meta,
                "download": download_meta,
            }
        )

    observability_response = client.request("GET", f"/projects/{project_id}/video-workflow/observability")
    observability = unwrap_ok("observability", observability_response)
    verify_proxy_url(observability_response[4], required_proxy, evidence["checks"])
    evidence["observability"] = {
        "metric_keys": sorted((observability.get("metrics") or {}).keys()),
        "event_count": len(observability.get("events") or []),
    }
    storage_response = client.request("GET", f"/projects/{project_id}/video-workflow/storage")
    storage = unwrap_ok("storage", storage_response)
    cleanup_response = client.request("POST", f"/projects/{project_id}/video-workflow/storage/cleanup", json_body={})
    cleanup = unwrap_ok("storage_cleanup", cleanup_response)
    verify_proxy_url(cleanup_response[4], required_proxy, evidence["checks"])
    evidence["storage"] = {
        "usage_keys": sorted((storage.get("usage") or {}).keys()),
        "cleanup_keys": sorted(cleanup.keys()),
    }
    evidence["completed_at"] = datetime.now(timezone.utc).isoformat()
    evidence["status"] = "passed"
    return redact_sensitive(evidence)


def local_test_client() -> SmokeHttpClient:
    provider = RecordingSmokeVideoProvider()
    temp_dir = tempfile.TemporaryDirectory(prefix="shanhai-video-workbench-staging-smoke-")
    app = create_app(
        {
            "storage_root": str(Path(temp_dir.name) / "storage"),
            "workflow_root": str(ROOT / "workflow"),
            "provider_mode": "fake",
            "video_provider_mode": "placeholder",
            "image_provider_mode": "placeholder",
            "tts_provider_mode": "placeholder",
        }
    )
    app.state.service.video_workflow.video_provider = provider
    app.state.service.video_workflow.provider_readiness = {"ok": True, "blocking_issues": []}
    client = TestClient(app)
    wrapped = SmokeHttpClient(base_url=None, token=None, test_client=client)
    setattr(wrapped, "_temp_dir", temp_dir)
    return wrapped


def write_reports(evidence: dict[str, Any], output_dir: Path, env_name: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    json_path = output_dir / f"{stamp}-{env_name}-{REPORT_KIND}.json"
    md_path = output_dir / f"{stamp}-{env_name}-{REPORT_KIND}.md"
    json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(evidence, env_name), encoding="utf-8")
    return json_path, md_path


def render_markdown_report(evidence: dict[str, Any], env_name: str) -> str:
    lines = [
        f"# 视频工作台 Staging Smoke 报告",
        "",
        f"- 环境：`{env_name}`",
        f"- 结果：`{evidence.get('status')}`",
        f"- 模式：`{evidence.get('mode')}`",
        f"- 开始：`{evidence.get('started_at')}`",
        f"- 结束：`{evidence.get('completed_at')}`",
        "",
        "## Runs",
        "",
        "| 场景 | run_id | 状态 | 参考图 | 文件大小 |",
        "|---|---|---|---:|---:|",
    ]
    for run in evidence.get("runs") or []:
        lines.append(
            f"| `{run.get('scenario')}` | `{run.get('run_id')}` | `{run.get('status')}` | "
            f"{run.get('reference_count')} | {run.get('download', {}).get('byte_size')} |"
        )
    lines.extend(
        [
            "",
            "## 脱敏说明",
            "",
            "- 不记录 token、鉴权头、provider task id、签名 URL 或本地绝对密钥路径。",
            "- 真实 provider 不可用时只记录阻塞原因，不伪造通过。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run video workbench staging smoke.")
    parser.add_argument("--base-url", help="Next proxy API base URL, for example https://staging.example.com/api/backend")
    parser.add_argument("--token", help="Backend API token for protected staging API. Do not put this in reports.")
    parser.add_argument("--env-name", default="local", help="Evidence environment label.")
    parser.add_argument("--output-dir", default=str(ROOT / "docs" / "qa-audits"), help="Evidence output directory.")
    parser.add_argument("--required-proxy", default="/api/backend", help="Required browser/API proxy path for HTTP mode.")
    parser.add_argument("--run-real-provider", action="store_true", help="Allow real provider paid smoke.")
    parser.add_argument("--max-sync-attempts", type=int, default=8, help="Maximum sync attempts per run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.base_url:
        client = SmokeHttpClient(base_url=args.base_url.rstrip("/"), token=args.token)
    else:
        client = local_test_client()
    try:
        evidence = run_staging_flow(
            client,
            required_proxy=args.required_proxy,
            run_real_provider=bool(args.run_real_provider),
            max_sync_attempts=args.max_sync_attempts,
        )
        json_path, md_path = write_reports(evidence, Path(args.output_dir), args.env_name)
        print(f"{REPORT_KIND} passed")
        print(f"json_report={json_path}")
        print(f"markdown_report={md_path}")
    except Exception as exc:
        failed = {
            "kind": REPORT_KIND,
            "status": "failed",
            "env": args.env_name,
            "mode": "real_provider" if args.run_real_provider else "fake_provider",
            "error": redact_sensitive(str(exc)),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        json_path, md_path = write_reports(failed, Path(args.output_dir), args.env_name)
        print(f"{REPORT_KIND} failed")
        print(f"json_report={json_path}")
        print(f"markdown_report={md_path}")
        raise


if __name__ == "__main__":
    main()
