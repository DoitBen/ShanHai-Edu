# 真实生图/视频 API 环境与演示运行手册

> 任务 ID：T066  
> 角色：运维/部署工程师  
> 日期：2026-06-21  
> 范围：真实文本 LLM、生图 provider、视频 provider、storage、ffmpeg、PPT 导出演示运行说明。本文只写变量名、用途和占位说明，不包含真实密钥。

## 1. 结论

当前后端已经把文本 LLM 与视频 provider 拆开：`PROVIDER_MODE` 只控制文本链路，`VIDEO_PROVIDER_MODE` 只控制视频链路。本地演示推荐先用 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 验证 DeepSeek 文本链路和 PPT/MP4 下载；真实 Octo 视频单独用 `VIDEO_PROVIDER_MODE=real` 跑 `scripts\smoke-octo-real-video.ps1`，避免把视频供应商波动和 fullchain 演示混在一起。

生图链路当前不在 `apps\api` 服务内，而由项目内 `skills\imagegen-myself` 的 OpenAI/NewAPI-compatible 脚本负责。生图真实输出应写入临时或 storage 产物目录，并已通过 `.gitignore` 定向防误提交。

`ffmpeg` 当前不是 `.env` 驱动变量，后端合成代码使用 `PATH` 中的 `ffmpeg`；`FFMPEG_PATH` 只作为运维记录/预留变量，除非后端后续明确接入。

## 2. 环境变量总表

### 文本 LLM

| 变量名 | 所属模块 | 是否敏感 | 用途 |
|---|---|---:|---|
| `PROVIDER_MODE` | API | 否 | 文本 provider 模式：`fake`、`real`、`deepseek`、`minimax`。 |
| `DEEPSEEK_API_KEY` | API | 是 | DeepSeek 服务端密钥。 |
| `DEEPSEEK_BASE_URL` | API | 否/可能敏感 | DeepSeek OpenAI-compatible base URL。 |
| `DEEPSEEK_MODEL` | API | 否 | DeepSeek 文本模型名。 |
| `MINMAX_API_KEY` | API | 是 | Minimax 服务端密钥。 |
| `MINMAX_BASE_URL` | API | 否/可能敏感 | Minimax base URL。 |
| `MINMAX_TEXT_MODEL` | API | 否 | Minimax 文本模型名。 |
| `MINMAX_VIDEO_MODEL` | API | 否 | 预留视频模型变量，当前文本链路不依赖。 |
| `MINMAX_TTS_MODEL` | API | 否 | 预留 TTS 模型变量，当前演示不依赖。 |

### 生图 Provider

| 变量名 | 所属模块 | 是否敏感 | 用途 |
|---|---|---:|---|
| `IMAGEGEN_MYSELF_API_KEY` | `skills\imagegen-myself` | 是 | 首选生图 provider 密钥。 |
| `IMAGEGEN_MYSELF_BASE_URL` | `skills\imagegen-myself` | 否/可能敏感 | 首选生图 OpenAI-compatible base URL。 |
| `IMAGEGEN_MYSELF_PRIMARY_API_KEY` | `skills\imagegen-myself` | 是 | 主 provider 密钥，优先级高于通用变量。 |
| `IMAGEGEN_MYSELF_PRIMARY_BASE_URL` | `skills\imagegen-myself` | 否/可能敏感 | 主 provider base URL。 |
| `IMAGEGEN_MYSELF_FALLBACK_API_KEY` | `skills\imagegen-myself` | 是 | 备用 provider 密钥。 |
| `IMAGEGEN_MYSELF_FALLBACK_BASE_URL` | `skills\imagegen-myself` | 否/可能敏感 | 备用 provider base URL。 |
| `NEWAPI_API_KEY` / `NEWAPI_BASE_URL` | `skills\imagegen-myself` | 是/否 | NewAPI-compatible 别名。 |
| `PINAI_API_KEY` / `PINAI_BASE_URL` | `skills\imagegen-myself` | 是/否 | PinAI-compatible 别名。 |
| `AIRCODE_API_KEY` | `skills\imagegen-myself` | 是 | AirCode-compatible 密钥别名。 |
| `AIRCODE_PROVIDER_TIMEOUT` | `skills\imagegen-myself` | 否 | 生图 provider 请求超时秒数。 |

生图脚本会读取当前工作区 `.env` / `.env.local` 和 `skills\imagegen-myself\.env.local`。项目规则要求不要读取或打印真实密钥；演示时只使用 `probe` 查看 masked 状态。

### 视频 Provider

| 变量名 | 所属模块 | 是否敏感 | 用途 |
|---|---|---:|---|
| `VIDEO_PROVIDER_MODE` | API | 否 | 视频 provider 模式：`placeholder`、`fake`、`real`。 |
| `OCTO_API_KEY` | API / `skills\videogen` | 是 | Octo/OTU NewAPI 服务端密钥。 |
| `OCTO_BASE_URL` | API / `skills\videogen` | 否/可能敏感 | Octo/OTU NewAPI base URL。 |
| `OCTO_VIDEO_PROVIDER` | API | 否 | provider 标签，当前通常为 `octo`。 |
| `VIDEO_MODEL` | API / T075 smoke | 否 | 后端 `final_video/generate` 和 T075 smoke 的默认视频模型覆盖变量。 |
| `OMNI_DEFAULT_MODEL` | `skills\videogen` | 否 | videogen helper 默认 Omni 模型。 |
| `OMNI_DEFAULT_SIZE` | `skills\videogen` | 否 | videogen helper 默认 Omni 尺寸。 |
| `NEWAPI_DEFAULT_MODEL` | `skills\videogen` | 否 | NewAPI video 默认模型。 |
| `NEWAPI_DEFAULT_SIZE` | `skills\videogen` | 否 | NewAPI video 默认尺寸。 |

API 内真实视频默认通过 `OctoVideoProvider` 调用 `POST /v1/videos`、`GET /v1/videos/{task_id}`，完成后下载返回的 URL。默认模型优先级为 `VIDEO_MODEL` > `OMNI_DEFAULT_MODEL` > `NEWAPI_DEFAULT_MODEL` > `omni_flash-10s`；T075 smoke 额外支持 `--video-model` 命令行参数作为最高优先级覆盖。

真实参考图传输设计口径：

- 生图成功后，后端必须先把图片下载到当前项目目录，例如 `<project_dir>\assets\generated_images\asset_001.png`。
- 提交真实视频时，默认不得把临时公网图片 URL 作为唯一输入交给 OTU 拉取；应优先用 `multipart/form-data` 直接携带本地图片文件，字段名为 `input_reference`。
- 只有在图片 URL 已通过外部机器无鉴权拉取验证时，才允许降级使用 JSON `images: ["https://..."]`。
- task/result 中需要记录 `reference_submission_mode=multipart|url`、`reference_image_ids`、本地 `reference_image_paths`，以及脱敏后的远程 URL 摘要，便于区分输入预处理失败和视频生成失败。
- 对象存储或临时签名 URL 是可选长期方案；签名 URL 必须允许 OTU 服务端直接 GET，不能只对本机或浏览器会话可见。

### Storage 与 Workflow

| 变量名 | 所属模块 | 是否敏感 | 用途 |
|---|---|---:|---|
| `STORAGE_ROOT` | API | 否 | 运行时项目数据根目录。 |
| `WORKFLOW_ROOT` | API | 否 | workflow 配置根目录。 |
| `CAPABILITIES_PATH` | API | 否 | 视频能力矩阵 JSON 路径。 |
| `BACKEND_API_TOKEN` | API | 是 | 可选后端 Bearer token，本地隔离演示可为空，非隔离环境必须配置。 |
| `CORS_ORIGINS` | API | 否 | 允许的前端来源，逗号分隔。 |

默认项目数据结构：

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

### FFmpeg

| 变量名 | 所属模块 | 是否敏感 | 用途 |
|---|---|---:|---|
| `FFMPEG_PATH` | 运维预留 | 否 | 记录 ffmpeg 可执行文件路径；当前后端不读取此变量。 |
| `PATH` | 操作系统 | 否 | 当前后端通过 `shutil.which("ffmpeg")` 从 `PATH` 查找 ffmpeg。 |

检查命令：

```powershell
ffmpeg -version
where.exe ffmpeg
```

## 3. `.env.example` 更新说明

已更新 `apps\api\.env.example`：

- 只包含变量名和占位说明。
- 不包含真实密钥。
- 覆盖文本 LLM、生图 provider、视频 provider、storage、workflow、CORS、后端 token、ffmpeg 预留变量。

本地使用方式：

```powershell
Copy-Item apps\api\.env.example apps\api\.env
```

然后只在本机未提交的 `apps\api\.env` 中填真实值。提交前必须确认 `apps\api\.env` 被 `.gitignore` 忽略。

## 4. 演示启动手册

### 4.1 后端启动命令

安装依赖：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
python -m pip install -r apps\api\requirements.txt
```

推荐演示模式：真实文本 LLM + 占位视频，适合完整 E2E 演示。

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE="real"
$env:VIDEO_PROVIDER_MODE="placeholder"
$env:STORAGE_ROOT="storage-real-demo"
$env:CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

真实视频 provider 单独演示：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE="fake"
$env:VIDEO_PROVIDER_MODE="real"
$env:STORAGE_ROOT="storage-octo-smoke"
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

另开终端执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-octo-real-video.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000
```

### 4.2 前端启动命令

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu\apps\web
$env:NEXT_PUBLIC_DEMO_MODE="false"
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
bun run dev
```

浏览器访问：

```text
http://127.0.0.1:3000
```

如果前端端口不是 `3000`，必须把对应 `localhost` 和 `127.0.0.1` 来源加入 `CORS_ORIGINS`。

### 4.3 必须检查的 health 接口

API 健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

预期重点：

- HTTP 200。
- 响应体 `ok=true`。
- `data.status=ok`。
- `data.workflow_version` 存在。

Workflow 配置检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/workflow
```

视频能力配置检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/video/capabilities
```

如果返回 `CAPABILITIES_NOT_FOUND`，检查 `CAPABILITIES_PATH` 是否指向存在的 JSON。

### 4.4 如何确认 provider 模式

当前 `/health` 不暴露 provider 模式。用以下无密钥输出命令确认运行时配置：

```powershell
python -c "from apps.api.app.settings import Settings; s=Settings.from_overrides(); print({'provider_mode': s.provider_mode, 'video_provider_mode': s.video_provider_mode, 'storage_root': str(s.storage_root)})"
```

行为侧确认：

- `PROVIDER_MODE=fake`：文本节点由 fake provider 生成，不需要文本密钥。
- `PROVIDER_MODE=real` 或 `deepseek`：文本节点使用 DeepSeek；缺少 `DEEPSEEK_API_KEY` 时会返回 `DEEPSEEK_KEY_MISSING`。
- `PROVIDER_MODE=minimax`：文本节点使用 Minimax；缺少 `MINMAX_API_KEY` 或 `MINMAX_BASE_URL` 时会返回对应错误。
- `VIDEO_PROVIDER_MODE=placeholder`：`final_video/generate` 不调用 Octo，会产出本地占位 MP4。
- `VIDEO_PROVIDER_MODE=real`：`final_video/generate` 会提交 Octo/OTU 任务；task 应出现 `provider_task_id`。

生图 provider masked 检查：

```powershell
python skills\imagegen-myself\scripts\aircode_image_gen.py probe
```

只看 `ready` 和 masked 状态，不复制输出中的任何真实配置。

### 4.5 如何确认 storage 可写

PowerShell 快速检查：

```powershell
$root = if ($env:STORAGE_ROOT) { $env:STORAGE_ROOT } else { "storage" }
$checkDir = Join-Path $root "ops-write-check"
New-Item -ItemType Directory -Force $checkDir | Out-Null
"ok" | Set-Content -LiteralPath (Join-Path $checkDir "write.txt") -Encoding UTF8
Get-Content -LiteralPath (Join-Path $checkDir "write.txt") -Encoding UTF8
```

预期输出为 `ok`。如失败，检查目录权限、路径是否在只读盘、是否被安全软件拦截。

API 行为检查：

- 创建项目后应出现 `<STORAGE_ROOT>\projects\<project_slug>_<project_id>\project.db`。
- 日志目录应出现 `<project_dir>\logs\`。
- 真实视频下载后 clip 应位于 `<project_dir>\clips\*.mp4`。
- 最终视频应位于 `<project_dir>\outputs\final_video.mp4`。
- PPT 导出应位于 `<project_dir>\exports\lesson-video-demo.pptx`。

## 5. 故障排查

### 5.1 生图失败

常见现象：

- `No API key is configured`
- provider 返回 503 或 account pool unavailable
- `upstream_error`
- 返回 URL 但下载失败
- 输出文件已存在

排查顺序：

1. 运行 `python skills\imagegen-myself\scripts\aircode_image_gen.py probe`，确认至少一个 provider `ready=true`。
2. 确认使用的是生图变量：`IMAGEGEN_MYSELF_API_KEY` / `NEWAPI_API_KEY` / `PINAI_API_KEY` / `AIRCODE_API_KEY`，不要误用 `OCTO_API_KEY` 当生图密钥，除非 provider 明确共用。
3. 确认 base URL 是 OpenAI-compatible image endpoint，并带 `/v1` 或脚本可自动补 `/v1`。
4. 先用小规格重试：`1024x1024`、`quality=high`；仍失败再降到 `quality=low`。
5. 文生图 provider 断连时，优先重试 `generate-stream`。
6. 如果 `/v1/images/generations` 被拒绝，说明该 endpoint 可能只支持 chat completions，不支持 OpenAI-style image API。
7. 输出文件已存在时，加 `--force` 或换输出路径；不要覆盖已用于报告的证据文件。

### 5.2 视频 provider 脱敏就绪检查

执行以下命令只会输出变量名、是否存在和非敏感配置值，不会打印真实密钥：

```powershell
python scripts\check_video_provider_readiness.py --require-real --provider-error-code VIDEO_QUOTA_EXHAUSTED
```

输出判定：

- `ok=true`：本地配置满足单 clip 真实 smoke 前置条件，可交给测试执行 T075。
- `blocking_issues` 包含 `VIDEO_PROVIDER_MODE`：当前未启用真实视频 provider。
- `blocking_issues` 包含 `OCTO_API_KEY`：服务端未注入视频 provider 密钥。
- `blocking_issues` 包含 `VIDEO_QUOTA_EXHAUSTED`：配置已可见，但外部账号额度、账号池或模型权限仍阻塞，需要恢复额度或切换可用账号池后再重跑真实 smoke。

2026-06-21 当前脱敏检查结论：

- `VIDEO_PROVIDER_MODE=real` 已生效。
- `OCTO_API_KEY` 已存在但已脱敏。
- `OCTO_BASE_URL` 为公开 base URL。
- 默认视频模型为 `omni_flash-10s`。
- 结合最新 provider 错误码，当前阻塞仍为 `VIDEO_QUOTA_EXHAUSTED`。

如果上游提示当前模型额度耗尽，但同账号池存在其他可用模型，可不改代码，直接通过环境变量切换后端 API 和 T075 使用的模型：

```powershell
$env:VIDEO_MODEL="sora-2-12s"
python scripts\t075_real_fullchain_smoke.py --api-base http://127.0.0.1:8199 --provider-mode real --image-provider-mode real --video-provider-mode real --tts-provider-mode real --image-limit 1 --image-quality low --min-successful-images 1 --video-shot-limit 1 --task-timeout-sec 1200 --poll-interval-sec 15
```

优先级：T075 为 `--video-model` 命令行参数 > `VIDEO_MODEL` > `OMNI_DEFAULT_MODEL` > `NEWAPI_DEFAULT_MODEL` > `omni_flash-10s`；后端 API 为 `VIDEO_MODEL` > `OMNI_DEFAULT_MODEL` > `NEWAPI_DEFAULT_MODEL` > `omni_flash-10s`，请求体显式 `model` 仍优先于默认配置。

### 5.3 视频 submit 失败

常见现象：

- `OCTO_KEY_MISSING`
- `OCTO_REQUEST_FAILED`
- `VIDEO_QUOTA_EXHAUSTED`
- HTTP 401/403/429/500/502/503/504
- task 没有 `provider_task_id`
- OTU 返回 `fail_to_fetch_task`、`媒体预处理失败`、`HTTP 403 下载失败`，且错误中指向参考图 URL

排查顺序：

1. 确认 `VIDEO_PROVIDER_MODE=real`；`placeholder` 不会提交 Octo。
2. 确认 `OCTO_API_KEY` 已在服务端进程环境或本地忽略文件中配置。
3. 确认 `OCTO_BASE_URL` 指向 Octo/OTU NewAPI base URL。
4. 如果错误是参考图 `HTTP 403 下载失败`，先确认项目本地图片文件是否已存在于 `<project_dir>\assets\generated_images\`；该类错误优先按“参考图输入通道失败”处理，不要先归因到模型额度。
5. 对参考图输入通道，默认修复方向是把视频提交改为 `multipart/form-data` + `input_reference=@本地图片`；公网 URL 只作为已验证可被 OTU 服务端拉取的降级路径。
6. 使用 `scripts\smoke-octo-real-video.ps1` 单镜头复测，不要直接跑完整 E2E。
7. HTTP 401/403 且不涉及参考图 URL：优先查密钥权限、账号余额、模型权限。
8. HTTP 429/503：优先按上游限流或账号池不可用处理，稍后重试；不要改代码绕过。
9. task 已创建但 submit 失败时，检查项目 `project.db` 的 tasks/errors 状态和 `<project_dir>\logs\errors.log`。

注意：参考图预处理阶段的 403 与 completed MP4 下载阶段的 403 不是同一个问题。前者发生在创建视频任务前，OTU 服务端无法拉取输入图片；后者发生在任务 completed 后，本机下载 provider 返回的 MP4 URL。后者按 5.4 处理。

### 5.4 视频下载失败

常见现象：

- `OCTO_DOWNLOAD_FAILED`
- task 已 completed，但本地 `clips\*.mp4` 不存在或大小为 0
- provider 返回中没有可用 `video_url` / `url` / `result_url`

排查顺序：

1. 轮询 `GET /projects/{project_id}/tasks/{task_id}`，确认 task 状态为 `completed`。
2. 确认响应里有 `video_url_present=true` 或 result 中存在下载 URL。
3. 检查运行机器是否能访问 provider 返回的 CDN URL。
4. 下载 completed MP4 时使用 browser-like `User-Agent` 和宽松 `Accept`，不要强制 `Referer: https://otuapi.com/`，避免文件主机防盗链返回 403。
5. 检查 `<project_dir>\clips\` 是否可写。
6. 下载失败后不要手工把无效文件改名为 `.mp4` 冒充成功；保留 task 错误供后端排查。

### 5.5 ffmpeg 合成失败

常见现象：

- `FINAL_VIDEO_COMPOSE_FAILED`
- `缺少 ffmpeg，无法合成真实 final_video.mp4`
- `视频片段不存在或为空`
- `ffmpeg 合成输出为空`

排查顺序：

1. 运行 `ffmpeg -version` 和 `where.exe ffmpeg`，确认 `ffmpeg` 在 `PATH` 中。
2. 注意：当前后端不读取 `FFMPEG_PATH`，仅从 `PATH` 查找。
3. 确认至少 2 个视频 task 都是 `completed` 且 `download_status=downloaded`；当前代码单 clip 不触发多 clip 合成。
4. 检查 `<project_dir>\clips\*.mp4` 是否存在且非 0 字节。
5. 如果 concat 失败，检查 clip 编码参数是否一致；当前合成使用 `ffmpeg -f concat -c copy`，不同编码参数可能失败。
6. 合成失败时应记录错误，不允许用 placeholder 伪装真实成片。

### 5.6 PPT 导出失败

常见现象：

- `PPT_EXPORT_FAILED`
- `真实视频模式下缺少已合成的 final_video.mp4`
- `真实视频模式下 final_video.mp4 不能是占位视频`
- `视频嵌入失败`
- `PPTX 保存失败`

排查顺序：

1. 确认 `python-pptx` 已安装：`python -m pip install -r apps\api\requirements.txt`。
2. 确认 `POST /projects/{project_id}/export/ppt` 前，`outputs\final_video.mp4` 已存在。
3. `VIDEO_PROVIDER_MODE=placeholder` 时允许占位 MP4；`VIDEO_PROVIDER_MODE=real` 时不允许占位视频冒充真实输出。
4. 确认 `<project_dir>\exports\` 可写，且目标 PPTX 没有被 PowerPoint 或其他进程占用。
5. 如果嵌入失败，先确认 MP4 文件可被本机播放器打开，再交给后端检查 `python-pptx` 嵌入兼容性。

## 6. Git Ignore 检查

本轮检查和更新后的结论：

- `.env`、`.env.local`、`.env.*.local` 已忽略。
- `apps\api\.env` 继承根 `.gitignore` 的 `.env` 规则，不应提交。
- 真实输出视频：全局 `*.mp4` 已忽略。
- 真实输出音频：全局 `*.wav`、`*.mp3` 已忽略。
- storage 数据：`storage/`、`storage-*/` 已忽略。
- SQLite 运行文件：`*.db`、`*.db-journal`、`*.db-wal`、`*.db-shm` 已忽略。
- provider 日志：新增 `provider-logs/`、`*.provider.log`、`*.provider.jsonl`、`provider-*.log`、`provider-*.jsonl`。
- 生图真实产物：新增 `output/imagegen/`、`docs/qa-audits/imagegen-real-smoke/` 和 `docs/qa-audits/**/*real*.png|jpg|jpeg|webp`。
- 真实视频 smoke 产物：新增 `docs/qa-audits/octo-real-video-smoke/`。
- fullchain smoke 二进制证据：新增 `docs/qa-audits/fullchain-smoke-evidence/` 和 `docs/qa-audits/**/lesson-video-demo.pptx`。

注意：仓库已跟踪 `apps\web\public\logo.png`，所以不能全局忽略 `*.png`；真实图片只能按产物目录和命名规则定向忽略。

## 7. 演示前检查清单

- `apps\api\.env` 只在本机存在，未被 git 跟踪。
- `python -m pip install -r apps\api\requirements.txt` 已完成。
- `Invoke-RestMethod http://127.0.0.1:8000/health` 返回 `ok=true`。
- `python -c "from apps.api.app.settings import Settings; s=Settings.from_overrides(); print({'provider_mode': s.provider_mode, 'video_provider_mode': s.video_provider_mode, 'storage_root': str(s.storage_root)})"` 输出符合本轮演示口径。
- `python skills\imagegen-myself\scripts\aircode_image_gen.py probe` 显示生图 provider ready。
- 真实视频 smoke 前，`VIDEO_PROVIDER_MODE=real`，并且 `scripts\smoke-octo-real-video.ps1` 单独执行。
- 真实视频参考图已落到 `<project_dir>\assets\generated_images\`，视频提交设计默认走本地文件 multipart；若仍走公网 URL，必须先从非本机网络验证该 URL 可无鉴权拉取。
- 多 clip 合成前，`ffmpeg -version` 成功。
- PPT 导出前，`outputs\final_video.mp4` 存在，且当前模式允许该视频类型。

## 8. 剩余风险

- `/health` 当前不直接暴露 provider 模式；运维只能用 Settings 检查命令或行为侧验证。
- `FFMPEG_PATH` 尚未被后端代码消费，仍需通过 `PATH` 配置 ffmpeg。
- 生图 provider 属于项目内 skill 脚本能力，不是 API 服务内 endpoint。
- 真实视频 provider 受上游账号池、模型可用性和网络波动影响，不能和完整课堂内容质量验收混为一谈。
- 真实视频参考图如果继续依赖临时公网 URL，仍可能在 OTU 预处理阶段因源站防盗链、IP 限制、User-Agent 限制或签名过期返回 403；底层设计应优先走本地文件 multipart 上传。
- 当前 `.gitignore` 定向忽略真实 provider 产物；如果后续真实产物目录变化，需要同步补规则。
