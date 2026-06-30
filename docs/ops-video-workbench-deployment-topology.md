# 视频工作台部署拓扑验证

> 范围：项目级 Google Flow 核心视频工作台。
> 日期：2026-06-29

## 推荐拓扑

浏览器只访问 Next.js Web 服务：

```text
Browser -> Next.js /api/backend/* -> FastAPI -> provider/storage
```

前端 `api-client` 固定使用 `/api/backend`。浏览器不读取 FastAPI 内网地址，不读取 provider token，也不直接访问 Octo/NewAPI。

## 代理要求

- `GET /projects/{project_id}/video-workflow`：读取配置、素材、任务历史。
- `POST /projects/{project_id}/video-workflow/assets`：multipart 上传参考图，Next 代理必须流式转发 request body。
- `DELETE /projects/{project_id}/video-workflow/assets/{asset_id}`：软删除参考图。
- `POST /projects/{project_id}/video-workflow/runs`：创建视频任务。
- `POST /projects/{project_id}/video-workflow/runs/{run_id}/sync`：手动排障同步。
- `GET /projects/{project_id}/video-workflow/observability`：读取当前项目的脱敏排障指标和事件。
- `GET /projects/{project_id}/video-workflow/runs/{run_id}/content`：播放器流式读取 MP4。
- `GET /projects/{project_id}/video-workflow/runs/{run_id}/download`：下载 MP4，保留响应头。

Next 代理必须由服务端注入 `BACKEND_API_TOKEN`，前端不得暴露该值。

## CORS 口径

推荐生产流量统一经 Next 代理，因此浏览器不需要跨域直连 FastAPI。

如果临时采用浏览器直连 FastAPI，必须单独验证：

- `CORS_ORIGINS` 包含实际 Web 域名。
- 允许方法包含 `GET`、`POST`、`PUT`、`PATCH`、`DELETE`。
- 允许请求头包含 `Authorization`、`Content-Type`。
- 文件上传、视频流和下载响应头在跨域场景下可用。

直连模式不作为本轮默认交付拓扑。

## 生产验收步骤

以下步骤是部署环境 E2E 的最小验收口径；staging 和正式发布前都应执行一次，证据只记录脱敏状态、HTTP 状态码和文件大小。

1. 打开正式 Web 域名，确认视频工作台入口来自项目工作区正式区域。
2. 浏览器 Network 中所有视频工作台 API 均命中 `/api/backend/...`。
3. 上传 1 张参考图，确认请求为 multipart 且返回素材 ID。
4. 删除参考图，确认 DELETE 经过 `/api/backend` 并返回软删除成功。
5. 创建 1 个 demo/fake 视频任务，确认轮询和同步请求经过 `/api/backend`。
6. 使用已完成的小型 MP4 fixture 验证播放器 `content` 和 `download` 都经代理返回。
7. 调用 `/api/backend/projects/{project_id}/video-workflow/observability`，确认只返回当前项目的脱敏 metrics/events。
8. 检查浏览器控制台和服务端日志，不出现 provider token、完整签名媒体地址或本地 storage 绝对路径。

## 回滚

- 代理异常时先回滚 Web 服务到上一版，不改 provider 配置。
- 如果 FastAPI 正常但 Web 代理异常，可临时停用视频工作台入口，保留历史任务和素材。
- 不建议切到浏览器直连 FastAPI 作为紧急回滚，除非完成 CORS 与密钥边界复核。
