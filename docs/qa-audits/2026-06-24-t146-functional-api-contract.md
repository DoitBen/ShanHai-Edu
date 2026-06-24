# T146 后端 FastAPI 功能接口全量合同回归

日期：2026-06-24
角色：测试工程师子智能体 A
范围：仅后端 FastAPI 功能接口
证据目录：`docs\qa-audits\t146-functional-api-evidence\20260624-153104`

## 结论

【通过，限定于 fake/placeholder + 本地 FastAPI 合同回归】。

本轮按 T146 调度要求执行后端目标批次与 `apps\api\tests` 全量批次，两个命令均 exit 0：

- 目标批次：`72 passed, 2 xfailed in 67.23s`
- 后端全量：`229 passed, 2 xfailed in 131.45s`

本结论只说明当前本地后端 FastAPI 合同、fake 文本 provider、placeholder 视频/图片/TTS 口径下未发现 P0/P1 阻塞。不代表真实 provider、生产 RBAC/JWT/session、多浏览器、容器冷启动、前端代理或浏览器用户态串联通过。

## 测试环境

- `PROVIDER_MODE=fake`
- `VIDEO_PROVIDER_MODE=placeholder`
- `IMAGE_PROVIDER_MODE=placeholder`
- `TTS_PROVIDER_MODE=placeholder`
- `STORAGE_ROOT=storage-t146-functional-api`
- 未读取、未打印真实密钥；未启动真实 provider；未修改 `apps\api` 业务源码。

## 执行命令与退出码

### 目标批次

```powershell
python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_api_contract_gate.py apps\api\tests\test_mvp_api.py apps\api\tests\test_textbook_pdf_parsing.py apps\api\tests\test_workspace_user_flow_contract.py apps\api\tests\test_ppt_runtime_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_flywheel_contract.py apps\api\tests\test_security_boundary.py apps\api\tests\test_control_plane_rules.py -q
```

- 退出码：0
- 输出摘要：`72 passed, 2 xfailed in 67.23s`
- 证据：`targeted-command.txt`、`targeted-pytest-output.txt`、`targeted-pytest-result.json`

### 后端全量

```powershell
python -m pytest apps\api\tests -q
```

- 退出码：0
- 输出摘要：`229 passed, 2 xfailed in 131.45s`
- 证据：`full-command.txt`、`full-pytest-output.txt`、`full-pytest-result.json`

## 覆盖接口面

已通过测试覆盖的接口/能力：

- 公共接口：`GET /health`、`GET /workflow`、`GET /video/capabilities`
- 鉴权与错误信封：配置 token 后的受保护接口、未授权响应、统一 `ok=false/error.code/message/retryable` 结构
- 项目接口：创建、列表、详情、更新、manifest、workspace、flywheel、feedback
- 教材挂载与教材解析：项目教材上传、教材库 fixture、教材库上传 job、知识点列表、知识点资产、PDF 切分、Markdown 抽取、资产确认
- 教案库：教案库列表、详情、从项目导入、项目引用教案后重生成
- 节点接口：`generate`、`edit`、`approve`、`retry`、节点详情、版本列表
- 状态/依赖门禁：上游未确认阻断、节点确认推进、StateEngine/manifest/workspace 用户态契约
- PPT 链路：`visual_contract`、`character_dict`、`ppt_assembly_plan`、`ppt_page_script`、`ppt_visual_asset`、`pptx_artifact`、兼容 `export/ppt` 与 PPTX 下载
- 视频/最终交付占位链路：fake/placeholder 下视频任务、`final_video`、`final_delivery` 相关后端合同
- 任务接口：项目任务列表、任务详情、任务重试
- 下载与资源边界：PPTX、final video、clip、image、project files、assets 查询及路径/后缀限制相关测试
- schema/rules：`GET /schemas/{schema_name}`、`GET /rules/coverage`
- admin rules/prompts：admin token 门禁、规则列表/详情/版本/激活/回滚/audit、workflow graph、prompt templates 版本接口
- 安全边界：前端源码不依赖 public API token、密钥式 client env 名称扫描、provider 摘要脱敏、`.env.example` 占位值约束

## 未覆盖 / 阻塞范围

本轮不覆盖：

- 真实文本、图片、视频、TTS provider 调用和真实服务响应质量。
- 生产 RBAC/JWT/session、多租户、行级权限。
- Next.js `/api/backend` live proxy、浏览器真实 API 串联、普通教师主界面红线扫描。
- Docker/compose 冷启动、持久卷、备份恢复、日志轮转、多实例并发。
- Edge/Firefox/移动端兼容与性能。

## 失败清单与缺陷分级

本轮没有命令失败，没有新增 P0/P1/P2 缺陷。

保留的 `2 xfailed` 属于已知待决策/待收口项，不是本轮新增失败：

| 等级 | 项 | 现状 | 影响 |
|---|---|---|---|
| 严重 / 已知 xfail | provider schema 缺必填字段严格拒绝 | `test_provider_schema_validation_rejects_missing_required_fields` 标记 strict xfail | 真实 provider 输出异常时仍需后端服务层继续收口，不能据此宣称真实 provider 合同完整通过 |
| 严重 / 架构待定 xfail | 未配置 `BACKEND_API_TOKEN` 时本地默认开放 | `test_unauthorized_request_cannot_create_project` 标记 strict xfail | 仅适用于本地联调默认口径；生产权限不可用此结论放行 |

## 证据文件

- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\evidence-dir.txt`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\targeted-command.txt`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\targeted-pytest-output.txt`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\targeted-pytest-result.json`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\full-command.txt`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\full-pytest-output.txt`
- `docs\qa-audits\t146-functional-api-evidence\20260624-153104\full-pytest-result.json`

## 回收建议

- T146 可作为后端 FastAPI 本地合同通过证据回收。
- T147/T148 需要分别以自己的报告和证据判断；T146 不替代前端代理、浏览器串联和用户态红线验收。
- 架构师回收 T146-T148 时，应继续把两个 strict xfail 保留为生产化前风险：真实 provider schema 严格拒绝、生产默认鉴权策略。
