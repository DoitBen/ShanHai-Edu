# T146-T148 功能接口全量测试调度

日期：2026-06-24
角色：首席系统架构师
状态：测试任务已安排，待测试工程师执行

## 结论

本轮按 3 个测试批次覆盖所有当前可见功能接口：

| 任务 | 测试对象 | 目标 |
|---|---|---|
| T146 | 后端 FastAPI 功能接口 | 覆盖公开接口、普通受保护接口、项目工作流、教材库、教案库、节点、任务、资源下载、管理员规则/Prompt 接口 |
| T147 | Next.js API 代理与前端接口适配 | 覆盖 `/api/backend/[...path]` 代理、服务端 token 注入、admin cookie 门禁、文件下载代理、前端 mapper/client 契约 |
| T148 | 浏览器真实 API 串联 | 用真实浏览器在 fake/placeholder 模式串起用户态 7 步、PPT/视频子门禁、下载入口、红线扫描和控制台 |

通过口径必须保守：T146-T148 通过后只能说明“fake/placeholder + 本地接口 + 浏览器用户态接口联动”通过，不代表真实 provider、生产 RBAC/JWT/session、多浏览器、容器冷启动、真实 PPT/视频质量通过。

## 接口盘点

### 后端 FastAPI

当前后端接口从 `apps\api\app\main.py` 可见，按功能分组如下：

- 公共接口：`GET /health`、`GET /workflow`、`GET /video/capabilities`。
- 教材库接口：`GET /textbook-library`、`POST /textbook-library/uploads`、`GET /textbook-library/jobs/{job_id}`、知识点、资产、切分、抽取、确认相关接口。
- 教案库接口：`GET /lesson-plan-library`、`GET /lesson-plan-library/{lesson_plan_id}`、`POST /lesson-plan-library/import/from-project`。
- 管理接口：`GET /admin/prompts/templates`、`GET/POST /admin/prompts/templates/{template_id}/versions`、`GET/POST /admin/rules...`、`GET /admin/workflow/graph`。
- 项目接口：`POST /projects`、`GET /projects`、`GET/PATCH /projects/{project_id}`、`GET /manifest`、`GET /workspace`、`GET /flywheel`、`POST /feedback`。
- 教材挂载接口：`POST /projects/{project_id}/textbook`、`POST /projects/{project_id}/textbook/from-library/{textbook_id}`。
- 节点接口：`POST /nodes/{node_id}/generate|edit|approve|retry`、`GET /nodes/{node_id}`、`GET /nodes/{node_id}/versions`。
- 任务接口：`GET /tasks`、`GET /tasks/{task_id}`、`POST /tasks/{task_id}/retry`。
- 产物接口：`POST /export/ppt`、`GET /exports/{filename}`、`GET /outputs/final_video.mp4`、`GET /clips/{filename}`、`GET /images/{filename}`、`GET /files/{asset_path}`、`GET /assets`、`GET /assets/{asset_id}`。
- 规则与 schema：`GET /schemas/{schema_name}`、`GET /rules/coverage`。

### 前端 Next API

当前前端 API 面很薄：

- `GET /api`：示例健康响应。
- `/api/backend/[...path]`：通用后端代理，支持 `GET/POST/PUT/PATCH/DELETE`，负责 admin cookie 门禁、去除 `Expect` header、服务端注入 `BACKEND_API_TOKEN`、转发文件流响应。

## 测试分工

### T146：后端 FastAPI 功能接口合同回归

**目标角色**：测试工程师子智能体 A
**范围**：后端所有公开、受保护、管理员和资源下载接口。
**不做**：不访问真实 provider，不读取或打印真实密钥，不改业务代码，不做浏览器 UI 判断。
**隔离环境**：

- API 端口：`8146`
- storage：`storage-t146-functional-api`
- provider：`PROVIDER_MODE=fake`、`VIDEO_PROVIDER_MODE=placeholder`、`IMAGE_PROVIDER_MODE=placeholder`、`TTS_PROVIDER_MODE=placeholder`

**建议命令**：

```powershell
$env:PROVIDER_MODE='fake'
$env:VIDEO_PROVIDER_MODE='placeholder'
$env:IMAGE_PROVIDER_MODE='placeholder'
$env:TTS_PROVIDER_MODE='placeholder'
$env:STORAGE_ROOT='storage-t146-functional-api'
python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_api_contract_gate.py apps\api\tests\test_mvp_api.py apps\api\tests\test_textbook_pdf_parsing.py apps\api\tests\test_workspace_user_flow_contract.py apps\api\tests\test_ppt_runtime_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_flywheel_contract.py apps\api\tests\test_security_boundary.py apps\api\tests\test_control_plane_rules.py -q
python -m pytest apps\api\tests -q
```

**必须覆盖**：

- 成功路径：项目创建、教材库、知识点资产、教案库、manifest、workspace、节点生成/编辑/确认/重试、任务查询、PPT/视频占位产物下载。
- 失败路径：不存在项目/节点/资产、上游未确认、节点未就绪、非法 schema、未配置/错误 token、admin 未授权隐藏为 404。
- 下载安全：`exports` 只能下载 `.pptx`，`clips` 只能下载 `.mp4`，`images` 只允许图片后缀，`files` 不允许逃逸项目目录。

**通过标准**：

- 目标批次通过，后端全量测试若有失败必须分级记录。
- 所有失败响应保持统一 `ok=false/error.code/message/retryable` 结构。
- 没有密钥、token、真实 provider 响应原文泄露。

**产物**：

- `docs\qa-audits\2026-06-24-t146-functional-api-contract.md`
- `docs\qa-audits\t146-functional-api-evidence\<timestamp>\`

### T147：Next 代理和前端接口适配回归

**目标角色**：测试工程师子智能体 B
**范围**：前端 API 代理、接口映射、管理员规则页面接口契约、workspace 用户态契约。
**不做**：不改 UI，不跑真实 provider，不读取真实 token 值，不把前端单测等同浏览器验收。
**隔离环境**：

- API 端口：`8147`
- Web 端口：`3147`
- storage：`storage-t147-proxy-contract`

**建议命令**：

```powershell
cd apps\web
$env:VITEST_MAX_WORKERS='2'
bun src\lib\api-proxy-contract.test.ts
bun src\lib\api-mappers-contract.test.ts
bun src\lib\admin-rules-contract.test.ts
bun src\lib\workspace-user-flow-contract.test.ts
bun src\lib\new-project-user-flow-contract.test.ts
bunx tsc --noEmit --pretty false
bun run scan:client-secrets
```

如需 live proxy 验证，再启动隔离 API/Web：

```powershell
$env:STORAGE_ROOT='storage-t147-proxy-contract'
$env:PROVIDER_MODE='fake'
$env:VIDEO_PROVIDER_MODE='placeholder'
$env:IMAGE_PROVIDER_MODE='placeholder'
$env:TTS_PROVIDER_MODE='placeholder'
$env:CORS_ORIGINS='http://localhost:3147,http://127.0.0.1:3147'
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8147
```

```powershell
cd apps\web
$env:NEXT_PUBLIC_DEMO_MODE='false'
$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8147'
$env:BACKEND_API_BASE_URL='http://127.0.0.1:8147'
bunx next dev -p 3147
```

**必须覆盖**：

- `/api/backend/[...path]` 代理 GET/POST/PATCH/DELETE 能转发。
- admin 后端路径没有本地 admin cookie 时前端代理返回 404。
- 后端 token 只在服务端注入，不进入浏览器可见源码、localStorage、sessionStorage 或普通响应。
- multipart 上传代理不带 `Expect` header。
- 下载代理返回文件流时不改坏 `content-type`。

**通过标准**：

- 前端契约测试、类型检查、client secret 扫描通过。
- live proxy 证据中浏览器不可见 `BACKEND_API_TOKEN` 和真实密钥。
- admin 非授权路径不暴露管理接口存在性。

**产物**：

- `docs\qa-audits\2026-06-24-t147-next-proxy-interface-regression.md`
- `docs\qa-audits\t147-next-proxy-evidence\<timestamp>\`

### T148：浏览器真实 API 功能接口串联回归

**目标角色**：测试工程师子智能体 C
**范围**：用户态浏览器路径覆盖功能接口联动，不替代 T146 的后端全量合同。
**不做**：不宣称真实视频/PPT 质量通过，不测试真实 provider，不测试 Edge/Firefox/移动端。
**隔离环境**：

- API 端口：`8148`
- Web 端口：`3148`
- storage：`storage-t148-browser-functional-interfaces`
- provider：fake/placeholder

**启动命令**：

```powershell
$env:STORAGE_ROOT='storage-t148-browser-functional-interfaces'
$env:PROVIDER_MODE='fake'
$env:VIDEO_PROVIDER_MODE='placeholder'
$env:IMAGE_PROVIDER_MODE='placeholder'
$env:TTS_PROVIDER_MODE='placeholder'
$env:CORS_ORIGINS='http://localhost:3148,http://127.0.0.1:3148'
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8148
```

```powershell
cd apps\web
$env:NEXT_PUBLIC_DEMO_MODE='false'
$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8148'
$env:BACKEND_API_BASE_URL='http://127.0.0.1:8148'
bunx next dev -p 3148
```

**必须覆盖**：

- 登录后进入真实 API 模式首页。
- 新建项目：教材库选择或上传、知识点选择、项目配置、视频/PPT 偏好。
- 工作区 7 步：项目信息、教材内容、教案生成、导入视频方案、PPT 草稿、视频生成、最终交付。
- 节点推进：至少覆盖教材、教案、导入方案、PPT 草稿子门禁、视频生成子门禁、PPTX/MP4 占位下载。
- 资源接口：页段 PDF、Markdown、PPTX、final_video.mp4 下载代理。
- 红线扫描：开发诊断之前不得出现 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage`。
- 控制台：应用级 `error/warn` 为空，若有第三方噪音必须单独解释。

**通过标准**：

- 普通教师主界面能说明“现在看什么、改什么、点什么进入下一步”。
- 所有下载 URL 走 `/api/backend/projects/...`，不暴露本地 storage 路径。
- placeholder 产物必须在 UI 或报告中标注为演示占位，不冒充真实成片。
- 浏览器证据不能替代后端全量接口合同；T146/T147/T148 三者必须一起回收。

**产物**：

- `docs\qa-audits\2026-06-24-t148-browser-functional-interface-regression.md`
- `docs\qa-audits\t148-browser-functional-interface-evidence\<timestamp>\`

## 执行顺序

1. T146 先跑后端目标批次和全量批次，确认接口合同底座没有明显失败。
2. T147 与 T146 可并行，但 live proxy 需要使用独立端口 `8147/3147`。
3. T148 等 T146/T147 没有 P0/P1 后再跑浏览器串联，避免 UI 证据建立在已知坏接口上。
4. 任一批次发现 P0/P1，停止宣布接口全量通过，由架构师新增窄范围返工任务。

## 缺陷分级

| 级别 | 判定 |
|---|---|
| 致命 | 核心接口无法创建/读取项目、节点无法推进、下载越权或路径逃逸、密钥/token 泄露 |
| 严重 | 某一主功能接口不可用、admin 权限绕过、普通区暴露工程红线、placeholder 冒充真实产物 |
| 一般 | 局部接口错误码不清、提示不友好、非主流程资源缺失但可绕行 |
| 优化建议 | 不影响主流程的文案、证据命名、低频兼容问题 |

## 回收与架构复核

测试工程师完成 T146-T148 后，主 Codex / 系统架构师需要统一回收：

- 三份测试报告。
- 三个证据目录。
- 命令退出码与失败清单。
- 缺陷分级和复现路径。
- 是否需要下发返工任务。

只有三组均无 P0/P1，且红线扫描、权限边界、下载代理和 secret 扫描均通过，才能声明“本地 fake/placeholder 功能接口全量回归通过”。真实 provider、生产权限、容器、多浏览器必须另起专项。
