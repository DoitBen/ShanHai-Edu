"use client";

import type { ReactNode } from "react";
import { AlertTriangle, Film, Loader2, Monitor, Smartphone, Upload, Wand2, Zap } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DSButton,
  DSCard,
  DSSectionTitle,
  DSBadge,
  DSPill,
} from "@/components/ui/ds";
import { cn } from "@/lib/utils";
import type { MediaAsset, VideoGenerationMode } from "@/lib/types";
import { downloadMediaWorkbenchAsset } from "@/lib/api-client";
import { RatioSelector } from "./RatioSelector";
import { PROMPT_TEMPLATES_VIDEO, DS_PILL_BTN_H8 } from "./constants";
import type { AspectRatio, ModelOption } from "./types";

/**
 * 视频操作面板（F2 / F5）
 *
 * 含：
 * - 参考图篮（上传 + 已加入缩略图）
 * - 视频提示词 + AI 润色
 * - 结构化模板
 * - 动态模型选择（PillSelect 来自 capabilities.video.models[]）
 * - 模式（text/reference）
 * - 比例预设按钮组（替代原分辨率 PillSelect）
 * - 时长（只读 Pill）
 * - 提交按钮 + 积分提示
 */
export interface VideoGenPanelProps {
  // 参考篮
  basketAssets: MediaAsset[];
  basketCount: number;
  maxReferenceImages: number;
  onUploadReferences: (files: FileList | null) => void;

  // 提示词
  prompt: string;
  onPromptChange: (value: string) => void;
  onInsertTemplate: (snippet: string) => void;
  onPolish: () => void;
  polishing: boolean;

  // 模型 / 模式 / 比例 / 时长
  model: string;
  onModelChange: (value: string) => void;
  models: ModelOption[];
  mode: VideoGenerationMode;
  onModeChange: (mode: VideoGenerationMode) => void;
  ratio: AspectRatio;
  onRatioChange: (ratio: AspectRatio) => void;
  durationSec: number;

  // 状态
  busy: boolean;
  workbenchLoaded: boolean;
  providerReady: boolean;
  providerUnavailable: boolean;
  effectiveVideoMode: VideoGenerationMode;
  submitDisabled: boolean;
  credits: number;

  // 提交
  onSubmit: () => void;
}

export function VideoGenPanel(props: VideoGenPanelProps) {
  const {
    basketAssets,
    basketCount,
    maxReferenceImages,
    onUploadReferences,
    prompt,
    onPromptChange,
    onInsertTemplate,
    onPolish,
    polishing,
    model,
    onModelChange,
    models,
    mode,
    onModeChange,
    ratio,
    onRatioChange,
    durationSec,
    busy,
    workbenchLoaded,
    providerReady,
    providerUnavailable,
    effectiveVideoMode,
    submitDisabled,
    credits,
    onSubmit,
  } = props;

  return (
    <DSCard className="h-full">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <DSSectionTitle
          className="mb-0"
          icon={<Film className="h-4 w-4" />}
          title="视频生成"
          desc="Omni 默认生成 10 秒横版视频"
        />
        <DSBadge variant={providerReady ? "success" : "neutral"}>
          {providerReady ? "真实接口已连接" : "检测中"}
        </DSBadge>
      </div>

      {/* 参考图篮 + 提示词 */}
      <div className="mt-6 rounded-xl border border-border bg-gradient-to-br from-muted/30 to-muted/10 p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="t-overline text-muted-foreground/70">参考图篮</div>
          <span
            className={cn(
              "t-caption font-semibold",
              basketCount > 0 ? "text-success" : "text-muted-foreground",
            )}
          >
            {basketCount} / {maxReferenceImages}
          </span>
        </div>
        <div className="grid gap-4 lg:grid-cols-[100px_minmax(0,1fr)]">
          <label className="group flex h-[100px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-card transition-all duration-300 ease-apple hover:border-bronze/50 hover:bg-bronze/5">
            <Upload className="h-5 w-5 text-muted-foreground transition-colors group-hover:text-bronze" />
            <span className="mt-2 text-xs font-medium text-foreground">上传参考图</span>
            <span className="text-[11px] text-muted-foreground">点击/拖拽</span>
            <input
              type="file"
              accept="image/*"
              multiple
              className="sr-only"
              onChange={(event) => onUploadReferences(event.target.files)}
            />
          </label>
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3">
              <Label className="t-caption text-muted-foreground">视频提示词</Label>
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
                <span className="t-caption tabular-nums text-muted-foreground">{prompt.length}/5000</span>
              </div>
            </div>
            <Textarea
              value={prompt}
              onChange={(event) => onPromptChange(event.target.value)}
              className="input-pro min-h-[100px] resize-none bg-background"
              placeholder="描述你想生成的视频内容，例如：温暖明亮的小学数学课堂导入镜头，镜头缓慢推进桌面上的计数棒和卡片。"
            />
          </div>
        </div>

        {/* 结构化模板 */}
        <div className="mt-4">
          <div className="mb-3 flex items-center gap-3 t-overline text-muted-foreground/70">
            <Wand2 className="h-3 w-3" />结构化模板
          </div>
          <div className="flex flex-wrap gap-3">
            {PROMPT_TEMPLATES_VIDEO.map((tpl) => (
              <button
                key={tpl.label}
                type="button"
                onClick={() => onInsertTemplate(tpl.snippet)}
                className={DS_PILL_BTN_H8}
              >
                {tpl.label}
              </button>
            ))}
          </div>
        </div>

        {basketCount > 0 && <MiniAssetList assets={basketAssets} compact />}

        {/* Pill 参数 + 比例预设 */}
        <div className="mt-4 flex flex-col gap-4">
          <div className="flex flex-wrap gap-3">
            <PillSelect
              icon={<span className="text-sm font-semibold">O</span>}
              value={model}
              values={models.length > 0 ? models.map((m) => m.model) : [model]}
              onValueChange={onModelChange}
              disabled={!workbenchLoaded}
            />
            <PillSelect
              icon={<Film className="h-4 w-4" />}
              value={effectiveVideoMode}
              onValueChange={(value) => onModeChange(value as VideoGenerationMode)}
              values={["text", "reference"]}
              disabled={!workbenchLoaded}
            />
            <ReadonlyPill icon={<Smartphone className="h-4 w-4" />} value={`${durationSec} 秒`} />
          </div>

          {/* 比例预设按钮组（替代原分辨率 PillSelect） */}
          <RatioSelector
            value={ratio}
            onChange={onRatioChange}
            disabled={!workbenchLoaded}
            compact
          />
        </div>

        {/* CTA */}
        <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3 t-caption text-muted-foreground">
            <Monitor className="h-4 w-4" />
            <span>
              当前模式：<span className="font-semibold text-foreground">{effectiveVideoMode === "reference" ? "参考图" : "纯文本"}</span>
            </span>
          </div>
          <DSButton
            variant="primary"
            size="lg"
            className="shrink-0"
            disabled={submitDisabled}
            onClick={onSubmit}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            <span>生成 {durationSec} 秒视频</span>
            <span className="credits-hint">≈{credits} 积分</span>
          </DSButton>
        </div>
      </div>

      {providerUnavailable && (
        <div className="alert-warning-pro mt-3 t-caption">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>后端没有检测到视频生成接口配置，暂时不能提交真实视频任务。</span>
        </div>
      )}
    </DSCard>
  );
}

/** Pill 风格的下拉选择器（保持原视觉） */
function PillSelect({
  icon,
  value,
  values,
  onValueChange,
  disabled,
}: {
  icon: ReactNode;
  value: string;
  values: string[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
}) {
  const items = values.length > 0 ? values : [value];
  return (
    <DSPill className="w-auto p-0">
      <span className="text-muted-foreground">{icon}</span>
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger className="h-10 w-auto border-0 bg-transparent px-0 shadow-none focus:ring-0 focus-visible:ring-0">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {items.map((item) => (
            <SelectItem key={item} value={item}>
              {item}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </DSPill>
  );
}

/** 只读 Pill（用于时长） */
function ReadonlyPill({ icon, value }: { icon: ReactNode; value: string }) {
  return (
    <DSPill>
      <span className="text-muted-foreground">{icon}</span>
      <span className="font-medium">{value}</span>
    </DSPill>
  );
}

/** 参考篮内的小缩略图列表 */
function MiniAssetList({ assets, compact = false }: { assets: MediaAsset[]; compact?: boolean }) {
  if (!assets.length) return null;
  return (
    <div className={cn("mt-4 grid gap-3", compact ? "sm:grid-cols-4" : "sm:grid-cols-2")}>
      {assets.map((asset) => (
        <div
          key={asset.asset_id}
          className="flex items-center gap-3 rounded-lg border border-border bg-card p-2 transition-all duration-300 ease-apple hover:border-bronze/30 hover:shadow-apple-sm"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={downloadMediaWorkbenchAsset(asset.asset_id)}
            alt={asset.filename}
            className={cn("rounded object-cover", compact ? "h-9 w-12" : "h-12 w-16")}
          />
          {!compact && (
            <div className="min-w-0">
              <div className="truncate t-caption font-medium">{asset.filename}</div>
              <div className="t-caption text-muted-foreground">{asset.source}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}


