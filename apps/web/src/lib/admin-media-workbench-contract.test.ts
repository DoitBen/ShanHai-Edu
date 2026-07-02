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
const sidebar = readProjectFile("src/components/layout/Sidebar.tsx");
const appShell = readProjectFile("src/components/layout/AppShell.tsx");
const commandPalette = readProjectFile("src/components/command-palette/CommandPalette.tsx");
const screen = readProjectFile("src/components/screens/AdminMediaWorkbenchScreen.tsx");

assert(types.includes("interface MediaWorkbenchCapabilities"), "types must define MediaWorkbenchCapabilities");
assert(types.includes("interface MediaAsset"), "types must define MediaAsset");
assert(types.includes("interface ImageWorkbenchRun"), "types must define ImageWorkbenchRun");
assert(types.includes("interface ImageWorkbenchRunRequest"), "types must define ImageWorkbenchRunRequest");
assert(types.includes("interface VideoWorkbenchRun"), "types must define VideoWorkbenchRun");
assert(types.includes("interface VideoWorkbenchRunRequest"), "types must define VideoWorkbenchRunRequest");
assert(types.includes("interface VideoReferenceBasket"), "types must define VideoReferenceBasket");
assert(types.includes('"admin-media-workbench"'), "ScreenKey must include admin-media-workbench");

assert(apiClient.includes("fetchMediaWorkbench"), "api client must expose fetchMediaWorkbench");
assert(apiClient.includes("fetchMediaWorkbenchCapabilities"), "api client must expose capabilities fetch");
assert(apiClient.includes("createImageWorkbenchRun"), "api client must create image runs");
assert(apiClient.includes("fetchImageWorkbenchRun"), "api client must fetch image runs for async polling");
assert(apiClient.includes("uploadMediaWorkbenchVideoReferences"), "api client must upload video references");
assert(apiClient.includes("importMediaWorkbenchVideoReferences"), "api client must import references from assets");
assert(apiClient.includes("createVideoWorkbenchRun"), "api client must create video runs");
assert(apiClient.includes("syncVideoWorkbenchRun"), "api client must sync video runs");
assert(apiClient.includes("/admin/media-workbench/images/runs"), "api client must call image run endpoint");
assert(apiClient.includes("/admin/media-workbench/videos/runs"), "api client must call video run endpoint");

assert(store.includes("mediaWorkbench"), "store must cache media workbench state");
assert(store.includes("loadMediaWorkbench"), "store must load media workbench");
assert(!store.includes('loadMediaWorkbench: async () => {\n    if (get().dataMode === "demo") return;'), "media workbench must load real admin backend even when the UI shell is demo-login enabled");
assert(store.includes("createImageWorkbenchRun"), "store must create image runs");
assert(store.includes("syncImageWorkbenchRun"), "store must sync async image runs");
assert(store.includes("importImagesToVideoReferences"), "store must import images to video references");
assert(store.includes("createVideoWorkbenchRun"), "store must create video runs");

assert(sidebar.includes("媒体生成工作台"), "Sidebar must expose admin media workbench entry");
assert(sidebar.includes('"admin-media-workbench"'), "Sidebar must route admin media workbench");
assert(appShell.includes("AdminMediaWorkbenchScreen"), "AppShell must render AdminMediaWorkbenchScreen");
assert(commandPalette.includes("媒体生成工作台"), "CommandPalette must expose media workbench command");

assert(screen.includes("gpt-image-2"), "image workbench default model must be gpt-image-2");
assert(screen.includes("1920x1080"), "image workbench default size must be 1920x1080");
assert(screen.includes("omni_flash-10s"), "video workbench default model must be omni_flash-10s");
assert(screen.includes("1280x720"), "video workbench default size must be 1280x720");
assert(screen.includes("最多 7 张"), "video workbench must show Omni reference limit");
assert(screen.includes("加入视频参考篮"), "image results must support sending selected images to video basket");
assert(screen.includes("setInterval") && screen.includes("30000"), "media workbench must auto-sync active runs every 30 seconds");
assert(screen.includes("syncImageWorkbenchRun"), "media workbench screen must poll async image runs");
assert(screen.includes("<video"), "completed video runs must render an inline preview player");
assert(screen.includes("参考图数量"), "video submit UI must make reference image count explicit");
assert(
  screen.includes('const effectiveVideoMode: VideoGenerationMode = basketCount > 0 ? "reference" : videoMode') &&
    screen.includes("mode: effectiveVideoMode") &&
    screen.includes("reference_asset_ids: referenceAssetIds"),
  "video workbench must submit reference mode with selected basket assets",
);
