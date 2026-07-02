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
  | "skipped"
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
  action: string;
  trace_id: string;
  details?: unknown;
}

export interface RuleWarningItem {
  rule_id: string;
  message?: string;
  severity?: string;
  details?: unknown;
}

export interface PendingRuleWarning {
  projectId: string;
  stageKey: string;
  nodeId: string;
  warnings: RuleWarningItem[];
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
  textbook_id?: string | null;
  textbook_version_id?: string | null;
  knowledge_point_id?: string | null;
  reference_lesson_plan_id?: string | null;
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
  textbook_id?: string;
  textbook_version_id?: string;
  knowledge_point_id?: string;
  reference_lesson_plan_id?: string;
  character_profile?: string;
  character_safety_rule?: string;
  visual_palette?: string;
  visual_style_keywords?: string;
  font_preference?: string;
  compliance_notes?: string;
}

export interface ApiNodeState {
  project_id: string;
  node_id: string;
  title?: string | null;
  step?: number | string | null;
  branch?: "shared" | "ppt" | "intro_video" | string | null;
  depends_on?: string[];
  schema?: string | null;
  status: string;
  current_version_id: string | null;
  updated_at: string | null;
  capabilities?: ApiNodeCapabilities;
  artifact?: ApiNodeArtifact | null;
  rule_summary?: ApiRuleSummary;
  latest_transition?: ApiStateTransition | null;
  review_reason?: ApiReviewReason | null;
}

export interface ApiNodeCapabilities {
  can_generate: boolean;
  can_edit: boolean;
  can_approve: boolean;
  can_redo: boolean;
  can_skip: boolean;
}

export interface ApiNodeArtifact {
  download_url?: string;
  pptx_path?: string;
  video_path?: string;
  lesson_plan_path?: string;
  pptx_final_path?: string;
  video_final_path?: string | null;
  delivery_manifest_path?: string;
  gate_result_json_path?: string;
  time_stats_md_path?: string;
  error_code?: string;
  error_message?: string;
}

export interface ApiRuleSummary {
  hard_block_count: number;
  warning_count: number;
  failed_rule_ids: string[];
  warning_rule_ids: string[];
  unimplemented_hard_block_count?: number;
  unimplemented_hard_block_rule_ids?: string[];
}

export interface ApiManifest {
  project: ApiProject;
  nodes: ApiNodeState[];
}

export interface ApiWorkspaceSubGate {
  gate_id?: string;
  id?: string;
  title?: string;
  label?: string;
  state?: string;
  status?: string;
  detail?: string;
  summary?: string;
  lock_reason?: string | null;
  review_summary?: string | null;
  primary_action?: string | null;
  [key: string]: unknown;
}

export interface ApiWorkspaceStep {
  step_id: string;
  title: string;
  state: string;
  primary_action?: string | null;
  lock_reason?: string | null;
  review_summary?: string | null;
  sub_gates?: ApiWorkspaceSubGate[];
  [key: string]: unknown;
}

export interface ApiProjectWorkspace {
  project_id?: string;
  current_step_id?: string | null;
  steps: ApiWorkspaceStep[];
  developer_diagnostics?: Record<string, unknown> | null;
  [key: string]: unknown;
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

export interface ApiStateTransition {
  transition_id: string;
  project_id: string;
  node_id: string;
  from_status: string | null;
  to_status: string;
  trigger: string;
  triggered_at: string;
  triggered_by_user_id: string | null;
  version_id_before: string | null;
  version_id_after: string | null;
  reason: string | null;
}

export interface ApiReviewReason {
  trigger: string;
  reason: string | null;
  version_id_before?: string | null;
  version_id_after?: string | null;
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

export type FeedbackType = "delivery" | "next_session" | "classroom_after_use";

export interface FeedbackPayload {
  feedback_type: FeedbackType;
  payload: Record<string, unknown>;
}

export interface ApiFeedbackResult {
  feedback_id: string;
  user_id: string | null;
  project_id: string;
  feedback_type: FeedbackType;
  payload: Record<string, unknown>;
  created_at: string;
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
  textbookId?: string | null;
  textbookVersionId?: string | null;
  knowledgePointId?: string | null;
  referenceLessonPlanId?: string | null;
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
  reviewReason?: string;
  reviewTrigger?: string;
  latestTransition?: ApiStateTransition | null;
  capabilities?: ApiNodeCapabilities;
  artifact?: ApiNodeArtifact | null;
  ruleSummary?: ApiRuleSummary;
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
  textbookId?: string;
  textbookVersionId?: string;
  knowledgePoints?: TextbookKnowledgePoint[];
  selectedKnowledgePointId?: string;
  selectedKnowledgePointMarkdown?: string;
  selectedKnowledgePointMarkdownPath?: string;
  selectedKnowledgePointPages?: {
    textbookPages?: string;
    pdfPages?: string;
  };
  selectedKnowledgePointAssetPackage?: TextbookKnowledgePointAssetPackage;
}

export interface TextbookKnowledgePointAssetPackage {
  assetId?: string;
  sourcePdfPath?: string;
  slicePdfPath?: string;
  mineruMdPath?: string;
  markdownPath?: string;
  textbookPages?: string;
  pdfPages?: string;
  parseStatus?: string;
  reviewStatus?: string;
  mineruJobId?: string;
  checksum?: string;
  downloadUrls?: {
    slicePdf?: string;
    mineruMd?: string;
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
  parseStatus?: string;
  reviewStatus?: string;
  assetPackage?: TextbookKnowledgePointAssetPackage;
}

export interface TextbookChapter {
  chapter_id: string;
  title: string;
  page_start?: number;
  page_end?: number;
  pdf_page_start?: number;
  pdf_page_end?: number;
  source?: string;
  review_status?: string;
}

export interface ApiTextbookMeta {
  subject?: string;
  grade?: string;
  textbook_version?: string;
  volume?: string;
  title?: string;
  textbook_id?: string;
  textbook_version_id?: string;
  publisher?: string;
  version?: string;
  toc_template_id?: string;
  page_mapping_strategy?: string;
  parser_profile?: string;
  verification_status?: string;
  review_status?: string;
}

export interface ApiTextbookKnowledgePointAssetPackage {
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
  parse_status?: string;
  review_status?: string;
  asset_package?: ApiTextbookKnowledgePointAssetPackage;
}

export interface ApiSelectedKnowledgePoint {
  knowledge_point_id?: string;
  title?: string;
  source_pages?: {
    textbook_pages?: string;
    pdf_pages?: string;
  };
  markdown_path?: string;
  mineru_md_path?: string;
  slice_pdf_path?: string;
  asset_package?: ApiTextbookKnowledgePointAssetPackage;
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
  textbook_id?: string;
  textbook_version_id?: string;
  knowledge_points?: ApiTextbookKnowledgePoint[];
  selected_knowledge_point_id?: string;
  selected_knowledge_point?: ApiSelectedKnowledgePoint;
  parse_artifacts?: {
    outline_path?: string;
    markdown_path?: string;
    mineru_md_path?: string;
    slice_pdf_path?: string;
  };
}

export interface ApiTextbookLibraryItem extends ApiTextbookMeta {
  textbook_id: string;
  textbook_version_id: string;
  source_pdf_path?: string;
  knowledge_point_count?: number;
  status?: string;
}

export interface ApiTextbookLibrary {
  textbooks: ApiTextbookLibraryItem[];
}

export interface ApiTextbookUploadResult {
  textbook_id: string;
  textbook_version_id: string;
  job_id: string;
  parse_status: string;
  filename?: string;
}

export interface ApiTextbookParseJob {
  job_id: string;
  textbook_id: string;
  textbook_version_id: string;
  knowledge_point_id?: string | null;
  job_type: string;
  status: string;
  provider: string;
  error_message?: string | null;
  result?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiTextbookKnowledgePoints {
  textbook?: ApiTextbookMeta;
  textbook_id: string;
  textbook_version_id: string;
  chapters?: TextbookChapter[];
  knowledge_points: ApiTextbookKnowledgePoint[];
}

export interface ApiTextbookKnowledgePointAsset extends ApiTextbookKnowledgePointAssetPackage {
  textbook_id: string;
  textbook_version_id: string;
  knowledge_point_id: string;
  title?: string;
}

export interface ApiTextbookAssetBatchResult {
  job_id: string;
  textbook_id: string;
  textbook_version_id: string;
  job_type: "textbook_split" | "mineru_extract_batch" | string;
  status: string;
  requested_count: number;
  successful_count: number;
  failed_count: number;
  assets: ApiTextbookKnowledgePointAsset[];
  failures: Array<{
    knowledge_point_id?: string;
    message?: string;
    asset?: ApiTextbookKnowledgePointAsset;
  }>;
}

export interface ApiLessonPlanLibraryItem {
  lesson_plan_id: string;
  title: string;
  source_project_id: string;
  source_textbook_id?: string | null;
  source_textbook_version_id?: string | null;
  source_knowledge_point_id?: string | null;
  source_slice_pdf_path?: string | null;
  source_mineru_md_path?: string | null;
  updated_at: string;
  created_at: string;
  markdown?: string;
  metadata?: Record<string, unknown>;
  created_by?: string;
}

export interface ApiLessonPlanLibrary {
  lesson_plans: ApiLessonPlanLibraryItem[];
}

export interface UploadLessonPlanLibraryMetadata {
  textbook_id?: string;
  textbook_version_id?: string;
  knowledge_point_id?: string;
  created_by?: string;
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
  sourceMode?: "textbook-library" | "lesson-plan";
  // step 1
  name: string;
  nameEdited: boolean;
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
  selectedAssetKnowledgePointIds?: string[];
  assetActionStatus?: "idle" | "imported" | "splitting" | "split_ready" | "extracting" | "needs_review" | "failed";
  selectedLessonReferenceId?: string;
  lessonReferences?: ApiLessonPlanLibraryItem[];
  lessonPlanFileName?: string;
  lessonPlanContent?: string;
  lessonPlanSummary?: string;
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
  durationSec: number;
}

export interface VideoWorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data?: Record<string, unknown>;
}

export interface VideoWorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface VideoWorkflowGraph {
  nodes: VideoWorkflowNode[];
  edges: VideoWorkflowEdge[];
  selected_model: string;
  mode: VideoGenerationMode;
  duration_sec: number;
  size: string;
}

export type VideoRunStatus =
  | "submitting"
  | "queued"
  | "processing"
  | "completed_pending_download"
  | "completed"
  | "failed"
  | "submission_unknown";

export type VideoDownloadStatus =
  | "not_started"
  | "pending_url"
  | "downloading"
  | "downloaded"
  | "download_failed";

export interface VideoStorageLifecyclePolicy {
  project_reference_quota_bytes: number;
  soft_delete_retention_days: number;
  failed_run_retention_days: number;
  temporary_file_retention_hours: number;
  backup_recommendation: string;
  soft_delete_behavior: string;
}

export interface VideoStorageUsage {
  reference_asset_bytes: number;
  deleted_reference_asset_bytes: number;
  total_reference_asset_bytes: number;
  active_reference_asset_count: number;
  deleted_reference_asset_count: number;
  reference_quota_bytes: number;
  reference_quota_used_percent: number;
}

export interface VideoWorkflowStorageResponse {
  policy: VideoStorageLifecyclePolicy;
  usage: VideoStorageUsage;
}

export interface VideoWorkflowStorageCleanupResponse {
  policy: VideoStorageLifecyclePolicy;
  purged_reference_assets: string[];
  purged_temporary_files: string[];
  expired_failed_runs: string[];
  storage_usage: VideoStorageUsage;
}

export interface VideoWorkflowObservabilityMetrics {
  provider_submit_success_count: number;
  provider_submit_failure_count: number;
  provider_submit_latency_ms_total: number;
  provider_submit_success_rate_percent: number;
  provider_query_count: number;
  provider_query_failure_count: number;
  download_success_count: number;
  download_failure_count: number;
  downloaded_video_bytes: number;
  duplicate_request_count: number;
  duplicate_request_rate_percent: number;
  queue_time_ms_total: number;
  generation_time_ms_total: number;
  download_time_ms_total: number;
  retry_count: number;
  retry_rate_percent: number;
  sync_backoff_count: number;
  provider_error_count: number;
  storage_reference_bytes: number;
  storage_reference_growth_bytes: number;
}

export interface VideoWorkflowObservabilityEvent {
  event: string;
  trace_id: string;
  created_at: string;
  project_id?: string;
  run_id?: string;
  status?: string;
  provider_task_id?: string;
  provider_status?: string;
  progress?: number;
  error_code?: string;
  retryable?: boolean;
  download_bytes?: number;
}

export interface VideoWorkflowObservabilitySnapshot {
  metrics: VideoWorkflowObservabilityMetrics;
  events: VideoWorkflowObservabilityEvent[];
  event_retention: {
    type: string;
    max_events: number;
  };
  redaction: {
    stores_provider_raw: boolean;
    stores_signed_media_locator: boolean;
    stores_authorization_header: boolean;
  };
}

export interface VideoWorkflowConfig {
  model: "omni_flash-10s";
  size: "1280x720";
  duration_sec: 10;
  max_reference_images: 7;
  max_project_assets: 50;
  max_asset_bytes: number;
  poll_interval_ms: number;
  run_create_window_seconds: number;
  run_create_project_window_limit: number;
  run_create_global_window_limit: number;
  provider_ready: boolean;
  provider_reason_code: string;
  provider_user_message: string;
  storage_lifecycle: VideoStorageLifecyclePolicy;
  runtime_concurrency?: {
    lock_scope: "single_api_process";
    supports_multi_worker: false;
    deployment_warning: string;
  };
}

export interface VideoReferenceAsset {
  asset_id: string;
  filename: string;
  path: string;
  mime_type: "image/jpeg" | "image/png" | "image/webp";
  byte_size: number;
  width: number;
  height: number;
  created_at: string;
  deleted_at: string | null;
}

export interface VideoWorkflowRun {
  run_id: string;
  client_request_id: string;
  retry_of_run_id: string | null;
  project_id: string;
  status: VideoRunStatus;
  download_status: VideoDownloadStatus;
  progress: number;
  prompt: string;
  model: "omni_flash-10s";
  mode?: VideoGenerationMode;
  size: "1280x720";
  duration_sec: 10;
  reference_asset_ids: string[];
  reference_assets: Array<
    Pick<
      VideoReferenceAsset,
      "asset_id" | "filename" | "mime_type" | "width" | "height"
    >
  >;
  provider_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  retryable: boolean;
  video_ready: boolean;
  created_at: string;
  updated_at: string;
  download_path?: string | null;
  download_bytes?: number | null;
  download_sha256?: string | null;
  video_url_present?: boolean;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface VideoWorkflowRunRequest {
  client_request_id: string;
  prompt: string;
  reference_asset_ids: string[];
}

export interface VideoWorkflowRetryRequest {
  client_request_id: string;
  confirm_possible_duplicate?: boolean;
}

export interface VideoWorkflowUploadError {
  filename: string;
  code: string;
  message: string;
}

export interface VideoWorkflowAssetsResponse {
  assets: VideoReferenceAsset[];
  uploaded: VideoReferenceAsset[];
  errors: VideoWorkflowUploadError[];
  max_reference_images: number;
  storage_usage: VideoStorageUsage;
}

export interface VideoWorkflowResponse {
  project_id: string;
  config: VideoWorkflowConfig;
  storage_usage: VideoStorageUsage;
  assets: VideoReferenceAsset[];
  runs: VideoWorkflowRun[];
  graph?: VideoWorkflowGraph;
  latest_run?: VideoWorkflowRun | null;
  capabilities?: VideoCapabilitiesResponse;
}
export interface MediaAsset {
  asset_id: string;
  asset_type: "image" | "video";
  source: "image_run" | "upload" | "video_run";
  filename: string;
  path: string;
  mime_type: string;
  prompt?: string | null;
  run_id?: string | null;
  provider_task_id?: string | null;
  created_at: string;
}

export interface MediaWorkbenchCapabilities {
  image: {
    provider: string;
    provider_ready: boolean;
    default_model: string;
    default_size: string;
    default_quality: string;
    models: Array<{
      model: string;
      sizes: string[];
      qualities: string[];
      max_count: number;
    }>;
  };
  video: {
    provider: string;
    provider_ready: boolean;
    default_model: string;
    default_size: string;
    default_duration_sec: number;
    models: VideoCapability[];
  };
}

export interface ImageWorkbenchRun {
  run_id: string;
  task_id: string;
  project_id: string;
  node_id: string;
  task_type: string;
  status: string;
  prompt?: string;
  model?: string;
  size?: string;
  quality?: string;
  count?: number;
  assets: MediaAsset[];
  progress?: number;
  error_message?: string | null;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface ImageWorkbenchRunRequest {
  prompt: string;
  model: string;
  size: string;
  quality: string;
  count: number;
}

export interface VideoWorkbenchRun {
  run_id: string;
  task_id: string;
  project_id: string;
  node_id: string;
  task_type: string;
  status: string;
  prompt?: string;
  model?: string;
  mode?: VideoGenerationMode;
  size?: string;
  duration_sec?: number;
  reference_asset_ids?: string[];
  reference_count?: number;
  progress?: number;
  download_path?: string | null;
  video_url_present?: boolean;
  asset?: MediaAsset | null;
  error_message?: string | null;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface VideoWorkbenchRunRequest {
  prompt: string;
  model: string;
  mode: VideoGenerationMode;
  size: string;
  duration_sec: number;
  reference_asset_ids: string[];
}

export interface VideoReferenceBasket {
  assets: MediaAsset[];
  max_reference_images: number;
}

export interface MediaWorkbenchResponse {
  capabilities: MediaWorkbenchCapabilities;
  assets: MediaAsset[];
  reference_basket: VideoReferenceBasket;
  image_runs: ImageWorkbenchRun[];
  video_runs: VideoWorkbenchRun[];
}

export type AdminRuleSeverity = "hard_block" | "warning" | "info";
export type AdminRuleStatus = "active" | "draft" | "archived";

export interface AdminRuleVersion {
  version_id: string;
  rule_id: string;
  version_number: number;
  status: AdminRuleStatus;
  severity: AdminRuleSeverity;
  enabled: boolean;
  check_json: Record<string, unknown>;
  action_message: string;
  source: string;
  source_file_path?: string | null;
  notes?: string | null;
  created_by: string;
  created_at: string;
  activated_at?: string | null;
}

export interface AdminRule {
  rule_id: string;
  title: string;
  trigger_node: string;
  trigger_event: string;
  executor?: string | null;
  legacy_source?: string | null;
  created_at: string;
  active_version: AdminRuleVersion | null;
  versions: AdminRuleVersion[];
}

export interface AdminRuleAuditLog {
  audit_id: string;
  rule_id?: string | null;
  version_id?: string | null;
  rule_set_version_id?: string | null;
  action: string;
  actor: string;
  notes?: string | null;
  created_at: string;
}

export interface AdminWorkflowGraphRule {
  rule_id: string;
  title?: string | null;
  trigger_event?: string | null;
  severity?: AdminRuleSeverity | null;
  enabled?: boolean | null;
  version_id?: string | null;
}

export interface AdminWorkflowGraphNode {
  id: string;
  title?: string | null;
  step?: number | string | null;
  branch?: string | null;
  depends_on: string[];
  rules: AdminWorkflowGraphRule[];
}

export interface AdminWorkflowGraph {
  version: string;
  editable: boolean;
  edit_scope: string;
  nodes: AdminWorkflowGraphNode[];
}

export interface CreateAdminRuleVersionPayload {
  severity: AdminRuleSeverity;
  enabled: boolean;
  action_message: string;
  check_json: Record<string, unknown>;
  created_by?: string;
  notes?: string;
}

export type ScreenKey =
  | "dashboard"
  | "new-project"
  | "project"
  | "config"
  | "logs"
  | "scripts"
  | "admin-workflow"
  | "admin-textbook-library"
  | "admin-media-workbench";

export interface AuthUser {
  userId: string;
  email: string;
  username: string;
  role: Role;
  displayName: string;
  status: "active" | "disabled";
  loginAt: string;
}

export interface ApiAuthUser {
  user_id: string;
  email: string;
  display_name: string;
  role: Role;
  status: "active" | "disabled";
}

export interface ApiAuthSession {
  user: ApiAuthUser;
  csrf_token: string;
  expires_at: string;
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
