"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Download, Film, Loader2, Play, Sparkles } from "lucide-react";
import { downloadVideoWorkflowRun, streamVideoWorkflowRun } from "@/lib/api-client";
import type { VideoWorkflowConfig, VideoWorkflowRun } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const videoComposerSubmitLocks = new Set<string>();

interface VideoComposerPanelProps {
  projectId: string;
  config: VideoWorkflowConfig;
  prompt: string;
  selectedCount: number;
  selectedRun: VideoWorkflowRun | null;
  submitting: boolean;
  hasActiveRun: boolean;
  onPromptChange: (value: string) => void;
  onSubmit: () => Promise<boolean>;
}

function statusLabel(run: VideoWorkflowRun | null): string {
  if (!run) return "待生成";
  if (run.status === "completed" && run.video_ready) return "已完成";
  if (run.status === "completed_pending_download") return "等待视频文件";
  if (run.status === "failed") return "生成失败";
  if (run.status === "submission_unknown") return "提交待确认";
  if (run.status === "processing") return "生成中";
  if (run.status === "queued") return "排队中";
  return "提交中";
}

function VideoRunPlaceholder({ run }: { run: VideoWorkflowRun | null }) {
  return (
    <div className="flex aspect-video w-full items-center justify-center bg-muted">
      <div className="max-w-sm text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-background text-muted-foreground">
          {run?.status === "failed" || run?.status === "submission_unknown" ? (
            <AlertTriangle className="h-5 w-5 text-destructive" />
          ) : run ? (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          ) : (
            <Film className="h-5 w-5" />
          )}
        </div>
        <div className="mt-3 t-module">{statusLabel(run)}</div>
        {run && (
          <div className="mt-3">
            <Progress value={run.progress} />
            <div className="mt-1 t-caption text-muted-foreground">{run.progress}%</div>
          </div>
        )}
      </div>
    </div>
  );
}

function VideoPreview({ projectId, run }: { projectId: string; run: VideoWorkflowRun }) {
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [reloadKey, setReloadKey] = useState(0);
  const downloadUrl = downloadVideoWorkflowRun(projectId, run.run_id);
  return (
    <div className="relative">
      {state === "loading" && (
        <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-black/60 t-caption text-white">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载视频
        </div>
      )}
      {state === "error" && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-black/80 px-4 text-center text-white">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <div className="t-caption">视频无法播放，可以重新加载或下载源文件。</div>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => {
              setState("loading");
              setReloadKey((current) => current + 1);
            }}
          >
            重新加载
          </Button>
          <Button type="button" size="sm" variant="secondary" asChild>
            <a href={downloadUrl} download>
              下载源文件
            </a>
          </Button>
        </div>
      )}
      <video
        key={`${run.run_id}-${reloadKey}`}
        controls
        preload="metadata"
        className="aspect-video w-full bg-black"
        src={streamVideoWorkflowRun(projectId, run.run_id)}
        onLoadedMetadata={() => setState("ready")}
        onError={() => setState("error")}
      />
      {state === "ready" && (
        <div className="absolute bottom-2 right-2">
          <Button type="button" size="sm" variant="secondary" className="gap-1 bg-background/90" asChild>
            <a href={downloadUrl} download>
              <Download className="h-3.5 w-3.5" />
              下载源文件
            </a>
          </Button>
        </div>
      )}
    </div>
  );
}

export function VideoComposerPanel({
  projectId,
  config,
  prompt,
  selectedCount,
  selectedRun,
  submitting,
  hasActiveRun,
  onPromptChange,
  onSubmit,
}: VideoComposerPanelProps) {
  const activeRunObservedRef = useRef(false);
  const normalizedPrompt = prompt.trim();
  const promptTooLong = prompt.length > 5000;
  const submitLocked = videoComposerSubmitLocks.has(projectId);
  const hardSubmitDisabled = !config.provider_ready || !normalizedPrompt || promptTooLong;
  const submitBlocked = hasActiveRun || submitting || submitLocked;
  const submitDisabled = submitBlocked || hardSubmitDisabled;
  const modeLabel = selectedCount > 0 ? `${selectedCount} 张参考图` : "文生视频";
  const disabledReason = !config.provider_ready
    ? config.provider_user_message
    : !normalizedPrompt
      ? "请先填写视频提示词。"
      : promptTooLong
        ? "视频提示词超过 5000 字，请删减后再生成。"
        : submitting || submitLocked
          ? "正在提交视频任务，请稍候。"
          : hasActiveRun
            ? "已有视频任务正在生成，请等待完成后再创建新任务。"
            : "";

  useEffect(() => {
    if (hasActiveRun) {
      activeRunObservedRef.current = true;
      return;
    }
    if (activeRunObservedRef.current) {
      activeRunObservedRef.current = false;
      videoComposerSubmitLocks.delete(projectId);
    }
  }, [hasActiveRun, projectId]);

  async function handleSubmit() {
    if (hardSubmitDisabled || submitBlocked || videoComposerSubmitLocks.has(projectId)) return;
    videoComposerSubmitLocks.add(projectId);
    let keepLocked = false;
    try {
      keepLocked = await onSubmit();
      if (!keepLocked) {
        videoComposerSubmitLocks.delete(projectId);
      }
    } finally {
      if (!keepLocked && !activeRunObservedRef.current && !hasActiveRun) {
        videoComposerSubmitLocks.delete(projectId);
      }
    }
  }

  return (
    <section className="rounded-md border border-border bg-card p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="t-module">创作与预览</h3>
          <p className="mt-1 t-caption text-muted-foreground">{modeLabel}</p>
        </div>
        <Badge variant={config.provider_ready ? "secondary" : "destructive"}>
          {config.provider_ready ? "可生成" : config.provider_user_message}
        </Badge>
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-black">
        {selectedRun?.video_ready ? (
          <VideoPreview projectId={projectId} run={selectedRun} />
        ) : (
          <VideoRunPlaceholder run={selectedRun} />
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge variant="outline">{config.model}</Badge>
        <Badge variant="outline">{config.size}</Badge>
        <Badge variant="outline">{config.duration_sec} 秒</Badge>
        <Badge variant="outline">单结果</Badge>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <Label htmlFor="video-workflow-prompt" className="t-caption text-muted-foreground">
            视频提示词
          </Label>
          <span className={promptTooLong ? "t-caption text-destructive" : "t-caption text-muted-foreground"}>
            {prompt.length}/5000
          </span>
        </div>
        <Textarea
          id="video-workflow-prompt"
          aria-label="视频提示词"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="描述画面主体、动作、镜头和课堂氛围。"
          className="min-h-36 resize-none bg-background"
        />
      </div>

      <Button
        className="mt-4 w-full gap-2"
        disabled={submitDisabled}
        aria-disabled={submitDisabled}
        onClick={() => void handleSubmit()}
      >
        {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : selectedCount ? <Play className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        生成 10 秒视频
      </Button>
      {disabledReason && (
        <p className={config.provider_ready ? "mt-2 t-caption text-muted-foreground" : "mt-2 t-caption text-destructive"}>
          {disabledReason}
        </p>
      )}
    </section>
  );
}
