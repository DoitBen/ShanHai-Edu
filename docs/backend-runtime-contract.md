# ShanHaiEdu API 运行契约

> 任务 ID：T006
> 角色席位：后端 1
> 日期：2026-06-24
> 范围：API 运行契约文档。本文只描述当前后端运行方式、配置边界、风险和生产前必须补齐项，不实现新业务功能，不读取或记录真实密钥。

## 1. 结论

当前 `apps\api` 是 FastAPI 后端，必须从仓库根目录启动，默认健康检查为 `GET /health`。本地和内测演示可以使用 `PROVIDER_MODE=fake`、`VIDEO_PROVIDER_MODE=placeholder`、`IMAGE_PROVIDER_MODE=placeholder`、`TTS_PROVIDER_MODE=placeholder` 跑通主要链路；真实 provider 需要只在后端运行环境注入密钥。

当前运行口径仍是本地/内测级，不是生产级上线契约。生产前必须补齐强制鉴权、密钥注入、单实例或外部数据库策略、storage 持久化与备份、日志轮转、外部 provider 超时/重试/任务队列策略和部署健康检查。

本文可作为 T008 容器化草案和 T009 测试计划的直接输入。

## 2. 启动目录、Python 与依赖

### 启动目录

API 必须从仓库根目录启动：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
```

原因：

- 默认 `WORKFLOW_ROOT=workflow`，依赖仓库根目录下的 workflow 配置。
- 默认 `CAPABILITIES_PATH=docs/api-research/octo-video/capabilities.json`，也是仓库根相对路径。
- 默认 `STORAGE_ROOT=storage`，会在仓库根目录下写运行数据。

### Python 版本

推荐 Python `3.11.x`。当前依赖未锁定到 patch 版本，T008 容器化建议固定基础镜像为 Python 3.11 slim 系列，并在构建日志中记录 `python --version`。

### 依赖入口

依赖文件：

```text
apps\api\requirements.txt
```

安装命令：

```powershell
python -m pip install -r apps\api\requirements.txt
```

当前依赖覆盖 FastAPI、Uvicorn、Pydantic、PyYAML、multipart 上传、pytest、httpx 和 `python-pptx`。未发现生产锁文件；生产前建议由 T008 决定是否补 `requirements.lock.txt` 或使用镜像层固定依赖版本。

## 3. 开发启动与生产启动建议

### 本地开发启动

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE="fake"
$env:VIDEO_PROVIDER_MODE="placeholder"
$env:IMAGE_PROVIDER_MODE="placeholder"
$env:TTS_PROVIDER_MODE="placeholder"
$env:BACKEND_API_TOKEN=""
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload
```

说明：

- `--reload` 仅用于本地开发。
- `BACKEND_API_TOKEN=""` 只允许在隔离本机演示中使用。
- 如果前端端口不是 3000，需同步设置 `CORS_ORIGINS`。

### 内测/生产启动建议

当前代码未提供正式进程管理配置。T008 容器化草案建议采用：

```powershell
python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```

生产注意：

- 不使用 `--reload`。
- 运行账号必须只拥有必要的 storage 读写权限。
- 必须配置 `BACKEND_API_TOKEN` 或升级到正式 JWT/RBAC/session 体系。
- 必须把密钥通过运行环境、secret manager 或 compose secret 注入，不能 baked into image。
- 当前 SQLite/storage 设计不支持随意横向多副本写入；生产部署默认应单 API 实例，除非先迁移数据库和文件存储。

## 4. 健康检查边界

当前健康检查：

```text
GET /health
```

当前返回内容只证明：

- FastAPI 进程可响应。
- workflow 配置对象已加载，并返回 `workflow_version`。

当前不证明：

- storage 可写。
- SQLite 文件可创建或可迁移。
- `BACKEND_API_TOKEN` 已配置。
- DeepSeek、Minimax、Octo、图片 provider、TTS provider 可连通。
- ffmpeg 可用。
- CORS 配置符合当前 Web 端口。

T008 容器健康检查可以先使用 `/health` 做 liveness。T009 应另外补 readiness 验收步骤：创建临时项目、检查 storage 写入、按目标 provider 模式执行最小 smoke。

## 5. 环境变量契约

只记录变量名和用途，不记录真实值。

### 基础运行变量

| 变量名 | 是否敏感 | 当前默认/边界 | 用途 |
|---|---:|---|---|
| `STORAGE_ROOT` | 否 | 默认 `storage` | API 运行数据根目录。 |
| `WORKFLOW_ROOT` | 否 | 默认 `workflow` | workflow、schema、rules、prompts 配置根目录。 |
| `CAPABILITIES_PATH` | 否 | 默认 `docs/api-research/octo-video/capabilities.json` | 视频能力矩阵路径；缺失时 `/video/capabilities` 返回错误，不阻断 API 启动。 |
| `CORS_ORIGINS` | 否 | 默认允许本机 3000 | FastAPI 允许的前端来源，逗号分隔。 |
| `BACKEND_API_TOKEN` | 是 | 未配置时普通 API 放行 | 后端 Bearer token。生产不得为空。 |

### Provider 模式变量

| 变量名 | 是否敏感 | 当前默认/边界 | 用途 |
|---|---:|---|---|
| `PROVIDER_MODE` | 否 | 默认 `fake` | 文本 LLM 模式：`fake`、`real`、`deepseek`、`minimax`。 |
| `VIDEO_PROVIDER_MODE` | 否 | 默认 `placeholder` | 视频 provider 模式：`placeholder`、`fake`、`real`。 |
| `IMAGE_PROVIDER_MODE` | 否 | 默认 `placeholder` | API 内图片 provider 模式；`real` 时启用 `NewApiImageProvider`。 |
| `TTS_PROVIDER_MODE` | 否 | 默认 `placeholder` | 旁白 TTS 模式；`real` 时启用 Minimax TTS。 |

### 文本 LLM 变量

| 变量名 | 是否敏感 | 用途 |
|---|---:|---|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek 服务端密钥。 |
| `DEEPSEEK_BASE_URL` | 否/可能敏感 | DeepSeek chat completions base URL。 |
| `DEEPSEEK_MODEL` | 否 | DeepSeek 文本模型名。 |
| `MINMAX_API_KEY` | 是 | Minimax 文本/TTS 兼容旧变量。 |
| `MINMAX_BASE_URL` | 否/可能敏感 | Minimax base URL 兼容旧变量。 |
| `MINMAX_TEXT_MODEL` | 否 | Minimax 文本模型名，`M3` 会映射为 `MiniMax-M3`。 |
| `MINIMAX_API_KEY` | 是 | Minimax 新命名密钥，优先于 `MINMAX_API_KEY`。 |
| `MINIMAX_BASE_URL` | 否/可能敏感 | Minimax 新命名 base URL，优先于 `MINMAX_BASE_URL`。 |

### 图片 provider 变量

| 变量名 | 是否敏感 | 用途 |
|---|---:|---|
| `IMAGEGEN_MYSELF_API_KEY` | 是 | 图片 provider 服务端密钥。 |
| `IMAGEGEN_MYSELF_BASE_URL` | 否/可能敏感 | OpenAI-compatible 图片 API base URL。 |
| `IMAGEGEN_MYSELF_PRIMARY_API_KEY` | 是 | 主图片 provider 密钥，优先级高。 |
| `IMAGEGEN_MYSELF_PRIMARY_BASE_URL` | 否/可能敏感 | 主图片 provider base URL。 |
| `NEWAPI_PRIMARY_API_KEY` / `NEWAPI_PRIMARY_BASE_URL` | 是/否 | NewAPI-compatible 主图片 provider 别名。 |
| `NEWAPI_API_KEY` / `NEWAPI_BASE_URL` | 是/否 | NewAPI-compatible 图片 provider 别名。 |
| `IMAGEGEN_API_KEY` / `IMAGEGEN_BASE_URL` | 是/否 | 通用图片 provider 别名。 |
| `PINAI_PRIMARY_API_KEY` / `PINAI_PRIMARY_BASE_URL` | 是/否 | PinAI-compatible 主图片 provider 别名。 |
| `PINAI_API_KEY` / `PINAI_BASE_URL` | 是/否 | PinAI-compatible 图片 provider 别名。 |
| `AIRCODE_PRIMARY_API_KEY` | 是 | AirCode-compatible 主图片 provider 密钥别名。 |
| `AIRCODE_API_KEY` | 是 | AirCode-compatible 图片 provider 密钥别名。 |
| `OPENAI_API_KEY` | 是 | OpenAI-compatible 图片 provider fallback 密钥别名。 |
| `IMAGEGEN_MODEL` / `NEWAPI_IMAGE_MODEL` / `IMAGEGEN_MYSELF_MODEL` | 否 | 图片模型名，默认 `gpt-image-2`。 |

### 视频与 TTS 变量

| 变量名 | 是否敏感 | 用途 |
|---|---:|---|
| `OCTO_API_KEY` | 是 | Octo/OTU NewAPI 视频 provider 服务端密钥。 |
| `OCTO_BASE_URL` | 否/可能敏感 | Octo/OTU base URL。 |
| `OCTO_VIDEO_PROVIDER` | 否 | provider 标签。 |
| `VIDEO_MODEL` | 否 | 后端默认视频模型覆盖变量。 |
| `OMNI_DEFAULT_MODEL` / `NEWAPI_DEFAULT_MODEL` | 否 | 视频模型 fallback。 |
| `OMNI_DEFAULT_SIZE` / `NEWAPI_DEFAULT_SIZE` | 否 | 视频尺寸 fallback。 |
| `MINIMAX_TTS_MODEL` / `MINMAX_TTS_MODEL` | 否 | TTS 模型名。 |
| `MINIMAX_TTS_VOICE_ID` | 否 | TTS 声音 ID。 |
| `FFMPEG_PATH` | 否 | 运维预留；当前后端代码不读取，仍从 `PATH` 查找 `ffmpeg`。 |

### 配置读取优先级

当前代码优先级：

```text
create_app(overrides) > 进程环境变量 > .env / apps\api\.env / skills\imagegen-myself\.env.local > 默认值
```

生产风险：

- `skills\imagegen-myself\.env.local` 会被当前 settings 读取。生产镜像或部署包应避免携带本地私有 env 文件。
- T008 应显式声明容器只通过环境变量或 secret 注入配置，不依赖仓库内任何真实 `.env`。

## 6. 鉴权默认策略

当前普通 API 鉴权由 `BACKEND_API_TOKEN` 控制：

- 未配置 token：普通受保护接口放行，适合隔离本机开发和内测演示。
- 配置 token：请求必须带 `Authorization: Bearer {后端令牌}`；缺失返回 401，错误 token 返回 403。

当前 admin API 策略更严格：

- 未配置 token：admin 路由返回 404，隐藏管理入口。
- 配置 token：同样要求 Bearer token，不匹配返回 404。

生产结论：

- 当前只是演示级 token 策略，不是生产级权限体系。
- 没有正式用户身份、JWT/session、RBAC、租户隔离、项目行级权限和审计闭环。
- 生产环境必须至少强制 `BACKEND_API_TOKEN` 非空；正式上线前应升级为用户身份与项目级授权。
- 前端不得把 token 放入 `NEXT_PUBLIC_*`；只能由 Next 服务端代理注入。

## 7. Storage 与 SQLite 运行边界

默认 storage 结构：

```text
<STORAGE_ROOT>\projects\<project_slug>_<project_id>\
├── uploads\
├── assets\
├── clips\
├── audio\
├── exports\
├── outputs\
├── logs\
└── project.db
```

另有控制面和 prompt registry 数据库：

```text
<STORAGE_ROOT>\control_plane.db
<STORAGE_ROOT>\prompt_registry.db
```

当前数据库模型：

- 每个项目一个 SQLite `project.db`，包含项目元数据、节点状态、版本、任务、事件、错误、规则日志、状态迁移等表。
- control plane 和 prompt registry 是 storage 根目录下独立 SQLite 文件。
- 文件下载接口限制在当前项目目录下，避免直接暴露任意本地路径。

运行边界：

- 当前适合单机、单 API 实例、本地磁盘或持久卷。
- 不适合多个 API 副本同时写同一组 SQLite 文件。
- 不适合 Cloud Run 无持久文件系统的默认形态。
- 备份必须同时覆盖 SQLite、uploads、assets、clips、audio、outputs、exports 和 logs。

生产前必须补：

- 明确单实例部署，或迁移到外部数据库与对象存储。
- SQLite 备份/恢复手册，包含 WAL/SHM 文件处理。
- storage 卷容量、权限、保留周期和清理策略。
- 运行日志与项目错误日志的轮转策略。
- 数据迁移策略；当前没有正式迁移工具链。

## 8. Provider 模式与任务状态边界

### 文本 provider

`PROVIDER_MODE=fake` 使用 `FakeProvider`，无需密钥。`PROVIDER_MODE=real|deepseek` 使用 DeepSeek。`PROVIDER_MODE=minimax` 使用 Minimax。

当前文本 provider 行为：

- DeepSeek 和 Minimax 会要求输出合法 JSON。
- JSON 解析或 schema 必填缺失失败时返回 provider 级错误，通常标记 `retryable=true`。
- 缺少密钥或 base URL 返回不可重试错误。
- 文本请求当前通过同步 HTTP 调用完成，不是后台队列。

边界：

- provider 输出质量、稳定性和 schema 完整性仍需按节点测试覆盖。
- `/health` 不检查文本 provider 连通性。
- 生产前应定义请求超时、重试次数、并发限制和成本日志策略。

### 图片 provider

`IMAGE_PROVIDER_MODE=placeholder` 不调用真实图片 provider。`IMAGE_PROVIDER_MODE=real` 时，`intro_video_asset/generate` 会创建 `image_generation` task，并下载图片到：

```text
assets\generated_images\*.png
```

当前图片 provider 行为：

- 支持 OpenAI-compatible 图片接口。
- 空响应、非 JSON、HTTP 错误、远端断连和 timeout 会包装为 provider 错误。
- task 会暴露 `provider_task_id`、`image_url`、`image_path`、`download_status`、`error_code`、`retryable` 等诊断字段。
- 单张图可通过 `POST /projects/{project_id}/tasks/{task_id}/retry` 重提。

边界：

- 图片真实产物不得提交。
- provider 账号池、模型权限和网络波动不属于本地代码通过的证明。
- `/health` 不检查图片 provider ready。

### 视频 provider

`VIDEO_PROVIDER_MODE=placeholder|fake` 不提交真实 Octo；`VIDEO_PROVIDER_MODE=real` 使用 Octo/OTU NewAPI：

- 提交：`POST /v1/videos`
- 查询：`GET /v1/videos/{provider_task_id}`
- 下载：从返回的 `video_url` / `url` / `result_url` 下载 MP4。

当前任务状态原则：

- `final_video/generate` 真实模式先创建本地 `submitting` task。
- submit 成功后 task 状态来自 provider，通常为 `queued`、`processing`、`completed`、`failed` 或 `unknown`。
- submit 失败时 task 写为 `failed`，`final_video` 节点写 provider failed 版本，不用 placeholder 冒充真实结果。
- `GET /projects/{project_id}/tasks/{task_id}` 会同步查询 provider；completed 后下载 clip 到 `clips\{shot_id}.mp4`。
- 全部当前视频 task `completed` 且 `download_status=downloaded` 后，才尝试合成 `outputs\final_video.mp4`。
- ffmpeg 缺失或合成失败写 `FINAL_VIDEO_COMPOSE_FAILED`，不伪造成片。
- `POST /projects/{project_id}/tasks/{task_id}/retry` 用于真实重提单个图片或视频 task。

边界：

- 真实视频 smoke 必须单独跑，不应和完整 E2E 混在一起。
- 当前没有独立后台 worker；长任务依赖前端或测试轮询 task 查询推动状态同步。
- 多 clip 合成依赖 `PATH` 中的 `ffmpeg`。
- 单 clip 不等同完整 final_video 合成验收。

### TTS provider

`TTS_PROVIDER_MODE=placeholder` 写本地占位旁白音频。`TTS_PROVIDER_MODE=real` 使用 Minimax TTS，并输出 `audio\narration.mp3`。

边界：

- TTS 真实模式需要服务端密钥。
- TTS 失败会影响 final video artifact finalize；生产前应补专项 smoke 和错误恢复策略。

## 9. 超时、重试与错误处理边界

当前代码事实：

- 通用 `_request_json()` 对 HTTP 408、429、500、502、503、504 标记为 `retryable=true`。
- 网络断连、socket timeout、远端断开通常标记为可重试。
- 视频和图片下载使用 120 秒 timeout。
- DeepSeek/Minimax 文本 JSON 解析在 provider 内部做 2 次尝试。
- API 路由遇到 `ProviderError` 统一返回 HTTP 502，携带 `code`、`retryable`、可选 `http_status` 和脱敏 `response_excerpt`。
- response excerpt 会脱敏 Bearer、API key、token、secret 和常见 key 前缀。

当前缺口：

- 没有全局请求超时配置变量。
- 没有进程级并发限制。
- 没有持久后台队列、死信队列或自动退避重试。
- task 状态同步依赖查询接口触发。
- provider 成本、额度和账号池健康只做部分日志，不是正式监控。

生产前必须补：

- 明确各 provider connect/read timeout、最大重试次数、退避策略。
- 明确 429/503/额度耗尽的用户提示与自动重试边界。
- 长任务应迁移到后台 worker 或外部任务队列。
- 建立 provider 失败率、平均耗时、队列堆积、成本和下载失败监控。

## 10. 给 T008 的容器化输入

T008 建议按以下约束设计：

- API 容器工作目录必须是仓库根或等价布局。
- Dockerfile 使用 Python 3.11。
- 安装入口使用 `apps\api\requirements.txt`。
- 启动命令不带 `--reload`。
- 暴露端口 `8000`。
- liveness 先使用 `GET /health`。
- readiness 需要自定义脚本：检查 storage 可写、workflow 存在、必要 env 已配置。
- 挂载持久卷到 `STORAGE_ROOT`。
- 默认单 API 实例，除非先迁移 SQLite。
- 不把 `.env`、`skills\imagegen-myself\.env.local`、storage、logs、provider 输出打进镜像。
- `ffmpeg` 是否安装进 API 镜像由 T008 按真实视频合成需求决定；如果不安装，必须标记真实 final_video 多 clip 合成不可用。
- `BACKEND_API_TOKEN`、provider keys 通过 secret 注入。

## 11. 给 T009 的测试输入

T009 至少覆盖：

- 新人从空环境安装 `apps\api\requirements.txt` 后可启动 API。
- `GET /health` 返回 200，但测试报告必须说明它不代表 provider/storage readiness。
- 未配置 `BACKEND_API_TOKEN` 时普通接口放行；配置后无 token 为 401，错误 token 为 403。
- admin 接口未配置 token 时返回 404；配置后错误 token 仍隐藏为 404。
- `CORS_ORIGINS` 对当前 Web 端口生效。
- 创建项目后 storage 目录和 `project.db` 写入成功。
- `PROVIDER_MODE=fake` + placeholder 模式可跑最小项目链路。
- `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 只验文本真实链路，不声明真实视频通过。
- `VIDEO_PROVIDER_MODE=real` 单独 smoke，检查 task 从 submit 到 query/download 的状态和失败脱敏。
- `IMAGE_PROVIDER_MODE=real` 单图 smoke，检查失败时 task/error 写入和 retryable 字段。
- `TTS_PROVIDER_MODE=real` 如纳入范围，应单独 smoke，不并入默认 E2E。
- 缺失 ffmpeg 时真实多 clip 合成应失败并写 `FINAL_VIDEO_COMPOSE_FAILED`，不得生成假成功。
- `.env`、SQLite、storage、真实图片/视频/PPT 产物不得进入 git 跟踪。

## 12. 当前不承诺

- 不承诺生产级 RBAC、多租户和行级权限已完成。
- 不承诺多 API 实例或 Cloud Run 横向扩容可用。
- 不承诺真实 provider 当前账号池、额度、模型权限和网络状态可用。
- 不承诺任意教材泛化、真实 MinerU、PPT 主链路或多浏览器验收通过。
- 不承诺 `/health` 是完整 readiness。
- 不承诺 `FFMPEG_PATH` 已被后端消费。

## 13. Workspace 用户态契约补充

T144 起，`GET /projects/{project_id}/workspace` 仍返回 7 个教师用户态步骤，但每个步骤必须把用户字段和开发诊断分开：

- 用户态步骤字段包含 `current_action`、`lock_reason`、`review_summary`、`sub_gates`，供前端展示当前要做什么、为什么未解锁、已完成回看摘要和子门禁状态。
- `developer_diagnostics` 保持顶层折叠区，继续承载底层 `node_id`、`schema`、依赖、规则摘要、状态迁移、artifact 和兼容别名；普通主步骤不依赖这些字段显示。
- PPT 草稿聚合四个子门禁：结构方案、逐页脚本、视觉资产、PPTX 文件，分别来自 `ppt_assembly_plan`、`ppt_page_script`、`ppt_visual_asset`、`pptx_artifact`。
- 视频生成聚合五个子门禁：文稿、分场剧本、资产与首帧、分镜、clip/TTS/合成，分别来自 `intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`、`final_video` 和 `tasks` 中的 clip/TTS 状态。
- 历史命名兼容口径只作为诊断和子门禁 metadata 返回：`lesson-plan-final` 归入 `lesson_plan`，`video-screenplay` 归入 `intro_video_screenplay`，`pptx-generation` 归入 `pptx_artifact`，`video-generation` / `video_clip_generation` 归入 `final_video`。

本补充只做契约聚合，不接真实 provider，不新增外部写入，也不代表真实 PPT/视频质量通过。
