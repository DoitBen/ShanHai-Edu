from __future__ import annotations

import argparse
import json
import re
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


def mask_text(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"',}]+", r"\1<redacted>", value)
    value = re.sub(r"(?i)((?:api[_-]?key|token|secret|key)\s*[\"']?\s*[:=]\s*[\"']?)[^\"',}\s]+", r"\1<redacted>", value)
    value = re.sub(r"\b(?:sk|octo|deepseek)-[A-Za-z0-9._-]{8,}\b", "<redacted>", value)
    return value


class EvidenceClient:
    def __init__(self, api_base: str, evidence: dict[str, Any]):
        self.api_base = api_base.rstrip("/")
        self.evidence = evidence
        self.client = httpx.Client(timeout=180)

    def close(self) -> None:
        self.client.close()

    def request_json(self, method: str, path: str, json_body: Any | None = None) -> dict[str, Any]:
        response = self.client.request(method, f"{self.api_base}{path}", json=json_body)
        text = response.text
        self._record(method, path, response.status_code, mask_text(text)[:900])
        response.raise_for_status()
        return response.json()

    def upload_file(self, path: str, file_path: Path) -> dict[str, Any]:
        with file_path.open("rb") as stream:
            response = self.client.post(
                f"{self.api_base}{path}",
                files={"file": (file_path.name, stream, "application/pdf")},
            )
        self._record("POST", path, response.status_code, mask_text(response.text)[:900])
        response.raise_for_status()
        return response.json()

    def download_file(self, path: str, out_file: Path) -> dict[str, Any]:
        response = self.client.get(f"{self.api_base}{path}")
        self._record("GET", path, response.status_code, f"<binary:{len(response.content)}>")
        response.raise_for_status()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(response.content)
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(response.content),
        }

    def ok_data(self, response: dict[str, Any], label: str) -> Any:
        if response.get("ok") is not True:
            raise RuntimeError(f"{label} returned non-ok response: {mask_text(json.dumps(response, ensure_ascii=False))}")
        return response["data"]

    def _record(self, method: str, path: str, status: int, excerpt: str) -> None:
        self.evidence["calls"].append(
            {
                "method": method,
                "path": path,
                "http_status": status,
                "body_excerpt": excerpt,
            }
        )


def generate_and_approve(client: EvidenceClient, project_id: str, node_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    generated = client.ok_data(
        client.request_json("POST", f"/projects/{project_id}/nodes/{node_id}/generate", body or {}),
        f"{node_id} generate",
    )
    node = client.ok_data(client.request_json("GET", f"/projects/{project_id}/nodes/{node_id}"), f"{node_id} get")
    approved = client.ok_data(
        client.request_json("POST", f"/projects/{project_id}/nodes/{node_id}/approve", {}),
        f"{node_id} approve",
    )
    return {"generated": generated, "node": node, "approved": approved}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    evidence_dir = (repo_root / args.evidence_root / timestamp).resolve()
    fixture_path = Path(args.fixture_path)
    if not fixture_path.is_absolute():
        fixture_path = repo_root / fixture_path
    evidence: dict[str, Any] = {
        "ok": False,
        "api_base_url": args.api_base_url,
        "evidence_dir": str(evidence_dir),
        "project_id": None,
        "generated_image_paths": [],
        "image_task_ids": [],
        "video_task_ids": [],
        "video_provider_task_ids": [],
        "clip_download_paths": [],
        "final_video_path": None,
        "ppt_path": None,
        "ppt_media_mp4_entries": [],
        "calls": [],
    }
    client = EvidenceClient(args.api_base_url, evidence)
    try:
        evidence["health"] = client.ok_data(client.request_json("GET", "/health"), "health")

        project = client.ok_data(
            client.request_json(
                "POST",
                "/projects",
                {
                    "name": args.project_name,
                    "subject": "math",
                    "grade": "1",
                    "textbook_version": "renjiao",
                    "volume": "shang",
                    "lesson_type": "public",
                },
            ),
            "create project",
        )
        project_id = project["project_id"]
        evidence["project_id"] = project_id

        client.ok_data(client.upload_file(f"/projects/{project_id}/textbook", fixture_path), "upload textbook")

        textbook = generate_and_approve(client, project_id, "textbook_parse", {"knowledge_point_id": "kp_001"})
        lesson = generate_and_approve(client, project_id, "lesson_plan")

        intro_selection = client.ok_data(
            client.request_json("POST", f"/projects/{project_id}/nodes/intro_selection/generate", {}),
            "intro_selection generate",
        )
        selection_content = dict(intro_selection["content"])
        selection_content["selected_anchor"] = (
            f"{selection_content.get('selected_anchor', '')} 这个镜头最后要回到课堂中5以内数的认识任务。"
        ).strip()
        client.ok_data(
            client.request_json("POST", f"/projects/{project_id}/nodes/intro_selection/edit", {"content": selection_content}),
            "intro_selection edit",
        )
        approved_selection = client.ok_data(
            client.request_json("POST", f"/projects/{project_id}/nodes/intro_selection/approve", {}),
            "intro_selection approve",
        )

        script_node = generate_and_approve(client, project_id, "intro_video_script")
        screenplay = generate_and_approve(client, project_id, "intro_video_screenplay")
        assets = generate_and_approve(client, project_id, "intro_video_asset", {"image_size": "1024x1024"})
        storyboard = generate_and_approve(client, project_id, "storyboard")

        tasks_after_images = client.ok_data(client.request_json("GET", f"/projects/{project_id}/tasks"), "tasks after images")
        image_tasks = [task for task in tasks_after_images if task.get("task_type") == "image_generation"]
        for task in image_tasks:
            evidence["image_task_ids"].append(task.get("task_id"))
            image_path = task.get("image_path")
            if image_path:
                evidence["generated_image_paths"].append(image_path)
                filename = Path(image_path).name
                client.download_file(f"/projects/{project_id}/images/{filename}", evidence_dir / filename)

        video = client.ok_data(
            client.request_json(
                "POST",
                f"/projects/{project_id}/nodes/final_video/generate",
                {"model": "omni_flash-10s", "size": "1280x720", "mode": "reference", "full_run": True},
            ),
            "final_video generate",
        )
        video_tasks = list(video.get("tasks", []))
        for task in video_tasks:
            evidence["video_task_ids"].append(task.get("task_id"))
            if task.get("provider_task_id"):
                evidence["video_provider_task_ids"].append(task.get("provider_task_id"))

        latest_tasks = []
        for _ in range(args.max_polls):
            time.sleep(args.poll_seconds)
            latest_tasks = [
                client.ok_data(client.request_json("GET", f"/projects/{project_id}/tasks/{task['task_id']}"), "task query")
                for task in video_tasks
            ]
            if latest_tasks and all(task.get("status") in {"completed", "failed"} for task in latest_tasks):
                break
        write_json(evidence_dir / "video-tasks-final.json", latest_tasks)

        completed_downloaded = [
            task
            for task in latest_tasks
            if task.get("status") == "completed" and task.get("download_status") == "downloaded"
        ]
        if not completed_downloaded:
            raise RuntimeError(f"No completed downloaded real video clip. Last task states: {mask_text(json.dumps(latest_tasks, ensure_ascii=False))}")

        for task in completed_downloaded:
            download_path = task.get("download_path")
            if not download_path:
                continue
            clip_out = evidence_dir / Path(download_path).name
            download = client.download_file(f"/projects/{project_id}/{download_path}", clip_out)
            evidence["clip_download_paths"].append(
                {
                    "api_path": download_path,
                    "local_path": str(clip_out),
                    **download,
                }
            )

        final_out = evidence_dir / "final_video.mp4"
        final_download = client.download_file(f"/projects/{project_id}/outputs/final_video.mp4", final_out)
        evidence["final_video_path"] = {"api_path": "outputs/final_video.mp4", "local_path": str(final_out), **final_download}

        export = client.ok_data(client.request_json("POST", f"/projects/{project_id}/export/ppt", {}), "export ppt")
        ppt_out = evidence_dir / export["filename"]
        ppt_download = client.download_file(export["download_url"], ppt_out)
        evidence["ppt_path"] = {
            "api_path": export["path"],
            "download_url": export["download_url"],
            "local_path": str(ppt_out),
            "video_path": export["video_path"],
            **ppt_download,
        }
        with zipfile.ZipFile(ppt_out) as archive:
            evidence["ppt_media_mp4_entries"] = [
                name for name in archive.namelist() if name.startswith("ppt/media/") and name.endswith(".mp4")
            ]
        if not evidence["ppt_media_mp4_entries"]:
            raise RuntimeError("PPT does not contain ppt/media/*.mp4")

        evidence["manifest"] = client.ok_data(client.request_json("GET", f"/projects/{project_id}/manifest"), "manifest")
        evidence["node_summaries"] = {
            "textbook_parse": textbook["approved"],
            "lesson_plan": lesson["approved"],
            "intro_selection": approved_selection,
            "intro_video_script": script_node["approved"],
            "intro_video_screenplay": screenplay["approved"],
            "intro_video_asset": assets["approved"],
            "storyboard": storyboard["approved"],
            "final_video": client.ok_data(client.request_json("GET", f"/projects/{project_id}/nodes/final_video"), "final_video get"),
        }
        evidence["ok"] = True
        return evidence
    except Exception as exc:
        evidence["ok"] = False
        evidence["failure"] = mask_text(str(exc))
        return evidence
    finally:
        client.close()
        write_json(evidence_dir / "summary.json", evidence)
        print(f"[t063] summary={evidence_dir / 'summary.json'}")
        if not evidence.get("ok"):
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8163")
    parser.add_argument("--project-name", default=f"T063 real image video e2e {datetime.now():%Y%m%d-%H%M%S}")
    parser.add_argument("--fixture-path", default=r"fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf")
    parser.add_argument("--evidence-root", default=r"docs\qa-audits\t063-real-image-video-evidence")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--max-polls", type=int, default=40)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
