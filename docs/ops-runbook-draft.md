# ShanHaiEdu 运维/部署方案与 Runbook 草案

> 任务 ID：T004  
> 角色：运维/部署工程师  
> 日期：2026-06-20  
> 范围：最小部署可复现基础。本文只记录启动、环境、日志、storage、git 忽略和部署缺口，不实现后端业务接口，不修改前端页面，不读取真实密钥值。

## 1. 结论

ShanHaiEdu 当前已经具备最小本地双服务启动基础：Web 使用 Bun + Next.js 16，默认端口 `3000`；API 使用 FastAPI + Uvicorn，默认端口 `8000`，健康检查为 `GET /health`。Web 生产启动脚本已基于 Next standalone 输出运行，API 已有 README 和健康检查接口。

距离正式部署仍缺关键运维资产：仓库未发现正式 `Dockerfile`、`docker-compose.yml` 或 compose 等价文件；`apps\api\.env.example` 为空；API 依赖文件缺失；备份、恢复、日志轮转、密钥注入和 Cloud Run/内网部署路线尚未固化。`docker-compose` 还是 Cloud Run 优先部署，应交由首席系统架构师裁决。

## 2. 当前部署现状

### Web

- 目录：`apps\web`
- 包管理与运行：Bun
- 框架：Next.js 16，`next.config.ts` 配置 `output: "standalone"`
- 开发启动：`bun run dev`
- 构建：`bun run build`
- 生产启动：`bun run start`
- 开发默认端口：`3000`
- Caddy 反代：`apps\web\Caddyfile` 监听 `:81`，默认反代到 `localhost:3000`；带 `XTransformPort` 查询参数时反代到指定本机端口。

### API

- 目录：`apps\api`
- 框架：FastAPI
- 启动命令：`uvicorn apps.api.app.main:app --reload --port 8000`
- 默认端口：`8000`
- 健康检查：`GET /health`
- 本地测试命令：`python -m pytest apps\api\tests -q`
- 默认 provider：`PROVIDER_MODE=fake`
- 真实 provider：`PROVIDER_MODE=minimax` 时，文本使用 Minimax，视频使用章鱼哥 NewAPI。

### 当前仓库部署文件

- 已有：`apps\web\Caddyfile`
- 已有：`scripts\videogen.ps1`
- 未发现：`Dockerfile`
- 未发现：`docker-compose.yml`
- 未发现：`docker-compose.yaml`
- 未发现：`compose.yml`
- 未发现：`compose.yaml`

## 3. 本地启动 Runbook

### 前置条件

- 安装 Bun。
- 安装 Python，并确保本机可运行 `uvicorn`、`fastapi`、`pydantic`、`pytest`、`yaml` 相关依赖。
- 在仓库根目录执行 API 启动命令，保证默认 `WORKFLOW_ROOT=workflow` 能找到 `workflow\workflow.yaml`。
- 如需真实 provider，服务端环境变量由本机 `.env` 或运行环境注入；不要写入前端、源码、日志或提交信息。

### 启动 API

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
uvicorn apps.api.app.main:app --reload --port 8000
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

预期重点：

- HTTP 状态码为 `200`。
- 响应体中应包含 `status=ok` 和 workflow 版本信息。

### 启动 Web

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu\apps\web
bun install
bun run dev
```

访问：

- Web：`http://127.0.0.1:3000`
- 通过 Caddy：`http://127.0.0.1:81`

### 构建与生产启动 Web

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu\apps\web
bun run build
bun run start
```

说明：

- `bun run build` 会执行 `next build`，随后运行 `scripts\copy-standalone-assets.mjs`，把 `.next\static` 和 `public` 复制到 standalone 输出所需位置。
- `bun run start` 会通过 `scripts\run-with-log.mjs` 启动 `.next\standalone\server.js`，并写入 `server.log`。

### 停止与重启

- 开发模式：在对应终端按 `Ctrl+C` 停止，再重新执行启动命令。
- 如后台启动过 Uvicorn 或 Next，先按端口定位进程，再停止进程后重启。
- Windows 示例：

```powershell
netstat -ano | findstr ":8000"
netstat -ano | findstr ":3000"
```

停止进程前需确认 PID 对应服务，避免误停其他本机服务。

## 4. 环境变量与密钥说明

只记录变量名和用途，不记录真实值。

| 变量名 | 所属服务 | 是否敏感 | 来源 | 说明 |
|---|---|---:|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Web | 否 | Web 构建/运行环境 | 前端调用 API 的 base URL，默认 `http://localhost:8000`。 |
| `NEXT_PUBLIC_API_TOKEN` | Web | 是 | Web 构建/运行环境 | 前端向 API 发送的 Bearer token。注意 `NEXT_PUBLIC_*` 会暴露给浏览器，不适合作为真正后端密钥；仅可用于本地或内网轻量门禁，正式部署需重新评估。 |
| `NEXT_PUBLIC_DEMO_MODE` | Web | 否 | Web 构建/运行环境 | 控制是否使用 demo/mock 模式；不等于 `false` 时默认为 demo 模式。 |
| `STORAGE_ROOT` | API | 否 | API 运行环境 / `.env` | 项目运行时数据根目录，默认 `storage`。 |
| `WORKFLOW_ROOT` | API | 否 | API 运行环境 / `.env` | workflow 配置根目录，默认 `workflow`。 |
| `CAPABILITIES_PATH` | API | 否 | API 运行环境 / `.env` | 视频能力矩阵 JSON 路径，默认 `docs/api-research/octo-video/capabilities.json`。 |
| `PROVIDER_MODE` | API | 否 | API 运行环境 / `.env` | provider 模式，默认 `fake`；真实模式为 `minimax`。 |
| `MINMAX_API_KEY` | API | 是 | API 密钥注入 | Minimax 服务端密钥。 |
| `MINMAX_BASE_URL` | API | 否/可能敏感 | API 运行环境 / `.env` | Minimax API base URL。 |
| `MINMAX_TEXT_MODEL` | API | 否 | API 运行环境 / `.env` | 文本模型名，默认 `M3`，代码内会映射为 MiniMax M3 对应模型名。 |
| `MINMAX_VIDEO_MODEL` | API | 否 | API 运行环境 / `.env` | 视频模型名，当前配置项存在，后端需确认实际使用范围。 |
| `MINMAX_TTS_MODEL` | API | 否 | API 运行环境 / `.env` | TTS 模型名，当前配置项存在，后端需确认实际使用范围。 |
| `OCTO_API_KEY` | API | 是 | API 密钥注入 | 章鱼哥 NewAPI 服务端密钥。 |
| `OCTO_BASE_URL` | API | 否/可能敏感 | API 运行环境 / `.env` | 章鱼哥 NewAPI base URL，默认指向服务端配置中的公共入口。 |
| `OCTO_VIDEO_PROVIDER` | API | 否 | API 运行环境 / `.env` | 章鱼哥视频 provider 名，当前配置项存在，后端需确认实际使用范围。 |
| `BACKEND_API_TOKEN` | API | 是 | API 密钥注入 | API 轻量 Bearer token。未配置时受保护接口默认开放，正式部署必须配置或替换为正式鉴权。 |
| `CORS_ORIGINS` | API | 否 | API 运行环境 / `.env` | API 允许的前端来源列表，逗号分隔，默认允许本机 `3000`。 |

密钥注入原则：

- 本地：仅写入未提交的 `.env`、`apps\api\.env` 或 shell 环境变量。
- 容器：通过 compose secrets、环境变量文件或平台 Secret 注入；不要 baked into image。
- Cloud Run：通过 Secret Manager / 环境变量注入；不要提交到源码或 Docker image。
- 前端：`NEXT_PUBLIC_*` 会进入浏览器包，不应承载真正服务端密钥。

## 5. 服务清单

| 服务 | 入口命令 | 端口 | 依赖 | 健康检查 |
|---|---|---:|---|---|
| Web 开发服务 | `cd apps\web; bun run dev` | `3000` | Bun、Node 兼容运行时、Next.js 依赖、可选 API `8000` | 浏览器访问 `/`；真实 API 模式下需 API 可达。 |
| Web 生产服务 | `cd apps\web; bun run build; bun run start` | `3000` | Bun、Next standalone 输出、`public` 和 `.next\static` 已复制 | 浏览器访问 `/`；观察 `server.log`。 |
| API 服务 | `uvicorn apps.api.app.main:app --reload --port 8000` | `8000` | Python、FastAPI、Uvicorn、Pydantic、PyYAML、workflow 文件、storage 写权限 | `GET /health`。 |
| Caddy 反代 | `caddy run --config apps\web\Caddyfile` | `81` | Caddy、本机 Web 服务 `3000` 或 `XTransformPort` 指定端口 | 访问 `http://127.0.0.1:81`。 |

## 6. 日志、storage、生成物说明

### 日志位置

- Web 开发日志：`apps\web\dev.log`
- Web 生产日志：`apps\web\server.log`
- API 当前已有本地日志文件样例：`apps\api\api-8001.log`、`apps\api\api-8001.err.log`
- 项目事件日志：`storage\projects\<project_slug>_<project_id>\logs\events.jsonl`
- 项目错误日志：`storage\projects\<project_slug>_<project_id>\logs\errors.log`

### storage 数据位置

默认 `STORAGE_ROOT=storage`。项目创建后写入：

```text
storage\projects\<project_slug>_<project_id>\
├── uploads\
├── assets\
├── clips\
├── audio\
├── exports\
├── logs\
└── project.db
```

说明：

- `project.db` 是每个项目的 SQLite 数据库。
- `uploads` 保存教材上传文件。
- `assets`、`clips`、`audio`、`exports` 是生成资产位置。
- `logs` 保存项目级事件和错误日志。

### 生成物

- Web 构建输出：`apps\web\.next`
- Web 依赖：`apps\web\node_modules`
- Python 缓存：`__pycache__`
- pytest 缓存：`.pytest_cache`
- graphify 输出：`graphify-out`、`apps\web\graphify-out`

## 7. .gitignore 与防误提交检查

当前根 `.gitignore` 已覆盖：

- `.env`、`.env.local`、`.env.*.local`
- `node_modules`、`.venv`、`venv`
- `.next`、`dist`、`build`
- `*.log`、`logs`
- `storage`、`projects`
- SQLite 运行文件：`*.db`、`*.db-journal`、`*.db-wal`、`*.db-shm`
- 前端上传目录与下载截图：`apps\web\upload`、`apps\web\download`
- 常见大文件：`*.mp4`、`*.wav`、`*.mp3`、`*.pptx`、`*.pdf`、`*.docx`，其中 `docs` 下 PDF/PPTX 有例外允许规则。

本轮只读检查结论：

- 未发现 `.env`、storage、SQLite 数据库或日志文件已被 git 跟踪。
- `apps\api\.env.example` 存在但为空，需要后续补变量名占位说明。
- `apps\web\.gitignore` 也覆盖了 `apps\web\.env*`、`.next`、`dev.log`、`server.log`。

建议新增或确认：

- 将 `graphify-out/` 和 `apps/web/graphify-out/` 是否作为生成物忽略交由架构师确认；当前仓库已有相关输出目录。
- 明确 `docs` 下 PDF/PPTX 白名单是否需要继续保留，避免误提交大体积非正式交付物。

## 8. Docker/compose 缺口清单

### 当前缺什么

- Web Dockerfile。
- API Dockerfile。
- `docker-compose.yml` 或等价 compose 文件。
- `.dockerignore`。
- API 依赖锁定文件或安装说明，如 `requirements.txt`、`pyproject.toml`。
- 非密钥版 `.env.example` 内容，尤其是 `apps\api\.env.example`。
- 容器内 storage 卷挂载约定。
- 容器健康检查与启动顺序。
- 日志输出到 stdout/stderr 还是文件的统一约定。
- 备份/恢复脚本或手册。
- 生产回滚手册。

### 应由运维补齐

- 最小 Web/API Dockerfile 草案。
- 最小 compose 草案，包含 Web、API、storage volume、环境变量占位、健康检查。
- `.dockerignore`。
- 部署版 Runbook、备份/恢复/回滚手册。
- 密钥注入规范和日志脱敏规范。

### 需要后端确认

- API 生产启动命令是否仍用 `uvicorn`，还是需要 `gunicorn + uvicorn worker`。
- API Python 版本与依赖清单。
- 真实 provider 的超时、重试、并发、任务队列和长任务模型。
- SQLite 是否允许多进程/多副本访问；如不允许，生产是否必须单实例或迁移到外部数据库。
- `MINMAX_VIDEO_MODEL`、`MINMAX_TTS_MODEL`、`OCTO_VIDEO_PROVIDER` 当前是否为保留配置或已接入配置。
- `/health` 是否需要扩展为检查 workflow、storage 写权限和 provider 配置状态。
- CORS 和鉴权的生产策略。

## 9. Cloud Run/内网部署风险

### Cloud Run 风险

- Cloud Run 文件系统非持久，`storage` 必须改为挂载卷、对象存储或外部数据库/文件服务。
- SQLite 不适合多实例共享写入；Cloud Run 多实例会放大写冲突和状态不一致风险。
- 视频生成与下载可能超过请求生命周期，需要后端确认异步任务队列、回调或任务轮询方案。
- `NEXT_PUBLIC_API_TOKEN` 会暴露在浏览器，不适合作为正式 API 密钥。
- Cloud Run 需要明确 Secret Manager 注入、最小权限、出网访问、超时和并发配置。

### 内网部署风险

- 本地磁盘 storage 需要备份策略、容量告警和恢复演练。
- 单机 SQLite 需要明确并发边界和文件锁风险。
- Caddy 反代需要 TLS、访问控制、日志轮转和端口开放策略。
- provider 出网需要代理、白名单或网络策略确认。
- 内网密钥文件权限需要限制到运行账号。

路线选择：

- `docker-compose` 优先还是 Cloud Run 优先，列为待首席系统架构师裁决。

## 10. 需要后端确认的问题

- API 依赖清单和 Python 版本。
- API 生产启动方式。
- `/health` 是否应纳入 workflow、storage、provider 配置检查。
- `BACKEND_API_TOKEN` 未配置时接口开放是否允许保留到正式部署前。
- SQLite 单项目一库模型在多并发、多实例下的边界。
- 真实 provider 的任务状态、超时、重试、下载与失败恢复策略。
- `apps\api\.env.example` 应补哪些变量默认值和注释。
- `CAPABILITIES_PATH` 文件缺失时是否应阻断启动，还是仅让 `/video/capabilities` 返回错误。

## 11. 需要测试工程师回归的问题

- 新人按本文从空环境启动 API，`GET /health` 可访问。
- 新人按本文从空环境启动 Web，浏览器可访问首页。
- Web demo/mock 模式与真实 API 模式切换行为可复核。
- API 未配置 `BACKEND_API_TOKEN` 与配置后 Bearer token 行为可复核。
- CORS 在 `localhost:3000`、`127.0.0.1:3000` 下可复核。
- 创建项目后 storage 目录结构、`project.db`、项目日志文件位置可复核。
- `.env`、日志、SQLite、storage、`.next` 不进入 git 跟踪。
- `bun run build` 与 `bun run start` 的生产启动链路由测试工程师按测试计划复核；运维本轮不宣布通过。

## 12. 下一步建议

1. 后端工程师补齐 API 依赖清单、`.env.example`、生产启动建议和健康检查边界。
2. 首席系统架构师裁决：当前阶段优先补 `docker-compose` 本地内网部署，还是按 Cloud Run 约束推进。
3. 运维在路线裁决后补 Dockerfile、compose 或 Cloud Run 配置草案。
4. 测试工程师基于本文建立“新人冷启动验收清单”，覆盖 Web、API、storage、日志和防误提交。
5. 正式部署前补备份/恢复/回滚演练记录。
