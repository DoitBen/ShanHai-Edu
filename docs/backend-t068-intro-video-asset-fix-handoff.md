# T068 intro_video_asset/generate 阻塞修复后端交接

## 结论

T068 已修复 T063 在 `intro_video_asset/generate` 的真实链路阻塞：真实 LLM 空响应、非 JSON、缺 `assets` 字段时不再漏出 `GENERATION_INPUT_INVALID + JSONDecodeError`，而是返回节点级、脱敏、可诊断的 `ProviderError`，并写入 `intro_video_asset` failed 节点和 errors log。合法资产 JSON 仍会继续进入 T064 的 `image_generation` task 创建和图片下载路径。

本轮不宣布 T063 通过；需要测试工程师按 T069 重跑真实 E2E。

## 修改文件

- `apps\api\app\providers.py`
- `apps\api\app\services.py`
- `apps\api\tests\test_real_providers.py`
- `docs\backend-t068-intro-video-asset-fix-handoff.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`
- `workflow\multi-agent\roles\backend-engineer.md`

## 修复前行为

- `intro_video_asset/generate` 先执行真实 LLM 资产 JSON 生成。
- LLM 空响应或非 JSON 时，异常可能以 `ValueError` / JSONDecodeError 原文形式冒出。
- API 返回 `400 / GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)`。
- 节点不落 failed 版本。
- 不创建 `image_generation` task。
- 后续 storyboard、真实视频、final_video、PPT 全部阻塞。

## 修复后行为

- LLM 空响应：
  - 返回 `502 / INTRO_VIDEO_ASSET_JSON_EMPTY`
  - 写入 `intro_video_asset` failed 节点
  - 写入 errors log
- LLM 非 JSON：
  - 返回 `502 / INTRO_VIDEO_ASSET_JSON_INVALID`
  - 响应和日志只保留脱敏摘要，不包含 API key、Bearer token 或完整上游响应
- LLM JSON 缺字段：
  - 返回 `502 / INTRO_VIDEO_ASSET_SCHEMA_INVALID`
  - message 明确指出缺 `assets` 或 asset 子字段
- LLM JSON 合法：
  - 继续进入 `_generate_image_tasks()`
  - `IMAGE_PROVIDER_MODE=real` 时创建 `image_generation` task
  - 图片成功下载到 `assets/generated_images/{asset_id}.png`
  - task 顶层继续保留 T064 字段：`provider_task_id`、`image_path`、`status`、`error_code`、`retryable`

## 测试

- T068 目标测试：
  - `python -m pytest apps\api\tests\test_real_providers.py::test_intro_video_asset_empty_llm_response_returns_diagnostic_provider_error apps\api\tests\test_real_providers.py::test_intro_video_asset_non_json_llm_response_returns_diagnostic_provider_error apps\api\tests\test_real_providers.py::test_intro_video_asset_missing_assets_returns_schema_error apps\api\tests\test_real_providers.py::test_intro_video_asset_valid_llm_json_continues_to_image_generation_tasks -q`
  - 结果：`4 passed`
- T064 回归：
  - `python -m pytest apps\api\tests\test_real_providers.py::test_real_image_provider_success_persists_task_and_downloadable_path apps\api\tests\test_real_providers.py::test_real_image_provider_failure_persists_failed_task_node_error_and_redacts apps\api\tests\test_real_providers.py::test_retry_image_task_resubmits_single_image_and_updates_task apps\api\tests\test_real_providers.py::test_retry_video_clip_task_resubmits_single_clip apps\api\tests\test_real_providers.py::test_download_image_returns_only_project_generated_images apps\api\tests\test_real_providers.py::test_download_final_video_returns_readable_error_when_missing -q`
  - 结果：`6 passed`
- 真实 provider 契约：
  - `python -m pytest apps\api\tests\test_real_providers.py -q`
  - 结果：`37 passed`
- 后端全量：
  - `python -m pytest apps\api\tests -q`
  - 结果：`69 passed, 2 xfailed`

## T069 复测建议

需要测试工程师重跑 T063 真实链路，至少确认：

- `intro_video_asset/generate` 不再返回 `GENERATION_INPUT_INVALID / Expecting value` 黑盒错误。
- 真实 LLM 合法输出后创建 `image_generation` task。
- 真实图片落盘到 `assets/generated_images\*.png`。
- 后续 storyboard、真实视频 clip、clip 下载、`outputs/final_video.mp4`、PPT 导出继续执行。
- 若真实 LLM 仍返回空/非 JSON，测试报告应记录新的 `INTRO_VIDEO_ASSET_*` 错误码和 failed 节点证据，而不是判为未知黑盒。
