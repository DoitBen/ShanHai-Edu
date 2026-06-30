# ShanHaiEdu 真实认证、RBAC 与项目级授权规格

> 状态：待实施
> 日期：2026-06-30
> 目标仓库：`DOIT-Ben/ShanHai-Edu`
> 规格基线：`main@29ac7fe5b1fcc9b3b99223c8e6d1b4e0cc64b604`
> 实施前置：PR #25 完成审查并 squash merge 到 `main`

## 1. 文档目的

本文是 ShanHaiEdu 第一版真实用户身份、角色权限和项目数据隔离的唯一实施规格。开发人员必须以本文为功能、接口、安全、迁移和验收真源，不得在实现过程中自行弱化权限边界或扩大功能范围。

本任务解决的不是“增加一个登录页”，而是建立完整的服务端安全边界：

`登录 -> 服务端会话 -> 角色判定 -> 项目归属判定 -> API/文件/任务统一授权 -> 审计与测试`

## 2. 当前问题与仓库事实

截至规格基线，仓库存在以下事实：

1. FastAPI 使用 `BACKEND_API_TOKEN` 作为全局 Bearer Token。一个令牌代表整个系统，不能代表具体用户。
2. 未配置 `BACKEND_API_TOKEN` 时，普通业务接口会直接放行，属于 fail-open 行为。
3. Next.js 后端代理会为请求统一注入全局 Bearer Token，因此浏览器请求最终都以同一系统身份访问后端。
4. 前端把 `AuthUser` 写入 `localStorage` 和可由 JavaScript 修改的 Cookie，用户可以伪造角色。
5. 前端存在 `switchRole`，角色是客户端状态，不是服务端授权结论。
6. `project_meta` 没有 `owner_id`；项目列表、节点、任务、素材、视频和下载接口没有对象级授权。
7. `apps/web/prisma/schema.prisma` 中的 `User` 是示例模型，不是现有后端身份真源。
8. 后端业务真源位于 FastAPI 和 SQLite。认证继续由 FastAPI 管理，不能在 Next.js/Prisma 中再建立第二套用户系统。

这些问题意味着当前“管理员/教师”只是一层界面演示，不具备真实安全性。

## 3. 目标与成功定义

本期必须交付：

1. 使用邮箱和密码登录的真实用户账户。
2. 服务端创建、校验、过期和撤销的不透明会话。
3. `admin`、`teacher` 两种服务端角色。
4. 项目 `owner_id` 和完整的项目级数据隔离。
5. 所有项目派生资源继承项目授权，包括节点、任务、素材、图片、视频、工作台运行记录和下载文件。
6. Next.js 代理只转发最终用户会话，不再使用全局 Token 代替用户。
7. 前端刷新后通过 `/auth/me` 恢复身份，客户端不能切换或伪造角色。
8. CSRF、登录限流、Cookie 安全属性、敏感信息脱敏和关键审计事件。
9. 现有项目的显式、可回滚归属迁移。
10. 后端、前端契约和端到端测试证明用户隔离成立。

成功标准：用户 A 即使知道用户 B 的 `project_id`、`run_id`、`task_id`、`asset_id` 或文件路径，也不能读取、修改、运行、重试或下载用户 B 的任何项目资源。

## 4. 明确不做

以下内容不进入本期：

- 用户自助注册。
- 邮件验证、忘记密码和邮件重置密码。
- OAuth、企业 SSO、LDAP、MFA。
- 组织、班级、团队、项目成员和项目分享。
- 项目所有权转移界面。
- 权限自定义、细粒度策略编辑器。
- 管理员用户管理页面。
- JWT、Refresh Token 或浏览器 `localStorage` Token。
- 计费、配额、套餐和支付。
- 创作会话、版本树、参考图语义和多镜头编辑。
- 对视频工作台增加任何新生成功能。

用户由运维 CLI 创建和维护。多人协作和项目共享另立规格，不得提前加入 `project_members`。

## 5. 前置条件与实施基线

1. PR #25 必须先完成独立审查、修复、squash merge。
2. 实现分支必须从 PR #25 合并后的最新 `main` 创建，不能从 `29ac7fe` 或 PR #25 的功能分支直接开发。
3. 开始实现前记录实际基线 SHA，并在 Draft PR 描述中注明。
4. 如果 PR #25 合并后路径或接口发生变化，应只做必要映射，不得改变本文的安全语义。
5. 本规格文档 PR 与功能实现 PR 分开；规格先合并，功能 PR 再开始。

## 6. 架构决策

### 6.1 唯一身份真源

FastAPI 是身份、会话、角色和授权的唯一真源。新增中央 SQLite 数据库：

`<STORAGE_ROOT>/auth.db`

Next.js 只承担页面和同源代理职责。`apps/web/prisma/schema.prisma` 不得承载认证数据；示例 `User`/`Post` 模型应删除，或明确保持未使用且不参与认证。不得同时维护 FastAPI 用户表和 Prisma 用户表。

### 6.2 会话模型

采用服务端不透明会话，不采用 JWT：

1. 登录成功后生成至少 32 字节密码学安全随机令牌。
2. 浏览器只通过 HttpOnly Cookie 持有原始令牌。
3. 数据库只保存令牌的 SHA-256 哈希，不保存原始令牌。
4. 每个会话具有绝对过期时间，默认 12 小时。
5. 退出登录、禁用用户、修改密码时必须撤销相关会话。
6. 过期或撤销的会话统一视为未登录，并清除 Cookie。

### 6.3 授权模型

采用两层授权：

1. RBAC：判断用户是否为 `admin` 或 `teacher`。
2. 对象级授权：判断用户是否有权访问指定 `project_id`。

规则固定为：

- `admin` 可以访问全部项目和管理接口。
- `teacher` 可以创建项目，只能访问 `owner_id` 等于自身用户 ID 的项目。
- 所有项目派生资源只能在项目授权通过后访问。
- 客户端传入的 `role`、`owner_id`、用户名或显示名不参与授权。

### 6.4 拒绝策略

- 未登录访问受保护接口：`401 AUTH_REQUIRED`。
- 登录用户访问明确的管理员全局接口：`403 FORBIDDEN`。
- 登录用户访问不存在或无权访问的项目及派生资源：统一 `404 PROJECT_NOT_FOUND` 或对应资源的 404。
- 不能通过状态码、错误正文、响应时间或列表结果确认其他用户项目是否存在。

## 7. 数据模型

### 7.1 `users`

| 字段 | 类型 | 约束 |
|---|---|---|
| `user_id` | TEXT | 主键，服务端生成 UUID |
| `email` | TEXT | 唯一，写入前去空格并小写化 |
| `display_name` | TEXT | 非空 |
| `password_hash` | TEXT | Argon2id 哈希 |
| `role` | TEXT | 仅 `admin` / `teacher` |
| `is_active` | INTEGER | 0/1，默认 1 |
| `created_at` | TEXT | UTC ISO-8601 |
| `updated_at` | TEXT | UTC ISO-8601 |
| `password_changed_at` | TEXT | UTC ISO-8601 |

密码使用 `argon2-cffi` 的 Argon2id 实现。参数采用库当前推荐配置并允许验证时 rehash；禁止自写密码算法、SHA-256 密码哈希或可逆加密。CLI 创建密码最少 12 个字符。

### 7.2 `sessions`

| 字段 | 类型 | 约束 |
|---|---|---|
| `session_id` | TEXT | 主键 UUID |
| `user_id` | TEXT | 外键到 `users` |
| `token_hash` | TEXT | 唯一，仅保存 SHA-256 |
| `csrf_token_hash` | TEXT | CSRF Token 的 SHA-256 |
| `created_at` | TEXT | UTC ISO-8601 |
| `expires_at` | TEXT | UTC ISO-8601，默认创建后 12 小时 |
| `last_seen_at` | TEXT | UTC ISO-8601，用于审计，不延长绝对过期时间 |
| `revoked_at` | TEXT NULL | 撤销时间 |
| `client_ip_hash` | TEXT NULL | 可选哈希，不保存原始 IP |
| `user_agent` | TEXT NULL | 截断到 256 字符 |

必须为 `token_hash`、`user_id`、`expires_at` 建索引。认证查询只接受未撤销、未过期且用户仍启用的会话。

### 7.3 `login_attempts`

保存限流窗口所需最少信息：规范化邮箱哈希、可信客户端 IP 哈希、失败时间。不得保存明文密码。记录应定期清理。

限流规则：同一规范化邮箱或同一可信客户端 IP 在 15 分钟内失败 5 次后，后续登录返回 `429 AUTH_RATE_LIMITED`；锁定窗口为 15 分钟。成功登录清除该邮箱的失败计数。错误提示不得区分“用户不存在”和“密码错误”。

### 7.4 `audit_events`

至少包含：

| 字段 | 说明 |
|---|---|
| `event_id` | UUID |
| `event_type` | 固定事件名 |
| `actor_user_id` | 可空 |
| `target_type` / `target_id` | 可空 |
| `result` | `success` / `denied` / `failed` |
| `metadata_json` | 脱敏后的最小上下文 |
| `created_at` | UTC ISO-8601 |

必须记录：登录成功、登录失败、限流、退出、会话撤销、密码修改、用户禁用、项目创建、项目越权拒绝。不得记录密码、原始 Session Token、原始 CSRF Token、Provider Key 或完整 Cookie。

### 7.5 项目归属

每个项目数据库的 `project_meta` 新增：

```sql
owner_id TEXT
```

新项目创建时，`owner_id` 必须由当前服务端用户写入，API 请求体不得接受该字段。迁移完成后应用层必须保证 `owner_id` 非空。

第一版不增加 `project_members`。项目内的节点、任务、素材、媒体运行记录和物理文件都继承项目归属，不重复保存独立 ACL。

## 8. 认证 API 契约

所有响应继续使用仓库现有 `ok/data`、`ok/error` Envelope。

### 8.1 `POST /auth/login`

请求：

```json
{
  "email": "teacher@example.com",
  "password": "user supplied password"
}
```

成功：

- 返回 `200`。
- 设置 `shanhai_session` Cookie。
- 返回当前用户和本次会话的 CSRF Token。

```json
{
  "ok": true,
  "data": {
    "user": {
      "user_id": "...",
      "email": "teacher@example.com",
      "display_name": "...",
      "role": "teacher"
    },
    "csrf_token": "...",
    "expires_at": "..."
  }
}
```

失败：

- 凭据错误或用户禁用：`401 AUTH_INVALID_CREDENTIALS`，使用同一通用文案。
- 触发限流：`429 AUTH_RATE_LIMITED`，可返回 `retry_after_seconds`。
- 登录接口必须做 Origin 校验，但不要求已有 CSRF Token。

### 8.2 `GET /auth/me`

要求有效会话。返回与登录成功相同的 `user`、`csrf_token`、`expires_at`。前端刷新后通过该接口恢复身份，不读取本地持久化用户对象。

### 8.3 `POST /auth/logout`

要求有效会话、合法 Origin 和 CSRF Header。成功后撤销当前会话并清除 Cookie。重复退出可返回 `401 AUTH_REQUIRED`，前端均应进入未登录状态。

### 8.4 Cookie 契约

Cookie 名：`shanhai_session`

必须设置：

- `HttpOnly`
- `Path=/`
- `SameSite=Lax`
- `Max-Age` 与 12 小时绝对过期一致
- 生产环境 `Secure=true`

生产环境若未启用 Secure Cookie，应用 readiness 必须失败，不能静默降级。Cookie 不设置 `Domain`，默认绑定当前主机。

## 9. CSRF 与请求来源保护

所有使用 Cookie 认证的 `POST`、`PUT`、`PATCH`、`DELETE` 请求必须同时满足：

1. `Origin` 与配置的精确允许来源匹配。
2. Header `X-CSRF-Token` 存在。
3. Token 哈希与当前 Session 中的 `csrf_token_hash` 恒定时间比较一致。

例外仅限：

- `POST /auth/login`：要求 Origin，不要求 CSRF Token。
- 明确公开且只读的 `GET /health`。

不得使用通配符 CORS Origin。启用 Cookie 后 `allow_credentials=True`，只允许配置中的精确 Origin、必要方法和必要 Header。

## 10. 权限矩阵

| 资源/操作 | 未登录 | teacher | admin |
|---|---:|---:|---:|
| `GET /health` | 允许 | 允许 | 允许 |
| `GET /auth/me`、退出 | 拒绝 | 自己 | 自己 |
| `GET /projects` | 401 | 仅自己的项目 | 全部项目 |
| `POST /projects` | 401 | 创建并归属自己 | 创建并归属自己 |
| 项目详情、更新、manifest、workspace | 401 | 仅自己的项目 | 全部项目 |
| 项目节点生成、编辑、审核、重试 | 401 | 仅自己的项目 | 全部项目 |
| 项目任务和任务重试 | 401 | 仅自己的项目 | 全部项目 |
| 项目素材、上传、下载、导出 | 401 | 仅自己的项目 | 全部项目 |
| 项目视频工作台全部接口 | 401 | 仅自己的项目 | 全部项目 |
| 教材库、教案库读取 | 401 | 允许 | 允许 |
| 教材库、教案库上传/拆分/提取/确认 | 401 | 403 | 允许 |
| `/video/capabilities` | 401 | 允许 | 允许 |
| `/media-workbench` 及全局媒体诊断接口 | 401 | 403 | 允许 |
| `/admin/*` | 404/401 | 403 | 允许 |
| `/readiness`、规则覆盖和控制面 | 401 | 403 | 允许 |

若 PR #25 合并后增加了新的项目级路由，必须按“项目派生资源”处理；不能因为本文未逐条列出而漏掉授权。

## 11. 项目级授权实现要求

### 11.1 集中授权入口

后端必须提供集中依赖，例如：

- `require_current_user`
- `require_role("admin")`
- `require_project_access(project_id)`

所有包含 `/projects/{project_id}` 的路由，在调用 Store、Service、Provider 或访问文件系统之前完成项目授权。授权失败时不能查询或返回目标项目的业务内容。

### 11.2 派生资源绑定

查询 `run_id`、`task_id`、`asset_id`、`filename` 时，必须同时带入并验证路径中的 `project_id`。禁止先按全局 ID 查资源再直接返回。

下载路由必须先授权项目，再做路径解析和文件存在性检查。无权用户不能通过不同的 404 文案推断文件是否存在。

### 11.3 列表隔离

- 教师的 `GET /projects` SQL/存储过滤必须在服务端完成。
- 不能先返回全部项目再由前端过滤。
- 项目计数、任务计数、最近记录和搜索结果都只能包含有权访问的数据。

### 11.4 路由覆盖防回归

增加自动化测试，枚举 FastAPI 路由：任何路径包含 `{project_id}` 的业务路由都必须声明项目授权依赖，除非在测试中的显式公开白名单中。白名单默认应为空。

## 12. 运维用户管理 CLI

新增无 Web UI 的运维 CLI，至少支持：

```bash
python -m apps.api.app.auth_cli create-user --email EMAIL --display-name NAME --role admin
python -m apps.api.app.auth_cli create-user --email EMAIL --display-name NAME --role teacher
python -m apps.api.app.auth_cli set-password --email EMAIL
python -m apps.api.app.auth_cli disable-user --email EMAIL
python -m apps.api.app.auth_cli enable-user --email EMAIL
python -m apps.api.app.auth_cli list-users
```

要求：

- 密码通过 `getpass` 交互输入两次，不提供明文 `--password` 参数。
- 创建重复邮箱必须失败。
- 修改密码和禁用用户必须撤销该用户全部会话。
- `list-users` 不输出密码哈希或会话信息。
- CLI 返回明确退出码，便于部署脚本判断结果。

## 13. 现有项目迁移

迁移不得自动把无主项目分配给“第一个登录用户”。采用显式两阶段流程：

1. 备份 `<STORAGE_ROOT>/auth.db` 和全部项目 `project.db`。
2. 创建至少一个管理员用户。
3. 对所有 `project_meta` 幂等增加 `owner_id`。
4. 运行 dry-run，列出所有无主项目。
5. 显式指定管理员邮箱并执行归属写入。
6. 再次扫描，确认不存在空 `owner_id` 或指向不存在用户的 `owner_id`。

建议命令：

```bash
python -m apps.api.app.auth_cli assign-legacy-projects --owner-email EMAIL
python -m apps.api.app.auth_cli assign-legacy-projects --owner-email EMAIL --apply
python -m apps.api.app.auth_cli verify-project-ownership
```

默认是 dry-run；只有 `--apply` 才能写入。若启用真实认证时仍存在无主项目，`/readiness` 必须失败，项目业务接口不得 fail-open。

迁移脚本必须可重复执行，并提供恢复说明。测试必须覆盖旧项目数据库无 `owner_id`、已有 `owner_id`、中途失败和重复执行。

## 14. Next.js 代理要求

`apps/web/src/app/api/backend/[...path]/route.ts` 必须调整：

1. 转发浏览器的 `Cookie`、`Origin`、`X-CSRF-Token` 和必要内容 Header。
2. 原样转发后端的 `Set-Cookie`，包括清除 Cookie。
3. 不再为用户请求注入 `Authorization: Bearer BACKEND_API_TOKEN`。
4. 不把全局后端 Token 解释成管理员身份。
5. 删除或停用基于 `ENABLE_ADMIN_BACKEND_PROXY` + 全局 Token 的用户授权判断；管理员权限由 FastAPI Session Role 决定。
6. 丢弃客户端主动发送的 `Authorization` Header，防止绕过既定会话模型。
7. 不记录 Cookie、CSRF Token 或登录请求正文。

如未来仍需机器到机器 Token，只能放到独立 `/internal/*` 接口并另立规格，本期不实现。

## 15. 前端行为

### 15.1 API 模式

- 应用启动时状态为 `authReady=false`，调用 `GET /auth/me`。
- 成功后使用服务端返回的用户和角色。
- 401 时进入登录页。
- 登录和退出改为异步真实 API 调用。
- CSRF Token 仅保存在当前内存状态，刷新后由 `/auth/me` 重新获取。
- 所有变更请求自动携带 `X-CSRF-Token`。
- 任一业务请求返回 401 时清空内存身份并回到登录页。
- 403 显示无权限状态，不伪装成网络错误。
- 404 项目资源返回统一“项目不存在或无权访问”。

### 15.2 禁止项

- 删除 API 模式下的 `shanhai_auth` localStorage 和 JavaScript 可写身份 Cookie。
- 删除 API 模式下的 `switchRole`。
- 不允许从 URL、表单或 localStorage 恢复角色。
- 不把密码、Session Token 或 CSRF Token写入 Zustand persist、localStorage、sessionStorage、日志或错误监控。

### 15.3 Demo 模式

`NEXT_PUBLIC_DEMO_MODE=true` 可保留纯本地演示登录，但必须与 API 模式代码路径明确隔离。Demo 身份不得被代理到真实后端，也不得作为 E2E 权限验收依据。

## 16. 安全与错误处理

1. 登录错误使用统一文案，避免账户枚举。
2. Session 和 CSRF 比较使用恒定时间比较。
3. 登录、登出、认证中间件和代理日志不得包含秘密。
4. 用户禁用后，现有会话下一个请求立即失效。
5. 修改密码后，除执行修改的运维动作外全部会话撤销。
6. 数据库异常不得回退到“允许访问”。
7. `owner_id` 缺失、用户不存在或权限服务不可用时一律拒绝。
8. `GET /health` 只返回存活状态，不暴露用户、配置、路径或 Provider 密钥状态。
9. `/readiness` 仅管理员可见，并检查 auth DB、Secure Cookie 配置、项目归属完整性。
10. 不使用客户端隐藏按钮代替后端授权；按钮隐藏只是体验优化。

## 17. 测试与验收

### 17.1 后端认证测试

必须覆盖：

- 正确密码登录成功并创建数据库会话。
- 错误邮箱、错误密码、禁用用户返回同一错误。
- 数据库不保存原始密码、Session Token、CSRF Token。
- Cookie 的 `HttpOnly`、`SameSite=Lax`、`Path=/`、过期时间和生产 `Secure`。
- `/auth/me` 的有效、过期、撤销、禁用用户场景。
- 退出撤销当前会话并清除 Cookie。
- 修改密码、禁用用户撤销全部会话。
- 5 次失败后的邮箱/IP 限流与窗口恢复。
- Origin 和 CSRF 的缺失、错误、跨会话 Token、正确 Token。
- 登录响应和日志不泄漏哈希、Token 或 Cookie。

### 17.2 RBAC 测试

必须使用至少两个教师账户和一个管理员账户：

- 教师不能访问 `/admin/*`、全局媒体工作台、控制面和写入型资源库接口。
- 管理员可以访问上述接口。
- 修改前端角色对象、请求体角色或伪造 Header 不提升权限。
- 未登录接口返回 401，角色不足的全局接口返回 403。

### 17.3 项目隔离测试

用户 A 和用户 B 各创建一个项目。对每类路由至少验证一次同用户成功和跨用户 404：

- 项目列表、详情、更新、manifest、workspace。
- 节点读取、生成、编辑、审核、重试、版本。
- 任务列表、任务详情、任务同步和重试。
- 教材上传到项目、项目素材和文件下载。
- PPT 导出、最终视频、片段和生成图片下载。
- PR #25 合并后的参考图、视频工作台配置、运行记录、同步、重试、预览和下载。
- 媒体工作台中任何绑定项目的资源。

还必须验证：把用户 B 的 `run_id`、`task_id` 或 `asset_id` 放入用户 A 的项目 URL 时不能得到数据。

### 17.4 迁移测试

- 旧项目 DB 无 `owner_id` 时 dry-run 不写数据。
- `--apply` 后归属指定用户。
- 重复执行不产生重复或改写已有归属。
- 指定用户不存在时不写任何项目。
- 中途失败可以重新执行且不留下部分错误状态。
- 存在无主项目时 readiness 失败。

### 17.5 前端与代理测试

- API 模式不读取或写入 `shanhai_auth`。
- 刷新页面通过 `/auth/me` 恢复会话。
- 登录、退出、会话过期 UX 正确。
- 代理转发 Cookie、CSRF 和 `Set-Cookie`。
- 代理不会注入全局 Bearer Token，也不会接受客户端 Bearer Token 提权。
- 教师界面不显示管理员入口，但后端测试仍独立证明 403。
- 两个独立浏览器上下文验证项目互不可见。
- Demo 模式和 API 模式互不污染。

### 17.6 回归门禁

功能 PR 至少提供以下新鲜证据：

```bash
python -m pytest apps/api/tests -q
cd apps/web && bun run test:contracts
cd apps/web && bunx tsc --noEmit --incremental false
cd apps/web && bun run lint
cd apps/web && bun run build
cd apps/web && bun run test:e2e -- --workers=1
cd apps/web && bun run scan:client-secrets
git diff --check
```

若仓库在 PR #25 合并后调整脚本名称，应使用等价完整命令，并在 PR 中写明映射。不能用缩小测试范围代替完整回归。

## 18. 完成定义

以下条件全部满足才算完成：

1. 身份、会话、RBAC、项目归属和 CSRF 均由 FastAPI 强制执行。
2. API 模式不存在 localStorage 身份和客户端角色切换。
3. 全局 Bearer Token 不再代表浏览器用户。
4. 所有项目路由经过统一项目授权，路由覆盖测试通过。
5. 两教师一管理员的隔离和权限 E2E 通过。
6. 现有项目完成显式归属迁移，readiness 无无主项目。
7. Cookie、限流、会话撤销和日志脱敏测试通过。
8. 后端、前端类型、Lint、Build、E2E 和秘密扫描全部通过。
9. Draft PR 清楚列出迁移步骤、权限矩阵、测试证据和剩余风险。
10. 有独立 Review；实现者不得自行合并。

仅完成登录页、仅增加用户表、仅隐藏管理员按钮或仅让测试通过，都不算完成。

## 19. 实施顺序

建议按以下顺序提交，保持每步可审查：

1. auth DB、用户 CLI、Argon2id 和迁移测试。
2. 登录、会话、Cookie、CSRF、限流和认证测试。
3. `project_meta.owner_id`、遗留项目迁移和项目授权依赖。
4. 全部项目路由与全局路由的 RBAC 收口。
5. Next.js 代理改造和 API Client 认证契约。
6. 前端真实登录、身份恢复、退出和角色 UI。
7. 双用户项目隔离 E2E、完整回归和文档更新。

实现过程中不得顺手重构工作流、Provider、媒体生成状态机或页面视觉系统。

## 20. 回滚方案

1. 发布前保留 `auth.db` 和所有项目 DB 备份。
2. 数据迁移只做向前兼容的加列，不删除原项目数据。
3. 应用回滚时恢复代码和迁移前数据库备份；不得通过清空 `owner_id` 或关闭认证临时恢复服务。
4. 若登录系统故障，修复认证或回滚版本；禁止启用无 Token 放行模式。
5. 回滚演练至少在复制的测试存储目录执行一次并记录结果。

## 21. 后续路线

本任务完成并合并后，下一项产品任务才是 GPT 风格创作工作台的核心：统一创作会话、消息/生成记录和可分叉版本链。认证与项目隔离未完成前，不应继续扩展创作功能，否则新增资源仍会建立在无真实用户边界的基础上。
