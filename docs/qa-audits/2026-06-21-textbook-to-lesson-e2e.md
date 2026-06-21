# T041 教材解析到教案生成端到端回归执行记录

- 日期：2026-06-21
- 角色：测试工程师
- 任务：T041，教材解析到教案生成端到端回归
- 执行环境：本地隔离演示环境，不做上线验收
- 当前结论：通过

## 结论

T041 本轮结论：通过。

本结论由两段证据组成：

- API fake 模式在 `http://127.0.0.1:8141` 启动，`/health` 正常。
- API 主链路沿用本轮已通过证据：创建项目、上传 fixture PDF、生成 `textbook_parse`、确认 `textbook_parse`、生成 `lesson_plan`。
- `textbook_parse` 产物包含目标字段、目标知识点和 Markdown。
- `lesson_plan` 产物来源为 `kp_001`，Markdown 包含“5以内数的认识”。
- manifest 推进到 `textbook_parse=approved`、`lesson_plan=needs_review`。
- UI 子链路补测已通过：浏览器内完成“上传 PDF → 点击解析教材 → 解析中状态 → 字段回填 → 字段手改 → 知识点下拉 → Markdown 预览”。
- 浏览器控制台未发现阻断性应用级 `error/warn`。

上一轮阻塞原因是 in-app browser 文件注入能力不足。本轮改用支持文件上传的 Chrome DevTools 浏览器环境完成补测，阻塞解除。

## 环境

| 项 | 实际值 |
|---|---|
| API | `http://127.0.0.1:8141` |
| Web | `http://127.0.0.1:3141` |
| Storage | `storage-t041-textbook-to-lesson-e2e` |
| Provider | `fake` |
| Web 模式 | 真实 API 模式 |
| 旧 8000 实例 | 未复用 |
| 测试项目 | `T041-教材到教案回归-633528` |
| 项目 ID | `proj_34be317be27c` |
| UI 子链路补测项目 | `T041-UI子链路-633528` |
| UI 子链路补测项目 ID | `proj_358af9eac8c7` |

## 测试资料

| 资料 | 状态 |
|---|---|
| `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf` | 已用于 API 上传 |
| `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\5以内数的认识_结构化文字教案.md` | 后端解析产物来源，Markdown 已回填 |

## 执行清单

| 编号 | 测试项 | 实际结果 | 结论 |
|---|---|---|---|
| 1 | 后端 API 健康检查 | `/health` 返回 `status=ok`、`workflow_version=1.0.0` | 通过 |
| 2 | Web 真实 API 模式可打开 | `GET /` 返回 200，页面登录真实 API 模式用户 `qa-t041` | 通过 |
| 3 | 新建项目可上传 fixture PDF | UI 第 2 步上传成功，页面显示 `1上-人教版小学数学课本（2024新版）.pdf`；网络请求 `POST /projects/proj_358af9eac8c7/textbook` 返回 200 | 通过 |
| 4 | 点击“解析教材”后出现解析中状态 | UI 按钮显示 `解析中…`，页面显示 `正在上传教材并调用后端解析…` | 通过 |
| 5 | 解析完成后字段回填 | UI 显示教材标题“人教版小学数学一年级上册”，字段为数学、一年级、人教版、上册 | 通过 |
| 6 | 字段支持手工修改 | 年级下拉从“一年级”改为“二年级”，顶部摘要同步变为 `数学 · 二年级` | 通过 |
| 7 | 知识点下拉包含“5以内数的认识” | 展开知识点下拉，唯一选项为“5以内数的认识”且处于选中状态 | 通过 |
| 8 | 选择该知识点后展示 Markdown 预览 | UI 显示 `knowledge-points/kp_001.md` 和 Markdown 预览内容 | 通过 |
| 9 | Markdown 内容包含“5以内数的认识” | API 产物包含目标文本 | 通过 |
| 10 | 确认教材解析后进入教案节点 | API approve 成功；Web 首页/工作区显示当前阶段“公开课教案” | 通过 |
| 11 | 生成教案 Markdown | `lesson_plan/generate` 成功，状态 `needs_review` | 通过 |
| 12 | 教案结果包含来源信息 | `source_knowledge_point_id=kp_001`，`source_markdown_path=knowledge-points/kp_001.md` | 通过 |
| 13 | 教案 Markdown 内容包含“5以内数的认识” | API 产物包含目标文本 | 通过 |
| 14 | 刷新页面后结果不丢失 | 刷新后 Web 首页仍显示项目、公开课教案阶段、30% 进度 | 通过 |
| 15 | 浏览器控制台无阻断性 error/warn | 仅有 React DevTools、HMR、Fast Refresh 开发提示；无应用级 error/warn | 通过 |

## API 证据

### `/health`

```json
{
  "status": "ok",
  "workflow_version": "1.0.0"
}
```

### 项目与上传

```json
{
  "project_id": "proj_34be317be27c",
  "project_name": "T041-教材到教案回归-633528",
  "upload": {
    "path": "uploads/1上-人教版小学数学课本（2024新版）.pdf",
    "filename": "1上-人教版小学数学课本（2024新版）.pdf",
    "status": "uploaded"
  }
}
```

### `textbook_parse`

```json
{
  "status": "approved",
  "textbook_meta": {
    "subject": "math",
    "grade": "1",
    "textbook_version": "renjiao",
    "volume": "shang",
    "title": "人教版小学数学一年级上册"
  },
  "knowledge_titles": ["5以内数的认识"],
  "selected_knowledge_point_id": "kp_001",
  "markdown_path": "knowledge-points/kp_001.md",
  "markdown_contains_target": true
}
```

字段展示口径：

- `subject=math` 等价 UI 文案“数学”。
- `grade=1` 等价 UI 文案“一年级”。
- `textbook_version=renjiao` 等价 UI 文案“人教版”。
- `volume=shang` 等价 UI 文案“上册”。

### `lesson_plan`

```json
{
  "status": "needs_review",
  "source_knowledge_point_id": "kp_001",
  "source_markdown_path": "knowledge-points/kp_001.md",
  "lesson_markdown_contains_target": true
}
```

### manifest

```json
[
  {"node_id": "project_meta", "status": "approved"},
  {"node_id": "project_config", "status": "approved"},
  {"node_id": "textbook_parse", "status": "approved"},
  {"node_id": "lesson_plan", "status": "needs_review"},
  {"node_id": "intro_selection", "status": "not_started"},
  {"node_id": "intro_video_script", "status": "not_started"},
  {"node_id": "intro_video_screenplay", "status": "not_started"},
  {"node_id": "intro_video_asset", "status": "not_started"},
  {"node_id": "storyboard", "status": "not_started"},
  {"node_id": "final_video", "status": "not_started"}
]
```

## Web 证据

### 首页与工作区状态读取

- Web 地址：`http://127.0.0.1:3141`
- 登录用户：`qa-t041`
- 首页项目列表显示 `T041-教材到教案回归-633528`
- 项目卡片显示：
  - 学科/年级/版本册次：数学 / 一年级 / 人教版 上册
  - 当前阶段：公开课教案
  - 下一步动作：进入「公开课教案」
  - 总进度：30%
- 工作区显示：
  - 项目名 `T041-教材到教案回归-633528`
  - `10 个后端 manifest 节点`
  - 当前节点 `公开课教案`
  - 节点状态 `待确认`
- 刷新后首页仍显示同一项目和同一阶段，状态未丢失。

### UI 子链路补测

- Web 地址：`http://127.0.0.1:3141`
- 登录用户：`qa-t041-ui`
- UI 子链路项目：`T041-UI子链路-633528`
- UI 子链路项目 ID：`proj_358af9eac8c7`

新建项目第 2 步真实后端入口：

- 标题：`教材解析（真实后端）`
- 说明：`上传 PDF 后调用后端解析教材`
- 按钮：`解析教材`
- 文件 input：`type=file`，`accept=.pdf,.txt,.md`

UI 直接证据：

- PDF 文件名显示：`1上-人教版小学数学课本（2024新版）.pdf`
- 解析中状态：按钮 `解析中…`，提示 `正在上传教材并调用后端解析…`
- 解析完成状态：`教材解析结果`、`来自后端解析`
- 字段回填：数学、一年级、人教版、上册
- 字段手改：年级从“一年级”改为“二年级”，顶部摘要同步显示 `数学 · 二年级`
- 知识点下拉：展开后包含并选中“5以内数的认识”
- Markdown 路径：`knowledge-points/kp_001.md`
- Markdown 内容：预览区包含 `# 《5以内数的认识》图文教材结构化整理`
- 截图：`docs\qa-audits\t041-ui-textbook-parse-result.png`

UI 触发的网络请求：

```text
POST http://127.0.0.1:8141/projects -> 200
POST http://127.0.0.1:8141/projects/proj_358af9eac8c7/textbook -> 200
POST http://127.0.0.1:8141/projects/proj_358af9eac8c7/nodes/textbook_parse/generate -> 200
GET  http://127.0.0.1:8141/projects/proj_358af9eac8c7/manifest -> 200
```

网络响应要点：

- 上传响应：`path=uploads/1上-人教版小学数学课本（2024新版）.pdf`，`mime_type=application/pdf`，`status=uploaded`
- 解析响应：`textbook_meta.subject=math`，`grade=1`，`textbook_version=renjiao`，`volume=shang`
- 解析响应：`selected_knowledge_point.knowledge_point_id=kp_001`
- 解析响应：`selected_knowledge_point.markdown_path=knowledge-points/kp_001.md`

## 控制台证据

浏览器控制台 `error/warn`：无。

结论：未发现阻断性应用级 `error/warn`。

Web dev server 日志：

- `GET / 200`
- Next dev 提示 `allowedDevOrigins` 跨源配置未来版本要求。该项为开发环境提示，不影响本轮本地演示主链路。

## 缺陷与阻塞

本轮补测后，T041 未发现阻塞演示或不通过缺陷。

### 已关闭：浏览器自动化无法注入本地 PDF，导致 T041 UI 子链路缺证

- 分类：环境配置 / 测试工具
- 原状态：阻塞
- 当前状态：已关闭
- 关闭依据：本轮改用支持文件上传的 Chrome DevTools 浏览器环境，已完成 PDF 上传、解析中状态、字段回填、字段手改、知识点下拉、Markdown 预览和控制台检查。
- 保留说明：上一轮 in-app browser 文件注入能力不足仍是工具限制，但不再阻塞 T041 验收结论。

### 优化建议：manifest API 字段名与前端展示字段存在兼容映射

- 分类：接口 / 前端
- 复现步骤：
  1. 调用 `GET /projects/{project_id}/manifest`。
  2. 查看节点数组。
- 实际结果：
  - API manifest 节点主键字段为 `node_id`。
  - 当前测试摘要中若按 `id/title/sort_order` 读取会得到空值，但前端已能正确显示节点标题，说明前端存在映射或使用 workflow 配置补足展示。
- 期望结果：
  - 上线前统一 manifest 节点字段契约，减少测试和前端兼容映射。
- 风险影响范围：
  - 不阻塞本地演示；可能影响后续自动化测试稳定性。
- 阻塞角色：后端工程师 / 前端工程师，需架构师统一契约。
- 标准修复方案：
  - 在 API 契约文档中明确 `node_id` 为节点唯一标识。
  - 如前端需要 `id/title/sort_order`，后端 manifest 直接返回或前端映射层集中补齐。

## 本轮不覆盖

- 不测真实 provider。
- 不做上线验收。
- 不测部署。
- 不测正式鉴权。
- 不判定生产级 MinerU 全书解析能力。
- 不判定真实 Minimax 教案质量。

## 复测建议

- 后续浏览器回归优先使用支持文件上传的 Chrome DevTools 或标准 Playwright 环境。
- 上线前仍需补真实 provider、正式鉴权、多浏览器、生产级 MinerU 异步解析、上传大小/版权/安全限制。
