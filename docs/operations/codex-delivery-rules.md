# Codex Delivery Rules

These rules keep future Codex work reviewable and recoverable.

## Scope Discipline

- Audit documents are issue pools, not one-shot execution task lists.
- Each PR must solve one primary goal.
- Do not bundle feature work, security work, docs cleanup, and CI repair into the same PR.
- If changed files exceed 20, provide a split plan before implementation.
- If a PR starts as docs-only, keep it docs-only.

## PR Flow

- All non-trivial PRs start as Draft.
- Every PR description must state:
  - What changed.
  - What explicitly did not change.
  - Test results.
  - Risks.
  - Next step.
- CI red means fix CI only. Do not add unrelated features while CI is red.
- Do not self-merge before the requested review/owner gate.

## Merge Policy

- Use Squash Merge.
- Do not use ordinary merge commits.
- Do not use rebase merge.
- Main should remain protected by required status checks.

## Testing Evidence

- Do not claim test success without fresh command output.
- Demo-mode E2E is compatibility evidence only.
- Mock API-mode E2E proves frontend behavior only.
- Real full-stack smoke proves the minimum browser-to-Next-to-FastAPI-to-SQLite path.
- If local fixtures are missing, say so directly and do not claim the affected full suite passed.

## Security and Secrets

- Never paste tokens, cookies, signed URLs, provider headers, raw secrets, or private key paths into PRs or docs.
- Frontend code must not receive provider tokens.
- Token compatibility paths must not bypass object-level authorization.
- Changes to auth, RBAC, proxy, cookies, CSRF, storage, or migrations require explicit tests and review.

## Stop Conditions

Stop and report instead of expanding scope when:

- A requested change requires modifying a forbidden area.
- A supposedly docs-only task needs application code changes.
- A branch has unrelated dirty files.
- A reviewer asks for one blocker fix but the fix appears to require a new feature.
