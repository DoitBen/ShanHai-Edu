# Final Auth/RBAC/Video Workbench Audit

> Date: 2026-07-01
>
> Repository: `DOIT-Ben/ShanHai-Edu`
>
> Phase E branch: `feat/final-e2e-security-audit`
>
> Baseline: `main@10673bc1843a60dbb9ff6aa6d15a04f8fd9423b6`
>
> Scope: Phase A-D auth/RBAC implementation plus Phase E mocked API-mode browser E2E and real FastAPI + Next full-stack smoke release gates.

## 1. Executive Conclusion

Final audit result: `PASS_WITH_RISKS`.

Recommendation: proceed to Draft PR and independent review after final CI verification.

The current branch completes the remaining release-gate work for the auth/RBAC/video-workbench security boundary:

- It adds mocked API-mode Playwright security coverage for frontend session recovery, login/logout UI behavior, teacher/admin visibility, cross-user project denial UX, CSRF header wiring, and video-workflow resource denial handling.
- It adds a real FastAPI + Next full-stack smoke that uses no Playwright route mocks and proves the minimum browser `/api/backend/*` path through Next proxy, FastAPI, `auth.db`, and `project.db`.
- It adds release readiness documentation for deployment, verification, and rollback.
- It records remaining release risks and P2/P3 backlog without implementing out-of-scope media features.

The result is `PASS_WITH_RISKS`, not `PASS`, because the real full-stack smoke intentionally covers the minimum session/project/video-workflow path and does not replace a real provider smoke, production deployment verification, or the full backend suite when local PDF fixtures are unavailable.

No new media generation feature, model, duration, ratio, project sharing, `project_members`, creative session, timeline, version graph, or multi-shot behavior is introduced.

## 2. Audit Inputs

Primary sources:

- `docs/superpowers/specs/2026-06-30-real-auth-project-rbac-design.md`
- `docs/audits/2026-06-30-media-workbench-auth-roadmap-v3.md`
- `docs/operations/project-ownership-migration.md`
- `docs/operations/project-ownership-phase-b-checklist.md`
- PR #28 description: Phase A auth foundation
- PR #30 description: Phase B project ownership migration
- PR #31 description: Phase C backend object access control and RBAC cleanup
- PR #32 description: Phase D frontend real session proxy and CSRF wiring
- Phase E local verification commands listed below

## 3. Phase Evidence Summary

| Phase | Evidence | Audit result |
| --- | --- | --- |
| Phase A Auth foundation | PR #28 merged; backend auth tests retained | PASS |
| Phase B Project ownership | PR #30 merged; ownership migration docs retained | PASS |
| Phase C Backend object RBAC | PR #31 merged; `require_current_user`, `require_role`, `require_project_access` covered by tests | PASS |
| Phase D Frontend real session proxy | PR #32 merged; proxy and frontend contract tests retained | PASS |
| Phase E mocked browser security gate | New API-mode Playwright tests in this branch using request mocks | PASS pending final CI |
| Phase E real full-stack smoke | New `real-backend-session-smoke.spec.ts` through Next proxy and FastAPI temporary SQLite storage | PASS_WITH_RISKS pending final CI |

## 4. P0/P1 Security Gates

### 4.1 Authentication and Session

Result: pass for mocked API-mode browser coverage; real session path is also covered by the full-stack smoke in section 4.7.

Evidence:

- API-mode frontend starts with `/auth/me`.
- Unauthenticated API-mode browser sees the real login screen.
- API-mode login uses `/auth/login`.
- API-mode logout uses `/auth/logout`.
- CSRF token is kept in memory and is not written to browser storage.
- `shanhai_auth` is not used in API mode.

Local mocked API-mode E2E evidence:

```text
bun run test:e2e -- e2e/api-mode-auth-harness.spec.ts e2e/real-session-rbac.spec.ts e2e/video-workbench-security.spec.ts --workers=1
8 passed
```

### 4.2 Teacher/Admin RBAC

Result: pass for mocked API-mode browser coverage and backend Phase C targeted tests.

Evidence:

- Teacher A sees only Teacher A project.
- Teacher A does not see Teacher B project in the project list.
- Teacher role does not show admin entry points.
- Admin sees both projects and admin entry points.
- Unauthenticated users remain on the login screen.

Covered by:

- `apps/web/e2e/real-session-rbac.spec.ts`

### 4.3 Object-Level Project Access

Result: pass for mocked Phase E browser gate and targeted backend tests; real cross-project project-route denial is covered by the full-stack smoke in section 4.7.

Evidence:

- Teacher A guessing Teacher B `project_id` through `/api/backend/projects/{project_id}/manifest` receives 404 with `PROJECT_NOT_FOUND`.
- Sending a browser-controlled `Authorization` header does not grant access to another project in the API-mode E2E mock.
- Backend Phase C tests remain part of the required targeted backend gate.

Targeted backend evidence:

```text
python -m pytest apps/api/tests/test_auth_phase_a.py apps/api/tests/test_project_access_control.py apps/api/tests/test_project_ownership_migration.py -q
38 passed, 1 warning
```

### 4.4 CSRF

Result: pass for mocked video-workbench E2E and real full-stack project creation/cleanup smoke.

Evidence:

- Video-workflow unsafe request without `X-CSRF-Token` returns `403 CSRF_INVALID` in the API-mode E2E harness.
- Same request with the session CSRF token succeeds.
- Video-workbench API-mode tests assert unsafe requests carry CSRF.
- Real full-stack smoke verifies missing and wrong CSRF failures on `POST /projects` and a successful CSRF-protected video-workflow cleanup request.

Covered by:

- `apps/web/e2e/video-workbench-security.spec.ts`
- Existing `apps/web/e2e/video-workbench.spec.ts`

### 4.5 Video Workbench Resource Isolation

Result: pass for mocked video-workflow browser coverage; minimum real project-level denial is covered by section 4.7.

Evidence:

Teacher A cannot access Teacher B:

- `GET /projects/{project_id}/video-workflow`
- `GET /projects/{project_id}/video-workflow/assets/{asset_id}/content`
- `GET /projects/{project_id}/video-workflow/runs/{run_id}/content`
- `GET /projects/{project_id}/video-workflow/runs/{run_id}/download`
- `POST /projects/{project_id}/video-workflow/storage/cleanup`

All return 404-style `PROJECT_NOT_FOUND` in API-mode E2E.

### 4.6 Demo Mode Isolation

Result: pass.

Evidence:

```text
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
4 passed
```

Demo mode remains compatible but is not used as security proof.

### 4.7 Real FastAPI + Next Full-Stack Smoke

Result: pass with risks.

Evidence:

```text
bun run test:e2e -- --config=playwright.fullstack.config.ts e2e/real-backend-session-smoke.spec.ts --workers=1
1 passed
```

Coverage:

- Starts a temporary FastAPI instance with temporary SQLite storage.
- Seeds active teacher A, teacher B, and admin users in the real `auth.db`.
- Starts Next API mode with `BACKEND_API_BASE_URL` pointing at the temporary FastAPI instance.
- Uses browser `fetch` against `/api/backend/*`; the test does not call `page.route("**/api/backend/**")`.
- Verifies `/api/backend/auth/login` succeeds.
- Verifies `/api/backend/auth/me` restores session and returns a CSRF token.
- Verifies teacher A and teacher B can create owned projects with valid CSRF.
- Verifies teacher A sees only project A.
- Verifies teacher A receives 404 when opening teacher B `manifest` and `video-workflow`.
- Verifies admin sees both projects.
- Verifies missing and wrong CSRF fail for unsafe project creation.
- Verifies a correct CSRF-protected unsafe video-workflow cleanup request succeeds.

Boundary:

- This is a minimum full-stack smoke, not a full provider smoke.
- It does not submit real paid media provider tasks.
- It does not cover every project-derived endpoint; detailed route coverage remains in backend tests and mocked browser E2E.

## 5. Verification Results

Collected on the Phase E branch before Draft PR creation.

### Backend

Targeted gate:

```text
python -m pytest apps/api/tests/test_auth_phase_a.py apps/api/tests/test_project_access_control.py apps/api/tests/test_project_ownership_migration.py -q
38 passed, 1 warning
```

Full backend suite:

```text
python -m pytest apps/api/tests -q
not run in this local workspace
```

Reason:

- The local ignored PDF fixture directory is absent: `apps/api/tests/fixtures/textbook-parsing/renjiao-grade1-volume1-2024`.
- GitHub Actions remains the final full-suite gate where repository fixtures and CI environment are authoritative.

### Frontend

Contract tests:

```text
bun run test:contracts
passed
```

TypeScript:

```text
bunx tsc --noEmit --incremental false
passed after C6 blocker fix
```

Lint:

```text
bun run lint
passed
```

Build:

```text
bun run build
passed
```

API-mode E2E:

```text
bun run test:e2e -- e2e/api-mode-auth-harness.spec.ts e2e/real-session-rbac.spec.ts e2e/video-workbench-security.spec.ts --workers=1
8 passed
```

Demo-mode video workbench E2E:

```text
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
4 passed
```

Client secret scan:

```text
bun run scan:client-secrets
Client-visible secret scan passed.
```

Diff hygiene:

```text
git diff --check
passed
```

Real full-stack smoke:

```text
bun run test:e2e -- --config=playwright.fullstack.config.ts e2e/real-backend-session-smoke.spec.ts --workers=1
1 passed
```

## 6. C6 Blocker Note

During Final Audit verification, TypeScript found a test-only blocker in `apps/web/e2e/video-workbench-security.spec.ts`: an empty array inside `page.evaluate` inferred as `never[]`.

Resolution:

- Add an explicit result item type to the local E2E test array.
- No product code or backend security rule was changed.
- The fix is expected to be committed separately as:

```text
fix: address final audit blocker
```

## 7. Remaining Risks

P0/P1 risks:

- None identified in the current Phase E scope after the C6 test-only blocker fix.
- Final merge should still wait for GitHub Actions on the Draft PR.

Operational risks:

- Current SQLite/local storage deployment still assumes a single API writer unless a later architecture introduces external locking or object storage.
- Production security depends on correct `AUTH_COOKIE_SECURE`, exact Origin allowlist, and HTTPS deployment.
- Legacy `POST /projects` token compatibility can remain only for controlled server-side callers and cannot read or operate project resources.
- Full backend suite is not run locally when the ignored PDF fixture is absent; CI must be treated as the final full-suite authority.
- Real full-stack smoke covers the minimum session/project/video-workflow path only; it should not be represented as exhaustive production E2E coverage.

Product-scope risks:

- No `project_members` or project sharing.
- No GPT-style creative sessions.
- No version graph, timeline, multi-shot editing, first/last-frame mode, or Extend mode.
- No quota/billing/cost governance UI beyond existing high-cost confirmation gates.

## 8. P2/P3 Backlog

Do not implement these in Phase E:

- GPT-style image/video creative sessions.
- Unified generation result object and version graph.
- Semantic reference roles beyond current video-workbench scope.
- Multi-shot timeline, captions, voiceover, transitions, and final composition.
- Cloud object storage migration.
- Multi-container concurrency hardening.
- Admin user management UI.
- Project sharing and membership model.

## 9. Final Decision

Recommended next action:

1. Commit C5 Final Audit.
2. Commit C6 test-only blocker fix.
3. Run the final verification command set.
4. Push `feat/final-e2e-security-audit`.
5. Create Draft PR titled `[phase-e-final] e2e security release readiness and final audit`.
6. Wait for GitHub Actions and independent review.

Merge recommendation:

- Recommended only after the Draft PR GitHub Actions are green and the reviewer accepts the documented local PDF fixture limitation and `PASS_WITH_RISKS` coverage boundary.
