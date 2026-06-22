import type {
  ApiManifest,
  ApiNodeDetail,
  ApiNodeMutationResult,
  ApiNodeState,
  ApiProject,
  ApiReviewReason,
  CreateProjectPayload,
  NewProjectDraft,
  ProjectMeta,
  ProjectStatus,
  StageStatus,
  WorkflowBranch,
  WorkflowStage,
} from "./types";

type NodeDef = {
  key: string;
  title: string;
  branch: WorkflowBranch;
  order: number;
  summary: string;
};

const NODE_DEFS: Record<string, NodeDef> = {
  project_meta: {
    key: "project-meta",
    title: "项目元信息",
    branch: "common",
    order: 1,
    summary: "后端项目基础记录",
  },
  project_config: {
    key: "project-config",
    title: "项目配置",
    branch: "common",
    order: 2,
    summary: "学科、年级、教材版本与课型配置",
  },
  visual_contract: {
    key: "visual-contract",
    title: "视觉契约",
    branch: "common",
    order: 3,
    summary: "PPT 与视频共用的风格、配色和字体约束",
  },
  character_dict: {
    key: "character-dict",
    title: "角色字典",
    branch: "common",
    order: 4,
    summary: "非写实角色设定与合规红线",
  },
  textbook_parse: {
    key: "textbook-parse",
    title: "教材解析与核验",
    branch: "common",
    order: 5,
    summary: "教材结构化解析结果",
  },
  lesson_plan: {
    key: "open-lesson-plan",
    title: "公开课教案",
    branch: "common",
    order: 6,
    summary: "公开课教案初稿",
  },
  intro_selection: {
    key: "video-design-import",
    title: "视频导入选择",
    branch: "video",
    order: 7,
    summary: "导入视频方向与候选策略",
  },
  ppt_assembly_plan: {
    key: "ppt-plan",
    title: "PPT 总装方案",
    branch: "ppt",
    order: 8,
    summary: "PPT 结构、页型配比和素材需求",
  },
  ppt_page_script: {
    key: "ppt-script",
    title: "PPT 页面脚本",
    branch: "ppt",
    order: 9,
    summary: "逐页教学动作、可编辑数学文本和画面说明",
  },
  ppt_visual_asset: {
    key: "ppt-assets",
    title: "PPT 视觉资产",
    branch: "ppt",
    order: 10,
    summary: "PPT 主视觉、页面插画和素材资产",
  },
  pptx_artifact: {
    key: "pptx-generation",
    title: "PPTX 生成",
    branch: "ppt",
    order: 11,
    summary: "可下载 PPTX artifact 与内测装配结果",
  },
  intro_video_script: {
    key: "video-script",
    title: "视频剧本",
    branch: "video",
    order: 12,
    summary: "课堂导入视频脚本",
  },
  intro_video_screenplay: {
    key: "video-screenplay",
    title: "视频分场剧本",
    branch: "video",
    order: 13,
    summary: "视频画面与旁白分场",
  },
  intro_video_asset: {
    key: "video-assets",
    title: "视频资产",
    branch: "video",
    order: 14,
    summary: "视频素材、配音与资产清单",
  },
  storyboard: {
    key: "storyboard",
    title: "分镜脚本",
    branch: "video",
    order: 15,
    summary: "镜头节奏与画面构成",
  },
  final_video: {
    key: "video-generation",
    title: "最终视频",
    branch: "video",
    order: 16,
    summary: "导入视频成片与交付结果",
  },
};

const SUBJECT_TO_API: Record<string, string> = {
  数学: "math",
  语文: "chinese",
  科学: "science",
  英语: "english",
  艺术: "art",
};

const SUBJECT_FROM_API: Record<string, string> = {
  math: "数学",
  chinese: "语文",
  science: "科学",
  english: "英语",
  art: "艺术",
};

const GRADE_TO_API: Record<string, string> = {
  一年级: "1",
  二年级: "2",
  三年级: "3",
  四年级: "4",
  五年级: "5",
  六年级: "6",
};

const GRADE_FROM_API: Record<string, string> = {
  "1": "一年级",
  "2": "二年级",
  "3": "三年级",
  "4": "四年级",
  "5": "五年级",
  "6": "六年级",
};

const VERSION_TO_API: Record<string, string> = {
  人教版: "renjiao",
  教科版: "jiaoke",
  统编版: "tongbian",
  苏教版: "sujiao",
};

const VERSION_FROM_API: Record<string, string> = {
  renjiao: "人教版",
  jiaoke: "教科版",
  tongbian: "统编版",
  sujiao: "苏教版",
};

const VOLUME_TO_API: Record<string, string> = {
  上册: "shang",
  下册: "xia",
};

const VOLUME_FROM_API: Record<string, string> = {
  shang: "上册",
  xia: "下册",
};

const LESSON_TYPE_TO_API: Record<string, string> = {
  新授课: "new",
  探究课: "inquiry",
  诵读课: "reading",
  复习课: "review",
  公开课: "public",
};

const LESSON_TYPE_FROM_API: Record<string, string> = {
  new: "新授课",
  inquiry: "探究课",
  reading: "诵读课",
  review: "复习课",
  public: "公开课",
};

export function draftToCreateProjectPayload(draft: NewProjectDraft): CreateProjectPayload {
  return {
    name: draft.name.trim() || "未命名项目",
    subject: SUBJECT_TO_API[draft.subject] || draft.subject,
    grade: GRADE_TO_API[draft.grade] || draft.grade,
    textbook_version: VERSION_TO_API[draft.textbookVersion] || draft.textbookVersion,
    volume: VOLUME_TO_API[draft.volume] || draft.volume,
    lesson_type: LESSON_TYPE_TO_API[draft.lessonType] || draft.lessonType,
    character_profile: draft.characterProfile.trim(),
    character_safety_rule: draft.characterSafetyRule.trim(),
    visual_palette: draft.visualPalette.trim(),
    visual_style_keywords: draft.visualStyleKeywords.trim(),
    font_preference: draft.fontPreference.trim(),
    compliance_notes: draft.complianceNotes.trim(),
  };
}

export function mapApiProject(project: ApiProject, nodes?: ApiNodeState[]): ProjectMeta {
  const stages = nodes ? mapApiNodesToStages(nodes) : [];
  const current = stages.find((stage) => !isPassableStageStatus(stage.status)) || stages[0];
  const passed = stages.filter((stage) => isPassableStageStatus(stage.status)).length;
  const progress = stages.length ? Math.round((passed / stages.length) * 100) : 0;

  return {
    id: project.project_id,
    name: project.name,
    subject: SUBJECT_FROM_API[project.subject] || project.subject,
    grade: GRADE_FROM_API[project.grade] || project.grade,
    textbookVersion: VERSION_FROM_API[project.textbook_version] || project.textbook_version,
    volume: VOLUME_FROM_API[project.volume] || project.volume,
    lessonType: LESSON_TYPE_FROM_API[project.lesson_type] || project.lesson_type,
    currentStage: current?.key || "project-config",
    currentStageTitle: current?.title,
    progress,
    status: mapProjectStatus(project.status, stages),
    nextAction: current ? `进入「${current.title}」` : "等待 manifest 同步",
    owner: "本地教师",
    createdAt: formatDateTime(project.created_at),
    updatedAt: formatDateTime(latestNodeUpdatedAt(nodes) || project.created_at),
  };
}

export function mapApiManifest(manifest: ApiManifest): {
  project: ProjectMeta;
  stages: WorkflowStage[];
} {
  const stages = mapApiNodesToStages(manifest.nodes);
  return {
    project: mapApiProject(manifest.project, manifest.nodes),
    stages,
  };
}

export function mapApiNodeDetailToStage(stage: WorkflowStage, detail: ApiNodeDetail): WorkflowStage {
  const reviewReason = formatReviewReason(detail.review_reason);
  return {
    ...stage,
    status: mapStageStatus(detail.status),
    reviewReason,
    reviewTrigger: detail.review_reason?.trigger,
    result: formatNodeContent(detail.content),
    logs: [
      ...stage.logs,
      {
        id: `node-${detail.node_id}-${detail.updated_at || "current"}`,
        time: formatTime(detail.updated_at),
        level: "info",
        message: detail.current_version_id
          ? `已读取后端节点详情，当前版本 ${detail.current_version_id}`
          : "已读取后端节点详情，暂无版本内容",
      },
      ...(reviewReason
        ? [
            {
              id: `review-${detail.node_id}-${detail.latest_transition?.transition_id || detail.updated_at || "current"}`,
              time: formatTime(detail.latest_transition?.triggered_at || detail.updated_at),
              level: "warn" as const,
              message: reviewReason,
            },
          ]
        : []),
    ],
  };
}

export function mapApiNodeMutationToStage(
  stage: WorkflowStage,
  result: ApiNodeMutationResult,
): WorkflowStage {
  const contentSource = mergeMutationVideoPath(result.content, result.video_path);
  const content = typeof contentSource === "undefined" ? stage.result : formatNodeContent(contentSource);
  return {
    ...stage,
    status: mapStageStatus(result.status),
    result: content,
    logs: [
      ...stage.logs,
      {
        id: `mutation-${result.node_id}-${Date.now()}`,
        time: formatTime(result.updated_at || new Date().toISOString()),
        level: result.status === "failed" ? "error" : "success",
        message: `后端节点动作完成：${result.node_id} -> ${result.status}`,
      },
    ],
  };
}

function mergeMutationVideoPath(content: unknown, videoPath?: string | null): unknown {
  if (!videoPath) return content;
  if (content === null || typeof content === "undefined") {
    return { video_path: videoPath };
  }
  if (typeof content === "object" && !Array.isArray(content)) {
    return { ...(content as Record<string, unknown>), video_path: videoPath };
  }
  return content;
}

function mapApiNodesToStages(nodes: ApiNodeState[]): WorkflowStage[] {
  return nodes
    .map((node, index) => {
      const def = NODE_DEFS[node.node_id] || fallbackNodeDef(node.node_id, index + 1);
      const reviewReason = formatReviewReason(node.review_reason);
      const branch = mapWorkflowBranch(node.branch, def.branch);
      return {
        key: def.key,
        apiNodeId: node.node_id,
        title: node.title || def.title,
        branch,
        order: typeof node.step === "number" ? node.step : def.order,
        status: mapStageStatus(node.status),
        reviewReason,
        reviewTrigger: node.review_reason?.trigger,
        summary: formatNodeSummary(node, def.summary),
        input: "",
        result: "",
        evidence: [],
        capabilities: node.capabilities,
        artifact: node.artifact,
        ruleSummary: node.rule_summary,
        logs: [
          {
            id: `manifest-${node.node_id}`,
            time: formatTime(node.updated_at),
            level: "info",
            message: `manifest 已同步：${node.node_id}`,
          },
          ...(reviewReason
            ? [
                {
                  id: `manifest-review-${node.node_id}-${node.latest_transition?.transition_id || node.updated_at || "current"}`,
                  time: formatTime(node.latest_transition?.triggered_at || node.updated_at),
                  level: "warn" as const,
                  message: reviewReason,
                },
              ]
            : []),
        ],
      } satisfies WorkflowStage;
    })
    .sort((a, b) => a.order - b.order);
}

function mapWorkflowBranch(apiBranch: ApiNodeState["branch"], fallback: WorkflowBranch): WorkflowBranch {
  if (apiBranch === "ppt") return "ppt";
  if (apiBranch === "intro_video" || apiBranch === "video") return "video";
  if (apiBranch === "shared" || apiBranch === "common") return "common";
  return fallback;
}

function formatNodeSummary(node: ApiNodeState, fallback: string): string {
  const details = [
    node.schema ? `schema: ${node.schema}` : null,
    node.depends_on?.length ? `依赖: ${node.depends_on.join(", ")}` : null,
  ].filter(Boolean);
  return details.length ? details.join("；") : fallback;
}

function fallbackNodeDef(nodeId: string, order: number): NodeDef {
  return {
    key: nodeId.replaceAll("_", "-"),
    title: nodeId,
    branch: "common",
    order: 100 + order,
    summary: "后端返回的工作流节点",
  };
}

function mapProjectStatus(status: string, stages: WorkflowStage[]): ProjectStatus {
  if (status === "done" || stages.length > 0 && stages.every((stage) => isPassableStageStatus(stage.status))) {
    return "done";
  }
  if (status === "failed" || stages.some((stage) => stage.status === "failed")) return "failed";
  if (status === "blocked" || stages.some((stage) => stage.status === "blocked")) return "blocked";
  if (stages.some((stage) => stage.status === "pending_confirm")) return "pending";
  if (status === "draft") return "draft";
  return "active";
}

function mapStageStatus(status: string): StageStatus {
  const map: Record<string, StageStatus> = {
    not_started: "not_started",
    input_required: "input_required",
    ready: "ready",
    running: "running",
    needs_review: "pending_confirm",
    pending_confirm: "pending_confirm",
    approved: "approved",
    blocked: "blocked",
    failed: "failed",
    skipped: "skipped",
    generated: "pending_confirm",
  };
  return map[status] || "not_started";
}

function isPassableStageStatus(status: StageStatus): boolean {
  return status === "approved" || status === "skipped";
}

function formatReviewReason(reviewReason?: ApiReviewReason | null): string | undefined {
  if (!reviewReason) return undefined;
  if (reviewReason.trigger === "cascade_invalidate") {
    return reviewReason.reason || "上游内容已变更，需要重新确认本节点是否仍可使用";
  }
  return reviewReason.reason || undefined;
}

function formatNodeContent(content: unknown): string {
  if (content === null || typeof content === "undefined") return "";
  if (typeof content === "string") return content;
  return JSON.stringify(content, null, 2);
}

function latestNodeUpdatedAt(nodes?: ApiNodeState[]): string | null {
  if (!nodes?.length) return null;
  return nodes
    .map((node) => node.updated_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1) || null;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())} ${p(
    date.getHours(),
  )}:${p(date.getMinutes())}`;
}

function formatTime(value: string | null | undefined): string {
  const formatted = formatDateTime(value);
  return formatted ? formatted.slice(11) : "--:--";
}
