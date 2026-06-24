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
- 2026-06-23：T107 StateEngine Phase 1 专项回归结论为【通过】。隔离 API `8107` + Web `3107` + storage `storage-t107-state-engine-phase1` + fake/placeholder provider 下，API 证据确认：创建项目后 `project_config=approved`；上游未 approved 时下游 generate 返回 `409 / UPSTREAM_NOT_APPROVED` 并写 `state_transition_log.trigger=dependency_gate_blocked`，R010 不再写 `rule_result_log`；上游 approved 后下游 generate 可继续；edit 后 `needs_review` 且记录 `user_edit/user_save_edit`；approve 后 `approved` 且记录 `user_approve`；skip 分支允许非视频下游继续；`RULE_WARNING` 与 `RULE_VIOLATION_R004` 不与 StateEngine 阻断混淆。浏览器真实 API 模式可展示阻断文案、`review_reason` 和 `latest_transition`，控制台 error/warn 为空。后端全量 `201 passed, 2 xfailed`；前端契约、tsc、lint、build 全部通过。报告：`docs\qa-audits\2026-06-23-t107-state-engine-phase1-regression.md`；证据目录：`docs\qa-audits\t107-state-engine-phase1-evidence\20260623-113852`。
- 2026-06-23：T126 教材库 / MinerU / 教案库边界收尾浏览器 E2E 结论为【通过】。隔离 API `8126` + Web `3126` + storage `storage-t126-browser-e2e` 下，浏览器真实 API 模式验证教材库选择、知识点 `kp_001`、教材证据包、PDF 页段弹窗、MinerU Markdown 弹窗、教案抽屉和选为参考；项目 `proj_4bd7d8ae2f59` 持久化 `reference_lesson_plan_id=lp_b16b139739bb`，教案生成仍追溯当前教材/版本/知识点/PDF 页段/MinerU Markdown。Web 代理上传 fixture PDF 入全局教材库返回 200，job `tj_e215896d59ca` 进入 `indexed`，provider 为 `mineru_fixture`；浏览器 console error/warn 为空。报告：`docs\qa-audits\2026-06-23-t126-textbook-library-browser-e2e.md`；证据目录：`docs\qa-audits\t126-textbook-library-browser-e2e`。剩余边界：真实 MinerU CLI/provider、任意教材泛化、生产级后台权限和浏览器文件选择器专项仍未验收。
- 2026-06-24：T132 T127-T132 用户态回归结论为【不通过】。隔离 API `8132` + Web `3132` + storage `storage-t132-user-flow-regression` 下，API 与浏览器证据确认教材库下拉、7 个目录章节、`kp_001` 页码映射、页段 PDF 10 页小于源 PDF 118 页、MinerU Markdown、教案来源追溯、工作区 7 步、未解锁提示和教案 Markdown 预览均可运行；浏览器 console error/warn 为空。后端全量 `221 passed, 2 xfailed`，前端 `new-project/workspace/api-mappers` 契约、tsc、lint、build 均通过。阻塞红线：工作区普通主界面直接显示 `JSON` 和结构化字段；教材/Markdown 弹窗暴露 `storage-t132...` 路径；一年级教材目标受众默认成“三年级学生”。报告：`docs\qa-audits\2026-06-23-t132-user-flow-regression.md`；证据目录：`docs\qa-audits\t132-user-flow-regression-evidence\20260624-002553`。后续前端返工后需补跑普通主界面禁词扫描和弹窗路径扫描。
- 2026-06-24：T138 用户态红线专项复测结论为【不通过】。隔离 API `8138` + Web `3138` + storage `storage-t138-user-flow-redline-regression` 下，三段式教材处理已通过 API 与浏览器验证：导入教材、切分教材、解析教材内容可执行，全量 9 个知识点和部分 `kp_001/kp_006` 均可切分/解析；目标受众默认已修为“一年级学生”；核心知识点与教材内容弹窗未再暴露 `storage` 路径，console error/warn 为空。阻塞红线仍存在：浏览器工作区普通主界面在“开发诊断”折叠区之前显示 `JSON` 和结构化字段，`browser-redline-scan-main.json` 命中 `main_hits_before_developer_diagnostics=["JSON"]`。报告：`docs\qa-audits\2026-06-24-t138-user-flow-redline-regression.md`；证据目录：`docs\qa-audits\t138-user-flow-redline-regression-evidence\20260624-085413`。后续前端需移除普通区 JSON fallback，并补浏览器红线门禁。
- 2026-06-24：V0.6 测试验收基线。涉及普通教师主界面的测试必须有真实浏览器或 DOM 级证据，且红线扫描必须分区：开发诊断折叠区之前的普通主界面不得命中 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage`；展开后的开发诊断可以包含工程词但必须默认折叠。测试报告必须区分“后端/API/构建通过”和“浏览器用户态通过”，不能用 tsc/lint/build 或契约测试替代浏览器红线结论。
- 2026-06-24：T140 T139 后用户态红线专项复测结论为【通过】。隔离 API `8140` + Web `3140` + storage `storage-t140-user-flow-redline-rerun` 下，工作区教材内容当前任务卡展示教师可读摘要、课时页码、解析状态、知识点和 Markdown 预览；“开发诊断”默认折叠，`browser-redline-scan-main.json` 中 `main_hits_before_developer_diagnostics=[]`、`visible_hits_in_main=[]`；“查看教材页段”按钮可用，弹窗和 iframe 地址不暴露本地 `storage` 路径，iframe 走 `/api/backend/projects/proj_305436b48356/files/knowledge-points/kp_001/source.pdf`，GET 返回 `application/pdf`；console error/warn 为空。报告：`docs\qa-audits\2026-06-24-t140-user-flow-redline-rerun.md`；证据目录：`docs\qa-audits\t140-user-flow-redline-rerun-evidence\20260624-100115`。该结论只表示测试验收通过，不代表阶段封板，后续交 T141 架构复核。
- 2026-06-24：T009 v1 E2E 回归验收计划已完成，计划文档位于 `docs\qa-audits\v1-e2e-regression-plan.md`。该文档明确这是验收计划而非通过报告，基于 T005-T008 与 T140/T141 输入，覆盖产品主流程、API 合同、真实 API 模式、新人冷启动、权限/密钥、防误提交、浏览器红线、storage/备份恢复、provider smoke、PPT/视频交付、跨浏览器和回归停止条件。计划结论：fake/placeholder、文档冷启动、权限默认策略、防误提交和 T140 同类红线基线可立即执行；真实图片/视频/TTS、PPT 主链路、容器冷启动、多浏览器和生产权限需等待开发交付、环境准备或外部 provider 恢复。T140/T141 只封板 T138/T139 用户态红线专项，不代表真实 provider、生产权限、多浏览器、真实视频或 PPT 主链路通过。
- 2026-06-24：T145 v1 最小封板门禁回归结论为【测试验收通过】。隔离 API `8145` + Web `3145` + storage `storage-t145-v1-minimum-gate-regression` + fake/placeholder provider 下，后端目标测试 `14 passed`、前端 workspace 契约 exit 0；主控补充验证后端 workspace/PPT/video 组合 `26 passed`、前端 `tsc --noEmit` exit 0。API 主链路初次因 `visual_contract`/`character_dict` 未确认触发 `UPSTREAM_NOT_APPROVED`，补齐上游后 `visual_contract`、`character_dict`、`ppt_page_script`、`ppt_visual_asset`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均可生成并确认，`pptx_artifact` 与 `final_video` 生成到 `needs_review`。浏览器目标项目 `proj_d62361b7e98c` 显示 `PPT 草稿 / 82% / 继续处理「PPT 装配」`，7 步导航、PPT 子门禁和 PPTX 下载按钮存在，下载链接走 `/api/backend/projects/.../exports/...pptx`，`mainHitsBeforeDeveloperDiagnostics=[]`、`pathLeakHitsBeforeDeveloperDiagnostics=[]`、`visibleHitsInBody=[]`，console error/warn 为空。报告：`docs\qa-audits\2026-06-24-t145-v1-minimum-gate-regression.md`；证据目录：`docs\qa-audits\t145-v1-minimum-gate-regression-evidence\20260624-115521`。该结论不代表阶段封板，需主 Codex / 系统架构师复核；真实 provider、真实视频质量、多浏览器、生产 RBAC/JWT/session、容器冷启动和重复同名项目污染仍是剩余风险。
- 2026-06-24：T146-T148 功能接口全量测试已由架构师下发，计划文档为 `docs\qa-audits\2026-06-24-t146-t148-functional-interface-test-dispatch.md`。测试执行必须拆成三份报告：T146 后端 FastAPI 全接口合同、T147 Next 代理与前端接口适配、T148 浏览器真实 API 串联。三者都默认 fake/placeholder，不读取真实密钥；任一 P0/P1 失败时停止接口全量通过判断，并转架构师新增窄范围返工任务。
- 2026-06-24：T146 后端 FastAPI 功能接口全量合同回归结论为【通过，限定于 fake/placeholder + 本地 FastAPI 合同】。隔离环境 `STORAGE_ROOT=storage-t146-functional-api`、`PROVIDER_MODE=fake`、`VIDEO_PROVIDER_MODE/IMAGE_PROVIDER_MODE/TTS_PROVIDER_MODE=placeholder` 下，目标批次 `72 passed, 2 xfailed` exit 0，后端全量 `229 passed, 2 xfailed` exit 0。报告：`docs\qa-audits\2026-06-24-t146-functional-api-contract.md`；证据目录：`docs\qa-audits\t146-functional-api-evidence\20260624-153104`。两个 xfail 为既有风险：provider schema 缺必填字段严格拒绝仍待服务层收口、未配置 `BACKEND_API_TOKEN` 时本地默认开放仍是架构待定；本结论不代表真实 provider、生产权限、Next 代理或浏览器用户态通过。
- 2026-06-24：T147 Next.js API 代理与前端接口适配回归结论为【通过，但 live proxy 未完成】。`apps\web` 下 5 个前端契约测试、`bunx tsc --noEmit --pretty false` 和 `bun run scan:client-secrets` 均 exit 0；报告位于 `docs\qa-audits\2026-06-24-t147-next-proxy-interface-regression.md`，证据目录为 `docs\qa-audits\t147-next-proxy-evidence\20260624-153142`。已确认前端默认走 `/api/backend`，代理服务端注入 `BACKEND_API_TOKEN`、删除 `Expect` header、admin path 用本地 admin cookie 隐藏为 404，client-visible secret 扫描通过。live proxy 因已有 Next dev 锁占用未完成，文件流和真实 HTTP 方法转发仍建议释放锁后补跑；本轮未发现 P0/P1，也不替代 T148 浏览器验收。
- 2026-06-24：T148 浏览器真实 API 功能接口串联回归结论为【不通过】。隔离 API `8148`、Web `3148`、storage `storage-t148-browser-functional-interfaces` 下，项目 `proj_d53d88dd7ff6` API 串联可推进到 `final_video=approved`，浏览器可生成 `final_delivery=needs_review`；API 直连和 Next 代理下载 PPTX/MP4/PDF/Markdown 均返回 200。但最终交付普通区暴露 `exports/final_delivery/...`、`delivery_manifest.json`、`gate_result.json`、JSON 片段和 `manifest` 红线；点击 `PPT 草稿可回看` / `视频生成可回看` 后主任务区仍显示最终交付；浏览器控制台有 4 条 React duplicate key error `摘要 17`。报告：`docs\qa-audits\2026-06-24-t148-browser-functional-interface-regression.md`；证据目录：`docs\qa-audits\t148-browser-functional-interface-evidence\20260624-153915`。后续必须先做 T149 前端返工，再由 T150 复测红线、回看、console 和下载代理。
- 2026-06-24：T150 T149 后窄范围复测结论为【通过】。隔离 API `8150` + Web `3150` + storage `storage-t150-t149-rerun` + fake/placeholder provider 下，新项目 `proj_3e68b8633bb9` 推进到 `final_video=approved`，浏览器登录 `qa-t150` 后生成 `final_delivery=needs_review`；最终交付普通区只显示教师可读摘要，`browser-workspace-target-final-dom-redline-scan.json` 中 `redlineHits=[]`、`pathLeakHits=[]`、`bodyVisibleHits=[]`，普通区无 evidence/JSON 结构化预览入口；点击 `PPT 草稿 可回看` 和 `视频生成 可回看` 均切到对应内容，`hasFinalDeliveryAsTask=false`；console error/warn 为空，未再出现 `摘要 17`；T148 同口径 Next 代理下载 PPTX/MP4/PDF/Markdown 均 200。报告：`docs\qa-audits\2026-06-24-t150-t149-rerun.md`；证据目录：`docs\qa-audits\t150-t149-rerun-evidence\20260624-170324`。关注项：`final_delivery` 嵌套 PPTX 路径 `exports/final_delivery/...pptx` 文件存在但下载路由返回 404，不阻塞 T149 失败面关闭，建议后续单独收口最终交付下载入口。
- 2026-06-24：T157 教材库管理员拆分与直接教案真实 API 集成验收结论为【PASS，带关注项】。在 `NEXT_PUBLIC_DEMO_MODE=false`、`BACKEND_API_BASE_URL=http://127.0.0.1:8000`、Web `3000`、API `8000` 组合下，配置核验与 `/health` 200 通过；后端目标批次 `12 passed`、教材 PDF 解析 `19 passed`；前端 `new-project` 契约、`admin-textbook-library` 契约、`tsc`、`lint` 均 exit 0。浏览器真实 API 模式验证教师新建项目页只保留“使用教材库”和“直接使用教案”，路径 A 可选择教材库和知识点，路径 B 可从教案库选择或上传教案文件；教师普通区红线词和工程词扫描为空。真实 API 创建 direct lesson 项目 `proj_0b60dd65a2a9` 后 `/workspace.current_step_id=lesson_plan`，浏览器工作区当前阶段为“教案生成”，不再卡“教材内容”。管理员侧左侧导航可见“管理教材库”，页面可见上传教材、切分教材、解析教材内容、确认资产、教案库/上传教案；教师侧左侧不显示该入口。报告：`docs\qa-audits\2026-06-24-t157-textbook-admin-and-direct-lesson-real-api.md`；证据目录：`docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-195033`。关注项：截图采集超时、首页项目列表刷新存在短暂空列表加载态；本轮不代表生产权限、多浏览器、容器冷启动或真实 provider 质量通过。
- 2026-06-24：T157 已补主 Codex 新鲜复核证据。补充证据目录 `docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-201700`：教师新建项目页 DOM 扫描 `forbiddenHits=[]` 且命中“使用教材库/直接使用教案/只选择已管理教材”；页面自带角色切换到管理员后，管理员页 DOM 扫描命中“上传教材/切分教材/解析教材内容/确认资产/教案库/上传教案”，`missing=[]`；console `error/warn=[]`。新鲜命令复核同样通过：后端 `12 passed`、教材解析 `19 passed`，前端目标契约、tsc、lint 均 exit 0。QA 后续不得把这次本地真实 API 模式验收写成生产上线验收。
