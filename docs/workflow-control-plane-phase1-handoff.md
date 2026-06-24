# Workflow Control Plane Phase 1 交接文档

## 1. 本阶段目标

本阶段把原先“文件配置 + 代码硬编码规则”的质量门禁，升级为控制面数据库驱动的运行时规则治理。

一期只治理规则，不开放完整 DAG 修改：

- `workflow.yaml` 继续作为 DAG 只读蓝图。
- `workflow/rules/*.yaml` 作为 Git 基线和灾难恢复源。
- `storage/control_plane.db` 作为运行时规则真源。
- 新项目创建时绑定当前 active rule set。
- 旧项目默认不迁移，继续按创建时绑定版本执行。
- 管理员可通过规则控制面创建草稿、发布、回滚和查看审计。

## 2. 运行时架构

### 控制面数据库

新增全局数据库：

```text
storage/control_plane.db
```

核心表：

| 表 | 职责 |
|---|---|
| `rule_templates` | 规则模板元数据，如 rule_id、触发节点、触发事件 |
| `rule_versions` | 规则版本、状态、严重级别、启停、check_json、文案 |
| `rule_set_versions` | 一组 active 规则的快照 |
| `rule_release_channels` | 默认发布通道，当前指向 active rule set |
| `project_rule_binding` | 项目到 rule set 的 pinned 绑定 |
| `rule_audit_log` | seed、创建草稿、发布、回滚、rule set 激活审计 |

启动时从 `workflow/rules/index.yaml` 和各规则 YAML seed。若规则已有版本，不覆盖管理员修改。

### 项目绑定

`POST /projects` 成功后会调用控制面，把项目绑定到当前 active rule set：

```text
project_id
rule_set_version_id
binding_mode = pinned
created_at
```

后续管理员发布新规则只影响新项目。旧项目不自动迁移。

兼容控制面上线前已存在的旧项目：API 启动时会扫描 `storage/projects/*/project.db`，对尚未出现在 `project_rule_binding` 的项目补写当前 active rule set 绑定。该补写发生在管理员发布新规则前，因此避免旧项目在后续发布时被隐式迁移。

## 3. RuleExecutor V2

`RuleExecutor` 不再维护 `IMPLEMENTED_RULE_IDS`，也不再按 `R001/R004/...` 写规则 ID 分支。执行逻辑改为读取项目绑定 rule set，并解释 `check_json` 通用算子。

一期已支持算子：

```text
all
field_exists
field_equals
field_compare
enum_in
list_contains
list_min_length
list_each
nested_list_each
object_count_compare
path_under
text_not_contains
pptx_visible_text_not_contains
dependency_passable
```

已迁移为参数化规则的重点规则：

```text
R001 中文音频提醒
R004 角色禁真人
R005 候选不得伪装终版
R006 数学事实必须可编辑
R023 板书小结页
R024 页面类型多样性
R026 学生可见层不得暴露内部信息
R030 PPT 必须有视觉资产
```

`R010` 依赖检查在一期仍由 `StateEngine` 处理，控制面中以 `dependency_passable` 语义暴露。

## 4. 管理员 API

新增后端接口：

```text
GET    /admin/rules
GET    /admin/rules/{rule_id}
POST   /admin/rules/{rule_id}/versions
POST   /admin/rules/{rule_id}/activate
POST   /admin/rules/{rule_id}/rollback
GET    /admin/rules/audit
GET    /admin/workflow/graph
```

当前鉴权边界：

- 后端 admin API 仍依赖 `BACKEND_API_TOKEN` 保护。
- 普通请求无 token 或 token 错误时返回 404。
- 前端本地代理对 `/admin/*` 增加了本地演示级角色拦截。
- 生产级管理员 JWT、RBAC、服务端 session 尚未完成，不得按上线安全边界宣称。

## 5. 管理员 UI

新增规则控制面页面：

```text
apps/web/src/components/screens/AdminWorkflowScreen.tsx
```

已接入：

- 侧栏“规则控制面”入口。
- ScreenKey：`admin-workflow`。
- 快捷键：`G W`。
- 命令面板入口。
- 只读 DAG。
- 节点规则列表。
- 规则 JSON 表单编辑。
- 创建草稿版本。
- 发布、回滚。
- 审计日志。

一期不开放：

- 新增/删除节点。
- 修改节点依赖。
- 修改 schema。
- 修改状态机。
- 批量迁移旧项目。
- YAML 专家模式。

## 6. 验证证据

本阶段已执行并通过：

```powershell
python -m pytest apps/api/tests/test_control_plane_rules.py apps/api/tests/test_rule_executor_contract.py -q
```

结果：`23 passed`。

```powershell
python -m pytest apps/api/tests/test_control_plane_rules.py apps/api/tests/test_rule_executor_contract.py apps/api/tests/test_flywheel_contract.py apps/api/tests/test_ppt_runtime_contract.py -q
```

结果：`37 passed`。

```powershell
python -m pytest apps/api/tests -q
```

结果：`196 passed, 2 xfailed`。

```powershell
cd apps/web
bun src/lib/admin-rules-contract.test.ts
bun run lint
bun run build
```

结果：三项均通过。

## 7. 当前缺口

| 优先级 | 缺口 | 说明 |
|---|---|---|
| P0 | 生产级管理员鉴权未完成 | 当前是 API token + 本地 UI 角色拦截，不能替代 JWT/RBAC/session |
| P0 | 规则表达式缺 schema 校验 | `check_json` 由后端执行时识别，不合法 JSON 只在创建时做基础校验 |
| P1 | Prompt 控制面仍独立 | PromptRegistry 继续使用独立 DB，后续再合并到统一 Control Plane |
| P1 | 旧项目迁移未做 | 符合本阶段边界，后续如要迁移需另做评估和 dry-run |
| P1 | 完整 DAG 编辑未开放 | 本阶段按用户裁决不开放节点、依赖、schema、状态机修改 |

## 8. 下一阶段建议

下一阶段进入 StateEngine 深化，而不是直接扩大 DAG 编辑：

1. 把 generate/edit/approve/redo/skip 的状态流统一收敛到 StateEngine。
2. 将 `R010` 依赖检查从 RuleExecutor 旁路彻底归入 StateEngine。
3. 为项目绑定版本、规则执行结果、状态迁移日志建立统一审计视图。
4. 完成生产级 admin auth 后，再扩大规则控制面权限。

本阶段可以作为“规则治理 Phase 1 已落地”的交接基线，但不能作为“管理员可完整改工作流 DAG”或“生产安全后台完成”的结论。
