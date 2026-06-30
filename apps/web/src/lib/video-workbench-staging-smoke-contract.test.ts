import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = join(process.cwd(), "..", "..");
const smokeScriptPath = join(root, "apps/api/scripts/video_workbench_staging_smoke.py");
const runbookPath = join(root, "docs/ops-video-workbench-staging-smoke-runbook.md");
const rollbackPath = join(root, "docs/ops-video-workbench-rollback-drill.md");
const workflowPath = join(root, ".github/workflows/video-workbench-delivery.yml");

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

assert(existsSync(smokeScriptPath), "staging smoke script must exist");
assert(existsSync(runbookPath), "staging smoke runbook must exist");
assert(existsSync(rollbackPath), "rollback drill document must exist");

const smokeScript = readFileSync(smokeScriptPath, "utf-8");
const runbook = readFileSync(runbookPath, "utf-8");
const rollback = readFileSync(rollbackPath, "utf-8");
const workflow = readFileSync(workflowPath, "utf-8");

assert(smokeScript.includes("video-workbench-staging-smoke"), "smoke report name must identify staging smoke");
assert(smokeScript.includes("/api/backend"), "smoke script must verify Next backend proxy usage");
assert(smokeScript.includes("OMNI_TEXT_TO_VIDEO"), "smoke script must include Omni text-to-video smoke");
assert(smokeScript.includes("OMNI_REFERENCE_TO_VIDEO"), "smoke script must include Omni reference-to-video smoke");
assert(smokeScript.includes("redact_sensitive"), "smoke script must redact sensitive fields");
assert(!smokeScript.includes("Authorization: Bearer"), "smoke script must not contain literal bearer headers");

assert(runbook.includes("staging"), "runbook must describe staging execution");
assert(runbook.includes("video_workbench_staging_smoke.py"), "runbook must document the smoke command");
assert(runbook.includes("docs/qa-audits"), "runbook must document the evidence output path");
assert(runbook.includes("不记录 token"), "runbook must document secret redaction requirements");

assert(rollback.includes("Web 回滚"), "rollback drill must cover web rollback");
assert(rollback.includes("API 回滚"), "rollback drill must cover API rollback");
assert(rollback.includes("SQLite"), "rollback drill must cover SQLite/storage recovery");
assert(rollback.includes("provider 故障降级"), "rollback drill must cover provider outage fallback");

assert(
  workflow.includes("video-workbench-staging-smoke-contract.test.ts"),
  "CI must run the staging smoke contract",
);
