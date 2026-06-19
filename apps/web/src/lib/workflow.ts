import type { WorkflowStage, WorkflowBranch, StageStatus } from "./types";

/**
 * Promax 工作流 —— 14 个节点
 * 分支：common（公共）/ video（视频线）/ ppt（PPT 线）
 */
export interface StageDef {
  key: string;
  title: string;
  branch: WorkflowBranch;
  order: number;
  short: string;
  desc: string;
}

export const STAGE_DEFS: StageDef[] = [
  {
    key: "project-config",
    title: "项目配置",
    branch: "common",
    order: 1,
    short: "配置",
    desc: "确定项目基本信息、学科、年级、教材版本与路径约束。",
  },
  {
    key: "textbook-parse",
    title: "教材解析与核验",
    branch: "common",
    order: 2,
    short: "教材",
    desc: "上传教材并解析，核验学科、年级、课题、知识点与教学目标。",
  },
  {
    key: "open-lesson-plan",
    title: "公开课教案",
    branch: "common",
    order: 3,
    short: "教案",
    desc: "基于教材解析生成公开课教案初稿，确认教学目标与重难点。",
  },
  {
    key: "video-design-import",
    title: "视频设计导入",
    branch: "video",
    order: 4,
    short: "视频导入",
    desc: "设定视频用途、类型、数量与创意方向，作为视频线起点。",
  },
  {
    key: "video-script",
    title: "视频剧本",
    branch: "video",
    order: 5,
    short: "剧本",
    desc: "生成视频剧本方案，采纳或编辑后进入资产阶段。",
  },
  {
    key: "video-assets",
    title: "视频资产",
    branch: "video",
    order: 6,
    short: "资产",
    desc: "整理视频所需画面、素材、配音与音乐资产清单。",
  },
  {
    key: "storyboard",
    title: "分镜脚本",
    branch: "video",
    order: 7,
    short: "分镜",
    desc: "拆解镜头节奏与画面构成，形成可执行的分镜表。",
  },
  {
    key: "video-generation",
    title: "视频生成",
    branch: "video",
    order: 8,
    short: "生成",
    desc: "依据分镜与资产生成课堂导入视频，核验后交付。",
  },
  {
    key: "ppt-plan",
    title: "PPT 方案",
    branch: "ppt",
    order: 9,
    short: "PPT方案",
    desc: "规划 PPT 结构、风格与页数，匹配教案落点。",
  },
  {
    key: "lesson-plan-final",
    title: "教案完善稿",
    branch: "common",
    order: 10,
    short: "教案完善",
    desc: "结合视频与 PPT 反馈，完善教案终稿。",
  },
  {
    key: "ppt-script",
    title: "PPT 脚本",
    branch: "ppt",
    order: 11,
    short: "PPT脚本",
    desc: "逐页撰写 PPT 文案与讲解脚本。",
  },
  {
    key: "ppt-assets",
    title: "PPT 资产",
    branch: "ppt",
    order: 12,
    short: "PPT资产",
    desc: "准备 PPT 配图、图标、版式与配色资产。",
  },
  {
    key: "pptx-generation",
    title: "PPTX 生成",
    branch: "ppt",
    order: 13,
    short: "PPTX",
    desc: "组装最终 PPTX 文件，校对排版与动效。",
  },
  {
    key: "final-delivery",
    title: "最终交付",
    branch: "common",
    order: 14,
    short: "交付",
    desc: "汇总教案、视频、PPTX 与素材，归档交付。",
  },
];

export const STAGE_KEY_BY_ORDER = STAGE_DEFS.map((s) => s.key);

export function stageDefByKey(key: string): StageDef | undefined {
  return STAGE_DEFS.find((s) => s.key === key);
}

export function stageDefByOrder(order: number): StageDef | undefined {
  return STAGE_DEFS.find((s) => s.order === order);
}

export const BRANCH_LABEL: Record<WorkflowBranch, string> = {
  common: "公共",
  video: "视频线",
  ppt: "PPT 线",
};

export const STAGE_STATUS_LABEL: Record<StageStatus, string> = {
  not_started: "未开始",
  input_required: "待输入",
  ready: "就绪",
  running: "运行中",
  pending_confirm: "待确认",
  approved: "已通过",
  blocked: "已阻塞",
  failed: "失败",
};

export type StageStatusTone =
  | "neutral"
  | "info"
  | "warning"
  | "success"
  | "danger"
  | "brand";

export const STAGE_STATUS_TONE: Record<StageStatus, StageStatusTone> = {
  not_started: "neutral",
  input_required: "warning",
  ready: "info",
  running: "brand",
  pending_confirm: "warning",
  approved: "success",
  blocked: "danger",
  failed: "danger",
};

export function nextStageKey(currentKey: string): string | null {
  const def = stageDefByKey(currentKey);
  if (!def) return null;
  const next = stageDefByOrder(def.order + 1);
  return next ? next.key : null;
}

export function makeEmptyStages(): WorkflowStage[] {
  return STAGE_DEFS.map((s) => ({
    key: s.key,
    title: s.title,
    branch: s.branch,
    order: s.order,
    status: "not_started" as StageStatus,
    summary: "",
    input: "",
    result: "",
    evidence: [],
    logs: [],
  }));
}
