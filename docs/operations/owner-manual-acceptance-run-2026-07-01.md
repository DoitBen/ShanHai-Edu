# Owner 人工验收记录 - 2026-07-01

本文档用于记录 ShanHai-Edu 认证/RBAC/视频工作台底座的人工验收过程。

未执行并记录证据的项目不得标记为 `PASS`。

## 1. 验收目标

在当前 `main` 基线上，验证真实用户认证、RBAC、项目归属、对象级授权、CSRF/Cookie 处理，以及项目视频工作台底座。

本文档只记录验收证据，不授权修 bug、不改应用代码、不改 CI、不改依赖、不改运行配置、不启动 Phase F，也不启动任何新产品功能。

## 2. 验收环境记录

| 字段 | 值 |
| --- | --- |
| main SHA | 待验收时填写实际运行的 main SHA |
| 日期 | 2026-07-01 |
| 验收人 | TBD |
| 验收环境 | TBD |
| API 模式 / demo 模式 | 安全验收必须使用 API 模式；demo 模式可作为兼容性证据单独记录 |

验收前必须填写实际运行环境对应的 main commit SHA；不得沿用旧 SHA。

## 3. 账号准备

| 账号 | 准备状态 | 标识 | 备注 |
| --- | --- | --- | --- |
| admin | NOT_RUN | TBD | 需要启用状态的 admin 账号 |
| teacher A | NOT_RUN | TBD | 必须拥有 Project A |
| teacher B | NOT_RUN | TBD | 必须拥有 Project B |

## 4. 项目准备

| 项目 | 归属人 | 准备状态 | 备注 |
| --- | --- | --- | --- |
| Project A | Teacher A | NOT_RUN | `project_meta.owner_id` 必须指向 Teacher A |
| Project B | Teacher B | NOT_RUN | `project_meta.owner_id` 必须指向 Teacher B |

## 5. 引用验收清单

人工验收覆盖范围以以下清单为准：

- `docs/operations/manual-acceptance-checklist.md`

## 6. 逐项验收记录

允许的结果值：

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_RUN`

### 前置检查

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| 部署 commit 与目标 SHA 一致 | NOT_RUN | TBD |  |
| 真实验收时 `NEXT_PUBLIC_DEMO_MODE=false` | NOT_RUN | TBD |  |
| FastAPI `STORAGE_ROOT` 指向预期环境 | NOT_RUN | TBD |  |
| 通过 HTTPS 提供服务时 `AUTH_COOKIE_SECURE=true` | NOT_RUN | TBD |  |
| Origin allowlist 只包含预期前端来源 | NOT_RUN | TBD |  |
| 启用状态的 admin、teacher A、teacher B 均存在 | NOT_RUN | TBD |  |
| `verify-project-ownership` 报告没有缺失 owner 或孤儿 owner 项目 | NOT_RUN | TBD |  |

### 登录与会话

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| 未登录用户看到登录页 | NOT_RUN | TBD |  |
| 有效 teacher 登录成功 | NOT_RUN | TBD |  |
| 有效 admin 登录成功 | NOT_RUN | TBD |  |
| 页面刷新后 `/auth/me` 能恢复用户 | NOT_RUN | TBD |  |
| logout 清除 session 并返回登录页 | NOT_RUN | TBD |  |
| disabled 或 invalid 用户不能登录 | NOT_RUN | TBD |  |
| `localStorage` 或 `sessionStorage` 中不出现 session token 或 CSRF token | NOT_RUN | TBD |  |

### 角色可见性

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| Teacher 只看到教师侧导航 | NOT_RUN | TBD |  |
| Teacher 看不到仅管理员可用入口 | NOT_RUN | TBD |  |
| Admin 能看到管理员入口 | NOT_RUN | TBD |  |
| API 模式下不显示 demo 角色切换 | NOT_RUN | TBD |  |

### 项目访问

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| Teacher A 在项目列表中只看到 Teacher A 项目 | NOT_RUN | TBD |  |
| Teacher B 在项目列表中只看到 Teacher B 项目 | NOT_RUN | TBD |  |
| Admin 能看到 Teacher A 和 Teacher B 项目 | NOT_RUN | TBD |  |
| Teacher A 打开 Teacher B 项目 URL 返回 404/no-access 响应 | NOT_RUN | TBD |  |
| 客户端提供的 `Authorization` 或角色数据不能获得额外访问权限 | NOT_RUN | TBD |  |

### 视频工作台

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| Teacher 能打开自己项目的视频工作台 | NOT_RUN | TBD |  |
| 视频能力通过 `/api/backend` 加载 | NOT_RUN | TBD |  |
| 自己项目的参考素材列表能加载 | NOT_RUN | TBD |  |
| 合法图片的参考图片上传成功 | NOT_RUN | TBD |  |
| 非法图片上传被受控校验错误拒绝 | NOT_RUN | TBD |  |
| 自己项目的参考图片删除成功 | NOT_RUN | TBD |  |
| 自己项目的历史运行记录列表能加载 | NOT_RUN | TBD |  |
| 使用合法输入创建视频运行记录成功 | NOT_RUN | TBD |  |
| 运行轮询和手动同步能正确更新状态 | NOT_RUN | TBD |  |
| Provider `completed` 但没有 URL 时，pending URL/download 状态可识别 | NOT_RUN | TBD |  |
| pending URL timeout 后进入可重试状态并允许 retry | NOT_RUN | TBD |  |
| completed output 可播放并可下载 | NOT_RUN | TBD |  |
| demo 模式视频工作台兼容性与安全验收分开记录 | NOT_RUN | TBD |  |

### 跨用户视频安全

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| Teacher A 不能读取 Teacher B 的 `/video-workflow` | NOT_RUN | TBD |  |
| Teacher A 不能访问 Teacher B 的 video-workflow assets | NOT_RUN | TBD |  |
| Teacher A 不能读取 Teacher B 的 video-workflow asset content | NOT_RUN | TBD |  |
| Teacher A 不能访问 Teacher B 的 video-workflow 运行记录 | NOT_RUN | TBD |  |
| Teacher A 不能读取 Teacher B 的运行内容 | NOT_RUN | TBD |  |
| Teacher A 不能下载 Teacher B 的运行输出 | NOT_RUN | TBD |  |
| Teacher A 不能下载 Teacher B 的 completed output | NOT_RUN | TBD |  |
| Teacher A 不能对 Teacher B 项目执行清理 | NOT_RUN | TBD |  |
| 存储清理只作用于当前有权限项目 | NOT_RUN | TBD |  |
| 所有跨用户拒绝使用 404-style 响应，且不泄露资源存在性 | NOT_RUN | TBD |  |

### CSRF 与 Cookie

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| 登录设置 `shanhai_session`，且为 `HttpOnly` | NOT_RUN | TBD |  |
| Cookie 包含 `Path=/` 和 `SameSite=Lax` | NOT_RUN | TBD |  |
| 生产 HTTPS Cookie 包含 `Secure` | NOT_RUN | TBD |  |
| 缺少 `X-CSRF-Token` 的 unsafe 请求失败 | NOT_RUN | TBD |  |
| 携带错误 `X-CSRF-Token` 的 unsafe 请求失败 | NOT_RUN | TBD |  |
| 授权用户携带当前 `X-CSRF-Token` 的 unsafe 请求成功 | NOT_RUN | TBD |  |

### 管理员与资源库

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| Teacher 不能调用 admin-only 接口 | NOT_RUN | TBD |  |
| Admin 能调用 admin-only 接口 | NOT_RUN | TBD |  |
| Teacher/admin 能读取允许的全局只读接口 | NOT_RUN | TBD |  |
| 教材库和教案库行为符合当前 RBAC 矩阵 | NOT_RUN | TBD |  |

### 就绪与运维

| 检查项 | 结果 | 证据 | 备注 |
| --- | --- | --- | --- |
| `/health` 返回 ok | NOT_RUN | TBD |  |
| `/readiness` 返回预期 provider 和 ownership 状态 | NOT_RUN | TBD |  |
| 存储清理返回策略和用量结构 | NOT_RUN | TBD |  |
| 存储清理已验证只作用于当前有权限项目 | NOT_RUN | TBD |  |
| 如果 provider URL 交付延迟，记录 pending URL timeout/retry 行为 | NOT_RUN | TBD |  |
| `auth.db` 和 project DB 文件有发布备份 | NOT_RUN | TBD |  |
| `docs/operations/release-readiness-auth-rbac.md` 中的回滚说明仍准确 | NOT_RUN | TBD |  |

## 7. 最终结论

结果：`NOT_RUN`

最终结论允许值：

- `PASS`
- `PASS_WITH_RISKS`
- `FAIL`

逐项验收记录执行并复核之前，不得填写最终结论。

## 8. 阻塞问题

| 问题 | 状态 | 证据 | 负责人 | 备注 |
| --- | --- | --- | --- | --- |
| TBD | NOT_RUN | TBD | TBD |  |

## 9. 已接受风险

| 风险 | 接受人 | 证据 | 备注 |
| --- | --- | --- | --- |
| TBD | TBD | TBD |  |

## 10. 下一步建议

当前建议：`NOT_RUN`

验收后记录一项建议：

- 可以发布
- 带已接受风险发布
- 阻止发布并修复问题
- 完成环境/数据准备后重新验收

备注：

- TBD
