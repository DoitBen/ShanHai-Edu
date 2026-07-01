# Owner Manual Acceptance Run - 2026-07-01

This document records the manual acceptance run for the ShanHai-Edu Auth/RBAC/video workbench foundation.

Do not mark an item as `PASS` unless it has been executed and evidence has been recorded.

## 1. Acceptance Goal

Validate the real user authentication, RBAC, project ownership, object-level authorization, CSRF/cookie handling, and project video workbench foundation on the current `main` baseline.

This run is for acceptance evidence only. It does not authorize bug fixes, application code changes, CI changes, dependency changes, runtime configuration changes, Phase F work, or new product features.

## 2. Acceptance Environment Record

| Field | Value |
| --- | --- |
| Main SHA | `16e103e46c11dc71aa00f549dcc225839733746f` |
| Date | 2026-07-01 |
| Tester | TBD |
| Environment | TBD |
| API mode / demo mode | API mode required for security acceptance; demo mode may be recorded separately as compatibility evidence |

## 3. Account Preparation

| Account | Prepared | Identifier | Notes |
| --- | --- | --- | --- |
| admin | NOT_RUN | TBD | Active admin account required |
| teacher A | NOT_RUN | TBD | Must own Project A |
| teacher B | NOT_RUN | TBD | Must own Project B |

## 4. Project Preparation

| Project | Owner | Prepared | Notes |
| --- | --- | --- | --- |
| Project A | Teacher A | NOT_RUN | `project_meta.owner_id` must point to Teacher A |
| Project B | Teacher B | NOT_RUN | `project_meta.owner_id` must point to Teacher B |

## 5. Referenced Acceptance Checklist

Use the canonical checklist as the source for manual coverage:

- `docs/operations/manual-acceptance-checklist.md`

## 6. Itemized Acceptance Record

Allowed results:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_RUN`

### Preflight

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Deployed commit matches target SHA | NOT_RUN | TBD |  |
| `NEXT_PUBLIC_DEMO_MODE=false` for real acceptance | NOT_RUN | TBD |  |
| FastAPI `STORAGE_ROOT` points to intended environment | NOT_RUN | TBD |  |
| `AUTH_COOKIE_SECURE=true` when served over HTTPS | NOT_RUN | TBD |  |
| Origin allowlist contains only expected frontend origins | NOT_RUN | TBD |  |
| Active admin, teacher A, and teacher B exist | NOT_RUN | TBD |  |
| `verify-project-ownership` reports no missing or orphaned owner projects | NOT_RUN | TBD |  |

### Login and Session

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Unauthenticated users see the login screen | NOT_RUN | TBD |  |
| Valid teacher login succeeds | NOT_RUN | TBD |  |
| Valid admin login succeeds | NOT_RUN | TBD |  |
| `/auth/me` restores the user after page refresh | NOT_RUN | TBD |  |
| Logout clears the session and returns to login | NOT_RUN | TBD |  |
| Disabled or invalid users cannot login | NOT_RUN | TBD |  |
| No session token or CSRF token appears in `localStorage` or `sessionStorage` | NOT_RUN | TBD |  |

### Role Visibility

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Teacher sees teacher-facing navigation only | NOT_RUN | TBD |  |
| Teacher does not see admin-only entry points | NOT_RUN | TBD |  |
| Admin sees admin entry points | NOT_RUN | TBD |  |
| Demo role switching is not visible in API mode | NOT_RUN | TBD |  |

### Project Access

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Teacher A sees only Teacher A projects in the project list | NOT_RUN | TBD |  |
| Teacher B sees only Teacher B projects in the project list | NOT_RUN | TBD |  |
| Admin sees Teacher A and Teacher B projects | NOT_RUN | TBD |  |
| Teacher A opening Teacher B project URL returns a 404/no-access response | NOT_RUN | TBD |  |
| Client-supplied `Authorization` or role data does not grant access | NOT_RUN | TBD |  |

### Video Workbench

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Teacher can open an owned project video workbench | NOT_RUN | TBD |  |
| Video capabilities load through `/api/backend` | NOT_RUN | TBD |  |
| Reference assets list loads for an owned project | NOT_RUN | TBD |  |
| Reference image upload succeeds for a valid image | NOT_RUN | TBD |  |
| Invalid image upload is rejected with a controlled validation error | NOT_RUN | TBD |  |
| Reference image deletion succeeds for an owned project | NOT_RUN | TBD |  |
| Existing runs list loads for an owned project | NOT_RUN | TBD |  |
| Creating a video run succeeds for an owned project with valid inputs | NOT_RUN | TBD |  |
| Run polling and manual sync update status correctly | NOT_RUN | TBD |  |
| Provider `completed` without URL is recognizable as pending URL/download state | NOT_RUN | TBD |  |
| Pending URL timeout moves to a retryable state and allows retry | NOT_RUN | TBD |  |
| Completed output can be played and downloaded | NOT_RUN | TBD |  |
| Demo-mode video workbench compatibility is recorded separately from security acceptance | NOT_RUN | TBD |  |

### Cross-User Video Security

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Teacher A cannot read Teacher B `/video-workflow` | NOT_RUN | TBD |  |
| Teacher A cannot access Teacher B video-workflow assets | NOT_RUN | TBD |  |
| Teacher A cannot read Teacher B video-workflow asset content | NOT_RUN | TBD |  |
| Teacher A cannot access Teacher B video-workflow runs | NOT_RUN | TBD |  |
| Teacher A cannot read Teacher B run content | NOT_RUN | TBD |  |
| Teacher A cannot download Teacher B run output | NOT_RUN | TBD |  |
| Teacher A cannot download Teacher B completed output | NOT_RUN | TBD |  |
| Teacher A cannot run cleanup on Teacher B project | NOT_RUN | TBD |  |
| Storage cleanup only affects the currently authorized project | NOT_RUN | TBD |  |
| All cross-user denials use 404-style responses and do not expose resource existence | NOT_RUN | TBD |  |

### CSRF and Cookie

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Login sets `shanhai_session` as `HttpOnly` | NOT_RUN | TBD |  |
| Cookie has `Path=/` and `SameSite=Lax` | NOT_RUN | TBD |  |
| Production HTTPS cookie has `Secure` | NOT_RUN | TBD |  |
| Unsafe requests without `X-CSRF-Token` fail | NOT_RUN | TBD |  |
| Unsafe requests with wrong `X-CSRF-Token` fail | NOT_RUN | TBD |  |
| Unsafe requests with current `X-CSRF-Token` succeed when authorized | NOT_RUN | TBD |  |

### Admin and Library

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Teacher cannot call admin-only endpoints | NOT_RUN | TBD |  |
| Admin can call admin-only endpoints | NOT_RUN | TBD |  |
| Teacher/admin can read allowed global read endpoints | NOT_RUN | TBD |  |
| Textbook and lesson-plan library behavior matches the current RBAC matrix | NOT_RUN | TBD |  |

### Readiness and Operations

| Check | Result | Evidence | Notes |
| --- | --- | --- | --- |
| `/health` returns ok | NOT_RUN | TBD |  |
| `/readiness` returns expected provider and ownership status | NOT_RUN | TBD |  |
| Storage cleanup reports policy and usage structure | NOT_RUN | TBD |  |
| Storage cleanup is verified against the current authorized project only | NOT_RUN | TBD |  |
| Pending URL timeout/retry behavior is recorded if provider URL delivery is delayed | NOT_RUN | TBD |  |
| Release backup exists for `auth.db` and project DB files | NOT_RUN | TBD |  |
| Rollback instructions in `docs/operations/release-readiness-auth-rbac.md` are still accurate | NOT_RUN | TBD |  |

## 7. Final Conclusion

Result: `NOT_RUN`

Final allowed conclusion values:

- `PASS`
- `PASS_WITH_RISKS`
- `FAIL`

Do not set a final conclusion until the itemized acceptance record has been executed and reviewed.

## 8. Blocking Issues

| Issue | Status | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- |
| TBD | NOT_RUN | TBD | TBD |  |

## 9. Accepted Risks

| Risk | Accepted By | Evidence | Notes |
| --- | --- | --- | --- |
| TBD | TBD | TBD |  |

## 10. Next Action Recommendation

Current recommendation: `NOT_RUN`

Record one recommendation after acceptance:

- proceed to release
- proceed with accepted risks
- block release and fix issues
- rerun acceptance after environment/data preparation

Notes:

- TBD
