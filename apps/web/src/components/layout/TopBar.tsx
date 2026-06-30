"use client";

import { useAppStore } from "@/lib/store";
import type { ScreenKey } from "@/lib/types";
import { LogoMark } from "@/components/brand/Logo";
import { isDemoMode } from "@/lib/demo-mode";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import {
  Menu,
  Bell,
  Search,
  ChevronRight,
  LogOut,
  UserRound,
  ShieldCheck,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const SCREEN_TITLE: Record<ScreenKey, string> = {
  dashboard: "首页",
  "new-project": "新建项目",
  project: "项目工作区",
  config: "配置中心",
  logs: "日志",
  scripts: "脚本",
  "admin-workflow": "规则控制面",
  "admin-textbook-library": "管理教材库",
  "admin-media-workbench": "媒体生成工作台",
};

export function TopBar({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const screen = useAppStore((s) => s.screen);
  const user = useAppStore((s) => s.user);
  const logout = useAppStore((s) => s.logout);
  const switchRole = useAppStore((s) => s.switchRole);
  const activeProjectId = useAppStore((s) => s.activeProjectId);
  const projects = useAppStore((s) => s.projects);
  const activeProject = projects.find((p) => p.id === activeProjectId);
  const demoMode = isDemoMode();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-md lg:px-8">
      <button
        type="button"
        onClick={onOpenMobileNav}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-muted lg:hidden focus-ring"
        aria-label="打开导航"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="lg:hidden">
        <LogoMark size={30} />
      </div>

      {/* 面包屑 */}
      <nav
        aria-label="面包屑"
        className="hidden items-center gap-2 text-sm lg:flex"
      >
        <span className="text-muted-foreground">工作台</span>
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
        <span className="font-medium text-foreground">
          {SCREEN_TITLE[screen]}
        </span>
        {screen === "project" && activeProject && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
            <span className="truncate text-muted-foreground">
              {activeProject.name}
            </span>
          </>
        )}
      </nav>

      <div className="ml-auto flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => useAppStore.getState().setCommandOpen(true)}
          className="hidden h-9 items-center gap-2 rounded-md border border-border bg-card pl-2.5 pr-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-ring md:inline-flex"
          aria-label="打开命令面板"
        >
          <Search className="h-[18px] w-[18px]" />
          <span className="t-caption">搜索…</span>
          <kbd className="ml-2 inline-flex h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground">
            ⌘K
          </kbd>
        </button>
        <Button
          variant="ghost"
          size="sm"
          className="h-9 w-9 p-0 text-muted-foreground md:hidden"
          aria-label="搜索"
          onClick={() => useAppStore.getState().setCommandOpen(true)}
        >
          <Search className="h-[18px] w-[18px]" />
        </Button>
        <ThemeToggle />
        <Button
          variant="ghost"
          size="sm"
          className="relative h-9 w-9 p-0 text-muted-foreground"
          aria-label="通知"
        >
          <Bell className="h-[18px] w-[18px]" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-bronze" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="ml-1 flex h-9 items-center gap-2 rounded-full border border-border bg-card pl-1 pr-3 text-left transition-colors hover:bg-muted focus-ring"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[0.7rem] font-semibold text-primary-foreground">
                {user?.displayName?.slice(0, 1) || "U"}
              </span>
              <span className="hidden sm:flex flex-col leading-none">
                <span className="t-body font-medium">{user?.displayName}</span>
                <span className="t-caption mt-0.5 text-muted-foreground">
                  {user?.role === "admin" ? "管理员" : "教师"}
                </span>
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>{user?.displayName}</span>
              <Badge
                variant="outline"
                className="border-border text-muted-foreground"
              >
                {user?.role === "admin" ? "管理员" : "教师"}
              </Badge>
            </DropdownMenuLabel>
            {demoMode && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => switchRole("admin")}
                  className="gap-2"
                >
                  <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                  切换为管理员
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => switchRole("teacher")}
                  className="gap-2"
                >
                  <UserRound className="h-4 w-4 text-muted-foreground" />
                  切换为教师
                </DropdownMenuItem>
              </>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => void logout()}
              className="gap-2 text-destructive focus:text-destructive"
            >
              <LogOut className="h-4 w-4" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
