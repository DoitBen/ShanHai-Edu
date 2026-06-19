import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  STAGE_STATUS_LABEL,
  STAGE_STATUS_TONE,
  type StageStatusTone,
} from "@/lib/workflow";
import type { ProjectStatus, StageStatus } from "@/lib/types";

const TONE_CLASS: Record<StageStatusTone, string> = {
  neutral: "bg-muted text-muted-foreground border-transparent",
  info: "bg-info/10 text-info border-info/20",
  warning: "bg-warning/10 text-warning border-warning/25",
  success: "bg-success/10 text-success border-success/25",
  danger: "bg-destructive/10 text-destructive border-destructive/25",
  brand: "bg-primary/10 text-primary border-primary/20",
};

const TONE_DOT: Record<StageStatusTone, string> = {
  neutral: "bg-muted-foreground/50",
  info: "bg-info",
  warning: "bg-warning",
  success: "bg-success",
  danger: "bg-destructive",
  brand: "bg-primary",
};

export function StatusBadge({
  status,
  className,
  withDot = true,
}: {
  status: StageStatus;
  className?: string;
  withDot?: boolean;
}) {
  const tone = STAGE_STATUS_TONE[status];
  const label = STAGE_STATUS_LABEL[status];
  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[0.7rem] font-medium tracking-wide",
        TONE_CLASS[tone],
        className
      )}
    >
      {withDot && (
        <span
          className={cn(
            "inline-block h-1.5 w-1.5 rounded-full",
            TONE_DOT[tone],
            tone === "brand" && "animate-pulse"
          )}
        />
      )}
      {label}
    </Badge>
  );
}

const PROJECT_STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: "草稿",
  active: "进行中",
  pending: "待确认",
  blocked: "阻塞",
  failed: "失败",
  done: "已完成",
};

const PROJECT_STATUS_TONE: Record<ProjectStatus, StageStatusTone> = {
  draft: "neutral",
  active: "brand",
  pending: "warning",
  blocked: "danger",
  failed: "danger",
  done: "success",
};

export function ProjectStatusBadge({
  status,
  className,
}: {
  status: ProjectStatus;
  className?: string;
}) {
  const tone = PROJECT_STATUS_TONE[status];
  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[0.7rem] font-medium tracking-wide",
        TONE_CLASS[tone],
        className
      )}
    >
      <span
        className={cn(
          "inline-block h-1.5 w-1.5 rounded-full",
          TONE_DOT[tone],
          tone === "brand" && "animate-pulse"
        )}
      />
      {PROJECT_STATUS_LABEL[status]}
    </Badge>
  );
}

export function ToneBadge({
  tone,
  children,
  className,
}: {
  tone: StageStatusTone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[0.7rem] font-medium tracking-wide",
        TONE_CLASS[tone],
        className
      )}
    >
      <span className={cn("inline-block h-1.5 w-1.5 rounded-full", TONE_DOT[tone])} />
      {children}
    </Badge>
  );
}
