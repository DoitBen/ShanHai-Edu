# StateEngine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `docs/architecture-optimization-v2.md` section 4.2 so node state, transition logs, dependency gates, and cascade invalidation are enforced at runtime.

**Architecture:** Add a backend `StateEngine` as the only workflow state transition coordinator. Keep `ProjectStore` focused on persistence primitives, use `WorkflowConfig.runtime_dependencies()` as the dependency graph, and expose cascade review reasons through manifest/node API data without adding a seventh business state.

**Tech Stack:** FastAPI, SQLite per project, Python pytest contract tests, existing Next.js manifest consumer.

---

## Stage Entry

- Issues read for this stage: `gh issue list --state all --limit 1000` returned `[]`.
- Remote sync: `git pull --ff-only origin main` completed with `Already up to date`.
- Scope order: this plan covers only `StateEngine`; `RuleExecutor`, `Flywheel`, and security boundary remain later fixed-order stages.

## File Structure

- Create: `apps/api/app/state_engine.py`
  - Owns valid states, passable states, upstream gate checks, version status transitions, approvals, cascade invalidation, and transition log writes.
- Modify: `apps/api/app/store.py`
  - Adds `state_transition_log`.
  - Adds persistence helpers used by `StateEngine`.
  - Adds manifest/node derived fields for latest transition and cascade review reason.
  - Stops using `approve_node()` as a direct business transition.
- Modify: `apps/api/app/services.py`
  - Replaces direct dependency/state writes in `generate_node()`, `edit_node()`, `approve_node()`, and artifact/failure branches with `StateEngine` calls.
- Modify: `apps/api/app/main.py`
  - Keeps API error mapping stable; node detail should include transition metadata from store helpers.
- Test: `apps/api/tests/test_state_engine_contract.py`
  - Contract coverage for blocked downstream generation, allowed generation after upstream approval, cascade invalidation, content retention, and transition log evidence.

## Task 1: Write Failing Contract Tests

- [ ] **Step 1: Add StateEngine contract test file**

Create `apps/api/tests/test_state_engine_contract.py` with a fake-provider project, helper functions matching `test_ppt_runtime_contract.py`, and these behaviors:

```python
def test_state_engine_blocks_downstream_until_upstreams_are_passable(tmp_path: Path):
    client = make_client(tmp_path)
    project_id = create_project(client)["project_id"]
    upload_textbook(client, project_id)

    blocked = client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={})

    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "UPSTREAM_NOT_APPROVED"
```

```python
def test_state_engine_cascades_approved_downstream_to_needs_review_without_losing_content(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)
    for node_id in ["textbook_parse", "lesson_plan", "ppt_assembly_plan"]:
        generate_and_approve(client, project_id, node_id)

    original = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_assembly_plan"))["content"]
    edited_lesson = unwrap_ok(client.get(f"/projects/{project_id}/nodes/lesson_plan"))["content"]
    edited_lesson["state_engine_marker"] = "upstream changed"

    unwrap_ok(client.post(f"/projects/{project_id}/nodes/lesson_plan/edit", json={"content": edited_lesson}))

    downstream = unwrap_ok(client.get(f"/projects/{project_id}/nodes/ppt_assembly_plan"))
    assert downstream["status"] == "needs_review"
    assert downstream["content"] == original
    assert downstream["review_reason"]["trigger"] == "cascade_invalidate"
```

- [ ] **Step 2: Run focused test and confirm RED**

Run:

```powershell
python -m pytest apps\api\tests\test_state_engine_contract.py -q
```

Expected: failures caused by missing `review_reason` / `state_transition_log` / cascade behavior, while existing API imports still load.

## Task 2: Add StateEngine and Persistence Primitives

- [ ] **Step 1: Create `StateEngine`**

Create `apps/api/app/state_engine.py` with:

```python
PASSABLE_STATES = {"approved", "skipped"}
STATE_VALUES = {"not_started", "drafted", "needs_review", "approved", "blocked", "skipped"}

class StateTransitionError(ValueError):
    pass

class StateEngine:
    def __init__(self, store: ProjectStore, dependencies: Mapping[str, Sequence[str]]):
        self.store = store
        self.dependencies = {node: list(deps) for node, deps in dependencies.items()}
```

Required public methods:

- `assert_upstreams_passable(conn, project_id, node_id) -> None`
- `record_version_ready(conn, project_id, node_id, version_result, trigger, user_id=None) -> dict`
- `approve(conn, project_id, node_id, user_id=None) -> dict`
- `cascade_invalidate(conn, project_id, changed_node_id, before_version_id, after_version_id, user_id=None) -> list[dict]`

- [ ] **Step 2: Add transition log table and helpers**

Modify `ProjectStore.init_db()` to create:

```sql
CREATE TABLE IF NOT EXISTS state_transition_log (
  transition_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT NOT NULL,
  trigger TEXT NOT NULL,
  triggered_at TEXT NOT NULL,
  triggered_by_user_id TEXT,
  version_id_before TEXT,
  version_id_after TEXT,
  reason TEXT
);
```

Add helpers:

- `record_state_transition(...)`
- `update_node_state(...)`
- `update_current_version_status(...)`
- `latest_transition(...)`
- `transition_log(project_id, node_id=None)`

## Task 3: Route WorkflowService Through StateEngine

- [ ] **Step 1: Instantiate StateEngine from workflow dependencies**

In `WorkflowService.__init__`, create:

```python
self.state_engine = StateEngine(store, self._dependencies())
```

- [ ] **Step 2: Replace dependency gate**

Change `_assert_dependencies()` to call `self.state_engine.assert_upstreams_passable(...)`.

- [ ] **Step 3: Replace write-version transitions**

For generate and edit paths, call `store.write_version(...)` to persist the version, then `state_engine.record_version_ready(...)` with triggers:

- `ai_generate_done` for AI generation and artifact generation.
- `user_save_edit` for user edits.
- `user_redo` for retry/redo generation if the retry endpoint later distinguishes it.

When the current version changes, call `state_engine.cascade_invalidate(...)`.

- [ ] **Step 4: Replace approve path**

In `WorkflowService.approve_node()`, after existing content validation, call:

```python
return self.state_engine.approve(conn, project_id, node_id)
```

`ProjectStore.approve_node()` should no longer be used by services for direct state transitions.

## Task 4: Expose Review Reason to API Consumers

- [ ] **Step 1: Decorate manifest nodes**

Update `ProjectStore.manifest()` so each node includes:

```python
"latest_transition": latest_transition_or_none,
"review_reason": {"trigger": "cascade_invalidate", "reason": "..."}  # only when current status is needs_review and latest trigger is cascade_invalidate
```

- [ ] **Step 2: Decorate node detail**

Update `/projects/{project_id}/nodes/{node_id}` to return the same transition metadata as manifest nodes.

## Task 5: Verification and Release

- [ ] **Step 1: Run focused StateEngine test**

```powershell
python -m pytest apps\api\tests\test_state_engine_contract.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run backend regression suite**

```powershell
python -m pytest apps\api\tests -q
```

Expected: existing passing/xfailed baseline is preserved.

- [ ] **Step 3: Run frontend checks**

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

Expected: typecheck, lint, and production build pass.

- [ ] **Step 4: Browser smoke**

Start existing API/web dev servers if needed, open the workspace, confirm real API manifest loads, PPT nodes remain visible, and cascade review copy is available when API provides `review_reason`.

- [ ] **Step 5: Commit and push**

Stage only StateEngine files and plan/test files. Commit format:

```text
feat: StateEngine 状态机落地 | architecture-optimization-v2 第1-2周 | 2026-06-22 HH:MM
```

Push `main` to `origin/main` after full verification passes.
