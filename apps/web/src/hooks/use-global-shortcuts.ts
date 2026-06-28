"use client";

import { useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import type { ScreenKey } from "@/lib/types";

/**
 * 全局键盘快捷键
 *
 * - ⌘K / Ctrl+K：打开命令面板
 * - g d：首页
 * - g n：新建项目
 * - g c：配置中心（管理员）
 * - g w：规则控制面（管理员）
 * - g m：媒体生成工作台（管理员）
 * - g l：日志（管理员）
 * - g s：脚本（管理员）
 * - g p：当前项目（若有 activeProjectId）
 * - Escape：关闭命令面板 / 移动端抽屉
 *
 * G 序列：按下 g 后 800ms 内按下第二个键触发；超时取消。
 * 在 input/textarea/contenteditable 中输入时不触发（⌘K 除外）。
 */
export function useGlobalShortcuts() {
  const user = useAppStore((s) => s.user);
  const setCommandOpen = useAppStore((s) => s.setCommandOpen);
  const commandOpen = useAppStore((s) => s.commandOpen);
  const go = useAppStore((s) => s.go);
  const openProject = useAppStore((s) => s.openProject);
  const activeProjectId = useAppStore((s) => s.activeProjectId);
  const setMobileNavOpen = useAppStore((s) => s.setMobileNavOpen);

  const gPressedAt = useRef<number>(0);
  const G_TIMEOUT = 800;

  useEffect(() => {
    if (!user) return;

    const isTyping = (target: EventTarget | null): boolean => {
      const el = target as HTMLElement | null;
      if (!el) return false;
      const tag = el.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT")
        return true;
      if (el.isContentEditable) return true;
      return false;
    };

    const handler = (e: KeyboardEvent) => {
      // ⌘K / Ctrl+K 始终生效（即使在输入框）
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen(true);
        return;
      }

      // Escape：关闭命令面板 / 移动端抽屉
      if (e.key === "Escape") {
        if (commandOpen) {
          setCommandOpen(false);
          return;
        }
        if (useAppStore.getState().mobileNavOpen) {
          setMobileNavOpen(false);
          return;
        }
      }

      // 以下快捷键在输入框中不触发
      if (isTyping(e.target)) return;
      // 命令面板打开时不触发导航快捷键
      if (useAppStore.getState().commandOpen) return;
      // 带修饰键的组合不触发
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      const key = e.key.toLowerCase();
      const now = Date.now();

      if (key === "g") {
        gPressedAt.current = now;
        return;
      }

      // G 序列：800ms 内按下第二个键
      if (gPressedAt.current && now - gPressedAt.current < G_TIMEOUT) {
        const isAdmin = user.role === "admin";
        let target: ScreenKey | null = null;
        switch (key) {
          case "d":
            target = "dashboard";
            break;
          case "n":
            target = "new-project";
            break;
          case "c":
            if (isAdmin) target = "config";
            break;
          case "w":
            if (isAdmin) target = "admin-workflow";
            break;
          case "m":
            if (isAdmin) target = "admin-media-workbench";
            break;
          case "l":
            if (isAdmin) target = "logs";
            break;
          case "s":
            if (isAdmin) target = "scripts";
            break;
          case "p":
            // 当前项目
            if (activeProjectId) {
              e.preventDefault();
              openProject(activeProjectId);
            }
            gPressedAt.current = 0;
            return;
        }
        if (target) {
          e.preventDefault();
          go(target);
        }
        gPressedAt.current = 0;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [
    user,
    setCommandOpen,
    commandOpen,
    go,
    openProject,
    activeProjectId,
    setMobileNavOpen,
  ]);
}
