"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import { useAppStore, initAuth } from "@/lib/store";
import { DEMO_PASSWORD, isDemoMode } from "@/lib/demo-mode";
import { useGlobalShortcuts } from "@/hooks/use-global-shortcuts";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { LoginScreen } from "@/components/screens/LoginScreen";
import { PageTransition } from "@/components/common/PageTransition";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Logo } from "@/components/brand/Logo";

const DashboardScreen = dynamic(
  () =>
    import("@/components/screens/DashboardScreen").then(
      (m) => m.DashboardScreen
    ),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载首页..." />,
  }
);

const NewProjectScreen = dynamic(
  () =>
    import("@/components/screens/NewProjectScreen").then(
      (m) => m.NewProjectScreen
    ),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载新建项目..." />,
  }
);

const ProjectWorkspaceScreen = dynamic(
  () =>
    import("@/components/screens/ProjectWorkspaceScreen").then(
      (m) => m.ProjectWorkspaceScreen
    ),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载项目工作区..." />,
  }
);

const ConfigScreen = dynamic(
  () =>
    import("@/components/screens/ConfigScreen").then((m) => m.ConfigScreen),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载配置中心..." />,
  }
);

const LogsScreen = dynamic(
  () => import("@/components/screens/LogsScreen").then((m) => m.LogsScreen),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载日志..." />,
  }
);

const ScriptsScreen = dynamic(
  () =>
    import("@/components/screens/ScriptsScreen").then((m) => m.ScriptsScreen),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载脚本..." />,
  }
);

const AdminWorkflowScreen = dynamic(
  () =>
    import("@/components/screens/AdminWorkflowScreen").then(
      (m) => m.AdminWorkflowScreen
    ),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载规则控制面..." />,
  }
);

const AdminTextbookLibraryScreen = dynamic(
  () =>
    import("@/components/screens/AdminTextbookLibraryScreen").then(
      (m) => m.AdminTextbookLibraryScreen
    ),
  {
    ssr: false,
    loading: () => <ScreenLoading label="正在加载教材库管理..." />,
  }
);

const CommandPalette = dynamic(
  () =>
    import("@/components/command-palette/CommandPalette").then(
      (m) => m.CommandPalette
    ),
  {
    ssr: false,
    loading: () => null,
  }
);

export function AppShell() {
  const demoMode = isDemoMode();
  const user = useAppStore((s) => s.user);
  const authReady = useAppStore((s) => s.authReady);
  const screen = useAppStore((s) => s.screen);
  const mobileNavOpen = useAppStore((s) => s.mobileNavOpen);
  const setMobileNavOpen = useAppStore((s) => s.setMobileNavOpen);
  const commandOpen = useAppStore((s) => s.commandOpen);

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
            {screen === "admin-workflow" && <AdminWorkflowScreen />}
            {screen === "admin-textbook-library" && <AdminTextbookLibraryScreen />}
          </PageTransition>
        </main>
        <footer className="mt-auto border-t border-border bg-background/80 px-4 py-4 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-2 text-center sm:flex-row sm:text-left">
            <Logo size={22} showWordmark={false} />
            <p className="t-caption text-muted-foreground">
              山海教育 · AI幼教ProMax可视化工作台 · 真实 API 工作台
            </p>
            {demoMode ? (
              <p className="t-caption text-muted-foreground/70">
                按 ⌘K 打开命令面板 · admin / {DEMO_PASSWORD}
              </p>
            ) : (
              <p className="t-caption text-muted-foreground/70">
                按 ⌘K 打开命令面板
              </p>
            )}
          </div>
        </footer>
      </div>

      {/* 命令面板 */}
      {commandOpen && <CommandPalette />}
    </div>
  );
}

function ScreenLoading({ label }: { label: string }) {
  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <div className="rounded-lg border border-border bg-card p-6 shadow-soft">
        <div className="t-body text-muted-foreground">{label}</div>
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full w-1/3 rounded-full bg-primary/50" />
        </div>
      </div>
    </div>
  );
}
