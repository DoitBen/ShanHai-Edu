import { readFileSync } from "node:fs";
import { join } from "node:path";

const loginSource = readFileSync(join(process.cwd(), "src/components/screens/LoginScreen.tsx"), "utf-8");
const dashboardSource = readFileSync(join(process.cwd(), "src/components/screens/DashboardScreen.tsx"), "utf-8");
const appShellSource = readFileSync(join(process.cwd(), "src/components/layout/AppShell.tsx"), "utf-8");

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

for (const copy of ["真实接口", "项目数据", "教材库", "当前为真实 API 模式"]) {
  assert(loginSource.includes(copy), `login screen must expose real API deployment copy: ${copy}`);
}

for (const copy of ["工作流节点", "演示项目", "视频方案"]) {
  assert(!loginSource.includes(copy), `login screen production hero stats must not expose demo copy: ${copy}`);
}

assert(
  !loginSource.includes("{demoMode ? (") || !loginSource.includes("<BrandStat label="),
  "login screen hero stats must not branch to demo stats in production deployment source",
);

assert(
  dashboardSource.includes("当前连接真实后端项目数据。"),
  "real API dashboard empty state must use real backend wording",
);
for (const copy of ["demo mock", "暂无真实待办", "真实 API 模式下待办事项"]) {
  assert(!dashboardSource.includes(copy), `real API dashboard visible copy must not expose old deployment wording: ${copy}`);
}

assert(appShellSource.includes("真实 API 工作台"), "footer must identify the real API deployment");
assert(!appShellSource.includes("第一阶段演示版"), "footer must not label the deployed app as a demo build");
