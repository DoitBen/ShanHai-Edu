# shared/seed_params_block.md
# 种子参数注入模板（在节点 prompt 里引用）
version: 1.0

---

## 本次生成的种子参数

{{#if seed_params}}
- 语言风格：{{seed_params.language_style}}
  - academic：学术严谨，多用术语和定义
  - research：教研化表达，平衡严谨和可读
  - classroom：偏课堂口语，便于教师宣讲
- 详略度：{{seed_params.verbosity}}
  - concise：精炼，只写关键
  - moderate：适中
  - detailed：详细，多展开
- 举例倾向：{{seed_params.example_tendency}}
  - life：偏生活情境（操场、超市、厨房）
  - math：偏数学情境（图形、数轴、算式）
  - history：偏历史 / 科普背景
- 探究强度：{{seed_params.inquiry_intensity}}
  - conservative：保守，按教材结构走
  - balanced：平衡，加适量探究环节
  - aggressive：激进，重设计探究链
{{#if seed_params.free_text_hint}}
- 用户的额外指示："{{seed_params.free_text_hint}}"
{{/if}}
{{/if}}

请按上述参数生成内容。
