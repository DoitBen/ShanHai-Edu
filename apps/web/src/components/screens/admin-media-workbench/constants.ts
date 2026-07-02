import type { AspectRatio, RatioPreset } from "./types";

/**
 * 媒体工作台常量集中定义。
 *
 * 注意：默认值（DEFAULT_IMAGE_MODEL / DEFAULT_IMAGE_SIZE 等）保留在主
 * AdminMediaWorkbenchScreen.tsx 中作为字符串字面量，便于契约测试识别；
 * 这里只导出比例预设、模板片段、共享样式 token。
 */

/** 默认比例 —— 16:9 宽屏 */
export const DEFAULT_RATIO: AspectRatio = "16:9";

/** 5 种比例预设，含图片默认尺寸与视频默认尺寸 */
export const ASPECT_RATIOS: RatioPreset[] = [
  { ratio: "1:1", label: "1:1", desc: "正方形", imageSize: "1024x1024", videoSize: "720x720", iconW: 1, iconH: 1 },
  { ratio: "4:3", label: "4:3", desc: "横版", imageSize: "1440x1080", videoSize: "960x720", iconW: 1, iconH: 0.75 },
  { ratio: "16:9", label: "16:9", desc: "宽屏", imageSize: "1920x1080", videoSize: "1280x720", iconW: 1, iconH: 0.5625 },
  { ratio: "9:16", label: "9:16", desc: "竖版", imageSize: "1080x1920", videoSize: "720x1280", iconW: 0.5625, iconH: 1 },
  { ratio: "3:4", label: "3:4", desc: "竖版", imageSize: "1080x1440", videoSize: "720x960", iconW: 0.75, iconH: 1 },
];

/** 图片提示词结构化模板片段 */
export const PROMPT_TEMPLATES_IMAGE: { label: string; snippet: string }[] = [
  { label: "主体", snippet: "[主体：明亮的小学数学课堂，桌面上有彩色计数棒和练习卡]" },
  { label: "风格", snippet: "[风格：非写实卡通插画 / 水彩手绘 / 3D 渲染 / 简约扁平]" },
  { label: "色调", snippet: "[色调：温暖明亮 / 柔和 pastel / 高饱和度 / 冷色调]" },
  { label: "构图", snippet: "[构图：俯视桌面 / 侧面视角 / 居中对称 / 三分法]" },
  { label: "细节", snippet: "[细节：无文字水印 / 高清细节 / 景深虚化 / 干净背景]" },
];

/** 视频提示词结构化模板片段 */
export const PROMPT_TEMPLATES_VIDEO: { label: string; snippet: string }[] = [
  { label: "主体", snippet: "[主体：温暖明亮的小学数学课堂]" },
  { label: "动作", snippet: "[动作：镜头缓慢推进桌面上的计数棒和卡片]" },
  { label: "运镜", snippet: "[运镜：缓慢推进 / 横向平移 / 环绕拍摄 / 固定机位]" },
  { label: "氛围", snippet: "[氛围：清晨阳光 / 暖色调 / 柔光散射]" },
  { label: "画质", snippet: "[画质：4K 超清 / 电影级动态范围 / 浅景深虚化]" },
];

// DSButton-equivalent anchor styles (for download links that must render as <a>)
export const DS_ANCHOR_PRIMARY_SM =
  "inline-flex items-center justify-center gap-3 font-medium rounded-lg transition-all duration-300 ease-apple focus-ring whitespace-nowrap h-9 px-3.5 text-xs bg-[#1a2b3c] text-white shadow-[0_4px_12px_rgba(26,43,60,0.25),0_8px_20px_-4px_rgba(26,43,60,0.20)] hover:bg-[#142233] hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(26,43,60,0.30),0_12px_28px_-6px_rgba(26,43,60,0.25)] active:translate-y-0";

export const DS_ANCHOR_SECONDARY_SM =
  "inline-flex items-center justify-center gap-3 font-medium rounded-lg transition-all duration-300 ease-apple focus-ring whitespace-nowrap h-9 px-3.5 text-xs bg-transparent text-foreground border border-border hover:border-bronze/50 hover:text-bronze hover:bg-bronze/5 hover:-translate-y-0.5 active:translate-y-0";

// DSPill-equivalent button styles (for template tag buttons that need onClick)
export const DS_PILL_BTN_H8 =
  "inline-flex h-8 items-center gap-3 rounded-full px-4 text-xs font-medium transition-all duration-300 ease-apple bg-muted text-foreground hover:bg-muted/70 hover:border-border border border-transparent cursor-pointer focus-ring";

/** 视频参考篮最大张数 —— Omni 接口的硬限制（用于辅助文案） */
export const VIDEO_REFERENCE_BASKET_LIMIT_HINT = "最多 7 张";

/** 批量模式提示词分隔符（按行切分） */
export const BATCH_PROMPT_SEPARATOR = "\n";

/** 批量模式单次提交的最大行数（防御性） */
export const BATCH_PROMPT_MAX_ROWS = 12;
