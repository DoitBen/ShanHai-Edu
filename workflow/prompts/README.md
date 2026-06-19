# prompts/ — Prompt 模板

版本：v1
角色：节点 × provider 的 prompt 模板存放处。LLM 调用层按 node_id + provider 组合查找。

## 目录组织

```
prompts/
  README.md                          ← 本文件
  shared/
    system_role.md                   ← 通用系统提示词
    output_format_json.md            ← JSON 输出格式约束模板
    seed_params_block.md             ← 种子参数注入模板
    flywheel_samples_block.md        ← 飞轮已通过样例注入模板

  node_01_lesson_plan/
    deepseek.md                      ← 默认
    claude.md                        ← fallback
    gpt.md                           ← fallback

  node_02_ppt_assembly/
    deepseek.md
    claude.md

  node_03_ppt_page_script/
    deepseek.md
    claude.md
    review_agent.md                  ← 逐页审查智能体专用

  node_4b_intro_video_script/
    deepseek.md
    claude.md

  node_4c_intro_video_screenplay/
    deepseek.md
    claude.md

  node_05a_ppt_visual_asset/
    image_gen_prompt.md              ← 给 gpt-image-2 的描述模板

  node_05b_intro_video_asset/
    image_gen_prompt.md

  node_06_storyboard/
    deepseek.md
    claude.md
    model_prompt_template.md         ← 给 omni_flash-10s 的拼装模板

  node_08_video_generation/
    omni_flash_prompt.md             ← 视频生成 prompt 模板

  supervisor/
    page_reviewer.md                 ← PPT 逐页审查智能体（Claude）
    output_validator.md              ← 通用产物校验（按 schema.md 字段验）
```

## 命名约定

- 文件名 = provider 名（lowercase）
- 同节点多 provider 的 prompt 必须输出同结构 JSON（差异只在表达方式）
- 审查智能体单独建文件，不混在生成模板里

## prompt 模板的通用结构

每个 `.md` 文件按以下骨架写：

```markdown
# Node {node_id} — {provider} prompt

## System
（系统级角色设定，从 shared/system_role.md 继承 + 节点专属补充）

## Inputs
- {{upstream_approved_outputs}}：上游 approved 产物 JSON
- {{specs}}：规范摘要（从 schema.md + rules.md 抽取相关条目）
- {{seed_params}}：种子参数
- {{flywheel_samples}}：飞轮检索到的近 3 个 approved 样例片段

## Task
（节点的核心任务描述，引用 schema.md 对应节点的字段清单）

## Output Format
（要求输出符合 schema.md 字段定义的 JSON）

## Constraints
（引用 rules.md 中对应 trigger_node 的规则，明确告诉 LLM 不要触犯）

## Examples
（few-shot：1 个 good case + 1 个 bad case 标注违反了哪条规则）
```

## prompt 与 schema/rules 的关系

prompt 不再是产品规则的源头。它的位置是：

```
schema.md → 定义字段
rules.md  → 定义机器可验规则
prompt    → 引导 LLM 输出符合 schema + 不触犯 rules 的内容
```

当 schema 或 rules 变更时，prompt 也要同步更新（在 CI 里加一致性检查）。

## 跨 provider 适配原则

同节点不同 provider 的 prompt 差异点：

| 维度 | DeepSeek | Claude | GPT |
|---|---|---|---|
| 输出格式 | JSON 严格模式 | JSON 在 ```json 块中 | JSON mode（API 强约束） |
| 系统提示词长度 | 简洁 | 可详细 | 中等 |
| 中文表达倾向 | 自然 | 偏书面 | 偏直白 |
| few-shot 数量 | 1-2 | 0-1（context 够长可不放） | 2-3 |

## v1 必须先写的 prompt（按优先级）

| 优先级 | 文件 |
|---|---|
| P0 | shared/system_role.md（所有节点继承） |
| P0 | shared/output_format_json.md |
| P0 | node_01_lesson_plan/deepseek.md |
| P0 | node_02_ppt_assembly/deepseek.md |
| P0 | node_03_ppt_page_script/deepseek.md |
| P0 | supervisor/page_reviewer.md（逐页审查智能体） |
| P0 | node_06_storyboard/model_prompt_template.md |
| P0 | node_08_video_generation/omni_flash_prompt.md |
| P1 | 其他节点的 deepseek.md |
| P1 | 所有节点的 claude.md（fallback） |
| P2 | 所有节点的 gpt.md（二级 fallback） |

## v1 不在 prompts/ 范围内的

- 教学法长文（给人看的）→ 进 v1.x 的「教程系统」
- 历史叙事和事故复盘 → 留在 `执行规范/` 老目录
- 项目级用户偏好文本框 → 进 prompt 时作为变量注入，不写死

## prompt 版本管理

- 每个 prompt 文件顶部带 `version: x.y` 和 `last_updated`
- 重大变更时 prompt 文件加备份 `.bak` 不删旧版
- 跑生成时记录用了哪个 prompt 版本（写入 `node_versions.prompt_version`）

## 与逐页审查智能体的接口约定

`supervisor/page_reviewer.md` 接受输入：

```json
{
  "page_index": 1,
  "page_script": { ... 按 schema.md 节点 3 字段 ... },
  "previous_page_summary": "上一页摘要（可空）",
  "applicable_rules": [ "R020", "R021", "R022", ... ]
}
```

输出固定结构：

```json
{
  "passed": true | false,
  "hard_blocks": [
    { "rule_id": "R026", "reason": "页面暴露准确性提醒" }
  ],
  "warnings": [
    { "rule_id": "R020", "reason": "学生动作字段为空" }
  ],
  "suggestions": "可选的改进建议"
}
```

状态机按 `passed` + `hard_blocks` 决定是否升级到 `blocked`。

## 待写但 v1 推迟的 prompt

- 跨项目复用的"风格学习" prompt（v2）
- 用户偏好画像的可视化生成 prompt（v2）
- 对标 PPT 的风格提取 prompt（v1 用现有 skill，不自写）
- AI 味检测 prompt（v1.x）
