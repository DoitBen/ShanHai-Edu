"use client";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import type { ScreenKey } from "@/lib/types";
import { Logo } from "@/components/brand/Logo";
import {
  LayoutDashboard,
  FolderPlus,
  FolderKanban,
  Settings,
  ScrollText,
  TerminalSquare,
  LifeBuoy,
  GitBranch,
  LibraryBig,
  Images,
} from "lucide-react";

type NavItem = {
  key: ScreenKey | "current-project";
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  screen: ScreenKey;
  adminOnly?: boolean;
  shortcut?: string;
};

const NAV: NavItem[] = [
  { key: "dashboard", label: "首页", icon: LayoutDashboard, screen: "dashboard", shortcut: "G D" },
  { key: "new-project", label: "新建项目", icon: FolderPlus, screen: "new-project", shortcut: "G N" },
  {
    key: "current-project",
    label: "当前项目",
    icon: FolderKanban,
    screen: "project",
    shortcut: "G P",
  },
  {
    key: "config",
    label: "配置中心",
    icon: Settings,
    screen: "config",
    adminOnly: true,
    shortcut: "G C",
  },
  {
    key: "admin-workflow",
    label: "规则控制面",
    icon: GitBranch,
    screen: "admin-workflow",
    adminOnly: true,
    shortcut: "G W",
  },
  {
    key: "admin-textbook-library",
    label: "管理教材库",
    icon: LibraryBig,
    screen: "admin-textbook-library",
    adminOnly: true,
  },
  {
    key: "admin-media-workbench",
    label: "媒体生成工作台",
    icon: Images,
    screen: "admin-media-workbench",
    adminOnly: true,
    shortcut: "G M",
  },
  { key: "logs", label: "日志", icon: ScrollText, screen: "logs", adminOnly: true, shortcut: "G L" },
  {
    key: "scripts",
    label: "脚本",
    icon: TerminalSquare,
    screen: "scripts",
    adminOnly: true,
    shortcut: "G S",
  },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const screen = useAppStore((s) => s.screen);
  const activeProjectId = useAppStore((s) => s.activeProjectId);
  const projects = useAppStore((s) => s.projects);
  const user = useAppStore((s) => s.user);
  const dataMode = useAppStore((s) => s.dataMode);
  const go = useAppStore((s) => s.go);
  const openProject = useAppStore((s) => s.openProject);

  const isAdmin = user?.role === "admin";
  const activeProject = projects.find((p) => p.id === activeProjectId);

  const handleClick = (item: NavItem) => {
    if (item.screen === "project" && activeProjectId) {
      openProject(activeProjectId);
    } else {
      go(item.screen);
    }
    onNavigate?.();
  };

  return (
    <div className="flex h-full flex-col bg-sidebar">
      {/* 品牌 */}
      <div className="relative flex h-16 items-center px-5">
        <span
          className="absolute left-0 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-r-full bg-primary"
          aria-hidden
        />
        <Logo size={32} subline="ProMax 工作台" />
      </div>

      <div className="mx-5 mb-2 h-px bg-sidebar-border" />

      {/* 主导航 */}
      <nav className="flex-1 overflow-y-auto scroll-fine px-3 py-2">
        <div className="t-overline mb-2 px-2 text-muted-foreground/70">
          工作台
        </div>
        <ul className="space-y-0.5">
          {NAV.filter((n) => !n.adminOnly || isAdmin).map((item) => {
            const Icon = item.icon;
            const isActive =
              item.screen === screen &&
              !(item.screen === "project" && !activeProjectId);
            const disabled = item.screen === "project" && !activeProjectId;
            return (
              <li key={item.key} className="relative">
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary"
                    aria-hidden
                  />
                )}
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => handleClick(item)}
                  className={cn(
                    "group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
                    "focus-ring",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                      : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                    disabled && "opacity-40 cursor-not-allowed hover:bg-transparent"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-[18px] w-[18px] shrink-0",
                      isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  <span className="t-body font-medium">{item.label}</span>
                  {item.screen === "project" && activeProject ? (
                    <span className="ml-auto hidden max-w-[5.5rem] truncate text-[0.7rem] text-muted-foreground sm:inline">
                      {activeProject.name}
                    </span>
                  ) : (
                    item.shortcut && (
                      <kbd className="ml-auto hidden shrink-0 items-center gap-0.5 rounded border border-sidebar-border bg-sidebar/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground/70 lg:inline-flex">
                        {item.shortcut}
                      </kbd>
                    )
                  )}
                </button>
              </li>
            );
          })}
        </ul>

        {isAdmin && (
          <>
            <div className="t-overline mb-2 mt-6 px-2 text-muted-foreground/70">
              系统轻状态
            </div>
            <div className="rounded-lg border border-sidebar-border bg-card/60 p-3.5">
              <div className="t-body flex items-center justify-between">
                <span className="text-muted-foreground">调度器</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 font-medium",
                    dataMode === "demo" ? "text-success" : "text-muted-foreground"
                  )}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      dataMode === "demo" ? "bg-success animate-pulse" : "bg-muted-foreground/50"
                    )}
                  />
                  {dataMode === "demo" ? "演示运行中" : "未接入运行检测"}
                </span>
              </div>
              <div className="t-body mt-2.5 flex items-center justify-between">
                <span className="text-muted-foreground">队列任务</span>
                <span className="font-medium">{dataMode === "demo" ? "3 个演示任务" : "未接入检测"}</span>
              </div>
              <div className="mt-2.5">
                <div className="flex items-center justify-between t-body">
                  <span className="text-muted-foreground">存储</span>
                  <span className="font-medium">{dataMode === "demo" ? "38%" : "未接入检测"}</span>
                </div>
                <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-bronze/70"
                    style={{ width: dataMode === "demo" ? "38%" : "0%" }}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </nav>

      {/* 底部帮助 */}
      <div className="border-t border-sidebar-border p-3">
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground focus-ring"
        >
          <LifeBuoy className="h-[18px] w-[18px] text-muted-foreground" />
          <span className="t-body">使用指引</span>
        </button>
        <div className="mt-2 px-3 t-caption text-muted-foreground/70">
          山海教育 · ProMax v1.0
        </div>
      </div>
    </div>
  );
}
