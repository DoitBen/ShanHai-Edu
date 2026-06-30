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
const workbench = readProjectFile("src/components/video-workflow/VideoWorkflowWorkbench.tsx");
const crossTab = readProjectFile("src/lib/video-workflow-cross-tab.ts");
const assetPanel = readProjectFile("src/components/video-workflow/VideoAssetPanel.tsx");
const composer = readProjectFile("src/components/video-workflow/VideoComposerPanel.tsx");
const history = readProjectFile("src/components/video-workflow/VideoRunHistoryPanel.tsx");
const videoErrors = readProjectFile("src/lib/video-workflow-errors.ts");
const uploadQueue = readProjectFile("src/lib/video-workflow-upload-queue.ts");

assert(types.includes("interface VideoWorkflowConfig"), "config contract is required");
assert(types.includes("provider_ready: boolean"), "config must expose provider readiness");
assert(types.includes("provider_reason_code: string"), "config must expose readiness reason code");
assert(types.includes("provider_user_message: string"), "config must expose readiness user message");
assert(types.includes("run_create_window_seconds: number"), "config must expose rate limit window");
assert(types.includes("run_create_project_window_limit: number"), "config must expose project run limit");
assert(types.includes("run_create_global_window_limit: number"), "config must expose global run limit");
assert(types.includes('"completed_pending_download"'), "run status must keep completed-without-url tasks pollable");
assert(types.includes('"pending_url"'), "download status must represent provider completed before URL is available");
assert(types.includes("runtime_concurrency?"), "config must expose current runtime concurrency boundary");
assert(types.includes("interface VideoStorageLifecyclePolicy"), "storage lifecycle policy type is required");
assert(types.includes("storage_lifecycle: VideoStorageLifecyclePolicy"), "config must expose storage lifecycle policy");
assert(types.includes("interface VideoStorageUsage"), "storage usage type is required");
assert(types.includes("storage_usage: VideoStorageUsage"), "workflow responses must expose storage usage");
assert(types.includes("interface VideoWorkflowStorageResponse"), "storage response type is required");
assert(types.includes("interface VideoWorkflowStorageCleanupResponse"), "storage cleanup response type is required");
assert(types.includes("interface VideoWorkflowObservabilitySnapshot"), "observability snapshot type is required");
assert(types.includes("provider_submit_success_count: number"), "observability metrics must expose provider submit success count");
assert(types.includes("trace_id: string"), "observability events must expose support trace id");
assert(types.includes("interface VideoWorkflowGraph"), "types must define VideoWorkflowGraph");
assert(types.includes("interface VideoReferenceAsset"), "types must define VideoReferenceAsset");
assert(types.includes("byte_size: number"), "asset byte size is required");
assert(types.includes("deleted_at: string | null"), "asset soft delete is required");
assert(types.includes("interface VideoWorkflowRun"), "types must define VideoWorkflowRun");
assert(types.includes("client_request_id: string"), "run idempotency key is required");
assert(types.includes("download_status: VideoDownloadStatus"), "download state is required");
assert(types.includes("download_bytes?: number | null"), "download byte size metadata is required");
assert(types.includes("download_sha256?: string | null"), "download checksum metadata is required");
assert(types.includes("interface VideoWorkflowRunRequest"), "types must define VideoWorkflowRunRequest");
assert(types.includes("interface VideoWorkflowRetryRequest"), "types must define retry request");
assert(types.includes("confirm_possible_duplicate?: boolean"), "retry request must expose duplicate confirmation");
assert(types.includes("runs: VideoWorkflowRun[]"), "workbench must expose history");

assert(apiClient.includes("fetchVideoWorkflow"), "api client must expose fetchVideoWorkflow");
assert(apiClient.includes("saveVideoWorkflow"), "api client must expose saveVideoWorkflow");
assert(apiClient.includes("uploadVideoWorkflowAssets"), "api client must expose uploadVideoWorkflowAssets");
assert(apiClient.includes("createVideoWorkflowRun"), "api client must expose createVideoWorkflowRun");
assert(apiClient.includes("syncVideoWorkflowRun"), "api client must expose syncVideoWorkflowRun");
assert(apiClient.includes("downloadVideoWorkflowRun"), "api client must expose downloadVideoWorkflowRun");
assert(apiClient.includes("deleteVideoWorkflowAsset"), "asset delete API is required");
assert(apiClient.includes("fetchVideoWorkflowRuns"), "run list API is required");
assert(apiClient.includes("retryVideoWorkflowRun"), "retry API is required");
assert(apiClient.includes("payload: VideoWorkflowRetryRequest"), "retry API must accept retry payload");
assert(apiClient.includes("streamVideoWorkflowRun"), "inline video API is required");
assert(apiClient.includes("fetchVideoWorkflowObservability"), "api client must expose video workflow observability fetch");
assert(apiClient.includes("/video-workflow/observability"), "api client must call video workflow observability endpoint");
assert(apiClient.includes("fetchVideoWorkflowStorage"), "api client must expose storage usage fetch");
assert(apiClient.includes("cleanupVideoWorkflowStorage"), "api client must expose storage cleanup call");
assert(apiClient.includes("/video-workflow/storage/cleanup"), "api client must call video workflow storage cleanup endpoint");
assert(apiClient.includes("/video-workflow/runs"), "api client must call video-workflow run endpoints");
assert(apiClient.includes("export class ApiClientError"), "api client must export structured errors for UI formatting");
assert(!apiClient.includes("；details:"), "api client must not append raw details to user-facing messages");

assert(store.includes("videoWorkflowByProject"), "store must cache video workflow state");
assert(store.includes("loadVideoWorkflow"), "store must load video workflow");
assert(store.includes("saveVideoWorkflowGraph"), "store must save video workflow graph");
assert(store.includes("uploadVideoWorkflowReferences"), "store must upload video workflow references");
assert(store.includes("createVideoWorkflowRun"), "store must create video workflow run");
assert(store.includes("videoWorkflowCreateLocks"), "store must guard video workflow create calls with a local lock");
assert(store.includes("videoWorkflowCreateLocks.has(projectId)"), "store create action must check the local create lock");
assert(store.includes("videoWorkflowCreateLocks.add(projectId)"), "store create action must acquire the local create lock");
assert(store.includes("videoWorkflowCreateLocks.delete(projectId)"), "store create action must release the local create lock");
assert(store.includes("confirmPossibleDuplicate"), "store retry must pass duplicate confirmation");
assert(store.includes("replaceVideoWorkflowRun"), "store must replace a run immutably");
assert(store.includes("removeVideoWorkflowAsset"), "store must remove soft-deleted assets");

assert(workspace.includes("omni_flash-10s"), "workspace video default must use omni_flash-10s");
assert(workspace.includes('mode: "text"'), "workspace video default mode must be text");
assert(workspace.includes("durationSec: 10"), "workspace video option must expose 10 second default");
assert(workspace.includes("fullRun: false"), "workspace video option must default to single 10 second run");
assert(workspace.includes("VideoWorkflowWorkbench"), "workspace must mount new workbench");
assert(workspace.includes("VideoWorkbenchErrorBoundary"), "formal workbench needs an isolated error boundary");
assert(!workspace.includes("VideoGenerationRunTab"), "developer diagnostics must not host the video workbench");
assert(!workspace.includes("<VideoWorkflowCanvas"), "workspace must not mount ReactFlow canvas");
assert(!workspace.includes("VideoWorkflowCanvas"), "old canvas must be removed");
assert(!workbench.includes("@xyflow/react"), "new workbench must not use ReactFlow");
assert(workbench.includes("useVideoWorkflowPolling"), "workbench must auto-poll");
assert(workbench.includes("confirmPossibleDuplicate"), "workbench must confirm uncertain retry");
assert(workbench.includes("确认生成 10 秒视频"), "workbench must confirm paid video generation before submit");
assert(workbench.includes("参考图数量"), "workbench cost confirmation must include reference count");
assert(workbench.includes("video-workflow-draft"), "workbench must persist per-project draft");
assert(workbench.includes("key={projectId}"), "workbench must remount local draft state on project change");
assert(workbench.includes("readDraft(projectId)"), "workbench must restore per-project draft");
assert(workbench.includes("submitInFlightRef"), "workbench must use a synchronous submit lock");
assert(
  workbench.includes("submitInFlightRef.current = true") &&
    workbench.includes("submitInFlightRef.current = false"),
  "workbench submit lock must be acquired and released synchronously",
);
assert(workbench.includes("const hasActiveRuns"), "workbench must derive active run state before rendering composer");
assert(workbench.includes("hasActiveRun={hasActiveRuns}"), "workbench must pass active run state to composer");
assert(composer.includes("hasActiveRun"), "composer must receive active run state");
assert(composer.includes("const submitBlocked = hasActiveRun || submitting"), "composer must block transient active submits in the click handler");
assert(composer.includes("const submitDisabled = submitBlocked || hardSubmitDisabled"), "composer must combine hard and transient submit blocks");
assert(composer.includes("disabled={submitDisabled}"), "composer must native-disable all blocked submits");
assert(composer.includes("aria-disabled={submitDisabled}"), "composer must expose submit disabled state accessibly");
assert(composer.includes("disabledReason"), "composer must explain why submit is disabled");
assert(composer.includes("已有视频任务正在生成，请等待完成后再创建新任务。"), "active run disabled reason must be user-readable");
assert(composer.includes("videoComposerSubmitLocks"), "composer must guard click entry with a module-level lock");
assert(composer.includes("videoComposerSubmitLocks.has(projectId)"), "composer click handler must check the local lock");
assert(composer.includes("videoComposerSubmitLocks.add(projectId)"), "composer click handler must acquire the local lock");
assert(composer.includes("videoComposerSubmitLocks.delete(projectId)"), "composer must release the local lock");
assert(composer.includes("onSubmit: () => Promise<boolean>"), "composer submit callback must report whether an active run was created");
assert(composer.includes("activeRunObservedRef"), "composer must keep active-run locks until an active run has been observed and settled");
assert(composer.includes("if (!keepLocked)"), "composer must not release a successful active-run lock immediately");
assert(store.includes("let keepCreateLocked = false"), "store create lock must stay held after an active run is created");
assert(store.includes("if (!keepCreateLocked)"), "store must not release active-run create locks immediately");
assert(workbench.includes("pollingState"), "workbench must surface polling connection state");
assert(workbench.includes("syncVideoWorkflowRun"), "workbench must expose manual polling retry");
assert(workbench.includes("下次重试"), "polling failures must show the next retry delay");
assert(crossTab.includes("video-workflow-sync"), "video workflow sync channel name is required");
assert(workbench.includes("VIDEO_WORKFLOW_SYNC_CHANNEL"), "workbench must subscribe to cross-tab workflow sync events");
assert(store.includes("broadcastVideoWorkflowChange"), "store must broadcast video workflow mutations to other tabs");
assert(videoErrors.includes("formatVideoWorkflowError"), "video workflow must centralize error formatting");
assert(videoErrors.includes("videoWorkflowErrorToast"), "video workflow must provide toast-safe error payloads");
assert(videoErrors.includes("追踪 ID"), "video workflow errors must include support trace id when available");
assert(videoErrors.includes("建议："), "video workflow errors must include next action text");
assert(videoErrors.includes("ACTION_LABELS"), "video workflow errors must translate API actions");
assert(workbench.includes("videoWorkflowErrorToast"), "workbench must use structured video error toasts");
assert(!workbench.includes("toast.error(result.msg ||"), "workbench must not toast raw store messages without action and trace id");

assert(assetPanel.includes("DndContext"), "asset panel must support drag ordering");
assert(assetPanel.includes("KeyboardSensor"), "asset panel must support keyboard sorting");
assert(assetPanel.includes("sortableKeyboardCoordinates"), "asset panel must use keyboard coordinates");
assert(assetPanel.includes("uploadItems"), "asset panel must show per-file upload state");
assert(uploadQueue.includes("retryableVideoWorkflowUploadFiles"), "upload queue must preserve failed files for retry");
assert(uploadQueue.includes("markVideoWorkflowUploadFailure"), "upload queue must support per-file failure states");
assert(uploadQueue.includes("markVideoWorkflowUploadUploaded"), "upload queue must support per-file success states");
assert(assetPanel.includes("retryableVideoWorkflowUploadFiles"), "asset panel must support retrying a failed single upload");
assert(assetPanel.includes("重试"), "asset panel must show a retry action for failed uploads");
assert(assetPanel.includes("部分参考图已上传"), "asset panel must explain partial upload success");
assert(assetPanel.includes("handleDragAttributes"), "selected reference drag must use a focused handle");
assert(assetPanel.includes("aria-label={`排序参考图"), "drag handle must be accessible");
assert(assetPanel.includes("maxSelected"), "asset panel must enforce reference limit");
assert(composer.includes("<video"), "composer must preview completed video");
assert(composer.includes("onLoadedMetadata"), "composer must handle video metadata loaded");
assert(composer.includes("onError"), "composer must handle video decode errors");
assert(composer.includes("重新加载"), "composer must provide video reload action");
assert(composer.includes("downloadVideoWorkflowRun"), "composer must provide source video download link");
assert(composer.includes("下载源文件"), "composer must label the source video download action");
assert(composer.includes("视频无法播放"), "composer must explain decode failures");
assert(composer.includes("生成 10 秒视频"), "composer must expose fixed action");
assert(composer.includes("provider_user_message"), "composer must show provider readiness message");
assert(history.includes("onRetry"), "history must support retry");
assert(history.includes("onReuse"), "history must support parameter reuse");
