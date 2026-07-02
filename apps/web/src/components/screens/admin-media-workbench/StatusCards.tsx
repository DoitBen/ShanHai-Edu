"use client";

import type { ReactNode } from "react";
import { Film, ImagePlus, Images, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { DSCard, DSBadge } from "@/components/ui/ds";
import type { StatusTileProps, StatusTone } from "./types";

/**
 * 状态卡片（StatusTile）—— 顶部 4 张指标卡。
 * loading 态用 `loading-dot` 轻量动画；用 DSCard + DSBadge 重写。
 */
export function StatusTile({ icon, label, value, tone, loading }: StatusTileProps) {
  const toneText =
    tone === "success"
      ? "stat-value-success"
      : tone === "info"
        ? "stat-value-info"
        : tone === "warning"
          ? "stat-value-warning"
          : "text-foreground font-semibold";
  const iconClass =
    tone === "success"
      ? "text-success"
      : tone === "info"
        ? "text-info"
        : tone === "warning"
          ? "text-warning"
          : "text-muted-foreground";
  const badgeVariant: "success" | "info" | "warning" | "neutral" =
    tone === "success" ? "success" : tone === "info" ? "info" : tone === "warning" ? "warning" : "neutral";
  return (
    <DSCard hover={false} className="h-full p-4">
      <div className="flex items-center justify-between">
        <span className="t-caption font-medium text-muted-foreground">{label}</span>
        <span className={iconClass}>{icon}</span>
      </div>
      <div className={cn("mt-3 flex items-center gap-3 text-lg", toneText)}>
        {loading && <span className="loading-dot" />}
        {value}
      </div>
      <div className="mt-3">
        <DSBadge variant={badgeVariant}>{value}</DSBadge>
      </div>
    </DSCard>
  );
}

/** 4 张状态卡片（图片接口 / 视频接口 / 图片素材 / 视频参考篮） */
export interface StatusCardsProps {
  workbenchLoaded: boolean;
  providerReadyImage: boolean;
  providerReadyVideo: boolean;
  imageAssetsCount: number;
  basketCount: number;
  maxReferenceImages: number;
}

/** 卡片网格容器 + 4 张卡片 */
export function StatusCards({
  workbenchLoaded,
  providerReadyImage,
  providerReadyVideo,
  imageAssetsCount,
  basketCount,
  maxReferenceImages,
}: StatusCardsProps) {
  const imageTone: StatusTone = !workbenchLoaded ? "neutral" : providerReadyImage ? "success" : "warning";
  const videoTone: StatusTone = !workbenchLoaded ? "neutral" : providerReadyVideo ? "success" : "warning";
  const basketTone: StatusTone =
    basketCount > maxReferenceImages ? "warning" : basketCount > 0 ? "success" : "neutral";

  const iconFor = (Icon: ReactNode) => Icon;

  return (
    <div className="mt-6 grid gap-4 md:grid-cols-4 items-stretch">
      <StatusTile
        icon={iconFor(<ImagePlus className="h-4 w-4" />)}
        label="图片接口"
        value={!workbenchLoaded ? "检测中" : providerReadyImage ? "已连接" : "未连接"}
        loading={!workbenchLoaded}
        tone={imageTone}
      />
      <StatusTile
        icon={iconFor(<Film className="h-4 w-4" />)}
        label="视频接口"
        value={!workbenchLoaded ? "检测中" : providerReadyVideo ? "已连接" : "未连接"}
        loading={!workbenchLoaded}
        tone={videoTone}
      />
      <StatusTile
        icon={iconFor(<Images className="h-4 w-4" />)}
        label="图片素材"
        value={`${imageAssetsCount} 张`}
        tone="info"
      />
      <StatusTile
        icon={iconFor(<Layers className="h-4 w-4" />)}
        label="视频参考篮"
        value={`${basketCount} / ${maxReferenceImages}`}
        tone={basketTone}
      />
    </div>
  );
}
