# Project Ownership Phase B Checklist

本清单用于 PR `[phase-b] project ownership and legacy migration` 的 Review 与上线前验收。Phase B 只交付 `project_meta.owner_id` 与历史迁移能力；Phase B.1 只补运维文档和验收清单。

## 1. 数据 Schema 验收

- [ ] 新项目 `project.db.project_meta` 包含 `owner_id TEXT`。
- [ ] 历史项目缺少 `owner_id` 列时，verify 能报告 `missing_owner_column`。
- [ ] 历史项目 `owner_id` 为空时，verify 能报告 `missing_owner`。
- [ ] `owner_id` 指向不存在用户时，verify 能报告 `orphaned_owner`。
- [ ] 内部系统项目不会被误计入项目归属迁移扫描。

## 2. 新建项目 owner_id 验收

- [ ] 有效 `shanhai_session` Cookie 创建项目时，`owner_id` 等于当前用户 `user_id`。
- [ ] 请求体传入 `owner_id` 时返回 `PROJECT_OWNER_FORBIDDEN`，不能覆盖服务端 owner。
- [ ] 没有有效 Cookie 且没有合法 fallback owner 时，创建失败。
- [ ] 创建失败时不产生项目目录或半成品 `project.db`。

## 3. Fallback Owner 验收

- [ ] `PROJECT_CREATION_DEFAULT_OWNER_USER_ID` 指向存在且 active 的用户。
- [ ] 旧 `BACKEND_API_TOKEN` 兼容路径创建项目时，`owner_id` 等于 fallback owner。
- [ ] fallback owner 不存在时，创建失败并返回 `PROJECT_OWNER_REQUIRED`。
- [ ] fallback owner 被禁用时，创建失败并返回 `PROJECT_OWNER_REQUIRED`。
- [ ] 已配置 fallback owner 但未配置 `BACKEND_API_TOKEN` 时，无 Cookie 创建失败并且不产生项目目录。
- [ ] 已配置 `BACKEND_API_TOKEN` 时，缺失 Bearer header 返回 `UNAUTHORIZED`。
- [ ] 已配置 `BACKEND_API_TOKEN` 时，错误 Bearer token 返回 `FORBIDDEN`。

## 4. CLI Dry-Run 验收

- [ ] `verify-project-ownership` 只读扫描，不修改任何 `project.db`。
- [ ] `verify-project-ownership --json` 输出可被部署脚本解析。
- [ ] `assign-legacy-projects --owner-email <email>` 不带 `--apply` 时 `written_count=0`。
- [ ] `assign-legacy-projects --owner-user-id <user_id>` 不带 `--apply` 时 `written_count=0`。
- [ ] `assign-legacy-projects --mapping-file <file>` 不带 `--apply` 时 `written_count=0`。
- [ ] Dry-run 输出包含 `planned_count`、`skipped_existing_owner_count`、`failed_count` 和 `errors`。

## 5. CLI Apply 验收

- [ ] `assign-legacy-projects --owner-email <email> --apply` 能为缺 owner 项目写入 owner。
- [ ] `assign-legacy-projects --owner-user-id <user_id> --apply` 能为缺 owner 项目写入 owner。
- [ ] `assign-legacy-projects --mapping-file <file> --apply` 能按项目分别写入 owner。
- [ ] 缺少 `owner_id` 列的历史项目会被幂等增加 `owner_id TEXT`。
- [ ] 已有 owner 的项目默认跳过，不覆盖。
- [ ] 重复执行 apply 保持幂等，不产生额外写入。

## 6. Preflight 0 写入验收

- [ ] owner email 不存在时，`--apply` 返回失败且 `written_count=0`。
- [ ] owner user id 不存在时，`--apply` 返回失败且 `written_count=0`。
- [ ] mapping file 不是合法 JSON object 时，`--apply` 返回失败且 `written_count=0`。
- [ ] mapping file 中有不存在的 `project_id` 时，`--apply` 返回失败且 `written_count=0`。
- [ ] mapping file 中有不存在的 owner 时，`--apply` 返回失败且 `written_count=0`。
- [ ] mapping entry 同时指定 `owner_email` 和 `owner_user_id` 时，`--apply` 返回失败且 `written_count=0`。

## 7. Readiness 验收

- [ ] `/readiness` 返回 `project_ownership`。
- [ ] Phase B 中 `/readiness` 保持非阻断，不因缺 owner 直接让整体服务不可用。
- [ ] `project_ownership.ready_for_phase_c=false` 能明确暴露缺口。
- [ ] `missing_owner_projects` 能统计缺列和空 owner 项目。
- [ ] `orphaned_owner_projects` 能统计 owner 指向不存在用户的项目。
- [ ] Phase C 前置门禁为：`missing_owner_projects=0` 且 `orphaned_owner_projects=0`。

## 8. 全量测试验收

- [ ] `python -m pytest apps/api/tests/test_project_ownership_migration.py -q`
- [ ] `python -m pytest apps/api/tests -q`
- [ ] `git diff --check`
- [ ] 如果全量测试失败，失败原因必须归因清楚，并确认是否与 Phase B 改动相关。
- [ ] PR 描述必须记录实际测试数量、失败数量和阻塞原因。

## 9. 明确未做 Phase C 授权

- [ ] 未实现 `require_project_access`。
- [ ] 未保护 `/projects/{project_id}` 及派生业务接口。
- [ ] 未保护 `video-workflow` 接口。
- [ ] 未修改 Next.js 代理。
- [ ] 未修改前端登录页。
- [ ] 未删除 API 模式下的旧前端身份逻辑。
- [ ] 未实现 `project_members`。
- [ ] 未实现项目共享。
- [ ] 未新增创作会话、版本链、时间线、多镜头。
- [ ] 未修改视频工作台 UI。

## 10. Review 结论模板

```text
Phase B / B.1 Review:

- Schema: pass / fail
- 新项目 owner 写入: pass / fail
- fallback owner: pass / fail
- CLI dry-run: pass / fail
- CLI apply: pass / fail
- preflight 0 写入: pass / fail
- readiness: pass / fail
- 测试: pass / fail / blocked
- Phase C 越界检查: pass / fail

结论：
- 可以合并，等待 Owner 最终确认
- 或需要修复后复审
```
