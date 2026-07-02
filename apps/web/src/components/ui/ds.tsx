"use client";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ReactNode, ButtonHTMLAttributes } from "react";

/**
 * 统一设计系统组件 (DS Components)
 * 对标 Runway / Linear / Stripe 级别的精致度
 * 所有组件强制统一：圆角/高度/间距/阴影/字体/动效
 */

// ===== 统一按钮 =====

interface DSButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export function DSButton({ 
  variant = "primary", 
  size = "md", 
  className, 
  children, 
  ...props 
}: DSButtonProps) {
  const base = "inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-300 ease-apple focus-ring whitespace-nowrap";
  
  const sizes = {
    sm: "h-9 px-3.5 text-xs",
    md: "h-11 px-5 text-sm",
    lg: "h-12 px-6 text-base",
  };
  
  const variants = {
    primary: "bg-[#1a2b3c] text-white shadow-[0_4px_12px_rgba(26,43,60,0.25),0_8px_20px_-4px_rgba(26,43,60,0.20)] hover:bg-[#142233] hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(26,43,60,0.30),0_12px_28px_-6px_rgba(26,43,60,0.25)] active:translate-y-0",
    secondary: "bg-transparent text-foreground border border-border hover:border-bronze/50 hover:text-bronze hover:bg-bronze/5 hover:-translate-y-0.5 active:translate-y-0",
    ghost: "bg-transparent text-muted-foreground hover:bg-muted hover:text-foreground",
  };
  
  return (
    <button className={cn(base, sizes[size], variants[variant], className)} {...props}>
      {children}
    </button>
  );
}

// ===== 统一卡片 =====

export function DSCard({ 
  className, 
  children, 
  hover = true,
  ...props 
}: { 
  className?: string; 
  children: ReactNode; 
  hover?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <Card 
      className={cn(
        "rounded-xl border border-border bg-card p-5",
        "shadow-[0_1px_2px_rgba(35,39,46,0.04),0_6px_16px_-6px_rgba(35,39,46,0.08)]",
        hover && "transition-all duration-300 ease-apple hover:shadow-[0_1px_2px_rgba(35,39,46,0.04),0_12px_32px_-8px_rgba(35,39,46,0.12),0_40px_80px_-24px_rgba(35,39,46,0.16)] hover:border-bronze/25 hover:-translate-y-0.5",
        className
      )}
      {...props}
    >
      {children}
    </Card>
  );
}

// ===== 统一 Section 标题 =====

export function DSSectionTitle({ 
  icon, 
  title, 
  desc,
  action,
  className 
}: { 
  icon?: ReactNode; 
  title: string; 
  desc?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-3", className)}>
      <div className="flex items-start gap-3">
        {icon && (
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-primary shadow-[0_1px_2px_rgba(35,39,46,0.04)] transition-colors duration-300 ease-apple hover:border-bronze/40">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-[1.0625rem] font-semibold leading-tight text-foreground">{title}</h2>
          {desc && <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{desc}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

// ===== 统一 Badge =====

export function DSBadge({ 
  children, 
  variant = "neutral",
  className 
}: { 
  children: ReactNode; 
  variant?: "success" | "warning" | "error" | "info" | "neutral";
  className?: string;
}) {
  const variants = {
    success: "bg-[#4f6b59]/12 text-[#4f6b59] border-[#4f6b59]/25",
    warning: "bg-[#9a7340]/12 text-[#9a7340] border-[#9a7340]/25",
    error: "bg-[#9a4747]/12 text-[#9a4747] border-[#9a4747]/25",
    info: "bg-[#45627a]/12 text-[#45627a] border-[#45627a]/25",
    neutral: "bg-muted text-muted-foreground border-border",
  };
  
  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[0.6875rem] font-semibold leading-relaxed",
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
}

// ===== 统一 Pill 选择器 =====

export function DSPill({ 
  children, 
  active = false,
  className 
}: { 
  children: ReactNode; 
  active?: boolean;
  className?: string;
}) {
  return (
    <span className={cn(
      "inline-flex h-10 items-center gap-2 rounded-full px-4 text-xs font-medium transition-all duration-300 ease-apple",
      active 
        ? "bg-primary text-primary-foreground" 
        : "bg-muted text-foreground hover:bg-muted/70 hover:border-border border border-transparent",
      className
    )}>
      {children}
    </span>
  );
}

// ===== 统一空状态 =====

export function DSEmptyState({ 
  icon, 
  title, 
  desc,
  action,
  className 
}: { 
  icon?: ReactNode; 
  title: string; 
  desc?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2.5 rounded-lg border border-dashed border-border bg-muted/20 px-6 py-10 text-center", className)}>
      {icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-background text-muted-foreground shadow-[0_1px_2px_rgba(35,39,46,0.04)]">
          {icon}
        </div>
      )}
      <div className="text-sm font-semibold text-foreground">{title}</div>
      {desc && <div className="max-w-xs text-xs leading-relaxed text-muted-foreground">{desc}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

// ===== 统一进度条 =====

export function DSProgress({ 
  value, 
  variant = "default",
  className 
}: { 
  value: number; 
  variant?: "default" | "success" | "warning";
  className?: string;
}) {
  const barColors = {
    default: "bg-gradient-to-r from-primary to-bronze",
    success: "bg-gradient-to-r from-[#4f6b59] to-[#6b8c78]",
    warning: "bg-gradient-to-r from-[#9a7340] to-[#c6a366]",
  };
  
  return (
    <div className={cn("h-1.5 overflow-hidden rounded-full bg-muted", className)}>
      <div 
        className={cn("h-full rounded-full transition-all duration-700 ease-apple", barColors[variant])}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

// ===== 统一状态圆点 =====

export function DSStatusDot({ 
  status,
  className 
}: { 
  status: "active" | "completed" | "failed" | "pending";
  className?: string;
}) {
  const colors = {
    active: "bg-primary animate-pulse",
    completed: "bg-[#4f6b59]",
    failed: "bg-[#9a4747]",
    pending: "bg-muted-foreground/50",
  };
  
  return (
    <span className={cn("inline-block h-2 w-2 shrink-0 rounded-full", colors[status], className)} />
  );
}
