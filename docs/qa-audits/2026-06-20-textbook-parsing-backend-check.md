# T038/T040 教材解析后端阶段验收记录

- 日期：2026-06-20
- 角色：首席系统架构师代执行后端阶段性验收
- 范围：只验收后端教材 PDF 解析与教案输入链路，不做前端浏览器回归，不做上线验收
- 结论：未通过

## 验收目标

验证后端是否已完成以下能力：

1. 上传 fixture 教材 PDF。
2. 触发教材解析。
3. 支持 PDF/MinerU 解析入口，而不是仅支持 `.txt` / `.md`。
4. 识别并回填一年级、人教版、上册、数学等基础字段。
5. 生成知识点列表，至少覆盖或映射到“5以内数的认识”。
6. 支持知识点锚定并抽取 Markdown。
7. `lesson_plan/generate` 可优先使用已选知识点 Markdown 作为输入。

## 新鲜验证

### 后端测试套件

命令：

```powershell
python -m pytest apps\api\tests -q
```

结果：

```text
33 passed, 2 xfailed
```

说明：现有后端测试通过，但测试覆盖仍停留在已有 `.txt` 教材与视频链 schema 校验；未覆盖 T038/T040 的 PDF/MinerU/知识点 Markdown 链路。

### fixture PDF 红线验证

测试输入：

```text
fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf
```

过程：

1. 创建项目，项目配置为数学、一年级、人教版、上册。
2. 上传上述 PDF 到 `/projects/{project_id}/textbook`。
3. 调用 `/projects/{project_id}/nodes/textbook_parse/generate`。

结果：

```json
{
  "ok": false,
  "error": {
    "code": "GENERATION_INPUT_INVALID",
    "message": "Unsupported textbook type for MVP: .pdf",
    "retryable": false
  }
}
```

## 缺陷清单

### 严重：后端仍不支持 PDF 教材解析

- 复现路径：上传 fixture PDF 后调用 `textbook_parse/generate`。
- 实际结果：返回 `400 / GENERATION_INPUT_INVALID`，提示 `Unsupported textbook type for MVP: .pdf`。
- 影响：T038 核心目标未达成；前端无法接入真实“解析教材”按钮。
- 建议：后端需在 PDF 上传后接入项目内 `skills\pdf` / MinerU，或至少提供可测试的本地 fixture fallback 解析链路。

### 严重：未发现知识点列表与知识点 Markdown 抽取 API

- 复现路径：检索后端路由与服务层，未发现教材大纲解析、知识点列表、知识点锚定抽取 Markdown 的接口。
- 影响：无法满足“课程知识点下拉框”和“选择知识点后抽取 Markdown”的需求。
- 建议：补充明确 API 契约，例如解析任务接口、知识点列表接口、知识点 Markdown 获取接口，或在 `textbook_parse` 节点内容中返回稳定字段。

### 严重：`lesson_plan/generate` 未验证读取知识点 Markdown 输入

- 复现路径：当前 PDF 链路无法产生知识点 Markdown，无法进入 T040 验收。
- 影响：教案节点仍可能只使用旧的 `textbook_parse` JSON，而不是用户指定知识点 Markdown。
- 建议：补测试证明 `lesson_plan/generate` 会优先读取已选知识点 Markdown，并在教案内容中保留教材来源页码/标题。

## 通过项

- 后端现有测试套件通过：`33 passed, 2 xfailed`。
- PDF 上传接口本身可保存 PDF asset。

## 当前判断

T038/T040 后端阶段验收未通过。当前不能让前端 T039 按真实接口继续联调，只能让前端做 UI 壳和 mock 状态。

## 返工要求

后端需要至少补齐：

1. PDF 教材解析入口，不能再在 `textbook_parse/generate` 阶段拒绝 `.pdf`。
2. 基础字段识别结果：subject、grade、textbook_version、volume。
3. 知识点列表，至少覆盖“5以内数的认识”。
4. 选择知识点后生成 Markdown，并返回或保存 markdown path。
5. `lesson_plan/generate` 读取该 Markdown 的测试。

