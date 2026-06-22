---
name: videogen
description: Use inside ShanHaiEdu whenever the user wants to generate, query, download, validate, batch, or QA videos through MiniMax/Hailuo or OTU/NewAPI Apifox gateways. Default OTU video generation must prefer omni_flash-10s first and sora-2-12s second; other OTU models require explicit user naming.
---

# videogen

Use this project-local skill to run MiniMax/Hailuo or NewAPI-compatible video generation for ShanHaiEdu lesson videos.

## Scope

This skill handles:

- text-to-video, image-to-video, first/last-frame video, and subject-reference video
- task status query and file download
- local `.env.local` configuration without exposing keys
- OpenAI/NewAPI-compatible `/v1/models` discovery for reseller or gateway endpoints
- OTU/Apifox `POST /v1/videos` video task creation, polling, and download
- per-shot manifest records for later QA
- conservative settings for classroom opening videos

Do not use this skill for image generation, TTS, music, or final editing unless the task is directly connected to Hailuo video generation.
The OTU/Apifox docs also include image models; keep them in the model matrix, but do not treat them as video-generation defaults.

## Local Commands

From the project root:

```powershell
.\scripts\videogen.ps1 --help
```

The Python implementation lives at:

```text
skills\videogen\scripts\videogen.py
```

The webapp integration lives at:

```text
apps\api\app\providers.py
apps\api\app\services.py
docs\api-research\octo-video\
```

OTU/Apifox reference matrix:

```text
skills\videogen\references\otuapi-apifox-video-matrix.md
```

## Configuration

Read credentials from the current project only. The helper checks `.env.local`, `.env`, and `apps\api\.env`, then process environment. For ShanHaiEdu, prefer the existing backend variables:

```text
OCTO_API_KEY=<redacted>
OCTO_BASE_URL=https://otuapi.com

# Compatibility aliases are also supported when needed:
MINIMAX_API_KEY=<redacted>
MINIMAX_BASE_URL=https://api.minimax.io
NEWAPI_API_KEY=<redacted>
NEWAPI_BASE_URL=https://otuapi.com
MINIMAX_DEFAULT_MODEL=MiniMax-Hailuo-2.3
MINIMAX_DEFAULT_RESOLUTION=768P
MINIMAX_DEFAULT_DURATION=6
MINIMAX_PROMPT_OPTIMIZER=false
OMNI_DEFAULT_MODEL=omni_flash-10s
OMNI_DEFAULT_SIZE=1280x720
NEWAPI_DEFAULT_MODEL=omni_flash-10s
NEWAPI_DEFAULT_SIZE=1280x720
```

Never print or copy API keys into replies, docs, manifests, commands, or logs. For ShanHaiEdu NewAPI-compatible video generation, `OCTO_API_KEY` is mapped internally to the helper's NewAPI aliases; do not depend on external project `.env.local` files.

## Available Official Video Interfaces

Count the MiniMax video-generation API surface as 6 primary interfaces:

1. Text to Video: `POST /v1/video_generation` with `model` + `prompt`
2. Image to Video: `POST /v1/video_generation` with `model` + `first_frame_image`
3. Start / End to Video: `POST /v1/video_generation` with `model` + `first_frame_image`/`last_frame_image`
4. Subject Reference to Video: `POST /v1/video_generation` with `model` + `subject_reference`
5. Query Video Generation Task: `GET /v1/query/video_generation`
6. Download Video File: `GET /v1/files/retrieve`

There are also file metadata/list/delete APIs and deprecated Video Agent template APIs, but do not count them as the core Hailuo video generation path unless the user asks.

## OTU / Apifox Gateway

Use this branch for `https://otuapi.com` and the official Apifox docs at `https://6l0ket291i.apifox.cn/`.

Active video flow:

1. Create: `POST /v1/videos`
2. Query: `GET /v1/videos/{task_id}`
3. Download: query until completed, then download the returned URL.

Always send `Authorization: Bearer <API_KEY>`. Keep the key in project-local `.env.local`; do not print it in replies, manifests, docs, or command examples.

Active video models from the Apifox docs:

| Model | Use | Key fields |
|---|---|---|
| `sora-2-12s` | 12s Sora text-to-video or image-to-video | `prompt`, required `size`; JSON `images` or multipart `input_reference` |
| `omni_flash-10s` | 10s 720p Omni text-to-video, reference image-to-video, video edit | `prompt`, optional `size`; max 7 `images` / `input_reference`; no first/last-frame mode |
| `veo_3_1-fast` | Veo text-to-video or reference-image video | `prompt`, optional `size`; max 3 references |
| `veo_3_1-fast-fl` | Veo first/last-frame video | `prompt`, optional `size`; 1-2 references, first image then last image |
| `veo_3_1-fast-extend` | Extend a previous Veo video to 15s | `prompt`, `remix_id`; no image field; save `remix_id` immediately after original task creation |

Default OTU model policy:

- First choice: `omni_flash-10s`.
- Second choice: `sora-2-12s`.
- Do not use Veo, `gpt-image-2*`, `nano_banana*`, Gemini image, or `image2` unless the user explicitly names that model or explicitly asks to test/use that family.
- The script enforces this for `newapi-create`: non-default OTU models require `--allow-other-model`.

Related image models in the same Apifox project:

- `/v1/videos` async image tasks: `gpt-image-2`, `gpt-image-2-2K`, `gpt-image-2-4K`, `nano_banana_2`, `nano_banana_pro-1K`, `nano_banana_pro-2K`, `nano_banana_pro-4K`
- Gemini-native image endpoint: `gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview`
- OpenAI-compatible image endpoint: `image2`

These are available in `otu-models`, but use a dedicated image workflow unless the user explicitly asks to inspect or test the image side.

Deprecated Apifox pages include old Sora 10s/15s/25s model names and Veo `*-remix` direct 15s models. Do not use them as defaults.

Result parsing must tolerate inconsistent fields:

```text
video_url
url
result_url
data.video_url
data.url
data.result_url
data.first_video_url
result.video_url
result.url
```

Normalize statuses from both lowercase and uppercase variants: `queued`, `processing`, `in_progress`, `completed`, `failed`, `SUBMITTED`, `IN_PROGRESS`, `SUCCESS`, `FAILURE`.

Use JSON for URL or Base64 references only when the URL has been verified as externally fetchable by the provider. For ShanHaiEdu runtime, prefer `--multipart` for local reference files that already exist under the project storage directory; this avoids provider-side 403 failures when OTU tries to fetch a temporary image URL.

## Model Defaults

Prefer:

- `MiniMax-Hailuo-2.3` for normal text-to-video and image-to-video quality
- `MiniMax-Hailuo-2.3-Fast` for fast image-to-video candidate generation
- `MiniMax-Hailuo-02` for first/last-frame generation
- `S2V-01` only when character face reference is the actual requirement

Default output:

- `duration`: `6`
- `resolution`: `768P`
- `prompt_optimizer`: `false` when prompts are already storyboard-controlled

## Camera Commands

Hailuo supports bracketed camera commands on supported models:

```text
[Truck left] [Truck right] [Pan left] [Pan right]
[Push in] [Pull out] [Pedestal up] [Pedestal down]
[Tilt up] [Tilt down] [Zoom in] [Zoom out]
[Shake] [Tracking shot] [Static shot]
```

For lesson opening videos, prefer `[Static shot]`, `[Push in]`, `[Pull out]`, and `[Tracking shot]`. Avoid `[Shake]` unless the story intentionally needs instability.

## Workflow

1. Confirm the shot is a story setup or instructional explanation.
2. For ShanHaiEdu, prefer image-to-video from approved keyframes when reference assets exist.
3. Confirm each approved keyframe has been downloaded to local project storage, for example `assets\generated_images\asset_001.png`.
4. Submit local keyframes as multipart `input_reference` by default. Do not rely on a temporary public image URL unless it is verified from a non-local machine without cookies, auth headers, or forced Referer.
5. Use 6-second clips first; only use 10 seconds for simple scenes with low continuity risk.
6. Submit one shot and save a manifest before scaling batch generation. Record whether the reference used `multipart` or `url`.
7. Query until `Success` or `Fail`.
8. Download the completed video URL promptly with browser-like headers.
9. Verify local file existence, size, duration, resolution, fps, and frame samples before accepting.

## Webapp Promax Mapping

When using the local workflow website, submit video jobs through:

```text
POST /api/video/{project_id}/submit
```

The `minimax` provider is the real Hailuo provider, not a demo provider. It reads `MINIMAX_API_KEY` only from environment variables or `.env.local`.

Promax asset mapping:

- `Shot.prompt` becomes the video prompt.
- `Shot.first_frame_asset_id` or a done keyframe with `frame_role=start` becomes `first_frame_image`.
- `Shot.last_frame_asset_id` or a done keyframe with `frame_role=end` becomes `last_frame_image`.
- `generation_mode=char_ref_plus_frames` adds a character reference from `asset_type=character` or `CHAR_` assets.
- `requires_exact_digits=1` disables prompt optimization and marks text, digits, RMB labels, and formulas for deterministic overlay.

For "小圆圈 + 提示词 + 垫图" packages, default to I2V. Use FL2V only when a real ending frame exists. Use S2V only when character identity consistency is more important than scene motion.

## Example Commands

Text to video dry run:

```powershell
.\scripts\videogen.ps1 t2v --prompt "A warm classroom mystery box on the table. [Push in]" --dry-run
```

Image to video:

```powershell
.\scripts\videogen.ps1 i2v --first-frame ".\video_task_packages\demo\keyframes\shot01.png" --prompt "Children lean closer with curiosity. [Static shot]" --out ".\video_task_packages\demo\videos\shot01.mp4"
```

Query:

```powershell
.\scripts\videogen.ps1 query --task-id "<task_id>"
```

Download:

```powershell
.\scripts\videogen.ps1 download --file-id "<file_id>" --out ".\output.mp4"
```

Models and interface list:

```powershell
.\scripts\videogen.ps1 interfaces
.\scripts\videogen.ps1 models
.\scripts\videogen.ps1 models --live
.\scripts\videogen.ps1 ping
.\scripts\videogen.ps1 otu-models
```

Use `models --live` or `ping` before any real generation when the endpoint is a NewAPI-style gateway. These commands call `/v1/models` only and should not submit a video generation task.

OTU/NewAPI-compatible video gateway:

```powershell
.\scripts\videogen.ps1 newapi-create --model omni_flash-10s --prompt "A warm classroom story hook. [Static shot]" --size 1280x720 --dry-run
.\scripts\videogen.ps1 newapi-create --model omni_flash-10s --image ".\storage-demo\projects\demo\assets\generated_images\asset_001.png" --prompt "A warm classroom story hook. [Static shot]" --size 1280x720 --multipart --dry-run
.\scripts\videogen.ps1 newapi-create --model sora-2-12s --prompt "A warm classroom story hook. [Static shot]" --size 1920x1080 --dry-run
.\scripts\videogen.ps1 newapi-create --model veo_3_1-fast-fl --image ".\video_task_packages\demo\keyframes\start.png" --image ".\video_task_packages\demo\keyframes\end.png" --prompt "A smooth transition between the approved frames." --size 1280x720 --multipart --allow-other-model --dry-run
.\scripts\videogen.ps1 newapi-create --model veo_3_1-fast-extend --remix-id "video_xxx" --prompt "Continue the previous shot naturally." --allow-other-model --dry-run
.\scripts\videogen.ps1 newapi-query --task-id "<task_id>"
.\scripts\videogen.ps1 newapi-download --task-id "<task_id>" --out ".\video_task_packages\demo\videos\shot01.mp4"
```

Compatibility aliases are still available:

```powershell
.\scripts\videogen.ps1 omni-t2v --prompt "A warm classroom story hook. [Static shot]" --dry-run
.\scripts\videogen.ps1 omni-i2v --image ".\video_task_packages\demo\keyframes\shot01.png" --prompt "Children lean closer with curiosity. [Static shot]" --dry-run
.\scripts\videogen.ps1 omni-query --task-id "<task_id>"
.\scripts\videogen.ps1 omni-download --task-id "<task_id>" --out ".\video_task_packages\demo\videos\shot01.mp4"
```

For the `otuapi.com` gateway tested in this project, treat `omni_flash-10s` and the Apifox Sora/Veo models as OTU/NewAPI `/v1/videos` models, not as MiniMax official `/v1/video_generation` models.

Live Omni smoke on 2026-06-21 confirmed `omni_flash-10s` can submit, reach `completed`, and return `video_url`. Download the completed URL promptly with browser-like `User-Agent` and broad `Accept`; do not force a `Referer` header, because the observed OSS download URL returned 403 when `Referer: https://otuapi.com/` was present.

T075 real fullchain continuation on 2026-06-22 showed a different 403 class: the video task failed before generation because OTU media preprocessing could not fetch the submitted reference image URL (`HTTP 403`). Treat this as a reference input transport failure, not as completed MP4 download failure. For ShanHaiEdu, the default design is to download image assets locally first and submit those local files through multipart `input_reference`; URL-based JSON `images` is a fallback only after external fetchability is proven.

Before a real paid generation, show the user the exact model, input images, prompt, size/aspect settings, and whether JSON or multipart will be used. Wait for approval unless the user has already explicitly approved that exact request.

## QA Rules

Reject clips with:

- wrong characters, changed props, wrong classroom layout, or scene replacement
- generated fake text, digits, formulas, money values, or board work
- drift into teaching exact content when the shot is only a story hook
- corrupt downloads or mismatched duration/resolution

Use deterministic overlays for exact captions, formulas, prices, and board content.
