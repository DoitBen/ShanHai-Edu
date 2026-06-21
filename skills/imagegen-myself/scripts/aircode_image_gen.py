#!/usr/bin/env python3
"""NewAPI/PinAI/AirCode image generator.

This script talks to the OpenAI-compatible image endpoint directly so image
generation stays predictable, and batch jobs can run in parallel by default.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlparse
import urllib.request


DEFAULT_BASE_URL = "https://img.baofu.eu.cc/v1"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1920x1080"
DEFAULT_QUALITY = "high"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_OUT = "output/imagegen/output.png"
MAX_BATCH_CONCURRENCY = 20
DOTENV_FILENAMES = (".env", ".env.local")


class Provider(NamedTuple):
    label: str
    base_url: str
    api_key: str | None


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def _load_dotenv_file(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for raw_line in text.splitlines():
        parsed = _parse_dotenv_line(raw_line)
        if not parsed:
            continue
        key, value = parsed
        os.environ[key] = value


def _load_local_env() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    start = Path.cwd().resolve()
    seen: set[Path] = set()
    for current in (start, *start.parents):
        if current in seen:
            continue
        seen.add(current)
        for filename in DOTENV_FILENAMES:
            _load_dotenv_file(current / filename)

    # This personal skill owns the imagegen-myself provider config. Load it last
    # so workspace-level generic .env files cannot steal this script's endpoint.
    for filename in DOTENV_FILENAMES:
        _load_dotenv_file(skill_dir / filename)


def _masked(value: str | None) -> str:
    if not value:
        return "missing"
    return "configured"


def _normalize_base_url(value: str) -> str:
    base_url = value.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    return base_url + "/v1"


def _providers() -> list[Provider]:
    primary = Provider(
        "primary",
        _normalize_base_url(
            os.environ.get("IMAGEGEN_MYSELF_PRIMARY_BASE_URL")
            or os.environ.get("IMAGEGEN_MYSELF_BASE_URL")
            or os.environ.get("NEWAPI_PRIMARY_BASE_URL")
            or os.environ.get("NEWAPI_BASE_URL")
            or os.environ.get("PINAI_PRIMARY_BASE_URL")
            or os.environ.get("PINAI_BASE_URL")
            or DEFAULT_BASE_URL
        ),
        os.environ.get("IMAGEGEN_MYSELF_PRIMARY_API_KEY")
        or os.environ.get("IMAGEGEN_MYSELF_API_KEY")
        or os.environ.get("NEWAPI_PRIMARY_API_KEY")
        or os.environ.get("NEWAPI_API_KEY")
        or os.environ.get("PINAI_PRIMARY_API_KEY")
        or os.environ.get("PINAI_API_KEY")
        or os.environ.get("AIRCODE_PRIMARY_API_KEY")
        or os.environ.get("AIRCODE_API_KEY")
        or os.environ.get("OPENAI_API_KEY"),
    )
    fallback = Provider(
        "fallback",
        _normalize_base_url(
            os.environ.get("IMAGEGEN_MYSELF_FALLBACK_BASE_URL")
            or os.environ.get("IMAGEGEN_MYSELF_BASE_URL")
            or os.environ.get("NEWAPI_FALLBACK_BASE_URL")
            or os.environ.get("NEWAPI_BASE_URL")
            or os.environ.get("PINAI_FALLBACK_BASE_URL")
            or os.environ.get("PINAI_BASE_URL")
            or DEFAULT_BASE_URL
        ),
        os.environ.get("IMAGEGEN_MYSELF_FALLBACK_API_KEY")
        or os.environ.get("IMAGEGEN_MYSELF_API_KEY")
        or os.environ.get("NEWAPI_FALLBACK_API_KEY")
        or os.environ.get("NEWAPI_API_KEY")
        or os.environ.get("PINAI_FALLBACK_API_KEY")
        or os.environ.get("PINAI_API_KEY")
        or os.environ.get("AIRCODE_FALLBACK_API_KEY")
        or os.environ.get("AIRCODE_API_KEY")
        or os.environ.get("OPENAI_API_KEY"),
    )
    providers: list[Provider] = []
    seen: set[tuple[str, str | None]] = set()
    for provider in (primary, fallback):
        key = (provider.base_url, provider.api_key)
        if key in seen:
            continue
        seen.add(key)
        providers.append(provider)
    return providers


def _require_key(provider: Provider, *, dry_run: bool = False) -> None:
    if provider.api_key:
        return
    if dry_run:
        return
    raise SystemExit("No API key is configured. Set NEWAPI_API_KEY, PINAI_API_KEY, AIRCODE_API_KEY, or OPENAI_API_KEY.")


def _provider_timeout(provider: Provider) -> float | None:
    specific = os.environ.get(f"AIRCODE_{provider.label.upper()}_TIMEOUT")
    value = specific or os.environ.get("AIRCODE_PROVIDER_TIMEOUT")
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid provider timeout: {value!r}") from exc


def _provider_client(provider: Provider):
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("The openai package is not installed in the active environment.") from exc
    return OpenAI(api_key=provider.api_key, base_url=provider.base_url)


def _write_b64_image(image_b64: str, out: str, *, force: bool) -> Path:
    out_path = Path(out)
    if out_path.exists() and not force:
        raise SystemExit(f"Output already exists: {out_path}. Use --force to overwrite.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(image_b64))
    return out_path


def _write_image_from_url(image_url: str, out: str, *, force: bool) -> Path:
    out_path = Path(out)
    if out_path.exists() and not force:
        raise SystemExit(f"Output already exists: {out_path}. Use --force to overwrite.")
    request = urllib.request.Request(
        image_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36",
            "Accept": "image/png,image/*;q=0.9,application/octet-stream,*/*;q=0.5",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(response.read())
    return out_path


def _extract_b64(payload: Any) -> str | None:
    data = getattr(payload, "data", None)
    if data is None and isinstance(payload, dict):
        data = payload.get("data")
    if not data:
        return None
    first = data[0]
    if isinstance(first, dict):
        value = first.get("b64_json")
        return value if isinstance(value, str) and value else None
    value = getattr(first, "b64_json", None)
    return value if isinstance(value, str) and value else None


def _extract_image_url(payload: Any) -> str | None:
    data = getattr(payload, "data", None)
    if data is None and isinstance(payload, dict):
        data = payload.get("data")
    if not data:
        return None
    first = data[0]
    if isinstance(first, dict):
        value = first.get("url")
        return value if isinstance(value, str) and value else None
    value = getattr(first, "url", None)
    return value if isinstance(value, str) and value else None


def _request_kwargs(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    output_format: str,
    background: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "response_format": "b64_json",
    }
    if background:
        kwargs["background"] = background
    if output_format and output_format.lower() != "png":
        kwargs["format"] = output_format.lower()
    return kwargs


def _generate_once(
    provider: Provider,
    *,
    prompt: str,
    model: str,
    size: str,
    quality: str,
    output_format: str,
    background: str | None,
    dry_run: bool,
) -> str:
    _require_key(provider, dry_run=dry_run)
    request = _request_kwargs(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        output_format=output_format,
        background=background,
    )
    if dry_run:
        print(
            json.dumps(
                {
                    "provider": provider.label,
                    "base_url": provider.base_url,
                    "request": request,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return ""

    client = _provider_client(provider)
    response = client.images.generate(**request)
    image_b64 = _extract_b64(response)
    if image_b64:
        return image_b64
    image_url = _extract_image_url(response)
    if image_url:
        return image_url
    raise RuntimeError("Provider returned a response without b64_json or url.")


def _retryable_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    patterns = (
        r"\b502\b",
        r"\b503\b",
        r"\b429\b",
        r"connection error",
        r"server disconnected without sending a response",
        r"remoteprotocolerror",
        r"upstream_error",
        r"timeout",
        r"timed out",
        r"rate limit",
        r"too many requests",
    )
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _generate_with_fallbacks(
    *,
    prompt: str,
    model: str,
    size: str,
    quality: str,
    output_format: str,
    background: str | None,
    dry_run: bool,
) -> tuple[str, Provider]:
    last_error: Exception | None = None
    for provider in _providers():
        print(f"AirCode provider: {provider.label}", file=sys.stderr)
        print(f"AirCode base URL: {provider.base_url}", file=sys.stderr)
        print(f"AirCode API key: {_masked(provider.api_key)}", file=sys.stderr)
        timeout = _provider_timeout(provider)
        if timeout is not None and timeout <= 0:
            raise SystemExit(f"Invalid provider timeout: {timeout!r}")

        attempts = 2 if not dry_run else 1
        for attempt in range(1, attempts + 1):
            try:
                if timeout is None:
                    image_b64 = _generate_once(
                        provider,
                        prompt=prompt,
                        model=model,
                        size=size,
                        quality=quality,
                        output_format=output_format,
                        background=background,
                        dry_run=dry_run,
                    )
                else:
                    image_b64 = asyncio.run(
                        asyncio.wait_for(
                            asyncio.to_thread(
                                _generate_once,
                                provider,
                                prompt=prompt,
                                model=model,
                                size=size,
                                quality=quality,
                                output_format=output_format,
                                background=background,
                                dry_run=dry_run,
                            ),
                            timeout=timeout,
                        )
                    )
                return image_b64, provider
            except Exception as exc:
                last_error = exc
                print(f"Provider {provider.label} failed: {exc}", file=sys.stderr)
                if attempt < attempts and _retryable_error(exc):
                    print(f"Retrying provider {provider.label} once after transient error.", file=sys.stderr)
                    continue
                break
        print(f"Provider {provider.label} exhausted; trying next provider if available.", file=sys.stderr)

    if last_error is None:
        raise SystemExit("No provider attempted.")
    raise SystemExit(f"{type(last_error).__name__}: {last_error}")


def _output_path_for_index(base: Path, index: int, total: int) -> Path:
    if total <= 1:
        return base
    suffix = base.suffix or ".png"
    stem = base.stem if base.suffix else base.name
    return base.with_name(f"{stem}-{index:02d}{suffix}")


def _resolve_concurrency(requested: int | None, total: int) -> int:
    if total <= 0:
        return 1
    if requested is None or requested <= 0:
        return min(total, MAX_BATCH_CONCURRENCY)
    return min(total, requested, MAX_BATCH_CONCURRENCY)


def _job_from_args(args: argparse.Namespace, *, index: int = 1, total: int = 1) -> dict[str, Any]:
    out_path = _output_path_for_index(Path(args.out), index, total)
    return {
        "prompt": args.prompt,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
        "background": args.background,
        "out": str(out_path),
        "force": args.force,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        jobs.append(json.loads(line))
    return jobs


def _parse_size(size: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)x(\d+)\s*", size)
    if not match:
        raise ValueError(f"Invalid size {size!r}; expected WIDTHxHEIGHT.")
    return int(match.group(1)), int(match.group(2))


def _validate_job_contract(job: dict[str, Any], *, index: int) -> None:
    required = ("prompt", "out", "size", "quality", "output_format", "model")
    missing = [name for name in required if not job.get(name)]
    if missing:
        raise ValueError(f"job {index} missing required fields: {', '.join(missing)}")

    aspect_ratio = str(job.get("aspect_ratio") or "").strip()
    if not aspect_ratio:
        return

    width, height = _parse_size(str(job["size"]))
    if aspect_ratio == "16:9" and width * 9 != height * 16:
        raise ValueError(
            f"job {index} aspect_ratio=16:9 conflicts with size={job['size']!r}; "
            "use the default 16:9 size 1920x1080."
        )
    if aspect_ratio == "1:1" and width != height:
        raise ValueError(
            f"job {index} aspect_ratio=1:1 conflicts with size={job['size']!r}; "
            "use the default 1:1 size 1024x1024."
        )
    if aspect_ratio == "9:16" and width * 16 != height * 9:
        raise ValueError(
            f"job {index} aspect_ratio=9:16 conflicts with size={job['size']!r}; "
            "use the default 9:16 size 1080x1920."
        )


def _print_probe() -> int:
    providers = []
    ready = False
    for provider in _providers():
        providers.append(
            {
                "label": provider.label,
                "base_url": provider.base_url,
                "api_key": _masked(provider.api_key),
                "ready": bool(provider.api_key),
            }
        )
        ready = ready or bool(provider.api_key)
    print(
        json.dumps(
            {
                "providers": providers,
                "batch_concurrency_limit": MAX_BATCH_CONCURRENCY,
                "ready": ready,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ready else 2


def cmd_probe(_args: argparse.Namespace) -> int:
    return _print_probe()


def cmd_generate(args: argparse.Namespace) -> int:
    total = max(1, args.n)
    if total == 1:
        image_payload, _provider = _generate_with_fallbacks(
            prompt=args.prompt,
            model=args.model,
            size=args.size,
            quality=args.quality,
            output_format=args.output_format,
            background=args.background,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            return 0
        if image_payload.startswith(("http://", "https://")):
            out_path = _write_image_from_url(image_payload, args.out, force=args.force)
        else:
            out_path = _write_b64_image(image_payload, args.out, force=args.force)
        print(f"Saved image: {out_path}", file=sys.stderr)
        return 0

    jobs = [_job_from_args(args, index=i, total=total) for i in range(1, total + 1)]
    return asyncio.run(_run_batch_jobs(jobs, concurrency=_resolve_concurrency(args.concurrency, total), dry_run=args.dry_run))


def cmd_edit(args: argparse.Namespace) -> int:
    _require_key(next(iter(_providers())), dry_run=args.dry_run)
    provider = next(iter(_providers()))
    print(f"AirCode provider: {provider.label}", file=sys.stderr)
    print(f"AirCode base URL: {provider.base_url}", file=sys.stderr)
    print(f"AirCode API key: {_masked(provider.api_key)}", file=sys.stderr)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "provider": provider.label,
                    "base_url": provider.base_url,
                    "request": {
                        "model": args.model,
                        "prompt": args.prompt,
                        "size": args.size,
                        "quality": args.quality,
                        "response_format": "b64_json",
                        "background": args.background,
                        "image": args.image,
                        "mask": args.mask,
                        "input_fidelity": args.input_fidelity,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    client = _provider_client(provider)
    with ExitStack() as stack:
        image_handles = [stack.enter_context(open(image, "rb")) for image in args.image]
        kwargs: dict[str, Any] = {
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "quality": args.quality,
            "response_format": "b64_json",
            "image": image_handles[0] if len(image_handles) == 1 else image_handles,
        }
        if args.mask:
            kwargs["mask"] = stack.enter_context(open(args.mask, "rb"))
        if args.input_fidelity:
            kwargs["input_fidelity"] = args.input_fidelity
        if args.background:
            kwargs["background"] = args.background
        response = client.images.edit(**kwargs)
    image_b64 = _extract_b64(response)
    if not image_b64:
        raise SystemExit("Provider returned an edit response without b64_json.")
    out_path = _write_b64_image(image_b64, args.out, force=args.force)
    print(f"Saved image: {out_path}", file=sys.stderr)
    return 0


def _run_single_job(job: dict[str, Any], *, dry_run: bool) -> tuple[str, str]:
    image_payload, _provider = _generate_with_fallbacks(
        prompt=str(job["prompt"]),
        model=str(job.get("model") or DEFAULT_MODEL),
        size=str(job.get("size") or DEFAULT_SIZE),
        quality=str(job.get("quality") or DEFAULT_QUALITY),
        output_format=str(job.get("output_format") or DEFAULT_OUTPUT_FORMAT),
        background=job.get("background"),
        dry_run=dry_run,
    )
    out = str(job["out"])
    if dry_run:
        return out, ""
    force = bool(job.get("force", False))
    if image_payload.startswith(("http://", "https://")):
        out_path = _write_image_from_url(image_payload, out, force=force)
    else:
        out_path = _write_b64_image(image_payload, out, force=force)
    return out, str(out_path)


async def _run_batch_jobs(jobs: list[dict[str, Any]], *, concurrency: int, dry_run: bool) -> int:
    concurrency = max(1, min(concurrency, MAX_BATCH_CONCURRENCY, len(jobs)))
    sem = asyncio.Semaphore(concurrency)
    print(f"Batch concurrency: {concurrency}", file=sys.stderr)

    async def run_one(idx: int, job: dict[str, Any]) -> tuple[int, bool, str]:
        async with sem:
            try:
                out, saved = await asyncio.to_thread(_run_single_job, job, dry_run=dry_run)
                if dry_run:
                    return idx, True, out
                print(f"[job {idx}] saved -> {saved}", file=sys.stderr)
                return idx, True, saved
            except Exception as exc:
                print(f"[job {idx}] failed: {exc}", file=sys.stderr)
                return idx, False, str(exc)

    results = await asyncio.gather(*(run_one(i, job) for i, job in enumerate(jobs, start=1)))
    failed = [idx for idx, ok, _msg in results if not ok]
    if failed:
        print(f"failed jobs: {failed}", file=sys.stderr)
        return 1
    return 0


def cmd_generate_batch(args: argparse.Namespace) -> int:
    jobs = _load_jsonl(Path(args.input))
    if not jobs:
        raise SystemExit("Input JSONL is empty.")
    for index, job in enumerate(jobs, start=1):
        job.setdefault("model", args.model)
        job.setdefault("size", args.size)
        job.setdefault("quality", args.quality)
        job.setdefault("output_format", args.output_format)
        job.setdefault("background", args.background)
        job.setdefault("force", args.force)
        _validate_job_contract(job, index=index)
    concurrency = _resolve_concurrency(args.concurrency, len(jobs))
    return asyncio.run(_run_batch_jobs(jobs, concurrency=concurrency, dry_run=args.dry_run))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate images through the AirCode-compatible endpoint.")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="Show provider configuration without network calls.")
    probe.set_defaults(func=cmd_probe)

    gen = sub.add_parser("generate", help="Generate one or more images from a single prompt.")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--model", default=DEFAULT_MODEL)
    gen.add_argument("--size", default=DEFAULT_SIZE)
    gen.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    gen.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "webp"])
    gen.add_argument("--out", default=DEFAULT_OUT)
    gen.add_argument("--n", type=int, default=1, help="Number of images to generate; repeated calls run in parallel.")
    gen.add_argument("--concurrency", type=int, default=0, help=f"Parallel request cap for --n > 1 or batch jobs; max {MAX_BATCH_CONCURRENCY}.")
    gen.add_argument("--background", choices=["transparent", "opaque", "auto"])
    gen.add_argument("--force", action="store_true")
    gen.add_argument("--dry-run", action="store_true")
    gen.set_defaults(func=cmd_generate)

    edit = sub.add_parser("edit", help="Edit one or more images through the direct image endpoint.")
    edit.add_argument("--image", action="append", required=True)
    edit.add_argument("--prompt", required=True)
    edit.add_argument("--model", default=DEFAULT_MODEL)
    edit.add_argument("--size", default=DEFAULT_SIZE)
    edit.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    edit.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "webp"])
    edit.add_argument("--out", default=DEFAULT_OUT)
    edit.add_argument("--mask")
    edit.add_argument("--input-fidelity", choices=["low", "high"])
    edit.add_argument("--background", choices=["transparent", "opaque", "auto"])
    edit.add_argument("--force", action="store_true")
    edit.add_argument("--dry-run", action="store_true")
    edit.set_defaults(func=cmd_edit)

    batch = sub.add_parser("generate-batch", help="Generate many prompts in parallel from a JSONL job file.")
    batch.add_argument("--input", required=True, help="Path to a JSONL file with prompt/out jobs.")
    batch.add_argument("--model", default=DEFAULT_MODEL)
    batch.add_argument("--size", default=DEFAULT_SIZE)
    batch.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    batch.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "webp"])
    batch.add_argument("--background", choices=["transparent", "opaque", "auto"])
    batch.add_argument("--concurrency", type=int, default=0, help=f"Parallel request cap; default auto, max {MAX_BATCH_CONCURRENCY}.")
    batch.add_argument("--force", action="store_true")
    batch.add_argument("--dry-run", action="store_true")
    batch.set_defaults(func=cmd_generate_batch)

    stream = sub.add_parser("generate-stream", help="Compatibility alias for generate.")
    stream.add_argument("--prompt", required=True)
    stream.add_argument("--model", default=DEFAULT_MODEL)
    stream.add_argument("--size", default=DEFAULT_SIZE)
    stream.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    stream.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "webp"])
    stream.add_argument("--out", default=DEFAULT_OUT)
    stream.add_argument("--n", type=int, default=1)
    stream.add_argument("--concurrency", type=int, default=0)
    stream.add_argument("--background", choices=["transparent", "opaque", "auto"])
    stream.add_argument("--force", action="store_true")
    stream.add_argument("--dry-run", action="store_true")
    stream.set_defaults(func=cmd_generate)

    return parser


def main() -> int:
    _load_local_env()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
