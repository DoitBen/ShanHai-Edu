"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, History, Images, Loader2, RefreshCw, Wand2 } from "lucide-react";
import { useAppStore } from "@/lib/store";
import type { VideoWorkflowConfig, VideoWorkflowRun } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VideoAssetPanel } from "./VideoAssetPanel";
import { VideoComposerPanel } from "./VideoComposerPanel";
import { VideoRunHistoryPanel } from "./VideoRunHistoryPanel";
import { useVideoWorkflowPolling } from "./use-video-workflow-polling";
import { isActiveVideoRun, addReference, reusableReferenceIds } from "./video-workflow-utils";
import { VIDEO_WORKFLOW_SYNC_CHANNEL, VIDEO_WORKFLOW_TAB_ID } from "@/lib/video-workflow-cross-tab";
import { videoWorkflowErrorToast } from "@/lib/video-workflow-errors";

const VIDEO_WORKFLOW_DRAFT_PREFIX = "video-workflow-draft";

/* ETA 估算：基于模型默认总时长 + 进度反推剩余秒数
 * - queued / submitting: 视为「等待启动」，估算为总时长
 * - processing: 用 (100 - progress) / 100 * 总时长，再叠加网络抖动 +2s
 * - 其他状态：返回 null（不展示）
 */
function estimateEta(run: VideoWorkflowRun, config: VideoWorkflowConfig | undefined): number | null {
  if (!config) return null;
  const totalSeconds = Math.max(5, config.duration_sec * 6); // 经验值：10s 视频约 60s 生成
  if (run.status === "queued" || run.status === "submission_unknown") return totalSeconds;
  if (run.status === "processing") {
    const remaining = Math.max(2, Math.ceil(((100 - run.progress) / 100) * totalSeconds) + 2);
    return remaining;
  }
  return null;
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m} 分 ${s} 秒` : `${m} 分`;
}

export function VideoWorkflowWorkbench({ projectId }: { projectId: string }) {
  return <VideoWorkflowWorkbenchInner key={projectId} projectId={projectId} />;
}

function readDraft(projectId: string): { prompt: string; selectedIds: string[] } {
  if (typeof window === "undefined") return { prompt: "", selectedIds: [] };
  const draft = window.localStorage.getItem(`${VIDEO_WORKFLOW_DRAFT_PREFIX}:${projectId}`);
  if (!draft) return { prompt: "", selectedIds: [] };
  try {
    const parsed = JSON.parse(draft) as { prompt?: string; selectedIds?: string[] };
    return {
      prompt: typeof parsed.prompt === "string" ? parsed.prompt : "",
      selectedIds: Array.isArray(parsed.selectedIds) ? parsed.selectedIds.filter((item) => typeof item === "string") : [],
    };
  } catch {
    window.localStorage.removeItem(`${VIDEO_WORKFLOW_DRAFT_PREFIX}:${projectId}`);
    return { prompt: "", selectedIds: [] };
  }
}

function VideoWorkflowWorkbenchInner({ projectId }: { projectId: string }) {
  const workflow = useAppStore((s) => s.videoWorkflowByProject[projectId]);
  const status = useAppStore((s) => s.videoWorkflowStatusByProject[projectId] || "idle");
  const error = useAppStore((s) => s.videoWorkflowErrorByProject[projectId]);
  const loadVideoWorkflow = useAppStore((s) => s.loadVideoWorkflow);
  const uploadVideoWorkflowReferences = useAppStore((s) => s.uploadVideoWorkflowReferences);
  const createVideoWorkflowRun = useAppStore((s) => s.createVideoWorkflowRun);
  const syncVideoWorkflowRun = useAppStore((s) => s.syncVideoWorkflowRun);
  const removeVideoWorkflowAsset = useAppStore((s) => s.removeVideoWorkflowAsset);
  const retryVideoWorkflowRun = useAppStore((s) => s.retryVideoWorkflowRun);
  const [prompt, setPrompt] = useState(() => readDraft(projectId).prompt);
  const [selectedIds, setSelectedIds] = useState<string[]>(() => readDraft(projectId).selectedIds);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submitInFlightRef = useRef(false);
  const [busyRunId, setBusyRunId] = useState<string | null>(null);

  useEffect(() => {
    window.localStorage.setItem(
      `${VIDEO_WORKFLOW_DRAFT_PREFIX}:${projectId}`,
      JSON.stringify({ prompt, selectedIds }),
    );
  }, [projectId, prompt, selectedIds]);

  useEffect(() => {
    if (status === "idle" || status === "error") void loadVideoWorkflow(projectId);
  }, [loadVideoWorkflow, projectId, status]);

  useEffect(() => {
    function syncFromMessage(raw: unknown) {
      if (typeof raw !== "string") return;
      try {
        const message = JSON.parse(raw) as { type?: string; projectId?: string; source?: string };
        if (
          message.type === VIDEO_WORKFLOW_SYNC_CHANNEL &&
          message.projectId === projectId &&
          message.source !== VIDEO_WORKFLOW_TAB_ID
        ) {
          void loadVideoWorkflow(projectId);
        }
      } catch {
        // Ignore unrelated localStorage or BroadcastChannel payloads.
      }
    }

    const storageHandler = (event: StorageEvent) => {
      if (event.key === VIDEO_WORKFLOW_SYNC_CHANNEL) syncFromMessage(event.newValue);
    };
    let channel: BroadcastChannel | null = null;
    if (typeof BroadcastChannel !== "undefined") {
      channel = new BroadcastChannel(VIDEO_WORKFLOW_SYNC_CHANNEL);
      channel.onmessage = (event) => syncFromMessage(event.data);
    }
    window.addEventListener("storage", storageHandler);
    return () => {
      window.removeEventListener("storage", storageHandler);
      channel?.close();
    };
  }, [loadVideoWorkflow, projectId]);

  const { pollingState, requestSync } = useVideoWorkflowPolling({
    projectId,
    runs: workflow?.runs || [],
    intervalMs: workflow?.config.poll_interval_ms || 4000,
    syncRun: async (id, runId) => {
      const result = await syncVideoWorkflowRun(id, runId);
      if (!result.ok) {
        throw result.error || new Error(result.msg || "视频任务同步失败");
      }
    },
  });

  const hasActiveRuns = (workflow?.runs || []).some(isActiveVideoRun);

  useEffect(() => {
    if (!hasActiveRuns) submitInFlightRef.current = false;
  }, [hasActiveRuns]);

  async function submit(): Promise<boolean> {
    if (!workflow || submitting || hasActiveRuns || submitInFlightRef.current) return false;
    const normalized = prompt.trim();
    if (!normalized || normalized.length > 5000) return false;
    const confirmed = window.confirm(
      [
        "确认生成 10 秒视频？",
        `模型：${workflow.config.model}`,
        `尺寸：${workflow.config.size}`,
        `时长：${workflow.config.duration_sec} 秒`,
        `参考图数量：${selectedIds.length}`,
        `频率限制：${Math.floor(workflow.config.run_create_window_seconds / 60)} 分钟内每个项目最多 ${workflow.config.run_create_project_window_limit} 次`,
      ].join("\n"),
    );
    if (!confirmed) return false;
    submitInFlightRef.current = true;
    setSubmitting(true);
    let keepLockedForActiveRun = false;
    try {
      const result = await createVideoWorkflowRun(projectId, {
        client_request_id: crypto.randomUUID(),
        prompt: normalized,
        reference_asset_ids: selectedIds,
      });
      if (!result.ok || !result.run) {
        const payload = videoWorkflowErrorToast(result.error || new Error(result.msg || "视频任务创建失败"), "视频任务创建失败");
        toast.error(payload.title, { description: payload.description });
        return false;
      }
      keepLockedForActiveRun = isActiveVideoRun(result.run);
      setSelectedRunId(result.run.run_id);
      return keepLockedForActiveRun;
    } finally {
      if (!keepLockedForActiveRun) submitInFlightRef.current = false;
      setSubmitting(false);
    }
  }

  function reuse(run: VideoWorkflowRun) {
    const active = new Set((workflow?.assets || []).map((asset) => asset.asset_id));
    const reusable = reusableReferenceIds(run.reference_asset_ids, active);
    setPrompt(run.prompt);
    setSelectedIds(reusable);
    if (reusable.length !== run.reference_asset_ids.length) {
      toast.warning("部分历史参考图已移除，请重新上传或替换");
    }
  }

  const selectedRun =
    workflow?.runs.find((run) => run.run_id === selectedRunId) || workflow?.runs[0] || null;

  async function upload(files: File[]) {
    const result = await uploadVideoWorkflowReferences(projectId, files);
    if (!result.ok) {
      const payload = videoWorkflowErrorToast(result.error || new Error(result.msg || "参考图上传失败"), "参考图上传失败");
      toast.error(payload.title, { description: payload.description });
      return result;
    }
    for (const uploadError of result.errors || []) {
      toast.error(`${uploadError.filename}：${uploadError.message}`);
    }
    return result;
  }

  function toggleAsset(assetId: string) {
    setSelectedIds((current) =>
      current.includes(assetId)
        ? current.filter((id) => id !== assetId)
        : addReference(current, assetId, workflow?.config.max_reference_images || 7),
    );
  }

  async function deleteAsset(assetId: string) {
    const result = await removeVideoWorkflowAsset(projectId, assetId);
    if (!result.ok) {
      const payload = videoWorkflowErrorToast(result.error || new Error(result.msg || "参考图移除失败"), "参考图移除失败");
      toast.error(payload.title, { description: payload.description });
      return;
    }
    setSelectedIds((current) => current.filter((id) => id !== assetId));
  }

  async function retry(runId: string) {
    const original = workflow?.runs.find((run) => run.run_id === runId);
    let confirmPossibleDuplicate = false;
    if (original?.status === "submission_unknown") {
      confirmPossibleDuplicate = window.confirm(
        "上次提交结果未知，可能已经产生费用。确认后会重新提交一个新的视频生成任务。",
      );
      if (!confirmPossibleDuplicate) return;
    }
    setBusyRunId(runId);
    const result =
      original?.status === "completed" && original.download_status === "download_failed"
        ? await syncVideoWorkflowRun(projectId, runId)
        : await retryVideoWorkflowRun(projectId, runId, { confirmPossibleDuplicate });
    setBusyRunId(null);
    if (!result.ok || !result.run) {
      const payload = videoWorkflowErrorToast(result.error || new Error(result.msg || "视频任务重试失败"), "视频任务重试失败");
      toast.error(payload.title, { description: payload.description });
      return;
    }
    setSelectedRunId(result.run.run_id);
  }

  if (status === "loading" && !workflow) {
    return (
      <Card className="flex min-h-[320px] items-center justify-center gap-2 p-6 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        正在加载视频工作台
      </Card>
    );
  }

  if (status === "error" && !workflow) {
    return (
      <Card className="border-destructive/30 bg-destructive/5 p-6 text-destructive">
        {error || "视频工作台加载失败"}
      </Card>
    );
  }

  if (!workflow) return null;
  const showPollingNotice = hasActiveRuns && (pollingState.state === "backoff" || pollingState.state === "paused");
  const retrySeconds = Math.max(1, Math.ceil((pollingState.nextRetryInMs || 0) / 1000));

  // 顶部活动任务状态条：取最早一个 active run（实际只允许一个）
  const activeRun = (workflow.runs || []).find(isActiveVideoRun) || null;
  const activeEta = activeRun ? estimateEta(activeRun, workflow.config) : null;

  const assetPanel = (
    <VideoAssetPanel
      projectId={projectId}
      assets={workflow.assets}
      selectedIds={selectedIds}
      maxSelected={workflow.config.max_reference_images}
      maxAssetBytes={workflow.config.max_asset_bytes}
      busy={status === "loading"}
      onUpload={upload}
      onToggle={toggleAsset}
      onReorder={setSelectedIds}
      onDelete={deleteAsset}
    />
  );
  const composerPanel = (
    <VideoComposerPanel
      projectId={projectId}
      config={workflow.config}
      prompt={prompt}
      selectedCount={selectedIds.length}
      selectedRun={selectedRun}
      submitting={submitting}
      hasActiveRun={hasActiveRuns}
      onPromptChange={setPrompt}
      onSubmit={submit}
    />
  );
  const historyPanel = (
    <VideoRunHistoryPanel
      projectId={projectId}
      runs={workflow.runs}
      selectedRunId={selectedRun?.run_id || null}
      busyRunId={busyRunId}
      onSelect={setSelectedRunId}
      onRetry={retry}
      onReuse={reuse}
    />
  );

  return (
    <>
      {/* 顶部活动任务状态条：非阻塞，带进度+ETA+pulse 动画 */}
      {activeRun && (
        <Card className="mb-4 border-primary/30 bg-gradient-to-r from-primary/[0.06] to-bronze/[0.04] p-4 shadow-apple-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary anim-pulse-soft" />
              </span>
              <div className="min-w-0">
                <div className="t-body font-semibold text-foreground">
                  视频生成中
                  <span className="ml-2 t-caption font-normal text-muted-foreground">
                    {activeRun.status === "queued" ? "排队等待" : `${activeRun.progress}%`}
                  </span>
                </div>
                <div className="mt-1 t-caption text-muted-foreground">
                  模型 {activeRun.model} · 尺寸 {activeRun.size}
                  {activeEta !== null && (
                    <span className="ml-2 inline-flex items-center gap-1 text-bronze">
                      · 预计剩余 {formatEta(activeEta)}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="progress-pro w-40 sm:w-56">
                <div
                  className="progress-pro-bar anim-pulse-soft"
                  style={{ width: `${Math.max(5, activeRun.progress)}%` }}
                />
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="btn-cta-secondary h-8 gap-1.5"
                onClick={requestSync}
              >
                <RefreshCw className="h-3.5 w-3.5" />
                立即同步
              </Button>
            </div>
          </div>
        </Card>
      )}

      {showPollingNotice && (
        <Card className="mb-4 flex flex-col gap-3 border-amber-300 bg-amber-50 p-4 text-amber-950 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="t-caption font-medium">
                {pollingState.state === "paused" ? "视频任务轮询已暂停" : "视频任务同步暂时失败"}
              </div>
              <div className="mt-1 t-caption">
                {pollingState.state === "paused"
                  ? "页面隐藏或网络离线时会暂停同步，恢复后可立即重试。"
                  : `系统会自动退避重试，下次重试约 ${retrySeconds} 秒后。`}
              </div>
            </div>
          </div>
          <Button type="button" size="sm" variant="outline" className="gap-1.5 self-start" onClick={requestSync}>
            <RefreshCw className="h-4 w-4" />
            立即重试
          </Button>
        </Card>
      )}

      {/* 三栏布局：xl 三栏、lg 三栏（更窄）、md 及以下 Tabs */}
      <div className="hidden min-h-[640px] gap-4 lg:grid lg:grid-cols-[240px_minmax(0,1fr)_320px] xl:grid-cols-[280px_minmax(0,1fr)_360px]">
        {assetPanel}
        {composerPanel}
        {historyPanel}
      </div>
      <Tabs defaultValue="create" className="lg:hidden">
        <TabsList className="grid h-auto w-full grid-cols-3 rounded-lg">
          <TabsTrigger value="assets" className="gap-1.5 h-11">
            <Images className="h-4 w-4" />素材
          </TabsTrigger>
          <TabsTrigger value="create" className="gap-1.5 h-11">
            <Wand2 className="h-4 w-4" />创作
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-1.5 h-11">
            <History className="h-4 w-4" />历史
          </TabsTrigger>
        </TabsList>
        <TabsContent value="assets" className="mt-4">{assetPanel}</TabsContent>
        <TabsContent value="create" className="mt-4">{composerPanel}</TabsContent>
        <TabsContent value="history" className="mt-4">{historyPanel}</TabsContent>
      </Tabs>
    </>
  );
}
