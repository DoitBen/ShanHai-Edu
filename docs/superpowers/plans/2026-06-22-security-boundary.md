# Security Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 `docs/architecture-optimization-v2.md` 第 5 周安全边界收口，并先修复本阶段读取到的开放 Issue #1/#2。

**Architecture:** 保持 provider key 只存在于后端 Settings/provider 实例中；前端仅请求自家 API，不再依赖公开 token。RuleExecutor 对 PPTX 成品可见层做结构化审计，Store 不暴露直接 approve 绕过入口。

**Tech Stack:** FastAPI、pytest、python-pptx、Next.js/TypeScript。

---

### Task 1: 修复阶段开放 Issue

**Files:**
- Modify: `apps/api/app/store.py`
- Modify: `apps/api/app/rule_executor.py`
- Modify: `apps/api/app/flywheel.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/services.py`
- Modify: `apps/api/tests/test_rule_executor_contract.py`
- Modify: `apps/api/tests/test_flywheel_contract.py`
- Create: `apps/api/tests/test_architecture_guards.py`
- Modify: `apps/web/src/components/screens/ProjectWorkspaceScreen.tsx`

- [x] **Issue #2: 移除 Store 直接 approve 绕过入口**

删除 `ProjectStore.approve_node()` 公共方法，保留 API approve 主路径为 `WorkflowService -> RuleExecutor -> StateEngine -> Flywheel`。

- [x] **Issue #1: R026 扫描真实 PPTX 可见层**

使用 `python-pptx` 读取项目目录内 `pptx_path` 对应文件，扫描 slide shape text；继续排除 `notes_text`。

- [x] **Issue #3: Flywheel 反馈入口拒绝占位伪反馈**

后端拒绝空 payload、模板/占位文案和缺少真实 comment 的 delivery feedback；前端反馈按钮改为打开输入弹窗，只有用户填写真实内容后才提交。

### Task 2: 安全边界测试

**Files:**
- Create: `apps/api/tests/test_security_boundary.py`
- Modify: `apps/web/src/lib/api-client.ts`

- [x] **前端公开 token 守卫**

测试禁止 `NEXT_PUBLIC_*KEY/TOKEN/SECRET` 出现在前端源码。

- [x] **provider 错误脱敏守卫**

测试 `sanitize_provider_excerpt()` 会脱敏 Authorization、api_key、token 和常见 provider key 形态。

- [x] **env example 占位守卫**

测试 `apps/api/.env.example` 中 key/token/secret 类变量值只允许占位。

### Task 3: 验证

- [x] `python -m pytest apps\api\tests\test_architecture_guards.py apps\api\tests\test_rule_executor_contract.py apps\api\tests\test_flywheel_contract.py apps\api\tests\test_security_boundary.py -q`
- [x] `python -m pytest apps\api\tests -q`
- [x] `cd apps\web; bunx tsc --noEmit --pretty false`
- [x] `cd apps\web; bun run lint`
- [x] `cd apps\web; bun run build`
- [x] 构建后 grep 前端生产产物不含公开 key/token/secret 类环境变量名
