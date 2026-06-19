"use client";

import { create } from "zustand";
import type {
  AuthUser,
  ProjectMeta,
  WorkflowStage,
  VideoIntroPlan,
  ScreenKey,
  NewProjectDraft,
  Role,
} from "./types";
import {
  MOCK_PROJECTS,
  buildStagesForProject,
  MOCK_VIDEO_PLANS,
} from "./mock-data";
import { nextStageKey } from "./workflow";

const AUTH_KEY = "shanhai_auth";

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

/* ---------------- 新建项目草稿 ---------------- */

export const EMPTY_DRAFT: NewProjectDraft = {
  step: 1,
  name: "",
  subject: "数学",
  grade: "三年级",
  textbookVersion: "人教版",
  volume: "上册",
  lessonType: "新授课",
  textbookFileName: "",
  textbookContent: "",
  parseResult: null,
  parseStatus: "idle",
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
  user: null,
  authReady: false,
  login: (username, password) => {
    if (username === "admin" && password === "shanhai2026") {
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
    if (username === "teacher" && password === "shanhai2026") {
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
  openProject: (projectId) =>
    set({ activeProjectId: projectId, screen: "project" }),

  projects: MOCK_PROJECTS,
  stagesByProject: {
    "demo-001": buildStagesForProject("demo-001"),
    "demo-002": buildStagesForProject("demo-002"),
    "demo-003": buildStagesForProject("demo-003"),
  },
  videoPlansByProject: {
    "demo-001": MOCK_VIDEO_PLANS.map((p) => ({ ...p })),
  },

  approveStage: (projectId, stageKey) => {
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
    const projects = get().projects.map((p) => {
      if (p.id !== projectId) return p;
      const nextKey = nextStageKey(stageKey);
      const approved = stages.filter((s) => s.status === "approved").length;
      const progress = Math.round((approved / stages.length) * 100);
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

/** 客户端初始化：从 localStorage 恢复登录态 */
export function initAuth() {
  const user = loadAuth();
  useAppStore.setState({ user, authReady: true });
}
