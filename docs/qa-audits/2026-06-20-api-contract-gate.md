# ShanHaiEdu API 契约测试门禁记录

- 日期：2026-06-20
- 角色：测试工程师
- 目标：建立真实前后端联调的基础测试门禁
- 范围：后端现有 API、最小链路、红线测试、前端 smoke checklist

## 测试用例清单

### 后端 API 契约测试

| 编号 | 用例 | 自动化状态 | 文件 |
|---|---|---|---|
| API-CONTRACT-001 | 成功响应统一返回 `{ ok: true, data }` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| API-CONTRACT-002 | 错误响应统一返回 `{ ok: false, error: { code, message, retryable } }` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| API-CONTRACT-003 | 创建项目缺必填字段时返回 422 / `REQUEST_VALIDATION_FAILED`，并在 `details` 中标出缺失字段 | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |

### 最小链路测试

| 编号 | 用例 | 自动化状态 | 文件 |
|---|---|---|---|
| FLOW-001 | 创建项目后 manifest 中 `textbook_parse` 与 `lesson_plan` 初始为 `not_started` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| FLOW-002 | 上传教材后返回上传资产路径与状态 | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| FLOW-003 | 生成 `textbook_parse` 后状态变为 `needs_review` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| FLOW-004 | approve `textbook_parse` 后状态变为 `approved` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| FLOW-005 | 生成 `lesson_plan` 后状态变为 `needs_review` | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |
| FLOW-006 | 每一步后查询 manifest 验证状态变化 | 已覆盖 | `apps\api\tests\test_api_contract_gate.py` |

### 红线测试

| 编号 | 红线 | 自动化状态 | 当前结果 |
|---|---|---|---|
| REDLINE-001 | 上游未 approve 时，下游 generate 必须失败 | 已覆盖 | 通过 |
| REDLINE-002 | schema 缺必填字段时，后端必须拒绝 | 已覆盖，标记 `xfail(strict=True)` | 当前失败：后端返回 200 并写入版本 |
| REDLINE-003 | 无权限请求不能写项目 | 已覆盖，标记 `xfail(strict=True)` | 当前失败：后端返回 200 并创建项目 |

## 自动化测试代码

新增文件：

- `apps\api\tests\test_api_contract_gate.py`

关键测试：

- `test_api_success_and_error_responses_use_stable_envelope`
- `test_minimal_frontend_backend_flow_updates_manifest_states`
- `test_downstream_generate_fails_when_upstream_is_not_approved`
- `test_project_create_rejects_missing_required_fields`
- `test_provider_schema_validation_rejects_missing_required_fields`
- `test_unauthorized_request_cannot_create_project`

说明：

- 常规门禁允许当前已知 P0 / P1 红线以 `xfail(strict=True)` 形式存在，保证测试套件可重复运行。
- 严格红线门禁使用 `--runxfail`，会把当前 P0 / P1 红线暴露为真实失败。
- 后续后端修复后，移除对应 `xfail` 标记，严格门禁应转为全绿。

## 测试运行命令

常规 API 门禁：

```powershell
python -m pytest apps\api\tests\test_api_contract_gate.py -q
```

全量后端测试：

```powershell
python -m pytest apps\api\tests -q
```

严格红线门禁：

```powershell
python -m pytest apps\api\tests\test_api_contract_gate.py --runxfail -q
```

预期：

- 当前常规 API 门禁应为 `4 passed, 2 xfailed`。
- 当前严格红线门禁应暴露 2 个失败。
- 后端修复 P0 / P1 后，严格红线门禁应全部通过。

## 缺陷分级报告

### P0：无权限请求可以写项目

- 分类：权限 / 后端 / API
- 测试：`test_unauthorized_request_cannot_create_project`
- 当前状态：`xfail(strict=True)`
- 复现步骤：
  1. 不携带任何认证信息。
  2. 请求 `POST /projects`。
  3. 当前后端返回 200，并创建项目。
- 影响：
  - 任意请求方可写入项目数据。
  - 接入真实 provider 后可能造成费用消耗和数据污染。
- 标准修复：
  - 为写接口增加认证依赖。
  - 未认证返回 401，越权返回 403。
  - 项目、节点、任务、资产接口做 owner / role 校验。

### P1：provider 输出缺 schema 必填字段时未拒绝

- 分类：数据契约 / 后端 / API
- 测试：`test_provider_schema_validation_rejects_missing_required_fields`
- 当前状态：`xfail(strict=True)`
- 复现步骤：
  1. provider 返回缺少 `core_knowledge_points` 等必填字段的 `textbook_parse` 内容。
  2. 请求生成 `textbook_parse`。
  3. 当前后端 normalize 默认值后返回 200，并写入版本。
- 影响：
  - LLM 输出不完整时可能被默认值掩盖。
  - 下游教案和视频链路基于不完整数据继续生成。
- 标准修复：
  - provider 原始输出必须先按 schema 完整校验。
  - normalize 只能做字段别名兼容，不能替代必填字段验证。
  - 校验失败返回 400 / `GENERATION_INPUT_INVALID`，不写版本。

### 已通过红线：上游未 approve 时下游 generate 被阻断

- 分类：流程控制 / 后端 / API
- 测试：`test_downstream_generate_fails_when_upstream_is_not_approved`
- 当前状态：通过
- 验证结果：
  - `textbook_parse` 生成后未 approve。
  - 请求 `lesson_plan/generate` 返回 409 / `UPSTREAM_NOT_APPROVED`。

## 前端 Smoke Checklist

前端开发联调后，按以下 checklist 做最小冒烟：

### 环境

- [ ] 前端 API Base 指向本机 FastAPI，例如 `http://127.0.0.1:8000`。
- [ ] FastAPI `/health` 返回 `ok: true`。
- [ ] 配置页 `/video/capabilities` 能正常展示模型能力矩阵。
- [ ] 浏览器控制台无 error。

### 最小链路

- [ ] 在前端创建项目，网络面板出现 `POST /projects`，返回 `ok: true`。
- [ ] 上传 `.txt` 教材，网络面板出现 `POST /projects/{project_id}/textbook`，返回上传状态。
- [ ] 点击生成教材解析，网络面板出现 `POST /nodes/textbook_parse/generate`。
- [ ] 教材解析完成后，前端状态显示待确认。
- [ ] approve 教材解析，网络面板出现 `POST /nodes/textbook_parse/approve`。
- [ ] approve 后 manifest 或页面状态显示 `textbook_parse=approved`。
- [ ] 点击生成教案，网络面板出现 `POST /nodes/lesson_plan/generate`。
- [ ] 教案生成后，manifest 或页面状态显示 `lesson_plan=needs_review`。

### 红线

- [ ] 未 approve `textbook_parse` 时，前端无法成功生成 `lesson_plan`，并展示明确错误。
- [ ] API 返回 409 / `UPSTREAM_NOT_APPROVED` 时，前端不应把阶段显示为成功。
- [ ] 未登录或无权限状态下，前端不能调用写接口；若后端返回 401 / 403，应展示登录或权限提示。
- [ ] provider schema 错误返回 400 时，前端不应推进阶段。

### 基础交互

- [ ] 创建、上传、生成、approve 按钮在请求中有 loading / disabled 状态。
- [ ] 重复点击不会发起重复写请求，或后端返回幂等结果。
- [ ] 网络失败时有可读错误提示。
- [ ] 页面刷新后能从后端重新拉取项目和 manifest 状态。

## 当前测试缺口

- 尚未有真实前端 Playwright E2E。当前只提供前端 smoke checklist。
- 无权限请求测试目前只能标记为 P0 xfail，因为后端尚无鉴权实现。
- schema 缺必填字段测试目前标记为 P1 xfail，因为后端当前 normalize 掩盖了缺字段。
- 尚未覆盖上传文件类型/大小边界，本轮范围聚焦用户指定红线。
- 尚未覆盖并发生成幂等，本轮范围聚焦最小链路与指定红线。
