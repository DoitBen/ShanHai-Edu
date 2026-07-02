"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, Download, Expand, Film, Loader2, Play, Sparkles, Wand2, Zap } from "lucide-react";
import { downloadVideoWorkflowRun, streamVideoWorkflowRun } from "@/lib/api-client";
import type { VideoWorkflowConfig, VideoWorkflowRun } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const videoComposerSubmitLocks = new Set<string>();

/* 六维结构化模板：主体 / 动作 / 运镜 / 氛围 / 画质 / 节奏 */
const PROMPT_TEMPLATES: { label: string; snippet: string }[] = [
  { label: "主体", snippet: "[主体：温暖明亮的小学数学课堂，桌面上有彩色计数棒和练习卡]" },
  { label: "动作", snippet: "[动作：镜头缓慢推进桌面上的计数棒和卡片，老师手指出示]" },
  { label: "运镜", snippet: "[运镜：缓慢推进 / 横向平移 / 环绕拍摄 / 固定机位]" },
  { label: "氛围", snippet: "[氛围：清晨阳光 / 暖色调 / 柔光散射]" },
  { label: "画质", snippet: "[画质：4K 超清 / 电影级动态范围 / 浅景深虚化]" },
  { label: "节奏", snippet: "[节奏：开场静默 2 秒，中段稳定推进，收尾定格特写]" },
];

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
    <div className="flex aspect-video w-full items-center justify-center bg-muted anim-float">
      <div className="max-w-sm text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center r-md bg-background text-muted-foreground shadow-apple-sm">
          {run?.status === "failed" || run?.status === "submission_unknown" ? (
            <AlertTriangle className="h-5 w-5 text-destructive" />
          ) : run ? (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          ) : (
            <Film className="h-5 w-5" />
          )}
        </div>
        <div className="mt-3 t-module font-semibold text-foreground">{statusLabel(run)}</div>
        {run && (
          <div className="mt-3">
            <div className="progress-pro mx-auto max-w-[200px]">
              <div
                className={cn("progress-pro-bar", run.status === "processing" && "anim-pulse-soft")}
                style={{ width: `${run.progress}%` }}
              />
            </div>
            <div className="mt-1.5 t-caption text-muted-foreground">{run.progress}%</div>
          </div>
        )}
      </div>
    </div>
  );
}

function VideoPreview({ projectId, run }: { projectId: string; run: VideoWorkflowRun }) {
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [reloadKey, setReloadKey] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const downloadUrl = downloadVideoWorkflowRun(projectId, run.run_id);
  return (
    <div className="relative">
      {state === "loading" && (
        <div className="absolute inset-0 z-10 flex items-center justify-center gap-sm bg-black/60 t-caption text-white">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载视频
        </div>
      )}
      {state === "error" && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-md bg-black/80 px-4 text-center text-white">
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
        <div className="absolute bottom-2 right-2 flex gap-sm">
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="gap-1 bg-background/90"
            onClick={() => setFullscreen(true)}
            aria-label="全屏预览"
          >
            <Expand className="h-3.5 w-3.5" />
          </Button>
          <Button type="button" size="sm" variant="secondary" className="gap-1 bg-background/90" asChild>
            <a href={downloadUrl} download>
              <Download className="h-3.5 w-3.5" />
              下载源文件
            </a>
          </Button>
        </div>
      )}
      <Dialog open={fullscreen} onOpenChange={setFullscreen}>
        <DialogContent className="max-w-[95vw] gap-0 border-border bg-black p-0 sm:max-w-[1200px]">
          <DialogTitle className="sr-only">视频全屏预览</DialogTitle>
          <video
            controls
            autoPlay
            className="aspect-video w-full bg-black"
            src={streamVideoWorkflowRun(projectId, run.run_id)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* 字数三色计数器：根据字数显示不同颜色 */
function promptLengthTone(length: number, max: number): {
  className: string;
  hint: string;
} {
  if (length > max) return { className: "text-destructive font-semibold", hint: "已超限" };
  if (length < 10) return { className: "text-muted-foreground", hint: "建议补充更多细节" };
  if (length < 200) return { className: "text-warning", hint: "略简短" };
  if (length < 2000) return { className: "text-success", hint: "字数合适" };
  return { className: "text-warning", hint: "偏长，可适当精简" };
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
  const [polishing, setPolishing] = useState(false);
  const normalizedPrompt = prompt.trim();
  const promptTooLong = prompt.length > 5000;
  const submitLocked = videoComposerSubmitLocks.has(projectId);
  const hardSubmitDisabled = !config.provider_ready || !normalizedPrompt || promptTooLong;
  const submitBlocked = hasActiveRun || submitting || submitLocked;
  const submitDisabled = submitBlocked || hardSubmitDisabled;
  const modeLabel = selectedCount > 0 ? `${selectedCount} 张参考图` : "文生视频";
  const videoCredits = 15; // 与媒体工作台保持一致

  const lengthTone = promptLengthTone(prompt.length, 5000);

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

  function insertTemplate(snippet: string) {
    onPromptChange(prompt.trim() ? `${prompt.trim()} ${snippet}` : snippet);
  }

  async function polishPrompt() {
    if (!normalizedPrompt || polishing) return;
    setPolishing(true);
    await new Promise((resolve) => setTimeout(resolve, 800));
    const hasSubject = /主体|课堂|桌面|老师|学生/.test(prompt);
    const hasAction = /动作|推进|横移|环绕|定格/.test(prompt);
    const hasAtmosphere = /氛围|光线|色调|阳光|柔光/.test(prompt);
    const hasQuality = /4K|超清|画质|电影级/.test(prompt);
    const additions: string[] = [];
    if (!hasSubject) additions.push("[主体：温暖明亮的小学数学课堂]");
    if (!hasAction) additions.push("[动作：镜头缓慢推进桌面]");
    if (!hasAtmosphere) additions.push("[氛围：清晨阳光、柔光散射]");
    if (!hasQuality) additions.push("[画质：4K 超清、电影级动态范围]");
    if (additions.length === 0) {
      toast.info("提示词已较为完整");
    } else {
      onPromptChange(`${prompt.trim()} ${additions.join(" ")}`);
      toast.success(`已补充 ${additions.length} 个维度`);
    }
    setPolishing(false);
  }

  return (
    <section className="card-unified card-pad-md">
      <div className="mb-lg flex items-start justify-between gap-md">
        <div>
          <h3 className="t-module font-semibold text-foreground">创作与预览</h3>
          <p className="mt-1 t-caption text-muted-foreground">{modeLabel}</p>
        </div>
        <Badge className="badge-unified" variant={config.provider_ready ? "secondary" : "destructive"}>
          {config.provider_ready ? "可生成" : config.provider_user_message}
        </Badge>
      </div>

      <div className="overflow-hidden r-lg border border-border bg-black">
        {selectedRun?.video_ready ? (
          <VideoPreview projectId={projectId} run={selectedRun} />
        ) : (
          <VideoRunPlaceholder run={selectedRun} />
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-sm">
        <Badge className="badge-unified" variant="outline">{config.model}</Badge>
        <Badge className="badge-unified" variant="outline">{config.size}</Badge>
        <Badge className="badge-unified" variant="outline">{config.duration_sec} 秒</Badge>
        <Badge className="badge-unified" variant="outline">单结果</Badge>
      </div>

      {/* 六维结构化模板 */}
      <div className="mt-4">
        <div className="mb-2 flex items-center gap-sm t-overline text-muted-foreground/70">
          <Wand2 className="h-3 w-3" />结构化模板
        </div>
        <div className="flex flex-wrap gap-sm">
          {PROMPT_TEMPLATES.map((tpl) => (
            <button
              key={tpl.label}
              type="button"
              onClick={() => insertTemplate(tpl.snippet)}
              className="pill-unified h-8!"
            >
              {tpl.label}
            </button>
          ))}
        </div>
      </div>

      {/* 提示词 + AI 润色 + 三色计数器 */}
      <div className="mt-4 space-y-sm">
        <div className="flex items-center justify-between gap-sm">
          <Label htmlFor="video-workflow-prompt" className="t-caption text-muted-foreground">
            视频提示词
          </Label>
          <div className="flex items-center gap-md">
            <button
              type="button"
              onClick={() => void polishPrompt()}
              disabled={!normalizedPrompt || polishing}
              className="ai-polish-link"
            >
              {polishing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}
              AI 润色
            </button>
            <span className={cn("t-caption tabular-nums", lengthTone.className)}>
              {prompt.length}/5000
              <span className="ml-1 font-normal text-muted-foreground/60">· {lengthTone.hint}</span>
            </span>
          </div>
        </div>
        <Textarea
          id="video-workflow-prompt"
          aria-label="视频提示词"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="描述画面主体、动作、镜头和课堂氛围。建议先用结构化模板补充维度，再用 AI 润色增强细节。"
          className="input-pro min-h-[120px] resize-none bg-background"
        />
      </div>

      {/* CTA 强化：btn-cta-primary + credits-hint */}
      <Button
        className="btn-cta-primary btn-lg mt-4 w-full gap-sm font-semibold"
        disabled={submitDisabled}
        aria-disabled={submitDisabled}
        onClick={() => void handleSubmit()}
      >
        {submitting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : selectedCount ? (
          <Play className="h-4 w-4" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        <span>生成 10 秒视频</span>
        <span className="credits-hint">≈{videoCredits} 积分</span>
      </Button>
      {disabledReason && (
        <p className={config.provider_ready ? "mt-2 t-caption text-muted-foreground" : "mt-2 t-caption text-destructive"}>
          {disabledReason}
        </p>
      )}
      {!disabledReason && (
        <p className="mt-2 flex items-center gap-sm t-caption text-muted-foreground/70">
          <Zap className="h-3 w-3 text-bronze" />
          参考图越多画面越稳定；空提示词时建议先用模板补全结构。
        </p>
      )}
    </section>
  );
}
