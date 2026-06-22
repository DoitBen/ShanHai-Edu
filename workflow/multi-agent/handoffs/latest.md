# 最新角色交接记录

## 【本轮】全栈架构师 — T102 architecture-optimization-v2 第0周 PPT 主链路

### 本轮目标

按 `docs\architecture-optimization-v2.md` 第 0 周裁决接通真实 PPT 主链路：后端运行时 manifest 必须包含视觉契约、角色字典和 PPT 线节点；前端真实 API 工作区必须可见；`pptx_artifact/generate` 必须生成可下载 PPTX artifact；不提前接 `final_delivery`。

### 已完成事项

- 新增 `apps\api\tests\test_ppt_runtime_contract.py` 覆盖新项目 manifest、PPT 分支 generate/edit/approve、PPTX artifact 下载和 `final_delivery` 缺席。
- `apps\api\app\workflow_config.py` 将 `visual_contract`、`character_dict`、`ppt_assembly_plan`、`ppt_page_script`、`ppt_visual_asset`、`pptx_artifact` 纳入运行时节点与依赖图。
- `apps\api\app\providers.py` 为新增节点补齐合法 fake 内容。
- `apps\api\app\services.py` 为 `pptx_artifact` 增加 artifact 分支，复用 `export_project_ppt()` 并写入节点版本。
- `apps\web\src\lib\api-mappers.ts` 补齐真实 API 模式下的 PPT 节点映射，工作区显示 16 个后端 manifest 节点。
- 已读取仓库 Issues：`gh issue list --state all --limit 200` 返回空列表；`git fetch --prune origin` 后 `origin/main` 未领先本地。

### 验证证据

```powershell
python -m pytest apps\api\tests -q
```

结果：`131 passed, 2 xfailed`。

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

结果：三项均通过。

浏览器 smoke：

- API：`http://127.0.0.1:8123`，fake/placeholder provider，临时 storage 位于用户临时目录。
- Web：`http://127.0.0.1:3123`，`NEXT_PUBLIC_DEMO_MODE=false`。
- 工作区显示：`16 个后端 manifest 节点`。
- 新增节点可见：`视觉契约`、`角色字典`、`PPT 总装方案`、`PPT 页面脚本`、`PPT 视觉资产`、`PPTX 生成`。
- 浏览器 console `error/warn` 为空。

### 当前状态

- `architecture-optimization-v2.md` 第 0 周 PPT 主链路已达到内测验收口径。
- 第 0 周不代表 StateEngine、RuleExecutor、Flywheel、安全边界或最终交付门禁完成。
- 下一阶段必须进入 StateEngine，仍需按同一流程先读 Issues、修缺陷、拆任务、开发、全流程测试、提交并推送。

### 已更新文件

- `apps\api\app\workflow_config.py`
- `apps\api\app\providers.py`
- `apps\api\app\services.py`
- `apps\api\tests\test_ppt_runtime_contract.py`
- `apps\api\tests\test_ppt_export.py`
- `apps\api\tests\test_video_demo_contract.py`
- `apps\api\tests\test_fullchain_e2e_contract.py`
- `apps\api\tests\test_mvp_api.py`
- `apps\api\tests\test_real_providers.py`
- `apps\web\src\lib\api-mappers.ts`
- `docs\superpowers\plans\2026-06-22-ppt-mainline-phase0.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\decisions.md`
- `workflow\multi-agent\handoffs\latest.md`

### 下个角色需要知道的上下文

- StateEngine 是下一阶段，不能跳到 RuleExecutor/Flywheel/安全边界。
- 当前 `ProjectStore.approve_node()` 仍是直接改状态，StateEngine 阶段应接管 generate/edit/approve/redo/skip、transition log 和 cascade invalidate。

## 【本轮】全栈工程师 — T101 后端 API 视频模型可配置化

### 本轮目标

继续推进真实端到端长期目标。T098 已让 T075 smoke 支持 `VIDEO_MODEL`，但后端 API 直连路径仍默认硬编码 `omni_flash-10s`，会导致前端或接口直接触发 `final_video/generate` 时无法跟随模型切换。

### 已完成事项

- `apps\api\app\settings.py` 新增 `video_model` 配置。
- 默认模型优先级统一为：`VIDEO_MODEL` > `OMNI_DEFAULT_MODEL` > `NEWAPI_DEFAULT_MODEL` > `omni_flash-10s`。
- `WorkflowService` 生成视频 clip 和 retry 视频 clip 时统一使用配置默认模型。
- 请求体显式传入 `model` 时仍优先于默认配置。
- `apps\api\.env.example` 新增 `VIDEO_MODEL` 占位变量。
- `docs\ops-real-provider-demo-runbook.md`、`docs\fullstack-real-e2e-long-term-goal-plan.md`、`dispatch.md`、`stage-review.md` 已同步更新。

### 验证证据

先红灯：

```powershell
python -m pytest apps\api\tests\test_real_providers.py::test_real_video_generate_uses_configured_default_video_model apps\api\tests\test_real_providers.py::test_real_video_generate_request_model_overrides_configured_default -q
```

结果：`1 failed, 1 passed`，失败点为后端默认仍提交 `omni_flash-10s`。

修复后目标批次：

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_video_provider_readiness.py apps\api\tests\test_real_providers.py::test_settings_video_model_prefers_video_model_then_legacy_defaults apps\api\tests\test_real_providers.py::test_real_video_generate_uses_configured_default_video_model apps\api\tests\test_real_providers.py::test_real_video_generate_request_model_overrides_configured_default apps\api\tests\test_real_providers.py::test_real_video_submit_creates_tasks_for_all_storyboard_shots_and_uses_reference_urls apps\api\tests\test_real_providers.py::test_octo_video_provider_classifies_quota_exhausted_query_failure apps\api\tests\test_real_providers.py::test_sync_task_persists_video_quota_exhausted_error_code -q
```

结果：`24 passed`。

### 当前状态

- T075 脚本和后端 API 的视频模型切换口径已经一致。
- provider 恢复后，运维/测试可设置 `VIDEO_MODEL` 切候选模型，不需要改代码。
- 真实 E2E 仍未完成：外部视频 provider 额度/账号池/模型权限仍是主阻塞。
- 下一步仍是 T095：外部 provider 恢复后执行单 clip 真实复跑。

## 【本轮】全栈工程师 — T100 T075 readiness 独立证据文件

### 本轮目标

继续推进真实端到端证据闭环。T099 已让 `summary.json` 内包含 `video_provider_readiness`，本轮进一步固定输出独立 `video-provider-readiness.json`，避免测试/运维每次打开大体积 summary。

### 已完成事项

- `scripts\t075_real_fullchain_smoke.py` 的 `EvidenceWriter.flush()` 固定写出：
  - `video-provider-readiness.json`
- `apps\api\tests\test_t075_smoke_script.py` 新增测试：
  - `test_t075_evidence_writer_flushes_video_provider_readiness_file`
- 更新 `dispatch.md` 和 `stage-review.md`，新增 T100 并标记完成。

### 验证证据

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_video_provider_readiness.py apps\api\tests\test_real_providers.py::test_octo_video_provider_classifies_quota_exhausted_query_failure apps\api\tests\test_real_providers.py::test_sync_task_persists_video_quota_exhausted_error_code -q
```

结果：`20 passed`。

### 当前状态

- T075 证据目录现在固定包含 `video-provider-readiness.json`。
- 真实 E2E 仍未完成，外部视频 provider 额度/账号池/模型可用性仍是阻塞。
- 下一步仍是 T095，在 provider 恢复后执行单 clip 真实复跑。

## 【本轮】全栈工程师 — T099 T075 视频 readiness 证据增强

### 本轮目标

继续推进真实端到端目标，增强 T075 真实 smoke 证据链：当真实视频任务全部 failed 且没有任何 downloaded clip 时，证据中自动带上视频 provider readiness 结论，测试和运维不用再手工拼接 T094 检查结果。

### 已完成事项

- `scripts\t075_real_fullchain_smoke.py` 复用 `app.video_provider_readiness.build_video_provider_readiness_report`。
- `sync_video_tasks` 在所有真实 clip failed 时，除 `video_task_failure_summary` 外，还写入 `video_provider_readiness`。
- T075 证据中的 `VIDEO_QUOTA_EXHAUSTED` 会给出 `next_action=restore_video_provider_quota_or_switch_account_pool`。
- 处理了脚本进程与 API 服务进程环境不同的问题：视频任务既然已由服务端提交，T075 证据不因脚本进程未持有 `OCTO_API_KEY` 而误报缺 key。
- 更新 `docs\fullstack-real-e2e-long-term-goal-plan.md`、`dispatch.md` 和 `stage-review.md`。

### 验证证据

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_video_provider_readiness.py apps\api\tests\test_real_providers.py::test_octo_video_provider_classifies_quota_exhausted_query_failure apps\api\tests\test_real_providers.py::test_sync_task_persists_video_quota_exhausted_error_code -q
```

结果：`19 passed`。

### 当前状态

- T099 证据链增强完成。
- 真实 E2E 仍未完成：外部视频 provider 额度/账号池/模型可用性未恢复。
- 下一步仍是 T095：provider 恢复后执行单 clip 真实复跑。

## 【本轮】全栈工程师 — T098 T075 视频模型可配置化

### 本轮目标

继续推进真实端到端目标，在外部视频 provider 额度恢复前，先补齐 T095 复跑可操作性：视频模型不再只能用脚本硬编码默认值，允许运维/测试通过环境变量切换候选模型。

### 已完成事项

- `scripts\t075_real_fullchain_smoke.py` 新增 `default_video_model_from_env()`。
- T075 默认视频模型优先级调整为：
  1. 命令行 `--video-model`
  2. `VIDEO_MODEL`
  3. `OMNI_DEFAULT_MODEL` / `NEWAPI_DEFAULT_MODEL`
  4. `omni_flash-10s`
- 新增测试：
  - `test_t075_parse_args_uses_video_model_environment_default`
  - `test_t075_parse_args_cli_video_model_overrides_environment`
- 更新 `docs\fullstack-real-e2e-long-term-goal-plan.md` 和 `docs\ops-real-provider-demo-runbook.md`，写入候选模型切换示例。
- 更新 `dispatch.md` 和 `stage-review.md`，新增 T098 并标记完成。

### 验证证据

```powershell
python -m pytest apps\api\tests\test_t075_smoke_script.py::test_t075_parse_args_uses_video_model_environment_default apps\api\tests\test_t075_smoke_script.py::test_t075_parse_args_cli_video_model_overrides_environment apps\api\tests\test_t075_smoke_script.py -q
```

结果：`14 passed`。

### 当前状态

- T075 单 clip 复跑现在可以通过 `$env:VIDEO_MODEL="sora-2-12s"` 这类方式切候选模型。
- 外部 provider 配额/账号池仍未恢复，真实 E2E 仍未打通。
- 下一步仍是 T094 外部恢复后执行 T095。

## 【本轮】全栈工程师/运维辅助 — T094 视频 provider 脱敏就绪检查

### 本轮目标

继续推进真实端到端生成目标，在不打印密钥、不消耗真实视频额度的前提下，完成视频 provider 可用性前置检查，并把当前阻塞归因到配置层还是外部 provider 层。

### 已完成事项

- 新增 `apps\api\app\video_provider_readiness.py`：构建视频 provider readiness 报告。
- 新增 `scripts\check_video_provider_readiness.py`：命令行脱敏检查工具。
- 新增 `apps\api\tests\test_video_provider_readiness.py`：覆盖密钥脱敏、real 模式缺 key 阻断、`VIDEO_QUOTA_EXHAUSTED` 运维阻塞归因。
- 更新 `docs\ops-real-provider-demo-runbook.md`：新增“视频 provider 脱敏就绪检查”章节。
- 更新 `dispatch.md` 和 `stage-review.md`：T094 标记为外部 provider 额度阻塞。

### 验证证据

测试：

```powershell
python -m pytest apps\api\tests\test_video_provider_readiness.py -q
```

结果：`3 passed`。

脱敏本地检查：

```powershell
python scripts\check_video_provider_readiness.py --require-real --provider-error-code VIDEO_QUOTA_EXHAUSTED
```

结果摘要：

- `ok=false`。
- `VIDEO_PROVIDER_MODE=real` 已生效。
- `OCTO_API_KEY` 存在，输出为 `<redacted>`。
- `OCTO_BASE_URL=https://otuapi.com`。
- `VIDEO_MODEL=omni_flash-10s`。
- `blocking_issues=["VIDEO_QUOTA_EXHAUSTED"]`。
- `next_action=restore_video_provider_quota_or_switch_account_pool`。

### 当前裁决

- 本地配置层可见，不是“没有启用 real 模式”或“密钥未注入”的问题。
- 当前仍不能进入 T095 真实 E2E 复跑，因为外部视频 provider 额度、账号池或模型权限未恢复。
- 不允许继续盲目 live 重跑真实视频。

### 下一棒建议

运维/部署工程师需要在外部 provider 侧处理以下任一项：

1. 恢复当前账号额度。
2. 切换到有额度的账号池。
3. 确认可用视频模型并更新运行环境。
4. 若上游不可用，明确记录外部 provider 阻塞，并暂缓 T095。

## 【本轮】全栈工程师/后端热修 — T093 视频 provider 配额错误分类

### 本轮目标

继续推进真实端到端目标，优先处理当前真实 smoke 暴露的代码级诊断缺口：视频 provider 返回配额耗尽时，任务 `error_code` 为空且错误日志仍写旧 `OCTO_TASK_FAILED`。

### 根因

最新证据 `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-214857\tasks.json` 中已包含 `RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED`，但 `OctoVideoProvider.query_task` 只返回 `error_message`，没有返回 `error_code/retryable`；`sync_task` 对 failed 远端任务固定记录 `OCTO_TASK_FAILED`，导致 T075 和任务接口不能准确区分“账号配额阻塞”和普通失败。

### 已完成事项

- 新增 provider 层测试：视频 query 返回配额耗尽时必须归类为 `VIDEO_QUOTA_EXHAUSTED`，`retryable=false`。
- 新增 service 层测试：`sync_task` 必须把 `VIDEO_QUOTA_EXHAUSTED` 写入 task 顶层、result 和 `errors.log`。
- 修改 `apps\api\app\providers.py`：`OctoVideoProvider.query_task` 返回 `error_code`、`retryable`、脱敏 `response_excerpt`，并从 error details 中抽取 `PUBLIC_ERROR_USER_QUOTA_REACHED`。
- 修改 `apps\api\app\services.py`：failed 远端视频任务按 provider 返回的错误码记录，不再统一写 `OCTO_TASK_FAILED`。
- 附带修复 `apps\api\app\video_outputs.py`：ffmpeg stderr 显式 `utf-8/errors=replace` 解码，并兜底 `UnicodeDecodeError` 为可诊断 `RuntimeError`。

### 验证证据

新增测试先红后绿。

目标批次：

```powershell
python -m pytest apps\api\tests\test_tts_and_final_video.py::test_compose_final_video_reports_ffmpeg_decode_errors_as_runtime_error apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_real_providers.py::test_octo_video_provider_classifies_quota_exhausted_query_failure apps\api\tests\test_real_providers.py::test_sync_task_persists_video_quota_exhausted_error_code apps\api\tests\test_real_providers.py::test_sync_task_queries_octo_and_downloads_completed_clip apps\api\tests\test_real_providers.py::test_sync_task_keeps_completed_status_when_download_fails apps\api\tests\test_real_providers.py::test_sync_task_composes_final_video_after_single_real_clip_when_limited -q
```

结果：`18 passed`。

### 当前状态

- T093 代码级修复通过。
- 真实端到端仍未通过，因为视频 provider 额度/账号池/模型可用性还未恢复。
- 不能进入产品演示录屏。

### 下一棒建议

1. 运维/部署工程师接 T094：检查视频 provider 额度、账号池、模型权限、base URL、模型名和本机网络，只输出变量名和状态，不输出密钥。
2. T094 明确可用 provider 后，测试工程师接 T095：复跑单 clip 真实 T075，验收真实 clip、TTS、`final_video.mp4`、PPT 和 ffprobe。

## 【本轮】全栈工程师 — 真实端到端长期目标计划与主线调度收口

### 本轮目标

用户要求全栈工程师接手项目，基于“真实端到端生成”目标构建一个长期执行计划，并继续围绕 `final_video.mp4 + PPT` 主线推进。

### 已完成事项

- 核对最新真实 E2E 状态：当前不是 PDF、教案、生图、storyboard 或 PPT 接口阻塞，而是视频 provider 返回 `429 RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED`。
- 新增长期执行目标计划：`docs\fullstack-real-e2e-long-term-goal-plan.md`。
- 在 `workflow\multi-agent\dispatch.md` 新增 T092-T097：
  - T092 长期目标计划。
  - T093 后端视频 provider 错误分类。
  - T094 运维恢复视频 provider 可用性。
  - T095 测试单 clip 真实 E2E 复跑。
  - T096 前端真实最终产物浏览器封版。
  - T097 全栈/架构最终阶段裁决。
- 更新 `workflow\multi-agent\stage-review.md`，明确“目标计划通过，但真实 E2E 仍阻塞”。

### 当前真实进度

- 已通过：PDF 上传、教材解析、教案、导入选择、视频脚本、分场剧本、真实生图 1 张、storyboard。
- 已有证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-214857`。
- 当前硬阻塞：唯一 `video_clip_generation` task 返回视频 provider 配额错误。
- 未产出：真实 clip、Minimax TTS 旁白、SRT、concat manifest、`outputs/final_video.mp4`、ffprobe、PPT。

### 关键裁决

- 不能宣布“真实端到端已打通”。
- 不能进入产品演示录屏。
- 不能继续把主线资源投入 Prompt 管理后台、UI 大重构或 PDF/PPT 重复修复。
- 下一步只围绕视频 provider 可用性和错误分类推进；provider 恢复后立即复跑单 clip 真实 E2E。

### 下一棒建议

1. 后端工程师接 T093：TDD 修复 `VIDEO_QUOTA_EXHAUSTED` 分类与 `sync_task` 结果落库。
2. 运维/部署工程师并行接 T094：检查视频 provider 额度、模型权限、账号池、base URL、模型名和网络，不打印密钥。
3. T093/T094 完成后，测试工程师接 T095：执行单 clip 真实 T075，验收真实 clip、TTS、final video、PPT。
4. T095 通过后，前端工程师接 T096：浏览器封版展示。

### 下个角色需要知道的上下文

- 当前真实 E2E 最新失败不能再被描述为 `download_final_video` 的业务问题，本质是视频 provider 配额导致没有任何真实 clip。
- T075 应在所有真实 clip failed 时准确停在 `sync_video_tasks`，并输出可分类 provider 错误。
- 所有报告、文档、日志只写变量名，不得写真实密钥值。

## 【本轮】全栈工程师 — 真实端到端 Phase 5 深度复测与视频 provider 阻塞定位

### 本轮目标

接手 ShanHaiEdu 项目，围绕用户目标“真实端到端生成 `final_video.mp4 + PPT`”继续推进长期计划；要求测试先行，不能把未通过的真实 E2E 说成通过。

### 已完成事项

- 修复 storyboard LLM prompt 污染：新增 LLM context 清洗，`data:image/png;base64,...`、`b64_json`、`base64` 等大字段只在 LLM 输入中省略，不改节点落库内容。
- 修复真实生图慢调用后的 SQLite 长事务可见性问题：`image_generation` task 创建、成功、失败后及时提交，避免 `manifest/tasks` 读接口被锁。
- 新增真实视频降配额演示参数：`NodeGenerateRequest` 支持 `video_shot_limit` / `clip_limit`，`final_video/generate` 可只提交 1 个真实 clip；T075 默认 `--video-shot-limit 1`。
- 放开单 clip 合成路径：真实单 clip 下载后也可触发 final video 合成，便于今晚先打通可演示端到端。
- 修复弱 storyboard 输出：数字 `shot_id` 归一化为 `shot_01`；过短或缺少“旁白/画面/禁止英文配音”的 `model_prompt` 自动补齐完整视频 prompt。
- 更新真实 E2E gate 报告：`docs\qa-audits\2026-06-21-real-e2e-generation-gate.md`。
- 更新长期计划、阶段总控和架构师记忆，明确当前不再卡 PDF、教案、生图或 storyboard。

### 验证证据

- `python -m pytest apps\api\tests\test_t075_smoke_script.py -q`：`11 passed`。
- `python -m pytest apps\api\tests\test_real_providers.py::test_storyboard_prompt_omits_large_data_image_payloads_but_keeps_asset_refs apps\api\tests\test_real_providers.py::test_storyboard_normalization_expands_weak_model_prompt_for_video_provider apps\api\tests\test_real_providers.py::test_real_video_generate_respects_video_shot_limit_for_quota_safe_demo apps\api\tests\test_real_providers.py::test_sync_task_composes_final_video_after_single_real_clip_when_limited apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met apps\api\tests\test_real_providers.py::test_image_task_is_committed_before_slow_real_image_provider_call -q`：`6 passed`。
- 最新真实 smoke 证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-214857`。
- 最新真实 smoke 结果：`failed_step=download_final_video`，`ok=False`。

### 最新真实 smoke 结论

- 已通过：PDF 上传、教材解析、教案、导入选择、视频脚本、分场剧本、真实生图 1 张、storyboard。
- 已修复：视频任务 prompt 从 16 字弱 prompt 变为完整结构，示例包含“旁白（男声，中文）”“画面”“禁止英文配音”。
- 当前阻塞：唯一 `video_clip_generation` task 返回 `429 RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED`。
- 未产出：真实 clip、`outputs/final_video.mp4`、旁白音频、SRT、concat manifest、ffprobe、PPT。

### 不得误判

- 真实 E2E 尚未打通，不能进入产品演示录屏或 Phase 6 浏览器验收。
- 当前不是 PDF/PPT/prompt 主阻塞，不应继续派人重复修教材解析、教案或 storyboard。
- 后端正确没有用 placeholder 冒充真实 clip；没有 completed/downloaded clip 时不生成真实 `final_video.mp4` 是正确行为。

### 下一棒建议

后端工程师 + 运维/部署工程师优先：

1. 检查视频 provider 账号额度、模型权限、账号池或可用模型，优先解决 `429 RESOURCE_EXHAUSTED`。
2. provider 恢复后复跑单 clip 真实 smoke：

```powershell
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --video-shot-limit 1 --min-successful-images 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

3. 单 clip 成功后再验收 Minimax TTS、ffmpeg 合成、`final_video.mp4`、PPT 和浏览器展示。

## 【本轮】全栈工程师 — 真实端到端生成长期计划 Phase 0-5 离线推进

### 本轮目标

接手项目开发测试全流程，按 `docs\superpowers\plans\2026-06-21-real-e2e-generation.md` 推进真实端到端生成。执行策略为测试先行、两阶段一测：先写测试，再实现；每推进两个阶段后集中测试，不做每个小阶段都跑一遍的低效节奏。

### 已完成事项

- 新增长期执行计划：`docs\superpowers\plans\2026-06-21-real-e2e-generation.md`。
- Phase 0：T075 smoke 成功标准升级，真实通过必须包含图片、clip、`final_video.mp4`、PPT、`ffprobe` 音频流、final_video 旁白 schema 和 PPT 内嵌 MP4。
- Phase 1：T075 smoke 默认向 `intro_video_asset/generate` 传 `min_successful_images=1`、`allow_partial_assets=true`，配合后端已有部分成功继续策略。
- Phase 2：T075 smoke 新增 `--tts-provider-mode`、`ffprobe` 本地探测、`final_video` 节点内容抓取和脱敏写证据。
- Phase 3：核对后端真实视频任务关键合同已覆盖：提交失败写 failed task、真实 task 完成后下载 clip、所有 clip 下载后合成 final video、合成失败写诊断。
- Phase 4：确认 PPT 导出必须嵌入 `ppt/media/*.mp4`，真实视频模式缺少已合成 `final_video.mp4` 时不得生成占位视频。
- Phase 5：新增真实 E2E 门禁报告模板 `docs\qa-audits\2026-06-21-real-e2e-generation-gate.md`；完成运行前环境存在性检查，不输出任何密钥值。
- 密钥安全：补充 `.gitignore`，明确忽略 `apps/api/.env`、`apps/api/.env.local`、`apps/api/.env.*.local`。
- Provider 合同文档：`docs\llm-provider-contract.md` 新增 `Real E2E Acceptance Contract`。

### 验证证据

- Phase 0-1 红灯：`python -m pytest apps\api\tests\test_t075_smoke_script.py -q` 曾按预期失败，缺少音频合同、TTS 参数和部分生图请求体函数。
- Phase 0-1 绿灯：
  - `python -m pytest apps\api\tests\test_t075_smoke_script.py -q`：`8 passed`。
  - `python -m pytest apps\api\tests\test_tts_and_final_video.py -q`：`3 passed`。
  - `python -m pytest apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met -q`：`1 passed`。
- Phase 2-3 绿灯：
  - `python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_tts_and_final_video.py -q`：`13 passed`。
  - 真实视频任务关键回归 5 条：`5 passed`。
- Phase 4-5 离线绿灯：
  - `python -m pytest apps\api\tests\test_ppt_export.py apps\api\tests\test_real_providers.py::test_real_video_mode_ppt_export_requires_composed_final_video apps\api\tests\test_t075_smoke_script.py -q`：`13 passed`。
  - `python -m pytest apps\api\tests\test_tts_and_final_video.py apps\api\tests\test_real_providers.py::test_sync_task_composes_final_video_after_all_real_clips_are_downloaded -q`：`4 passed`。

### 本轮真实 smoke 结果

- 已启动真实 API：`http://127.0.0.1:8188`。
- 已执行 T075 真实 smoke：`PROVIDER_MODE=real`、`IMAGE_PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real`、`TTS_PROVIDER_MODE=real`。
- 证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-205104`。
- 已通过节点：`textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay` 均已生成并确认。
- 失败节点：`intro_video_asset_generate`。
- 失败表现：客户端请求超时；随后 `manifest` / `tasks` 查询返回 500。
- API 栈：`sqlite3.OperationalError: database is locked`。
- 已修复：`_generate_image_tasks` 创建 `image_generation` task 后立即提交；成功/失败更新后也提交，避免真实生图慢调用期间任务不可见和长事务占锁。
- 已新增回归：`test_image_task_is_committed_before_slow_real_image_provider_call`。

### 当前阻塞 / 不得误判

- 真实图片 + 真实视频 + 真实 TTS + PPT 完整外部 E2E 仍未执行，不能宣布“真实端到端已打通”。
- 更准确地说：真实 E2E 已启动一次，但未通过，尚未产出真实图片、真实视频 clip、`final_video.mp4` 或 PPT。
- 当前第一阻塞仍是 `intro_video_asset_generate`，下一轮需要验证锁修复后是否仍超时；若仍超时，应专项处理生图 provider 超时/异步化/重试策略。
- 当前不能进入 Phase 6 浏览器验证，因为 Phase 5 未通过。

### 下一棒建议

继续 Phase 5：

1. 重跑 T075 真实 smoke，确认 `intro_video_asset_generate` 不再引发数据库锁和状态不可见。
2. 如果仍超时，直接修生图 provider 调用超时、单图低成本 smoke、异步任务或重试策略。
3. 如果生图通过，再继续推进 storyboard、真实视频 clip、Minimax TTS、`ffprobe`、PPT 嵌入。
4. 只有 `docs\qa-audits\2026-06-21-real-e2e-generation-gate.md` 裁决通过后，才能进入 Phase 6 浏览器验证。

---

## 【本轮】首席系统架构师/后端热修 — T078/T079/T088/T089 Prompt + TTS + final_video 止血重构

### 本轮目标

落实用户要求的全链路生产与 Prompt/TTS 架构重构止血版：Prompt 文件必须进入运行时；Prompt DB/Registry 成为运行时真源基础；真实生图允许部分成功继续；`final_video/generate` 必须产生旁白音频、SRT、concat manifest 和 `outputs/final_video.mp4`；前端补齐教案结构和最终视频音频/合成状态展示。

### 已完成事项

- PromptLoader：新增 `apps\api\app\prompt_loader.py`，支持 `workflow/prompts/{node_id}/{provider}.md`、`{{var}}`、`{{include shared/xxx.md}}`、缺变量/缺文件错误。
- PromptRegistry：新增 `apps\api\app\prompt_registry.py`，包含 `prompt_templates`、`prompt_versions`、`prompt_usage_log`、`prompt_audit_log`，active 唯一索引、seed 幂等、canary 稳定路由和 TTL cache。
- Prompt 运行链路：`services._build_prompt` 现在优先走 PromptRegistry，再走文件 prompt，最后才回硬编码 fallback。
- T076 生图阻塞：`intro_video_asset/generate` 在显式 `min_successful_images` 或 `allow_partial_assets` 时允许部分成功继续；成功图片进入节点内容，失败图片保留 `failed_assets` 和 failed task 诊断。
- TTS：新增 `MinimaxTTSProvider`，支持 `TTS_PROVIDER_MODE=placeholder|real`、`MINIMAX_API_KEY`，兼容旧 `MINMAX_API_KEY`，默认模型 `speech-2.8-hd`、声线 `Chinese (Mandarin)_Gentleman`。
- final_video：生成/同步时补 `audio/narration.mp3`、`audio/narration.srt`、`outputs/concat_manifest.json`、`outputs/final_video.mp4`；schema 字段包含 `voice_gender=male`、`voice_language=zh-CN`、`audio_verified=true`、`english_audio_detected=false`、`narration_audio_path`、`concat_manifest_path`。
- 前端展示：`ProjectWorkspaceScreen.tsx` 增加教案两层结构摘要和最终视频旁白/合成状态面板。
- 文档：更新 `apps\api\.env.example`、`apps\api\README.md`、`docs\llm-provider-contract.md`。
- 本地 `.env`：已补 TTS 相关变量名，默认 `TTS_PROVIDER_MODE=placeholder`；真实演示时显式改为 `real`。真实密钥未写入文档或输出。

### 验证证据

- 后端核心专项：`python -m pytest apps\api\tests\test_prompt_platform.py apps\api\tests\test_tts_and_final_video.py apps\api\tests\test_real_providers.py::test_intro_video_asset_partial_image_success_continues_when_minimum_met -q`：`9 passed`。
- T075/real provider 回归：`python -m pytest apps\api\tests\test_t075_smoke_script.py apps\api\tests\test_real_providers.py -q`：`66 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`106 passed, 2 xfailed`。
- 前端 lint：`bun run lint`：通过。
- 前端 build：`bun run build`：通过。
- 真实 Minimax TTS smoke：`storage\tts-smoke\narration.mp3`，33396 bytes；ffprobe 显示 `codec_name=mp3`、`sample_rate=32000`、`channels=1`、`duration=1.98s`。

### 未完成 / 不得误判为已完成

- Prompt 管理完整后台未完成：JWT、`ADMIN_USERNAMES`、发布/回滚/灰度 UI、用户态 bundle 隔离仍由 T080-T082/T090 继续。
- 本轮没有执行真实图片+真实视频+真实 TTS 的完整外部 API E2E；只证明真实 TTS 单点 smoke 成功。
- 默认 `.env` 保持 `TTS_PROVIDER_MODE=placeholder`，避免开发/测试误触发真实 TTS；真实演示必须显式切换。
- fake/placeholder 旧契约仍保持 `final_video=running`，但已同步写入 final video 产物字段；不要把 running 误判为没有产物。

### 下一棒建议

测试工程师接 T090：只测新增功能和旧阻塞点，不做无关全量探索。重点覆盖 Prompt 文件生效、Prompt DB seed、部分图片成功继续、fake/placeholder E2E 不回退、真实 TTS smoke、final_video 音频字段、浏览器最终视频展示。

---

## 【本轮】测试工程师 — T076 真实图片/视频/PPT 主链路专项回归

### 本轮目标

只验收 T069 历史阻塞点和 T073-T075 新增能力：`intro_video_asset/generate` 不得再返回旧的 `GENERATION_INPUT_INVALID / Expecting value`；真实图片需生成并落盘；后续应推进到 storyboard、真实视频 clip、`final_video.mp4` 和 PPT。

### 复测结论

**T076 结论：【部分通过】。**

历史旧错误已解除，真实生图能力已部分证明，但真实 provider 第 3 张图连接失败，链路未进入 storyboard、视频、final video 和 PPT 阶段，不能交给 T077 做通过复核。

### 环境

- API：`http://127.0.0.1:8176`
- Web：`http://127.0.0.1:3176`
- Storage：`storage-t076-real-media-regression-20260621-181000`
- Provider：`PROVIDER_MODE=real`
- Image Provider：`IMAGE_PROVIDER_MODE=real`
- Video Provider：`VIDEO_PROVIDER_MODE=real`
- 项目 ID：`proj_b06c60b79093`
- 测试账号：`qa-t076`
- 密钥安全：未输出、截图或写入任何真实密钥。

### 已通过部分

- `/health`、创建项目、PDF 上传、`textbook_parse` 生成/确认、`lesson_plan` 生成/确认、`intro_selection` 生成/编辑/确认、`intro_video_script` 生成/确认、`intro_video_screenplay` 生成/确认均返回 200。
- `intro_video_asset/generate` 未再返回旧红线 `400 / GENERATION_INPUT_INVALID / Expecting value`。
- 已创建 3 个 `image_generation` task。
- 2 个 image task completed，真实图片落盘：
  - `assets/generated_images/asset_001.png`，1791450 bytes。
  - `assets/generated_images/asset_002.png`，1814474 bytes。
- Web 真实 API 模式可进入项目工作区，首页和工作区显示 `视频资产 / 70% / 失败`。
- 浏览器控制台应用级 `error/warn=[]`。

### 未通过部分

- `POST /projects/proj_b06c60b79093/nodes/intro_video_asset/generate` 返回 `502 / IMAGE_REQUEST_FAILED / Connection error.`。
- 第 3 个 `image_generation` task 为 failed，`retryable=true`。
- `intro_video_asset` 节点为 `failed`，`storyboard=not_started`。
- 未创建 `video_clip_generation` task。
- 未生成 clip、`outputs/final_video.mp4` 或 PPT。

### 证据

- 报告：`docs\qa-audits\2026-06-21-t076-real-media-regression.md`
- 证据目录：`docs\qa-audits\t076-real-media-regression-evidence\20260621-184529`
- 关键文件：`summary.json`、`manifest.json`、`tasks.json`、`tasks-sanitized.json`、`node-intro_video_asset.json`、`node-storyboard.json`、`generated-image-paths.json`、`video-task-paths.json`、`clip-paths.json`、`final-artifact-paths.json`、`browser-workspace.png`、`browser-console.json`

### 建议下一个接手角色

后端工程师 + 运维/部署工程师。

### 下个角色需要知道的上下文

- 本轮不是旧 LLM JSON 解析阻塞，错误已经转为 provider 级 `IMAGE_REQUEST_FAILED`。
- 后端 failed node 和 failed task 可诊断闭环成立。
- 当前真实图片链路能完成前 2 张，说明配置和下载路径部分可用；更像真实生图 provider 连接稳定性、账号池、网关或重试策略问题。
- 修复后可复用 `scripts\t075_real_fullchain_smoke.py` 重跑，重点确认第 3 张及后续资产能否完成，并继续验证 storyboard、真实视频 clip、final_video 和 PPT。

---

## 【本轮】后端工程师1 — T073 真实生图 provider 打穿与诊断加固

### 本轮目标

保证 `intro_video_asset/generate` 在 `IMAGE_PROVIDER_MODE=real` 下能真实生成至少 1 张图片并落盘；provider 失败时返回 provider 级错误、写 failed 节点和 failed image task，禁止回退到 `GENERATION_INPUT_INVALID / Expecting value`。

### 已完成事项

- `NewApiImageProvider` 对 base URL 自动补 `/v1`，兼容 `/images/generations` 完整 endpoint。
- 默认请求改为 OpenAI SDK transport，保留 urllib `_http_transport` 作为测试和 fallback 覆盖路径，对齐项目内 `skills\imagegen-myself` 的真实成功路径。
- 图片配置读取对齐 `imagegen-myself`：优先 `IMAGEGEN_MYSELF_PRIMARY_*` / `IMAGEGEN_MYSELF_*`，再读 `NEWAPI_PRIMARY_*` / `NEWAPI_*`，兼容 `PINAI_*`、`AIRCODE_*`、`OPENAI_*`。
- 兼容响应格式：`data[0].url`、`data[0].b64_json`、`data.url`、`data.image_url`、顶层 `url`、顶层 `image_url`；异步 task-only 响应返回 `IMAGE_ASYNC_TASK_UNSUPPORTED`，不假装同步成功。
- `_request_json()` 现在包装空响应、非 JSON、HTTPError、URLError、远端断连和 timeout 为 `ProviderError`。
- `intro_video_asset/generate` 的图片任务 prompt 加固：弱输入如 `shot_01` 会结合 screenplay 场景描述生成完整中文生图提示词。
- `NodeGenerateRequest` 新增 `image_limit`、`image_quality`、`image_size`、`image_model`，支持本地 smoke 只生成 1 张低成本图片。
- 失败路径会写 `image_generation` failed task、`intro_video_asset` failed 节点、`error_code`、`retryable` 和脱敏 `response_excerpt`。

### 验证证据

- `python -m pytest apps\api\tests\test_real_providers.py -q`：`60 passed`。
- `python -m pytest apps\api\tests -q`：`97 passed, 2 xfailed`。
- 项目内 `skills\imagegen-myself` 当前 smoke 也可生成图片：`docs\qa-audits\t073-real-image-api-smoke\skill-current-smoke.png`，607600 bytes。
- API 级真实 smoke 已通过：`intro_video_asset/generate` 使用 `IMAGE_PROVIDER_MODE=real`、`image_limit=1`、`image_quality=low` 返回 HTTP 200，节点状态 `needs_review`，创建 1 条 `image_generation` completed task。
- API 级真实图片产物：`docs\qa-audits\t073-real-image-api-smoke\storage-api-sdk-one-low\projects\T073-API-real-image-sdk-one-low_proj_fdd7c02a37ed\assets\generated_images\asset_ref_01.png`，1203501 bytes。

### 已更新文件

- `apps\api\app\providers.py`
- `apps\api\app\services.py`
- `apps\api\app\settings.py`
- `apps\api\app\models.py`
- `apps\api\tests\test_real_providers.py`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`
- `workflow\multi-agent\dispatch.md`

### 剩余风险

- 异步图片任务只做了明确错误码 `IMAGE_ASYNC_TASK_UNSUPPORTED`，尚未实现 query/download；若供应商切到异步图片接口，需要补最小查询下载链路。
- 真实上游偶发 503/断连，当前已做同 profile 一次 transient retry 和 1024 fallback，但完整 6 张图片仍可能受账号池波动影响；演示 smoke 建议先用 `image_limit=1`。
- 本轮不改前端、不接真实视频 provider、不处理正式上线鉴权。

### 建议下一个接手角色

测试工程师或后端工程师3。

### 下个角色需要知道的上下文

- 重新跑 T075 real/real 时，建议先传 `image_limit=1` 验证图片节点，再恢复多图生成。
- `intro_video_asset/generate` 成功后真实图片位于项目目录 `assets\generated_images\*.png`，可通过受限下载接口 `/projects/{project_id}/images/{filename}` 读取。

---

## 【本轮】后端工程师3 — T075 真实全链路一键 smoke、证据采集和 PPT 交付闭环

### 本轮目标

交付今晚可反复执行的一键端到端脚本，覆盖 PDF → 教案 → 导入策划 → 视频脚本链 → 图片 → storyboard → 视频 clip → `final_video.mp4` → PPT，并输出结构化证据；脚本不得读取或打印真实 provider key。

### 已完成事项

- 新增 `scripts\t075_real_fullchain_smoke.py`。
- 脚本支持 `--api-base`、`--fixture-pdf`、`--storage`、`--provider-mode`、`--image-provider-mode`、`--video-provider-mode`、`--task-timeout-sec`、`--poll-interval-sec`。
- 脚本逐步推进：health、create project、upload PDF、`textbook_parse`、`lesson_plan`、`intro_selection` 生成/编辑 `selected_anchor`/确认、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`、`final_video/generate`、video task 轮询、clip 下载、`outputs/final_video.mp4` 下载、PPT 导出下载。
- 证据固定输出：`summary.json`、`manifest.json`、`tasks.json`、`generated-image-paths.json`、`video-task-paths.json`、`final-artifact-paths.json`、`provider-error-summary.json`。
- 写盘前做递归脱敏，避免 provider 错误摘要中出现 token/key。
- 新增 `apps\api\tests\test_t075_smoke_script.py`，覆盖脱敏、成功标准、provider 错误摘要和递归证据脱敏。
- 新增 `docs\qa-audits\2026-06-21-t075-real-fullchain-smoke.md`，记录使用方式、证据目录、fake/placeholder 结果和 real/real 阻塞。

### 验证证据

- `python -m pytest apps\api\tests\test_t075_smoke_script.py -q`：`5 passed`。
- fake/placeholder 结构 smoke 通过，证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-175007`。
- fake/placeholder 项目 ID：`proj_add5dc2e2ca7`，已下载 `final_video.mp4` 和 `lesson-video-demo.pptx`，PPT 内含 `ppt/media/media1.mp4`。
- real/real smoke 已执行，证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-174737`。
- real/real 停在 `intro_video_asset_generate`，HTTP `502`，错误码 `IMAGE_RESPONSE_INVALID`；后端已写 `intro_video_asset=failed` 和 `image_generation` failed task，未继续伪造 storyboard、video clip、final_video 或 PPT。

### 关键结论

- T075 的脚本和证据闭环已完成，可以反复运行并在失败节点留下接口、HTTP 状态、错误码和脱敏响应摘要。
- 当前真实全链路未通过的原因是生图 provider 返回 HTML 非 JSON 响应，不是 T075 脚本吞错或继续假跑。
- fake/placeholder 模式只能验证脚本结构和 MP4/PPT 交付闭环；real/real 成功标准仍要求至少 1 张真实图片、至少 1 个真实 video clip、`outputs/final_video.mp4` 和 PPT 均存在。

### 已更新文件

- `scripts\t075_real_fullchain_smoke.py`
- `apps\api\tests\test_t075_smoke_script.py`
- `docs\qa-audits\2026-06-21-t075-real-fullchain-smoke.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`
- `workflow\multi-agent\dispatch.md`

### 待处理问题

- 真实生图 provider 当前返回 HTML 页面，需后端/运维继续检查 `IMAGEGEN_*` base URL、模型路径、鉴权或网关路由，让 `intro_video_asset/generate` 能返回 JSON 图片结果并下载真实图片。
- 修复生图 provider 后再重跑 T075 real/real；只有跑过图片、storyboard、真实 video clip、final_video 和 PPT，才能宣布真实交付闭环通过。

### 建议下一个接手角色

后端工程师或运维/部署工程师。

### 下个角色需要知道的上下文

- 直接看 `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-174737\provider-error-summary.json` 可定位真实失败。
- 失败项目 `proj_2a6bb6bc4280` 的 `tasks.json` 中已有 `image_generation` failed task，错误码 `IMAGE_RESPONSE_INVALID`，`response_excerpt` 是 HTML 网关页。
- 脚本可继续复用，不需要为了下一次真实复测改调用顺序。

---

## 【本轮】后端工程师2 — T074 真实视频 clip 生成、下载和 final_video 合成

### 本轮目标

在 storyboard 已生成、真实图片已落盘后，保证 `VIDEO_PROVIDER_MODE=real` 下 `final_video/generate` 能提交真实视频任务、轮询、下载 clip，并在所有 clip 完成后合成 `outputs/final_video.mp4`；不改前端、不用 placeholder 冒充真实视频。

### 已完成事项

- `final_video/generate` 真实模式默认提交 storyboard 全部 shots。
- 每个 shot 创建 `video_clip_generation` task，字段包含 `provider_task_id`、`shot_id`、`download_path`。
- 默认模型 `omni_flash-10s`，prompt 使用 storyboard `model_prompt`。
- 若真实图片 task 已有公网 `image_url`，按 `reference_image_ids` 注入 video submit payload 的 `images`；本地路径不强传，不阻塞主链路。
- `GET /projects/{project_id}/tasks/{task_id}` 查询 completed 后下载到 `clips/{shot_id}.mp4`。
- 下载失败写 `VIDEO_DOWNLOAD_FAILED` 到 task result 和 errors log。
- 所有 clip `downloaded` 后合成 `outputs/final_video.mp4`。
- ffmpeg 缺失或合成失败写 `FINAL_VIDEO_COMPOSE_FAILED` 到当前 task result 和 `final_video` failed 节点。
- PPT 导出继续复用 `outputs/final_video.mp4`，真实模式下没有合成文件不会伪造 placeholder。

### 输出路径

- clip：`clips/{shot_id}.mp4`
- final video：`outputs/final_video.mp4`

### 验证

- T074 目标测试：`3 passed`。
- `python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_video_demo_contract.py apps\api\tests\test_ppt_export.py -q`：`65 passed`。
- `python -m pytest apps\api\tests -q`：`90 passed, 2 xfailed`。

### 剩余风险

- 本轮使用 stub provider 做契约测试，未调用真实外部 Octo API。
- 真实 API live E2E 仍需测试工程师复测，确认上游真实任务、下载速度、ffmpeg 环境和视频内容质量。

---

## 【本轮】首席系统架构师/后端热修 — T072 真实生图 provider 空响应诊断修复

### 本轮目标

直接处理 T069 暴露的阻塞：真实生图 provider 在 `intro_video_asset/generate` 阶段返回空 body 或非 JSON 时，后端仍漏出 `400 / GENERATION_INPUT_INVALID / Expecting value`，导致不写 failed 节点、不保留 image task，真实图片/视频/PPT 主链路中断。

### 根因判断

T069 第一次复测曾返回 `502 / IMAGE_KEY_MISSING`，说明文本 LLM 的 assets JSON 已经成功生成并进入生图分支。第二次补齐生图配置后复现旧错误，根因定位为 `apps\api\app\providers.py` 的公共 `_request_json()` 对 HTTP 200 但空 body/非 JSON 响应直接 `json.loads()`，`JSONDecodeError` 没有包装为 `ProviderError`，最终被路由层当作 `ValueError` 返回 `GENERATION_INPUT_INVALID`。

### 已完成修复

- `apps\api\app\providers.py`
  - `_request_json()` 读取 HTTP 200 响应后先判断空 body。
  - 空 body / 非 JSON 响应统一包装为 `ProviderError`。
  - `IMAGE_REQUEST_FAILED` 对应响应解析错误会变成 `IMAGE_RESPONSE_INVALID`。
  - 保留脱敏 `response_excerpt`，不输出真实 token 或完整敏感响应。
- `apps\api\tests\test_real_providers.py`
  - 新增 `NewApiImageProvider` 空 body / 非 JSON provider 单元回归。
  - 新增 `intro_video_asset` 集成回归：真实生图空响应时接口返回 502、写 failed 节点、写 failed image task。

### 验证

- 新增目标测试：`3 passed`。
- T068/T064 相关回归：`5 passed`。
- `python -m pytest apps\api\tests\test_real_providers.py -q`：`40 passed`。
- `python -m pytest apps\api\tests -q`：`72 passed, 2 xfailed`。

### 当前状态

T072 代码级热修已完成。当前只能说明旧的 `GENERATION_INPUT_INVALID / Expecting value` 不应再由生图 provider 空/非 JSON 响应触发；真实外部 API 全链路仍需测试工程师重跑 T069。

### 建议下一个接手角色

测试工程师重跑 T069。若真实生图 provider 仍失败，应看到 `IMAGE_RESPONSE_INVALID`、`IMAGE_REQUEST_FAILED`、`IMAGE_RESPONSE_INVALID` 或其他 provider 级错误，并且应有 failed 节点和 failed image task；如果真实生图成功，继续推进 storyboard、真实视频 clip、`final_video.mp4` 和 PPT。

---

## 【本轮】测试工程师 — T069 真实 API 全链路返工复测

### 本轮目标

验证 T068 后端修复后，真实 API 链路是否能从教材 PDF 一路跑到真实图片、真实视频、`final_video.mp4` 和 PPT 导出。

### 复测结论

**T069 结论：【阻塞】。**

T068 后的真实外部 API E2E 仍未通过，不能交给首席系统架构师做 T071 通过复核。

### 环境

- API：`http://127.0.0.1:8169`
- Web：`http://127.0.0.1:3169`
- Storage：`storage-t069-real-image-video-e2e-20260621-165407`
- Provider：`PROVIDER_MODE=real`
- 生图 Provider：`IMAGE_PROVIDER_MODE=real`
- 视频 Provider：`VIDEO_PROVIDER_MODE=real`
- 项目 ID：`proj_0f50893204c6`
- 测试账号：`qa-t069`
- 密钥安全：未输出、截图或写入任何真实密钥。

### 已通过部分

- `GET /health`：200。
- 创建项目：200。
- 上传 fixture PDF：200。
- `textbook_parse/generate`、get、approve：200。
- `lesson_plan/generate`、get、approve：200。
- `intro_selection/generate`、edit、approve：200。
- `intro_video_script/generate`、get、approve：200。
- `intro_video_screenplay/generate`、get、approve：200。
- Web 真实 API 模式可进入项目工作区。
- 浏览器控制台应用级 `error/warn=[]`。

### 阻塞点

- 接口：`POST /projects/proj_0f50893204c6/nodes/intro_video_asset/generate`
- HTTP：`400`
- 错误码：`GENERATION_INPUT_INVALID`
- 错误消息：`Expecting value: line 1 column 1 (char 0)`

### 红线判断

本轮复现了 T069 明确禁止的旧错误：

- 未返回 `INTRO_VIDEO_ASSET_JSON_EMPTY`
- 未返回 `INTRO_VIDEO_ASSET_JSON_INVALID`
- 未返回 `INTRO_VIDEO_ASSET_SCHEMA_INVALID`
- `intro_video_asset` 节点仍为 `not_started`，未写 failed 版本
- `GET /projects/proj_0f50893204c6/tasks` 返回空数组
- 未创建 `image_generation` task
- 未生成真实图片、storyboard、真实视频 clip、`final_video.mp4` 或 PPT

### 证据

- 报告：`docs\qa-audits\2026-06-21-real-image-video-e2e-rerun.md`
- 证据目录：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442`
- API summary：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\summary.json`
- Manifest：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\manifest-after-failure.json`
- Tasks：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\tasks-after-failure.json`
- 浏览器截图：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\browser-workspace.png`
- 浏览器控制台：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\browser-console.json`
- 产物清单：`generated-image-paths.json`、`task-id-lists.json`、`clip-paths.json`、`final-artifact-paths.json`

### 建议下一个接手角色

后端工程师继续返工 `intro_video_asset/generate` 真实链路，重点排查 JSONDecodeError/空响应是否仍从某条路径漏到 `ValueError -> GENERATION_INPUT_INVALID`，并补充从 `intro_video_screenplay=approved` 到创建 `image_generation` task 的集成级回归。

---

## 【本轮】首席系统架构师 — T068 后端阻塞修复验收

### 本轮目标

复核后端 T068 是否真正修复 T063/T067 中 `intro_video_asset/generate` 的真实链路阻塞，尤其是 LLM 空响应、非 JSON、缺字段时的错误诊断，以及合法资产 JSON 后续创建图片任务的路径。

### 复核结论

**T068 通过架构师验收，可以进入 T069 真实全链路返工复测。**

本结论不等于 T063 真实图片/视频/PPT 全链路通过；真实外部 API E2E 必须由测试工程师按 T069 重跑。

### 核验证据

- 交接文档：`docs\backend-t068-intro-video-asset-fix-handoff.md`。
- 关键代码：`apps\api\app\services.py` 中 `intro_video_asset` 文本生成诊断包装、schema 校验、failed 节点写入和 image task 创建路径。
- 回归测试：`apps\api\tests\test_real_providers.py` 中 T068 四个新增用例覆盖空响应、非 JSON、缺 `assets`、合法 JSON 创建 `image_generation` task。

### 新鲜验证

- T068 目标测试：`4 passed`。
- 真实 provider 契约文件：`37 passed`。
- 后端全量：`69 passed, 2 xfailed`。

### 已确认行为

- 空响应不再漏出 `400 / GENERATION_INPUT_INVALID / Expecting value`，改为 `502 / INTRO_VIDEO_ASSET_JSON_EMPTY`。
- 非 JSON 响应改为 `502 / INTRO_VIDEO_ASSET_JSON_INVALID`，错误摘要脱敏。
- 缺 `assets` 或 asset 子字段改为 `502 / INTRO_VIDEO_ASSET_SCHEMA_INVALID`。
- 上述失败会写入 `intro_video_asset` failed 节点。
- 合法资产 JSON 会继续进入 `_generate_image_tasks()` 并创建 `image_generation` task。

### 剩余风险

- 本轮没有调用真实外部 provider 做端到端复测。
- 真实 LLM 若仍持续返回空/非 JSON，T069 应记录新的 `INTRO_VIDEO_ASSET_*` 诊断，而不是判为未知黑盒。
- 真实图片、storyboard、真实视频 clip、`final_video.mp4` 和 PPT 实物仍未在 T068 中证明。
- T070 运维手册生图 provider 口径仍需修正。

### 已更新文件

- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`
- `workflow\multi-agent\dispatch.md`

### 建议下一个接手角色

测试工程师接 T069，按真实 API 全链路重跑：PDF → 教材解析 → 教案 → 导入策划 → 视频脚本链 → 真实图片 → storyboard → 真实视频 clip → clip 下载 → `final_video.mp4` → PPT 导出。

---

## 【本轮】后端工程师 — T068 intro_video_asset/generate 真实链路阻塞修复

### 本轮目标

修复 T063/T067 发现的真实全链路阻塞：`intro_video_asset/generate` 在真实 LLM 资产 JSON 阶段返回 `400 / GENERATION_INPUT_INVALID / Expecting value`，导致没有创建 image task，后续 storyboard、真实视频、final_video 和 PPT 全部中断。

### 已完成事项

- 为 `intro_video_asset` 增加文本生成阶段的节点级诊断包装。
- LLM 空响应现在返回 `502 / INTRO_VIDEO_ASSET_JSON_EMPTY`。
- LLM 非 JSON 现在返回 `502 / INTRO_VIDEO_ASSET_JSON_INVALID`。
- LLM JSON 缺 `assets` 或 asset 子字段现在返回 `502 / INTRO_VIDEO_ASSET_SCHEMA_INVALID`。
- 上述失败都会写入 `intro_video_asset` failed 节点和 errors log。
- 错误信息经过 `sanitize_provider_excerpt()` 脱敏，不输出 API key、Bearer token 或完整上游响应。
- 合法资产 JSON 保持继续进入 `_generate_image_tasks()`；`IMAGE_PROVIDER_MODE=real` 时创建 `image_generation` task 并下载图片到 `assets/generated_images/{asset_id}.png`。
- 补充 T068 后端交接文档：`docs\backend-t068-intro-video-asset-fix-handoff.md`。

### 验证

- 红灯验证：新增 T068 测试初始失败，表现为空/非 JSON 仍返回 400，缺 `assets` 仍 200。
- T068 目标测试：`4 passed`。
- T064 回归测试：`6 passed`。
- `python -m pytest apps\api\tests\test_real_providers.py -q`：`37 passed`。
- `python -m pytest apps\api\tests -q`：`69 passed, 2 xfailed`。

### 修复前后差异

- 修复前：`intro_video_asset/generate` 真实 LLM 异常会漏成 `GENERATION_INPUT_INVALID`，节点不落 failed，tasks 为空。
- 修复后：失败有明确 `INTRO_VIDEO_ASSET_*` 错误码、failed 节点和日志；合法 JSON 会继续创建真实图片 task。

### 剩余风险

- 本轮没有重跑真实外部 API E2E，不宣布 T063 通过。
- 真实 LLM 若仍稳定返回空/非 JSON，T069 应记录新的诊断错误码和 failed 节点证据。
- 真实图片、storyboard、真实视频 clip、final_video、PPT 仍需 T069 按完整链路复测。

### 建议下一个接手角色

测试工程师接 T069，重跑 T063 真实 API 全链路；运维/部署工程师继续接 T070 修正文档中生图 provider 口径。

---

## 【本轮】首席系统架构师 — T067 真实图片/视频全链路阶段复核

### 本轮目标

复核 T063-T066、关键代码 diff、浏览器证据、`final_video.mp4` 和 PPT 实物路径，裁决是否达到“本地真实 API 可演示”，以及是否可以进入产品演示录屏。

### 复核结论

**T067 阻塞不通过。当前不能进入产品演示录屏。**

### 关键证据

- T063 报告：`docs\qa-audits\2026-06-21-real-image-video-e2e.md`，结论为【阻塞】。
- T063 summary：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\summary.json` 中 `ok=false`。
- T063 实物证据缺失：`generated_image_paths=[]`、`video_task_ids=[]`、`final_video_path=null`、`ppt_path=null`。
- T063 证据目录只有 `summary.json`、`browser-workspace.png`、`browser-console.json`，不存在 `final_video.mp4` 或 PPT。
- T064 架构师新鲜复核目标测试：`6 passed`，但该测试只证明 task 状态、retry 和下载安全；没有复测真实外部 API 全链路。
- T065 前端截图存在，但前端交接明确未重新触发外部真实 provider 新任务。
- T066 运维手册存在，但生图 provider 口径滞后：手册仍写生图不在 `apps\api` 服务内，而 T064 已新增 API 层 `NewApiImageProvider`。

### 阻塞点

- 接口：`POST /projects/proj_6a0c9a3a6d81/nodes/intro_video_asset/generate`
- HTTP：`400`
- 错误码：`GENERATION_INPUT_INVALID`
- 消息：`Expecting value: line 1 column 1 (char 0)`
- 影响：未创建 `image_generation` task，无法进入真实生图、storyboard、真实视频、clip 下载、`final_video.mp4` 和 PPT 导出。

### 架构判断

T063 失败发生在 `intro_video_asset` 的文本资产 JSON 生成阶段。当前代码是先 `_generate_text_node()`，成功后才进入 `_generate_image_tasks()`；因此 T064 的图片 task 加固不能自动解除 T063 阻塞。

### 已更新文件

- 新增：`docs\qa-audits\2026-06-21-real-image-video-stage-review-t067.md`
- 更新：`workflow\multi-agent\dispatch.md`
- 更新：`workflow\multi-agent\handoffs\latest.md`
- 更新：`workflow\multi-agent\stage-review.md`
- 更新：`workflow\multi-agent\roles\architect.md`

### 下一棒任务

- T068 后端工程师：修复 `intro_video_asset/generate` 真实 LLM 输出解析和失败诊断，确保能创建 `image_generation` task。
- T069 测试工程师：重跑 T063 真实全链路，必须产出图片、视频 task、clip、`final_video.mp4` 和 PPT 实物。
- T070 运维/部署工程师：修正真实生图 provider 运行手册口径。
- T071 首席系统架构师：T068-T070 完成后重新复核。

---

## 【本轮】前端工程师 — T065 真实图片/视频生成过程用户可见体验收口

### 本轮目标

在不改后端、不接真实 provider、不重构工作区大组件的前提下，收口真实 API 模式下图片资产、视频 clip 和最终交付区域的用户可见状态，让教师能看到生成中、成功、失败、可重试和下载入口。

### 已完成事项

- `intro_video_asset` 结果页新增图片资产生成状态面板：生成中显示加载状态，成功展示图片预览和输出路径，失败展示脱敏失败原因和“重试该图片”入口。
- `final_video` 结果页增强：展示“演示视频文件已生成”和“下载 MP4”入口；保留 PPT 导出/PPT 下载；展示每个 clip 的状态、模型、尺寸、输出路径和脱敏 `provider_task_id`；支持单 clip 刷新和失败后重试。
- API client 与 store 补齐 `GET /projects/{project_id}/tasks/{task_id}`、`POST /projects/{project_id}/tasks/{task_id}/retry`，前端 `refreshProjectTask` / `retryProjectTask` 会 upsert 当前任务。
- provider 错误提示已脱敏：只展示错误码/HTTP 摘要或截断后的安全摘要，不展示 token、key、Bearer 或完整上游响应。
- 保持课程锚点展示：视频脚本和分镜摘要都会从 `intro_selection.selected_anchor` / `video-script.anchor_to_lesson` 解析并展示同一课程锚点。

### 已更新文件

- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\store.ts`
- `apps\web\src\lib\types.ts`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 验证

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器真实 API 模式：
  - 已有截图 `docs\qa-audits\t065-video-assets-real-api.png`：可见视频资产结果页、图片预览、任务状态、Provider 状态、刷新任务和 JSON 高级入口。
  - 已有截图 `docs\qa-audits\t065-final-video-real-api.png`：可见最终视频结果页、MP4 下载、PPT 导出、clip 已完成、脱敏 provider_task_id 和 clip MP4 下载。
  - 本轮补充只读核验：`http://127.0.0.1:3163/` 可进入真实 API 工作区，项目处于“视频资产 / 70%”；进入视频资产结果页后页面包含重试入口，浏览器 console `error/warn` 为 0。

### 剩余风险

- 本轮未重新触发外部真实 provider 生成新图片或新视频任务，避免重复消耗和引入 provider 波动；浏览器证据沿用已有真实 API 项目截图，并补充当前在线实例只读核验。
- 当前截图中的视频资产项目没有现场失败任务，因此失败/重试分支主要由代码路径和后端 T064 契约支撑，仍建议测试工程师后续用可控 failed task 做专项回归。
- 未处理真实视频 provider 质量、reference image 映射、多 clip 合成稳定性和上线级权限。

### 建议下一个接手角色

测试工程师。

### 下个角色需要知道的上下文

- 不要把“演示视频文件已生成”理解为真实 AI 成片质量验收通过；该文案只承诺本地可下载演示文件。
- provider 失败时前端只展示脱敏摘要和可重试建议；完整上游响应仍应留在后端日志/诊断侧，不进前端页面。
- 如果要补 T065 自动化/浏览器专项，请优先准备一个包含 `image_generation=failed` 和 `video_clip_generation=failed` 的后端项目或 fixture。

---

## 【本轮】测试工程师 — T063 真实 API 全链路验收

### 本轮目标

按用户直接派发的 T063，使用真实文本 LLM、真实生图 provider、真实视频 provider 做本地完整轻量 E2E，覆盖 PDF 上传到 PPT 下载；不做上线验收，不输出任何真实密钥。

### 环境与证据

- API：`http://127.0.0.1:8163`
- Web：`http://127.0.0.1:3163`
- Storage：`storage-t063-real-image-video-e2e-20260621-155205`
- Provider：`PROVIDER_MODE=real`、`IMAGE_PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real`
- 项目 ID：`proj_6a0c9a3a6d81`
- 报告：`docs\qa-audits\2026-06-21-real-image-video-e2e.md`
- API 证据：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\summary.json`
- 浏览器截图：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-workspace.png`
- 控制台证据：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-console.json`
- 测试脚本：`scripts\t063_real_image_video_e2e.py`

### 执行结论

T063 结论：【阻塞】。

已通过节点：

- `/health=200`
- 创建项目 `200`
- 上传 fixture PDF `200`
- `textbook_parse/generate/get/approve=200`
- `lesson_plan/generate/get/approve=200`
- `intro_selection/generate/edit/approve=200`
- `intro_video_script/generate/get/approve=200`
- `intro_video_screenplay/generate/get/approve=200`

阻塞节点：

- `POST /projects/proj_6a0c9a3a6d81/nodes/intro_video_asset/generate`
- HTTP：`400`
- 错误码：`GENERATION_INPUT_INVALID`
- 消息：`Expecting value: line 1 column 1 (char 0)`
- 同项目二次重试仍稳定复现。
- `tasks` 表为空，未创建 `image_generation` task。

### 影响范围

- 未产出真实图片路径。
- 未生成 storyboard。
- 未提交真实视频任务，故无视频任务 ID / provider task ID。
- 未下载 clip。
- 未合成或落盘 `final_video.mp4`。
- 未导出 PPT，无法验证 PPT 内嵌视频或可下载视频链接。

### 浏览器结果

- Web 真实 API 模式可登录。
- 首页项目卡显示 `视频资产 / 70% / 进入「视频资产」`。
- 工作区显示当前阶段 `视频资产`，节点详情为 `视频资产 · 未开始`。
- 浏览器应用级 `error/warn=[]`。
- 首次 Web dev 遇到 Turbopack `.next\dev` 缓存损坏 panic，清理 `apps\web\.next\dev` 后重启恢复；该问题未出现在页面控制台。

### 建议下一个接手角色

后端工程师。

### 后端修复建议

- 修复 `intro_video_asset/generate` 在真实 LLM 返回空响应 / 非 JSON 时的错误包装与诊断，避免返回不可定位的 `GENERATION_INPUT_INVALID`。
- 为 `intro_video_asset` 补充节点失败版本或 errors log，前端才能展示可读失败原因。
- 确认文本资产 JSON 生成成功后，再进入 `image_generation` task 创建；若图片 provider 失败，应持久化 failed task 和脱敏 provider 错误。
- 补回归：LLM 空响应、非 JSON、缺必填字段、真实图片 provider 成功、真实图片 provider 失败。

---

## 【本轮】后端工程师 — T064 真实生图/视频 API 稳定性加固

### 本轮目标

让真实生图/视频 API 从“能调用”加固为“可诊断、可重试、可下载”，不改前端大 UI，不打印或写入真实 token。

### 已完成事项

- 新增 API 层 `NewApiImageProvider`，支持 OpenAI 兼容图片生成响应中的 `url` / `b64_json`。
- 新增图片 provider 配置：`IMAGE_PROVIDER_MODE`、`IMAGEGEN_*`、`IMAGEGEN_MYSELF_*`、`NEWAPI_*` 相关变量名。
- `intro_video_asset/generate` 在真实图片 provider 存在时，为每个 asset 创建 `image_generation` task，并下载到 `assets/generated_images/{asset_id}.png`。
- task 顶层字段统一补齐：`provider_task_id`、`image_url`、`image_path`、`clip_path`、`download_status`、`error_code`、`retryable`。
- `POST /projects/{project_id}/tasks/{task_id}/retry` 改为真实 retry：
  - `image_generation`：重提单张图，下载回原 `image_path`。
  - `video_clip_generation`：重提单个 clip，保留原 `clip_path`。
- 新增 `GET /projects/{project_id}/images/{filename}`，只允许下载当前项目 `assets/generated_images` 下 `.png/.jpg/.jpeg/.webp`。
- 图片、clip、final_video、PPT 下载接口维持当前项目目录限制；路径穿越测试已覆盖。
- 新增后端交接文档：`docs\backend-t064-real-media-stability-handoff.md`。

### 验证

- 红灯验证：新增 T064 测试初始失败，暴露图片任务未入库、图片失败未转 failed、task retry 假返回、图片下载接口缺失。
- 目标测试：`6 passed`。
- 相关回归：`python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_video_demo_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_fullchain_e2e_contract.py -q`：`46 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`65 passed, 2 xfailed`。
- 脱敏扫描：未发现真实密钥形态；命中项为脚本/文档文件名和测试中的假 token，用于脱敏断言。

### 剩余风险

- 本轮没有再次调用真实外部 provider；自动化用 stub provider 验证契约。
- 图片 provider 当前接同步 OpenAI 兼容生图；若后续切到章鱼哥 `/v1/videos` 异步图片路线，需要补 query/download 状态机。
- 真实视频 reference image 到 Omni 的公网 URL / multipart 映射仍待后续质量链路处理。
- 多 clip 合成仍依赖本机 `ffmpeg`。

### 建议下一个接手角色

测试工程师可基于 `docs\backend-t064-real-media-stability-handoff.md` 做 T064 验收；后端后续处理 reference image 映射和异步图片 provider。

---

## 【本轮】运维/部署工程师 — T066 真实生图/视频 API 环境与演示运行手册

### 本轮目标

按用户直接派发的 T066，补齐真实文本 LLM、生图 provider、视频 provider、storage、ffmpeg 和 PPT 导出的演示运行手册，并更新 `.env.example` 与防误提交规则。

### 已完成事项

- 新增 `docs\ops-real-provider-demo-runbook.md`。
- 更新 `apps\api\.env.example`：只保留变量名和占位说明，覆盖文本 LLM、生图 provider、视频 provider、storage、workflow、CORS、后端 token 和 `FFMPEG_PATH` 预留说明。
- 更新 `.gitignore`：补 provider 日志、`storage-*`、真实生图 smoke、真实视频 smoke、fullchain 二进制证据和真实图片产物定向忽略。
- 梳理运行模式：`PROVIDER_MODE` 控制文本 LLM，`VIDEO_PROVIDER_MODE` 控制视频 provider。
- 明确演示口径：完整 E2E 推荐 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`；真实 Octo 视频单独运行 `scripts\smoke-octo-real-video.ps1`。
- 明确生图 provider 当前由 `skills\imagegen-myself` 脚本负责，不是 API 内建 endpoint。
- 明确 ffmpeg 当前从 `PATH` 查找，`FFMPEG_PATH` 只是预留/运维说明变量。

### 关键结论

- T066 在当前 `dispatch.md` 未找到既有任务行，本轮按用户当前明确指令直接执行。
- `.env.example` 未写入真实密钥。
- 手册覆盖后端启动、前端启动、health 检查、provider 模式确认、storage 可写确认和五类故障排查。
- `.gitignore` 不能全局忽略 `*.png`，因为仓库已有 `apps\web\public\logo.png`；真实图片采用目录和命名规则定向忽略。

### 已更新文件

- `docs\ops-real-provider-demo-runbook.md`
- `apps\api\.env.example`
- `.gitignore`
- `workflow\multi-agent\roles\ops-devops-engineer.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待处理问题

- 后端如需真正支持 `FFMPEG_PATH`，需要后端工程师修改 `apps\api\app\video_outputs.py`，当前仅支持 `PATH`。
- 如未来把生图纳入 API endpoint，需要后端补 settings、provider adapter、接口和日志脱敏策略。
- 如果真实 provider 输出目录变化，运维需同步补 `.gitignore`。

### 建议下一个接手角色

测试工程师。

### 下个角色需要知道的上下文

- 可按 `docs\ops-real-provider-demo-runbook.md` 第 7 节做演示前检查。
- 不要把真实视频 smoke 失败等同于完整 E2E 失败；真实 Octo 链路应单独诊断。
- 不要把 `FFMPEG_PATH` 当作已生效配置，当前必须确保 `ffmpeg` 在系统 `PATH`。

---

## 【本轮】后端工程师3 — 真实视频与图片生成最小闭环 smoke

### 本轮目标

按用户要求重启本地 API，单独验证“视频生成是否有问题”和“图片供应商是否能生成”，不扩大到完整 PPT/前端质量验收。

### 已完成事项

- 停止旧 `apps.api.app.main` 进程，使用 `PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real` 重启 API 到 `http://127.0.0.1:8000`。
- 修复 `scripts\smoke-octo-real-video.ps1` 的旧 fixture，补齐课程锚点字段 `selected_anchor`。
- 执行真实视频 smoke：`omni_flash-10s` 单镜头提交、轮询、完成、下载。
- 修复 `skills\imagegen-myself\scripts\aircode_image_gen.py`，支持图片供应商返回 `url` 时下载保存，不再只接受 `b64_json`。
- 扩展 `skills\imagegen-myself\scripts\test_aircode_image_gen_env.py`，覆盖 URL 提取与 URL 下载。
- 执行真实图片生成 smoke：`gpt-image-2` 生成 PNG。
- 新增复测报告：`docs\qa-audits\2026-06-21-real-video-image-smoke.md`。

### 关键结论

- 视频链路已打通：`submit -> query -> completed -> download` 成功。
- 视频产物：`docs\qa-audits\octo-real-video-smoke\20260621-145411\shot_01.mp4`，大小 `2570764` bytes。
- 图片链路已打通：项目 `imagegen-myself` 供应商真实生成成功。
- 图片产物：`docs\qa-audits\imagegen-real-smoke\20260621-145411\imagegen-smoke.png`，大小 `1283726` bytes，PNG 签名有效。
- 本轮只证明最小生成链路打通，不代表多镜头合成、PPT 嵌入、前端展示、视频艺术质量、音频质量全部验收通过。

### 验证

- `python .\skills\imagegen-myself\scripts\test_aircode_image_gen_env.py`：`OK`，4 个测试通过。
- `scripts\smoke-octo-real-video.ps1`：`PASS status=completed`。
- 图片生成：第一次连接错误后脚本自动重试成功，保存 PNG。

### 建议下一个接手角色

- 后端工程师继续补真实多镜头、reference image 映射和合成。
- 测试工程师后续做 6 镜头最终视频 + PPT 嵌入回归。

---

## 【本轮】前端工程师 — T060 课程锚点确认/编辑控件

### 本轮目标

补齐 `intro_selection` 节点的课程锚点确认/编辑控件，让教师不再只能通过 JSON 手改 `selected_anchor`，并保证下游视频脚本摘要能看到同一个课程锚点。

### 已完成事项

- `intro_selection` 结果页新增“课程锚点确认”编辑框。
- 用户点击候选导入方案时，前端同步更新：
  - `primary_design_id`
  - `selected_design_ids`
  - `selected_anchor`，默认取该方案 `anchor_to_lesson`
- 用户可手工修改 `selected_anchor`。
- 保存和确认前做前端校验：
  - `selected_anchor` 不能为空。
  - `selected_anchor` 长度不得小于 10。
- 保留 JSON 高级编辑入口，但默认操作路径已变为“选方案 → 确认/修改课程锚点 → 保存”。
- 视频脚本节点摘要中展示同一个课程锚点，优先读取 `selected_anchor`，兼容 `anchor_to_lesson`。
- API client 错误 message 会附带后端 `details` 摘要，便于承接 T059 后端字段级错误。

### 涉及文件

- `apps\web\src\lib\api-client.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）
- `docs\qa-audits\t060-anchor-ui-evidence.json`
- `docs\qa-audits\t060-intro-selection-dom-evidence.txt`
- `docs\qa-audits\t060-video-script-dom-evidence.txt`

### 验证

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器证据：隔离 API `8060` + Web `3060`，项目 `proj_dc79e4da64e2`。
  - 选择“电梯按钮”方案后，`primary_design_id=design_application_02`，`selected_design_ids=[design_application_02]`。
  - `selected_anchor` 先自动写入该方案 `anchor_to_lesson`。
  - 手工修改为：`电梯按钮闪烁时必须先数清楼层数字，接回5以内数的认识任务。`
  - 保存后后端 `intro_selection` 节点落盘同一 `selected_anchor`。
  - 确认后进入 `intro_video_script`，生成视频脚本，摘要展示同一课程锚点，旁白包含该锚点。
  - 浏览器 console error/warn 为 0。
  - 证据文件：
    - `docs\qa-audits\t060-anchor-ui-evidence.json`
    - `docs\qa-audits\t060-intro-selection-dom-evidence.txt`
    - `docs\qa-audits\t060-video-script-dom-evidence.txt`

### 剩余风险

- 截图接口在本轮浏览器环境中连续超时，已用 DOM 快照 + API 产物 + 控制台日志 JSON 替代。
- 课程锚点完整端到端质量仍需测试工程师执行 T061，覆盖 `storyboard` 末帧字幕和旧 DeepSeek + placeholder MP4 E2E 不回退。

### 建议下一个接手角色

测试工程师接 T061，做课程锚点专项回归。

---

## 【本轮】后端工程师 — T058 lesson_plan 课程锚点契约修复

### 本轮目标

接 T058，修复 `lesson_plan` 课程锚点契约：`lesson_plan/generate` 必须稳定产出 9 套导入视频策划卡，science/application/story 各 3 套；每套包含“独立创意 + 课堂接入”两层字段，且 9 套 `anchor_to_lesson` 各不相同、不得是抽象套语。

### 已完成事项

- 升级 `apps\api\app\services.py` 的 `lesson_plan` prompt，明确 9 套导入视频策划卡、三类各 3 套、13 个必填字段和锚点红线。
- 重写 `lesson_plan` 归一化兜底：旧版 1-3 套 provider 输出会被补齐到 9 套完整强锚点，并替换过短、重复或抽象锚点。
- 更新 `workflow\schemas\lesson_plan.schema.json`：`intro_designs` 固定 9 条，intro_design 必填字段扩展为 13 个，`recommend_score` 改为 1-100。
- 补充后端契约测试，覆盖字段完整性、9 套数量、三类分布、锚点不同、禁用抽象锚点、prompt 不再要求旧版 3 套，以及真实 provider 返回旧 3 套时的归一化。

### 验证

- 红灯验证：新增 T058 测试最初失败，表现为旧归一化只返回 3 套、旧 prompt 不包含 9 套要求。
- 目标测试：`python -m pytest apps\api\tests\test_real_providers.py::test_lesson_plan_normalization_produces_nine_complete_intro_designs apps\api\tests\test_real_providers.py::test_lesson_plan_prompt_requires_nine_distinct_anchor_designs -q`：`2 passed`。
- 相关回归：`python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_textbook_pdf_parsing.py apps\api\tests\test_video_demo_contract.py apps\api\tests\test_api_contract.py -q`：`47 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`59 passed, 2 xfailed`。
- Schema 解析：`python -m json.tool workflow\schemas\lesson_plan.schema.json`：通过。

### 已更新文件

- `apps\api\app\services.py`
- `apps\api\tests\test_real_providers.py`
- `workflow\schemas\lesson_plan.schema.json`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`

### 剩余风险

- 本轮只完成 T058 的 `lesson_plan` 端契约修复，不改前端。
- 当前工作树已存在 T059 相关实现和交接记录；后续仍建议按 T059/T060/T061 做专项复核，尤其是前端课程锚点确认控件和测试工程师完整回归。
- 真实 DeepSeek live smoke 未在本轮执行；本轮通过 stub/provider 契约测试和 fake/placeholder 回归证明结构稳定。
- 课程锚点内容质量仍需产品/测试人工抽查，自动化当前只阻断数量、字段、重复和明显抽象套语。

### 建议下一个接手角色

测试工程师在 T060 前端控件完成后接 T061 做课程锚点专项回归；首席系统架构师可先复核当前 T058/T059 后端实现是否允许 T060 开始联调。

---

## 【本轮】后端工程师 — T059 selected_anchor 与 R047/R048/R049 修复

### 本轮目标

修复课程锚点链路：让 `intro_selection.selected_anchor` 成为正式用户确认锚点，并让 `intro_video_script` 与 `storyboard` 可验证地继承该锚点。

### 已完成事项

- `workflow\schemas\intro_selection.schema.json` 新增必填字段 `selected_anchor`，类型 `string`，`minLength=10`。
- `intro_selection` 生成归一化会从选中方案的 `anchor_to_lesson` 写入 `selected_anchor`，作为用户最终确认版课程锚点默认值。
- `intro_selection` prompt 已要求输出 `selected_anchor`，并说明其来自选中方案 `anchor_to_lesson`，表示用户最终确认版课程锚点。
- R047：`validate_edit_content()` 校验 `intro_selection.selected_anchor`；新增 `WorkflowService.approve_node()`，approve 前通过 `validate_approve_content()` 阻断缺失或过短锚点。
- R048：`intro_video_script/generate` 前调用 `_assert_selected_anchor()`，缺失 `intro_selection.selected_anchor` 时返回 `400 / GENERATION_INPUT_INVALID`；脚本归一化强制 `anchor_to_lesson=selected_anchor`，旁白末句追加/落在 selected_anchor。
- R049：`storyboard` 生成时额外加载 `intro_selection` 和 `intro_video_script` 上下文，归一化后执行 `_storyboard_anchor_warnings()`；末帧字幕未命中锚点关键词时返回 `rule_warnings`，不阻断现有 final_video 链路。
- Fake provider 已同步输出/继承 `selected_anchor`，旧真实 provider stub 测试也更新到新契约。

### 实现位置

- R047：`apps\api\app\services.py` 的 `validate_edit_content()`、`validate_approve_content()`、`WorkflowService.approve_node()`。
- R048：`apps\api\app\services.py` 的 `WorkflowService.generate_node()`、`_assert_selected_anchor()`、`_normalize_intro_video_script()` 和 `intro_video_script` prompt。
- R049：`apps\api\app\services.py` 的 `_normalize_storyboard()`、`_storyboard_anchor_warnings()`、`_anchor_keywords()`。

### 验证

- 新增/补充测试覆盖：
  - `intro_selection` 缺 `selected_anchor` edit 失败。
  - `intro_selection` 过短 `selected_anchor` edit/approve 失败。
  - `intro_video_script/generate` 缺 `selected_anchor` 失败。
  - 旁白与 `anchor_to_lesson` 继承 `selected_anchor`。
  - `storyboard` 末帧锚点 warning 可验证。
- 聚焦测试：`python -m pytest apps\api\tests\test_video_demo_contract.py -q`：`10 passed`。
- 真实 provider/fullchain 回归：`python -m pytest apps\api\tests\test_fullchain_e2e_contract.py apps\api\tests\test_real_providers.py -q`：`28 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`59 passed, 2 xfailed`。

### 已更新文件

- `apps\api\app\services.py`
- `apps\api\app\providers.py`
- `apps\api\app\main.py`
- `workflow\schemas\intro_selection.schema.json`
- `apps\api\tests\test_video_demo_contract.py`
- `apps\api\tests\test_real_providers.py`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

### 剩余风险

- R049 当前按 warning/details 返回，不阻断 storyboard approve；符合本轮“不破坏 final_video 链路”的边界。
- 前端还需要 T060 做课程锚点确认/编辑控件，否则用户只能通过 JSON 编辑 `selected_anchor`。

---

## 【本轮】后端工程师3 — 章鱼哥 Apifox 全接口文档沉淀

### 本轮目标

根据用户提供的章鱼哥 AI Apifox 接口列表，并发调研图片、视频和本地历史卡点，形成后续他人可直接接手的本地接口对接文档。

### 已完成事项

- 确认并保存 13 份 Apifox 原文快照到 `docs\api-research\octo-apifox\raw\`。
- 新增总入口文档 `docs\api-research\octo-apifox\README.md`，覆盖接口索引、认证、图片/视频路线、失效接口、当前接入状态、历史卡点和复测命令。
- 更新 `skills\videogen\references\otuapi-apifox-video-matrix.md`，修正旧的 Referer 下载建议。
- 更新 `skills\videogen\SKILL.md`，沉淀 2026-06-21 真实 Omni smoke 结论：`omni_flash-10s` 可提交、完成并返回 `video_url`；下载不应强制加 `Referer`。
- 补强 `OctoVideoProvider` 的结果 URL 字段兼容，支持 `data.url`、`data.result_url`、`data.first_video_url`、`result.video_url`、`result.url`。
- 扩展 `apps\api\tests\test_real_providers.py`，把上述 URL 字段纳入契约测试。

### 关键结论

- ShanHaiEdu 真实视频默认先走章鱼哥 OTU/NewAPI：`POST /v1/videos` 提交，`GET /v1/videos/{task_id}` 查询，完成后从 URL 下载。
- 默认视频模型为 `omni_flash-10s`，`sora-2-12s` 作为第二选择；Veo、图片模型和失效接口必须显式指定后再用。
- `/v1/videos` 任务不能走 MiniMax 官方 `download --file-id` 路线。
- 下载章鱼哥完成 URL 时保留浏览器类 `User-Agent` 和 `Accept`，不要强行加 `Referer: https://otuapi.com/`。
- 当前后端仍未完整实现 multipart `input_reference` 和 `reference_image_ids -> images[]` 公网 URL 映射，这是后续真实视频质量链路的关键缺口。

### 验证

- 需执行：`python -m pytest apps\api\tests\test_real_providers.py -q`
- 需执行脱敏扫描：文档和脚本不得出现真实 `DEEPSEEK_API_KEY`、`OCTO_API_KEY` 值，只能出现变量名或 `<redacted>`。

### 建议下一个接手角色

- 后端工程师继续补 multipart/reference image 映射。
- 测试工程师在最新 API 重启后跑 `scripts\smoke-octo-real-video.ps1` 做真实 live 复测。

---

## 【本轮】首席系统架构师 — T057 课程锚点后端实现排查

### 本轮目标

接 T057，全面排查课程锚点在后端代码里的真实实现状态，判断当前代码是否满足“导入视频策划卡 + 课堂接入说明 + selected_anchor + R047/R048/R049”的新口径。

### 已完成事项

- 新增排查报告：`docs\qa-audits\2026-06-21-anchor-code-audit.md`。
- 更新 `workflow\multi-agent\dispatch.md`：T057 标记已完成，并新增 T058-T061 修复任务。
- 排查范围覆盖：`apps\api\app\services.py`、`workflow\schemas\lesson_plan.schema.json`、`workflow\schemas\intro_selection.schema.json`、`workflow\schemas\storyboard.schema.json`、`apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`。

### 关键结论

- 当前旧版 E2E 能跑通，但课程锚点闭环不通过。
- `lesson_plan/generate` 后端 prompt 仍只要求 3 个导入方案和旧字段，未接入 9 套方案、两层结构和 9 套锚点各不相同约束。
- `selected_anchor` 还不是 `intro_selection` 的正式字段；后端只有通用 JSON 落盘能力，没有课程锚点专项 schema、prompt 和 R047 校验。
- `intro_video_script` 没有把 `selected_anchor` 作为硬输入，也没有要求旁白最后一句体现锚点。
- `storyboard` 没有实现末帧 subtitle 体现锚点的 R049 检查。
- `lesson_plan.schema.json` 仍缺 `video_theme`、`eye_catch_tag`、`classroom_entry_question`、`no_pre_teach`、`entry_position`、`recommend_reason`。

### 下一棒角色

- 后端工程师：优先接 T058、T059，补契约、prompt、schema 和校验。
- 前端工程师：接 T060，补课程锚点确认/编辑控件。
- 测试工程师：等 T058-T060 完成后接 T061，做课程锚点专项回归。

### 架构裁决

下一步不应直接追真实视频 provider 质量验收。先补课程锚点闭环，否则真实视频生成会放大“视频和教案连接不自然”的内容风险。

---

## 【本轮】产品经理 — 导入视频真实意图与课程锚点口径更新

### 本轮目标

根据用户反馈，修正 P01 用户设定和 PRD 中对导入视频的理解：导入视频不是教案知识讲解前置稿，而是独立、有吸引力的开场短片，最后通过课程锚点自然接回课堂。

### 已完成事项

- 更新 `workflow\multi-agent\user-personas.md`：补充 P01 对导入视频的真实意图，明确"导入视频策划卡 + 课堂接入说明"两层结构。
- 更新 `docs\PRD.md`：新增导入视频与教案连接原则，明确课程锚点是唯一硬连接。
- 更新 `workflow\multi-agent\shared-facts.md`：同步为团队共同产品事实。
- 更新 `workflow\multi-agent\decisions.md`：登记 2026-06-21 导入视频课程锚点决策。
- 更新 `workflow\multi-agent\roles\product-manager.md`：沉淀产品经理记忆。

### 关键结论

- 如果本课需要导入视频，教案中的导入设计必须拆成两层：导入视频策划卡、课堂接入说明。
- 导入视频和教案之间的唯一硬连接字段是课程锚点。
- 课程锚点只负责把独立视频主题自然接回本课学习任务，不负责提前讲解知识点。
- 导入视频不得被教案限制成知识讲解，不能提前讲定义、方法、结论或课堂探究步骤。

### 建议下一个接手角色

首席系统架构师可判断是否需要下发前端/后端/测试同步任务；前端角色后续应检查视频方案卡片是否按"策划卡 + 接入说明"呈现；测试角色后续应把"视频不提前讲知识点"纳入验收口径。

---

> 本文件最新补充：后端工程师3完成真实 Octo 视频链路 T053-T056 基础实现，并将真实视频默认模型统一为 `omni_flash-10s`。真实模式 submit 失败不再黑盒，task/节点会持久化失败诊断；submit/query/download/compose 契约已补测试，真实 live smoke 需在 `VIDEO_PROVIDER_MODE=real` 且注入 Octo key 的 API 上执行。

---

## 【本轮】后端工程师3 — 真实视频生成链路 T053-T056 基础实现

### 本轮目标

落实真实视频生成链路计划：先让 Octo submit 503 可诊断，再补单镜头提交、查询、下载和多 clip 合成的后端基础能力，并保留 placeholder 演示兜底不被破坏。

### 已完成事项

- `final_video/generate` 真实模式改为 submit 前先创建本地 `submitting` task。
- Octo submit 失败时，task 会标记 `failed`，写入 `OCTO_REQUEST_FAILED`、HTTP 状态、retryable 和脱敏响应摘要。
- submit 失败时同步写入 `final_video` failed 节点，避免 `tasks=0`、`final_video=not_started` 的黑盒状态。
- task 返回补齐顶层字段：`provider_task_id`、`error_code`、`download_path`、`video_url_present`、`updated_at`。
- `GET /projects/{project_id}/tasks/{task_id}` 会查询 provider；完成后下载真实 clip 到 `clips/{shot_id}.mp4`。
- 新增 `GET /projects/{project_id}/clips/{filename}`，只允许下载项目 clips 目录下的 `.mp4`。
- 多 clip 全部 `completed + downloaded` 后才尝试合成 `outputs/final_video.mp4`。
- 合成依赖 `ffmpeg`；缺失或失败记录 `FINAL_VIDEO_COMPOSE_FAILED`，不写 placeholder 冒充真实成片。
- 新增真实视频专项 smoke：`scripts\smoke-octo-real-video.ps1`。
- 真实视频默认模型调整为 `omni_flash-10s`；仍走 OTU/NewAPI task 路线，不走 MiniMax `file_id` 下载路径。
- 新增复测指南：`docs\qa-audits\2026-06-21-real-video-rerun-guide.md`。
- 更新 `apps\api\README.md` 的真实 Octo smoke 命令入口。

### 验证

- 红灯验证：新增真实视频 submit 失败测试最初失败，表现为 `tasks=[]`；成功 submit 测试最初缺少顶层 `provider_task_id`。
- 目标 provider 测试：`python -m pytest apps\api\tests\test_real_providers.py -q`：`19 passed`。
- placeholder fullchain 回归：`python -m pytest apps\api\tests\test_fullchain_e2e_contract.py -q`：`1 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`48 passed, 2 xfailed`。
- PowerShell AST：`scripts\smoke-octo-real-video.ps1` parse-ok。

### 剩余风险

- 本轮未执行真实 Octo live smoke；需 API 按 `VIDEO_PROVIDER_MODE=real` 注入真实 Octo key 后运行。
- 单镜头 smoke 只证明 provider submit/query/download，不代表最终视频质量。
- 真实多镜头合成依赖本机 `ffmpeg`；缺失时不会伪造成片。
- 音频、男声、英文音频检测和艺术质量仍是后续质量任务。

### 建议下一个接手角色

测试工程师执行 `scripts\smoke-octo-real-video.ps1` 的真实 live smoke；首席系统架构师根据真实 Octo 返回结果裁决是否继续 Octo 或切换供应商。

---

## 【历史】测试工程师 — T052 全链路轻量 E2E 复测

### 本轮目标

验证 T047 阻塞修复后，系统能在本地以真实 DeepSeek 文本链路 + placeholder MP4 视频链路完整跑通：PDF 上传 → 教材解析 → 字段回填/手改 → 知识点 Markdown → 教案生成 → 视频脚本链 → `final_video/generate` → MP4 下载 → PPT 导出下载。

### 执行环境

- API：`http://127.0.0.1:8152`
- Web：`http://127.0.0.1:3152`
- Storage：`storage-t052-fullchain-e2e`
- 文本 Provider：`PROVIDER_MODE=real`
- 视频 Provider：`VIDEO_PROVIDER_MODE=placeholder`
- 运行态脱敏确认：
  - `provider_mode=real`
  - `video_provider_mode=placeholder`
  - `provider_class=DeepSeekTextProvider`
  - `video_provider_is_none=True`
- Web：真实 API 模式
- 测试账号：`qa-t052`
- 项目：`T052全链路复测`
- 项目 ID：`proj_ef5de05702de`
- 未输出任何 DeepSeek / Octo 密钥。

### 已完成事项

- API `/health` 正常，Web 首屏 200。
- fixture PDF 上传成功。
- `textbook_parse` 生成、字段回填、字段手工修改、知识点 `kp_001` Markdown 均通过，节点已确认。
- `lesson_plan` 使用真实文本 provider 生成并确认，教案 Markdown 包含“5以内数的认识”。
- 5 个视频脚本链节点均生成并确认：
  - `intro_selection`
  - `intro_video_script`
  - `intro_video_screenplay`
  - `intro_video_asset`
  - `storyboard`
- `final_video/generate` 返回 `200`，`status=running`，顶层和 content 均返回 `video_path=outputs/final_video.mp4`。
- `/projects/{id}/tasks` 返回 6 个 `generated` task。
- `GET /projects/{id}/outputs/final_video.mp4` 返回 `200`，content-type 为 `video/mp4`。
- `POST /projects/{id}/export/ppt` 返回 `200`。
- `GET /projects/{id}/exports/lesson-video-demo.pptx` 返回 `200`。
- PPT 内存在 `ppt/media/media1.mp4`，且该内嵌 MP4 sha256 与下载 MP4 一致。
- 浏览器真实 API 模式首页显示项目 `最终视频 / 90%`。
- 工作区最终视频结果页显示：
  - `演示视频文件已生成`
  - `下载 MP4`
  - `路径：outputs/final_video.mp4`
  - `交付 PPT`
  - 导出后显示 `lesson-video-demo.pptx` 和 `下载 PPT`
- 浏览器应用级 `error/warn` 为空。

### 关键证据

- 测试报告：`docs\qa-audits\2026-06-21-fullchain-e2e-t052-rerun.md`
- API 证据：`docs\qa-audits\t052-1782019558-api-evidence.json`
- 浏览器证据：`docs\qa-audits\t052-browser-evidence.json`
- 下载 MP4：`docs\qa-audits\t052-1782019558-final_video.mp4`
- 下载 PPT：`docs\qa-audits\t052-1782019558-lesson-video-demo.pptx`

### 当前结论

T052 复测【通过】。

T047 阻塞点已关闭：`PROVIDER_MODE=real` 不再误触发真实 Octo；在 `VIDEO_PROVIDER_MODE=placeholder` 下 `final_video/generate` 可产出主链路 MP4，并被 PPT 导出复用。

### 剩余风险

- 本轮只代表本地轻量 E2E 可演示，不代表上线验收通过。
- placeholder MP4 只证明链路产物、下载和 PPT 嵌入可用，不代表真实视频质量。
- 真实 Octo provider、音频、剪辑、转码、正式鉴权、多租户、部署和性能均未覆盖。
- `t052-web.log` 有 Next.js dev server 跨源开发提示；浏览器采集的应用级 error/warn 为空，不阻塞本轮。

### 建议下一个接手角色

首席系统架构师复核 T052，对照 T047 阻塞修复目标裁决是否关闭本阶段阻塞并进入下一阶段。

---

---

## 【本轮】首席系统架构师 — T048-T051 架构验收

### 验收目标

复核 T047 阻塞修复是否达到 T052 复测前置条件：文本 provider 与视频 provider 解耦、`final_video/generate` placeholder 主链路可产 MP4、PPT 复用同一 MP4、前端能展示 MP4/PPT 下载入口。

### 代码与交接复核

- T048：`Settings` 已新增 `video_provider_mode`，默认 `placeholder`；`main.py` 中 `PROVIDER_MODE=real|deepseek` 只决定 DeepSeek 文本 provider，只有 `VIDEO_PROVIDER_MODE=real` 才初始化 `OctoVideoProvider`。
- T049：`video_provider=None` 时 `final_video/generate` 走占位链路，返回顶层和 `content.video_path=outputs/final_video.mp4`，并保留 final_video 任务记录。
- T050：新增 `apps\api\tests\test_fullchain_e2e_contract.py`、`scripts\smoke-fullchain-e2e.ps1` 和复测指南。
- T051：最终视频结果页可展示“演示视频文件已生成”、MP4 下载入口、PPT 下载入口；`OCTO_REQUEST_FAILED` 有可读提示。

### 新鲜验证

- 后端专项：`python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_video_demo_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_fullchain_e2e_contract.py -q`：`18 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`44 passed, 2 xfailed`。
- 前端：`cd apps\web; bunx tsc --noEmit --pretty false; bun run lint; bun run build`：通过。
- 隔离 smoke：启动 `PROVIDER_MODE=fake` + `VIDEO_PROVIDER_MODE=placeholder` API 于 `8191`，执行 `scripts\smoke-fullchain-e2e.ps1` 通过；产出 48 bytes MP4，PPT 下载成功，PPT 内 `embedded_mp4=1`。

### 结论

T048-T051 架构验收【通过】，可以进入 T052。

### T052 注意事项

- 必须重启最新 API，不要复用当前可能旧口径的 `8000` 服务。
- 必须确认运行环境为 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`。
- T052 仍要做真实 DeepSeek 文本链路 + placeholder MP4 的完整浏览器/API E2E，覆盖 PDF 上传到 PPT 下载。
- 当前通过不代表上线发布，不代表真实 Octo 视频 provider 可用。

---

## 【本轮】后端工程师3 — T050 fullchain E2E 契约测试与复测脚本

### 本轮目标

补全可重复执行的 fullchain E2E 契约测试、PowerShell smoke 脚本和复测指南，让团队不再靠手动拼接口判断链路。

### 已完成事项

- 新增 `apps\api\tests\test_fullchain_e2e_contract.py`。
- 契约测试覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 服务创建，且确认 `video_provider is None`，不会触发真实 Octo。
- 契约测试通过接口完成：创建项目、上传教材输入、推进到 `storyboard=approved`、调用 `final_video/generate`、下载 `outputs/final_video.mp4`、导出 PPT、检查 PPT 内存在 `ppt/media/*.mp4`。
- 新增 `scripts\smoke-fullchain-e2e.ps1`，参数包含 `ApiBaseUrl`、`ProjectName`、`FixturePath`。
- smoke 脚本只走 HTTP 接口，不直接写数据库或伪造结果；默认生成文本 fixture，显式 `-FixturePath` 可复测 PDF。
- smoke 脚本输出脱敏，不打印真实 `DEEPSEEK_API_KEY` 或 `OCTO_API_KEY`。
- 新增 `docs\qa-audits\2026-06-21-fullchain-e2e-rerun-guide.md`，写明启动命令、环境变量、通过标准和失败证据。
- 本轮未改前端，未读取或输出真实密钥。

### 验证

- 指定 pytest：`python -m pytest apps\api\tests\test_fullchain_e2e_contract.py -q`：`1 passed`。
- 指定 live smoke 对当前 `http://127.0.0.1:8000` 执行过；该服务健康检查通过，但运行 provider 表现为 Minimax/旧 schema，`lesson_plan/generate` 返回 `502 / MINIMAX_JSON_INVALID / Missing required JSON field: textbook_anchor`，不符合 T050 指南要求的 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 运行口径。
- 脚本机制验证：隔离启动 `PROVIDER_MODE=fake` + `VIDEO_PROVIDER_MODE=placeholder` API 于 `http://127.0.0.1:8182`，执行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-fullchain-e2e.ps1 -ApiBaseUrl http://127.0.0.1:8182 -ProjectName "T050 script verify"` 通过；产物包含 48 bytes MP4、PPT 内 `embedded_mp4=1`、`summary.json`。

### 已更新文件

- `apps\api\tests\test_fullchain_e2e_contract.py`
- `scripts\smoke-fullchain-e2e.ps1`
- `docs\qa-audits\2026-06-21-fullchain-e2e-rerun-guide.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

### 剩余风险

- `outputs\final_video.mp4` 仍是占位 MP4，只证明本地链路和交付物存在。
- 当前 8000 live 服务不是 T052 目标运行口径；测试工程师执行 T052 前需按指南重启 API，并确认 `PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=placeholder`。
- PDF live smoke 需要 API 进程已重启到支持 PDF 解析的最新代码；否则可能返回 `GENERATION_INPUT_INVALID / Unsupported textbook type for MVP: .pdf`。

### 建议下一个接手角色

测试工程师执行 T052。复测前先按 `docs\qa-audits\2026-06-21-fullchain-e2e-rerun-guide.md` 启动 API，再运行 smoke 脚本；如需 PDF 口径，显式传入 PDF fixture。

---

> 历史最新补充：前端工程师完成 T051 最终视频节点体验收口。最终视频结果页现在可展示 MP4 下载、保留 PPT 下载，并对 `OCTO_REQUEST_FAILED` 给出可读恢复提示。

---

## 【本轮】后端工程师 2 — T049 final_video 占位视频主链路核验

### 本轮目标

修复并核验 `final_video/generate` 占位视频主链路，让本地端到端实测不再依赖 `export/ppt` 兜底。

### 已完成事项

- 读取 `docs\fullchain-e2e-recovery-plan.md` 和 T049 指定后端文件。
- 核验 T048 后当前 `main.py` 已按 `VIDEO_PROVIDER_MODE` 解耦：`placeholder|fake` 对应 `video_provider=None`，`real` 才初始化 Octo。
- 核验 `services.py` 当前在 `video_provider=None` 时已走占位链路，并调用 `ensure_final_video_output(project_dir)`。
- 核验 `final_video/generate` 响应顶层返回 `video_path=outputs/final_video.mp4`，`content.video_path` 同样返回该路径。
- 核验 `/projects/{project_id}/outputs/final_video.mp4` 下载接口返回 `video/mp4`。
- 核验 `/projects/{project_id}/tasks` 仍可查询 `final_video` 任务记录。
- 核验 `export/ppt` 复用 `ensure_final_video_output()`，不覆盖已有 `outputs/final_video.mp4`。
- 新增测试 `test_fake_video_generation_reuses_existing_final_video_output`，锁定 `final_video/generate` 不覆盖已有 MP4。
- 本轮未调用真实 Octo，未改前端 UI，未打印任何密钥。

### 验证

- T049 指定验收：`python -m pytest apps\api\tests\test_video_demo_contract.py::test_fake_video_generation_chain_creates_queryable_tasks apps\api\tests\test_ppt_export.py -q`：`3 passed`。
- 真实阻塞组合相关契约：`python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_video_demo_contract.py -q`：`15 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`：`44 passed, 2 xfailed`。

### 已更新文件

- `apps\api\tests\test_video_demo_contract.py`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

### 剩余风险

- `outputs\final_video.mp4` 仍是占位 MP4，只用于本地 E2E 演示。
- 真实 Octo provider、视频质量、音频、剪辑、转码仍不在本轮范围。
- 既有两个 xfail 仍未处理，不能视为上线验收完成。

### 建议下一个接手角色

后端工程师3继续 T050，补 fullchain E2E 契约测试、PowerShell smoke 脚本和复测指南；测试工程师等待 T048-T051 完成后执行 T052。

---

## 【本轮】前端工程师 — T051 最终视频节点用户可用体验收口

### 本轮目标

在不改后端、不重构工作区大组件、不改整体 UI 版式的前提下，让真实 API 模式下的最终视频节点支持 placeholder MP4 下载、PPT 下载，并在真实视频 provider 失败时给用户可理解的提示。

### 已完成事项

- 最终视频结果页新增/强化 MP4 下载面板。
- placeholder 成功时使用“演示视频文件已生成”文案，明确这是本地演示用 MP4，不误导为真实 AI 视频成片完成。
- MP4 路径提取兼容：
  - 节点 `content.video_path`
  - `final_video/generate` mutation 顶层 `video_path`
  - task `result.download_path`
  - task `result.video_path`
  - PPT 导出返回的 `video_path`
- MP4 下载链接按后端返回路径或约定路径拼接为 `/projects/{project_id}/outputs/final_video.mp4` 这类 API 下载地址。
- 保留现有“交付 PPT”面板，PPT 导出成功后继续展示 `download_url` 下载入口。
- API client 错误信息现在保留非 `HTTP_ERROR` 的后端错误码，便于前端识别 `OCTO_REQUEST_FAILED`。
- 若最终视频生成失败信息包含 `OCTO_REQUEST_FAILED`，结果页显示“真实视频服务暂不可用，可切换占位视频模式完成本地演示”，并保留原始错误信息，不吞掉失败。

### 涉及文件

- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\api-mappers.ts`
- `apps\web\src\lib\types.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 验证状态

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过；Next 仍显示 `Skipping validation of types`，已由独立 tsc 覆盖类型检查。

### 下一步

- 等 T049/T050 完成后，由测试工程师执行 T052 完整轻量 E2E：真实 DeepSeek 文本链路 + `VIDEO_PROVIDER_MODE=placeholder` + MP4 下载 + PPT 下载。
- 若要覆盖浏览器证据，建议沿用隔离 API/Web 端口，进入最终视频节点后点击“生成草稿”确认 MP4 下载入口，再点击“导出 PPT”确认 PPT 下载入口。

---

> 历史最新补充：首席系统架构师已基于 T047 阻塞制定 T048-T052 修复计划。下一轮安排三个后端和一个前端并行，目标是本地端到端可实测：真实 DeepSeek 文本链路 + placeholder MP4 + PPT 下载。

---

## 【本轮】后端工程师 1 — T048 文本 Provider 与视频 Provider 模式拆分

### 本轮目标

修复 T047 阻塞根因：`PROVIDER_MODE=real` 同时控制 DeepSeek 文本 provider 和 Octo 视频 provider，导致本地 E2E 在 `final_video/generate` 误触发真实视频服务。

### 已完成事项

- `Settings` 新增 `video_provider_mode`。
- 新增环境变量 `VIDEO_PROVIDER_MODE`，默认值为 `placeholder`。
- `PROVIDER_MODE=real|deepseek` 现在只决定文本 provider 使用 DeepSeek。
- `VIDEO_PROVIDER_MODE=real` 时才初始化 `OctoVideoProvider`。
- `VIDEO_PROVIDER_MODE=placeholder|fake` 时 `video_provider=None`。
- 更新 `apps\api\.env.example`，新增 `VIDEO_PROVIDER_MODE=placeholder`。
- 更新 `apps\api\README.md`，说明本地 E2E 推荐 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`。
- 更新 `docs\llm-provider-contract.md`，明确文本 provider 与视频 provider 的环境变量边界。
- 新增契约测试覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 不初始化 Octo。

### 修改文件

- `apps\api\app\settings.py`
- `apps\api\app\main.py`
- `apps\api\.env.example`
- `apps\api\README.md`
- `docs\llm-provider-contract.md`
- `apps\api\tests\test_api_contract.py`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

### 验证

- 红灯验证：新增测试最初失败，原因是 `Settings` 没有 `video_provider_mode`。
- 修复后目标测试：`python -m pytest apps\api\tests\test_api_contract.py::test_real_text_provider_with_placeholder_video_mode_does_not_initialize_octo -q`：`1 passed`。
- 用户指定验收命令：`python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_video_demo_contract.py -q`：`14 passed`。
- 脱敏运行态检查：`provider=deepseek`、`video_provider_is_none=True`、`video_mode=placeholder`。

### 剩余风险

- 本轮不追真实 Octo provider 稳定性。
- `VIDEO_PROVIDER_MODE=real` 的真实视频任务仍需后续独立 smoke 和错误兜底。
- 当前只完成 T048 配置拆分；完整 T052 复测还依赖 T049/T050/T051 全部交付。

---

## 【本轮】首席系统架构师 — T047 阻塞后端到端可实测修复计划

### 背景

T047 不是上线验收，而是本地完整轻量 E2E。测试已证明 DeepSeek 文本链路跑到 `storyboard=approved`，PPT 兜底链路也能生成并嵌入占位 MP4。真正阻塞点是 `PROVIDER_MODE=real` 同时控制文本和视频，导致 `final_video/generate` 调用真实 Octo provider 并遇到 `503`。

### 架构裁决

本轮不追真实视频 provider 稳定性，先保证用户可端到端实测。运行模式拆分为：

- `PROVIDER_MODE=real`：只控制 DeepSeek 文本链路。
- `VIDEO_PROVIDER_MODE=placeholder`：控制本地演示视频链路，`final_video/generate` 直接产出 `outputs/final_video.mp4`，不调用 Octo。

### 已新增文档

- `docs\fullchain-e2e-recovery-plan.md`

### 已新增任务

- T048 后端工程师1：拆分文本 provider 与视频 provider 模式，新增 `VIDEO_PROVIDER_MODE=placeholder|fake|real`。
- T049 后端工程师2：修复 `final_video/generate` 占位视频主链路，保证主链路产出并下载 `outputs/final_video.mp4`。
- T050 后端工程师3：补 fullchain E2E 契约测试、PowerShell smoke 脚本和复测指南。
- T051 前端工程师：最终视频节点展示 MP4 下载入口、PPT 下载入口和真实视频 provider 失败的可读提示。
- T052 测试工程师：等待 T048-T051 完成后复跑完整轻量 E2E。

### 当前目标

本地用户可用：PDF 上传 → 教材解析 → 教案生成 → 视频脚本链 → final_video 占位 MP4 → MP4 下载 → PPT 下载。

### 硬边界

- 不做上线发布。
- 不追真实 Octo 视频生成稳定性。
- 不做音频、转码、剪辑。
- 不打印、不提交任何真实密钥。

---

## 【本轮】测试工程师 — T047 全链路冲刺验收

### 本轮目标

在真实 DeepSeek + 占位 MP4 口径下执行本地完整轻量 E2E：PDF 上传 → 教材解析 → 字段回填/知识点选择 → 教案生成 → 5 个视频脚本链节点 → `final_video/generate` → MP4 下载 → PPT 导出与下载。

### 执行环境

- API：`http://127.0.0.1:8147`
- Web：`http://127.0.0.1:3147`
- Storage：`storage-t047-fullchain-e2e`
- Provider：`PROVIDER_MODE=real`
- Web：真实 API 模式
- 测试账号：`qa-t047`
- 项目：`T047全链路冲刺验收`
- 项目 ID：`proj_b930449fae90`
- 未输出任何 DeepSeek key。

### 已通过事项

- API `/health` 正常，Web 首屏 200。
- fixture PDF 上传成功。
- `textbook_parse` 生成、字段回填、字段手工修改、知识点 `kp_001` Markdown 均通过，节点已确认。
- `lesson_plan` 使用真实 DeepSeek 生成并确认，教案 Markdown 包含“5以内数的认识”。
- 5 个视频脚本链节点均生成并确认：
  - `intro_selection`
  - `intro_video_script`
  - `intro_video_screenplay`
  - `intro_video_asset`
  - `storyboard`
- 浏览器真实 API 模式可读取该项目，首页/工作区显示 `最终视频 / 90%`。
- 浏览器控制台应用级 `error/warn` 为空。

### 阻塞点

`POST /projects/proj_b930449fae90/nodes/final_video/generate` 返回：

- HTTP `502`
- error code：`OCTO_REQUEST_FAILED`
- message：`HTTP 503`
- retryable：`true`

后续状态：

- `final_video=not_started`
- `/projects/{id}/tasks` 返回 0 个任务。
- `/projects/{id}/outputs/final_video.mp4` 返回 `404 / OUTPUT_NOT_FOUND`。
- 浏览器最终视频运行页显示“后端动作执行失败 / HTTP 503”。

### 判断

T047 结论：【阻塞】。

原因是当前后端把 `PROVIDER_MODE=real` 同时用于 DeepSeek 文本 provider 和 Octo 视频 provider；T047 需要的是“真实 DeepSeek 文本 + 占位 MP4 视频”，但当前没有独立的视频 placeholder/no-provider 模式。

### 补充定位

阻塞后单独调用 `POST /projects/{id}/export/ppt` 可成功：

- 生成并下载 `outputs/final_video.mp4`，content-type 为 `video/mp4`。
- 生成并下载 `lesson-video-demo.pptx`。
- PPT 内 `ppt/media/media1.mp4` 的 hash 与下载 MP4 一致。

这说明 PPT 兜底链路可用，但 `final_video/generate` 主链路没有复用占位 MP4 逻辑，因此不判定 T047 通过。

### 已更新文件

- `docs\qa-audits\2026-06-21-fullchain-e2e.md`
- `docs\qa-audits\t047-blocked-final-video-error.json`
- `docs\qa-audits\t047-preblock-node-summary.json`
- `docs\qa-audits\t047-browser-evidence.json`
- `docs\qa-audits\t047-postblock-ppt-evidence.json`
- `docs\qa-audits\t047-postblock-final_video.mp4`
- `docs\qa-audits\t047-postblock-lesson-video-demo.pptx`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

后端工程师。

建议修复方向：拆分文本 provider 与视频 provider 的运行模式，例如 `PROVIDER_MODE=real` 负责 DeepSeek 文本链路，新增 `VIDEO_PROVIDER_MODE=placeholder|real|fake` 控制 `final_video/generate`；本地 T047 演示应运行在 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`。

---

---

## 【本轮】首席系统架构师 — 后端2视频产物闭环验收

### 验收目标

复核后端2是否完成 fake/no-provider 模式下最终视频文件产物闭环，支撑本地端到端演示继续推进到 MP4 下载和 PPT 导出下载。

### 代码检查

- `apps\api\app\video_outputs.py` 已抽出统一 `FINAL_VIDEO_REL_PATH=outputs/final_video.mp4` 和 `ensure_final_video_output(project_dir)`。
- `apps\api\app\services.py` 的 `final_video/generate` 已同步确保最终视频文件存在，并在顶层 `video_path` 与 `content.video_path` 返回同一路径。
- `apps\api\app\main.py` 已提供 `GET /projects/{project_id}/outputs/final_video.mp4`，返回 `video/mp4`。
- `apps\api\app\ppt_exporter.py` 已复用 `ensure_final_video_output()`，不会在已有 `outputs/final_video.mp4` 时覆盖成另一份占位视频。
- `apps\api\tests\test_video_demo_contract.py` 覆盖最终视频生成、任务查询、MP4 文件存在和下载。
- `apps\api\tests\test_ppt_export.py` 覆盖 PPT 导出创建占位视频，以及复用已有最终视频文件并嵌入 PPT。

### 新鲜验证

- 专项测试：`python -m pytest apps\api\tests\test_video_demo_contract.py::test_fake_video_generation_chain_creates_queryable_tasks apps\api\tests\test_ppt_export.py -q`，结果 `3 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`，结果 `41 passed, 2 xfailed`。

### 结论

后端2视频产物闭环【通过】。

通过范围：fake/no-provider 口径下可以得到稳定的 `outputs/final_video.mp4`，可以下载 MP4，PPT 导出会嵌入并复用同一份视频文件。

### 剩余风险

- `final_video.mp4` 仍是最小占位 MP4，只证明端到端链路和交付物存在，不代表真实视频质量。
- 真实视频 provider、剪辑、配音、转码、任务队列和视频质量验收仍未完成。
- 完整浏览器路径 PDF 上传 → DeepSeek 教案 → 视频脚本链 → final_video → MP4 下载 → PPT 下载尚未由测试工程师复跑。

### 下一棒

- 测试工程师接 T047。
- T047 范围：真实 DeepSeek + 占位 MP4 口径下执行完整轻量 E2E，覆盖 PDF 上传、教材解析、字段回填/知识点选择、教案生成、5 个视频脚本链节点、`final_video/generate`、MP4 下载、PPT 导出和 PPT 下载。
- 本轮不再安排后端继续做事，除非 T047 暴露阻塞缺陷。

---

## 【本轮】首席系统架构师 — 前端 PPT 导出入口验收

### 验收目标

复核前端是否完成最终视频/交付区域的 PPT 导出按钮和下载入口，并判断是否可以进入测试回归。

### 代码检查

- `apps\web\src\lib\api-client.ts` 已提供 `exportProjectPpt(projectId)` 和 `resolveApiDownloadUrl(downloadUrl)`。
- `apps\web\src\lib\types.ts` 已有 `ApiPptExport`。
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx` 已在真实 API 模式、`video-generation` 结果页渲染 `PptExportPanel`。
- 导出成功后展示后端返回文件名和“下载 PPT”链接；失败时在面板内展示错误；loading 时按钮文案为“导出中...”。

### 验证

- 前端静态验证：`cd apps\web; bunx tsc --noEmit --pretty false; bun run lint; bun run build` 全部通过。
- 浏览器真实 API 验收：隔离 API `8175`，Web `3175`，项目 `proj_1c6012f6ad5d`。
- 页面状态：真实 API 首页显示目标项目 `最终视频 / 90% / 进入「最终视频」`。
- 工作区“最终视频 → 结果”页显示“交付 PPT”面板。
- 点击“导出 PPT”后显示：`已生成`、文件 `lesson-video-demo.pptx`、下载链接 `http://127.0.0.1:8175/projects/proj_1c6012f6ad5d/exports/lesson-video-demo.pptx`。
- 浏览器控制台 error/warn：空。

### 结论

前端 PPT 导出入口【通过】。当前通过范围是“已到 final_video 的项目可以导出 PPT 并展示下载入口”。还不是完整 PDF → PPT 用户路径验收。

### 下一步

- 等后端视频产物快速轨道补齐 `final_video.mp4` 下载/产物语义后，测试工程师执行完整轻量 E2E。
- E2E 范围：PDF 上传 → 教材解析 → DeepSeek 教案 → 视频脚本链 → final_video 产物 → PPT 导出下载。

---
> 本文件最新补充：后端工程师已打通 fake/no-provider 模式下 `final_video/generate` 同步产出 `outputs\final_video.mp4`、返回 `video_path`、提供 MP4 下载接口，并确保 PPT 导出复用同一份视频文件。

---

## 【本轮】后端工程师 — fake/no-provider 最终视频文件产物闭环

### 本轮目标

快速打通端到端“产视频文件”能力，服务全链路演示。目标不是视频质量，而是保证 fake/no-provider 模式下可稳定得到一个可下载、可嵌入、可交付的 `outputs\final_video.mp4`。

### 已完成事项

- 新增共享视频输出 helper：`apps\api\app\video_outputs.py`。
- `final_video/generate` 在 fake/no-provider 模式下同步确保 `outputs/final_video.mp4` 存在。
- `final_video/generate` 返回顶层 `video_path=outputs/final_video.mp4`，同时在 `content.video_path` 保留同一路径。
- 新增下载接口：`GET /projects/{project_id}/outputs/final_video.mp4`，返回 `video/mp4`。
- `export/ppt` 改为复用同一个 `ensure_final_video_output()`，如果 `outputs/final_video.mp4` 已存在，不覆盖、不重复生成另一份占位视频。
- 保留现有 fake task 查询能力：`/projects/{project_id}/tasks` 仍可查询 `final_video` 的 generated 任务。
- 本轮未接真实视频 provider，未读取或打印真实 provider key，未改前端 UI，未做复杂异步队列、剪辑、音频或转码链路。

### 验证

- TDD 红灯：新增测试后，`test_fake_video_generation_chain_creates_queryable_tasks` 先因缺少 `video_path` 失败。
- 目标测试：`python -m pytest apps\api\tests\test_video_demo_contract.py::test_fake_video_generation_chain_creates_queryable_tasks apps\api\tests\test_ppt_export.py -q`：`3 passed`。
- 全量后端：`python -m pytest apps\api\tests -q`：`41 passed, 2 xfailed`。

### 已更新文件

- `apps\api\app\video_outputs.py`
- `apps\api\app\services.py`
- `apps\api\app\ppt_exporter.py`
- `apps\api\app\main.py`
- `apps\api\tests\test_video_demo_contract.py`
- `apps\api\tests\test_ppt_export.py`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

### 剩余风险

- `final_video.mp4` 仍是最小占位 MP4，只用于端到端演示和 PPT 嵌入，不代表真实视频质量。
- 真实视频 provider、剪辑、音频、转码、任务队列仍未实现。
- 既有两个 xfail 仍保留：未配置 token 写接口开放、provider schema 缺必填字段严格拒绝。

### 建议下一个接手角色

测试工程师可执行 PDF → 教案 → 视频脚本链 → `final_video/generate` → 下载 MP4 → `export/ppt` 的轻量 E2E，确认前端演示链路使用同一份最终视频。

---

## 【本轮】后端工程师 — DeepSeek live smoke 与 LLM 输出链路修复

### 本轮目标

使用本地 `apps\api\.env` 中已配置的 DeepSeek 环境变量，启动后端 API，确认 `PROVIDER_MODE=real` 生效，并真实跑通从教材解析到分镜生成的 LLM 链路。禁止打印、提交或文档记录真实 API key。

### 脱敏配置核验

- `provider_mode=real`。
- 运行 provider 类：`DeepSeekTextProvider`。
- 服务端凭据已配置，仅核验存在与长度，未输出真实值。
- 本轮未读取或打印完整 `.env` 内容。

### Smoke 过程

运行方式：

- API：`python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8188`
- Storage：`storage-deepseek-live-smoke`
- 教材：fixture PDF `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`

HTTP 链路：

1. `GET /health`
2. `POST /projects`
3. `POST /projects/{project_id}/textbook`
4. `POST /projects/{project_id}/nodes/textbook_parse/generate`
5. approve 每个成功节点后继续下游
6. `lesson_plan/generate`
7. `intro_selection/generate`
8. `intro_video_script/generate`
9. `intro_video_screenplay/generate`
10. `intro_video_asset/generate`
11. `storyboard/generate`

### 首次失败与根因

首次 live smoke：

- `textbook_parse/generate` 成功。
- `lesson_plan/generate` 失败：`502 / DEEPSEEK_JSON_INVALID`。
- 错误摘要：缺少 `textbook_anchor`。

根因：

- provider 返回内容尚未进入 `services.py` 的 `_normalize_lesson_plan()`。
- `DeepSeekTextProvider.complete_json()` 在 provider 层先用 `workflow/schemas/lesson_plan.schema.json` 校验旧必填字段，导致可归一化的真实输出被提前拒绝。

### 修复

只改后端服务层：

- `apps\api\app\services.py`
- 在 `_schema_for_node()` 中对 `lesson_plan` 使用 provider 前置最小 schema：`lesson_plan_markdown` + `intro_designs`。
- 让真实 LLM 输出先进入 `_normalize_lesson_plan()`，由归一化补齐 `textbook_anchor`、`teaching_objectives`、`key_difficulty`、`teaching_flow`、`blackboard_design`。
- 未改前端，未重构 provider。

### 修复后结果

重启 API 后重新 live smoke，项目 `proj_b549543cb908`：

- `textbook_parse/generate`：成功，识别 `5以内数的认识`，`selected_kp=kp_001`。
- `lesson_plan/generate`：成功，`lesson_plan_markdown` 长度约 870，`intro_designs=3`。
- `intro_selection/generate`：成功，选中 1 个方案，primary 为 `design_story_01`。
- `intro_video_script/generate`：成功，时长 75 秒，旁白长度 144，禁用项 4 个。
- `intro_video_screenplay/generate`：成功，分场 5 个。
- `intro_video_asset/generate`：成功，资产 16 个。
- `storyboard/generate`：成功，分镜 8 个，首镜头字段齐全，`model_prompt` 含“旁白（男声，中文）”。

### 验证

- 目标回归：`python -m pytest apps\api\tests\test_real_providers.py::test_real_provider_mode_uses_deepseek_for_lesson_plan apps\api\tests\test_real_providers.py::test_real_provider_mode_generates_video_script_chain_with_shared_llm -q`：`2 passed`。
- 全量后端：`python -m pytest apps\api\tests -q`：`40 passed, 2 xfailed`。

### 剩余风险

- 本轮只验证真实 DeepSeek 文本链路，不验证真实视频 provider。
- 真实 LLM 内容质量未做人工教学质量验收，只验证 JSON 字段可被后端消费。
- `intro_video_asset` 真实输出数量偏多，本地演示可消费；后续可按成本和前端展示需要做数量上限策略。
- provider 层仍只做轻量字段校验，完整 schema/业务质量门禁需后续补。

---

## 【本轮】前端工程师 — PPT 导出按钮与下载入口接入

### 本轮目标

在不改整体 UI 版式、不接真实视频 provider 的前提下，把后端已有 `POST /projects/{project_id}/export/ppt` 暴露到工作区最终视频/交付相关区域，形成本地演示可点击的 PPT 导出与下载入口。

### 已完成事项

- 在工作区“最终视频”结果页增加“交付 PPT”面板。
- 点击“导出 PPT”调用已有 `exportProjectPpt(projectId)` API client。
- 导出中显示 loading 状态与“导出中...”文案，避免重复点击。
- 导出成功后展示后端返回的 `filename`，并显示“下载 PPT”入口。
- 下载入口使用后端返回 `download_url`，并通过 `NEXT_PUBLIC_API_BASE_URL` 对相对路径补全。
- 导出失败时在面板内展示可读错误，并通过 toast 提示。
- demo 模式不伪造导出成功；按钮只出现在真实 API 模式的最终视频结果分支。

### 涉及文件

- `apps\web\src\lib\api-client.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 验证状态

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过；Next 仍显示 `Skipping validation of types`，已由独立 tsc 覆盖类型检查。

### 下一步

- 测试工程师可在后端 live smoke 完成后，执行 PDF → 教案 → 视频脚本链 → PPT 导出的轻量 E2E。
- 真实视频 provider 未定前，PPT 导出仍可接受后端占位 MP4 口径。

---

> 历史最新补充：运维/部署工程师完成 DeepSeek 本地环境脱敏检查。`apps\api\.env` 已被 git ignore，后端可读取真实 provider 配置；测试工程师暂缓进场，等待后端 live smoke 和前端 PPT 导出按钮完成。

---

## 【本轮】运维/部署工程师 — DeepSeek 本地环境脱敏检查

### 本轮目标

只做本地 DeepSeek 环境脱敏检查，不回显真实 key；确认后端可从本地环境文件稳定读取真实 provider 配置，并给出后端启动与 fake 回退命令。

### 已完成事项

- 确认 `apps\api\.env` 命中 `.gitignore` 规则，不会进入 git 提交。
- 脱敏确认以下变量存在：
  - `PROVIDER_MODE=real`
  - `DEEPSEEK_API_KEY=<redacted>`
  - `DEEPSEEK_BASE_URL=<configured>`
  - `DEEPSEEK_MODEL=<configured>`
- 确认后端配置读取路径：`apps\api\app\settings.py` 会读取仓库 `.env` 与 `apps\api\.env`，进程环境变量优先于本地 `.env`。
- 确认 provider 路由：`PROVIDER_MODE=real` 或 `deepseek` 会在 `apps\api\app\main.py` 中使用 `DeepSeekTextProvider`。
- 本轮未调用真实 provider，未执行 live smoke，未输出真实密钥。

### 建议启动命令

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

如需避开默认端口：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8141
```

### 临时回退 fake 模式

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE='fake'
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

### 当前结论

- DeepSeek 本地环境读取基线：通过。
- 后端 live smoke：未执行，交给后端工程师。
- 测试工程师：暂缓进场；等待后端 live smoke 和前端 PPT 导出按钮完成后，再执行 `PDF 上传 → 教材解析 → 教案生成 → 视频脚本链 → PPT 导出下载` 的轻量 E2E。

### 下一步

- 后端工程师启动 API 后执行 DeepSeek live smoke，至少覆盖 `lesson_plan` 和一个视频脚本链节点，仍需脱敏日志。
- 前端工程师继续完成 PPT 导出按钮接入。
- 测试工程师等待上述两项完成后再进场。

---

> 历史补充：DeepSeek API 已完成脱敏 live smoke，并已写入本地后端忽略环境文件。后续开发统一查看 `docs\llm-provider-contract.md`，禁止回显真实 key。

---

## 【本轮】首席系统架构师 — DeepSeek 环境配置与 LLM 文档

### 本轮目标

验证用户提供的 DeepSeek API 是否可用；可用后写入项目本地环境变量，并补齐后续开发可查找的 LLM 接口文档。

### 已完成事项

- 使用 DeepSeek `/chat/completions` 做最小 JSON smoke，返回正常。
- 本地 `apps\api\.env` 已写入：`PROVIDER_MODE=real`、`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`。
- 已脱敏核验：`DEEPSEEK_API_KEY` 存在且长度正常；未在输出中展示真实值。
- 已确认 `apps\api\.env` 被 `.gitignore` 忽略，不会进入 git 提交。
- 新增 `docs\llm-provider-contract.md`，说明 provider 路由、环境变量、统一调用接口、错误码、节点契约、验证命令和安全要求。
- 更新 `apps\api\README.md`，增加 DeepSeek 模式入口并指向 LLM 文档。

### 证据

- DeepSeek smoke：返回 `DEEPSEEK_SMOKE_OK`，模型响应标识为 `deepseek-v4-flash`，JSON 内容正常。
- `.env` 脱敏核验：`PROVIDER_MODE=real`，`DEEPSEEK_API_KEY=<redacted>`，base URL 和 model 已配置。
- git ignore 核验：`apps\api\.env` 命中 `.gitignore` 规则。

### 下一步

- 后端工程师可直接启动 API，用真实 DeepSeek 跑 `lesson_plan` 和视频脚本链 live smoke。
- 前端工程师继续接 PPT 导出按钮。
- 测试工程师在 live smoke 后执行 PDF → 教案 → 脚本链 → PPT 的轻量 E2E。
- 真实视频 provider 仍待项目负责人裁决。

---
> 本文件最新补充：首席系统架构师完成全链路冲刺 Day1 基础实现复核。用户已明确本轮按 `docs\fullchain-sprint.md` 使用 DeepSeek；T044-T046 已完成本地基础能力，但尚未做真实 key live smoke 和真实视频 provider 验收。

---

## 【本轮】首席系统架构师 — 全链路冲刺 Day1 T044-T046

### 本轮目标

把当前 fake 教案/视频脚本链替换为可配置真实 LLM 入口，并先用占位 MP4 跑通 PPT 导出接口，支撑 PDF → 教案 → 视频脚本 → PPT 的下一轮端到端联调。

### 已完成事项

- 轨道 B：新增 `DeepSeekTextProvider`，支持 OpenAI-compatible `chat/completions`、JSON 输出解析、fenced JSON 兼容、必填字段校验和缺 key 错误；`PROVIDER_MODE=real` / `deepseek` 走 DeepSeek，`fake` 保留。
- 轨道 B：`lesson_plan/generate` 真实 provider prompt 已优先使用 `textbook_parse.selected_knowledge_point.markdown`，输出 `lesson_plan_markdown` 后会归一化为现有前端所需字段。
- 轨道 C：`intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 已复用同一 `complete_json` 入口，并新增节点级 prompt。
- 轨道 C：`storyboard` 支持把冲刺契约 3 的 `id/duration/scene/subject/subtitle/visual_type` 归一化为现有后端/前端使用的 `shot_id/duration_sec/main_subject/reference_image_ids/model_prompt` 等字段。
- 轨道 D：新增 `POST /projects/{project_id}/export/ppt`，使用 `python-pptx` 生成 `.pptx`；无真实视频时写入 `outputs/final_video.mp4` 占位 MP4，第 2 页嵌入该视频。
- 轨道 D：新增 `GET /projects/{project_id}/exports/{filename}` 下载导出文件。
- 前端底层：新增 `ApiPptExport` 类型和 `exportProjectPpt(projectId)` API client 方法，页面按钮尚未接入。
- 配置：`apps\api\.env.example` 已新增 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` 占位；未读取或写入真实密钥。

### 验证证据

- 目标测试：`python -m pytest apps\api\tests\test_real_providers.py::test_deepseek_text_provider_sends_openai_compatible_payload_and_auth apps\api\tests\test_real_providers.py::test_deepseek_text_provider_requires_api_key apps\api\tests\test_real_providers.py::test_real_provider_mode_uses_deepseek_for_lesson_plan apps\api\tests\test_real_providers.py::test_real_provider_mode_generates_video_script_chain_with_shared_llm apps\api\tests\test_ppt_export.py::test_export_ppt_creates_pptx_with_placeholder_video -q`，结果 `5 passed`。
- 后端全量：`python -m pytest apps\api\tests -q`，结果 `40 passed, 2 xfailed`。
- 前端验证：`cd apps\web; bunx tsc --noEmit --pretty false; bun run lint; bun run build`，全部通过。

### 当前结论

- T044-T046 判定为【通过】，但通过范围仅限本地基础能力、mock transport、占位视频导出。
- 这不代表真实 DeepSeek 线上调用通过，不代表真实视频 provider 通过，不代表 PPT 内容质量通过。
- T043 仍未完成：非 fixture PDF 的知识点 Markdown 稳定性还需要单独验收。

### 下一步任务派发建议

- 运维/部署工程师：在本地 `.env` 或运行环境中注入 DeepSeek 相关环境变量，只做脱敏验证，不回显真实值；给后端提供启动命令和确认 provider 模式的方法。
- 后端工程师：用真实 DeepSeek key 做 live smoke，至少覆盖 `lesson_plan` 和一个脚本链节点；失败时记录 provider 原始错误码但不得打印密钥。
- 前端工程师：在最终视频或交付节点接入“导出 PPT”按钮，调用 `exportProjectPpt`，成功后展示下载入口；不改 UI 大版式。
- 测试工程师：等运维和前端完成后，执行 PDF → 教案 → 视频脚本链 → PPT 导出的轻量端到端回归；真实视频 provider 未定前允许使用占位 MP4。
- 项目负责人：尽快裁决真实视频 provider，用于替换占位 MP4。

---
> 本文件最新补充：首席系统架构师完成 T042 阶段复核。教材解析到教案生成 T037-T042 在本地 fake provider + fixture 演示口径下通过；下一阶段进入 PDF → 教案 → 视频 → PPT 全链路打通冲刺，但大脑层 provider 口径需按项目默认 Minimax M3 执行，除非用户明确改为 DeepSeek。

---

## 【本轮】首席系统架构师 — T042 教材解析到教案生成阶段复核

### 本轮目标

复核 T038-T041 的后端、前端、测试交付，判断“教材解析到教案生成”阶段是否通过，并衔接下一阶段。

### 复核依据

- T038/T040 后端：fixture PDF 可解析，知识点 `kp_001` Markdown 可落盘，`lesson_plan/generate` 可读取该 Markdown。
- T039 前端：新建项目第 2 步已接入真实上传、解析按钮、字段回填/手改、知识点下拉和 Markdown 预览。
- T041 测试：`docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md` 最终结论为通过。
- T041 截图：`docs\qa-audits\t041-ui-textbook-parse-result.png`。
- 新鲜验证：后端 `python -m pytest apps\api\tests -q` 为 `35 passed, 2 xfailed`；前端 `tsc`、`lint`、`build` 均通过。

### 关键结论

- T037-T042 阶段复核【通过】。
- 通过范围：本地 fake provider + fixture 教材解析演示。
- 已验证链路：上传 fixture PDF → 真实接口解析教材 → 字段回填/手改 → 知识点下拉选择“5以内数的认识” → Markdown 预览 → 确认教材解析 → 生成基于知识点 Markdown 的教案 Markdown。
- 不代表上线验收通过，不代表生产级 MinerU 全书异步解析通过，不代表真实 Minimax 教案质量通过。

### 下一阶段裁决

进入全链路打通冲刺，目标是 PDF → 教案 → 视频 → PPT。冲刺文档为 `docs\fullchain-sprint.md`。

需要注意：`docs\fullchain-sprint.md` 写了 DeepSeek API，但项目规则中“大脑层文本生成默认走 Minimax M3”。除非用户明确批准改 provider，否则后端/大脑层真实 provider 按 Minimax M3 口径执行。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

后端工程师先拆全链路冲刺后端任务，前端工程师同步准备全链路状态入口和下载入口，测试工程师准备 PDF → 教案 → 视频 → PPT 的新 E2E 清单。

---

> 本文件最新补充：测试工程师继续 T041 并补齐 UI 子链路证据。API 主链路沿用本轮通过证据，浏览器 UI 内上传 PDF、解析教材、字段回填/手改、知识点下拉和 Markdown 预览均已补测通过，T041 最终结论更新为【通过】。

---

## 【本轮】测试工程师 — T041 UI 子链路补测

### 本轮目标

不重新测试 API 主链路，只补齐浏览器 UI 内“上传 PDF → 解析教材 → 字段回填 → 手改字段 → 知识点下拉 → Markdown 预览”的直接证据。

### 执行环境

- API：`http://127.0.0.1:8141`
- Web：`http://127.0.0.1:3141`
- Storage：`storage-t041-textbook-to-lesson-e2e`
- Provider：`fake`
- Web 模式：真实 API 模式
- 测试账号：`qa-t041-ui`
- UI 子链路项目：`T041-UI子链路-633528`
- UI 子链路项目 ID：`proj_358af9eac8c7`

### 已完成事项

- 使用支持文件上传的 Chrome DevTools 浏览器环境打开 Web。
- 登录真实 API 模式。
- 新建项目并进入第 2 步。
- 确认第 2 步显示真实后端解析入口：
  - `教材解析（真实后端）`
  - `上传 PDF 后调用后端解析教材`
  - `解析教材`
- 上传 fixture PDF 后，UI 显示文件名：
  - `1上-人教版小学数学课本（2024新版）.pdf`
- 点击 `解析教材` 后，UI 显示：
  - `解析中…`
  - `正在上传教材并调用后端解析…`
- 解析完成后，UI 显示：
  - `教材解析结果`
  - `来自后端解析`
  - 教材标题：`人教版小学数学一年级上册`
  - 学科：`数学`
  - 年级：`一年级`
  - 教材版本：`人教版`
  - 册次：`上册`
- 字段手改验证：
  - 将年级从 `一年级` 改为 `二年级`。
  - 顶部摘要同步显示 `T041-UI子链路-633528 · 数学 · 二年级 · 角色与视觉契约已配置`。
- 知识点下拉验证：
  - 展开知识点下拉，包含并选中 `5以内数的认识`。
- Markdown 预览验证：
  - 显示路径 `knowledge-points/kp_001.md`。
  - 内容包含 `# 《5以内数的认识》图文教材结构化整理`。
- UI 触发的网络请求均成功：
  - `POST /projects`：200
  - `POST /projects/proj_358af9eac8c7/textbook`：200
  - `POST /projects/proj_358af9eac8c7/nodes/textbook_parse/generate`：200
  - `GET /projects/proj_358af9eac8c7/manifest`：200
- 浏览器控制台 `error/warn` 为空。
- 保存截图：`docs\qa-audits\t041-ui-textbook-parse-result.png`。

### 当前结论

T041 最终结论：【通过】。

API 主链路沿用上一轮已通过证据；本轮已补齐 UI 子链路直接证据。上一轮“浏览器自动化无法注入本地 PDF”的阻塞已关闭，原因是本轮换用支持文件上传的浏览器环境完成验证。

### 已更新文件

- `docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`
- `docs\qa-audits\t041-ui-textbook-parse-result.png`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）
- `workflow\multi-agent\dispatch.md`

### 建议下一个接手角色

首席系统架构师接 T042：基于 T041 最终通过报告复核“教材解析到教案生成”阶段是否通过，并裁决下一阶段。

### 下个角色需要知道的上下文

- 本轮没有重跑 API 主链路；API 主链路沿用上一轮通过证据。
- 本轮只补 UI 子链路，且 UI 直接证据已补齐。
- 仍不代表上线验收通过；真实 provider、正式鉴权、多浏览器、生产级 MinerU 异步解析、上传大小/版权/安全限制仍是上线前范围。

---

## 【本轮】测试工程师 — T041 教材解析到教案生成端到端回归执行

### 本轮目标

按用户指定隔离环境正式执行 T041：打开 Web、新建项目、上传 fixture PDF、解析教材、校验字段回填与知识点 Markdown、确认教材解析、生成教案 Markdown、刷新持久化，并采集 API/Web/控制台证据。

### 执行环境

- API：`http://127.0.0.1:8141`
- Web：`http://127.0.0.1:3141`
- Storage：`storage-t041-textbook-to-lesson-e2e`
- Provider：`fake`
- Web 模式：真实 API 模式
- 旧 `8000` 后端实例：未复用
- 项目：`T041-教材到教案回归-633528`
- 项目 ID：`proj_34be317be27c`

### 已完成事项

- 验证 API `/health` 返回 `status=ok`、`workflow_version=1.0.0`。
- 验证 Web `3141` 可打开，并以真实 API 模式登录 `qa-t041`。
- 浏览器确认新建项目第 2 步存在真实后端解析入口：
  - `教材解析（真实后端）`
  - `上传 PDF 后调用后端解析教材`
  - `解析教材` 按钮
  - `input[type=file]`，`accept=.pdf,.txt,.md`
- 通过 API 完成主链路：
  - 创建项目。
  - 上传 fixture PDF。
  - `textbook_parse/generate` 传 `knowledge_point_id=kp_001`。
  - `textbook_parse/approve`。
  - `lesson_plan/generate`。
- API 产物验证：
  - `textbook_meta.subject=math`
  - `grade=1`
  - `textbook_version=renjiao`
  - `volume=shang`
  - `knowledge_points` 包含“5以内数的认识”
  - `selected_knowledge_point.knowledge_point_id=kp_001`
  - `selected_knowledge_point.markdown_path=knowledge-points/kp_001.md`
  - 教案 `source_knowledge_point_id=kp_001`
  - 教案 Markdown 包含“5以内数的认识”
- manifest 验证：
  - `textbook_parse=approved`
  - `lesson_plan=needs_review`
- Web 读取状态验证：
  - 首页项目列表显示 `T041-教材到教案回归-633528`。
  - 项目卡片显示 `数学 / 一年级 / 人教版 上册`。
  - 当前阶段为 `公开课教案`，总进度 `30%`，下一步动作 `进入「公开课教案」`。
  - 工作区显示 `10 个后端 manifest 节点`，当前节点为 `公开课教案`。
  - 刷新后首页仍显示同一项目和阶段，状态未丢失。
- 浏览器控制台验证：
  - 仅有 React DevTools、HMR、Fast Refresh 开发提示。
  - 未发现阻断性应用级 `error/warn`。
- 更新 T041 执行报告：`docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`。
- 更新测试角色记忆：`workflow\multi-agent\roles\qa-engineer.md`。

### 当前结论

T041 结论：【阻塞】。

阻塞原因不是 API 主链路失败，也不是已确认的前端/后端运行缺陷，而是本轮测试执行环境无法完成浏览器 UI 文件上传子链路证据采集：

- 当前 in-app browser 的 Playwright 封装不暴露 `setInputFiles`。
- 页面脚本环境不暴露 `File`、`Blob`、`DataTransfer`、`fetch`。
- 因此无法自动完成“选择 fixture PDF → 点击解析教材 → 观察解析中状态 → 字段回填 → 字段手工修改 → 知识点下拉 → Markdown 预览 → 确认解析结果”的 UI 子链路。

按 T041 验收口径，浏览器 UI 子链路缺证，不能判定通过。

### 缺陷与风险

#### 严重：浏览器自动化无法注入本地 PDF，导致 T041 UI 子链路缺证

- 分类：环境配置 / 测试工具
- 影响：阻塞本轮 T041 验收结论，不作为前端或后端产品缺陷判定。
- 复现：在当前 in-app browser 中尝试 `locator(...).setInputFiles` 和页面脚本构造文件对象均不可用。
- 标准修复方案：用支持 `setInputFiles` 的 Playwright 环境复测，或人工选择 PDF 后继续采集 UI 证据，或增加本地测试模式 fixture 入口。

#### 优化建议：manifest API 字段名与前端展示字段存在兼容映射

- 分类：接口 / 前端
- 影响：不阻塞本地演示；后续自动化测试按 `id/title/sort_order` 读取会误判为空。
- 标准修复方案：接口契约明确 `node_id` 为唯一标识；如前端需要 `id/title/sort_order`，由后端直接返回或在前端映射层集中补齐。

### 已更新文件

- `docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

首席系统架构师接 T042：复核 T041 报告，裁决是否接受“API 主链路通过 + UI 文件上传证据阻塞”的状态，或要求测试工程师用支持文件上传的浏览器环境补跑 UI 子链路后再复核。

### 下个角色需要知道的上下文

- 本轮没有复用旧 `8000` 后端实例。
- API 主链路已验证到 `lesson_plan` 生成，后端产物路径和来源字段满足 T041 目标。
- Web 真实 API 模式能读取项目、manifest 当前阶段和刷新后状态。
- T041 未通过的唯一核心缺口是浏览器 UI 文件上传和解析结果页的直接证据，不是 API 产物缺失。

---

## 【本轮】测试工程师 — T041 教材解析到教案生成端到端回归准备

### 本轮目标

准备 T041 教材解析到教案生成端到端回归；在用户要求的准备阶段，不启动正式浏览器回归，不判定 T041 通过。

目标正式链路为：上传 fixture 教材 PDF → 解析教材 → 字段回填 → 选择“5以内数的认识” → 展示知识点 Markdown → 确认教材解析 → 生成教案 Markdown。

### 已完成事项

- 读取项目规则、协作机制、共享事实、用户画像、测试角色记忆、最新交接和调度台账。
- 核对最新交接：T038/T040 已通过架构师红线复核，T039 已完成真实教材解析前端联调。
- 核对 T039 交付信息：真实 API 模式浏览器入口为 API `8139` + Web `3139`，前端 `tsc/lint/build` 已通过，页面存在真实“解析教材”按钮、字段回填、知识点下拉和 Markdown 预览。
- 核验 fixture 测试资料存在：
  - `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
  - `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\5以内数的认识_结构化文字教案.md`
- 新增 T041 准备记录：`docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`。
- 更新测试角色记忆，标注旧 T038/T040 失败结论已被后续返工和架构师复核覆盖。

### 当前结论

- T041 正式回归结论：阻塞。
- 阻塞原因：本轮按用户指令只准备测试清单和数据，未执行正式浏览器回归，因此不能判定通过。
- 阻塞角色：测试工程师待正式执行授权；正式执行时若失败，再按实际失败点归属前端、后端或环境配置。

### 准备好的正式测试重点

- API `/health`。
- Web 真实 API 模式。
- 新建项目上传 fixture PDF。
- 点击“解析教材”后的解析中状态。
- 字段回填：数学、一年级、人教版、上册。
- 字段手工修改。
- 知识点下拉包含“5以内数的认识”。
- 选中知识点后展示 Markdown，内容包含“5以内数的认识”。
- 确认教材解析后进入教案节点。
- 生成教案 Markdown。
- 教案结果包含 `source_knowledge_point_id=kp_001` 或等价来源信息。
- 刷新页面后解析结果和教案结果不丢失。
- 浏览器控制台无阻断性 error/warn。

### 正式执行注意事项

- 不要复用旧 `http://127.0.0.1:8000` 后端实例；T039 交接记录说明旧实例仍可能返回 `.pdf` 不支持。
- 建议使用隔离端口，例如 API `8141`、Web `3141`、storage `storage-t041-textbook-to-lesson-e2e`。
- 正式报告必须包含 API、Web、教材解析节点、教案节点、刷新持久化和浏览器控制台证据。

### 已更新文件

- `docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

测试工程师在收到正式执行指令后，按 `docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md` 执行 T041 浏览器 + API 双证据回归；完成后由首席系统架构师接 T042 复核。

---

## 【本轮】前端工程师 — T039 新建项目真实教材解析联调

### 本轮目标

在新建项目 / 教材上传流程中接入真实教材解析能力，替换旧“生成教材预览”本地预览口径，让用户可以上传 PDF、点击“解析教材”、查看字段回填、选择知识点并预览 Markdown。

### 已完成事项

- API client / store：
  - 新增文件上传 client：`uploadProjectTextbookFile(projectId, file)`，调用 `POST /projects/{project_id}/textbook`。
  - `GenerateNodePayload` 支持 `knowledge_point_id`，用于 `POST /projects/{project_id}/nodes/textbook_parse/generate`。
  - 新增 `parseDraftTextbook(file, knowledgePointId?)`：真实 API 模式下先创建后端项目，上传 PDF，再调用 `textbook_parse/generate`。
  - 新增 `selectDraftKnowledgePoint(knowledgePointId)`：切换知识点时重新调用 `textbook_parse/generate` 并刷新 Markdown。
  - 新增后端教材解析内容映射：`content.textbook_meta`、`content.knowledge_points`、`content.selected_knowledge_point.markdown`。
- 页面入口：
  - `apps\web\src\components\screens\NewProjectScreen.tsx` 第 2 步改为“教材解析（真实后端）”。
  - 支持 `.pdf,.txt,.md` 上传，页面明确“解析结果必须来自后端，不使用固定 mock 知识点”。
  - 按钮文案为“解析教材”，不再使用“生成教材预览”或旧本地预览口径。
  - 展示解析中、解析失败、解析完成状态。
  - 解析完成后展示“来自后端解析”标签。
  - 用 `textbook_meta` 回填学科、年级、教材版本、册次，并在解析结果卡中允许教师手工调整。
  - 用 `knowledge_points` 渲染知识点下拉；fixture 链路显示“5以内数的认识”。
  - 用 `selected_knowledge_point.markdown` 展示 Markdown 预览，并显示 `markdown_path`。

### 验证证据

- 前端静态验证：
  - `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
  - `cd apps\web && bun run lint`：通过。
  - `cd apps\web && bun run build`：通过。
- API 红线验证：
  - 使用隔离 API `http://127.0.0.1:8139`，`PROVIDER_MODE=fake`，`STORAGE_ROOT=storage-t039-frontend-smoke`。
  - 创建项目 → 上传 fixture PDF → `POST /nodes/textbook_parse/generate` 传 `knowledge_point_id=kp_001` → `GET /nodes/textbook_parse`。
  - 返回：`textbook_meta.title=人教版小学数学一年级上册`，`subject=math`，`grade=1`，`textbook_version=renjiao`，`volume=shang`，`selected=5以内数的认识`，`markdown_path=knowledge-points/kp_001.md`，Markdown 包含“5以内数的认识”。
- 浏览器 smoke：
  - Web：`http://127.0.0.1:3139`，真实 API 模式指向 `http://127.0.0.1:8139`。
  - 操作链路：登录真实 API 模式 → 新建项目 → 第 2 步上传 `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf` → 点击“解析教材”。
  - 页面证据：显示“教材解析结果 / 来自后端解析”，教材标题“人教版小学数学一年级上册”，学科“数学”，年级“一年级”，教材版本“人教版”，册次“上册”，课题与知识点下拉均为“5以内数的认识”，Markdown 预览显示 `knowledge-points/kp_001.md` 和目标内容。
  - 控制台：应用级 `error/warn` 为空。
  - 截图：`docs\qa-audits\t039-browser-textbook-parse.png`。

### 已更新文件

- `apps\web\src\lib\types.ts`
- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\store.ts`
- `apps\web\src\components\screens\NewProjectScreen.tsx`
- `docs\qa-audits\t039-browser-textbook-parse.png`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 关键结论

- T039 前端真实教材解析联调按本地演示口径完成。
- 前端不再把旧“生成教材预览”包装成真实解析。
- 前端不使用固定 mock 知识点冒充 MinerU 结果；知识点下拉和 Markdown 预览均来自后端返回内容。
- demo/mock 模式与真实 API 模式边界清楚：demo 模式下禁用真实“解析教材”按钮并提示需切换真实 API 模式。

### 剩余风险

- 当前本机已有旧 `http://127.0.0.1:8000` 后端进程仍返回 `400 / GENERATION_INPUT_INVALID / Unsupported textbook type for MVP: .pdf`，说明该运行实例未重启到 T038/T040 后的新代码。T039 验证使用当前仓库新启动的隔离端口 `8139` 通过；后续若继续使用 8000，需先重启后端。
- 第 2 步真实解析会提前创建后端项目。当前后端没有“更新项目基础元信息”接口，解析后教师在前端手改学科、年级、版本、册次，只能更新前端草稿和后续 UI，不能回写已提前创建的后端项目记录；上线前建议后端补最小项目元信息更新接口，或调整为先上传临时教材、最终创建项目时再落库。
- 当前是 fixture PDF 本地演示口径，不代表生产级全书异步 MinerU 解析、进度轮询、失败重试、缓存、大小/版权限制和上传安全已完成。

### 建议下一个接手角色

测试工程师接 T041：按“上传 fixture 教材 PDF → 解析教材 → 字段回填 → 选择‘5以内数的认识’ → 抽取 Markdown → 生成教案 Markdown”做回归；复现时优先重启后端到最新代码或使用隔离端口，避免旧 8000 实例干扰。

---

> 本文件最新补充：首席系统架构师复核 T038/T040 后端返工。结论：后端本地演示红线通过，前端 T039 可恢复真实接口联调；但生产级异步 MinerU 解析仍未完成。

---

## 【本轮】首席系统架构师 — T038/T040 后端返工红线复核

### 本轮目标

用户反馈后端已完成。本轮按架构师口径复核 T038/T040，不直接进入前端或测试阶段。

### 验证证据

- `python -m pytest apps\api\tests\test_textbook_pdf_parsing.py -q`：`2 passed`。
- `python -m pytest apps\api\tests -q`：`35 passed, 2 xfailed`。
- 架构师独立 API 红线：
  - 创建项目。
  - 上传 fixture PDF：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`。
  - 调用 `POST /projects/{project_id}/nodes/textbook_parse/generate`，传入 `knowledge_point_id=kp_001`。
  - 返回 `textbook_meta.title=人教版小学数学一年级上册`。
  - `knowledge_points` 包含 `5以内数的认识`。
  - `selected_knowledge_point.markdown_path=knowledge-points/kp_001.md`，文件存在。
  - approve `textbook_parse` 后调用 `lesson_plan/generate`，返回 `source_knowledge_point_id=kp_001`，且 `lesson_plan_markdown` 包含 `5以内数的认识`。

### 关键结论

- T038 后端 PDF 教材解析本地演示红线【通过】。
- T040 教案生成优先读取知识点 Markdown 本地演示红线【通过】。
- 前端 T039 阻塞解除，可以恢复真实接口联调。
- 当前后端实现是 fixture 稳定解析边界，不是生产级全书异步 MinerU 能力；上线前仍需补任务化、进度轮询、失败重试、缓存、多知识点自动发现、上传安全和版权/大小限制。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

前端工程师接 T039：接入上传 PDF、真实“解析教材”按钮、字段回填/手改、知识点下拉和 Markdown 预览。测试工程师继续等待 T039 完成后再执行 T041。

---

> 本文件最新补充：后端工程师完成 T038/T040 返工，PDF 教材解析到知识点 Markdown，再到教案 Markdown 输入链路已解除阻塞；前端 T039 可恢复真实接口联调。

---

## 【本轮】后端工程师 — T038/T040 PDF 教材解析到教案 Markdown 输入返工

### 本轮目标

解除 fixture 教材 PDF 在 `textbook_parse/generate` 阶段被拒绝的问题，并让 `lesson_plan/generate` 优先读取已选知识点 Markdown，支撑前端后续做“解析教材、字段回填、知识点下拉、Markdown 预览”真实接入。

### 已完成事项

- 新增后端教材解析边界 `apps\api\app\textbook_parser.py`。
- `textbook_parse/generate` 支持上传后的 PDF，不再返回 `Unsupported textbook type for MVP: .pdf`。
- fixture 教材 PDF 解析产物包含：
  - `textbook_meta.subject=math`
  - `textbook_meta.grade=1`
  - `textbook_meta.textbook_version=renjiao`
  - `textbook_meta.volume=shang`
  - `textbook_meta.title=人教版小学数学一年级上册`
- `knowledge_points` 至少包含 `5以内数的认识`。
- 支持在 `textbook_parse/generate` 请求体传 `knowledge_point_id`；当前 fixture 可传 `kp_001`，不传时默认选择 `kp_001`。
- 选中知识点会落盘 Markdown：`knowledge-points/kp_001.md`，并在节点结果中返回 `selected_knowledge_point.markdown_path` 和 `selected_knowledge_point.markdown`。
- `lesson_plan/generate` 在 fake provider 下优先读取 `textbook_parse.selected_knowledge_point.markdown`，返回：
  - `source_knowledge_point_id`
  - `source_markdown_path`
  - `lesson_plan_markdown`
  - 兼容旧前端的 `intro_designs`、`teaching_flow` 等字段。

### 前端 T039 可用接口

1. 上传 PDF：

```http
POST /projects/{project_id}/textbook
Content-Type: multipart/form-data
```

2. 解析教材并选择知识点：

```http
POST /projects/{project_id}/nodes/textbook_parse/generate
Content-Type: application/json

{
  "knowledge_point_id": "kp_001"
}
```

3. 获取解析产物：

```http
GET /projects/{project_id}/nodes/textbook_parse
```

4. 确认教材解析后生成教案：

```http
POST /projects/{project_id}/nodes/textbook_parse/approve
POST /projects/{project_id}/nodes/lesson_plan/generate
```

### 验证证据

- 先新增测试并确认红灯：fixture PDF 上传后旧实现返回 `400 / GENERATION_INPUT_INVALID / Unsupported textbook type for MVP: .pdf`。
- 目标测试：`python -m pytest apps\api\tests\test_textbook_pdf_parsing.py -q`：`2 passed`。
- 全量后端测试：`python -m pytest apps\api\tests -q`：`35 passed, 2 xfailed`。
- HTTP 红线路径验证：
  - fixture PDF：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
  - 创建项目 → 上传 PDF → `textbook_parse/generate` → `textbook_parse/approve` → `lesson_plan/generate` 全部通过。
  - 验证结果：`parse_status=needs_review`，`has_target_knowledge_point=true`，`markdown_path=knowledge-points/kp_001.md`，`markdown_exists=true`，`lesson_markdown_contains_target=true`。

### 已更新文件

- `apps\api\app\models.py`
- `apps\api\app\store.py`
- `apps\api\app\services.py`
- `apps\api\app\providers.py`
- `apps\api\app\textbook_parser.py`
- `apps\api\tests\test_textbook_pdf_parsing.py`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 剩余风险

- 当前是本地演示口径：fixture PDF 使用项目内 `skills\pdf` / MinerU 边界和稳定解析产物，不代表生产级全书异步 MinerU 解析已完成。
- 真实大 PDF 解析耗时、任务化、进度轮询、失败重试、缓存和多知识点自动发现仍需后续实现。
- `lesson_plan` 仍是 fake provider 输出，不代表真实 Minimax 教案质量验收。
- PDF 文件大小、版权合规、上传安全、OCR 失败兜底和正式字段级编辑校验仍是上线前风险。

### 建议下一个接手角色

前端工程师恢复 T039：接入上传 PDF、真实解析按钮、字段回填/手改、知识点下拉和 Markdown 预览。测试工程师随后执行 T041 后端+前端端到端回归。

---

## 【本轮】前端工程师 — T039 阻塞确认与交接补充

### 本轮目标

用户明确要求：当前 T039 暂停真实联调，等待后端 T038/T040 解除阻塞。前端只能在“已完成则补证据”和“未完成则不要伪造完成”之间二选一。

### 结论

T039 真实接口接入尚未完成，本轮不继续伪造完成，也不把现有“生成教材预览”包装成真实教材解析。

当前前端状态：

- 新建项目第 2 步仍是“教材内容准备 / 生成教材预览”。
- `生成教材预览` 只是前端本地预览逻辑，不触发 MinerU，不触发后端真实教材解析。
- `apps\web\src\lib\api-client.ts` 当前只有 `uploadProjectTextbook()`，没有教材解析、知识点列表、知识点 Markdown 预览相关 client。
- 页面没有真实“解析教材”按钮、解析中状态、字段自动回填、知识点下拉、知识点 Markdown 预览入口。
- 当前不使用固定 mock 知识点冒充 MinerU 解析结果。

### 已确认阻塞

- T038 后端阻塞：fixture PDF 上传后 `textbook_parse/generate` 仍返回 `Unsupported textbook type for MVP: .pdf`，未形成 PDF/MinerU 解析 API。
- T040 后端阻塞：因为 T038 未产出知识点 Markdown，`lesson_plan/generate` 优先读取知识点 Markdown 的链路无法验证。
- 前端 T039 需要等待后端稳定契约后再接：
  - 解析教材触发接口。
  - 解析任务状态/轮询或同步返回结构。
  - 字段回填结构。
  - 知识点列表结构。
  - 知识点 Markdown 预览/抽取接口。
  - 错误码和用户可读错误信息。

### 本轮改动

未修改业务代码。

已更新：

- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 后续复现与接入条件

后端解除阻塞后，前端再按以下最小链路接入并验证：

1. 新建项目第 2 步上传 fixture PDF。
2. 点击真实“解析教材”按钮。
3. 页面展示解析中/失败/完成状态。
4. 完成后回填学科、年级、版本、册次等字段，并允许手工修改。
5. 知识点下拉展示后端 MinerU 解析出的真实知识点。
6. 选择知识点后展示对应 Markdown 预览。
7. 创建项目后进入工作区，`lesson_plan/generate` 使用所选知识点 Markdown。

### 建议下一个接手角色

后端工程师优先返工 T038/T040。前端等待稳定 API 契约后再恢复 T039 真实联调；测试工程师暂不启动 T041。

---

> 上一条交接：首席系统架构师复核前端交付与教材解析链路。结论：前端基础质量通过，但 T039 不具备真实教材解析链路验收条件；T038/T040 后端 PDF/MinerU/知识点 Markdown 仍是主阻塞。

---

## 【本轮】首席系统架构师 — 教材解析链路前端交付复核与下一轮调度

### 本轮目标

用户反馈前端工程师也已完成，要求架构师检查并汇总下一步安排。本轮按 T038-T042 “教材解析到教案生成”阶段复核，不替代测试工程师做完整端到端验收。

### 验证证据

- `python -m pytest apps\api\tests -q`：`33 passed, 2 xfailed`。
- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 源码抽检：
  - `apps\web\src\components\screens\NewProjectScreen.tsx` 仍显示“生成教材预览”，未见真实“解析教材”按钮。
  - `apps\web\src\lib\api-client.ts` 仅见 `uploadProjectTextbook()`，未见教材解析、知识点列表、知识点 Markdown 预览 API。
  - `apps\web\src\lib\types.ts` 的 `NewProjectDraft` 仍是 `textbookFileName/textbookContent/parseResult/parseStatus`，未见知识点选择或 Markdown 预览状态。
  - 后端 `apps\api\app\store.py` 仍在 `latest_textbook_text()` 对非 `.txt/.md` 教材报 `Unsupported textbook type for MVP: .pdf`。

### 关键结论

- 本轮前端基础质量检查【通过】：类型检查、lint、build 均通过。
- T039 教材解析前端交付【未通过/阻塞】：当前未形成真实解析按钮、字段回填、知识点下拉、知识点 Markdown 预览和 API client 接入证据。
- T038/T040 后端仍是主阻塞：PDF/MinerU/知识点 Markdown 链路未通，`lesson_plan/generate` 优先读取知识点 Markdown 也无法验证。
- T041 测试暂不启动端到端回归，避免测试在核心 API 不存在或不通时做无效回归。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

后端工程师优先返工 T038/T040。前端工程师只做两件事之一：补交真实 T039 分支/交接证据，或等待后端契约后再联调。测试工程师等待后端红线复测通过后再接 T041。

---

> 本文件最新补充：首席系统架构师代执行 T038/T040 后端阶段验收，教材 PDF/MinerU 到教案输入链路未通过。历史交接保留，便于后续角色追溯。

---

## 【本轮】首席系统架构师 — T038/T040 后端阶段验收

### 本轮目标

用户反馈后端已完成，要求可以先测试。本轮只验收后端“教材 PDF 解析到教案生成输入”链路，不做前端浏览器回归。

### 验证证据

- `python -m pytest apps\api\tests -q`：`33 passed, 2 xfailed`。
- fixture PDF：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`。
- API 红线验证：创建项目 → 上传 PDF → 调用 `POST /projects/{project_id}/nodes/textbook_parse/generate`。
- 实际返回：`400 / GENERATION_INPUT_INVALID`，错误信息为 `Unsupported textbook type for MVP: .pdf`。

### 关键结论

- T038/T040 后端阶段验收【未通过】。
- 当前代码仍只支持 `.txt` / `.md` 教材进入 `textbook_parse/generate`，不支持 PDF/MinerU 解析。
- 未发现知识点列表与知识点 Markdown 抽取 API。
- 因为 T038 未产出知识点 Markdown，T040 的 `lesson_plan/generate` 优先读取 Markdown 输入也无法验证。

### 已更新文件

- `docs\qa-audits\2026-06-20-textbook-parsing-backend-check.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

后端工程师返工 T038/T040。前端 T039 暂时不要接真实接口，只能先做 UI 壳或等待后端契约。

---

## 【本轮】前端工程师 — T032/T034 本地演示体验打磨

### 本轮目标

在不改后端接口、不接真实 provider、不重构全站的前提下，完成两项本地演示体验修复：

- T032：新建项目第 2 步教材预览不能再让用户误以为固定样例就是自己的教材解析结果。
- T034：`final_video=running` 时底部 CTA 不再显示“创建视频任务”，并把视频链轻量 JSON 编辑器优化成更清晰的分区展示/编辑入口雏形。

### 已完成事项

- 新建项目第 2 步：
  - 步骤语义继续保持“教材内容准备 / 内容准备与预览”。
  - 有足够用户粘贴教材正文时，预览摘要基于粘贴内容生成，并标注“来自粘贴内容”。
  - 教材正文不足时才使用固定 mock 示例，并明确标注“示例预览”。
  - 示例预览文案明确说明：固定示例不能当作用户教材解析结果，真实解析仍在工作区点击“生成草稿”后发生。
- 最终视频节点：
  - `final_video=running` 时底部主 CTA 显示“查看任务状态”，点击后刷新状态。
  - 不再把已创建 fake 任务的 running 状态误导成可重复点击“创建视频任务”。
- 视频链轻量编辑器：
  - `intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 等视频链节点结果页显示“结构化编辑雏形”。
  - 上方增加节点摘要区，例如分镜节点展示镜头数量、镜头 ID、时长、主体、字幕和首帧状态。
  - 中间增加“编辑入口说明”，用 3 步解释先看摘要、再改 JSON、保存后确认。
  - 下方保留 JSON 编辑入口，避免本轮引入正式富编辑器。
  - 预留后端 `details` 字段级错误提示挂点，后续可继续把 T033 的校验结果映射到具体字段。

### 验证证据

- 浏览器真实 API 模式：
  - API：`http://127.0.0.1:8124`，fake provider。
  - Web：`http://127.0.0.1:3124`，真实 API 模式。
  - 验证项目：`T032-T034-体验验证-224358`，项目 ID `proj_571dc9dd4758`。
  - API 造数结果：`final_video=running`，`/tasks` 返回 6 个 `generated` fake task。
  - 首页项目卡：显示 `最终视频 / 90% / 进入「最终视频」`。
  - 工作区最终视频：底部主 CTA 显示“查看任务状态”，页面未出现误导性的主 CTA“创建视频任务”；结果页显示 `fake 视频生成任务`、`clip 数量 6`、`任务数量 6`、6 个 `generated` task，并继续声明不承诺真实成片质量。
  - 工作区分镜结果页：显示 `分镜脚本结构化编辑雏形`、`分镜脚本摘要`、`6 镜`、编辑入口说明、`JSON 编辑入口` 和字段级 details 提示预留文案。
  - 新建项目第 2 步短内容/空内容：显示 `示例预览摘要`、`示例预览`，并提示不能当作用户教材解析结果。
  - 新建项目第 2 步粘贴教材正文：显示 `教材预览摘要`、`来自粘贴内容`，课题识别为 `平均分与二分之一`，并提示真实教材解析仍在工作区生成草稿后发生。
  - 浏览器控制台应用级 `error/warn` 为空。

### 已更新文件

- `apps\web\src\lib\types.ts`
- `apps\web\src\components\screens\NewProjectScreen.tsx`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 剩余风险

- 视频链编辑器仍是轻量 JSON 编辑雏形，不是教师长期使用的正式富编辑器。
- 字段级错误提示入口已预留，但尚未把后端 T033 `details` 逐字段渲染到表单或摘要区。
- 新建项目第 2 步仍不触发真实教材解析；后续 T038/T039 教材 PDF/MinerU 链路完成后，需要再接真实“解析教材”按钮、字段回填和知识点选择。
- fake final video 仍只代表已创建视频生成任务，不代表真实视频成片、下载、拼接、音频合规或质量验收。

### 建议下一个接手角色

测试工程师接 T035，按本地演示口径回归：新建项目第 2 步示例/粘贴内容预览、视频链结构化编辑入口、`final_video=running` CTA、完整 fake 视频链路不回退。

---

> 上一条交接：后端工程师完成 T033，视频链节点 `/edit` 已增加最小 schema 校验和稳定错误码。历史交接保留，便于后续角色追溯。

---

## 【本轮】后端工程师 — T033 视频链节点 edit 最小校验

### 本轮目标

为 `intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`、`final_video` 的 `/edit` 增加节点级最小 schema 校验和稳定错误码，支撑前端后续字段级错误提示；不接真实 provider、不做复杂版本 diff、不改前端。

### 已完成事项

- 在 `WorkflowService.edit_node()` 写入版本前增加视频链节点最小内容校验。
- 新增轻量异常 `NodeContentValidationError`，路由统一返回 `400 / NODE_CONTENT_INVALID`。
- 错误响应带 `details[{field, code, message}]`，供前端按字段展示。
- 校验覆盖必填字段缺失、字段类型明显错误、必填数组为空、重复 ID、上游引用不存在、`final_video.clip_count` 与 `clips.length` 不一致。
- 更新 `docs\backend-video-generation-contract.md`，补充每个节点最小必填字段和错误码。
- 更新 `workflow\multi-agent\dispatch.md` 中 T033 状态为已完成。
- 更新后端角色记忆。

### 接口契约摘要

非法 `/edit` 返回：

```json
{
  "ok": false,
  "error": {
    "code": "NODE_CONTENT_INVALID",
    "message": "节点内容不符合最小契约",
    "retryable": false,
    "details": [
      {
        "field": "selected_design_ids",
        "code": "required",
        "message": "selected_design_ids 为必填字段"
      }
    ]
  }
}
```

当前 `details[].code`：`required`、`invalid_type`、`empty`、`duplicate`、`reference_not_found`、`count_mismatch`。

非对象 `content` 继续由 Pydantic 拒绝，返回 `422 / REQUEST_VALIDATION_FAILED`。

完整字段要求见 `docs\backend-video-generation-contract.md`。

### 验证证据

- 先运行新增测试，确认旧实现红灯：`test_video_demo_contract.py` 中 3 个非法保存用例返回 200，测试失败。
- 补实现后运行：`python -m pytest apps\api\tests\test_video_demo_contract.py -q`：`6 passed`。
- 全量后端测试：`python -m pytest apps\api\tests -q`：`33 passed, 2 xfailed`。

### 已更新文件

- `apps\api\app\services.py`
- `apps\api\app\main.py`
- `apps\api\tests\test_video_demo_contract.py`
- `docs\backend-video-generation-contract.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 剩余风险

- 当前是最小校验，不是完整 JSON Schema 引擎；仍允许演示用额外字段。
- 不校验所有业务语义，例如文案质量、时长总和、视频合规完整性。
- `final_video` fake 任务仍不代表真实视频生成、下载、拼接或质量验收。
- 上线前仍需正式鉴权、行级隔离、真实 provider、完整 schema 和错误文案设计。

### 建议下一个接手角色

前端工程师接 T034：可基于 `NODE_CONTENT_INVALID` 的 `details` 做字段级提示，并修复 `final_video=running` 时 CTA 文案。

---

> 上一条交接：首席系统架构师完成 T037，教材解析到教案生成链路需求、测试资料和 PDF/MinerU 项目技能已落地。历史交接保留，便于后续角色追溯。

---

## 【本轮】首席系统架构师 — T037 教材解析到教案生成链路需求收口

### 本轮目标

理解并沉淀用户关于“上传教材 PDF → MinerU 大纲解析 → 字段回填 → 知识点选择 → 知识点 Markdown 抽取 → 教案 Markdown 生成”的需求，并把测试资料和 PDF 解析技能纳入项目。

### 已完成事项

- 将用户提供的 3 个测试文件复制到项目稳定目录：
  - `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
  - `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\5以内数的认识_公开课教案.pdf`
  - `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\5以内数的认识_结构化文字教案.md`
- 将本机 PDF skill 副本复制到项目内：`skills\pdf`。
- 读取 `skills\pdf\SKILL.md` 和 MinerU 路由说明，确认本机默认 MinerU 路线。
- 探测 MinerU：`mineru, version 3.2.0`。
- 新增需求契约：`docs\textbook-parsing-to-lesson-plan-requirement.md`。
- 更新 `workflow\multi-agent\dispatch.md`，新增 T037-T042。

### 需求理解

- 教材 PDF 上传是用户真实入口，不应继续依赖固定样例。
- “解析教材”按钮应触发后端 MinerU 大纲解析。
- 解析结果需要回填学科、年级、版本、上下册等字段，同时允许教师手工修改。
- 知识点列表应来自整本教材解析结果，并进入下拉框供用户选择。
- 用户选择某个知识点后，后端需锚定对应页码/章节，再抽取该知识点教材内容为 Markdown。
- 抽取出的 Markdown 是教案生成节点的核心输入。
- 示例教案 PDF 只作为效果参考，不是模板；示例 Markdown 是教材片段抽取质量参考。

### 已下发下一阶段任务

- T038 后端工程师：接入 `skills\pdf` / MinerU，完成教材大纲解析、字段识别、知识点列表和知识点 Markdown 抽取 API。
- T039 前端工程师：接入上传教材、解析按钮、字段回填/手改、知识点下拉和 Markdown 预览入口。
- T040 后端工程师：让 `lesson_plan/generate` 优先使用已选知识点 Markdown 生成教案 Markdown。
- T041 测试工程师：等待 T038-T040/T039 完成后做教材解析到教案生成端到端回归。
- T042 首席系统架构师：阶段复核。

### 风险

- 教材 PDF 约 50MB，上线前需要文件大小限制、存储策略和版权合规说明。
- MinerU 解析可能耗时较长，后端需要异步任务或至少明确超时/状态返回。
- 知识点自动识别需要人工可改，不能把模型/解析结果当绝对事实。
- Markdown 作为教案生成输入时，需要保留来源页码，方便教师核对。

### 建议下一个接手角色

后端工程师和前端工程师并行；后端先定义 API 契约，前端可先做 UI 状态与适配层。

---

## 【本轮】首席系统架构师 — T031 本地 fake 视频生成端到端演示复核

### 本轮目标

对照 T023-T030 的后端契约、前端交付、测试报告、关键代码和新鲜验证证据，判断“本地 fake 视频生成端到端演示”是否通过，并决定下一阶段任务方向。

### 已完成事项

- 复核 `docs\backend-video-generation-contract.md`、`apps\api\tests\test_video_demo_contract.py`、`docs\qa-audits\2026-06-20-local-demo-smoke.md`。
- 复核后端视频链关键实现：`services.py`、`providers.py`、`workflow_config.py`。
- 复核前端真实 API 调用链：`api-client.ts`、`api-mappers.ts`、`store.ts`、`types.ts`、`ProjectWorkspaceScreen.tsx`。
- 新鲜运行后端测试、前端类型检查、lint 和 build。
- 启动隔离 API：`http://127.0.0.1:8101`，fake provider，storage `storage-t031-architect-review`。
- 启动隔离 Web：`http://127.0.0.1:3101`，真实 API 模式，API Base 指向 `http://127.0.0.1:8101`。
- API 直连创建 T031 复核项目并推进完整链路到 `final_video=running`。
- 浏览器复核：首页读到后端项目，显示 `最终视频 / 90% / 进入「最终视频」`；工作区结果页展示 6 个 generated 任务和 fake 输出路径。
- 更新 `workflow\multi-agent\dispatch.md`、`workflow\multi-agent\stage-review.md`、`workflow\multi-agent\roles\architect.md` 和本文件。

### 验证证据

- `python -m pytest apps\api\tests -q`：`29 passed, 2 xfailed`。
- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- T031 复核项目：`T031-架构复核-完整视频链路`。
- 后端项目 ID：`proj_30cdbe43c317`。
- 后端 manifest：9 个前置节点 approved，`final_video=running`。
- 后端 `/tasks`：6 个任务，状态集合为 `generated`。
- 浏览器首页：显示 `最终视频 / 90% / 进入「最终视频」`。
- 浏览器工作区结果页：显示 `FAKE 视频生成任务`、`clip 数量 6`、`任务数量 6`、6 个 `generated` task、`clips/shot_01.mp4` 到 `clips/shot_06.mp4`。
- 浏览器控制台：`error/warn` 日志为空。

### 关键结论

- T031 判定为【通过】，范围仅限本地 fake provider 端到端演示。
- 当前项目已经可以本地演示从创建项目推进到最终视频 fake 任务创建与查询。
- 不进入上线发布，也不直接宣布真实视频生成通过。
- 下一阶段建议先做“项目创建体验固定样例修复 + 后端 schema 校验 + 前端结构化编辑器雏形”，再进入真实 provider smoke。

### 发现的风险

- 视频链各节点 `/edit` 仍缺节点级 schema 校验和字段级错误提示。
- 视频链编辑器仍是轻量 JSON/text 演示，不是教师可长期使用的正式编辑体验。
- `final_video=running` 时底部主按钮仍显示“创建视频任务”，存在状态文案不一致风险，但不阻塞本地演示。
- fake provider 不代表真实任务提交、轮询、下载、拼接、音频合规和成片质量。
- 正式鉴权、角色权限、多用户隔离、部署、性能和多浏览器仍未验收。

### 已下发下一阶段任务

- T032 前端工程师：修复新建项目第 2 步教材预览固定样例口径。
- T033 后端工程师：补视频链节点 `/edit` 最小 schema 校验和错误码。
- T034 前端工程师：修复 `final_video=running` CTA 状态文案，并优化视频链轻量编辑入口雏形。
- T035 测试工程师：等待 T032-T034 完成后做轻量回归。
- T036 首席系统架构师：等待 T035 完成后复核是否进入真实 provider smoke。

### 建议下一个接手角色

前端工程师、后端工程师先并行；测试工程师暂不接入。

---

## 【本轮】测试工程师 — T025/T030 本地 fake 视频生成端到端演示轻量回归

### 本轮目标

在 T023、T024、T027、T028、T029 已完成后，执行两个本地演示口径回归：

- T025：视频导入选择小链路，覆盖创建项目 → 教材解析确认 → 教案生成/保存/确认 → 视频导入选择生成/选择/确认 → 首页和工作区状态同步。
- T030：完整本地 fake 视频生成链路，覆盖创建项目 → 教材解析 → 教案 → 视频导入选择 → 视频剧本 → 视频分场剧本 → 视频资产 → 分镜脚本 → `final_video` fake 任务生成 → `/tasks` 查询 → 首页/工作区状态同步。

本轮不测真实 provider、不做上线验收、不测部署、不测正式鉴权。

### 已完成事项

- 读取项目规则、协作机制、共享事实、用户画像、测试角色记忆、最新交接、调度台账和后端视频生成契约。
- 确认 T023、T024、T027、T028、T029 均已完成，可以执行 T025/T030。
- 启动隔离 API：`http://127.0.0.1:8091`，fake provider，storage `storage-t025-t030-regression`。
- 启动隔离 Web：`http://127.0.0.1:3091`，真实 API 模式，API Base 指向 `http://127.0.0.1:8091`。
- 通过浏览器完成 T025 小链路，并验证首页/工作区同步到 `视频剧本 / 50%`。
- 继续通过浏览器完成 T030 完整链路，并验证 `final_video` fake 任务页面展示 6 个 generated tasks。
- 使用后端 API 复核 manifest、`lesson_plan` 编辑 marker、`intro_selection.primary_design_id`、`final_video` content 和 `/tasks`。
- 读取浏览器控制台 `error/warn`，本轮为空。
- 追加 `docs\qa-audits\2026-06-20-local-demo-smoke.md` 的 T025/T030 回归记录。
- 更新测试角色记忆和本文件。

### 验证证据

- API：`GET /health` 返回 `ok=true`、`status=ok`、`workflow_version=1.0.0`。
- Web：`GET http://127.0.0.1:3091` 返回 200。
- 回归项目：`T025-T030-视频链路-760635`。
- 后端项目 ID：`proj_8067c6d39b21`。
- T025 结果：工作区和首页均显示 `视频剧本 / 50% / 进入「视频剧本」`。
- T030 结果：工作区和首页均显示 `最终视频 / 90% / 进入「最终视频」`。
- 后端 manifest：`project_meta=approved`、`project_config=approved`、`textbook_parse=approved`、`lesson_plan=approved`、`intro_selection=approved`、`intro_video_script=approved`、`intro_video_screenplay=approved`、`intro_video_asset=approved`、`storyboard=approved`、`final_video=running`。
- 后端任务：`/projects/proj_8067c6d39b21/tasks` 返回 6 个 `video_clip_generation` task，状态集合为 `generated`。
- `final_video` 节点 content：`clip_count=6`，clips 包含 `shot_01` 到 `shot_06`，download path 为 `clips/shot_01.mp4` 到 `clips/shot_06.mp4`。
- 浏览器控制台：`error/warn` 日志为空。

### 关键结论

- T025 在本地演示口径下判定为【可演示】。
- T030 在本地演示口径下判定为【可演示】。
- 本轮未发现阻塞本地演示的问题。
- 当前只证明 fake provider 下任务创建、状态推进和查询链路可演示，不代表真实视频成片质量或上线发布通过。

### 上线前仍是风险

- 视频链各节点 `/edit` 仍缺少节点级 schema 校验、字段级错误提示和非法引用拦截。
- `final_video` fake task 不代表真实 provider 任务提交、轮询、下载、拼接、音频合规和视频质量验收。
- 前端视频链编辑器仍是轻量文本/JSON 演示形态，不是正式教师编辑体验。
- 正式鉴权、角色权限、多人数据隔离、部署、多浏览器、多分辨率和性能压测未覆盖。
- 首页真实 API 模式仍存在 manifest fan-out，请求量增长后需后端列表摘要或前端分页/懒加载。

### 建议下一个接手角色

首席系统架构师接 T031，对照 T023-T030 的后端契约、前端交付、测试报告和关键代码/配置 diff，复核“本地 fake 视频生成端到端演示”阶段是否通过。

---

## 【本轮】前端工程师 — T024/T028/T029 本地 fake 视频生成演示链路

### 本轮目标

把工作区从“教案确认后进入视频导入选择”推进到“fake 最终视频生成任务可演示”，覆盖 `intro_selection`、视频生产四节点和 `final_video` fake task 展示；当前阶段只做本地端到端演示，不做上线发布。

### 已完成事项

- `intro_selection`：
  - 复用后端 `generate/get/edit/approve`。
  - 结果页展示来自已确认教案 `intro_designs` 的 3 类候选方案：科普类、应用类、故事类。
  - 支持点击候选方案写入 `primary_design_id` / `selected_design_ids`。
  - 支持“保存选择”写回 `/nodes/intro_selection/edit`，确认后推进到 `intro_video_script`。
- 视频生产节点：
  - `intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均复用轻量文本/JSON 编辑器。
  - 每个节点支持生成、查看、编辑保存到后端、确认推进。
- `final_video`：
  - 运行页支持模型、尺寸、模式和生成范围选项。
  - 触发 `final_video/generate` 后自动刷新 `/projects/{project_id}/tasks`。
  - 结果页展示 fake 视频任务、clip 数量、任务数量、每个 task 状态、模型、尺寸和 fake 输出路径。
  - 文案明确“只证明已创建视频生成任务和 clip 记录，不承诺真实成片质量”。
- 稳定性修复：
  - 进入 `intro_selection` 时主动补拉 `lesson_plan` 节点详情，避免候选方案依赖的 `intro_designs` 未加载导致空白。
  - `final_video` 的主按钮改为“创建视频任务”，次按钮为“重新创建任务”，避免把 fake 任务误表达为真实成片完成。
  - fake provider 默认生成范围与后端契约对齐为完整 6 段。

### 验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器真实 API smoke：
  - API：`http://127.0.0.1:8081`，fake provider。
  - Web：`http://127.0.0.1:3081`，真实 API 模式。
  - 项目：`T024-T028-T029-168836`。
  - 链路：创建项目 → 教材内容准备并自动上传 → `textbook_parse` 生成/确认 → `lesson_plan` 生成/轻量编辑保存/确认 → `intro_selection` 生成 3 类候选/选择应用类/保存选择/确认 → `intro_video_script` 生成/编辑保存/确认 → `intro_video_screenplay` 生成/编辑保存/确认 → `intro_video_asset` 生成/编辑保存/确认 → `storyboard` 生成/编辑保存/确认 → `final_video` 创建 fake 视频任务。
  - 最终页面证据：`FAKE 视频生成任务`、`clip 数量 6`、`任务数量 6`、6 个 task 均为 `generated`、fake 输出包含 `clips/shot_01.mp4` 到 `clips/shot_06.mp4`，页面显示“不承诺真实成片质量”。
  - 浏览器控制台：应用级 `error/warn` 为空；自动化过程中出现过 Codex 浏览器工具自身 Statsig 网络超时和一次取证脚本变量错误，非 ShanHaiEdu 应用日志。

### 已更新文件

- `apps\web\src\lib\types.ts`
- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\store.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 上线前仍是风险

- 视频链各节点 `/edit` 当前仍是完整 JSON 内容写入，缺少节点级 schema 校验、字段级错误提示和正式编辑体验。
- `final_video` 当前只演示 fake task 创建和查询，不代表真实视频生成、下载、拼接、质量验收或中文男声合规验证。
- 真实 provider 的异步状态恢复、失败重试、成本日志、素材下载和权限隔离未覆盖。
- 首页项目列表仍通过 manifest fan-out 同步阶段摘要，项目量增长后需要后端列表摘要或前端分页优化。

### 建议下一个接手角色

测试工程师接 T030，按本地演示口径回归完整链路，并追加 `docs\qa-audits\2026-06-20-local-demo-smoke.md`；之后首席系统架构师接 T031 复核是否通过“本地 fake 视频生成端到端演示”阶段。

---

## 【本轮】后端工程师 — T023/T027 本地 fake 视频生成契约

### 本轮目标

补齐本地 fake provider 视频生成演示所需后端契约：`intro_selection` 节点生成/获取/编辑/确认，以及视频生产链 `intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`、`final_video` 的最小 generate/get/edit/approve 和 fake tasks 查询链路。

### 已完成事项

- 复核现有后端实现，确认通用节点接口已覆盖 T023/T027 所需行为。
- 新增 `apps\api\tests\test_video_demo_contract.py`：
  - 覆盖 `intro_selection` 在 `lesson_plan` 未确认前返回 `UPSTREAM_NOT_APPROVED`。
  - 覆盖 `intro_selection` 的 generate/get/edit/approve 和 approve 后 manifest 推进。
  - 覆盖 `intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 的 generate/get/edit/approve。
  - 覆盖 `final_video/generate` fake 任务创建和 `/projects/{project_id}/tasks` 查询。
- 新增 `docs\backend-video-generation-contract.md`，作为前端 T024/T028/T029 和测试 T025/T030 的后端契约输入。
- HTTP 直连跑通从 `lesson_plan=approved` 到 `final_video` fake tasks。
- 更新 `workflow\multi-agent\dispatch.md`，将 T023/T027 标为已完成。
- 更新后端角色记忆。

### 接口契约摘要

所有视频生产文本/结构化节点复用：

```http
POST /projects/{project_id}/nodes/{node_id}/generate
GET  /projects/{project_id}/nodes/{node_id}
POST /projects/{project_id}/nodes/{node_id}/edit
POST /projects/{project_id}/nodes/{node_id}/approve
GET  /projects/{project_id}/manifest
```

`edit` 请求体仍是完整内容写入：

```json
{
  "content": {}
}
```

T023 前置：

- `intro_selection` 必须在 `lesson_plan=approved` 后生成。
- `intro_selection=approved` 后，manifest 中 `intro_video_script` 保持 `not_started`，前端可推进到视频文稿节点。

T027 视频生产顺序：

```text
intro_video_script -> intro_video_screenplay -> intro_video_asset -> storyboard -> final_video
```

`final_video/generate` fake 演示请求体建议：

```json
{
  "model": "veo_3_1-fast",
  "size": "1280x720",
  "mode": "reference",
  "full_run": true
}
```

fake 模式结果：

- `final_video` 节点状态为 `running`
- 创建 6 个 `video_clip_generation` 任务
- `/projects/{project_id}/tasks` 返回 6 个任务
- 任务状态集合为 `generated`

完整契约见：`docs\backend-video-generation-contract.md`。

### 验证证据

- `python -m pytest apps\api\tests\test_video_demo_contract.py -q`：`2 passed`。
- `python -m pytest apps\api\tests -q`：`29 passed, 2 xfailed`。
- HTTP 直连 API：`http://127.0.0.1:8087`，fake provider，临时 storage `storage-t023-t027-smoke`。
- HTTP 直连项目：`proj_57b91a8359ae`。
- HTTP 结果：
  - `intro_selection` 在 `lesson_plan` 未 approve 前返回 `UPSTREAM_NOT_APPROVED`。
  - `intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均完成 generate/edit/approve，编辑 marker 均可读回。
  - `final_video/generate` 返回 `running`。
  - `final_video.clip_count=6`。
  - `/tasks` 查询 `taskCount=6`，状态集合为 `generated`。
- 临时 API 端口 `8087` 已停止。

### 现有接口是否足够

足够。T023/T027 不需要新增业务 endpoint。新增的是契约测试和后端契约文档；业务实现仍复用现有通用节点服务与 fake provider。

### 上线前仍是风险

- 各节点 `edit` 当前仅校验 `content` 是对象，未按节点 schema 做严格字段校验。
- `final_video` fake tasks 只证明任务记录和查询链路，不代表真实视频生成、下载、拼接或质量验收。
- 本轮不接真实 provider；真实 Minimax / 章鱼哥任务提交、查询 token、下载和失败重试仍需单独验收。
- 未配置 `BACKEND_API_TOKEN` 时本地联调接口开放，上线前必须补正式鉴权和行级隔离。

### 已更新文件

- `apps\api\tests\test_video_demo_contract.py`
- `docs\backend-video-generation-contract.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

前端工程师接 T024/T028/T029，按契约接入 `intro_selection`、视频生产节点和 `final_video` fake 任务展示；随后测试工程师执行 T025/T030 本地演示轻量回归。

> 本文件最新补充：首席系统架构师在 T022 后追加视频生成推进总控任务，目标从“视频导入选择”扩展到“本地 fake 最终视频生成”链路。历史交接保留，便于后续角色追溯。

---

## 【本轮】首席系统架构师 — 视频生成推进任务扩展

### 本轮目标

用户要求任务安排不仅完善视频导入选择，还要保证能继续推进视频生成。因此本轮将后续任务拆成可执行的本地演示链：视频导入选择 → 视频剧本 → 分场剧本 → 视频资产 → 分镜 → fake 最终视频任务。

### 已完成事项

- 新增实施计划：`docs\superpowers\plans\2026-06-20-video-generation-demo-chain.md`。
- 更新 `workflow\multi-agent\dispatch.md`，保留 T023-T026，并新增 T027-T032。
- 更新架构师角色记忆，明确当前目标是本地 fake provider 视频生成演示，不是上线发布。
- 更新本交接记录。

### 新任务范围

- T023-T026：先完成 `intro_selection` 视频导入选择节点生成、选择、保存、确认和架构复核。
- T027-T031：继续完成视频剧本、分场剧本、视频资产、分镜、fake 最终视频任务生成和全链路测试/复核。
- T032：后续打磨新建项目第 2 步教材预览固定样例口径，不阻塞视频生成主线。

### 关键结论

- 后端和前端可以先并行执行 T023/T024。
- T027 后端视频生产链契约应尽快启动，避免前端做视频节点时靠猜。
- 测试工程师不需要每个小开发动作都介入；测试在 T025 和 T030 两个链路节点完成后接入。
- 架构师分别在 T026 和 T031 做阶段复核。

### 建议下一个接手角色

后端工程师、前端工程师。

---

## 【本轮】首席系统架构师 — T022 教案节点端到端演示复核

### 本轮目标

复核 T019-T021 是否真实完成，判断公开课教案节点生成、编辑保存、确认推进是否可以作为本地端到端演示通过，并决定下一阶段任务。

### 已完成事项

- 读取多角色机制、共享事实、用户画像、最新交接、调度台账、阶段总控、架构师记忆、用户反馈台账、决策台账和冲突台账。
- 复核关键代码与 diff：前端 API client、API mapper、store、工作区、首页卡片；后端 `/generate`、`/edit`、`/approve`、store/version 持久化和接口模型。
- 新鲜运行后端测试、前端类型检查、lint、build。
- 启动隔离 API：`http://127.0.0.1:8071`，fake provider，storage `storage-t022-architect-review`。
- 启动隔离 Web：`http://127.0.0.1:3071`，真实 API 模式，API Base 指向 `http://127.0.0.1:8071`。
- 浏览器复核：登录真实 API 模式 → 创建项目 → 教材解析生成/确认 → 教案生成 → 编辑保存 marker → 后端读回 marker → 教案确认 → 首页/工作区同步到下一节点。
- 停止本轮 API/Web 服务。
- 更新 `workflow\multi-agent\dispatch.md`、`workflow\multi-agent\stage-review.md`、`workflow\multi-agent\roles\architect.md` 和本交接记录。

### 验证证据

- `python -m pytest apps\api\tests -q`：`27 passed, 2 xfailed`。
- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器项目：`T022-架构复核-教案链路`，后端项目 ID `proj_e4a624d593e4`。
- 编辑 marker：`t022_architect_edit_620`。
- 后端复核：`lesson_status=approved`，`contains_marker=true`。
- 最终 manifest：`textbook_parse=approved`、`lesson_plan=approved`、`intro_selection=not_started`。
- 工作区最终状态：`视频导入选择 / 40% / 进入「视频导入选择」`。
- 首页“继续工作”和“项目概览”最终状态同样为：`视频导入选择 / 40% / 进入「视频导入选择」`。
- 浏览器控制台：应用级 `error/warn` 为空；浏览器控制环境自身出现过 Statsig 外部统计请求超时，不属于 ShanHaiEdu 应用日志。

### 关键结论

- T019-T021 通过架构师复核，本轮公开课教案节点本地端到端演示【通过】。
- 当前通过范围仅限本地 fake provider + 真实 API 模式演示，不代表上线发布通过。
- 下一阶段进入“视频导入选择节点端到端演示”，不继续优先停留在教案节点。

### 复核发现的风险

- `lesson_plan/edit` 当前只要求 `content` 是对象，缺少公开课教案 schema、必填字段和字段级错误提示；上线前必须补。
- 前端教案编辑器仍是轻量文本/JSON 演示形态，不是正式教师编辑体验。
- 新建向导第 2 步已明确“预览不等于真实解析”，但教材预览摘要仍可能显示固定样例课题，后续打磨项目创建体验时需修。
- 真实 provider、正式鉴权、多人数据隔离、部署、多浏览器、多分辨率和性能未覆盖。
- 首页真实 API 模式仍存在项目列表 manifest fan-out，请求量增长后需优化。

### 新增任务

- T023：后端工程师确认或补齐 `intro_selection` generate/edit/approve 最小契约。
- T024：前端工程师接入 `intro_selection` 视频导入选择节点生成、查看、选择/轻量保存、确认推进。
- T025：测试工程师做“教材解析 → 教案 → 视频导入选择”本地演示轻量回归。
- T026：首席系统架构师在 T023-T025 后复核是否进入视频剧本节点。

### 建议下一个接手角色

后端工程师和前端工程师并行接手 T023/T024；测试工程师等待二者完成后执行 T025。

---

## 【本轮】测试工程师 — T021 公开课教案节点本地端到端演示轻量回归

### 本轮目标

等待 T019 后端和 T020 前端完成后，按本地演示口径回归公开课教案节点端到端链路：创建项目、教材解析确认、教案生成、编辑保存、重新读取持久化、确认推进、首页/工作区状态同步；不做上线验收。

### 已完成事项

- 读取 `AGENTS.md`、最新交接、调度台账和本地演示 QA 报告，确认 T019/T020 已完成且可进入 T021。
- 使用 fake provider 和隔离 storage 启动 API，验证 `/health` 正常。
- 使用真实 API 模式启动 Web，验证页面可访问。
- 通过浏览器完成：创建项目 → 进入工作区 → 生成并确认 `textbook_parse` → 生成 `lesson_plan` → 编辑并保存教案 → 刷新/重新读取节点 → 确认 `lesson_plan` → manifest 推进 → 首页状态同步。
- 使用后端 GET 复核编辑 marker 已持久化，避免只依赖页面 `innerText` 判断 textarea 内容。
- 追加 `docs\qa-audits\2026-06-20-local-demo-smoke.md` 的 T021 回归记录。
- 更新测试角色记忆和本文件。

### 验证证据

- API：`http://127.0.0.1:8061`，fake provider，隔离 storage `storage-t021-regression`。
- Web：`http://127.0.0.1:3061`，真实 API 模式，API Base 指向 `http://127.0.0.1:8061`。
- `GET /health`：`ok=true`、`status=ok`、`workflow_version=1.0.0`。
- Web 首页：`GET http://127.0.0.1:3061` 返回 200。
- 回归项目：`T021-教案回归-336362`，后端项目 ID `proj_91cc9fcc3318`。
- 编辑 marker：`t021_smoke_edit_336362`。
- 后端复核：`GET /projects/{project_id}/nodes/lesson_plan` 返回内容包含 marker，`lessonStatus=approved`。
- 最终 manifest：`textbook_parse=approved`、`lesson_plan=approved`、`intro_selection=not_started`。
- 最终首页和工作区：均显示 `视频导入选择 / 40% / 进入「视频导入选择」`。
- 浏览器控制台：阻断性 `error/warn` 为空。

### 关键结论

- T021 在本地端到端演示口径下判定为【可演示】。
- 本轮未发现阻塞演示问题。
- T019/T020 的最小契约和前端接入可以支撑“公开课教案节点生成、编辑保存、确认推进”的本地演示。

### 上线前仍是风险

- `lesson_plan/edit` 仍接受任意 dict，上线前必须补 schema 校验、必填字段校验和字段级错误提示。
- 前端公开课教案编辑器仍是轻量文本/JSON 演示形态，不是正式教师编辑体验。
- 正式鉴权、角色权限、多人数据隔离、真实 provider、多浏览器、多分辨率、部署和性能压测未在 T021 覆盖。
- 首页真实 API 模式仍会为项目列表逐个补拉 manifest，项目数量增长后存在请求放大风险。

### 建议下一个接手角色

首席系统架构师复核 T019-T021，对照本地演示目标、回归报告和关键改动判断是否通过“公开课教案节点端到端演示”小阶段。

---

## 【本轮】前端工程师 — T020 公开课教案节点端到端演示

### 本轮目标

在本地演示口径下，打通 `lesson_plan` 公开课教案节点的生成、查看、轻量编辑、保存到后端、确认推进链路；不做全节点重构、不做正式权限 UI、不扩展后端接口。

### 已完成事项

- 扩展前端 API client：新增 `editProjectNode()`，接入 `POST /projects/{project_id}/nodes/{node_id}/edit`。
- 扩展 store：新增 `editStageRemote(projectId, stageKey, content)`，真实 API 模式下执行后端 edit，成功后刷新 manifest 和节点详情。
- 工作区真实 API 模式下，`open-lesson-plan` 节点结果页新增轻量文本/JSON 编辑器和“保存教案”按钮。
- 保存行为仅对 `open-lesson-plan` 开放；其他节点在真实 API 模式下不伪造成功，显示当前仅开放公开课教案节点编辑保存。
- 生成教案复用现有 `/generate`，确认通过复用现有 `/approve`，未新增后端接口。
- 真实 API 映射新增 `currentStageTitle`，首页继续工作和项目卡片优先显示后端 manifest 当前节点标题，修复教案确认后首页把后端 `视频导入选择` 显示成本地 `视频设计导入` 的同步口径问题。
- 更新 `workflow\multi-agent\dispatch.md` 中 T020 状态为已完成。
- 更新前端角色记忆。

### 验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器真实 API smoke：
  - API：`127.0.0.1:8050`，fake provider，临时 storage `storage-t020-smoke`。
  - Web：`127.0.0.1:3050`，`NEXT_PUBLIC_DEMO_MODE=false`，API Base 指向 `http://127.0.0.1:8050`。
  - 项目：`T020-教案编辑演示`。
  - 操作链路：进入工作区 → 生成并确认 `textbook_parse` → 工作区推进到 `公开课教案 / 30%` → 生成 `lesson_plan` → 结果页显示“公开课教案编辑”和“保存教案” → 添加 `t020_smoke_edit` 课堂追问 → 点击“保存教案”并显示“已保存到后端” → 点击“确认通过” → 工作区推进到 `视频导入选择 / 40% / 进入「视频导入选择」`。
  - 返回首页并刷新后，“继续工作”和“项目概览”均显示 `视频导入选择 / 40% / 进入「视频导入选择」`，未再显示本地标题 `视频设计导入`。
  - 浏览器控制台 `error/warn` 为空。

### 已更新文件

- `apps\web\src\lib\types.ts`
- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\api-mappers.ts`
- `apps\web\src\lib\store.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `apps\web\src\components\project\ProjectCard.tsx`
- `apps\web\src\components\screens\DashboardScreen.tsx`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 关键结论

- T020 不需要补后端接口；T019 确认的 `/generate`、`GET /nodes/{node_id}`、`/edit`、`/approve` 足够支撑本地演示。
- 当前编辑器是本地演示用轻量文本/JSON 编辑，不是上线级富文本教案编辑器。
- 保存语义是提交完整 content 到后端新版本；当前不做字段级 diff 或局部 patch。

### 上线前仍是风险

- `lesson_plan/edit` 后端仍接受任意 dict，上线前需要 schema 校验和字段级错误提示。
- 前端编辑器仍是轻量文本/JSON，不适合正式教师编辑体验。
- 正式鉴权、行级权限、真实 provider、多浏览器、性能和部署不在 T020 范围。
- 首页真实 API 模式仍会为每个项目补拉 manifest；项目数量增长后应由后端列表接口提供阶段摘要，或前端做分页/懒加载。

### 建议下一个接手角色

测试工程师接手 T021，按本地演示口径回归：创建项目 → 生成并确认教材解析 → 生成教案 → 编辑保存 → 确认推进 → 首页/工作区状态同步；随后首席系统架构师复核 T019-T021 是否通过。

---

## 【本轮】后端工程师 — T019 公开课教案节点最小契约确认

### 本轮目标

与前端 T020 并行推进公开课教案节点端到端演示，确认 `lesson_plan` 节点可生成、可获取当前产出、可保存轻量编辑、可确认，并在确认后通过 manifest 推进到下一节点。

### 已完成事项

- 读取项目规则、最新交接、任务调度、后端 API 契约和本地演示 QA 冒烟报告。
- 复核现有后端接口：`POST /projects/{project_id}/nodes/lesson_plan/generate`、`GET /projects/{project_id}/nodes/lesson_plan`、`POST /projects/{project_id}/nodes/lesson_plan/edit`、`POST /projects/{project_id}/nodes/lesson_plan/approve`。
- 判断现有接口已足够支撑 T019，本轮未修改后端业务代码。
- 使用 fake provider 和隔离 storage 跑 HTTP 直连链路：创建项目 → 上传教材 → `textbook_parse generate/approve` → `lesson_plan generate` → `GET lesson_plan` → `lesson_plan edit` → `GET lesson_plan` → `lesson_plan approve` → `GET manifest`。
- 更新 `workflow\multi-agent\dispatch.md` 中 T019 状态为已完成。
- 更新后端角色记忆。

### 验证证据

- `python -m pytest apps\api\tests -q`：`27 passed, 2 xfailed`。
- HTTP 直连项目：`proj_243d95a1b8ff`，API 使用 `PROVIDER_MODE=fake`、临时 storage `storage-t019-smoke`。
- HTTP 直连结果：`textbook_parse generate=needs_review`、`textbook_parse approve=approved`、`lesson_plan generate=needs_review`、`lesson_plan edit=needs_review`、编辑后的 `teaching_objectives` 已通过 `GET lesson_plan` 持久化、`lesson_plan approve=approved`。
- 最终 manifest：`textbook_parse=approved`、`lesson_plan=approved`、`intro_selection=not_started`。

### 前端 T020 调用建议

1. 前置条件：`textbook_parse` 已经 `approved`。
2. 生成教案：`POST /projects/{project_id}/nodes/lesson_plan/generate`，body 可传 `{}`。
3. 获取当前产出：`GET /projects/{project_id}/nodes/lesson_plan`，读取 `data.content` 渲染教案。
4. 保存轻量编辑：`POST /projects/{project_id}/nodes/lesson_plan/edit`，body 为 `{ "content": { ...完整 lesson_plan 内容... } }`；后端会写入新版本并保持 `needs_review`。
5. 保存后刷新：再次 `GET /projects/{project_id}/nodes/lesson_plan`，确认编辑内容已成为当前版本。
6. 确认教案：`POST /projects/{project_id}/nodes/lesson_plan/approve`，body 可为空或 `{ "approve_note": "..." }`。
7. 推进展示：`GET /projects/{project_id}/manifest`，前端应看到 `lesson_plan=approved`，下一节点 `intro_selection=not_started`，即可进入导入方案选择入口。

### 现有接口是否足够

足够。T019 不需要新增 endpoint，也不需要扩展请求模型。当前 `/edit` 的语义是“提交完整节点内容的新人工编辑版本”，适合本地演示的轻量编辑保存；本轮不做字段级 diff、复杂版本树或局部 patch。

### 上线前仍是风险

- `lesson_plan/edit` 当前接受任意 dict，未做 lesson_plan schema 严格校验；本地演示可用，上线前必须补字段校验和错误提示。
- 未配置 `BACKEND_API_TOKEN` 时本地接口开放；上线前必须补正式鉴权、用户权限和行级隔离。
- 真实 Minimax provider 未在本轮调用；本轮只验证 fake provider 和后端状态机契约。
- 编辑保存当前要求前端传完整 content；若后续要支持字段级保存，需要由架构师裁决是否新增 patch 语义。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

前端工程师继续 T020，按上述调用顺序打通工作区公开课教案生成、查看、编辑、保存和确认推进；随后测试工程师执行 T021 本地演示轻量回归。

> 本文件最新补充：首席系统架构师安排前后端并行推进教案节点端到端演示。历史交接保留，便于后续角色追溯。

---

## 【本轮】首席系统架构师 — 前后端并行推进教案端到端演示安排

### 本轮目标

直接安排后端 T019 与前端 T020 并行推进“公开课教案节点端到端演示”，测试 T021 在前后端完成后做轻量回归。

### 关键安排

- 后端 T019：稳定 `lesson_plan` 节点 generate/edit/approve 最小契约，保证可生成、可保存编辑、可确认推进。
- 前端 T020：基于现有接口实现教案节点生成、查看、轻量编辑、保存、确认推进。
- 测试 T021：只做本地演示轻量回归，不做上线验收。

### 协作规则

- 前后端可以同时开始。
- 若后端发现现有 `/nodes/{node_id}/edit` 已足够，后端不必强行改代码，只需补交接说明和验证证据。
- 若前端发现接口缺字段或保存语义不够，先在交接中列出最小阻塞点，由架构师裁决是否扩后端。
- 本轮不处理真实 provider、正式鉴权、部署、完整 9 步流程和复杂版本 diff。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

后端工程师和前端工程师并行接手；测试工程师等待二者交付后接手。

---

## 【本轮】前端工程师 — T015/T016 二次复核

### 本轮目标

用户重复下发 T015 和 T016 后，前端工程师按本地演示打磨口径重新复核当前代码、验证命令和浏览器主链路；不做上线发布、不扩展后端接口、不重复改动已经通过的功能。

### 已完成事项

- 重新读取 `AGENTS.md`、`workflow\multi-agent\handoffs\latest.md`、`workflow\multi-agent\dispatch.md`、`docs\qa-audits\2026-06-20-local-demo-smoke.md`。
- 复核当前代码：
  - `apps\web\src\lib\store.ts`：真实 API 模式 `loadProjects()` 已在读取列表后补拉各项目 manifest 摘要，合并当前阶段、进度、下一步动作。
  - `apps\web\src\components\project\ProjectCard.tsx`：项目卡片已展示当前阶段、下一步动作和总进度。
  - `apps\web\src\components\screens\NewProjectScreen.tsx`：第 2 步已统一为“教材内容准备 / 教材预览 / 确认用于创建项目”，并明确工作区“生成草稿”才触发后端真实解析。
- 未做新的功能代码改动；只更新前端角色记忆和本交接记录，补充本轮复核证据。

### 验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器真实 API 模式复核：
  - API：`127.0.0.1:8042`，fake provider，临时 storage `storage-t015-t016-recheck`。
  - Web：`127.0.0.1:3042`，`NEXT_PUBLIC_DEMO_MODE=false`，API Base 指向 `http://127.0.0.1:8042`。
  - 创建项目 `T015-T016-复核项目`。
  - 新建向导第 2 步显示“教材内容准备”“生成教材预览”“确认用于创建项目”，并明确“创建项目后上传教材，进入工作区点击生成草稿才触发后端真实解析”。
  - 工作区点击 `生成草稿` 后 `textbook_parse` 进入待确认并显示后端产出；点击 `确认通过` 后工作区推进到 `公开课教案 / 30% / 进入「公开课教案」`。
  - 返回首页后，“继续工作”和“项目概览”均显示 `公开课教案 / 30% / 进入「公开课教案」`，不再显示 `项目配置 / 0%`。
  - 浏览器控制台 `error/warn` 为空。

### 已更新文件

- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 关键结论

- T015、T016 当前代码和浏览器链路均仍满足验收。
- 本轮未发现需要补后端接口的问题。
- T015/T016 已经过测试 T017 与架构师 T018 复核，本轮前端二次复核结果与既有结论一致。

### 剩余风险

- 首页真实 API 模式仍存在 manifest fan-out 请求，项目数量大时需后端列表摘要或前端分页/懒加载。
- 新建项目第 2 步仍是本地演示预览语义，不是上线级教材文件上传、替换、版本管理和解析状态闭环。

### 建议下一个接手角色

按当前调度继续推进 T019/T020：后端确认教案节点 edit/approve 契约，前端接手公开课教案节点编辑/保存/确认演示链路。

---

## 【本轮】首席系统架构师 — T018 本地演示打磨复核

### 本轮目标

复核 T015-T017 是否符合本地演示打磨目标，并决定下一小阶段方向。

### 已完成事项

- 读取 T015、T016、T017 最新交接记录和测试报告。
- 复核关键 diff：`apps\web\src\lib\store.ts`、`apps\web\src\components\project\ProjectCard.tsx`、`apps\web\src\components\screens\NewProjectScreen.tsx`。
- 新鲜运行后端测试：`python -m pytest apps\api\tests -q`。
- 新鲜运行前端验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build`。
- 启动隔离 API：`127.0.0.1:8031`，fake provider，临时 storage。
- 启动 Web：`127.0.0.1:3031`，真实 API 模式指向 `127.0.0.1:8031`。
- 浏览器复核新建项目第 2 步语义、教材解析生成/确认、返回首页后阶段/进度/下一步动作同步。
- 更新 `workflow\multi-agent\dispatch.md`、`workflow\multi-agent\stage-review.md`、`workflow\multi-agent\roles\architect.md` 和本交接记录。

### 关键结论

- T015-T017 通过架构师复核，本轮本地演示打磨【通过】。
- T015 达标：首页“继续工作”和“项目概览”均能显示 `公开课教案 / 30% / 进入「公开课教案」`，与工作区 manifest 一致。
- T016 达标：新建项目第 2 步清楚表达为“教材内容准备 / 教材预览”，并说明真实解析在工作区点击“生成草稿”触发。
- 下一小阶段进入“公开课教案节点编辑/保存/确认演示”，不继续优先打磨项目创建体验。

### 验证证据

- `python -m pytest apps\api\tests -q`：`27 passed, 2 xfailed`。
- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过；Next 仍显示 `Skipping validation of types`，已由独立 tsc 覆盖。
- 浏览器：真实 API 模式创建项目 `T018-架构复核项目`，第 2 步显示“教材内容准备”“生成教材预览”“确认用于创建项目”。
- 浏览器：工作区 `textbook_parse` 生成并确认后推进到 `公开课教案 / 30%`。
- 浏览器：首页继续工作和项目概览均显示 `公开课教案 / 30% / 进入「公开课教案」`。
- 浏览器控制台：`error/warn` 为空。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待处理问题

- 首页真实 API 模式为每个项目补拉 manifest，数据量大时需后端列表摘要或前端分页/懒加载。
- 新建项目第 2 步仍不是正式教材文件上传、替换、版本管理和真实解析闭环。
- 上线前风险仍未处理：真实 provider、生产鉴权、部署、多浏览器、性能。

### 新增任务

- T019：后端确认或补齐教案节点 edit/approve 最小演示契约。
- T020：前端打通公开课教案生成、轻量编辑、保存、确认推进演示链路。
- T021：测试工程师做教案节点本地演示轻量回归。

### 建议下一个接手角色

后端工程师和前端工程师；若确认现有 `/nodes/{node_id}/edit` 足够，后端可只做交接确认，主要工作由前端执行 T020。

---

## 【本轮】测试工程师 — T017 本地演示轻量回归

### 本轮目标

在 T015-T016 完成后，只按本地演示口径回归首页 manifest 同步、新建项目第 2 步教材语义、真实 API 最小链路；不做上线验收。

### 已完成事项

- 启动隔离 fake API：`http://127.0.0.1:8027`，storage 使用 `storage-t017-regression`。
- 启动 Web 真实 API 模式：`http://127.0.0.1:3027`，API Base 指向 `http://127.0.0.1:8027`。
- 验证 API `/health` 正常，Web 首页 200。
- 浏览器真实 API 模式创建项目 `T017-本地回归-255800`，创建后进入工作区。
- 验证新建项目第 2 步显示为“教材内容准备 / 生成教材预览 / 确认用于创建项目”，并提示真实解析在工作区点击“生成草稿”触发。
- 在工作区生成并确认 `textbook_parse`，确认后工作区推进到 `公开课教案 / 30% / 进入「公开课教案」`。
- 返回首页后精确复核“继续工作”和“项目概览”均显示 `公开课教案 / 30% / 进入「公开课教案」`。
- 浏览器控制台 `error/warn` 为空。
- 后端 manifest 抽检：`textbook_parse=approved`，`lesson_plan=not_started`，节点数 `10`。

### 关键结论

- T017 本地演示轻量回归【通过】，标记为【可演示】。
- T015 首页项目卡片与工作区 manifest 状态不同步问题已回归通过。
- T016 新建项目第 2 步语义误导问题已回归通过。
- 本轮未发现阻塞本地演示的问题。

### 已更新文件

- `docs\qa-audits\2026-06-20-local-demo-smoke.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 上线前仍是风险

- 首页真实 API 模式仍会对每个项目补拉 manifest；上线前建议后端列表接口提供阶段摘要，或前端分页/懒加载。
- 新建项目第 2 步当前是教材预览语义，不是正式教材文件上传、替换、版本管理和真实解析闭环。
- 真实 provider、生产鉴权、部署、多浏览器和性能不在 T017 范围。

### 建议下一个接手角色

首席系统架构师接 T018，做本地演示打磨阶段复核。

---

## 【本轮】前端工程师 — T016 新建项目第 2 步教材语义收口

### 本轮目标

本地演示打磨阶段收口新建项目第 2 步“教材解析”的 UI 语义，避免用户误以为创建向导里的前端演示预览已经等同后端真实教材解析；不扩展后端接口、不做复杂上传版本管理、不破坏真实 API 创建项目和自动上传教材文本链路。

### 已完成事项

- 修改 `apps\web\src\components\screens\NewProjectScreen.tsx`：
  - 步骤标题从“教材上传与内容 / 上传与解析”改为“教材内容准备 / 内容准备与预览”。
  - 第 2 步顶部增加说明：创建阶段只准备教材文本和预览摘要；创建项目后会上传教材内容；进入工作区点击“生成草稿”才触发后端真实教材解析生成。
  - 按钮、进度、toast、结果卡片和步骤摘要统一改为“生成教材预览”“确认用于创建项目”“教材预览摘要”等语义。
  - 保留现有 `parseStatus` 内部状态和 `MOCK_TEXTBOOK_PARSE` 预览结果，仅收口用户可见语义，避免扩大重构。
- 未修改 `createProjectFromDraft()`、`uploadProjectTextbook()` 或后端接口；真实 API 模式创建项目后自动上传教材文本的链路保持不变。

### 验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 文案扫描：新建项目第 2 步不再出现“开始解析 / 解析中 / 确认解析结果 / 已解析 / 未解析 / 解析结果预览”等会暗示后端已真实解析的用户可见文案。

### 已更新文件

- `apps\web\src\components\screens\NewProjectScreen.tsx`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 关键结论

- T016 不需要补后端接口；当前本地演示阶段用文案和状态提示即可清楚区分“新建向导教材准备”和“工作区真实教材解析”。
- 用户在创建向导第 2 步看到的是预览与准备；真实 `textbook_parse/generate` 仍由工作区节点的“生成草稿”触发。

### 剩余风险

- 当前第 2 步仍是前端演示预览，不是正式文件上传、替换、版本管理和解析状态闭环；上线前仍需设计真实上传与版本管理体验。
- 本轮未做浏览器截图复核；已完成静态文案扫描和 tsc/lint/build。建议 T017 由测试工程师做浏览器轻量回归。

### 建议下一个接手角色

测试工程师接手 T017，回归 T015 首页 manifest 同步、T016 新建项目教材语义和真实 API 最小链路；随后首席系统架构师处理 T018 阶段复核。

---

## 【本轮】前端工程师 — T015 首页项目卡片同步 manifest 状态

### 本轮目标

本地演示打磨阶段修复真实 API 模式下“首页项目卡片进度”和“工作区 manifest 状态”不同步问题；不做全站重构、不改无关 UI、不扩展后端接口。

### 已完成事项

- 定位根因：真实 API 模式下 `loadProjectManifest` 已能把项目推进到后端当前阶段，但首页挂载会重新 `loadProjects()`；`GET /projects` 只返回基础项目摘要，`mapApiProject(project)` 无 manifest 节点时会回退为 `project-config / 0%`。
- 修改 `apps\web\src\lib\store.ts`：真实 API 模式 `loadProjects` 在读取项目列表后，并行拉取每个项目的 manifest 摘要，用 `mapApiManifest` 合并项目当前阶段、进度、下一步动作与 `stagesByProject`。
- 修改 `apps\web\src\components\project\ProjectCard.tsx`：项目概览卡片补充显示“下一步动作”，保证首页卡片直接传达后端当前阶段、总进度和下一步操作。
- 未补后端接口；当前后端已有 `GET /projects/{project_id}/manifest` 能支撑本地演示同步。

### 验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器真实 API 模式验证：
  - API：`127.0.0.1:8001`，fake provider，临时 storage `storage-t015-smoke`，CORS 允许 `localhost:3002` 和 `127.0.0.1:3002`。
  - Web：`127.0.0.1:3002`，`NEXT_PUBLIC_DEMO_MODE=false`，API Base 指向 `http://127.0.0.1:8001`。
  - 创建项目 `T015-首页同步验证`，进入工作区后触发 `textbook_parse` 生成并确认。
  - 工作区推进到 `公开课教案 / 30%` 后返回首页，继续工作区和项目概览卡片均显示 `公开课教案`、`30%`、`进入「公开课教案」`，不再显示 `项目配置 / 0%`。

### 已更新文件

- `apps\web\src\lib\store.ts`
- `apps\web\src\components\project\ProjectCard.tsx`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 关键结论

- T015 不需要补后端接口即可完成；前端通过列表后同步 manifest 摘要解决本地演示状态一致性。
- 首页“继续工作”和“项目概览”现在共用合并后的项目状态，展示后端当前阶段、总进度和下一步动作。

### 剩余风险

- 真实 API 模式首页现在会对项目列表中的每个项目额外请求一次 manifest；本地演示数据量小可以接受。上线前若项目数量增多，建议后端 `GET /projects` 返回当前阶段、进度和下一步摘要，或前端做分页/懒加载。
- T016 “新建项目第 2 步教材解析语义”尚未处理，仍待前端接手。

### 建议下一个接手角色

前端工程师继续处理 T016；之后测试工程师执行 T017 本地演示轻量回归。

---

## 【本轮】首席系统架构师 — 本地演示打磨任务派发

### 本轮目标

在本地可演示阶段已通过的基础上，继续只做演示体验打磨，不进入上线发布、不启动运维、不做完整测试闭环。

### 已完成事项

- 新增 T015：前端修复首页项目卡片与工作区 manifest 不同步。
- 新增 T016：前端收口新建项目第 2 步教材解析语义。
- 新增 T017：测试工程师在 T015-T016 后做轻量回归。
- 新增 T018：首席系统架构师在 T017 后做阶段复核。

### 关键结论

- 下一轮主力只派前端；测试延后做轻量回归。
- 后端暂不派活，除非前端发现现有 API 无法支撑首页 manifest 摘要。
- 运维暂不介入；上线发布风险继续挂起。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 建议下一个接手角色

前端工程师。

---

## 【本轮】首席系统架构师 — 本地可演示阶段验收

### 本轮目标

验收后端、前端、测试工程师完成的“本地可演示”阶段，不按上线发布标准验收。

### 已完成事项

- 读取后端、前端、测试工程师最新交接记录。
- 复核本地演示轻量冒烟报告：`docs\qa-audits\2026-06-20-local-demo-smoke.md`。
- 复核关键代码：后端 `settings.py`、前端 `api-client.ts`、`api-mappers.ts`、`store.ts`、工作区真实 API 链路。
- 新鲜运行后端测试：`python -m pytest apps\api\tests -q`。
- 新鲜运行前端验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build`。
- 启动隔离 API：`127.0.0.1:8021`，fake provider，临时 storage。
- HTTP 抽检：`/health`、创建项目、`.txt` 教材上传、`textbook_parse` 生成/确认、`lesson_plan` 生成、manifest 状态。
- 浏览器抽检：`127.0.0.1:3021` 真实 API 模式登录、项目列表、进入工作区、读取 10 个后端 manifest 节点。
- 更新 `workflow\multi-agent\dispatch.md`、`workflow\multi-agent\stage-review.md`、`workflow\multi-agent\roles\architect.md` 和本交接记录。

### 关键结论

- 本地可演示阶段【通过】。
- 验收范围只覆盖本地 API + Web + fake provider + 真实 API 模式最小链路，不代表上线发布通过。
- 后端最小链路可用：健康检查、创建项目、上传 `.txt` 教材、教材解析生成/确认、教案生成。
- 前端真实 API 模式可用：登录后读取后端项目列表，进入工作区后显示后端 manifest 和节点详情。
- 测试报告中提出的非阻塞问题已复现：首页项目卡进度仍可能显示项目配置 0%，但工作区 manifest 已推进到公开课教案。

### 验证证据

- `python -m pytest apps\api\tests -q`：`27 passed, 2 xfailed`。
- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过；Next 仍显示 `Skipping validation of types`，已由独立 tsc 覆盖类型验证。
- HTTP 抽检结果：`health=true`，`.txt` 教材 `uploaded`，`textbook_parse=approved`，`lesson_plan=needs_review`。
- 浏览器抽检：真实 API 模式登录成功，首页读到后端项目，工作区显示 `10 个后端 manifest 节点`，控制台 `error/warn` 为空。

### 已更新文件

- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待处理问题

- 前端：首页项目卡片应同步 manifest 摘要，否则回到首页后仍可能显示“项目配置 0%”。
- 前端/后端：新建项目第 2 步仍是前端演示解析，不等同真实教材上传链路，需要统一 UI 语义。
- 后端：上线前仍需修复两个 xfail：未配置 token 时写接口开放、provider schema 缺必填字段未严格拒绝。
- 运维：上线前仍需容器化、密钥注入、日志、备份、回滚。

### 建议下一个接手角色

前端工程师优先处理首页 manifest 摘要同步；随后前端/后端一起收口“新建项目第 2 步真实教材上传”语义。测试工程师暂不需要完整上线验收。

---

## 【本轮】测试工程师 — 本地演示轻量冒烟

### 本轮目标

只做本地演示冒烟，不做上线验收；验证 API/Web 可启动、前端真实 API 模式创建项目、列表刷新、工作区 manifest、fake provider 生成/确认链路和浏览器控制台。

### 已完成事项

- 启动隔离 fake API：`http://127.0.0.1:8001`，storage 使用 `storage-smoke-fake`。
- 显式配置本地演示 CORS 允许 `http://localhost:3002` 和 `http://127.0.0.1:3002`。
- 启动 Web：`http://127.0.0.1:3002`，真实 API 模式指向 `http://127.0.0.1:8001`。
- 直接 HTTP 验证 `/health`、创建项目、列表、教材 `.txt` 上传、`textbook_parse` 生成/确认、`lesson_plan` 生成和 manifest 状态变化。
- 浏览器验证前端创建项目 `UI冒烟-8001-clean`、首页项目列表刷新、进入工作区、显示 `10 个后端 manifest 节点`。
- 浏览器点击 `生成草稿` 触发 fake provider 生成教材解析，随后点击 `确认通过`，工作区推进到 `公开课教案`。
- 浏览器控制台 `error/warn` 为空。
- 新增轻量冒烟报告：`docs\qa-audits\2026-06-20-local-demo-smoke.md`。

### 关键结论

- 本地演示口径下判定为【可演示】。
- 本轮未发现阻塞本地演示的问题。
- 上线前再修：新建项目第 2 步仍是前端演示解析，不等同真实教材上传链路；3002 端口需显式 CORS；首页项目卡进度与工作区 manifest 推进存在展示不同步。

### 已更新文件

- `docs\qa-audits\2026-06-20-local-demo-smoke.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待决策问题

- 是否把前端新建项目第 2 步改为真实教材上传和后端解析入口，还是保留为配置草稿并把真实解析统一放到工作区。
- 是否为本地演示提供固定 dev profile，避免 3000/3002 端口和 CORS 配置反复手动切换。
- 首页项目列表是否必须展示 manifest 推进后的当前阶段和进度。

### 建议下一个接手角色

首席系统架构师。

### 下个角色需要知道的上下文

- 当前冒烟不是上线验收，只证明本地演示可跑。
- fake provider 链路可用于演示，但真实 provider、权限、部署、多浏览器和性能均未覆盖。
- 本轮为避免端口和旧服务干扰，最终有效组合是 8001 API + 3002 Web + 显式 3002 CORS。

---

## 【本轮】前端工程师 — 本地真实 API 演示主流程打通

### 本轮目标

在“不上线发布、只保证本地可演示”的阶段目标下，把前端从 mock 工作台推进到真实 API 最小闭环：demo/mock 模式和真实 API 模式边界清楚，真实模式可创建项目、读取项目列表、进入工作区拉取 manifest 和节点详情，并至少打通一个生成、确认、刷新状态的最小演示链路。

### 已完成事项

- 扩展前端 API client：接入项目列表、项目创建、manifest、节点详情、教材上传、节点生成和节点确认接口。
- 真实 API 模式下，项目列表来自 `GET /projects`，创建项目走 `POST /projects`，不再把 mock 项目当真实状态来源。
- 真实 API 模式下，进入项目工作区后读取 `GET /projects/{project_id}/manifest` 和 `GET /projects/{project_id}/nodes/{node_id}`。
- 新建项目后自动把向导教材内容或 mock 解析摘要上传为 `textbook.txt`，满足后端 `textbook_parse/generate` 的本地演示前置条件。
- 工作区已打通 `textbook_parse` 最小链路：生成草稿、刷新状态、确认通过，并可进入 `lesson_plan` 节点查看后端状态。
- demo/mock 模式继续隔离使用 mock 数据和本地模拟动作；真实 API 模式不混用 mock 项目、mock manifest 或 mock 节点作为业务真状态。
- API 错误会在工作区节点操作区显示用户可读提示，并保留 toast 提示，不再静默失败。

### 测试与验证证据

- `cd apps\web && bunx tsc --noEmit --pretty false`：通过。
- `cd apps\web && bun run lint`：通过。
- `cd apps\web && bun run build`：通过。
- 浏览器 smoke 已验证本地链路：
  - 后端：`PROVIDER_MODE=fake`、`STORAGE_ROOT=storage-local-demo`、`CORS_ORIGINS=http://localhost:3002,http://127.0.0.1:3002`，再运行 `python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8011`
  - 前端：`NEXT_PUBLIC_DEMO_MODE=false`、`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8011`、`bunx next dev -p 3002`
  - 操作链路：登录真实 API 模式 → 首页项目列表 → 创建项目 → 自动上传教材文本 → 进入工作区 → manifest 显示 10 个后端节点 → 对 `textbook_parse` 生成草稿 → 查看后端 JSON 产出 → 确认通过 → 进入 `lesson_plan` 节点。

### 已更新文件

- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\api-mappers.ts`
- `apps\web\src\lib\store.ts`
- `apps\web\src\lib\types.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 本地演示已满足

- 前端可通过 `NEXT_PUBLIC_DEMO_MODE` 在 demo/mock 和真实 API 模式之间清楚切换。
- 真实 API 模式可创建项目，并在首页/项目列表看到后端项目数据。
- 真实 API 模式可进入项目工作区查看后端 manifest 和节点详情。
- 最小生成/确认链路已通：`textbook_parse/generate` → `textbook_parse/approve` → manifest/节点刷新。
- 后端返回错误时，前端会给用户可读提示，适合本地演示排障。

### 上线前仍是风险

- 教材上传目前是创建项目后自动生成 `textbook.txt`，不是正式文件上传、预览、替换和版本管理闭环。
- `lesson_plan` 之后的完整工作流还没做全链路 UI 优化。
- 节点编辑、退回、重试、保存草稿、视频方案采纳等写动作仍未完整接真实 API。
- 首页系统轻状态、日志页、脚本页、配置页仍有 mock 展示内容。
- 权限 UI 仍是本地演示模式，不是生产认证或多用户权限体系。
- Next dev 可能出现 `allowedDevOrigins` 跨源提示，属于本地开发体验待优化，不影响当前 smoke。

### 建议下一个接手角色

测试工程师基于本轮 smoke 链路做本地验收；首席系统架构师随后对照“本地可演示”阶段目标复核是否进入下一阶段。

### 下个角色需要知道的上下文

- 当前不要按上线发布验收，本轮只承诺本地 fake provider / 真实 API 模式可演示。
- 本轮 smoke 生成了本地临时数据目录 `storage-local-demo`，未做清理。
- 若要复现真实 API 模式，请显式设置 `NEXT_PUBLIC_DEMO_MODE=false` 和 `NEXT_PUBLIC_API_BASE_URL`，否则默认会进入 demo/mock 模式。
- 若前端使用非默认端口，后端 `CORS_ORIGINS` 必须包含对应 `localhost` 和 `127.0.0.1` 来源，否则浏览器会显示项目列表读取失败但后端日志仍可能是 200。

---

## 【本轮】后端工程师 — 本地演示后端基础收口

### 本轮目标

补齐本地演示所需的后端最小稳定链路，保证前端真实联调前不会在项目、manifest、节点详情和 fake provider 最小生成链路上遇到 500。

### 已完成事项

- 验证 API 可从仓库根目录通过 `uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8017` 启动。
- 验证 `GET /health` 正常返回。
- 验证 fake provider 模式下可创建项目、查询项目列表、查询 manifest、查询 `textbook_parse` / `lesson_plan` 节点详情。
- 验证教材上传、`textbook_parse/generate`、`textbook_parse/approve`、`lesson_plan/generate`、`lesson_plan/approve` 最小链路可跑通。
- 验证上游未 approve 时生成下游会返回 `409 / UPSTREAM_NOT_APPROVED`。
- 新增 `apps\api\requirements.txt`，补齐本地后端依赖清单。
- 更新 `apps\api\README.md`，补充仓库根目录启动、依赖安装、fake provider 演示配置和常用验证说明。
- 修正后端配置优先级：进程环境变量优先于本地 `.env`，便于本地演示时临时强制 `PROVIDER_MODE=fake` 和清空 `BACKEND_API_TOKEN`，不需要读取或修改真实密钥文件。

### 测试与验证证据

- `python -m pytest apps\api\tests -q`：`27 passed, 2 xfailed`。
- HTTP 冒烟结果：`healthOk=true`，项目列表可查，`textbook_parse` 从 `not_started` 到 `needs_review` 再到 `approved`，`lesson_plan` 从生成到 `approved`。
- HTTP 红线验证：未确认 `textbook_parse` 时请求 `lesson_plan/generate` 返回 `409 / UPSTREAM_NOT_APPROVED`。

### 已更新文件

- `apps\api\app\settings.py`
- `apps\api\tests\test_api_contract.py`
- `apps\api\requirements.txt`
- `apps\api\README.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 本地演示已满足

- 仓库根目录 API 启动可用。
- fake provider 不需要真实密钥即可演示项目创建、列表、manifest、节点详情、教材解析和教案生成确认。
- 前端调用创建项目、项目列表、manifest、节点详情这几类接口不应出现后端 500。
- 最小状态机红线有效：下游生成依赖上游 approved。

### 上线前仍是风险

- 未配置 `BACKEND_API_TOKEN` 时接口仍对本地联调开放；共享网络或生产环境必须配置 token，并补正式账号/行级权限。
- provider 原始输出 schema 严格校验仍是已知 xfail，不可作为正式质量门禁放行。
- Docker、Cloud Run、多实例 SQLite、日志轮转、备份恢复不在本轮范围，仍需运维/架构师后续推进。
- 真实 Minimax / 章鱼哥 provider 未在本轮调用，本轮只验证 fake provider 本地演示链路。

### 建议下一个接手角色

前端工程师接入本地 API 做页面联调；测试工程师按 `docs\qa-audits\2026-06-20-api-contract-gate.md` 复跑前端 smoke checklist。

> 本文件包含三段交接：① 本轮架构师 V0.4 总控闭环升级与任务派发；② 上轮架构师用户反馈飞轮；③ 运维 T004 部署 Runbook。历史交接保留，便于后续角色追溯。

---

## 【本轮】首席系统架构师 — V0.4 总控闭环升级与下一轮任务派发

### 本轮目标

把多角色协作从“分别做完各自任务”升级为“架构师可验收、测试可回归、失败可再派发”的总控闭环，并基于当前产品形态下发下一轮任务。

### 已完成事项

- 更新 `docs\multi-agent\README.md`：新增 V0.4 总控闭环和文件沉淀原则。
- 更新 `workflow\multi-agent\dispatch.md`：补充总控验收规则，并新增 T005-T010。
- 更新 `workflow\multi-agent\decisions.md`：登记 V0.4 总控闭环决策，以及 docker-compose/内网最小部署优先的部署路线裁决。
- 更新 `workflow\multi-agent\stage-review.md`：登记 V0.4 阶段状态为进行中。
- 更新 `workflow\multi-agent\shared-facts.md`：同步总控闭环和部署路线共同事实。
- 更新 `workflow\multi-agent\roles\architect.md`：沉淀架构师总控复核职责。

### 关键结论

- 重要任务默认必须经过：架构师下发 → 专业角色交付 → 测试工程师验收 → 架构师复核 → 通过或再调度。
- 轻量问答不强制落盘；影响阶段推进、接口契约、部署、安全、测试验收或正式交付的任务必须落盘。
- 当前部署路线裁决为：优先补 docker-compose/内网最小部署，Cloud Run 后置。
- 下一轮主线围绕 v1 产品形态收口：P01 用户主流程、第 0 步配置、工作区、反馈飞轮、后端运行契约、前端工作流口径、内网部署、端到端测试。

### 已更新文件

- `docs\multi-agent\README.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\decisions.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待决策问题

- T005 完成后，是否将 PRD 中的“9 步主线”作为前端工作流唯一口径，还是保留当前 14 节点显示并建立映射。
- T006 完成后，是否将 `BACKEND_API_TOKEN` 未配置时接口开放视为仅本地开发可用，生产必须阻断。
- T009 执行后，是否进入 v1 主流程修复阶段。

### 建议下一个接手角色

产品经理、后端工程师、前端工程师可以并行接手 T005-T007；运维等待 T006 结果后接 T008；测试工程师先准备 T009 计划，待 T005-T008 交付后执行。

### 下个角色需要知道的上下文

- 当前产品文档强调“网页优先、线性 9 步、P01 李雪老师、项目第 0 步、PPT/视频双分支、反馈飞轮”。
- 当前前端 `workflow.ts` 显示 14 个节点，可能与 PRD 的 9 步主线存在口径差异，需前端先做差距审查。
- 当前部署不可直接宣布完成，T004 只是 Runbook 草案；下一步需后端运行契约和运维容器化草案。

---

## 【本轮】首席系统架构师 — 建立用户反馈飞轮体系

### 本轮目标

让用户角色的反馈不再是一次性输出，而是回流到文件、被 PM 消费、转化为开发任务的闭环数据资产。

### 已完成事项

- 新建 `workflow\multi-agent\user-feedback.md`：用户反馈台账，含反馈模板、四类分类（亮点/担心/缺口/体验断点）、飞轮闭环图。
- 反馈编号格式 `F-{画像ID}-{序号}`；处理状态：待评估 / 已转任务（T00X）/ 驳回 / 已采纳为决策。
- 更新 `AGENTS.md`：用户角色启动清单加入 `user-feedback.md`；新增"强制反馈回流"和"历史一致性"行为规则；PM 和架构师启动清单加入反馈台账。
- 更新 `docs\multi-agent\README.md`：台账表新增 `user-feedback.md`；用户角色专属规则补两条。
- 更新 `workflow\multi-agent\roles\product-manager.md`：启动必读加入画像和反馈；新增"反馈消费职责"章节。
- 更新 `workflow\multi-agent\roles\architect.md`：启动必读加入 `user-feedback.md`。
- 更新 `workflow\multi-agent\decisions.md`：登记反馈飞轮决策。

### 关键结论

- 用户角色对话结束前必须追加反馈条目，不落盘视为未闭环。
- PM 是反馈台账唯一维护者，决定"转任务 / 驳回 / 升级为决策"。
- 反馈转任务需在 `dispatch.md` 同步标记，形成全链路追溯。
- 飞轮闭环：用户体验 → 反馈回流 → PM 消费 → 任务下发 → 开发改进 → 用户角色再体验。

### 已更新文件

- `workflow\multi-agent\user-feedback.md`（新建）
- `AGENTS.md`
- `docs\multi-agent\README.md`
- `workflow\multi-agent\roles\product-manager.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\decisions.md`
- `workflow\multi-agent\handoffs\latest.md`（本文件）

### 待决策问题

- 是否需要设置季度复盘节奏（PM 定期统计反馈类型分布）。
- 上轮运维 T004 遗留：部署路线 docker-compose vs Cloud Run 仍待裁决。

### 建议下一个接手角色

**用户角色**——首次实地测试飞轮，让"你是用户：……"对话跑起来，产出第一条 `F-P01-001` 反馈。
或**产品经理**——首次消费反馈台账，验证 PM 工作流。
或**首席系统架构师**——继续处理上轮运维遗留的部署路线裁决。

### 下个角色需要知道的上下文

- 反馈飞轮已就位但还是空的，需要第一次"你是用户：……"对话产生 F-P01-001。
- 第一次反馈建议覆盖完整产品入口：登录 + 首页 + 新建项目第 0 步 + 工作区，让 PM 拿到全景式初始反馈。
- 反馈飞轮原则：用户角色只输出感受不给方案，PM 翻译为开发任务，架构师裁决优先级。

---

## 【上轮】运维/部署工程师 — T004 部署 Runbook

### 本轮目标

完成 T004：建立 ShanHaiEdu 项目的最小部署可复现基础，让新人能够按文档启动 Web 和 API，并明确当前距离正式部署还缺什么。

### 已完成事项

- 只读梳理 `apps\web\package.json`、`apps\web\Caddyfile`、`apps\api\README.md`、`.gitignore`、API settings/main/security/store/provider 相关运行信息。
- 新增 `docs\ops-runbook-draft.md`，输出《运维/部署方案与 Runbook 草案》。
- 梳理 Web 开发、构建、生产启动命令和日志位置。
- 梳理 API 启动命令、健康检查、默认 provider、storage 目录结构和受保护接口 token 行为。
- 梳理环境变量名与用途，仅记录变量名，不读取、不打印真实密钥。
- 检查 Docker/compose 文件现状：未发现正式 Dockerfile 或 docker-compose/compose 文件。
- 检查防误提交规则：`.env`、日志、SQLite、storage、`.next` 等已在忽略规则覆盖范围内；未发现这些运行时文件已被 git 跟踪。
- 更新运维角色记忆、共享事实和 T004 调度状态。

### 关键结论

- 当前已具备 Web/API 本地最小启动基础，但尚不具备正式可部署基础设施。
- Web 默认端口 `3000`，API 默认端口 `8000`，API 健康检查为 `GET /health`。
- `apps\api\.env.example` 为空，API 依赖清单缺失，是新人复现和容器化前的关键缺口。
- 当前仓库未发现正式 Dockerfile、docker-compose/compose 文件。
- 正式部署前必须解决密钥注入、storage 持久化、SQLite 多实例风险、日志轮转、备份恢复和回滚。
- `docker-compose` 还是 Cloud Run 优先推进，需首席系统架构师裁决。

### 已更新文件

- `docs\ops-runbook-draft.md`
- `workflow\multi-agent\roles\ops-devops-engineer.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\dispatch.md`

### 待决策问题

- 当前阶段部署路线：优先补 docker-compose/内网最小部署，还是直接按 Cloud Run 约束推进。
- `docs` 下 PDF/PPTX 白名单是否继续保留。

### 建议下一个接手角色

首席系统架构师。

### 下个角色需要知道的上下文

- 运维已完成 T004 Runbook 草案，未实现 Dockerfile/compose，也未修改业务代码。
- 建议首席系统架构师先裁决部署路线；随后后端工程师补 API 依赖清单、`.env.example` 和生产启动边界；再由运维补容器化或 Cloud Run 配置草案。
- 测试工程师可基于 `docs\ops-runbook-draft.md` 第 11 节建立新人冷启动回归清单。




