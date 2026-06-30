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
  apiClient.includes("videoWorkflowAssetContent") &&
    apiClient.includes("${API_BASE}/projects/${encodeURIComponent(projectId)}/video-workflow/assets"),
  "video workflow asset content must be served through the Next.js backend proxy",
);
assert(
  apiClient.includes("streamVideoWorkflowRun") &&
    apiClient.includes("${API_BASE}/projects/${encodeURIComponent(projectId)}/video-workflow/runs"),
  "video workflow run stream must be served through the Next.js backend proxy",
);
assert(
  apiClient.includes("downloadVideoWorkflowRun") &&
    apiClient.includes("/download"),
  "video workflow download must be served through the Next.js backend proxy",
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
assert(
  proxyRoute.includes("request.body") && proxyRoute.includes('duplex: "half"'),
  "backend proxy must stream multipart uploads to FastAPI",
);
assert(
  proxyRoute.includes("new NextResponse(response.body") && proxyRoute.includes("headers: response.headers"),
  "backend proxy must stream binary downloads and preserve response headers",
);
assert(
  proxyRoute.includes("export async function DELETE"),
  "backend proxy must support DELETE for video reference cleanup",
);
assert(apiClient.includes("action: string | null"), "api client error must preserve action");
assert(apiClient.includes("traceId: string | null"), "api client error must preserve trace id");
assert(apiClient.includes("error?.trace_id"), "api client must read trace id from API errors");
