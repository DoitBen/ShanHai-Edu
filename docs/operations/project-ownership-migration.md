# Project Ownership Migration Operations

本文档说明 Phase B 的项目归属迁移运维流程。Phase B 只建立 `project_meta.owner_id` 数据地基，为 Phase C 的对象级授权做准备；本阶段不实现项目访问控制、不保护 `video-workflow`，也不修改 Next.js 代理或前端登录逻辑。

## 背景

真实认证引入后，后端需要知道每个项目属于哪个用户，后续才能做到：

- 教师只能访问自己的项目。
- 管理员可以访问全部项目。
- 跨用户项目和派生资源统一返回 404，避免资源枚举。

因此 Phase B 为每个项目的 `project.db` 中 `project_meta` 增加 `owner_id TEXT`。新建项目必须写入明确的 `owner_id`；历史项目在迁移完成前可能处于 legacy unowned 状态，需要通过 CLI 显式分配。

## 新项目 Owner Resolver 规则

创建项目时，服务端按以下顺序决定 owner：

1. 如果请求带有有效 `shanhai_session` Cookie，使用当前登录用户的 `user_id`。
2. 如果没有有效 Cookie，必须走旧 `BACKEND_API_TOKEN` 兼容路径。
3. 兼容路径必须配置后端令牌，并且请求的 Bearer token 必须匹配。
4. 兼容路径必须配置 `PROJECT_CREATION_DEFAULT_OWNER_USER_ID`。
5. fallback owner 必须存在于 `auth.db.users`，且用户状态为 active。
6. 请求体中的 `owner_id` 不被接受；客户端不能覆盖服务端 owner。
7. 如果无法解析出合法 owner，创建项目失败，不允许写入 `owner_id=NULL`。

相关错误：

- `PROJECT_OWNER_FORBIDDEN`：请求体包含 `owner_id`。
- `PROJECT_OWNER_REQUIRED`：没有有效登录用户，也没有合法 fallback owner。
- `UNAUTHORIZED`：无 Cookie 请求没有配置后端令牌，或没有合法 Bearer header。
- `FORBIDDEN`：Bearer token 与 `BACKEND_API_TOKEN` 不匹配。

## Fallback Owner 配置

`PROJECT_CREATION_DEFAULT_OWNER_USER_ID` 只用于旧后端令牌兼容路径。它应指向一个已存在且 active 的 admin 或 teacher 用户。无 Cookie 请求不能只依赖 fallback owner；必须同时配置后端令牌并通过 Bearer token 校验。

示例：

```powershell
$env:PROJECT_CREATION_DEFAULT_OWNER_USER_ID = "user_xxx"
$env:BACKEND_API_TOKEN = "<server-side-token>"
```

上线前必须确认 fallback owner 存在：

```powershell
python -m apps.api.app.auth_cli --storage-root storage list-users
```

如果启用 fallback owner，必须同时配置 `BACKEND_API_TOKEN`。未配置后端令牌时，无 Cookie 请求会返回 `UNAUTHORIZED`，不会创建项目。

## verify-project-ownership

该命令只读扫描所有项目，不修改数据库。

```powershell
python -m apps.api.app.auth_cli --storage-root storage verify-project-ownership
python -m apps.api.app.auth_cli --storage-root storage verify-project-ownership --json
```

文本输出包含：

- `total_projects`
- `owned_projects`
- `missing_owner_projects`
- `orphaned_owner_projects`
- `projects_missing_owner_column`
- `ready_for_phase_c`
- `issues`

退出码：

- `0`：`ready_for_phase_c=true`
- `1`：仍存在缺失 owner 或孤儿 owner

## assign-legacy-projects Dry-Run

不带 `--apply` 时只输出计划，不写入任何 `project.db`。

按 owner email 分配：

```powershell
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --owner-email teacher@example.com
```

按 owner user id 分配：

```powershell
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --owner-user-id user_xxx
```

按 mapping file 批量分配：

```powershell
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --mapping-file .\ownership-mapping.json
```

Dry-run 输出：

- `planned_count`
- `written_count=0`
- `skipped_existing_owner_count`
- `failed_count=0`
- `errors`

## assign-legacy-projects --apply

带 `--apply` 时才会写入项目数据库。

```powershell
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --owner-email teacher@example.com --apply
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --owner-user-id user_xxx --apply
python -m apps.api.app.auth_cli --storage-root storage assign-legacy-projects --mapping-file .\ownership-mapping.json --apply
```

写入规则：

- 对缺少 `owner_id` 列的历史项目，先幂等增加 `owner_id TEXT`。
- 对 `owner_id` 为空的项目，写入目标 owner。
- 已有 owner 的项目默认跳过，不覆盖。
- 同一命令可重复执行。

## Mapping File 示例

根节点必须是对象，key 为 `project_id`。value 可以是 email、`user_id` 字符串，或包含 `owner_email` / `owner_user_id` 的对象。

```json
{
  "proj_aaaaaaaaaaaa": "teacher@example.com",
  "proj_bbbbbbbbbbbb": "user_123456",
  "proj_cccccccccccc": {
    "owner_email": "teacher2@example.com"
  },
  "proj_dddddddddddd": {
    "owner_user_id": "user_abcdef"
  }
}
```

同一个 mapping 条目不要同时写 `owner_email` 和 `owner_user_id`。

## Preflight 0 写入保证

`assign-legacy-projects --apply` 在写库前会先完成全量校验：

- owner email 必须存在。
- owner user id 必须存在。
- mapping file 必须是合法 JSON object。
- mapping file 中所有 `project_id` 必须存在。
- mapping file 中所有 owner 必须存在。
- 已有 owner 的项目默认不覆盖。

只要 preflight 存在错误，apply 阶段 `written_count=0`，不会发生部分写入。

注意：项目分散在多个 `project.db`，当前没有跨 DB 全局事务。Phase B 通过 preflight 避免“校验失败导致部分写入”，但不能把多项目写入声明为全局事务。

## ready_for_phase_c 判定

Phase B 的 `/readiness` 保持非阻断，但会返回 `project_ownership`：

```json
{
  "project_ownership": {
    "ready_for_phase_c": false,
    "missing_owner_projects": 1,
    "orphaned_owner_projects": 0,
    "issues": []
  }
}
```

进入 Phase C 前必须满足：

```text
missing_owner_projects = 0
orphaned_owner_projects = 0
ready_for_phase_c = true
```

问题类型：

- `missing_owner_column`：项目数据库缺少 `project_meta.owner_id` 列。
- `missing_owner`：项目存在 `owner_id` 列，但值为空。
- `orphaned_owner`：项目 `owner_id` 指向不存在的用户。

## 常见错误和处理方式

| 错误 | 场景 | 处理 |
| --- | --- | --- |
| `PROJECT_OWNER_REQUIRED` | 创建项目时无登录用户且 fallback owner 不合法 | 创建或启用 fallback 用户，并配置 `PROJECT_CREATION_DEFAULT_OWNER_USER_ID` |
| `UNAUTHORIZED` | 无 Cookie 请求缺少后端令牌配置或 Bearer header | 配置后端令牌，并通过服务端调用传入匹配的 Bearer token |
| `PROJECT_OWNER_FORBIDDEN` | 请求体试图传入 `owner_id` | 删除请求体中的 `owner_id`，让服务端解析 owner |
| `PROJECT_OWNER_NOT_FOUND` | CLI 指定的 owner 不存在 | 先用 `create-user` 创建用户，或修正 email/user id |
| `PROJECT_OWNER_AMBIGUOUS` | 同时指定 owner email 和 owner user id | 只保留一种 owner 指定方式 |
| `MAPPING_FILE_INVALID` | mapping JSON 格式错误或根节点不是 object | 修复 JSON 格式后重新 dry-run |
| `MAPPING_PROJECT_NOT_FOUND` | mapping 中包含不存在的项目 | 修正 mapping 或确认项目目录是否缺失 |
| `missing_owner_column` | 历史项目没有 owner 列 | 用 `assign-legacy-projects --apply` 迁移 |
| `missing_owner` | 历史项目 owner 为空 | 用 `assign-legacy-projects --apply` 迁移 |
| `orphaned_owner` | owner 指向不存在用户 | 创建对应用户或重新分配 owner |

## 回滚方式

Phase B 修改的是每个项目目录下的 `project.db`。上线前必须备份 storage，尤其是 `storage\projects\*\project.db` 和 `storage\auth.db`。

推荐备份：

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item -Recurse -LiteralPath .\storage -Destination ".\storage-backup-project-ownership-$stamp"
```

恢复单个项目：

```powershell
Copy-Item -LiteralPath ".\storage-backup-project-ownership-YYYYMMDD-HHMMSS\projects\<project-folder>\project.db" `
  -Destination ".\storage\projects\<project-folder>\project.db" -Force
```

恢复全部 storage：

```powershell
Rename-Item -LiteralPath .\storage -NewName "storage-broken-YYYYMMDD-HHMMSS"
Copy-Item -Recurse -LiteralPath ".\storage-backup-project-ownership-YYYYMMDD-HHMMSS" -Destination .\storage
```

不要通过清空 `owner_id` 回滚；这会破坏 Phase C 的授权前置条件。

## 上线前检查清单

- [ ] 已确认 PR #28 真实认证基础设施在 main。
- [ ] 已创建或确认 fallback owner 用户，并记录 `user_id`。
- [ ] 已配置 `PROJECT_CREATION_DEFAULT_OWNER_USER_ID`。
- [ ] 若仍使用旧后端令牌路径，已配置 `BACKEND_API_TOKEN`，且无 Cookie 请求必须通过 Bearer token 校验。
- [ ] 已备份 `storage` 或至少备份全部 `project.db` 与 `auth.db`。
- [ ] 已执行 `verify-project-ownership --json` 并保存输出。
- [ ] 已对 `assign-legacy-projects` 执行 dry-run。
- [ ] apply 前 mapping file 已人工复核。
- [ ] apply 后再次执行 `verify-project-ownership --json`。
- [ ] `missing_owner_projects=0`。
- [ ] `orphaned_owner_projects=0`。
- [ ] 已运行 Phase B 目标测试。
- [ ] 已确认本阶段仍未启用 Phase C 对象级授权。
