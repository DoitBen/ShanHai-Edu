"use client";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import type { ProjectMeta } from "@/lib/types";
import { stageDefByKey } from "@/lib/workflow";
import { ProjectStatusBadge } from "@/components/common/StatusBadge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  CalendarClock,
  BookOpen,
  Layers,
} from "lucide-react";

export function ProjectCard({
  project,
  variant = "default",
}: {
  project: ProjectMeta;
  variant?: "default" | "compact";
}) {
  const openProject = useAppStore((s) => s.openProject);
  const stage = stageDefByKey(project.currentStage);
  const stageTitle = project.currentStageTitle || stage?.title || project.currentStage;

  return (
    <div className="h-full">
    <Card
      className={cn(
        "group card-pro card-pro-radius relative h-full overflow-hidden border-border bg-card p-5 shadow-apple-sm",
        variant === "compact" && "p-4"
      )}
    >
      {/* 顶部品牌色细线：hover 时从左侧展开 */}
      <span
        className="absolute left-0 top-0 h-[2px] w-0 bg-primary transition-all duration-300 group-hover:w-full"
        aria-hidden
      />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="t-caption rounded-md bg-muted px-2 py-0.5 text-muted-foreground">
              {project.subject}
            </span>
            <span className="t-caption text-muted-foreground">
              {project.grade} · {project.textbookVersion} {project.volume}
            </span>
          </div>
          <h3 className="mt-2 t-module truncate">{project.name}</h3>
        </div>
        <ProjectStatusBadge status={project.status} />
      </div>

      <div className="mt-4 flex items-center gap-2 text-muted-foreground">
        <Layers className="h-3.5 w-3.5" />
        <span className="t-body">当前阶段</span>
        <span className="t-body font-medium text-foreground">
          {stageTitle}
        </span>
      </div>

      <div className="mt-2 rounded-md border border-border bg-muted/35 px-3 py-2">
        <div className="t-caption text-muted-foreground">下一步动作</div>
        <div className="mt-0.5 line-clamp-1 t-body font-medium text-foreground">
          {project.nextAction}
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-center justify-between t-caption text-muted-foreground">
          <span>总进度</span>
          <span className="font-medium text-foreground">{project.progress}%</span>
        </div>
        <Progress
          value={project.progress}
          className="mt-1.5 h-1.5 bg-muted"
        />
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 border-t border-border pt-3">
        <div className="flex min-w-0 items-center gap-1.5 t-caption text-muted-foreground">
          <CalendarClock className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">{project.updatedAt}</span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          className="h-8 gap-1 px-2 text-muted-foreground group-hover:text-foreground"
          onClick={() => openProject(project.id)}
        >
          进入
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </Card>
    </div>
  );
}

export function ProjectCardMinimal({ project }: { project: ProjectMeta }) {
  const openProject = useAppStore((s) => s.openProject);
  const stage = stageDefByKey(project.currentStage);
  const stageTitle = project.currentStageTitle || stage?.title || project.currentStage;
  return (
    <button
      type="button"
      onClick={() => openProject(project.id)}
      className="flex w-full items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-left shadow-apple-sm transition-all duration-300 ease-apple hover:bg-muted/60 hover:-translate-y-0.5 focus-ring"
    >
      <BookOpen className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="t-body truncate font-medium">{project.name}</div>
        <div className="t-caption mt-0.5 text-muted-foreground">
          {stageTitle} · {project.progress}%
        </div>
      </div>
      <ProjectStatusBadge status={project.status} />
    </button>
  );
}
