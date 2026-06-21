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

export type DataMode = "demo" | "api";

export type LoadStatus = "idle" | "loading" | "ready" | "error";

export interface ApiErrorPayload {
  code: string;
  message: string;
  retryable: boolean;
  details?: unknown;
}

export type ApiEnvelope<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiErrorPayload };

export interface ApiProject {
  project_id: string;
  name: string;
  subject: string;
  grade: string;
  textbook_version: string;
  volume: string;
  lesson_type: string;
  created_at: string;
  status: string;
  project_dir: string;
}

export interface CreateProjectPayload {
  name: string;
  subject: string;
  grade: string;
  textbook_version: string;
  volume: string;
  lesson_type: string;
}

export interface ApiNodeState {
  project_id: string;
  node_id: string;
  status: string;
  current_version_id: string | null;
  updated_at: string | null;
}

export interface ApiManifest {
  project: ApiProject;
  nodes: ApiNodeState[];
}

export interface ApiNodeDetail extends ApiNodeState {
  content: unknown;
}

export interface ApiNodeMutationResult {
  node_id: string;
  status: string;
  content?: unknown;
  current_version_id?: string | null;
  updated_at?: string | null;
  video_path?: string | null;
  tasks?: ApiTask[];
}

export interface GenerateNodePayload {
  model?: string;
  size?: string;
  mode?: string;
  full_run?: boolean;
  knowledge_point_id?: string;
}

export interface EditNodePayload {
  content: unknown;
}

export interface ApiTask {
  task_id: string;
  project_id: string;
  node_id: string;
  task_type: string;
  status: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  error_message: string | null;
  provider_task_id?: string | null;
  error_code?: string | null;
  download_path?: string | null;
  image_path?: string | null;
  image_url?: string | null;
  clip_path?: string | null;
  video_url_present?: boolean;
  retryable?: boolean;
}

export interface ApiPptExport {
  filename: string;
  path: string;
  download_url: string;
  video_path: string;
}

export interface ProjectMeta {
  id: string;
  name: string;
  subject: string;
  grade: string;
  textbookVersion: string;
  volume: string;
  lessonType: string;
  currentStage: string;
  currentStageTitle?: string;
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
  apiNodeId?: string;
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
  source?: "api" | "user_content" | "example";
  subject: string;
  grade: string;
  textbookVersion: string;
  volume: string;
  lesson: string;
  coreKnowledgePoints: string[];
  teachingGoalSummary: string;
  keyPoints: string[];
  difficulties: string[];
  textbookTitle?: string;
  knowledgePoints?: TextbookKnowledgePoint[];
  selectedKnowledgePointId?: string;
  selectedKnowledgePointMarkdown?: string;
  selectedKnowledgePointMarkdownPath?: string;
  selectedKnowledgePointPages?: {
    textbookPages?: string;
    pdfPages?: string;
  };
}

export interface TextbookKnowledgePoint {
  id: string;
  title: string;
  unit?: string;
  pageStart?: number;
  pageEnd?: number;
  pdfPageStart?: number;
  pdfPageEnd?: number;
  keywords?: string[];
}

export interface ApiTextbookMeta {
  subject?: string;
  grade?: string;
  textbook_version?: string;
  volume?: string;
  title?: string;
}

export interface ApiTextbookKnowledgePoint {
  id: string;
  title: string;
  unit?: string;
  page_start?: number;
  page_end?: number;
  pdf_page_start?: number;
  pdf_page_end?: number;
  keywords?: string[];
}

export interface ApiSelectedKnowledgePoint {
  knowledge_point_id?: string;
  title?: string;
  source_pages?: {
    textbook_pages?: string;
    pdf_pages?: string;
  };
  markdown_path?: string;
  markdown?: string;
}

export interface ApiTextbookParseContent {
  subject?: string;
  grade?: string;
  textbook_version?: string;
  volume?: string;
  lesson_title?: string;
  core_knowledge_points?: string[];
  teaching_goal_summary?: string;
  key_points?: string[];
  difficulties?: string[];
  textbook_meta?: ApiTextbookMeta;
  knowledge_points?: ApiTextbookKnowledgePoint[];
  selected_knowledge_point_id?: string;
  selected_knowledge_point?: ApiSelectedKnowledgePoint;
  parse_artifacts?: {
    outline_path?: string;
    markdown_path?: string;
  };
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
  characterProfile: string;
  characterSafetyRule: string;
  visualPalette: string;
  visualStyleKeywords: string;
  fontPreference: string;
  complianceNotes: string;
  // step 2
  apiProjectId: string | null;
  textbookFileName: string;
  textbookContent: string;
  parseResult: TextbookParseResult | null;
  parseStatus: "idle" | "parsing" | "done" | "failed";
  parseError: string | null;
  selectedKnowledgePointId: string;
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

export type VideoGenerationMode = "text" | "reference" | "first_last_frame" | "extend";

export interface VideoCapability {
  provider: string;
  model: string;
  max_seconds: number | null;
  resolution: {
    supported: string[];
    parameter: string;
    notes: string;
  } | null;
  reference_image_support: boolean;
  max_reference_images: number;
  first_last_frame: boolean;
  video_edit: boolean;
  extend: boolean;
  endpoint: {
    create?: string;
    query: string;
  };
  auth: {
    type: string;
    header: string;
  };
  query_requires_authorization: boolean;
  recommended_use: string;
  limitations: string[];
}

export interface VideoCapabilitiesResponse {
  provider: string;
  source?: {
    llms?: string;
    raw_markdown_dir?: string;
  };
  models: VideoCapability[];
}

export interface VideoModelOption {
  provider: string;
  model: string;
  size: string;
  mode: VideoGenerationMode;
  fullRun: boolean;
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
