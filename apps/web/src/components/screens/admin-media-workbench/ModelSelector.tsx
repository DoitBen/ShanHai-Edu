"use client";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ModelOption } from "./types";

/**
 * 动态模型选择器 —— 从 `mediaWorkbench.capabilities.image.models[]`
 * 或 `capabilities.video.models[]` 渲染模型列表。
 *
 * 视觉与原 SelectField 一致（input-pro 控件），仅模型来源由父组件
 * 从 capabilities 计算后传入。
 */
export interface ModelSelectorProps {
  label: string;
  value: string;
  models: ModelOption[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
}

export function ModelSelector({ label, value, models, onValueChange, disabled }: ModelSelectorProps) {
  // 兜底：capabilities 未加载时 models 可能为空 —— 显示一个 value 占位，避免 Select 报错
  const items = models.length > 0 ? models : [{ model: value }];
  return (
    <div className="form-field-pro">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger className="input-pro ctrl-md bg-background">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {items.map((item) => (
            <SelectItem key={item.model} value={item.model}>
              {item.model}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

/** 兼容性导出：原 SelectField 同名 API，供质量/张数等静态下拉复用 */
export interface SelectFieldProps {
  label: string;
  value: string;
  values: string[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
}

export function SelectField({ label, value, values, onValueChange, disabled }: SelectFieldProps) {
  return (
    <div className="form-field-pro">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger className="input-pro ctrl-md bg-background">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {values.map((item) => (
            <SelectItem key={item} value={item}>
              {item}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
