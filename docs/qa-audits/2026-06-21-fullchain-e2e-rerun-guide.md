# T050 Fullchain E2E 复测指南

日期：2026-06-21  
范围：本地真实文本 provider + 占位视频 provider 的 fullchain 契约复测  
结论口径：只判断链路可重复执行，不判断真实视频质量、不做上线验收。

## 1. 启动 API

从仓库根目录启动：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
$env:PROVIDER_MODE='real'
$env:VIDEO_PROVIDER_MODE='placeholder'
$env:STORAGE_ROOT='storage-fullchain-e2e-rerun'
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

必需环境变量：

- `PROVIDER_MODE=real`：文本节点走真实文本 provider。
- `VIDEO_PROVIDER_MODE=placeholder`：最终视频走本地占位 MP4，不调用真实视频 provider。
- `DEEPSEEK_API_KEY`：仅注入后端进程环境或本地忽略文件，禁止打印。
- `DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`：按本地环境配置。

禁止事项：

- 不在终端、文档、日志摘要里输出 `DEEPSEEK_API_KEY` 或 `OCTO_API_KEY` 的真实值。
- 不把 `.env`、storage、下载产物作为代码提交内容。
- 本轮不设置 `VIDEO_PROVIDER_MODE=real` 作为通过条件。

## 2. 契约测试

后端内置契约测试使用 stub 文本 provider，不访问真实 DeepSeek 或 Octo，只验证服务创建和接口链路契约：

```powershell
python -m pytest apps\api\tests\test_fullchain_e2e_contract.py -q
```

通过标准：

- pytest 输出 `1 passed`。
- 测试确认 `PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=placeholder`。
- 测试确认 `video_provider is None`，不会初始化真实 Octo provider。
- 链路完成：创建项目、上传教材输入、`storyboard=approved`、`final_video/generate`、下载 MP4、导出 PPT、PPT 内存在 `ppt/media/*.mp4`。

## 3. Live Smoke

API 已启动后执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-fullchain-e2e.ps1 -ApiBaseUrl http://127.0.0.1:8000
```

默认不传 `-FixturePath` 时，脚本会在本次证据目录生成一个临时 `.txt` 教材 fixture，用于稳定复测 fullchain 接口链路。

可选参数：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-fullchain-e2e.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ProjectName "T052 fullchain rerun" `
  -FixturePath "fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf"
```

如需复测 PDF 教材上传与解析，显式传入 PDF fixture：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-fullchain-e2e.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ProjectName "T052 PDF fullchain rerun" `
  -FixturePath "fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf"
```

PDF 复测前需确认 API 进程已经重启到支持 PDF 解析的最新代码；旧进程可能返回 `GENERATION_INPUT_INVALID / Unsupported textbook type for MVP: .pdf`。

脚本通过标准：

- `/health` 返回 `ok=true`。
- 创建项目成功并输出 `project_id`。
- 教材上传成功。
- 以下节点均生成并 approve：
  - `textbook_parse`
  - `lesson_plan`
  - `intro_selection`
  - `intro_video_script`
  - `intro_video_screenplay`
  - `intro_video_asset`
  - `storyboard`
- `storyboard` 状态为 `approved`。
- `final_video/generate` 返回 `video_path=outputs/final_video.mp4`。
- `GET /projects/{project_id}/outputs/final_video.mp4` 返回 200 且文件非空。
- `POST /projects/{project_id}/export/ppt` 返回 `.pptx` 下载链接。
- 下载 PPT 后，压缩包内至少存在一个 `ppt/media/*.mp4`。
- 终端最后输出 `PASS summary=...summary.json`。

## 4. 失败证据

脚本会把证据写到：

```text
docs\qa-audits\fullchain-smoke-evidence\<YYYYMMDD-HHMMSS>\
```

目录内容：

- `textbook-fixture.txt`：默认 smoke 自动生成的文本教材；显式传 `-FixturePath` 时不会生成。
- `final_video.mp4`：下载到的最终视频文件。
- `lesson-video-demo.pptx` 或后端返回的 PPT 文件名：下载到的 PPT。
- `summary.json`：脱敏摘要，包含 API base URL、项目 ID、文件大小和 PPT 内 MP4 数量。

失败时保留以下信息给后端或测试工程师：

- 失败的接口路径和 HTTP 状态。
- `project_id`。
- 最后一个成功节点。
- API 服务日志中的对应错误码；日志里不得包含真实 key。
- 如果是 `final_video/generate` 失败，重点检查 `VIDEO_PROVIDER_MODE` 是否为 `placeholder`。
- 如果是 PPT 内没有 MP4，重点检查 `export/ppt` 是否复用 `outputs/final_video.mp4`。

## 5. 与 T047 阻塞的区别

T047 阻塞原因是 `PROVIDER_MODE=real` 同时影响文本与视频，导致 `final_video/generate` 调用真实 Octo 并返回 `OCTO_REQUEST_FAILED`。

T050/T052 复测口径固定为：

```text
PROVIDER_MODE=real
VIDEO_PROVIDER_MODE=placeholder
```

因此通过时应看到占位 MP4 主链路产物，而不是依赖 `export/ppt` 兜底生成视频。
