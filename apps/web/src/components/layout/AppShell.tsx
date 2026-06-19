"use client";

import { useEffect } from "react";
import { useAppStore, initAuth } from "@/lib/store";
import { useGlobalShortcuts } from "@/hooks/use-global-shortcuts";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { LoginScreen } from "@/components/screens/LoginScreen";
import { DashboardScreen } from "@/components/screens/DashboardScreen";
import { NewProjectScreen } from "@/components/screens/NewProjectScreen";
import { ProjectWorkspaceScreen } from "@/components/screens/ProjectWorkspaceScreen";
import { ConfigScreen } from "@/components/screens/ConfigScreen";
import { LogsScreen } from "@/components/screens/LogsScreen";
import { ScriptsScreen } from "@/components/screens/ScriptsScreen";
import { CommandPalette } from "@/components/command-palette/CommandPalette";
import { PageTransition } from "@/components/common/PageTransition";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Logo } from "@/components/brand/Logo";

export function AppShell() {
  const user = useAppStore((s) => s.user);
  const authReady = useAppStore((s) => s.authReady);
  const screen = useAppStore((s) => s.screen);
  const mobileNavOpen = useAppStore((s) => s.mobileNavOpen);
  const setMobileNavOpen = useAppStore((s) => s.setMobileNavOpen);

  useEffect(() => {
    initAuth();
  }, []);

  // 全局键盘快捷键：⌘K 命令面板、g d/n/c/l/s/p 单键导航、Escape 关闭
  useGlobalShortcuts();

  if (!authReady) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="t-body text-muted-foreground">正在加载工作台…</div>
      </div>
    );
  }

  if (!user) {
    return <LoginScreen />;
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* 桌面侧栏 */}
      <aside className="hidden w-64 shrink-0 border-r border-sidebar-border lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </aside>

      {/* 移动端抽屉 */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-72 p-0">
          <Sidebar onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* 主体 */}
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main className="flex-1">
          <PageTransition>
            {screen === "dashboard" && <DashboardScreen />}
            {screen === "new-project" && <NewProjectScreen />}
            {screen === "project" && <ProjectWorkspaceScreen />}
            {screen === "config" && <ConfigScreen />}
            {screen === "logs" && <LogsScreen />}
            {screen === "scripts" && <ScriptsScreen />}
          </PageTransition>
        </main>
        <footer className="mt-auto border-t border-border bg-background/80 px-4 py-4 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-2 text-center sm:flex-row sm:text-left">
            <Logo size={22} showWordmark={false} />
            <p className="t-caption text-muted-foreground">
              山海教育 · AI幼教ProMax可视化工作台 · 第一阶段演示版
            </p>
            <p className="t-caption text-muted-foreground/70">
              按 ⌘K 打开命令面板 · admin / shanhai2026
            </p>
          </div>
        </footer>
      </div>

      {/* 命令面板 */}
      <CommandPalette />
    </div>
  );
}
