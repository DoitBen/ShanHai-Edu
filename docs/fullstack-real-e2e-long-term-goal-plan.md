# ShanHaiEdu 真实端到端生成长期执行目标计划

## 目标

把 ShanHaiEdu 从“本地 fake/placeholder 可演示”推进到“本地真实 API 可演示”，最终稳定产出同一项目下的：

- 真实教材解析与知识点 Markdown。
- 真实 LLM 教案与视频脚本链。
- 至少 1 张真实图片资产。
- 至少 1 个真实视频 clip。
- Minimax 中文男声 TTS 旁白音频。
- `outputs/final_video.mp4`，且 `ffprobe` 证明有视频流和音频流。
- 内嵌该 MP4 的 `.pptx`。
- 浏览器工作区能让教师用户看到生成进度、失败原因、最终视频和 PPT 下载入口。

## 当前真实进度

截至 2026-06-22 最新证据：

- `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260622-182434\summary.json`
- `docs\qa-audits\manual-real-e2e-continuation\20260622-182731\summary-brief.json`

已通过：

- PDF 上传。
- 教材解析。
- 教案生成。
- 导入选择。
- 视频脚本。
- 角色字典和视觉契约经人工最小合法种子补齐后 approved。
- 分场剧本。
- 真实生图 1 张。
- storyboard。
- 视频 prompt 已归一化为完整中文旁白、画面、禁止英文配音结构。

未通过：

- T075 自动化脚本首次漏跑 `character_dict` / `visual_contract`，导致 `intro_video_screenplay` 首次卡在 `UPSTREAM_NOT_APPROVED`。
- 共享节点真实 LLM 输出曾缺 `characters`、`palette` 等必填字段，需要默认种子或 schema repair。
- `final_video` 提交真实视频时把参考图公网 URL 放入 JSON `images`，OTU 预处理参考图时拉取该 URL 返回 `HTTP 403`。
- OTU 纯文本 `omni_flash-10s` 对照任务可创建，但最终失败为 `upstream_error`，说明 provider 自身仍可能波动。
- 未下载真实 clip。
- 未触发 Minimax TTS、SRT、concat manifest、ffmpeg 合成。
- 未产出 `outputs/final_video.mp4`。
- 未导出 PPT。
- 未进入浏览器演示封版。

当前裁决：

- 真实端到端尚未打通。
- 主阻塞已从早期配额/账号池问题收窄为视频参考图输入通道和视频 provider 稳定性，不是 PDF、教案、生图、storyboard 或 PPT 接口。
- 真实图片已落本地，但当前视频提交路径让 OTU 服务端通过公网 URL 拉图；该 URL 对 OTU 返回 403，所以必须先把底层设计收敛为本地文件 multipart 上传或稳定对象存储/临时签名 URL。
- 在参考图输入通道未收敛前，不继续盲目跑完整真实视频，以免浪费额度和时间。

## 长期成功门禁

只有满足以下全部条件，才允许宣布“本地真实 API 可演示”：

1. `scripts\t075_real_fullchain_smoke.py` 返回 `ok=true`。
2. 证据目录包含真实图片、真实 clip、`final_video.mp4`、PPT、`summary.json`、`ffprobe` 结果。
3. `ffprobe.audio_stream_count >= 1` 且 `video_stream_count >= 1`。
4. `final_video` 节点内容包含：
   - `voice_gender=male`
   - `voice_language=zh-CN`
   - `audio_verified=true`
   - `english_audio_detected=false`
   - `narration_audio_path`
   - `subtitle_srt_path`
   - `concat_manifest_path`
   - `video_path=outputs/final_video.mp4`
5. PPT 内部存在 `ppt/media/*.mp4`。
6. 浏览器工作区能展示最终视频、音频状态、PPT 下载和失败诊断。
7. 文档、日志、报告和截图不包含真实密钥值。

## 执行阶段

### 阶段 A：当前阻塞收口

目标：不改主流程，先把视频 provider 失败变成可分类、可决策、可复跑的工程状态。

任务：

- 后端补齐视频 provider 错误分类：`RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED` 归类为 `VIDEO_QUOTA_EXHAUSTED`，`retryable=false`。
- 对 `fail_to_fetch_task`、`媒体预处理失败`、参考图 `HTTP 403 下载失败` 单独归类为参考图输入通道失败，例如 `VIDEO_REFERENCE_FETCH_FORBIDDEN`，并在 task/result 中保留脱敏 URL 摘要。
- T075 smoke 在所有真实 clip failed 时停在 `sync_video_tasks`，不误报 `download_final_video`。
- T075 自动化脚本必须先生成/确认共享前置节点 `character_dict` 和 `visual_contract`，再进入 `intro_video_screenplay`、`intro_video_asset`、`storyboard`。
- `character_dict` / `visual_contract` 需要默认种子或 schema repair，避免真实 LLM 缺必填字段后阻塞视频链路。
- 运维检查视频 provider 账号额度、模型权限、账号池、可用模型和 base URL，不打印密钥。
- 更新真实 E2E gate 报告，明确“代码可继续，外部 provider 未恢复”。

阶段出口：

- 代码测试通过。
- 运行手册能指导切换可用 provider 或账号池。
- 同类配额错误不再需要人工翻 `tasks.json` 才能判断。
- T075 证据目录自动包含 `video_provider_readiness`，测试工程师可直接从 `summary.json`/证据 JSON 判断下一步是复跑、切模型还是恢复账号额度。
- T075 证据目录能区分“参考图输入 403”和“completed MP4 下载 403”。

### 阶段 B：单 clip 真实打通

目标：用最低成本先跑通 1 个真实视频 clip。

参考图传输设计：

- 生图完成后以 `<project_dir>\assets\generated_images\*.png` 本地文件作为视频参考图的主输入。
- 后端提交 OTU 时默认使用 `multipart/form-data`，字段名 `input_reference`，直接上传本地图片字节。
- JSON `images: ["https://..."]` 只作为降级路径，前提是该 URL 已通过非本机网络无鉴权 GET 验证。
- 如果使用对象存储或临时签名 URL，签名必须允许 OTU 服务端直接下载，且证据中记录过期时间、HTTP 状态和脱敏 URL 摘要。
- task/result 需要记录 `reference_submission_mode=multipart|url`、`reference_image_ids`、`reference_image_paths`，避免排障时只看到 provider 400。

固定参数：

```powershell
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --image-limit 1 --image-quality low --min-successful-images 1 --video-shot-limit 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

如果当前视频模型额度耗尽，可先在环境中切换候选模型，再复跑同一命令：

```powershell
$env:VIDEO_MODEL="sora-2-12s"
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --image-limit 1 --image-quality low --min-successful-images 1 --video-shot-limit 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

优先级：命令行 `--video-model` 高于 `VIDEO_MODEL`，`VIDEO_MODEL` 高于 `OMNI_DEFAULT_MODEL` / `NEWAPI_DEFAULT_MODEL`，最后 fallback 到 `omni_flash-10s`。

阶段出口：

- 真实 clip 下载到 `clips\*.mp4`。
- `final_video/generate` 不再停在视频 provider。
- 若失败，失败码必须是可分类码，而不是黑盒 `unknown`。
- 若失败发生在参考图输入阶段，错误码必须指向参考图 fetch/upload，而不是泛化为模型生成失败。

### 阶段 C：真实 TTS 与 final video 合成

目标：真实 clip 下载后自动进入 Minimax TTS、SRT、concat manifest、ffmpeg 合成。

验收：

- `audio\narration.mp3` 存在。
- `audio\narration.srt` 存在。
- `outputs\concat_manifest.json` 存在。
- `outputs\final_video.mp4` 存在。
- `ffprobe` 证明有音频流。
- 合成前丢弃或静音视频原声，统一叠加中文男声旁白。

阶段出口：

- T075 的 final video schema 全部通过。
- 不允许用 placeholder 冒充真实 final video。

### 阶段 D：PPT 交付闭环

目标：PPT 导出必须复用同一个真实 `outputs\final_video.mp4`。

验收：

- `POST /projects/{id}/export/ppt` 成功。
- 下载的 `.pptx` 内存在 `ppt/media/*.mp4`。
- PPT 内嵌 MP4 与项目 final video 同源。
- 真实模式缺 final video 时，PPT 导出必须明确失败，不自动生成占位视频。

### 阶段 E：浏览器可演示

目标：教师用户无需看 JSON，也能理解当前进度和最终产物。

验收：

- Web 指向真实 API。
- 工作区可见教材解析、教案、视频资产、storyboard、final video、音频和 PPT 状态。
- provider 失败时展示可读、脱敏、可重试或需运维处理的原因。
- 浏览器控制台无应用级阻断错误。
- 前端 `tsc/lint/build` 通过。

### 阶段 F：稳定化与可复跑

目标：把一次成功变成团队可重复执行的能力。

任务：

- 固化真实 E2E demo runbook。
- 固化 `.env.example` 变量名和本地 `.env` 忽略规则。
- 保存证据目录、截图、ffprobe、PPT 路径。
- 建立失败分类表：生图失败、视频配额、视频下载、TTS、ffmpeg、PPT、浏览器展示。
- 明确回退策略：真实 provider 不可用时只允许回退到“本地 placeholder 演示”，不得标记为真实 E2E 通过。

## 测试策略

原则：

- 新行为先写测试，再实现。
- 两个阶段形成一个批次后集中跑目标测试；阻塞修复允许小红绿测试。
- 真实 provider 调用只在配置和代码门禁通过后执行。

最小目标测试：

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py -q
python -m pytest apps\api\tests\test_real_providers.py::test_sync_task_composes_final_video_after_single_real_clip_when_limited -q
python -m pytest apps\api\tests\test_tts_and_final_video.py -q
python -m pytest apps\api\tests\test_ppt_export.py -q
```

真实 E2E 通过后再跑：

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

## 角色分工

### 全栈工程师

- 维护本计划、真实 E2E gate、跨前后端接口闭环。
- 只在主链路阻塞时直接修代码。
- 每轮结束更新 `workflow\multi-agent\handoffs\latest.md` 和 `stage-review.md`。

### 后端工程师

- 负责 provider adapter、task 状态、final video 合成、PPT 导出和错误分类。
- 禁止把 placeholder 结果标记为真实结果。
- 所有 provider 错误必须脱敏、可分类、可落库。

### 前端工程师

- 负责真实 API 模式下的工作区状态可见性、下载入口、错误展示。
- 不阻塞当前主线做大 UI 重构。
- final video 成功前不宣称演示封版。

### 测试工程师

- 只围绕新增能力和历史阻塞点复测。
- 测试报告必须包含证据目录、路径、ffprobe、浏览器截图和缺陷分级。
- 不用 fake/placeholder 证据替代真实 E2E 证据。

### 运维/部署工程师

- 负责真实 provider 环境变量、账号额度、模型权限、ffmpeg、storage、运行手册。
- 不打印、不提交、不写入文档真实密钥。
- provider 配额恢复后通知后端/测试复跑 T075。

## 暂缓事项

以下事项有价值，但不进入当前真实 E2E 主阻塞：

- Prompt 管理后台完整 GA。
- 管理员 UI 和 JWT 后台。
- Cloud Run 正式部署。
- 多用户权限体系。
- 视频质量精修、多 clip 美术一致性。
- 大规模项目列表性能优化。

这些事项在 `final_video.mp4 + PPT` 真实本地门禁通过后再排期。

## 下一步

1. 已完成代码级前置：`VIDEO_QUOTA_EXHAUSTED` 错误分类、T075 readiness 证据、独立 `video-provider-readiness.json`、脚本与后端 API 默认视频模型配置化。
2. 运维确认视频 provider 可用额度、账号池或替代模型；如需切模型，优先设置 `VIDEO_MODEL`，无需改代码。
3. provider 可用后，测试执行单 clip 真实 T075。
4. 单 clip 通过后，进入 TTS、合成、PPT、浏览器封版。
