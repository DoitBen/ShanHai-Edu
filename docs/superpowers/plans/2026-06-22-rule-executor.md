# RuleExecutor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `docs/architecture-optimization-v2.md` section 4.3 so rules in `workflow/rules` become runtime gates for save/generate/approve and write `rule_result_log`.

**Architecture:** Add `RuleExecutor` beside `StateEngine`. `WorkflowService` calls it before save and approve, while StateEngine remains the owner of state transitions. Builtin checks cover the priority rules R010, R001, R004, R006, R026, and R030; unsupported script/agent rules are loaded but only executed when a builtin implementation exists.

**Tech Stack:** FastAPI, SQLite per project, YAML rule definitions, Python pytest contract tests, existing Next.js API consumer.

---

## Stage Entry

- Issues read for this stage: `gh issue list --state all --limit 1000` returned `[]`.
- Remote sync: `git pull --ff-only origin main` completed with `Already up to date`.
- Fixed stage order: this follows the pushed StateEngine commit `77ee47b`; Flywheel and security remain later stages.

## File Structure

- Create: `apps/api/app/rule_executor.py`
  - Loads `workflow/rules/index.yaml` and individual rule YAML files.
  - Filters rules by `trigger_node + trigger_event`.
  - Executes builtin checks for priority rules.
  - Raises hard-block and warning exceptions with structured results.
- Modify: `apps/api/app/store.py`
  - Adds `rule_result_log`.
  - Adds helper `record_rule_result()` and `rule_results()`.
- Modify: `apps/api/app/services.py`
  - Calls `RuleExecutor` before `edit_node()` saves and before `approve_node()` commits approval.
  - Keeps existing content validation first where it already exists.
- Modify: `apps/api/app/main.py`
  - Maps hard-block violations to structured `RULE_VIOLATION_<id>` API errors.
  - Maps non-overridden warnings to `RULE_WARNING`.
- Modify: `apps/api/app/models.py`
  - Adds `override_warning_rule_ids` and `override_reason` to approve payload.
- Test: `apps/api/tests/test_rule_executor_contract.py`
  - Covers R004, R006, R030, warning override, hard-block non-override, R001, and R010 evidence.

## Task 1: Failing RuleExecutor Contract Tests

- [ ] **Step 1: Add rule contract test file**

Create `apps/api/tests/test_rule_executor_contract.py` with fake-provider helpers and these behaviors:

```python
def test_r004_blocks_character_dict_save_and_logs_result(tmp_path: Path):
    broken = {"characters": [{"style_constraint": "photorealistic", "banned_keywords": []}]}
    response = client.post(f"/projects/{project_id}/nodes/character_dict/edit", json={"content": broken})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "RULE_VIOLATION_R004"
```

```python
def test_warning_requires_override_and_override_is_logged(tmp_path: Path):
    warning_response = client.post(f"/projects/{project_id}/nodes/ppt_assembly_plan/approve", json={})
    assert warning_response.status_code == 409
    assert warning_response.json()["error"]["code"] == "RULE_WARNING"

    approved = unwrap_ok(client.post(
        f"/projects/{project_id}/nodes/ppt_assembly_plan/approve",
        json={"override_warning_rule_ids": ["R023"], "override_reason": "内测页数压缩"},
    ))
    assert approved["status"] == "approved"
```

- [ ] **Step 2: Run focused test and confirm RED**

```powershell
python -m pytest apps\api\tests\test_rule_executor_contract.py -q
```

Expected: failure because `RuleExecutor`, `rule_result_log`, and warning override payload do not exist yet.

## Task 2: Persistence and Rule Executor

- [ ] **Step 1: Add `rule_result_log`**

Create table:

```sql
CREATE TABLE IF NOT EXISTS rule_result_log (
  result_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  version_id TEXT,
  rule_id TEXT NOT NULL,
  trigger_event TEXT NOT NULL,
  severity TEXT NOT NULL,
  passed INTEGER NOT NULL,
  message TEXT NOT NULL,
  details_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

- [ ] **Step 2: Implement `RuleExecutor`**

Implement:

- `run_for_event(conn, project_id, node_id, trigger_event, content, override_warning_rule_ids=None, override_reason=None)`
- builtin checks for `R001`, `R004`, `R006`, `R023`, `R026`, `R030`
- structured exceptions `RuleHardBlockError` and `RuleWarningError`

## Task 3: Service/API Integration

- [ ] **Step 1: Wire service startup**

Instantiate:

```python
self.rule_executor = RuleExecutor(Path(workflow.root) / "rules")
```

- [ ] **Step 2: Gate save and approve**

Call:

- `on_save` before `store.write_version()` in `edit_node()`
- `on_approve_attempt` before `state_engine.approve()`

- [ ] **Step 3: Map API errors**

Return hard-block errors as:

```json
{"code": "RULE_VIOLATION_R004", "details": {"rule_id": "R004", "severity": "hard_block"}}
```

Return warnings as:

```json
{"code": "RULE_WARNING", "details": {"warnings": [{"rule_id": "R023"}]}}
```

## Task 4: Verification and Release

- [ ] **Step 1: Focused RuleExecutor tests**

```powershell
python -m pytest apps\api\tests\test_rule_executor_contract.py -q
```

- [ ] **Step 2: Backend regression**

```powershell
python -m pytest apps\api\tests -q
```

- [ ] **Step 3: Frontend checks**

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

- [ ] **Step 4: Browser smoke**

Start temporary API/Web ports, verify real API workspace still loads `16 个后端 manifest 节点`, and confirm rule warning/hard-block responses do not crash the UI.

- [ ] **Step 5: Commit and push**

Commit format:

```text
feat: RuleExecutor 规则门禁落地 | architecture-optimization-v2 第3周 | 2026-06-22 HH:MM
```
