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

const types = readProjectFile("src/lib/types.ts");
const apiClient = readProjectFile("src/lib/api-client.ts");
const store = readProjectFile("src/lib/store.ts");
const workspace = readProjectFile("src/components/screens/ProjectWorkspaceScreen.tsx");
const videoCanvas = readProjectFile("src/components/video-workflow/VideoWorkflowCanvas.tsx");

assert(types.includes("interface VideoWorkflowGraph"), "types must define VideoWorkflowGraph");
assert(types.includes("interface VideoReferenceAsset"), "types must define VideoReferenceAsset");
assert(types.includes("interface VideoWorkflowRun"), "types must define VideoWorkflowRun");
assert(types.includes("interface VideoWorkflowRunRequest"), "types must define VideoWorkflowRunRequest");

assert(apiClient.includes("fetchVideoWorkflow"), "api client must expose fetchVideoWorkflow");
assert(apiClient.includes("saveVideoWorkflow"), "api client must expose saveVideoWorkflow");
assert(apiClient.includes("uploadVideoWorkflowAssets"), "api client must expose uploadVideoWorkflowAssets");
assert(apiClient.includes("createVideoWorkflowRun"), "api client must expose createVideoWorkflowRun");
assert(apiClient.includes("syncVideoWorkflowRun"), "api client must expose syncVideoWorkflowRun");
assert(apiClient.includes("downloadVideoWorkflowRun"), "api client must expose downloadVideoWorkflowRun");
assert(apiClient.includes("/video-workflow/runs"), "api client must call video-workflow run endpoints");

assert(store.includes("videoWorkflowByProject"), "store must cache video workflow state");
assert(store.includes("loadVideoWorkflow"), "store must load video workflow");
assert(store.includes("saveVideoWorkflowGraph"), "store must save video workflow graph");
assert(store.includes("uploadVideoWorkflowReferences"), "store must upload video workflow references");
assert(store.includes("createVideoWorkflowRun"), "store must create video workflow run");

assert(workspace.includes("omni_flash-10s"), "workspace video default must use omni_flash-10s");
assert(workspace.includes('mode: "text"'), "workspace video default mode must be text");
assert(workspace.includes("durationSec: 10"), "workspace video option must expose 10 second default");
assert(workspace.includes("fullRun: false"), "workspace video option must default to single 10 second run");
assert(workspace.includes("VideoWorkflowCanvas"), "workspace must render VideoWorkflowCanvas");
assert(videoCanvas.includes("参考图最多"), "workspace must show reference image limit wording");
assert(videoCanvas.includes("@xyflow/react"), "video canvas must use @xyflow/react");
