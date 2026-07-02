import type { MediaAsset, VideoCapability, VideoGenerationMode } from "@/lib/types";

/**
 * 媒体工作台子组件共享类型。
 * 主容器（AdminMediaWorkbenchScreen）持有 state，通过 props 传给子面板。
 */

/** 比例预设枚举 —— 1:1 / 4:3 / 16:9 / 9:16 / 3:4 */
export type AspectRatio = "1:1" | "4:3" | "16:9" | "9:16" | "3:4";

/** 单个图片模型的能力描述（与 capabilities.image.models[] 同构） */
export interface ImageModelOption {
  model: string;
  sizes: string[];
  qualities: string[];
  max_count: number;
}

/** 比例预设：含图片默认尺寸与视频默认尺寸，以及 CSS 图标的宽高比 */
export interface RatioPreset {
  ratio: AspectRatio;
  label: string;
  desc: string;
  /** 图片默认尺寸（横向用 widthxheight） */
  imageSize: string;
  /** 视频默认尺寸 */
  videoSize: string;
  /** 用于按钮上的迷你 CSS 比例图标的宽度比例（0~1） */
  iconW: number;
  /** 用于按钮上的迷你 CSS 比例图标的高度比例（0~1） */
  iconH: number;
}

/** 状态卡片 4 种语义色 */
export type StatusTone = "success" | "warning" | "info" | "neutral";

/** 状态卡片入参 */
export interface StatusTileProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: StatusTone;
  loading?: boolean;
}

/** RunList / VideoRunPanel 单条视频任务的最小展示模型 */
export interface VideoRunView {
  run_id: string;
  status: string;
  prompt?: string;
  progress?: number;
  download_path?: string | null;
  error_message?: string | null;
  /** 已下载好的视频缩略图（可选，由父组件从 asset 字段映射） */
  thumbnail_url?: string | null;
  /** 视频时长（秒），仅用于展示 */
  duration_sec?: number;
}

/** 图片/视频任务的最小历史展示模型 */
export interface HistoryRow {
  id: string;
  kind: "图片" | "视频";
  status: string;
  prompt?: string;
  meta: string;
}

/** ModelSelector 接受的模型条目（图片/视频统一，仅需 model 字段） */
export interface ModelOption {
  model: string;
}

/** 复用 React 类型，避免在子组件里重复 import */
export type { MediaAsset, VideoCapability, VideoGenerationMode };
