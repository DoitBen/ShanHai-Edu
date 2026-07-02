"use client";

import { useCallback, useEffect } from "react";
import { ChevronLeft, ChevronRight, Download, Send, X } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { DSButton } from "@/components/ui/ds";
import { cn } from "@/lib/utils";
import type { MediaAsset } from "@/lib/types";
import { downloadMediaWorkbenchAsset } from "@/lib/api-client";

/**
 * 图片全屏预览弹窗（F6）
 *
 * - 大图居中显示
 * - 左右箭头切换上一张/下一张
 * - 下载按钮
 * - 「加入视频参考篮」按钮
 * - ESC 关闭（Dialog 自带）/ 点击遮罩关闭（Dialog 自带）
 */
export interface ImagePreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assets: MediaAsset[];
  index: number;
  onIndexChange: (index: number) => void;
  onAddToBasket: (assetId: string) => void;
  /** 单图下载基础 URL 工厂（默认走 mediaWorkbenchAsset 下载端点） */
  downloadUrl?: (assetId: string) => string;
}

export function ImagePreviewModal({
  open,
  onOpenChange,
  assets,
  index,
  onIndexChange,
  onAddToBasket,
  downloadUrl = downloadMediaWorkbenchAsset,
}: ImagePreviewModalProps) {
  const total = assets.length;
  const current = total > 0 ? assets[clamp(index, 0, total - 1)] : null;

  const goPrev = useCallback(() => {
    if (total <= 1) return;
    onIndexChange((index - 1 + total) % total);
  }, [index, total, onIndexChange]);

  const goNext = useCallback(() => {
    if (total <= 1) return;
    onIndexChange((index + 1) % total);
  }, [index, total, onIndexChange]);

  // 左右方向键切换
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goPrev();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goNext();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, goPrev, goNext]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton={false}
        className="flex max-h-[92vh] w-full max-w-[1200px] flex-col gap-0 overflow-hidden bg-black/95 p-0 sm:max-w-[1200px]"
      >
        <DialogTitle className="sr-only">图片预览</DialogTitle>
        {/* 顶部工具栏 */}
        <div className="flex items-center justify-between gap-4 border-b border-white/10 px-5 py-3 text-white/80">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-white">
              {current?.filename || "图片预览"}
            </div>
            <div className="mt-0.5 text-[11px] text-white/60">
              {total > 0 ? `${index + 1} / ${total}` : "暂无图片"}
              {current?.prompt ? ` · ${truncate(current.prompt, 60)}` : ""}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {current && (
              <>
                <a
                  href={downloadUrl(current.asset_id)}
                  className={cn(
                    "inline-flex h-9 items-center gap-2 rounded-lg border border-white/20 px-3.5 text-xs font-medium text-white/90 transition-all duration-300 ease-apple",
                    "hover:border-white/50 hover:bg-white/10 hover:-translate-y-0.5",
                  )}
                  download
                >
                  <Download className="h-3.5 w-3.5" />
                  下载
                </a>
                <DSButton
                  variant="primary"
                  size="sm"
                  onClick={() => current && onAddToBasket(current.asset_id)}
                >
                  <Send className="h-3.5 w-3.5" />
                  加入视频参考篮
                </DSButton>
              </>
            )}
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              aria-label="关闭"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/20 text-white/80 transition-all duration-300 ease-apple hover:border-white/50 hover:bg-white/10"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 大图区 */}
        <div className="relative flex min-h-[320px] flex-1 items-center justify-center bg-black/80 p-4">
          {total > 1 && (
            <button
              type="button"
              onClick={goPrev}
              aria-label="上一张"
              className="absolute left-3 z-10 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition-all duration-300 ease-apple hover:bg-white/25 hover:-translate-y-0.5"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          )}
          {current ? (
             
            <img
              src={downloadUrl(current.asset_id)}
              alt={current.filename}
              className="max-h-[78vh] max-w-full rounded-lg object-contain shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
            />
          ) : (
            <div className="text-sm text-white/60">暂无可预览的图片</div>
          )}
          {total > 1 && (
            <button
              type="button"
              onClick={goNext}
              aria-label="下一张"
              className="absolute right-3 z-10 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition-all duration-300 ease-apple hover:bg-white/25 hover:-translate-y-0.5"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function clamp(value: number, min: number, max: number): number {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}
