# shared/flywheel_samples_block.md
# 飞轮已通过样例注入模板
version: 1.0

---

## 该用户最近通过的同类节点样例（参考其风格，但不是抄袭）

{{#if flywheel_samples}}
{{#each flywheel_samples}}
### 样例 {{@index}}（{{this.project_name}}）
{{this.snippet}}

---
{{/each}}

注意：
- 这些是该教研员**审过的版本**，反映了他的偏好
- 不要复制内容，**只学习风格、用词、结构密度**
- 当前任务的课题、年级、教材都不同，内容必须重新生成
{{else}}
（该用户没有过往同类样例，按 schema 默认生成。）
{{/if}}
