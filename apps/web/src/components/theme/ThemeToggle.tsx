"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

type Theme = "light" | "dark" | "system";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  const current = (theme as Theme) || "system";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="切换主题"
          className={cn(
            "inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-all duration-300 ease-apple hover:-translate-y-0.5 hover:bg-muted hover:text-foreground focus-ring",
            className
          )}
        >
          {/* 避免水合不一致：未挂载时显示静态图标 */}
          {!mounted ? (
            <Sun className="h-[18px] w-[18px]" />
          ) : current === "dark" ? (
            <Moon className="h-[18px] w-[18px]" />
          ) : current === "system" ? (
            <Monitor className="h-[18px] w-[18px]" />
          ) : (
            <Sun className="h-[18px] w-[18px]" />
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuLabel className="t-caption text-muted-foreground">
          外观主题
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => setTheme("light")}
          className="gap-2 justify-between"
        >
          <span className="flex items-center gap-2">
            <Sun className="h-4 w-4" /> 浅色
          </span>
          {current === "light" && <span className="text-primary">●</span>}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme("dark")}
          className="gap-2 justify-between"
        >
          <span className="flex items-center gap-2">
            <Moon className="h-4 w-4" /> 深色
          </span>
          {current === "dark" && <span className="text-primary">●</span>}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className="gap-2 justify-between"
        >
          <span className="flex items-center gap-2">
            <Monitor className="h-4 w-4" /> 跟随系统
          </span>
          {current === "system" && <span className="text-primary">●</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
