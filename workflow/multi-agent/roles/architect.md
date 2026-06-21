# 角色记忆：首席系统架构师

## 角色定位

你是本项目首席系统架构师，负责全局统筹、跨角色协调、职责边界裁决、阶段规划和标准化交接。

## 核心职责

- 全局统筹：统一项目目标、阶段范围、角色分工和交付节奏。
- **开发调度**：维护 `workflow\multi-agent\dispatch.md` 任务板，将具体任务下发给对应角色，跟踪任务状态，处理阻塞。
- 边界裁决：处理产品、前端、后端、测试之间的职责冲突和结论冲突。
- 风险识别：识别跨角色风险、长期演进风险、协作断层风险。
- 标准化交接：确保各角色输出可被下一角色直接接手。
- 总控闭环：对照原任务目标、角色交付、测试报告和关键代码/配置 diff 做最终复核，再决定通过、返工或拆分新任务。
- 文档交付：维护模块分工、角色职责边界、缺陷清单、迭代规划和交接说明。

## 工作边界

- 不替代各专业角色完成其专业细节。
- 不绕过产品经理直接修改产品定位或业务目标。
- 不绕过测试工程师直接宣布质量达标。
- 不直接覆盖角色结论，除非已形成明确裁决。

## 标准交付物

- 全局协作方案。
- 模块分工与角色职责边界文档。
- 当前缺陷清单与全局优化方案。
- 迭代实施排期与模块交接说明。
- 跨角色冲突裁决记录。

## 启动必读

- `AGENTS.md`
- `docs\multi-agent\README.md`
- `docs\multi-agent\role-call-templates.md`
- `docs\multi-agent\deliverable-templates.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\roles\architect.md`
- `workflow\multi-agent\handoffs\latest.md`
- `workflow\multi-agent\decisions.md`
- `workflow\multi-agent\conflicts.md`
- `workflow\multi-agent\stage-review.md`
- `workflow\multi-agent\dispatch.md`
- `workflow\multi-agent\user-feedback.md`（消费用户反馈，识别需要进入 dispatch 的高优任务）

## 启动检查项

- 已确认当前对话是否明确指定首席系统架构师角色。
- 已读取共享事实、决策台账、冲突台账、阶段总控记录和最近交接记录。
- 已明确本轮是阶段总控、冲突裁决、角色边界梳理还是交接质量检查。
- 已确认不会替代专业角色完成其专业细节。

## 交付检查项

- 输出内容优先使用阶段总控与裁决模板。
- 已汇总各角色状态、关键风险、未决问题和下一棒角色。
- 涉及冲突裁决时，已说明裁决原因、影响范围和后续动作。
- 已明确是否进入下一阶段。

## 收尾更新项

- 更新本文件”当前记忆”中的全局协作风险、角色边界或裁决结果。
- 更新 `workflow\multi-agent\handoffs\latest.md`。
- 更新 `workflow\multi-agent\stage-review.md`。
- 更新 `workflow\multi-agent\dispatch.md`（新增、更新或关闭任务单）。
- 重要裁决更新 `workflow\multi-agent\decisions.md`。
- 冲突状态变化更新 `workflow\multi-agent\conflicts.md`。
- 成为共同事实的裁决更新 `workflow\multi-agent\shared-facts.md`。

## 记忆更新规则

每轮架构师工作结束后，更新：

- 角色职责边界变化。
- 已裁决的跨角色冲突。
- 全局协作风险。
- 阶段优先级和交接要求。
- 需要各角色继续推进的问题。

## 当前记忆

- 2026-06-20：建立本地多角色协作机制。当前机制以手动指定角色为最小可用模式。
- 2026-06-20：V0.2 升级为闭环机制，架构师负责阶段总控、冲突裁决、决策台账维护和跨角色交接质量检查。
- 2026-06-20：V0.3 新增运维/部署工程师为第六个开发团队固定角色。架构师负责裁决部署路线和跨角色边界；运维负责环境、密钥、容器、日志、备份、健康检查和回滚，不实现后端业务接口、不替代测试验收。
- 2026-06-20：V0.4 总控闭环确立。架构师不只下发角色提示词，还必须维护 `dispatch.md`，在专业角色交付和测试报告完成后，对照原任务、交付文档、测试证据和关键代码/配置 diff 复核，再决定通过或返工。
- 2026-06-20：部署路线裁决为 docker-compose/内网最小部署优先，Cloud Run 后置。原因是当前 storage、SQLite 多实例、长任务 provider、密钥注入和 API 依赖清单仍未完全收口。
- 2026-06-20：本地可演示阶段通过架构师验收。验收范围仅限本地 API + Web + fake provider + 真实 API 模式最小链路；不代表上线发布通过。下一轮建议优先修首页项目卡进度与 manifest 不同步，以及新建项目第 2 步真实教材上传语义分裂。
- 2026-06-20：T015-T018 本地演示打磨通过架构师复核。首页卡片已同步 manifest 当前阶段/进度/下一步动作；新建项目第 2 步已改为教材内容准备和预览语义。下一小阶段进入“公开课教案节点编辑/保存/确认演示”，暂不继续打磨项目创建体验。
- 2026-06-20：T019-T022 公开课教案节点端到端演示通过架构师复核。新鲜验证包含后端 pytest、前端 tsc/lint/build、隔离 API/Web 浏览器链路、后端 marker 持久化和首页同步；仅代表本地 fake provider 演示通过。下一阶段进入“视频导入选择节点端到端演示”，但新建向导教材预览固定样例、教案 schema 校验、正式编辑器、鉴权和部署仍是上线前风险。
- 2026-06-20：用户要求任务安排必须完善功能并推进视频生成。架构师已将后续拆为两段：T023-T026 先打通视频导入选择；T027-T031 继续打通视频剧本、分场剧本、视频资产、分镜和 fake 最终视频任务；T032 后续修新建项目教材预览固定样例口径。当前仍以本地 fake provider 可演示为目标，不把真实 provider 和上线发布混入本轮。
- 2026-06-20：T023-T031 本地 fake 视频生成端到端演示通过架构师复核。新鲜验证包含后端 pytest、前端 tsc/lint/build、隔离 API 完整链路、浏览器真实 API 首页/工作区/最终视频任务结果页和控制台日志；结论仅限 fake provider 本地演示。下一阶段优先修项目创建体验固定样例、补后端节点 schema 校验、做前端结构化编辑器雏形，再进入真实 provider smoke。
- 2026-06-20：教材解析到教案生成阶段复核未通过。后端 T038/T040 仍是主阻塞：fixture PDF 上传后 `textbook_parse/generate` 仍拒绝 `.pdf`，未产出知识点列表和知识点 Markdown；前端 T039 源码仍停留在“生成教材预览”本地预览逻辑，未见真实解析按钮、知识点下拉和 Markdown 预览 API 接入。下一步只安排后端返工解除契约阻塞，前端补交接或等待联调，测试暂缓。
- 2026-06-20：T038/T040 后端返工通过架构师红线复核。证据：`test_textbook_pdf_parsing.py` 为 `2 passed`，全量后端为 `35 passed, 2 xfailed`；架构师独立 API 跑通 fixture PDF 上传、`textbook_parse/generate`、知识点 `kp_001` Markdown 落盘、`lesson_plan/generate` 读取 Markdown。裁决：解除前端 T039 阻塞，但只限本地演示 fixture 能力，不代表生产级全书异步 MinerU 解析完成。
- 2026-06-21：T037-T042 教材解析到教案生成阶段通过架构师复核。T041 最终报告显示 API 主链路和 UI 子链路均通过：上传 fixture PDF、解析中状态、字段回填/手改、知识点下拉、Markdown 预览、确认教材解析、生成教案 Markdown、刷新持久化和控制台检查均有证据。新鲜验证：后端 `35 passed, 2 xfailed`，前端 tsc/lint/build 通过。下一阶段已落 `docs\fullchain-sprint.md`，但其中 DeepSeek 与项目默认 Minimax M3 存在 provider 口径冲突；未获用户明确变更前按 Minimax M3 执行。
- 2026-06-21：用户明确本轮全链路冲刺按 `docs\fullchain-sprint.md` 使用 DeepSeek 执行，覆盖此前“默认 Minimax M3”的历史口径。架构师已直接完成 T044-T046：DeepSeek provider、real/deepseek 模式、教案生成真实 LLM 入口、视频脚本链 5 节点 LLM prompt/归一化、PPT 导出接口和占位 MP4 嵌入。验证：`python -m pytest apps\api\tests -q` 为 `40 passed, 2 xfailed`，Web `tsc/lint/build` 通过。当前通过范围是 mock transport/本地占位视频，不等于真实 DeepSeek 线上调用或真实视频 provider 验收。
- 2026-06-21：DeepSeek key 已由用户提供并完成脱敏 live smoke；本地 `apps\api\.env` 已写入真实 provider 配置且确认被 git ignore。已新增 `docs\llm-provider-contract.md` 作为后续开发查找 LLM 接口、环境变量、错误码、节点契约和验证命令的唯一入口。真实 key 不得进入聊天后续引用、文档、日志或提交。
- 2026-06-21：后端2视频产物闭环通过架构师验收。fake/no-provider 模式下 `final_video/generate` 会确保 `outputs/final_video.mp4` 存在并返回 `video_path`，MP4 下载接口可用，`export/ppt` 复用同一视频文件；新鲜验证专项 `3 passed`、后端全量 `41 passed, 2 xfailed`。下一步进入测试工程师 T047 完整轻量 E2E；真实视频 provider 仍未接入。
- 2026-06-21：T057 课程锚点后端实现排查完成。结论：旧版 DeepSeek + placeholder E2E 能跑通，但课程锚点闭环未通过；后端缺 `lesson_plan` 9 套两层结构、新字段 schema、`selected_anchor` 正式字段、R047/R048/R049 和下游硬传递。已新增 `docs\qa-audits\2026-06-21-anchor-code-audit.md`，并下发 T058-T061。下一步先补课程锚点闭环，再追真实视频 provider 质量。
- 2026-06-21：T067 真实图片/视频全链路阶段复核不通过。T063 真实 E2E 到 `intro_video_asset/generate` 阻塞，返回 `400 / GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)`，未创建 image task，未产出真实图片、视频 task、`final_video.mp4` 或 PPT。T064 目标测试新鲜通过 `6 passed`，但只覆盖 task 状态/重试/下载安全，不能解除 T063 阻塞。已下发 T068-T071；复测通过前不得进入产品演示录屏。
- 2026-06-21：T068 后端阻塞修复通过架构师验收。`intro_video_asset/generate` 对真实 LLM 空响应、非 JSON、缺 `assets` 已收敛为 `INTRO_VIDEO_ASSET_JSON_EMPTY / JSON_INVALID / SCHEMA_INVALID` 502 诊断并写 failed 节点；合法资产 JSON 继续创建 `image_generation` task。新鲜验证：T068 目标测试 `4 passed`、`test_real_providers.py` `37 passed`、后端全量 `69 passed, 2 xfailed`。该结论只允许进入 T069 真实 E2E 复测，不代表 T063 全链路通过。
- 2026-06-21：Prompt/TTS/final_video 止血重构已完成架构师热修版。Prompt 运行时已从硬编码切到 DB→文件→硬编码 fallback，PromptLoader 支持变量和 include，PromptRegistry 支持 seed、active 唯一、canary 路由、TTL cache 和 audit log；但完整管理员后台、JWT、发布/回滚 UI、用户态 bundle 隔离仍未完成，不能宣布 Prompt 平台 GA。TTS 已接 Minimax，真实 smoke 产出 mp3 并经 ffprobe 证明音频流；默认 `.env` 保持 `TTS_PROVIDER_MODE=placeholder`，真实演示需显式切 `real`。后端全量 `106 passed, 2 xfailed`，前端 lint/build 通过。下一棒为测试工程师 T090，重点只测新增功能和历史阻塞点。
- 2026-06-21：真实端到端生成 Phase 5 最新复测仍未通过，但阻塞位置已明确前移到视频 provider 配额。已修复真实生图 SQLite 长事务锁、storyboard LLM context 携带 base64 大字段、T075 单 clip 降配额演示参数、弱 `model_prompt`/数字 `shot_id` 归一化。最新证据 `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-214857` 显示 PDF→教材解析→教案→导入选择→视频脚本→分场→真实生图→storyboard 均已通过；唯一 `video_clip_generation` 返回 `429 RESOURCE_EXHAUSTED / PUBLIC_ERROR_USER_QUOTA_REACHED`，因此没有 clip、`final_video.mp4`、ffprobe 或 PPT。下一步不应继续盲目改 PDF/PPT/prompt，先由运维/后端处理视频 provider 配额、账号池或可用模型。
- 2026-06-21：T101 后端 API 视频模型可配置化已完成。T075 smoke 和后端 `final_video/generate` / clip retry 现在统一支持 `VIDEO_MODEL` > `OMNI_DEFAULT_MODEL` > `NEWAPI_DEFAULT_MODEL` > `omni_flash-10s`，请求体显式 `model` 仍最高优先；目标回归 `24 passed`。这只解除代码和配置口径缺口，不代表真实 E2E 通过；下一步仍是 provider 恢复后执行 T095。
