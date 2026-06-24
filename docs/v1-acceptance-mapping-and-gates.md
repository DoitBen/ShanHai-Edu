# v1 统一验收映射与最小封板门禁

日期：2026-06-24
任务：T142
角色：系统架构师子智能体
状态：架构裁决文档

## 1. 结论先行

推荐采用三层映射：

1. 7 步用户态作为教师主导航。
2. PRD 9 步作为验收语义层。
3. 底层 workflow / manifest 节点作为诊断与执行层。

理由：

- P01 李雪老师需要的是“我现在看什么、改什么、点什么进入下一步”，不应被 9 步双分支和底层节点打散注意力。
- PRD 9 步仍是 v1 验收语义真源，尤其是 PPT 逐页脚本、PPT 视觉资产、PPTX、视频首帧/分镜/clip/合成等门禁，不能因为前端压成 7 步而丢失。
- workflow / manifest 节点保留为执行、诊断、测试选择器和回归证据真源，普通教师主界面默认不展示内部节点名。

裁决口径：下一阶段所有前端、后端、测试任务必须同时标注它触达的用户态步骤、PRD 语义步骤和底层节点。测试报告不得只写“第 5 步通过”或“PPT 草稿通过”，必须说明对应的 PRD 门禁和底层节点证据。

## 2. 三层职责边界

| 层级 | 面向对象 | 职责 | 不做 |
|---|---|---|---|
| 7 步用户态 | P01 教师用户 | 主导航、当前任务卡、已完成回看、未解锁提示、最终交付与反馈 | 不暴露 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage` |
| PRD 9 步验收语义 | 产品、测试、架构师 | 定义公开课作品包的验收含义、分支门禁、是否能进入下一阶段 | 不要求普通 UI 逐字显示 PRD 步骤名 |
| workflow / manifest 执行层 | 后端、前端工程、QA 证据 | 节点状态、依赖、产物、任务、版本、错误诊断、文件下载 | 不替代用户态语言，不直接作为教师主导航 |

## 3. 统一映射表

| PRD 9 步 / 收尾 | 用户态 7 步 | 底层 workflow / manifest 节点 | 用户可见产物 | 封板证据 |
|---|---|---|---|---|
| 第 0 步：项目配置、角色字典、视觉契约 | 1. 项目信息 | `project-meta`、`project-config`、`visual-contract`、`character-dict`；前端旧定义为 `project-config` | 课题、教材、公开课目标、班级基础、导入视频偏好、PPT 偏好、角色字典摘要、视觉契约、合规红线 | 新建项目截图或 DOM：角色/视觉/合规可见；普通区不出现输出路径、安全模式、API/provider 等工程词；创建后 manifest 保留项目上下文 |
| 教材前置支撑：教材库、目录、知识点、页段、MinerU Markdown | 2. 教材内容 | `textbook-parse`；教材库相关接口和资产包属于该用户态步骤的支撑层 | 教材页码、PDF 页码、知识点摘要、教材内容 Markdown、页段预览、解析/确认状态 | HTTP 证据、manifest、浏览器截图、页段代理 GET；普通区红线零命中；本地路径不泄露 |
| 第 1 步：公开课教案 | 3. 教案生成 | `open-lesson-plan`；旧前端另有 `lesson-plan-final`，后续只作为教案修订/回看子产物，不单独成为教师主导航 | 教案 Markdown、教材依据、教学目标、重难点、流程、板书、三类九套导入设计 | 生成/编辑/保存/确认 HTTP 证据；Markdown 编辑/预览截图；确认后下游解锁；教案来源追溯当前教材内容 |
| 第 1.5 步：导入设计选择集 | 4. 导入视频方案 | `video-design-import` / 后端历史命名可为 `intro_selection`；映射到同一语义 | 候选导入方案、视频独立主题、吸睛点、课程锚点、课堂落点问题、接入教案位置、不提前讲解内容、推荐理由 | 浏览器候选卡截图；选择/保存/确认 API 证据；课程锚点向下游脚本/分镜传递；候选不冒充终版 |
| PPT 分支第 2 步：PPT 总装方案 | 5. PPT 草稿 | `ppt-plan` | PPT 页数范围、结构模板、页面类型配比、整体风格、板书/练习/探究安排 | 节点产物 JSON/摘要、用户态 PPT 子状态截图；至少能说明“结构方案已确认” |
| PPT 分支第 3 步：PPT 页面脚本 | 5. PPT 草稿 | `ppt-script` | 逐页脚本：每页讲法、学生动作、页面类型、主视觉、数学内容、分区、衔接、信息密度、教师备注 | 逐页脚本证据；抽样页包含 PRD 13 字段或其用户态等价信息；逐页审查/数学准确性结果另列证据 |
| PPT 分支第 4A 步：PPT 视觉资产 | 5. PPT 草稿 | `ppt-assets` | 每页待生图清单、真实生活场景标签、角色字典引用、视觉资产状态、可替换素材 | 资产清单、图片/占位图文件或任务状态、合规红线检查；未真实生图时必须标注 placeholder |
| PPT 分支第 7 步：ppt-master 生成 PPTX | 5. PPT 草稿，最终下载在 7. 最终交付 | `pptx-generation` / runtime 可见 `pptx_artifact` | 可下载 PPTX、文件名、生成时间、PPT 媒体/可编辑层说明 | PPTX 文件存在、下载返回、必要时页面或文件检查；真实 PPT 主链路未专项通过时不得宣称正式 PPT 质量通过 |
| 视频分支第 4B 步：导入视频文稿 | 6. 视频生成 | `video-script` | 已确认课程锚点、视频类型、时长、旁白正文、禁用清单 | 文稿节点产物、课程锚点一致性、用户可回看/编辑证据 |
| 视频分支第 4C 步：导入视频剧本 | 6. 视频生成 | `video-screenplay`；旧 `workflow.ts` 未列入 14 节点但工作区聚合已引用，后续应作为底层执行节点对齐 | 分场剧本、场次、时长、场景描述、角色引用、旁白 | 剧本节点产物；分场数量和时长合理；不提前讲知识点 |
| 视频分支第 5B 步：导入视频资产 | 6. 视频生成 | `video-assets` | 首帧方向、参考图、角色/场景素材、配音/音乐/字幕资产清单、图片任务状态 | 首帧或 placeholder 资产证据；真实图片 smoke 未通过时必须写明 placeholder 或阻塞 |
| 视频分支第 6 步：分镜 + 小云雀提示词 | 6. 视频生成 | `storyboard` | 逐镜头表、镜头编号、时长、画面主体、旁白切片、模型 prompt、数学点 | 分镜节点产物；镜头级可回看；prompt 只在用户态必要摘要中展示，完整诊断进开发诊断 |
| 视频分支第 8 步：视频生成 + 中文配音 + 拼接 | 6. 视频生成，最终下载在 7. 最终交付 | `video-generation` / 历史 runtime 可含 `video_clip_generation`、`final_video` | clip 状态、失败段局部重试、中文 TTS、字幕、合成 MP4、下载入口 | fake/placeholder 下可证明任务、占位文件和下载；真实视频必须另有 submit/query/download/clip/ffprobe 或浏览器证据；provider 不可用只能记阻塞 |
| 收尾：最终交付门禁 | 7. 最终交付 | `final-delivery`；同时汇总 `pptx-generation`、`video-generation`、教案节点、反馈节点 | 教案、PPTX、导入视频、逐页讲稿、检查清单、反馈入口、项目归档状态 | 交付清单、下载文件、反馈弹窗、红线扫描、console；真实 PPT/视频未专项通过时必须显示未完成或待验证 |

说明：

- `project-meta`、`visual-contract`、`character-dict` 是后端/用户态契约中的节点名；`apps\web\src\lib\workflow.ts` 当前只静态列出 `project-config`，这属于执行层历史差异，不影响本裁决。
- `lesson-plan-final` 不作为新增用户态步骤；下一阶段若继续保留，应归入“教案生成”的回看/修订子状态或“最终交付”的教案终稿检查。
- `video-screenplay` 已被工作区用户态聚合引用，但旧 `workflow.ts` 未静态列出。后续前后端若修节点定义，应统一到底层 manifest 命名，但本轮不改代码。

## 4. PPT 分支表达方式

PPT 分支在用户态 7 步中统一归入“PPT 草稿”，但验收不得只看一个聚合卡片。该用户态步骤内必须保留四个子门禁：

| 子门禁 | 对应 PRD | 对应节点 | 必要证据 |
|---|---|---|---|
| 结构方案 | 第 2 步 PPT 总装方案 | `ppt-plan` | 页数、结构模板、页面类型配比、视觉风格 |
| 逐页脚本 | 第 3 步 PPT 页面脚本 | `ppt-script` | 抽样页逐页脚本、数学内容、学生动作、板书/练习/探究安排 |
| 视觉资产 | 第 4A 步 PPT 视觉资产 | `ppt-assets` | 待生图清单、角色字典引用、合规检查、图片或 placeholder 状态 |
| PPTX 文件 | 第 7 步 ppt-master 生成 PPTX | `pptx-generation` / `pptx_artifact` | PPTX 文件存在、可下载、必要时文件结构或截图检查 |

封板约束：

- 下一阶段 fake/placeholder 用户态封板只要求 PPT 子状态可被用户理解、PPTX placeholder 或已存在 artifact 不冒充真实质量。
- 真实 PPT 主链路封板必须另起专项覆盖逐页审查、视觉资产、PPTX 下载和文件质量；不能由 T140/T141 或本地 placeholder 下载替代。

## 5. 视频分支表达方式

视频分支在用户态 7 步中统一归入“导入视频方案”和“视频生成”两步：

- “导入视频方案”承接 PRD 第 1.5 步，重点验收独立创意、课程锚点和候选/终版区分。
- “视频生成”承接 PRD 第 4B、4C、5B、6、8 步，内部必须保留文稿、剧本、资产/首帧、分镜、clip/TTS/合成五类子状态。

| 子门禁 | 对应 PRD | 对应节点 | 必要证据 |
|---|---|---|---|
| 文稿 | 第 4B 步 | `video-script` | 旁白、时长、禁用清单、课程锚点一致 |
| 分场剧本 | 第 4C 步 | `video-screenplay` | 场次、场景、角色引用、旁白 |
| 资产与首帧 | 第 5B 步 | `video-assets` | 首帧/参考图/图片任务/placeholder 状态 |
| 分镜 | 第 6 步 | `storyboard` | 镜头编号、时长、画面主体、旁白切片、prompt |
| clip、TTS、合成 | 第 8 步 | `video-generation` / `video_clip_generation` / `final_video` | clip task、局部重试、TTS 音频、字幕、合成 MP4、下载 |

封板约束：

- fake/placeholder 下可以封板“用户态流程可走通、占位产物不冒充真实成片、失败提示可懂”。
- 真实视频 provider 未恢复时，只能记录 provider 阻塞，不得阻塞本地主流程，也不得宣称真实视频通过。
- 单段 10 秒素材不得冒充终版；多 clip、中文 TTS、字幕、拼接和局部重试必须进入真实视频专项。

## 6. 最小封板门禁

### 6.1 下一阶段必须先跑：fake/placeholder + 浏览器用户态门禁

以下门禁是下一阶段最小封板前置，建议作为 T009 的第一批执行或后续实现任务完成后的回归：

| 门禁 | 最小要求 | 证据 |
|---|---|---|
| 文档冷启动一致性 | 范围、非范围、变量名、T140/T141 边界无冲突 | 文档核对表 |
| fake/placeholder API 主链路 | 创建项目、教材内容、教案、导入视频方案、PPT 草稿、视频生成、最终交付至少状态可推进或可解释锁定 | HTTP JSON、manifest、日志摘要 |
| Web 真实 API 模式基础 | 登录、首页、新建项目、工作区能进入同一项目，不混用 mock 业务状态 | 浏览器截图、network、console |
| 7 步用户态导航 | 已完成可回看、当前可操作、未解锁不误入 | DOM 扫描、截图 |
| 普通界面红线扫描 | 工作区开发诊断前零命中；新建/首页另扫 API/mock/demo/token 等产品语言风险 | `browser-redline-scan-main.json` 类证据 |
| 教材页段和下载代理 | 页段 PDF、PPTX/MP4 placeholder 下载走后端代理，不暴露本地 storage 路径 | URL 扫描、GET 响应、文件 hash |
| 错误可懂 | 上游未确认、provider placeholder、下载缺失等错误转成用户下一步动作 | 浏览器截图、HTTP 错误样本 |
| 防误提交与密钥边界 | `.env*`、storage、SQLite、logs、真实产物和私有 skill env 不被跟踪或打包 | `git status`、ignore 检查、上下文清单 |
| 权限默认策略核验 | 本地空 token 放行边界、配置 token 后拒绝错误 token，admin 未配置不可误开放 | HTTP 状态表 |

这些门禁通过后，只能声明“v1 fake/placeholder + 浏览器用户态主流程达到下一阶段封板口径”。不得外推为真实 provider、真实视频、真实 PPT、生产权限、多浏览器或上线通过。

### 6.2 后置专项

以下内容不进入最小封板前置，必须另起专项：

- 真实文本 provider smoke。
- 真实图片 provider smoke。
- 真实视频 provider smoke 和完整多 clip 主线。
- 真实 TTS smoke。
- PPT 主链路真实验收：逐页审查、视觉资产、PPTX 文件质量。
- 正式 Dockerfile/compose 冷启动、storage volume、备份恢复和回滚。
- 生产级 JWT/RBAC/session、多租户、用户态 bundle 隔离。
- Edge/Firefox/移动端断点和性能压测。
- 任意教材泛化、真实 MinerU CLI/provider、全教材库后台。

## 7. 真实 provider 分离泳道

真实 provider 不作为 fake/placeholder 用户态主流程的前置阻塞。真实能力按类型分离触发，失败只记录阻塞和脱敏错误，不拖垮本地封板。

| 泳道 | 触发条件 | 通过证据 | 阻塞记录方式 |
|---|---|---|---|
| 文本 provider | 用户明确要求真实文本演示；或账号、额度、模型权限已确认；或进入真实教案/脚本质量专项 | 脱敏模式、HTTP、节点产物、manifest 状态、错误重试记录 | 记录 provider 名、模式、脱敏错误码、节点、是否可重试；不记录密钥 |
| 图片 provider | 需要验证首帧/视觉资产真实生成；图片账号、额度、模型权限确认 | task submit/query/download、图片文件、合规检查 | 记录 task 状态、脱敏错误、影响的 PPT/视频资产节点 |
| 视频 provider | 视频账号池/额度/模型权限恢复；或用户明确要求真实视频 smoke；优先单 clip submit/query/download | submit/query/download、clip 文件、必要时 ffprobe、局部重试证据 | 若 429/权限/模型不可用，标为真实视频 provider 阻塞；不得阻塞 fake/placeholder 用户态封板 |
| TTS provider | 需要真实中文旁白验证；TTS 账号和音色可用 | 音频文件、时长、ffprobe 或播放检查、下载状态 | 记录音色/模式、脱敏错误、是否影响最终合成专项 |

真实视频 provider 未恢复时的裁决：

1. `video-generation` 可以在 fake/placeholder 下继续验证状态、用户态文案、失败提示、占位下载和红线。
2. 真实视频专项记录为 `BLOCKED_BY_PROVIDER` 或等价状态，附脱敏错误、发生节点、复跑条件。
3. 不允许把真实视频阻塞升级为本地主流程不通过，除非普通 UI 把 placeholder 冒充真实成片、泄露密钥/路径或给出错误承诺。

## 8. 后续任务拆分建议

给主 Codex 回收后拆任务使用，不超过 6 条：

1. 前端：按本文映射表给工作区 7 步补 PPT 和视频子状态文案，不改底层大流程；任何触及工作区普通区的改动后必须复扫红线。
2. 前端：把首页、新建项目、工作区普通路径中的 API/mock/demo/provider 等模式词替换成教师可懂产品语言，工程词保留到开发诊断或管理员区。
3. 后端：补齐或稳定 workspace 用户态契约，使每个用户态步骤都能返回当前动作、锁定原因、回看摘要、子门禁状态和开发诊断分离字段。
4. 后端：对 `video-screenplay`、`lesson-plan-final`、`pptx_artifact` 等历史命名给出 manifest 兼容口径，避免前端 7 步与 PRD 语义漂移。
5. 测试：按本文抽取最小封板用例，先跑 fake/placeholder + 浏览器用户态 + 红线 + 下载代理，不等待真实 provider。
6. 测试：建立真实 provider 分离 smoke 报告模板，分别记录文本、图片、视频、TTS 的触发条件、脱敏错误和复跑条件。

## 9. 不包含范围

本裁决文档不代表：

- v1 E2E 已执行或通过。
- 真实 provider 已通过。
- 生产权限、JWT/RBAC/session、多租户或用户态 bundle 隔离已通过。
- 多浏览器、移动端或性能验收已通过。
- PPT 主链路真实验收已通过。
- 真实视频主链路、真实 TTS、字幕、拼接或最终 MP4 质量已通过。
- 任意教材泛化、真实 MinerU CLI/provider 或全教材库后台已通过。

T140/T141 的封板范围仍只限 T138/T139 用户态红线专项。下一阶段若修改首页、新建项目或工作区普通教师主界面，必须重新提供浏览器或 DOM 级用户态证据。
