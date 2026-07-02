"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Download,
  Film,
  Loader2,
  RefreshCw,
} from "lucide-react";
import {
  DSBadge,
  DSButton,
  DSCard,
  DSEmptyState,
  DSProgress,
  DSStatusDot,
  DSSectionTitle,
} from "@/components/ui/ds";
import { cn } from "@/lib/utils";
import { downloadVideoWorkbenchRun } from "@/lib/api-client";
import type { VideoWorkbenchRun } from "@/lib/types";
import { DS_ANCHOR_PRIMARY_SM } from "./constants";

/** DS 风格内联错误提示条 —— 替换原 alert-error-pro 自定义类（D10/F10） */
function DSErrorAlert({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border border-[#9a4747]/25 bg-[#9a4747]/8 px-3.5 py-2 t-caption text-[#9a4747]",
      )}
    >
      <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
      <span>{children}</span>
    </div>
  );
}

/**
 * 视频任务面板（F7）
 *
 * 任务卡片改为缩略图模式：
 * - 已完成：视频封面缩略图（<video> 抓首帧）+ 下载按钮
 * - 处理中：进度条 + 预估剩余时间
 * - 排队中：「排队中」占位图
 * - 失败：错误信息卡片
 *
 * 用 DSStatusDot + DSProgress 组件。
 */
export interface VideoRunPanelProps {
  runs: VideoWorkbenchRun[];
  syncingRunId: string | null;
  onSync: (runId: string) => Promise<void>;
}

export function VideoRunPanel({ runs, syncingRunId, onSync }: VideoRunPanelProps) {
  return (
    <DSCard className="h-full p-4">
      <DSSectionTitle
        className="mb-3"
        icon={<Clock className="h-4 w-4" />}
        title="视频任务"
        desc="任务队列"
      />
      {runs.length === 0 ? (
        <DSEmptyState
          className="mt-4"
          icon={<Clock className="h-4 w-4" />}
          title="等待生成"
          desc="提交视频生成后，任务状态会出现在这里"
        />
      ) : (
        <div
          className="mt-4 flex-1 space-y-3 overflow-y-auto scroll-fine"
          style={{ maxHeight: "calc(100vh - 320px)" }}
        >
          {runs.map((run) => (
            <VideoRunCard
              key={run.run_id}
              run={run}
              syncing={syncingRunId === run.run_id}
              onSync={() => void onSync(run.run_id)}
            />
          ))}
        </div>
      )}
    </DSCard>
  );
}

/** 单条视频任务卡片 */
function VideoRunCard({
  run,
  syncing,
  onSync,
}: {
  run: VideoWorkbenchRun;
  syncing: boolean;
  onSync: () => void;
}) {
  const isActive = run.status === "processing" || run.status === "queued";
  const isCompleted = run.status === "completed" || run.status === "completed_pending_download";
  const isFailed = run.status === "failed";
  const isQueued = run.status === "queued";

  const dotStatus: "active" | "completed" | "failed" | "pending" = isCompleted
    ? "completed"
    : isFailed
      ? "failed"
      : isActive
        ? "active"
        : "pending";

  const badgeVariant: "success" | "warning" | "error" | "info" | "neutral" = isFailed
    ? "error"
    : isCompleted
      ? "success"
      : isActive
        ? "info"
        : "neutral";

  const progress = run.progress || 0;
  const remainingSec = estimateRemainingSeconds(run.status, progress);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border bg-background transition-all duration-300 ease-apple",
        isActive ? "border-primary/30 shadow-apple-sm" : "border-border hover:border-bronze/30",
      )}
    >
      <div className="flex flex-col gap-3 p-3">
        <div className="flex items-center gap-3">
          <DSStatusDot status={dotStatus} />
          <DSBadge variant={badgeVariant}>{run.status}</DSBadge>
          {isActive && (
            <span className="flex items-center gap-3 t-caption text-muted-foreground">
              <Clock className="h-3 w-3" />
              {progress}%
            </span>
          )}
          {isCompleted && run.download_path && (
            <span className="flex items-center gap-3 t-caption text-success">
              <CheckCircle2 className="h-3 w-3" />可下载
            </span>
          )}
        </div>

        {/* 缩略图区域（按状态展示不同占位） */}
        <RunThumbnail run={run} isCompleted={isCompleted} isQueued={isQueued} isFailed={isFailed} />

        <p className="line-clamp-2 t-caption text-foreground">{run.prompt || run.run_id}</p>

        {isActive && (
          <div className="flex items-center gap-3">
            <DSProgress value={progress} variant="default" className="flex-1" />
            {remainingSec !== null && (
              <span className="shrink-0 tabular-nums t-caption text-muted-foreground">
                ≈ {remainingSec}s
              </span>
            )}
          </div>
        )}

        {run.error_message && (
          <DSErrorAlert>{run.error_message}</DSErrorAlert>
        )}

        <div className="flex shrink-0 gap-3">
          <DSButton
            variant="secondary"
            size="sm"
            className="t-caption"
            onClick={onSync}
            disabled={syncing}
          >
            {syncing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            同步
          </DSButton>
          {run.download_path && (
            <a
              href={downloadVideoWorkbenchRun(run.run_id)}
              className={cn(DS_ANCHOR_PRIMARY_SM, "t-caption")}
              download
            >
              <Download className="h-3.5 w-3.5" />下载
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

/** 任务缩略图区域 */
function RunThumbnail({
  run,
  isCompleted,
  isQueued,
  isFailed,
}: {
  run: VideoWorkbenchRun;
  isCompleted: boolean;
  isQueued: boolean;
  isFailed: boolean;
}) {
  // 已完成且可下载 —— 用 video 元素抓首帧
  if (isCompleted && run.download_path) {
    const videoUrl = downloadVideoWorkbenchRun(run.run_id);
    return (
      <div className="relative aspect-video overflow-hidden rounded-md bg-black">
        <video
          src={`${videoUrl}#t=0.1`}
          className="h-full w-full object-cover"
          preload="metadata"
          muted
          playsInline
          aria-label={`视频缩略图 ${run.run_id}`}
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black/20">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/85 text-foreground shadow-apple-sm">
            <Film className="h-4 w-4" />
          </span>
        </div>
      </div>
    );
  }

  // 排队中 —— 占位图
  if (isQueued) {
    return (
      <div className="flex aspect-video items-center justify-center rounded-md border border-dashed border-border bg-muted/40">
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Clock className="h-5 w-5" />
          <span className="t-caption font-medium">排队中</span>
        </div>
      </div>
    );
  }

  // 失败 —— 错误信息卡片视觉
  if (isFailed) {
    return (
      <div className="flex aspect-video items-center justify-center rounded-md border border-dashed border-[#9a4747]/40 bg-[#9a4747]/8">
        <div className="flex flex-col items-center gap-2 text-[#9a4747]">
          <AlertTriangle className="h-5 w-5" />
          <span className="t-caption font-medium">生成失败</span>
        </div>
      </div>
    );
  }

  // 处理中 —— 旋转图标占位
  return (
    <div className="flex aspect-video items-center justify-center rounded-md border border-dashed border-primary/30 bg-primary/5">
      <div className="flex flex-col items-center gap-2 text-primary">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="t-caption font-medium">生成中…</span>
      </div>
    </div>
  );
}

/** 预估剩余秒数 —— 简单线性外推（仅展示用） */
function estimateRemainingSeconds(status: string, progress: number): number | null {
  if (status !== "processing") return null;
  if (progress <= 0 || progress >= 100) return null;
  // 假设满进度 60s，线性外推
  const remaining = Math.max(1, Math.round(((100 - progress) / 100) * 60));
  return remaining;
}
