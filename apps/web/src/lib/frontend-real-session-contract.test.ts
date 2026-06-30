import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

function readProjectFile(path: string): string {
  return readFileSync(join(root, path), "utf-8");
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const store = readProjectFile("src/lib/store.ts");
const apiClient = readProjectFile("src/lib/api-client.ts");
const loginScreen = readProjectFile("src/components/screens/LoginScreen.tsx");
const topBar = readProjectFile("src/components/layout/TopBar.tsx");
const commandPalette = readProjectFile("src/components/command-palette/CommandPalette.tsx");
const sidebar = readProjectFile("src/components/layout/Sidebar.tsx");
const e2e = readProjectFile("e2e/video-workbench.spec.ts");

assert(
  apiClient.includes("export function setApiCsrfToken") &&
    apiClient.includes("export function getApiCsrfToken"),
  "api-client must keep CSRF in memory with explicit setter/getter",
);
assert(
  apiClient.includes("fetchCurrentSession") && apiClient.includes("/auth/me"),
  "api-client must expose /auth/me for refresh recovery",
);
assert(
  apiClient.includes("loginWithPassword") && apiClient.includes("/auth/login"),
  "api-client must expose /auth/login",
);
assert(
  apiClient.includes("logoutSession") && apiClient.includes("/auth/logout"),
  "api-client must expose /auth/logout",
);
assert(
  !apiClient.includes("localStorage") && !apiClient.includes("sessionStorage"),
  "api-client must not persist auth or CSRF in browser storage",
);

assert(
  store.includes("loadDemoAuth") && store.includes("saveDemoAuth"),
  "demo auth persistence must be named as demo-only",
);
assert(
  store.includes("if (isDemoMode())") && store.includes("fetchCurrentSession"),
  "initAuth must use /auth/me in API mode and local demo auth only in demo mode",
);
assert(
  store.includes("loginWithPassword(username.trim(), password)") ||
    store.includes("loginWithPassword(username, password)"),
  "API mode login must call /auth/login",
);
assert(
  store.includes("logoutSession()"),
  "API mode logout must call /auth/logout",
);
assert(
  store.includes("setApiCsrfToken(null)") && store.includes("csrfToken:"),
  "store must clear in-memory CSRF on logout/auth loss and expose session state",
);
assert(
  store.includes("if (!isDemoMode()) return;"),
  "switchRole must be disabled outside demo mode",
);

assert(
  loginScreen.includes("await login(") &&
    loginScreen.includes('type={demoMode ? "text" : "email"}'),
  "login screen must perform async real login and use email input in API mode while keeping demo username login usable",
);
assert(
  topBar.includes("demoMode &&") && topBar.includes("void logout()"),
  "TopBar must hide role switching outside demo mode and call async logout",
);
assert(
  commandPalette.includes("if (demoMode)") && commandPalette.includes("void logout()"),
  "CommandPalette must keep role switching demo-only and call async logout",
);
assert(
  sidebar.includes('const isAdmin = user?.role === "admin"') &&
    sidebar.includes("NAV.filter((n) => !n.adminOnly || isAdmin)"),
  "Sidebar must hide admin entries from teacher sessions and show them to admin sessions",
);
assert(
  commandPalette.includes('const isAdmin = user?.role === "admin"') &&
    commandPalette.includes("if (isAdmin)"),
  "CommandPalette must derive admin entries from the real session role",
);
assert(
  e2e.includes("mockAuthenticatedApiSession") && !e2e.includes('window.localStorage.setItem(\n      "shanhai_auth"'),
  "video workbench E2E must use a mocked real session instead of localStorage auth",
);
