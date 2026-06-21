# T053-T056 真实视频链路复测指南

日期：2026-06-21  
范围：真实 Octo 视频 provider 的提交、查询、下载和多 clip 合成诊断。  
结论口径：先证明真实链路可诊断、可提交、可下载；视频艺术质量、配音、音频检测不在本轮范围。

## 1. 启动 API

从仓库根目录启动：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE='fake'
$env:VIDEO_PROVIDER_MODE='real'
$env:STORAGE_ROOT='storage-octo-real-smoke'
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

必需环境变量：

- `VIDEO_PROVIDER_MODE=real`：启用真实 Octo 视频 provider。
- `OCTO_API_KEY`：只注入后端进程环境或本地忽略文件，禁止打印。
- `OCTO_BASE_URL`：默认可用时保持 `https://otuapi.com`。
- `PROVIDER_MODE=fake`：真实视频专项 smoke 不跑文本 fullchain，避免把 DeepSeek 文本链路混入 Octo 诊断。

## 2. 后端契约测试

```powershell
python -m pytest apps\api\tests\test_real_providers.py -q
```

通过标准：

- Octo submit 失败时仍创建本地 `failed` task。
- task 返回字段包含 `status`、`provider_task_id`、`error_code`、`download_path`、`video_url_present`、`updated_at`。
- submit 成功时 task 暴露 `provider_task_id`。
- task 查询完成后下载到 `clips/{shot_id}.mp4`。
- 单镜头下载不强制合成最终视频。
- 多 clip 全部 downloaded 后才尝试合成 `outputs/final_video.mp4`。

## 3. 真实单镜头 Smoke

API 已按 `VIDEO_PROVIDER_MODE=real` 启动后执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-octo-real-video.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ProjectName "T053 real octo one-shot"
```

脚本行为：

- 只通过公开 HTTP 接口创建项目。
- 通过节点 `edit/approve` 写入最小固定内容，不直接写数据库。
- 只提交 `storyboard.shots[0]` 一个固定镜头。
- 默认模型为 `omni_flash-10s`。
- 走 OTU/NewAPI 路线：`POST /v1/videos` 提交，`GET /v1/videos/{task_id}` 查询，完成后从 `video_url` / `url` / `result_url` 下载；不走 MiniMax `file_id` 下载路线。
- 记录脱敏请求摘要、HTTP 状态、provider task id、原始错误码和响应体摘要。
- 若任务完成且 clip 已下载，保存 `shot_01.mp4` 到证据目录。

通过标准：

- `/health` 返回 `ok=true`。
- `final_video/generate` 返回 200。
- 只创建 1 个 `final_video` task。
- task 顶层存在 `provider_task_id`。
- `/projects/{id}/tasks/{task_id}` 可查询并推进状态。
- 若 provider 返回 completed，后端保存 `clips/shot_01.mp4`，脚本可下载同一 clip。

失败证据：

```text
docs\qa-audits\octo-real-video-smoke\<YYYYMMDD-HHMMSS>\summary.json
```

重点查看：

- `http_status`
- `provider_task_id`
- `task_status`
- `error_code`
- `body_excerpt`
- `failure`

## 4. 多镜头与最终视频

多镜头阶段必须满足：

- 使用 `final_video/generate` 的 `full_run=true` 提交全部 storyboard shots。
- 未显式传入 `model` 时默认使用 `omni_flash-10s`。
- 所有 task 均达到 `completed` 且 `result.download_status=downloaded`。
- 后端才尝试合成 `outputs/final_video.mp4`。
- 真实模式下的 `outputs/final_video.mp4` 必须来自真实 clips 合成，不允许使用 placeholder。
- 缺少 `ffmpeg` 时返回或记录 `FINAL_VIDEO_COMPOSE_FAILED`，不能伪造成片。

## 5. 密钥与日志要求

- 终端、文档、summary、日志摘要不得打印 `DEEPSEEK_API_KEY`、`OCTO_API_KEY` 或 Bearer token。
- 失败响应只保留脱敏 excerpt。
- 证据目录可以保留 task id、HTTP 状态、错误码和文件大小。
- 不提交 `.env`、storage、真实 MP4、真实 PPT 到代码仓库。

## 6. 与 Placeholder 的边界

`VIDEO_PROVIDER_MODE=placeholder` 只用于演示兜底，证明 fullchain、下载和 PPT 嵌入链路可跑。

`VIDEO_PROVIDER_MODE=real` 才代表生产视频链路诊断。本轮真实视频通过不等于质量验收通过；音频、男声、英文音频检测和艺术质量另开后续任务。
