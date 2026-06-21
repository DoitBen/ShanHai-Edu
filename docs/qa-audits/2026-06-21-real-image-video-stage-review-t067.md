# T067 真实图片/视频全链路阶段复核

日期：2026-06-21  
角色：首席系统架构师  
结论：**阶段阻塞，不达到“本地真实 API 可演示”，不能进入产品演示录屏。**

## 复核依据

- T063 测试报告：`docs\qa-audits\2026-06-21-real-image-video-e2e.md`
- T063 API 证据：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\summary.json`
- T063 浏览器证据：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-workspace.png`
- T063 控制台证据：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-console.json`
- T064 后端交接：`docs\backend-t064-real-media-stability-handoff.md`
- T065 前端交接：`workflow\multi-agent\handoffs\latest.md`
- T065 截图证据：`docs\qa-audits\t065-video-assets-real-api.png`、`docs\qa-audits\t065-final-video-real-api.png`
- T066 运维手册：`docs\ops-real-provider-demo-runbook.md`

## 裁决

| 裁决项 | 结论 | 依据 |
|---|---|---|
| 是否达到“本地真实 API 可演示” | 否 | T063 `summary.json` 中 `ok=false`，`generated_image_paths=[]`、`video_task_ids=[]`、`final_video_path=null`、`ppt_path=null` |
| 是否可以进入产品演示录屏 | 否 | 无真实图片、无真实视频 task、无 clip 下载、无 `final_video.mp4`、无 PPT 实物 |
| 是否还有阻塞项 | 有 | `intro_video_asset/generate` 返回 `400 / GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)` |
| 下一阶段 | B 前的阻塞修复，不是 A/B/C 三选一 | 先修真实链路阻塞并复测；复测通过后再进入“演示封版”或“视频质量打磨” |

## 关键事实

1. T063 已经证明真实文本链路可从 PDF 推进到 `intro_video_screenplay=approved`。
2. T063 在 `intro_video_asset/generate` 稳定阻塞，接口返回 400，且没有创建 `image_generation` task。
3. T063 证据目录不存在 `final_video.mp4` 和 PPT 文件，只有 `summary.json`、浏览器截图和控制台 JSON。
4. T064 后端加固的新鲜目标测试通过：`6 passed`。该测试证明图片/视频 task 状态、重试和下载安全有效，但没有复测 T063 的真实外部 API 全链路，也没有覆盖 `intro_video_asset/generate` 的真实 LLM 空响应/非 JSON 原始阻塞。
5. T065 前端体验收口可接受，但交接明确“未重新触发外部真实 provider 生成新图片或新视频任务”。
6. T066 运维手册存在口径滞后：手册写“生图链路当前不在 apps\api 服务内”，但 T064 已新增 API 层 `NewApiImageProvider`。需要运维修正文档，避免后续演示配置误导。

## 阻塞问题

### P1：`intro_video_asset/generate` 真实链路在进入生图前失败

- 现象：`POST /projects/proj_6a0c9a3a6d81/nodes/intro_video_asset/generate` 返回 400。
- 错误：`GENERATION_INPUT_INVALID`，消息为 `Expecting value: line 1 column 1 (char 0)`。
- 影响：无法创建 `image_generation` task，无法进入 storyboard、真实视频、clip 下载、final video、PPT 导出。
- 代码判断：`apps\api\app\services.py` 先执行 `_generate_text_node()`，成功后才会进入 `_generate_image_tasks()`；因此 T063 失败点发生在文本资产 JSON 生成阶段，T064 的图片 task 加固不能自动修复此阻塞。

### P2：T066 运维手册与当前 API 能力不一致

- T064 已新增 API 层 `NewApiImageProvider` 和 `IMAGE_PROVIDER_MODE`。
- T066 仍写生图由 `skills\imagegen-myself` 脚本负责，不是 API 内建 endpoint。
- 影响：演示人员可能按错误模式配置，导致真实生图链路无法复测。

## 返工任务

### T068 后端阻塞修复

修复 `intro_video_asset/generate` 在真实 LLM 返回空响应/非 JSON/缺字段时的错误诊断与兜底策略；确保文本资产 JSON 成功后能创建 `image_generation` task。补测试覆盖空响应、非 JSON、缺必填字段、图片 provider 成功、图片 provider 失败。

### T069 测试复测

在 T068 后重跑 T063 完整真实链路，必须产出真实图片路径、视频 task id、clip 下载路径、`final_video.mp4`、PPT 路径，并验证 PPT 内嵌视频或下载链接有效。

### T070 运维修正

修正 `docs\ops-real-provider-demo-runbook.md` 的生图 provider 口径，按当前 API 层 `NewApiImageProvider` 和 `IMAGE_PROVIDER_MODE` 更新启动、检查和排障说明。

### T071 架构师复核

T068-T070 完成后再次复核，裁决是否进入 A 演示封版、B 视频质量打磨或 C 部署上线准备。

## 阶段结论

T067 不通过。当前只能说“真实文本链路 + 前端状态展示 + 后端任务状态机加固”已有基础，不能说“真实图片/视频全链路可演示”。下一步必须先修 T068 并由 T069 复测产出实物，再谈演示录屏。
