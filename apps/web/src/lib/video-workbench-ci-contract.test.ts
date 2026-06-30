import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = join(process.cwd(), "..", "..");
const workflow = readFileSync(
  join(root, ".github/workflows/video-workbench-delivery.yml"),
  "utf-8",
);
const deploymentTopology = readFileSync(
  join(root, "docs/ops-video-workbench-deployment-topology.md"),
  "utf-8",
);

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

assert(workflow.includes("test_video_workflow_canvas.py"), "CI must run video workflow API tests");
assert(workflow.includes("test_api_contract_gate.py"), "CI must run backend API contract gate");
assert(workflow.includes("video-workflow-contract.test.ts"), "CI must run frontend video workflow contract");
assert(workflow.includes("video-workbench-ci-contract.test.ts"), "CI must run its own delivery gate contract");
assert(
  workflow.includes("video-workbench-staging-smoke-contract.test.ts"),
  "CI must run staging smoke delivery contract",
);
assert(workflow.includes("video-workflow-polling-controller.test.ts"), "CI must run polling contract");
assert(workflow.includes("api-proxy-contract.test.ts"), "CI must run proxy contract");
assert(workflow.includes("tsc --noEmit --incremental false"), "CI must run TypeScript typecheck");
assert(workflow.includes("bun run lint"), "CI must run lint");
assert(workflow.includes("bun run build"), "CI must run production build");
assert(workflow.includes("e2e/video-workbench.spec.ts"), "CI must run formal entry Playwright test");
assert(workflow.includes("scan:client-secrets"), "CI must run client secret scan");
assert(workflow.includes("git grep -n -E"), "CI must run repository secret pattern scan");
assert(workflow.includes("bun audit --audit-level critical"), "CI must fail on critical dependency advisories");
assert(workflow.includes("concurrency:"), "CI must avoid overlapping duplicate runs");
assert(workflow.includes("scripts/ci_startup_smoke.py"), "CI must run API startup and storage smoke");
assert(workflow.includes("Run API startup smoke"), "CI must name the API startup smoke gate");
assert(
  deploymentTopology.includes("Browser -> Next.js /api/backend/* -> FastAPI"),
  "deployment topology must document the supported Next proxy path",
);
assert(
  deploymentTopology.includes("GET /projects/{project_id}/video-workflow/observability"),
  "deployment topology must include the observability proxy endpoint",
);
assert(
  deploymentTopology.includes("部署环境 E2E"),
  "deployment topology must document the production/staging E2E acceptance gate",
);
