import { cn } from "@/lib/utils";
import { Inbox, Loader2, AlertTriangle } from "lucide-react";

export function EmptyState({
  title = "暂无内容",
  desc,
  className,
  icon,
}: {
  title?: string;
  desc?: string;
  className?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-12 text-center",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        {icon || <Inbox className="h-5 w-5" />}
      </div>
      <div className="t-module text-foreground/80">{title}</div>
      {desc && <p className="t-body max-w-sm text-muted-foreground">{desc}</p>}
    </div>
  );
}

export function LoadingState({
  label = "加载中",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-center gap-3 py-10 text-muted-foreground",
        className
      )}
    >
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="t-body">{label}</span>
    </div>
  );
}

export function ErrorState({
  title = "出现错误",
  desc,
  className,
}: {
  title?: string;
  desc?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-10 text-center",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <div className="t-module text-foreground/80">{title}</div>
      {desc && <p className="t-body max-w-sm text-muted-foreground">{desc}</p>}
    </div>
  );
}
