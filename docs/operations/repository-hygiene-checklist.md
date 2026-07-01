# Repository Hygiene Checklist

This checklist records the repository cleanup decisions after the Phase E final audit merge.

## PR Cleanup

- [x] PR #22 should be closed: `[codex] add production risk audit and remediation plan`
- [x] PR #23 should be closed: `[docs] update media workbench audit and roadmap v2`
- [ ] PR #26 remains open for separate Owner decision: `[codex] 设计轻量协作机制 V1`

PR #22 and PR #23 are superseded by:

- `docs/audits/2026-06-30-media-workbench-auth-roadmap-v3.md`
- `docs/audits/2026-07-01-final-auth-rbac-video-workbench-audit.md`
- `docs/operations/release-readiness-auth-rbac.md`

## Merged Remote Branch Cleanup

These merged branches should be deleted from the remote after confirming their PRs were merged:

- [x] `feat/google-flow-core-video-workbench` - PR #25
- [x] `codex/real-auth-project-rbac-spec` - PR #27
- [x] `feat/real-auth-project-rbac` - PR #28
- [x] `codex/media-workbench-auth-roadmap-v3` - PR #29
- [x] `feat/project-ownership-migration` - PR #30
- [x] `feat/backend-object-rbac` - PR #31
- [x] `feat/frontend-real-session-proxy` - PR #32
- [x] `feat/final-e2e-security-audit` - PR #33

Do not delete:

- `main`
- `codex/collaboration-v1-design`

## GitHub Settings Recommendations

Owner should review repository settings:

- [ ] Disable merge commits.
- [ ] Disable rebase merge.
- [ ] Keep squash merge enabled.
- [ ] Protect `main`.
- [ ] Require status checks before merging.
- [ ] Require the `Video Workbench Delivery Gate` checks for covered paths.
- [ ] Require conversation resolution before merge.
- [ ] Restrict force pushes on protected branches.

## Owner Manual Actions

- [ ] Decide whether PR #26 should be kept, revised, or closed.
- [ ] Confirm branch protection rules on `main`.
- [ ] Confirm squash-only merge policy in repository settings.
- [ ] Confirm required CI checks match the current four-job gate.
- [ ] Periodically close or supersede stale Draft PRs with a comment linking to current source-of-truth docs.
- [ ] Periodically delete remote branches after Squash Merge when no longer needed.
