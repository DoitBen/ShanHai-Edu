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
const proxyRoute = readProjectFile("src/app/api/backend/[...path]/route.ts");
const forbiddenPublicBaseEnv = "NEXT_PUBLIC" + "_API_BASE_URL";

assert(
  apiClient.includes('const API_BASE = "/api/backend"'),
  "api-client must call the Next.js backend proxy by default",
);
assert(
  !apiClient.includes(forbiddenPublicBaseEnv),
  "api-client must not expose backend origin through public base URL env",
);
assert(
  proxyRoute.includes("process.env.BACKEND_API_TOKEN"),
  "backend proxy must read BACKEND_API_TOKEN on the server",
);
assert(
  proxyRoute.includes("Authorization") && proxyRoute.includes("Bearer"),
  "backend proxy must forward Authorization bearer header to FastAPI",
);
assert(
  proxyRoute.includes('headers.delete("expect")'),
  "backend proxy must drop the Expect header because Undici fetch cannot forward it",
);
