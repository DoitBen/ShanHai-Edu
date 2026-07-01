# 生产 Dry-run 方案 - 2026-07-01

本文档用于把当前 `main` 从“生产上线前 runbook 已归档”推进到“可执行生产 dry-run”。本轮仍不是正式上线。

## 1. 目标边界

- 本轮是 production dry-run 准备，不是正式上线。
- 不切公网流量。
- 不调用真实 provider。
- 不迁移真实用户数据。
- 不进入 Phase F。
- 不修改业务代码。
- 不修改 CI、依赖、部署脚本或运行配置。
- 不覆盖生产环境变量、storage、数据库、日志配置。

## 2. 前置条件

| 条件 | 状态 |
| --- | --- |
| PR #39 已合并 | 已完成，真实 provider 本地 smoke 通过 |
| PR #40 已合并 | 已完成，生产上线前 runbook 已归档 |
| 当前 main SHA | `cefb1d6f5d59f81727bebb46196130ec2898690e` |
| 服务器访问权限 | 待 Owner 确认 |
| 部署路径 | 待 Owner 确认 |
| 备份路径 | 待 Owner 确认 |
| 回滚路径 | 待 Owner 确认 |
| dry-run API/Web 端口 | 待 Owner 确认 |
| provider key 存放方式 | 只允许存在于服务器环境变量或安全配置，不入仓 |

## 3. Dry-run 执行方案

1. 连接服务器。
2. 进入 dry-run 工作目录，不进入当前生产运行目录直接操作。
3. 拉取 `main`。
4. 核验 `main` SHA 必须等于 Owner 批准的目标 SHA。
5. 不覆盖生产 env。
6. 先备份当前部署目录、env、storage、日志配置。
7. 构建 Web。
8. 启动 API/Web 到隔离端口或隔离 compose project。
9. 只跑 `/health`、`/readiness`、`/api/backend/health`。
10. 不跑真实 provider smoke。
11. 不切换公网 nginx。
12. 不影响当前线上服务。
13. 记录 PASS/FAIL、时间、main SHA、端口、是否隔离。

## 4. 端口与隔离要求

- dry-run 必须使用隔离端口。
- 禁止占用当前生产端口。
- 禁止修改现有 nginx upstream。
- 禁止覆盖现有 storage。
- 禁止复用生产数据库写入路径，除非 Owner 明确批准且仅做只读检查。
- dry-run 日志必须写入隔离日志路径。
- dry-run Web 必须指向 dry-run API，不得指向当前生产 API。
- dry-run API 必须指向 dry-run storage 或只读验证路径，不得写入生产 storage。

## 5. 验收清单

- [ ] API `/health` 返回 200。
- [ ] Next `/api/backend/health` 返回 200。
- [ ] `/readiness` 显示真实 API mode。
- [ ] provider mode 可读，但未触发 live smoke。
- [ ] 登录页可打开。
- [ ] 不出现 demo/placeholder 误导文案。
- [ ] 日志不泄露 key、token、cookie、session、签名 URL。
- [ ] 端口隔离符合 Owner 确认的端口规划。
- [ ] 当前线上服务未受影响。
- [ ] 未切公网流量。
- [ ] 未调用真实 provider。
- [ ] 未迁移真实用户数据。

## 6. 回滚方案

如果 dry-run 失败或 Owner 要求停止：

1. 停止 dry-run API/Web 服务。
2. 删除 dry-run 临时容器或进程。
3. 保留部署目录、env、storage、日志配置备份。
4. 因不改生产 nginx，正常情况下无需流量回滚。
5. 如果误改配置，按备份恢复。
6. 回滚后检查线上 `/health`。
7. 记录失败点、恢复动作和剩余风险。

## 7. Owner 确认点

执行 dry-run 前，Owner 必须逐项确认：

- [ ] 是否允许连接服务器。
- [ ] 是否允许读取生产 env 变量名但不展示值。
- [ ] 是否允许备份 storage。
- [ ] dry-run API 端口使用哪个。
- [ ] dry-run Web 端口使用哪个。
- [ ] 是否允许启动隔离 API/Web 服务。
- [ ] 是否允许后续正式上线。
- [ ] 是否允许真实 provider smoke。默认不允许。

## 8. 明确禁止项

- 不提交任何密钥。
- 不截图含 token、完整 URL、签名 URL 的页面。
- 不记录完整 provider URL。
- 不记录签名 URL。
- 不调用 provider。
- 不改 nginx。
- 不切公网。
- 不删生产数据。
- 不覆盖 env。
- 不覆盖 storage。
- 不使用生产数据库写入路径。
- 不启动 Phase F。
- 不修改业务代码。

## 9. 本 PR 之后的唯一下一步

Owner 审阅本文档并确认 dry-run 参数。没有 Owner 明确批准，不得连接服务器；没有 Owner 明确批准，不得启动隔离服务；没有 Owner 明确批准，不得调用真实 provider。
