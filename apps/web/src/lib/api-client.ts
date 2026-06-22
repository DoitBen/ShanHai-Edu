import type {
  ApiEnvelope,
  ApiManifest,
  ApiNodeDetail,
  ApiNodeMutationResult,
  ApiFeedbackResult,
  ApiPptExport,
  ApiProject,
  ApiTask,
  CreateProjectPayload,
  EditNodePayload,
  FeedbackPayload,
  GenerateNodePayload,
  VideoCapabilitiesResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN;

export function resolveApiDownloadUrl(downloadUrl: string): string {
  if (/^https?:\/\//i.test(downloadUrl)) return downloadUrl;
  return `${API_BASE}${downloadUrl.startsWith("/") ? downloadUrl : `/${downloadUrl}`}`;
}

class ApiClientError extends Error {
  code: string;
  status: number;
  retryable: boolean;

  constructor(message: string, code: string, status: number, retryable = false) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.retryable = retryable;
  }
}

function headers(extra?: HeadersInit): HeadersInit {
  return {
    Accept: "application/json",
    ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
    ...extra,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: headers(init?.headers),
    cache: "no-store",
  });

  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !payload.ok) {
    const error = payload.ok ? null : payload.error;
    const message = formatApiErrorMessage(
      error?.message || `请求失败：${response.status}`,
      error?.details,
    );
    const code = error?.code || "HTTP_ERROR";
    throw new ApiClientError(
      code === "HTTP_ERROR" ? message : `${code}: ${message}`,
      code,
      response.status,
      error?.retryable,
    );
  }
  return payload.data;
}

function formatApiErrorMessage(message: string, details: unknown): string {
  if (typeof details === "undefined" || details === null) return message;
  const detailsText =
    typeof details === "string"
      ? details
      : JSON.stringify(details);
  return detailsText ? `${message}；details: ${detailsText}` : message;
}

export async function fetchProjects(): Promise<ApiProject[]> {
  return request<ApiProject[]>("/projects");
}

export async function createProject(payload: CreateProjectPayload): Promise<ApiProject> {
  return request<ApiProject>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchProjectManifest(projectId: string): Promise<ApiManifest> {
  return request<ApiManifest>(`/projects/${encodeURIComponent(projectId)}/manifest`);
}

export async function uploadProjectTextbook(
  projectId: string,
  content: string,
  filename = "textbook.txt",
): Promise<unknown> {
  const formData = new FormData();
  formData.append(
    "file",
    new Blob([content], { type: "text/plain;charset=utf-8" }),
    filename,
  );
  return request<unknown>(`/projects/${encodeURIComponent(projectId)}/textbook`, {
    method: "POST",
    body: formData,
  });
}

export async function uploadProjectTextbookFile(
  projectId: string,
  file: File,
): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  return request<unknown>(`/projects/${encodeURIComponent(projectId)}/textbook`, {
    method: "POST",
    body: formData,
  });
}

export async function fetchProjectNode(
  projectId: string,
  nodeId: string,
): Promise<ApiNodeDetail> {
  return request<ApiNodeDetail>(
    `/projects/${encodeURIComponent(projectId)}/nodes/${encodeURIComponent(nodeId)}`,
  );
}

export async function fetchProjectTasks(projectId: string): Promise<ApiTask[]> {
  return request<ApiTask[]>(`/projects/${encodeURIComponent(projectId)}/tasks`);
}

export async function fetchProjectTask(
  projectId: string,
  taskId: string,
): Promise<ApiTask> {
  return request<ApiTask>(
    `/projects/${encodeURIComponent(projectId)}/tasks/${encodeURIComponent(taskId)}`,
  );
}

export async function retryProjectTask(
  projectId: string,
  taskId: string,
): Promise<ApiTask> {
  return request<ApiTask>(
    `/projects/${encodeURIComponent(projectId)}/tasks/${encodeURIComponent(taskId)}/retry`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
}

export async function exportProjectPpt(projectId: string): Promise<ApiPptExport> {
  return request<ApiPptExport>(`/projects/${encodeURIComponent(projectId)}/export/ppt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function generateProjectNode(
  projectId: string,
  nodeId: string,
  payload?: GenerateNodePayload,
): Promise<ApiNodeMutationResult> {
  return request<ApiNodeMutationResult>(
    `/projects/${encodeURIComponent(projectId)}/nodes/${encodeURIComponent(nodeId)}/generate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : undefined,
    },
  );
}

export async function editProjectNode(
  projectId: string,
  nodeId: string,
  payload: EditNodePayload,
): Promise<ApiNodeMutationResult> {
  return request<ApiNodeMutationResult>(
    `/projects/${encodeURIComponent(projectId)}/nodes/${encodeURIComponent(nodeId)}/edit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export async function approveProjectNode(
  projectId: string,
  nodeId: string,
  approveNote?: string,
): Promise<ApiNodeMutationResult> {
  return request<ApiNodeMutationResult>(
    `/projects/${encodeURIComponent(projectId)}/nodes/${encodeURIComponent(nodeId)}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(approveNote ? { approve_note: approveNote } : {}),
    },
  );
}

export async function submitProjectFeedback(
  projectId: string,
  payload: FeedbackPayload,
): Promise<ApiFeedbackResult> {
  return request<ApiFeedbackResult>(
    `/projects/${encodeURIComponent(projectId)}/feedback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export async function fetchVideoCapabilities(): Promise<VideoCapabilitiesResponse> {
  return request<VideoCapabilitiesResponse>("/video/capabilities");
}
