# PPT Mainline Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 接通 `docs/architecture-optimization-v2.md` 第 0 周 PPT 主链路，让真实 API manifest 和工作区可生成、编辑、确认 PPT 分支，并由 `pptx_artifact/generate` 产出可下载 PPTX。

**Architecture:** 复用现有 `workflow/workflow.yaml` 节点定义、`WorkflowConfig.runtime_node_ids()`、通用节点 generate/edit/approve 和 `export_project_ppt()`。第 0 周只扩展运行时节点、fake 产物和 artifact 生成分支，不引入 `final_delivery`。

**Tech Stack:** FastAPI、SQLite per project、pytest、Next.js TypeScript、现有 PPT exporter。

---

### Task 1: Backend PPT Runtime Contract

**Files:**
- Create: `apps/api/tests/test_ppt_runtime_contract.py`
- Modify: `apps/api/app/workflow_config.py`
- Modify: `apps/api/app/providers.py`
- Modify: `apps/api/app/services.py`

- [x] **Step 1: Write the failing contract test**

```python
def test_ppt_runtime_manifest_and_artifact_generation(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_textbook(client, project_id)

    manifest = unwrap_ok(client.get(f"/projects/{project_id}/manifest"))
    states = {node["node_id"]: node["status"] for node in manifest["nodes"]}
    assert "final_delivery" not in states
    for node_id in ["visual_contract", "character_dict", "ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset", "pptx_artifact"]:
        assert states[node_id] == "not_started"

    for node_id in ["textbook_parse", "lesson_plan"]:
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    for node_id in ["visual_contract", "character_dict", "ppt_assembly_plan", "ppt_page_script", "ppt_visual_asset"]:
        generated = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/generate", json={}))
        content = dict(generated["content"])
        content["_phase0_marker"] = node_id
        edited = unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/edit", json={"content": content}))
        assert edited["status"] == "needs_review"
        unwrap_ok(client.post(f"/projects/{project_id}/nodes/{node_id}/approve", json={}))

    artifact = unwrap_ok(client.post(f"/projects/{project_id}/nodes/pptx_artifact/generate", json={}))
    assert artifact["status"] == "needs_review"
    assert artifact["content"]["pptx_path"].endswith(".pptx")
    assert (Path(project["project_dir"]) / artifact["content"]["pptx_path"]).exists()
    downloaded = client.get(artifact["content"]["download_url"])
    assert downloaded.status_code == 200
```

- [x] **Step 2: Run red test**

Run: `python -m pytest apps\api\tests\test_ppt_runtime_contract.py -q`

Expected: FAIL because PPT nodes are missing from runtime manifest or FakeProvider does not support them.

- [x] **Step 3: Implement minimal backend**

Update `MVP_RUNTIME_NODE_IDS` / `MVP_NODE_IDS`, add fake JSON for six PPT-adjacent nodes, and route `pptx_artifact` generation through `export_project_ppt()`.

- [x] **Step 4: Run green tests**

Run: `python -m pytest apps\api\tests\test_ppt_runtime_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_video_demo_contract.py -q`

Expected: PASS.

### Task 2: Frontend Real API Mapping

**Files:**
- Modify: `apps/web/src/lib/api-mappers.ts`
- Modify: `apps/web/src/lib/types.ts`

- [x] **Step 1: Map backend PPT node IDs**

Add explicit entries for `visual_contract`, `character_dict`, `ppt_assembly_plan`, `ppt_page_script`, `ppt_visual_asset`, and `pptx_artifact`. Use `branch: "ppt"` for PPT work, and keep `final_delivery` absent from real API mode unless backend returns it.

- [x] **Step 2: Type artifact mutation**

Allow `ApiNodeMutationResult` to carry `pptx_path`, `download_url`, and `path` so node mutation logs and result rendering preserve artifact metadata.

- [x] **Step 3: Verify frontend**

Run:

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

Expected: all commands exit 0.

### Task 3: Phase 0 Acceptance

**Files:**
- Modify: `workflow/multi-agent/dispatch.md`
- Modify: `workflow/multi-agent/stage-review.md`
- Modify: `workflow/multi-agent/roles/architect.md`
- Modify: `workflow/multi-agent/handoffs/latest.md`

- [x] **Step 1: Run focused backend and frontend verification**

Run focused pytest, frontend type/lint/build, and an HTTP smoke against `TestClient` through the new pytest contract.

- [ ] **Step 2: Commit and push**

Stage only files changed for 第 0 周. Commit message format:

```text
feat: 第0周PPT主链路接通 | architecture-optimization-v2 第0周 | 2026-06-22 HH:MM
```

Then push `main` to `origin`.
