import { readFileSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert";

const root = join(__dirname, "..");

function readProjectFile(path: string) {
  return readFileSync(join(root, path), "utf-8");
}

const types = readProjectFile("lib/types.ts");
const apiClient = readProjectFile("lib/api-client.ts");
const proxyRoute = readProjectFile("app/api/backend/[...path]/route.ts");
const appShell = readProjectFile("components/layout/AppShell.tsx");
const sidebar = readProjectFile("components/layout/Sidebar.tsx");

assert(
  types.includes('| "admin-workflow"'),
  "ScreenKey must include the admin workflow control plane",
);

assert(
  apiClient.includes("fetchAdminRules"),
  "api-client must expose fetchAdminRules",
);

assert(
  apiClient.includes("createAdminRuleVersion"),
  "api-client must expose createAdminRuleVersion",
);

assert(
  apiClient.includes("activateAdminRuleVersion"),
  "api-client must expose activateAdminRuleVersion",
);

assert(
  apiClient.includes("rollbackAdminRuleVersion"),
  "api-client must expose rollbackAdminRuleVersion",
);

assert(
  apiClient.includes("fetchAdminWorkflowGraph"),
  "api-client must expose fetchAdminWorkflowGraph",
);

assert(
  !proxyRoute.includes("BACKEND_API_TOKEN") && !proxyRoute.includes("Bearer"),
  "backend proxy must not inject a global backend bearer token for admin paths",
);

assert(
  proxyRoute.includes('headers.delete("authorization")'),
  "backend proxy must drop client Authorization headers for admin paths",
);

assert(
  proxyRoute.includes('copyHeader(request.headers, headers, "cookie")') &&
    proxyRoute.includes('copyHeader(request.headers, headers, "x-csrf-token")'),
  "backend proxy must forward session Cookie and CSRF headers for FastAPI admin RBAC",
);

assert(
  !proxyRoute.includes("shanhai_auth") && !proxyRoute.includes("isLocalAdminRequest"),
  "backend proxy must not trust editable local auth cookies for admin paths",
);

assert(
  appShell.includes("AdminWorkflowScreen"),
  "AppShell must render AdminWorkflowScreen",
);

assert(
  sidebar.includes("规则控制面"),
  "Sidebar must expose an admin-only workflow control plane entry",
);
