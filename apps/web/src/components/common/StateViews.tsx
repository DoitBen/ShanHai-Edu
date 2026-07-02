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
        "empty-state-pro",
        className
      )}
    >
      <div className="icon-wrap">{icon || <Inbox className="h-5 w-5" />}</div>
      <div className="title">{title}</div>
      {desc && <p className="desc">{desc}</p>}
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
        "empty-state-pro",
        className
      )}
    >
      <div className="icon-wrap bg-destructive/10! text-destructive!">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <div className="title">{title}</div>
      {desc && <p className="desc">{desc}</p>}
    </div>
  );
}
