# T132 用户态回归测试报告

## 结论

【不通过】。

T127-T129 后端契约与 T130-T131 前端基础能力可运行：教材库、目录章节、知识点页码、页段 PDF、MinerU Markdown、教案来源追溯、工作区 7 步流、未解锁提示、教案 Markdown 编辑/预览均有证据。后端全量测试与前端契约、tsc、lint、build 均通过。

但普通教师工作区主界面直接出现红线词 `JSON`，且提示“完整内容仍在下方 JSON 中编辑”。这违反 T132 红线要求，必须判定用户态回归不通过。另有教材/Markdown 弹窗暴露本地 storage 路径、目标受众默认错为“三年级学生”等问题。

## 测试环境

- API：`http://127.0.0.1:8132`
- Web：`http://127.0.0.1:3132`
- Storage：`storage-t132-user-flow-regression`
- Provider：`PROVIDER_MODE=fake`，`VIDEO_PROVIDER_MODE=placeholder`，`IMAGE_PROVIDER_MODE=placeholder`，`TTS_PROVIDER_MODE=placeholder`
- Web 模式：真实 API 模式
- 证据目录：`docs\qa-audits\t132-user-flow-regression-evidence\20260624-002553`
- API 项目 ID：`proj_168e084cb7a6`
- 浏览器创建项目 ID：`proj_b9b6a883a06b`
- 教材 ID：`renjiao-grade1-volume1-2024`
- 教材版本 ID：`renjiao-grade1-volume1-2024-v1`
- 知识点 ID：`kp_001`

## 通过项

- `/health` 正常，API/Web 隔离端口启动成功。
- `GET /textbook-library` 返回 `人教版 / 小学数学 / 一年级 / 上册`。
- `GET /textbook-library/{id}/knowledge-points` 返回 7 个目录章节和 9 个课时知识点；`kp_001` 归属 `5以内数的认识和加、减法`，教材页 `14-23`，PDF 页 `19-28`。
- 资产包抽取成功：源 PDF 118 页，页段 PDF 10 页，页段不是整册；MinerU Markdown 包含 `5以内数的认识` 和结构化章节。
- 教案生成结果包含 `source_textbook_id`、`source_textbook_version_id`、`source_knowledge_point_id=kp_001`、`source_slice_pdf_path`、`source_mineru_md_path`。
- 新建项目页显示教材库下拉、上传入口、知识点顶部选择、字段回填、核心知识点抽屉、关键词标签、90 秒时长和 PPT 模板下拉。
- 工作区显示 7 步用户态流程，未解锁步骤点击提示“请先完成【教材内容】后，再进入【教案生成】。”
- 确认教材后进入教案步骤，教案 Markdown 编辑/预览可用。
- 浏览器 console error/warn 为空。

## 缺陷清单

### P0 / 前端 / 工作区普通主界面暴露 JSON 红线

复现步骤：
1. 打开 `http://127.0.0.1:3132`，真实 API 模式登录。
2. 新建项目，载入教材库教材，确认 `5以内数的认识`，完成创建。
3. 进入项目工作区，查看“教材内容”当前任务卡。

实际结果：
- 普通主界面显示“当前节点暂按通用结构展示，完整内容仍在下方 JSON 中编辑。”
- 普通主界面显示 `JSON`、`subject`、`textbook_version` 等结构化字段。
- 红线扫描文件 `browser-redline-scan-workspace.json` 命中 `JSON`。

期望结果：
- 普通教师主界面不得出现 `JSON` 或结构化字段编辑入口。
- 结构化原文只允许放入默认关闭的“开发诊断”折叠区。

风险影响：
- 直接违反 T132 红线，用户态验收不通过。
- P01 李雪老师会认为页面仍是工程调试台，不是可用备课流程。

标准修复方案：
- 为 `textbook_parse` 等节点补用户态摘要渲染，不在普通区 fallback 到 JSON。
- 将 raw JSON、字段名、原始结构全部移动到“开发诊断”折叠区，默认关闭。
- 增加前端契约或浏览器 smoke：普通主界面禁词扫描不得命中 `JSON`。

建议转交角色：前端工程师，后端工程师配合补 `/workspace` review/result 映射字段。

### P1 / 前端 / 教材内容与页段弹窗暴露本地 storage 路径

复现步骤：
1. 新建项目第 2 步点击“查看核心知识点”。
2. 点击“查看教材页段”。
3. 点击“查看教材内容”。

实际结果：
- 弹窗标题下方显示 `storage-t132-user-flow-regression/.../knowledge-points/kp_001/mineru.md` 或 `.../source.pdf`。

期望结果：
- 教师只看到“教材页 14-23 / PDF 页 19-28”“教材内容已解析”等用户可读信息。
- 内部 storage 路径只允许在开发诊断中展示。

风险影响：
- 暴露内部文件组织，削弱教师用户信任。
- 接近“输出路径/内部路径”红线，后续部署路径还可能泄露环境信息。

标准修复方案：
- 弹窗 subtitle 改为用户态来源说明，例如“人教版一年级上册 · 教材页 14-23 · PDF 页 19-28”。
- 如需下载/预览，用后端代理 URL，不展示本地相对/绝对路径。

建议转交角色：前端工程师。

### P1 / 前端 / 新建项目字段回填目标受众默认错误

复现步骤：
1. 新建项目，载入教材库“人教版 / 小学数学 / 一年级 / 上册”。
2. 进入第 2 步“选择课时知识点”。
3. 查看“目标受众”输入框。

实际结果：
- 目标受众默认显示“三年级学生”。

期望结果：
- 按需求应默认“一年级学生”。

风险影响：
- 教师若未手改，后续教案、视频和 PPT 可能按错误学段生成。

标准修复方案：
- 字段回填逻辑从教材年级 label 派生目标受众。
- 增加契约测试：一年级教材解析后目标受众默认值必须为“一年级学生”。

建议转交角色：前端工程师。

### P2 / 前端 / 新建项目第 3 步仍偏配置台口径

复现步骤：
1. 新建项目进入第 3 步“项目信息”。

实际结果：
- 页面出现“第 0 步核心配置”“角色字典描述”“角色安全规则”“合规红线”等专业配置项。

期望结果：
- 普通教师只看到与备课相关的简单偏好；高级视觉/角色/合规配置应弱化、折叠或换成教师可理解话术。

风险影响：
- 不阻断流程，但仍不像 P01 教师能自然理解的备课表单。

标准修复方案：
- 将专业字段放到“高级设置”默认折叠区。
- 文案从“角色字典/合规红线”改为“人物风格/画面安全要求”等用户语言。

建议转交角色：产品经理 + 前端工程师。

## 验证命令

后端：

```powershell
$env:PYTHONPATH='apps/api'
python -m pytest apps\api\tests -q
```

结果：`221 passed, 2 xfailed in 105.39s`。

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

## 关键证据

- API 汇总：`summary-api.json`
- 教材库：`textbook-library.json`
- 目录与知识点：`knowledge-points.json`
- 资产包：`asset-kp001-extract.json`
- 页段/Markdown 文件检查：`artifact-file-check.json`
- 教材解析节点：`node-textbook_parse-generate.json`
- 教案节点：`node-lesson_plan-generate.json`
- 工作区契约：`workspace-user-flow.json`
- 新建项目第 1 步：`browser-new-project-initial.png`
- 教材库载入：`browser-after-load-textbook.png`
- 知识点与字段回填：`browser-step2-knowledge-point.png`
- 字段手改：`browser-step2-field-manual-edit.png`
- 核心知识点抽屉：`browser-core-knowledge-drawer.png`
- 页段 PDF 弹窗：`browser-textbook-page-segment-dialog.png`
- MinerU Markdown 弹窗：`browser-mineru-markdown-dialog.png`
- 关键词/时长：`browser-step4-video-preferences.png`
- PPT 模板：`browser-step5-ppt-template.png`
- 工作区创建后：`browser-workspace-after-create.png`
- 未解锁点击：`browser-workspace-locked-click.png`
- 教案 Markdown 预览：`browser-workspace-lesson-preview.png`
- 红线扫描：`browser-redline-scan-workspace.json`
- 控制台：`browser-console.json`
- 后端测试：`backend-pytest-all.log`
- 前端测试：`frontend-command-results.json`

## 剩余风险

- 本轮只测固定 fixture，不代表任意教材泛化。
- 未验收真实视频 provider 成片。
- 未做多浏览器、多分辨率与正式权限测试。
- Next build 使用 31 workers，这是项目当前构建行为；本轮未调整构建并发配置。

## 整改清单

1. P0：前端移除工作区普通主界面的 `JSON` fallback 和结构化字段展示。
2. P1：前端移除核心知识点、教材页段、教材内容弹窗中的 storage 路径展示。
3. P1：前端修复一年级教材的目标受众默认值。
4. P2：PM/前端将第 3 步专业配置项改成教师可理解的默认折叠高级设置。
5. 修复后由测试工程师补跑 T132 红线复测：普通主界面禁词扫描、弹窗路径扫描、创建项目到教案预览链路。
