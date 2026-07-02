"use client";

import { cn } from "@/lib/utils";
import { ASPECT_RATIOS } from "./constants";
import type { AspectRatio } from "./types";

/**
 * 比例预设选择器（F3）
 *
 * 替换裸分辨率下拉框：1:1 / 4:3 / 16:9 / 9:16 / 3:4 按钮组横排，
 * 每个按钮含小型 CSS 比例图标 + 文字。
 *
 * 选中态：深色背景 + 白字；未选中：浅灰背景。
 * 默认选中 16:9（由父组件控制 value）。
 */
export interface RatioSelectorProps {
  value: AspectRatio;
  onChange: (ratio: AspectRatio) => void;
  /** 横向密排 / 宽松（默认紧凑两行） */
  compact?: boolean;
  disabled?: boolean;
}

export function RatioSelector({ value, onChange, compact = false, disabled }: RatioSelectorProps) {
  return (
    <div className="form-field-pro">
      <div className="flex items-center justify-between">
        <label className="t-caption font-medium text-foreground">比例预设</label>
        <span className="t-caption text-muted-foreground">{currentSizeHint(value)}</span>
      </div>
      <div
        role="radiogroup"
        aria-label="比例预设"
        className={cn(
          "mt-2 grid gap-2",
          compact ? "grid-cols-5" : "grid-cols-3 sm:grid-cols-5",
        )}
      >
        {ASPECT_RATIOS.map((preset) => {
          const selected = preset.ratio === value;
          return (
            <button
              key={preset.ratio}
              type="button"
              role="radio"
              aria-checked={selected}
              disabled={disabled}
              onClick={() => onChange(preset.ratio)}
              className={cn(
                "group flex flex-col items-center justify-center gap-2 rounded-lg border px-2 py-2.5 transition-all duration-300 ease-apple focus-ring",
                "h-[68px]",
                selected
                  ? "border-[#1a2b3c] bg-[#1a2b3c] text-white shadow-[0_4px_12px_rgba(26,43,60,0.20),0_8px_20px_-4px_rgba(26,43,60,0.16)]"
                  : "border-border bg-muted/40 text-foreground hover:border-bronze/40 hover:bg-muted/70 hover:-translate-y-0.5",
                disabled && "cursor-not-allowed opacity-60 hover:translate-y-0",
              )}
            >
              <RatioIcon w={preset.iconW} h={preset.iconH} selected={selected} />
              <div className="flex flex-col items-center leading-tight">
                <span className="text-xs font-semibold">{preset.label}</span>
                <span
                  className={cn(
                    "text-[10px]",
                    selected ? "text-white/70" : "text-muted-foreground",
                  )}
                >
                  {preset.desc}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** 迷你 CSS 比例图标 —— 用 div 模拟不同宽高比，匹配选中/未选中态描边 */
function RatioIcon({ w, h, selected }: { w: number; h: number; selected: boolean }) {
  // 取宽高较大的一边为 22px 基准
  const base = 22;
  const max = Math.max(w, h);
  const width = (w / max) * base;
  const height = (h / max) * base;
  return (
    <span
      className="flex items-center justify-center"
      style={{ width: base, height: base }}
      aria-hidden="true"
    >
      <span
        className={cn(
          "rounded-[3px] border transition-colors duration-300 ease-apple",
          selected ? "border-white/80 bg-white/15" : "border-foreground/40 bg-foreground/5",
        )}
        style={{ width, height }}
      />
    </span>
  );
}

/** 当前比例的尺寸提示文案 */
function currentSizeHint(ratio: AspectRatio): string {
  const preset = ASPECT_RATIOS.find((item) => item.ratio === ratio);
  return preset ? `${preset.imageSize} · ${preset.videoSize}` : "";
}
