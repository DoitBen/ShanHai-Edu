"use client";

import * as React from "react";
import { useAppStore } from "@/lib/store";
import { isDemoMode } from "@/lib/demo-mode";
import type { ScreenKey } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { stageDefByKey } from "@/lib/workflow";
import { toast } from "sonner";
import { useTheme } from "next-themes";
import {
  LayoutDashboard,
  FolderPlus,
  Settings,
  ScrollText,
  TerminalSquare,
  FolderKanban,
  Sun,
  Moon,
  Monitor,
  UserRound,
  ShieldCheck,
  CornerDownLeft,
  Search,
  GitBranch,
  Images,
} from "lucide-react";
import { cn } from "@/lib/utils";

type CommandItemDef = {
  id: string;
  label: string;
  desc?: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  group: string;
  run: () => void;
  keywords?: string;
};

export function CommandPalette() {
  const open = useAppStore((s) => s.commandOpen);
  const setOpen = useAppStore((s) => s.setCommandOpen);
  const go = useAppStore((s) => s.go);
  const openProject = useAppStore((s) => s.openProject);
  const projects = useAppStore((s) => s.projects);
  const user = useAppStore((s) => s.user);
  const switchRole = useAppStore((s) => s.switchRole);
  const logout = useAppStore((s) => s.logout);
  const { setTheme } = useTheme();

  const isAdmin = user?.role === "admin";
  const demoMode = isDemoMode();

  const items = React.useMemo<CommandItemDef[]>(() => {
    const navItems: CommandItemDef[] = [
      {
        id: "nav-dashboard",
        label: "前往首页",
        icon: LayoutDashboard,
        shortcut: "G D",
        group: "导航",
        run: () => go("dashboard"),
        keywords: "首页 工作台 dashboard home",
      },
      {
        id: "nav-new",
        label: "新建项目",
        icon: FolderPlus,
        shortcut: "G N",
        group: "导航",
        run: () => go("new-project"),
        keywords: "新建 创建 项目 new create",
      },
    ];
    if (isAdmin) {
      navItems.push(
        {
          id: "nav-config",
          label: "配置中心",
          icon: Settings,
          group: "导航",
          run: () => go("config"),
          keywords: "配置 设置 模型 密钥 config settings",
        },
        {
          id: "nav-admin-workflow",
          label: "规则控制面",
          icon: GitBranch,
          group: "导航",
          run: () => go("admin-workflow"),
          keywords: "规则 控制面 工作流 DAG rule workflow control plane",
        },
        {
          id: "nav-admin-media-workbench",
          label: "媒体生成工作台",
          icon: Images,
          group: "导航",
          run: () => go("admin-media-workbench"),
          keywords: "媒体 生成 图片 视频 生图 生视频 image video media workbench",
        },
        {
          id: "nav-logs",
          label: "日志",
          icon: ScrollText,
          group: "导航",
          run: () => go("logs"),
          keywords: "日志 记录 logs",
        },
        {
          id: "nav-scripts",
          label: "脚本",
          icon: TerminalSquare,
          group: "导航",
          run: () => go("scripts"),
          keywords: "脚本 运行 scripts",
        }
      );
    }

    const projectItems: CommandItemDef[] = projects.map((p) => {
      const stage = stageDefByKey(p.currentStage);
      return {
        id: `proj-${p.id}`,
        label: p.name,
        desc: `${p.subject} · ${p.grade} · ${stage?.title || ""}`,
        icon: FolderKanban,
        group: "项目",
        run: () => openProject(p.id),
        keywords: `${p.subject} ${p.grade} ${p.textbookVersion} ${p.lessonType} ${stage?.title || ""}`,
      };
    });

    const themeItems: CommandItemDef[] = [
      {
        id: "theme-light",
        label: "切换到浅色主题",
        icon: Sun,
        group: "外观",
        run: () => setTheme("light"),
        keywords: "浅色 light 主题 theme",
      },
      {
        id: "theme-dark",
        label: "切换到深色主题",
        icon: Moon,
        group: "外观",
        run: () => setTheme("dark"),
        keywords: "深色 暗色 dark 主题 theme",
      },
      {
        id: "theme-system",
        label: "跟随系统主题",
        icon: Monitor,
        group: "外观",
        run: () => setTheme("system"),
        keywords: "系统 跟随 system 主题 theme",
      },
    ];

    const accountItems: CommandItemDef[] = [
      {
        id: "logout",
        label: "退出登录",
        icon: CornerDownLeft,
        group: "账户",
        run: () => {
          void logout();
        },
        keywords: "退出 登出 logout signout",
      },
    ];
    if (demoMode) {
      accountItems.unshift(
        {
          id: "role-admin",
          label: "切换为管理员",
          icon: ShieldCheck,
          group: "账户",
          run: () => {
            switchRole("admin");
            toast.success("已切换为管理员视角");
          },
          keywords: "管理员 admin 角色 role",
        },
        {
          id: "role-teacher",
          label: "切换为教师",
          icon: UserRound,
          group: "账户",
          run: () => {
            switchRole("teacher");
            toast.success("已切换为教师视角");
          },
          keywords: "教师 teacher 角色 role",
        },
      );
    }

    return [...navItems, ...projectItems, ...themeItems, ...accountItems];
  }, [projects, isAdmin, demoMode, go, openProject, setTheme, switchRole, logout]);

  const runItem = (item: CommandItemDef) => {
    setOpen(false);
    // 延迟执行以让 Dialog 先关闭，避免焦点冲突
    setTimeout(() => item.run(), 50);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="overflow-hidden p-0 shadow-lift max-w-[640px] gap-0" aria-describedby={undefined}>
        <DialogTitle className="sr-only">命令面板</DialogTitle>
        <DialogDescription className="sr-only">
          输入关键词搜索导航、项目、外观与账户操作。
        </DialogDescription>
        <Command className="rounded-lg">
          <div className="flex items-center gap-2 border-b border-border px-3">
            <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
            <CommandInput
              placeholder="搜索项目、页面或操作…"
              className="h-12 border-0 focus:ring-0 placeholder:text-muted-foreground/70"
            />
            <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground">
              ESC
            </kbd>
          </div>
          <CommandList className="max-h-[420px] scroll-fine">
            <CommandEmpty>
              <div className="py-8 text-center">
                <div className="t-body text-muted-foreground">未找到匹配项</div>
                <div className="t-caption mt-1 text-muted-foreground/70">
                  试试输入“项目”“首页”“深色”
                </div>
              </div>
            </CommandEmpty>
            <CommandGroup heading="导航">
              {items
                .filter((i) => i.group === "导航")
                .map((item) => (
                  <CommandRow
                    key={item.id}
                    item={item}
                    onSelect={() => runItem(item)}
                  />
                ))}
            </CommandGroup>
            {items.some((i) => i.group === "项目") && (
              <>
                <CommandSeparator />
                <CommandGroup heading="项目">
                  {items
                    .filter((i) => i.group === "项目")
                    .map((item) => (
                      <CommandRow
                        key={item.id}
                        item={item}
                        onSelect={() => runItem(item)}
                      />
                    ))}
                </CommandGroup>
              </>
            )}
            <CommandSeparator />
            <CommandGroup heading="外观">
              {items
                .filter((i) => i.group === "外观")
                .map((item) => (
                  <CommandRow
                    key={item.id}
                    item={item}
                    onSelect={() => runItem(item)}
                  />
                ))}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="账户">
              {items
                .filter((i) => i.group === "账户")
                .map((item) => (
                  <CommandRow
                    key={item.id}
                    item={item}
                    onSelect={() => runItem(item)}
                  />
                ))}
            </CommandGroup>
          </CommandList>
          <div className="flex items-center justify-between border-t border-border bg-muted/30 px-3 py-2">
            <div className="flex items-center gap-3 t-caption text-muted-foreground">
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-4 w-4 items-center justify-center rounded border border-border bg-card font-mono text-[9px]">
                  ↑
                </kbd>
                <kbd className="inline-flex h-4 w-4 items-center justify-center rounded border border-border bg-card font-mono text-[9px]">
                  ↓
                </kbd>
                选择
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-4 items-center justify-center rounded border border-border bg-card font-mono text-[9px]">
                  ↵
                </kbd>
                执行
              </span>
            </div>
            <span className="t-caption text-muted-foreground/70">
              山海教育工作台
            </span>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

function CommandRow({
  item,
  onSelect,
}: {
  item: CommandItemDef;
  onSelect: () => void;
}) {
  const Icon = item.icon;
  return (
    <CommandItem
      value={`${item.label} ${item.desc || ""} ${item.keywords || ""}`}
      onSelect={onSelect}
      className={cn(
        "group flex cursor-pointer items-center gap-3 px-3 py-2.5 aria-selected:bg-accent aria-selected:text-accent-foreground"
      )}
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground group-aria-selected:bg-primary/10 group-aria-selected:text-primary">
        <Icon className="h-3.5 w-3.5" />
      </span>
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="t-body truncate font-medium">{item.label}</span>
        {item.desc && (
          <span className="t-caption truncate text-muted-foreground">
            {item.desc}
          </span>
        )}
      </div>
      {item.shortcut && (
        <CommandShortcut className="hidden sm:inline-flex">
          {item.shortcut}
        </CommandShortcut>
      )}
    </CommandItem>
  );
}
