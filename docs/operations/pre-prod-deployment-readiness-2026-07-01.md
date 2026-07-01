# 生产上线前安全部署准备清单 - 2026-07-01

本文档只用于把当前 `main` 从“本地真实 provider smoke 通过”推进到“可准备生产部署验收”。本文档不授权直接上线、不启动生产环境、不调用真实 provider、不进入 Phase F。

## 1. 当前主线收尾状态

| 项目 | 状态 |
| --- | --- |
| PR #39 | 已合并 |
| 合并方式 | Squash Merge |
| main 最新 SHA | `b794218157e95411583ceb019aecdf71206ff6a1` |
| PR #39 原分支 | `codex/media-workbench-provider-minimal` 已删除 |
| PR #38 | CLOSED，废弃，不再作为合并对象 |
| 本地真实 provider 验收环境 | 已停止 |
| Phase F | 未启动 |
| 生产环境 | 未启动 |

## 2. 本轮已通过范围

- 生图 provider 配置读取修复：后端 settings 可读取 `IMAGEGEN_FREE_*`。
- 图片 provider 网络/超时错误中文化：不再把底层英文连接错误直接展示给用户。
- 参考篮有图时视频按 `reference` mode 提交：前端提交 payload 与 UI 选择一致。
- PR #39 分支最小真实 smoke 已通过：
  - 生图：PASS。
  - 文生视频：PASS。
  - 参考图视频：PASS。
- Smoke 环境为本地 API-mode，非生产环境。

## 3. 本轮不代表

- 不代表生产上线通过。
- 不代表 HTTPS Cookie Secure 通过。
- 不代表生产备份、回滚、监控通过。
- 不代表多浏览器通过。
- 不代表压测通过。
- 不代表 #38 中 auth/session/admin proxy/RBAC 改动通过。
- 不代表 Phase F 可以启动。

## 4. 生产部署前配置核验清单

### API 环境变量

- [ ] `PROVIDER_MODE` 明确为预期值。
- [ ] `VIDEO_PROVIDER_MODE` 明确为预期值。
- [ ] `IMAGE_PROVIDER_MODE` 明确为预期值。
- [ ] `TTS_PROVIDER_MODE` 明确为预期值；未启用时必须清楚标记为 placeholder 或 disabled。
- [ ] 文本 provider 相关 key/base/model 已配置在生产密钥系统或生产 `.env`，不得入仓。
- [ ] 图片 provider 相关 key/base/model 已配置在生产密钥系统或生产 `.env`，不得入仓。
- [ ] 视频 provider 相关 key/base/model 已配置在生产密钥系统或生产 `.env`，不得入仓。
- [ ] `STORAGE_ROOT` 指向生产持久化目录。
- [ ] `WORKFLOW_ROOT` 指向发布包内预期目录。
- [ ] `CAPABILITIES_PATH` 指向发布包内预期 capabilities 文件。
- [ ] 日志路径指向生产日志目录，确认可轮转、可清理。

### Web 环境变量

- [ ] `NEXT_PUBLIC_DEMO_MODE=false`。
- [ ] `BACKEND_API_BASE_URL` 指向生产 API 内网或反代地址。
- [ ] Web 运行端口与反代配置一致。
- [ ] 不在客户端公开 provider key、backend token、cookie、CSRF token。

### 后端 token 与代理

- [ ] `BACKEND_API_TOKEN` 已配置为生产专用强随机值。
- [ ] token 只存在于服务端环境，不进入浏览器、不进入文档、不进入日志。
- [ ] 如启用 Web 后端代理，确认代理只由服务端读取 token。

### CORS / Origin

- [ ] CORS origin 只包含生产 Web 域名。
- [ ] 不包含通配符生产配置。
- [ ] 本地开发 origin 不混入生产配置。

### Cookie / HTTPS / 反代

- [ ] 生产通过 HTTPS 访问。
- [ ] `AUTH_COOKIE_SECURE=true`。
- [ ] Cookie `HttpOnly`、`SameSite`、`Path` 符合预期。
- [ ] 反代保留必要的 `Host`、`X-Forwarded-Proto`、`X-Forwarded-For`。
- [ ] 反代请求体大小限制满足图片/视频参考素材上传需求。
- [ ] 反代超时满足视频 polling/download，但不无限等待。

### Storage / backup / rollback

- [ ] 生产 storage 路径存在且权限正确。
- [ ] 项目 DB、auth DB、媒体输出目录纳入备份。
- [ ] 备份路径与恢复路径已记录。
- [ ] 回滚到上一发布包的方法已记录。
- [ ] 回滚后 storage 与 DB 兼容性已评估。

## 5. 生产前验收清单

- [ ] 登录成功。
- [ ] `/auth/me` 刷新后可恢复会话。
- [ ] 缺少 CSRF 的 unsafe request 被拒绝。
- [ ] Teacher A 不能访问 Teacher B 项目。
- [ ] Teacher A 不能访问 Teacher B assets/runs/download/cleanup。
- [ ] 生图 smoke 通过。
- [ ] 文生视频 smoke 通过。
- [ ] 参考图视频 smoke 通过。
- [ ] completed output 可播放/下载。
- [ ] 日志不泄露 key/token/完整 URL/签名 URL/完整 provider 响应。
- [ ] readiness 仅显示脱敏配置状态。
- [ ] 失败 toast 为中文、可理解、可操作。

## 6. 风险清单

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| 真实 provider 成本 | 未接受 | 任何真实 smoke 都可能产生费用，必须由 Owner 明确批准。 |
| 本地 SQLite/storage 与生产差异 | 未接受 | 本地通过不等于生产存储可靠。 |
| Cookie Secure 依赖 HTTPS | 未接受 | 未经过 HTTPS 反代验收前不能视为生产安全通过。 |
| provider 签名 URL 脱敏 | 未接受 | 日志、文档、PR、截图都不得记录完整签名 URL。 |
| 备份恢复未演练 | 未接受 | 只配置备份不等于可恢复。 |
| 并发/压测未完成 | 未接受 | 最小 smoke 不覆盖并发、队列、资源耗尽。 |
| #38 安全基座改动未合入 | 已知 | #38 已废弃；如需 auth/session/RBAC 改动，必须另开安全 PR。 |

## 7. 下一步

下一步只能是 Owner 审阅 runbook 与本清单，确认生产部署准备口径。没有 Owner 明确批准，不得启动生产环境；没有 Owner 明确批准，不得调用真实 provider。
