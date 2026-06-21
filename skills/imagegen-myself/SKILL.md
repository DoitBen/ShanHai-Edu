---
name: "imagegen-myself"
description: "Use when the user asks to generate images, 生图, role sheets, character boards, concept art, covers, image prompts, or third-party image generation through the local NewAPI/PinAI/AirCode-compatible image endpoint instead of the built-in image tool."
---

# NewAPI Image Generation

Use this personal skill for image generation through the user's third-party NewAPI-compatible endpoint. This skill intentionally defaults to the local wrapper and batch runner rather than the built-in `image_gen` tool.

## Provider

- Primary base URL: `https://img.baofu.eu.cc/v1`
- Model: `gpt-image-2`
- Current workflow default: `1920x1080`, `quality=high`, PNG for 16:9 video assets
- Verified aspect profiles: `1920x1080` for 16:9, `1024x1024` for 1:1, `1080x1920` for 9:16
- Preferred API key environment variable: `IMAGEGEN_MYSELF_API_KEY`
- Preferred base URL environment variable: `IMAGEGEN_MYSELF_BASE_URL`
- NewAPI-compatible variables: `NEWAPI_API_KEY` and `NEWAPI_BASE_URL`
- Backward-compatible API key variables: `PINAI_API_KEY`, `AIRCODE_API_KEY`, or `OPENAI_API_KEY`
- The wrapper maps these to the direct OpenAI-compatible image client via `OPENAI_API_KEY` and `OPENAI_BASE_URL`.
- Local private provider config should live in this skill directory's `.env.local`; do not read or print its secret values.
- Provider config precedence is intentional: workspace `.env` is only a low-priority fallback; this skill directory's `.env.local` is loaded last and wins for `imagegen-myself`.
- Variable precedence inside this skill is: `IMAGEGEN_MYSELF_PRIMARY_*` / `IMAGEGEN_MYSELF_*`, then `NEWAPI_PRIMARY_*` / `NEWAPI_*`, then backward-compatible `PINAI_*`, `AIRCODE_*`, and `OPENAI_*`.

Do not put API keys in `SKILL.md`, prompts, output files, or scripts. If the key is missing, ask the user to set `IMAGEGEN_MYSELF_API_KEY` or `NEWAPI_API_KEY`, or set it for the current process only when the user explicitly provides it.

The configured NewAPI endpoint was verified on 2026-06-10 with `1920x1080 + high`, `1024x1024 + high`, and `1080x1920 + high`. The old `us.pinai-cn.com` endpoint was previously verified to generate with `1024x1024 + low`, but it returned `503 No available compatible accounts` for `medium`, `high`, `2048x2048`, and `3840x2160` during that check. Prefer the configured NewAPI endpoint unless the user explicitly asks to test another provider.

## Default Workflow

1. Treat normal image requests as NewAPI-compatible image generation requests.
2. Use `scripts/aircode_image_gen.py generate` for single-image requests.
3. Use `scripts/aircode_image_gen.py generate-batch` for multiple images or asset sets. Run them in parallel by default.
4. Cap parallel requests at 20. If there are 20 or fewer images, run them all concurrently; if there are more, split into parallel batches.
5. Use `scripts/aircode_image_gen.py edit` for image-to-image requests when the endpoint supports it.
6. Save final images under `output/imagegen/` in the current workspace unless the user names another location.
7. Prefer these defaults unless the user asks otherwise:
   - model: `gpt-image-2`
   - size: `1920x1080` for 16:9 video assets; use `1024x1024` for 1:1 and `1080x1920` for 9:16
   - quality: `high`
   - output format: `png`
8. For a dry run or endpoint check, use `--dry-run` or `probe`.
9. After generation or editing, inspect the saved image if possible and report the final path and prompt.

## Commands

Dry run, no network:

```powershell
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" generate `
  --prompt "A polished character design board" `
  --size 1920x1080 `
  --quality high `
  --out "output/imagegen/character-board.png" `
  --dry-run
```

Probe provider configuration:

```powershell
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" probe
```

Generate:

```powershell
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" generate-stream `
  --prompt "A polished character design board" `
  --size 1920x1080 `
  --quality high `
  --out "output/imagegen/character-board.png"
```

Batch generate in parallel:

```powershell
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" generate-batch `
  --input "jobs.jsonl" `
  --concurrency 20 `
  --force
```

Verified sizes:

```powershell
# NewAPI verified working profile
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" generate-stream `
  --prompt "A simple polished object on a plain white background, no text" `
  --size 1920x1080 `
  --quality high `
  --out "output/imagegen/pinai-1k-low.png"

# Probe only when the user explicitly asks for larger output; provider account pools can reject larger or higher-quality settings
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" generate-stream `
  --prompt "A simple polished object on a plain white background, no text" `
  --size 3840x2160 `
  --quality low `
  --out "output/imagegen/pinai-4k-probe.png" `
  --timeout 300
```

Image edit:

```powershell
python "C:\Users\HB\.agents\skills\imagegen-myself\scripts\aircode_image_gen.py" edit `
  --image "input.png" `
  --prompt "Change only the background; keep the subject unchanged" `
  --size 1024x1024 `
  --quality high `
  --out "output/imagegen/edited.png"
```

## Prompt Guidance

For character setting boards, structure prompts with:

- asset type and use
- character identity
- silhouette and proportions
- face, hair, costume, accessories
- front/side/back or expression/details if needed
- background/layout constraints
- text policy: avoid text unless exact text is required

Keep prompts specific enough for visual consistency. Do not invent unrelated characters, brands, logos, or text.

## Failure Handling

If generation fails:

1. Check whether `NEWAPI_API_KEY` is present.
2. Check whether the provider is defaulting to `https://img.baofu.eu.cc/v1`.
3. If the provider rejects `gpt-image-2`, retry only after explaining the provider may not support that image model.
4. If the provider returns `503 No available compatible accounts`, first retry once with the verified working profile: `1024x1024`, `quality=high`. If that fails, retry `1024x1024`, `quality=low` before reporting upstream/account-pool unavailability.
5. If the provider disconnects or returns `upstream_error`, retry once with `generate-stream` for text-to-image. If it still fails, report upstream instability.
6. If `/v1/images/edits` disconnects without a response, retry once with a small PNG input when practical. If it still fails, report upstream instability.
7. If the provider rejects `/v1/images/generations` or `/v1/images/edits`, explain that this endpoint may support chat completions but not OpenAI-style image generation or editing.
8. Do not silently switch to a non-image chat model for image requests.
