# 工作流符合度审计与薄弱点分析

**版本**：v1.0
**日期**：2026-06-21
**审计角色**：首席系统架构师
**审计方式**：三路并行只读扫描（后端代码 / 前端代码 / 工作流文档自身）
**审计范围**：节点字段实现、规则执行、状态机、课程锚点链路、prompt 模板、provider 矩阵

---

## 一、整体结论

本次审计聚焦三个问题：
1. 后端代码是否落实了工作流定义文档？
2. 前端代码是否呈现了工作流定义的字段？
3. 工作流文档自身有无设计薄弱点？

**整体判定：课程锚点链路 v1 字段落地良好（后端 5/5 已实现），但规则执行模式、PPT 线前端、prompt 矩阵和状态机完整度仍存在系统性薄弱面。**

### 符合度评分

| 维度 | 评分 | 说明 |
|---|---:|---|
| 锚点链路后端实现 | 9/10 | 字段、normalize、prompt、edit/approve 校验、R049 warning 全部到位 |
| 锚点链路前端呈现 | 6/10 | intro_selection 完整可编辑；但 lesson_plan 9 套卡片只展示 3 字段（缺 7 个）|
| 节点字段覆盖度 | 5/10 | 视频链 OK；PPT 13 字段、角色字典、视觉契约前端基本未实现 |
| 规则执行 | 4/10 | 散落在 normalize/prompt/validate；无通用规则引擎；多条红线规则无执行器 |
| 状态机完整度 | 4/10 | 后端有 `running`/`failed`，文档有 `drafted`/`blocked` 但后端不写入；连锁失效未实现 |
| 内部一致性 | 7/10 | schema 与 rules 有 2 处字段引用/字数不一致；status 枚举遗漏 `not_started` |
| Prompt 矩阵 | 2/10 | 所有节点 prompt 只有 deepseek 一个版本，跨 provider fallback 完全未落地 |
| Prompt 文件实际使用 | 0/10 | `workflow/prompts/` 全部 prompt 文件**未被后端读取**，prompt 全部硬编码在 services.py |

---

## 二、后端实现 vs 工作流定义 — 详细差距

### 2.1 锚点链路（重点，已基本到位）

| 检查点 | 状态 | 关键证据 |
|---|---|---|
| lesson_plan.intro_designs 13 字段 normalize | ✅ 已实现 | `apps/api/app/services.py` L13-27 `INTRO_DESIGN_REQUIRED_FIELDS`；L183-213 `_normalize_intro_designs`；L234-237 `_is_abstract_anchor` |
| intro_selection.selected_anchor 落盘 + 校验 | ✅ 已实现 | `services.py` L102-111 normalize、L1096-1106 edit 校验、L1186-1192 approve 校验、L596-599 generate prompt |
| intro_video_script 接收 selected_anchor | ✅ 已实现 | `services.py` L475-477 `_assert_selected_anchor`、L114-122 旁白末句注入、L601-607 prompt |
| storyboard 末帧锚点（R049） | ✅ 已实现（warning 级）| `services.py` L1322-1345 `_storyboard_anchor_warnings`、L619-623 prompt |
| R046 抽象套语过滤 | ⚠️ 部分实现 | normalize 层自动回填而非 hard_block 阻断；规则 `severity=hard_block` 但实际是 fallback |

### 2.2 既有规则 R001-R045 执行情况

| 规则 | 实际执行 |
|---|---|
| R001 中文男声 | ❌ 后端无 `voice_gender`/`voice_language` 字段校验；final_video edit 校验 L1161-1181 仅查 clip_count、clips、model_audio_policy、english_audio_detected |
| R010 上游 approved | ✅ `_assert_dependencies` L467-473 |
| R013 参考图非空 | ✅ edit 校验 L1152 |
| R032 角色一致性 | ❌ 后端**完全没有 character_dict 概念** |
| R043 model_prompt 男声 | ⚠️ prompt/normalize 硬写"旁白（男声，中文）"，但 on_save 时无独立执行器校验 |

**核心问题**：规则执行模式是"normalize 自动修复 + prompt 软约束"，**没有独立 rules engine**。`severity=hard_block` 的规则在代码里实际是 fallback，会静默替换问题内容而非阻断。

### 2.3 prompt 文件未被使用（系统性问题）

- `workflow/prompts/node_01_lesson_plan/deepseek.md`（v1.1）、`node_4b_intro_video_script/`、`node_06_storyboard/` 等 7 个节点 prompt 文件存在
- grep 确认 `apps/api/app/` 中**没有任何代码读取这些文件**
- `_build_prompt`（services.py L571-633）**全部硬编码**在 Python 字符串中

**风险**：prompt 文档与代码可能漂移，刚更新的 v1.1 deepseek.md 实际未生效。我此前更新该 prompt 的工作产生不了线上效果。

### 2.4 状态机后端 vs 文档

- 后端节点状态实际使用：`not_started / needs_review / approved / running / failed`
- state_machine.md 定义：`not_started / drafted / needs_review / approved / blocked / skipped`
- **差异**：
  - `drafted` 完全不出现在后端写入逻辑中（AI 生成直接写 `needs_review`）
  - `blocked` 完全不写入
  - `skipped` 只在依赖检查中作为"允许读"，无代码写入
  - `running`、`failed` 是后端使用但文档未定义
  - **连锁失效（cascade invalidate）机制完全未实现**

---

## 三、前端实现 vs 工作流字段定义 — 详细差距

### 3.1 锚点链路前端

| 检查点 | 状态 | 关键证据 |
|---|---|---|
| intro_selection 用户可编辑 selected_anchor | ✅ 已实现 | `ProjectWorkspaceScreen.tsx` L1537-1716 `IntroSelectionResult`；L2417-2422 `validateIntroSelectionAnchor` |
| intro_video_script / storyboard 锚点贯穿提示 | ✅ 已实现 | L2308-2328 video-script 摘要；L2369-2393 storyboard 摘要；L2425-2437 `resolveCourseAnchorForStage` |
| lesson_plan 9 套卡片两层结构展示 | ❌ 严重缺失 | `normalizeIntroDesigns`（L2642-2667）只提取 `type/title/hook/anchor_to_lesson/recommend_score`，**缺失 7 个字段**：video_theme、eye_catch_tag、classroom_entry_question、no_pre_teach、entry_position、recommend_reason、risk_note |

**结论**：用户在 lesson_plan 节点页**看不到** AI 实际产出的两层结构完整内容。后端字段已落，前端 UI 没跟上。

### 3.2 PPT 线前端几乎为零

PPT 探究型 13 字段（schema.md 节点 3）—— grep `core_competency`、`student_action`、`page_type`、`main_visual`、`zone_layout`、`density_limits`、`math_assertions` 在整个前端代码中**零命中**。`NODE_DEFS` 不包含 `ppt_page_script` 映射。落入通用 JSON textarea，用户面对的是一堆 JSON 字符串。

**PPT 线节点 API 映射缺口**：
- `ppt_assembly_plan` — 缺 NODE_DEFS 映射
- `ppt_page_script` — 缺
- `ppt_visual_asset` — 缺
- `pptx_artifact` — 缺
- `final_delivery` — 缺

**额外发现**：前端有虚拟阶段 `lesson-plan-final`，但 schema.md 中**不存在**此节点。

### 3.3 角色字典 / 视觉契约前端降级

- 角色字典：NewProjectScreen.tsx L644-662 仅有两个自由文本 Textarea（`characterProfile` + `characterSafetyRule`），grep `character_id/view_front/outfit_lock/banned_keywords` 在前端**零命中**
- 视觉契约：L667-694 三个 Input（palette/style_keywords/font_preference），均为单行字符串，非 schema 要求的列表结构；`template_pptx` 上传完全缺失

**这意味着 v1 红线规则 R004（角色字典禁真人，必须含 banned_keywords 三项）后端无字段、前端无表单，整条规则形同虚设。**

### 3.4 Demo vs 真实 API 字段不一致

- Demo `VideoIntroPlan` 用 camelCase（`courseAnchor/classroomLandingQuestion`）
- 真实 API 用 snake_case（`anchor_to_lesson/classroom_entry_question`）
- Demo mock 数据缺新增 7 字段
- 阶段数也不同（demo 14 / API 10）

---

## 四、工作流文档自身薄弱点

### 4.1 内部一致性问题

| 问题 | 严重程度 | 位置 |
|---|---|---|
| `schema.md` L360 `node_version.status` 枚举遗漏 `not_started` | 高 | schema vs state_machine 不一致 |
| `rules.md` R046 写"字数 ≥ 10" vs `schema.md` L108 写"15-40 字" | 中 | rules vs schema 不一致 |
| `prompts/node_4b/deepseek.md` L43 写"10-20 字" vs schema "15-40 字" | 中 | prompts vs schema 不一致 |
| `rules.md` R049 引用 `shots[-1].subtitle` 但 schema 中分镜集合命名未统一 | 中 | 路径表达不规范 |
| `recommend_score` schema 有定义但 PRD 无决策依据 | 低 | 字段缺产品背书 |

### 4.2 锚点链路设计薄弱点（重点）

**链路 5 步只有前 3 步有机器规则**：

```
[1] AI 产出 anchor_to_lesson      → R046（normalize 回填，非阻断）
[2] 用户确认 selected_anchor       → R047（hard_block，OK）
[3] script 接收 selected_anchor   → R048（hard_block 但只查输入存在性）
[4] narration_full_text 末句体现 → ❌ 无规则
[5] shots[-1].subtitle           → R049（warning，可 override）
[6] final_video 末 10 秒           → ❌ 无规则
```

**关键缺口**：第 [4] 步只靠 prompt 软约束，第 [6] 步完全无校验。整条链路后半段可被绕过。

**建议**：
- 新增 **R048.5（hard_block）**：narration_full_text 末 50 字必须包含 selected_anchor 关键词
- 新增 **R049.5（warning）**：final_video 最后 clip 字幕/旁白落在锚点上

### 4.3 R046 字面黑名单不足

R046 黑名单只列 3 个套语（"自然引出本课"、"教学目标对应点"、"教案关联点"），AI 可轻易换说法绕过（"自然回归本课内容"、"与教学目标衔接"）。但 anchor-lesson-to-video.md 第五节列出了 5 种不合格写法。

**建议**：
- 黑名单扩到 5 条
- 增加结构化检查：锚点中必须含至少一个具体名词（现象/物品/人物/场景）
- 增加与 teaching_objectives 文本相似度上限校验（防止把教学目标抄成锚点）

### 4.4 "9 套锚点必须各不相同" — 无判定标准

- schema.md / anchor-lesson-to-video.md 都写了硬约束
- 但 rules.md 完全没有对应规则 ID
- 没有定义"不相同"是字面 diff 还是语义相似度

**建议**：新增 R046.5（hard_block），用 agent:claude 做 9 个锚点两两语义相似度检查，超过阈值即阻断。

### 4.5 PPT 探究型 warning 是否应升级

R023（必须有板书小结页）和 R025（信息密度上限）目前是 warning，用户可一路 override。这两条直接关系公开课评议硬指标。

**建议**：
- R023 → hard_block（板书小结是公开课评议硬指标）
- R025 保留 warning 但加 override 上限（同项目超 3 页自动升级为 hard_block）

### 4.6 Prompt 跨 provider 矩阵未落地

PRD 8.3 要求"每个节点至少在 default + fallback 两个 provider 上跑过"，但所有 prompt 目录下**只有 deepseek.md 一个文件**。fallback 切换时使用同一 prompt，跨模型效果可能崩。

**建议**：v1 至少为 lesson_plan 和 storyboard 两个关键节点补 GPT 版 prompt。

---

## 五、修复优先级清单（推荐下发任务）

按"风险大小 × 修复成本"排序，建议作为 T058 起的修复任务批次。

### P0（紧急 — 直接影响产品红线 / 用户可感知）

| 编号 | 任务 | 目标角色 | 范围 |
|---|---|---|---|
| **T058** | 前端 lesson_plan 9 套卡片补齐两层结构 7 字段展示 | 前端工程师 | 改造 `IntroSelectionResult` 的 `normalizeIntroDesigns`，渲染 video_theme、eye_catch_tag、classroom_entry_question、no_pre_teach、entry_position、recommend_reason、risk_note |
| **T059** | 后端 prompt 文件加载机制接入 | 后端工程师 | 让 `services._build_prompt` 优先从 `workflow/prompts/{node_id}/{provider}.md` 读取，硬编码作为 fallback；解决 prompt 漂移 |
| **T060** | 后端补 R001 中文男声执行器 | 后端工程师 | final_video edit/approve 时校验 `voice_gender=male` / `voice_language=zh-CN`；当前完全空缺，是产品红线 |
| **T061** | 锚点链路第 [4] 步加 R048.5 hard_block | 后端工程师 | 校验 narration_full_text 末 50 字含 selected_anchor 关键词；同步写入 rules.md |

### P1（高 — 工作流自身一致性）

| 编号 | 任务 | 目标角色 | 范围 |
|---|---|---|---|
| **T062** | 修工作流文档内部不一致 | 产品经理（或架构师） | schema.md status 补 `not_started`；R046 字数下限改 15；node_4b prompt 字数改 15-40；R049 路径表达统一 |
| **T063** | 新增 R046.5（9 套锚点唯一性 hard_block） | 产品经理 + 后端 | rules.md 增规则 + 后端实现 agent:claude 语义相似度检查 |
| **T064** | R023 升级 hard_block + R025 加 override 上限 | 产品经理 | rules.md 字段更新 |
| **T065** | R046 黑名单扩展 + 结构化检查 | 产品经理 + 后端 | 增加具体名词检查、与 teaching_objectives 相似度上限 |

### P2（中 — 长期债务）

| 编号 | 任务 | 目标角色 | 范围 |
|---|---|---|---|
| **T066** | PPT 线 5 节点 API 映射 + 前端结构化 UI | 后端 + 前端 | 后端补 ppt_assembly_plan、ppt_page_script 等节点；前端补 13 字段表单 |
| **T067** | 角色字典 / 视觉契约结构化表单 | 前端工程师 | NewProjectScreen 第 0 步把自由文本升级为结构化字段，落实 R004 红线 |
| **T068** | 状态机后端落地（drafted/blocked/skipped + 连锁失效） | 后端工程师 | 与 state_machine.md 对齐；schema status 枚举对齐 |
| **T069** | 通用规则引擎抽离 | 后端工程师 | 把 normalize/validate 中散落的规则检查统一到 `rules_engine.py`；按 rule_id 注册执行器 |
| **T070** | Prompt 矩阵补齐 GPT/Claude 版（lesson_plan + storyboard 优先） | 后端工程师 | 落实 PRD 8.3 |
| **T071** | Demo 模式 mock 数据同步新 schema | 前端工程师 | 字段命名 camelCase → snake_case 统一；补 7 个新字段；阶段数对齐 |

---

## 六、本次审计未覆盖

- 真实视频 provider（Octo）的稳定性、质量验收
- 性能、并发、SQLite 多实例
- 上线鉴权、多租户、计费
- 飞轮信号采集和偏好画像可视化
- 中文 TTS 选型
- 教程系统

以上属于 PRD 已明确推迟事项或正在进行中的任务，不在本次审计范围。

---

## 七、报告关联文件

- `workflow/schema.md`（v2 含两层结构）
- `workflow/rules.md`（含 R046-R049）
- `workflow/state_machine.md`
- `docs/anchor-lesson-to-video.md`
- `docs/PRD.md`
- `workflow/prompts/node_01_lesson_plan/deepseek.md`（v1.1）
- `apps/api/app/services.py`
- `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`
- `apps/web/src/components/screens/NewProjectScreen.tsx`
- `apps/web/src/lib/api-mappers.ts`
