"use client";

import { Download, Images, RefreshCw } from "lucide-react";
import {
  DSCard,
  DSSectionTitle,
  DSBadge,
  DSEmptyState,
} from "@/components/ui/ds";
import type { MediaAsset, ImageWorkbenchRun, VideoWorkbenchRun } from "@/lib/types";
import { downloadMediaWorkbenchAsset } from "@/lib/api-client";
import { DS_ANCHOR_SECONDARY_SM } from "./constants";

/**
 * 素材篮 / 历史面板（第 3 个 Tab）
 *
 * 左：素材库（图片 + 上传参考图 + 视频输出统一展示）
 * 右：历史任务（图片任务 + 视频任务）
 */
export interface AssetBasketPanelProps {
  imageAssets: MediaAsset[];
  videoAssets: MediaAsset[];
  imageRuns: ImageWorkbenchRun[];
  videoRuns: VideoWorkbenchRun[];
}

export function AssetBasketPanel({
  imageAssets,
  videoAssets,
  imageRuns,
  videoRuns,
}: AssetBasketPanelProps) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1fr] items-stretch">
      <DSCard className="h-full">
        <DSSectionTitle
          icon={<Images className="h-4 w-4" />}
          title="素材库"
          desc="图片、上传参考图和视频输出统一保存"
        />
        <AssetList assets={[...imageAssets, ...videoAssets]} />
      </DSCard>
      <DSCard className="h-full">
        <DSSectionTitle
          icon={<RefreshCw className="h-4 w-4" />}
          title="历史任务"
          desc="图片任务和视频任务"
        />
        <HistoryList imageRuns={imageRuns} videoRuns={videoRuns} />
      </DSCard>
    </div>
  );
}

/** 素材列表（下载入口） */
function AssetList({ assets }: { assets: MediaAsset[] }) {
  if (!assets.length) {
    return (
      <DSEmptyState
        className="mt-6"
        icon={<Images className="h-5 w-5" />}
        title="暂无素材"
        desc="生成图片或视频后，素材会在这里归档。"
      />
    );
  }
  return (
    <div className="mt-6 max-h-[560px] space-y-3 overflow-y-auto scroll-fine">
      {assets.map((asset) => (
        <div
          key={asset.asset_id}
          className="flex items-center justify-between gap-4 rounded-lg border border-border bg-background p-3 transition-all duration-300 ease-apple hover:border-bronze/30 hover:-translate-y-0.5"
        >
          <div className="min-w-0">
            <div className="truncate t-body font-medium text-foreground">{asset.filename}</div>
            <div className="t-caption text-muted-foreground">
              {asset.asset_type} · {asset.source}
            </div>
          </div>
          <a href={downloadMediaWorkbenchAsset(asset.asset_id)} className={DS_ANCHOR_SECONDARY_SM} download>
            <Download className="h-3.5 w-3.5" />下载
          </a>
        </div>
      ))}
    </div>
  );
}

/** 历史任务列表 */
function HistoryList({
  imageRuns,
  videoRuns,
}: {
  imageRuns: ImageWorkbenchRun[];
  videoRuns: VideoWorkbenchRun[];
}) {
  const rows = [
    ...imageRuns.map((run) => ({
      id: run.run_id,
      kind: "图片" as const,
      status: run.status,
      prompt: run.prompt,
      meta: `${run.assets?.length || 0} 张`,
    })),
    ...videoRuns.map((run) => ({
      id: run.run_id,
      kind: "视频" as const,
      status: run.status,
      prompt: run.prompt,
      meta: `${run.progress || 0}%`,
    })),
  ];
  if (!rows.length) {
    return (
      <DSEmptyState
        className="mt-6"
        icon={<RefreshCw className="h-5 w-5" />}
        title="暂无历史任务"
        desc="真实生成任务会在这里保留最近记录。"
      />
    );
  }
  return (
    <div className="mt-6 max-h-[560px] space-y-3 overflow-y-auto scroll-fine">
      {rows.map((row) => {
        const badgeVariant: "success" | "warning" | "error" | "info" | "neutral" =
          row.status === "failed"
            ? "error"
            : row.status === "completed" || row.status === "completed_pending_download"
              ? "success"
              : row.status === "processing" || row.status === "queued"
                ? "info"
                : "neutral";
        return (
          <div
            key={row.id}
            className="rounded-lg border border-border bg-background p-3 transition-all duration-300 ease-apple hover:border-bronze/30 hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="t-caption font-medium text-muted-foreground">
                {row.kind} · {row.meta}
              </div>
              <DSBadge variant={badgeVariant}>{row.status}</DSBadge>
            </div>
            <p className="mt-2 line-clamp-2 t-caption text-foreground">{row.prompt || row.id}</p>
          </div>
        );
      })}
    </div>
  );
}
