# ShanHaiEdu v1 E2E 回归验收计划

日期：2026-06-24
任务：T009
角色：测试工程师子智能体
状态：验收计划，待开发交付后执行

## 1. 结论先行

本文是 v1 下一阶段端到端验收计划，不是验收通过报告。

当前可立即执行的只有文档冷启动、fake/placeholder 最小链路、静态防误提交核验、权限默认策略核验、浏览器用户态红线基线复扫等低外部依赖测试。真实文本、真实图片、真实视频、真实 TTS、PPT 主链路、容器冷启动、多浏览器和生产权限验收必须等待对应开发交付、临时环境准备或外部 provider 账号/额度/模型权限恢复后再执行。

T140/T141 只封板 T138/T139 用户态红线专项：工作区普通教师主界面不暴露指定工程词、开发诊断默认折叠、教材页段入口不暴露本地路径。它不代表真实 provider、生产权限、多浏览器、真实视频、PPT 主链路通过。V0.6 三层完成定义仍有效：代码级完成、测试验收通过、阶段封板通过不能混用。

## 2. 范围和非范围

### 依据文件

- `AGENTS.md`：项目规则、T140/T141 边界、V0.6 三层完成定义、密钥与真实 provider 约束。
- `docs\multi-agent\README.md`：V0.7 单入口总控、V0.6 验收门禁、用户态红线与并行冻结规则。
- `workflow\multi-agent\shared-facts.md`：当前产品/协作/部署共同事实、真实 provider 与生产权限边界。
- `workflow\multi-agent\handoffs\latest.md`：T140 测试交接、T141 阶段封板复核和 T005-T008 上下文。
- `workflow\multi-agent\roles\qa-engineer.md`：QA 历史回归基线、T076/T132/T138/T140 风险记忆。
- `workflow\multi-agent\dispatch.md`：T005-T010、T140、T141 任务状态、交付物和范围说明。
- `docs\product-v1-next-scope.md`：T005 产品范围和 P01 主流程验收输入。
- `docs\backend-runtime-contract.md`：T006 API 运行、权限、storage、provider 模式和测试输入。
- `docs\frontend-product-shape-gap.md`：T007 前端产品形态差距、浏览器断点和红线复测建议。
- `docs\ops-containerization-plan.md`：T008 本地/内网容器化、密钥注入、storage、备份恢复和回滚草案。
- `docs\qa-audits\2026-06-24-t140-user-flow-redline-rerun.md`：T140 用户态红线专项复测报告。
- `docs\qa-audits\t140-user-flow-redline-rerun-evidence\20260624-100115`：只引用关键证据文件名，不复制大规模内容。

### 范围

- P01 李雪老师标准公开课场景和一晚应急场景。
- 登录、首页、新建项目第 0 步、工作区 7 个用户态步骤、最终交付和反馈入口。
- 前后端契约：项目创建、教材挂载、manifest/节点详情、节点生成/编辑/确认、任务查询、文件代理和下载。
- fake/placeholder 模式下的本地最小 E2E。
- 真实 API 模式下的文本、图片、视频、TTS 分离 smoke。
- 新人冷启动、容器化草案、storage 持久化、备份恢复和回滚验收。
- 防误提交、密钥变量、权限鉴权、浏览器断点、红线词和路径泄露。

### 非范围

- 不在本文直接执行真实 E2E。
- 不读取、打印或记录真实 token/key/secret 值。
- 不把真实视频主线复跑列为默认必须立即执行前置；该主线仍阻塞于外部 provider 配额、账号池或模型权限。
- 不承诺真实 MinerU/provider、任意教材泛化、生产级 RBAC、多租户、多浏览器、PPT 主链路、真实视频主链路已通过。
- 不更新 `dispatch.md`、`stage-review.md`、`handoffs\latest.md`，由主 Codex 回收审查后统一更新。

## 3. 前置输入矩阵

| 输入 | 提供什么 | 不能证明什么 | T009 使用方式 |
|---|---|---|---|
| T005 `docs\product-v1-next-scope.md` | P01 公开课成品包目标、登录/首页/第 0 步/工作区/反馈飞轮业务验收、红线边界 | 不证明前端已实现，不证明真实 provider 或 PPT/视频主链路通过 | 作为产品主流程和验收语言基准 |
| T006 `docs\backend-runtime-contract.md` | API 启动目录、Python/依赖、`/health` 边界、鉴权策略、storage/SQLite、provider 模式、任务状态、变量名 | 不证明生产权限、provider readiness、多实例或 Cloud Run 可用 | 作为 API 合同、权限、storage、provider smoke 基准 |
| T007 `docs\frontend-product-shape-gap.md` | 首页/新建/工作区现状，PRD 9 步、前端 7 步、底层 14 节点差异，P0/P1/P2 改造建议 | 不证明新 UI 已改，不代表浏览器新回归通过 | 作为浏览器断点、流程口径和文案红线测试输入 |
| T008 `docs\ops-containerization-plan.md` | Web/API 双容器草案、`.dockerignore`、storage volume、health/readiness、密钥注入、日志、备份、恢复、回滚 | 不证明正式 Dockerfile/compose 已落地，不证明容器构建通过 | 作为新人冷启动、容器、备份恢复和防误提交验收输入 |
| T140/T141 | T138/T139 用户态红线专项测试通过并阶段封板 | 不证明真实 provider、生产权限、多浏览器、真实视频、PPT 主链路通过 | 作为工作区红线基线和后续复扫模板 |

T140 关键证据文件名：`runtime-launch-params.json`、`api-health.json`、`textbook-parse-generate.json`、`manifest-final.json`、`workspace-user-flow-api-after-prep.json`、`browser-workspace-textbook-main.png`、`browser-redline-scan-main.json`、`browser-textbook-slice-dialog.png`、`browser-pdf-entry-scan.json`、`pdf-proxy-get.json`、`browser-console.json`。

## 4. 测试分层

1. 产品主流程：P01 从登录、首页、新建项目、教材内容、教案、导入视频方案、PPT 草稿、视频生成到最终交付和反馈。
2. API 合同：`/health`、项目、教材、manifest、节点、任务、文件代理、导出下载、错误码和状态推进。
3. 前后端真实 API 模式：`NEXT_PUBLIC_DEMO_MODE=false` 下不混用 mock 项目，不把工程词暴露给普通教师。
4. 浏览器用户态红线：开发诊断之前不得出现 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage`，首页和新建项目另扫 `API/mock/demo/token` 等产品语言风险。
5. 新人冷启动/容器化草案：从干净环境按文档启动 fake/placeholder 最小链路；容器草案只在临时验证目录或临时分支执行。
6. 防误提交/密钥：只检查变量名、忽略规则、镜像上下文和 git 跟踪状态，不读取真实值。
7. 权限鉴权：`BACKEND_API_TOKEN` 空/正确/错误、admin 隐藏策略、Web 服务端代理不把 token 暴露给浏览器。
8. storage/备份恢复：项目目录、SQLite/WAL/SHM、uploads/assets/outputs/exports/logs 持久化、备份和恢复 smoke。
9. provider smoke：文本、图片、视频、TTS 分离执行；真实视频不作为默认 E2E 前置。
10. PPT/视频交付：placeholder/fake 可验证下载和状态；真实 PPTX、真实多 clip、配音字幕和视频质量另起专项。
11. 跨浏览器/响应式：至少 Chrome 基线后，再安排 Edge/Firefox 和移动断点；当前不由 T140 覆盖。
12. 回归停止条件：P0/P1 红线、密钥泄露、权限越界、storage 路径泄露、生产误宣称或真实 provider 阻塞时停止封板。

## 5. 测试用例表

| ID | 目标 | 步骤摘要 | 证据 | 通过标准 | 依赖/是否可立即执行 |
|---|---|---|---|---|---|
| QA-V1-001 | 文档冷启动一致性 | 按 T005-T008 和 AGENTS 逐项核对范围、非范围、变量名和风险 | 文档核对表 | 无真实密钥、无范围外承诺、T140/T141 边界清楚 | 可立即执行 |
| QA-V1-002 | fake/placeholder 最小 API 链路 | 启动隔离 API，创建项目，上传教材文本或 fixture，生成/确认 `textbook_parse` 和 `lesson_plan` | HTTP JSON、manifest、server log | 状态推进正确，错误不暴露密钥 | 可立即执行 |
| QA-V1-003 | Web 真实 API 模式基础 | 启动隔离 Web，登录，首页创建项目，进入工作区，读取 manifest/节点 | 浏览器截图、network、console | 不混用 mock 项目，console error/warn 为空 | 可立即执行，需短时服务 |
| QA-V1-004 | 首页产品语言 | 检查项目卡、空态、待办、系统轻状态 | DOM 扫描、截图 | P01 能看懂下一步；普通路径不以 API/mock/demo/provider 解释核心状态 | 等待前端文案交付后执行 |
| QA-V1-005 | 新建项目第 0 步 | 走教材来源、知识点、项目信息、视频偏好、PPT 模板 | 表单截图、字段值、请求 | 5 分钟内能完成应急资料；角色/视觉/合规/PPT/视频偏好可见 | 等待第 0 步改造交付后执行 |
| QA-V1-006 | 工作区 7 步用户态 | 覆盖已完成回看、当前任务卡、未解锁提示、主按钮 | DOM 扫描、截图、manifest | 用户能回答看什么、改什么、点什么；不暴露工程词 | 可复用 T140 模板，改动后执行 |
| QA-V1-007 | 红线词分区扫描 | 扫描开发诊断之前、展开诊断后、弹窗/iframe 地址 | `browser-redline-scan-main.json` 类证据 | 普通区零命中，诊断默认折叠，路径不泄露 | 可立即执行基线；UI 改动后必须执行 |
| QA-V1-008 | API 合同与状态阻断 | 上游未 approved 生成下游、edit、approve、skip、task 查询 | HTTP 响应、DB/manifest 摘要 | 409/状态迁移/错误码符合 T006，不混淆代码完成和验收通过 | 可立即执行 |
| QA-V1-009 | 鉴权默认策略 | 分别空 token、正确 token、错误 token 访问普通/admin API | HTTP 状态表 | 普通 API 空 token 仅本地放行；配置后 401/403；admin 未配置隐藏为 404 | 可立即执行，不读取真实值 |
| QA-V1-010 | Web token 不外泄 | 浏览器抓取页面源码、localStorage、sessionStorage、network headers 可见面 | 脱敏扫描报告 | 浏览器不可见 `BACKEND_API_TOKEN`，不出现真实 key | 等待 Web 代理交付后执行 |
| QA-V1-011 | 防误提交 | 检查 `.gitignore`/`.dockerignore` 草案、git tracked、构建上下文清单 | `git status`、ignore 检查、上下文文件列表 | `.env*`、storage、SQLite、logs、真实图片/视频/PPT、私有 skill env 不被跟踪或打包 | 可立即执行文档级；容器交付后复验 |
| QA-V1-012 | 新人冷启动文档核对 | 按 T006/T008 和现有 runbook 逐项核对依赖、端口、变量、启动命令和无需真实密钥边界；不在新环境安装 | 文档核对表 | 新人能看懂最小链路所需步骤；缺脚本、缺正式说明或歧义必须列为待补 | 可立即执行 |
| QA-V1-012R | 新人真实冷启动 | 在干净环境安装依赖，按正式 runbook 启动 API/Web fake/placeholder | 命令日志、健康检查、浏览器截图 | 不需要真实密钥即可完成最小链路 | 等待冷启动脚本或正式说明后执行 |
| QA-V1-013 | 容器草案验证 | 在临时目录创建 Dockerfile/compose 草案，build/up fake 链路 | build log、compose ps、health、storage | 镜像不含密钥/运行数据，API/Web 可通信 | 等待主 Codex 确认可验证容器草案 |
| QA-V1-014 | storage 持久化 | 创建项目，重启 API/Web 或容器，复查项目和 manifest | 项目目录、DB 文件、浏览器回看 | 数据不丢失，删除容器不删除 volume | 等待容器或重启环境 |
| QA-V1-015 | 备份恢复 | 停服务，备份 storage，恢复到新 storage，启动 smoke | 备份清单、恢复日志、HTTP/浏览器证据 | SQLite/WAL/SHM 和产物一致恢复 | 等待运维脚本或人工窗口 |
| QA-V1-016 | 真实文本 smoke | `PROVIDER_MODE=real/deepseek/minimax`，视频 placeholder，跑到教案或脚本节点 | 脱敏 provider 模式、HTTP、manifest | 文本真实链路通过，不声明真实视频通过 | 等待密钥/额度，非立即 |
| QA-V1-017 | 真实图片 smoke | `IMAGE_PROVIDER_MODE=real`，单图或最小资产生成 | task JSON、失败/成功截图、下载状态 | task/error/retryable 脱敏正确；失败不阻断默认 E2E | 等待 provider 恢复，非立即 |
| QA-V1-018 | 真实视频 smoke | `VIDEO_PROVIDER_MODE=real`，单 clip submit/query/download | task JSON、provider 状态、clip 文件 | submit/query/download 行为可解释；不要求完整 final video | 等待外部 provider，非立即 |
| QA-V1-019 | TTS smoke | `TTS_PROVIDER_MODE=real` 单独生成旁白 | task/audio、错误摘要 | 音频或失败状态脱敏可追踪 | 等待 TTS provider，非立即 |
| QA-V1-020 | PPT/视频 placeholder 交付 | fake/placeholder 下通过 API 或已有下载入口生成 MP4/PPT 或导出占位包；交付页 UI 另等页面改造后复验 | 下载文件、hash、PPT 媒体检查、必要时补交付页截图 | 只声明演示占位交付，不冒充真实成片 | API/下载层可立即执行；交付页 UI 等待改造 |
| QA-V1-021 | PPT 主链路真实验收 | 逐页脚本、视觉资产、PPTX 下载、逐页审查 | PPTX、截图、页面脚本 | 每页讲法/学生动作/数学点可核验 | 等待 PPT 主链路开发交付 |
| QA-V1-022 | 视频主链路真实验收 | 首帧、分镜、clip、TTS、字幕、拼接、局部重试 | 视频文件、clip/task、浏览器验收 | 真实视频质量和下载通过 | 等待 provider 和视频链开发交付 |
| QA-V1-023 | 跨浏览器与响应式 | Chrome 基线后跑 Edge/Firefox、桌面/移动断点 | 多浏览器截图、console | 无遮挡、主流程可操作、红线仍零命中 | 等待主流程稳定后执行 |
| QA-V1-024 | 回归停止条件演练 | 人为制造或复用 fixture：provider 失败、权限失败、缺 ffmpeg、storage 不可写 | 错误页、task/error、日志 | 用户态提示可懂，不伪造成片，不泄密 | 部分可立即，部分待 fixture |

## 6. 执行顺序建议

1. 先执行 fake/placeholder 和文档级冷启动核对：QA-V1-001、002、007、008、009、011、012。这里的 QA-V1-012 只做文档核对，不做干净新环境真实安装。
2. 再分离执行真实 provider smoke：QA-V1-016 文本、017 图片、018 视频、019 TTS。任一真实 provider 不可用时只记录阻塞，不阻断 fake/placeholder 验收计划；真实视频 provider 未恢复前不得进入真实视频主线通过判断。
3. 然后执行浏览器基础真实 API 模式和用户端到端回归：QA-V1-003、004、005、006，重点看普通教师路径、流程口径和红线词。
4. 在正式说明或脚本补齐后做新人真实冷启动、容器和 storage：QA-V1-012R、013、014、015。
5. 最后执行 PPT/视频交付与跨浏览器：QA-V1-020 到 QA-V1-023。
6. 全程保留 QA-V1-024 作为停止条件演练，防止错误被包装成通过。

## 7. 当前可立即执行与等待项

### 可立即执行

- 文档冷启动一致性。
- fake/placeholder 最小 API 链路；需要隔离本机短时服务可启动，不代表无需环境准备。
- API 合同与状态阻断。
- 鉴权默认策略。
- 防误提交文档级核验。
- T140 同类浏览器红线基线复扫。
- `/health` liveness 与 storage 写入 readiness 区分。

### 等待开发交付或环境准备

- 首页/新建/工作区产品语言改造后的浏览器回归。
- 第 0 步结构化角色字典、视觉契约、合规红线改造验收。
- 正式 Dockerfile/compose/`.dockerignore` 落地后的容器冷启动。
- Web 服务端代理鉴权和浏览器 token 不外泄验收。
- storage 备份恢复脚本或人工窗口。
- PPT 主链路和真实视频主链路。
- Edge/Firefox/移动端断点。

### 等待外部 provider 恢复

- 真实图片 provider smoke。
- 真实视频 provider smoke。
- 真实 TTS smoke。
- 真实视频完整多 clip 主线复跑。

## 8. 风险和阻塞清单

- R1：PRD 9 步、前端 7 步、底层 14 节点仍需统一映射，否则测试选择器、文案和阶段判定会漂移。
- R2：真实视频主线仍受外部 provider 配额、账号池、模型权限或网络稳定性阻塞，不能作为默认立即执行前置。
- R3：`/health` 只能证明 liveness，不能证明 storage、provider、token、ffmpeg 或 CORS readiness。
- R4：当前普通 API 未配置 `BACKEND_API_TOKEN` 时放行，只能用于隔离本机或内测演示，不是生产权限通过。
- R5：SQLite/storage 只适合单 API 实例；多实例或 Cloud Run 默认形态需另起架构专题。
- R6：容器草案尚未落地，`*_FILE` secret 支持方式需验证。
- R7：真实 provider 产物、storage、SQLite、日志和私有 env 误提交或进入 Docker build context 是高风险门禁。
- R8：PPT/视频 placeholder 下载不能冒充真实成片质量验收。
- R9：工作区普通主界面已通过 T140/T141，但任何新 UI 文案或流程改动后都必须重新浏览器/DOM 红线复扫。
- R10：多浏览器、响应式和移动端仍未覆盖，不能对外宣称兼容通过。

## 9. 交给 T010 架构师的复核输入

- 请确认 T009 计划是否覆盖 T005 的 P01 产品主流程、T006 的运行/安全边界、T007 的前端口径差距、T008 的内网容器化草案。
- 请裁决 PRD 9 步、前端 7 步、底层 14 节点的统一验收映射表由谁补齐、何时补齐。
- 请确认哪些用例作为下一阶段必须先跑的封板门禁，哪些作为专项后置。
- 请继续强调 T140/T141 只封板用户态红线专项，不代表真实 provider、生产权限、多浏览器、真实视频或 PPT 主链路通过。
- 请决定真实 provider smoke 的触发条件：账号/额度/模型权限恢复后再跑，还是先建立失败 fixture 做可控回归。
- 请确认容器草案是否进入临时验证任务，还是等待正式 Dockerfile/compose 文件落地后再由 QA 执行。
