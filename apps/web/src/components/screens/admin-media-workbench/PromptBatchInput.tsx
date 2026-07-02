"use client";

import { useMemo } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { BATCH_PROMPT_MAX_ROWS } from "./constants";

/**
 * 批量提示词输入（F1）
 *
 * 多行 textarea，每行一个独立提示词。
 * - 提交时父组件按行切分，逐行调用 createImageWorkbenchRun
 * - 用 Promise.allSettled 并发提交
 *
 * 本组件只负责输入与行计数显示，提交逻辑由父组件持有。
 */
export interface PromptBatchInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  /** 单行最大长度（用于显示提示，不做硬截断） */
  maxLineLength?: number;
}

export function PromptBatchInput({
  value,
  onChange,
  disabled,
  maxLineLength = 500,
}: PromptBatchInputProps) {
  const { total, valid, overflow } = useMemo(() => {
    const lines = value.split("\n");
    const trimmed = lines.map((line) => line.trim()).filter(Boolean);
    const overflowed = trimmed.filter((line) => line.length > maxLineLength).length;
    return {
      total: trimmed.length,
      valid: trimmed.length,
      overflow: overflowed,
    };
  }, [value, maxLineLength]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <Label className="t-caption text-muted-foreground">批量提示词（每行一个）</Label>
        <div className="flex items-center gap-3 t-caption text-muted-foreground">
          <span className="tabular-nums">
            {total} / {BATCH_PROMPT_MAX_ROWS} 条
          </span>
          {overflow > 0 && (
            <span className="tabular-nums text-warning">{overflow} 条过长</span>
          )}
        </div>
      </div>
      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="input-pro min-h-[140px] resize-y bg-background font-mono text-[13px] leading-relaxed"
        placeholder={
          "每行一个独立提示词，提交后会并发生成：\n明亮的小学数学课堂，桌面上有彩色计数棒\n水彩风格的数学符号漂浮在白板前\n3D 渲染的几何图形拼图"
        }
      />
      <p className="t-caption text-muted-foreground">
        将并发提交最多 {BATCH_PROMPT_MAX_ROWS} 条任务，结果逐个出现在右侧缩略图区。
      </p>
    </div>
  );
}

/** 工具：将批量输入按行切分为有效提示词数组（去除空行/空白） */
export function splitBatchPrompts(input: string): string[] {
  return input
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, BATCH_PROMPT_MAX_ROWS);
}
