# PPT 工作流优化方案

> **文档定位**：从已成熟的「AI-youjiao-PPT-workflow-最新版」参考项目中，筛选 ShanHai-Edu v1 应吸纳的 PPT 子系统能力
> **编制日期**：2026-06-22
> **编制依据**：参考项目实地研读（根目录 + skill 子目录 + samples/cm-premium-real 样例）
> **目标读者**：ShanHai-Edu 全栈主导、教学法负责人、产品负责人

---

## 一、背景与核心洞察

### 1.1 为什么做这次梳理

ShanHai-Edu 的 PPT 子系统（ppt_assembly_plan / ppt_page_script / ppt_visual_asset / pptx_artifact 四个节点）目前**只定义了字段和门禁规则，没有「精品」层面的视觉硬约束**。2026-06-21 手动跑通的「5以内数的认识」12 页 PPT 大概率是"标题 + 卡片 + 小图标"的模板稿——这与产品第一性原理「**核心卖点不是效率，是让人眼前一亮的课件**」（PRD 第 1.2 节）冲突。

### 1.2 两个项目的差异化定位

| 维度 | 参考项目 | ShanHai-Edu |
|------|----------|-------------|
| 形态 | 一次性脚本流 | 用户编辑工作流（状态机 + approve） |
| PPT 成熟度 | ★★★★★ 实战精品 | ★★☆☆☆ 仅骨架 |
| 用户主导权 | 无 | 有 |
| 飞轮 | 无 | 设计中 |
| 多课管理 | 无 | 有 |

**结论**：参考项目是 ShanHai-Edu 的「PPT 生产内核参考实现」，但只有内核；ShanHai-Edu 的壳（用户编辑 + 飞轮 + 状态机 + 多课管理）是参考项目没有的差异化价值。**壳不动，内核可吸收**。

### 1.3 参考项目打过仗的证据

- **`AI-youjiao-PPT精品生产总纲.md` 第 45-62 行**「三点五、模板事故复盘规则」明确写了 2026-06-15 的「六份教案 20 页批量稿」事故复盘，催生出 17 条硬门槛
- **`visual-divergence.md` 第 103-119 行** v20 复盘：「同一主对象原样复用不得超过 3 次」等条款来自实战
- **`samples/cm-premium-real\`** 有 1 个真实 26 页精品交付样例（含 .pptx / .pdf / contact-sheet.png / QA 报告）

---

## 二、8 个值得吸收的点（按 ROI 排序）

### 吸收 1：反模板化硬规则（**最高 ROI**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-divergence.md` 第 27-36 行

**核心规则**：

```
- 连续 3 页不得使用同一构图策略
- 连续 5 页不得让图片保持同一尺寸、位置、留白方向
- 至少 6 种构图策略进入成品
- 至少 3 种图片尺度（全屏背景 / 半屏大图 / 小道具贴）
- 概念页/算式页/练习页/总结页不得只放一个定义/算式/卡片
- 必须补入两类儿童课堂支架（观察证据/短任务/圆点分组/同伴表达/道具贴）
```

**ShanHai-Edu 现状**：

| 文件 | 缺失内容 |
|------|----------|
| `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\rules.md` | R020-R032 共 13 条 PPT 规则，**无一条关于版面发散** |
| `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\schema.md` 第 149-167 行 | 13 字段 PPT 页面定义，**无版面策略字段** |

**实施方式**：在 rules.md 加 R033-R038 共 6 条 hard_block 规则：

| 新规则 | 检查内容 |
|--------|----------|
| R033 | 任意连续 3 页构图策略唯一（构图策略枚举见 schema 增项） |
| R034 | 任意连续 5 页图片尺寸/位置/留白方向有变化 |
| R035 | 整套至少 6 种构图策略（premium tier 强制） |
| R036 | 至少 3 种图片尺度（大场景/半屏/小道具贴） |
| R037 | 概念页/算式页/练习页/总结页必须含 2 类儿童课堂支架 |
| R038 | contact sheet 必须含"重复版式风险清单"小节 |

**工作量**：0.5 人日（仅文档修改）

---

### 吸收 2：真实图片资产治理（**高 ROI**）

**来源**：
- `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-assets.md` 第 1-60 行
- `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-assets.md` 第 65-66 行

**核心规则**：

```
每张图必须写明：
- 本课专属状态（禁写"通用/复用/共享/generic/shared/common/placeholder"）
- 课题关键词
- 教学职责（观察/分类/指认/测量/搭建/记录/迁移）
- 构图留白
- 文字策略
- 生成来源（必须写明"由图片生成技能生成"）

至少 7 张本课专属、由图片生成技能生成的照片级真实图片
覆盖：封面 / 导入 / 操作观察 / 记录测量 / 应用迁移 / 课后实践
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\schema.md` 第 219-230 行 ppt_visual_asset | 仅 6 个字段（asset_id / source_prompt_id / storage_path / status / api_job_id / failed_reason），**无任何真实性或教学职责字段** |

**实施方式**：

**步骤 1**：schema.md 加 5 个新字段到 ppt_visual_asset：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dedicated | bool | required | 是否本课专属（禁 false for premium tier） |
| subject_keywords | list<string> | required | 课题关键词，用于检测复用 |
| teaching_role | enum | required | 7 类之一：observe / classify / identify / measure / build / record / transfer |
| composition_margin | text | optional | 构图留白说明 |
| generation_source | string | required | 必须包含「图片生成技能」或「imagegen」字样 |

**步骤 2**：rules.md 加 R050-R053 hard_block 规则：

| 新规则 | 检查内容 |
|--------|----------|
| R050 | premium tier 必须 ≥7 张本课专属真实图片 |
| R051 | ppt_visual_asset.description 不得含「通用/复用/共享/generic/shared/common/placeholder」 |
| R052 | image_assets.md 必填字段：dedicated / subject_keywords / teaching_role / generation_source |
| R053 | 真实图片必须覆盖 5 类必填场景：封面/导入/操作/应用迁移/课后实践 |

**工作量**：1 人日

---

### 吸收 3：精品门槛作为配置档位（**高 ROI**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\premium-benchmark-cuboid.md` 第 6-15 行

**核心规则**：

```
精品公开课最低 22 页
至少 7 张本课专属真实感图片
至少 10 种页面类型（45 页版至少 14 种）
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\schema.md` 第 33-42 行 project_config | `ppt_page_range: tuple<int,int> = (12, 16)`，**没有 quality_tier 概念** |
| `workflow\workflow.yaml` 第 105-112 行 project_config 节点 | 同上 |

**实施方式**：

**步骤 1**：schema.md 加新字段到 project_config：

```yaml
quality_tier: enum  # 新增
  default: standard
  values: [standard, premium, luxury]

# 不同 tier 的硬性下限
standard:
  min_pages: 12
  min_images: 0
  min_page_types: 5

premium:
  min_pages: 22
  min_images: 7
  min_page_types: 10

luxury:
  min_pages: 40
  min_images: 12
  min_page_types: 14
```

**步骤 2**：rules.md 加 R039 hard_block：

| 新规则 | 检查内容 |
|--------|----------|
| R039 | 根据 quality_tier 检查 min_pages / min_images / min_page_types 是否达到下限 |

**工作量**：1 人日

---

### 吸收 4：项目契约文件 `project.json`（**中 ROI**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\samples\cm-premium-real\project.json`

**示例结构**：

```json
{
  "schema_version": 1,
  "created": "2026-06-16",
  "course": {
    "title": "认识厘米",
    "subject": "数学",
    "grade": "二年级",
    "publisher": "..."
  },
  "workflow": {
    "stage": "delivery_real_photo_assets",
    "gates": {
      "source_research": "done",
      "lesson_plan": "done",
      "slide_director": "done",
      "visual_lock": "done",
      "assets": "done",
      "production": "done",
      "visual_enhancement": "done",
      "rendered_qa": "done",
      "delivery": "done"
    }
  },
  "delivery": {
    "expected_slide_count": 26,
    "required_outputs": ["output/*.pptx", "output/*.pdf", "output/QA报告.md"]
  }
}
```

**ShanHai-Edu 现状**：

| 目录 | 现状 |
|------|------|
| `storage\manual-fullchain-runs\20260621-5以内数的认识\` | **无 project.json**，状态由 _tools 目录的运行日志推断 |

**实施方式**：

**步骤 1**：写 `apps\api\app\init_project.py`，调用时生成：

```
<project_dir>/
├── project.json              ← 课程元信息 + 9 个 stage gates
├── sources/
│   ├── research-notes.md
│   ├── lesson-plan.md
│   └── slide-director-script.md
├── design/
│   ├── design-spec.md
│   └── spec-lock.md
├── assets/
│   ├── image-assets.md
│   └── video-storyboard.md
├── output/
│   └── (空，待最终交付)
└── qa/
    └── qa-checklist.md
```

**步骤 2**：每个 stage 的 ai_generate_done / user_approve 事件更新 project.json 对应 gate 字段。

**工作量**：1-2 人日

---

### 吸收 5：视觉基础约束作为强约束（**中 ROI**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-foundations.md` 第 18-48 行

**核心设计令牌**：

```
视觉锁定阶段必须先建立整套设计令牌，再开始生产：
- 文字档位（封面标题/页标题/任务卡标题/正文/数学结论/页脚动作条/页码 各自固定字号、字重、行距）
- 间距基线（8 点或 10 点）
- 色彩角色（主色/辅助色/强调色/成功/警示/中性/背景）
- 形状语言（圆角/线宽/阴影/标签/箭头/放大镜/记录框）
- 图标与小部件（尺寸/描边/填充/标签关系）
- 投影可读性 + 对比度（最低字号/低对比禁用）
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\schema.md` 第 44-53 行 visual_contract | 仅 4 字段（palette / style_keywords / font_preference / template_pptx），**无强制锁定机制** |
| `workflow\workflow.yaml` 第 113-122 行 visual_contract 节点 | 同上 |

**实施方式**：

**步骤 1**：schema.md 加 8 个字段到 visual_contract：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| palette | list<color> | required | 主色（现有） |
| style_keywords | list<string> | required | 风格关键词（现有） |
| font_preference | string | optional | 字体偏好（现有） |
| template_pptx | file | optional | 模板上传（现有） |
| **typography_scale** | object | required (premium tier) | 7 档字号：{ cover_title, page_title, card_title, body, math_conclusion, footer_action, page_number } |
| **spacing_baseline** | int | required (premium tier) | 8 或 10 点基线 |
| **color_roles** | object | required (premium tier) | 7 色：{ primary, secondary, accent, success, warning, neutral, background } |
| **shape_language** | object | required (premium tier) | 5 项：{ radius, stroke_width, shadow, label, arrow } |
| **icon_rules** | object | required (premium tier) | 图标尺寸/描边/标签规则 |

**步骤 2**：rules.md 加 R040-R041 hard_block：

| 新规则 | 检查内容 |
|--------|----------|
| R040 | premium tier 的 ppt_assembly_plan 必须引用的 visual_contract 包含完整 typography_scale / spacing_baseline / color_roles / shape_language / icon_rules |
| R041 | pptx_artifact 生成前必须验证 visual_contract.locked == true |

**工作量**：1-2 人日

---

### 吸收 6：QA 报告必须包含的具体证据项（**中 ROI**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\qa-contract.md` 第 60-77 行

**核心 15 条完成标准**：

```
1. 导演稿质量评分器通过
2. 精品交付门通过
3. 项目交付验收器通过
4. 全套 contact sheet 已人工查看
5. 重点页面已高清查看
6. PPTX 在 PowerPoint 中实际打开
7. 已完成字体字号和版式一致性审计
8. 已完成视觉基础约束审查
9. 已记录仍未完成的媒体或已知限制
10. 已核对本课专属图片资产
11. 已按 premium-benchmark-cuboid.md 检查
12. 已完成页面发散构图审查
13. 已完成空白页与半空白页复查
14. 输出目录已清理旧版残留和锁文件
15. 已完成版式自由度审查
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\rules.md` 第 533-582 行 R060-R063 | 仅 4 条收尾规则，**无"人工视觉证据""contact sheet 审查""最终文件版本核对"**等硬证据 |

**实施方式**：rules.md 的 R060 升级为 15 条完成标准清单，每条作为 hard_block 子项：

```yaml
R060:
  title: 最终交付完成标准
  severity: hard_block
  check_items:
    - id: E01
      desc: audit_courseware_quality.py 通过
    - id: E02
      desc: audit_premium_delivery.py 通过
    - id: E03
      desc: verify_project.py 通过
    - id: E04
      desc: contact sheet 全套人工查看（contact_sheet_reviewed: true）
    - id: E05
      desc: 重点页高清查看（highlight_pages_reviewed: true）
    - id: E06
      desc: PPTX 在 PowerPoint 中实际打开（pptx_opened: true）
    - id: E07
      desc: 字体字号版式一致性审计（typography_audit_passed: true）
    - id: E08
      desc: 视觉基础约束审查（visual_foundations_audit_passed: true）
    - id: E09
      desc: 已知限制记录（known_limitations_recorded: true）
    - id: E10
      desc: 本课专属图片资产核对（dedicated_assets_verified: true）
    - id: E11
      desc: premium-benchmark 检查（premium_benchmark_passed: true）
    - id: E12
      desc: 页面发散构图审查（layout_divergence_reviewed: true）
    - id: E13
      desc: 空白页/半空白页复查（blank_page_reviewed: true）
    - id: E14
      desc: 输出目录单 PPTX + 无锁文件（output_clean: true）
    - id: E15
      desc: 版式自由度审查（layout_freedom_reviewed: true）
```

**工作量**：0.5 人日

---

### 吸收 7：禁止项清单（**低 ROI 但必须**）

**来源**：
- `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\SKILL.md` 第 140-146 行「禁止捷径」
- `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\qa-contract.md` 第 50-56 行「用户可见层审计」

**核心禁止项**：

```
- 不得用代码绘制/程序位图/PIL/SVG/canvas 冒充真实图片
- 不得把数学文字烘焙进图片
- 不得在学生可见层出现 A版/B版/C版/debug/TODO/AI生成/生成器/验收/工具名/工作流标签
- 不得只在一个软件中检查（必须 PowerPoint + 另一渲染链路对比）
- 不得在正式 output 保留多个候选 PPTX 或旧版残留
- 不得用装饰数量代替教学功能
- 不得用"留白很多"掩盖页面教学动作不足
- 不得换版式就等于去模板化（必须状态演化）
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\rules.md` 第 271-282 行 R026 | 仅 1 条「学生可见层不得暴露内部信息」，**范围窄** |

**实施方式**：合并 R026 + 新增 7 条禁止项到 rules.md：

| 新规则 | 检查内容 |
|--------|----------|
| R026 (升级) | 学生可见层禁止词：原 R026 + 新增 A版/B版/C版/信息饱满版 |
| R042 | ppt_visual_asset.generation_source 不得含「代码绘制/程序位图/PIL/SVG/canvas」 |
| R043 | 同一 output 目录不得含 ≥2 个 PPTX 主交付物 |
| R044 | output 目录不得含 `~$*.pptx` Office/WPS 临时锁文件 |
| R045 | 数学事实（公式/题干/答案/单位/刻度）不得在 ppt_visual_asset 中烘焙进图片 |
| R046 | 单页正文字数 ≤ 170 字（参考项目阈值） |
| R047 | 单页项目符号 ≤ 6 条（参考项目阈值） |

**工作量**：0.5 人日

---

### 吸收 8：状态变体 > 换皮（**低 ROI 但有哲学价值**）

**来源**：`E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\AI-youjiao-PPT精品生产总纲.md` 第 103-119 行「v20 复盘：状态变体优先于换皮」

**核心规则**：

```
- 同一课的主对象原样复用不得超过 3 次，且连续复用时必须至少改变
  数量/视角/距离/动作/错例/场景中的 2 项
- 每课至少建立 2-3 个专属状态变体组件
- 周长：生活轮廓/绕边操作/对照判断（3 个变体）
- 厘米：对齐测量/1cm 放大/排序比较（3 个变体）
- 余数：分组/余量槽/算式身份（3 个变体）
```

**ShanHai-Edu 现状**：

| 文件 | 现状 |
|------|------|
| `workflow\rules.md` | **无类似规则** |
| `workflow\schema.md` | 角色字典 character_dict 没有"状态变体"概念 |

**实施方式**：

**步骤 1**：schema.md 在 character_dict 加可选字段：

```yaml
state_variants:
  type: list<object>
  required: optional
  min_count: 0  # premium tier 时 required 且 ≥2
  fields:
    - variant_id: string
    - variant_description: text
    - scenario: text   # 场景描述
    - action: text     # 动作/状态变化
```

**步骤 2**：rules.md 加 R048 warning 规则：

| 新规则 | 检查内容 |
|--------|----------|
| R048 | premium tier 必须为每页主对象建立 ≥2 个 state_variant |
| R049 | 同一 character_id 在 PPT 中出现 >3 次时，每次必须改 2 项状态 |

**工作量**：0.5 人日

---

## 三、不该吸收的（保持 ShanHai-Edu 差异点）

| 参考项目没有 | ShanHai-Edu 有 | 不要照搬 |
|--------------|----------------|----------|
| 状态机 / cascade | ✓ 有 | 不要为了反模板破坏状态机 |
| 用户编辑 | ✓ 有 | 不要改成"一次性脚本流" |
| 飞轮 | ✓ 设计中 | 不要让反模板规则覆盖飞轮数据 |
| 多课管理 | ✓ 有 | 不要每课独立目录丢上下文 |
| Web UI | ✓ 设计中 | 不要回退到 CLI 模式 |

**核心原则**：参考项目是 ShanHai-Edu 的「PPT 生产内核」；ShanHai-Edu 的价值是**给生产内核套上用户编辑 + 飞轮 + 状态机的壳**。壳不动，内核可吸收。

---

## 四、具体吸收路径（按 MVP 优先分 3 阶段）

### 阶段 1：最高 ROI（1 周）

| 序号 | 动作 | 对应吸收点 | 工作量 | 文件 |
|------|------|------------|--------|------|
| 1 | 加 R033-R038 反模板硬规则 | 吸收 1 | 0.5 人日 | `workflow\rules.md` |
| 2 | ppt_visual_asset 加 5 字段（dedicated / subject_keywords / teaching_role / composition_margin / generation_source）| 吸收 2 | 0.5 人日 | `workflow\schema.md` |
| 3 | 加 R050-R053 图片资产硬规则 | 吸收 2 | 0.5 人日 | `workflow\rules.md` |

**阶段 1 合计**：1.5 人日

### 阶段 2：高/中 ROI（2-3 周）

| 序号 | 动作 | 对应吸收点 | 工作量 | 文件 |
|------|------|------------|--------|------|
| 4 | visual_contract 升级为 12 字段设计令牌 | 吸收 5 | 1 人日 | `workflow\schema.md` |
| 5 | project_config 加 quality_tier 字段 + 3 档配置 | 吸收 3 | 0.5 人日 | `workflow\schema.md` |
| 6 | 加 R039 精品门槛规则 + R040-R041 视觉令牌规则 | 吸收 3 / 5 | 0.5 人日 | `workflow\rules.md` |
| 7 | R060 升级为 15 条完成标准清单 | 吸收 6 | 0.5 人日 | `workflow\rules.md` |

**阶段 2 合计**：2.5 人日

### 阶段 3：长 ROI（4-6 周）

| 序号 | 动作 | 对应吸收点 | 工作量 | 文件 |
|------|------|------------|--------|------|
| 8 | 写 `apps\api\app\init_project.py`（生成项目目录结构 + project.json）| 吸收 4 | 1-2 人日 | `apps\api\app\init_project.py` |
| 9 | 移植参考项目 `audit_premium_delivery.py` 到 ShanHai-Edu | 吸收 6 实施 | 2-3 人日 | `apps\api\app\audit_scripts\audit_premium_delivery.py` |
| 10 | 合并 R026 + 新增 7 条禁止项 R042-R047 | 吸收 7 | 0.5 人日 | `workflow\rules.md` |
| 11 | character_dict 加 state_variants 字段 + R048-R049 | 吸收 8 | 0.5 人日 | `workflow\schema.md` + `workflow\rules.md` |

**阶段 3 合计**：4.5-6.5 人日

### 总计：8.5-10.5 人日（约 2 周）

---

## 五、实施建议

### 5.1 不要"全部照搬"

参考项目是 PPT 子系统的「最佳实践」，但**不是 ShanHai-Edu 的完整答案**。三个吸收原则：

1. **边做边吸**：每次内测 PPT 失败时反问"参考项目有这条规则吗？"，命中的就吸收
2. **拒绝过度设计**：吸收点 8（state_variants）是哲学参考，不是必须实现
3. **保持壳不动**：状态机 / 用户编辑 / 飞轮是差异化资产，吸收时不要破坏

### 5.2 优先级判断

| 如果只能做一件事 | 做吸收 1（反模板硬规则） |
|------------------|------------------------|
| 投入 1 周能做的 | 阶段 1 全部 |
| 投入 2 周能做的 | 阶段 1 + 阶段 2 |
| 投入 4 周能做的 | 阶段 1 + 2 + 3（完整吸收）|

### 5.3 风险与回退

- **风险 1**：新加的 R033-R038 规则可能误杀合理的连续相同构图（如 22 页中"5 页连续算式页"是合理的）
  - **回退**：规则加 override 机制（用户可标注「教学法上确需连续」+ 计入飞轮）
- **风险 2**：visual_contract 字段升级会破坏现有项目数据
  - **回退**：新增字段设 optional，旧项目读不到也不报错
- **风险 3**：quality_tier 切换时旧项目如何升级
  - **回退**：旧项目保持 standard 默认值，premium 由用户主动开启

---

## 六、参考来源清单

### 6.1 参考项目根目录

| 文件 | 路径 |
|------|------|
| 根目录 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\` |
| 项目入口 README | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\README.md` |
| 项目规则 AGENTS | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\AGENTS.md` |
| 精品生产总纲 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\AI-youjiao-PPT精品生产总纲.md` |
| 精品 PPT 验收清单 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\docs\精品PPT验收清单.md` |

### 6.2 参考项目 skill 子目录

| 文件 | 路径 |
|------|------|
| Skill 入口 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\SKILL.md` |
| 工作流说明 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\工作流说明.md` |

### 6.3 参考项目 references 目录（核心规则来源）

| 规则文件 | 路径 | 用途 |
|----------|------|------|
| 九阶段工作流 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\workflow.md` | 工作流架构参考 |
| 页面发散规则 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-divergence.md` | 吸收 1 来源 |
| 视觉基础约束 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-foundations.md` | 吸收 5 来源 |
| 视觉资产管理 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-assets.md` | 吸收 2 来源 |
| QA 契约 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\qa-contract.md` | 吸收 6 / 7 来源 |
| 精品标杆 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\premium-benchmark-cuboid.md` | 吸收 3 来源 |
| 教学设计 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\teaching-design.md` | 教学法参考 |
| 视觉增强 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\references\visual-enhancement.md` | 增强版策略 |

### 6.4 参考项目 scripts 目录（可移植审计脚本）

| 脚本 | 路径 | 工作量 |
|------|------|--------|
| 精品交付门 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\scripts\audit_premium_delivery.py` | 2-3 人日移植 |
| 课件质量评分 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\scripts\audit_courseware_quality.py` | 2-3 人日移植 |
| 项目验证 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\scripts\verify_project.py` | 1-2 人日移植 |
| 项目初始化 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\scripts\init_project.py` | 1-2 人日移植 |
| 资产规划草稿 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\skill\ai-youjiao-ppt\scripts\draft_asset_plan.py` | 1 人日移植 |

### 6.5 参考项目 samples 目录（真实交付样例）

| 样例 | 路径 | 说明 |
|------|------|------|
| 认识厘米精品 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\samples\cm-premium-real\` | 26 页交付，含 pptx/pdf/contact-sheet/QA 报告 |
| 项目契约 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\samples\cm-premium-real\project.json` | 吸收 4 来源 |
| 图片资产说明 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\samples\cm-premium-real\assets\image-assets.md` | 吸收 2 实例参考 |
| 设计规格 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\samples\cm-premium-real\design\design-spec.md` | 吸收 5 实例参考 |

---

## 七、变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-06-22 | 初版，从 AI-youjiao-PPT-workflow-最新版 提炼 8 个吸收点 | Claude |

---

## 八、相关文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| ShanHai-Edu PRD | `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\docs\PRD.md` | 第一性原理来源 |
| ShanHai-Edu workflow.yaml | `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\workflow.yaml` | 待修改的目标文件 |
| ShanHai-Edu rules.md | `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\rules.md` | 待修改的目标文件 |
| ShanHai-Edu schema.md | `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\schema.md` | 待修改的目标文件 |
| ShanHai-Edu state_machine.md | `E:\desktop\AI\02_Agents\lab\ShanHaiEdu\workflow\state_machine.md` | 不动（差异化资产）|
| 参考项目总纲 | `E:\desktop\AI-youjiao-PPT-workflow-最新版(1)\AI-youjiao-PPT精品生产总纲.md` | 反模板规则哲学来源 |