# Google Flow 核心视频工作台验收记录

> 日期：2026-06-29 03:07:13 +08:00
> 分支：`feat/google-flow-core-video-workbench`
> 范围：项目级视频工作台 Task 11 全量验证
> 说明：本报告只记录脱敏证据；不包含第三方 key、Bearer token、完整 header、上游结果 URL 或个人凭据路径。

## 自动化门禁

| 检查项 | 命令 | 结果 |
|---|---|---|
| 后端全量回归 | `python -m pytest apps/api/tests -q` | 通过：271 passed, 2 xfailed |
| 前端契约测试 | `bun run test:contracts` | 通过 |
| TypeScript | `bunx tsc --noEmit` | 通过 |
| ESLint | `bun run lint` | 通过 |
| Next production build | `bun run build` | 通过 |
| Playwright 视频工作台 E2E | `NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1` | 通过：1 passed |
| Playwright 视频工作台连续稳定性 | `NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1 --repeat-each=10` | 通过：10 passed |
| 客户端密钥扫描 | `bun run scan:client-secrets` | 通过：Client-visible secret scan passed |

## 真实 Omni Smoke 状态

已执行一次真实 provider smoke，使用山海后端项目级 `/projects/{project_id}/video-workflow/*` 接口，不直接请求第三方 provider。

| 字段 | 结果 |
|---|---|
| 模型 | `omni_flash-10s` |
| 尺寸 | `1280x720` |
| 时长 | 10 秒 |
| 参考图数量 | 2 |
| run_id | `task_c8a5235778ba` |
| 终态 | `completed` |
| progress | 100 |
| download_status | `downloaded` |
| video_ready | true |
| 本地 MP4 大小 | 2,664,611 bytes |

本次 smoke 创建了一个真实上游视频任务。报告不记录第三方 key、Bearer token、完整 header、provider task id、上游下载 URL 或本地绝对文件路径。

## 13 项验收清单

| # | 验收项 | 证据 | 状态 |
|---:|---|---|---|
| 1 | 项目工作区上传、预览、选择、排序和移除图片 | 后端 asset/delete/content 测试；前端 `VideoAssetPanel`；E2E 上传 3 张图 | 通过 |
| 2 | 单次最多 7 张，顺序与上游请求一致 | `test_real_providers.py` multipart 顺序/MIME；前端选择工具测试 | 通过 |
| 3 | 文生视频和多参考图视频均能真实提交 | 后端 text/reference payload 契约通过；真实 Omni 图生视频 smoke completed | 通过 |
| 4 | 页面自动显示状态和进度，不需要手动同步 | polling hook 契约；E2E queued/processing/completed 流程 | 通过 |
| 5 | 完成视频能够页面内播放并下载 | content/download 路由测试；E2E `video` 可见；真实 smoke MP4 downloaded | 通过 |
| 6 | 任务历史至少最近 50 条 | latest_fifty_runs 后端测试 | 通过 |
| 7 | 失败任务具有错误、重试入口和审计关系 | retry/sync 测试；历史面板重试入口契约 | 通过 |
| 8 | 历史任务可以恢复提示词和参考图组合 | E2E 点击“复用参数”恢复 prompt；复用工具测试 | 通过 |
| 9 | 刷新、关闭浏览器、服务重启后任务不丢失 | SQLite task/manifest 持久化测试；E2E reload 后仍有视频 | 通过 |
| 10 | 相同 `client_request_id` 不会创建两次上游任务 | 后端 idempotency 测试 | 通过 |
| 11 | 所有自动化测试通过 | 见自动化门禁 | 通过 |
| 12 | 至少一次受控真实 Omni API 烟测 | 真实 smoke run `task_c8a5235778ba` completed 且 `video_ready=true` | 通过 |
| 13 | 连续执行 10 次完整流程无串数据、素材丢失、任务覆盖或错误状态倒退 | Playwright 视频工作台完整流程 `--repeat-each=10` 连续通过；自动化覆盖项目隔离、幂等和历史 | 通过 |

## 当前剩余风险

- 真实 smoke 已证明项目级 Omni 图生视频闭环可完成并下载 MP4；连续稳定性由 fake-provider E2E 10 次重复通过证明，未额外执行 10 次真实付费 smoke。
- E2E 使用 fake provider，验证浏览器交互闭环；真实 smoke 负责证明 provider 链路。
- 教材 PDF fixture 是 `.gitignore` 忽略的大文件；本地全量 pytest 依赖该 fixture，验证时从主工作区临时复制，未纳入提交。