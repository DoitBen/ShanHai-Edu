# Node 03 PPT 页面脚本 — DeepSeek prompt（细粒度 13 字段，逐页生成）
version: 1.0
provider: deepseek
node_id: ppt_page_script

---

{{include shared/system_role.md}}

## 你的任务

为已 approved 的 PPT 总装方案，逐页生成符合 schemas/ppt_page_script.schema.json 的页面脚本 JSON。

**注意：本任务采用「一页一审」模式**——每页生成后立即由逐页审查智能体校验，
不通过的会被打回让你单独重做该页。所以**质量重于数量，宁可慢也要每页都过**。

## 输入

### 当前要生成第几页
```
page_index: {{page_index}}
```

### 上一页摘要（用于衔接，可空）
```
{{previous_page_summary}}
```

### 上游 approved 产物
```json
{
  "ppt_assembly_plan": {{ppt_assembly_plan}},
  "lesson_plan": {{lesson_plan}},
  "character_dict": {{character_dict}},
  "visual_contract": {{visual_contract}}
}
```

{{include shared/seed_params_block.md}}
{{include shared/flywheel_samples_block.md}}

## 13 个字段逐条说明

| # | 字段 | 注意 |
|---|---|---|
| 1 | `core_competency` | 从 11 个新课标核心素养中选 1-2 个（不要选超过 2 个） |
| 2 | `page_objective` | ≤30 字，单一动词驱动（"理解"、"判断"、"计算"等） |
| 3 | `student_action` | **必填**，从 14 词表选 1。封面 / 目录 / 纯视频页可写 null 并在 `accuracy_notes` 写明例外原因 |
| 4 | `page_type` | 必须与总装方案 `page_type_quota` 的配比一致 |
| 5 | `main_visual` | description + serves_purpose；serves_purpose 不得是"装饰"或"decoration"（R021） |
| 6 | `character_refs` | 引用 character_dict 中的 character_id，不存在的 ID 会被 R032 拒 |
| 7 | `image_prompts` | 待生图清单。real_life_scene=true 时优先生活场景。aspect_ratio 必须是 16:9 / 1:1 / 9:16 |
| 8 | `math_assertions` | 公式/数字/单位/答案。editable_layer **只能** 是 ppt_text / ppt_shape / ppt_chart（R006），禁止 ppt_image / video |
| 9 | `zone_layout` | 三区分别一句话描述 |
| 10 | `evidence_requirement` | **判断 / 练习 / 说理类页面必填**（R022） |
| 11 | `accuracy_notes` | 教师备注层。最终学生层看不到（R026 守护） |
| 12 | `link_to_prev_page` | 一句话衔接上一页 |
| 13 | `density_limits` | body_text_max ≤25，info_chunks_max ≤5（R025） |

## 11 类核心素养枚举

number_sense / quantity_sense / symbol_awareness / operation_ability / geometric_intuition / spatial_concept / reasoning_awareness / data_awareness / model_awareness / application_awareness / innovation_awareness

## image_prompts 字段示例

```json
{
  "prompt_id": "page_03_visual_01",
  "description": "明亮教室桌面上摆着两张桌布，左侧蓝色方形，右侧绿色长方形，俯视角度。卡通扁平风格。",
  "knowledge_link": "对比不同形状的面积感知",
  "real_life_scene": true,
  "character_refs": [],
  "aspect_ratio": "16:9"
}
```

**不得**在 description 里写公式、数字、答案——这些走 `math_assertions` 字段（R052）。

## math_assertions 字段示例

```json
{
  "content": "长方形面积 = 长 × 宽",
  "answer": "面积 S = 5 × 3 = 15（平方厘米）",
  "editable_layer": "ppt_text"
}
```

## 红线总结

- 任一字段不符合上面规则，会被审查智能体 hard_block
- 不得在学生可见的字段里写"准确性提醒""QA""任务包""task_id"等内部词
- 角色字典中没定义的角色 ID 不得引用

{{include shared/output_format_json.md}}
