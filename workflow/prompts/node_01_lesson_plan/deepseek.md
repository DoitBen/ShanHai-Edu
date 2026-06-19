# Node 01 公开课教案 — DeepSeek prompt
version: 1.0
last_updated: 2026-06-19
provider: deepseek
node_id: lesson_plan

---

{{include shared/system_role.md}}

## 你的任务

为以下小学数学公开课，生成符合 schemas/lesson_plan.schema.json 的教案 JSON。

## 输入

### 项目元数据
```json
{{project_meta}}
```

### 项目配置
```json
{{project_config}}
```

{{include shared/seed_params_block.md}}

{{include shared/flywheel_samples_block.md}}

## 输出要求

输出 JSON 对象，包含以下 6 个字段：

| 字段 | 含义 | 注意 |
|---|---|---|
| `textbook_anchor` | 教材依据 | 必须精准到「{教材版本}{年级}{上下册}第X单元/页码 课题《X》」 |
| `teaching_objectives` | 教学目标 | 围绕新课标 2022 核心素养（数感/几何直观等），3 条左右 |
| `key_difficulty` | 教学重难点 | 重点和难点分别陈述 |
| `teaching_flow` | 教学流程 | 导入 / 探究 / 练习 / 小结四段式，每段一句话 |
| `blackboard_design` | 板书设计 | 一屏内呈现核心概念，结构特征 / 方法步骤 / 关系发现分区 |
| `intro_designs` | 三类九套导入设计 | 见下面详细说明 |

### intro_designs 字段（重要）

生成 9 个导入设计方案，每类（科普 / 应用 / 故事）3 个：

```json
{
  "design_id": "design_science_01",   // 严格按 design_{type}_{NN} 格式
  "type": "science",                  // science / application / story
  "title": "方案名（10 字内）",
  "hook": "钩子描述（50 字内，描述视频开场怎么抓住学生）",
  "anchor_to_lesson": "课程锚点（如何自然引出本课题）",
  "recommend_score": 4,               // 1-5 推荐分
  "risk_note": "适配风险（可选）"
}
```

## 红线约束

- 教学目标不得写"了解 / 知道"这种空目标，必须可观察可检测
- 板书设计不得超过 50 字
- 钩子描述里**不得出现真人未成年人、真实课堂场景描述**——这条会被规则 R045 验
- 不得写任何中英混杂的奇怪术语

## 输出格式

{{include shared/output_format_json.md}}
