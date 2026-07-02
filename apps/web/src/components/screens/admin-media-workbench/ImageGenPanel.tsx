"use client";

import { AlertTriangle, Loader2, Sparkles, Wand2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DSCard, DSSectionTitle, DSButton } from "@/components/ui/ds";
import { cn } from "@/lib/utils";
import { ModelSelector, SelectField } from "./ModelSelector";
import { RatioSelector } from "./RatioSelector";
import { PromptBatchInput } from "./PromptBatchInput";
import { PROMPT_TEMPLATES_IMAGE, DS_PILL_BTN_H8 } from "./constants";
import type { AspectRatio, ImageModelOption } from "./types";

/**
 * 图片操作面板（F1 / F2 / F3 / F5）
 *
 * 含：
 * - 批量模式切换（普通 / 批量）
 * - 结构化模板标签
 * - 单行提示词 / 多行批量提示词
 * - 动态模型选择器（来自 capabilities.image.models[]）
 * - 比例预设按钮组（替代裸分辨率下拉框）
 * - 画质选择器（跟随模型 qualities[] 过滤）
 * - 张数选择器（仅单模式，跟随模型 max_count）
 * - 提交按钮 + 积分提示
 */
export interface ImageGenPanelProps {
  // 提示词
  prompt: string;
  onPromptChange: (value: string) => void;
  batchMode: boolean;
  onBatchModeChange: (mode: boolean) => void;
  batchPrompts: string;
  onBatchPromptsChange: (value: string) => void;
  onInsertTemplate: (snippet: string) => void;
  onPolish: () => void;
  polishing: boolean;

  // 模型与参数
  model: string;
  onModelChange: (value: string) => void;
  models: ImageModelOption[];
  ratio: AspectRatio;
  onRatioChange: (ratio: AspectRatio) => void;
  quality: string;
  onQualityChange: (value: string) => void;
  availableQualities: string[];
  count: string;
  onCountChange: (value: string) => void;
  maxCount: number;

  // 状态
  busy: boolean;
  workbenchLoaded: boolean;
  providerUnavailable: boolean;
  credits: number;

  // 提交
  onSubmit: () => void;
}

export function ImageGenPanel(props: ImageGenPanelProps) {
  const {
    prompt,
    onPromptChange,
    batchMode,
    onBatchModeChange,
    batchPrompts,
    onBatchPromptsChange,
    onInsertTemplate,
    onPolish,
    polishing,
    model,
    onModelChange,
    models,
    ratio,
    onRatioChange,
    quality,
    onQualityChange,
    availableQualities,
    count,
    onCountChange,
    maxCount,
    busy,
    workbenchLoaded,
    providerUnavailable,
    credits,
    onSubmit,
  } = props;

  // 张数选项跟随模型 max_count
  const countValues = makeCountValues(maxCount);

  return (
    <DSCard className="h-full">
      <DSSectionTitle
        icon={<Sparkles className="h-4 w-4" />}
        title="图片生成"
        desc="默认 gpt-image-2 / 1920x1080 / high"
      />

      {/* 批量模式切换 */}
      <BatchModeToggle value={batchMode} onChange={onBatchModeChange} disabled={!workbenchLoaded || providerUnavailable} />

      {/* 结构化模板 */}
      <div className="mt-4">
        <div className="mb-3 flex items-center gap-3 t-overline text-muted-foreground/70">
          <Wand2 className="h-3 w-3" />结构化模板
        </div>
        <div className="flex flex-wrap gap-3">
          {PROMPT_TEMPLATES_IMAGE.map((tpl) => (
            <button
              key={tpl.label}
              type="button"
              onClick={() => onInsertTemplate(tpl.snippet)}
              className={DS_PILL_BTN_H8}
              disabled={batchMode}
            >
              {tpl.label}
            </button>
          ))}
        </div>
        {batchMode && (
          <p className="mt-2 t-caption text-muted-foreground">
            批量模式下模板不可用，请直接在下方输入框按行填写提示词。
          </p>
        )}
      </div>

      {/* 提示词区 */}
      <div className="mt-4 flex flex-col gap-3">
        {batchMode ? (
          <PromptBatchInput
            value={batchPrompts}
            onChange={onBatchPromptsChange}
            disabled={busy}
          />
        ) : (
          <>
            <div className="flex items-center justify-between gap-3">
              <Label className="t-caption text-muted-foreground">图片提示词</Label>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={onPolish}
                  disabled={!prompt.trim() || polishing}
                  className="ai-polish-link"
                >
                  {polishing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}
                  AI 润色
                </button>
                <span className="t-caption tabular-nums text-muted-foreground">{prompt.length}/2000</span>
              </div>
            </div>
            <Textarea
              value={prompt}
              onChange={(event) => onPromptChange(event.target.value)}
              className="input-pro min-h-[100px] bg-background"
              placeholder="例如：明亮的小学数学课堂，桌面上有彩色计数棒和练习卡，非写实卡通插画风格，无文字。"
            />
          </>
        )}
      </div>

      {/* 模型 + 画质 */}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ModelSelector
          label="模型"
          value={model}
          models={models}
          onValueChange={onModelChange}
          disabled={!workbenchLoaded}
        />
        <SelectField
          label="质量"
          value={quality}
          values={availableQualities}
          onValueChange={onQualityChange}
          disabled={!workbenchLoaded}
        />
      </div>

      {/* 比例预设（替换原尺寸下拉框） */}
      <div className="mt-4">
        <RatioSelector
          value={ratio}
          onChange={onRatioChange}
          disabled={!workbenchLoaded}
        />
      </div>

      {/* 张数（仅单模式） */}
      {!batchMode && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <SelectField
            label="张数"
            value={count}
            values={countValues}
            onValueChange={onCountChange}
            disabled={!workbenchLoaded}
          />
        </div>
      )}

      {/* 提交 */}
      <DSButton
        variant="primary"
        size="lg"
        className="mt-6 w-full font-semibold"
        onClick={onSubmit}
        disabled={busy || !workbenchLoaded || providerUnavailable}
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
        <span>{batchMode ? "批量生成图片" : "生成图片"}</span>
        <span className="credits-hint">≈{credits} 积分</span>
      </DSButton>

      {providerUnavailable && (
        <div className="alert-warning-pro mt-3 t-caption">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>后端没有检测到图片生成接口配置，暂时不能提交真实生图任务。</span>
        </div>
      )}
    </DSCard>
  );
}

/** 批量模式开关（普通 / 批量） */
function BatchModeToggle({
  value,
  onChange,
  disabled,
}: {
  value: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className="mt-2 flex items-center justify-between rounded-lg border border-border bg-muted/30 p-1">
      <div className="flex flex-1 gap-1">
        <button
          type="button"
          onClick={() => onChange(false)}
          disabled={disabled}
          className={cn(
            "flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all duration-300 ease-apple focus-ring",
            !value
              ? "bg-background text-foreground shadow-[0_1px_2px_rgba(35,39,46,0.06)]"
              : "text-muted-foreground hover:text-foreground",
            disabled && "cursor-not-allowed opacity-60",
          )}
        >
          普通模式
        </button>
        <button
          type="button"
          onClick={() => onChange(true)}
          disabled={disabled}
          className={cn(
            "flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all duration-300 ease-apple focus-ring",
            value
              ? "bg-background text-foreground shadow-[0_1px_2px_rgba(35,39,46,0.06)]"
              : "text-muted-foreground hover:text-foreground",
            disabled && "cursor-not-allowed opacity-60",
          )}
        >
          批量模式
        </button>
      </div>
      <span className="px-3 t-caption text-muted-foreground">
        {value ? "多行并发" : "单提示词"}
      </span>
    </div>
  );
}

/** 生成张数候选：1..maxCount，最多 4 个 */
function makeCountValues(maxCount: number): string[] {
  const upper = Math.max(1, Math.min(4, maxCount || 1));
  const out: string[] = [];
  for (let i = 1; i <= upper; i += 1) out.push(String(i));
  return out;
}
