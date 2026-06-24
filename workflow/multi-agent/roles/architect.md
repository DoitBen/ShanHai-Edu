# 角色记忆：首席系统架构师

## 角色定位

你是本项目首席系统架构师。V0.7 起，系统架构师能力默认服务于主 Codex 单入口总控：负责全局统筹、跨角色协调、职责边界裁决、阶段规划、子智能体派发策略和标准化交接。

## 核心职责

- 全局统筹：统一项目目标、阶段范围、角色分工和交付节奏。
- **开发调度**：维护 `workflow\multi-agent\dispatch.md` 任务板，将具体任务下发给对应角色，跟踪任务状态，处理阻塞。
- **子智能体调度**：在用户只对接主 Codex 的前提下，将任务拆给内置子智能体扮演前端、后端、测试或系统架构师，并明确冻结区、文件边界和验收标准。
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
- 不要求用户人工承担调度器角色；默认由主 Codex 派发、回收和复核子智能体结果。

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
- 已确认当前任务是否应由主 Codex 直接处理、内置子智能体执行、手动角色对话讨论或外部长期线程承接。
- 已确认协议升级不会自动改变 `dispatch.md` 里既有任务状态。

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

- 2026-06-24：ShanHaiEdu 已完成腾讯云 Lighthouse 真实环境上线收口，公网地址 `http://124.221.149.145:3020/`。线上拓扑为 nginx `3020` -> Web `127.0.0.1:3021`，API `127.0.0.1:8020->8000`；真实 API 验收包含 `/api/backend/health` 返回 `ok=true/status=ok/workflow_version=1.0.0`，`/api/backend/textbook-library` 返回真实教材库“人教版小学数学一年级上册”且 `knowledge_point_count=9`。公网浏览器登录页已关闭旧 demo 口径：未命中“演示项目/工作流节点/视频方案/演示账号/demo mock/第一阶段演示版”，console error/warn 为空。后续用户说“上线/部署/发布”时，必须走真实服务器/真实运行环境和公网验收，不能把本地 demo/mock 或本地真实 API 模式当上线。
- 2026-06-24：T142 v1 统一验收映射裁决完成。后续采用“三层映射”：7 步用户态作为教师主导航，PRD 9 步作为验收语义层，workflow/manifest 节点作为诊断与执行层；PPT 分支在“PPT 草稿”内保留总装方案、逐页脚本、视觉资产、PPTX 四个子门禁，视频分支在“导入视频方案/视频生成”内保留课程锚点、文稿、剧本、资产/首帧、分镜、clip/TTS/合成门禁。下一阶段最小封板先跑 fake/placeholder + 浏览器用户态 + 红线 + 下载代理；真实文本、图片、视频、TTS provider 进入分离 smoke 泳道，真实视频 provider 未恢复时只记录阻塞，不阻塞本地主流程。
- 2026-06-24：T133-T138 教材资产与用户态补强已代码级完成。教材处理正式拆为导入、切分、解析三段；上传入库不自动生成页段 PDF 或 MinerU Markdown；前端支持全量/部分知识点处理；工作区普通主界面关闭高级 JSON/provider 细节，`selected_anchor` 用户态改为“课堂衔接点”，教材弹窗不再展示本地 storage 路径。项目级 `skills/jiaocaiTojiaoan` 已沉淀为 MinerU Markdown 经验包，但不得替代 ShanHaiEdu 教材库、StateEngine、RuleExecutor 或现有工作流。下一步必须由测试工程师复跑 T132 红线复测。
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
- 2026-06-22：`docs\architecture-optimization-v2.md` 第 0 周 PPT 主链路已通过架构验收。真实 API runtime manifest 现在包含 `visual_contract`、`character_dict` 和 PPT 线 4 节点，前端工作区显示 `16 个后端 manifest 节点`，`pptx_artifact/generate` 会写入可下载 PPTX artifact 节点版本；`final_delivery` 仍按文档裁决暂不接入。下一阶段必须按固定顺序进入 StateEngine，且每阶段都先读取 Issues、修缺陷、再开发测试提交推送。
- 2026-06-23：Workflow Control Plane Phase 1 已落地。规则治理运行时真源迁到 `storage\control_plane.db`，`workflow\rules\*.yaml` 退为 Git 基线和灾备源；新项目绑定 active rule set，旧项目默认不迁移；RuleExecutor V2 改为解释 `check_json` 通用算子，不再维护规则 ID 硬编码分支；管理员规则 API/UI 可查看 DAG、编辑规则草稿、发布、回滚和查看审计。当前通过范围是规则控制面 Phase 1，不代表完整 DAG 可编辑或生产级管理员 JWT/RBAC 完成。
- 2026-06-23：T108 StateEngine Phase 1 架构复核有条件通过。StateEngine 已成为主流程 `generate/edit/approve/retry/config skip/restore/cascade` 和 R010 依赖门禁的统一入口，R010 不再写 `rule_result_log`，改由 `state_transition_log.trigger=dependency_gate_blocked` 诊断承接；新鲜验证后端目标 `33 passed`、后端全量 `201 passed, 2 xfailed`，前端 mapper contract/tsc/lint/build 通过。裁决口径必须保守：`RuleExecutor` hard_block、provider failed/blocked、`VideoOrchestrator.final_video` 仍存在状态直写，下一阶段先做 T109 StateEngine Phase 2，再做 T110 RuleExecutor Phase 2 / Flywheel，不返工 T104-T107。
- 2026-06-23：教材资产库驱动教案生成 MVP 已进入架构师复核。当前固定支持人教版一年级上册 fixture：教材库选择/上传 fixture、课时级知识点索引、PDF 页段裁剪、MinerU Markdown 资产包、项目教材绑定和 `lesson_plan` 来源追溯已落地；前端主页面只展示证据摘要，PDF/Markdown/教案正文按需弹窗或抽屉展示。裁决边界必须保守：这不是完整教材库平台，上传新教材解析入全局 DB、真实 MinerU 异步精抽、正式教案库后台和 `reference_lesson_plan_id` 后端持久化仍是后续任务。
- 2026-06-23：教材库 / MinerU / 教案库边界收尾 T119-T125 已完成代码级和契约级复核。`storage\textbook_library.db` 与 `storage\lesson_plan_library.db` 已成为教材库和教案库全局运行时存储；上传 fixture PDF 可入库并复用，知识点资产抽取/确认有 job、checksum 和状态，`reference_lesson_plan_id` 已持久化并进入教案生成输出但不替代当前教材 MinerU Markdown。裁决口径：本轮通过“平台化边界收口”，但真实 MinerU provider、浏览器完整 E2E、生产级后台权限、多教材自动泛化和旧项目迁移仍不得宣称完成。
- 2026-06-23：T126 浏览器 E2E 已补证据并通过。真实 API 浏览器验证教材库选择、证据包摘要、PDF 页段弹窗、MinerU Markdown 弹窗、教案抽屉和 `reference_lesson_plan_id` 已选择；Web 代理 multipart 上传 fixture PDF 入全局教材库返回 200，job 进入 `indexed`，项目保留教材/版本/知识点/reference 绑定，console error/warn 为空。顺手修复 Web 代理转发 `Expect` header 导致上传 500 的兼容 bug。保守边界不变：当前仍是 fixture provider，不是真实 MinerU CLI/provider，也不是任意教材泛化或生产级后台。
- 2026-06-23：多角色派发升级为 V0.5 文档绑定派发。用户指出仅给角色提示词缺少共同参考文档和验收依据，正式任务必须先沉淀共同需求、契约和测试文档，再写入 `dispatch.md` 并输出角色提示词。本轮已新增 `docs\product-workspace-user-flow-requirements.md`、`docs\textbook-directory-and-evidence-contract.md`、`docs\qa-audits\t127-t132-user-flow-regression-plan.md`，并正式下发 T127-T132。
- 2026-06-23：V0.5 派发收尾要求已明确：角色提示词必须包含任务编号、统一背景、共同参考文档、角色参考文档、目标、必须完成、不做事项、验收标准和交付要求；后续重要任务若缺这些字段，只能视为临时沟通，不能视为正式任务派发。
- 2026-06-24：多角色协作机制升级为 V0.6 验收门禁与并行冻结。T132/T138/T139 的教训是：执行角色代码级完成和静态测试通过，不等于浏览器用户态通过，更不等于阶段封板通过。架构师后续必须明确三层状态：代码级完成、测试验收通过、阶段封板通过；测试不通过时必须新建窄范围返工任务，引用失败报告和证据目录，不允许原任务无限延长。红线复测期间，其他后端/前端只能做不影响当前验收面的旁路准备，禁止改当前验收接口、页面主流程、provider/storage、状态机或资产状态契约。
- 2026-06-24：多角色协作机制升级为 V0.7 单入口总控。默认执行路径改为用户只对接主 Codex；主 Codex 作为产品负责人兼全栈总控，派发内置子智能体扮演 3 个前端、3 个后端、1 个测试、1 个系统架构师。旧的手动角色对话保留为特殊讨论入口，不再是默认开发路径。协议升级不改变现有任务状态；未完成任务继续按当前状态和冻结区推进。
- 2026-06-24：T139-T141 用户态红线专项已阶段封板通过。T140 真实浏览器证据显示工作区普通区在“开发诊断”之前 `main_hits_before_developer_diagnostics=[]`、`visible_hits_in_main=[]`，页段 PDF 入口走 `/api/backend/projects/.../files/...` 代理且 GET 返回 `application/pdf`，console error/warn 为空。该封板只覆盖 T138/T139 用户态红线，不代表真实 MinerU/provider、任意教材泛化、生产权限、多浏览器、真实视频或 PPT 主链路通过。
- 2026-06-24：T005-T010 v1 下一阶段文档链与验收计划已完成架构复核。T005 产品范围、T006 后端运行契约、T007 前端形态差距、T008 内网容器化草案和 T009 E2E 验收计划均已落盘；T009 经规格与质量复审通过，已修正新人冷启动立即项歧义和执行顺序。裁决：文档链与计划质量通过，可作为下一阶段执行输入；但不代表 v1 E2E、真实 provider、正式部署、生产权限、多浏览器、真实视频或 PPT 主链路通过。下一步先裁决 PRD 9 步、前端 7 步、底层 14 节点统一映射和最小封板门禁；真实 provider smoke 作为分离专项泳道，不阻塞 fake/placeholder 与浏览器用户态主流程验收。
- 2026-06-24：T143-T145 v1 最小封板门禁已完成有条件架构复核。T143 前端接入 `/workspace` 用户态契约并修复 Header/任务卡一致性、PPT 子门禁和 PPTX 普通摘要；T144 后端 `/workspace` 普通 `sub_gates` 已与开发诊断分离，兼容别名只在 `developer_diagnostics.steps.*.compatibility_aliases`；T145 测试验收通过，目标项目 `proj_d62361b7e98c` 浏览器普通区红线和路径泄漏扫描为空，PPTX 下载走 `/api/backend/projects/.../exports/...`，console error/warn 为空。裁决：v1 最小封板门禁有条件通过，范围仅限 fake/placeholder + 浏览器用户态 + 红线 + 下载代理 + 本地/内测权限默认策略；真实 provider、真实 PPT/视频质量、多浏览器、生产 RBAC/JWT/session、容器冷启动和备份恢复仍需另起专项。
- 2026-06-24：按用户要求安排 T146-T148 功能接口全量测试。架构裁决为 3 个测试批次而非扩大单个 T145：T146 覆盖后端 FastAPI 全接口合同，T147 覆盖 Next 代理和前端接口适配，T148 覆盖浏览器真实 API 串联与普通区红线。三者均使用独立端口和 storage，默认 fake/placeholder，不读取真实密钥，不宣称真实 provider、生产权限、多浏览器、容器冷启动或真实 PPT/视频质量通过。
- 2026-06-24：T146-T148 功能接口测试回收裁决为【不通过，待返工复测】。T146 后端 FastAPI 合同通过，T147 Next 代理/前端契约通过且 T148 已补 PPTX/MP4/PDF/Markdown 下载代理实测；但 T148 浏览器用户态失败：最终交付普通区暴露 `exports/final_delivery`、`delivery_manifest.json`、`gate_result.json`、JSON 片段和 `manifest`，已完成步骤回看被当前步骤覆盖，console 出现 duplicate key error。架构结论：不能宣布所有功能接口通过；新增 T149 前端窄范围返工和 T150 测试复测，T150 通过前冻结当前工作区用户态与最终交付普通区验收面。
- 2026-06-24：T149/T150 修复复测后，T146-T150 功能接口测试回收裁决更新为【有条件通过，T148 浏览器阻塞已关闭】。T149 前端修复最终交付普通区工程信息泄露、duplicate key 和已完成步骤回看 override；T150 真实浏览器复测确认最终交付普通区红线扫描空命中，PPT/视频回看切换正常，console error/warn 为空，T148 同口径 PPTX/MP4/PDF/Markdown Next 代理下载均 200。保守边界：本结论仅覆盖 fake/placeholder + 本地 FastAPI/Next/Web + 浏览器用户态 + 下载代理；不代表真实 provider、生产权限、真实 RBAC/JWT/session、多浏览器、容器冷启动或真实 PPT/视频质量。T150 发现的 `final_delivery` 嵌套导出路径 `/exports/final_delivery/...` 404 已拆为 T151，不阻塞本轮门禁。
- 2026-06-24：T152-T157 教材库管理员拆分与直接教案阶段已封板通过。教师新建项目页不再承载导入教材、切分教材、解析教材内容、重新解析等后台加工动作，只保留“使用教材库”和“直接使用教案”；管理员侧新增“管理教材库”承载上传教材、切分、解析、确认资产、教案库/上传教案。direct lesson 项目通过 `reference_lesson_plan_id` 进入教案步骤，用户态教材内容显示由教案替代/跳过，诊断中 `textbook_parse=skipped`，`current_step_id=lesson_plan`。新鲜验证：后端目标 `12 passed`、教材解析 `19 passed`，前端 new-project/admin-textbook-library 契约、tsc、lint 均 exit 0，真实 API 浏览器补证据目录 `docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-201700` 中教师页 `forbiddenHits=[]`、管理员页 `missing=[]`、console `error/warn=[]`。通过范围是本地 Web/API 真实 API 模式，不代表生产上线、生产 RBAC/JWT/session、多浏览器、容器冷启动、真实 provider 质量或管理员批量写入全流程通过。
