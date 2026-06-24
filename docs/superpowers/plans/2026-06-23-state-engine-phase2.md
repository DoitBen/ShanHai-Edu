# StateEngine Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the StateEngine authority line by routing remaining business status writes through StateEngine before RuleExecutor Phase 2 and Flywheel work continue.

**Architecture:** Keep `ProjectStore` as the low-level persistence primitive, but require application business flows to mutate node status only through `StateEngine`. `RuleExecutor` must produce rule results, not own workflow state. Provider failure and `final_video` async/video states must be represented as StateEngine transitions so diagnostics, audit, and old project compatibility remain consistent.

**Tech Stack:** FastAPI, SQLite project storage, Python pytest, existing Next.js StateEngine diagnostics.

---

## Stage Entry

- Previous gate: T108 StateEngine Phase 1 architecture review is conditionally passed.
- Mainline decision: do not start RuleExecutor Phase 2, Flywheel, real provider E2E, or frontend redesign until T109 closes the remaining status-write bypasses.
- Known bypasses from T108:
  - `apps/api/app/rule_executor.py` directly calls `store.update_node_state(..., "blocked")` for hard block on `on_save/on_generate`.
  - `apps/api/app/services.py` provider failure paths call `store.write_version(..., "blocked")`.
  - `apps/api/app/video_orchestrator.py` writes `final_video` `drafted/blocked/needs_review` directly.

## File Structure

- Modify: `apps/api/app/state_engine.py`
  - Add explicit helpers for blocked/drafted/review version transitions and rule-block transitions.
  - Keep transition legality enforced by workflow config.
- Modify: `apps/api/app/services.py`
  - Replace provider failure and image partial failure status writes with StateEngine helpers.
  - Wrap rule hard-block calls so service layer owns status transition after RuleExecutor returns/raises rule results.
- Modify: `apps/api/app/rule_executor.py`
  - Remove direct `node_state` mutation. It should record rule results and raise structured errors only.
- Modify: `apps/api/app/video_orchestrator.py`
  - Inject StateEngine and route all `final_video` status writes through StateEngine.
- Test: `apps/api/tests/test_state_engine_phase2_contract.py`
  - New focused regression tests proving no remaining business bypass for rule hard block, provider failed node, and final video.
- Optionally modify: `apps/api/tests/test_state_engine_contract.py`
  - Only if existing StateEngine helpers are better colocated with current tests.

## Task 1: Backend Tests First

**Files:**
- Create: `apps/api/tests/test_state_engine_phase2_contract.py`

- [ ] **Step 1: Add hard-block StateEngine ownership test**

Create a test that saves invalid `character_dict` content and expects:

```python
def test_rule_hard_block_transition_is_owned_by_state_engine(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    response = client.post(
        f"/projects/{project_id}/nodes/character_dict/edit",
        json={
            "content": {
                "characters": [
                    {
                        "character_id": "c1",
                        "display_name": "真人学生",
                        "role": "student",
                        "style_constraint": "photorealistic",
                        "banned_keywords": [],
                    }
                ]
            }
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "RULE_VIOLATION_R004"

    rows = transition_rows(project["project_dir"], project_id, "character_dict")
    blocked_rows = [row for row in rows if row["to_status"] == "blocked"]
    assert blocked_rows
    assert blocked_rows[-1]["trigger"] == "hard_block_rule_hit"
    assert '"handled_by": "StateEngine"' in blocked_rows[-1]["reason"]
    assert '"rule_id": "R004"' in blocked_rows[-1]["reason"]
```

- [ ] **Step 2: Add final video transition test**

Seed upstream nodes approved, generate `final_video` in fake/placeholder mode, and assert `state_transition_log` records the final status instead of only changing `node_state` through `store.write_version`.

```python
def test_final_video_generate_records_state_engine_transition(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    seed_final_video_upstreams_approved(client, project)

    response = client.post(f"/projects/{project_id}/nodes/final_video/generate", json={})

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["node_id"] == "final_video"
    assert body["status"] in {"drafted", "needs_review"}

    rows = transition_rows(project["project_dir"], project_id, "final_video")
    assert rows
    assert rows[-1]["to_status"] == body["status"]
    assert rows[-1]["trigger"] in {"ai_generate_done", "video_tasks_submitted"}
```

- [ ] **Step 3: Add blocked provider failure test**

Use an existing fake provider failure path or a small stub provider to force `intro_video_asset` failure, then assert the blocked state includes StateEngine transition reason.

```python
def test_provider_failure_blocked_state_is_recorded_by_state_engine(tmp_path: Path):
    client = make_client(tmp_path, provider=BrokenIntroVideoAssetProvider())
    project = create_project(client)
    project_id = project["project_id"]
    seed_intro_video_asset_upstreams_approved(client, project)

    response = client.post(f"/projects/{project_id}/nodes/intro_video_asset/generate", json={})

    assert response.status_code == 502
    rows = transition_rows(project["project_dir"], project_id, "intro_video_asset")
    blocked_rows = [row for row in rows if row["to_status"] == "blocked"]
    assert blocked_rows
    assert '"handled_by": "StateEngine"' in blocked_rows[-1]["reason"]
```

- [ ] **Step 4: Run test and confirm RED**

Run:

```powershell
python -m pytest apps\api\tests\test_state_engine_phase2_contract.py -q
```

Expected before implementation: at least one failure showing missing StateEngine reason or missing final_video transition.

## Task 2: Add StateEngine Business Write Helpers

**Files:**
- Modify: `apps/api/app/state_engine.py`
- Test: `apps/api/tests/test_state_engine_phase2_contract.py`

- [ ] **Step 1: Add helper for version-backed transitions**

Add a helper with this shape:

```python
def record_written_version(
    self,
    conn: sqlite3.Connection,
    project_id: str,
    node_id: str,
    version_result: dict[str, Any],
    trigger: str,
    *,
    reason: dict[str, Any] | str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    if isinstance(reason, dict):
        reason_text = json.dumps({"handled_by": "StateEngine", **reason}, ensure_ascii=False)
    else:
        reason_text = reason
    public = self.record_version_ready(conn, project_id, node_id, version_result, trigger, user_id=user_id)
    if reason_text:
        latest = self.store.latest_transition(conn, project_id, node_id)
        if latest:
            conn.execute(
                "UPDATE state_transition_log SET reason = ? WHERE transition_id = ?",
                (reason_text, latest["transition_id"]),
            )
    return public
```

- [ ] **Step 2: Add helper for blocked existing-version transitions**

Add:

```python
def mark_blocked(
    self,
    conn: sqlite3.Connection,
    project_id: str,
    node_id: str,
    trigger: str,
    *,
    rule_id: str | None = None,
    error_code: str | None = None,
    message: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    state = self.store.node_state(conn, project_id, node_id)
    reason = {
        "handled_by": "StateEngine",
        "rule_id": rule_id,
        "error_code": error_code,
        "message": message,
    }
    return self.transition(
        conn,
        project_id,
        node_id,
        "blocked",
        trigger,
        user_id=user_id,
        current_version_id=state.get("current_version_id"),
        version_status="blocked" if state.get("current_version_id") else None,
        reason=json.dumps({key: value for key, value in reason.items() if value is not None}, ensure_ascii=False),
    )
```

- [ ] **Step 3: Run StateEngine tests**

Run:

```powershell
python -m pytest apps\api\tests\test_state_engine_contract.py apps\api\tests\test_state_engine_phase2_contract.py -q
```

Expected: existing StateEngine tests still pass; Phase 2 tests may still fail until service paths are rewired.

## Task 3: Remove RuleExecutor State Mutation

**Files:**
- Modify: `apps/api/app/rule_executor.py`
- Modify: `apps/api/app/services.py`
- Test: `apps/api/tests/test_rule_executor_contract.py`
- Test: `apps/api/tests/test_state_engine_phase2_contract.py`

- [ ] **Step 1: Remove direct node state updates from RuleExecutor**

In `RuleExecutor.run_for_event()`, remove this responsibility:

```python
store.update_node_state(...)
store.record_state_transition(...)
```

Keep:

```python
result = self._record(...)
conn.commit()
raise RuleHardBlockError(result)
```

- [ ] **Step 2: Catch hard-block errors in WorkflowService where state should change**

Add a private wrapper:

```python
def _run_rules_for_event(self, conn, project_id: str, node_id: str, trigger_event: str, content: dict[str, Any], **kwargs):
    try:
        return self.rule_executor.run_for_event(conn, self.store, project_id, node_id, trigger_event, content, **kwargs)
    except RuleHardBlockError as exc:
        if trigger_event in {"on_save", "on_generate"}:
            self.state_engine.mark_blocked(
                conn,
                project_id,
                node_id,
                "hard_block_rule_hit",
                rule_id=exc.rule_id,
                message=str(exc),
            )
            conn.commit()
        raise
```

Replace direct calls in `edit_node()` and `approve_node()` with this wrapper. Keep approve hard-block behavior unchanged unless tests explicitly require status change; current expected behavior is only save/generate changes node state to blocked.

- [ ] **Step 3: Run rule and StateEngine tests**

Run:

```powershell
python -m pytest apps\api\tests\test_rule_executor_contract.py apps\api\tests\test_state_engine_phase2_contract.py -q
```

Expected: RuleExecutor behavior stays compatible; hard-block status transition now has `handled_by=StateEngine`.

## Task 4: Route Provider Failed/Blocked Paths Through StateEngine

**Files:**
- Modify: `apps/api/app/services.py`
- Test: `apps/api/tests/test_real_providers.py`
- Test: `apps/api/tests/test_state_engine_phase2_contract.py`

- [ ] **Step 1: Replace `_record_failed_node()` direct blocked write**

Change `_record_failed_node()` so it still records the error and blocked content, but calls `state_engine.record_written_version(...)` or `mark_blocked(...)` for the business transition.

Target behavior:

```python
version = self.store.write_version(conn, project_id, node_id, content, "ai", self.provider.name, "blocked")
self.state_engine.record_written_version(
    conn,
    project_id,
    node_id,
    version,
    "provider_failed",
    reason={"error_code": exc.code, "retryable": exc.retryable},
)
```

- [ ] **Step 2: Replace intro_video_asset partial failure blocked writes**

In `_generate_image_tasks()`, replace both `store.write_version(..., "blocked")` branches with the same StateEngine helper and preserve current API errors.

- [ ] **Step 3: Run provider-focused tests**

Run:

```powershell
python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_state_engine_phase2_contract.py -q
```

Expected: provider diagnostics do not regress, and blocked transitions include StateEngine ownership.

## Task 5: Route VideoOrchestrator Final Video Status Through StateEngine

**Files:**
- Modify: `apps/api/app/video_orchestrator.py`
- Modify: `apps/api/app/services.py`
- Test: `apps/api/tests/test_tts_and_final_video.py`
- Test: `apps/api/tests/test_video_orchestrator.py`
- Test: `apps/api/tests/test_state_engine_phase2_contract.py`

- [ ] **Step 1: Inject StateEngine into VideoOrchestrator**

Update constructor call in `WorkflowService.__init__`:

```python
self.video_orchestrator = VideoOrchestrator(
    store=self.store,
    state_engine=self.state_engine,
    ...
)
```

Update `VideoOrchestrator.__init__` to store `self.state_engine`.

- [ ] **Step 2: Replace final_video direct status writes**

For every `self.store.write_version(conn, project_id, "final_video", ..., final_status)` in `video_orchestrator.py`, call:

```python
version = self.store.write_version(conn, project_id, "final_video", content, "ai", self.text_provider.name, final_status)
return self.state_engine.record_written_version(
    conn,
    project_id,
    "final_video",
    version,
    "video_tasks_submitted" if final_status == "drafted" else "ai_generate_done",
)
```

For blocked failure paths, use trigger `provider_failed` or `final_video_compose_failed` and include `error_code` in reason.

- [ ] **Step 3: Run video tests**

Run:

```powershell
python -m pytest apps\api\tests\test_video_orchestrator.py apps\api\tests\test_tts_and_final_video.py apps\api\tests\test_state_engine_phase2_contract.py -q
```

Expected: final_video task submission, compose success, and compose failure still work, with transition log present.

## Task 6: Compatibility, Coverage, and Docs

**Files:**
- Modify: `workflow/multi-agent/handoffs/latest.md`
- Modify: `workflow/multi-agent/roles/backend-engineer.md`
- Modify if needed: `workflow/multi-agent/stage-review.md`

- [ ] **Step 1: Verify no application business direct writes remain**

Run:

```powershell
rg -n "write_version\\(|update_node_state\\(" apps/api/app
```

Expected allowed direct calls:

- `apps/api/app/store.py` persistence primitives.
- `apps/api/app/state_engine.py`.
- service code only when immediately wrapped by StateEngine helper in the same branch.
- test fixtures outside `apps/api/app` are allowed.

- [ ] **Step 2: Run backend full suite**

Run:

```powershell
python -m pytest apps\api\tests -q
```

Expected: current baseline preserved or improved. As of T108 the baseline is `201 passed, 2 xfailed`.

- [ ] **Step 3: Run frontend sanity checks**

Run:

```powershell
cd apps\web
bun src/lib/api-mappers-contract.test.ts
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

Expected: all exit code 0.

- [ ] **Step 4: Update handoff**

Add backend handoff that states:

- StateEngine Phase 2 closed remaining status-write bypasses.
- Which direct writes remain and why they are allowed.
- Exact test commands and results.
- Any compatibility risks for old blocked/final_video nodes.

## Self-Review Checklist

- R010 remains StateEngine-owned and is not reintroduced into RuleExecutor runtime results.
- RuleExecutor no longer owns `node_state`.
- Provider failure and final_video statuses produce StateEngine transition evidence.
- Old project statuses `not_started/drafted/needs_review/approved/blocked/skipped` remain valid.
- No real provider keys, tokens, or endpoint secrets are printed in docs, tests, or logs.
