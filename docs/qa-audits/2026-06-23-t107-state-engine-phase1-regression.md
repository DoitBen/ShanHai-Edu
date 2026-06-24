# T107 StateEngine Phase 1 专项回归报告

## 结论

【通过】StateEngine Phase 1 专项回归通过，可交首席系统架构师继续复核。

本轮只验证新增 StateEngine 状态流、R010 依赖门禁归属、旧阻塞点和前端真实 API 诊断展示；未执行真实 provider 图片/视频/PPT 全链路。

## 环境

- API：`http://127.0.0.1:8107`
- Web：`http://127.0.0.1:3107`
- Storage：`storage-t107-state-engine-phase1`
- Provider：`PROVIDER_MODE=fake`
- Video/Image/TTS：`placeholder`
- Web 模式：真实 API 模式，代理到 `BACKEND_API_BASE_URL=http://127.0.0.1:8107`
- 证据目录：`docs\qa-audits\t107-state-engine-phase1-evidence\20260623-113852\`

## API 证据

核心证据文件：

- `summary.json`
- `health.json`
- `initial-manifest.json`
- `blocked-lesson-plan-generate.json`
- `blocked-lesson-plan-transitions.json`
- `rule-result-r010-after-block.json`
- `textbook-parse-generate.json`
- `textbook-parse-approve.json`
- `lesson-plan-generate-after-upstream-approved.json`
- `lesson-plan-edit.json`
- `lesson-plan-node-after-edit.json`
- `lesson-plan-approve.json`
- `lesson-plan-transitions.json`
- `skip-manifest.json`
- `skipped-node-generate.json`
- `skipped-upstream-ppt-plan-generate.json`
- `rules-coverage.json`
- `rule-warning-response.json`
- `rule-hard-block-response.json`

`summary.json` 检查项全部为 `true`：

- `/health` 返回 200。
- 创建项目后 `project_config=approved`。
- `lesson_plan/generate` 在 `textbook_parse` 未 approved 时返回 `409 / UPSTREAM_NOT_APPROVED`。
- 依赖阻断写入 `state_transition_log.trigger=dependency_gate_blocked`。
- R010 不再写入 `rule_result_log`。
- `textbook_parse` approved 后，`lesson_plan/generate` 返回 200 且状态为 `needs_review`。
- `lesson_plan/edit` 后状态为 `needs_review`，transition 包含 `user_edit` 和 `user_save_edit`。
- `lesson_plan/approve` 后状态为 `approved`，transition 包含 `user_approve`。
- `needs_intro_video=false` 的 skipped 分支允许非视频下游继续生成。
- 对 skipped 节点自身 generate 返回 `409 / NODE_SKIPPED`。
- 规则 warning 返回 `409 / RULE_WARNING`。
- 规则 hard block 返回 `400 / RULE_VIOLATION_R004`。

关键项目 ID：

- StateEngine 主状态流项目：`proj_331820f8f59c`
- skip 依赖链项目：`proj_a82ed4835b4c`
- warning 项目：`proj_e3a3e2b7cbae`
- hard block 项目：`proj_2b2b0da459a9`
- 浏览器诊断项目：`proj_2f17be91a802`

## 浏览器证据

证据文件：

- `browser-workspace.png`
- `browser-workspace-snapshot.txt`
- `browser-console.json`
- `browser-diagnostics-project.json`

浏览器验证结果：

- 真实 API 模式可登录并读取后端项目列表。
- 工作区可打开 `T107-Browser-Diagnostics`。
- `PPT 总装方案` 节点列表显示“上游变更后需重审”。
- 节点详情展示 `StateEngine 状态`、`approved → needs_review`、`cascade_invalidate`、重审详情。
- `公开课教案` 节点详情展示 `drafted → needs_review`、`user_save_edit` 和状态迁移详情。
- 对 `导入设计选择集` 触发生成时，前端展示“上游未确认：请先确认依赖节点后再继续”，toast 保留 `UPSTREAM_NOT_APPROVED`。
- `browser-console.json` 为 `[]`，无应用级 error/warn。

## 回归命令

后端：

```powershell
python -m pytest apps\api\tests -q
```

结果：`201 passed, 2 xfailed in 67.78s`

前端：

```powershell
cd apps\web
bun src/lib/api-mappers-contract.test.ts
bun src/lib/admin-rules-contract.test.ts
bun src/lib/api-proxy-contract.test.ts
bun src/lib/api-warning-override-contract.test.ts
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

结果：全部退出码 0；`bun run build` 成功完成 Next.js 生产构建。

## 缺陷与阻塞项

无阻塞项。

未发现 T107 范围内新增缺陷。

## 上线前再修

- StateEngine Phase 2 仍建议继续收口异步任务、provider failed/blocked 路径和 `VideoOrchestrator` 直接写版本路径。
- 本轮浏览器只做真实 API 模式最小核验，未覆盖多浏览器、多分辨率和真实 provider 链路。
