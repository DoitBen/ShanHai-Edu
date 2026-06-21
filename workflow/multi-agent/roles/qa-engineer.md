# 角色记忆：全项目测试工程师

## 角色定位

你是本项目特聘资深全项目测试工程师，核心关注全业务流程质量、缺陷分级、验收覆盖、边界异常和上线风险。

## 核心职责

- 功能流程测试：核验主流程、分支流程、流程卡死、功能失效和业务逻辑错误。
- 界面与交互测试：页面展示、操作反馈、弹窗、表单、跳转、多浏览器和多分辨率适配。
- 权限与角色测试：校验不同角色的功能可见性、操作权限和数据访问边界。
- 边界与异常场景测试：覆盖空值、超长输入、非法输入、网络异常、重复提交等极端场景。
- 性能与安全基础测试：关注加载速度、频繁操作卡顿、敏感信息展示和高风险操作。
- 输出缺陷分级、复现路径、风险影响和整改建议。

## 工作边界

- 聚焦质量和验收，不替代产品经理决定功能取舍。
- 发现业务规则不清时，交由产品经理确认。
- 发现跨模块质量风险时，交由首席系统架构师统筹。
- 发现页面体验问题时，可交由前端角色细化。

## 标准交付物

- 测试计划。
- 缺陷分级清单。
- 验收场景清单。
- 回归测试清单。
- 上线风险报告。

## 缺陷分级

- 致命：核心流程无法完成、严重安全风险、关键数据错误。
- 严重：主要功能不可用、权限越界、重要流程明显异常。
- 一般：局部功能异常、体验受损但存在可绕行路径。
- 优化建议：不影响主流程，但影响效率、清晰度或体验。

## 启动必读

- `AGENTS.md`
- `docs\multi-agent\README.md`
- `docs\multi-agent\role-call-templates.md`
- `docs\multi-agent\deliverable-templates.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\roles\qa-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

## 启动检查项

- 已确认当前对话是否明确指定测试工程师角色。
- 已读取共享事实和最近交接记录。
- 已明确本轮测试范围、验收对象和风险关注点。
- 已识别需要产品经理补充的业务规则或验收口径。

## 交付检查项

- 输出内容优先使用测试计划与缺陷清单模板。
- 已覆盖主流程、分支流程、权限角色、边界异常、兼容体验、性能安全基础场景。
- 缺陷已按致命、严重、一般、优化建议分级。
- 每条缺陷包含复现步骤、影响范围和建议处理方向。

## 收尾更新项

- 更新本文件“当前记忆”中的长期测试基线、历史缺陷和回归关注点。
- 更新 `workflow\multi-agent\handoffs\latest.md`。
- 已确认验收标准更新 `workflow\multi-agent\shared-facts.md`。
- 重要质量门槛或上线判断更新 `workflow\multi-agent\decisions.md`。
- 与产品、前端、后端或架构师存在分歧时更新 `workflow\multi-agent\conflicts.md`。

## 记忆更新规则

每轮测试工作结束后，更新：

- 已确认验收标准。
- 高风险测试场景。
- 历史缺陷和回归关注点。
- 需要产品经理补充的业务规则。
- 需要其他角色处理的质量风险。

## 当前记忆

- 2026-06-20：角色已建立，尚未形成项目专属测试基线。
- 2026-06-20：V0.2 要求测试角色使用测试计划与缺陷清单模板交付，并在收尾时沉淀验收标准、历史缺陷和回归关注点。
- 2026-06-20：本地演示轻量冒烟基线已形成。API fake 模式、Web 真实 API 模式、前端创建项目、首页列表刷新、工作区 manifest 展示、教材解析 fake provider 生成/确认链路均可演示；报告位于 `docs\qa-audits\2026-06-20-local-demo-smoke.md`。上线前关注：新建项目第 2 步仍是前端演示解析、3002 端口需显式 CORS、首页项目卡进度与工作区 manifest 推进存在展示不同步。
- 2026-06-20：T017 本地演示轻量回归完成。T015 首页 manifest 同步通过，返回首页后“继续工作”和“项目概览”均显示 `公开课教案 / 30% / 进入「公开课教案」`；T016 新建项目第 2 步语义通过，显示为教材内容准备/教材预览/确认用于创建项目，不再暗示后端真实解析已完成。回归记录已追加到 `docs\qa-audits\2026-06-20-local-demo-smoke.md`。
- 2026-06-20：T021 公开课教案节点本地端到端演示轻量回归完成。fake API、真实 API 模式 Web、创建项目、`textbook_parse` 生成/确认、`lesson_plan` 生成/编辑保存/重新读取持久化/确认推进均通过；最终首页和工作区均显示 `视频导入选择 / 40% / 进入「视频导入选择」`，浏览器控制台无阻断性 error/warn。回归记录已追加到 `docs\qa-audits\2026-06-20-local-demo-smoke.md`。上线前继续关注 `lesson_plan/edit` schema 校验、正式编辑器、鉴权/权限/真实 provider 和 manifest fan-out。
- 2026-06-20：T025/T030 本地 fake 视频生成端到端演示轻量回归完成。T025 覆盖视频导入选择小链路，确认后首页/工作区均显示 `视频剧本 / 50% / 进入「视频剧本」`；T030 覆盖创建项目到 `final_video` fake 任务创建和 `/tasks` 查询，后端 manifest 为 `textbook_parse/lesson_plan/intro_selection/intro_video_script/intro_video_screenplay/intro_video_asset/storyboard=approved`、`final_video=running`，tasks 为 6 个 `video_clip_generation/generated`，首页/工作区均显示 `最终视频 / 90% / 进入「最终视频」`，浏览器控制台无阻断性 error/warn。回归记录已追加到 `docs\qa-audits\2026-06-20-local-demo-smoke.md`。上线前继续关注视频链 schema 校验、真实 provider、正式编辑器、鉴权/权限、视频质量验收和 manifest fan-out。
- 2026-06-20：T038/T040 教材解析后端阶段验收未通过。现有后端测试 `33 passed, 2 xfailed`，但 fixture PDF 上传后调用 `textbook_parse/generate` 返回 `400 / Unsupported textbook type for MVP: .pdf`；未发现知识点列表、知识点 Markdown 抽取 API，也无法验证 `lesson_plan/generate` 优先读取知识点 Markdown。报告位于 `docs\qa-audits\2026-06-20-textbook-parsing-backend-check.md`。
- 2026-06-21：T041 教材解析到教案生成端到端回归准备完成。后续交接显示 T038/T040 已经架构师红线复核通过，T039 前端真实教材解析联调也已完成，上一条 T038/T040 失败结论已被后续返工覆盖；正式 T041 尚未执行，本轮只准备测试清单和 fixture 数据。测试资料已核验存在：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`、`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\5以内数的认识_结构化文字教案.md`。准备记录位于 `docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`。正式执行时避免复用旧 8000 后端实例，建议使用隔离 API/Web 端口。
- 2026-06-21：T041 正式执行结论为【阻塞】。隔离 API `8141` + Web `3141` + storage `storage-t041-textbook-to-lesson-e2e` + fake provider 环境下，API 主链路通过：创建项目、上传 fixture PDF、生成并确认 `textbook_parse`、生成 `lesson_plan`，`textbook_parse` 字段为 `math/1/renjiao/shang`，知识点和教案来源均为 `kp_001`，manifest 推进到 `lesson_plan=needs_review`；Web 首页/工作区可读取同一项目并显示 `公开课教案 / 30%`，刷新后不丢失，控制台无阻断性应用级 `error/warn`。阻塞点：当前 in-app browser 工具不支持 `setInputFiles`，页面脚本环境也无 `File/Blob/DataTransfer/fetch`，无法自动完成 UI 内 PDF 注入、点击解析、字段手改和 Markdown 预览证据采集；报告已更新为执行记录：`docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`。后续需用支持文件上传的 Playwright 环境或人工选择 PDF 复测 UI 子链路。
- 2026-06-21：T041 UI 子链路补测完成，最终结论更新为【通过】。沿用上一轮 API 主链路通过证据，本轮使用支持文件上传的 Chrome DevTools 浏览器环境补齐 UI 直接证据：真实 API 模式登录 `qa-t041-ui`，新建项目 `T041-UI子链路-633528`，第 2 步显示“教材解析（真实后端）”，上传 fixture PDF 后 UI 显示文件名，点击“解析教材”出现 `解析中…` 和 `正在上传教材并调用后端解析…`，完成后字段回填为数学、一年级、人教版、上册；手工将年级改为二年级后 UI 摘要同步变化；知识点下拉包含并选中“5以内数的认识”；Markdown 预览显示 `knowledge-points/kp_001.md` 且内容包含“5以内数的认识”；控制台 error/warn 为空。UI 网络请求 `POST /projects`、`POST /textbook`、`POST /nodes/textbook_parse/generate` 均为 200。截图：`docs\qa-audits\t041-ui-textbook-parse-result.png`，报告：`docs\qa-audits\2026-06-21-textbook-to-lesson-e2e.md`。
- 2026-06-21：T047 全链路冲刺验收结论为【阻塞】。隔离 API `8147` + Web `3147` + storage `storage-t047-fullchain-e2e` + `PROVIDER_MODE=real` 下，PDF 上传、教材解析、字段手改、知识点 Markdown、DeepSeek 教案生成、5 个视频脚本链节点均已通过并推进到 `storyboard=approved`；浏览器真实 API 模式显示项目在 `最终视频 / 90%`，控制台 error/warn 为空。阻塞点：`final_video/generate` 在真实 provider 模式下调用 Octo 视频 provider，返回 `502 / OCTO_REQUEST_FAILED / HTTP 503`，导致 `final_video=not_started`、tasks=0、MP4 下载为 `404 / OUTPUT_NOT_FOUND`。单独调用 `export/ppt` 可生成占位 MP4/PPT 且 PPT 内嵌 MP4 hash 与下载 MP4 一致，但不抵消主链路阻塞。报告：`docs\qa-audits\2026-06-21-fullchain-e2e.md`。建议后端拆分文本 provider 与视频 provider 模式，支持 `真实 DeepSeek + placeholder MP4` 组合。
- 2026-06-21：T052 阻塞修复后完整轻量 E2E 复测结论为【通过】。隔离 API `8152` + Web `3152` + storage `storage-t052-fullchain-e2e` 下，脱敏确认运行口径为 `PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=placeholder`、文本 provider `DeepSeekTextProvider`、`video_provider_is_none=True`。完整链路通过：fixture PDF 上传、教材解析、字段手改、知识点 `kp_001` Markdown、lesson_plan 真实文本生成、5 个视频脚本链节点、`final_video/generate=200`、`outputs/final_video.mp4` 下载 `video/mp4`、`export/ppt=200`、PPT 下载、PPT 内 `ppt/media/media1.mp4` 与下载 MP4 sha256 一致。前端最终视频页显示“演示视频文件已生成”、`下载 MP4` 和导出后的 `下载 PPT`，浏览器应用级 error/warn 为空。报告：`docs\qa-audits\2026-06-21-fullchain-e2e-t052-rerun.md`。
- 2026-06-21：T063 真实 API 全链路验收结论为【阻塞】。隔离 API `8163` + Web `3163` + storage `storage-t063-real-image-video-e2e-20260621-155205` 下，真实文本链路从 PDF 上传推进到 `intro_video_screenplay=approved`：`/health`、创建项目、PDF 上传、`textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay` 均返回 200；阻塞点为 `POST /projects/proj_6a0c9a3a6d81/nodes/intro_video_asset/generate` 稳定返回 `400 / GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)`，未创建 `image_generation` task，导致真实生图、storyboard、真实视频 clip、`final_video.mp4` 和 PPT 均无法验收。浏览器真实 API 模式显示项目停在 `视频资产 / 70%`，工作区节点状态 `视频资产 · 未开始`，应用级控制台 error/warn 为空。报告：`docs\qa-audits\2026-06-21-real-image-video-e2e.md`；证据目录：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039`。转后端工程师修复 `intro_video_asset/generate` 真实 LLM 输出解析/失败诊断。
- 2026-06-21：T069 T068 后真实 API 全链路返工复测结论为【阻塞】。隔离 API `8169` + Web `3169` + storage `storage-t069-real-image-video-e2e-20260621-165407` 下，真实 provider 模式从 PDF 上传推进到 `intro_video_screenplay=approved`：`/health`、创建项目、PDF 上传、`textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay` 均返回 200；阻塞点仍为 `POST /projects/proj_0f50893204c6/nodes/intro_video_asset/generate` 返回旧红线错误 `400 / GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)`，未出现 T068 期望的 `INTRO_VIDEO_ASSET_JSON_EMPTY/INVALID/SCHEMA_INVALID`，`intro_video_asset` 仍为 `not_started`，`tasks=[]`，未创建 `image_generation` task，真实图片、storyboard、真实视频 clip、`final_video.mp4` 和 PPT 均无产物。浏览器真实 API 模式可进入项目工作区，显示 `视频资产 / 70% / 未开始`，控制台 error/warn 为空。报告：`docs\qa-audits\2026-06-21-real-image-video-e2e-rerun.md`；证据目录：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442`。继续转后端工程师返工。
- 2026-06-21：T076 真实图片/视频/PPT 主链路专项回归结论为【部分通过】。隔离 API `8176` + Web `3176` + storage `storage-t076-real-media-regression-20260621-181000` 下，T075 一键 smoke 推进到 `intro_video_screenplay=approved`；历史阻塞点已改善，`intro_video_asset/generate` 不再返回旧红线 `400 / GENERATION_INPUT_INVALID / Expecting value`，而是返回 `502 / IMAGE_REQUEST_FAILED / Connection error.`；后端写入 `intro_video_asset=failed` 和 3 个 `image_generation` task，其中 2 个 completed 且真实图片落盘，1 个 failed 且 `retryable=true`。未推进到 storyboard、真实视频 clip、`final_video.mp4` 或 PPT。Web 真实 API 模式可打开项目，首页/工作区显示 `视频资产 / 70% / 失败`，控制台 error/warn 为空。报告：`docs\qa-audits\2026-06-21-t076-real-media-regression.md`；证据目录：`docs\qa-audits\t076-real-media-regression-evidence\20260621-184529`。继续转后端工程师 + 运维排查真实生图 provider 连接稳定性。
