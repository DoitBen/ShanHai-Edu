"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import {
  STAGE_DEFS,
  stageDefByKey,
  nextStageKey,
  BRANCH_LABEL,
  makeEmptyStages,
} from "@/lib/workflow";
import { MOCK_VIDEO_PLANS } from "@/lib/mock-data";
import type {
  ProjectMeta,
  VideoIntroPlan,
  VideoIntroType,
  WorkflowStage,
} from "@/lib/types";
import { StatusBadge, ProjectStatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, LoadingState } from "@/components/common/StateViews";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Clock,
  FileText,
  Save,
  RefreshCw,
  Check,
  RotateCcw,
  Star,
  Info,
  AlertCircle,
  Play,
  GitCompare,
  X,
  Download,
  Eye,
  FileJson,
  FileImage,
  FileType2,
  Maximize2,
} from "lucide-react";

/* ---------------- 常量 ---------------- */

const VIDEO_TYPE_LABEL: Record<VideoIntroType, string> = {
  science: "科普类",
  application: "应用类",
  story: "故事类",
  suspense: "悬念类",
  discovery: "奇妙发现",
  all: "全部类型",
};

const LOG_LEVEL_META = {
  info: { Icon: Info, color: "text-muted-foreground" },
  warn: { Icon: AlertTriangle, color: "text-warning" },
  error: { Icon: AlertCircle, color: "text-destructive" },
  success: { Icon: CheckCircle2, color: "text-success" },
} as const;

type TabKey = "input" | "run" | "result" | "evidence" | "logs";

/* ============================================================
 * 主组件 —— 项目工作区指挥台
 * ============================================================ */

export function ProjectWorkspaceScreen() {
  const activeProjectId = useAppStore((s) => s.activeProjectId);
  const projects = useAppStore((s) => s.projects);
  const go = useAppStore((s) => s.go);

  const project = projects.find((p) => p.id === activeProjectId);

  if (!project) {
    return <EmptyWorkspace onBack={() => go("dashboard")} />;
  }

  // key={project.id}：切换项目时整个内层组件重挂载，状态自然重置，避免 effect 同步
  return <ProjectWorkspace key={project.id} project={project} />;
}

function EmptyWorkspace({ onBack }: { onBack: () => void }) {
  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <Card className="border-dashed bg-card p-0">
        <EmptyState
          title="未选择项目"
          desc="请先从工作台首页选择一个项目进入工作区。"
          icon={<AlertTriangle className="h-5 w-5" />}
        />
        <div className="flex justify-center pb-8">
          <Button className="gap-2" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            返回首页
          </Button>
        </div>
      </Card>
    </div>
  );
}

function ProjectWorkspace({ project }: { project: ProjectMeta }) {
  const stagesByProject = useAppStore((s) => s.stagesByProject);
  const videoPlansByProject = useAppStore((s) => s.videoPlansByProject);
  const go = useAppStore((s) => s.go);
  const approveStage = useAppStore((s) => s.approveStage);
  const rejectStage = useAppStore((s) => s.rejectStage);
  const runStage = useAppStore((s) => s.runStage);
  const saveStageInput = useAppStore((s) => s.saveStageInput);
  const acceptVideoPlan = useAppStore((s) => s.acceptVideoPlan);

  // 订阅最新 project 元信息（progress / currentStage / status 等会随操作更新）
  const liveProject =
    useAppStore((s) => s.projects.find((p) => p.id === project.id)) || project;

  const stages = stagesByProject[project.id] || makeEmptyStages();

  const [selectedKey, setSelectedKey] = useState<string>(project.currentStage);
  const [tab, setTab] = useState<TabKey>("input");
  const [inputDraft, setInputDraft] = useState<string>(
    () => stages.find((s) => s.key === project.currentStage)?.input || "",
  );
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState<string | null>(null);

  const selectedStage =
    stages.find((s) => s.key === selectedKey) || stages[0];

  // 按 order 排序的阶段 key 列表（用于键盘 ←/→ 切换）
  const orderedStageKeys = stages
    .slice()
    .sort((a, b) => a.order - b.order)
    .map((s) => s.key);
  const currentIndex = Math.max(
    0,
    orderedStageKeys.indexOf(selectedStage.key),
  );

  /* ---------- handlers ---------- */
  function goToStageByOffset(offset: number) {
    const next = orderedStageKeys[currentIndex + offset];
    if (next) syncToStage(next);
  }
  function syncToStage(key: string) {
    const newStage = stages.find((s) => s.key === key);
    setSelectedKey(key);
    setTab("input");
    setInputDraft(newStage?.input || "");
  }

  function handleSelectStage(key: string) {
    syncToStage(key);
  }

  function handleSave(text?: string) {
    const value = typeof text === "string" ? text : inputDraft;
    saveStageInput(project.id, selectedStage.key, value);
    setInputDraft(value);
    toast.success("已保存");
  }

  function handleRegenerate() {
    runStage(project.id, selectedStage.key);
    setTab("run");
    toast.info("正在生成…");
  }

  function handleApproveAndNext() {
    approveStage(project.id, selectedStage.key);
    toast.success("已确认，进入下一阶段");
    const next = nextStageKey(selectedStage.key);
    if (next) syncToStage(next);
  }

  function handleReject() {
    rejectStage(project.id, selectedStage.key);
    setTab("input");
    toast.success("已退回修改");
  }

  function handleNextStep() {
    if (selectedStage.status !== "approved") {
      approveStage(project.id, selectedStage.key);
    }
    const next = nextStageKey(selectedStage.key);
    if (next) {
      syncToStage(next);
      toast.success("已进入下一步");
    } else {
      toast.success("已是最后阶段");
    }
  }

  function handleAcceptVideoPlan(planId: string) {
    acceptVideoPlan(project.id, planId);
    toast.success("已采纳该方案");
  }

  // 键盘快捷键：←/→ 切换节点，1-5 切换 Tab
  useEffect(() => {
    const isTyping = (target: EventTarget | null): boolean => {
      const el = target as HTMLElement | null;
      if (!el) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
    };
    const handler = (e: KeyboardEvent) => {
      // 对比/预览 Dialog 打开时不触发
      if (compareOpen || previewFile) return;
      if (isTyping(e.target)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToStageByOffset(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToStageByOffset(1);
      } else if (["1", "2", "3", "4", "5"].includes(e.key)) {
        const tabMap: TabKey[] = ["input", "run", "result", "evidence", "logs"];
        const idx = parseInt(e.key, 10) - 1;
        if (idx >= 0 && idx < tabMap.length) {
          e.preventDefault();
          setTab(tabMap[idx]);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentIndex, orderedStageKeys, compareOpen, previewFile]);

  /* ---------- 按钮启用规则 ---------- */
  const status = selectedStage?.status;
  const isRunning = status === "running";
  const canSave = !!status && status !== "running";
  const canRegenerate = !!status && status !== "running";
  const canApprove =
    !!status &&
    ["ready", "pending_confirm", "approved"].includes(status) &&
    !isRunning;
  const canReject =
    !!status && status !== "not_started" && status !== "running";
  const canNext =
    !!status &&
    !["not_started", "input_required", "running"].includes(status);

  const stageDef = stageDefByKey(selectedStage?.key || "");
  const videoPlans = videoPlansByProject[project.id] || MOCK_VIDEO_PLANS;

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* ===== 顶部 Header ===== */}
      <WorkspaceHeader project={liveProject} onBack={() => go("dashboard")} />

      {/* ===== 工作流节点轨 ===== */}
      <section className="mt-6">
        <SectionLabel
          index="01"
          title="流程节点"
          desc="14 个阶段按顺序推进，点击节点切换详情"
          right={<KeyboardHint keys={["←", "→"]} label="切换节点" />}
        />
        <Card className="border-border bg-card p-3 shadow-soft">
          <WorkflowRail
            stages={stages}
            selectedKey={selectedStage?.key || ""}
            onSelect={handleSelectStage}
          />
        </Card>
      </section>

      {/* ===== 详情区 5 Tabs + 底部操作 ===== */}
      <section className="mt-8">
        <SectionLabel
          index="02"
          title="节点详情"
          desc={
            stageDef
              ? `${stageDef.title} · ${stageDef.desc}`
              : "选择一个节点查看详情"
          }
          right={
            selectedStage ? <StatusBadge status={selectedStage.status} /> : null
          }
        />
        <Card className="border-border bg-card p-0 shadow-soft">
          {/* 节点标题条 */}
          {selectedStage && (
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-6">
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary t-body font-semibold">
                  {stageDef?.order}
                </span>
                <div className="min-w-0">
                  <div className="t-module truncate">{selectedStage.title}</div>
                  <div className="mt-0.5 t-caption text-muted-foreground line-clamp-1">
                    {BRANCH_LABEL[selectedStage.branch]}
                    {selectedStage.summary ? ` · ${selectedStage.summary}` : ""}
                  </div>
                </div>
              </div>
              {selectedStage.duration && (
                <div className="flex shrink-0 items-center gap-1.5 t-caption text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  耗时 {selectedStage.duration}
                </div>
              )}
            </div>
          )}

          <Tabs
            value={tab}
            onValueChange={(v) => setTab(v as TabKey)}
            className="gap-0"
          >
            <div className="overflow-x-auto scroll-fine px-3 py-2 sm:px-5">
              <TabsList className="bg-muted/60">
                <TabsTrigger value="input" className="gap-1.5">
                  输入
                  <kbd className="hidden sm:inline-flex h-4 w-4 items-center justify-center rounded bg-background/70 font-mono text-[9px] text-muted-foreground">1</kbd>
                </TabsTrigger>
                <TabsTrigger value="run" className="gap-1.5">
                  运行
                  <kbd className="hidden sm:inline-flex h-4 w-4 items-center justify-center rounded bg-background/70 font-mono text-[9px] text-muted-foreground">2</kbd>
                </TabsTrigger>
                <TabsTrigger value="result" className="gap-1.5">
                  结果
                  <kbd className="hidden sm:inline-flex h-4 w-4 items-center justify-center rounded bg-background/70 font-mono text-[9px] text-muted-foreground">3</kbd>
                </TabsTrigger>
                <TabsTrigger value="evidence" className="gap-1.5">
                  证据
                  <kbd className="hidden sm:inline-flex h-4 w-4 items-center justify-center rounded bg-background/70 font-mono text-[9px] text-muted-foreground">4</kbd>
                </TabsTrigger>
                <TabsTrigger value="logs" className="gap-1.5">
                  日志
                  <kbd className="hidden sm:inline-flex h-4 w-4 items-center justify-center rounded bg-background/70 font-mono text-[9px] text-muted-foreground">5</kbd>
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="px-4 pb-5 pt-4 sm:px-6">
              <TabsContent value="input" className="mt-0">
                <InputTab
                  stage={selectedStage}
                  value={inputDraft}
                  onChange={setInputDraft}
                  onSave={() => handleSave()}
                />
              </TabsContent>
              <TabsContent value="run" className="mt-0">
                <RunTab stage={selectedStage} onRegenerate={handleRegenerate} />
              </TabsContent>
              <TabsContent value="result" className="mt-0">
                {selectedStage?.key === "video-script" ? (
                  <VideoPlanGrid
                    plans={videoPlans}
                    selectedIds={compareIds}
                    onToggleSelect={(id) =>
                      setCompareIds((prev) =>
                        prev.includes(id)
                          ? prev.filter((x) => x !== id)
                          : prev.length >= 3
                            ? (toast.warning("最多对比 3 套方案"), prev)
                            : [...prev, id],
                      )
                    }
                    onAccept={handleAcceptVideoPlan}
                    onEdit={() => toast.info("演示版暂不支持编辑")}
                    onCompare={() => {
                      if (compareIds.length < 2) {
                        toast.warning("请至少选择 2 套方案进行对比");
                        return;
                      }
                      setCompareOpen(true);
                    }}
                    onRegenerate={handleRegenerate}
                  />
                ) : (
                  <ResultTab stage={selectedStage} />
                )}
              </TabsContent>
              <TabsContent value="evidence" className="mt-0">
                <EvidenceTab
                  stage={selectedStage}
                  onPreview={(file) => setPreviewFile(file)}
                />
              </TabsContent>
              <TabsContent value="logs" className="mt-0">
                <LogsTab stage={selectedStage} />
              </TabsContent>
            </div>
          </Tabs>

          {/* 底部操作（在 Card 内） */}
          <div className="border-t border-border bg-muted/20 px-4 py-3 sm:px-6">
            <StageActions
              canSave={canSave}
              canRegenerate={canRegenerate}
              canApprove={canApprove}
              canReject={canReject}
              canNext={canNext}
              isRunning={isRunning}
              onSave={() => handleSave()}
              onRegenerate={handleRegenerate}
              onApprove={handleApproveAndNext}
              onReject={handleReject}
              onNext={handleNextStep}
            />
          </div>
        </Card>
      </section>

      {/* 视频方案对比 */}
      <VideoPlanCompareDialog
        open={compareOpen}
        onOpenChange={setCompareOpen}
        plans={videoPlans.filter((p) => compareIds.includes(p.id))}
        onAccept={(id) => {
          handleAcceptVideoPlan(id);
          setCompareOpen(false);
          setCompareIds([]);
        }}
      />

      {/* 证据文件预览 */}
      <EvidencePreviewDialog
        file={previewFile}
        onClose={() => setPreviewFile(null)}
        stageTitle={selectedStage?.title}
      />

      <div className="h-2" />
    </div>
  );
}

/* ============================================================
 * 子组件
 * ============================================================ */

function SectionLabel({
  index,
  title,
  desc,
  right,
}: {
  index: string;
  title: string;
  desc?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div className="flex items-baseline gap-3">
        <span className="t-overline text-bronze">{index}</span>
        <div>
          <h2 className="t-module">{title}</h2>
          {desc && (
            <p className="mt-0.5 t-caption text-muted-foreground">{desc}</p>
          )}
        </div>
      </div>
      {right}
    </div>
  );
}

/* ---------- 顶部 Header ---------- */

function WorkspaceHeader({
  project,
  onBack,
}: {
  project: ProjectMeta;
  onBack: () => void;
}) {
  const stage = stageDefByKey(project.currentStage);
  return (
    <Card className="border-border bg-card p-0 shadow-soft">
      <div className="p-4 sm:p-6">
        {/* 顶部行：返回 + 项目名 + 状态 */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <button
              type="button"
              onClick={onBack}
              className="-mx-2 -my-1 inline-flex items-center gap-1.5 rounded-md px-2 py-1 t-caption text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-ring"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              返回项目列表
            </button>
            <h1 className="mt-2 t-title">{project.name}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 t-body text-muted-foreground">
              <span>{project.subject}</span>
              <span className="h-3 w-px bg-border" />
              <span>{project.grade}</span>
              <span className="h-3 w-px bg-border" />
              <span>
                {project.textbookVersion} {project.volume}
              </span>
              <span className="h-3 w-px bg-border" />
              <span>{project.lessonType}</span>
            </div>
          </div>
          <ProjectStatusBadge status={project.status} />
        </div>

        {/* 底部 3 列：当前阶段 / 总进度 / 下一步动作 */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div>
            <div className="t-overline text-muted-foreground/70">当前阶段</div>
            <div className="mt-1.5 t-body font-medium text-foreground">
              {stage?.title || project.currentStage}
            </div>
          </div>
          <div>
            <div className="t-overline text-muted-foreground/70">总进度</div>
            <div className="mt-1.5 flex items-baseline gap-2">
              <span className="t-module">{project.progress}%</span>
            </div>
            <Progress
              value={project.progress}
              className="mt-2 h-1.5 bg-muted"
            />
          </div>
          <div>
            <div className="t-overline text-muted-foreground/70">下一步动作</div>
            <div className="mt-1.5 t-body font-medium text-foreground">
              {project.nextAction}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

/* ---------- 工作流节点轨 ---------- */

function WorkflowRail({
  stages,
  selectedKey,
  onSelect,
}: {
  stages: WorkflowStage[];
  selectedKey: string;
  onSelect: (key: string) => void;
}) {
  return (
    <div className="overflow-x-auto scroll-fine pb-1">
      <div className="flex min-w-max items-stretch px-1 py-1">
        {STAGE_DEFS.map((def, i) => {
          const stage = stages.find((s) => s.key === def.key);
          const status = stage?.status || "not_started";
          const isSelected = def.key === selectedKey;
          const isApproved = status === "approved";
          const isRunning = status === "running";
          const isError = status === "failed" || status === "blocked";
          const isPending =
            status === "pending_confirm" ||
            status === "input_required" ||
            status === "ready";

          return (
            <div key={def.key} className="flex items-stretch">
              <button
                type="button"
                onClick={() => onSelect(def.key)}
                aria-current={isSelected ? "true" : undefined}
                className={cn(
                  "relative flex h-[88px] w-[88px] shrink-0 flex-col items-center gap-1 rounded-md border px-2 pt-2.5 pb-2 text-center transition-all focus-ring",
                  isSelected
                    ? "border-primary bg-primary/[0.04] shadow-soft"
                    : "border-transparent hover:bg-muted/60",
                )}
              >
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-[0.7rem] font-semibold",
                    isApproved && "bg-success/15 text-success",
                    isRunning && "bg-primary text-primary-foreground",
                    isError && "bg-destructive/10 text-destructive",
                    isPending && !isSelected && "bg-warning/15 text-warning",
                    isPending && isSelected && "bg-primary text-primary-foreground",
                    status === "not_started" &&
                      !isSelected &&
                      "bg-muted text-muted-foreground",
                    status === "not_started" &&
                      isSelected &&
                      "bg-primary text-primary-foreground",
                  )}
                >
                  {isApproved ? (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  ) : isRunning ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : isError ? (
                    <AlertTriangle className="h-3.5 w-3.5" />
                  ) : (
                    def.order
                  )}
                </span>
                <span
                  className={cn(
                    "t-caption leading-tight",
                    isSelected
                      ? "font-medium text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  {def.short}
                </span>
                <span
                  className={cn(
                    "t-overline text-[0.55rem] leading-none",
                    def.branch === "common" && "text-muted-foreground/60",
                    def.branch === "video" && "text-info",
                    def.branch === "ppt" && "text-bronze",
                  )}
                >
                  {BRANCH_LABEL[def.branch]}
                </span>
                {isRunning && (
                  <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                )}
              </button>
              {i < STAGE_DEFS.length - 1 && (
                <div className="flex w-3 justify-center pt-6">
                  <span
                    className={cn(
                      "h-px w-full",
                      isApproved ? "bg-success/50" : "bg-border",
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- Tab: 输入 ---------- */

function InputTab({
  stage,
  value,
  onChange,
  onSave,
}: {
  stage?: WorkflowStage;
  value: string;
  onChange: (v: string) => void;
  onSave: () => void;
}) {
  if (!stage) return null;
  const needsInput =
    stage.status === "not_started" || stage.status === "input_required";
  return (
    <div className="space-y-3">
      {needsInput && (
        <div className="flex items-start gap-2 rounded-md border border-warning/25 bg-warning/5 px-3 py-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <p className="t-body text-warning">
            请填写该阶段的输入内容后保存，再触发运行。
          </p>
        </div>
      )}
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="输入该阶段需要的素材、要求或参数…"
        className="min-h-40 bg-card"
      />
      <div className="flex justify-end">
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={onSave}
          disabled={stage.status === "running"}
        >
          <Save className="h-4 w-4" />
          保存输入
        </Button>
      </div>
    </div>
  );
}

/* ---------- Tab: 运行 ---------- */

function RunTab({
  stage,
  onRegenerate,
}: {
  stage?: WorkflowStage;
  onRegenerate: () => void;
}) {
  if (!stage) return null;
  if (stage.status === "running") {
    return <LoadingState label="运行中，请稍候…" />;
  }
  const statusText: Record<WorkflowStage["status"], string> = {
    not_started: "尚未运行",
    input_required: "等待输入",
    ready: "可运行",
    running: "运行中",
    pending_confirm: "运行完成，待确认",
    approved: "已通过",
    blocked: "已阻塞",
    failed: "运行失败",
  };
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={stage.status} />
        <span className="t-body text-muted-foreground">
          {statusText[stage.status]}
        </span>
        {stage.duration && (
          <span className="ml-auto flex items-center gap-1.5 t-caption text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            上次耗时 {stage.duration}
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" className="gap-1.5" onClick={onRegenerate}>
          <Play className="h-4 w-4" />
          {stage.status === "not_started" ? "开始运行" : "重新生成"}
        </Button>
      </div>
    </div>
  );
}

/* ---------- Tab: 结果 ---------- */

function ResultTab({ stage }: { stage?: WorkflowStage }) {
  if (!stage) return null;
  if (!stage.result) {
    return (
      <EmptyState
        title="暂无结果"
        desc="运行完成后将在此显示该阶段的产出。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="space-y-3">
      <div className="t-overline text-muted-foreground/70">阶段产出</div>
      <div className="whitespace-pre-wrap rounded-md border border-border bg-muted/30 p-4 t-body text-foreground/90">
        {stage.result}
      </div>
    </div>
  );
}

/* ---------- Tab: 证据 ---------- */

function EvidenceTab({
  stage,
  onPreview,
}: {
  stage?: WorkflowStage;
  onPreview?: (file: string) => void;
}) {
  if (!stage) return null;
  if (!stage.evidence || stage.evidence.length === 0) {
    return (
      <EmptyState
        title="暂无证据文件"
        desc="该阶段尚无产出的文件或资产。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="t-caption text-muted-foreground">
          共 {stage.evidence.length} 个文件，点击文件名可预览内容。
        </p>
      </div>
      <ul className="space-y-1.5">
        {stage.evidence.map((file, i) => {
          const meta = getFileMeta(file);
          const Icon = meta.Icon;
          return (
            <li key={i}>
              <button
                type="button"
                onClick={() => onPreview?.(file)}
                className="group flex w-full items-center gap-2.5 rounded-md border border-border bg-card px-3 py-2.5 text-left transition-colors hover:border-primary/30 hover:bg-muted/50 focus-ring"
              >
                <span className={cn("shrink-0", meta.tone)}>
                  <Icon className="h-4 w-4" />
                </span>
                <span className="t-body min-w-0 flex-1 truncate text-foreground">
                  {file}
                </span>
                <span className="t-caption shrink-0 text-muted-foreground group-hover:text-foreground">
                  {meta.label}
                </span>
                <Maximize2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50 transition-colors group-hover:text-primary" />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ---------- Tab: 日志 ---------- */

function LogsTab({ stage }: { stage?: WorkflowStage }) {
  if (!stage) return null;
  if (!stage.logs || stage.logs.length === 0) {
    return (
      <EmptyState
        title="暂无日志"
        desc="该阶段运行后日志将在此显示。"
        icon={<Info className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="max-h-96 overflow-y-auto scroll-fine rounded-md border border-border bg-muted/20">
      <ul className="divide-y divide-border">
        {stage.logs.map((log) => {
          const meta = LOG_LEVEL_META[log.level];
          const Icon = meta.Icon;
          return (
            <li key={log.id} className="flex items-start gap-2.5 px-3 py-2.5">
              <Icon
                className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", meta.color)}
              />
              <span className="w-20 shrink-0 font-mono t-caption text-muted-foreground">
                {log.time}
              </span>
              <span className="flex-1 t-body text-foreground/90">
                {log.message}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ---------- 视频方案卡片网格 ---------- */

function VideoPlanGrid({
  plans,
  selectedIds,
  onToggleSelect,
  onAccept,
  onEdit,
  onCompare,
  onRegenerate,
}: {
  plans: VideoIntroPlan[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onAccept: (planId: string) => void;
  onEdit: () => void;
  onCompare: () => void;
  onRegenerate: () => void;
}) {
  const selectedCount = selectedIds.length;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="t-overline text-muted-foreground/70">
            视频剧本方案
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            共 {plans.length} 套方案，按推荐分数排序。勾选 2-3 套可对比，采纳后可继续推进。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={selectedCount >= 2 ? "default" : "outline"}
            className="gap-1.5"
            onClick={onCompare}
            disabled={selectedCount < 2}
          >
            <GitCompare className="h-4 w-4" />
            对比{selectedCount > 0 ? ` (${selectedCount})` : ""}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={onRegenerate}
          >
            <RefreshCw className="h-4 w-4" />
            重新生成方案
          </Button>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {plans.map((plan) => (
          <VideoPlanCard
            key={plan.id}
            plan={plan}
            selected={selectedIds.includes(plan.id)}
            onToggleSelect={() => onToggleSelect(plan.id)}
            onAccept={onAccept}
            onEdit={onEdit}
          />
        ))}
      </div>
    </div>
  );
}

/* ---------- 视频方案卡片 ---------- */

function VideoPlanCard({
  plan,
  selected,
  onToggleSelect,
  onAccept,
  onEdit,
}: {
  plan: VideoIntroPlan;
  selected: boolean;
  onToggleSelect: () => void;
  onAccept: (planId: string) => void;
  onEdit: () => void;
}) {
  const isRecommended = plan.rank === 1;
  return (
    <Card
      className={cn(
        "relative border bg-card p-0 shadow-soft transition-all",
        plan.accepted
          ? "border-primary/40 bg-primary/[0.02] ring-1 ring-primary/20"
          : selected
            ? "border-primary/50 ring-1 ring-primary/20"
            : isRecommended
              ? "border-bronze/30"
              : "border-border",
      )}
    >
      {/* 推荐角标 */}
      {isRecommended && (
        <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-bronze/15 px-2 py-0.5 t-caption font-medium text-bronze">
          <Star className="h-3 w-3" />
          推荐
        </span>
      )}
      <div className="p-4 sm:p-5">
        {/* 选择条 */}
        <div className="flex items-center gap-2.5 border-b border-border pb-3">
          <Checkbox
            id={`sel-${plan.id}`}
            checked={selected}
            onCheckedChange={onToggleSelect}
            className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
          />
          <label
            htmlFor={`sel-${plan.id}`}
            className="t-caption cursor-pointer select-none text-muted-foreground"
          >
            加入对比
          </label>
        </div>
        {/* header row */}
        <div className="flex flex-wrap items-center gap-2 pr-16">
          <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 t-caption font-medium text-muted-foreground">
            #{plan.rank} 排序
          </span>
          <span className="inline-flex items-center rounded-md bg-success/10 px-2 py-0.5 t-caption font-medium text-success">
            {plan.score} 分
          </span>
          <span className="inline-flex items-center rounded-md bg-info/10 px-2 py-0.5 t-caption font-medium text-info">
            {VIDEO_TYPE_LABEL[plan.type]}
          </span>
          {plan.accepted && (
            <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 t-caption font-medium text-primary">
              <Check className="h-3 w-3" />
              已采纳
            </span>
          )}
        </div>

        {/* title */}
        <h4 className="mt-3 t-module">{plan.title}</h4>

        <Separator className="my-4" />

        {/* term rows */}
        <dl className="space-y-2.5">
          <TermRow label="吸睛点" value={plan.hook} />
          <TermRow label="课程锚点" value={plan.courseAnchor} />
          <TermRow
            label="课堂落点问题"
            value={plan.classroomLandingQuestion}
          />
          <TermRow
            label="不提前讲解的内容"
            value={plan.avoidTeaching}
          />
          <TermRow label="接入教案的位置" value={plan.lessonEntryPoint} />
        </dl>

        <Separator className="my-4" />

        {/* reason */}
        <div className="flex gap-3">
          <span className="w-32 shrink-0 pt-0.5 t-caption text-muted-foreground">
            推荐理由
          </span>
          <p className="flex-1 t-body text-foreground/90">{plan.reason}</p>
        </div>

        {/* actions */}
        <div className="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
          <Button
            size="sm"
            className="gap-1.5"
            onClick={() => onAccept(plan.id)}
            disabled={plan.accepted}
          >
            <Check className="h-4 w-4" />
            {plan.accepted ? "已采纳" : "采纳"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={onEdit}
          >
            编辑
          </Button>
        </div>
      </div>
    </Card>
  );
}

/* ---------- 视频方案对比 Dialog ---------- */

const COMPARE_FIELDS: {
  key: keyof Pick<
    VideoIntroPlan,
    | "type"
    | "score"
    | "hook"
    | "courseAnchor"
    | "classroomLandingQuestion"
    | "avoidTeaching"
    | "lessonEntryPoint"
    | "reason"
  >;
  label: string;
}[] = [
  { key: "type", label: "视频类型" },
  { key: "score", label: "推荐分数" },
  { key: "hook", label: "吸睛点" },
  { key: "courseAnchor", label: "课程锚点" },
  { key: "classroomLandingQuestion", label: "课堂落点问题" },
  { key: "avoidTeaching", label: "不提前讲解" },
  { key: "lessonEntryPoint", label: "接入教案位置" },
  { key: "reason", label: "推荐理由" },
];

function VideoPlanCompareDialog({
  open,
  onOpenChange,
  plans,
  onAccept,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  plans: VideoIntroPlan[];
  onAccept: (id: string) => void;
}) {
  const bestScore = Math.max(...plans.map((p) => p.score), 0);

  // 计算差异高亮：某方案在某字段的值是否唯一（其他方案都没有相同值）
  // 仅对文本类字段生效
  const TEXT_FIELDS: (typeof COMPARE_FIELDS)[number]["key"][] = [
    "hook",
    "courseAnchor",
    "classroomLandingQuestion",
    "avoidTeaching",
    "lessonEntryPoint",
    "reason",
  ];
  const isUnique = (fieldKey: string, planId: string): boolean => {
    if (!TEXT_FIELDS.includes(fieldKey as never)) return false;
    const target = plans.find((p) => p.id === planId);
    if (!target) return false;
    const val = target[fieldKey as keyof VideoIntroPlan];
    if (typeof val !== "string") return false;
    const sameCount = plans.filter(
      (p) => p[fieldKey as keyof VideoIntroPlan] === val,
    ).length;
    return sameCount === 1;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[1100px] gap-0 p-0 shadow-lift" aria-describedby={undefined}>
        <DialogTitle className="sr-only">视频方案对比</DialogTitle>
        <DialogDescription className="sr-only">
          并排对比已选中的视频方案字段，便于择优采纳。
        </DialogDescription>
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary">
              <GitCompare className="h-4 w-4" />
            </span>
            <div>
              <div className="t-module">视频方案对比</div>
              <div className="t-caption text-muted-foreground">
                共 {plans.length} 套方案，按字段并排展示
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => onOpenChange(false)}
            aria-label="关闭"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <ScrollArea className="max-h-[70vh]">
          <div className="overflow-x-auto scroll-fine">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="sticky left-0 z-10 w-28 bg-muted/30 px-4 py-3 text-left align-top t-caption font-medium text-muted-foreground">
                    对比项
                  </th>
                  {plans.map((p) => (
                    <th
                      key={p.id}
                      className="min-w-[220px] border-l border-border px-4 py-3 text-left align-top"
                    >
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 t-caption font-medium text-muted-foreground">
                          #{p.rank}
                        </span>
                        {p.rank === 1 && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-bronze/15 px-1.5 py-0.5 t-caption font-medium text-bronze">
                            <Star className="h-3 w-3" /> 推荐
                          </span>
                        )}
                      </div>
                      <div className="mt-1.5 t-body font-medium text-foreground">
                        {p.title}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPARE_FIELDS.map((field, idx) => (
                  <tr
                    key={field.key}
                    className={cn(
                      "border-b border-border",
                      idx % 2 === 1 && "bg-muted/20",
                    )}
                  >
                    <td className="sticky left-0 z-10 bg-inherit px-4 py-3 align-top t-caption font-medium text-muted-foreground">
                      {field.label}
                    </td>
                    {plans.map((p) => {
                      const val = p[field.key];
                      const isBest =
                        field.key === "score" && val === bestScore;
                      const unique = isUnique(field.key, p.id);
                      return (
                        <td
                          key={p.id}
                          className={cn(
                            "relative border-l border-border px-4 py-3 align-top t-body text-foreground/90",
                            unique && "border-l-2 border-l-bronze/60 bg-bronze/[0.04]",
                          )}
                        >
                          {field.key === "type" ? (
                            <span className="inline-flex items-center rounded-md bg-info/10 px-1.5 py-0.5 t-caption font-medium text-info">
                              {VIDEO_TYPE_LABEL[val as VideoIntroType]}
                            </span>
                          ) : field.key === "score" ? (
                            <span
                              className={cn(
                                "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 t-caption font-medium",
                                isBest
                                  ? "bg-success/15 text-success"
                                  : "bg-muted text-muted-foreground",
                              )}
                            >
                              {isBest && <Star className="h-3 w-3" />}
                              {val} 分
                            </span>
                          ) : (
                            <span className="whitespace-pre-wrap">
                              {val}
                              {unique && (
                                <span className="ml-1.5 inline-flex items-center rounded bg-bronze/15 px-1 py-0.5 align-middle t-caption font-medium text-bronze">
                                  独特
                                </span>
                              )}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/30">
                  <td className="sticky left-0 z-10 bg-muted/30 px-4 py-3" />
                  {plans.map((p) => (
                    <td
                      key={p.id}
                      className="border-l border-border px-4 py-3"
                    >
                      <Button
                        size="sm"
                        className="gap-1.5"
                        disabled={p.accepted}
                        onClick={() => onAccept(p.id)}
                      >
                        <Check className="h-4 w-4" />
                        {p.accepted ? "已采纳" : "采纳此方案"}
                      </Button>
                    </td>
                  ))}
                </tr>
              </tfoot>
            </table>
          </div>
        </ScrollArea>
        {/* 图例 */}
        <div className="flex flex-wrap items-center gap-4 border-t border-border bg-muted/20 px-5 py-2.5">
          <span className="t-caption text-muted-foreground">图例：</span>
          <span className="inline-flex items-center gap-1.5 t-caption text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded bg-bronze/15 px-1 py-0.5 text-bronze">
              独特
            </span>
            该方案独有内容
          </span>
          <span className="inline-flex items-center gap-1.5 t-caption text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded bg-success/15 px-1 py-0.5 text-success">
              <Star className="h-2.5 w-2.5" />
              最高分
            </span>
            推荐分数最高
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ---------- 证据文件预览 Dialog ---------- */

function getFileMeta(file: string): {
  Icon: React.ComponentType<{ className?: string }>;
  tone: string;
  label: string;
} {
  const ext = file.split(".").pop()?.toLowerCase();
  if (ext === "json")
    return { Icon: FileJson, tone: "text-info", label: "JSON 结构化数据" };
  if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext || ""))
    return { Icon: FileImage, tone: "text-bronze", label: "图片资源" };
  if (["pdf"].includes(ext || ""))
    return { Icon: FileType2, tone: "text-destructive", label: "PDF 文档" };
  if (["log", "txt"].includes(ext || ""))
    return { Icon: FileText, tone: "text-muted-foreground", label: "日志/文本" };
  return { Icon: FileText, tone: "text-muted-foreground", label: "文件" };
}

function mockPreviewContent(file: string): string {
  const ext = file.split(".").pop()?.toLowerCase();
  if (ext === "json") {
    return `{
  "stage": "textbook-parse",
  "version": "1.0",
  "parsedAt": "2026-06-12T09:25:00+08:00",
  "subject": "数学",
  "grade": "三年级",
  "lesson": "认识分数——分一分",
  "coreKnowledgePoints": [
    "二分之一的含义",
    "四分之一的含义",
    "分数各部分名称"
  ],
  "confidence": 0.94
}`;
  }
  if (ext === "log") {
    return `[2026-06-12 09:24:01] INFO  开始解析教材
[2026-06-12 09:24:14] INFO  识别 9 页，抽取结构化字段
[2026-06-12 09:25:00] INFO  解析完成，等待确认
[2026-06-12 09:30:12] INFO  教师确认解析结果`;
  }
  if (ext === "pdf") {
    return "该文件为 PDF 文档，演示环境暂不支持内嵌预览。\n实际环境中将在此处渲染文档内容。";
  }
  if (["png", "jpg", "jpeg"].includes(ext || "")) {
    return "该文件为图片资源，演示环境暂不支持内嵌预览。\n实际环境中将在此处显示缩略图。";
  }
  return "演示环境暂不支持该文件类型的内嵌预览。";
}

function EvidencePreviewDialog({
  file,
  onClose,
  stageTitle,
}: {
  file: string | null;
  onClose: () => void;
  stageTitle?: string;
}) {
  const meta = file ? getFileMeta(file) : null;
  const Icon = meta?.Icon || FileText;
  return (
    <Dialog open={!!file} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-[680px] gap-0 p-0 shadow-lift" aria-describedby={undefined}>
        <DialogTitle className="sr-only">证据文件预览</DialogTitle>
        <DialogDescription className="sr-only">
          预览阶段产出的证据文件内容。
        </DialogDescription>
        {file && meta && (
          <>
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex min-w-0 items-center gap-2.5">
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted",
                    meta.tone,
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <div className="t-module truncate">{file}</div>
                  <div className="t-caption text-muted-foreground">
                    {meta.label}
                    {stageTitle ? ` · ${stageTitle}` : ""}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-1.5 text-muted-foreground"
                  onClick={() => toast.info("演示版暂不支持下载")}
                >
                  <Download className="h-4 w-4" />
                  下载
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={onClose}
                  aria-label="关闭"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="bg-muted/20 p-5">
              <pre className="max-h-[55vh] overflow-auto scroll-fine rounded-md border border-border bg-card p-4 font-mono t-caption leading-relaxed text-foreground/85">
                <HighlightedPreview file={file} />
              </pre>
              <div className="mt-3 flex items-center gap-2 t-caption text-muted-foreground">
                <Eye className="h-3.5 w-3.5" />
                演示环境预览内容为模拟数据，仅作占位展示。
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function TermRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-32 shrink-0 pt-0.5 t-caption text-muted-foreground">
        {label}
      </dt>
      <dd className="flex-1 t-body text-foreground/90">{value}</dd>
    </div>
  );
}

/* ---------- 底部操作栏 ---------- */

function StageActions({
  canSave,
  canRegenerate,
  canApprove,
  canReject,
  canNext,
  isRunning,
  onSave,
  onRegenerate,
  onApprove,
  onReject,
  onNext,
}: {
  canSave: boolean;
  canRegenerate: boolean;
  canApprove: boolean;
  canReject: boolean;
  canNext: boolean;
  isRunning: boolean;
  onSave: () => void;
  onRegenerate: () => void;
  onApprove: () => void;
  onReject: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onSave}
          disabled={!canSave}
        >
          <Save className="h-4 w-4" />
          保存
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onRegenerate}
          disabled={!canRegenerate}
        >
          <RefreshCw
            className={cn("h-4 w-4", isRunning && "animate-spin")}
          />
          {isRunning ? "运行中" : "重新生成"}
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={onReject}
          disabled={!canReject}
        >
          <RotateCcw className="h-4 w-4" />
          退回修改
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onNext}
          disabled={!canNext}
        >
          进入下一步
          <ArrowRight className="h-4 w-4" />
        </Button>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={onApprove}
          disabled={!canApprove}
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Check className="h-4 w-4" />
          )}
          确认通过
        </Button>
      </div>
    </div>
  );
}

/* ---------- 键盘快捷键提示 ---------- */

function KeyboardHint({ keys, label }: { keys: string[]; label: string }) {
  return (
    <div className="hidden items-center gap-1.5 sm:flex">
      <span className="t-caption text-muted-foreground">{label}</span>
      <span className="flex items-center gap-1">
        {keys.map((k) => (
          <kbd
            key={k}
            className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded border border-border bg-card px-1 font-mono text-[10px] text-muted-foreground shadow-sm"
          >
            {k}
          </kbd>
        ))}
      </span>
    </div>
  );
}

/* ---------- 语法高亮预览 ---------- */

/** 简易 JSON 语法高亮：用正则 tokenize，返回 React 节点数组。零外部依赖。 */
function highlightJson(jsonStr: string): React.ReactNode[] {
  // 按行处理，每行识别 key / string / number / boolean / null / punctuation
  const lines = jsonStr.split("\n");
  return lines.map((line, lineIdx) => {
    // 缩进
    const indentMatch = line.match(/^(\s*)/);
    const indent = indentMatch ? indentMatch[1] : "";
    const rest = line.slice(indent.length);
    // 匹配 "key": value 或 value
    const tokens: React.ReactNode[] = [];
    let key = 1;
    // key: "..." :
    const keyMatch = rest.match(/^"([^"\\]*(?:\\.[^"\\]*)*)"(\s*:\s*)/);
    if (keyMatch) {
      tokens.push(
        <span key={`k${key++}`} className="text-primary">{`"${keyMatch[1]}"`}</span>,
        <span key={`c${key++}`} className="text-muted-foreground">{keyMatch[2]}</span>,
      );
      const valuePart = rest.slice(keyMatch[0].length);
      tokens.push(...tokenizeValue(valuePart, key));
    } else {
      tokens.push(...tokenizeValue(rest, key));
    }
    return (
      <span key={lineIdx} className="block">
        {indent}
        {tokens}
      </span>
    );
  });
}

function tokenizeValue(s: string, keyBase: number): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  let key = keyBase * 100;
  // 简单分词：字符串、数字、布尔/null、标点
  const regex = /("(?:[^"\\]|\\.)*")|(\b-?\d+(?:\.\d+)?\b)|(\btrue\b|\bfalse\b|\bnull\b)|([{}\[\],])/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(s)) !== null) {
    if (m.index > last) {
      out.push(<span key={`t${key++}`}>{s.slice(last, m.index)}</span>);
    }
    if (m[1]) {
      // 字符串值
      out.push(<span key={`s${key++}`} className="text-success">{m[1]}</span>);
    } else if (m[2]) {
      out.push(<span key={`n${key++}`} className="text-bronze">{m[2]}</span>);
    } else if (m[3]) {
      out.push(<span key={`b${key++}`} className="text-info">{m[3]}</span>);
    } else if (m[4]) {
      out.push(<span key={`p${key++}`} className="text-muted-foreground">{m[4]}</span>);
    }
    last = regex.lastIndex;
  }
  if (last < s.length) {
    out.push(<span key={`t${key++}`}>{s.slice(last)}</span>);
  }
  return out;
}

/** 日志级别着色 */
function highlightLog(logStr: string): React.ReactNode[] {
  return logStr.split("\n").map((line, idx) => {
    const m = line.match(/^(\[[^\]]+\])\s+(INFO|WARN|ERROR|SUCCESS)\s+(.*)$/);
    if (m) {
      const [, ts, level, msg] = m;
      const levelColor =
        level === "ERROR"
          ? "text-destructive"
          : level === "WARN"
            ? "text-warning"
            : level === "SUCCESS"
              ? "text-success"
              : "text-info";
      return (
        <span key={idx} className="block">
          <span className="text-muted-foreground">{ts}</span>{" "}
          <span className={`font-semibold ${levelColor}`}>{level}</span>{" "}
          <span className="text-foreground/90">{msg}</span>
        </span>
      );
    }
    return <span key={idx} className="block">{line}</span>;
  });
}

function HighlightedPreview({ file }: { file: string }) {
  const ext = file.split(".").pop()?.toLowerCase();
  const content = mockPreviewContent(file);
  if (ext === "json") {
    return <>{highlightJson(content)}</>;
  }
  if (ext === "log" || ext === "txt") {
    return <>{highlightLog(content)}</>;
  }
  return <span className="whitespace-pre-wrap">{content}</span>;
}
