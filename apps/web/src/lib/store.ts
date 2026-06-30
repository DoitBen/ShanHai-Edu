"use client";

import { create } from "zustand";
import type {
  AuthUser,
  DataMode,
  LoadStatus,
  PendingRuleWarning,
  ProjectMeta,
  ApiProjectWorkspace,
  ApiTask,
  WorkflowStage,
  VideoIntroPlan,
  VideoReferenceAsset,
  VideoWorkflowGraph,
  VideoWorkflowResponse,
  VideoWorkflowRun,
  VideoWorkflowRunRequest,
  VideoWorkflowRetryRequest,
  VideoWorkflowUploadError,
  ScreenKey,
  NewProjectDraft,
  Role,
  VideoModelOption,
  ImageWorkbenchRun,
  ImageWorkbenchRunRequest,
  MediaWorkbenchResponse,
  VideoWorkbenchRun,
  VideoWorkbenchRunRequest,
} from "./types";
import {
  MOCK_PROJECTS,
  buildStagesForProject,
  MOCK_VIDEO_PLANS,
} from "./mock-data";
import { DEMO_PASSWORD, isDemoMode } from "./demo-mode";
import { nextStageKey } from "./workflow";
import {
  approveProjectNode,
  attachProjectTextbookFromLibrary,
  createProject,
  editProjectNode,
  fetchLessonPlanLibrary,
  fetchTextbookLibrary,
  fetchTextbookParseJob,
  fetchTextbookKnowledgePointAsset,
  splitTextbookKnowledgePointAssets,
  extractTextbookKnowledgePointAssets,
  fetchProjectManifest,
  fetchProjectNode,
  fetchProjectWorkspace,
  fetchProjectTask,
  fetchProjectTasks,
  fetchProjects,
  fetchVideoWorkflow,
  fetchMediaWorkbench,
  generateProjectNode,
  retryProjectTask as retryProjectTaskRequest,
  saveVideoWorkflow,
  createVideoWorkflowRun as createVideoWorkflowRunRequest,
  deleteVideoWorkflowAsset,
  retryVideoWorkflowRun as retryVideoWorkflowRunRequest,
  syncVideoWorkflowRun as syncVideoWorkflowRunRequest,
  uploadVideoWorkflowAssets,
  createImageWorkbenchRun as createImageWorkbenchRunRequest,
  createVideoWorkbenchRun as createVideoWorkbenchRunRequest,
  importMediaWorkbenchVideoReferences,
  syncVideoWorkbenchRun as syncVideoWorkbenchRunRequest,
  uploadMediaWorkbenchVideoReferences,
  submitProjectFeedback,
  updateProject,
  uploadTextbookToLibrary,
  isApiClientError,
} from "./api-client";
import { VIDEO_WORKFLOW_SYNC_CHANNEL, VIDEO_WORKFLOW_TAB_ID } from "./video-workflow-cross-tab";
import { formatVideoWorkflowError } from "./video-workflow-errors";
import {
  draftToCreateProjectPayload,
  mapApiManifest,
  mapApiNodeDetailToStage,
  mapApiNodeMutationToStage,
  mapApiProject,
  mapTextbookParseContent,
} from "./api-mappers";

const AUTH_KEY = "shanhai_auth";
const videoWorkflowCreateLocks = new Set<string>();

function hasActiveVideoWorkflowRun(workflow?: VideoWorkflowResponse): boolean {
  return Boolean(
    workflow?.runs?.some(isActiveVideoWorkflowRun),
  );
}

function isActiveVideoWorkflowRun(run: VideoWorkflowRun): boolean {
  return (
    run.status === "submitting" ||
    run.status === "queued" ||
    run.status === "processing" ||
    run.status === "completed_pending_download"
  );
}

function releaseVideoWorkflowCreateLockIfSettled(projectId: string, workflow?: VideoWorkflowResponse) {
  if (!hasActiveVideoWorkflowRun(workflow)) videoWorkflowCreateLocks.delete(projectId);
}

function upsertVideoRun(
  workflow: VideoWorkflowResponse,
  run: VideoWorkflowRun,
): VideoWorkflowResponse {
  return {
    ...workflow,
    runs: [run, ...(workflow.runs || []).filter((item) => item.run_id !== run.run_id)]
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
      .slice(0, 50),
    latest_run: run,
  };
}

function broadcastVideoWorkflowChange(projectId: string, reason: "asset" | "run" | "graph") {
  if (typeof window === "undefined") return;
  const message = JSON.stringify({
    type: VIDEO_WORKFLOW_SYNC_CHANNEL,
    projectId,
    reason,
    source: VIDEO_WORKFLOW_TAB_ID,
    at: Date.now(),
  });
  try {
    const channel = new BroadcastChannel(VIDEO_WORKFLOW_SYNC_CHANNEL);
    channel.postMessage(message);
    channel.close();
  } catch {
    // BroadcastChannel is not available in every embedded browser; storage keeps same-origin tabs in sync.
  }
  try {
    window.localStorage.setItem(VIDEO_WORKFLOW_SYNC_CHANNEL, message);
  } catch {
    // Ignore private-mode or quota failures; the current tab already has the local mutation.
  }
}

const DATA_MODE: DataMode = isDemoMode() ? "demo" : "api";
const INITIAL_PROJECTS: ProjectMeta[] = DATA_MODE === "demo" ? MOCK_PROJECTS : [];
const INITIAL_STAGES_BY_PROJECT: Record<string, WorkflowStage[]> =
  DATA_MODE === "demo"
    ? {
        "demo-001": buildStagesForProject("demo-001"),
        "demo-002": buildStagesForProject("demo-002"),
        "demo-003": buildStagesForProject("demo-003"),
      }
    : {};
const INITIAL_VIDEO_PLANS_BY_PROJECT: Record<string, VideoIntroPlan[]> =
  DATA_MODE === "demo"
    ? {
        "demo-001": MOCK_VIDEO_PLANS.map((p) => ({ ...p })),
      }
    : {};

/* ---------------- Auth ---------------- */

function loadAuth(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(AUTH_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

function saveAuth(user: AuthUser | null) {
  if (typeof window === "undefined") return;
  if (user) {
    const encoded = encodeURIComponent(JSON.stringify(user));
    window.localStorage.setItem(AUTH_KEY, JSON.stringify(user));
    document.cookie = `${AUTH_KEY}=${encoded}; Path=/; SameSite=Lax`;
  } else {
    window.localStorage.removeItem(AUTH_KEY);
    document.cookie = `${AUTH_KEY}=; Path=/; Max-Age=0; SameSite=Lax`;
  }
}

function extractRuleWarnings(details: unknown): PendingRuleWarning["warnings"] {
  const maybeDetails = details && typeof details === "object" ? details as Record<string, unknown> : {};
  const warnings = Array.isArray(maybeDetails.warnings) ? maybeDetails.warnings : [];
  return warnings
    .filter((item): item is Record<string, unknown> => item !== null && typeof item === "object")
    .map((item) => ({
      rule_id: typeof item.rule_id === "string" ? item.rule_id : "UNKNOWN_RULE",
      message: typeof item.message === "string" ? item.message : undefined,
      severity: typeof item.severity === "string" ? item.severity : "warning",
      details: item.details,
    }));
}

/* ---------------- 新建项目草稿 ---------------- */

export const EMPTY_DRAFT: NewProjectDraft = {
  step: 1,
  sourceMode: "textbook-library",
  name: "",
  nameEdited: false,
  subject: "数学",
  grade: "三年级",
  textbookVersion: "人教版",
  volume: "上册",
  lessonType: "新授课",
  characterProfile:
    "主角使用非写实卡通学生形象；锁定服装、发型和配色，不出现可识别真实儿童脸。",
  characterSafetyRule:
    "禁真人、photorealistic、真实课堂实拍感；所有儿童角色必须为非写实卡通或剪影风格。",
  visualPalette: "暖纸白 #F6F5F1、深青灰 #2D4356、古铜金 #9C7C4E",
  visualStyleKeywords: "温润、克制、真实生活情境、可编辑 PPT 视觉资产",
  fontPreference: "系统无衬线中文优先，正文清晰，数学内容必须可编辑",
  complianceNotes:
    "中文旁白可配置声线；禁英文配音；完整视频必须多分镜拼接；候选不得冒充终版。",
  apiProjectId: null,
  textbookFileName: "",
  textbookContent: "",
  parseResult: null,
  parseStatus: "idle",
  parseError: null,
  selectedKnowledgePointId: "",
  selectedAssetKnowledgePointIds: [],
  assetActionStatus: "idle",
  selectedLessonReferenceId: undefined,
  lessonReferences: [],
  lessonPlanFileName: "",
  lessonPlanContent: "",
  lessonPlanSummary: "",
  videoPurpose: "课堂导入",
  videoTypes: ["science", "application", "story"],
  videoCountPerType: 3,
  videoTheme: "",
  audience: "三年级学生",
  duration: "90秒",
  creativeBrief: "",
  pptStyle: "清新简约",
  pptSlides: 18,
  pptStructure: "导入-探究-归纳-练习-小结",
  outputPath: "/output/",
  constraints: "",
  safeMode: true,
};

/* ---------------- Store ---------------- */

interface AppState {
  dataMode: DataMode;

  // auth
  user: AuthUser | null;
  authReady: boolean;
  login: (username: string, password: string) => { ok: boolean; msg?: string };
  logout: () => void;
  switchRole: (role: Role) => void;

  // navigation
  screen: ScreenKey;
  activeProjectId: string | null;
  go: (screen: ScreenKey) => void;
  openProject: (projectId: string) => void;

  // projects
  projects: ProjectMeta[];
  stagesByProject: Record<string, WorkflowStage[]>;
  videoPlansByProject: Record<string, VideoIntroPlan[]>;
  projectsStatus: LoadStatus;
  projectsError: string | null;
  manifestStatusByProject: Record<string, LoadStatus>;
  manifestErrorByProject: Record<string, string | null>;
  nodeStatusByProject: Record<string, Record<string, LoadStatus>>;
  nodeErrorByProject: Record<string, Record<string, string | null>>;
  stageActionStatusByProject: Record<string, Record<string, LoadStatus>>;
  stageActionErrorByProject: Record<string, Record<string, string | null>>;
  pendingRuleWarningByProject: Record<string, Record<string, PendingRuleWarning | null>>;
  tasksByProject: Record<string, ApiTask[]>;
  tasksStatusByProject: Record<string, LoadStatus>;
  tasksErrorByProject: Record<string, string | null>;
  workspaceByProject: Record<string, ApiProjectWorkspace>;
  workspaceStatusByProject: Record<string, LoadStatus>;
  workspaceErrorByProject: Record<string, string | null>;
  videoWorkflowByProject: Record<string, VideoWorkflowResponse>;
  videoWorkflowStatusByProject: Record<string, LoadStatus>;
  videoWorkflowErrorByProject: Record<string, string | null>;
  mediaWorkbench: MediaWorkbenchResponse | null;
  mediaWorkbenchStatus: LoadStatus;
  mediaWorkbenchError: string | null;
  loadProjects: () => Promise<void>;
  createProjectFromDraft: () => Promise<string>;
  loadProjectManifest: (projectId: string) => Promise<void>;
  loadProjectWorkspace: (projectId: string) => Promise<void>;
  loadProjectNode: (projectId: string, stageKey: string) => Promise<void>;
  loadProjectTasks: (projectId: string) => Promise<void>;
  refreshProjectTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  retryProjectTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  loadVideoWorkflow: (projectId: string) => Promise<void>;
  saveVideoWorkflowGraph: (projectId: string, graph: VideoWorkflowGraph) => Promise<{ ok: boolean; msg?: string; error?: unknown }>;
  uploadVideoWorkflowReferences: (
    projectId: string,
    files: File[],
  ) => Promise<{
    ok: boolean;
    msg?: string;
    error?: unknown;
    assets?: VideoReferenceAsset[];
    errors?: VideoWorkflowUploadError[];
  }>;
  createVideoWorkflowRun: (
    projectId: string,
    payload: VideoWorkflowRunRequest,
  ) => Promise<{ ok: boolean; msg?: string; error?: unknown; run?: VideoWorkflowRun }>;
  syncVideoWorkflowRun: (projectId: string, runId: string) => Promise<{ ok: boolean; msg?: string; error?: unknown; run?: VideoWorkflowRun }>;
  removeVideoWorkflowAsset: (projectId: string, assetId: string) => Promise<{ ok: boolean; msg?: string; error?: unknown }>;
  replaceVideoWorkflowRun: (projectId: string, run: VideoWorkflowRun) => void;
  retryVideoWorkflowRun: (
    projectId: string,
    runId: string,
    options?: { confirmPossibleDuplicate?: boolean },
  ) => Promise<{ ok: boolean; msg?: string; error?: unknown; run?: VideoWorkflowRun }>;
  loadMediaWorkbench: () => Promise<void>;
  createImageWorkbenchRun: (payload: ImageWorkbenchRunRequest) => Promise<{ ok: boolean; msg?: string; run?: ImageWorkbenchRun }>;
  uploadMediaWorkbenchReferences: (files: File[]) => Promise<{ ok: boolean; msg?: string }>;
  importImagesToVideoReferences: (assetIds: string[]) => Promise<{ ok: boolean; msg?: string }>;
  createVideoWorkbenchRun: (payload: VideoWorkbenchRunRequest) => Promise<{ ok: boolean; msg?: string; run?: VideoWorkbenchRun }>;
  syncVideoWorkbenchRun: (runId: string) => Promise<{ ok: boolean; msg?: string; run?: VideoWorkbenchRun }>;
  parseDraftTextbook: (
    file: File,
    knowledgePointId?: string,
  ) => Promise<{ ok: boolean; msg?: string }>;
  selectDraftKnowledgePoint: (
    knowledgePointId: string,
    options?: { force?: boolean },
  ) => Promise<{ ok: boolean; msg?: string }>;
  loadTextbookFromLibrary: (textbookId?: string) => Promise<{ ok: boolean; msg?: string }>;
  splitDraftTextbookAssets: (knowledgePointIds?: string[]) => Promise<{ ok: boolean; msg?: string }>;
  extractDraftTextbookAssets: (knowledgePointIds?: string[]) => Promise<{ ok: boolean; msg?: string }>;
  selectDraftLessonReference: (lessonPlanId: string) => Promise<{ ok: boolean; msg?: string }>;
  generateStage: (
    projectId: string,
    stageKey: string,
    option?: VideoModelOption,
  ) => Promise<{ ok: boolean; msg?: string }>;
  approveStageRemote: (
    projectId: string,
    stageKey: string,
    options?: { override_warning_rule_ids?: string[]; override_reason?: string },
  ) => Promise<{ ok: boolean; msg?: string }>;
  editStageRemote: (
    projectId: string,
    stageKey: string,
    content: unknown,
  ) => Promise<{ ok: boolean; msg?: string }>;
  submitDeliveryFeedback: (
    projectId: string,
    payload: Record<string, unknown>,
  ) => Promise<{ ok: boolean; msg?: string }>;

  // project actions
  approveStage: (projectId: string, stageKey: string) => void;
  rejectStage: (projectId: string, stageKey: string) => void;
  runStage: (projectId: string, stageKey: string) => void;
  saveStageInput: (projectId: string, stageKey: string, input: string) => void;
  acceptVideoPlan: (projectId: string, planId: string) => void;

  // new project draft
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
  resetDraft: () => void;
  commitDraftToProject: () => string; // returns new project id

  // mobile sidebar
  mobileNavOpen: boolean;
  setMobileNavOpen: (v: boolean) => void;

  // command palette
  commandOpen: boolean;
  setCommandOpen: (v: boolean) => void;
  toggleCommand: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  dataMode: DATA_MODE,

  user: null,
  authReady: false,
  login: (username, password) => {
    if (!isDemoMode()) {
      saveAuth(null);
      set({ user: null });
      return { ok: false, msg: "真实 API 模式未接入后端登录，禁止使用本地账号进入工作台" };
    }
    if (username === "admin" && password === DEMO_PASSWORD) {
      const user: AuthUser = {
        username,
        role: "admin",
        displayName: "管理员",
        loginAt: new Date().toISOString(),
      };
      saveAuth(user);
      set({ user });
      return { ok: true };
    }
    if (username === "teacher" && password === DEMO_PASSWORD) {
      const user: AuthUser = {
        username,
        role: "teacher",
        displayName: "演示教师",
        loginAt: new Date().toISOString(),
      };
      saveAuth(user);
      set({ user });
      return { ok: true };
    }
    return { ok: false, msg: "账号或密码不正确" };
  },
  logout: () => {
    saveAuth(null);
    set({ user: null, screen: "dashboard", activeProjectId: null });
  },
  switchRole: (role) => {
    if (!isDemoMode()) return;
    const u = get().user;
    if (!u) return;
    const next: AuthUser = { ...u, role, displayName: role === "admin" ? "管理员" : "演示教师" };
    saveAuth(next);
    set({ user: next });
  },

  screen: "dashboard",
  activeProjectId: null,
  go: (screen) => set({ screen }),
  openProject: (projectId) => {
    set({ activeProjectId: projectId, screen: "project" });
    if (get().dataMode === "api") {
      void get().loadProjectManifest(projectId);
    }
  },

  projects: INITIAL_PROJECTS,
  stagesByProject: INITIAL_STAGES_BY_PROJECT,
  videoPlansByProject: INITIAL_VIDEO_PLANS_BY_PROJECT,
  projectsStatus: DATA_MODE === "demo" ? "ready" : "idle",
  projectsError: null,
  manifestStatusByProject: {},
  manifestErrorByProject: {},
  nodeStatusByProject: {},
  nodeErrorByProject: {},
  stageActionStatusByProject: {},
  stageActionErrorByProject: {},
  pendingRuleWarningByProject: {},
  tasksByProject: {},
  tasksStatusByProject: {},
  tasksErrorByProject: {},
  workspaceByProject: {},
  workspaceStatusByProject: {},
  workspaceErrorByProject: {},
  videoWorkflowByProject: {},
  videoWorkflowStatusByProject: {},
  videoWorkflowErrorByProject: {},
  mediaWorkbench: null,
  mediaWorkbenchStatus: "idle",
  mediaWorkbenchError: null,

  loadProjects: async () => {
    if (get().dataMode === "demo") {
      set({ projectsStatus: "ready", projectsError: null });
      return;
    }
    if (get().projectsStatus === "loading") return;
    set({ projectsStatus: "loading", projectsError: null });
    try {
      const apiProjects = await fetchProjects();
      const manifestResults = await Promise.allSettled(
        apiProjects.map((project) => fetchProjectManifest(project.project_id)),
      );
      const workspaceResults = await Promise.allSettled(
        apiProjects.map((project) => fetchProjectWorkspace(project.project_id)),
      );
      const nextStagesByProject = { ...get().stagesByProject };
      const nextManifestStatusByProject = { ...get().manifestStatusByProject };
      const nextManifestErrorByProject = { ...get().manifestErrorByProject };
      const nextWorkspaceByProject = { ...get().workspaceByProject };
      const nextWorkspaceStatusByProject = { ...get().workspaceStatusByProject };
      const nextWorkspaceErrorByProject = { ...get().workspaceErrorByProject };
      const projects = apiProjects.map((project, index) => {
        const manifestResult = manifestResults[index];
        const workspaceResult = workspaceResults[index];
        if (workspaceResult?.status === "fulfilled") {
          nextWorkspaceByProject[project.project_id] = workspaceResult.value;
          nextWorkspaceStatusByProject[project.project_id] = "ready";
          nextWorkspaceErrorByProject[project.project_id] = null;
        } else {
          nextWorkspaceStatusByProject[project.project_id] = "error";
          nextWorkspaceErrorByProject[project.project_id] =
            workspaceResult?.status === "rejected" && workspaceResult.reason instanceof Error
              ? workspaceResult.reason.message
              : "workspace 摘要读取失败";
        }
        if (manifestResult?.status === "fulfilled") {
          const mapped = mapApiManifest(manifestResult.value);
          nextStagesByProject[mapped.project.id] = mapped.stages;
          nextManifestStatusByProject[mapped.project.id] = "ready";
          nextManifestErrorByProject[mapped.project.id] = null;
          return mapped.project;
        }

        const existing = get().projects.find((item) => item.id === project.project_id);
        nextManifestStatusByProject[project.project_id] = "error";
        nextManifestErrorByProject[project.project_id] =
          manifestResult?.status === "rejected" && manifestResult.reason instanceof Error
            ? manifestResult.reason.message
            : "manifest 摘要读取失败";
        return existing || mapApiProject(project);
      });
      set({
        projects,
        stagesByProject: nextStagesByProject,
        manifestStatusByProject: nextManifestStatusByProject,
        manifestErrorByProject: nextManifestErrorByProject,
        workspaceByProject: nextWorkspaceByProject,
        workspaceStatusByProject: nextWorkspaceStatusByProject,
        workspaceErrorByProject: nextWorkspaceErrorByProject,
        projectsStatus: "ready",
        projectsError: null,
      });
    } catch (error) {
      set({
        projectsStatus: "error",
        projectsError: error instanceof Error ? error.message : "项目列表读取失败",
      });
    }
  },

  createProjectFromDraft: async () => {
    if (get().dataMode === "demo") {
      return get().commitDraftToProject();
    }
    const draft = get().draft;
    const payload = draftToCreateProjectPayload(draft);
    const project = draft.apiProjectId
      ? await updateProject(draft.apiProjectId, payload)
      : await createProject(payload);
    const projectId = draft.apiProjectId || project?.project_id;
    if (!projectId) {
      throw new Error("项目创建失败：缺少后端项目 ID");
    }
    const mapped = project
      ? mapApiProject(project)
      : mapApiProject((await fetchProjects()).find((item) => item.project_id === projectId) || {
          project_id: projectId,
          name: draft.name.trim() || "未命名项目",
          subject: draftToCreateProjectPayload(draft).subject,
          grade: draftToCreateProjectPayload(draft).grade,
          textbook_version: draftToCreateProjectPayload(draft).textbook_version,
          volume: draftToCreateProjectPayload(draft).volume,
          lesson_type: draftToCreateProjectPayload(draft).lesson_type,
          created_at: new Date().toISOString(),
          status: "active",
          project_dir: "",
        });
    const libraryTextbookId = draft.parseResult?.textbookId;
    if (draft.sourceMode === "textbook-library" && !draft.apiProjectId && libraryTextbookId) {
      await attachProjectTextbookFromLibrary(mapped.id, libraryTextbookId);
    }
    set({
      projects: [mapped, ...get().projects.filter((item) => item.id !== mapped.id)],
      draft: { ...EMPTY_DRAFT },
    });
    await get().loadProjectManifest(mapped.id);
    await get().loadProjectWorkspace(mapped.id);
    return mapped.id;
  },

  parseDraftTextbook: async (file, knowledgePointId) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材解析接口" };
    }
    const draft = get().draft;
    set({
      draft: {
        ...draft,
        textbookFileName: file.name,
        parseStatus: "parsing",
        parseError: null,
      },
    });
    try {
      const latestDraft = get().draft;
      let projectId = latestDraft.apiProjectId;
      if (!projectId) {
        const project = await createProject(
          draftToCreateProjectPayload(latestDraft, {
            fallbackName: `教材解析临时项目-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "")}`,
          }),
        );
        projectId = project.project_id;
        set({
          projects: [
            mapApiProject(project),
            ...get().projects.filter((item) => item.id !== project.project_id),
          ],
          draft: {
            ...get().draft,
            apiProjectId: projectId,
          },
        });
      }

      const uploaded = await uploadTextbookToLibrary(file);
      const job = await fetchTextbookParseJob(uploaded.job_id);
      if (job.status === "failed") {
        throw new Error(job.error_message || "教材入库解析失败");
      }
      await updateProject(projectId, {
        textbook_id: uploaded.textbook_id,
        textbook_version_id: uploaded.textbook_version_id,
      });
      await attachProjectTextbookFromLibrary(projectId, uploaded.textbook_id);
      const generated = await generateProjectNode(
        projectId,
        "textbook_parse",
        knowledgePointId ? { knowledge_point_id: knowledgePointId } : undefined,
      );
      let parsed = mapTextbookParseContent(
        generated.content,
        get().draft,
      );
      parsed = await enrichParseResultWithLibraryAsset(parsed);
      const currentDraft = get().draft;
      const nextDraft: NewProjectDraft = {
        ...currentDraft,
        name: currentDraft.nameEdited ? currentDraft.name : suggestedProjectName(parsed),
        subject: parsed.subject,
        grade: parsed.grade,
        textbookVersion: parsed.textbookVersion,
        volume: parsed.volume,
        audience: currentDraft.audience === EMPTY_DRAFT.audience ? `${parsed.grade}学生` : currentDraft.audience,
        parseStatus: "done" as const,
        parseResult: parsed,
        parseError: null,
        selectedKnowledgePointId:
          parsed.selectedKnowledgePointId ||
          parsed.knowledgePoints?.[0]?.id ||
          "",
        selectedAssetKnowledgePointIds: [
          parsed.selectedKnowledgePointId ||
          parsed.knowledgePoints?.[0]?.id ||
          "",
        ].filter(Boolean),
        assetActionStatus: "imported",
        lessonReferences: [],
      };
      const references = await fetchLessonPlanLibrary({
        textbookId: parsed.textbookId,
        knowledgePointId: nextDraft.selectedKnowledgePointId,
      });
      nextDraft.lessonReferences = references.lesson_plans || [];
      const updatedProject = await updateProject(projectId, draftToCreateProjectPayload(nextDraft));
      set({
        projects: [
          mapApiProject(updatedProject),
          ...get().projects.filter((item) => item.id !== updatedProject.project_id),
        ],
        draft: {
          ...nextDraft,
        },
      });
      await get().loadProjectManifest(projectId);
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "教材解析失败";
      set({
        draft: {
          ...get().draft,
          parseStatus: "failed",
          parseError: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  loadTextbookFromLibrary: async (textbookId) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材库接口" };
    }
    set({
      draft: {
        ...get().draft,
        parseStatus: "parsing",
        parseError: null,
      },
    });
    try {
      const library = await fetchTextbookLibrary();
      const textbook =
        (textbookId
          ? library.textbooks?.find((item) => item.textbook_id === textbookId)
          : undefined) ||
        library.textbooks?.[0];
      if (!textbook?.textbook_id) {
        throw new Error("教材库为空，请先上传教材");
      }
      const latestDraft = get().draft;
      let projectId = latestDraft.apiProjectId;
      if (!projectId) {
        const project = await createProject(
          draftToCreateProjectPayload(latestDraft, {
            fallbackName: `${textbook.title || "教材库"}-临时项目`,
          }),
        );
        projectId = project.project_id;
        set({
          projects: [
            mapApiProject(project),
            ...get().projects.filter((item) => item.id !== project.project_id),
          ],
          draft: {
            ...get().draft,
            apiProjectId: projectId,
          },
        });
      }
      await attachProjectTextbookFromLibrary(projectId, textbook.textbook_id);
      const generated = await generateProjectNode(projectId, "textbook_parse", undefined);
      let parsed = mapTextbookParseContent(generated.content, get().draft);
      parsed = await enrichParseResultWithLibraryAsset(parsed);
      const currentDraft = get().draft;
      const nextDraft: NewProjectDraft = {
        ...currentDraft,
        textbookFileName: "教材库：" + (textbook.title || textbook.textbook_id),
        name: currentDraft.nameEdited ? currentDraft.name : suggestedProjectName(parsed),
        subject: parsed.subject,
        grade: parsed.grade,
        textbookVersion: parsed.textbookVersion,
        volume: parsed.volume,
        audience: currentDraft.audience === EMPTY_DRAFT.audience ? `${parsed.grade}学生` : currentDraft.audience,
        parseStatus: "done" as const,
        parseResult: parsed,
        parseError: null,
        selectedKnowledgePointId:
          parsed.selectedKnowledgePointId ||
          parsed.knowledgePoints?.[0]?.id ||
          "",
        selectedAssetKnowledgePointIds: [
          parsed.selectedKnowledgePointId ||
          parsed.knowledgePoints?.[0]?.id ||
          "",
        ].filter(Boolean),
        assetActionStatus: "imported",
        lessonReferences: [],
      };
      const references = await fetchLessonPlanLibrary({
        textbookId: parsed.textbookId,
        knowledgePointId: nextDraft.selectedKnowledgePointId,
      });
      nextDraft.lessonReferences = references.lesson_plans || [];
      const updatedProject = await updateProject(projectId, draftToCreateProjectPayload(nextDraft));
      set({
        projects: [
          mapApiProject(updatedProject),
          ...get().projects.filter((item) => item.id !== updatedProject.project_id),
        ],
        draft: {
          ...nextDraft,
        },
      });
      await get().loadProjectManifest(projectId);
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "教材库读取失败";
      set({
        draft: {
          ...get().draft,
          parseStatus: "failed",
          parseError: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  selectDraftKnowledgePoint: async (knowledgePointId, options) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材解析接口" };
    }
    if (!options?.force && knowledgePointId === get().draft.selectedKnowledgePointId) {
      return { ok: true };
    }
    const projectId = get().draft.apiProjectId;
    if (!projectId) {
      return { ok: false, msg: "请先上传教材并完成解析" };
    }
    set({
      draft: {
        ...get().draft,
        parseStatus: "parsing",
        parseError: null,
        selectedKnowledgePointId: knowledgePointId,
      },
    });
    try {
      const generated = await generateProjectNode(projectId, "textbook_parse", {
        knowledge_point_id: knowledgePointId,
      });
      let parsed = mapTextbookParseContent(generated.content, get().draft);
      parsed = await enrichParseResultWithLibraryAsset(parsed);
      const currentDraft = get().draft;
      const nextDraft: NewProjectDraft = {
        ...currentDraft,
        name: currentDraft.nameEdited ? currentDraft.name : suggestedProjectName(parsed),
        subject: parsed.subject,
        grade: parsed.grade,
        textbookVersion: parsed.textbookVersion,
        volume: parsed.volume,
        audience: currentDraft.audience === EMPTY_DRAFT.audience ? `${parsed.grade}学生` : currentDraft.audience,
        parseStatus: "done" as const,
        parseResult: parsed,
        parseError: null,
        selectedKnowledgePointId: parsed.selectedKnowledgePointId || knowledgePointId,
        selectedAssetKnowledgePointIds: [
          parsed.selectedKnowledgePointId || knowledgePointId,
        ].filter(Boolean),
        selectedLessonReferenceId: undefined,
        lessonReferences: [],
      };
      const references = await fetchLessonPlanLibrary({
        textbookId: parsed.textbookId,
        knowledgePointId: nextDraft.selectedKnowledgePointId,
      });
      nextDraft.lessonReferences = references.lesson_plans || [];
      const updatedProject = await updateProject(projectId, draftToCreateProjectPayload(nextDraft));
      set({
        projects: [
          mapApiProject(updatedProject),
          ...get().projects.filter((item) => item.id !== updatedProject.project_id),
        ],
        draft: {
          ...nextDraft,
        },
      });
      await get().loadProjectManifest(projectId);
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "知识点切换失败";
      set({
        draft: {
          ...get().draft,
          parseStatus: "failed",
          parseError: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  splitDraftTextbookAssets: async (knowledgePointIds) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材切分接口" };
    }
    const parsed = get().draft.parseResult;
    const textbookId = parsed?.textbookId;
    if (!textbookId) {
      return { ok: false, msg: "请先导入或载入教材" };
    }
    set({
      draft: {
        ...get().draft,
        parseStatus: "parsing",
        assetActionStatus: "splitting",
        parseError: null,
      },
    });
    try {
      const result = await splitTextbookKnowledgePointAssets(textbookId, knowledgePointIds);
      const nextParsed = applyAssetBatchToParseResult(get().draft.parseResult, result.assets);
      set({
        draft: {
          ...get().draft,
          parseStatus: "done",
          assetActionStatus: "split_ready",
          selectedAssetKnowledgePointIds: knowledgePointIds || get().draft.selectedAssetKnowledgePointIds,
          parseResult: nextParsed,
          parseError: null,
        },
      });
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "教材切分失败";
      set({
        draft: {
          ...get().draft,
          parseStatus: "failed",
          assetActionStatus: "failed",
          parseError: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  extractDraftTextbookAssets: async (knowledgePointIds) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材内容解析接口" };
    }
    const parsed = get().draft.parseResult;
    const textbookId = parsed?.textbookId;
    if (!textbookId) {
      return { ok: false, msg: "请先导入或载入教材" };
    }
    set({
      draft: {
        ...get().draft,
        parseStatus: "parsing",
        assetActionStatus: "extracting",
        parseError: null,
      },
    });
    try {
      const result = await extractTextbookKnowledgePointAssets(textbookId, knowledgePointIds);
      let nextParsed = applyAssetBatchToParseResult(get().draft.parseResult, result.assets);
      const selectedAsset = result.assets.find((asset) => asset.knowledge_point_id === nextParsed?.selectedKnowledgePointId);
      if (!selectedAsset && nextParsed?.selectedKnowledgePointId) {
        nextParsed = await enrichParseResultWithLibraryAsset(nextParsed);
      }
      set({
        draft: {
          ...get().draft,
          parseStatus: "done",
          assetActionStatus: "needs_review",
          selectedAssetKnowledgePointIds: knowledgePointIds || get().draft.selectedAssetKnowledgePointIds,
          parseResult: nextParsed,
          parseError: null,
        },
      });
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "教材内容解析失败";
      set({
        draft: {
          ...get().draft,
          parseStatus: "failed",
          assetActionStatus: "failed",
          parseError: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  selectDraftLessonReference: async (lessonPlanId) => {
    const projectId = get().draft.apiProjectId;
    if (!projectId) {
      return { ok: false, msg: "请先完成教材解析并创建临时项目" };
    }
    const nextDraft = {
      ...get().draft,
      selectedLessonReferenceId: lessonPlanId,
    };
    try {
      const updatedProject = await updateProject(projectId, draftToCreateProjectPayload(nextDraft));
      set({
        projects: [
          mapApiProject(updatedProject),
          ...get().projects.filter((item) => item.id !== updatedProject.project_id),
        ],
        draft: nextDraft,
      });
      return { ok: true };
    } catch (error) {
      return { ok: false, msg: error instanceof Error ? error.message : "参考教案绑定失败" };
    }
  },

  loadProjectManifest: async (projectId) => {
    if (get().dataMode === "demo") return;
    const status = get().manifestStatusByProject[projectId];
    if (status === "loading") return;
    set({
      manifestStatusByProject: {
        ...get().manifestStatusByProject,
        [projectId]: "loading",
      },
      manifestErrorByProject: {
        ...get().manifestErrorByProject,
        [projectId]: null,
      },
    });
    try {
      const manifest = await fetchProjectManifest(projectId);
      const mapped = mapApiManifest(manifest);
      set({
        projects: [
          mapped.project,
          ...get().projects.filter((project) => project.id !== projectId),
        ],
        stagesByProject: {
          ...get().stagesByProject,
          [projectId]: mapped.stages,
        },
        manifestStatusByProject: {
          ...get().manifestStatusByProject,
          [projectId]: "ready",
        },
        manifestErrorByProject: {
          ...get().manifestErrorByProject,
          [projectId]: null,
        },
      });
      await get().loadProjectWorkspace(projectId);
    } catch (error) {
      set({
        manifestStatusByProject: {
          ...get().manifestStatusByProject,
          [projectId]: "error",
        },
        manifestErrorByProject: {
          ...get().manifestErrorByProject,
          [projectId]: error instanceof Error ? error.message : "manifest 读取失败",
        },
      });
    }
  },

  loadProjectWorkspace: async (projectId) => {
    if (get().dataMode === "demo") return;
    const status = get().workspaceStatusByProject[projectId];
    if (status === "loading") return;
    set({
      workspaceStatusByProject: {
        ...get().workspaceStatusByProject,
        [projectId]: "loading",
      },
      workspaceErrorByProject: {
        ...get().workspaceErrorByProject,
        [projectId]: null,
      },
    });
    try {
      const workspace = await fetchProjectWorkspace(projectId);
      set({
        workspaceByProject: {
          ...get().workspaceByProject,
          [projectId]: workspace,
        },
        workspaceStatusByProject: {
          ...get().workspaceStatusByProject,
          [projectId]: "ready",
        },
        workspaceErrorByProject: {
          ...get().workspaceErrorByProject,
          [projectId]: null,
        },
      });
    } catch (error) {
      set({
        workspaceStatusByProject: {
          ...get().workspaceStatusByProject,
          [projectId]: "error",
        },
        workspaceErrorByProject: {
          ...get().workspaceErrorByProject,
          [projectId]: error instanceof Error ? error.message : "workspace 读取失败",
        },
      });
    }
  },

  loadProjectNode: async (projectId, stageKey) => {
    if (get().dataMode === "demo") return;
    const stage = get().stagesByProject[projectId]?.find((item) => item.key === stageKey);
    const nodeId = stage?.apiNodeId;
    if (!nodeId) return;
    const projectNodeStatus = get().nodeStatusByProject[projectId] || {};
    if (projectNodeStatus[stageKey] === "loading") return;
    set({
      nodeStatusByProject: {
        ...get().nodeStatusByProject,
        [projectId]: { ...projectNodeStatus, [stageKey]: "loading" },
      },
      nodeErrorByProject: {
        ...get().nodeErrorByProject,
        [projectId]: {
          ...(get().nodeErrorByProject[projectId] || {}),
          [stageKey]: null,
        },
      },
    });
    try {
      const detail = await fetchProjectNode(projectId, nodeId);
      const stages = (get().stagesByProject[projectId] || []).map((item) =>
        item.key === stageKey ? mapApiNodeDetailToStage(item, detail) : item,
      );
      set({
        stagesByProject: {
          ...get().stagesByProject,
          [projectId]: stages,
        },
        nodeStatusByProject: {
          ...get().nodeStatusByProject,
          [projectId]: {
            ...(get().nodeStatusByProject[projectId] || {}),
            [stageKey]: "ready",
          },
        },
        nodeErrorByProject: {
          ...get().nodeErrorByProject,
          [projectId]: {
            ...(get().nodeErrorByProject[projectId] || {}),
            [stageKey]: null,
          },
        },
      });
    } catch (error) {
      set({
        nodeStatusByProject: {
          ...get().nodeStatusByProject,
          [projectId]: {
            ...(get().nodeStatusByProject[projectId] || {}),
            [stageKey]: "error",
          },
        },
        nodeErrorByProject: {
          ...get().nodeErrorByProject,
          [projectId]: {
            ...(get().nodeErrorByProject[projectId] || {}),
            [stageKey]: error instanceof Error ? error.message : "节点详情读取失败",
          },
        },
      });
    }
  },

  loadProjectTasks: async (projectId) => {
    if (get().dataMode === "demo") return;
    const status = get().tasksStatusByProject[projectId];
    if (status === "loading") return;
    set({
      tasksStatusByProject: {
        ...get().tasksStatusByProject,
        [projectId]: "loading",
      },
      tasksErrorByProject: {
        ...get().tasksErrorByProject,
        [projectId]: null,
      },
    });
    try {
      const tasks = await fetchProjectTasks(projectId);
      set({
        tasksByProject: {
          ...get().tasksByProject,
          [projectId]: tasks,
        },
        tasksStatusByProject: {
          ...get().tasksStatusByProject,
          [projectId]: "ready",
        },
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: null,
        },
      });
    } catch (error) {
      set({
        tasksStatusByProject: {
          ...get().tasksStatusByProject,
          [projectId]: "error",
        },
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: error instanceof Error ? error.message : "任务列表读取失败",
        },
      });
    }
  },

  refreshProjectTask: async (projectId, taskId) => {
    if (get().dataMode === "demo") return { ok: false, msg: "演示模式不刷新后端任务" };
    try {
      const task = await fetchProjectTask(projectId, taskId);
      const current = get().tasksByProject[projectId] || [];
      const next = upsertTask(current, task);
      set({
        tasksByProject: {
          ...get().tasksByProject,
          [projectId]: next,
        },
        tasksStatusByProject: {
          ...get().tasksStatusByProject,
          [projectId]: "ready",
        },
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: null,
        },
      });
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "任务状态刷新失败";
      set({
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  retryProjectTask: async (projectId, taskId) => {
    if (get().dataMode === "demo") return { ok: false, msg: "演示模式不重试后端任务" };
    try {
      const task = await retryProjectTaskRequest(projectId, taskId);
      const current = get().tasksByProject[projectId] || [];
      const next = upsertTask(current, task);
      set({
        tasksByProject: {
          ...get().tasksByProject,
          [projectId]: next,
        },
        tasksStatusByProject: {
          ...get().tasksStatusByProject,
          [projectId]: "ready",
        },
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: null,
        },
      });
      await get().loadProjectNode(projectId, apiNodeIdToStageKey(task.node_id));
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "任务重试失败";
      set({
        tasksErrorByProject: {
          ...get().tasksErrorByProject,
          [projectId]: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  loadVideoWorkflow: async (projectId) => {
    set({
      videoWorkflowStatusByProject: {
        ...get().videoWorkflowStatusByProject,
        [projectId]: "loading",
      },
      videoWorkflowErrorByProject: {
        ...get().videoWorkflowErrorByProject,
        [projectId]: null,
      },
    });
    try {
      const workflow = await fetchVideoWorkflow(projectId);
      releaseVideoWorkflowCreateLockIfSettled(projectId, workflow);
      set({
        videoWorkflowByProject: {
          ...get().videoWorkflowByProject,
          [projectId]: workflow,
        },
        videoWorkflowStatusByProject: {
          ...get().videoWorkflowStatusByProject,
          [projectId]: "ready",
        },
      });
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "视频画布加载失败").message;
      set({
        videoWorkflowStatusByProject: {
          ...get().videoWorkflowStatusByProject,
          [projectId]: "error",
        },
        videoWorkflowErrorByProject: {
          ...get().videoWorkflowErrorByProject,
          [projectId]: msg,
        },
      });
    }
  },

  saveVideoWorkflowGraph: async (projectId, graph) => {
    try {
      const workflow = await saveVideoWorkflow(projectId, graph);
      set({
        videoWorkflowByProject: {
          ...get().videoWorkflowByProject,
          [projectId]: workflow,
        },
        videoWorkflowStatusByProject: {
          ...get().videoWorkflowStatusByProject,
          [projectId]: "ready",
        },
      });
      broadcastVideoWorkflowChange(projectId, "graph");
      return { ok: true };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "视频画布保存失败").message;
      set({
        videoWorkflowErrorByProject: {
          ...get().videoWorkflowErrorByProject,
          [projectId]: msg,
        },
      });
      return { ok: false, msg };
    }
  },

  uploadVideoWorkflowReferences: async (projectId, files) => {
    try {
      const result = await uploadVideoWorkflowAssets(projectId, files);
      const current = get().videoWorkflowByProject[projectId];
      if (current) {
        const nextWorkflow = { ...current, assets: result.assets };
        releaseVideoWorkflowCreateLockIfSettled(projectId, nextWorkflow);
        set({
          videoWorkflowByProject: {
            ...get().videoWorkflowByProject,
            [projectId]: nextWorkflow,
          },
        });
      }
      broadcastVideoWorkflowChange(projectId, "asset");
      return { ok: true, assets: result.assets, errors: result.errors };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "参考图上传失败").message;
      return { ok: false, msg, error };
    }
  },

  createVideoWorkflowRun: async (projectId, payload) => {
    const existingWorkflow = get().videoWorkflowByProject[projectId];
    releaseVideoWorkflowCreateLockIfSettled(projectId, existingWorkflow);
    if (videoWorkflowCreateLocks.has(projectId) || hasActiveVideoWorkflowRun(existingWorkflow)) {
      return { ok: false, msg: "当前项目已有视频任务正在生成，请等待完成后再创建新任务" };
    }
    videoWorkflowCreateLocks.add(projectId);
    let keepCreateLocked = false;
    try {
      const run = await createVideoWorkflowRunRequest(projectId, payload);
      const current = get().videoWorkflowByProject[projectId];
      keepCreateLocked = isActiveVideoWorkflowRun(run);
      if (current) {
        const nextWorkflow = upsertVideoRun(current, run);
        keepCreateLocked = hasActiveVideoWorkflowRun(nextWorkflow);
        set({
          videoWorkflowByProject: {
            ...get().videoWorkflowByProject,
            [projectId]: nextWorkflow,
          },
        });
      }
      broadcastVideoWorkflowChange(projectId, "run");
      return { ok: true, run };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "视频任务创建失败").message;
      return { ok: false, msg, error };
    } finally {
      if (!keepCreateLocked) videoWorkflowCreateLocks.delete(projectId);
    }
  },

  syncVideoWorkflowRun: async (projectId, runId) => {
    try {
      const run = await syncVideoWorkflowRunRequest(projectId, runId);
      const current = get().videoWorkflowByProject[projectId];
      if (current) {
        const nextWorkflow = upsertVideoRun(current, run);
        releaseVideoWorkflowCreateLockIfSettled(projectId, nextWorkflow);
        set({
          videoWorkflowByProject: {
            ...get().videoWorkflowByProject,
            [projectId]: nextWorkflow,
          },
        });
      }
      broadcastVideoWorkflowChange(projectId, "run");
      return { ok: true, run };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "视频任务同步失败").message;
      return { ok: false, msg, error };
    }
  },

  removeVideoWorkflowAsset: async (projectId, assetId) => {
    try {
      await deleteVideoWorkflowAsset(projectId, assetId);
      const current = get().videoWorkflowByProject[projectId];
      if (current) {
        const nextWorkflow = {
          ...current,
          assets: current.assets.filter((item) => item.asset_id !== assetId),
        };
        releaseVideoWorkflowCreateLockIfSettled(projectId, nextWorkflow);
        set({
          videoWorkflowByProject: {
            ...get().videoWorkflowByProject,
            [projectId]: nextWorkflow,
          },
        });
      }
      broadcastVideoWorkflowChange(projectId, "asset");
      return { ok: true };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "参考图移除失败").message;
      return { ok: false, msg, error };
    }
  },

  replaceVideoWorkflowRun: (projectId, run) => {
    const current = get().videoWorkflowByProject[projectId];
    if (!current) return;
    const nextWorkflow = upsertVideoRun(current, run);
    releaseVideoWorkflowCreateLockIfSettled(projectId, nextWorkflow);
    set({
      videoWorkflowByProject: {
        ...get().videoWorkflowByProject,
        [projectId]: nextWorkflow,
      },
    });
    broadcastVideoWorkflowChange(projectId, "run");
  },

  retryVideoWorkflowRun: async (projectId, runId, options) => {
    try {
      const payload: VideoWorkflowRetryRequest = {
        client_request_id: crypto.randomUUID(),
        confirm_possible_duplicate: options?.confirmPossibleDuplicate,
      };
      const run = await retryVideoWorkflowRunRequest(projectId, runId, payload);
      get().replaceVideoWorkflowRun(projectId, run);
      return { ok: true, run };
    } catch (error) {
      const msg = formatVideoWorkflowError(error, "视频任务重试失败").message;
      return { ok: false, msg, error };
    }
  },

  loadMediaWorkbench: async () => {
    set({ mediaWorkbenchStatus: "loading", mediaWorkbenchError: null });
    try {
      const mediaWorkbench = await fetchMediaWorkbench();
      set({ mediaWorkbench, mediaWorkbenchStatus: "ready", mediaWorkbenchError: null });
    } catch (error) {
      set({
        mediaWorkbenchStatus: "error",
        mediaWorkbenchError: error instanceof Error ? error.message : "媒体生成工作台加载失败",
      });
    }
  },

  createImageWorkbenchRun: async (payload) => {
    try {
      const run = await createImageWorkbenchRunRequest(payload);
      const current = get().mediaWorkbench;
      if (current) {
        set({
          mediaWorkbench: {
            ...current,
            assets: [...run.assets, ...current.assets.filter((asset) => !run.assets.some((item) => item.asset_id === asset.asset_id))],
            image_runs: [run, ...current.image_runs.filter((item) => item.run_id !== run.run_id)],
          },
          mediaWorkbenchStatus: "ready",
        });
      } else {
        await get().loadMediaWorkbench();
      }
      return { ok: true, run };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "图片生成任务创建失败";
      set({ mediaWorkbenchError: msg });
      return { ok: false, msg };
    }
  },

  uploadMediaWorkbenchReferences: async (files) => {
    try {
      const basket = await uploadMediaWorkbenchVideoReferences(files);
      const current = get().mediaWorkbench;
      if (current) {
        await get().loadMediaWorkbench();
        set({
          mediaWorkbench: {
            ...(get().mediaWorkbench || current),
            reference_basket: basket,
          },
        });
      }
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "视频参考图上传失败";
      set({ mediaWorkbenchError: msg });
      return { ok: false, msg };
    }
  },

  importImagesToVideoReferences: async (assetIds) => {
    try {
      const basket = await importMediaWorkbenchVideoReferences(assetIds);
      const current = get().mediaWorkbench;
      if (current) {
        set({ mediaWorkbench: { ...current, reference_basket: basket } });
      } else {
        await get().loadMediaWorkbench();
      }
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "图片加入视频参考篮失败";
      set({ mediaWorkbenchError: msg });
      return { ok: false, msg };
    }
  },

  createVideoWorkbenchRun: async (payload) => {
    try {
      const run = await createVideoWorkbenchRunRequest(payload);
      const current = get().mediaWorkbench;
      if (current) {
        set({
          mediaWorkbench: {
            ...current,
            video_runs: [run, ...current.video_runs.filter((item) => item.run_id !== run.run_id)],
          },
          mediaWorkbenchStatus: "ready",
        });
      } else {
        await get().loadMediaWorkbench();
      }
      return { ok: true, run };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "视频生成任务创建失败";
      set({ mediaWorkbenchError: msg });
      return { ok: false, msg };
    }
  },

  syncVideoWorkbenchRun: async (runId) => {
    try {
      const run = await syncVideoWorkbenchRunRequest(runId);
      const current = get().mediaWorkbench;
      if (current) {
        const assets = run.asset
          ? [run.asset, ...current.assets.filter((asset) => asset.asset_id !== run.asset?.asset_id)]
          : current.assets;
        set({
          mediaWorkbench: {
            ...current,
            assets,
            video_runs: [run, ...current.video_runs.filter((item) => item.run_id !== run.run_id)],
          },
        });
      }
      return { ok: true, run };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "视频任务同步失败";
      set({ mediaWorkbenchError: msg });
      return { ok: false, msg };
    }
  },

  generateStage: async (projectId, stageKey, option) => {
    if (get().dataMode === "demo") {
      get().runStage(projectId, stageKey);
      return { ok: true };
    }
    const stage = get().stagesByProject[projectId]?.find((item) => item.key === stageKey);
    const nodeId = stage?.apiNodeId;
    if (!nodeId) return { ok: false, msg: "未找到后端节点 ID" };
    const actionStatus = get().stageActionStatusByProject[projectId] || {};
    if (actionStatus[stageKey] === "loading") return { ok: false, msg: "节点动作正在执行" };

    set({
      stageActionStatusByProject: {
        ...get().stageActionStatusByProject,
        [projectId]: { ...actionStatus, [stageKey]: "loading" },
      },
      stageActionErrorByProject: {
        ...get().stageActionErrorByProject,
        [projectId]: {
          ...(get().stageActionErrorByProject[projectId] || {}),
          [stageKey]: null,
        },
      },
    });

    try {
      const payload =
        nodeId === "final_video" && option
          ? {
              model: option.model,
              size: option.size,
              mode: option.mode,
              full_run: option.fullRun,
              video_shot_limit: option.fullRun ? undefined : 1,
            }
          : undefined;
      const result = await generateProjectNode(projectId, nodeId, payload);
      const stages = (get().stagesByProject[projectId] || []).map((item) =>
        item.key === stageKey ? mapApiNodeMutationToStage(item, result) : item,
      );
      set({
        stagesByProject: {
          ...get().stagesByProject,
          [projectId]: stages,
        },
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "ready",
          },
        },
      });
      await get().loadProjectManifest(projectId);
      await get().loadProjectNode(projectId, stageKey);
      if (nodeId === "final_video") {
        await get().loadProjectTasks(projectId);
      }
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "节点生成失败";
      set({
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "error",
          },
        },
        stageActionErrorByProject: {
          ...get().stageActionErrorByProject,
          [projectId]: {
            ...(get().stageActionErrorByProject[projectId] || {}),
            [stageKey]: msg,
          },
        },
      });
      return { ok: false, msg };
    }
  },

  approveStageRemote: async (projectId, stageKey, options) => {
    if (get().dataMode === "demo") {
      get().approveStage(projectId, stageKey);
      return { ok: true };
    }
    const stage = get().stagesByProject[projectId]?.find((item) => item.key === stageKey);
    const nodeId = stage?.apiNodeId;
    if (!nodeId) return { ok: false, msg: "未找到后端节点 ID" };
    const actionStatus = get().stageActionStatusByProject[projectId] || {};
    if (actionStatus[stageKey] === "loading") return { ok: false, msg: "节点动作正在执行" };

    set({
      stageActionStatusByProject: {
        ...get().stageActionStatusByProject,
        [projectId]: { ...actionStatus, [stageKey]: "loading" },
      },
      stageActionErrorByProject: {
        ...get().stageActionErrorByProject,
        [projectId]: {
          ...(get().stageActionErrorByProject[projectId] || {}),
          [stageKey]: null,
        },
      },
      pendingRuleWarningByProject: {
        ...get().pendingRuleWarningByProject,
        [projectId]: {
          ...(get().pendingRuleWarningByProject[projectId] || {}),
          [stageKey]: null,
        },
      },
    });

    try {
      const result = await approveProjectNode(projectId, nodeId, {
        approve_note: "本地演示确认通过",
        ...(options?.override_warning_rule_ids?.length
          ? {
              override_warning_rule_ids: options.override_warning_rule_ids,
              override_reason: options.override_reason,
            }
          : {}),
      });
      const stages = (get().stagesByProject[projectId] || []).map((item) =>
        item.key === stageKey ? mapApiNodeMutationToStage(item, result) : item,
      );
      set({
        stagesByProject: {
          ...get().stagesByProject,
          [projectId]: stages,
        },
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "ready",
          },
        },
        pendingRuleWarningByProject: {
          ...get().pendingRuleWarningByProject,
          [projectId]: {
            ...(get().pendingRuleWarningByProject[projectId] || {}),
            [stageKey]: null,
          },
        },
      });
      await get().loadProjectManifest(projectId);
      await get().loadProjectNode(projectId, stageKey);
      return { ok: true };
    } catch (error) {
      if (isApiClientError(error) && error.code === "RULE_WARNING") {
        const warnings = extractRuleWarnings(error.details);
        set({
          stageActionStatusByProject: {
            ...get().stageActionStatusByProject,
            [projectId]: {
              ...(get().stageActionStatusByProject[projectId] || {}),
              [stageKey]: "ready",
            },
          },
          stageActionErrorByProject: {
            ...get().stageActionErrorByProject,
            [projectId]: {
              ...(get().stageActionErrorByProject[projectId] || {}),
              [stageKey]: error.message,
            },
          },
          pendingRuleWarningByProject: {
            ...get().pendingRuleWarningByProject,
            [projectId]: {
              ...(get().pendingRuleWarningByProject[projectId] || {}),
              [stageKey]: {
                projectId,
                stageKey,
                nodeId,
                warnings,
              },
            },
          },
        });
        return { ok: false, msg: error.message };
      }
      const msg = error instanceof Error ? error.message : "节点确认失败";
      set({
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "error",
          },
        },
        stageActionErrorByProject: {
          ...get().stageActionErrorByProject,
          [projectId]: {
            ...(get().stageActionErrorByProject[projectId] || {}),
            [stageKey]: msg,
          },
        },
      });
      return { ok: false, msg };
    }
  },

  editStageRemote: async (projectId, stageKey, content) => {
    if (get().dataMode === "demo") {
      const value = typeof content === "string" ? content : JSON.stringify(content, null, 2);
      get().saveStageInput(projectId, stageKey, value);
      return { ok: true };
    }
    const stage = get().stagesByProject[projectId]?.find((item) => item.key === stageKey);
    const nodeId = stage?.apiNodeId;
    if (!nodeId) return { ok: false, msg: "未找到后端节点 ID" };
    const actionStatus = get().stageActionStatusByProject[projectId] || {};
    if (actionStatus[stageKey] === "loading") return { ok: false, msg: "节点动作正在执行" };

    set({
      stageActionStatusByProject: {
        ...get().stageActionStatusByProject,
        [projectId]: { ...actionStatus, [stageKey]: "loading" },
      },
      stageActionErrorByProject: {
        ...get().stageActionErrorByProject,
        [projectId]: {
          ...(get().stageActionErrorByProject[projectId] || {}),
          [stageKey]: null,
        },
      },
    });

    try {
      const result = await editProjectNode(projectId, nodeId, { content });
      const stages = (get().stagesByProject[projectId] || []).map((item) =>
        item.key === stageKey ? mapApiNodeMutationToStage(item, result) : item,
      );
      set({
        stagesByProject: {
          ...get().stagesByProject,
          [projectId]: stages,
        },
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "ready",
          },
        },
      });
      await get().loadProjectManifest(projectId);
      await get().loadProjectNode(projectId, stageKey);
      return { ok: true };
    } catch (error) {
      const msg = error instanceof Error ? error.message : "节点编辑保存失败";
      set({
        stageActionStatusByProject: {
          ...get().stageActionStatusByProject,
          [projectId]: {
            ...(get().stageActionStatusByProject[projectId] || {}),
            [stageKey]: "error",
          },
        },
        stageActionErrorByProject: {
          ...get().stageActionErrorByProject,
          [projectId]: {
            ...(get().stageActionErrorByProject[projectId] || {}),
            [stageKey]: msg,
          },
        },
      });
      return { ok: false, msg };
    }
  },

  submitDeliveryFeedback: async (projectId, payload) => {
    if (get().dataMode === "demo") return { ok: true };
    try {
      await submitProjectFeedback(projectId, {
        feedback_type: "delivery",
        payload,
      });
      return { ok: true };
    } catch (error) {
      return {
        ok: false,
        msg: error instanceof Error ? error.message : "反馈提交失败",
      };
    }
  },

  approveStage: (projectId, stageKey) => {
    if (get().dataMode === "api") return;
    const stagesByProject = { ...get().stagesByProject };
    const stages = (stagesByProject[projectId] || []).map((s) => {
      if (s.key === stageKey) {
        return { ...s, status: "approved" as const };
      }
      const next = nextStageKey(stageKey);
      if (next && s.key === next && s.status === "not_started") {
        return { ...s, status: "input_required" as const };
      }
      return s;
    });
    stagesByProject[projectId] = stages;
    // 更新项目元信息
    const projects: ProjectMeta[] = get().projects.map((p) => {
      if (p.id !== projectId) return p;
      const nextKey = nextStageKey(stageKey);
      const passed = stages.filter((s) => s.status === "approved" || s.status === "skipped").length;
      const progress = Math.round((passed / stages.length) * 100);
      const cur = stages.find((s) => s.key === nextKey);
      return {
        ...p,
        currentStage: nextKey || p.currentStage,
        progress,
        status: nextKey ? "active" : "done",
        nextAction: cur ? `进入「${cur.title}」` : "项目已完成",
        updatedAt: nowStr(),
      };
    });
    set({ stagesByProject, projects });
  },

  rejectStage: (projectId, stageKey) => {
    if (get().dataMode === "api") return;
    const stagesByProject = { ...get().stagesByProject };
    const stages = (stagesByProject[projectId] || []).map((s) =>
      s.key === stageKey
        ? { ...s, status: "input_required" as const }
        : s
    );
    stagesByProject[projectId] = stages;
    const projects = get().projects.map((p) =>
      p.id === projectId
        ? { ...p, status: "active" as const, nextAction: "退回修改，等待重新输入", updatedAt: nowStr() }
        : p
    );
    set({ stagesByProject, projects });
  },

  runStage: (projectId, stageKey) => {
    if (get().dataMode === "api") return;
    const stagesByProject = { ...get().stagesByProject };
    const stages = (stagesByProject[projectId] || []).map((s) =>
      s.key === stageKey
        ? { ...s, status: "running" as const }
        : s
    );
    stagesByProject[projectId] = stages;
    set({ stagesByProject });
    // 模拟异步完成
    setTimeout(() => {
      const cur = get().stagesByProject[projectId] || [];
      const stages2 = cur.map((s) =>
        s.key === stageKey
          ? { ...s, status: "pending_confirm" as const }
          : s
      );
      const stagesByProject2 = { ...get().stagesByProject, [projectId]: stages2 };
      const projects = get().projects.map((p) =>
        p.id === projectId
          ? { ...p, nextAction: `「${stages2.find((x) => x.key === stageKey)?.title}」运行完成，待确认`, updatedAt: nowStr() }
          : p
      );
      set({ stagesByProject: stagesByProject2, projects });
    }, 1400);
  },

  saveStageInput: (projectId, stageKey, input) => {
    if (get().dataMode === "api") return;
    const stagesByProject = { ...get().stagesByProject };
    const stages = (stagesByProject[projectId] || []).map((s) =>
      s.key === stageKey
        ? { ...s, input, status: s.status === "input_required" ? "ready" : s.status }
        : s
    );
    stagesByProject[projectId] = stages;
    set({ stagesByProject });
  },

  acceptVideoPlan: (projectId, planId) => {
    if (get().dataMode === "api") return;
    const videoPlansByProject = { ...get().videoPlansByProject };
    const plans = (videoPlansByProject[projectId] || []).map((p) => ({
      ...p,
      accepted: p.id === planId ? true : p.accepted,
    }));
    videoPlansByProject[projectId] = plans;
    set({ videoPlansByProject });
  },

  draft: EMPTY_DRAFT,
  setDraft: (patch) => set({ draft: { ...get().draft, ...patch } }),
  resetDraft: () => set({ draft: { ...EMPTY_DRAFT } }),
  commitDraftToProject: () => {
    if (get().dataMode === "api") {
      return "";
    }
    const d = get().draft;
    const id = "new-" + Math.random().toString(36).slice(2, 8);
    const newProject: ProjectMeta = {
      id,
      name: d.name || "未命名项目",
      subject: d.subject,
      grade: d.grade,
      textbookVersion: d.textbookVersion,
      volume: d.volume,
      lessonType: d.lessonType,
      currentStage: "textbook-parse",
      progress: 8,
      status: "active",
      nextAction: "进入工作区继续备课",
      owner: get().user?.displayName || "教师",
      createdAt: nowStr(),
      updatedAt: nowStr(),
    };
    const projects = [newProject, ...get().projects];
    set({ projects, draft: { ...EMPTY_DRAFT } });
    return id;
  },

  mobileNavOpen: false,
  setMobileNavOpen: (v) => set({ mobileNavOpen: v }),

  commandOpen: false,
  setCommandOpen: (v) => set({ commandOpen: v }),
  toggleCommand: () => set((s) => ({ commandOpen: !s.commandOpen })),
}));

function nowStr() {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(
    d.getHours()
  )}:${p(d.getMinutes())}`;
}

async function enrichParseResultWithLibraryAsset(
  parsed: NonNullable<NewProjectDraft["parseResult"]>,
): Promise<NonNullable<NewProjectDraft["parseResult"]>> {
  if (!parsed.textbookId || !parsed.selectedKnowledgePointId) return parsed;
  try {
    const asset = await fetchTextbookKnowledgePointAsset(
      parsed.textbookId,
      parsed.selectedKnowledgePointId,
    );
    return {
      ...parsed,
      selectedKnowledgePointAssetPackage: {
        ...parsed.selectedKnowledgePointAssetPackage,
        ...mapApiTextbookAssetToDraftAsset(asset),
      },
    };
  } catch {
    return parsed;
  }
}

function applyAssetBatchToParseResult(
  parsed: NewProjectDraft["parseResult"],
  assets: Array<{
    asset_id?: string;
    knowledge_point_id: string;
    source_pdf_path?: string;
    slice_pdf_path?: string;
    mineru_md_path?: string;
    markdown_path?: string;
    textbook_pages?: string;
    pdf_pages?: string;
    parse_status?: string;
    review_status?: string;
    mineru_job_id?: string;
    checksum?: string;
    download_urls?: {
      slice_pdf?: string;
      mineru_md?: string;
    };
  }>,
): NewProjectDraft["parseResult"] {
  if (!parsed) return parsed;
  const byId = new Map(assets.map((asset) => [asset.knowledge_point_id, asset]));
  const selected = parsed.selectedKnowledgePointId ? byId.get(parsed.selectedKnowledgePointId) : undefined;
  return {
    ...parsed,
    knowledgePoints: parsed.knowledgePoints?.map((point) => {
      const asset = byId.get(point.id);
      if (!asset) return point;
      return {
        ...point,
        parseStatus: asset.parse_status || point.parseStatus,
        reviewStatus: asset.review_status || point.reviewStatus,
        assetPackage: {
          ...point.assetPackage,
          ...mapApiTextbookAssetToDraftAsset(asset),
        },
      };
    }),
    selectedKnowledgePointAssetPackage: selected
      ? {
          ...parsed.selectedKnowledgePointAssetPackage,
          ...mapApiTextbookAssetToDraftAsset(selected),
        }
      : parsed.selectedKnowledgePointAssetPackage,
  };
}

function mapApiTextbookAssetToDraftAsset(asset: {
  asset_id?: string;
  source_pdf_path?: string;
  slice_pdf_path?: string;
  mineru_md_path?: string;
  markdown_path?: string;
  textbook_pages?: string;
  pdf_pages?: string;
  parse_status?: string;
  review_status?: string;
  mineru_job_id?: string;
  checksum?: string;
  download_urls?: {
    slice_pdf?: string;
    mineru_md?: string;
  };
}) {
  return {
    assetId: asset.asset_id,
    sourcePdfPath: asset.source_pdf_path,
    slicePdfPath: asset.slice_pdf_path,
    mineruMdPath: asset.mineru_md_path,
    markdownPath: asset.markdown_path,
    textbookPages: asset.textbook_pages,
    pdfPages: asset.pdf_pages,
    parseStatus: asset.parse_status,
    reviewStatus: asset.review_status,
    mineruJobId: asset.mineru_job_id,
    checksum: asset.checksum,
    downloadUrls: {
      slicePdf: asset.download_urls?.slice_pdf,
      mineruMd: asset.download_urls?.mineru_md,
    },
  };
}

function upsertTask(tasks: ApiTask[], task: ApiTask): ApiTask[] {
  const index = tasks.findIndex((item) => item.task_id === task.task_id);
  if (index < 0) return [task, ...tasks];
  return tasks.map((item) => (item.task_id === task.task_id ? task : item));
}

function suggestedProjectName(parseResult: NonNullable<NewProjectDraft["parseResult"]>): string {
  const subject = parseResult.subject || "课程";
  const title = parseResult.lesson || "教材知识点";
  return `${parseResult.textbookVersion}${parseResult.grade}${parseResult.volume}${subject} - ${title}`;
}

function apiNodeIdToStageKey(nodeId: string): string {
  const map: Record<string, string> = {
    lesson_plan: "open-lesson-plan",
    intro_selection: "video-design-import",
    intro_video_script: "video-script",
    intro_video_screenplay: "video-screenplay",
    intro_video_asset: "video-assets",
    storyboard: "storyboard",
    final_video: "video-generation",
  };
  return map[nodeId] || nodeId;
}

/** 客户端初始化：从 localStorage 恢复登录态 */
export function initAuth() {
  const user = loadAuth();
  useAppStore.setState({ user, authReady: true });
}
