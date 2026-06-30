# 角色记忆：高级 UI 设计大师 + 前端工程师

## 角色定位

你是本项目特聘高级 UI 设计大师 + 资深前端工程师，核心关注 UI 视觉、UX 交互、页面信息传达和用户操作体验。

## 核心职责

- 视觉层面：统一设计语言、优化色彩层级、排版留白、组件质感、页面层次感，修正不协调视觉缺陷。
- 交互层面：梳理用户操作链路，简化操作步骤，优化反馈逻辑、过渡动画、状态提示和操作容错性。
- 产品价值传递：通过页面布局、信息权重、功能分区，直观凸显产品核心能力，降低用户理解成本。
- 前端体验交付：围绕页面体验、适配性、可用性和交互一致性提出可交付建议。

## 工作边界

- 优先输出视觉与交互优化结论。
- 涉及产品定位或功能取舍时，交由产品经理确认。
- 涉及跨模块边界或全局协作冲突时，交由首席系统架构师裁决。
- 涉及质量验收场景时，交由测试工程师补充。

## 标准交付物

- UI/UX 评审报告。
- 页面体验优化清单。
- 交互流程说明。
- 视觉一致性问题清单。
- 前端体验验收标准。

## 启动必读

- `AGENTS.md`
- `docs\multi-agent\README.md`
- `docs\multi-agent\role-call-templates.md`
- `docs\multi-agent\deliverable-templates.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

## 启动检查项

- 已确认当前对话是否明确指定前端开发或 UI 设计角色。
- 已读取共享事实和最近交接记录。
- 已明确本轮页面、流程或体验评审范围。
- 已识别需要产品经理确认的业务价值或功能取舍问题。

## 交付检查项

- 输出内容优先使用 UI/UX 评审模板。
- 已分别覆盖视觉问题、交互问题、信息层级、状态反馈和适配关注点。
- 已给出前端体验验收标准。
- 涉及产品定位、功能优先级或业务文案权重的问题已标记给产品经理。

## 收尾更新项

- 更新本文件“当前记忆”中的长期 UI/UX 结论。
- 更新 `workflow\multi-agent\handoffs\latest.md`。
- 形成共同体验原则时更新 `workflow\multi-agent\shared-facts.md`。
- 重要体验取舍被确认后更新 `workflow\multi-agent\decisions.md`。
- 与产品、测试、后端或架构师存在分歧时更新 `workflow\multi-agent\conflicts.md`。

## 记忆更新规则

每轮前端体验工作结束后，更新：

- 已确认设计语言和页面体验原则。
- 关键页面的 UI/UX 结论。
- 用户操作链路问题。
- 需要产品经理确认的功能价值或文案权重问题。
- 需要测试工程师覆盖的交互验收点。

## 当前记忆

- 2026-06-29：视频工作台 P1-7 费用保护前端代码级收口。生成视频前新增 `window.confirm` 确认，明确展示“确认生成 10 秒视频”、模型、尺寸、时长、参考图数量和项目频率限制；取消确认不会创建真实任务。`VideoWorkflowConfig` 新增 `run_create_window_seconds/run_create_project_window_limit/run_create_global_window_limit`，用于展示后端限流口径。验证：`bun src/lib/video-workflow-contract.test.ts`、`bun src/lib/video-workflow-errors.test.ts`、`bunx tsc --noEmit --incremental false`、`bun run lint`、`bun run build`、`bun run scan:client-secrets` 通过。仍需后续补浏览器确认弹窗验收。
- 2026-06-29：视频工作台 P1-6 播放器体验代码级收口。`VideoComposerPanel` 已为完成视频补“下载源文件”入口，正常加载后右下角可下载；解码/加载失败遮罩保留“重新加载”和“下载源文件”，并继续使用 `onLoadedMetadata/onError` 区分 loading/ready/error。类型 `VideoWorkflowRun` 新增 `download_bytes/download_sha256`，便于前端后续展示文件大小和校验信息。验证：`bun src/lib/video-workflow-contract.test.ts`、`bunx tsc --noEmit --incremental false`、`bun run lint`、`bun run build`、`bun run scan:client-secrets` 通过。仍需后续补真实浏览器 `loadedmetadata`/播放失败 E2E 证据。
- 2026-06-29：视频工作台 P1-5 上传交互代码级收口。`VideoAssetPanel` 改为逐个文件上传并显示每个文件的等待、上传中、成功、失败状态；批量上传允许部分成功，成功项会显示“部分参考图已上传”；失败项保留原始 `File` 并提供可点击/触屏可见的“重试”按钮。新增 `video-workflow-upload-queue.ts` 解决同名同大小文件状态混淆，上传异常兜底为“网络失败，请重试”。验证：`bun src/lib/video-workflow-upload-queue.test.ts`、`bun src/lib/video-workflow-contract.test.ts`、`bun src/lib/video-workflow-errors.test.ts`、`bun src/lib/video-workflow-polling-controller.test.ts`、`bunx tsc --noEmit --incremental false`、`bun run lint`、`bun run build`、`bun run scan:client-secrets`、`git diff --check` 通过。仍需后续补正式浏览器触屏/DOM 专项验收。
- 2026-06-29：视频工作台 P1-4 错误提示分层已代码级收口。前端新增 `video-workflow-errors.ts`，统一把结构化 API 错误转成教师/管理员可理解的中文说明、建议动作和追踪 ID；`VideoWorkflowWorkbench` 的创建、上传、删除、重试错误不再直接 toast 原始 store 字符串。`ApiClientError` 改为导出并保留结构化 details/action/traceId，但不再把 `details:` 拼入用户可见 message。轮询 sync 返回 `{ok:false}` 时也会进入退避和“下次重试”提示，避免同步失败被静默当成功。验证：`bun src/lib/video-workflow-errors.test.ts`、`bun src/lib/video-workflow-contract.test.ts`、`bun src/lib/video-workflow-polling-controller.test.ts`、`bunx tsc --noEmit --incremental false`、`bun run lint`、`bun run build` 通过。
- 2026-06-20：角色已建立，尚未形成项目专属 UI/UX 设计语言沉淀。
- 2026-06-20：V0.2 要求前端角色使用 UI/UX 评审模板交付，并在收尾时沉淀体验结论、验收点和跨角色分歧。
- 2026-06-20：已完成 `AppShell` 首屏模块图性能止血：业务大页与 `CommandPalette` 改为 `next/dynamic` 按需加载，保留登录页、壳层、侧栏、顶栏静态加载；命令面板仅在 `commandOpen` 时挂载。
- 2026-06-20：已完成前端 UI/UX 第一轮落地修复：新建项目补齐第 0 步核心配置，工作区底部操作区收敛为单主 CTA，演示账号接入 `NEXT_PUBLIC_DEMO_MODE` 开关，设计语言文档统一为暖纸白、深青灰、古铜金教研工作台体系。
- 2026-06-20：验证口径补充：`bunx tsc --noEmit`、`bun run lint`、`bun run build` 和桌面浏览器主流程均需作为前端收口证据；当前 `examples` 目录为示例代码，已从主应用 TypeScript 检查范围排除。
- 2026-06-20：已完成真实 API 最小闭环接入：真实模式下项目列表走 `GET /projects`，创建项目走 `POST /projects`，项目工作区 manifest 走 `GET /projects/{project_id}/manifest`，节点详情走 `GET /projects/{project_id}/nodes/{node_id}`；demo mode 继续使用 mock，真实 API mode 不再用 mock 项目/节点作为业务真状态。
- 2026-06-20：真实 API 工作区只渲染后端 manifest 返回的 10 个 MVP 节点，不再用前端 14 节点 `STAGE_DEFS` 补齐；保存、生成、确认、退回、采纳视频方案等写动作在真实模式下仅提示待接后端接口，避免伪装成功。
- 2026-06-20：本地真实 API 演示主流程已打通到最小写链路：新建项目后自动把教材解析摘要上传为 `textbook.txt`，工作区可对 `textbook_parse` 执行后端生成、刷新节点详情、确认通过，并进入 `lesson_plan` 节点；API 错误会在节点区显示可读提示，不再只静默失败或只 toast。
- 2026-06-20：本地演示验证命令基线为 `bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build`；浏览器 smoke 需覆盖真实 API 模式下“创建项目 → 进入项目 → 查看工作区状态 → 触发生成/确认/刷新”。
- 2026-06-20：T015 已修复真实 API 模式首页项目卡片与工作区 manifest 状态不同步；真实模式 `loadProjects` 会拉取项目列表后并行同步各项目 manifest 摘要，首页“继续工作”和“项目概览”都显示后端当前阶段、总进度和下一步动作。浏览器验证：确认 `textbook_parse` 后返回首页，项目显示“公开课教案 / 30% / 进入公开课教案”。
- 2026-06-20：T016 已收口新建项目第 2 步教材语义；创建向导统一表达为“教材内容准备 / 教材预览摘要 / 确认用于创建项目”，明确这里只准备教材文本并在创建后上传，工作区点击“生成草稿”才触发后端真实 `textbook_parse/generate`。本轮未改后端接口，未破坏真实 API 创建项目后的自动上传教材文本链路。
- 2026-06-20：收到重复 T015/T016 指令后完成前端二次复核；未新增功能改动。新鲜验证 `bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；浏览器真实 API 模式在 `8042/3042` 隔离端口创建 `T015-T016-复核项目`，第 2 步语义正确，工作区确认 `textbook_parse` 后返回首页，“继续工作”和“项目概览”均显示 `公开课教案 / 30% / 进入「公开课教案」`，控制台 error/warn 为空。
- 2026-06-20：T020 已打通公开课教案节点端到端本地演示：真实 API 模式下可在工作区生成 `lesson_plan`、查看后端内容、用轻量文本/JSON 编辑器保存到 `/nodes/{node_id}/edit`，再确认通过推进到 `intro_selection`。为保持首页/工作区同步，真实 API 映射新增 `currentStageTitle`，首页继续工作和项目卡片优先显示后端 manifest 阶段标题，避免 `视频导入选择` 被本地 workflow 标题显示成 `视频设计导入`。验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；浏览器真实 API smoke 完成 `textbook_parse` 生成确认、`lesson_plan` 生成/编辑/保存/确认，首页显示 `视频导入选择 / 40% / 进入「视频导入选择」`，控制台 error/warn 为空。
- 2026-06-20：T024/T028/T029 已把工作区真实 API 模式推进到本地 fake 视频生成任务可演示：`intro_selection` 支持生成 3 类候选、选择/轻量编辑保存、确认推进；`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 支持生成、查看、轻量编辑保存、确认推进；`final_video` 支持模型/尺寸/模式/生成范围选项，触发 fake `final_video/generate` 后展示 6 个 generated task、clip 数量和 `clips/shot_*.mp4` fake 输出路径。验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；浏览器真实 API smoke 项目 `T024-T028-T029-168836` 完成创建项目 → 教材解析 → 教案 → 视频导入选择 → 视频剧本 → 视频分场剧本 → 视频资产 → 分镜脚本 → 最终视频 fake 任务，应用级 error/warn 为空。
- 2026-06-20：T032/T034 已完成本地演示体验打磨：新建项目第 2 步预览优先基于用户粘贴教材内容生成并标注“来自粘贴内容”，正文不足时明确显示“示例预览”且提示不能当作用户教材解析结果；`final_video=running` 时底部主 CTA 改为“查看任务状态”，避免重复创建任务误导；视频链节点结果页改为“结构化编辑雏形”，先展示节点摘要和编辑步骤，再保留 JSON 编辑入口，并预留后端 `details` 字段级提示挂点。验证项目 `T032-T034-体验验证-224358`：首页/工作区显示 `最终视频 / 90%`，最终视频结果页显示 6 个 generated fake task，分镜结果页显示“分镜脚本摘要 / JSON 编辑入口”，浏览器 error/warn 为空。
- 2026-06-20：T039 当前未完成真实接口接入，保持阻塞等待后端 T038/T040。已复核当前前端仅有“生成教材预览”本地预览和 `uploadProjectTextbook()`，没有真实“解析教材”按钮、教材解析 API client、字段回填/手改状态、知识点下拉或知识点 Markdown 预览。前端后续必须等待后端给出稳定 PDF/MinerU/知识点 Markdown 契约后再接入，不得把“生成教材预览”说成真实教材解析，也不得用固定 mock 知识点冒充 MinerU 结果。
- 2026-06-21：T039 已恢复并完成真实教材解析前端联调。新建项目第 2 步在真实 API 模式下支持上传 fixture PDF，点击“解析教材”会先创建后端项目、上传 `POST /projects/{project_id}/textbook`，再调用 `POST /projects/{project_id}/nodes/textbook_parse/generate`，并用返回的 `content.textbook_meta` 回填学科、年级、教材版本、册次；这四项在解析结果卡内可手工调整。知识点下拉只渲染后端 `content.knowledge_points`，所选知识点 Markdown 来自 `content.selected_knowledge_point.markdown`，不再使用固定 mock 或本地预览冒充 MinerU 结果。验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；隔离端口 API `8139` + Web `3139` 浏览器 smoke 完成上传 fixture PDF → 解析教材 → 回填一年级/人教版/上册 → 知识点下拉显示“5以内数的认识” → Markdown 预览显示目标内容，控制台 error/warn 为空，截图在 `docs\qa-audits\t039-browser-textbook-parse.png`。剩余风险：若本机旧 `8000` API 未重启，仍可能返回 `.pdf` 不支持；当前后端没有独立更新项目元信息接口，解析后教师手改字段先保留在前端草稿，不能回写已提前创建的后端项目记录。
- 2026-06-21：已接入最终视频/交付区域的 PPT 导出入口。真实 API 模式下，工作区进入 `final_video` 对应的“最终视频”结果页后，会显示“交付 PPT”面板；点击“导出 PPT”调用 `POST /projects/{project_id}/export/ppt`，loading 时显示“导出中...”，成功后展示后端返回文件名和“下载 PPT”入口，下载链接使用后端 `download_url` 并按 API base 补全；失败时在面板内展示可读错误并 toast。demo 模式不伪造 PPT 导出。
- 2026-06-21：前端 PPT 导出入口通过架构师验收。新鲜验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 全部通过；浏览器真实 API 模式使用隔离 API `8175` 和 Web `3175`，项目 `proj_1c6012f6ad5d` 已到 `最终视频 / 90%`，进入“结果”页点击“导出 PPT”后显示 `已生成`、文件 `lesson-video-demo.pptx` 和下载链接 `GET /projects/proj_1c6012f6ad5d/exports/lesson-video-demo.pptx`；浏览器 console error/warn 为空。剩余：未做完整 PDF→PPT E2E，交由测试工程师统一回归。
- 2026-06-21：T051 已收口最终视频节点用户可用体验。最终视频结果页会优先从节点 `content.video_path`、mutation 顶层 `video_path`、task `result.download_path/video_path` 或 PPT 导出 `video_path` 中提取 MP4 路径，展示“演示视频文件已生成”和“下载 MP4”；MP4 链接按 `/projects/{project_id}/outputs/final_video.mp4` 或后端返回路径补全。PPT 导出入口继续保留，成功后仍展示 PPT 下载链接。若生成失败信息包含 `OCTO_REQUEST_FAILED`，页面展示“真实视频服务暂不可用，可切换占位视频模式完成本地演示”的恢复提示，不吞掉原始错误。
- 2026-06-21：T060 已补课程锚点确认/编辑控件。真实 API 模式下，`intro_selection` 结果页新增“课程锚点确认”编辑框；选择候选方案会同步更新 `primary_design_id`、`selected_design_ids`，并把该方案 `anchor_to_lesson` 写入 `selected_anchor`；教师可手工修改 `selected_anchor`。保存和确认前前端校验 `selected_anchor` 非空且不少于 10 个字。JSON 高级编辑入口保留但不再是唯一编辑路径。视频脚本摘要优先展示 `selected_anchor/anchor_to_lesson` 课程锚点。浏览器证据：隔离 API `8060` + Web `3060`，项目 `proj_dc79e4da64e2` 完成选择“电梯按钮”→ 自动填锚点 → 手改锚点 → 保存 → 确认 → 生成视频脚本，脚本摘要展示同一锚点；控制台 error/warn 为 0，证据在 `docs\qa-audits\t060-anchor-ui-evidence.json`、`docs\qa-audits\t060-intro-selection-dom-evidence.txt`、`docs\qa-audits\t060-video-script-dom-evidence.txt`。
- 2026-06-21：T065 已收口真实图片/视频生成过程的用户可见体验。`intro_video_asset` 结果页展示图片生成状态、成功图片预览、失败原因、刷新任务和单图重试入口；`final_video` 结果页展示 MP4 下载、PPT 导出/PPT 下载、每个 clip 的状态、脱敏 `provider_task_id`、单 clip 刷新/重试和 provider 失败可重试提示。错误文案通过脱敏摘要处理，不暴露密钥、token 或完整上游响应。视频脚本与分镜摘要持续展示同一 `selected_anchor` 课程锚点。验证：`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；浏览器真实 API 模式复核 3163 工作区进入视频资产结果页，包含重试入口且控制台 error/warn 为 0；截图证据在 `docs\qa-audits\t065-final-video-real-api.png`、`docs\qa-audits\t065-video-assets-real-api.png`。剩余风险：本轮未重新触发外部真实 provider 生成新任务，沿用已有真实 API 项目结果截图。
- 2026-06-23：T106 已轻量接入 StateEngine 状态诊断展示。真实 API 工作区节点详情会在标题下方显示 StateEngine 状态、`review_reason`、`latest_transition` 最近迁移和依赖阻断说明；`UPSTREAM_NOT_APPROVED` 显示为“上游未确认”，`RULE_WARNING` 显示为“规则警告可覆盖”，`RULE_VIOLATION*` 显示为“硬阻断不可继续”。`WorkflowStage` 已保留后端 `latest_transition`，mapper 契约测试覆盖该字段。demo/mock 模式不渲染诊断块。验证：`bun src/lib/api-mappers-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过。
- 2026-06-23：T131 已完成工作区备课工作台用户态重构。`ProjectWorkspaceScreen` 普通主界面改为 7 个教师可理解步骤：项目信息、教材内容、教案生成、导入视频方案、PPT 草稿、视频生成、最终交付；已完成步骤可回看，未解锁步骤点击只 toast 提示先完成上一阶段，不进入详情。当前步骤主区域改为任务卡，展示“这一步要做什么 / 你现在需要做什么 / 当前结果或可编辑区域 / 依据 / 唯一主按钮”。教案使用 Markdown 编辑/预览，已完成回看默认只读；视频方案、PPT 草稿、分镜等主界面只展示可读摘要，不铺 raw JSON。原输入/运行/结果/依据/日志 Tab、StateEngine、原始结构和日志保留在默认关闭的“开发诊断”折叠区。验证：`bun src/lib/workspace-user-flow-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 通过；浏览器证据在 `docs\qa-audits\t131-workspace-user-flow-evidence\`。
- 2026-06-23：T130 已完成新建项目页用户态重构。新建页第一步改为“选择教材来源”，教材库用下拉框展示“人教版 / 小学数学 / 一年级 / 上册”，上传教材文案明确进入同一套“目录 / 课时知识点”真实后端流程；第二步知识点选择置顶，并集中展示/可改学科、年级、教材版本、册次、教材标题、项目名称、课型、目标受众。核心知识点不再常驻铺开，改为“查看核心知识点”弹窗；教材页段、教材内容、教案参考均按按钮打开。视频关键词改为标签多选并支持自定义保留，预计时长支持下拉和自定义输入，PPT 结构改为固定模板下拉。普通新建页隐藏输出路径、安全模式、provider 等技术字段。验证：T130 契约测试、工作区用户态契约、api mapper 契约、tsc、lint、build 通过；浏览器截图在 `docs\qa-audits\t130-new-project-textbook-source.png`。剩余：T132 需在真实 API 环境下补知识点下拉、证据包弹窗、标签/时长/PPT 模板完整截图。
- 2026-06-24：T139 已修复 T138 P0 工作区 JSON fallback。`textbook_parse` 普通任务卡改为 `TextbookContentResult` 教师可读卡，展示课时标题、教材页码、知识点摘要、解析状态、教材依据和教材内容预览；普通区不再显示“完整内容仍在下方 JSON 中编辑”、`JSON` badge 或 raw 字段名。raw content、字段名、StateEngine 等仍只在默认折叠的“开发诊断”中。页段 PDF 按钮走 `/api/backend/projects/{project_id}/files/knowledge-points/...` 代理入口，新建项目证据包同样修正为 `/files` 代理，不显示 storage 路径。首页加载态从“数据来源：GET /projects”改为“正在同步项目列表”。验证：T139 先让工作区契约测试失败后修复，最终 `bun src/lib/workspace-user-flow-contract.test.ts`、`bun src/lib/new-project-user-flow-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint`、`bun run build` 均通过；仍需测试工程师执行 T140 浏览器红线复测。
- 2026-06-24：V0.6 用户态红线基线。前端后续涉及普通教师主界面时，不能只以源码/契约测试/tsc/lint/build 作为通过依据；交接只能写“代码级完成，待测试验收”。普通区不得出现 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage`，这些只允许在默认折叠的“开发诊断”内部。若使用通用 fallback 展示后端结构，必须先转换成教师可读摘要；禁止在普通区展示 raw object、字段名或内部路径。
- 2026-06-24：T007 已完成前端产品形态差距审查，产出 `docs\frontend-product-shape-gap.md`。当前形态为：首页继续工作/项目概览/待办/系统轻状态；新建项目 5 步；工作区 7 个用户态步骤；底层 `workflow.ts` 仍是 14 节点，PRD 是 9 步双分支。核心差距是三套流程口径未统一，第 0 步角色字典/视觉契约/合规红线仍偏文本化，demo/API/mock 模式词对普通教师有理解风险，反馈飞轮机制文件存在但前端可见性不足。建议主 Codex 先裁决 9 步/7 步/14 节点映射，再拆小任务处理模式词、第 0 步结构化、PPT/视频子状态和反馈入口；任何触及工作区普通主界面的实现都需重新做浏览器红线复测。
- 2026-06-24：T143 已按 T142 映射表完成工作区用户态子状态与普通文案代码级改造。`PPT 草稿`普通任务卡新增结构方案、逐页脚本、视觉资产、PPTX 文件四个子状态；`视频生成`新增文稿、分场剧本、资产与首帧、分镜、clip/TTS/合成五个子状态，并明确本地演示视频不代表真实成片质量。`导入视频方案`强化课程锚点、课堂落点问题、不提前讲解内容三字段；普通路径替换 API/demo/provider/fake/artifact/manifest/selected_anchor 等工程词，开发诊断仍保留内部结构。验证：先让 `bun src/lib/workspace-user-flow-contract.test.ts` 因缺少结构方案失败，再实现后通过；`bunx tsc --noEmit --pretty false` 通过。仍需 T145 做浏览器/DOM 红线与用户态验收，当前仅为代码级完成。
- 2026-06-24：T145 后确认 T143 前端接入通过最小门禁测试验收。后续工作区优先使用后端 `/workspace` 用户态契约驱动 Header、任务卡和子门禁；manifest fallback 只能作为兼容降级，不能覆盖当前步骤真实待处理 stage。PPTX 普通结果区只能显示教师可读状态、文件名和下载按钮，禁止显示 `exports/...`、`/projects/proj...`、artifact、provider、manifest、API 等工程路径或术语；内部路径和兼容别名只能留在默认折叠的“开发诊断”。
- 2026-06-24：T149 已完成 T148 前端失败点二轮代码级返工。红灯先覆盖最终交付专用教师摘要、动态摘要 key、显式用户回看 override、最终交付普通区隐藏 evidence 预览，并分别确认缺少 `final-delivery` 专用摘要、缺少显式 override 时契约失败。修复后 `ProjectWorkspaceScreen.tsx` 中已完成步骤回看使用 `selectedUserStepOverride`，默认加载/刷新仍以 `/workspace.current_step_id` 为权威，主按钮推进、刷新和后端 current 变化会清理 override；最终交付普通区改为教案材料、PPT 文件、导入视频、材料检查等教师摘要，只读取路径字段存在性，不渲染内部路径、delivery/gate 文件名或 JSON 片段；最终交付普通任务卡不再渲染 `stage.evidence` 预览按钮，内部 evidence/JSON/gate/manifest 文件只留开发诊断；动态摘要 key 改为 label+index，避免 `摘要 17` 重复。验证：`bun src\lib\workspace-user-flow-contract.test.ts`、`bun src\lib\api-mappers-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint` 均 exit 0。当前仅为代码级完成，仍需 T150 浏览器 DOM 红线、回看点击和 console 复测。
- 2026-06-24：T156 已完成管理员“管理教材库”代码级交付。新增 `AdminTextbookLibraryScreen`，采用管理员控制台式布局，真实 API 接入教材库列表、上传教材、任务查询、知识点选择、全量/选中切分、全量/选中解析、资产查看/确认、教案库查询/查看/上传；左侧导航新增 admin-only “管理教材库”，`AppShell` 可路由到 `admin-textbook-library`。新增 `uploadLessonPlanToLibrary(file, metadata)` 和 `admin-textbook-library-contract.test.ts`，先红灯验证页面不存在，再实现转绿。验证：`bun src/lib/admin-textbook-library-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint` 均 exit 0。当前仅为代码级完成，待 T157 用真实 API 浏览器集成验收管理员页面和教师普通区红线。
- 2026-06-24：T155/T156 已通过 T157 真实 API 浏览器验收并封板。教师新建项目页当前只展示“使用教材库”和“直接使用教案”两条起点，旧教材加工词 `导入教材/切分教材/解析教材内容/重新解析/重新导入教材` 在教师页 DOM 扫描中 `forbiddenHits=[]`；上传教案在真实 API 模式下会调用教案库上传并回填 `selectedLessonReferenceId`，用于创建 direct lesson 项目。管理员页“管理教材库”承载上传教材、切分教材、解析教材内容、确认资产、教案库和上传教案，只有管理员侧导航可见。新鲜验证：`bun src\lib\new-project-user-flow-contract.test.ts`、`bun src\lib\admin-textbook-library-contract.test.ts`、`bunx tsc --noEmit --pretty false`、`bun run lint` 均 exit 0；浏览器补证据 `docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-201700` 中教师页禁词为空、管理员页 `missing=[]`、console `error/warn=[]`。关注项：真实 API 首页项目列表刷新有短暂空列表 loading 态，后续可单独优化。
