# 生产部署 Runbook

本文档用于生产部署前审阅和演练准备，不代表已经批准上线。执行任何生产启动、真实 provider smoke、域名切流或数据迁移前，必须获得 Owner 明确确认。

## 1. 前置原则

- 只从已确认的 `main` SHA 部署。
- 生产密钥只来自生产环境变量或密钥系统，不写入仓库。
- 不在日志、截图、PR、文档中记录 key、token、cookie、CSRF token、完整 provider URL、签名 URL、完整上游响应。
- Phase F 功能不在本 runbook 范围内。
- auth/session/RBAC 如需改动，必须进入独立安全 PR。

## 2. 拉取 main

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git rev-parse HEAD
```

期望 SHA：由 Owner 在部署窗口确认。当前准备基线为：

```text
b794218157e95411583ceb019aecdf71206ff6a1
```

## 3. 配置核验

部署前核验以下配置，禁止把实际值粘贴到文档或聊天：

- API：
  - `PROVIDER_MODE`
  - `VIDEO_PROVIDER_MODE`
  - `IMAGE_PROVIDER_MODE`
  - `TTS_PROVIDER_MODE`
  - `BACKEND_API_TOKEN`
  - `CORS_ORIGINS`
  - `AUTH_COOKIE_SECURE`
  - `STORAGE_ROOT`
  - `WORKFLOW_ROOT`
  - `CAPABILITIES_PATH`
  - 日志目录
- Web：
  - `NEXT_PUBLIC_DEMO_MODE=false`
  - `BACKEND_API_BASE_URL`
  - Web 监听端口
- 反代：
  - HTTPS 证书有效。
  - 生产域名 origin 与 CORS 一致。
  - 上传大小限制、请求超时、下载超时符合媒体工作台需求。
- 备份：
  - auth DB 备份路径。
  - project DB 备份路径。
  - media storage 备份路径。
  - 回滚发布包路径。

## 4. 构建 Web

```powershell
cd apps\web
bun install --frozen-lockfile
bun run build
```

通过标准：

- build 退出码为 0。
- 不输出密钥或完整 provider 响应。
- `.next` 产物只作为构建产物，不提交入仓。

## 5. 启动 API

示例命令仅表达形态，实际生产进程管理应使用生产服务管理器：

```powershell
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port <API_PORT>
```

启动后检查：

```powershell
Invoke-WebRequest http://127.0.0.1:<API_PORT>/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:<API_PORT>/readiness -UseBasicParsing
```

通过标准：

- `/health` 返回 200。
- `/readiness` 只显示脱敏配置状态。
- provider mode 与部署计划一致。

## 6. 启动 Web

示例命令仅表达形态，实际生产进程管理应使用生产服务管理器：

```powershell
cd apps\web
set NEXT_PUBLIC_DEMO_MODE=false
set BACKEND_API_BASE_URL=<API_BASE_URL>
bun .next\standalone\server.js
```

启动后检查：

```powershell
Invoke-WebRequest https://<WEB_DOMAIN>/api/backend/health -UseBasicParsing
```

通过标准：

- Web 页面可访问。
- `/api/backend/health` 返回 200。
- 浏览器端不出现 provider key、backend token、cookie、CSRF token。

## 7. 最小 smoke

必须由 Owner 明确批准后执行，因为真实 provider 调用可能产生费用。

执行项：

- 登录。
- `/auth/me` 刷新后恢复会话。
- 缺少 CSRF 的 unsafe request 被拒绝。
- Teacher A 不能访问 Teacher B 项目。
- Teacher A 不能访问 Teacher B assets/runs/download/cleanup。
- 生图 1 次，确认 completed，可预览/下载。
- 文生视频 1 次，确认 completed，可播放/下载。
- 参考图视频 1 次，确认 reference mode，completed，可播放/下载。
- 检查日志不泄露 key/token/完整 URL/签名 URL/完整 provider 响应。

记录方式：

- 只记录 PASS/FAIL、时间、commit SHA、环境名。
- 不记录 key、cookie、session、CSRF token、完整 URL、签名 URL、完整上游响应。

## 8. 停止服务

按生产服务管理器停止 API/Web。停止后确认端口不再监听：

```powershell
Get-NetTCPConnection -LocalPort <API_PORT>,<WEB_PORT> -ErrorAction SilentlyContinue
```

## 9. 回滚

回滚前先确认：

- 当前发布包路径。
- 上一稳定发布包路径。
- 当前 DB/storage 备份已完成。
- 回滚是否涉及 DB schema 或 storage 格式不兼容。

回滚步骤：

1. 停止 Web。
2. 停止 API。
3. 切回上一稳定发布包或上一稳定 main SHA。
4. 恢复必要环境变量。
5. 如需要，恢复 DB/storage 备份。
6. 启动 API。
7. 启动 Web。
8. 检查 `/health`、`/readiness`、`/api/backend/health`。
9. 记录回滚结果与剩余风险。

## 10. 不允许事项

- 未经 Owner 确认直接上线。
- 未经 Owner 确认调用真实 provider。
- 把本地 smoke 当作生产验收。
- 把 #38 中 auth/session/admin proxy/RBAC 改动作为已通过内容。
- 在同一个 PR 混入 Phase F 功能开发。
