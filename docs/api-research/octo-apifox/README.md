# 章鱼哥 Apifox 接口对接指南

更新时间：2026-06-21  
资料来源：用户提供的章鱼哥 Apifox `.md` 文档快照，原文已保存到 `docs\api-research\octo-apifox\raw\`。  
安全边界：本文只写接口路径、模型名、参数和脱敏结论，不记录任何真实 `DEEPSEEK_API_KEY`、`OCTO_API_KEY` 或 Bearer token。

## 结论先行

- ShanHaiEdu 真实视频默认先走章鱼哥 OTU/NewAPI 路线，默认模型为 `omni_flash-10s`。
- OTU/NewAPI 视频和部分异步图片都复用同一条任务路线：`POST /v1/videos` 提交，`GET /v1/videos/{task_id}` 查询，完成后从返回 URL 下载。
- `/v1/videos` 返回的是任务 ID，不是 MiniMax 官方 `file_id`；不能用 `download --file-id` 下载章鱼哥 NewAPI 任务。
- 生产真实视频必须由后端读取环境变量并携带 `Authorization: Bearer <token>`；前端、日志、文档、测试输出都不得接触明文密钥。
- Apifox 里 `失效接口` 分类下的旧 Sora、旧 Nano Banana Gemini 原生、Veo 直出 15s 不作为新接入依据，只保留历史兼容说明。
- 真实 smoke 已证明 `omni_flash-10s` 可以成功提交、轮询到 `completed` 并拿到 `video_url`；当时后端旧下载逻辑带 `Referer` 导致 OSS 403，手动不带 `Referer` 下载成功。后续下载逻辑应保留浏览器类 `User-Agent` 和 `Accept`，不要给 OSS 下载 URL 强行加 `Referer`。

## 本地原文索引

| 分类 | 接口 | 原始链接 | 本地快照 |
|---|---|---|---|
| 图片生成 | 香蕉 Gemini 原生格式 | `https://6l0ket291i.apifox.cn/466136668e0.md` | `raw\image-banana-gemini-native.md` |
| 图片生成 | 香蕉异步 | `https://6l0ket291i.apifox.cn/424561006e0.md` | `raw\image-banana-async.md` |
| 图片生成 | image2 OpenAI 原生格式 | `https://6l0ket291i.apifox.cn/447357296e0.md` | `raw\image2-openai-compatible.md` |
| 图片生成 | gpt-image-2 异步 | `https://6l0ket291i.apifox.cn/447634846e0.md` | `raw\gpt-image-2-async.md` |
| 图片生成 | 任务查询 | `https://6l0ket291i.apifox.cn/455245131e0.md` | `raw\image-task-query.md` |
| 视频生成 | Sora 创建 | `https://6l0ket291i.apifox.cn/454078398e0.md` | `raw\video-sora-create.md` |
| 视频生成 | Omni 创建 | `https://6l0ket291i.apifox.cn/462450037e0.md` | `raw\video-omni-create.md` |
| 视频生成 | Veo 创建 | `https://6l0ket291i.apifox.cn/424653897e0.md` | `raw\video-veo-create.md` |
| 视频生成 | Veo 延长至 15s | `https://6l0ket291i.apifox.cn/440214130e0.md` | `raw\video-veo-extend-15s.md` |
| 视频生成 | 任务查询 | `https://6l0ket291i.apifox.cn/424659184e0.md` | `raw\video-task-query.md` |
| 失效接口 | 旧 Sora 视频接口 | `https://6l0ket291i.apifox.cn/424645155e0.md` | `raw\deprecated-sora-video.md` |
| 失效接口 | 旧 Nano Banana Gemini 原生格式 | `https://6l0ket291i.apifox.cn/426900205e0.md` | `raw\deprecated-nano-banana-gemini-native.md` |
| 失效接口 | 旧 Veo 直出 15s | `https://6l0ket291i.apifox.cn/449549907e0.md` | `raw\deprecated-veo-direct-15s.md` |

## 认证与密钥

所有章鱼哥接口统一使用：

```text
Authorization: Bearer <API_KEY>
```

项目内只允许用变量名描述密钥：

- 后端运行环境：`OCTO_API_KEY`
- 后端章鱼哥地址：`OCTO_BASE_URL`，默认按现有代码使用 `https://otuapi.com`
- 真实视频开关：`VIDEO_PROVIDER_MODE=real`

禁止把真实 token 写入源码、文档、提交信息、测试快照、smoke 输出或前端环境变量。

## 视频接口矩阵

### 通用任务流

1. 提交：`POST /v1/videos`
2. 记录返回的 `id` 或 `task_id`
3. 轮询：`GET /v1/videos/{task_id}`
4. 状态进入完成态后提取结果 URL
5. 立即下载到本地，避免临时 URL 过期

建议状态归一化：

```text
queued, processing, in_progress, completed, failed
SUBMITTED, IN_PROGRESS, SUCCESS, FAILURE
```

建议结果 URL 读取顺序：

```text
data.video_url
video_url
url
result_url
data.url
data.result_url
data.first_video_url
result.video_url
result.url
```

### 可用视频模型

| 模型 | Endpoint | 用途 | 关键参数 | 接入建议 |
|---|---|---|---|---|
| `omni_flash-10s` | `POST /v1/videos` | Omni 文生视频、参考图生视频、视频修改 | `model`、`prompt`、可选 `size`、JSON `images[]` 或 multipart `input_reference`，最多 7 个参考 | ShanHaiEdu 默认真实视频模型；当前先用于 10s 单镜头和多镜头 clip |
| `sora-2-12s` | `POST /v1/videos` | Sora 12s 文生视频或图生视频 | `model`、`prompt`、必填 `size`、JSON `images[]` 或 multipart `input_reference` | 第二选择；只有明确要 Sora 时使用 |
| `veo_3_1-fast` | `POST /v1/videos` | Veo 文生视频、参考图视频 | `model`、`prompt`、可选 `size`、参考图最多 3 张 | 适合需要 Veo 风格或参考图时显式测试 |
| `veo_3_1-fast-fl` | `POST /v1/videos` | Veo 首尾帧视频 | `model`、`prompt`、可选 `size`、1 到 2 张图，顺序为首帧、尾帧 | 只有明确首尾帧需求时用 |
| `veo_3_1-fast-extend` | `POST /v1/videos` | Veo 延长到 15s | `model`、`remix_id`、`prompt` | `remix_id` 来自原任务 `data.remix_id`；文档提示有 12 小时窗口 |

### 视频请求体规则

JSON 适合公网 URL 或 base64 引用：

```json
{
  "model": "omni_flash-10s",
  "prompt": "Chinese male narration. A non-realistic classroom story hook.",
  "size": "1280x720",
  "images": ["https://example.com/reference.png"]
}
```

multipart 适合本地图片或视频文件：

```powershell
curl.exe -X POST "https://otuapi.com/v1/videos" `
  -H "Authorization: Bearer <API_KEY>" `
  -F "model=omni_flash-10s" `
  -F "prompt=Chinese male narration. A non-realistic classroom story hook." `
  -F "size=1280x720" `
  -F "input_reference=@D:\path\reference.png"
```

注意：

- JSON 用 `images[]`，multipart 用重复 `input_reference`；不要混用字段名。
- 图片和视频 URL 必须是公网可访问直链，不能是 HTML 页面、登录态链接或短链落地页。
- `size` 建议显式传入，横屏常用 `1280x720`，竖屏常用 `720x1280`。

## 图片接口矩阵

章鱼哥图片接口分三条路线，不能混成一条。

| 路线 | Endpoint | 模型 | 返回/查询方式 | 使用建议 |
|---|---|---|---|---|
| Gemini 原生同步图片 | `POST /v1beta/models/{model}:generateContent` | `gemini-3-pro-image-preview`、`gemini-3.1-flash-image-preview` | 同步响应，取 `candidates[].content.parts[].image_url.url` 或 `data[0].url` | 不是视频任务，不走 `/v1/videos/{task_id}` |
| `/v1/videos` 异步 Banana 图片 | `POST /v1/videos` + `GET /v1/videos/{task_id}` | `nano_banana_2`、`nano_banana_pro-1K`、`nano_banana_pro-2K`、`nano_banana_pro-4K` | 提交返回任务 ID，完成后取 `url` | 与视频共用任务接口，但产物是图片 |
| `/v1/videos` 异步 GPT 图片 | `POST /v1/videos` + `GET /v1/videos/{task_id}` | `gpt-image-2`、`gpt-image-2-2K`、`gpt-image-2-4K` | 提交返回任务 ID，完成后取 `url` | 这是异步图片任务，不等同于 `image2` |
| OpenAI 兼容图片 | `POST /v1/images/generations`、`POST /v1/images/edits` | `image2` | 多数示例返回 `b64_json`，也可能按响应格式返回 URL | 不走任务查询；适合 OpenAI 兼容图片工作流 |

图片参数差异：

- `nano_banana*` 使用顶层 `aspect_ratio`，常见取值 `1:1`、`9:16`、`16:9`、`auto`。
- `gpt-image-2*` 使用顶层 `aspect_ratio`，支持更多比例，例如 `1:1`、`5:4`、`9:16`、`21:9`、`16:9`、`3:2`、`4:3`、`4:5`、`3:4`、`2:3`。
- `image2` 使用 OpenAI 兼容的 `size`，例如 `1024x1024`、`1024x1792`。
- `gpt-image-2` 与 `image2` 不是同一路线：前者是 `/v1/videos` 异步任务，后者是 `/v1/images/*` OpenAI 兼容接口。

## 失效接口处理

Apifox 明确标在 `失效接口` 分类的页面只用于历史排查，不要作为新接入默认：

| 失效页面 | 原用途 | 不再使用原因 |
|---|---|---|
| 旧 Sora 视频接口 | `sora-2-landscape-10s`、`sora-2-portrait-15s` 等旧模型 | 新 Sora 文档统一为 `sora-2-12s`，字段也从旧 `image_url` 迁移到 `images[]` / `input_reference` |
| 旧 Nano Banana Gemini 原生格式 | `nano_banana_2-landscape` 等路径模型 | 已被 Apifox 标为失效；当前 Banana 图片应走新 Gemini 原生或 `/v1/videos` 异步路线 |
| 旧 Veo 直出 15s | `veo_3_1-fast-remix` 等 `*-remix` 模型 | 15s 新路线是先生成 Veo，再用 `veo_3_1-fast-extend` 延长 |

## ShanHaiEdu 当前接入状态

### 已接入

- 后端真实视频 provider：`OctoVideoProvider`
- 提交：`POST {OCTO_BASE_URL}/v1/videos`
- 查询：`GET {OCTO_BASE_URL}/v1/videos/{task_id}`
- 下载：完成后从 URL 下载真实 clip 到 `clips/{shot_id}.mp4`
- 多镜头：所有 clip 完成下载后才尝试用 `ffmpeg` 合成 `outputs/final_video.mp4`
- 演示兜底：`VIDEO_PROVIDER_MODE=placeholder` 只生成 placeholder MP4，不能当生产视频

### 已知实现缺口

- 当前后端真实视频提交主要覆盖 JSON `model/prompt/size`；尚未完整实现 multipart `input_reference`。
- 当前 storyboard 的 `reference_image_ids` 还没有完整转换为章鱼哥可访问的 `images[]` 公网 URL。
- URL 字段解析需要持续保持宽松兼容，至少覆盖 `data.video_url`、`video_url`、`url`、`result_url`、`data.url`、`data.result_url`、`data.first_video_url`、`result.video_url`、`result.url`。
- MiniMax 官方视频 `/v1/video_generation`、`file_id` 下载路线不是当前后端真实视频 provider；不要把它和章鱼哥 `/v1/videos` 混用。

## 历史卡点与排查规则

### T047 阻塞

现象：`PROVIDER_MODE=real` 同时控制文本 provider 和视频 provider，导致 `final_video/generate` 误触发真实 Octo，返回 `502 / OCTO_REQUEST_FAILED / HTTP 503`，且当时 `tasks=0`、`final_video=not_started`，缺少诊断材料。

处理结果：

- 已拆分 `PROVIDER_MODE` 和 `VIDEO_PROVIDER_MODE`。
- `PROVIDER_MODE=real` 只代表真实文本 provider。
- `VIDEO_PROVIDER_MODE=placeholder` 用于演示兜底。
- `VIDEO_PROVIDER_MODE=real` 才启用真实章鱼哥视频 provider。

### 真实 Omni smoke 卡点

已执行过一次真实 `omni_flash-10s` 单镜头 smoke，结论：

- 真实提交成功，任务进入 `queued -> processing -> completed`。
- 查询结果包含 `video_url`。
- 后端旧下载流程失败为 `HTTP 403`。
- 同一 `video_url` 手动不带 `Referer` 下载成功，本地 MP4 大小约 2.5 MB。
- 复盘根因是 OSS 文件域对 `Referer: https://otuapi.com/` 不兼容；下载时不要强行加 `Referer`。

### 任务路线混用

章鱼哥 `/v1/videos`：

```powershell
.\scripts\videogen.ps1 newapi-query --task-id "<task_id>"
.\scripts\videogen.ps1 newapi-download --task-id "<task_id>" --out ".\output.mp4"
```

MiniMax 官方视频：

```powershell
.\scripts\videogen.ps1 query --task-id "<task_id>"
.\scripts\videogen.ps1 download --file-id "<file_id>" --out ".\output.mp4"
```

判断标准：

- 如果提交接口是 `POST /v1/videos`，后续就用 `GET /v1/videos/{task_id}` 和 URL 下载。
- 如果提交接口是 MiniMax 官方 `/v1/video_generation`，才可能走 `file_id` 下载。

### 常见失败分类

| 现象 | 优先判断 |
|---|---|
| `HTTP 401` | token 缺失或错误；不要打印 token，只记录状态和脱敏摘要 |
| `token has no access to model` | 账号没有对应模型权限，不是下载问题 |
| `HTTP 503` | 上游服务不可用、模型不可用、网关错误或请求不合规；保存脱敏响应摘要 |
| 查询 `/v1/videos/{task_id}/result` 返回 404 | 查错接口，正确路径是 `/v1/videos/{task_id}` |
| `completed` 但没有 URL | 检查原始 query JSON，补充字段兼容 |
| 下载 403 | 检查下载头和 URL 时效；不要给 OSS URL 强加 `Referer` |
| 只保存 queued manifest | 轮询未完成；继续查询到 `completed` 或 `failed` |

## 推荐复测命令

查看章鱼哥模型矩阵：

```powershell
.\scripts\videogen.ps1 otu-models
```

提交 Omni dry run：

```powershell
.\scripts\videogen.ps1 newapi-create --model omni_flash-10s --prompt "A non-realistic classroom story hook. [Static shot]" --size 1280x720 --dry-run
```

真实单镜头 smoke：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-octo-real-video.ps1 -ApiBaseUrl http://127.0.0.1:8000
```

前置环境：

```powershell
$env:PROVIDER_MODE = "real"
$env:VIDEO_PROVIDER_MODE = "real"
$env:OCTO_API_KEY = "<redacted>"
$env:OCTO_BASE_URL = "https://otuapi.com"
uvicorn apps.api.app.main:app --reload --port 8000
```

通过标准：

- `final_video/generate` 创建本地 task。
- task 返回 `provider_task_id`。
- `GET /projects/{project_id}/tasks/{task_id}` 能推进状态。
- 完成后 `download_path=clips/{shot_id}.mp4`。
- 本地 clip 文件不是 48 bytes placeholder。
- 任何失败都能在 task 里看到 `error_code`、`error_message`、`http_status`、`retryable` 或脱敏响应摘要。

## 后续接入建议

1. 真实生产视频继续以 `omni_flash-10s` 为默认模型，先稳定单镜头，再扩展多镜头。
2. 补齐 multipart `input_reference`，让本地审核通过的首帧图可以进入真实视频 provider。
3. 把 `reference_image_ids` 映射为后端可访问的公网或内网可下载 URL，再传给章鱼哥 `images[]`。
4. 保持 task 持久化和错误可观测，不允许再出现真实 submit 失败后 `tasks=0` 的黑盒状态。
5. 真实模式下 `outputs/final_video.mp4` 只能来自真实 clip 合成；placeholder 只用于演示，不混入生产结果。
