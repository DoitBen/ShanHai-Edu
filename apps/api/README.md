# ShanHaiEdu API MVP

视频闭环 MVP 后端，负责项目落盘、教材上传、节点状态机、节点版本、任务记录和后续 provider 服务端调用。

## 本地依赖

建议使用 Python 3.11+。首次运行前在仓库根目录安装依赖：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
python -m pip install -r apps\api\requirements.txt
```

## 本地演示启动

从仓库根目录启动 API：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE="fake"
$env:VIDEO_PROVIDER_MODE="placeholder"
$env:BACKEND_API_TOKEN=""
uvicorn apps.api.app.main:app --reload --port 8000
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

本地演示默认使用 `PROVIDER_MODE=fake`，不需要真实密钥，可以跑通创建项目、项目列表、manifest、节点详情、教材上传、教材解析生成、approve、教案生成和 approve。

`VIDEO_PROVIDER_MODE=placeholder` 表示最终视频节点使用本地占位视频链路，不调用真实 Octo 视频服务。

`TTS_PROVIDER_MODE=placeholder` 表示最终视频旁白使用本地占位音频；真实演示时设置为 `real`，并在服务端环境或 `apps\api\.env` 配置：

```powershell
TTS_PROVIDER_MODE=real
MINIMAX_API_KEY=<redacted>
MINIMAX_TTS_MODEL=speech-2.8-hd
MINIMAX_TTS_VOICE_ID=Chinese (Mandarin)_Gentleman
```

后端仍兼容旧变量名 `MINMAX_API_KEY` / `MINMAX_TTS_MODEL`，但新配置优先使用 `MINIMAX_*`。

## DeepSeek LLM 模式

全链路冲刺的真实文本生成使用 DeepSeek。配置写入服务端环境或本地忽略文件 `apps\api\.env`：

```powershell
PROVIDER_MODE=real
VIDEO_PROVIDER_MODE=placeholder
DEEPSEEK_API_KEY=<redacted>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

`PROVIDER_MODE=real` 只控制文本 LLM provider。若要调用真实视频 provider，需另外显式设置：

```powershell
VIDEO_PROVIDER_MODE=real
OCTO_API_KEY=<redacted>
OCTO_BASE_URL=https://otuapi.com
```

本地端到端演示推荐使用 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`，即 DeepSeek 负责文本链路，最终视频使用本地占位 MP4。

真实 Octo 视频链路需要单独诊断，不和 fullchain 演示混跑：

```powershell
$env:PROVIDER_MODE="fake"
$env:VIDEO_PROVIDER_MODE="real"
$env:OCTO_API_KEY="<redacted>"
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000

powershell -ExecutionPolicy Bypass -File scripts\smoke-octo-real-video.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000
```

该 smoke 只提交 1 个固定镜头，证据写入 `docs\qa-audits\octo-real-video-smoke\`，输出会脱敏。
真实视频默认模型为 `omni_flash-10s`，并走 OTU/NewAPI 的 task 路线：提交 `/v1/videos`，查询 `/v1/videos/{task_id}`，完成后下载返回的 `video_url` / `url` / `result_url`。不要用 MiniMax `file_id` 下载路径处理 NewAPI 任务。

完整接口、节点契约、错误码和验证方式见 `docs\llm-provider-contract.md`。

## 配置文件

可复制 `apps\api\.env.example` 为 `apps\api\.env` 后填写本机配置。真实 provider 密钥只能放服务端环境变量或本地忽略文件，不要写入前端、源码、日志或提交信息。

配置优先级：

```text
create_app(overrides) > 进程环境变量 > apps\api\.env / .env > 默认值
```

本地演示时可通过进程环境变量临时覆盖 `.env`，例如强制 `PROVIDER_MODE=fake` 或 `VIDEO_PROVIDER_MODE=placeholder`，避免误触发真实 provider。

## 常用验证

后端自动化测试：

```powershell
python -m pytest apps\api\tests -q
```

当前本地演示基线允许已知上线前风险保留为 `xfail`：

- provider schema 严格校验缺口。
- 未配置 `BACKEND_API_TOKEN` 时接口对本地联调开放。

## 前端联调接口

前端本地演示至少依赖以下接口：

- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/nodes/{node_id}`
- `POST /projects/{project_id}/textbook`
- `POST /projects/{project_id}/nodes/{node_id}/generate`
- `POST /projects/{project_id}/nodes/{node_id}/approve`

接口契约详见 `docs\api-contracts\backend-mvp-api-contract.md`。
