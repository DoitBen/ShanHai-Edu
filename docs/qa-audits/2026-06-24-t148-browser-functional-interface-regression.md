# T148 浏览器真实 API 功能接口串联回归

日期：2026-06-24
角色：测试工程师子智能体 C / 主 Codex 回收
范围：浏览器真实 API 串联、工作区用户态、资源下载代理、普通区红线和控制台
证据目录：`docs\qa-audits\t148-browser-functional-interface-evidence\20260624-153915`

## 结论

【不通过】。

接口层和下载代理层可以跑通：隔离 API/Web 环境下项目可创建、教材可挂载，PPT/视频链路可推进到 `final_video=approved`，浏览器中可生成 `final_delivery=needs_review`；PPTX、MP4、PDF、Markdown 直连 API 与 Next 代理下载均返回 200。

但浏览器教师主界面存在 P1 用户态红线和 P2 控制台错误，不能宣布“所有功能接口通过”：

- 普通教师主界面最终交付摘要暴露内部路径和工程文件名：`exports/final_delivery/...`、`delivery_manifest.json`、`gate_result.json`。
- 普通区命中工程红线词 `manifest`，DOM 扫描还记录 `visibleHitsInBody=["manifest","StateEngine"]`。
- 已完成步骤回看失效：点击 `PPT 草稿可回看` / `视频生成可回看` 后，主任务区仍显示 `最终交付`。
- 浏览器控制台出现 4 条 React duplicate key error：`Encountered two children with the same key ... 摘要 17`。

本结论只覆盖 fake/placeholder + 本地 API/Web + 浏览器真实 API 串联。不代表真实文本/图片/视频/TTS provider、生产权限、多浏览器、容器冷启动或真实 PPT/视频质量通过。

## 测试环境

- API：`http://127.0.0.1:8148`
- Web：`http://127.0.0.1:3148`
- Storage：`storage-t148-browser-functional-interfaces`
- Provider：`PROVIDER_MODE=fake`
- 视频/图片/TTS：`placeholder`
- 测试用户：`qa-t148`
- 项目：`proj_d53d88dd7ff6`
- 证据：`runtime-launch-params.json`、`server-launch-pids.json`、`listen-ports-after-launch.json`

本轮未读取、未打印真实密钥；未跑真实 provider；未修改业务代码。

## 已通过项

| 验收点 | 结果 | 证据 |
|---|---|---|
| API 健康检查 | 通过 | `api-health.json` |
| 创建项目与教材挂载 | 通过 | `api-create-project.json`、`api-attach-textbook.json` |
| PPT/视频链路 API 准备 | 通过 | `api-prep-summary.json`，`pptx_artifact/final_video=approved` |
| 已 approved 上游跳过策略 | 通过 | `api-prep-summary.json` 中 `visual_contract`、`character_dict` 为 `skip_already_approved` |
| 工作区进入最终交付步骤 | 通过 | `workspace-user-flow-api.json`，`workspace_current_step=final_delivery` |
| 浏览器登录与项目可见 | 通过 | `browser-after-login-state.json`、`browser-dashboard-snapshot.txt` |
| 浏览器触发最终交付生成 | 通过 | `browser-workspace-final-delivery-after-generate-state.json`、`api-get-final_delivery-after-browser.json` |
| API 直连下载 | 通过 | `api-download-checks.json`：PPTX、MP4、PDF、Markdown 均 200 |
| Next 代理下载 | 通过 | `next-proxy-download-checks.json`：PPTX、MP4、PDF、Markdown 均 200 |

## 失败项

### P1：最终交付普通区暴露内部路径和工程文件

复现路径：

1. 使用真实 API 模式登录 `qa-t148`。
2. 进入项目 `T148功能接口串联回归`。
3. 在最终交付步骤点击 `生成草稿`。
4. 查看普通教师主界面最终交付摘要。

实际结果：

- 普通区显示 `exports/final_delivery/lesson_plan.md`。
- 普通区显示 `exports/final_delivery/T148功能接口串联回归-pptx-artifact.pptx`。
- 普通区显示 `exports/final_delivery/final_video.mp4`。
- 普通区显示 `exports/final_delivery/delivery_manifest.json` 和 `exports/final_delivery/gate_result.json`。
- 普通区还显示 JSON 片段：`{"mode":"final","gate_passed":true,...}`。

证据：

- `browser-workspace-final-delivery-after-generate-state.json`
- `browser-workspace-target-final-dom-redline-scan.json`
- `browser-workspace-final-delivery-after-generate-state.png`

影响：

这违反 V0.6 普通教师主界面红线。李雪老师视角下，最终交付应该看到“教案、PPT、导入视频、检查清单是否已准备好”和下载/确认动作，而不是内部目录、manifest/gate 文件和 JSON 片段。

### P1：普通区红线扫描命中 `manifest`

证据文件 `browser-workspace-target-final-dom-redline-scan.json` 显示：

- `developerDiagnosticsDefaultCollapsed=true`
- `mainHitsBeforeDeveloperDiagnostics=["manifest"]`
- `pathLeakHitsBeforeDeveloperDiagnostics=["exports/final_delivery/","delivery_manifest.json","gate_result.json"]`
- `visibleHitsInBody=["manifest","StateEngine"]`

影响：

T148 不能通过浏览器用户态门禁；必须返工最终交付普通摘要生成和红线扫描。

### P1：已完成步骤回看失效

复现路径：

1. 在工作区最终交付阶段，点击 `PPT 草稿可回看`。
2. 再点击 `视频生成可回看`。

实际结果：

- 页面按钮已显示这些步骤“可回看”。
- 主任务卡仍显示 `最终交付`，没有切换到 PPT 草稿或视频生成的回看内容。

证据：

- `browser-workspace-ppt-draft-state.json`
- `browser-workspace-video-generation-state.json`
- `browser-workspace-after-ppt-click-fail-snapshot.txt`

推断原因：

从现象看，前端很可能在渲染选中步骤时优先使用 `workspace.current_step_id`，覆盖了用户点击的 completed step。该推断需要前端返工时结合 `ProjectWorkspaceScreen.tsx` 复核。

### P2：浏览器控制台 duplicate key error

证据文件 `browser-console-target-final.json` 显示 4 条 React error：

`Encountered two children with the same key ... 摘要 17`

影响：

当前不直接阻断接口串联，但说明最终交付摘要列表 key 生成不稳定，可能导致摘要项重复、遗漏或更新错乱。应与最终交付摘要红线一起修复。

## T147 live proxy 补充说明

T147 报告中 live proxy 未完成，原因是 Next dev lock 被占用。T148 在运行态补充了 4 类资源下载代理实测：

- PPTX：200，`application/vnd.openxmlformats-officedocument.presentationml.presentation`
- MP4：200，`video/mp4`
- PDF：200，`application/pdf`
- Markdown：200，`text/markdown; charset=utf-8`

这可以补充证明文件流下载代理在 T148 环境可用，但不完全替代 T147 原计划中的 GET/POST/PATCH/DELETE、admin 404、multipart header 等 live proxy 全项 smoke。

## 失败分级

| 级别 | 问题 | 影响 | 建议责任 |
|---|---|---|---|
| P1 严重 | 最终交付普通区暴露内部路径、manifest/gate 文件和 JSON 片段 | 违反普通教师主界面红线，阻塞功能接口全量通过判断 | 前端 |
| P1 严重 | 已完成步骤回看不生效 | 用户无法回看 PPT 草稿/视频生成等已完成步骤，影响工作区核心流程 | 前端 |
| P2 一般 | 最终交付摘要 duplicate key console error | 可能导致摘要项渲染错乱，需与摘要重构一起修 | 前端 |
| P2 一般 | T147 live proxy 全项仍未单独补齐 | T148 已覆盖二进制下载代理，但未覆盖所有代理方法和 admin smoke | 测试 |

## 回收建议

- T146 可判后端 FastAPI 本地合同通过。
- T147 可判前端代理/契约通过，但保留 live proxy 全项补测风险；T148 已补二进制下载代理实测。
- T148 判不通过，不能宣布“所有功能接口通过”。
- 新增 T149 前端返工：只修最终交付普通区红线、duplicate key、已完成步骤回看选择逻辑。
- 新增 T150 测试复测：只复跑 T149 失败点、T148 红线/console、下载代理；如 T149 触及更大工作区状态逻辑，再扩大回归面。
