"use client";

import { useEffect, useMemo, useState } from "react";
import { useAppStore } from "@/lib/store";
import { MOCK_PENDING_ITEMS, MOCK_SYSTEM_STATUS, MOCK_RECENT_ACTIVITIES } from "@/lib/mock-data";
import { stageDefByKey } from "@/lib/workflow";
import { ProjectCard } from "@/components/project/ProjectCard";
import { ProjectStatusBadge, ToneBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/StateViews";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowRight,
  ArrowUpRight,
  Plus,
  ClipboardList,
  Activity,
  ServerCog,
  HardDrive,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Inbox,
  Search,
  ArrowDownUp,
  X,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PendingItem, ProjectStatus, ActivityItem } from "@/lib/types";

export function DashboardScreen() {
  const user = useAppStore((s) => s.user);
  const dataMode = useAppStore((s) => s.dataMode);
  const projects = useAppStore((s) => s.projects);
  const projectsStatus = useAppStore((s) => s.projectsStatus);
  const projectsError = useAppStore((s) => s.projectsError);
  const loadProjects = useAppStore((s) => s.loadProjects);
  const go = useAppStore((s) => s.go);
  const openProject = useAppStore((s) => s.openProject);

  const isAdmin = user?.role === "admin";

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  // 继续工作：选择最近活跃的进行中/待确认/阻塞项目
  const continueProject =
    projects.find((p) => p.status === "active") ||
    projects.find((p) => p.status === "pending") ||
    projects.find((p) => p.status === "blocked") ||
    projects[0];

  const pendingItems = dataMode === "demo" ? MOCK_PENDING_ITEMS : [];
  const system = MOCK_SYSTEM_STATUS;

  const hour = new Date().getHours();
  const greeting = hour < 6 ? "凌晨好" : hour < 12 ? "上午好" : hour < 18 ? "下午好" : "晚上好";

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* 页头 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">工作台首页</div>
          <h1 className="mt-2 t-title">
            {greeting}，{user?.displayName}
          </h1>
          <p className="mt-2 t-body text-muted-foreground">
            以下是当前需要你关注的工作。一眼看清下一步要做什么。
          </p>
        </div>
        <Button className="gap-2" onClick={() => go("new-project")}>
          <Plus className="h-4 w-4" />
          新建项目
        </Button>
      </div>

      {/* 1. 继续工作 —— 首页视觉主角 */}
      <section className="mt-8">
        <SectionHeader index="01" title="继续工作" desc="从上次离开的地方继续推进" />
        {projectsStatus === "loading" ? (
          <Card className="border-border bg-card p-10 text-center">
            <Activity className="mx-auto h-8 w-8 animate-pulse text-muted-foreground" />
            <p className="mt-3 t-module">正在读取真实项目列表</p>
            <p className="mt-1 t-caption text-muted-foreground">
              数据来源：GET /projects
            </p>
          </Card>
        ) : projectsStatus === "error" ? (
          <Card className="border-dashed bg-card p-10 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-destructive" />
            <p className="mt-3 t-module">项目列表读取失败</p>
            <p className="mt-1 t-caption text-muted-foreground">
              {projectsError || "请确认后端 API 已启动"}
            </p>
            <Button className="mt-4 gap-2" onClick={() => void loadProjects()}>
              <RefreshCwIcon />
              重试
            </Button>
          </Card>
        ) : continueProject ? (
          <ContinueWorkHero
            project={continueProject}
            onEnter={() => openProject(continueProject.id)}
          />
        ) : (
          <Card className="border-dashed bg-card p-10 text-center">
            <Inbox className="mx-auto h-8 w-8 text-muted-foreground" />
            <p className="mt-3 t-module">暂无进行中的项目</p>
            {dataMode === "api" && (
              <p className="mt-1 t-caption text-muted-foreground">
                当前为真实 API 模式，项目列表不会使用 demo mock 数据。
              </p>
            )}
            <Button className="mt-4 gap-2" onClick={() => go("new-project")}>
              <Plus className="h-4 w-4" /> 新建第一个项目
            </Button>
          </Card>
        )}
      </section>

      {/* 2 + 3 双栏 */}
      <div className="mt-10 grid gap-8 lg:grid-cols-3">
        {/* 2. 项目概览（带筛选/排序/搜索） */}
        <section className="lg:col-span-2">
          <ProjectOverview />
        </section>

        {/* 3. 待处理事项 */}
        <section>
          <SectionHeader
            index="03"
            title="待处理事项"
            desc="需要你确认或处理"
          />
          <Card className="border-border bg-card p-2">
            {pendingItems.length > 0 ? (
              <ul className="divide-y divide-border">
                {pendingItems.map((item) => (
                  <PendingRow
                    key={item.id}
                    item={item}
                    onClick={() => openProject(item.projectId)}
                  />
                ))}
              </ul>
            ) : (
              <EmptyState
                title="暂无真实待办"
                desc="真实 API 模式下待办事项需等待任务接口接入。"
                icon={<Inbox className="h-5 w-5" />}
              />
            )}
          </Card>
        </section>
      </div>

      {/* 4. 系统轻状态 */}
      <section className="mt-10">
        <SectionHeader
          index="04"
          title="系统轻状态"
          desc="仅显示必要的运行状态，不堆砌监控"
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <LightStat
            icon={<Activity className="h-4 w-4" />}
            label="调度器"
            value={system.scheduler === "running" ? "运行中" : system.scheduler}
            tone={system.scheduler === "running" ? "success" : "neutral"}
          />
          <LightStat
            icon={<ServerCog className="h-4 w-4" />}
            label="队列任务"
            value={`${system.queueTasks} 个`}
            tone="info"
          />
          <LightStat
            icon={<HardDrive className="h-4 w-4" />}
            label="存储使用"
            value={`${system.storageUsedPct}%`}
            tone={system.storageUsedPct > 80 ? "warning" : "neutral"}
            progress={system.storageUsedPct}
          />
          <LightStat
            icon={<Clock className="h-4 w-4" />}
            label="最近心跳"
            value={system.lastHeartbeat.slice(11)}
            tone="neutral"
          />
        </div>

        {isAdmin && (
          <Card className="mt-4 border-border bg-card p-5">
            <div className="t-overline mb-3 text-muted-foreground/70">
              服务状态
            </div>
            <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
              {system.services.map((svc) => (
                <div
                  key={svc.name}
                  className="flex items-center justify-between gap-3"
                >
                  <span className="t-body text-muted-foreground">{svc.name}</span>
                  <ServiceStatus status={svc.status} note={svc.note} />
                </div>
              ))}
            </div>
          </Card>
        )}
      </section>

      <div className="h-2" />
    </div>
  );
}

function SectionHeader({
  index,
  title,
  desc,
  action,
}: {
  index: string;
  title: string;
  desc?: string;
  action?: React.ReactNode;
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
      {action}
    </div>
  );
}

function ContinueWorkHero({
  project,
  onEnter,
}: {
  project: ReturnType<typeof useAppStore.getState>["projects"][number];
  onEnter: () => void;
}) {
  const stage = stageDefByKey(project.currentStage);
  const stageTitle = project.currentStageTitle || stage?.title || project.currentStage;
  return (
    <Card className="relative overflow-hidden border-border bg-card p-0">
      <div className="grid gap-0 lg:grid-cols-[1.4fr_1fr]">
        {/* 左：项目信息 */}
        <div className="p-6 lg:p-8">
          <div className="flex items-center gap-2">
            <span className="t-overline text-bronze">继续工作</span>
            <ProjectStatusBadge status={project.status} />
          </div>
          <h3 className="mt-3 text-2xl font-semibold leading-tight">
            {project.name}
          </h3>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 t-body text-muted-foreground">
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

          <div className="mt-6 rounded-lg border border-border bg-muted/40 p-4">
            <div className="t-caption text-muted-foreground">下一步动作</div>
            <div className="mt-1.5 flex items-center gap-2 t-body font-medium">
              <span className="inline-block h-4 w-1 rounded-full bg-primary" />
              {project.nextAction}
            </div>
          </div>

          <div className="mt-5">
            <div className="flex items-center justify-between t-caption text-muted-foreground">
              <span>当前阶段：{stageTitle}</span>
              <span className="font-medium text-foreground">
                {project.progress}%
              </span>
            </div>
            <Progress value={project.progress} className="mt-2 h-1.5 bg-muted" />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button className="gap-2" onClick={onEnter}>
              进入工作区
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" className="gap-2">
              <ClipboardList className="h-4 w-4" />
              查看流程
            </Button>
          </div>
        </div>

        {/* 右：阶段进度 + 最近活动 */}
        <div className="relative hidden border-l border-border bg-muted/30 p-6 lg:block lg:p-8">
          <div className="t-overline text-muted-foreground/70">阶段进度</div>
          <StageMiniRail currentStageKey={project.currentStage} />

          <div className="mt-8 border-t border-border pt-6">
            <div className="flex items-center justify-between">
              <div className="t-overline text-muted-foreground/70">最近活动</div>
              <span className="t-caption text-muted-foreground/60">今日</span>
            </div>
            <ActivityTimeline projectId={project.id} />
          </div>
        </div>
      </div>
    </Card>
  );
}

/* ---------- 活动时间线 ---------- */

const ACTIVITY_META: Record<
  ActivityItem["kind"],
  { Icon: React.ComponentType<{ className?: string }>; tone: string; bg: string; label: string }
> = {
  approve: { Icon: CheckCircle2, tone: "text-success", bg: "bg-success/10", label: "确认" },
  reject: { Icon: AlertTriangle, tone: "text-destructive", bg: "bg-destructive/10", label: "退回" },
  generate: { Icon: Activity, tone: "text-info", bg: "bg-info/10", label: "生成" },
  parse: { Icon: ClipboardList, tone: "text-info", bg: "bg-info/10", label: "解析" },
  adopt: { Icon: CheckCircle2, tone: "text-bronze", bg: "bg-bronze/10", label: "采纳" },
  comment: { Icon: ClipboardList, tone: "text-muted-foreground", bg: "bg-muted", label: "备注" },
  upload: { Icon: ClipboardList, tone: "text-muted-foreground", bg: "bg-muted", label: "上传" },
};

function ActivityTimeline({ projectId }: { projectId?: string }) {
  const dataMode = useAppStore((s) => s.dataMode);
  const openProject = useAppStore((s) => s.openProject);
  const items = useMemo(() => {
    if (dataMode === "api") return [];
    const list = projectId
      ? MOCK_RECENT_ACTIVITIES.filter((a) => a.projectId === projectId)
      : MOCK_RECENT_ACTIVITIES;
    return list.slice(0, 5);
  }, [dataMode, projectId]);

  if (items.length === 0) {
    return (
      <div className="mt-3 t-caption text-muted-foreground/70">
        暂无最近活动
      </div>
    );
  }

  return (
    <ol className="mt-3 space-y-3.5">
      {items.map((item, idx) => {
        const meta = ACTIVITY_META[item.kind];
        const Icon = meta.Icon;
        const isLast = idx === items.length - 1;
        return (
          <li key={item.id} className="relative flex gap-3">
            {/* 时间线竖线 */}
            {!isLast && (
              <span
                className="absolute left-[13px] top-7 bottom-[-14px] w-px bg-border"
                aria-hidden
              />
            )}
            <span
              className={cn(
                "relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                meta.bg,
              )}
            >
              <Icon className={cn("h-3.5 w-3.5", meta.tone)} />
            </span>
            <div className="min-w-0 flex-1 pb-1">
              <div className="flex items-center justify-between gap-2">
                <span className="t-caption font-medium text-foreground/80">
                  {item.title}
                </span>
                <span className="shrink-0 font-mono t-caption text-muted-foreground/70">
                  {item.time}
                </span>
              </div>
              <p className="mt-0.5 t-caption text-muted-foreground line-clamp-1">
                {item.desc}
              </p>
              <button
                type="button"
                onClick={() => openProject(item.projectId)}
                className="mt-1 inline-flex items-center gap-1 t-caption text-muted-foreground/70 transition-colors hover:text-primary focus-ring"
              >
                {item.projectName} · {item.stageTitle}
                <ArrowRight className="h-2.5 w-2.5" />
              </button>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function RefreshCwIcon() {
  return <RefreshCw className="h-4 w-4" />;
}

function StageMiniRail({ currentStageKey }: { currentStageKey: string }) {
  // 简化版阶段轨：展示三个分支的关键节点
  const nodes = [
    { k: "project-config", t: "配置" },
    { k: "textbook-parse", t: "教材" },
    { k: "open-lesson-plan", t: "教案" },
    { k: "video-script", t: "视频剧本" },
    { k: "video-generation", t: "视频生成" },
    { k: "ppt-plan", t: "PPT方案" },
    { k: "pptx-generation", t: "PPTX" },
    { k: "final-delivery", t: "交付" },
  ];
  const currentIndex = nodes.findIndex((n) => n.k === currentStageKey);
  return (
    <div className="mt-4 space-y-2.5">
      {nodes.map((n, i) => {
        const done = i < currentIndex;
        const current = i === currentIndex;
        return (
          <div key={n.k} className="flex items-center gap-3">
            <span
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full text-[0.65rem] font-medium",
                done && "bg-success/15 text-success",
                current && "bg-primary text-primary-foreground",
                !done && !current && "bg-muted text-muted-foreground"
              )}
            >
              {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span
              className={cn(
                "t-body",
                current ? "font-medium text-foreground" : "text-muted-foreground"
              )}
            >
              {n.t}
            </span>
            {current && (
              <span className="ml-auto t-caption text-primary">进行中</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PendingRow({
  item,
  onClick,
}: {
  item: PendingItem;
  onClick: () => void;
}) {
  const kindMeta: Record<
    PendingItem["kind"],
    { label: string; tone: "warning" | "info" | "danger" | "success" }
  > = {
    confirm: { label: "待确认", tone: "warning" },
    input: { label: "待输入", tone: "info" },
    review: { label: "待复核", tone: "info" },
    error: { label: "异常", tone: "danger" },
  };
  const meta = kindMeta[item.kind];
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className="flex w-full items-start gap-3 px-3 py-3 text-left transition-colors hover:bg-muted/50 focus-ring"
      >
        <span
          className={cn(
            "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
            meta.tone === "danger"
              ? "bg-destructive/10 text-destructive"
              : meta.tone === "warning"
              ? "bg-warning/10 text-warning"
              : "bg-info/10 text-info"
          )}
        >
          {meta.tone === "danger" ? (
            <AlertTriangle className="h-3.5 w-3.5" />
          ) : (
            <ClipboardList className="h-3.5 w-3.5" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="t-body truncate font-medium">{item.title}</span>
            {item.priority === "high" && (
              <span className="t-caption rounded bg-destructive/10 px-1.5 py-0.5 text-destructive">
                高
              </span>
            )}
          </div>
          <div className="mt-0.5 t-caption text-muted-foreground line-clamp-1">
            {item.desc}
          </div>
          <div className="mt-1.5 flex items-center gap-2 t-caption text-muted-foreground/80">
            <span className="truncate">{item.projectName}</span>
            <span>·</span>
            <span>{item.stageTitle}</span>
          </div>
        </div>
        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
      </button>
    </li>
  );
}

function LightStat({
  icon,
  label,
  value,
  tone,
  progress,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "success" | "info" | "warning" | "neutral";
  progress?: number;
}) {
  const toneText =
    tone === "success"
      ? "text-success"
      : tone === "info"
      ? "text-info"
      : tone === "warning"
      ? "text-warning"
      : "text-foreground";
  return (
    <Card className="border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="t-caption text-muted-foreground">{label}</span>
        <span className={cn("text-muted-foreground", toneText)}>{icon}</span>
      </div>
      <div className={cn("mt-2 text-xl font-semibold", toneText)}>{value}</div>
      {typeof progress === "number" && (
        <Progress value={progress} className="mt-2 h-1 bg-muted" />
      )}
    </Card>
  );
}

function ServiceStatus({
  status,
  note,
}: {
  status: "ok" | "degraded" | "down";
  note: string;
}) {
  const map = {
    ok: { label: "正常", tone: "success" as const },
    degraded: { label: "降级", tone: "warning" as const },
    down: { label: "异常", tone: "danger" as const },
  };
  const m = map[status];
  return (
    <div className="flex items-center gap-2">
      <ToneBadge tone={m.tone}>{m.label}</ToneBadge>
      <span className="t-caption text-muted-foreground">{note}</span>
    </div>
  );
}

/* ---------- 项目概览：筛选 / 排序 / 搜索 ---------- */

type StatusFilter = "all" | ProjectStatus;
type SortKey = "updated" | "progress" | "name";

const STATUS_FILTER_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "全部状态" },
  { value: "active", label: "进行中" },
  { value: "pending", label: "待确认" },
  { value: "blocked", label: "阻塞" },
  { value: "failed", label: "失败" },
  { value: "done", label: "已完成" },
  { value: "draft", label: "草稿" },
];

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "updated", label: "最近更新" },
  { value: "progress", label: "进度" },
  { value: "name", label: "名称" },
];

function ProjectOverview() {
  const projects = useAppStore((s) => s.projects);

  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [subjectFilter, setSubjectFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("updated");

  const subjects = useMemo(() => {
    const set = new Set(projects.map((p) => p.subject));
    return ["all", ...Array.from(set)];
  }, [projects]);

  const filtered = useMemo(() => {
    let list = projects.slice();
    if (statusFilter !== "all") {
      list = list.filter((p) => p.status === statusFilter);
    }
    if (subjectFilter !== "all") {
      list = list.filter((p) => p.subject === subjectFilter);
    }
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.subject.toLowerCase().includes(q) ||
          p.grade.toLowerCase().includes(q) ||
          p.textbookVersion.toLowerCase().includes(q) ||
          p.owner.toLowerCase().includes(q),
      );
    }
    list.sort((a, b) => {
      if (sortKey === "progress") return b.progress - a.progress;
      if (sortKey === "name") return a.name.localeCompare(b.name, "zh");
      // updated：按 updatedAt 降序（字符串日期可比较）
      return b.updatedAt.localeCompare(a.updatedAt);
    });
    return list;
  }, [projects, statusFilter, subjectFilter, query, sortKey]);

  const hasActiveFilter =
    statusFilter !== "all" ||
    subjectFilter !== "all" ||
    query.trim() !== "";

  const resetFilters = () => {
    setStatusFilter("all");
    setSubjectFilter("all");
    setQuery("");
    setSortKey("updated");
  };

  return (
    <>
      <SectionHeader
        index="02"
        title="项目概览"
        desc="所有项目的当前状态一览"
        action={
          <span className="t-caption text-muted-foreground">
            共 {projects.length} 个 · 显示 {filtered.length} 个
          </span>
        }
      />

      {/* 筛选栏 */}
      <Card className="mb-4 border-border bg-card p-3">
        <div className="flex flex-col gap-2.5 lg:flex-row lg:items-center">
          {/* 搜索 */}
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索项目名、学科、年级、负责人…"
              className="h-9 border-border bg-background pl-9 pr-8"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="absolute right-2 top-1/2 inline-flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground focus-ring"
                aria-label="清除搜索"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* 状态筛选 */}
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as StatusFilter)}
          >
            <SelectTrigger className="h-9 w-full border-border bg-background sm:w-[130px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              {STATUS_FILTER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* 学科筛选 */}
          <Select
            value={subjectFilter}
            onValueChange={setSubjectFilter}
          >
            <SelectTrigger className="h-9 w-full border-border bg-background sm:w-[110px]">
              <SelectValue placeholder="学科" />
            </SelectTrigger>
            <SelectContent>
              {subjects.map((s) => (
                <SelectItem key={s} value={s}>
                  {s === "all" ? "全部学科" : s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* 排序 */}
          <Select
            value={sortKey}
            onValueChange={(v) => setSortKey(v as SortKey)}
          >
            <SelectTrigger className="h-9 w-full border-border bg-background sm:w-[130px]">
              <ArrowDownUp className="mr-1.5 h-3.5 w-3.5 text-muted-foreground" />
              <SelectValue placeholder="排序" />
            </SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {hasActiveFilter && (
            <Button
              variant="ghost"
              size="sm"
              className="h-9 gap-1.5 text-muted-foreground"
              onClick={resetFilters}
            >
              <X className="h-3.5 w-3.5" />
              重置
            </Button>
          )}
        </div>

        {/* 激活筛选标签 */}
        {hasActiveFilter && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border pt-2.5">
            <span className="t-caption text-muted-foreground">已筛选：</span>
            {statusFilter !== "all" && (
              <FilterChip
                label={STATUS_FILTER_OPTIONS.find((o) => o.value === statusFilter)?.label || ""}
                onClear={() => setStatusFilter("all")}
              />
            )}
            {subjectFilter !== "all" && (
              <FilterChip label={subjectFilter} onClear={() => setSubjectFilter("all")} />
            )}
            {query.trim() && (
              <FilterChip label={`"${query.trim()}"`} onClear={() => setQuery("")} />
            )}
          </div>
        )}
      </Card>

      {/* 项目卡片网格 */}
      {filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      ) : (
        <Card className="border-dashed bg-card p-10">
          <EmptyState
            title="未找到匹配的项目"
            desc="尝试调整筛选条件或搜索关键词。"
            icon={<Search className="h-5 w-5" />}
          />
          {hasActiveFilter && (
            <div className="flex justify-center pb-2">
              <Button variant="outline" size="sm" className="gap-1.5" onClick={resetFilters}>
                <X className="h-3.5 w-3.5" />
                清除筛选
              </Button>
            </div>
          )}
        </Card>
      )}
    </>
  );
}

function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/5 px-2 py-0.5 t-caption text-primary">
      {label}
      <button
        type="button"
        onClick={onClear}
        className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full hover:bg-primary/15 focus-ring"
        aria-label={`移除筛选 ${label}`}
      >
        <X className="h-2.5 w-2.5" />
      </button>
    </span>
  );
}
