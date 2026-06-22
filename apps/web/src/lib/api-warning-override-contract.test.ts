import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

function readProjectFile(path: string): string {
  return readFileSync(join(root, path), "utf-8");
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const apiClient = readProjectFile("src/lib/api-client.ts");
const store = readProjectFile("src/lib/store.ts");
const workspace = readProjectFile("src/components/screens/ProjectWorkspaceScreen.tsx");

assert(apiClient.includes("export interface ApproveNodeOptions"), "api-client must expose approve override options");
assert(apiClient.includes("override_warning_rule_ids"), "approve client must send override warning rule ids");
assert(apiClient.includes("override_reason"), "approve client must send override reason");
assert(apiClient.includes("details: unknown"), "ApiClientError must retain structured error details");
assert(apiClient.includes("isApiClientError"), "api-client must export an ApiClientError type guard");
assert(store.includes("pendingRuleWarningByProject"), "store must keep pending rule warnings for UI override");
assert(store.includes("RULE_WARNING"), "store must handle RULE_WARNING separately from generic errors");
assert(workspace.includes("RuleWarningOverrideDialog"), "workspace must render a warning override dialog");
