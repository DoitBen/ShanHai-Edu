import { ApiClientError } from "./api-client";
import { formatVideoWorkflowError, videoWorkflowErrorToast } from "./video-workflow-errors";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const retryable = new ApiClientError(
  "上游视频服务超时",
  "VIDEO_PROVIDER_TEMPORARY_FAILURE",
  502,
  true,
  { provider_phase: "query", upstream_body: "raw provider detail" },
  "retry",
  "trace_demo123",
);

const formattedRetryable = formatVideoWorkflowError(retryable, "视频任务同步失败");

assert(formattedRetryable.title === "视频任务同步失败", "title must use the caller context");
assert(formattedRetryable.message === "上游视频服务超时", "message must preserve user-facing API message");
assert(formattedRetryable.action === "可以直接重试，系统会继续查询或重新执行可恢复步骤。", "retry action must be translated to Chinese");
assert(formattedRetryable.traceId === "trace_demo123", "trace id must be preserved for support");
assert(!formattedRetryable.message.includes("details"), "message must not show raw details marker");
assert(!formattedRetryable.message.includes("upstream_body"), "message must not leak structured provider details");
assert(!formattedRetryable.message.includes("VIDEO_PROVIDER_TEMPORARY_FAILURE"), "message must not show internal error code");

const toastPayload = videoWorkflowErrorToast(retryable, "视频任务同步失败");
assert(toastPayload.description.includes("上游视频服务超时"), "toast description must include the user message");
assert(toastPayload.description.includes("建议：可以直接重试"), "toast description must include the suggested action");
assert(toastPayload.description.includes("追踪 ID：trace_demo123"), "toast description must include trace id");
assert(!toastPayload.description.includes("VIDEO_PROVIDER_TEMPORARY_FAILURE"), "toast must hide internal code");

const conflict = new ApiClientError(
  "当前项目已有视频任务正在生成，请等待完成后再创建新任务",
  "VIDEO_WORKFLOW_ACTIVE_RUN_EXISTS",
  409,
  false,
  null,
  "wait_for_active_run",
  "trace_wait456",
);
const formattedConflict = formatVideoWorkflowError(conflict, "视频任务创建失败");
assert(formattedConflict.action === "请等待当前视频任务结束，再创建新任务。", "active run action must be specific");

const unknown = formatVideoWorkflowError(new Error("NetworkError when attempting to fetch resource"), "视频任务创建失败");
assert(unknown.message === "网络连接失败，请检查网络后重试。", "network errors must be user-friendly");
assert(unknown.action === "请稍后重试；如果多次失败，把追踪 ID 发给技术支持。", "unknown fallback action must be helpful");
