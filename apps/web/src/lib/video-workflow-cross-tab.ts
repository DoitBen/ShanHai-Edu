export const VIDEO_WORKFLOW_SYNC_CHANNEL = "video-workflow-sync";

export const VIDEO_WORKFLOW_TAB_ID =
  typeof globalThis.crypto !== "undefined" && "randomUUID" in globalThis.crypto
    ? globalThis.crypto.randomUUID()
    : Math.random().toString(36).slice(2);
