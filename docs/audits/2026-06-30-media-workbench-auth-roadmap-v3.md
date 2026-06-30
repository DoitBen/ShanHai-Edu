# ShanHaiEdu 媒体工作台与认证授权审计路线 V3

> 审计对象：`DOIT-Ben/ShanHai-Edu`
>
> 当前基线：`main@1c4bc5522dc3305f36de0e4a5bba9029065b169f`
>
> 日期：2026-06-30
>
> 状态：当前唯一整改路线草案，替代旧 PR #23 的 V2 口径
>
> 审计重点：视频工作台、媒体生成链路、真实认证、项目归属、对象级授权、GPT 式创作体验

## 1. 当前结论

截至 `main@1c4bc55`，项目已经完成两件关键地基工作：

1. PR #25 已合并，视频工作台从装饰性画布收敛为可用的单段视频生成工作台。
2. PR #28 已合并，FastAPI 后端具备真实认证 Phase A：用户、密码哈希、服务端 session、HttpOnly Cookie、CSRF、登录限流、CLI 和后端测试。

但系统还不能视为真正可多人上线：

1. 现有项目、任务、素材、视频工作流和下载接口仍主要依赖全局 `BACKEND_API_TOKEN`。
2. `project_meta` 仍没有 `owner_id`。
3. Next.js 代理和前端登录态仍未接入真实用户会话。
4. 视频工作台仍是“单 prompt + 单结果 + 任务历史”，不是 GPT 式连续创作工作台。

当前下一步不是继续扩展视频功能，而是完成项目归属和对象级授权。

## 2. 已合并事实

| 范围 | 状态 | 证据 | 结论 |
|---|---|---|---|
| PR #25 视频工作台 | 已合并 | `main` 已包含 Google Flow 核心视频工作台 | 单段视频生成基础可继续承载后续体验 |
| PR #27 认证/RBAC 规格 | 已合并 | `docs/superpowers/specs/2026-06-30-real-auth-project-rbac-design.md` | 后续认证与授权以此为规格真源 |
| PR #28 认证 Phase A | 已合并 | `main@1c4bc5522dc3305f36de0e4a5bba9029065b169f` | 用户、session、Cookie、CSRF、CLI 已进入主线 |
| main Actions | 已通过 | `Video Workbench Delivery Gate #47` on `main@1c4bc55` | 可以开始下一阶段规划 |

## 3. 仍未解决的核心问题

| ID | 级别 | 问题 | 当前状态 | 下一阶段 |
|---|---|---|---|---|
| MW-001 | P0 | 管理员代理和后端接口仍未以真实用户授权 | 部分解决：认证有了，授权未接入 | Phase C/D |
| MW-002 | P0 | 前端真实登录闭环未完成 | 部分解决：后端 auth API 有了，前端未接入 | Phase D |
| MW-004 | P1 | 上传安全与存储治理仍需继续收口 | 部分解决 | 后续安全收口 |
| MW-005 | P1 | 图片生成仍偏同步请求模式 | 未解决 | 创作任务基础设施 |
| MW-013 | P1 | 任务取消和后台队列仍未完成 | 部分解决 | 创作任务基础设施 |
| MW-015 | P1 | 参考素材没有角色、风格、首帧、尾帧等语义 | 未解决 | GPT 式创作阶段 |
| MW-016 | P0 | 项目已有项目级数据，但没有用户级隔离 | 部分解决 | Phase B/C |
| MW-018 | P2 | 没有基于结果继续修改和版本树 | 未解决 | GPT 式创作阶段 |
| MW-019 | P2 | 缺少候选对比、版本对比和完整预览体验 | 部分解决 | GPT 式创作阶段 |
| MW-020 | P2 | 素材库缺少搜索、筛选、分页、批量管理 | 部分解决 | 素材规模化阶段 |
| MW-027 | P1 | 缺少用户级额度、费用审计和高成本治理 | 部分解决 | 多用户发布前 |
| MW-028 | P1 | 缺少真实用户隔离 E2E | 部分解决 | Phase C/D/E |

## 4. 当前架构风险

### 4.1 认证已经有了，但业务接口还没有用

PR #28 增加了：

- `users`
- `sessions`
- `login_attempts`
- `auth_audit_events`
- `/auth/login`
- `/auth/me`
- `/auth/logout`
- Auth CLI

但 `apps/api/app/main.py` 中业务接口仍主要使用：

```python
protected = [Depends(require_api_token(settings))]
```

这意味着真实用户身份还没有进入项目、任务、素材、视频工作台和下载链路。Phase A 只解决“你是谁”，还没有解决“你能访问什么”。

### 4.2 `ProjectStore.create_project` 还不知道当前用户

当前 `ProjectStore.create_project(payload, workflow)` 只从请求 payload 写入项目元数据。它没有 `current_user` 参数，也不会写 `owner_id`。

Phase B 必须完成：

- `project_meta.owner_id`
- 新项目创建写入 owner
- 历史项目显式归属迁移
- 缺 owner 项目的 readiness/verify 检查

### 4.3 Next.js 代理仍是后续风险点

Phase D 前，不应宣称前端真实权限已完成。只要 Next 代理仍然替浏览器注入全局 `BACKEND_API_TOKEN`，浏览器侧的真实用户会话就不是完整安全边界。

### 4.4 视频工作台不是 GPT 式创作工作台

PR #25 已让视频生成能用，但当前体验仍不是 GPT 风格：

- 没有创作会话。
- 没有消息流。
- 没有“基于这个结果继续改”。
- 没有版本分支。
- 没有参考素材语义。
- 没有多镜头时间线。
- 没有字幕、配音和镜头组装。

这些应放在认证和对象级授权之后做，不能提前塞进 RBAC PR。

## 5. 后续阶段定义

### Phase B：项目归属与历史迁移

目标：让每个项目拥有明确 `owner_id`，为对象级授权准备数据地基。

必须做：

1. `project_meta` 增加 `owner_id`。
2. 新建项目时由服务端当前用户写入 `owner_id`。
3. 历史项目迁移 CLI，支持 `dry-run` 和 `apply`。
4. 迁移不得自动分配给第一个用户。
5. 支持显式 owner email/user_id 或映射文件。
6. readiness/verify 能发现缺失 `owner_id` 的项目。
7. 后端测试覆盖新项目、旧项目、迁移、幂等和失败场景。

禁止做：

- 不保护业务接口。
- 不改 Next.js 代理。
- 不改前端登录页。
- 不做 `project_members`。
- 不做项目共享。
- 不做完整 RBAC。
- 不改视频工作台功能。

建议分支：

```text
feat/project-ownership-migration
```

建议 PR 标题：

```text
[phase-b] project ownership and legacy migration
```

### Phase C：后端对象级授权

目标：业务 API 开始使用真实用户和项目归属。

必须做：

1. 增加 `require_current_user`。
2. 增加 `require_role`。
3. 增加 `require_project_access`。
4. 保护 `/projects/{project_id}` 派生接口。
5. 保护节点、任务、素材、视频工作流、下载和 cleanup。
6. teacher 只能访问自己的项目。
7. admin 可以访问全部项目。
8. 越权访问项目返回 404，不能泄露项目存在性。
9. 补两名 teacher 的隔离测试。

禁止做：

- 不改前端登录 UI。
- 不做 project_members。
- 不做共享项目。
- 不做 GPT 式创作会话。

### Phase D：Next 代理与前端真实登录

目标：浏览器侧不再靠 localStorage 伪造身份，也不再由 Next 代理注入全局系统 Token 代表用户。

必须做：

1. 前端登录页调用 `/auth/login`。
2. 前端启动调用 `/auth/me` 恢复身份。
3. 前端使用服务端返回的角色和状态。
4. 移除或禁用 `switchRole`。
5. 移除 localStorage 作为授权真源。
6. Next 代理转发 Cookie 和 CSRF。
7. 浏览器请求不得自行携带后端全局 Token。

### Phase E：端到端安全门禁

目标：证明多用户隔离不是只在单元测试里成立。

必须做：

1. E2E：teacher A 不能看 teacher B 项目列表。
2. E2E：teacher A 猜测 B 的 project_id 返回 404。
3. E2E：teacher A 不能下载 B 的视频、图片、素材和导出文件。
4. E2E：admin 可以查看所有项目。
5. E2E：未登录访问业务页跳登录。
6. CI 必须跑前后端契约、类型检查、lint、build、Playwright 和 secret scan。

## 6. GPT 式媒体工作台路线

认证与授权完成前，不开始 GPT 式创作工作台。完成 Phase B/C/D/E 后，再进入媒体体验阶段。

建议顺序：

1. Creative Sessions：创作会话、消息流、上下文保存。
2. Generation Results：图片/视频结果统一结果对象。
3. Version Graph：从任一结果继续修改，形成版本链。
4. Semantic References：参考图角色、风格、主体、场景、首帧、尾帧。
5. Multi-shot Timeline：多镜头脚本、镜头顺序、时长、转场。
6. Audio/Subtitles：配音、字幕、背景音乐。
7. Composition Export：镜头合成、PPT/视频导出闭环。

## 7. 旧 PR 处理建议

| PR | 当前建议 | 原因 |
|---|---|---|
| #22 | 关闭或摘取仍有效内容到本 V3 后关闭 | 基线过旧，和后续规格重复 |
| #23 | 关闭，由本 V3 替代 | V2 仍把 PR #25 视为 Draft，已不准确 |
| #26 | 暂缓，不进入当前主线 | 协作机制不是当前 P0 技术风险 |

不要同时维护多份路线图。后续以本 V3 和 `docs/superpowers/specs/2026-06-30-real-auth-project-rbac-design.md` 为准。

## 8. Phase B 开发任务指令

在本 V3 合并后，再把以下指令发给执行者：

```text
当前状态：
PR #25、PR #27、PR #28 均已合并到 main。

main 最新基线 SHA：
1c4bc5522dc3305f36de0e4a5bba9029065b169f

现在开始 Phase B，但只允许进入计划阶段，不写代码。

请从最新 main 创建新分支：
feat/project-ownership-migration

唯一规格来源：
docs/superpowers/specs/2026-06-30-real-auth-project-rbac-design.md

路线图参考：
docs/audits/2026-06-30-media-workbench-auth-roadmap-v3.md

本轮目标：
实现项目归属基础与历史项目迁移，为后续对象级授权做准备。

本轮只允许规划以下内容：
1. project_meta.owner_id 的数据结构方案。
2. 新建项目时 owner_id 的写入方案。
3. 历史项目归属迁移 CLI 方案。
4. dry-run / apply 迁移流程。
5. 缺失 owner_id 的 readiness / verify 检查方案。
6. 对应测试计划。
7. 预计修改文件清单。

本轮禁止：
- 不写代码
- 不做完整 RBAC
- 不保护现有项目接口
- 不改 video-workflow 权限
- 不改 Next.js 代理
- 不改前端登录页
- 不做 project_members
- 不做项目共享
- 不做创作会话、版本链、时间线、多镜头
- 不顺手重构视频工作台

请先输出 Phase B 实施计划和预计修改文件清单，等待确认后再开发。
```

## 9. 合并门禁

本 V3 文档合并后，进入 Phase B 前必须满足：

1. `main` 最新 Actions 通过。
2. PR #28 已合并且不再追加认证 Phase A 内容。
3. 旧审计 PR #23 不再作为执行真源。
4. Phase B 只允许提交计划，不直接写代码。

## 10. 当前一句话判断

ShanHaiEdu 已经完成视频工作台基础和认证地基，但还没有完成项目归属、对象级授权和前端真实登录闭环；下一阶段必须先做 Phase B 项目归属迁移，而不是继续扩展视频创作功能。
