# Real E2E Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a repeatable real-provider end-to-end chain that produces verified `outputs/final_video.mp4` with Chinese male narration and an exported `.pptx` from a textbook PDF.

**Architecture:** Keep the product chain linear and evidence-driven: PDF upload creates structured teaching content, LLM nodes produce lesson and video plans, real image/video providers produce media assets, Minimax TTS creates narration, ffmpeg composes final video, and PPT export embeds the final video. The short-term execution path favors the existing API, provider, storage, and smoke-script boundaries; Prompt management platform GA stays parallel and must not block the real media chain.

**Tech Stack:** FastAPI, SQLite-backed local storage, provider adapters in Python, Minimax TTS, DeepSeek/Minimax text LLM modes, NewAPI-compatible image generation, Octo/NewAPI-compatible video generation, ffmpeg/ffprobe, python-pptx, pytest, Next.js 16/React 19 frontend.

---

## Current Position

- Local fake/placeholder E2E is structurally working.
- Real Minimax TTS single-provider smoke has passed.
- Real image provider can generate and persist at least one image in the T075 chain.
- Real storyboard generation now passes after LLM context sanitization and weak `model_prompt` normalization.
- Real image + real video + real TTS + final video + PPT E2E has not passed yet because the video provider currently returns `429 RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED` for the single submitted clip.
- Prompt file/runtime loading has a stopgap and registry base; full admin Prompt platform is not part of the short-term release blocker.
- T075 smoke and backend `final_video/generate` now share the same configurable video-model default: request `model` or T075 `--video-model` first, then `VIDEO_MODEL`, `OMNI_DEFAULT_MODEL`, `NEWAPI_DEFAULT_MODEL`, and finally `omni_flash-10s`.

## Success Standard

The chain is accepted only when one run with real provider modes produces all of the following evidence in one timestamped folder under `docs/qa-audits/t075-real-fullchain-smoke-evidence/`:

- `summary.json` with `"ok": true`.
- At least one downloaded real image under `images/`.
- At least one downloaded real video clip under `clips/`.
- `final_video.mp4` with a non-empty audio stream proven by `ffprobe`.
- `lesson-video-demo.pptx` or exported `.pptx` with at least one embedded `ppt/media/*.mp4`.
- Final video node content includes `voice_gender=male`, `voice_language=zh-CN`, `audio_verified=true`, `english_audio_detected=false`, `narration_audio_path`, `subtitle_srt_path`, `concat_manifest_path`, and `video_path=outputs/final_video.mp4`.
- No report, log, evidence JSON, or documentation contains raw provider keys.

## File Map

- `scripts/t075_real_fullchain_smoke.py`: main real E2E runner and evidence collector.
- `apps/api/tests/test_t075_smoke_script.py`: smoke-script unit coverage.
- `apps/api/tests/test_tts_and_final_video.py`: TTS and final-video contract tests.
- `apps/api/tests/test_real_providers.py`: provider integration and partial asset continuation tests.
- `apps/api/app/models.py`: node generation request options, including partial image controls.
- `apps/api/app/services.py`: node orchestration, partial image behavior, final video composition, and artifact schema.
- `apps/api/app/providers.py`: real provider adapters, including Minimax TTS and real media providers.
- `apps/api/app/video_outputs.py`: ffmpeg/ffprobe helper boundary if final video verification needs to be centralized.
- `apps/api/app/main.py`: provider wiring and environment-mode routing.
- `apps/api/app/settings.py`: environment variables and defaults.
- `apps/api/README.md`, `apps/api/.env.example`, `docs/llm-provider-contract.md`: developer-facing runtime and provider contract docs.
- `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`: frontend status visibility for final video, audio, and artifact state.
- `workflow/multi-agent/stage-review.md`, `workflow/multi-agent/handoffs/latest.md`: stage-level record after successful real run.

## Phase 0: Freeze The Real E2E Contract

**Objective:** Make the pass/fail definition executable before changing the chain again.

**Files:**
- Modify: `scripts/t075_real_fullchain_smoke.py`
- Modify: `apps/api/tests/test_t075_smoke_script.py`
- Modify: `docs/llm-provider-contract.md`

- [x] **Step 0.1: Add final media schema checks to the smoke-script tests**

Add a test case in `apps/api/tests/test_t075_smoke_script.py` that builds an evidence dictionary with `final_video_node_content` and `ffprobe` fields, then asserts success requires audio and narration metadata:

```python
def test_success_checks_require_final_video_audio_contract():
    from scripts.t075_real_fullchain_smoke import evaluate_success_checks

    evidence = {
        "generated_image_paths": [{"bytes": 1024}],
        "clip_download_paths": [{"bytes": 2048}],
        "final_video_path": {"bytes": 4096},
        "ppt_path": {"bytes": 8192, "ppt_media_mp4_entries": ["ppt/media/media1.mp4"]},
        "final_video_node_content": {
            "voice_gender": "male",
            "voice_language": "zh-CN",
            "audio_verified": True,
            "english_audio_detected": False,
            "narration_audio_path": "audio/narration.mp3",
            "subtitle_srt_path": "audio/narration.srt",
            "concat_manifest_path": "outputs/concat_manifest.json",
            "video_path": "outputs/final_video.mp4",
        },
        "ffprobe": {"audio_stream_count": 1},
    }

    checks = evaluate_success_checks(evidence)

    assert checks["has_verified_audio"]["ok"] is True
    assert checks["has_final_video_schema"]["ok"] is True
    assert checks["has_embedded_ppt_video"]["ok"] is True
```

- [x] **Step 0.2: Run the new test and confirm it fails before script changes**

Run:

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py::test_success_checks_require_final_video_audio_contract -q
```

Expected before implementation: failure because `has_verified_audio`, `has_final_video_schema`, or `has_embedded_ppt_video` is not produced.

- [x] **Step 0.3: Extend `evaluate_success_checks`**

Update `scripts/t075_real_fullchain_smoke.py` so `evaluate_success_checks` adds these checks:

```python
final_content = evidence.get("final_video_node_content") if isinstance(evidence.get("final_video_node_content"), dict) else {}
ffprobe = evidence.get("ffprobe") if isinstance(evidence.get("ffprobe"), dict) else {}
ppt_media = ((evidence.get("ppt_path") or {}).get("ppt_media_mp4_entries") or [])
has_schema = (
    final_content.get("voice_gender") == "male"
    and final_content.get("voice_language") == "zh-CN"
    and final_content.get("audio_verified") is True
    and final_content.get("english_audio_detected") is False
    and bool(final_content.get("narration_audio_path"))
    and bool(final_content.get("subtitle_srt_path"))
    and bool(final_content.get("concat_manifest_path"))
    and final_content.get("video_path") == FINAL_VIDEO_REL_PATH
)
```

The returned checks must include `has_verified_audio`, `has_final_video_schema`, and `has_embedded_ppt_video`.

- [x] **Step 0.4: Document the frozen contract**

Update `docs/llm-provider-contract.md` with a short section named `Real E2E Acceptance Contract` that lists the required evidence files, final video schema fields, and the rule that only variable names may appear in documentation.

- [x] **Step 0.5: Verify Phase 0**

Run:

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py -q
```

Expected: all smoke-script tests pass.

## Phase 1: Make Partial Real Images Continue To Storyboard

**Objective:** A single failed real image must not stop the demo chain when at least one valid image exists and the caller explicitly requests partial continuation.

**Files:**
- Modify: `scripts/t075_real_fullchain_smoke.py`
- Modify: `apps/api/tests/test_t075_smoke_script.py`
- Verify: `apps/api/app/services.py`
- Verify: `apps/api/tests/test_real_providers.py`

- [x] **Step 1.1: Add smoke-script arguments for partial image continuation**

Add arguments to `parse_args()`:

```python
parser.add_argument("--min-successful-images", type=int, default=1)
parser.add_argument("--allow-partial-assets", action="store_true", default=True)
```

Record both fields in the `evidence` dictionary.

- [x] **Step 1.2: Pass partial image controls to `intro_video_asset/generate`**

Change the node body construction in `run()`:

```python
if node_id == "intro_video_asset":
    body = {
        "image_size": args.image_size,
        "min_successful_images": args.min_successful_images,
        "allow_partial_assets": args.allow_partial_assets,
    }
else:
    body = {}
```

- [x] **Step 1.3: Add a regression test for request payload**

In `apps/api/tests/test_t075_smoke_script.py`, add a test using the existing fake client pattern or monkeypatching around `generate_and_approve` to assert that the request body sent for `intro_video_asset` contains:

```python
{
    "image_size": "1024x1024",
    "min_successful_images": 1,
    "allow_partial_assets": True,
}
```

- [x] **Step 1.4: Verify backend partial continuation still works**

Run:

```powershell
python -m pytest apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met -q
```

Expected: pass.

- [x] **Step 1.5: Verify Phase 1**

Run:

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met -q
```

Expected: pass.

## Phase 2: Add TTS Mode And Audio Evidence To The Smoke Script

**Objective:** The real E2E runner must explicitly record the expected TTS mode and prove that final video audio exists.

**Files:**
- Modify: `scripts/t075_real_fullchain_smoke.py`
- Modify: `apps/api/tests/test_t075_smoke_script.py`
- Verify: `apps/api/tests/test_tts_and_final_video.py`

- [x] **Step 2.1: Add `--tts-provider-mode`**

Add to `parse_args()`:

```python
parser.add_argument("--tts-provider-mode", default="real", choices=["placeholder", "real"])
```

Record it in `evidence["tts_provider_mode"]`.

- [x] **Step 2.2: Fetch final video node content after sync**

After `sync_video_tasks(...)` and before downloading final artifacts, call:

```python
final_video_node = client.request_json("final_video_get", "GET", f"/projects/{project_id}/nodes/final_video")
content = final_video_node.get("content") if isinstance(final_video_node.get("content"), dict) else {}
evidence["node_results"]["final_video"] = summarize_node(final_video_node)
evidence["final_video_node_content"] = sanitize_for_evidence(content)
writer.flush()
```

- [x] **Step 2.3: Add local ffprobe verification**

Add a helper in `scripts/t075_real_fullchain_smoke.py`:

```python
def probe_media(path: Path) -> dict[str, Any]:
    import subprocess

    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {"ok": False, "error": mask_text(completed.stderr.strip())}
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") if isinstance(payload.get("streams"), list) else []
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    return {
        "ok": True,
        "audio_stream_count": len(audio_streams),
        "video_stream_count": len(video_streams),
        "audio_codecs": [stream.get("codec_name") for stream in audio_streams],
    }
```

Call it after `download_final_artifacts(...)` and store `evidence["ffprobe"]`.

- [x] **Step 2.4: Verify TTS/final-video tests**

Run:

```powershell
python -m pytest apps\api\tests\test_tts_and_final_video.py apps\api\tests\test_t075_smoke_script.py -q
```

Expected: pass.

## Phase 3: Complete Real Video Clip Submission, Polling, Download, And Composition

**Objective:** Once storyboard exists, `final_video/generate` must create real video tasks, poll them to completion, download clips, compose `outputs/final_video.mp4`, and expose a verified final schema.

**Files:**
- Verify and modify if needed: `apps/api/app/services.py`
- Verify and modify if needed: `apps/api/app/providers.py`
- Verify and modify if needed: `apps/api/app/video_outputs.py`
- Modify tests if behavior changes: `apps/api/tests/test_real_providers.py`
- Modify tests if behavior changes: `apps/api/tests/test_tts_and_final_video.py`

- [x] **Step 3.1: Confirm task terminal-state semantics**

Inspect `GET /projects/{project_id}/tasks/{task_id}` handling and ensure completed real video tasks include:

```json
{
  "status": "completed",
  "download_status": "downloaded",
  "clip_path": "clips/<shot_id>.mp4",
  "download_path": "clips/<shot_id>.mp4"
}
```

- [x] **Step 3.2: Add a regression for finalization after downloaded clips**

In `apps/api/tests/test_tts_and_final_video.py`, keep or add an assertion that finalization creates:

```python
assert (project_dir / "audio" / "narration.mp3").exists()
assert (project_dir / "audio" / "narration.srt").exists()
assert (project_dir / "outputs" / "concat_manifest.json").exists()
assert (project_dir / "outputs" / "final_video.mp4").exists()
assert content["voice_gender"] == "male"
assert content["voice_language"] == "zh-CN"
assert content["audio_verified"] is True
assert content["english_audio_detected"] is False
```

- [x] **Step 3.3: Ensure failed clips are visible and retryable**

If any real video task fails, the task result must include:

```json
{
  "error_code": "VIDEO_REQUEST_FAILED",
  "retryable": true,
  "response_excerpt": "<redacted provider excerpt>"
}
```

The chain may fail the run, but it must not hide the provider failure or generate fake real clips.

- [x] **Step 3.4: Verify Phase 3 without live spend**

Run:

```powershell
python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_tts_and_final_video.py -q
```

Expected: pass.

## Phase 4: Make PPT Export Depend On The Real Final Video

**Objective:** PPT export must embed the composed final video and fail clearly when no final video exists in real mode.

**Files:**
- Verify and modify if needed: `apps/api/app/services.py`
- Verify and modify if needed: `apps/api/tests/test_ppt_export.py`
- Verify and modify if needed: `scripts/t075_real_fullchain_smoke.py`

- [x] **Step 4.1: Assert PPT media embedding in script checks**

The `has_embedded_ppt_video` check must require:

```python
len((evidence.get("ppt_path") or {}).get("ppt_media_mp4_entries") or []) >= 1
```

- [x] **Step 4.2: Keep real mode strict**

Ensure PPT export does not create a placeholder video when `VIDEO_PROVIDER_MODE=real` and `outputs/final_video.mp4` is missing.

- [x] **Step 4.3: Verify Phase 4**

Run:

```powershell
python -m pytest apps\api\tests\test_ppt_export.py apps\api\tests\test_t075_smoke_script.py -q
```

Expected: pass.

## Phase 5: Run The Real Provider E2E Gate

**Objective:** Perform the first complete real-provider run and capture evidence that can be reviewed without rerunning.

**Files:**
- Read local only: `apps/api/.env`
- Run: `scripts/t075_real_fullchain_smoke.py`
- Output: `docs/qa-audits/t075-real-fullchain-smoke-evidence/<timestamp>/`
- Create report: `docs/qa-audits/2026-06-21-real-e2e-generation-gate.md`

- [x] **Step 5.1: Confirm local environment variables exist without printing values**

Use a local check that prints only variable names and present/missing state:

```powershell
python -c "import os; names=['PROVIDER_MODE','IMAGE_PROVIDER_MODE','VIDEO_PROVIDER_MODE','TTS_PROVIDER_MODE','DEEPSEEK_API_KEY','MINIMAX_API_KEY','MINMAX_API_KEY']; print({name: bool(os.environ.get(name)) for name in names})"
```

Expected: provider modes are configured for the intended run; at least one supported TTS key variable is present for real TTS.

- [x] **Step 5.2: Start the API in real mode**

Use a separate terminal or managed session:

```powershell
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8188
```

Expected: `GET http://127.0.0.1:8188/health` returns ok.

- [x] **Step 5.3: Run the real smoke**

Run:

```powershell
python scripts\t075_real_fullchain_smoke.py `
  --api-base http://127.0.0.1:8188 `
  --provider-mode real `
  --image-provider-mode real `
  --video-provider-mode real `
  --tts-provider-mode real `
  --min-successful-images 1 `
  --task-timeout-sec 1200 `
  --poll-interval-sec 15
```

Expected success: `[t075] ok=True`.

- [x] **Step 5.4: If the run fails, classify by failed step**

Use the generated `provider-error-summary.json`:

```powershell
Get-Content -LiteralPath "docs\qa-audits\t075-real-fullchain-smoke-evidence\<timestamp>\provider-error-summary.json" -Raw
```

Allowed classifications:

- `intro_video_asset_generate`: image provider or partial-continuation bug.
- `storyboard_generate`: upstream content schema or LLM output issue.
- `final_video_generate`: video provider submission issue.
- `sync_video_tasks`: video provider polling or timeout issue.
- `download_final_video`: composition or artifact serving issue.
- `export_ppt`: PPT embedding or artifact path issue.
- `success_checks`: evidence contract issue.

Replace `<timestamp>` with the generated folder name from the smoke output.

- [x] **Step 5.5: Write the gate report**

Create `docs/qa-audits/2026-06-21-real-e2e-generation-gate.md` with these exact sections:

```markdown
# Real E2E Generation Gate

## Verdict

## Environment

## Evidence Directory

## Node Progress

## Media Artifacts

## ffprobe Result

## PPT Verification

## Blocking Issues

## Next Action
```

The report must contain only variable names for secrets.

## Phase 6: Browser Verification For Teacher-Visible Flow

**Current Phase 5 Verdict:** Not accepted yet. Real smoke now reaches `final_video/generate` with `--video-shot-limit 1`; PDF, lesson plan, video script chain, real image, and storyboard pass. The remaining hard blocker is the real video provider returning `429 RESOURCE_EXHAUSTED`, so no clip is downloaded and `final_video.mp4` / PPT are not produced. Phase 6 cannot start until a real clip is successfully downloaded and final artifacts pass the T075 success checks.

**Objective:** Confirm the frontend can show the real-chain progress and artifacts without requiring users to inspect JSON.

**Files:**
- Verify and modify if needed: `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`
- Verify and modify if needed: `apps/web/src/lib/api-client.ts`
- Verify and modify if needed: `apps/web/src/lib/api-mappers.ts`
- Output: browser screenshot under the same gate evidence folder if possible.

- [ ] **Step 6.1: Start the frontend against the real API**

Run:

```powershell
cd apps\web
$env:NEXT_PUBLIC_DEMO_MODE="false"
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8188"
bun run dev
```

Expected: Web loads and can read projects from the real API.

- [ ] **Step 6.2: Verify user-visible final status**

In the project workspace, confirm the user can see:

- Textbook parsing status.
- Lesson plan status.
- Video asset status.
- Storyboard status.
- Final video status.
- Narration/audio status.
- Downloadable final video or PPT artifact.

- [ ] **Step 6.3: Run frontend gates**

Run:

```powershell
cd apps\web
bun run lint
bun run build
```

Expected: both commands pass.

## Phase 7: Stabilize And Operationalize The Chain

**Objective:** Convert a successful local real run into a repeatable engineering capability.

**Files:**
- Modify: `apps/api/README.md`
- Modify: `apps/api/.env.example`
- Modify: `docs/ops-real-provider-demo-runbook.md`
- Modify: `workflow/multi-agent/stage-review.md`
- Modify: `workflow/multi-agent/handoffs/latest.md`

- [ ] **Step 7.1: Update runtime documentation**

Document the real E2E command, required variable names, evidence folder, and failure classification table. Do not include any secret values.

- [ ] **Step 7.2: Add a release gate checklist**

Add a checklist to `docs/ops-real-provider-demo-runbook.md`:

```markdown
## Real E2E Demo Gate

- [ ] API starts in real provider modes.
- [ ] Web points to the real API.
- [ ] T075 smoke returns ok=true.
- [ ] Evidence folder contains images, clips, final_video.mp4, PPT, summary.json, and ffprobe result.
- [ ] Browser shows final video/audio/PPT state.
- [ ] No evidence file contains raw keys.
```

- [ ] **Step 7.3: Update stage records after a successful run**

Update:

- `workflow/multi-agent/stage-review.md`
- `workflow/multi-agent/handoffs/latest.md`

The stage verdict must be one of:

- `通过：本地真实 API 可演示`
- `阻塞：真实 provider 未完成`
- `阻塞：最终合成或 PPT 失败`

## Phase 8: Parallel Prompt Platform GA Track

**Objective:** Finish Prompt platform safely after the real generation chain is no longer blocked.

**Files:**
- Modify: `apps/api/app/prompt_registry.py`
- Modify: `apps/api/app/main.py`
- Add or modify admin API tests under `apps/api/tests/`
- Add frontend admin pages only after backend auth is enforced.

- [ ] **Step 8.1: Keep Prompt platform out of the real E2E critical path**

Do not block the real E2E gate on admin UI, JWT, canary UI, or user-facing Prompt management.

- [ ] **Step 8.2: Finish backend admin boundaries**

Admin Prompt APIs must require backend authorization based on `ADMIN_USERNAMES` or equivalent authenticated admin identity. Frontend hiding is not a security boundary.

- [ ] **Step 8.3: Verify Prompt publishing and rollback**

The backend acceptance test must prove:

```python
assert active_prompt_before != active_prompt_after_publish
assert active_prompt_after_rollback == active_prompt_before
```

The audit log must record publish and rollback actions.

## Execution Order

1. Phase 0-4 are code-level complete for the current single-clip real run path.
2. Provider recovery remains the active blocker: restore video quota, switch account pool, or set `VIDEO_MODEL` to a confirmed available model.
3. Phase 5 real provider run.
4. Phase 6 browser verification.
5. Phase 7 documentation and stage records.
6. Phase 8 Prompt platform GA track.

## Immediate First Batch

Current immediate batch is T095 after provider recovery. Use the existing single-clip command, adding `VIDEO_MODEL` only if the restored provider requires a different model:

```powershell
$env:VIDEO_MODEL="sora-2-12s"
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --image-limit 1 --image-quality low --min-successful-images 1 --video-shot-limit 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

If no alternate model is needed, omit `VIDEO_MODEL`. The batch is complete only when the evidence folder contains a real downloaded clip, TTS audio/SRT, `outputs/final_video.mp4`, ffprobe proof, and PPT.

## Stop Conditions

- Stop and report if a command would print or persist raw provider keys.
- Stop and report if real provider E2E would consume API credits and the user has not approved the live run for the current session.
- Stop and report if the same provider failure recurs across three live attempts with the same failed step and no code/config change between attempts.
- Do not mark the project as real E2E complete until Phase 5 and Phase 6 both pass.
