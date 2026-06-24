import { readFileSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert";

const root = join(__dirname, "..");

function readProjectFile(path: string) {
  return readFileSync(join(root, path), "utf-8");
}

const types = readProjectFile("lib/types.ts");
const sidebar = readProjectFile("components/layout/Sidebar.tsx");
const appShell = readProjectFile("components/layout/AppShell.tsx");
const apiClient = readProjectFile("lib/api-client.ts");
const adminScreen = readProjectFile("components/screens/AdminTextbookLibraryScreen.tsx");
const newProjectScreen = readProjectFile("components/screens/NewProjectScreen.tsx");

assert(
  types.includes('| "admin-textbook-library"'),
  "ScreenKey must include the admin textbook library screen",
);

assert(
  sidebar.includes("管理教材库") &&
    sidebar.includes("admin-textbook-library") &&
    sidebar.includes("adminOnly: true"),
  "Sidebar must expose an admin-only 管理教材库 entry",
);

assert(
  appShell.includes("AdminTextbookLibraryScreen") &&
    appShell.includes('screen === "admin-textbook-library"'),
  "AppShell must route admin-textbook-library to AdminTextbookLibraryScreen",
);

const requiredAdminActions = [
  "上传教材",
  "切分教材",
  "解析教材内容",
  "确认资产",
  "上传教案",
  "教案库",
];

for (const copy of requiredAdminActions) {
  assert(
    adminScreen.includes(copy),
    `AdminTextbookLibraryScreen must expose admin textbook-library action: ${copy}`,
  );
}

assert(
  apiClient.includes("uploadLessonPlanToLibrary"),
  "api-client must expose uploadLessonPlanToLibrary(file, metadata)",
);

const forbiddenTeacherCopy = [
  "导入教材",
  "切分教材",
  "解析教材内容",
  "重新解析",
];

for (const copy of forbiddenTeacherCopy) {
  assert(
    !newProjectScreen.includes(copy),
    `NewProjectScreen must not expose admin textbook processing copy: ${copy}`,
  );
}
