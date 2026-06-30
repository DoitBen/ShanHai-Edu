import { isApiClientError } from "./api-client";

export interface VideoWorkflowErrorView {
  title: string;
  message: string;
  action: string;
  traceId: string | null;
  retryable: boolean;
}

const ACTION_LABELS: Record<string, string> = {
  retry: "可以直接重试，系统会继续查询或重新执行可恢复步骤。",
  wait_and_retry: "请稍后再试，系统限制是为了避免重复扣费或触发上游限流。",
  wait_for_active_run: "请等待当前视频任务结束，再创建新任务。",
  resolve_conflict: "请按页面提示处理冲突后再重试。",
  fix_request: "请检查提示词、参考图和参数后再提交。",
  check_input: "请检查输入内容后再提交。",
  check_resource: "请刷新页面确认项目或素材仍然存在。",
  login_or_check_permission: "请重新登录，或确认当前账号有权限访问该项目。",
  contact_support: "请稍后重试；如果多次失败，把追踪 ID 发给技术支持。",
};

export function formatVideoWorkflowError(error: unknown, fallbackTitle: string): VideoWorkflowErrorView {
  if (isApiClientError(error)) {
    return {
      title: fallbackTitle,
      message: normalizeErrorMessage(error.message),
      action: actionLabel(error.action, error.retryable),
      traceId: error.traceId,
      retryable: error.retryable,
    };
  }

  const message = error instanceof Error ? error.message : "";
  return {
    title: fallbackTitle,
    message: normalizeErrorMessage(message || fallbackTitle),
    action: ACTION_LABELS.contact_support,
    traceId: null,
    retryable: false,
  };
}

export function videoWorkflowErrorToast(error: unknown, fallbackTitle: string): {
  title: string;
  description: string;
} {
  const view = formatVideoWorkflowError(error, fallbackTitle);
  const parts = [view.message, `建议：${view.action}`];
  if (view.traceId) parts.push(`追踪 ID：${view.traceId}`);
  return {
    title: view.title,
    description: parts.join("\n"),
  };
}

function actionLabel(action: string | null, retryable: boolean): string {
  if (action && ACTION_LABELS[action]) return ACTION_LABELS[action];
  if (retryable) return ACTION_LABELS.retry;
  return ACTION_LABELS.contact_support;
}

function normalizeErrorMessage(message: string): string {
  if (/networkerror|failed to fetch|load failed|fetch resource/i.test(message)) {
    return "网络连接失败，请检查网络后重试。";
  }
  const detailsIndex = message.indexOf("；details:");
  if (detailsIndex >= 0) return message.slice(0, detailsIndex).trim();
  return message.trim() || "视频任务处理失败。";
}
