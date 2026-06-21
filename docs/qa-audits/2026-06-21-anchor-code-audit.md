# T057 课程锚点后端实现状态排查

日期：2026-06-21  
角色：首席系统架构师  
范围：后端代码为主，前端只作为 `intro_selection` 是否可编辑的旁证。  
结论：**未达到课程锚点闭环验收**。当前系统能跑通旧版 E2E，但后端仍停留在 `anchor_to_lesson` 最小字段链路；新口径要求的“两层导入设计 + 用户确认 selected_anchor + 下游硬传递 + 末句/末帧锚点约束”尚未实现。

## 一、检查矩阵

| 检查项 | 状态 | 证据 | 判断 |
|---|---|---|---|
| `lesson_plan/generate` prompt 是否包含两层结构要求 | 缺失 | `apps/api/app/services.py:243-248` 只要求 `lesson_plan_markdown`、`intro_designs`，每个方案只含 `design_id/type/title/hook/anchor_to_lesson/recommend_score/risk_note` | 未接入 `workflow/prompts/node_01_lesson_plan/deepseek.md:57-70` 的“独立创意 + 课堂接入”两层结构 |
| `lesson_plan/generate` 是否要求 9 套且锚点各不相同 | 缺失 | `apps/api/app/services.py:247` 写死 3 个方案；`workflow/prompts/node_01_lesson_plan/deepseek.md:55` 要求 9 套，`workflow/prompts/node_01_lesson_plan/deepseek.md:133` 要求 9 套锚点不同 | 后端 prompt 与产品新口径不一致 |
| `lesson_plan` 归一化 fallback 是否产出新字段 | 缺失 | `apps/api/app/services.py:63-69` fallback 只生成 3 个 `_intro_design`；`apps/api/app/services.py:126-135` `_intro_design` 只含旧字段，且锚点为抽象套语 | fallback 会继续产生不合格锚点 |
| `intro_selection` 是否有 `selected_anchor` 字段 | 缺失 | `workflow/schemas/intro_selection.schema.json:6-25` required/properties 均无 `selected_anchor`；`apps/api/app/services.py:253-257` prompt 也不要求输出该字段 | 没有用户确认版课程锚点 |
| `intro_selection` 是否落盘 | 部分实现 | 后端通用写版本能力会保存任意 content：`apps/api/app/services.py:194-199`、`apps/api/app/store.py:218-236` | 如果前端手写 `selected_anchor` 可以随 JSON 一起保存，但后端没有 schema/prompt/校验保证 |
| `intro_selection` 是否前端可编辑 | 部分实现 | 前端可保存真实 API 可编辑节点：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:256-278`；选择 UI 只改 `primary_design_id/selected_design_ids/selection_reason`：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:1518-1527`；底部 JSON 可编辑：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:1586-1590` | 只能通过 JSON 手改，不是专门的课程锚点编辑控件 |
| R047 用户确认锚点非空是否实现 | 缺失 | 文档规则在 `workflow/rules.md:450-459`；后端 `validate_edit_content` 对 `intro_selection` 只校验 5 个旧字段：`apps/api/app/services.py:500-507` | approve/edit 都不会阻断空锚点 |
| `intro_video_script` prompt 是否接收 `selected_anchor` 作为硬输入 | 缺失 | 依赖包含 `intro_selection`：`apps/api/app/workflow_config.py:95-96`，上下文会加载依赖内容：`apps/api/app/services.py:163-166`；但 prompt 只泛称根据教案和已选导入方案生成：`apps/api/app/services.py:258-262` | 有依赖上下文底座，但没有硬输入字段和阻断规则 |
| `intro_video_script` 旁白末句是否要求体现锚点 | 缺失 | `apps/api/app/services.py:258-262` 未出现“最后一句/selected_anchor/课程锚点”；编辑校验只要求 `anchor_to_lesson` 非空：`apps/api/app/services.py:508-514` | R048 未实现，旁白可能偏离用户确认锚点 |
| `storyboard` prompt 是否要求末帧 subtitle 体现锚点 R049 | 缺失 | `apps/api/app/services.py:273-279` 只要求分镜字段、男声中文、禁止英文配音；`validate_edit_content` 未校验 subtitle：`apps/api/app/services.py:541-561`；`workflow/schemas/storyboard.schema.json:18-22` 甚至未把 `subtitle` 设为 required | R049 未实现 |
| `lesson_plan.schema.json` 是否包含两层结构新字段 | 缺失 | `workflow/schemas/lesson_plan.schema.json:26-34` 只包含旧字段，无 `video_theme`、`eye_catch_tag`、`classroom_entry_question`、`no_pre_teach`、`entry_position`、`recommend_reason` | schema 仍是旧版 |

## 二、关键缺口清单

### P1-1 lesson_plan 后端 prompt 与 schema 未升级到课程锚点新口径

- 影响：DeepSeek 即使可用，也会按旧契约生成 3 套导入方案，缺少 9 套、两层结构和课堂接入说明。
- 证据：
  - `apps/api/app/services.py:243-248`
  - `apps/api/app/services.py:292-294`
  - `workflow/schemas/lesson_plan.schema.json:26-34`
  - 对照新口径：`workflow/prompts/node_01_lesson_plan/deepseek.md:57-70`、`workflow/prompts/node_01_lesson_plan/deepseek.md:103-134`
- 后果：前端无法稳定展示“导入视频策划卡 + 课堂接入说明”，测试也无法用 schema 阻断旧结构。

### P1-2 `selected_anchor` 没有成为用户确认节点的正式字段

- 影响：用户最终确认的课程锚点没有结构化字段，后续视频脚本链不能知道哪个锚点是最终版。
- 证据：
  - `workflow/schemas/intro_selection.schema.json:6-25`
  - `apps/api/app/services.py:253-257`
  - `apps/api/app/services.py:500-507`
- 后果：当前链路只能依赖 LLM 自行从 `intro_selection` 和 `lesson_plan` 中理解锚点，无法保证一致。

### P1-3 R047/R048/R049 未在后端实现

- 影响：空锚点、过短锚点、旁白末句不落锚点、分镜末帧不体现锚点都不会被阻断或警告。
- 证据：
  - R047 文档规则：`workflow/rules.md:450-459`，后端只校验旧字段：`apps/api/app/services.py:500-507`
  - R048 文档规则：`workflow/rules.md:463-474`，后端 prompt/校验没有 `selected_anchor` 硬输入：`apps/api/app/services.py:258-262`、`apps/api/app/services.py:508-514`
  - R049 文档规则：`workflow/rules.md:476-487`，后端 storyboard prompt/校验不检查末帧 subtitle：`apps/api/app/services.py:273-279`、`apps/api/app/services.py:541-561`
- 后果：真实视频生成前缺少最关键的内容一致性门禁。

### P2-1 前端可编辑能力存在，但不是课程锚点专项编辑

- 影响：用户可以通过 JSON 改内容，但没有明确的“课程锚点确认/编辑”工作流，低可用且易漏填。
- 证据：
  - 可保存 JSON：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:256-278`
  - 选择卡片只更新选择字段，不写 `selected_anchor`：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:1518-1527`
  - JSON 编辑入口：`apps/web/src/components/screens/ProjectWorkspaceScreen.tsx:1586-1590`
- 后果：即使后端补字段，前端仍需显式控件承接用户确认。

## 三、已实现底座能力

- 运行依赖链路已具备：`intro_video_script` 依赖 `intro_selection` 和 `lesson_plan`，见 `apps/api/app/workflow_config.py:95-96`。
- 后端生成时会把依赖节点内容放进上下文，见 `apps/api/app/services.py:163-166`。
- 通用节点编辑和落盘能力已具备，见 `apps/api/app/main.py:141-144`、`apps/api/app/services.py:194-199`、`apps/api/app/store.py:218-236`。
- 因此本轮修复不需要重做存储层，主要是补契约、prompt、校验和前端交互。

## 四、修复任务拆分

### T058 后端：升级课程锚点契约与 prompt

目标：
- `lesson_plan/generate` 生成 9 套导入设计，每类 science/application/story 各 3 套。
- 每套包含两层字段：`video_theme`、`eye_catch_tag`、`hook`、`anchor_to_lesson`、`classroom_entry_question`、`no_pre_teach`、`entry_position`、`recommend_score`、`recommend_reason`、`risk_note`。
- 9 套 `anchor_to_lesson` 必须各不相同，且不能是教学目标或抽象套语。

涉及文件：
- `apps/api/app/services.py`
- `workflow/schemas/lesson_plan.schema.json`
- `apps/api/tests/`

验收：
- 新增/更新后端测试覆盖 lesson_plan schema、prompt 关键要求、fallback 输出字段。

### T059 后端：实现 selected_anchor 与 R047/R048/R049

目标：
- `intro_selection` schema/prompt/edit 校验增加 `selected_anchor`。
- R047：`selected_anchor` 非空且长度 ≥ 10，否则 edit/approve 前阻断。
- R048：`intro_video_script/generate` 必须从 `intro_selection.selected_anchor` 取硬输入；缺失时阻断。
- R049：storyboard 末帧 `subtitle` 必须体现锚点关键词；先按 warning 或 `details` 返回，不影响已有视频任务接口稳定性。

涉及文件：
- `apps/api/app/services.py`
- `workflow/schemas/intro_selection.schema.json`
- `workflow/schemas/storyboard.schema.json`
- `apps/api/tests/`

验收：
- 新增测试覆盖空 `selected_anchor` 阻断、脚本生成缺锚点阻断、末帧 subtitle 不含锚点时可检测。

### T060 前端：补课程锚点确认编辑控件

目标：
- 在 `intro_selection` 节点提供明确的课程锚点编辑框。
- 选择某方案时默认把该方案 `anchor_to_lesson` 写入 `selected_anchor`。
- 保存/确认前提示 `selected_anchor` 不能为空且长度 ≥ 10。

涉及文件：
- `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`

验收：
- 浏览器证据显示用户能看到、修改、保存最终课程锚点，且进入视频脚本后锚点一致。

### T061 测试：课程锚点专项回归

目标：
- 覆盖 PDF→lesson_plan 9 套方案→intro_selection 选定/改锚点→intro_video_script 旁白落锚点→storyboard 末帧字幕体现锚点。
- 同时确认旧的 DeepSeek + placeholder MP4 E2E 不回退。

产出：
- `docs/qa-audits/2026-06-21-anchor-chain-regression.md`

## 五、阶段裁决

本轮 T057 通过“排查交付”，但课程锚点功能本身不通过。下一阶段不应直接追真实视频质量，应先完成 T058-T061，让真实 LLM 输出和视频链具备课程锚点一致性门禁；否则真实视频 provider 进入生产后，只会放大“视频和教案连接不自然”的内容风险。
