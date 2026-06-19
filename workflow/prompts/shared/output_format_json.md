# shared/output_format_json.md
# 通用 JSON 输出格式约束模板
version: 1.0

---

## 输出格式

**只输出一个合法的 JSON 对象**，不要 markdown 包装，不要前后任何说明文字。

如果使用支持 JSON mode 的 provider（GPT-4 / Claude 3.5 / DeepSeek-V3）：
- 启用 `response_format: { type: "json_object" }`
- 输出必须 `JSON.parse` 通过

如果使用 Markdown 包装的 provider（Claude）：
- 把 JSON 放在 ```json ... ``` 代码块中
- 解析器会自动剥离包装

## JSON Schema 校验

调用层会用 `schemas/{node_id}.schema.json` 校验你的输出。

校验失败的常见原因：
1. 字段名拼错（如 `studentAction` 而不是 `student_action`）
2. 枚举值不在白名单（如 `student_action: "discuss"` 不在 14 词表）
3. 必填字段缺失（如忘了写 `density_limits`）
4. 类型错误（如 `page_index: "1"` 应为整数）

你被允许重试 1 次。第二次仍然格式错的话，产品会切到 fallback provider。
