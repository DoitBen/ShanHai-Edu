# Auth/RBAC Release Readiness Checklist

> Scope: Phase A-D auth, project ownership, backend object authorization, frontend real session proxy, and Phase E E2E security gates.
>
> Baseline for Phase E: `main@10673bc1843a60dbb9ff6aa6d15a04f8fd9423b6`
>
> This document is an operations checklist. It does not introduce product features.

## 1. Release Boundary

This release may ship only the completed security boundary:

- FastAPI users, Argon2id passwords, opaque server sessions, HttpOnly Cookie, CSRF, login rate limiting, logout/session revocation, and auth audit events.
- `project_meta.owner_id` and explicit legacy project ownership migration.
- Backend RBAC and project object-level authorization.
- Next.js proxy forwarding real browser session headers without injecting global Bearer tokens.
- API-mode frontend session recovery via `/auth/me`, login via `/auth/login`, logout via `/auth/logout`, and in-memory CSRF handling.
- Project video workbench access through the real session path.
- Phase E browser validation split into mocked API-mode E2E and real FastAPI + Next full-stack smoke.

The release must not claim support for:

- `project_members` or project sharing.
- GPT-style creative sessions, version graph, timeline, multi-shot editing, first/last-frame mode, or Extend mode.
- New media models, ratios, durations, or generation counts.
- Multi-container/multi-worker write safety beyond documented single-instance boundaries.

## 2. Required Environment Configuration

### FastAPI

- [ ] `STORAGE_ROOT` points to the intended production or staging storage directory.
- [ ] `AUTH_COOKIE_SECURE=true` in HTTPS production.
- [ ] Allowed Origin config contains exact frontend origins only; no wildcard origin is allowed for credentialed requests.
- [ ] `AUTH_SESSION_TTL_SECONDS` is set or accepted at the default 12-hour absolute session TTL.
- [ ] `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS` and `AUTH_LOGIN_RATE_LIMIT_MAX_FAILURES` are reviewed for the deployment network.
- [ ] `PROJECT_CREATION_DEFAULT_OWNER_USER_ID` is configured only if the legacy token create-project path is still needed.
- [ ] If legacy project creation is needed, `BACKEND_API_TOKEN` is configured and stored only server-side.
- [ ] Provider tokens remain server-side only and are not exposed to the frontend.

### Next.js

- [ ] `BACKEND_API_BASE_URL` points to the FastAPI deployment.
- [ ] `NEXT_PUBLIC_DEMO_MODE=false` for production.
- [ ] The Next proxy does not read or inject `BACKEND_API_TOKEN`.
- [ ] Client requests through `/api/backend/*` forward `Cookie`, `Origin`, `X-CSRF-Token`, `Content-Type`, and accept binary/`Set-Cookie` responses.
- [ ] Client-side auth state does not persist session tokens or CSRF tokens to `localStorage` or `sessionStorage`.

## 3. Database and Storage Readiness

- [ ] `auth.db` exists under `STORAGE_ROOT`.
- [ ] At least one active admin user exists.
- [ ] Intended teacher users exist and are active.
- [ ] No password is stored in plaintext.
- [ ] No session token or CSRF token is stored in plaintext.
- [ ] Every production project DB has `project_meta.owner_id`.
- [ ] No project has a blank `owner_id`.
- [ ] No project has an orphan `owner_id` pointing to a missing user.
- [ ] Storage backup exists before release.

Run before release:

```powershell
python -m apps.api.app.auth_cli --storage-root <storage> list-users
python -m apps.api.app.auth_cli --storage-root <storage> verify-project-ownership --json
```

Phase C/D/E release gate:

```text
missing_owner_projects = 0
orphaned_owner_projects = 0
ready_for_phase_c = true
```

## 4. Migration Checklist

- [ ] Backup `auth.db` and all `storage\projects\*\project.db` files.
- [ ] Run `verify-project-ownership --json` and archive the output.
- [ ] Run `assign-legacy-projects` dry-run with `--owner-email`, `--owner-user-id`, or `--mapping-file`.
- [ ] Confirm dry-run reports the expected `planned_count` and `written_count=0`.
- [ ] Review mapping file manually if used.
- [ ] Run `assign-legacy-projects --apply`.
- [ ] Re-run `verify-project-ownership --json`.
- [ ] Confirm no missing or orphaned owner remains.

Mapping file example:

```json
{
  "project_teacher_a": {
    "owner_email": "teacher.a@example.test"
  },
  "project_teacher_b": {
    "owner_user_id": "user_teacher_b"
  }
}
```

## 5. Security Gate Checklist

### Authentication

- [ ] Correct credentials create a server session and set `shanhai_session`.
- [ ] Cookie is `HttpOnly`, `Path=/`, `SameSite=Lax`, and production `Secure=true`.
- [ ] `/auth/me` restores a user and returns a fresh usable CSRF token.
- [ ] `/auth/logout` revokes the current session and clears Cookie.
- [ ] Expired, revoked, disabled-user sessions are rejected.
- [ ] Login failures do not reveal whether the user exists.
- [ ] Login rate limiting returns `AUTH_RATE_LIMITED`.
- [ ] Auth audit events do not contain passwords, raw tokens, raw CSRF, cookies, provider keys, or raw IP addresses.

### RBAC and Object Access

- [ ] Unauthenticated business requests return `401 AUTH_REQUIRED`.
- [ ] Teacher can list only owned projects.
- [ ] Teacher cannot open another teacher project by guessed `project_id`.
- [ ] Teacher cannot access another project nodes, tasks, assets, files, exports, final video, video workflow runs, content, downloads, or cleanup.
- [ ] Cross-project denial returns 404-style responses and does not reveal resource existence.
- [ ] Admin can access all owned projects and admin-only global interfaces.
- [ ] Teacher cannot access admin-only interfaces.
- [ ] Client-provided role, owner, or Authorization header cannot elevate privileges.

### Next Proxy and Frontend

- [ ] Proxy drops browser-supplied `Authorization`.
- [ ] Proxy does not inject global Bearer tokens for browser users.
- [ ] Proxy forwards Cookie and CSRF headers.
- [ ] Proxy forwards backend `Set-Cookie`.
- [ ] API mode does not read or write `shanhai_auth`.
- [ ] Demo mode remains isolated and is not used as release security evidence.
- [ ] Teacher UI hides admin entry points.
- [ ] Admin UI shows admin entry points.

### Video Workbench

- [ ] Project video workbench loads through a valid session.
- [ ] Video workbench unsafe requests include `X-CSRF-Token`.
- [ ] Cross-user video workflow asset/run/content/download/cleanup requests return 404.
- [ ] Mocked API-mode browser E2E covers frontend video-workbench session, CSRF, and denial behavior.
- [ ] Real FastAPI + Next full-stack smoke covers the minimum `/api/backend/*` path through Next proxy, FastAPI, `auth.db`, and `project.db`.
- [ ] Demo-mode video workbench still passes its compatibility gate, but is not treated as security proof.

## 6. Required Verification Commands

Backend targeted gate:

```powershell
python -m pytest apps/api/tests/test_auth_phase_a.py apps/api/tests/test_project_access_control.py apps/api/tests/test_project_ownership_migration.py -q
```

Backend full gate when local fixtures are available:

```powershell
python -m pytest apps/api/tests -q
```

Frontend gate:

```powershell
cd apps/web
bun run test:contracts
bunx tsc --noEmit --incremental false
bun run lint
bun run build
bun run test:e2e -- e2e/api-mode-auth-harness.spec.ts e2e/real-session-rbac.spec.ts e2e/video-workbench-security.spec.ts --workers=1
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
bun run test:e2e -- --config=playwright.fullstack.config.ts e2e/real-backend-session-smoke.spec.ts --workers=1
bun run scan:client-secrets
```

Gate meaning:

- Mocked API-mode E2E proves frontend session restoration, role visibility, CSRF header wiring, and video-workbench denial UX with controlled backend responses.
- Real full-stack smoke proves the minimum browser-to-Next-to-FastAPI-to-SQLite path and must not use `page.route("**/api/backend/**")`.
- Demo-mode video workbench E2E is a compatibility gate only, not release security evidence.

Repository gate:

```powershell
git diff --check
```

## 7. Rollback Plan

Rollback must restore both code and storage state. Do not roll back by clearing `owner_id`, disabling auth, or re-enabling anonymous/token-only project access.

1. Stop the affected deployment.
2. Restore the previous application image or commit.
3. Restore `auth.db` from the pre-release backup if auth data was migrated or modified.
4. Restore affected `storage\projects\*\project.db` files from the pre-release backup if project ownership migration changed them.
5. Restart one API instance first and run:

```powershell
python -m apps.api.app.auth_cli --storage-root <storage> verify-project-ownership --json
```

6. Verify:
   - Login works for admin.
   - Teacher can see only owned projects.
   - Cross-user guessed project returns 404.
   - Video workbench can load owned project data.

## 8. Known Deployment Limits

- Current local SQLite/storage deployment assumes a single API writer unless external locking/storage architecture is introduced later.
- Legacy `POST /projects` token compatibility may remain only for controlled server-side callers and cannot be used to read or operate project resources.
- Project sharing is not supported.
- Demo mode is for local demonstration only and must stay disabled in production.

## 9. Release Decision Template

```text
Auth/RBAC Release Readiness:

- Baseline SHA:
- Storage backup captured: yes/no
- verify-project-ownership: pass/fail
- Backend targeted tests: pass/fail
- Backend full tests: pass/fail/fixture-blocked
- Frontend contracts/type/lint/build: pass/fail
- Mocked API-mode E2E: pass/fail
- Real FastAPI + Next full-stack smoke: pass/fail
- Demo-mode video-workbench gate: pass/fail
- Secret scan: pass/fail
- git diff --check: pass/fail
- Remaining P0/P1 blockers: none/list
- P2/P3 backlog recorded: yes/no

Decision:
- PASS / PASS_WITH_RISKS / FAIL
- recommend merge / do not merge
```
