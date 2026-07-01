# Manual Acceptance Checklist

Use this checklist for human acceptance after CI is green. Record the environment, account roles, browser, and date before starting.

## Preflight

- [ ] The deployed commit matches the target SHA.
- [ ] Owner has reviewed the production deployment runbook before any production start.
- [ ] Owner has approved the production dry-run plan and isolated ports before any server-side dry-run.
- [ ] Owner has explicitly approved any real provider smoke that may incur cost.
- [ ] `NEXT_PUBLIC_DEMO_MODE=false` for real acceptance.
- [ ] FastAPI `STORAGE_ROOT` points to the intended environment.
- [ ] `AUTH_COOKIE_SECURE=true` when served over HTTPS.
- [ ] Origin allowlist contains only the expected frontend origins.
- [ ] Production backup paths and rollback package paths are recorded before smoke.
- [ ] At least one active admin and one active teacher exist.
- [ ] `verify-project-ownership` reports no missing or orphaned owner projects.

## Login and Session

- [ ] Unauthenticated users see the login screen.
- [ ] Valid teacher login succeeds.
- [ ] Valid admin login succeeds.
- [ ] `/auth/me` restores the user after page refresh.
- [ ] Logout clears the session and returns to login.
- [ ] Disabled or invalid users cannot login.
- [ ] No session token or CSRF token appears in `localStorage` or `sessionStorage`.

## Role Visibility

- [ ] Teacher sees teacher-facing navigation only.
- [ ] Teacher does not see admin-only entry points.
- [ ] Admin sees admin entry points.
- [ ] Demo role switching is not visible in API mode.

## Project Access

- [ ] Teacher A sees only Teacher A projects in the project list.
- [ ] Teacher B sees only Teacher B projects in the project list.
- [ ] Admin sees Teacher A and Teacher B projects.
- [ ] Teacher A opening Teacher B project URL returns a 404/no-access response.
- [ ] Client-supplied `Authorization` or role data does not grant access.

## Video Workbench

- [ ] Teacher can open an owned project video workbench.
- [ ] Video capabilities load through `/api/backend`.
- [ ] Reference assets list loads for an owned project.
- [ ] Reference image upload succeeds for a valid image.
- [ ] Invalid image upload is rejected with a controlled validation error.
- [ ] Reference image deletion succeeds for an owned project.
- [ ] Existing runs list loads for an owned project.
- [ ] Creating a video run succeeds for an owned project with valid inputs.
- [ ] Run polling and manual sync update status correctly.
- [ ] Provider `completed` without URL is recognizable as pending URL/download state.
- [ ] Pending URL timeout moves to a retryable state and allows retry.
- [ ] Completed output can be played and downloaded.
- [ ] Player/download actions work for owned completed outputs when fixture data exists.
- [ ] Demo-mode video workbench compatibility remains separate from real-session acceptance.

## Cross-User Video Security

- [ ] Teacher A cannot read Teacher B `/video-workflow`.
- [ ] Teacher A cannot access Teacher B video-workflow assets.
- [ ] Teacher A cannot read Teacher B video-workflow asset content.
- [ ] Teacher A cannot access Teacher B video-workflow runs.
- [ ] Teacher A cannot read Teacher B run content.
- [ ] Teacher A cannot download Teacher B run output.
- [ ] Teacher A cannot download Teacher B completed output.
- [ ] Teacher A cannot run cleanup on Teacher B project.
- [ ] Storage cleanup only affects the currently authorized project.
- [ ] All cross-user denials use 404-style responses and do not expose resource existence.

## CSRF and Cookie

- [ ] Login sets `shanhai_session` as `HttpOnly`.
- [ ] Cookie has `Path=/` and `SameSite=Lax`.
- [ ] Production HTTPS cookie has `Secure`.
- [ ] Unsafe requests without `X-CSRF-Token` fail.
- [ ] Unsafe requests with wrong `X-CSRF-Token` fail.
- [ ] Unsafe requests with current `X-CSRF-Token` succeed when authorized.

## Admin and Library

- [ ] Teacher cannot call admin-only endpoints.
- [ ] Admin can call admin-only endpoints.
- [ ] Teacher/admin can read allowed global read endpoints.
- [ ] Textbook and lesson-plan library behavior matches the current RBAC matrix.

## Readiness and Operations

- [ ] `/health` returns ok.
- [ ] `/readiness` returns expected provider and ownership status.
- [ ] Web `/api/backend/health` returns ok through the production frontend origin.
- [ ] Dry-run, if used, runs on isolated ports and does not change the public nginx upstream.
- [ ] Logs do not contain provider key, backend token, cookie, CSRF token, complete provider URL, signed URL, or full upstream response.
- [ ] Storage cleanup reports policy and usage structure.
- [ ] Storage cleanup is verified against the current authorized project only.
- [ ] Pending URL timeout/retry behavior is recorded if provider URL delivery is delayed.
- [ ] Release backup exists for `auth.db` and project DB files.
- [ ] Rollback instructions in `docs/operations/release-readiness-auth-rbac.md` are still accurate.

## Acceptance Result

Record one result:

- [ ] PASS
- [ ] PASS_WITH_RISKS
- [ ] FAIL

Notes:

- Accepted by:
- Date:
- Environment:
- SHA:
- Known risks:
