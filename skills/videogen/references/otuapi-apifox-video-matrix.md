# OTU/NewAPI Apifox Video Matrix

Source snapshot: `https://6l0ket291i.apifox.cn/llms.txt`, checked 2026-06-14.

Use this reference for the `https://otuapi.com` NewAPI-compatible gateway documented in the Apifox project. Keep API keys only in project-local `.env.local`.

## Common Flow

All active video tasks use:

1. Create: `POST /v1/videos`
2. Query: `GET /v1/videos/{task_id}`
3. Download: use the URL returned by the completed task.

Always send:

```text
Authorization: Bearer <API_KEY>
```

Polling status values seen in docs and live tests:

```text
queued, processing, in_progress, completed, failed
SUBMITTED, IN_PROGRESS, SUCCESS, FAILURE
```

Result URL fields are inconsistent across pages and responses. Read in this order:

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

## Active Video Models

Default policy for this project: prefer `omni_flash-10s` first and `sora-2-12s` second. Do not use other OTU models unless the user explicitly names them.

| Model | Use | Endpoint | Images / References | Notes |
|---|---|---|---|---|
| `sora-2-12s` | Sora text-to-video or image-to-video | `POST /v1/videos` | JSON `images` uses URL array and takes first image; multipart uses `input_reference` | `size` is required; duration is in the model name. |
| `omni_flash-10s` | Omni text-to-video, reference image-to-video, video edit | `POST /v1/videos` | JSON `images`, or multipart repeated `input_reference`; max 7 | Current docs say no first/last-frame mode. |
| `veo_3_1-fast` | Veo text-to-video or reference image-to-video | `POST /v1/videos` | JSON `images`, or multipart repeated `input_reference`; max 3 | Use for reference-image mode. |
| `veo_3_1-fast-fl` | Veo first/last-frame video | `POST /v1/videos` | 1-2 images; order is first frame then last frame | Some examples mention `veo_3_1-fl`; prefer documented `veo_3_1-fast-fl` unless live model list says otherwise. |
| `veo_3_1-fast-extend` | Extend an existing Veo video to 15s | `POST /v1/videos` | No image field; requires `remix_id` | `remix_id` is a `video_xxx` ID, not `task_id`; use within 12 hours. |

## Related Async Image Models Through `/v1/videos`

| Model | Use | Endpoint | References | Notes |
|---|---|---|---|---|
| `gpt-image-2` | Async text-to-image or image-to-image | `POST /v1/videos` | JSON `images`; max 5 | Uses `aspect_ratio`, not `size`. |
| `gpt-image-2-2K` | 2K async image | `POST /v1/videos` | JSON `images`; max 5 | Same parameters as `gpt-image-2`. |
| `gpt-image-2-4K` | 4K async image | `POST /v1/videos` | JSON `images`; max 5 | Same parameters as `gpt-image-2`. |
| `nano_banana_2` | Async text-to-image or image-to-image | `POST /v1/videos` | JSON `images`; max 5 | Uses `aspect_ratio`, not `size`; standard fast tier. |
| `nano_banana_pro-1K` | 1K async image | `POST /v1/videos` | JSON `images`; max 5 | Uses `aspect_ratio`, not `size`. |
| `nano_banana_pro-2K` | 2K async image | `POST /v1/videos` | JSON `images`; max 5 | Uses `aspect_ratio`, not `size`. |
| `nano_banana_pro-4K` | 4K async image | `POST /v1/videos` | JSON `images`; max 5 | Uses `aspect_ratio`, not `size`. |

Supported `aspect_ratio` values for `gpt-image-2*`:

```text
1:1, 5:4, 9:16, 21:9, 16:9, 3:2, 4:3, 4:5, 3:4, 2:3
```

Supported `aspect_ratio` values for `nano_banana*`:

```text
1:1, 9:16, 16:9, auto
```

## Other Active Image Endpoints

These models were present in the same Apifox project but are not video-generation models.

| Model | Use | Endpoint | Notes |
|---|---|---|---|
| `gemini-3-pro-image-preview` | Gemini-native synchronous text-to-image / image-to-image | `POST /v1beta/models/{model}:generateContent` | Model ID is embedded in the URL path; uses `generationConfig.imageConfig.aspectRatio`. |
| `gemini-3.1-flash-image-preview` | Gemini-native synchronous text-to-image / image-to-image | `POST /v1beta/models/{model}:generateContent` | Supports extra aspect ratios and `imageSize` values `1K`, `2K`, `4K`. |
| `image2` | OpenAI-compatible image generation and edits | `POST /v1/images/generations`, `POST /v1/images/edits` | Uses `size`; supports JSON and multipart. |

## Request Body Rules

Use JSON for URL/base64 references:

```json
{
  "model": "omni_flash-10s",
  "prompt": "A classroom story hook.",
  "size": "1280x720",
  "images": ["https://example.com/ref.jpg"]
}
```

Use multipart for local image or video files:

```powershell
curl.exe -X POST "https://otuapi.com/v1/videos" `
  -H "Authorization: Bearer <API_KEY>" `
  -F "model=omni_flash-10s" `
  -F "prompt=A classroom story hook." `
  -F "size=1280x720" `
  -F "input_reference=@D:\path\ref.jpg"
```

For Veo 15s extension:

```json
{
  "model": "veo_3_1-fast-extend",
  "remix_id": "video_xxx",
  "prompt": "Continue the motion naturally."
}
```

## Deprecated / Historical Pages

The Apifox project marks these as invalid or historical. Do not use them as defaults:

```text
sora-2-landscape-10s
sora-2-portrait-10s
sora-2-landscape-15s
sora-2-portrait-15s
sora-2-pro-landscape-25s
sora-2-pro-portrait-25s
sora-2-pro-landscape-hd-15s
sora-2-pro-portrait-hd-15s
veo_3_1-fast-remix
veo_3_1-fast-fl-remix
veo_3_1-fast-hd-remix
veo_3_1-fast-fl-hd-remix
veo_3_1-hd-remix
veo_3_1-hd-fl-remix
veo_3_1-remix
veo_3_1-fl-remix
```

## Known Operational Findings

- The gateway may return both `id` and `task_id`; prefer the ID returned at creation, and keep both in manifests.
- Completed downloads may be blocked by the file host if using a bare Python `urllib` request. Send a browser-like `User-Agent` and broad `Accept`, but do not force `Referer: https://otuapi.com/`; live Omni smoke on 2026-06-21 showed the OSS file host returned 403 when that Referer was present, while the same URL downloaded successfully without it.
- Inputs can fail with upstream image/content policy errors such as `PUBLIC_ERROR_IP_INPUT_IMAGE`; this is separate from token/auth failure.
- Query without a token returns `401`; query with a valid token can still fail model authorization or content policy checks.
