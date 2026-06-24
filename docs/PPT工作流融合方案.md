# PPT 工作流 → 山海教育 融合方案

> **来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\`（"PPT 工作流"）
> **目标**：`E:\desktop\AI\02_Agents\lab\ShanHaiEdu\`
> **原则**：PPT 工作流为主架构，山海为运行层；砍冗余、保留山海优势（状态机/词表/规则执行器）
> **版本**：v0.1 | 2026-06-23

---

## 一、总体架构：8 阶段 → 6 节点

PPT 工作流 9 阶段砍掉 1 个冗余（阶段 7 视觉增强合并进阶段 6），收敛为山海 6 个节点：

```
PPT 工作流 9 阶段               →  山海 workflow.yaml 节点
─────────────────                   ─────────────────────
阶段 1  课程证据                →  无变化（textbook_parse 保留）
阶段 2  公开课教案              →  无变化（lesson_plan 保留）
阶段 3  逐页导演稿              →  ppt_director_script（新，替换 ppt_page_script）
阶段 4  视觉锁定                →  ppt_visual_lock（新，替换 visual_contract）
阶段 5  资产验收                →  ppt_visual_asset（改造，字段从 Air）
阶段 6+7 课件生产 + 视觉增强     →  ppt_artifact（改造，合并）
阶段 8  双重 QA                 →  final_delivery（改造，加 Air 审计逻辑）
阶段 9  正式交付                →  final_delivery（改造，加 Air 交付校验）
```

山海现有 PPT 节点处置：
- `ppt_assembly_plan` → **删除**，逻辑并入 ppt_director_script
- `ppt_page_script` → **删除**，替换为 ppt_director_script
- `ppt_visual_asset` → **保留并改造**，字段用 Air 的
- `pptx_artifact` → **保留并改造**，合并 Air 视觉增强
- `visual_contract` → **删除**，替换为 ppt_visual_lock

---

## 二、节点详细设计

### 节点 1：textbook_parse（保留，不做改动）

Air 的课程证据阶段有"来源可信度等级 + 未核实内容标记"理念，但不单独开节点，而是作为 `textbook_parse` 输出 schema 的补充字段：

```yaml
# 新增字段（optional）
source_trust_level: enum["官方教材", "教师用书", "教研资料", "网页"]  # Air 理念
unverified_items: list<string>  # 未核实内容标记
```

---

### 节点 2：lesson_plan（保留，追加 Air 字段）

Air 教案包含完整的课堂时间分配 + 师生活动 + 板书迁移链。山海 schema 追加以下字段：

```yaml
# 追加字段
time_allocation:           # Air 阶段 2 核心输出
  导入: "5分钟"
  新授: "20分钟"
  巩固: "10分钟"
  总结: "5分钟"
teacher_activities: list<{time, action}>  # 教师活动时间线
student_activities: list<{time, action}>  # 学生活动时间线
blackboard_design: text    # 板书设计（Air 保留字段）
after_class_transfer: text # 课后迁移（Air 保留字段）
misconceptions: list<string>  # 常见误区（Air 阶段 1 输出，移到教案）
```

---

### 节点 3：ppt_director_script（新建，核心节点）

**替换**：`ppt_assembly_plan` + `ppt_page_script`

**依赖**：`depends_on: [lesson_plan, character_dict]`

**schema**：`schemas/ppt_director_script.schema.json`

#### 每一页的字段（14 字段，Air 15 砍 4 + 加 3）

```yaml
# === 来自 Air（必须填）===
page: integer                          # 页码
page_type: enum[cover, intro_video, intro_observe, conflict_story,
                hands_on, mission_release, observation, comparison,
                concept_formation, variant_observe, representation,
                life_observe, step_demo, quick_find, measure_demo,
                record, reasoning_judge, problem_pivot, experiment,
                method_form, variant_diagnosis, life_apply,
                real_task, certification, knowledge_map]  # 山海 11 类 → 扩展为 Air 25 类
teaching_function: text                # 教学功能（Air 字段）
student_visible_title: text            # ≤15字（Air 约束）
student_visible_body: text             # ≤25字，≤3行（Air 约束）
main_visual: text                      # 主视觉描述（Air 的"主视觉或数学对象"）
student_action: enum[lift_hand, observe, point, read_aloud,
                     count_fingers, move_sticks, draw, write,
                     circle, connect, classify, compare,
                     speak_pattern, group_discuss]  # 山海 14 枚举，保留
speak_pattern: text                    # 表达或说理句式（Air 字段，山海无）
math_expression: text                  # 数学表达（Air 字段）
reveal_order: text                     # 揭示顺序（Air 字段）
blackboard_deposit: text               # 板书沉淀（Air 字段）

# === 来自山海（保留有价值字段）===
teacher_hint: text                     # 教师提示（山海 accuracy_notes）
core_competency: enum[number_sense, symbol_awareness, spatial_perception,
                       application_awareness, reasoning, computation,
                       model_thinking, classification, comparison,
                       estimation, representation]  # 山海 11 枚举
evidence_requirement: text             # 证据要求（山海保留字段，Air 阶段 1 理念）
zone_layout: text                      # 布局建议（山海保留字段）

# === 新增（Air 理念 + 审计需要）===
visual_asset_ref: string               # 引用 image-assets.md 的 asset_id（互锁关键字段）
page_rhythm: enum[anchor, dense, breathing]  # Air 视觉锁定节奏标记
```

#### 砍掉的 Air 字段（4 个）

| 字段 | 砍掉原因 |
|---|---|
| 构图策略（composition_strategy） | 移到视觉锁定的发散矩阵统一管理 |
| 主视觉尺度（visual_scale） | 同上 |
| 元素发散点（variation_point） | 同上 |
| 与前后页差异（neighbor_difference） | 同上 |

#### 导演稿级别的约束

```yaml
# 在 schema 层面强制
page_count: integer ≥ 22              # Air 硬门槛
unique_page_types: integer ≥ 8        # Air 审计脚本检查
unique_student_actions: integer ≥ 5   # AT3 反模板
no_3_consecutive_same_page_type: bool # AT2 反模板（机检）
no_3_consecutive_same_rhythm: bool    # Air 视觉锁定约束
sustained_storyline: string ≥ 20字符  # Air 审计: 导稿中必须有持续的课堂身份
```

#### prompts 目录

```
prompts/node_03_ppt_director_script/
  ├── system.md           # 导演角色定义（从 Air SKILL.md 提取）
  ├── page_templates.md   # 25 种 page_type 的页模板
  └── supervisor.md       # 逐页审查（山海现有 supervisor 保留）
```

---

### 节点 4：ppt_visual_lock（新建，Air 最关键的设计层）

**替换**：`visual_contract`

**依赖**：`depends_on: [ppt_director_script, character_dict]`

**schema**：`schemas/ppt_visual_lock.schema.json`

#### 字段定义

```yaml
# === 课堂身份 ===
classroom_identity: text              # 如"小小长度调查员"（Air 核心字段）
visual_motif: text                    # 视觉母题，如"直尺、木条、1厘米小棒、记录卡"
sustained_storyline: text             # 持续故事线，≥20字

# === 字体 6 档（Air 视觉基础）===
font_system:
  family: string                      # 推荐：微软雅黑 / 黑体
  cover_title: {size: integer, bold: bool}     # 档位1：封面标题
  page_title: {size: integer, bold: bool}      # 档位2：页标题
  task_card_title: {size: integer, bold: bool} # 档位3：任务卡标题
  task_card_body: {size: integer, bold: bool}  # 档位4：任务卡正文
  math_conclusion: {size: integer, bold: bool} # 档位5：数学结论
  footer_label: {size: integer, bold: bool}    # 档位6：页脚/标签

# === 间距基线（Air 视觉基础）===
spacing_baseline: integer             # 8pt 或 10pt（Air 要求: 8pt）
internal_padding: integer             # 同类卡片统一内边距
line_height_ratio: float              # 行距倍率（建议 1.5-1.8）

# === 色彩角色（Air 视觉基础）===
color_roles:
  primary: string                     # 主色（如 #1A5276 深青蓝）
  auxiliary: string                   # 辅色
  emphasis: string                    # 强调色（如 cm-gold）
  success: string                     # 成功/发现色（如 operation-green）
  warning: string                     # 警告/错误色（如 diagnosis-red）
  neutral: string                     # 中性色
  background: string                  # 背景色
  projection_contrast_checked: bool   # 投影对比度已验证

# === 形状语言（Air 视觉基础）===
shape_language:
  corner_radius: integer              # 圆角半径
  line_weight: integer                # 线条粗细
  shadow_preset: enum[none, soft, medium]  # 投影类型
  arrow_style: enum[none, simple, filled]  # 箭头样式
  label_badge_style: text             # 标签/徽章规则
  magnifier_style: text               # 放大镜/局部强调规则

# === 图标规则（Air 视觉基础）===
icon_rules:
  min_touch_size: integer             # 最小触控尺寸（低年级≥20mm）
  icon_set: string                    # 图标集名称
  icon_size_tiers: list<integer>      # 图标尺寸档位

# === 形状卡片规格（Air visual-foundations）===
card_specs:
  uniform_width: integer              # 同类卡片统一宽度
  uniform_height: integer             # 同类卡片统一高度
  corner_radius: integer              # 统一圆角
  title_position: enum[top, left]     # 标题位置
  body_line_height: float             # 正文行距
  emphasis_color_rule: text           # 强调色应用规则

# === 数学图形特殊规则（Air visual-foundations）===
math_graphic_rules:
  tick_label_size: integer            # 刻度数字字号（分离于正文）
  unit_size: integer                  # 单位字号（分离于正文）
  separate_padding: bool              # 不与正文统一内边距

# === 长文本换行策略（Air visual-foundations）===
text_wrap_strategy: enum[rewrite_short, widen_box, never_compress]
  # 优先改写为短课堂语言 → 加宽文本框 → 禁止压缩字号

# === 视觉基础来源证据（Air 强制）===
visual_foundations_source: text       # 固定填："visual-design-foundations 已加载"
  # 注意：山海没有 external-skill 机制，visual-design-foundations 的核心规则
  # 已吸收进本 schema 的上述字段，不需要额外加载外部 skill

# === 页面发散矩阵（Air 的核心反模板武器）===
# 每页一行，由模型在视觉锁定阶段填写
page_divergence_matrix:
  - page: integer                     # 页码
    page_type: string                 # 页面类型
    composition_strategy: text        # 构图策略（Air 砍下来的字段，在此处用）
    visual_scale: text                # 主视觉尺度（全页/半页/角标/特写）
    divergence_point: text            # 元素发散点（本页与相邻页有何不同）
    neighbor_difference: text         # 与前后页差异
    image_position: text              # 图片位置（left/right/top/bottom/center_overlay）

# === 发散矩阵级约束 ===
composition_rotation: integer         # 每 3-4 页必须切换构图（Air 锁规则）
max_consecutive_same_composition: integer = 2
max_consecutive_same_image_position: integer = 2
image_scale_diversity: integer ≥ 3    # 至少 3 种不同图片尺度

# === 儿童趣味与密度策略（Air 要求）===
density_strategy:
  large_scene_pages: list<integer>    # 大场景页
  prop_closeup_pages: list<integer>   # 道具特写页
  material_detail_pages: list<integer> # 材料特写页
  evidence_sticker_pages: list<integer> # 证据贴页
  interactive_button_pages: list<integer> # 互动按钮页
  group_model_pages: list<integer>    # 分组模型页
  peer_expression_pages: list<integer> # 同伴表达页
  gallery_pages: list<integer>        # 作品画廊页
  no_bare_formula_pages: bool         # 禁止概念页只有公式/定义/空卡片
```

---

### 节点 5：ppt_visual_asset（改造）

**依赖**：`depends_on: [ppt_director_script, ppt_visual_lock, character_dict]`

**schema**：`schemas/ppt_visual_asset.schema.json`（改造）

#### 字段定义（Air 8 字段 + 山海 2 字段）

```yaml
# === Air 字段（全部保留）===
asset_id: string                      # A01, A02, ...（Air 编号格式）
filename: string                      # images/A01-cover-xxx.png
teaching_role: enum[cover, intro, operation, record, transfer, homework]  # Air 5+1 角色
course_keywords: list<string>         # 课题关键词（Air 互锁字段）
serves_purpose: text                  # 教学用途（Air 字段）
composition_margin: enum[left, right, top, bottom, center_overlay]  # 构图留白
generation_source: enum[imagegen, photo, placeholder]  # 生图来源
pptx_pages: list<integer>             # 使用页面（Air 互锁字段，对应导演稿 page）

# === 山海保留字段 ===
storage_path: text                    # 山海路径约束：08A_PPT视觉资产/
provider_override:
  image: string                       # 默认 gpt-image-2
status: enum[pending, generated, failed]

# === Air 资产级约束（schema 级强制）===
dedicated_count: integer ≥ 7          # 专属图片 ≥ 7
role_coverage: [cover, intro, operation, transfer, homework]  # 5 类必覆盖
no_code_drawn: bool                   # 禁止代码绘制/SVG绘制/PIL生成
no_generic_label: bool                # 禁止通用/复用/共享标记
photo_realistic_count: integer ≥ 7    # 照片级真实 ≥ 7
sha256_in_pptx_media: bool            # 入袋校验（Air 核心检查）

# === 文字策略（Air 字段，每张图必填）===
text_strategy: text                   # 图片不含中文标题/结论/题干/标签
```

#### 图片 prompt 模板（吸收自 Air）

```
# 每张图生成时拼接以下约束
"{serves_purpose}。
儿童绘本风格/照片级真实感，16:9，1920x1080。
{composition_margin} 留白区为空，留给 PPT 文字层。
图片不含中文标题、数字、公式、题干和标签。
自然教室/户外/家庭光线，无文字叠加。"
```

---

### 节点 6：ppt_artifact（改造，合并 Air 阶段 6+7）

**依赖**：`depends_on: [ppt_director_script, ppt_visual_asset, ppt_visual_lock]`

**schema**：`schemas/pptx_artifact.schema.json`（改造）

#### 字段定义

```yaml
# === 输出文件 ===
pptx_path: text                       # 最终 PPTX
pdf_path: text                        # PDF 导出
contact_sheet_path: text              # Contact sheet PNG

# === 装配约束（Air 派生）===
slide_count: integer ≥ 22             # Air 门槛（原山海 schema 无此字段）
media_count: integer ≥ 7              # Air 门槛
sha256_media_match: bool              # 所有 asset 都在 PPTX media 中
no_teacher_layer_leaks: bool          # 学生可见层无"教具/教学目标/教师提示"
no_forbidden_visible_terms: bool      # 无 A版/B版/debug/TODO/AI生成/提示词
no_lock_files: bool                   # 输出目录无 ~$*.pptx

# === 山海保留字段 ===
eight_confirmations_done: bool        # R027 八大确认
svg_quality_passed: bool              # R028 SVG质量
single_pptx_only: bool                # Air: 输出目录只有一个 PPTX，无旧版本
```

---

## 三、审核规则迁移

### Air 3 个 Python 脚本 → 山海 rule_executor.py

| Air 脚本 | 核心检查逻辑 | → 山海 Rule ID |
|---|---|---|
| `audit_courseware_quality.py` | 解析导演稿 markdown、检查每页 10+ 字段非空、页数 ≥22、页面类型 ≥8、连续同类型不超 3 | **R033** (新增) |
| `audit_courseware_quality.py` | image-assets.md 表解析、≥7 行、每行有 teaching_role + text_strategy、无代码绘制词 | **R034** (新增) |
| `audit_courseware_quality.py` | design-spec.md 含 7 个视觉基础词（文字档位/间距基线/色彩角色/形状语言/图标/投影/对比）、含 visual-design-foundations 已加载 | **R035** (新增) |
| `audit_premium_delivery.py` | PPTX 有效性（合法 zip、有 slide*.xml）、≥22 页、≥7 media、无非法 media header | **R036** (新增) |
| `audit_premium_delivery.py` | SHA256 图片入袋校验（image-assets → PPTX media 交叉比对）、5 类教学角色覆盖 | **R037** (新增) |
| `audit_premium_delivery.py` | QA 报告 12 个证据短语检查、contact sheet 已查看证据、关键页高清证据 | **R038** (新增) |

### 山海现有 PPT 规则处置

| 现有 Rule ID | 处置 |
|---|---|
| R020-R024（动作/主视觉/证据/板书/类型） | **保留**，阈值升级到 Air 标准 |
| R025（密度限制） | **改造**，阈值从 25 字改为 Air 标准（≤25字标题 + ≤125字正文/页） |
| R026（学生文本扫描） | **保留** |
| R027（Eight Confirm） | **保留** |
| R028（SVG 质量） | **保留** |
| R029（PPT notes） | **保留** |
| R030（media_count > 0） | **改造**，升级为 ≥7（Air 标准） |
| R031（调色板） | **保留** |
| R032（角色引用） | **保留** |

### R024 阈值升级详情

```yaml
# 山海当前
R024:
  description: "页面类型数 ≥ 5"
  threshold: 5

# 融合后（Air 标准）
R024:
  description: "页面类型数 ≥ 8"
  threshold: 8
  page_type_enum: 25  # 从山海 11 类扩展到 Air 25 类
```

---

## 四、Air 冗余约束砍除清单

| Air 原约束 | 砍除理由 |
|---|---|
| **阶段 7 "视觉增强"** | Air 自己的 `认识厘米` 样本根本没走这一步；合并进 ppt_artifact 装配逻辑 |
| **导演稿 4 个视觉字段**（构图策略/主视觉尺度/元素发散点/与前后页差异） | Air 样本自己就漏填；改到视觉锁定的发散矩阵统一管理 |
| **总纲 17 条中的 3 条"重复反模板"条款**（原条 11/12/13） | "换文字不换图""连续页同布局""图片槽死板"是同一件事的不同说法 |
| **`project.json` 的 `gates` 9 状态** | 山海 state_machine 6 状态已覆盖 |
| **`init_project.py` 模板占位符** | 山海 schema + form 填写已做同样的事 |
| **Air 的 `update_premium_doc.py`** | 边角料工具，山海不需要 |
| **Air 的 `build_workflow_package.py` / `verify_workflow_package.py`** | 打包发布工具，山海不涉及 |
| **`visual-design-foundations` 独立 external skill** | 核心规则已吸收进 ppt_visual_lock schema，字段即约束 |
| **总纲原条 8/9/10（"数位笔/手写板/表情包"）** | 属于排版具体实现，不是工作流约束 |
| **总纲原条 13（"SVG 占位符"）** | 已被山海现有 ppt-master skill 覆盖 |
| **总纲原条 14（"数学图形字体"）** | 已被山海现有 R006（数学可编辑）覆盖 |

---

## 五、山海现有文件处置清单

### 删除

| 文件 | 原因 |
|---|---|
| `workflow/schemas/ppt_assembly_plan.schema.json` | 逻辑并入导演稿 |
| `workflow/schemas/ppt_page_script.schema.json` | 被 ppt_director_script.schema.json 替代 |
| `workflow/prompts/node_02_ppt_assembly/` | 删除 |
| `workflow/prompts/node_03_ppt_page_script/` | 改为 node_03_ppt_director_script/ |
| `workflow/schemas/visual_contract.schema.json` | 被 ppt_visual_lock.schema.json 替代 |

### 改造

| 文件 | 改动 |
|---|---|
| `workflow/workflow.yaml` | PPT 分支从 4 节点 → 4 节点（删除 assembly_plan，重命名 page_script→director_script，新增 visual_lock，artifact 改造） |
| `workflow/schemas/ppt_visual_asset.schema.json` | 字段从 6 升级到 10（加 Air 的 8 字段 + 保留山海 2 字段） |
| `workflow/schemas/pptx_artifact.schema.json` | 加 Air 的 22 页 / 7 media / SHA256 / 锁文件检查字段 |
| `workflow/rules.md` | 加 R033-R038 定义 |
| `apps/api/app/rule_executor.py` | 实现 `_check_r033` 到 `_check_r038`，改造 `_check_r024`（阈值 5→8）、`_check_r030`（>0→≥7） |
| `workflow/schemas/lesson_plan.schema.json` | 加 Air 教案字段（time_allocation/teacher_activities/student_activities/blackboard_design/after_class_transfer/misconceptions） |

### 新建

| 文件 | 内容 |
|---|---|
| `workflow/schemas/ppt_director_script.schema.json` | 14 字段逐页导演稿 schema |
| `workflow/schemas/ppt_visual_lock.schema.json` | 视觉锁定 schema（字体 6 档/色彩/形状/发散矩阵） |
| `workflow/prompts/node_03_ppt_director_script/` | 导演稿 prompt 目录（system.md + page_templates.md + supervisor.md） |
| `workflow/prompts/node_04_ppt_visual_lock/` | 视觉锁定 prompt 目录 |
| `workflow/rules/R033.yaml` ~ `R038.yaml` | 6 个新规则定义 |

---

## 六、实施批次

### 批次 1：Schema 层（零冲击，1 人日）

1. 新建 `ppt_director_script.schema.json`（14 字段）
2. 新建 `ppt_visual_lock.schema.json`
3. 改造 `ppt_visual_asset.schema.json`（6→10 字段）
4. 改造 `pptx_artifact.schema.json`（加 Air 约束字段）
5. 改造 `lesson_plan.schema.json`（加 Air 教案字段）

### 批次 2：流程层（低冲击，1 人日）

6. 改 `workflow.yaml`：删除 assembly_plan + visual_contract，新建 director_script + visual_lock，改 artifact 依赖链
7. 写 prompts 目录（node_03 + node_04）
8. 更新 `rules.md` 加 R033-R038

### 批次 3：规则层（中冲击，2 人日）

9. 实现 `_check_r033`（导演稿字段级验证）
10. 实现 `_check_r034`（图片资产计划验证）
11. 实现 `_check_r035`（视觉锁定验证）
12. 实现 `_check_r036`（PPTX + media 验证）
13. 实现 `_check_r037`（SHA256 入袋 + 教学角色）
14. 实现 `_check_r038`（QA 证据短语）
15. 改造 `_check_r024`（5→8 阈值）、`_check_r030`（>0→≥7）

### 批次 4：验证层（1 人日）

16. 写 `test_ppt_premium_gate.py`（用 `认识厘米` 26 页样本做回归测试）
17. 跑一轮真实课题验证（如"5以内数的认识"重建）

---

## 七、fusion 后的 workflow.yaml PPT 分支

```yaml
  # -------- PPT 分支：第 3 步 导演稿 --------
  - id: ppt_director_script
    runtime_enabled: true
    step: 3
    title: PPT 逐页导演稿
    branch: ppt
    depends_on: [lesson_plan, character_dict]
    schema: schemas/ppt_director_script.schema.json
    prompts_dir: prompts/node_03_ppt_director_script/
    supervisor: prompts/supervisor/director_page_reviewer.md
    per_page: true
    hard_stop: true
    optional: false

  # -------- PPT 分支：第 4 步 视觉锁定 --------
  - id: ppt_visual_lock
    runtime_enabled: true
    step: 4
    title: PPT 视觉锁定
    branch: ppt
    depends_on: [ppt_director_script, character_dict]
    schema: schemas/ppt_visual_lock.schema.json
    prompts_dir: prompts/node_04_ppt_visual_lock/
    hard_stop: true
    optional: false

  # -------- PPT 分支：第 5 步 视觉资产 --------
  - id: ppt_visual_asset
    runtime_enabled: true
    step: 5
    title: PPT 视觉资产
    branch: ppt
    depends_on: [ppt_director_script, ppt_visual_lock, character_dict]
    schema: schemas/ppt_visual_asset.schema.json
    prompts_dir: prompts/node_05_ppt_visual_asset/
    provider_override:
      image: gpt-image-2
    storage_path_constraint: "08A_PPT视觉资产/"
    optional: false

  # -------- PPT 分支：第 6 步 PPT 装配 --------
  - id: ppt_artifact
    runtime_enabled: true
    step: 6
    title: PPT 装配+增强
    branch: ppt
    depends_on: [ppt_director_script, ppt_visual_asset, ppt_visual_lock]
    schema: schemas/pptx_artifact.schema.json
    prompts_dir: null
    pre_submit_check:
      - eight_confirmations_done       # R027 保留
      - svg_quality_passed             # R028 保留
      - at_anti_template_pass          # R033 新增（AT 反模板）
      - premium_media_pass             # R036 新增（≥22页 ≥7图）
      - sha256_asset_match             # R037 新增（入袋校验）
    optional: false
```

---

## 八、变更历史

| 版本 | 日期 | 变更 | 作者 |
|---|---|---|---|
| v0.1 | 2026-06-23 | 初版：8阶段→6节点，14字段导演稿，视觉锁定完整schema，6条规则迁移，冗余清理清单 | Claude |
