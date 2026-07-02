"use client";

import { useState } from "react";
import { Images, Maximize2, Send } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DSCard,
  DSSectionTitle,
  DSButton,
  DSEmptyState,
} from "@/components/ui/ds";
import { cn } from "@/lib/utils";
import type { MediaAsset } from "@/lib/types";
import { downloadMediaWorkbenchAsset } from "@/lib/api-client";
import { ImagePreviewModal } from "./ImagePreviewModal";

/**
 * 右侧缩略图面板（F6）
 *
 * - 2-3 列小图缩略图（每张约 120-160px）
 * - 点击缩略图弹出全屏预览弹窗（ImagePreviewModal）
 * - 缩略图上有勾选框，支持批量选中后一键加入参考篮
 * - 已选择数量提示
 */
export interface ThumbnailPanelProps {
  assets: MediaAsset[];
  selectedIds: string[];
  onToggle: (assetId: string) => void;
  onAddToBasket: (assetIds: string[]) => void;
  selectedCount: number;
  maxReferenceImages: number;
}

export function ThumbnailPanel({
  assets,
  selectedIds,
  onToggle,
  onAddToBasket,
  selectedCount,
  maxReferenceImages,
}: ThumbnailPanelProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewIndex, setPreviewIndex] = useState(0);

  function openPreview(index: number) {
    setPreviewIndex(index);
    setPreviewOpen(true);
  }

  function handleAddFromModal(assetId: string) {
    onAddToBasket([assetId]);
  }

  return (
    <DSCard className="h-full">
      <DSSectionTitle
        icon={<Images className="h-4 w-4" />}
        title="图片结果"
        desc="选择后可加入视频参考篮 · 点击图片全屏预览"
      />

      {assets.length === 0 ? (
        <DSEmptyState
          className="mt-6"
          icon={<Images className="h-5 w-5" />}
          title="暂无图片素材"
          desc="先在左侧生成图片，结果会出现在这里。"
        />
      ) : (
        <div className="mt-4 grid max-h-[560px] grid-cols-2 gap-3 overflow-y-auto scroll-fine sm:grid-cols-3">
          {assets.map((asset, index) => {
            const selected = selectedIds.includes(asset.asset_id);
            return (
              <div
                key={asset.asset_id}
                className={cn(
                  "group relative overflow-hidden rounded-lg border bg-background transition-all duration-300 ease-apple",
                  selected
                    ? "border-primary ring-2 ring-primary/25 shadow-apple-sm"
                    : "border-border hover:border-bronze/40 hover:-translate-y-0.5",
                )}
              >
                <button
                  type="button"
                  onClick={() => openPreview(index)}
                  className="block w-full cursor-zoom-in"
                  aria-label={`预览 ${asset.filename}`}
                >
                  <div className="aspect-square overflow-hidden bg-muted">
                    { }
                    <img
                      src={downloadMediaWorkbenchAsset(asset.asset_id)}
                      alt={asset.filename}
                      className="h-full w-full object-cover transition-transform duration-500 ease-apple group-hover:scale-[1.06]"
                    />
                  </div>
                </button>

                {/* 选中勾选框 */}
                <label
                  className="absolute left-2 top-2 inline-flex cursor-pointer items-center gap-2 rounded-md bg-background/90 px-1.5 py-1 shadow-apple-sm backdrop-blur-sm transition-all duration-200 ease-apple hover:bg-background"
                  onClick={(event) => event.stopPropagation()}
                >
                  <Checkbox
                    checked={selected}
                    onCheckedChange={() => onToggle(asset.asset_id)}
                    aria-label={`选择 ${asset.filename}`}
                  />
                </label>

                {/* 全屏预览按钮 */}
                <button
                  type="button"
                  onClick={() => openPreview(index)}
                  className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-md bg-background/90 text-muted-foreground shadow-apple-sm backdrop-blur-sm transition-all duration-200 ease-apple hover:bg-background hover:text-foreground"
                  aria-label={`全屏预览 ${asset.filename}`}
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>

                {/* 文件名 / prompt */}
                <div className="px-2 py-2">
                  <div className="truncate text-[11px] font-medium text-foreground">{asset.filename}</div>
                  <p className="line-clamp-1 text-[10px] text-muted-foreground">
                    {asset.prompt || asset.source}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 底部操作 */}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="t-caption text-muted-foreground">
          已选择 <span className="font-semibold text-foreground">{selectedCount}</span> 张 · 参考篮最多 {maxReferenceImages} 张
        </p>
        <DSButton
          variant="secondary"
          size="md"
          onClick={() => onAddToBasket(selectedIds)}
          disabled={selectedCount === 0}
        >
          <Send className="h-4 w-4" />加入视频参考篮
        </DSButton>
      </div>

      <ImagePreviewModal
        open={previewOpen}
        onOpenChange={setPreviewOpen}
        assets={assets}
        index={previewIndex}
        onIndexChange={setPreviewIndex}
        onAddToBasket={handleAddFromModal}
      />
    </DSCard>
  );
}
