import type {
  ApiEnvelope,
  ApiManifest,
  ApiNodeDetail,
  ApiNodeMutationResult,
  ApiFeedbackResult,
  ApiPptExport,
  ApiProject,
  ApiTextbookLibrary,
  ApiTextbookKnowledgePoints,
  ApiTextbookKnowledgePointAsset,
  ApiTextbookAssetBatchResult,
  ApiTextbookUploadResult,
  ApiTextbookParseJob,
  ApiLessonPlanLibrary,
  ApiLessonPlanLibraryItem,
  ApiTask,
  ApiProjectWorkspace,
  AdminRule,
  AdminRuleAuditLog,
  AdminRuleVersion,
  AdminWorkflowGraph,
  CreateProjectPayload,
  CreateAdminRuleVersionPayload,
  EditNodePayload,
  FeedbackPayload,
  GenerateNodePayload,
  UploadLessonPlanLibraryMetadata,
  VideoCapabilitiesResponse,
} from "./types";

const API_BASE = "/api/backend";

export function resolveApiDownloadUrl(downloadUrl: string): string {
  if (/^https?:\/\//i.test(downloadUrl)) return downloadUrl;
  return `${API_BASE}${downloadUrl.startsWith("/") ? downloadUrl : `/${downloadUrl}`}`;
}

export function resolveProjectFileUrl(projectId: string, relPath: string): string {
  const cleanPath = relPath.replace(/^\/+/, "");
  return `${API_BASE}/projects/${encodeURIComponent(projectId)}/${cleanPath}`;
}

class ApiClientError extends Error {
  code: string;
  status: number;
  retryable: boolean;
  details: unknown;

  constructor(message: string, code: string, status: number, retryable = false, details: unknown = null) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.retryable = retryable;
    this.details = details;
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export interface ApproveNodeOptions {
  approve_note?: string;
  override_warning_rule_ids?: string[];
  override_reason?: string;
}

function headers(extra?: HeadersInit): HeadersInit {
  return {
    Accept: "application/json",
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
      error?.details,
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

export async function updateProject(
  projectId: string,
  payload: Partial<CreateProjectPayload>,
): Promise<ApiProject> {
  return request<ApiProject>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchProjectManifest(projectId: string): Promise<ApiManifest> {
  return request<ApiManifest>(`/projects/${encodeURIComponent(projectId)}/manifest`);
}

export async function fetchProjectWorkspace(projectId: string): Promise<ApiProjectWorkspace> {
  return request<ApiProjectWorkspace>(`/projects/${encodeURIComponent(projectId)}/workspace`);
}

export async function fetchTextbookLibrary(): Promise<ApiTextbookLibrary> {
  return request<ApiTextbookLibrary>("/textbook-library");
}

export async function uploadTextbookToLibrary(file: File): Promise<ApiTextbookUploadResult> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  return request<ApiTextbookUploadResult>("/textbook-library/uploads", {
    method: "POST",
    body: formData,
  });
}

export async function fetchTextbookParseJob(jobId: string): Promise<ApiTextbookParseJob> {
  return request<ApiTextbookParseJob>(`/textbook-library/jobs/${encodeURIComponent(jobId)}`);
}

export async function fetchTextbookKnowledgePoints(textbookId: string): Promise<ApiTextbookKnowledgePoints> {
  return request<ApiTextbookKnowledgePoints>(`/textbook-library/${encodeURIComponent(textbookId)}/knowledge-points`);
}

export async function fetchTextbookKnowledgePointAsset(
  textbookId: string,
  knowledgePointId: string,
): Promise<ApiTextbookKnowledgePointAsset> {
  return request<ApiTextbookKnowledgePointAsset>(
    `/textbook-library/${encodeURIComponent(textbookId)}/knowledge-points/${encodeURIComponent(knowledgePointId)}/assets`,
  );
}

export async function splitTextbookKnowledgePointAssets(
  textbookId: string,
  knowledgePointIds?: string[],
): Promise<ApiTextbookAssetBatchResult> {
  return request<ApiTextbookAssetBatchResult>(
    `/textbook-library/${encodeURIComponent(textbookId)}/split`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ knowledge_point_ids: knowledgePointIds || [] }),
    },
  );
}

export async function extractTextbookKnowledgePointAssets(
  textbookId: string,
  knowledgePointIds?: string[],
): Promise<ApiTextbookAssetBatchResult> {
  return request<ApiTextbookAssetBatchResult>(
    `/textbook-library/${encodeURIComponent(textbookId)}/assets/extract`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ knowledge_point_ids: knowledgePointIds || [] }),
    },
  );
}

export async function extractTextbookKnowledgePointAsset(
  textbookId: string,
  knowledgePointId: string,
): Promise<ApiTextbookKnowledgePointAsset> {
  return request<ApiTextbookKnowledgePointAsset>(
    `/textbook-library/${encodeURIComponent(textbookId)}/knowledge-points/${encodeURIComponent(knowledgePointId)}/assets/extract`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
}

export async function confirmTextbookKnowledgePointAsset(
  assetId: string,
): Promise<ApiTextbookKnowledgePointAsset> {
  return request<ApiTextbookKnowledgePointAsset>(`/textbook-library/assets/${encodeURIComponent(assetId)}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer: "teacher-ui" }),
  });
}

export async function fetchLessonPlanLibrary(params: {
  textbookId?: string;
  knowledgePointId?: string;
} = {}): Promise<ApiLessonPlanLibrary> {
  const search = new URLSearchParams();
  if (params.textbookId) search.set("textbook_id", params.textbookId);
  if (params.knowledgePointId) search.set("knowledge_point_id", params.knowledgePointId);
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ApiLessonPlanLibrary>(`/lesson-plan-library${suffix}`);
}

export async function fetchLessonPlanLibraryItem(lessonPlanId: string): Promise<ApiLessonPlanLibraryItem> {
  return request<ApiLessonPlanLibraryItem>(`/lesson-plan-library/${encodeURIComponent(lessonPlanId)}`);
}

export async function uploadLessonPlanToLibrary(
  file: File,
  metadata: UploadLessonPlanLibraryMetadata = {},
): Promise<ApiLessonPlanLibraryItem> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  if (metadata.textbook_id) formData.append("textbook_id", metadata.textbook_id);
  if (metadata.textbook_version_id) {
    formData.append("textbook_version_id", metadata.textbook_version_id);
  }
  if (metadata.knowledge_point_id) {
    formData.append("knowledge_point_id", metadata.knowledge_point_id);
  }
  if (metadata.created_by) formData.append("created_by", metadata.created_by);
  return request<ApiLessonPlanLibraryItem>("/lesson-plan-library/uploads", {
    method: "POST",
    body: formData,
  });
}

export async function importLessonPlanFromProject(
  projectId: string,
): Promise<ApiLessonPlanLibraryItem> {
  return request<ApiLessonPlanLibraryItem>("/lesson-plan-library/import/from-project", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, created_by: "teacher-ui" }),
  });
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

export async function attachProjectTextbookFromLibrary(
  projectId: string,
  textbookId: string,
): Promise<unknown> {
  return request<unknown>(
    `/projects/${encodeURIComponent(projectId)}/textbook/from-library/${encodeURIComponent(textbookId)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
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
  options?: string | ApproveNodeOptions,
): Promise<ApiNodeMutationResult> {
  const payload =
    typeof options === "string"
      ? { approve_note: options }
      : options || {};
  return request<ApiNodeMutationResult>(
    `/projects/${encodeURIComponent(projectId)}/nodes/${encodeURIComponent(nodeId)}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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

export async function fetchAdminRules(): Promise<AdminRule[]> {
  return request<AdminRule[]>("/admin/rules");
}

export async function fetchAdminRule(ruleId: string): Promise<AdminRule> {
  return request<AdminRule>(`/admin/rules/${encodeURIComponent(ruleId)}`);
}

export async function fetchAdminRuleAudit(): Promise<AdminRuleAuditLog[]> {
  return request<AdminRuleAuditLog[]>("/admin/rules/audit");
}

export async function fetchAdminWorkflowGraph(): Promise<AdminWorkflowGraph> {
  return request<AdminWorkflowGraph>("/admin/workflow/graph");
}

export async function createAdminRuleVersion(
  ruleId: string,
  payload: CreateAdminRuleVersionPayload,
): Promise<AdminRuleVersion> {
  return request<AdminRuleVersion>(`/admin/rules/${encodeURIComponent(ruleId)}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function activateAdminRuleVersion(
  ruleId: string,
  versionId: string,
  notes?: string,
): Promise<{ active_version: AdminRuleVersion; rule_set_version: unknown }> {
  return request<{ active_version: AdminRuleVersion; rule_set_version: unknown }>(
    `/admin/rules/${encodeURIComponent(ruleId)}/activate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        version_id: versionId,
        actor: "admin-ui",
        notes,
      }),
    },
  );
}

export async function rollbackAdminRuleVersion(
  ruleId: string,
  versionId: string,
  notes?: string,
): Promise<{ active_version: AdminRuleVersion; rule_set_version: unknown }> {
  return request<{ active_version: AdminRuleVersion; rule_set_version: unknown }>(
    `/admin/rules/${encodeURIComponent(ruleId)}/rollback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        version_id: versionId,
        actor: "admin-ui",
        notes,
      }),
    },
  );
}
