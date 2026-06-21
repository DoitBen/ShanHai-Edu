# Real E2E Generation Gate

## Verdict

阻塞：真实 provider 完整门禁已多轮执行，链路已从早期 `intro_video_asset_generate` 阶段推进到真实视频 provider 阶段，但仍未产出 `outputs/final_video.mp4` 和 PPT。

最新结论：本地代码链路已跑通到 `storyboard=approved` 并成功提交 1 个真实视频 clip 任务；该视频任务最终返回 `429 RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED`，未下载 clip，因而未触发 Minimax TTS、ffmpeg 合成、ffprobe 和 PPT 导出。

当前不能宣布“真实端到端已打通”，但可以明确：PDF、教材解析、教案、导入选择、视频脚本、分场剧本、真实生图、storyboard 这几段已越过；剩余硬阻塞在视频 provider 配额/可用性。

## Environment

- API：`http://127.0.0.1:8199`（本轮临时实例，已停止）。
- Provider：`PROVIDER_MODE=real`。
- Image Provider：`IMAGE_PROVIDER_MODE=real`。
- Video Provider：`VIDEO_PROVIDER_MODE=real`。
- TTS Provider：`TTS_PROVIDER_MODE=real`。
- Fixture PDF：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`。
- 执行参数：`--image-limit 1`、`--image-quality low`、`--min-successful-images 1`、`--video-shot-limit 1`。
- 密钥安全：报告只记录变量名，不记录真实值。

## Evidence Directory

最新证据目录：

`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-214857`

关键历史证据：

- `20260621-205104`：首次真实 smoke，卡在 `intro_video_asset_generate` 超时，并暴露 SQLite 长事务锁。
- `20260621-212611`：修复锁和 base64 context 后，越过 storyboard，6 个视频任务中 1 个完成、其余失败/配额不足，未合成 final video。
- `20260621-213757`：降为 1 个视频任务后，唯一视频任务 provider 失败，未下载 clip。
- `20260621-214857`：修复弱 storyboard prompt 后，唯一视频任务 prompt 已合格，但 provider 返回 `429 RESOURCE_EXHAUSTED`。

## Node Progress

最新真实运行进度：

| Node | Status | Evidence |
| --- | --- | --- |
| `textbook_parse` | `approved` | `summary.json` |
| `lesson_plan` | `approved` | `summary.json` |
| `intro_selection` | `approved` | `summary.json` |
| `intro_video_script` | `approved` | `summary.json` |
| `intro_video_screenplay` | `approved` | `summary.json` |
| `intro_video_asset` | `approved`，1 张真实图片落盘 | `generated-image-paths.json` / `tasks.json` |
| `storyboard` | `approved`，视频 prompt 已归一化 | `summary.json` / `tasks.json` |
| `final_video` | `running` 后因唯一视频 task failed 未产物 | `tasks.json` |

## Media Artifacts

最新真实运行产物：

- 真实图片：1 张，`images\asset_001.png`，约 1.4 MB。
- 真实视频 clip：无，唯一 `video_clip_generation` task 为 failed。
- 旁白音频：无，未进入合成阶段。
- SRT：无，未进入合成阶段。
- concat manifest：无，未进入合成阶段。
- `final_video.mp4`：无。
- PPT：无。

## ffprobe Result

未进入 final video 阶段，`summary.json.ffprobe` 为空：

```json
{
  "ok": null,
  "audio_stream_count": null,
  "video_stream_count": null,
  "audio_codecs": []
}
```

## PPT Verification

未进入 PPT 导出阶段：

- PPT 是否下载成功：否。
- 是否包含 `ppt/media/*.mp4`：否。
- 嵌入视频条目：无。

## Blocking Issues

已修复的本地代码问题：

- SQLite 长事务锁：真实生图慢调用期间 `image_generation` task 创建后未提交，导致超时后 `manifest/tasks` 读接口 500。已改为 task 创建、成功、失败后及时 `conn.commit()`。
- LLM context 大字段污染：`intro_video_asset` 中 `data:image/png;base64,...` 和 `b64_json` 会进入 storyboard prompt，导致 DeepSeek 请求体过大/远端断连。已新增 LLM prompt context 清洗，只对 LLM 输入去除大字段，不改节点落库内容。
- 视频配额安全演示：`final_video/generate` 新增 `video_shot_limit/clip_limit`，T075 默认 `--video-shot-limit 1`，支持单真实 clip 合成路径。
- 弱 storyboard prompt：真实 LLM 可能返回极短 `model_prompt` 和数字 `shot_id`。已归一化为 `shot_01`，并在 prompt 缺少“旁白/画面/禁止英文配音”结构时自动补齐完整视频 prompt。

当前剩余阻塞：

- 唯一视频任务 `task_42ba428e8774` 提交并轮询完成后返回 failed。
- provider 错误为 `429 RESOURCE_EXHAUSTED`，原因 `PUBLIC_ERROR_USER_QUOTA_REACHED`。
- 因没有任何 completed/downloaded video clip，后端正确未生成 `outputs/final_video.mp4`，未伪造真实成片。

## Verification

本轮已通过的代码级验证：

- `python -m pytest apps\api\tests\test_t075_smoke_script.py -q`：`11 passed`。
- `python -m pytest apps\api\tests\test_real_providers.py::test_storyboard_prompt_omits_large_data_image_payloads_but_keeps_asset_refs apps\api\tests\test_real_providers.py::test_storyboard_normalization_expands_weak_model_prompt_for_video_provider apps\api\tests\test_real_providers.py::test_real_video_generate_respects_video_shot_limit_for_quota_safe_demo apps\api\tests\test_real_providers.py::test_sync_task_composes_final_video_after_single_real_clip_when_limited apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met apps\api\tests\test_real_providers.py::test_image_task_is_committed_before_slow_real_image_provider_call -q`：`6 passed`。

## Next Action

1. 运维/后端先处理视频 provider 配额或切换可用视频模型/账号池；当前代码侧不应继续盲目消耗真实视频额度。
2. provider 恢复后，直接复跑：

```powershell
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --video-shot-limit 1 --min-successful-images 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

3. 若单 clip 成功下载，后端应自动进入 Minimax TTS、SRT、concat manifest、ffmpeg 合成、`final_video.mp4`、PPT 导出和 ffprobe 验证。
4. 只有 T075 返回 `ok=True` 且证据包含真实图片、真实 clip、`final_video.mp4`、PPT、音频流和 final_video schema 后，才能进入 Phase 6 浏览器验证。
