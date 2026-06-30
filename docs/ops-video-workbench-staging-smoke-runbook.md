# 视频工作台 Staging Smoke Runbook

> 范围：项目级 Google Flow 核心视频工作台。  
> 目标：在 staging 或发布候选环境证明正式入口、Next 代理、生成任务、播放下载、观测和存储清理可工作。

## 执行前检查

- Web 入口必须通过 Next.js 暴露，视频工作台请求统一走 `/api/backend`。
- FastAPI 后端只在服务端持有 provider token，浏览器不得读取真实密钥。
- staging 若只做 fake/demo 验收，不需要真实 provider 密钥。
- 真实 Omni smoke 必须显式加 `--run-real-provider`，避免默认消耗真实额度。
- 报告输出到 `docs/qa-audits`，不记录 token、鉴权头、provider task id、签名 URL 或个人密钥路径。

## 本地自校验

从仓库根目录执行：

```powershell
python apps/api/scripts/video_workbench_staging_smoke.py --env-name local-fake
```

该模式使用 FastAPI TestClient 和内置 fake 视频 provider，覆盖：

- 创建项目并读取 `/projects/{project_id}/video-workflow`
- 上传、删除、再次上传参考图
- Omni 文生视频 smoke：`OMNI_TEXT_TO_VIDEO`
- Omni 图生视频 smoke：`OMNI_REFERENCE_TO_VIDEO`
- `content` 与 `download` 返回非空 MP4
- `observability` 返回脱敏指标
- `storage` 与 `storage/cleanup` 返回用量和策略结构

## Staging fake/demo 验收

将 `--base-url` 指向 Next 代理后的 API 根路径：

```powershell
python apps/api/scripts/video_workbench_staging_smoke.py `
  --env-name staging-fake `
  --base-url https://staging.example.com/api/backend `
  --token $env:BACKEND_API_TOKEN
```

验收要求：

- 脚本记录的 HTTP URL 必须包含 `/api/backend`。
- 上传和删除参考图均成功。
- 视频任务可创建、同步、播放、下载。
- 浏览器或 HTTP 层不得直连 FastAPI 内网地址或 provider 域名。

## 真实 Provider Smoke

只在确认 staging 后端已经配置真实 Omni provider、额度和模型权限后执行：

```powershell
python apps/api/scripts/video_workbench_staging_smoke.py `
  --env-name staging-real-omni `
  --base-url https://staging.example.com/api/backend `
  --token $env:BACKEND_API_TOKEN `
  --run-real-provider `
  --max-sync-attempts 60
```

通过标准：

- 文生视频完成并下载 MP4。
- 图生视频使用至少 2 张参考图完成并下载 MP4。
- 下载文件非空，Content-Type 包含 `video/mp4`，文件头包含 MP4 `ftyp`。
- 失败时报告只记录脱敏错误摘要；provider 不可用时标记阻塞，不伪造成功。

## 证据位置

脚本会生成两份证据：

- `docs/qa-audits/<timestamp>-<env>-video-workbench-staging-smoke.json`
- `docs/qa-audits/<timestamp>-<env>-video-workbench-staging-smoke.md`

提交前必须人工检查报告，不得包含：

- token、鉴权头、API key、secret
- provider task id
- 完整签名媒体 URL
- 本地绝对密钥路径

## 失败处理

- 401/403：先检查 Next 代理是否注入后端 token，再检查后端 protected 依赖。
- 404：确认 `--base-url` 是否已经包含 `/api/backend`。
- 上传失败：检查 multipart 代理、文件大小限制和图片解码错误。
- 生成失败：检查 provider readiness，真实 provider 不可用时记录阻塞。
- 播放或下载失败：检查 `content`/`download` 是否经代理返回 MP4。
- `storage/cleanup` 失败：检查项目 storage 权限和 SQLite 可写状态。
