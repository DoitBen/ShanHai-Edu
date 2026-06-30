"use client";

import { Download, RefreshCw, RotateCcw } from "lucide-react";
import {
  downloadVideoWorkflowRun,
  videoWorkflowAssetContent,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { VideoWorkflowRun } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

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

export function VideoRunHistoryPanel({
  projectId,
  runs,
  selectedRunId,
  busyRunId,
  onSelect,
  onRetry,
  onReuse,
}: VideoRunHistoryPanelProps) {
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <div className="mb-4">
        <h3 className="t-module">视频任务</h3>
        <p className="mt-1 t-caption text-muted-foreground">{runs.length} 条历史</p>
      </div>

      <div className="space-y-3">
        {runs.length === 0 && (
          <div className="rounded-md border border-dashed border-border bg-muted/20 p-6 text-center t-caption text-muted-foreground">
            暂无任务
          </div>
        )}
        {runs.map((run) => {
          const selected = selectedRunId === run.run_id;
          const references = run.reference_assets || [];
          const retryLabel =
            run.status === "completed" && run.download_status === "download_failed"
              ? "重试下载"
              : "重试生成";
          return (
            <article
              key={run.run_id}
              className={cn(
                "rounded-md border bg-background p-3 transition-colors",
                selected ? "border-primary ring-1 ring-primary/20" : "border-border hover:border-muted-foreground/40",
              )}
            >
              <button type="button" className="block w-full text-left" onClick={() => onSelect(run.run_id)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Badge variant={statusVariant(run)}>{statusText(run)}</Badge>
                    <div className="mt-2 line-clamp-2 t-caption text-foreground">{run.prompt}</div>
                  </div>
                  <time className="shrink-0 t-caption text-muted-foreground">{formatDateTime(run.created_at)}</time>
                </div>
                <div className="mt-3">
                  <Progress value={run.progress} />
                  <div className="mt-1 t-caption text-muted-foreground">{run.progress}%</div>
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
                    className="gap-1.5"
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
                  className="gap-1.5"
                  onClick={() => onReuse(run)}
                >
                  <RotateCcw className="h-4 w-4" />
                  复用参数
                </Button>
                {run.video_ready && (
                  <Button asChild size="sm" variant="secondary" className="gap-1.5">
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
    </section>
  );
}
