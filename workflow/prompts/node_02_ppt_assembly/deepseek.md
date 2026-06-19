# Node 02 PPT 总装方案 — DeepSeek prompt
version: 1.0
provider: deepseek
node_id: ppt_assembly_plan

---

{{include shared/system_role.md}}

## 你的任务

为已 approved 的公开课教案，生成符合 schemas/ppt_assembly_plan.schema.json 的总装方案 JSON。

## 输入

### 项目配置（含目标页数范围）
```json
{{project_config}}
```

### 公开课教案（上游 approved）
```json
{{lesson_plan}}
```

{{include shared/seed_params_block.md}}
{{include shared/flywheel_samples_block.md}}

## 输出要求

| 字段 | 含义 | 关键约束 |
|---|---|---|
| `persistent_context` | 持续情境（例"操场跑步"） | 全套 PPT 围绕同一情境，避免散乱 |
| `page_count_target` | 计划页数 | 必须在 project_config.ppt_page_range 内 |
| `page_type_quota` | 11 类页面类型配比 | **必须包含 ≥1 页 blackboard_summary（R023）**，**至少覆盖 5 类（R024）** |
| `action_chain` | 学生动作链 | 从 14 词表中选，覆盖导入 / 探究 / 练习 / 小结 |
| `inquiry_path` | 探究链路 | 几何课："生活物体 → 抽象图形 → 结构特征 → 关系发现 → 证据判断"；运算课："生活问题 → 数量关系 → 算法探究 → 算理解释 → 迁移练习" |
| `ppt_video_division` | PPT 与导入视频的分工 | PPT 负责精确数字 / 公式 / 题干 / 答案 / 板书；视频负责开场兴趣 / 故事钩子 |
| `material_requirements` | 素材需求清单 | 一行一个，如 "封面底图"、"角色正面卡通"、"操作教具" |
| `editable_text_rules` | 精确文本层规则 | 明示哪些必须是 PPT 可编辑文本（公式 / 数字 / 单位 / 答案） |
| `accuracy_warnings` | 准确性提醒 | 列出本课最容易被 AI 误写 / 误画的 3-5 条 |

## 11 类页面类型枚举

life_observation / role_task / inquiry_operation / step_reveal / dual_image_compare / error_judge / practice_challenge / evidence_reasoning / math_id_card / blackboard_summary / homework_practice

## 14 类学生动作词表

look / touch / arrange / count / divide / compare / circle / link / draw / speak / judge / fill / correct / find

## 红线

- page_type_quota 中 `blackboard_summary` 必须 ≥1
- 配比总和必须等于 page_count_target
- 不得规划"全是讲解页"的方案

{{include shared/output_format_json.md}}
