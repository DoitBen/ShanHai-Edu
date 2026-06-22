"use client";

import { create } from "zustand";
import type {
  AuthUser,
  DataMode,
  LoadStatus,
  PendingRuleWarning,
  ProjectMeta,
  ApiTask,
  ApiTextbookParseContent,
  WorkflowStage,
  VideoIntroPlan,
  ScreenKey,
  NewProjectDraft,
  Role,
  VideoModelOption,
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
  createProject,
  editProjectNode,
  fetchProjectManifest,
  fetchProjectNode,
  fetchProjectTask,
  fetchProjectTasks,
  fetchProjects,
  generateProjectNode,
  retryProjectTask as retryProjectTaskRequest,
  submitProjectFeedback,
  uploadProjectTextbook,
  uploadProjectTextbookFile,
  isApiClientError,
} from "./api-client";
import {
  draftToCreateProjectPayload,
  mapApiManifest,
  mapApiNodeDetailToStage,
  mapApiNodeMutationToStage,
  mapApiProject,
} from "./api-mappers";

const AUTH_KEY = "shanhai_auth";

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
    window.localStorage.setItem(AUTH_KEY, JSON.stringify(user));
  } else {
    window.localStorage.removeItem(AUTH_KEY);
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
  name: "",
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
  loadProjects: () => Promise<void>;
  createProjectFromDraft: () => Promise<string>;
  loadProjectManifest: (projectId: string) => Promise<void>;
  loadProjectNode: (projectId: string, stageKey: string) => Promise<void>;
  loadProjectTasks: (projectId: string) => Promise<void>;
  refreshProjectTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  retryProjectTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  parseDraftTextbook: (
    file: File,
    knowledgePointId?: string,
  ) => Promise<{ ok: boolean; msg?: string }>;
  selectDraftKnowledgePoint: (
    knowledgePointId: string,
  ) => Promise<{ ok: boolean; msg?: string }>;
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
      if (!username.trim()) {
        return { ok: false, msg: "请输入用户名" };
      }
      const user: AuthUser = {
        username: username.trim(),
        role: "teacher",
        displayName: username.trim(),
        loginAt: new Date().toISOString(),
      };
      saveAuth(user);
      set({ user });
      return { ok: true };
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
      const nextStagesByProject = { ...get().stagesByProject };
      const nextManifestStatusByProject = { ...get().manifestStatusByProject };
      const nextManifestErrorByProject = { ...get().manifestErrorByProject };
      const projects = apiProjects.map((project, index) => {
        const manifestResult = manifestResults[index];
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
    const project = draft.apiProjectId
      ? null
      : await createProject(draftToCreateProjectPayload(draft));
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
    const textbookContent = buildTextbookUploadContent(draft);
    if (!draft.apiProjectId && textbookContent.trim()) {
      await uploadProjectTextbook(
        mapped.id,
        textbookContent,
        draft.textbookFileName || "textbook.txt",
      );
    }
    set({
      projects: [mapped, ...get().projects.filter((item) => item.id !== mapped.id)],
      draft: { ...EMPTY_DRAFT },
    });
    await get().loadProjectManifest(mapped.id);
    return mapped.id;
  },

  parseDraftTextbook: async (file, knowledgePointId) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材解析接口" };
    }
    const draft = get().draft;
    if (!draft.name.trim()) {
      return { ok: false, msg: "请先填写项目名称" };
    }
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
        const project = await createProject(draftToCreateProjectPayload(latestDraft));
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

      await uploadProjectTextbookFile(projectId, file);
      const generated = await generateProjectNode(
        projectId,
        "textbook_parse",
        knowledgePointId ? { knowledge_point_id: knowledgePointId } : undefined,
      );
      const parsed = mapTextbookParseContent(
        generated.content,
        get().draft,
      );
      set({
        draft: {
          ...get().draft,
          subject: parsed.subject,
          grade: parsed.grade,
          textbookVersion: parsed.textbookVersion,
          volume: parsed.volume,
          parseStatus: "done",
          parseResult: parsed,
          parseError: null,
          selectedKnowledgePointId:
            parsed.selectedKnowledgePointId ||
            parsed.knowledgePoints?.[0]?.id ||
            "",
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

  selectDraftKnowledgePoint: async (knowledgePointId) => {
    if (get().dataMode === "demo") {
      return { ok: false, msg: "demo 模式不调用真实教材解析接口" };
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
      const parsed = mapTextbookParseContent(generated.content, get().draft);
      set({
        draft: {
          ...get().draft,
          subject: parsed.subject,
          grade: parsed.grade,
          textbookVersion: parsed.textbookVersion,
          volume: parsed.volume,
          parseStatus: "done",
          parseResult: parsed,
          parseError: null,
          selectedKnowledgePointId: parsed.selectedKnowledgePointId || knowledgePointId,
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
      nextAction: "进入教材解析阶段",
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

function buildTextbookUploadContent(draft: NewProjectDraft): string {
  if (draft.textbookContent.trim()) return draft.textbookContent.trim();
  const parsed = draft.parseResult;
  if (!parsed) return "";
  return [
    `${parsed.grade}${parsed.subject}，${parsed.lesson}。`,
    parsed.teachingGoalSummary,
    `核心知识点：${parsed.coreKnowledgePoints.join("、")}。`,
    `教学重点：${parsed.keyPoints.join("、")}。`,
    `教学难点：${parsed.difficulties.join("、")}。`,
  ]
    .filter(Boolean)
    .join("\n");
}

function mapTextbookParseContent(
  content: unknown,
  fallback: NewProjectDraft,
): NonNullable<NewProjectDraft["parseResult"]> {
  const data = isRecord(content) ? (content as ApiTextbookParseContent) : {};
  const meta = isRecord(data.textbook_meta) ? data.textbook_meta : {};
  const knowledgePoints = Array.isArray(data.knowledge_points)
    ? data.knowledge_points
        .filter(isRecord)
        .map((point) => ({
          id: stringValue(point.id),
          title: stringValue(point.title) || "未命名知识点",
          unit: stringValue(point.unit),
          pageStart: numberValue(point.page_start),
          pageEnd: numberValue(point.page_end),
          pdfPageStart: numberValue(point.pdf_page_start),
          pdfPageEnd: numberValue(point.pdf_page_end),
          keywords: Array.isArray(point.keywords)
            ? point.keywords.filter((item): item is string => typeof item === "string")
            : [],
        }))
        .filter((point) => point.id)
    : [];
  const selected = isRecord(data.selected_knowledge_point)
    ? data.selected_knowledge_point
    : {};
  const selectedPages = isRecord(selected.source_pages) ? selected.source_pages : {};
  const subject = apiSubjectToLabel(stringValue(meta.subject) || stringValue(data.subject), fallback.subject);
  const grade = apiGradeToLabel(stringValue(meta.grade) || stringValue(data.grade), fallback.grade);
  const textbookVersion = apiVersionToLabel(
    stringValue(meta.textbook_version) || stringValue(data.textbook_version),
    fallback.textbookVersion,
  );
  const volume = apiVolumeToLabel(stringValue(meta.volume) || stringValue(data.volume), fallback.volume);
  const selectedTitle = stringValue(selected.title);
  const lesson = stringValue(data.lesson_title) || selectedTitle || fallback.name || "教材知识点";
  const coreKnowledgePoints =
    Array.isArray(data.core_knowledge_points) && data.core_knowledge_points.length
      ? data.core_knowledge_points.filter((item): item is string => typeof item === "string")
      : knowledgePoints.map((point) => point.title);

  return {
    source: "api",
    subject,
    grade,
    textbookVersion,
    volume,
    lesson,
    coreKnowledgePoints,
    teachingGoalSummary:
      stringValue(data.teaching_goal_summary) ||
      `已从后端教材解析结果中选定“${lesson}”。`,
    keyPoints:
      Array.isArray(data.key_points) && data.key_points.length
        ? data.key_points.filter((item): item is string => typeof item === "string")
        : coreKnowledgePoints,
    difficulties:
      Array.isArray(data.difficulties) && data.difficulties.length
        ? data.difficulties.filter((item): item is string => typeof item === "string")
        : ["请结合 Markdown 预览核对教学难点"],
    textbookTitle: stringValue(meta.title),
    knowledgePoints,
    selectedKnowledgePointId:
      stringValue(data.selected_knowledge_point_id) ||
      stringValue(selected.knowledge_point_id) ||
      knowledgePoints[0]?.id ||
      "",
    selectedKnowledgePointMarkdown: stringValue(selected.markdown),
    selectedKnowledgePointMarkdownPath: stringValue(selected.markdown_path),
    selectedKnowledgePointPages: {
      textbookPages: stringValue(selectedPages.textbook_pages),
      pdfPages: stringValue(selectedPages.pdf_pages),
    },
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function upsertTask(tasks: ApiTask[], task: ApiTask): ApiTask[] {
  const index = tasks.findIndex((item) => item.task_id === task.task_id);
  if (index < 0) return [task, ...tasks];
  return tasks.map((item) => (item.task_id === task.task_id ? task : item));
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

function apiSubjectToLabel(value: string, fallback: string): string {
  const map: Record<string, string> = {
    math: "数学",
    chinese: "语文",
    science: "科学",
    english: "英语",
    art: "艺术",
  };
  return map[value] || value || fallback;
}

function apiGradeToLabel(value: string, fallback: string): string {
  const map: Record<string, string> = {
    "1": "一年级",
    "2": "二年级",
    "3": "三年级",
    "4": "四年级",
    "5": "五年级",
    "6": "六年级",
  };
  return map[value] || value || fallback;
}

function apiVersionToLabel(value: string, fallback: string): string {
  const map: Record<string, string> = {
    renjiao: "人教版",
    jiaoke: "教科版",
    tongbian: "统编版",
    sujiao: "苏教版",
  };
  return map[value] || value || fallback;
}

function apiVolumeToLabel(value: string, fallback: string): string {
  const map: Record<string, string> = {
    shang: "上册",
    xia: "下册",
  };
  return map[value] || value || fallback;
}

/** 客户端初始化：从 localStorage 恢复登录态 */
export function initAuth() {
  const user = loadAuth();
  useAppStore.setState({ user, authReady: true });
}
