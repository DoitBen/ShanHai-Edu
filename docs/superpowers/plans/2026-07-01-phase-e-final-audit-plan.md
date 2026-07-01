# Phase E Final Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Phase E security validation and final audit documentation for the auth/RBAC/video workbench release gate.

**Architecture:** Phase E does not add product capability. It validates the completed Phase A-D security boundary through two distinct browser gates: mocked API-mode Playwright coverage for frontend behavior and a real FastAPI + Next full-stack smoke for the minimum session/RBAC/CSRF path. It also adds contract checks, release-readiness documentation, and a final audit report. Any blocker fix is limited to P0/P1 regressions discovered by the Phase E gates.

**Tech Stack:** FastAPI, SQLite auth/project storage, Next.js 16, React 19, TypeScript, Bun, Playwright.

---

## Current Baseline

- Repository: `DOIT-Ben/ShanHai-Edu`
- Branch to create/use: `feat/final-e2e-security-audit`
- Baseline: `main@10673bc1843a60dbb9ff6aa6d15a04f8fd9423b6`
- Included upstream phases:
  - PR #28: Phase A auth foundation
  - PR #30: Phase B project ownership migration
  - PR #31: Phase C backend object access control and RBAC cleanup
  - PR #32: Phase D frontend real session proxy and CSRF wiring

## Phase E Objective

Phase E must validate the API-mode security boundary in two layers:

1. Mock API-mode browser E2E: uses Playwright request mocks to prove frontend session recovery, role visibility, CSRF header wiring, and video-workbench no-access UX.
2. Real FastAPI + Next full-stack smoke: uses no Playwright route mocks and proves a minimal browser `fetch` path through `/api/backend/*`, Next proxy, FastAPI, `auth.db`, and `project.db`.

The combined gates must show:

- Real session recovery, login, logout, and CSRF are exercised by E2E tests.
- Teacher A cannot enumerate, open, operate, preview, download, or cleanup Teacher B project resources.
- Admin can see authorized cross-project data where the backend allows it.
- Video workbench unsafe requests carry CSRF and use the real session path.
- Demo mode remains isolated and does not become security evidence.

## Final Audit Objective

The final audit must summarize whether the auth/RBAC/video-workbench release gate is ready for independent review and merge. It must separate:

- Passed P0/P1 gates with evidence.
- Remaining known risks.
- P2/P3 backlog items that are explicitly not implemented in Phase E.
- Deployment prerequisites and rollback checks.
- Final conclusion as exactly one of `PASS`, `PASS_WITH_RISKS`, or `FAIL`.

Because the real full-stack smoke is intentionally a minimum path rather than an exhaustive production provider smoke, the expected Phase E conclusion is `PASS_WITH_RISKS` when all gates pass.

## C0-C6 Commit Boundaries

### C0: Execution Plan

Commit message:

```text
docs: add phase e final audit execution plan
```

Allowed modification scope:

- Add this execution plan.
- No code, tests, workflow, product UI, backend RBAC, proxy, or video state-machine changes.

Verification command:

```powershell
git diff --check
```

Acceptance:

- Plan records baseline SHA, Phase E goal, final audit goal, C0-C6 boundaries, validation commands, forbidden scope, and final PR acceptance standard.

### C1: E2E Test Infrastructure

Commit message:

```text
test: add api-mode e2e auth harness
```

Allowed modification scope:

- Add or modify Playwright test helpers under `apps/web/e2e/`.
- Add reusable mocked API-mode auth/project/RBAC harness code.
- Add fixtures only when needed for browser tests.
- No product UI, store, API client, backend RBAC, or video state machine changes.

Verification command:

```powershell
cd apps/web
bun run test:e2e -- --workers=1
git diff --check
```

Acceptance:

- E2E helpers can model unauthenticated, teacher A, teacher B, and admin sessions for mocked API-mode browser coverage.
- Helpers can assert browser requests go through `/api/backend`.
- Helpers do not store session token or CSRF token in localStorage/sessionStorage.

### C2: Real Login and RBAC E2E

Commit message:

```text
test: cover real session rbac e2e
```

Allowed modification scope:

- Add Playwright coverage for real-session browser behavior.
- Add contract tests only if needed to lock role visibility or API-mode identity behavior.
- No backend authorization rule changes unless a P0 blocker is found and deferred to C6.

Verification command:

```powershell
cd apps/web
bun run test:e2e -- --workers=1
bun run test:contracts
git diff --check
```

Acceptance:

- Unauthenticated API-mode browser starts on the login screen.
- Teacher sees only teacher-owned projects in API-mode project list.
- Teacher A guessing Teacher B project receives a user-facing 404/no-access state.
- Teacher role does not show admin navigation.
- Admin role shows admin navigation and can see all mocked projects.
- This gate is not a substitute for real FastAPI + Next full-stack smoke.

### C3: CSRF and Video Workbench Real Session E2E

Commit message:

```text
test: cover csrf and video workbench real session e2e
```

Allowed modification scope:

- Add Playwright coverage for video-workbench API-mode unsafe requests.
- Add assertions for CSRF on `POST`/`PUT`/`PATCH`/`DELETE`.
- Add cross-project denial coverage for video-workflow assets, runs, content, download, and cleanup using mocked backend responses.
- Do not add new video models, modes, durations, ratios, generation counts, state-machine transitions, timelines, or multi-shot UI.

Verification command:

```powershell
cd apps/web
bun run test:e2e -- --workers=1
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
git diff --check
```

Acceptance:

- Video workbench can load through the mocked API-mode session harness.
- Unsafe video-workflow requests include `X-CSRF-Token`.
- Cross-user video-workflow resource guesses resolve to 404/no-access behavior.
- Demo-mode gate still passes and remains separate from API-mode security evidence.
- Cross-project video-workflow checks here are mocked frontend E2E; the separate real full-stack smoke must cover at least project manifest or video-workflow denial through FastAPI.

### C4: Release Readiness Documentation

Commit message:

```text
docs: add auth rbac release readiness checklist
```

Allowed modification scope:

- Add `docs/operations/release-readiness-auth-rbac.md`.
- Document deployment prerequisites, environment variables, migration/readiness checks, E2E gate commands, rollback, and operational verification.
- Do not add smoke scripts, observability panels, workflow changes, or implementation code.

Verification command:

```powershell
git diff --check
```

Acceptance:

- Checklist clearly separates required P0/P1 release gates from deferred P2/P3 work.
- Checklist names auth/session/CSRF/project ownership/RBAC/video-workbench gates.
- Rollback guidance references storage/auth DB/project DB backup and restore.

### C5: Final Audit Documentation

Commit message:

```text
docs: add final auth rbac video workbench audit
```

Allowed modification scope:

- Add `docs/audits/2026-07-01-final-auth-rbac-video-workbench-audit.md`.
- Summarize Phase A-D evidence, Phase E E2E evidence, final conclusion, known risks, and audit backlog.
- P2/P3 findings must be recorded as backlog, not implemented.

Verification command:

```powershell
git diff --check
```

Acceptance:

- Audit conclusion states whether final merge is recommended.
- Audit includes explicit evidence references and command results.
- Audit does not contain secrets, provider URLs, personal paths, tokens, cookies, or real user data.

### C6: P0/P1 Blocker Fix Only

Commit message:

```text
fix: address final audit blocker
```

Allowed modification scope:

- Only minimal code/test changes required to fix a blocker discovered by C1-C5 or final verification.
- Add a failing regression test first.
- No feature expansion.
- If no blocker is found, skip C6 and document "not needed" in the PR description.

Verification command:

```powershell
python -m pytest apps/api/tests/test_auth_phase_a.py apps/api/tests/test_project_access_control.py apps/api/tests/test_project_ownership_migration.py -q
cd apps/web
bun run test:contracts
bunx tsc --noEmit --incremental false
bun run lint
bun run build
bun run test:e2e -- e2e/api-mode-auth-harness.spec.ts e2e/real-session-rbac.spec.ts e2e/video-workbench-security.spec.ts --workers=1
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
bun run test:e2e -- --config=playwright.fullstack.config.ts e2e/real-backend-session-smoke.spec.ts --workers=1
bun run scan:client-secrets
git diff --check
```

Acceptance:

- The blocker is fixed by the smallest aligned change.
- The failing test fails before the fix and passes after the fix.
- No forbidden feature scope is touched.
- Review blocker follow-ups may add CI gates, real full-stack smoke infrastructure, or documentation corrections when they directly close a P0/P1 release-audit gap.

## Explicitly Forbidden Scope

- Do not implement GPT-style creative sessions.
- Do not implement version graph, timeline, multi-shot editing, first/last-frame mode, or Extend mode.
- Do not implement `project_members`.
- Do not implement project sharing.
- Do not change the video generation state machine.
- Do not refactor UI.
- Do not add image/video workbench product features.
- Do not add models, ratios, durations, or generation counts.
- Do not implement P2/P3 backlog items; record them in the final audit only.

## Final PR Acceptance Standard

The Draft PR titled `[phase-e-final] e2e security release readiness and final audit` is ready for independent review only when:

- C0-C5 commits exist with the requested boundaries and messages.
- C6 is either absent because no blocker was found or present only for a documented P0/P1 blocker.
- Required backend targeted tests pass or any local fixture limitation is explicitly recorded.
- Required frontend contracts, typecheck, lint, build, mocked API-mode E2E, demo-mode video-workbench E2E, real FastAPI + Next full-stack smoke, and client secret scan pass.
- CI workflow runs the mocked API-mode E2E specs and the real full-stack smoke; demo-mode video-workbench remains a separate compatibility gate.
- `git diff --check` passes.
- The release readiness checklist exists.
- The final audit document exists and uses `PASS`, `PASS_WITH_RISKS`, or `FAIL` with coverage boundaries.
- The PR description is organized by C0-C6 and includes test results, final audit conclusion, remaining risks, and merge recommendation.
- The PR remains Draft and is not self-merged.
