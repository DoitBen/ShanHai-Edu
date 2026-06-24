# T145 v1 最小封板门禁回归报告

## 结论

测试验收通过；建议进入主 Codex / 系统架构师阶段复核。

本结论只覆盖 T142 定义的本地最小封板门禁：fake/placeholder API 主链路、真实 API 浏览器用户态、7 步导航、普通区红线、PPTX 下载代理、防误提交静态检查和本地/内测权限默认策略。它不代表真实 provider、真实视频质量、生产权限、多浏览器或容器冷启动通过。

## 环境

- API：`http://127.0.0.1:8145`
- Web：`http://127.0.0.1:3145`
- Storage：`storage-t145-v1-minimum-gate-regression`
- Provider：fake 文本 provider
- Image / Video / TTS：placeholder 路线
- 测试用户：`qa-t145`
- 目标项目：`proj_d62361b7e98c`
- 证据目录：`docs\qa-audits\t145-v1-minimum-gate-regression-evidence\20260624-115521`

## 命令验证

| 类型 | 命令 | 结果 |
|---|---|---|
| 后端目标测试 | `python -m pytest apps/api/tests/test_workspace_user_flow_contract.py apps/api/tests/test_security_boundary.py apps/api/tests/test_api_contract.py::test_real_text_provider_with_placeholder_video_mode_does_not_initialize_octo -q` | `14 passed` |
| 前端用户态契约 | `bun src/lib/workspace-user-flow-contract.test.ts` | exit 0 |
| 主控补充后端回归 | `python -m pytest apps\api\tests\test_workspace_user_flow_contract.py apps\api\tests\test_ppt_runtime_contract.py apps\api\tests\test_video_demo_contract.py -q` | `26 passed` |
| 主控补充前端类型检查 | `bunx tsc --noEmit --pretty false` | exit 0 |

## API 主链路

初次 API 主链路跑到 PPT / 视频分支时失败，原因是 `visual_contract` 和 `character_dict` 等上游节点尚未生成并确认，后端按 StateEngine 依赖门禁返回 `UPSTREAM_NOT_APPROVED`。该失败属于测试准备顺序问题，不是业务契约回归。

补跑后主链路通过：

- `visual_contract`、`character_dict`、`ppt_page_script`、`ppt_visual_asset`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均生成到 `needs_review` 并确认到 `approved`。
- `pptx_artifact` 生成到 `needs_review`，并产出可下载 PPTX。
- `final_video` 生成到 `needs_review`，placeholder 路线可进入待确认态。

证据文件：

- `api-main-chain-results.json`
- `api-main-chain-results-after-fix.json`
- `manifest-after-fix.json`
- `workspace-user-flow-api-after-fix.json`

## 浏览器用户态

最终浏览器证据使用目标项目 `proj_d62361b7e98c`，不是同名旧项目 `proj_66bbbd7002ca`。

验证结果：

- 当前阶段：`PPT 草稿`
- 下一步动作：`继续处理「PPT 装配」`
- 7 步导航存在。
- PPT 草稿展示 4 个子门禁：PPT 总装方案、PPT 页面脚本、PPT 视觉资产、PPT 装配。
- “开发诊断”默认折叠。
- 开发诊断之前普通区红线扫描为空：`mainHitsBeforeDeveloperDiagnostics=[]`。
- 开发诊断之前路径泄漏扫描为空：`pathLeakHitsBeforeDeveloperDiagnostics=[]`。
- 页面可见正文无红线命中：`visibleHitsInBody=[]`。
- PPTX 下载按钮存在。
- PPTX 下载链接走后端代理：`/api/backend/projects/proj_d62361b7e98c/exports/T145最小封板回归-pptx-artifact.pptx`。
- 浏览器 console error/warn 为空。

证据文件：

- `browser-workspace-target-final-dom-redline-scan.json`
- `browser-workspace-target-final-viewport.png`
- `browser-console-target-final.json`

## 防误提交与权限默认策略

静态检查结果只用于本地/内测门禁，不扩大解释为生产安全通过：

- `.gitignore` 覆盖 `apps/api/.env.example` 之外的本地 `.env`、storage、日志、SQLite、真实 provider 产物等运行时文件。
- Web 代理会删除 `expect` header；配置 `BACKEND_API_TOKEN` 时才注入后端 `Authorization`，未配置时不转发浏览器 Authorization。
- 后端 `require_api_token()` 在未配置 `BACKEND_API_TOKEN` 时允许本地/内测联调；配置 token 后要求 Bearer token。
- 源码红线扫描仍可在开发诊断、demo 模式或源码内部命中工程词；本轮通过依据是浏览器普通区分区扫描为空。

证据文件：

- `static-git-ignore-check.txt`
- `static-config-security-files.txt`
- `static-redline-source-scan.txt`

## 剩余风险

- 真实文本、图片、视频、TTS provider 未在本轮作为主流程门禁执行。
- placeholder 视频不代表真实成片质量、配音质量、数学画面准确性或合规素材质量。
- 本轮只覆盖 Chromium/in-app browser，不代表多浏览器通过。
- 本地/内测权限默认策略不等于生产 RBAC/JWT/session 通过。
- 未覆盖容器冷启动、持久卷、备份恢复、日志轮转和并发多实例。
- 测试过程中存在两个同名 T145 项目，后续复跑必须明确目标项目 ID，避免误用旧项目状态。

## 验收建议

T145 测试验收通过。建议由主 Codex / 系统架构师对照 T142、T143、T144、本报告和关键 diff 做阶段复核；若复核通过，可声明“v1 最小封板门禁有条件通过”，但封板范围必须限定在 fake/placeholder + 浏览器用户态 + 红线 + 下载代理这一本地门禁内。
