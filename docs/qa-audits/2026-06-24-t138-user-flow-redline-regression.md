# T138 用户态红线专项复测报告

## 结论

【不通过】。

T133-T137 修复后，三段式教材处理已可用，目标受众默认值已从旧缺陷“三年级学生”修复为“一年级学生”，核心知识点和教材内容弹窗未再暴露 `storage` 路径；但浏览器真实 API 模式下，工作区普通教师主界面仍在“开发诊断”折叠区之前直接显示 `JSON` 与结构化字段，触发 T138 红线，不能进入下一阶段封板。

## 测试环境

- API：`http://127.0.0.1:8138`
- Web：`http://127.0.0.1:3138`
- Storage：`storage-t138-user-flow-redline-regression`
- Provider：`fake`
- Video/Image/TTS provider：`placeholder`
- Web 模式：真实 API 模式
- API 项目 ID：`proj_20cc0610a314`
- 浏览器项目 ID：`proj_e2cc3f58298b`
- 教材 ID：`renjiao-grade1-volume1-2024`
- 教材版本 ID：`renjiao-grade1-volume1-2024-v1`
- 知识点 ID：`kp_001`
- 证据目录：`docs\qa-audits\t138-user-flow-redline-regression-evidence\20260624-085413`

## 通过项

- API `/health` 返回正常。
- Web 真实 API 模式可启动，首页 HTTP 200。
- 教材库下拉显示 `人教版 / 小学数学 / 一年级 / 上册`。
- API 三段式教材处理可用：
  - 全量切分：`status=split_ready`，`requested_count=9`。
  - 全量解析：`status=needs_review`。
  - 部分切分：`kp_001/kp_006`，`requested_count=2`，`status=split_ready`。
  - 部分解析：`kp_001/kp_006`，`status=needs_review`。
- 浏览器 UI 可见并执行三段式动作：
  - 载入教材后显示 `导入教材 / 切分教材 / 解析教材内容`。
  - 支持“选择部分”和“全部知识点”。
  - 点击“切分教材”后切分步骤显示“已完成”。
  - 点击“解析教材内容”后解析步骤显示“待确认”。
- 字段回填符合预期：数学、一年级、人教版、上册。
- 目标受众默认值为“一年级学生”。
- 核心知识点弹窗未命中 `storage` 或本地盘符路径。
- 教材内容 Markdown 弹窗未命中 `storage` 或本地盘符路径，内容包含 `5以内数的认识`。
- 未解锁“教案生成”步骤点击后未进入详情，仍停留在当前教材内容任务。
- 开发诊断默认折叠。
- 浏览器 console `error/warn` 为空。
- 后端目标测试通过：`18 passed in 16.97s`。
- 前端 `new-project/workspace/api-mappers` 契约、`tsc`、`lint`、`build` 全部退出码 0。

## 阻塞缺陷

### P0 / 前端 / 工作区普通主界面仍暴露 `JSON`

复现步骤：
1. 启动 T138 隔离环境：API `8138`，Web `3138`，Web 真实 API 模式。
2. 登录 Web，进入新建项目。
3. 从教材库载入“人教版 / 小学数学 / 一年级 / 上册”。
4. 点击“切分教材”，再点击“解析教材内容”。
5. 进入第 2 步，确认教材信息与课时。
6. 继续到第 5 步并创建项目。
7. 进入项目工作区，查看“教材内容 / 教材解析与核验”当前任务卡。

实际结果：
- 普通主界面显示“当前节点暂按通用结构展示，完整内容仍在下方 JSON 中编辑。”
- 普通主界面显示 `JSON`、`subject`、`grade`、`textbook_version`、`volume`、`lesson_title`、`core_knowledge_points` 等结构化字段。
- 红线扫描 `browser-redline-scan-main.json` 显示 `main_hits_before_developer_diagnostics=["JSON"]`。
- “开发诊断”本身是默认折叠的，但红线命中发生在折叠区之前。

期望结果：
- 普通教师主界面不得出现 `JSON` 或结构化字段。
- 原始结构、字段名和调试信息只能出现在默认折叠的“开发诊断”内。
- 教材内容步骤应展示教师可读摘要、Markdown 预览或教材依据说明。

影响范围：
- 直接违反 T138 验收红线，用户态封板不能通过。
- P01 李雪老师会看到工程调试语言，无法把工作区理解为教师备课流程。

标准修复方案：
- 前端为 `textbook_parse/textbook_content` 当前任务补用户态结果渲染，禁止普通区 fallback 到 `JSON`。
- 将 raw content、字段名、原始结构、节点输出全部移动到“开发诊断”折叠区。
- 增加浏览器级或 DOM 级红线测试：在“开发诊断”之前扫描 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage` 不得命中。

建议转交角色：前端工程师。

## 一般缺陷 / 上线前再修

### P2 / 前端 / 教材页段按钮仍处于禁用状态

复现步骤：
1. 新建项目第 2 步完成切分教材和解析教材内容。
2. 进入教材证据包区域。
3. 查看“查看教材页段”按钮状态。

实际结果：
- “查看教材页段”按钮仍为禁用。
- API 证据中 `slice_pdf_path` 已存在，切分接口返回成功。

期望结果：
- 切分完成后，教师应能打开教材页段预览弹窗或 PDF 代理预览。
- 弹窗不得显示本地 `storage` 路径。

影响范围：
- 不触发本轮硬红线，因为没有暴露路径；但 T138 明确要求验证教材页段弹窗不得显示本地路径，当前只能验证“不可打开”，无法验证页段弹窗展示质量。

标准修复方案：
- 前端在 `slice_pdf_path` 存在时启用“查看教材页段”。
- 使用后端代理或用户态页码说明展示，不在弹窗中显示内部路径。

建议转交角色：前端工程师。

### P2 / 前端 / 首页仍显示接口口径文案

复现步骤：
1. 登录真实 API 模式首页。
2. 查看“继续工作”区域。

实际结果：
- 首页显示“数据来源：GET /projects”。

期望结果：
- 普通教师首页使用“正在同步项目列表”等用户态文案。

影响范围：
- T138 红线词清单未包含 `GET` 或 `API`，本轮不作为阻塞；但与用户态方向不一致。

标准修复方案：
- 将接口来源文案移动到开发诊断或本地调试提示中。

建议转交角色：前端工程师。

## 关键证据

- API 健康检查：`api-health.json`
- Web 健康检查：`web-health.json`
- 启动参数：`runtime-launch-params.json`
- 教材库：`textbook-library.json`
- 目录与知识点：`knowledge-points.json`
- 全量切分：`textbook-split-all.json`
- 全量解析：`textbook-extract-all.json`
- 部分切分：`textbook-split-selected.json`
- 部分解析：`textbook-extract-selected.json`
- API 项目创建：`project-created-api.json`
- API workspace：`workspace-user-flow-api.json`
- 浏览器项目列表：`projects-list-after-browser-create.json`
- 浏览器项目 workspace：`workspace-user-flow-browser-project.json`
- 新建项目第 1 步：`browser-new-project-step1.png`
- 三段式载入后：`browser-new-project-three-stage-loaded.png`
- 切分后：`browser-new-project-after-split.png`
- 解析后：`browser-new-project-after-extract.png`
- 目标受众：`browser-step2-target-audience.png`
- 核心知识点弹窗：`browser-core-knowledge-dialog.png`
- 教材内容弹窗：`browser-mineru-markdown-dialog.png`
- 弹窗路径扫描：`browser-dialog-path-scan.json`
- 创建前摘要：`browser-new-project-before-create.png`
- 工作区截图：`browser-workspace-after-create.png`
- 未解锁点击：`browser-workspace-locked-click.png`
- 红线扫描：`browser-redline-scan-main.json`
- 浏览器控制台：`browser-console.json`
- 后端目标测试：`backend-targeted-tests.log`
- 前端测试：`frontend-command-results.json`

## 验证命令

后端：

```powershell
python -m pytest apps\api\tests\test_textbook_pdf_parsing.py apps\api\tests\test_workspace_user_flow_contract.py -q
```

结果：`18 passed in 16.97s`。

前端：

```powershell
cd apps\web
bun src/lib/new-project-user-flow-contract.test.ts
bun src/lib/workspace-user-flow-contract.test.ts
bun src/lib/api-mappers-contract.test.ts
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

结果：全部退出码 0，`next build` 成功。

## 剩余风险

- 本轮只测固定 fixture，不代表任意教材泛化。
- 本轮不测真实 MinerU provider。
- 本轮不测真实视频生成 provider。
- 本轮不做上线验收、正式权限、多浏览器和性能验收。
- 当前前端静态契约测试通过但浏览器红线仍失败，说明需要补浏览器或 DOM 红线门禁，不能只依赖源码包含性断言。

## 最终判定

【不通过】。

阻塞点唯一归因：前端工作区普通主界面仍暴露 `JSON` 红线词。修复后建议只补跑 T138 红线专项，不需要重跑后端三段式全量链路。
