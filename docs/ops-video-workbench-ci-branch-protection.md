# 视频工作台 CI 与分支保护

> 范围：`feat/google-flow-core-video-workbench` 合并门禁。
> 日期：2026-06-29

## GitHub Actions

工作流文件：`.github/workflows/video-workbench-delivery.yml`

必跑门禁：

- API：`test_video_workflow_canvas.py`、`test_api_contract_gate.py`。
- 前端契约：视频工作台、轮询控制、API 代理。
- 类型检查：`bunx tsc --noEmit --incremental false`。
- 代码检查：`bun run lint`。
- 生产构建：`bun run build`。
- 浏览器验收：`e2e/video-workbench.spec.ts`，从正式入口执行。
- 安全：前端 secret scan、仓库 secret pattern scan、依赖审计 critical 门禁。
- 启动冒烟：`python apps/api/scripts/ci_startup_smoke.py`，验证 `/health`、`/readiness`、临时 storage 写入和项目级视频工作台默认配置。

真实 provider smoke 不在普通 PR 中执行，避免消耗真实额度；只在 staging 手工或计划任务执行，并提交脱敏报告。依赖审计口径见 `docs/ops-video-workbench-dependency-audit.md`。

## 分支保护建议

在 GitHub 仓库设置中对 `main` 启用：

- Require a pull request before merging。
- Require status checks to pass before merging。
- Required checks：
  - `API contract and concurrency tests`
  - `Web contracts, typecheck, lint and build`
  - `Playwright formal video workbench entry`
  - `Secret and dependency scan`
- Require branches to be up to date before merging。
- Block force pushes。
- Restrict who can dismiss reviews。

## 本地验收

提交前至少运行：

```powershell
python -m pytest apps/api/tests/test_video_workflow_canvas.py apps/api/tests/test_api_contract_gate.py -q
python apps/api/scripts/ci_startup_smoke.py
cd apps/web
bun src/lib/video-workbench-ci-contract.test.ts
bun src/lib/video-workflow-contract.test.ts
bunx tsc --noEmit --incremental false
bun run lint
```
