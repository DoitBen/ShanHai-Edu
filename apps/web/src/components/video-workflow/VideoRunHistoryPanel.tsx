"use client";

import { AlertTriangle, Clock, Download, Film, History, RefreshCw, RotateCcw } from "lucide-react";
import {
  downloadVideoWorkflowRun,
  videoWorkflowAssetContent,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { VideoWorkflowRun } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface VideoRunHistoryPanelProps {
  projectId: string;
  runs: VideoWorkflowRun[];
  selectedRunId: string | null;
  busyRunId: string | null;
  onSelect: (runId: string) => void;
  onRetry: (runId: string) => Promise<void>;
  onReuse: (run: VideoWorkflowRun) => void;
}

function statusText(run: VideoWorkflowRun): string {
  if (run.status === "completed" && run.download_status === "download_failed") return "下载失败";
  if (run.status === "completed") return "已完成";
  if (run.status === "failed") return "失败";
  if (run.status === "submission_unknown") return "提交待确认";
  if (run.status === "processing") return "生成中";
  if (run.status === "queued") return "排队";
  return "提交中";
}

function statusVariant(run: VideoWorkflowRun): "default" | "secondary" | "destructive" | "outline" {
  if (run.status === "failed" || run.status === "submission_unknown" || run.download_status === "download_failed") {
    return "destructive";
  }
  if (run.status === "completed") return "default";
  if (run.status === "processing" || run.status === "queued") return "secondary";
  return "outline";
}

function statusDotClass(run: VideoWorkflowRun): string {
  if (run.status === "failed" || run.status === "submission_unknown") return "bg-destructive";
  if (run.status === "completed") return "bg-success";
  if (run.status === "processing" || run.status === "queued") return "bg-primary anim-pulse-soft";
  return "bg-muted-foreground";
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function canRetry(run: VideoWorkflowRun): boolean {
  return run.retryable || run.status === "submission_unknown" || run.download_status === "download_failed";
}

/* ETA 剩余秒数：仅 processing / queued 状态返回数值 */
function estimateEta(run: VideoWorkflowRun): number | null {
  if (run.status === "queued" || run.status === "submission_unknown") return 60;
  if (run.status === "processing") {
    const totalSeconds = Math.max(5, run.duration_sec * 6);
    return Math.max(2, Math.ceil(((100 - run.progress) / 100) * totalSeconds) + 2);
  }
  return null;
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m} 分 ${s} 秒` : `${m} 分`;
}

export function VideoRunHistoryPanel({
  projectId,
  runs,
  selectedRunId,
  busyRunId,
  onSelect,
  onRetry,
  onReuse,
}: VideoRunHistoryPanelProps) {
  const completedCount = runs.filter((r) => r.status === "completed").length;
  const failedCount = runs.filter((r) => r.status === "failed" || r.status === "submission_unknown").length;
  const activeCount = runs.filter((r) => r.status === "processing" || r.status === "queued").length;

  return (
    <section className="card-pro card-pro-radius flex h-full flex-col rounded-lg border border-border bg-card p-4 shadow-apple-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="t-module font-semibold text-foreground">视频任务</h3>
          <p className="mt-1 t-caption text-muted-foreground">{runs.length} 条历史</p>
        </div>
        <History className="h-4 w-4 text-muted-foreground" />
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto scroll-fine pr-1" style={{ maxHeight: "calc(100vh - 220px)" }}>
        {runs.length === 0 && (
          <div className="empty-state-pro rounded-lg border border-dashed border-border">
            <div className="icon-wrap">
              <Film className="h-5 w-5" />
            </div>
            <div className="title">暂无视频任务</div>
            <div className="desc">填写提示词并生成后，任务记录会出现在这里。可复用历史参数快速再生成。</div>
          </div>
        )}
        {runs.map((run) => {
          const selected = selectedRunId === run.run_id;
          const references = run.reference_assets || [];
          const isActive = run.status === "processing" || run.status === "queued";
          const eta = estimateEta(run);
          const retryLabel =
            run.status === "completed" && run.download_status === "download_failed"
              ? "重试下载"
              : "重试生成";
          return (
            <article
              key={run.run_id}
              className={cn(
                "relative overflow-hidden rounded-lg border bg-background p-3 transition-all duration-300 ease-apple",
                selected
                  ? "border-primary ring-2 ring-primary/15 shadow-apple-sm"
                  : isActive
                  ? "border-primary/30 shadow-apple-sm"
                  : "border-border hover:border-bronze/30",
              )}
            >
              {/* 扫描光效：仅 active 状态显示 */}
              {isActive && (
                <span
                  className="pointer-events-none absolute inset-x-0 top-0 h-px anim-pulse-soft"
                  style={{
                    background:
                      "linear-gradient(90deg, transparent 0%, rgba(45,67,86,0.45) 50%, transparent 100%)",
                  }}
                  aria-hidden
                />
              )}
              <button type="button" className="block w-full text-left" onClick={() => onSelect(run.run_id)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className={cn("h-2 w-2 shrink-0 rounded-full", statusDotClass(run))} />
                      <Badge variant={statusVariant(run)}>{statusText(run)}</Badge>
                    </div>
                    <div className="mt-2 line-clamp-2 t-caption text-foreground">{run.prompt}</div>
                  </div>
                  <time className="shrink-0 t-caption text-muted-foreground">{formatDateTime(run.created_at)}</time>
                </div>
                <div className="mt-3">
                  <div className="progress-pro">
                    <div
                      className={cn("progress-pro-bar", isActive && "anim-pulse-soft")}
                      style={{ width: `${Math.max(2, run.progress)}%` }}
                    />
                  </div>
                  <div className="mt-1.5 flex items-center justify-between t-caption text-muted-foreground">
                    <span>{run.progress}%</span>
                    {eta !== null && (
                      <span className="inline-flex items-center gap-1 text-bronze">
                        <Clock className="h-3 w-3" />
                        预计剩余 {formatEta(eta)}
                      </span>
                    )}
                  </div>
                </div>
                {references.length > 0 && (
                  <div className="mt-3 flex items-center gap-1.5">
                    {references.slice(0, 4).map((asset) => (
                      <img
                        key={asset.asset_id}
                        src={videoWorkflowAssetContent(projectId, asset.asset_id)}
                        alt={asset.filename}
                        loading="lazy"
                        className="h-9 w-12 rounded border border-border object-cover"
                      />
                    ))}
                    {references.length > 4 && (
                      <span className="flex h-9 min-w-10 items-center justify-center rounded border border-border bg-muted px-2 t-caption">
                        +{references.length - 4}
                      </span>
                    )}
                  </div>
                )}
                {(run.status === "failed" || run.status === "submission_unknown") && (
                  <p className="mt-2 line-clamp-2 t-caption text-destructive">
                    <AlertTriangle className="mr-1 inline h-3 w-3" />
                    {run.error_message || run.error_code || "任务未完成"}
                  </p>
                )}
              </button>

              <div className="mt-3 grid grid-cols-2 gap-2">
                {canRetry(run) && (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="btn-cta-secondary gap-1.5"
                    disabled={busyRunId === run.run_id}
                    onClick={() => void onRetry(run.run_id)}
                  >
                    {busyRunId === run.run_id ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                    {retryLabel}
                  </Button>
                )}
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="btn-cta-secondary gap-1.5"
                  onClick={() => onReuse(run)}
                >
                  <RotateCcw className="h-4 w-4" />
                  复用参数
                </Button>
                {run.video_ready && (
                  <Button asChild size="sm" className="btn-cta-primary gap-1.5">
                    <a href={downloadVideoWorkflowRun(projectId, run.run_id)}>
                      <Download className="h-4 w-4" />
                      下载
                    </a>
                  </Button>
                )}
              </div>
            </article>
          );
        })}
      </div>

      {/* 底部状态汇总 */}
      {runs.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-3">
          <div className="rounded-md bg-muted/30 p-2 text-center">
            <div className="t-overline text-muted-foreground/70">已完成</div>
            <div className="mt-0.5 t-module font-bold text-success">{completedCount}</div>
          </div>
          <div className="rounded-md bg-muted/30 p-2 text-center">
            <div className="t-overline text-muted-foreground/70">进行中</div>
            <div className="mt-0.5 t-module font-bold text-primary">{activeCount}</div>
          </div>
          <div className="rounded-md bg-muted/30 p-2 text-center">
            <div className="t-overline text-muted-foreground/70">失败</div>
            <div className="mt-0.5 t-module font-bold text-destructive">{failedCount}</div>
          </div>
        </div>
      )}
    </section>
  );
}
