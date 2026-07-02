"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "@/lib/store";

/**
 * 页面切换动效包装器
 *
 * 根据 store 的 screen 切换做克制的淡入 + 轻微上移（12px）。
 * 遵循设计"克制"原则：时长 240ms，仅 opacity + y，无弹性、无旋转。
 * 避免布局抖动：使用 layout 不依赖，只用初始+进入动画。
 */
export function PageTransition({ children }: { children: React.ReactNode }) {
  const screen = useAppStore((s) => s.screen);
  const activeProjectId = useAppStore((s) => s.activeProjectId);

  // key 由 screen + activeProjectId 组成，确保切换项目工作区时也触发动画
  const key = screen === "project" ? `project-${activeProjectId}` : screen;

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={key}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{
          duration: 0.28,
          ease: [0.16, 1, 0.3, 1],
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
