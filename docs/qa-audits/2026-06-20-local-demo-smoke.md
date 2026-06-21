# ShanHaiEdu 本地演示轻量冒烟报告

- 日期：2026-06-20
- 角色：测试工程师
- 结论：本地演示口径下判定为【可演示】
- 范围：仅本地 API + Web 真实 API 模式 + fake provider 最小链路；不作为上线验收结论。

## 测试环境

- API：`http://127.0.0.1:8001`
- Web：`http://127.0.0.1:3002`
- Provider：fake
- Storage：`storage-smoke-fake`
- Web 模式：真实 API 模式，`NEXT_PUBLIC_DEMO_MODE=false`，API Base 指向 `http://127.0.0.1:8001`
- CORS：本轮显式允许 `http://localhost:3002` 和 `http://127.0.0.1:3002`

## 验证结果总览

| 编号 | 验证项 | 结果 | 标记 | 证据 |
|---|---|---|---|---|
| 1 | API 可启动，`/health` 正常 | 通过 | 可演示 | `GET /health` 返回 `ok=true`、`status=ok`、`workflow_version=1.0.0` |
| 2 | Web 可启动 | 通过 | 可演示 | `GET http://127.0.0.1:3002` 返回 200 |
| 3 | 前端真实 API 模式下能创建项目 | 通过 | 可演示 | 浏览器创建项目 `UI冒烟-8001-clean` 后自动进入项目工作区 |
| 4 | 项目列表可刷新出来 | 通过 | 可演示 | 首页项目概览显示 `UI冒烟-8001-clean`，无 `Failed to fetch` |
| 5 | 工作区能显示 manifest / 节点状态 | 通过 | 可演示 | 工作区显示 `10 个后端 manifest 节点`，当前阶段为 `教材解析与核验` |
| 6 | 至少一个 fake provider 生成/确认链路能跑通 | 通过 | 可演示 | UI 点击 `生成草稿` 后出现 `阶段产出` 和 `待确认`；点击 `确认通过` 后进入 `公开课教案`，提示 `后端 manifest 已刷新` |
| 7 | 浏览器控制台无阻断性 error | 通过 | 可演示 | 浏览器 `error/warn` 日志为空 |

## 过程证据

### API 直接链路

使用 fake API 直接跑通：

1. 创建项目。
2. 查询项目列表。
3. 以 `.txt` 教材文件上传。
4. 生成 `textbook_parse`，状态为 `needs_review`。
5. approve `textbook_parse`，状态为 `approved`。
6. 生成 `lesson_plan`，状态为 `needs_review`。
7. 查询 manifest，得到 `textbook_parse=approved`、`lesson_plan=needs_review`。

本轮直接链路项目：`proj_a39e25c832f2`。

### 浏览器真实 API 链路

浏览器在 `http://127.0.0.1:3002` 完成：

1. 首页真实 API 项目列表可读，无项目列表失败提示。
2. 新建项目 `UI冒烟-8001-clean`。
3. 自动进入工作区。
4. 工作区显示 manifest 节点和当前节点详情。
5. 点击 `生成草稿` 触发 fake provider 生成教材解析。
6. 点击 `确认通过` 后 manifest 刷新，当前阶段推进到 `公开课教案`。
7. 回到首页后项目概览显示 `UI冒烟-8001-clean`。

## 可演示

- API 本地 fake 模式可启动并通过健康检查。
- Web 本地真实 API 模式可启动。
- 前端可通过真实 API 创建项目、进入工作区、刷新项目列表。
- 工作区可展示 manifest / 节点状态。
- fake provider 教材解析节点可由 UI 触发生成并确认，确认后 manifest 推进到下游节点。
- 浏览器控制台本轮无阻断性 error/warn。

## 阻塞演示

- 本轮未发现阻塞本地演示的问题。

## 上线前再修

### 一般：前端新建项目第 2 步仍是前端演示解析，不等同于真实教材上传链路

- 分类：前端 / 接口联调
- 复现步骤：进入新建项目第 2 步，填写教材内容并点击 `开始解析`。
- 现象：页面使用前端 mock 解析结果推进表单；真实 API 的教材上传与 `textbook_parse/generate` 是进入工作区后点击 `生成草稿` 才触发。
- 影响范围：不阻塞本地演示，但会让“上传教材 -> 生成 textbook_parse”的真实链路在 UI 语义上分裂。
- 标准修复方案：前端第 2 步接入 `uploadProjectTextbook`，并明确“上传/解析/确认”与工作区节点状态之间的关系；避免用户以为第 2 步已经真实完成后端教材解析。

### 优化建议：默认 CORS 只包含 3000，演示使用 3002 时需显式配置

- 分类：环境配置 / 后端
- 复现步骤：API 使用默认 CORS 启动，Web 使用 3002 访问真实 API。
- 现象：`OPTIONS /projects` 对 `Origin: http://127.0.0.1:3002` 返回 `Disallowed CORS origin`；显式配置 3002 后通过。
- 影响范围：不阻塞按文档配置后的本地演示，但临时换端口会出现浏览器跨域失败。
- 标准修复方案：在本地演示 Runbook 中写明 3002 端口时必须配置 CORS；或提供本地 dev profile 覆盖常用端口。

### 优化建议：首页项目卡进度在刚回首页后仍显示项目配置 0%

- 分类：前端 / 状态展示
- 复现步骤：工作区确认 `textbook_parse` 后回到首页。
- 现象：首页项目概览能显示新项目，但卡片仍显示 `当前阶段：项目配置`、`总进度 0%`，与工作区已推进到 `公开课教案` 不一致。
- 影响范围：不阻塞演示主链路，但会影响观众对状态推进的理解。
- 标准修复方案：首页列表卡片应在读取项目列表后同步 manifest，或后端列表接口返回当前阶段与进度摘要。

## 未覆盖范围

- 不覆盖真实 Minimax / 章鱼哥 provider。
- 不覆盖生产鉴权、角色权限、多人数据隔离。
- 不覆盖正式部署、Docker、云端、备份恢复。
- 不覆盖多浏览器、多分辨率兼容。
- 不覆盖性能压测和并发稳定性。

---

# T017 本地演示轻量回归记录

- 日期：2026-06-20
- 角色：测试工程师
- 任务：T017，本地演示体验回归
- 结论：本地演示口径下判定为【可演示】
- 范围：只验证 T015 首页 manifest 同步、T016 新建项目第 2 步语义、真实 API 最小链路；不作为上线验收结论。

## 回归环境

- API：`http://127.0.0.1:8027`
- Web：`http://127.0.0.1:3027`
- Provider：fake
- Storage：`storage-t017-regression`
- Web 模式：真实 API 模式，API Base 指向 `http://127.0.0.1:8027`
- CORS：本轮显式允许 `http://localhost:3027` 和 `http://127.0.0.1:3027`

## 回归结果总览

| 编号 | 验证项 | 结果 | 标记 | 证据 |
|---|---|---|---|---|
| 1 | API fake 模式可启动，`/health` 正常 | 通过 | 可演示 | `GET /health` 返回 `ok=true`、`status=ok`、`workflow_version=1.0.0` |
| 2 | Web 真实 API 模式可启动 | 通过 | 可演示 | `GET http://127.0.0.1:3027` 返回 200 |
| 3 | 创建项目后进入工作区 | 通过 | 可演示 | 浏览器创建 `T017-本地回归-255800` 后进入项目工作区，显示 `10 个后端 manifest 节点` |
| 4 | 生成并确认 `textbook_parse` | 通过 | 可演示 | 点击 `生成草稿` 后显示 `待确认` 与 `阶段产出`；点击 `确认通过` 后推进到 `公开课教案` |
| 5 | 返回首页后项目卡片阶段和进度与工作区一致 | 通过 | 可演示 | 工作区为 `公开课教案 / 30% / 进入「公开课教案」`；首页“继续工作”和“项目概览”同样显示 `公开课教案 / 30% / 进入「公开课教案」` |
| 6 | 新建项目第 2 步不会误导用户以为已完成后端真实解析 | 通过 | 可演示 | 第 2 步显示 `教材内容准备`、`生成教材预览`、`确认用于创建项目`，并说明创建后上传教材、进入工作区点击 `生成草稿` 才触发后端真实解析 |
| 7 | 浏览器控制台无阻断性 error | 通过 | 可演示 | 浏览器 `error/warn` 日志为空 |

## 关键过程证据

- 回归项目：`T017-本地回归-255800`
- 后端项目 ID：`proj_e80816eae33f`
- 后端 manifest 复核：`textbook_parse=approved`，`lesson_plan=not_started`，节点数 `10`
- 工作区确认后状态：当前阶段 `公开课教案`，总进度 `30%`，下一步动作 `进入「公开课教案」`
- 首页项目概览卡片：当前阶段 `公开课教案`，总进度 `30%`，下一步动作 `进入「公开课教案」`
- 首页继续工作卡片：当前阶段 `公开课教案`，总进度 `30%`，下一步动作 `进入「公开课教案」`

## 可演示

- API fake 模式和 Web 真实 API 模式可在本地隔离端口启动。
- 新建项目第 2 步已从“解析”语义收口为“教材内容准备 / 教材预览”，不会把前端预览包装成后端真实解析完成。
- 创建项目后可进入工作区，工作区能展示后端 manifest 和节点详情。
- `textbook_parse` 可由 UI 触发 fake provider 生成并确认。
- T015 首页状态同步回归通过：返回首页后阶段、进度、下一步动作与工作区一致。
- 浏览器控制台无阻断性 `error/warn`。

## 阻塞演示

- 本轮未发现阻塞本地演示的问题。

## 上线前再修

### 优化建议：真实 API 模式首页会为项目列表逐个拉取 manifest

- 分类：前端 / 接口性能
- 复现步骤：真实 API 模式进入首页，加载项目列表。
- 现象：前端在 `GET /projects` 后对列表中的每个项目补拉一次 `GET /projects/{project_id}/manifest`，用于同步阶段、进度和下一步动作。
- 影响范围：本地演示数据量小，不阻塞；上线后项目数量增大时可能造成请求放大。
- 标准修复方案：后端列表接口补充当前阶段、进度和下一步摘要，或前端分页/懒加载 manifest。

### 优化建议：新建项目第 2 步仍是教材预览，不是正式上传版本管理

- 分类：前端 / 产品体验
- 复现步骤：新建项目第 2 步填写教材内容并生成教材预览。
- 现象：当前文案已避免误导，但该步骤仍不是正式文件上传、替换、版本管理和真实解析闭环。
- 影响范围：不阻塞本地演示；上线前若要支持真实教师教材文件，需要补完整上传和版本管理体验。
- 标准修复方案：上线前设计教材文件上传、替换、预览、解析状态、版本回滚与错误提示闭环。

---

# T021 公开课教案节点本地端到端演示轻量回归记录

- 日期：2026-06-20
- 角色：测试工程师
- 任务：T021，公开课教案节点端到端演示回归
- 结论：本地演示口径下判定为【可演示】
- 范围：只验证 T019/T020 后的 fake provider 本地端到端演示链路；不作为上线验收结论。

## 回归环境

- API：`http://127.0.0.1:8061`
- Web：`http://127.0.0.1:3061`
- Provider：fake
- Storage：`storage-t021-regression`
- Web 模式：真实 API 模式，API Base 指向 `http://127.0.0.1:8061`
- CORS：本轮显式允许 `http://127.0.0.1:3061`

## 回归结果总览

| 编号 | 验证项 | 结果 | 标记 | 证据 |
|---|---|---|---|---|
| 1 | API fake 模式启动，`/health` 正常 | 通过 | 可演示 | `GET /health` 返回 `ok=true`、`status=ok`、`workflow_version=1.0.0` |
| 2 | Web 真实 API 模式启动 | 通过 | 可演示 | `GET http://127.0.0.1:3061` 返回 200 |
| 3 | 创建项目 | 通过 | 可演示 | 浏览器创建 `T021-教案回归-336362` 后进入工作区，显示 `10 个后端 manifest 节点` |
| 4 | 生成并确认 `textbook_parse` | 通过 | 可演示 | `textbook_parse` 生成后显示 `待确认`，确认后工作区推进到 `公开课教案 / 30%` |
| 5 | 生成 `lesson_plan` | 通过 | 可演示 | 点击生成后页面显示 `公开课教案编辑`、`保存教案`、`待确认` |
| 6 | 编辑 `lesson_plan` 内容并保存 | 通过 | 可演示 | 向教案内容写入 `t021_smoke_edit_336362`，点击 `保存教案` 后显示 `已保存到后端` |
| 7 | 刷新或重新读取节点后，编辑内容仍存在 | 通过 | 可演示 | 后端 `GET /projects/{project_id}/nodes/lesson_plan` 复核 `containsEditMarker=true` |
| 8 | 确认 `lesson_plan` | 通过 | 可演示 | 点击 `确认通过` 后后端节点状态为 `approved` |
| 9 | manifest 推进到下一节点 | 通过 | 可演示 | manifest 显示 `textbook_parse=approved`、`lesson_plan=approved`、`intro_selection=not_started` |
| 10 | 首页和工作区状态一致 | 通过 | 可演示 | 工作区和首页“继续工作/项目概览”均显示 `视频导入选择 / 40% / 进入「视频导入选择」` |
| 11 | 浏览器控制台无阻断性 error/warn | 通过 | 可演示 | 浏览器 `error/warn` 日志为空 |

## 关键过程证据

- 回归项目：`T021-教案回归-336362`
- 后端项目 ID：`proj_91cc9fcc3318`
- 编辑持久化 marker：`t021_smoke_edit_336362`
- 后端复核结果：`lessonStatus=approved`，`containsEditMarker=true`
- 最终 manifest：`textbook_parse=approved`，`lesson_plan=approved`，`intro_selection=not_started`
- 最终演示状态：当前阶段 `视频导入选择`，总进度 `40%`，下一步动作 `进入「视频导入选择」`

## 可演示

- API fake 模式和 Web 真实 API 模式可在本地隔离端口启动。
- 创建项目后可进入工作区，并读取后端 manifest。
- `textbook_parse` 可由 UI 触发 fake provider 生成并确认。
- `lesson_plan` 可由 UI 触发生成，轻量编辑后保存到后端，重新读取节点可看到编辑内容仍存在。
- `lesson_plan` 确认后 manifest 推进到 `intro_selection`，首页和工作区展示一致。
- 浏览器控制台无阻断性 `error/warn`。

## 阻塞演示

- 本轮未发现阻塞本地端到端演示的问题。

## 上线前再修

### 严重：`lesson_plan/edit` 仍缺少正式 schema 校验

- 分类：后端 / 接口
- 复现步骤：调用 `POST /projects/{project_id}/nodes/lesson_plan/edit`，提交任意 dict 结构。
- 现象：当前接口按本地演示口径接受完整 content 并写入新版本，未对公开课教案必填字段、字段类型和业务约束做严格校验。
- 影响范围：不阻塞本地 fake 演示；上线后可能写入不完整或错误结构的教案数据，影响后续导入方案、视频文稿等下游节点。
- 标准修复方案：补充 `lesson_plan` 专用 schema、必填字段校验、字段级错误响应和前端错误展示；红线测试覆盖缺字段、错类型和空内容。

### 一般：公开课教案编辑器仍是轻量文本/JSON 演示形态

- 分类：前端 / 界面交互
- 复现步骤：生成 `lesson_plan` 后进入结果页编辑内容。
- 现象：当前编辑器适合本地演示保存能力，不是教师可长期使用的结构化或富文本教案编辑体验。
- 影响范围：不阻塞演示；上线前会影响教师编辑效率、可读性和误操作恢复。
- 标准修复方案：按正式教案字段拆分编辑区，补字段说明、保存状态、错误提示、撤销/恢复或版本提示。

### 优化建议：首页真实 API 模式仍存在 manifest fan-out

- 分类：前端 / 接口性能
- 复现步骤：真实 API 模式进入首页并加载项目列表。
- 现象：前端仍会为项目列表逐个补拉 manifest，用于同步阶段、进度和下一步动作。
- 影响范围：本地演示数据量小，不阻塞；项目数量增长后可能造成请求放大。
- 标准修复方案：后端列表接口补充当前阶段、进度和下一步摘要，或前端分页/懒加载 manifest。

### 优化建议：本轮未覆盖上线级质量项

- 分类：测试范围 / 环境配置
- 复现步骤：本轮按本地 fake provider 演示口径执行。
- 现象：未覆盖真实 Minimax provider、正式鉴权、角色权限、多人数据隔离、部署、多浏览器、多分辨率、性能压测和异常网络。
- 影响范围：不影响本地演示结论；不能据此判断上线发布通过。
- 标准修复方案：进入上线验收前单独建立完整 E2E、契约、权限、安全、部署和性能测试门禁。

---

# T025/T030 本地 fake 视频生成端到端演示轻量回归记录

- 日期：2026-06-20
- 角色：测试工程师
- 任务：T025 视频导入选择小链路回归；T030 完整本地 fake 视频生成链路回归
- 结论：本地演示口径下判定为【可演示】
- 范围：只验证本地 fake provider + Web 真实 API 模式；不测真实 provider、不做上线验收、不测部署、不测正式鉴权。

## 回归环境

- API：`http://127.0.0.1:8091`
- Web：`http://127.0.0.1:3091`
- Provider：fake
- Storage：`storage-t025-t030-regression`
- Web 模式：真实 API 模式，API Base 指向 `http://127.0.0.1:8091`
- CORS：本轮显式允许 `http://localhost:3091` 和 `http://127.0.0.1:3091`
- 回归项目：`T025-T030-视频链路-760635`
- 后端项目 ID：`proj_8067c6d39b21`

## T025 回归结果总览

| 编号 | 验证项 | 结果 | 标记 | 证据 |
|---|---|---|---|---|
| 1 | API fake 模式启动，`/health` 正常 | 通过 | 可演示 | `GET /health` 返回 `ok=true`、`status=ok`、`workflow_version=1.0.0` |
| 2 | Web 真实 API 模式启动 | 通过 | 可演示 | `GET http://127.0.0.1:3091` 返回 200 |
| 3 | 创建项目并进入工作区 | 通过 | 可演示 | 浏览器创建 `T025-T030-视频链路-760635`，工作区显示 `10 个后端 manifest 节点` |
| 4 | 教材解析生成/确认 | 通过 | 可演示 | `textbook_parse` 生成后显示 `待确认`，确认后推进到 `公开课教案 / 30%` |
| 5 | 教案生成/保存/确认 | 通过 | 可演示 | `lesson_plan` 生成后显示 `公开课教案编辑`；写入 `t025_t030_lesson_edit_913856` 后显示 `已保存到后端`，确认后推进到 `视频导入选择 / 40%` |
| 6 | 视频导入选择生成 | 通过 | 可演示 | 页面显示 `视频导入候选方案`，包含科普类、应用类、故事类 3 类候选 |
| 7 | 视频导入选择选择/保存/确认 | 通过 | 可演示 | 改选故事类后点击 `保存选择`，页面显示 `已保存到后端`；确认后推进到 `视频剧本 / 50%` |
| 8 | 首页和工作区状态同步 | 通过 | 可演示 | 工作区为 `视频剧本 / 50% / 进入「视频剧本」`；首页“继续工作”和“项目概览”同样显示 `视频剧本 / 50% / 进入「视频剧本」` |

## T030 回归结果总览

| 编号 | 验证项 | 结果 | 标记 | 证据 |
|---|---|---|---|---|
| 1 | 创建项目 → 教材解析 → 教案 → 视频导入选择 | 通过 | 可演示 | 沿用 T025 同一真实 UI 链路，前置节点均 approved |
| 2 | 视频剧本生成/编辑/确认 | 通过 | 可演示 | 写入 `script_marker_033769` 并确认后推进到 `视频分场剧本 / 60%` |
| 3 | 视频分场剧本生成/编辑/确认 | 通过 | 可演示 | 写入 `screenplay_marker_044914` 并确认后推进到 `视频资产 / 70%` |
| 4 | 视频资产生成/编辑/确认 | 通过 | 可演示 | 写入 `asset_marker_057287` 并确认后推进到 `分镜脚本 / 80%` |
| 5 | 分镜脚本生成/编辑/确认 | 通过 | 可演示 | 写入 `storyboard_marker_070203` 并确认后推进到 `最终视频 / 90%` |
| 6 | `final_video` fake 任务生成 | 通过 | 可演示 | 点击 `创建视频任务` 后页面显示 `fake 视频生成任务`、`clip 数量 6`、`任务数量 6` |
| 7 | tasks 查询 | 通过 | 可演示 | 后端 `/projects/proj_8067c6d39b21/tasks` 返回 6 个 `video_clip_generation` task，状态集合为 `generated` |
| 8 | fake 输出路径展示 | 通过 | 可演示 | 页面显示 `clips/shot_01.mp4` 到 `clips/shot_06.mp4`；后端 `final_video` 节点 content 同样返回 6 个 clips |
| 9 | 首页和工作区状态同步 | 通过 | 可演示 | 工作区和首页“继续工作/项目概览”均显示 `最终视频 / 90% / 进入「最终视频」` |
| 10 | 浏览器控制台无阻断性 error/warn | 通过 | 可演示 | 浏览器 `error/warn` 日志为空 |

## 后端证据

- API `/health`：`ok=true`，`status=ok`，`workflow_version=1.0.0`。
- API 访问日志覆盖：`GET /projects`、`POST /projects`、`POST /textbook`、各节点 `generate/edit/approve`、`GET /manifest`、`POST /nodes/final_video/generate`、`GET /tasks`，关键请求均返回 200。
- 后端 manifest 复核：
  - `project_meta=approved`
  - `project_config=approved`
  - `textbook_parse=approved`
  - `lesson_plan=approved`
  - `intro_selection=approved`
  - `intro_video_script=approved`
  - `intro_video_screenplay=approved`
  - `intro_video_asset=approved`
  - `storyboard=approved`
  - `final_video=running`
- 后端节点复核：
  - `lesson_plan` 内容包含编辑 marker `t025_t030_lesson_edit_913856`
  - `intro_selection.primary_design_id=design_story_01`
  - `final_video.content.clip_count=6`
  - `final_video.content.clips` 包含 `shot_01` 到 `shot_06`，状态均为 `generated`
- 后端 tasks 复核：
  - `taskCount=6`
  - `taskTypes=video_clip_generation`
  - `taskStatuses=generated`
  - 单个任务示例：`task_5c30919e1c9c`，`node_id=final_video`，`payload.shot_id=shot_01`，`result.download_path=clips/shot_01.mp4`

## 前端与控制台证据

- Web 真实 API 模式访问：`GET http://127.0.0.1:3091` 返回 200。
- T025 首页同步证据：项目卡片显示 `当前阶段：视频剧本`，`总进度 50%`，下一步 `进入「视频剧本」`。
- T030 最终页面证据：`fake 视频生成任务`、`clip 数量 6`、`任务数量 6`、6 个 task 均为 `generated`，fake 输出从 `clips/shot_01.mp4` 到 `clips/shot_06.mp4`。
- T030 首页同步证据：项目卡片显示 `当前阶段：最终视频`，`总进度 90%`，下一步 `进入「最终视频」`。
- 浏览器控制台：本轮 `error/warn` 日志为空。
- Web dev server 提示：Next.js dev server 输出 `Cross origin request detected from 127.0.0.1 to /_next/* resource`，属于 Next 开发服务器未来版本配置提示，不是 ShanHaiEdu 应用阻断性错误；上线前可补 `allowedDevOrigins` 或固定 localhost 访问口径。

## 可演示

- T025：视频导入选择小链路可演示，覆盖创建项目、教材解析确认、教案生成/保存/确认、视频导入选择生成/选择/保存/确认和首页/工作区同步。
- T030：完整本地 fake 视频生成链路可演示，覆盖到 `final_video` fake 任务创建和 `/tasks` 查询。
- fake 模式下最终视频节点清楚表达“只证明已创建视频生成任务和 clip 记录，不承诺真实成片质量”，未误导为真实 MP4 成片验收。
- 浏览器控制台无阻断性 `error/warn`。

## 阻塞演示

- 本轮未发现阻塞本地演示的问题。

## 上线前再修

### 严重：视频链节点仍缺少节点级 schema 校验

- 分类：后端 / 接口
- 复现步骤：对 `intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 等节点调用 `/edit`，提交任意 dict。
- 现象：当前本地演示链路接受完整 JSON 内容写入，未按节点 schema 做必填字段、类型、引用关系和业务约束校验。
- 影响范围：不阻塞 fake 演示；上线后可能污染下游视频任务输入，造成脚本、资产、分镜和生成任务不一致。
- 标准修复方案：为每个视频链节点补 schema、字段级错误响应和前端错误提示；契约测试覆盖缺字段、错类型、空数组、非法引用和重复提交。

### 严重：`final_video` fake task 不代表真实视频生成质量

- 分类：后端 / Provider / 测试范围
- 复现步骤：fake provider 模式点击 `创建视频任务`。
- 现象：后端创建 6 个 `generated` 状态的 fake task 和 fake download path，但没有真实提交 provider、下载、拼接、音频核验或成片质量验收。
- 影响范围：只可用于本地演示“任务创建和查询链路”；不能作为真实视频上线依据。
- 标准修复方案：真实 provider 阶段补任务提交、轮询、失败重试、下载持久化、中文男声/英文音频拦截、视频拼接和人工验收门禁。

### 一般：视频链编辑器仍是轻量 JSON 演示形态

- 分类：前端 / 界面交互
- 复现步骤：进入视频剧本、分场剧本、视频资产、分镜脚本节点结果页。
- 现象：当前可编辑保存，但主要是文本/JSON 编辑器，不是教师可长期使用的结构化编辑体验。
- 影响范围：不阻塞本地演示；上线前影响教师可读性、编辑效率和误操作恢复。
- 标准修复方案：按节点拆字段化编辑区，补保存状态、字段校验、撤销/版本提示和可读预览。

### 优化建议：Next dev server 跨源提示需收口演示访问口径

- 分类：环境配置 / 前端
- 复现步骤：使用 `127.0.0.1:3091` 访问 Next dev server。
- 现象：dev server 输出 `Cross origin request detected from 127.0.0.1 to /_next/* resource`，当前不阻塞页面运行。
- 影响范围：不阻塞本地演示；未来 Next 版本可能需要显式配置 `allowedDevOrigins`。
- 标准修复方案：本地演示统一使用 `localhost` 访问 Web，或在 `next.config` 中补允许的 dev origins。

### 优化建议：首页真实 API 模式仍存在 manifest fan-out

- 分类：前端 / 接口性能
- 复现步骤：真实 API 模式返回首页加载项目列表。
- 现象：前端仍为项目列表补拉 manifest 以同步阶段、进度和下一步动作。
- 影响范围：本地单项目不阻塞；项目数量增长后会放大请求量。
- 标准修复方案：后端项目列表接口返回当前阶段、进度和下一步摘要，或前端分页/懒加载 manifest。
