"use client";

import { useEffect, useRef, useState, Fragment } from "react";
import { useAppStore } from "@/lib/store";
import type {
  NewProjectDraft,
  VideoIntroType,
  TextbookParseResult,
  ApiLessonPlanLibraryItem,
  ApiTextbookLibraryItem,
  ApiTextbookKnowledgePoints,
} from "@/lib/types";
import {
  fetchLessonPlanLibrary,
  fetchLessonPlanLibraryItem,
  fetchTextbookLibrary,
  fetchTextbookKnowledgePoints,
  uploadLessonPlanToLibrary,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
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
  RefreshCw,
  CheckCircle2,
  Save,
  FolderPlus,
  BookOpen,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

/* ----------------- 常量 ----------------- */

const STEPS = [
  { key: 1, title: "选择起点/资料来源", desc: "使用教材库或直接使用教案" },
  { key: 2, title: "确认本课资料", desc: "选择知识点或查看教案摘要" },
  { key: 3, title: "项目信息", desc: "项目名称、课型、目标受众" },
  { key: 4, title: "导入视频偏好", desc: "关键词、时长与创意方向" },
  { key: 5, title: "PPT 草稿模板", desc: "风格、页数与结构模板" },
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

const DURATIONS = ["45秒", "60秒", "90秒", "120秒"];
const PPT_STYLES = ["清新简约", "童趣插画", "极简文档"];
const PPT_STRUCTURE_TEMPLATES = [
  "导入-探究-归纳-练习-小结",
  "情境-问题-操作-表达-应用",
  "复习-新知-例题-练习-总结",
];
const DEFAULT_TEXTBOOK_DISPLAY = "人教版 / 小学数学 / 一年级 / 上册";
const SUGGESTED_KEYWORDS = ["真实生活", "故事感", "悬念导入", "动手操作", "数学表达", "不提前讲结论"];

type StepStatus = "todo" | "current" | "done";

/* ----------------- 主组件 ----------------- */

export function NewProjectScreen() {
  const draft = useAppStore((s) => s.draft);
  const setDraft = useAppStore((s) => s.setDraft);
  const dataMode = useAppStore((s) => s.dataMode);
  const createProjectFromDraft = useAppStore((s) => s.createProjectFromDraft);
  const openProject = useAppStore((s) => s.openProject);
  const go = useAppStore((s) => s.go);

  const initStep = draft.step && draft.step >= 1 ? draft.step : 1;
  const [currentStep, setCurrentStep] = useState<number>(initStep);
  const [maxStep, setMaxStep] = useState<number>(initStep);
  const [creating, setCreating] = useState(false);

  /* 每步校验 */
  const validateStep = (step: number): { ok: boolean; msg?: string } => {
    if (step === 1) {
      if (draft.sourceMode === "lesson-plan") {
        if (!draft.selectedLessonReferenceId && !draft.lessonPlanFileName)
          return { ok: false, msg: "请选择已有教案或上传教案文件" };
        return { ok: true };
      }
      if (!draft.parseResult?.textbookId)
        return { ok: false, msg: "请先从教材库选择教材" };
      return { ok: true };
    }
    if (step === 2) {
      if (draft.sourceMode === "lesson-plan") return { ok: true };
      if (!draft.selectedKnowledgePointId)
        return { ok: false, msg: "请选择课程知识点" };
      return { ok: true };
    }
    if (step === 3) {
      if (!draft.name.trim()) return { ok: false, msg: "请填写项目名称" };
      if (!draft.lessonType) return { ok: false, msg: "请选择课型" };
      if (!draft.audience.trim()) return { ok: false, msg: "请填写目标受众" };
      return { ok: true };
    }
    if (step === 4) {
      if (draft.videoTypes.length === 0)
        return { ok: false, msg: "请至少选择一种视频类型" };
      if (draft.videoCountPerType <= 0)
        return { ok: false, msg: "每类生成数量需大于 0" };
      return { ok: true };
    }
    if (step === 5) {
      if (!draft.pptStyle) return { ok: false, msg: "请选择 PPT 风格" };
      if (draft.pptSlides <= 0) return { ok: false, msg: "PPT 页数需大于 0" };
      if (!draft.pptStructure) return { ok: false, msg: "请选择 PPT 结构模板" };
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

  const handleCreate = async () => {
    if (creating) return;
    for (let i = 1; i <= 5; i++) {
      const v = validateStep(i);
      if (!v.ok) {
        toast.error(`第 ${i} 步：${v.msg}`);
        setCurrentStep(i);
        return;
      }
    }
    setCreating(true);
    try {
      const id = await createProjectFromDraft();
      toast.success("项目已创建，正在进入工作区");
      setTimeout(() => openProject(id), 220);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "项目创建失败");
    } finally {
      setCreating(false);
    }
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
              summary={getSummary(step.key, draft)}
              onToggle={clickable ? () => handleStepClick(step.key) : undefined}
            >
              {expanded && step.key === 1 && (
                <Step1SourceChoice
                  draft={draft}
                  setDraft={setDraft}
                  dataMode={dataMode}
                />
              )}
              {expanded && step.key === 2 && (
                <Step2SourceDetails
                  draft={draft}
                  setDraft={setDraft}
                />
              )}
              {expanded && step.key === 3 && (
                <Step3BasicInfo draft={draft} setDraft={setDraft} />
              )}
              {expanded && step.key === 4 && (
                <Step4Video draft={draft} setDraft={setDraft} />
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
            <Button onClick={handleCreate} className="gap-1.5" disabled={creating}>
              {creating ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <FolderPlus className="h-4 w-4" />
              )}
              {creating ? "创建中" : "创建项目"}
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
  labels,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
  disabled?: boolean;
  labels?: Record<string, string>;
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="h-11 w-full bg-card" disabled={disabled}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt} value={opt}>
            {labels?.[opt] || opt}
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

/* ----------------- Step 3 基本信息与视觉约束 ----------------- */

function Step3BasicInfo({
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
          onChange={(e) => setDraft({ name: e.target.value, nameEdited: true })}
          placeholder="如：人教版一年级上册数学 - 5以内数的认识"
          className="h-11 bg-card"
        />
      </FieldGroup>
      <div className="grid gap-5 sm:grid-cols-2">
        <FieldGroup label="课型">
          <SelectBox
            value={draft.lessonType}
            onChange={(v) => setDraft({ lessonType: v })}
            options={LESSON_TYPES}
          />
        </FieldGroup>
      </div>

      <Separator className="bg-border" />

      <div className="space-y-4">
        <div>
          <div className="t-overline text-muted-foreground/70">
            第 0 步核心配置
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            角色字典、视觉契约和合规红线会作为 PPT 与导入视频的共同上下文。
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          <FieldGroup label="角色字典描述" htmlFor="np-character">
            <Textarea
              id="np-character"
              value={draft.characterProfile}
              onChange={(e) => setDraft({ characterProfile: e.target.value })}
              placeholder="如：主角为非写实卡通学生，锁定服装、发型、配色和多视角描述..."
              className="min-h-28 bg-card"
            />
          </FieldGroup>
          <FieldGroup label="角色安全规则" htmlFor="np-character-safety">
            <Textarea
              id="np-character-safety"
              value={draft.characterSafetyRule}
              onChange={(e) =>
                setDraft({ characterSafetyRule: e.target.value })
              }
              placeholder="如：禁真人、photorealistic、真实课堂实拍感..."
              className="min-h-28 bg-card"
            />
          </FieldGroup>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <FieldGroup label="主配色" htmlFor="np-palette">
            <Input
              id="np-palette"
              value={draft.visualPalette}
              onChange={(e) => setDraft({ visualPalette: e.target.value })}
              placeholder="如：暖纸白、深青灰、古铜金"
              className="h-11 bg-card"
            />
          </FieldGroup>
          <FieldGroup label="视觉风格关键词" htmlFor="np-style-keywords">
            <Input
              id="np-style-keywords"
              value={draft.visualStyleKeywords}
              onChange={(e) =>
                setDraft({ visualStyleKeywords: e.target.value })
              }
              placeholder="如：温润、克制、生活情境"
              className="h-11 bg-card"
            />
          </FieldGroup>
          <FieldGroup label="字体偏好" htmlFor="np-font">
            <Input
              id="np-font"
              value={draft.fontPreference}
              onChange={(e) => setDraft({ fontPreference: e.target.value })}
              placeholder="如：系统无衬线，数学内容可编辑"
              className="h-11 bg-card"
            />
          </FieldGroup>
        </div>

        <FieldGroup label="合规红线" htmlFor="np-compliance">
          <Textarea
            id="np-compliance"
            value={draft.complianceNotes}
            onChange={(e) => setDraft({ complianceNotes: e.target.value })}
            placeholder="如：中文旁白可配置声线、禁英文配音、完整视频必须多分镜拼接、候选不得冒充终版..."
            className="min-h-24 bg-card"
          />
        </FieldGroup>
      </div>
    </div>
  );
}

/* ----------------- Step 1 资料来源 ----------------- */

function Step1SourceChoice({
  draft,
  setDraft,
  dataMode,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
  dataMode: "demo" | "api";
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [libraryItems, setLibraryItems] = useState<ApiTextbookLibraryItem[]>(
    dataMode === "api" ? [] : [demoTextbookItem()],
  );
  const [lessonItems, setLessonItems] = useState<ApiLessonPlanLibraryItem[]>([]);
  const [selectedTextbookId, setSelectedTextbookId] = useState(
    dataMode === "api" ? "" : demoTextbookItem().textbook_id,
  );
  const [selectedLessonId, setSelectedLessonId] = useState("");
  const [libraryStatus, setLibraryStatus] = useState<"idle" | "loading" | "error">(
    dataMode === "api" ? "loading" : "idle",
  );
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [lessonUploadStatus, setLessonUploadStatus] = useState<"idle" | "uploading">("idle");

  useEffect(() => {
    if (dataMode !== "api") {
      return;
    }
    let cancelled = false;
    Promise.all([fetchTextbookLibrary(), fetchLessonPlanLibrary()])
      .then(([library, lessons]) => {
        if (cancelled) return;
        const items = library.textbooks?.length ? library.textbooks : [demoTextbookItem()];
        setLibraryItems(items);
        setLessonItems(lessons.lesson_plans || []);
        setSelectedTextbookId((current) => current || draft.parseResult?.textbookId || items[0]?.textbook_id || "");
        setSelectedLessonId((current) => current || draft.selectedLessonReferenceId || lessons.lesson_plans?.[0]?.lesson_plan_id || "");
        setLibraryStatus("idle");
      })
      .catch((error) => {
        if (cancelled) return;
        setLibraryStatus("error");
        setLibraryError(error instanceof Error ? error.message : "教材库读取失败");
      });
    return () => {
      cancelled = true;
    };
  }, [dataMode, draft.parseResult?.textbookId, draft.selectedLessonReferenceId]);

  const selectedTextbook =
    libraryItems.find((item) => item.textbook_id === selectedTextbookId) ||
    libraryItems[0] ||
    demoTextbookItem();
  const selectedLesson =
    lessonItems.find((item) => item.lesson_plan_id === selectedLessonId) ||
    lessonItems.find((item) => item.lesson_plan_id === draft.selectedLessonReferenceId);

  const chooseSourceMode = (sourceMode: NonNullable<NewProjectDraft["sourceMode"]>) => {
    setDraft({ sourceMode });
  };

  const chooseTextbook = async () => {
    if (!selectedTextbook?.textbook_id) {
      toast.error("请先选择教材");
      return;
    }
    try {
      const knowledge =
        dataMode === "api"
          ? await fetchTextbookKnowledgePoints(selectedTextbook.textbook_id)
          : demoKnowledgePoints(selectedTextbook);
      const parseResult = mapLibraryChoiceToDraftResult(selectedTextbook, knowledge, draft);
      setDraft({
        sourceMode: "textbook-library",
        parseStatus: "done",
        parseError: null,
        parseResult,
        textbookFileName: `教材库：${formatTextbookDisplayName(selectedTextbook)}`,
        selectedKnowledgePointId: parseResult.selectedKnowledgePointId || parseResult.knowledgePoints?.[0]?.id || "",
        selectedAssetKnowledgePointIds: [],
        lessonReferences: [],
      });
      toast.success("已选择教材库资料");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "教材库读取失败");
    }
  };

  const chooseLessonReference = async () => {
    if (!selectedLessonId) {
      toast.error("请先选择教案");
      return;
    }
    const item = lessonItems.find((lesson) => lesson.lesson_plan_id === selectedLessonId);
    setDraft({
      sourceMode: "lesson-plan",
      selectedLessonReferenceId: selectedLessonId,
      lessonPlanSummary: item?.title || "已选择教案",
      lessonReferences: item ? [item] : draft.lessonReferences,
      name: draft.nameEdited ? draft.name : item?.title || draft.name,
    });
    toast.success("已选择教案资料");
  };

  const recordLessonFile = async (file?: File | null) => {
    if (!file) return;
    const isTextLike = /\.(md|markdown|txt)$/i.test(file.name);
    let content = "";
    if (isTextLike) {
      try {
        content = (await file.text()).slice(0, 4000);
      } catch {
        content = "";
      }
    }
    const summary = content
      ? summarizeLessonPlanContent(content)
      : `${file.name} 已选择；Word/PDF 正文将在后续工作区中核对。`;
    let uploaded: ApiLessonPlanLibraryItem | null = null;
    if (dataMode === "api") {
      setLessonUploadStatus("uploading");
      try {
        uploaded = await uploadLessonPlanToLibrary(file, {
          textbook_id: draft.parseResult?.textbookId,
          textbook_version_id: draft.parseResult?.textbookVersionId,
          knowledge_point_id: draft.selectedKnowledgePointId,
          created_by: "teacher-ui",
        });
        setLessonItems((current) => [
          uploaded!,
          ...current.filter((item) => item.lesson_plan_id !== uploaded!.lesson_plan_id),
        ]);
        setSelectedLessonId(uploaded.lesson_plan_id);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "教案上传失败");
        setLessonUploadStatus("idle");
        return;
      }
      setLessonUploadStatus("idle");
    }
    const lessonReferences = draft.lessonReferences || [];
    setDraft({
      sourceMode: "lesson-plan",
      lessonPlanFileName: file.name,
      lessonPlanContent: content,
      lessonPlanSummary: uploaded?.title || summary,
      selectedLessonReferenceId: uploaded?.lesson_plan_id,
      lessonReferences: uploaded
        ? [uploaded, ...lessonReferences.filter((item) => item.lesson_plan_id !== uploaded.lesson_plan_id)]
        : lessonReferences,
      name: draft.nameEdited ? draft.name : uploaded?.title || file.name.replace(/\.[^.]+$/, ""),
    });
    toast.success(dataMode === "api" ? "教案已上传并选为项目起点" : "已选择教案文件");
  };

  const openLessonFilePicker = () => {
    fileInputRef.current?.click();
  };

  const sourceMode = draft.sourceMode || "textbook-library";

  return (
    <div className="space-y-6">
      <div className="t-overline text-muted-foreground/70">
        选择起点/资料来源
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <SourceModeCard
          title="使用教材库"
          desc="从已管理教材库选择教材、知识点和可选教案参考。"
          active={sourceMode === "textbook-library"}
          icon={<BookOpen className="h-5 w-5" />}
          onClick={() => chooseSourceMode("textbook-library")}
        />
        <SourceModeCard
          title="直接使用教案"
          desc="上传 PDF/Word/Markdown，或从教案库选择已有教案。"
          active={sourceMode === "lesson-plan"}
          icon={<FileText className="h-5 w-5" />}
          onClick={() => chooseSourceMode("lesson-plan")}
        />
      </div>

      {sourceMode === "textbook-library" ? (
        <div className="space-y-4 rounded-lg border border-border bg-card p-4">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <FieldGroup label="教材库">
              <Select
                value={selectedTextbookId || selectedTextbook.textbook_id}
                onValueChange={setSelectedTextbookId}
                disabled={libraryStatus === "loading"}
              >
                <SelectTrigger className="h-11 bg-card">
                  <SelectValue
                    placeholder={libraryStatus === "loading" ? "正在读取教材库..." : DEFAULT_TEXTBOOK_DISPLAY}
                  />
                </SelectTrigger>
                <SelectContent>
                  {(libraryItems.length ? libraryItems : [demoTextbookItem()]).map((item) => (
                    <SelectItem key={item.textbook_id} value={item.textbook_id}>
                      {formatTextbookDisplayName(item)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="mt-1 t-caption text-muted-foreground">
                只选择已管理教材，不在教师新建项目页做后台加工。
              </div>
            </FieldGroup>
            <Button
              type="button"
              variant="outline"
              onClick={chooseTextbook}
              className="gap-1.5"
              disabled={libraryStatus === "loading"}
            >
              <CheckCircle2 className="h-4 w-4" />
              使用这本教材
            </Button>
          </div>
          {libraryStatus === "error" && (
            <div className="rounded-md border border-warning/25 bg-warning/5 px-3 py-2 t-caption text-warning">
              {libraryError || "教材库读取失败"}
            </div>
          )}
          <div className="rounded-md border border-border bg-muted/20 p-3">
            <div className="t-caption text-muted-foreground">当前教材</div>
            <div className="mt-1 t-body font-medium">
              {draft.parseResult?.textbookTitle || formatTextbookDisplayName(selectedTextbook)}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4 rounded-lg border border-border bg-card p-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2">
              <FieldLabel>从教案库选择</FieldLabel>
              <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <Select
                  value={selectedLessonId}
                  onValueChange={setSelectedLessonId}
                  disabled={libraryStatus === "loading" || lessonItems.length === 0}
                >
                  <SelectTrigger className="h-11 bg-card">
                    <SelectValue placeholder={lessonItems.length ? "请选择已有教案" : "暂无可选教案"} />
                  </SelectTrigger>
                  <SelectContent>
                    {lessonItems.map((item) => (
                      <SelectItem key={item.lesson_plan_id} value={item.lesson_plan_id}>
                        {item.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button type="button" variant="outline" onClick={chooseLessonReference} disabled={!selectedLessonId}>
                  选择教案
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <FieldLabel>上传教案文件</FieldLabel>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => void recordLessonFile(e.target.files?.[0])}
                accept=".pdf,.doc,.docx,.md,.markdown,.txt"
              />
              <button
                type="button"
                onClick={openLessonFilePicker}
                disabled={lessonUploadStatus === "uploading"}
                className="flex min-h-11 w-full items-center gap-3 rounded-md border border-dashed border-border bg-muted/20 px-3 py-2 text-left transition-colors hover:bg-muted/40 focus-ring"
              >
                <Upload className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="min-w-0">
                  <span className="block truncate t-body font-medium">
                    {lessonUploadStatus === "uploading"
                      ? "正在上传教案"
                      : draft.lessonPlanFileName || "选择 PDF、Word 或 Markdown"}
                  </span>
                  <span className="block t-caption text-muted-foreground">
                    基于教案进入下一步，不要求教材确认。
                  </span>
                </span>
              </button>
            </div>
          </div>

          {(draft.lessonPlanSummary || selectedLesson) && (
            <div className="rounded-md border border-border bg-muted/20 p-3">
              <div className="t-caption text-muted-foreground">已选教案摘要</div>
              <div className="mt-1 t-body font-medium">
                {draft.lessonPlanSummary || selectedLesson?.title}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SourceModeCard({
  title,
  desc,
  active,
  icon,
  onClick,
}: {
  title: string;
  desc: string;
  active: boolean;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex min-h-28 items-start gap-3 rounded-lg border bg-card p-4 text-left transition-colors focus-ring",
        active ? "border-primary/45 ring-1 ring-primary/15" : "border-border hover:bg-muted/30",
      )}
    >
      <span
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-md border",
          active ? "border-primary/30 bg-primary/10 text-primary" : "border-border bg-muted/30 text-muted-foreground",
        )}
      >
        {icon}
      </span>
      <span>
        <span className="block t-module">{title}</span>
        <span className="mt-1 block t-caption leading-relaxed text-muted-foreground">
          {desc}
        </span>
      </span>
    </button>
  );
}

/* ----------------- Step 2 资料确认 ----------------- */

function Step2SourceDetails({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  if ((draft.sourceMode || "textbook-library") === "lesson-plan") {
    return <LessonPlanSourceSummary draft={draft} setDraft={setDraft} />;
  }

  if (!draft.parseResult) {
    return (
      <div className="rounded-lg border border-warning/25 bg-warning/5 px-4 py-3 t-body text-warning">
        请先在第一步选择教材库资料。
      </div>
    );
  }

  return <TextbookLibrarySourceSummary draft={draft} setDraft={setDraft} />;
}

function TextbookLibrarySourceSummary({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  const result = draft.parseResult;
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);
  const [lessonOpen, setLessonOpen] = useState(false);
  const [lessonDetail, setLessonDetail] = useState<ApiLessonPlanLibraryItem | null>(null);
  const [lessonLoading, setLessonLoading] = useState(false);
  const selectedPoint = result?.knowledgePoints?.find(
    (point) => point.id === (draft.selectedKnowledgePointId || result?.selectedKnowledgePointId),
  );

  useEffect(() => {
    if (!result?.textbookId || !draft.selectedKnowledgePointId) return;
    let cancelled = false;
    fetchLessonPlanLibrary({
      textbookId: result.textbookId,
      knowledgePointId: draft.selectedKnowledgePointId,
    })
      .then((library) => {
        if (!cancelled) setDraft({ lessonReferences: library.lesson_plans || [] });
      })
      .catch(() => {
        if (!cancelled) setDraft({ lessonReferences: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [result?.textbookId, draft.selectedKnowledgePointId, setDraft]);

  if (!result) return null;

  const lessonReferences = draft.lessonReferences || [];
  const selectedReference = lessonReferences.find(
    (item) => item.lesson_plan_id === draft.selectedLessonReferenceId,
  );

  const chooseKnowledgePoint = (knowledgePointId: string) => {
    const point = result.knowledgePoints?.find((item) => item.id === knowledgePointId);
    if (!point) return;
    setDraft({
      selectedKnowledgePointId: knowledgePointId,
      parseResult: {
        ...result,
        selectedKnowledgePointId: knowledgePointId,
        lesson: point.title,
        selectedKnowledgePointPages: {
          textbookPages: formatPageRange(point.pageStart, point.pageEnd),
          pdfPages: formatPageRange(point.pdfPageStart, point.pdfPageEnd),
        },
      },
      selectedLessonReferenceId: undefined,
      name: draft.nameEdited ? draft.name : suggestedDraftName(result, point.title),
    });
  };

  const openLessonReference = async (item: ApiLessonPlanLibraryItem) => {
    setLessonOpen(true);
    setLessonLoading(true);
    try {
      setLessonDetail(await fetchLessonPlanLibraryItem(item.lesson_plan_id));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "教案读取失败");
    } finally {
      setLessonLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-muted/20 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="t-module">使用教材库</div>
            <p className="mt-1 t-caption text-muted-foreground">
              已选择：{result.textbookTitle || `${result.textbookVersion} ${result.grade} ${result.volume}`}
            </p>
          </div>
          <span className="rounded-full border border-border bg-card px-2.5 py-1 t-caption text-muted-foreground">
            {result.knowledgePoints?.length || 0} 个知识点
          </span>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <FieldGroup label="选择知识点">
            <Select
              value={draft.selectedKnowledgePointId || result.selectedKnowledgePointId}
              onValueChange={chooseKnowledgePoint}
              disabled={!result.knowledgePoints?.length}
            >
              <SelectTrigger className="h-11 bg-card">
                <SelectValue placeholder="请选择知识点" />
              </SelectTrigger>
              <SelectContent>
                {(result.knowledgePoints || []).map((point) => (
                  <SelectItem key={point.id} value={point.id}>
                    {point.unit ? `${point.unit} / ${point.title}` : point.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FieldGroup>
          <div className="rounded-md border border-border bg-card p-3">
            <div className="t-caption text-muted-foreground">页码范围</div>
            <div className="mt-1 t-body font-medium">
              教材页 {formatPageRange(selectedPoint?.pageStart, selectedPoint?.pageEnd)} / PDF 页{" "}
              {formatPageRange(selectedPoint?.pdfPageStart, selectedPoint?.pdfPageEnd)}
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" className="gap-1.5" onClick={() => setKnowledgeOpen(true)}>
            <BookOpen className="h-4 w-4" />
            查看核心知识点
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="t-module">可选教案参考</div>
            <p className="mt-0.5 t-caption text-muted-foreground">
              可选择一份已有教案作为写作参考；不选也可以继续。
            </p>
          </div>
          {selectedReference && (
            <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 t-caption text-success">
              已选择
            </span>
          )}
        </div>
        {lessonReferences.length ? (
          <div className="mt-3 space-y-2">
            {lessonReferences.slice(0, 3).map((item) => {
              const selected = item.lesson_plan_id === draft.selectedLessonReferenceId;
              return (
                <div key={item.lesson_plan_id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-muted/20 p-3">
                  <div className="min-w-0">
                    <div className="truncate t-body font-medium">{item.title}</div>
                    <div className="mt-1 t-caption text-muted-foreground">
                      {selected ? "已作为参考" : "可作为参考"}
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={() => openLessonReference(item)}>
                      查看教案
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant={selected ? "secondary" : "default"}
                      onClick={() => setDraft({ selectedLessonReferenceId: item.lesson_plan_id })}
                      disabled={selected}
                    >
                      {selected ? "已选择" : "选为参考"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="mt-3 rounded-md border border-border bg-muted/20 p-3 t-body text-muted-foreground">
            暂无同知识点历史教案，可以不选参考继续。
          </div>
        )}
      </div>

      <Dialog open={knowledgeOpen} onOpenChange={setKnowledgeOpen}>
        <DialogContent className="max-h-[86vh] max-w-3xl overflow-auto">
          <DialogHeader>
            <DialogTitle>核心知识点</DialogTitle>
            <DialogDescription>
              用于确认本课内容范围，后续教案和课件会围绕所选知识点展开。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 sm:grid-cols-2">
            <KnowledgeList title="核心知识点" items={selectedPoint?.keywords?.length ? selectedPoint.keywords : result.coreKnowledgePoints} accent="bg-bronze" />
            <KnowledgeList title="教学重点" items={result.keyPoints} accent="bg-success" />
            <KnowledgeList title="教学难点" items={result.difficulties} accent="bg-warning" />
            <KnowledgeList title="课时信息" items={[selectedPoint?.title || result.lesson, selectedPoint?.unit || "未分组"]} accent="bg-primary" />
          </div>
        </DialogContent>
      </Dialog>

      <Sheet open={lessonOpen} onOpenChange={setLessonOpen}>
        <SheetContent side="right" className="w-full overflow-auto p-6 sm:max-w-2xl">
          <SheetHeader>
            <SheetTitle>{lessonDetail?.title || "教案参考"}</SheetTitle>
            <SheetDescription>供本课写作参考，可关闭后继续配置项目。</SheetDescription>
          </SheetHeader>
          <div className="mt-6">
            {lessonLoading ? (
              <div className="rounded-md border border-border bg-muted/30 p-4 t-body text-muted-foreground">
                正在读取教案正文…
              </div>
            ) : (
              <pre className="whitespace-pre-wrap rounded-md bg-muted/50 p-4 font-mono text-xs leading-relaxed text-foreground">
                {lessonDetail?.markdown || "暂无正文。"}
              </pre>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

function LessonPlanSourceSummary({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  const selectedReference = draft.lessonReferences?.find(
    (item) => item.lesson_plan_id === draft.selectedLessonReferenceId,
  );
  const title = draft.lessonPlanFileName || selectedReference?.title || draft.lessonPlanSummary || "已选择教案";
  const summary =
    draft.lessonPlanSummary ||
    selectedReference?.markdown?.slice(0, 220) ||
    "已基于教案资料进入下一步，可继续填写项目名称、视频偏好和 PPT 模板。";

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-border bg-muted/20 p-5">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-bronze" />
          <h4 className="t-module">直接使用教案</h4>
        </div>
        <div className="mt-4 rounded-md border border-border bg-card p-4">
          <div className="t-caption text-muted-foreground">已选/已上传教案摘要</div>
          <div className="mt-1 t-body font-medium">{title}</div>
          <p className="mt-2 t-body leading-relaxed text-foreground/85">{summary}</p>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <FieldGroup label="项目名称" htmlFor="np-name-lesson">
          <Input
            id="np-name-lesson"
            value={draft.name}
            onChange={(e) => setDraft({ name: e.target.value, nameEdited: true })}
            placeholder="如：万以内加法公开课"
            className="h-10 bg-card"
          />
        </FieldGroup>
        <FieldGroup label="课型">
          <SelectBox
            value={draft.lessonType}
            onChange={(lessonType) => setDraft({ lessonType })}
            options={LESSON_TYPES}
          />
        </FieldGroup>
      </div>
    </div>
  );
}

function KnowledgeList({ title, items, accent }: { title: string; items: string[]; accent: string }) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="t-caption font-medium text-muted-foreground">{title}</div>
      <ul className="mt-2 space-y-1.5">
        {items.length ? (
          items.map((item, index) => (
            <li key={`${title}-${index}`} className="flex items-start gap-2 t-body">
              <span className={cn("mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full", accent)} />
              <span>{item}</span>
            </li>
          ))
        ) : (
          <li className="t-body text-muted-foreground">暂无内容</li>
        )}
      </ul>
    </div>
  );
}

function demoTextbookItem(): ApiTextbookLibraryItem {
  return {
    textbook_id: "renjiao-grade1-volume1-2024",
    textbook_version_id: "renjiao-grade1-volume1-2024-v1",
    title: DEFAULT_TEXTBOOK_DISPLAY,
    subject: "math",
    grade: "1",
    textbook_version: "renjiao",
    volume: "shang",
    knowledge_point_count: 3,
  };
}

function demoKnowledgePoints(item: ApiTextbookLibraryItem): ApiTextbookKnowledgePoints {
  return {
    textbook: item,
    textbook_id: item.textbook_id,
    textbook_version_id: item.textbook_version_id,
    knowledge_points: [
      {
        id: "kp-count-within-5",
        title: "5以内数的认识",
        unit: "第一单元",
        page_start: 2,
        page_end: 5,
        pdf_page_start: 4,
        pdf_page_end: 7,
        keywords: ["数数", "数量对应", "数学表达"],
      },
      {
        id: "kp-add-within-10",
        title: "10以内加法",
        unit: "第三单元",
        page_start: 24,
        page_end: 28,
        pdf_page_start: 26,
        pdf_page_end: 30,
        keywords: ["合并", "加法意义", "生活情境"],
      },
    ],
  };
}

function mapLibraryChoiceToDraftResult(
  item: ApiTextbookLibraryItem,
  knowledge: ApiTextbookKnowledgePoints,
  draft: NewProjectDraft,
): NonNullable<NewProjectDraft["parseResult"]> {
  const points = knowledge.knowledge_points.map((point) => ({
    id: point.id,
    title: point.title,
    unit: point.unit,
    pageStart: point.page_start,
    pageEnd: point.page_end,
    pdfPageStart: point.pdf_page_start,
    pdfPageEnd: point.pdf_page_end,
    keywords: point.keywords || [],
    parseStatus: point.parse_status,
    reviewStatus: point.review_status,
    assetPackage: point.asset_package
      ? {
          assetId: point.asset_package.asset_id,
          textbookPages: point.asset_package.textbook_pages,
          pdfPages: point.asset_package.pdf_pages,
          parseStatus: point.asset_package.parse_status,
          reviewStatus: point.asset_package.review_status,
        }
      : undefined,
  }));
  const selected = points[0];
  return {
    source: "api",
    subject: apiLabel(item.subject, { math: "数学", mathematics: "数学" }, draft.subject),
    grade: apiLabel(item.grade, { "1": "一年级", grade1: "一年级", "一年级": "一年级" }, draft.grade),
    textbookVersion: apiLabel(item.textbook_version, { renjiao: "人教版" }, draft.textbookVersion),
    volume: apiLabel(item.volume, { shang: "上册", volume1: "上册", "上册": "上册" }, draft.volume),
    lesson: selected?.title || "请选择知识点",
    coreKnowledgePoints: selected?.keywords?.length ? selected.keywords : ["结合教材目录选择本课知识点"],
    teachingGoalSummary: "根据所选教材库知识点生成教案、课件和导入视频。",
    keyPoints: selected?.keywords?.length ? selected.keywords : ["本课核心概念"],
    difficulties: ["用学生熟悉的情境表达数学关系"],
    textbookTitle: formatTextbookDisplayName(item),
    textbookId: item.textbook_id,
    textbookVersionId: item.textbook_version_id,
    knowledgePoints: points,
    selectedKnowledgePointId: selected?.id || "",
    selectedKnowledgePointPages: {
      textbookPages: formatPageRange(selected?.pageStart, selected?.pageEnd),
      pdfPages: formatPageRange(selected?.pdfPageStart, selected?.pdfPageEnd),
    },
  };
}

function formatPageRange(start?: number, end?: number): string {
  if (!start && !end) return "-";
  if (start && end) return `${start}-${end}`;
  return String(start || end);
}

function summarizeLessonPlanContent(content: string): string {
  const compact = content.replace(/\s+/g, " ").trim();
  return compact.length > 220 ? `${compact.slice(0, 220)}...` : compact || "已选择教案文件。";
}

function suggestedDraftName(result: TextbookParseResult, lesson: string): string {
  return `${result.textbookVersion}${result.grade}${result.volume}${result.subject} - ${lesson}`;
}

/* ----------------- Step 4 视频设计导入 ----------------- */

function Step4Video({
  draft,
  setDraft,
}: {
  draft: NewProjectDraft;
  setDraft: (patch: Partial<NewProjectDraft>) => void;
}) {
  const [customKeyword, setCustomKeyword] = useState("");
  const [customDuration, setCustomDuration] = useState(
    DURATIONS.includes(draft.duration) ? "" : draft.duration,
  );
  const selectedKeywords = parseKeywordTags(draft.creativeBrief);

  const toggleType = (t: VideoIntroType) => {
    if (draft.videoTypes.includes(t)) {
      setDraft({ videoTypes: draft.videoTypes.filter((x) => x !== t) });
    } else {
      setDraft({ videoTypes: [...draft.videoTypes, t] });
    }
  };

  const setKeywordTags = (tags: string[]) => {
    const unique = Array.from(new Set(tags.map((tag) => tag.trim()).filter(Boolean)));
    setDraft({ creativeBrief: unique.join("、") });
  };

  const toggleKeyword = (keyword: string) => {
    setKeywordTags(
      selectedKeywords.includes(keyword)
        ? selectedKeywords.filter((item) => item !== keyword)
        : [...selectedKeywords, keyword],
    );
  };

  const addCustomKeyword = () => {
    const value = customKeyword.trim();
    if (!value) return;
    setKeywordTags([...selectedKeywords, value]);
    setCustomKeyword("");
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
            value={DURATIONS.includes(draft.duration) ? draft.duration : "__custom__"}
            onChange={(v) => {
              if (v === "__custom__") {
                setDraft({ duration: customDuration || "" });
              } else {
                setCustomDuration("");
                setDraft({ duration: v });
              }
            }}
            options={[...DURATIONS, "__custom__"]}
            labels={{ __custom__: "自定义时长" }}
          />
          {!DURATIONS.includes(draft.duration) && (
            <Input
              value={customDuration}
              onChange={(e) => {
                setCustomDuration(e.target.value);
                setDraft({ duration: e.target.value });
              }}
              placeholder="自定义时长，如：75秒"
              className="mt-2 h-10 bg-card"
            />
          )}
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

      <div className="space-y-3">
        <FieldLabel>关键词标签</FieldLabel>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_KEYWORDS.map((keyword) => {
            const selected = selectedKeywords.includes(keyword);
            return (
              <Button
                key={keyword}
                type="button"
                size="sm"
                variant={selected ? "default" : "outline"}
                onClick={() => toggleKeyword(keyword)}
              >
                {keyword}
              </Button>
            );
          })}
        </div>
        <div className="flex gap-2">
          <Input
            value={customKeyword}
            onChange={(e) => setCustomKeyword(e.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addCustomKeyword();
              }
            }}
            placeholder="自定义关键词，如：校园义卖"
            className="h-10 bg-card"
          />
          <Button type="button" variant="outline" onClick={addCustomKeyword}>
            添加
          </Button>
        </div>
        {selectedKeywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {selectedKeywords.map((keyword) => (
              <span key={keyword} className="rounded-full border border-border bg-muted/40 px-2.5 py-1 t-caption">
                {keyword}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
        <div className="t-caption text-muted-foreground">
          术语提示：本流程使用「课程锚点」与「课堂落点问题」作为视频方案的固定术语，将在视频剧本阶段生成。
        </div>
      </div>
    </div>
  );
}

/* ----------------- Step 5 PPT 与输出约束 ----------------- */

function Step5Constraints({
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
        <FieldGroup label="PPT 结构模板">
          <SelectBox
            value={draft.pptStructure}
            onChange={(v) => setDraft({ pptStructure: v })}
            options={PPT_STRUCTURE_TEMPLATES}
          />
        </FieldGroup>
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
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <SummaryGroup
          title="教材"
          rows={[
            ["教材", draft.parseResult?.textbookTitle || `${draft.textbookVersion} ${draft.volume}`],
            ["知识点", draft.parseResult?.lesson || "—"],
            ["学科 / 年级", `${draft.subject} · ${draft.grade}`],
          ]}
        />
        <SummaryGroup
          title="教案"
          rows={[
            ["项目名称", draft.name || "未填写"],
            ["课型", draft.lessonType],
            ["目标受众", draft.audience || "未填写"],
          ]}
        />
        <SummaryGroup
          title="视频"
          rows={[
            ["视频类型", videoTypeLabel],
            ["关键词", draft.creativeBrief || "未选择"],
            ["预计时长", draft.duration],
          ]}
        />
        <SummaryGroup
          title="PPT"
          rows={[
            ["风格", draft.pptStyle],
            ["页数", `${draft.pptSlides} 页`],
            ["结构模板", draft.pptStructure],
          ]}
        />
      </div>
    </div>
  );
}

function SummaryGroup({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="t-caption font-medium text-muted-foreground">{title}</div>
      <div className="mt-2 space-y-1.5">
        {rows.map(([label, value]) => (
          <SummaryRow key={label} label={label} value={value} />
        ))}
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
  draft: NewProjectDraft
): string {
  if (step === 1) {
    if (draft.sourceMode === "lesson-plan") {
      return draft.lessonPlanFileName || draft.lessonPlanSummary || "已选择教案路径";
    }
    if (draft.parseStatus === "idle")
      return draft.textbookFileName
        ? `已选择资料：${draft.textbookFileName}`
        : "尚未选择教材库资料";
    if (draft.parseStatus === "parsing") return "正在读取资料…";
    if (draft.parseStatus === "failed") return draft.parseError || "资料读取失败";
    if (draft.parseStatus === "done") {
      const count = draft.parseResult?.knowledgePoints?.length || 0;
      return `已选择教材库资料：${draft.parseResult?.textbookTitle || draft.textbookFileName || "教材"} · ${count} 个知识点`;
    }
    return "—";
  }
  if (step === 2) {
    if (draft.sourceMode === "lesson-plan") {
      return draft.lessonPlanSummary || draft.lessonPlanFileName || "教案资料已就绪";
    }
    if (draft.parseStatus !== "done") return "等待选择教材库资料";
    const lesson = draft.parseResult?.lesson || "课程知识点";
    return `已选择：${draft.subject} · ${draft.grade} · ${lesson}`;
  }
  if (step === 3) {
    if (!draft.name) return "未填写项目名称";
    return `${draft.name} · ${draft.lessonType} · 角色与视觉契约已配置`;
  }
  if (step === 4) {
    if (draft.videoTypes.length === 0) return "未选择视频类型";
    const labels = draft.videoTypes
      .map((t) => VIDEO_TYPE_OPTIONS.find((o) => o.value === t)?.label)
      .filter(Boolean)
      .join("、");
    return `${labels} · 每类 ${draft.videoCountPerType} 套 · ${draft.duration}`;
  }
  if (step === 5) {
    return `${draft.pptStyle} · ${draft.pptSlides} 页 · ${draft.pptStructure}`;
  }
  return "";
}

function formatTextbookDisplayName(item: ApiTextbookLibraryItem): string {
  if (item.title?.includes(" / ")) return item.title;
  const publisher = apiLabel(item.textbook_version, { renjiao: "人教版" }, item.title || "人教版");
  const subject = apiLabel(item.subject, { math: "小学数学", mathematics: "小学数学" }, "小学数学");
  const grade = apiLabel(item.grade, { "1": "一年级", grade1: "一年级", "一年级": "一年级" }, "一年级");
  const volume = apiLabel(item.volume, { shang: "上册", volume1: "上册", "上册": "上册" }, "上册");
  return `${publisher} / ${subject} / ${grade} / ${volume}`;
}

function formatAssetStatus(parseStatus?: string, reviewStatus?: string): string {
  if (reviewStatus === "approved" || parseStatus === "approved") return "已确认";
  if (parseStatus === "needs_review" || reviewStatus === "needs_review") return "待确认";
  if (parseStatus === "extracting") return "解析中";
  if (parseStatus === "split_ready") return "已切分";
  if (parseStatus === "failed") return "失败";
  if (reviewStatus === "unreviewed") return "未确认";
  return "未切分";
}

function resolveTextbookAssetPreviewUrl(projectId: string | null, path: string): string {
  if (!projectId || !path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  const normalized = normalizeTextbookAssetPath(path);
  if (!normalized) return "";
  return `/api/backend/projects/${encodeURIComponent(projectId)}/files/${normalized
    .split("/")
    .map(encodeURIComponent)
    .join("/")}`;
}

function normalizeTextbookAssetPath(path: string): string {
  const normalized = path.replaceAll("\\", "/").replace(/^\/+/, "");
  const knowledgePointIndex = normalized.indexOf("knowledge-points/");
  if (knowledgePointIndex >= 0) return normalized.slice(knowledgePointIndex);
  const filesIndex = normalized.indexOf("/files/");
  if (filesIndex >= 0) return normalized.slice(filesIndex + "/files/".length);
  return normalized;
}

function apiLabel(value: string | undefined, map: Record<string, string>, fallback: string): string {
  if (!value) return fallback;
  return map[value] || value;
}

function parseKeywordTags(value: string): string[] {
  return value
    .split(/[、,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}
