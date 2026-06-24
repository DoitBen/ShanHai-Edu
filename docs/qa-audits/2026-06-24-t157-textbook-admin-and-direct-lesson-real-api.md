# T157 教材库管理员拆分与直接教案真实 API 集成验收

## 结论

PASS，带关注项。

T157 指定后端目标测试、前端目标测试、真实 API 浏览器 smoke 均完成。教师新建项目页不再承担教材加工动作，普通教师路径收敛为：

- 路径 A：使用教材库，选择已管理教材与知识点。
- 路径 B：直接使用教案，从教案库选择或上传教案文件开始。

管理员侧“管理教材库”页面可见并提供上传教材、切分教材、解析教材内容、确认资产、教案库/上传教案能力。浏览器测试使用 `NEXT_PUBLIC_DEMO_MODE=false` 的真实 API 模式，未把 demo/mock 页面作为通过依据；本轮未读取或打印真实密钥。

## 测试范围

- 配置核验：`apps/web/.env.local` 中 `NEXT_PUBLIC_DEMO_MODE=false`、`BACKEND_API_BASE_URL=http://127.0.0.1:8000`。
- 后端目标测试：教案库上传、用户态 workspace、直接教案项目、教材 PDF 解析。
- 前端目标测试：教师新建项目契约、管理员教材库契约、TypeScript、ESLint。
- 浏览器真实 API smoke：`http://127.0.0.1:3000` Web + `http://127.0.0.1:8000` API。
- 教师普通区红线：新建项目页不得出现教材加工词和工程词。
- 管理员侧：左侧导航与管理教材库页面能力可见。

证据目录：

`docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-195033`

补充证据目录：

`docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-200154`

架构师补充复核证据目录：

`docs\qa-audits\t157-textbook-admin-and-direct-lesson-real-api-evidence\20260624-201700`

## 命令结果

| 类别 | 命令 | 结果 | 证据 |
|---|---|---:|---|
| 配置/服务 | `.env.local` 指定项 + `/health` | PASS；API `/health` 200 | `config-and-server-check.json` |
| 后端 | `python -m pytest apps\api\tests\test_lesson_plan_library_upload.py apps\api\tests\test_workspace_user_flow_contract.py apps\api\tests\test_direct_lesson_project_contract.py -q` | PASS；12 passed | `backend-target-user-flow-pytest.txt` |
| 后端 | `python -m pytest apps\api\tests\test_textbook_pdf_parsing.py -q` | PASS；19 passed | `backend-textbook-pdf-parsing-pytest.txt` |
| 前端 | `cd apps\web; bun src\lib\new-project-user-flow-contract.test.ts` | PASS；exit 0 | `frontend-new-project-user-flow-contract.txt` |
| 前端 | `cd apps\web; bun src\lib\admin-textbook-library-contract.test.ts` | PASS；exit 0 | `frontend-admin-textbook-library-contract.txt` |
| 前端 | `cd apps\web; bunx tsc --noEmit --pretty false` | PASS；exit 0 | `frontend-tsc-noemit.txt` |
| 前端 | `cd apps\web; bun run lint` | PASS；exit 0 | `frontend-lint.txt` |

补充新鲜验证（2026-06-24 20:17 后）：

- `python -m pytest apps\api\tests\test_lesson_plan_library_upload.py apps\api\tests\test_workspace_user_flow_contract.py apps\api\tests\test_direct_lesson_project_contract.py -q`：`12 passed`
- `python -m pytest apps\api\tests\test_textbook_pdf_parsing.py -q`：`19 passed`
- `cd apps\web; bun src\lib\new-project-user-flow-contract.test.ts`：exit 0
- `cd apps\web; bun src\lib\admin-textbook-library-contract.test.ts`：exit 0
- `cd apps\web; bunx tsc --noEmit --pretty false`：exit 0
- `cd apps\web; bun run lint`：exit 0

## 浏览器验收

| 场景 | 结果 | 证据 |
|---|---|---|
| 登录页真实 API 模式 | PASS；登录页显示“当前为真实 API 模式，登录后将读取后端项目数据。” | `browser-login-initial-snapshot.txt` |
| 教师新建项目首屏 | PASS；可见“使用教材库”“直接使用教案”，未命中教材加工词和工程词 | `browser-teacher-new-project-initial-dom-scan.json` |
| 路径 A：使用教材库 | PASS；选择教材后第 2 步显示 9 个知识点，知识点下拉含“5以内数的认识”，未命中红线 | `browser-teacher-path-a-step2-dom-scan.json` |
| 路径 B：直接使用教案 | PASS；可见“从教案库选择”、上传教案文件入口，file input 接受 `.pdf/.doc/.docx/.md/.markdown/.txt`，未命中红线 | `browser-teacher-path-b-dom-scan.json` |
| direct lesson API 项目 | PASS；上传教案到教案库，创建引用教案项目，`workspace.current_step_id=lesson_plan`，教材内容 completed，教案步骤 current 且操作启用 | `api-direct-lesson-project-smoke.json` |
| direct lesson 浏览器工作区 | PASS；项目打开后当前阶段为“教案生成”，不是“教材内容”；普通区工程词扫描为空 | `browser-direct-lesson-workspace-dom-scan.json` |
| 管理员导航 | PASS；管理员左侧导航可见“管理教材库” | `browser-admin-nav-snapshot.txt` |
| 管理员教材库页面 | PASS；可见上传教材、切分教材、解析教材内容、确认资产、教案库/上传教案 | `browser-admin-textbook-library-dom-scan.json` |
| 教师导航权限 | PASS；教师态左侧不显示“管理教材库”；刷新后主体不显示管理员管理功能 | `browser-teacher-nav-admin-hidden-scan.json`、`browser-teacher-after-admin-page-reload-access-scan.json` |
| 控制台 | PASS；浏览器采集 `error/warn=[]` | `browser-console-final-error-warn.json` |

补充浏览器复核：

- 教师新建项目页：`20260624-201700\browser-teacher-new-project-dom-scan.json`，`forbiddenHits=[]`，可见 `使用教材库`、`直接使用教案`、`只选择已管理教材`。
- 管理员导航与管理页：`20260624-201700\browser-admin-nav-scan.json`、`20260624-201700\browser-admin-textbook-library-dom-scan.json`，页面自带角色切换到管理员后可见 `管理教材库`，管理页命中 `上传教材`、`切分教材`、`解析教材内容`、`确认资产`、`教案库`、`上传教案`，`missing=[]`。
- 控制台：`20260624-201700\browser-console-error-warn.json`，`error/warn=[]`。

## 红线扫描

教师新建项目页禁词：

- 教材加工词：`导入教材`、`切分教材`、`解析教材内容`、`重新解析`、`重新导入教材`
- 工程词：`JSON`、`storage`、`API`、`provider`、`manifest`、`node_id`、`StateEngine`、`schema`、`R010`

结果：

- 首屏：`forbiddenHits=[]`、`engineeringHits=[]`、`bodyVisibleHits=[]`
- 路径 A 第 2 步：`forbiddenHits=[]`、`engineeringHits=[]`
- 路径 B：`forbiddenHits=[]`、`engineeringHits=[]`
- direct lesson 工作区开发诊断前：`engineeringHitsBeforeDiagnostics=[]`

## 缺陷清单

| 级别 | 问题 | 复现步骤 | 影响范围 | 建议处理 |
|---|---|---|---|---|
| 关注项 | 浏览器截图采集超时，截图文件未生成 | Browser `Page.captureScreenshot` 多次超时 | 不影响 DOM/API 验收结论，但本轮缺少截图证据 | 后续若必须截图，改用 Chrome DevTools MCP 或外部 Playwright 截图 |
| 关注项 | 首页项目列表刷新后有短暂 `共 0 个` 加载态 | 登录真实 API 首页，刷新后等待项目同步 | 短时体验抖动；后续恢复到 28 个并可搜到 direct lesson 项目 | 前端可优化 loading/ready 状态，避免把加载中展示成空列表 |

## 上线风险

- 本轮是本地真实 API 模式集成验收，不代表生产 RBAC/JWT/session、多浏览器、容器冷启动或真实 provider 质量通过。
- 本轮没有执行管理员“上传教材/切分/解析/确认资产”的破坏性或写入型完整批处理，只验收页面能力可见和既有后端目标测试。
- direct lesson 项目通过 API 上传测试 Markdown 教案并创建真实项目，已产生本地测试数据：`proj_0b60dd65a2a9`。

## 回归测试清单

- 后续若继续修改 `NewProjectScreen`，必须复跑教师新建项目禁词 DOM 扫描。
- 后续若继续修改 `AdminTextbookLibraryScreen` 或 `Sidebar`，必须复跑管理员入口可见与教师入口隐藏。
- 后续若继续修改 workspace/state gate，必须复跑 direct lesson 项目 `current_step_id=lesson_plan` 和教材内容跳过断言。

## 交接给其他角色

- 交给系统架构师做 T157 阶段复核：本轮测试验收 PASS，建议将 T157 标记为已完成。
- 交给前端角色关注：首页项目列表刷新短暂空列表体验。
