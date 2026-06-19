/**
 * 山海教育 ProMax 工作台 —— 类型定义
 */

export type ProjectStatus =
  | "draft"
  | "active"
  | "pending"
  | "blocked"
  | "failed"
  | "done";

export type StageStatus =
  | "not_started"
  | "input_required"
  | "ready"
  | "running"
  | "pending_confirm"
  | "approved"
  | "blocked"
  | "failed";

export type WorkflowBranch = "common" | "video" | "ppt";

export type Role = "admin" | "teacher";

export interface ProjectMeta {
  id: string;
  name: string;
  subject: string;
  grade: string;
  textbookVersion: string;
  volume: string;
  lessonType: string;
  currentStage: string;
  progress: number;
  status: ProjectStatus;
  nextAction: string;
  owner: string;
  updatedAt: string;
  createdAt: string;
}

export interface StageLog {
  id: string;
  time: string;
  level: "info" | "warn" | "error" | "success";
  message: string;
}

export interface WorkflowStage {
  key: string;
  title: string;
  branch: WorkflowBranch;
  order: number;
  status: StageStatus;
  summary: string;
  input: string;
  result: string;
  evidence: string[];
  logs: StageLog[];
  duration?: string;
}

export interface TextbookParseResult {
  subject: string;
  grade: string;
  textbookVersion: string;
  volume: string;
  lesson: string;
  coreKnowledgePoints: string[];
  teachingGoalSummary: string;
  keyPoints: string[];
  difficulties: string[];
}

export type VideoIntroType =
  | "science"
  | "application"
  | "story"
  | "suspense"
  | "discovery"
  | "all";

export interface VideoIntroPlan {
  id: string;
  rank: number;
  score: number;
  type: VideoIntroType;
  title: string;
  hook: string;
  courseAnchor: string;
  classroomLandingQuestion: string;
  avoidTeaching: string;
  lessonEntryPoint: string;
  reason: string;
  accepted: boolean;
}

export interface PptPlan {
  id: string;
  slides: number;
  style: string;
  structure: string[];
  highlight: string;
  accepted: boolean;
}

export interface SystemStatus {
  scheduler: "idle" | "running" | "paused";
  queueTasks: number;
  storageUsedPct: number;
  lastHeartbeat: string;
  services: { name: string; status: "ok" | "degraded" | "down"; note: string }[];
}

export interface PendingItem {
  id: string;
  projectId: string;
  projectName: string;
  stage: string;
  stageTitle: string;
  kind: "confirm" | "input" | "review" | "error";
  title: string;
  desc: string;
  priority: "high" | "medium" | "low";
  createdAt: string;
}

export interface NewProjectDraft {
  step: number;
  // step 1
  name: string;
  subject: string;
  grade: string;
  textbookVersion: string;
  volume: string;
  lessonType: string;
  // step 2
  textbookFileName: string;
  textbookContent: string;
  parseResult: TextbookParseResult | null;
  parseStatus: "idle" | "parsing" | "done" | "failed";
  // step 3
  videoPurpose: string;
  videoTypes: VideoIntroType[];
  videoCountPerType: number;
  videoTheme: string;
  audience: string;
  duration: string;
  creativeBrief: string;
  // step 4
  pptStyle: string;
  pptSlides: number;
  pptStructure: string;
  // step 5
  outputPath: string;
  constraints: string;
  safeMode: boolean;
}

export type ScreenKey =
  | "dashboard"
  | "new-project"
  | "project"
  | "config"
  | "logs"
  | "scripts";

export interface AuthUser {
  username: string;
  role: Role;
  displayName: string;
  loginAt: string;
}

export interface ActivityItem {
  id: string;
  time: string;
  kind: "approve" | "reject" | "generate" | "parse" | "adopt" | "comment" | "upload";
  projectName: string;
  projectId: string;
  stageTitle: string;
  title: string;
  desc: string;
}
