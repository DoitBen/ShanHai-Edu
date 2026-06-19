"use client";

import { useRef, useState, Fragment } from "react";
import { useAppStore } from "@/lib/store";
import { MOCK_TEXTBOOK_PARSE } from "@/lib/mock-data";
import type { NewProjectDraft, VideoIntroType, TextbookParseResult } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Upload,
  FileText,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Save,
  FolderPlus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

/* ----------------- 常量 ----------------- */

const STEPS = [
  { key: 1, title: "基本信息", desc: "项目基础字段" },
  { key: 2, title: "教材上传与内容", desc: "上传与解析" },
  { key: 3, title: "视频设计导入", desc: "用途与方向" },
  { key: 4, title: "PPT 配置", desc: "风格与结构" },
  { key: 5, title: "路径与约束", desc: "输出与安全" },
] as const;

const SUBJECTS = ["数学", "语文", "科学", "英语", "艺术"];
const GRADES = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"];
const VERSIONS = ["人教版", "教科版", "统编版", "苏教版"];
const VOLUMES = ["上册", "下册"];
const LESSON_TYPES = ["新授课", "探究课", "诵读课", "复习课"];

const VIDEO_TYPE_OPTIONS: { value: VideoIntroType; label: string }[] = [
  { value: "science", label: "科普类" },
  { value: "application", label: "应用类" },
  { value: "story", label: "故事类" },
  { value: "suspense", label: "悬念类" },
  { value: "discovery", label: "奇妙发现" },
];

const DURATIONS = ["60秒", "90秒", "120秒"];
const PPT_STYLES = ["清新简约", "童趣插画", "极简文档"];

type StepStatus = "todo" | "current" | "done";

/* ----------------- 主组件 ----------------- */

export function NewProjectScreen() {
  const draft = useAppStore((s) => s.draft);
  const setDraft = useAppStore((s) => s.setDraft);
  const commitDraftToProject = useAppStore((s) => s.commitDraftToProject);
  const openProject = useAppStore((s) => s.openProject);
  const go = useAppStore((s) => s.go);

  const initStep = draft.step && draft.step >= 1 ? draft.step : 1;
  const [currentStep, setCurrentStep] = useState<number>(initStep);
  const [maxStep, setMaxStep] = useState<number>(initStep);
  const [parseConfirmed, setParseConfirmed] = useState<boolean>(false);

  /* 每步校验 */
  const validateStep = (step: number): { ok: boolean; msg?: string } => {
    if (step === 1) {
      if (!draft.name.trim()) return { ok: false, msg: "请填写项目名称" };
      return { ok: true };
    }
    if (step === 2) {
      if (draft.parseStatus !== "done")
        return { ok: false, msg: "请先解析教材并等待结果" };
      if (!parseConfirmed)
        return { ok: false, msg: "请确认教材解析结果后再继续" };
      return { ok: true };
    }
    if (step === 3) {
      if (draft.videoTypes.length === 0)
        return { ok: false, msg: "请至少选择一种视频类型" };
      if (draft.videoCountPerType <= 0)
        return { ok: false, msg: "每类生成数量需大于 0" };
      return { ok: true };
    }
    if (step === 4) {
      if (!draft.pptStyle) return { ok: false, msg: "请选择 PPT 风格" };
      if (draft.pptSlides <= 0) return { ok: false, msg: "PPT 页数需大于 0" };
      return { ok: true };
    }
    if (step === 5) {
      if (!draft.outputPath.trim()) return { ok: false, msg: "请填写输出路径" };
      return { ok: true };
    }
    return { ok: true };
  };

  const stepStatus = (step: number): StepStatus => {
    if (step === currentStep) return "current";
    if (step <= maxStep) return "done";
    return "todo";
  };

  const handleNext = () => {
    const v = validateStep(currentStep);
    if (!v.ok) {
      toast.error(v.msg || "请完善当前步骤");
      return;
    }
    const next = Math.min(5, currentStep + 1);
    setCurrentStep(next);
    setMaxStep((m) => Math.max(m, next));
    setDraft({ step: next });
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handlePrev = () => {
    if (currentStep <= 1) return;
    setCurrentStep(currentStep - 1);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleStepClick = (step: number) => {
    if (step > maxStep) {
      toast.info("请先完成当前步骤");
      return;
    }
    setCurrentStep(step);
  };

  const handleSaveDraft = () => {
    setDraft({ step: currentStep });
    toast.success("草稿已保存");
  };

  const handleCreate = () => {
    for (let i = 1; i <= 5; i++) {
      const v = validateStep(i);
      if (!v.ok) {
        toast.error(`第 ${i} 步：${v.msg}`);
        setCurrentStep(i);
        return;
      }
    }
    const id = commitDraftToProject();
    toast.success("项目已创建，正在进入工作区");
    setParseConfirmed(false);
    setTimeout(() => openProject(id), 220);
  };

  const handleBackToDashboard = () => {
    go("dashboard");
  };

  const currentValidation = validateStep(currentStep);

  return (
    <div className="mx-auto w-full max-w-[1100px] px-4 py-6 lg:px-8 lg:py-8">
      {/* 页头 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">新建项目</div>
          <h1 className="mt-2 t-title">新建项目</h1>
          <p className="mt-2 t-body text-muted-foreground">
            按 5 步工作流配置教学资源生产项目。当前步骤展开，其他步骤折叠为摘要。
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 self-start text-muted-foreground"
          onClick={handleBackToDashboard}
        >
          <ArrowLeft className="h-4 w-4" />
          返回首页
        </Button>
      </div>

      {/* Stepper */}
      <Stepper
        current={currentStep}
        max={maxStep}
        onStepClick={handleStepClick}
      />

      {/* 步骤卡片列表 */}
      <div className="mt-6 space-y-3">
        {STEPS.map((step) => {
          const status = stepStatus(step.key);
          const expanded = step.key === currentStep;
          const clickable = status === "done";
          return (
            <StepCard
              key={step.key}
              step={step.key}
              title={step.title}
              desc={step.desc}
              status={status}
              expanded={expanded}
              summary={getSummary(step.key, draft, parseConfirmed)}
              onToggle={clickable ? () => handleStepClick(step.key) : undefined}
            >
              {expanded && step.key === 1 && (
                <Step1BasicInfo draft={draft} setDraft={setDraft} />
              )}
              {expanded && step.key === 2 && (
                <Step2Textbook
                  draft={draft}
                  setDraft={setDraft}
                  parseConfirmed={parseConfirmed}
                  setParseConfirmed={setParseConfirmed}
                />
              )}
              {expanded && step.key === 3 && (
                <Step3Video draft={draft} setDraft={setDraft} />
              )}
              {expanded && step.key === 4 && (
                <Step4PPT draft={draft} setDraft={setDraft} />
              )}
              {expanded && step.key === 5 && (
                <Step5Constraints draft={draft} setDraft={setDraft} />
              )}
            </StepCard>
          );
        })}
      </div>

      {/* 底部操作栏 */}
      <div className="mt-6 flex flex-col gap-3 rounded-xl border border-border bg-card p-4 shadow-soft sm:flex-row sm:items-center sm:justify-between lg:px-6">
        <div className="t-caption text-muted-foreground">
          步骤 {currentStep} / 5 ·{" "}
          <span
            className={cn(
              currentValidation.ok ? "text-success" : "text-warning"
            )}
          >
            {currentValidation.ok ? "当前步骤已就绪" : "请完善当前步骤"}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="ghost"
            className="gap-1.5"
            onClick={handleSaveDraft}
          >
            <Save className="h-4 w-4" />
            保存草稿
          </Button>
          {currentStep > 1 && (
            <Button
              variant="outline"
              onClick={handlePrev}
              className="gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              上一步
            </Button>
          )}
          {currentStep < 5 ? (
            <Button onClick={handleNext} className="gap-1.5">
              下一步
              <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleCreate} className="gap-1.5">
              <FolderPlus className="h-4 w-4" />
              创建项目
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ----------------- Stepper ----------------- */

function Stepper({
  current,
  max,
  onStepClick,
}: {
  current: number;
  max: number;
  onStepClick: (step: number) => void;
}) {
  return (
    <div className="mt-6 overflow-x-auto scroll-fine">
      <ol className="flex w-max min-w-full items-start">
        {STEPS.map((step, i) => {
          const isCurrent = step.key === current;
          const isDone = step.key <= max && !isCurrent;
          const isLocked = step.key > max;
          const status: StepStatus = isCurrent
            ? "current"
            : isDone
            ? "done"
            : "todo";
          const clickable = !isLocked;
          return (
            <Fragment key={step.key}>
              <li className="flex shrink-0 flex-col items-center gap-2 px-1">
                <button
                  type="button"
                  disabled={!clickable}
                  onClick={() => clickable && onStepClick(step.key)}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-md focus-ring",
                    clickable ? "cursor-pointer" : "cursor-default"
                  )}
                  aria-label={`步骤 ${step.key} ${step.title}`}
                >
                  <StepCircle step={step.key} status={status} />
                  <div className="text-center">
                    <div
                      className={cn(
                        "t-caption font-medium",
                        isCurrent
                          ? "text-foreground"
                          : isDone
                          ? "text-foreground/80"
                          : "text-muted-foreground"
                      )}
                    >
                      {step.title}
                    </div>
                    <div className="hidden t-caption text-muted-foreground/70 sm:block">
                      {step.desc}
                    </div>
                  </div>
                </button>
              </li>
              {i < STEPS.length - 1 && (
                <li
                  aria-hidden
                  className={cn(
                    "mt-[1.125rem] h-px flex-1 self-start",
                    step.key < max ? "bg-primary/40" : "bg-border"
                  )}
                />
              )}
            </Fragment>
          );
        })}
      </ol>
    </div>
  );
}

function StepCircle({ step, status }: { step: number; status: StepStatus }) {
  if (status === "done") {
    return (
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-success/15 text-success ring-1 ring-success/30">
        <Check className="h-4 w-4" />
      </span>
    );
  }
  if (status === "current") {
    return (
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground ring-2 ring-primary/20 ring-offset-2 ring-offset-background">
        {step}
      </span>
    );
  }
  return (
    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground ring-1 ring-border">
      {step}
    </span>
  );
}

/* ----------------- StepCard ----------------- */

function StepCard({
  step,
  title,
  desc,
  status,
  expanded,
  summary,
  onToggle,
  children,
}: {
  step: number;
  title: string;
  desc: string;
  status: StepStatus;
  expanded: boolean;
  summary: string;
  onToggle?: () => void;
  children?: React.ReactNode;
}) {
  return (
    <Card
      className={cn(
        "gap-0 border-border bg-card p-0 shadow-sm",
        expanded && "shadow-soft"
      )}
    >
      <div
        role={onToggle ? "button" : undefined}
        tabIndex={onToggle ? 0 : undefined}
        onClick={onToggle}
        onKeyDown={
          onToggle
            ? (e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onToggle();
                }
              }
            : undefined
        }
        className={cn(
          "flex items-center gap-4 px-6 py-4 lg:px-8",
          onToggle &&
            "cursor-pointer transition-colors hover:bg-muted/30 focus-ring"
        )}
      >
        <StepCircle step={step} status={status} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="t-module">{title}</h3>
            <StepStatusLabel status={status} />
          </div>
          {expanded ? (
            <p className="mt-0.5 t-caption text-muted-foreground">{desc}</p>
          ) : (
            <p className="mt-0.5 t-caption text-muted-foreground line-clamp-1">
              {summary}
            </p>
          )}
        </div>
      </div>
      {expanded && (
        <div className="border-t border-border px-6 py-6 lg:px-8 lg:py-8">
          {children}
        </div>
      )}
    </Card>
  );
}

function StepStatusLabel({ status }: { status: StepStatus }) {
  if (status === "current") {
    return (
      <span className="t-caption rounded bg-primary/10 px-1.5 py-0.5 text-primary">
        进行中
      </span>
    );
  }
  if (status === "done") {
    return (
      <span className="t-caption rounded bg-success/10 px-1.5 py-0.5 text-success">
        已完成
      </span>
    );
  }
  return (
    <span className="t-caption rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
      未开始
    </span>
  );
}

/* ----------------- 公共表单组件 ----------------- */

function FieldLabel({
  children,
  htmlFor,
}: {
  children: React.ReactNode;
  htmlFor?: string;
}) {
  return (
    <Label
      htmlFor={htmlFor}
      className="t-body font-medium text-foreground"
    >
      {children}
    </Label>
  );
}

function SelectBox({
  value,
  onChange,
  options,
  placeholder,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="h-11 w-full bg-card" disabled={disabled}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt} value={opt}>
            {opt}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function FieldGroup({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <FieldLabel htmlFor={htmlFor}>{label}</FieldLabel>
      {children}
    </div>
  );
}

/* ----------------- Step 1 基本信息 ----------------- */

function Step1BasicInfo({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  return (
    <div className="space-y-5">
      <FieldGroup label="项目名称" htmlFor="np-name">
        <Input
          id="np-name"
          value={draft.name}
          onChange={(e) => setDraft({ name: e.target.value })}
          placeholder="如：认识分数——分一分"
          className="h-11 bg-card"
        />
      </FieldGroup>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <FieldGroup label="学科">
          <SelectBox
            value={draft.subject}
            onChange={(v) => setDraft({ subject: v })}
            options={SUBJECTS}
          />
        </FieldGroup>
        <FieldGroup label="年级">
          <SelectBox
            value={draft.grade}
            onChange={(v) => setDraft({ grade: v })}
            options={GRADES}
          />
        </FieldGroup>
        <FieldGroup label="教材版本">
          <SelectBox
            value={draft.textbookVersion}
            onChange={(v) => setDraft({ textbookVersion: v })}
            options={VERSIONS}
          />
        </FieldGroup>
        <FieldGroup label="册次">
          <SelectBox
            value={draft.volume}
            onChange={(v) => setDraft({ volume: v })}
            options={VOLUMES}
          />
        </FieldGroup>
        <FieldGroup label="课型">
          <SelectBox
            value={draft.lessonType}
            onChange={(v) => setDraft({ lessonType: v })}
            options={LESSON_TYPES}
          />
        </FieldGroup>
      </div>
    </div>
  );
}

/* ----------------- Step 2 教材上传与内容 ----------------- */

function Step2Textbook({
  draft,
  setDraft,
  parseConfirmed,
  setParseConfirmed,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
  parseConfirmed: boolean;
  setParseConfirmed: (v: boolean) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const recordFile = (file?: File | null) => {
    if (file) {
      setDraft({ textbookFileName: file.name });
    }
  };

  const handleParse = () => {
    if (draft.parseStatus === "parsing") return;
    setParseConfirmed(false);
    setDraft({ parseStatus: "parsing" });
    window.setTimeout(() => {
      setDraft({
        parseStatus: "done",
        parseResult: MOCK_TEXTBOOK_PARSE,
      });
      toast.success("解析完成");
    }, 1200);
  };

  const handleReset = () => {
    setDraft({ parseStatus: "idle", parseResult: null });
    setParseConfirmed(false);
  };

  const handleConfirm = () => {
    setParseConfirmed(true);
    toast.success("已确认解析结果，可继续下一步");
  };

  return (
    <div className="space-y-6">
      <div className="t-overline text-muted-foreground/70">
        教材上传与内容（整体模块）
      </div>

      {/* 文件上传区 */}
      <div className="space-y-2">
        <FieldLabel>教材文件</FieldLabel>
        <label
          onDragOver={(e) => {
            e.preventDefault();
          }}
          onDrop={(e) => {
            e.preventDefault();
            recordFile(e.dataTransfer.files?.[0]);
          }}
          className="flex cursor-pointer items-center gap-4 rounded-lg border border-dashed border-border bg-muted/30 p-4 transition-colors hover:bg-muted/50 hover:border-primary/30 focus-ring lg:p-5"
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => recordFile(e.target.files?.[0])}
            accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
          />
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground">
            <Upload className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="t-body truncate font-medium">
              {draft.textbookFileName || "点击或拖拽上传教材文件"}
            </div>
            <div className="mt-0.5 t-caption text-muted-foreground">
              支持 PDF / Word / 图片 / 文本，演示环境仅记录文件名
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            tabIndex={-1}
            className="pointer-events-none shrink-0"
            onClick={(e) => {
              e.preventDefault();
              fileInputRef.current?.click();
            }}
          >
            选择文件
          </Button>
        </label>
      </div>

      {/* 教材内容文本框 */}
      <div className="space-y-2">
        <FieldLabel htmlFor="np-content">教材内容</FieldLabel>
        <Textarea
          id="np-content"
          value={draft.textbookContent}
          onChange={(e) => setDraft({ textbookContent: e.target.value })}
          placeholder="可粘贴教材原文、章节要点或课题描述，用于辅助解析…"
          className="min-h-32 bg-card"
        />
        <div className="t-caption text-muted-foreground">
          若已上传文件，可留空；解析将基于文件名生成演示结果。
        </div>
      </div>

      {/* 解析动作行 */}
      <div className="flex flex-wrap items-center gap-3">
        {draft.parseStatus === "idle" && (
          <Button type="button" onClick={handleParse} className="gap-1.5">
            <Sparkles className="h-4 w-4" />
            开始解析
          </Button>
        )}
        {draft.parseStatus === "parsing" && (
          <Button type="button" disabled className="gap-1.5">
            <RefreshCw className="h-4 w-4 animate-spin" />
            解析中…
          </Button>
        )}
        {draft.parseStatus === "done" && (
          <>
            {!parseConfirmed ? (
              <Button
                type="button"
                onClick={handleConfirm}
                className="gap-1.5"
              >
                <Check className="h-4 w-4" />
                确认解析结果
              </Button>
            ) : (
              <span className="inline-flex items-center gap-1.5 t-body text-success">
                <CheckCircle2 className="h-4 w-4" />
                已确认，可进入下一步
              </span>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={handleParse}
              className="gap-1.5"
            >
              <RefreshCw className="h-4 w-4" />
              重新解析
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={handleReset}
              className="gap-1.5 text-muted-foreground"
            >
              重置
            </Button>
          </>
        )}
      </div>

      {/* 解析进度 */}
      {draft.parseStatus === "parsing" && (
        <div className="rounded-lg border border-border bg-muted/30 p-4">
          <div className="flex items-center justify-between">
            <span className="t-body text-muted-foreground">
              正在解析教材结构…
            </span>
            <span className="t-caption text-muted-foreground">约 1 秒</span>
          </div>
          <Progress value={62} className="mt-2 h-1.5 bg-muted" />
        </div>
      )}

      {/* 解析结果预览 */}
      {draft.parseStatus === "done" && draft.parseResult && (
        <ParseResultCard result={draft.parseResult} />
      )}
    </div>
  );
}

function ParseResultCard({ result }: { result: TextbookParseResult }) {
  return (
    <div className="rounded-lg border border-border bg-muted/20 p-5">
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-bronze" />
        <h4 className="t-module">解析结果预览</h4>
      </div>

      <div className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        <MetaField label="学科" value={result.subject} />
        <MetaField label="年级" value={result.grade} />
        <MetaField label="教材版本" value={result.textbookVersion} />
        <MetaField label="册次" value={result.volume} />
      </div>
      <div className="mt-3">
        <MetaField label="课题" value={result.lesson} />
      </div>

      <Separator className="my-4 bg-border" />

      <div>
        <div className="t-caption text-muted-foreground">核心知识点</div>
        <ul className="mt-2 space-y-1.5">
          {result.coreKnowledgePoints.map((p, i) => (
            <li key={i} className="flex items-start gap-2 t-body">
              <span className="mt-1.5 inline-block h-1 w-1 shrink-0 rounded-full bg-bronze" />
              <span>{p}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4">
        <div className="t-caption text-muted-foreground">教学目标摘要</div>
        <p className="mt-1.5 t-body text-foreground/90">
          {result.teachingGoalSummary}
        </p>
      </div>

      <div className="mt-4 grid gap-6 sm:grid-cols-2">
        <div>
          <div className="t-caption text-muted-foreground">教学重点</div>
          <ul className="mt-2 space-y-1.5">
            {result.keyPoints.map((p, i) => (
              <li key={i} className="flex items-start gap-2 t-body">
                <span className="mt-1.5 inline-block h-1 w-1 shrink-0 rounded-full bg-success" />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="t-caption text-muted-foreground">教学难点</div>
          <ul className="mt-2 space-y-1.5">
            {result.difficulties.map((p, i) => (
              <li key={i} className="flex items-start gap-2 t-body">
                <span className="mt-1.5 inline-block h-1 w-1 shrink-0 rounded-full bg-warning" />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="t-caption text-muted-foreground">{label}</div>
      <div className="mt-0.5 t-body font-medium">{value}</div>
    </div>
  );
}

/* ----------------- Step 3 视频设计导入 ----------------- */

function Step3Video({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  const toggleType = (t: VideoIntroType) => {
    if (draft.videoTypes.includes(t)) {
      setDraft({ videoTypes: draft.videoTypes.filter((x) => x !== t) });
    } else {
      setDraft({ videoTypes: [...draft.videoTypes, t] });
    }
  };

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <FieldGroup label="视频用途">
          <SelectBox
            value={draft.videoPurpose}
            onChange={(v) => setDraft({ videoPurpose: v })}
            options={["课堂导入"]}
          />
        </FieldGroup>
        <FieldGroup label="预计时长">
          <SelectBox
            value={draft.duration}
            onChange={(v) => setDraft({ duration: v })}
            options={DURATIONS}
          />
        </FieldGroup>
      </div>

      <div className="space-y-2">
        <FieldLabel>视频类型（可多选）</FieldLabel>
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
          {VIDEO_TYPE_OPTIONS.map((opt) => {
            const checked = draft.videoTypes.includes(opt.value);
            return (
              <label
                key={opt.value}
                className={cn(
                  "flex cursor-pointer items-center gap-2.5 rounded-lg border bg-card px-3 py-2.5 transition-colors focus-ring",
                  checked
                    ? "border-primary/40 ring-1 ring-primary/15"
                    : "border-border hover:bg-muted/30"
                )}
              >
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => toggleType(opt.value)}
                />
                <span className="t-body">{opt.label}</span>
              </label>
            );
          })}
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <FieldGroup label="每类生成数量" htmlFor="np-count">
          <Input
            id="np-count"
            type="number"
            min={1}
            max={10}
            value={draft.videoCountPerType}
            onChange={(e) =>
              setDraft({ videoCountPerType: Number(e.target.value) || 0 })
            }
            className="h-11 bg-card"
          />
        </FieldGroup>
        <FieldGroup label="视频主题初始方向" htmlFor="np-theme">
          <Input
            id="np-theme"
            value={draft.videoTheme}
            onChange={(e) => setDraft({ videoTheme: e.target.value })}
            placeholder="如：分披萨里的分数"
            className="h-11 bg-card"
          />
        </FieldGroup>
        <FieldGroup label="目标受众" htmlFor="np-audience">
          <Input
            id="np-audience"
            value={draft.audience}
            onChange={(e) => setDraft({ audience: e.target.value })}
            placeholder="如：三年级学生"
            className="h-11 bg-card"
          />
        </FieldGroup>
      </div>

      <div className="space-y-2">
        <FieldLabel htmlFor="np-brief">创意要求</FieldLabel>
        <Textarea
          id="np-brief"
          value={draft.creativeBrief}
          onChange={(e) => setDraft({ creativeBrief: e.target.value })}
          placeholder="如：贴近生活、悬念引入、不直接给出答案…"
          className="min-h-24 bg-card"
        />
      </div>

      <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
        <div className="t-caption text-muted-foreground">
          术语提示：本流程使用「课程锚点」与「课堂落点问题」作为视频方案的固定术语，将在视频剧本阶段生成。
        </div>
      </div>
    </div>
  );
}

/* ----------------- Step 4 PPT 配置 ----------------- */

function Step4PPT({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-3">
        <FieldGroup label="PPT 风格">
          <SelectBox
            value={draft.pptStyle}
            onChange={(v) => setDraft({ pptStyle: v })}
            options={PPT_STYLES}
          />
        </FieldGroup>
        <FieldGroup label="页数" htmlFor="np-slides">
          <Input
            id="np-slides"
            type="number"
            min={1}
            max={60}
            value={draft.pptSlides}
            onChange={(e) =>
              setDraft({ pptSlides: Number(e.target.value) || 0 })
            }
            className="h-11 bg-card"
          />
        </FieldGroup>
        <FieldGroup label="结构" htmlFor="np-structure">
          <Input
            id="np-structure"
            value={draft.pptStructure}
            onChange={(e) => setDraft({ pptStructure: e.target.value })}
            placeholder="如：导入-探究-归纳-练习-小结"
            className="h-11 bg-card"
          />
        </FieldGroup>
      </div>
      <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
        <div className="t-caption text-muted-foreground">
          PPT 方案将在后续「PPT 方案」工作流节点中基于本步骤配置生成，可再行确认与调整。
        </div>
      </div>
    </div>
  );
}

/* ----------------- Step 5 路径与约束 ----------------- */

function Step5Constraints({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <FieldGroup label="输出路径" htmlFor="np-output">
          <Input
            id="np-output"
            value={draft.outputPath}
            onChange={(e) => setDraft({ outputPath: e.target.value })}
            placeholder="/output/"
            className="h-11 bg-card font-mono text-[0.8rem]"
          />
        </FieldGroup>
        <div className="space-y-2">
          <FieldLabel>安全模式</FieldLabel>
          <label className="flex w-full cursor-pointer items-center justify-between gap-4 rounded-lg border border-border bg-card px-4 py-2.5 transition-colors hover:bg-muted/30 focus-ring">
            <div className="min-w-0">
              <div className="t-body font-medium">开启安全模式</div>
              <div className="t-caption text-muted-foreground">
                限制外部资源访问与脚本执行范围
              </div>
            </div>
            <Switch
              checked={draft.safeMode}
              onCheckedChange={(v) => setDraft({ safeMode: v })}
            />
          </label>
        </div>
      </div>

      <div className="space-y-2">
        <FieldLabel htmlFor="np-constraints">约束说明</FieldLabel>
        <Textarea
          id="np-constraints"
          value={draft.constraints}
          onChange={(e) => setDraft({ constraints: e.target.value })}
          placeholder="如：仅使用本地素材；视频时长不超过 90 秒；PPT 页数控制在 18 页以内…"
          className="min-h-24 bg-card"
        />
      </div>

      <Separator className="bg-border" />

      <ConfigSummary draft={draft} />
    </div>
  );
}

function ConfigSummary({ draft }: { draft: NewProjectDraft }) {
  const videoTypeLabel = draft.videoTypes.length
    ? draft.videoTypes
        .map((t) => VIDEO_TYPE_OPTIONS.find((o) => o.value === t)?.label)
        .filter(Boolean)
        .join("、")
    : "—";
  return (
    <div className="rounded-lg border border-border bg-muted/20 p-5">
      <div className="t-overline text-muted-foreground/70">配置摘要</div>
      <div className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        <SummaryRow label="项目名称" value={draft.name || "未填写"} />
        <SummaryRow
          label="学科 / 年级"
          value={`${draft.subject} · ${draft.grade}`}
        />
        <SummaryRow
          label="教材版本"
          value={`${draft.textbookVersion} ${draft.volume}`}
        />
        <SummaryRow label="课型" value={draft.lessonType} />
        <SummaryRow
          label="课题"
          value={draft.parseResult?.lesson || "—"}
        />
        <SummaryRow label="视频类型" value={videoTypeLabel} />
        <SummaryRow
          label="视频数量"
          value={`${draft.videoCountPerType} 套 / 类`}
        />
        <SummaryRow label="预计时长" value={draft.duration} />
        <SummaryRow label="PPT 风格" value={draft.pptStyle} />
        <SummaryRow label="PPT 页数" value={`${draft.pptSlides} 页`} />
        <SummaryRow label="PPT 结构" value={draft.pptStructure} />
        <SummaryRow
          label="安全模式"
          value={draft.safeMode ? "开启" : "关闭"}
        />
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="t-caption text-muted-foreground">{label}</span>
      <span className="t-body text-right font-medium">{value}</span>
    </div>
  );
}

/* ----------------- 摘要工具 ----------------- */

function getSummary(
  step: number,
  draft: NewProjectDraft,
  parseConfirmed: boolean
): string {
  if (step === 1) {
    if (!draft.name) return "未填写项目名称";
    return `${draft.name} · ${draft.subject} · ${draft.grade} · ${draft.textbookVersion}${draft.volume} · ${draft.lessonType}`;
  }
  if (step === 2) {
    if (draft.parseStatus === "idle")
      return draft.textbookFileName
        ? `已上传：${draft.textbookFileName}（未解析）`
        : "尚未上传或解析教材";
    if (draft.parseStatus === "parsing") return "正在解析教材结构…";
    if (draft.parseStatus === "done") {
      const lesson = draft.parseResult?.lesson || "解析结果";
      return parseConfirmed ? `已确认：${lesson}` : `已解析：${lesson}（待确认）`;
    }
    return "—";
  }
  if (step === 3) {
    if (draft.videoTypes.length === 0) return "未选择视频类型";
    const labels = draft.videoTypes
      .map((t) => VIDEO_TYPE_OPTIONS.find((o) => o.value === t)?.label)
      .filter(Boolean)
      .join("、");
    return `${labels} · 每类 ${draft.videoCountPerType} 套 · ${draft.duration}`;
  }
  if (step === 4) {
    return `${draft.pptStyle} · ${draft.pptSlides} 页 · ${draft.pptStructure}`;
  }
  if (step === 5) {
    return `输出 ${draft.outputPath} · 安全模式${draft.safeMode ? "开" : "关"}`;
  }
  return "";
}
