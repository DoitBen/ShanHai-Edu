# Testing Guide

This guide defines the current repository test gates after the auth/RBAC/video workbench release readiness work.

## GitHub Actions Jobs

The `Video Workbench Delivery Gate` workflow currently has four jobs:

- `API contract and concurrency tests`
- `Web contracts, typecheck, lint and build`
- `Playwright formal video workbench entry`
- `Secret and dependency scan`

All release PRs that touch the covered paths must wait for these jobs before merge.

## API Tests

Targeted backend gate:

```powershell
python -m pytest apps/api/tests/test_auth_phase_a.py apps/api/tests/test_project_access_control.py apps/api/tests/test_project_ownership_migration.py -q
```

Video workflow/API contract gate used by CI:

```powershell
python -m pytest apps/api/tests/test_video_workflow_canvas.py apps/api/tests/test_api_contract_gate.py -q
python apps/api/scripts/ci_startup_smoke.py
```

Full backend suite when fixtures are available:

```powershell
python -m pytest apps/api/tests -q
```

The local full backend suite depends on this PDF fixture directory:

```text
apps/api/tests/fixtures/textbook-parsing/renjiao-grade1-volume1-2024
```

If that fixture is missing, do not claim local full backend test success. Record the fixture limitation and rely on GitHub Actions or a fixture-complete environment for the full-suite gate.

## Web Contracts, Typecheck, Lint, Build

Run from `apps/web`:

```powershell
bun run test:contracts
bunx tsc --noEmit --incremental false
bun run lint
bun run build
```

`bun run test:contracts` is the canonical web contract command. Do not replace it with a hand-picked subset unless the PR explicitly explains why.

## E2E Gates

Demo-mode video workbench gate:

```powershell
NEXT_PUBLIC_DEMO_MODE=true bun run test:e2e -- e2e/video-workbench.spec.ts --workers=1
```

This is a compatibility gate only. It does not prove the real auth/RBAC security boundary.

Mock API-mode E2E gate:

```powershell
NEXT_PUBLIC_DEMO_MODE=false bun run test:e2e -- e2e/api-mode-auth-harness.spec.ts e2e/real-session-rbac.spec.ts e2e/video-workbench-security.spec.ts --workers=1
```

This proves frontend API-mode behavior with controlled mocked backend responses. It covers session restoration UI, role visibility, CSRF header wiring, and video-workbench denial UX. It does not prove the real FastAPI path.

Real full-stack smoke:

```powershell
bun run test:e2e -- --config=playwright.fullstack.config.ts e2e/real-backend-session-smoke.spec.ts --workers=1
```

This is the minimum real-chain proof for:

```text
browser -> Next proxy -> FastAPI -> auth.db/project.db
```

It must not use `page.route("**/api/backend/**")`.

## Secret Scan

Run from `apps/web`:

```powershell
bun run scan:client-secrets
```

Before pushing, also inspect staged docs and commit messages for tokens, provider URLs, signed URLs, cookies, personal paths, and raw headers.

## Diff Hygiene

Run from the repository root:

```powershell
git status --short
git diff --stat
git diff --check
```

Docs-only PRs should not run app tests unless they change application code, test code, workflow files, dependency manifests, or runtime configuration.
