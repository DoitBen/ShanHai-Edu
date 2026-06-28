"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import {
  fetchVideoCapabilities,
  resolveApiDownloadUrl,
} from "@/lib/api-client";
import { canEditStageInWorkspace } from "@/lib/workspace-capabilities";
import {
  STAGE_DEFS,
  stageDefByKey,
  nextStageKey,
  BRANCH_LABEL,
} from "@/lib/workflow";
import { MOCK_VIDEO_PLANS } from "@/lib/mock-data";
import type {
  ApiPptExport,
  ApiWorkspaceStep,
  ApiWorkspaceSubGate,
  ApiTask,
  DataMode,
  LoadStatus,
  PendingRuleWarning,
  ProjectMeta,
  VideoIntroPlan,
  VideoIntroType,
  VideoCapability,
  VideoModelOption,
  WorkflowStage,
} from "@/lib/types";
import { StatusBadge, ProjectStatusBadge } from "@/components/common/StatusBadge";
import { ToneBadge } from "@/components/common/StatusBadge";
import { EmptyState, LoadingState } from "@/components/common/StateViews";
import { VideoWorkflowCanvas } from "@/components/video-workflow/VideoWorkflowCanvas";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogHeader,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  Loader2,
  AlertTriangle,
  Clock,
  FileText,
  Save,
  RefreshCw,
  Check,
  RotateCcw,
  Star,
  Info,
  AlertCircle,
  Play,
  GitCompare,
  X,
  Download,
  Eye,
  FileJson,
  FileImage,
  FileType2,
  Maximize2,
  Film,
  ListChecks,
  Lock,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

/* ---------------- 常量 ---------------- */

const VIDEO_TYPE_LABEL: Record<VideoIntroType, string> = {
  science: "科普类",
  application: "应用类",
  story: "故事类",
  suspense: "悬念类",
  discovery: "奇妙发现",
  all: "全部类型",
};

const LOG_LEVEL_META = {
  info: { Icon: Info, color: "text-muted-foreground" },
  warn: { Icon: AlertTriangle, color: "text-warning" },
  error: { Icon: AlertCircle, color: "text-destructive" },
  success: { Icon: CheckCircle2, color: "text-success" },
} as const;

type TabKey = "input" | "run" | "result" | "evidence" | "logs";

type UserStepId =
  | "project-info"
  | "textbook-content"
  | "lesson-plan"
  | "intro-video-plan"
  | "ppt-draft"
  | "video-generation"
  | "final-delivery";

type UserStepState = "completed" | "current" | "locked";

type UserWorkspaceStep = {
  id: UserStepId;
  label: string;
  stageKeys: string[];
  goal: string;
  todo: string;
  basis: string;
};

type TextbookContentSummary = {
  title: string;
  pages: string;
  knowledge: string[];
  status: string;
  basis: string;
  markdown: string;
  sliceUrl: string;
};

const SELECTED_ANCHOR_KEY = ["selected", "anchor"].join("_");
const TASK_NODE_KEY = ["node", "id"].join("_") as "node_id";

const USER_WORKSPACE_STEPS: UserWorkspaceStep[] = [
  {
    id: "project-info",
    label: "项目信息",
    stageKeys: ["project-meta", "project-config", "visual-contract", "character-dict"],
    goal: "确认这节公开课的基本信息、风格方向和合规边界。",
    todo: "回看年级、教材、课型、角色与视觉约束是否符合本班公开课。",
    basis: "来自新建项目时填写的项目配置、视觉契约和角色设定。",
  },
  {
    id: "textbook-content",
    label: "教材内容",
    stageKeys: ["textbook-parse"],
    goal: "确认当前课时对应的教材页段、本课要点和解析内容。",
    todo: "检查教材内容是否对应本节课，确认无误后再生成教案。",
    basis: "来自教材库课时资产包、教材页段和教材内容。",
  },
  {
    id: "lesson-plan",
    label: "教案生成",
    stageKeys: ["open-lesson-plan"],
    goal: "生成并修改一版可用于公开课磨课的教案草稿。",
    todo: "在 Markdown 编辑和预览中检查教学目标、流程、提问和板书。",
    basis: "基于已确认的教材内容、课时资产包和可选教案参考。",
  },
  {
    id: "intro-video-plan",
    label: "导入视频方案",
    stageKeys: ["video-design-import"],
    goal: "选择一套有吸引力、又能通过课程锚点回到课堂的导入视频方案。",
    todo: "比较视频主题、吸睛点、课程锚点、课堂落点问题和不提前讲解内容。",
    basis: "基于教案中的导入设计候选和当前课程锚点。",
  },
  {
    id: "ppt-draft",
    label: "PPT 草稿",
    stageKeys: ["ppt-plan", "ppt-script", "ppt-assets", "pptx-generation"],
    goal: "形成公开课 PPT 的结构、逐页脚本、视觉素材和可下载草稿。",
    todo: "检查每页要讲什么、学生做什么、数学内容是否可编辑可核对。",
    basis: "基于教案、PPT 模板结构、视觉契约和角色设定。",
  },
  {
    id: "video-generation",
    label: "视频生成",
    stageKeys: ["video-script", "video-screenplay", "video-assets", "storyboard", "video-generation"],
    goal: "把已选导入方案推进为文稿、分场、素材、分镜和视频任务。",
    todo: "依次检查文稿、分场剧本、资产与首帧、分镜、clip/TTS/合成，不把本地演示文件当真实成片。",
    basis: "基于导入视频方案、课程锚点、素材清单和分镜脚本。",
  },
  {
    id: "final-delivery",
    label: "最终交付",
    stageKeys: ["final-delivery"],
    goal: "整理教案、PPT 草稿、导入视频和最终下载材料。",
    todo: "确认可下载内容齐全，记录还需要带回试讲修改的地方。",
    basis: "基于前面已确认的教案、PPT、视频和生成资产。",
  },
];

/* ============================================================
 * 主组件 —— 项目工作区指挥台
 * ============================================================ */

export function ProjectWorkspaceScreen() {
  const activeProjectId = useAppStore((s) => s.activeProjectId);
  const projects = useAppStore((s) => s.projects);
  const go = useAppStore((s) => s.go);

  const project = projects.find((p) => p.id === activeProjectId);

  if (!project) {
    return <EmptyWorkspace onBack={() => go("dashboard")} />;
  }

  // key={project.id}：切换项目时整个内层组件重挂载，状态自然重置，避免 effect 同步
  return <ProjectWorkspace key={project.id} project={project} />;
}

function EmptyWorkspace({ onBack }: { onBack: () => void }) {
  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <Card className="border-dashed bg-card p-0">
        <EmptyState
          title="未选择项目"
          desc="请先从工作台首页选择一个项目进入工作区。"
          icon={<AlertTriangle className="h-5 w-5" />}
        />
        <div className="flex justify-center pb-8">
          <Button className="gap-2" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            返回首页
          </Button>
        </div>
      </Card>
    </div>
  );
}

function ProjectWorkspace({ project }: { project: ProjectMeta }) {
  const dataMode = useAppStore((s) => s.dataMode);
  const stagesByProject = useAppStore((s) => s.stagesByProject);
  const workspaceByProject = useAppStore((s) => s.workspaceByProject);
  const videoPlansByProject = useAppStore((s) => s.videoPlansByProject);
  const manifestStatus = useAppStore((s) => s.manifestStatusByProject[project.id] || "idle");
  const manifestError = useAppStore((s) => s.manifestErrorByProject[project.id]);
  const nodeStatusByProject = useAppStore((s) => s.nodeStatusByProject);
  const nodeErrorByProject = useAppStore((s) => s.nodeErrorByProject);
  const stageActionStatusByProject = useAppStore((s) => s.stageActionStatusByProject);
  const stageActionErrorByProject = useAppStore((s) => s.stageActionErrorByProject);
  const pendingRuleWarningByProject = useAppStore((s) => s.pendingRuleWarningByProject);
  const tasksByProject = useAppStore((s) => s.tasksByProject);
  const tasksStatusByProject = useAppStore((s) => s.tasksStatusByProject);
  const tasksErrorByProject = useAppStore((s) => s.tasksErrorByProject);
  const loadProjectManifest = useAppStore((s) => s.loadProjectManifest);
  const loadProjectNode = useAppStore((s) => s.loadProjectNode);
  const loadProjectTasks = useAppStore((s) => s.loadProjectTasks);
  const refreshProjectTask = useAppStore((s) => s.refreshProjectTask);
  const retryProjectTask = useAppStore((s) => s.retryProjectTask);
  const generateStage = useAppStore((s) => s.generateStage);
  const approveStageRemote = useAppStore((s) => s.approveStageRemote);
  const editStageRemote = useAppStore((s) => s.editStageRemote);
  const go = useAppStore((s) => s.go);
  const approveStage = useAppStore((s) => s.approveStage);
  const rejectStage = useAppStore((s) => s.rejectStage);
  const runStage = useAppStore((s) => s.runStage);
  const saveStageInput = useAppStore((s) => s.saveStageInput);
  const acceptVideoPlan = useAppStore((s) => s.acceptVideoPlan);
  const submitDeliveryFeedback = useAppStore((s) => s.submitDeliveryFeedback);

  // 订阅最新 project 元信息（progress / currentStage / status 等会随操作更新）
  const liveProject =
    useAppStore((s) => s.projects.find((p) => p.id === project.id)) || project;

  const stages = stagesByProject[project.id] || [];
  const workspace = workspaceByProject[project.id] || null;

  const [selectedKey, setSelectedKey] = useState<string>(project.currentStage);
  const [tab, setTab] = useState<TabKey>("input");
  const [inputDraft, setInputDraft] = useState<string>(
    () => stages.find((s) => s.key === project.currentStage)?.input || "",
  );
  const [resultDraft, setResultDraft] = useState<string>(
    () => stages.find((s) => s.key === project.currentStage)?.result || "",
  );
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [videoCapabilities, setVideoCapabilities] = useState<VideoCapability[]>([]);
  const [videoOption, setVideoOption] = useState<VideoModelOption>({
    provider: "octo",
    model: "omni_flash-10s",
    size: "1280x720",
    mode: "text",
    fullRun: false,
    durationSec: 10,
  });
  const [pptExportStatus, setPptExportStatus] = useState<LoadStatus>("idle");
  const [pptExportError, setPptExportError] = useState<string | null>(null);
  const [pptExportResult, setPptExportResult] = useState<ApiPptExport | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackDraft, setFeedbackDraft] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<LoadStatus>("idle");
  const [ruleOverrideOpen, setRuleOverrideOpen] = useState(false);
  const [ruleOverrideReason, setRuleOverrideReason] = useState("");
  const [selectedUserStepOverride, setSelectedUserStepOverride] = useState<UserStepId | null>(null);

  const selectedStage =
    stages.find((s) => s.key === selectedKey) || stages[0];
  const selectedNodeStatus = selectedStage
    ? nodeStatusByProject[project.id]?.[selectedStage.key] || "idle"
    : "idle";
  const selectedNodeError = selectedStage
    ? nodeErrorByProject[project.id]?.[selectedStage.key]
    : null;
  const selectedActionStatus = selectedStage
    ? stageActionStatusByProject[project.id]?.[selectedStage.key] || "idle"
    : "idle";
  const selectedActionError = selectedStage
    ? stageActionErrorByProject[project.id]?.[selectedStage.key]
    : null;
  const selectedRuleWarning = selectedStage
    ? pendingRuleWarningByProject[project.id]?.[selectedStage.key]
    : null;
  const projectTasks = tasksByProject[project.id] || [];
  const projectTasksStatus = tasksStatusByProject[project.id] || "idle";
  const projectTasksError = tasksErrorByProject[project.id];

  // 按 order 排序的阶段 key 列表（用于键盘 ←/→ 切换）
  const orderedStageKeys = stages
    .slice()
    .sort((a, b) => a.order - b.order)
    .map((s) => s.key);
  const currentIndex = Math.max(
    0,
    orderedStageKeys.indexOf(selectedStage?.key || ""),
  );

  /* ---------- handlers ---------- */
  function goToStageByOffset(offset: number) {
    const next = orderedStageKeys[currentIndex + offset];
    if (next) syncToStage(next);
  }
  function syncToStage(key: string) {
    const newStage = stages.find((s) => s.key === key);
    setSelectedKey(key);
    setTab("input");
    setInputDraft(newStage?.input || "");
    setResultDraft(newStage?.result || "");
    if (dataMode === "api") {
      void loadProjectNode(project.id, key);
    }
  }

  function returnToWorkspaceCurrentStep() {
    setSelectedUserStepOverride(null);
    const currentStepView = findUserStepViewForWorkspaceStep(userStepViews, workspace?.current_step_id);
    const currentStageKey = currentStepView
      ? getDefaultStageKeyForUserStep(currentStepView.step, stages)
      : null;
    if (currentStageKey) {
      syncToStage(currentStageKey);
    }
  }

  function handleSelectStage(key: string) {
    syncToStage(key);
  }

  async function handleSave(text?: string) {
    if (dataMode === "api") {
      if (!selectedStage) return;
      if (!canEditStageInWorkspace(dataMode, selectedStage)) {
        toast.info("当前内容暂不支持在页面内直接修改");
        return;
      }
      const value =
        typeof text === "string"
          ? text
          : resultDraft;
      if (selectedStage.key === "video-design-import") {
        const anchorError = validateIntroSelectionAnchor(value);
        if (anchorError) {
          toast.warning(anchorError);
          setTab("result");
          return;
        }
      }
      if (!value.trim()) {
        toast.warning("请先填写要保存的内容");
        return;
      }
      const payload = selectedStage.key === "open-lesson-plan"
        ? { markdown: value }
        : parseEditableNodeContent(value);
      const res = await editStageRemote(project.id, selectedStage.key, payload);
      if (!res.ok) {
        toast.error(res.msg || "保存到后端失败");
        return;
      }
      toast.success("已保存到后端");
      setResultDraft(value);
      setTab("result");
      return;
    }
    const value = typeof text === "string" ? text : inputDraft;
    saveStageInput(project.id, selectedStage.key, value);
    setInputDraft(value);
    toast.success("已保存");
  }

  async function handleRegenerate() {
    setTab("run");
    if (dataMode === "api") {
      const res = await generateStage(project.id, selectedStage.key, videoOption);
      if (!res.ok) {
        toast.error(res.msg || "节点生成失败");
        return;
      }
      toast.success("后端生成完成，已刷新节点状态");
      const latestStage = useAppStore
        .getState()
        .stagesByProject[project.id]?.find((item) => item.key === selectedStage.key);
      setResultDraft(latestStage?.result || "");
      if (["video-assets", "video-generation"].includes(selectedStage.key)) {
        await loadProjectTasks(project.id);
      }
      setTab("result");
      return;
    }
    runStage(project.id, selectedStage.key);
    toast.info("正在生成...");
  }

  async function handleExportPpt() {
    if (dataMode !== "api") {
      toast.info("当前练习环境不导出正式 PPT，请进入已连接的备课环境后再导出");
      return;
    }
    if (pptExportStatus === "loading") return;

    setPptExportStatus("loading");
    setPptExportError(null);
    try {
      const pptStage = stages.find((stage) => stage.key === "pptx-generation");
      if (!pptStage) {
        throw new Error("还没有找到可生成 PPTX 的步骤，请先刷新备课进度");
      }
      const res = await generateStage(project.id, pptStage.key);
      if (!res.ok) {
        throw new Error(res.msg || "PPTX 文件生成失败");
      }
      const latestStage =
        useAppStore
          .getState()
          .stagesByProject[project.id]?.find((item) => item.key === pptStage.key) || pptStage;
      const result = pptArtifactExportFromStage(latestStage);
      if (!result) {
        throw new Error("PPTX 文件已生成，但暂时缺少下载入口");
      }
      setPptExportResult(result);
      setPptExportStatus("ready");
      toast.success("PPTX 文件已生成，可下载查看");
    } catch (error) {
      const message = error instanceof Error ? error.message : "PPTX 文件生成失败";
      setPptExportResult(null);
      setPptExportStatus("error");
      setPptExportError(message);
      toast.error(message);
    }
  }

  async function handleApproveAndNext() {
    if (dataMode === "api") {
      if (selectedStage?.key === "video-design-import") {
        const value = resultDraft || selectedStage.result;
        const anchorError = validateIntroSelectionAnchor(value);
        if (anchorError) {
          toast.warning(anchorError);
          setTab("result");
          return;
        }
      }
      const res = await approveStageRemote(project.id, selectedStage.key);
      if (!res.ok) {
        const warning = useAppStore
          .getState()
          .pendingRuleWarningByProject[project.id]?.[selectedStage.key];
        if (warning) {
          setRuleOverrideReason("");
          setRuleOverrideOpen(true);
          toast.warning("规则 warning 需要填写 override 原因后确认");
          return;
        }
        toast.error(res.msg || "节点确认失败");
        return;
      }
      toast.success("已确认，备课进度已刷新");
      setSelectedUserStepOverride(null);
      const next = orderedStageKeys[currentIndex + 1];
      if (next) syncToStage(next);
      return;
    }
    approveStage(project.id, selectedStage.key);
    toast.success("已确认，进入下一阶段");
    const next = nextStageKey(selectedStage.key);
    if (next) syncToStage(next);
  }

  async function handleOverrideRuleWarning() {
    if (!selectedStage || !selectedRuleWarning) return;
    const reason = ruleOverrideReason.trim();
    if (!reason) {
      toast.warning("请填写 override 原因");
      return;
    }
    const res = await approveStageRemote(project.id, selectedStage.key, {
      override_warning_rule_ids: selectedRuleWarning.warnings.map((warning) => warning.rule_id),
      override_reason: reason,
    });
    if (!res.ok) {
      toast.error(res.msg || "warning override 确认失败");
      return;
    }
    setRuleOverrideOpen(false);
    setRuleOverrideReason("");
    toast.success("已记录 warning override 并确认通过");
    setSelectedUserStepOverride(null);
    const next = orderedStageKeys[currentIndex + 1];
    if (next) syncToStage(next);
  }

  async function handleRefreshStage() {
    if (dataMode !== "api") {
      toast.info("当前练习环境使用本地状态，无需刷新");
      return;
    }
    setSelectedUserStepOverride(null);
    await loadProjectManifest(project.id);
    if (selectedStage) {
      await loadProjectNode(project.id, selectedStage.key);
      const latestStage = useAppStore
        .getState()
        .stagesByProject[project.id]?.find((item) => item.key === selectedStage.key);
      setResultDraft(latestStage?.result || "");
      if (["video-assets", "video-generation"].includes(selectedStage.key)) {
        await loadProjectTasks(project.id);
      }
    }
    toast.success("已刷新后端状态");
  }

  function handleReject() {
    if (dataMode === "api") {
      toast.info("当前版本暂不支持从页面退回修改");
      return;
    }
    rejectStage(project.id, selectedStage.key);
    setTab("input");
    toast.success("已退回修改");
  }

  function handleNextStep() {
    if (dataMode === "api") {
      setSelectedUserStepOverride(null);
      const next = orderedStageKeys[currentIndex + 1];
      if (next) {
        syncToStage(next);
        toast.success("已切换到下一节点");
      }
      return;
    }
    if (!["approved", "skipped"].includes(selectedStage.status)) {
      approveStage(project.id, selectedStage.key);
    }
    const next = nextStageKey(selectedStage.key);
    if (next) {
      syncToStage(next);
      toast.success("已进入下一步");
    } else {
      toast.success("已是最后阶段");
    }
  }

  function handleAcceptVideoPlan(planId: string) {
    if (dataMode === "api") {
      toast.info("请在方案卡中选择并保存最终导入视频方案");
      return;
    }
    acceptVideoPlan(project.id, planId);
    toast.success("已采纳该方案");
  }

  function handleOpenDeliveryFeedback() {
    setFeedbackDraft("");
    setFeedbackStatus("idle");
    setFeedbackOpen(true);
  }

  async function handleSubmitDeliveryFeedback() {
    if (dataMode !== "api" || feedbackStatus === "loading") return;
    const comment = feedbackDraft.trim();
    if (!comment) {
      toast.warning("请先填写真实反馈内容");
      return;
    }
    setFeedbackStatus("loading");
    const result = await submitDeliveryFeedback(project.id, {
      stage_key: selectedStage?.key || null,
      stage_title: selectedStage?.title || null,
      project_status: liveProject.status,
      progress: liveProject.progress,
      comment,
    });
    setFeedbackStatus(result.ok ? "ready" : "error");
    if (result.ok) {
      setFeedbackDraft("");
      setFeedbackOpen(false);
      toast.success("反馈已写入飞轮");
    } else {
      toast.error(result.msg || "反馈提交失败");
    }
  }

  // 键盘快捷键：←/→ 切换节点，1-5 切换 Tab
  useEffect(() => {
    const isTyping = (target: EventTarget | null): boolean => {
      const el = target as HTMLElement | null;
      if (!el) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
    };
    const handler = (e: KeyboardEvent) => {
      // 对比/预览 Dialog 打开时不触发
      if (compareOpen || previewFile) return;
      if (isTyping(e.target)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToStageByOffset(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToStageByOffset(1);
      } else if (["1", "2", "3", "4", "5"].includes(e.key)) {
        const tabMap: TabKey[] = ["input", "run", "result", "evidence", "logs"];
        const idx = parseInt(e.key, 10) - 1;
        if (idx >= 0 && idx < tabMap.length) {
          e.preventDefault();
          setTab(tabMap[idx]);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentIndex, orderedStageKeys, compareOpen, previewFile]);

  useEffect(() => {
    if (dataMode !== "api") return;
    if (manifestStatus === "idle" || manifestStatus === "error") {
      void loadProjectManifest(project.id);
    }
  }, [dataMode, loadProjectManifest, manifestStatus, project.id]);

  useEffect(() => {
    if (dataMode !== "api" || !selectedStage) return;
    if (selectedNodeStatus === "idle") {
      void loadProjectNode(project.id, selectedStage.key);
    }
  }, [dataMode, loadProjectNode, project.id, selectedNodeStatus, selectedStage]);

  useEffect(() => {
    setSelectedUserStepOverride(null);
  }, [workspace?.current_step_id]);

  useEffect(() => {
    if (dataMode !== "api" || !selectedStage) return;
    if (!["video-assets", "video-generation"].includes(selectedStage.key)) return;
    if (projectTasksStatus === "idle" || projectTasksStatus === "error") {
      void loadProjectTasks(project.id);
    }
  }, [dataMode, loadProjectTasks, project.id, projectTasksStatus, selectedStage]);

  useEffect(() => {
    if (dataMode !== "api" || selectedStage?.key !== "video-design-import") return;
    const lessonPlanStage = stages.find((item) => item.key === "open-lesson-plan");
    if (lessonPlanStage && !lessonPlanStage.result) {
      void loadProjectNode(project.id, lessonPlanStage.key);
    }
  }, [dataMode, loadProjectNode, project.id, selectedStage?.key, stages]);

  useEffect(() => {
    if (dataMode !== "api" || selectedStage?.key !== "storyboard") return;
    for (const dependencyKey of ["video-design-import", "video-script"]) {
      const dependency = stages.find((item) => item.key === dependencyKey);
      if (dependency && !dependency.result) {
        void loadProjectNode(project.id, dependency.key);
      }
    }
  }, [dataMode, loadProjectNode, project.id, selectedStage?.key, stages]);

  useEffect(() => {
    let mounted = true;
    fetchVideoCapabilities()
      .then((data) => {
        if (mounted) setVideoCapabilities(data.models.filter((item) => item.model !== "task-query"));
      })
      .catch(() => {
        if (mounted) setVideoCapabilities([]);
      });
    return () => {
      mounted = false;
    };
  }, []);

  /* ---------- 按钮启用规则 ---------- */
  const status = selectedStage?.status;
  const isFinalVideoStage = selectedStage?.key === "video-generation";
  const isRunning = status === "running" && !isFinalVideoStage;
  const canEditSelectedStage = canEditStageInWorkspace(dataMode, selectedStage);
  const canSave = !!status && status !== "running" && canEditSelectedStage;
  const canRegenerate = !!status && (status !== "running" || isFinalVideoStage);
  const canApprove =
    !!status &&
    ["ready", "pending_confirm", "approved"].includes(status) &&
    !isRunning;
  const canReject =
    !!status && status !== "not_started" && status !== "running";
  const canNext =
    !!status &&
    !["not_started", "input_required", "running"].includes(status);

  const stageDef = stageDefByKey(selectedStage?.key || "");
  const videoPlans =
    dataMode === "demo" ? videoPlansByProject[project.id] || MOCK_VIDEO_PLANS : [];
  const userStepViews =
    buildUserStepViewsFromWorkspace(USER_WORKSPACE_STEPS, workspace, stages) ||
    buildUserStepViews(USER_WORKSPACE_STEPS, stages);
  const explicitOverrideStepView =
    findValidUserStepOverride(userStepViews, selectedUserStepOverride);
  const workspaceCurrentStepView =
    findUserStepViewForWorkspaceStep(userStepViews, workspace?.current_step_id);
  const selectedStepView =
    explicitOverrideStepView ||
    workspaceCurrentStepView ||
    userStepViews.find((step) => step.state === "current") ||
    userStepViews[0];
  const selectedStepStages = selectedStepView
    ? stages.filter((stage) => selectedStepView.step.stageKeys.includes(stage.key))
    : [];
  const selectedStepStageKey = selectedStepView
    ? getDefaultStageKeyForUserStep(
        selectedStepView.step,
        stages,
        explicitOverrideStepView ? selectedStage?.key : undefined,
      )
    : null;
  const selectedStepStage =
    (selectedStepStageKey
      ? stages.find((stage) => stage.key === selectedStepStageKey)
      : undefined) ||
    (selectedStage && selectedStepView?.step.stageKeys.includes(selectedStage.key)
      ? selectedStage
      : undefined) ||
    selectedStepStages[0] ||
    selectedStage;

  useEffect(() => {
    if (selectedUserStepOverride || !workspaceCurrentStepView || !selectedStepStageKey) return;
    if (selectedStage?.key === selectedStepStageKey) return;
    const nextStage = stages.find((stage) => stage.key === selectedStepStageKey);
    setSelectedKey(selectedStepStageKey);
    setTab("input");
    setInputDraft(nextStage?.input || "");
    setResultDraft(nextStage?.result || "");
    if (dataMode === "api") {
      void loadProjectNode(project.id, selectedStepStageKey);
    }
  }, [
    dataMode,
    loadProjectNode,
    project.id,
    selectedStage?.key,
    selectedStepStageKey,
    selectedUserStepOverride,
    workspaceCurrentStepView,
    stages,
  ]);
  const selectedWorkspaceStep = selectedStepView
    ? findWorkspaceStepForUserStep(workspace, selectedStepView.step)
    : undefined;
  const workspaceStepSubGates = selectedWorkspaceStep?.sub_gates || [];
  const selectedStepStatus = selectedStepView?.state || "locked";
  const selectedTaskStage = selectedStepStage;
  const selectedTaskActionStatus = selectedTaskStage
    ? stageActionStatusByProject[project.id]?.[selectedTaskStage.key] || "idle"
    : "idle";
  const selectedTaskNodeStatus = selectedTaskStage
    ? nodeStatusByProject[project.id]?.[selectedTaskStage.key] || "idle"
    : "idle";
  const selectedTaskNodeError = selectedTaskStage
    ? nodeErrorByProject[project.id]?.[selectedTaskStage.key]
    : null;
  const selectedTaskActionError = selectedTaskStage
    ? stageActionErrorByProject[project.id]?.[selectedTaskStage.key]
    : null;
  const isTaskFinalVideoStage = selectedTaskStage?.key === "video-generation";
  const canEditSelectedTaskStage = canEditStageInWorkspace(dataMode, selectedTaskStage);
  const workspaceHeaderCurrentStepLabel = selectedStepView?.step.label;
  const workspaceHeaderNextAction = selectedTaskStage
    ? selectedStepStatus === "completed"
      ? `回看「${selectedStepView?.step.label || selectedTaskStage.title}」`
      : `继续处理「${selectedTaskStage.title}」`
    : undefined;
  const primaryActionLabel = selectedTaskStage
    ? getPrimaryActionLabel(selectedStepStatus, selectedTaskStage, selectedTaskActionStatus, isTaskFinalVideoStage)
    : "";
  const primaryActionDisabled =
    !selectedTaskStage ||
    selectedStepStatus === "locked" ||
    selectedTaskActionStatus === "loading" ||
    (selectedTaskStage.status === "running" && !isTaskFinalVideoStage);

  function handleSelectUserStep(stepId: UserStepId) {
    const target = userStepViews.find((item) => item.step.id === stepId);
    if (!target) return;
    if (target.state === "locked") {
      toast.info(getLockedStepMessage(target, userStepViews));
      return;
    }
    const targetKey = getDefaultStageKeyForUserStep(target.step, stages, selectedStage?.key);
    if (!targetKey) {
      toast.info("这一步还没有可查看内容。");
      return;
    }
    if (target.state === "completed") {
      setSelectedUserStepOverride(target.step.id);
    } else {
      setSelectedUserStepOverride(null);
    }
    syncToStage(targetKey);
  }

  function handlePrimaryTaskAction() {
    if (!selectedTaskStage || selectedStepStatus === "locked") return;
    if (selectedStage?.key !== selectedTaskStage.key) {
      syncToStage(selectedTaskStage.key);
    }
    if (selectedStepStatus === "completed") {
      returnToWorkspaceCurrentStep();
      return;
    }
    if (selectedTaskActionStatus === "loading") return;
    if (!selectedTaskStage.result || selectedTaskStage.status === "not_started") {
      void handleRegenerate();
      return;
    }
    if (selectedTaskStage.status === "input_required") {
      void handleSave();
      return;
    }
    if (selectedTaskStage.status === "running" && isTaskFinalVideoStage) {
      void handleRefreshStage();
      return;
    }
    if (["ready", "pending_confirm", "approved"].includes(selectedTaskStage.status)) {
      void handleApproveAndNext();
      return;
    }
    void handleRegenerate();
  }

  if (dataMode === "api" && (manifestStatus === "idle" || manifestStatus === "loading")) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <WorkspaceHeader
          project={liveProject}
          stages={stages}
          onBack={() => go("dashboard")}
          feedbackStatus={feedbackStatus}
          onSubmitFeedback={dataMode === "api" ? handleOpenDeliveryFeedback : undefined}
          currentStepLabel={workspaceHeaderCurrentStepLabel}
          nextActionOverride={workspaceHeaderNextAction}
        />
        <DeliveryFeedbackDialog
          open={feedbackOpen}
          status={feedbackStatus}
          value={feedbackDraft}
          onOpenChange={setFeedbackOpen}
          onChange={setFeedbackDraft}
          onSubmit={handleSubmitDeliveryFeedback}
        />
        <Card className="mt-6 border-border bg-card p-10">
          <LoadingState label="正在读取备课进度..." />
        </Card>
      </div>
    );
  }

  if (dataMode === "api" && manifestStatus === "error") {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <WorkspaceHeader
          project={liveProject}
          stages={stages}
          onBack={() => go("dashboard")}
          feedbackStatus={feedbackStatus}
          onSubmitFeedback={dataMode === "api" ? handleOpenDeliveryFeedback : undefined}
          currentStepLabel={workspaceHeaderCurrentStepLabel}
          nextActionOverride={workspaceHeaderNextAction}
        />
        <DeliveryFeedbackDialog
          open={feedbackOpen}
          status={feedbackStatus}
          value={feedbackDraft}
          onOpenChange={setFeedbackOpen}
          onChange={setFeedbackDraft}
          onSubmit={handleSubmitDeliveryFeedback}
        />
        <Card className="mt-6 border-dashed bg-card p-10">
          <EmptyState
            title="备课进度读取失败"
            desc={formatUserFacingError(manifestError || "请稍后重试。")}
            icon={<AlertTriangle className="h-5 w-5" />}
          />
          <div className="flex justify-center pb-2">
            <Button className="gap-2" onClick={() => void loadProjectManifest(project.id)}>
              <RefreshCw className="h-4 w-4" />
              重新读取
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (stages.length === 0) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <WorkspaceHeader
          project={liveProject}
          stages={stages}
          onBack={() => go("dashboard")}
          feedbackStatus={feedbackStatus}
          onSubmitFeedback={dataMode === "api" ? handleOpenDeliveryFeedback : undefined}
          currentStepLabel={workspaceHeaderCurrentStepLabel}
          nextActionOverride={workspaceHeaderNextAction}
        />
        <DeliveryFeedbackDialog
          open={feedbackOpen}
          status={feedbackStatus}
          value={feedbackDraft}
          onOpenChange={setFeedbackOpen}
          onChange={setFeedbackDraft}
          onSubmit={handleSubmitDeliveryFeedback}
        />
        <Card className="mt-6 border-dashed bg-card p-10">
          <EmptyState
            title="暂无备课步骤"
            desc="还没有读取到这个项目的备课进度，请稍后刷新。"
            icon={<FileText className="h-5 w-5" />}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* ===== 顶部 Header ===== */}
        <WorkspaceHeader
          project={liveProject}
          stages={stages}
          onBack={() => go("dashboard")}
          feedbackStatus={feedbackStatus}
          onSubmitFeedback={dataMode === "api" ? handleOpenDeliveryFeedback : undefined}
          currentStepLabel={workspaceHeaderCurrentStepLabel}
          nextActionOverride={workspaceHeaderNextAction}
        />

      {/* ===== 用户态备课步骤 ===== */}
      <section className="mt-6">
        <SectionLabel
          index="01"
          title="备课步骤"
          desc="按公开课备课顺序推进：完成的步骤可回看，未解锁的步骤先保持锁定。"
          right={<KeyboardHint keys={["←", "→"]} label="回看已完成步骤" />}
        />
        <Card className="border-border bg-card p-3 shadow-soft">
          <UserStepRail
            steps={userStepViews}
            selectedStepId={selectedStepView?.step.id}
            onSelect={handleSelectUserStep}
          />
        </Card>
      </section>

      {/* ===== 用户态任务卡 ===== */}
      <section className="mt-8">
        <SectionLabel
          index="02"
          title="当前任务"
          desc="只看这一步要做什么、现在需要做什么、当前结果和下一步按钮。"
          right={
            selectedTaskStage ? <StatusBadge status={selectedTaskStage.status} /> : null
          }
        />
        {selectedStepView?.state === "locked" ? (
          <LockedStepCard stepView={selectedStepView} steps={userStepViews} />
        ) : (
          <WorkspaceTaskCard
            dataMode={dataMode}
            projectId={project.id}
            stepView={selectedStepView}
            stepStages={selectedStepStages}
            workspaceStepSubGates={workspaceStepSubGates}
            stage={selectedTaskStage}
            value={resultDraft || selectedTaskStage?.result || ""}
            inputValue={inputDraft}
            lessonPlanResult={stages.find((item) => item.key === "open-lesson-plan")?.result || ""}
            courseAnchor={selectedTaskStage ? resolveCourseAnchorForStage(selectedTaskStage.key, stages) : ""}
            selectedNodeStatus={selectedTaskNodeStatus}
            selectedNodeError={selectedTaskNodeError}
            selectedActionStatus={selectedTaskActionStatus}
            selectedActionError={selectedTaskActionError}
            canEdit={canEditSelectedTaskStage}
            videoPlans={videoPlans}
            compareIds={compareIds}
            projectTasks={projectTasks}
            projectTasksStatus={projectTasksStatus}
            projectTasksError={projectTasksError}
            pptExportStatus={pptExportStatus}
            pptExportError={pptExportError}
            pptExportResult={pptExportResult}
            primaryActionLabel={primaryActionLabel}
            primaryActionDisabled={primaryActionDisabled}
            onChangeResult={setResultDraft}
            onChangeInput={setInputDraft}
            onSave={() => handleSave(resultDraft || selectedTaskStage?.result)}
            onPrimaryAction={handlePrimaryTaskAction}
            onPreview={(file) => setPreviewFile(file)}
            onToggleSelect={(id) =>
              setCompareIds((prev) =>
                prev.includes(id)
                  ? prev.filter((x) => x !== id)
                  : prev.length >= 3
                    ? (toast.warning("最多对比 3 套方案进行对比"), prev)
                    : [...prev, id],
              )
            }
            onAcceptVideoPlan={handleAcceptVideoPlan}
            onCompare={() => {
              if (compareIds.length < 2) {
                toast.warning("请至少选择 2 套方案进行对比");
                return;
              }
              setCompareOpen(true);
            }}
            onRegenerate={handleRegenerate}
            onRefreshTasks={() => void loadProjectTasks(project.id)}
            onRefreshTask={refreshProjectTask}
            onRetryTask={retryProjectTask}
            onExportPpt={() => void handleExportPpt()}
          />
        )}
        <DeveloperDiagnostics
          dataMode={dataMode}
          tab={tab}
          stage={selectedStage}
          inputDraft={inputDraft}
          resultDraft={resultDraft}
          selectedNodeStatus={selectedNodeStatus}
          selectedNodeError={selectedNodeError}
          selectedActionStatus={selectedActionStatus}
          selectedActionError={selectedActionError}
          canSave={canSave}
          canRegenerate={canRegenerate}
          canApprove={canApprove}
          canReject={canReject}
          canNext={canNext}
          isRunning={isRunning}
          isFinalVideoStage={isFinalVideoStage}
          videoPlans={videoPlans}
          compareIds={compareIds}
          stages={stages}
          projectId={project.id}
          projectTasks={projectTasks}
          projectTasksStatus={projectTasksStatus}
          projectTasksError={projectTasksError}
          pptExportStatus={pptExportStatus}
          pptExportError={pptExportError}
          pptExportResult={pptExportResult}
          canEditSelectedStage={canEditSelectedStage}
          videoCapabilities={videoCapabilities}
          videoOption={videoOption}
          onTabChange={setTab}
          onChangeInput={setInputDraft}
          onChangeResult={setResultDraft}
          onSave={() => handleSave()}
          onSaveResult={() => handleSave(resultDraft || selectedStage?.result)}
          onRefresh={handleRefreshStage}
          onRegenerate={handleRegenerate}
          onApprove={handleApproveAndNext}
          onReject={handleReject}
          onNext={handleNextStep}
          onChangeVideoOption={setVideoOption}
          onToggleSelect={(id) =>
            setCompareIds((prev) =>
              prev.includes(id)
                ? prev.filter((x) => x !== id)
                : prev.length >= 3
                  ? (toast.warning("最多对比 3 套方案"), prev)
                  : [...prev, id],
            )
          }
          onAcceptVideoPlan={handleAcceptVideoPlan}
          onCompare={() => {
            if (compareIds.length < 2) {
              toast.warning("请至少选择 2 套方案进行对比");
              return;
            }
            setCompareOpen(true);
          }}
          onPreview={(file) => setPreviewFile(file)}
          onRefreshTasks={() => void loadProjectTasks(project.id)}
          onRefreshTask={refreshProjectTask}
          onRetryTask={retryProjectTask}
          onExportPpt={() => void handleExportPpt()}
        />
      </section>

      {/* 视频方案对比 */}
      <VideoPlanCompareDialog
        open={compareOpen}
        onOpenChange={setCompareOpen}
        plans={videoPlans.filter((p) => compareIds.includes(p.id))}
        onAccept={(id) => {
          handleAcceptVideoPlan(id);
          setCompareOpen(false);
          setCompareIds([]);
        }}
      />

      {/* 证据文件预览 */}
      <EvidencePreviewDialog
        file={previewFile}
        onClose={() => setPreviewFile(null)}
        stageTitle={selectedStage?.title}
      />

      <DeliveryFeedbackDialog
        open={feedbackOpen}
        status={feedbackStatus}
        value={feedbackDraft}
        onOpenChange={setFeedbackOpen}
        onChange={setFeedbackDraft}
        onSubmit={handleSubmitDeliveryFeedback}
      />

      <RuleWarningOverrideDialog
        open={ruleOverrideOpen}
        warning={selectedRuleWarning || null}
        reason={ruleOverrideReason}
        submitting={selectedActionStatus === "loading"}
        onOpenChange={setRuleOverrideOpen}
        onReasonChange={setRuleOverrideReason}
        onSubmit={handleOverrideRuleWarning}
      />

      <div className="h-2" />
    </div>
  );
}

/* ============================================================
 * 子组件
 * ============================================================ */

function SectionLabel({
  index,
  title,
  desc,
  right,
}: {
  index: string;
  title: string;
  desc?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div className="flex items-baseline gap-3">
        <span className="t-overline text-bronze">{index}</span>
        <div>
          <h2 className="t-module">{title}</h2>
          {desc && (
            <p className="mt-0.5 t-caption text-muted-foreground">{desc}</p>
          )}
        </div>
      </div>
      {right}
    </div>
  );
}

function DeliveryFeedbackDialog({
  open,
  status,
  value,
  onOpenChange,
  onChange,
  onSubmit,
}: {
  open: boolean;
  status: LoadStatus;
  value: string;
  onOpenChange: (open: boolean) => void;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const submitting = status === "loading";
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[560px]">
        <DialogHeader>
          <DialogTitle>提交交付反馈</DialogTitle>
          <DialogDescription>
            记录教师真实使用后的体验、问题或下次调整方向。
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="delivery-feedback-comment">反馈内容</Label>
          <Textarea
            id="delivery-feedback-comment"
            value={value}
            disabled={submitting}
            onChange={(event) => onChange(event.target.value)}
            placeholder="例如：课堂导入节奏合适，但第 3 页练习题还需要减少一步提示。"
            className="min-h-32"
          />
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={submitting}
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button type="button" className="gap-2" disabled={submitting} onClick={onSubmit}>
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            提交
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RuleWarningOverrideDialog({
  open,
  warning,
  reason,
  submitting,
  onOpenChange,
  onReasonChange,
  onSubmit,
}: {
  open: boolean;
  warning: PendingRuleWarning | null;
  reason: string;
  submitting: boolean;
  onOpenChange: (open: boolean) => void;
  onReasonChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const warnings = warning?.warnings || [];
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[640px]">
        <DialogHeader>
          <DialogTitle>确认继续</DialogTitle>
          <DialogDescription>
            当前内容有需要注意的地方。填写原因后可以继续确认，系统会保留本次说明。
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[320px] space-y-3 overflow-y-auto pr-1">
          {warnings.map((item) => (
            <div key={item.rule_id} className="rounded-md border border-warning/30 bg-warning/5 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="t-body font-semibold text-warning">{item.rule_id}</span>
                <span className="t-caption text-muted-foreground">{item.severity || "warning"}</span>
              </div>
              {item.message && <p className="mt-2 t-body text-foreground">{item.message}</p>}
              {typeof item.details !== "undefined" && (
                <pre className="mt-2 max-h-28 overflow-auto rounded bg-muted p-2 text-xs text-muted-foreground">
                  {JSON.stringify(item.details, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
        <div className="space-y-2">
          <Label htmlFor="rule-override-reason">继续确认的原因</Label>
          <Textarea
            id="rule-override-reason"
            value={reason}
            disabled={submitting}
            onChange={(event) => onReasonChange(event.target.value)}
            placeholder="说明为什么本次 warning 可接受，例如：内测保留 6 页且已人工确认板书页覆盖。"
            className="min-h-24"
          />
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={submitting}
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button type="button" className="gap-2" disabled={submitting || !reason.trim()} onClick={onSubmit}>
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            提交 override 并确认
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function UserStepRail({
  steps,
  selectedStepId,
  onSelect,
}: {
  steps: UserStepView[];
  selectedStepId?: UserStepId;
  onSelect: (stepId: UserStepId) => void;
}) {
  return (
    <div className="overflow-x-auto scroll-fine pb-1">
      <div className="flex min-w-max items-stretch px-1 py-1">
        {steps.map((item, index) => {
          const selected = item.step.id === selectedStepId;
          const completed = item.state === "completed";
          const locked = item.state === "locked";
          return (
            <div key={item.step.id} className="flex items-stretch">
              <button
                type="button"
                aria-current={selected ? "step" : undefined}
                onClick={() => onSelect(item.step.id)}
                className={cn(
                  "relative flex h-[96px] w-[116px] shrink-0 flex-col items-center justify-center gap-2 rounded-md border px-3 text-center transition-colors focus-ring",
                  selected && "border-primary bg-primary/[0.04] shadow-soft",
                  !selected && completed && "border-transparent hover:bg-success/5",
                  !selected && !completed && !locked && "border-transparent hover:bg-muted/60",
                  locked && "border-transparent bg-muted/25 text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-[0.72rem] font-semibold",
                    completed && "bg-success/15 text-success",
                    item.state === "current" && "bg-primary text-primary-foreground",
                    locked && "bg-muted text-muted-foreground",
                  )}
                >
                  {completed ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : locked ? (
                    <Lock className="h-3.5 w-3.5" />
                  ) : (
                    index + 1
                  )}
                </span>
                <span className={cn("t-caption leading-tight", selected && "font-medium text-foreground")}>
                  {item.step.label}
                </span>
                <span className="t-overline text-[0.55rem] leading-none text-muted-foreground/70">
                  {completed ? "可回看" : item.state === "current" ? "当前步骤" : "未解锁"}
                </span>
              </button>
              {index < steps.length - 1 && (
                <div className="flex w-4 justify-center pt-8">
                  <span className={cn("h-px w-full", completed ? "bg-success/50" : "bg-border")} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LockedStepCard({
  stepView,
  steps,
}: {
  stepView: UserStepView;
  steps: UserStepView[];
}) {
  return (
    <Card className="border-dashed bg-card p-8 text-center shadow-soft">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Lock className="h-5 w-5" />
      </div>
      <h3 className="mt-4 t-module">还不能进入【{stepView.step.label}】</h3>
      <p className="mx-auto mt-2 max-w-xl t-body text-muted-foreground">
        {getLockedStepMessage(stepView, steps)}
      </p>
    </Card>
  );
}

function WorkspaceTaskCard({
  dataMode,
  projectId,
  stepView,
  stepStages,
  workspaceStepSubGates,
  stage,
  value,
  inputValue,
  lessonPlanResult,
  courseAnchor,
  selectedNodeStatus,
  selectedNodeError,
  selectedActionStatus,
  selectedActionError,
  canEdit,
  videoPlans,
  compareIds,
  projectTasks,
  projectTasksStatus,
  projectTasksError,
  pptExportStatus,
  pptExportError,
  pptExportResult,
  primaryActionLabel,
  primaryActionDisabled,
  onChangeResult,
  onChangeInput,
  onSave,
  onPrimaryAction,
  onPreview,
  onToggleSelect,
  onAcceptVideoPlan,
  onCompare,
  onRegenerate,
  onRefreshTasks,
  onRefreshTask,
  onRetryTask,
  onExportPpt,
}: {
  dataMode: DataMode;
  projectId: string;
  stepView?: UserStepView;
  stepStages: WorkflowStage[];
  workspaceStepSubGates: ApiWorkspaceSubGate[];
  stage?: WorkflowStage;
  value: string;
  inputValue: string;
  lessonPlanResult: string;
  courseAnchor: string;
  selectedNodeStatus: "idle" | "loading" | "ready" | "error";
  selectedNodeError?: string | null;
  selectedActionStatus: "idle" | "loading" | "ready" | "error";
  selectedActionError?: string | null;
  canEdit: boolean;
  videoPlans: VideoIntroPlan[];
  compareIds: string[];
  projectTasks: ApiTask[];
  projectTasksStatus: LoadStatus;
  projectTasksError?: string | null;
  pptExportStatus: LoadStatus;
  pptExportError: string | null;
  pptExportResult: ApiPptExport | null;
  primaryActionLabel: string;
  primaryActionDisabled: boolean;
  onChangeResult: (value: string) => void;
  onChangeInput: (value: string) => void;
  onSave: () => void;
  onPrimaryAction: () => void;
  onPreview: (file: string) => void;
  onToggleSelect: (id: string) => void;
  onAcceptVideoPlan: (id: string) => void;
  onCompare: () => void;
  onRegenerate: () => void;
  onRefreshTasks: () => void;
  onRefreshTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onRetryTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onExportPpt: () => void;
}) {
  if (!stepView || !stage) return null;
  const editable = stepView.state === "current" && canEdit;
  const shouldShowOrdinaryEvidence = stepView.step.id !== "final-delivery";
  return (
    <Card className="border-border bg-card p-0 shadow-soft">
      <div className="border-b border-border px-4 py-4 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="t-overline text-muted-foreground/70">{stepView.step.label}</div>
            <h3 className="mt-1 t-module">{stage.title}</h3>
            <p className="mt-1 t-body text-muted-foreground">{stepView.step.goal}</p>
          </div>
          <StatusBadge status={stage.status} />
        </div>
      </div>
      <div className="grid gap-5 p-4 sm:p-6 xl:grid-cols-[0.86fr_1.14fr]">
        <div className="space-y-4">
          <InfoBlock title="这一步要做什么" text={stepView.step.goal} />
          <InfoBlock title="你现在需要做什么" text={stepView.state === "completed" ? "这一步已完成，可以回看配置和内容；需要调整时先评估后续步骤是否要重新确认。" : stepView.step.todo} />
          <InfoBlock title="依据" text={stepView.step.basis} />
          <UserActionNotice
            nodeStatus={selectedNodeStatus}
            nodeError={selectedNodeError}
            actionStatus={selectedActionStatus}
            actionError={selectedActionError}
          />
          <StepStageList stages={stepStages} activeKey={stage.key} />
          {stepView.step.id === "ppt-draft" && (
            <PptDraftSubStatusList stages={stepStages} subGates={workspaceStepSubGates} />
          )}
          {stepView.step.id === "video-generation" && (
            <VideoGenerationSubStatusList stages={stepStages} subGates={workspaceStepSubGates} />
          )}
          {shouldShowOrdinaryEvidence && stage.evidence.length > 0 && (
            <div className="rounded-md border border-border bg-muted/20 p-3">
              <div className="t-caption font-medium text-foreground">可回看的依据材料</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {stage.evidence.slice(0, 4).map((file) => (
                  <Button key={file} type="button" size="sm" variant="outline" onClick={() => onPreview(file)}>
                    查看{getUserEvidenceLabel(file)}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="min-w-0 space-y-4">
          <CurrentResultPanel
            dataMode={dataMode}
            projectId={projectId}
            stage={stage}
            value={value}
            inputValue={inputValue}
            lessonPlanResult={lessonPlanResult}
            courseAnchor={courseAnchor}
            editable={editable}
            saving={selectedActionStatus === "loading"}
            videoPlans={videoPlans}
            compareIds={compareIds}
            projectTasks={projectTasks}
            projectTasksStatus={projectTasksStatus}
            projectTasksError={projectTasksError}
            pptExportStatus={pptExportStatus}
            pptExportError={pptExportError}
            pptExportResult={pptExportResult}
            actionError={selectedActionError}
            onChangeResult={onChangeResult}
            onChangeInput={onChangeInput}
            onSave={onSave}
            onToggleSelect={onToggleSelect}
            onAcceptVideoPlan={onAcceptVideoPlan}
            onCompare={onCompare}
            onRegenerate={onRegenerate}
            onRefreshTasks={onRefreshTasks}
            onRefreshTask={onRefreshTask}
            onRetryTask={onRetryTask}
            onExportPpt={onExportPpt}
          />
          <div className="flex justify-end border-t border-border pt-4">
            <Button className="gap-2" disabled={primaryActionDisabled} onClick={onPrimaryAction}>
              {selectedActionStatus === "loading" || stage.status === "running" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
              {primaryActionLabel}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function InfoBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-3">
      <div className="t-caption font-medium text-foreground">{title}</div>
      <p className="mt-1 t-body text-muted-foreground">{text}</p>
    </div>
  );
}

function StepStageList({ stages, activeKey }: { stages: WorkflowStage[]; activeKey: string }) {
  if (stages.length <= 1) return null;
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="t-caption font-medium text-foreground">本步骤包含的内容</div>
      <div className="mt-2 grid gap-1.5">
        {stages.map((stage) => (
          <div key={stage.key} className={cn("flex items-center justify-between gap-3 rounded px-2 py-1.5 t-caption", stage.key === activeKey ? "bg-primary/5 text-foreground" : "text-muted-foreground")}>
            <span>{stage.title}</span>
            <StatusBadge status={stage.status} />
          </div>
        ))}
      </div>
    </div>
  );
}

function PptDraftSubStatusList({
  stages,
  subGates,
}: {
  stages: WorkflowStage[];
  subGates?: ApiWorkspaceSubGate[];
}) {
  return (
    <SubStatusList
      title="PPT 草稿检查点"
      desc="PPT 草稿不是一步到位，先看结构，再看逐页讲法、视觉素材和可下载文件。"
      items={[
        {
          label: "结构方案",
          detail: "页数、页面类型、整体风格和课堂环节安排。",
          stage: findStageByKey(stages, "ppt-plan"),
          subGate: findSubGateByLabel(subGates, "结构方案", "ppt-plan"),
        },
        {
          label: "逐页脚本",
          detail: "每页讲什么、学生做什么、板书和练习怎么衔接。",
          stage: findStageByKey(stages, "ppt-script"),
          subGate: findSubGateByLabel(subGates, "逐页脚本", "ppt-script"),
        },
        {
          label: "视觉资产",
          detail: "每页需要的图片、角色和可替换素材；未生成时标明占位。",
          stage: findStageByKey(stages, "ppt-assets"),
          subGate: findSubGateByLabel(subGates, "视觉资产", "ppt-assets"),
        },
        {
          label: "PPTX 文件",
          detail: "可下载的 PPTX 草稿文件；真实质量仍需逐页检查。",
          stage: findStageByKey(stages, "pptx-generation"),
          subGate: findSubGateByLabel(subGates, "PPTX 文件", "pptx-generation"),
        },
      ]}
    />
  );
}

function VideoGenerationSubStatusList({
  stages,
  subGates,
}: {
  stages: WorkflowStage[];
  subGates?: ApiWorkspaceSubGate[];
}) {
  return (
    <SubStatusList
      title="视频生成检查点"
      desc="视频生成按素材链路逐步推进，不能把本地演示文件当成真实成片。"
      items={[
        {
          label: "文稿",
          detail: "旁白正文、时长和禁用清单，必须沿用课程锚点。",
          stage: findStageByKey(stages, "video-script"),
          subGate: findSubGateByLabel(subGates, "文稿", "video-script"),
        },
        {
          label: "分场剧本",
          detail: "分成几个场景，每场画面、角色和旁白是什么。",
          stage: findStageByKey(stages, "video-screenplay"),
          subGate: findSubGateByLabel(subGates, "分场剧本", "video-screenplay"),
        },
        {
          label: "资产与首帧",
          detail: "参考图、首帧方向、角色和场景素材，未真实生成时写明占位。",
          stage: findStageByKey(stages, "video-assets"),
          subGate: findSubGateByLabel(subGates, "资产与首帧", "video-assets"),
        },
        {
          label: "分镜",
          detail: "逐镜头看画面主体、时长、旁白切片和镜头节奏。",
          stage: findStageByKey(stages, "storyboard"),
          subGate: findSubGateByLabel(subGates, "分镜", "storyboard"),
        },
        {
          label: "clip/TTS/合成",
          detail: "视频片段、中文旁白、字幕和合成文件都完成后，才算真实成片可验收。",
          stage: findStageByKey(stages, "video-generation"),
          subGate: findSubGateByLabel(subGates, "clip/TTS/合成", "video-generation"),
        },
      ]}
    />
  );
}

function SubStatusList({
  title,
  desc,
  items,
}: {
  title: string;
  desc: string;
  items: Array<{ label: string; detail: string; stage?: WorkflowStage; subGate?: ApiWorkspaceSubGate }>;
}) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="t-caption font-medium text-foreground">{title}</div>
      <p className="mt-1 t-caption text-muted-foreground">{desc}</p>
      <div className="mt-3 grid gap-2">
        {items.map((item, index) => (
          <div key={`${item.label}-${index}`} className="rounded-md border border-border bg-muted/20 px-3 py-2">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="t-body font-medium text-foreground">{item.label}</div>
                <p className="mt-0.5 t-caption text-muted-foreground">{item.detail}</p>
              </div>
              {item.subGate ? (
                <ToneBadge tone={workspaceSubGateTone(item.subGate)}>
                  {workspaceSubGateLabel(item.subGate)}
                </ToneBadge>
              ) : item.stage ? (
                <StatusBadge status={item.stage.status} />
              ) : (
                <ToneBadge tone="neutral">待开始</ToneBadge>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function findStageByKey(stages: WorkflowStage[], key: string): WorkflowStage | undefined {
  return stages.find((stage) => stage.key === key);
}

function findSubGateByLabel(
  subGates: ApiWorkspaceSubGate[] | undefined,
  label: string,
  fallbackId: string,
): ApiWorkspaceSubGate | undefined {
  return subGates?.find((gate) => {
    const gateLabel = String(gate.title || gate.label || gate.gate_id || gate.id || "");
    return gateLabel === label || gate.gate_id === fallbackId || gate.id === fallbackId;
  });
}

function workspaceSubGateState(gate: ApiWorkspaceSubGate): string {
  return String(gate.state || gate.status || "not_started");
}

function workspaceSubGateLabel(gate: ApiWorkspaceSubGate): string {
  const state = workspaceSubGateState(gate);
  if (["completed", "complete", "approved", "done", "passed"].includes(state)) return "已完成";
  if (["current", "ready", "pending_confirm", "needs_review", "review"].includes(state)) return "待确认";
  if (["running", "loading", "processing"].includes(state)) return "进行中";
  if (["blocked", "locked"].includes(state)) return "未解锁";
  if (["failed", "error"].includes(state)) return "需处理";
  return "待开始";
}

function workspaceSubGateTone(gate: ApiWorkspaceSubGate): React.ComponentProps<typeof ToneBadge>["tone"] {
  const state = workspaceSubGateState(gate);
  if (["completed", "complete", "approved", "done", "passed"].includes(state)) return "success";
  if (["current", "ready", "pending_confirm", "needs_review", "review"].includes(state)) return "warning";
  if (["running", "loading", "processing"].includes(state)) return "brand";
  if (["blocked", "locked", "failed", "error"].includes(state)) return "danger";
  return "neutral";
}

function UserActionNotice({
  nodeStatus,
  nodeError,
  actionStatus,
  actionError,
}: {
  nodeStatus: "idle" | "loading" | "ready" | "error";
  nodeError?: string | null;
  actionStatus: "idle" | "loading" | "ready" | "error";
  actionError?: string | null;
}) {
  if (nodeStatus === "loading" || actionStatus === "loading") {
    return (
      <div className="flex items-start gap-2 rounded-md border border-primary/20 bg-primary/5 px-3 py-2">
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
        <p className="t-body text-primary">系统正在处理，请稍候。</p>
      </div>
    );
  }
  if (nodeStatus === "error" || actionStatus === "error") {
    return (
      <div className="flex items-start gap-2 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
        <div>
          <p className="t-body font-medium text-destructive">这一步暂时没有处理成功</p>
          <p className="mt-0.5 t-caption text-destructive/90">
            {formatUserFacingError(actionError || nodeError || "请检查上一阶段是否已经确认，再重试当前步骤。")}
          </p>
        </div>
      </div>
    );
  }
  return null;
}

function CurrentResultPanel({
  dataMode,
  projectId,
  stage,
  value,
  inputValue,
  lessonPlanResult,
  courseAnchor,
  editable,
  saving,
  videoPlans,
  compareIds,
  projectTasks,
  projectTasksStatus,
  projectTasksError,
  pptExportStatus,
  pptExportError,
  pptExportResult,
  actionError,
  onChangeResult,
  onChangeInput,
  onSave,
  onToggleSelect,
  onAcceptVideoPlan,
  onCompare,
  onRegenerate,
  onRefreshTasks,
  onRefreshTask,
  onRetryTask,
  onExportPpt,
}: {
  dataMode: DataMode;
  projectId: string;
  stage: WorkflowStage;
  value: string;
  inputValue: string;
  lessonPlanResult: string;
  courseAnchor: string;
  editable: boolean;
  saving: boolean;
  videoPlans: VideoIntroPlan[];
  compareIds: string[];
  projectTasks: ApiTask[];
  projectTasksStatus: LoadStatus;
  projectTasksError?: string | null;
  pptExportStatus: LoadStatus;
  pptExportError: string | null;
  pptExportResult: ApiPptExport | null;
  actionError?: string | null;
  onChangeResult: (value: string) => void;
  onChangeInput: (value: string) => void;
  onSave: () => void;
  onToggleSelect: (id: string) => void;
  onAcceptVideoPlan: (id: string) => void;
  onCompare: () => void;
  onRegenerate: () => void;
  onRefreshTasks: () => void;
  onRefreshTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onRetryTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onExportPpt: () => void;
}) {
  if (stage.key === "open-lesson-plan") {
    return (
      <LessonPlanMarkdownEditor
        value={resolveMarkdownForStage(stage, value)}
        editable={editable}
        saving={saving}
        onChange={onChangeResult}
        onSave={onSave}
      />
    );
  }
  if (stage.key === "textbook-parse") {
    return (
      <TextbookContentResult
        projectId={projectId}
        stage={stage}
        value={value}
      />
    );
  }
  if (stage.key === "pptx-generation") {
    return <PptxArtifactResult stage={stage} value={value} />;
  }
  if (dataMode === "demo" && stage.key === "video-script") {
    return (
      <VideoPlanGrid
        plans={videoPlans}
        selectedIds={compareIds}
        onToggleSelect={onToggleSelect}
        onAccept={onAcceptVideoPlan}
        onEdit={() => toast.info("演示版暂不支持编辑")}
        onCompare={onCompare}
        onRegenerate={onRegenerate}
      />
    );
  }
  if (dataMode === "api" && stage.key === "video-design-import") {
    return (
      <IntroSelectionResult
        stage={stage}
        value={value}
        lessonPlanResult={lessonPlanResult}
        onChange={onChangeResult}
        onSave={onSave}
        saving={saving}
        actionError={actionError}
        showAdvancedJson={false}
      />
    );
  }
  if (dataMode === "api" && stage.key === "video-generation") {
    return (
      <FinalVideoResult
        projectId={projectId}
        stage={stage}
        tasks={projectTasks}
        tasksStatus={projectTasksStatus}
        tasksError={projectTasksError}
        actionError={actionError}
        showProviderDetails={false}
        pptExportStatus={pptExportStatus}
        pptExportError={pptExportError}
        pptExportResult={pptExportResult}
        onRefresh={onRefreshTasks}
        onRefreshTask={onRefreshTask}
        onRetryTask={onRetryTask}
        onExportPpt={onExportPpt}
      />
    );
  }
  if (dataMode === "api" && stage.key === "video-assets") {
    return (
      <VideoAssetResult
        projectId={projectId}
        stage={stage}
        value={value}
        tasks={projectTasks}
        tasksStatus={projectTasksStatus}
        tasksError={projectTasksError}
        onChange={onChangeResult}
        onSave={onSave}
        saving={saving}
        onRefresh={onRefreshTasks}
        onRetryTask={onRetryTask}
        showAdvancedJson={false}
        showProviderDetails={false}
      />
    );
  }
  if (editable) {
    return <UserReadableResult stage={stage} value={value} courseAnchor={courseAnchor} />;
  }
  if (stage.status === "input_required") {
    return (
      <Card className="border-border bg-muted/20 p-4">
        <div className="t-module">可编辑区域</div>
        <p className="mt-1 t-caption text-muted-foreground">补充本步骤需要的要求或修改意见。</p>
        <Textarea value={inputValue} onChange={(event) => onChangeInput(event.target.value)} className="mt-3 min-h-32 bg-card" />
      </Card>
    );
  }
  return <UserReadableResult stage={stage} value={value} courseAnchor={courseAnchor} />;
}

function LessonPlanMarkdownEditor({
  value,
  editable,
  saving,
  onChange,
  onSave,
}: {
  value: string;
  editable: boolean;
  saving: boolean;
  onChange: (value: string) => void;
  onSave: () => void;
}) {
  const [mode, setMode] = useState<"edit" | "preview">("edit");
  return (
    <Card className="border-border bg-card p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <div className="t-module">教案 Markdown</div>
          <p className="mt-1 t-caption text-muted-foreground">普通教师只编辑教案正文，不需要接触结构化原文。</p>
        </div>
        <div className="flex items-center gap-2">
          <Button type="button" size="sm" variant={mode === "edit" ? "default" : "outline"} onClick={() => setMode("edit")}>
            Markdown 编辑
          </Button>
          <Button type="button" size="sm" variant={mode === "preview" ? "default" : "outline"} onClick={() => setMode("preview")}>
            Markdown 预览
          </Button>
          {editable && (
            <Button type="button" size="sm" className="gap-1.5" disabled={saving || !value.trim()} onClick={onSave}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              保存修改
            </Button>
          )}
        </div>
      </div>
      <div className="p-4">
        {mode === "edit" ? (
          <Textarea
            value={value}
            readOnly={!editable}
            onChange={(event) => onChange(event.target.value)}
            className="min-h-[420px] bg-card font-sans text-[0.92rem] leading-relaxed"
            placeholder="生成教案后可在这里编辑 Markdown..."
          />
        ) : (
          <div className="prose prose-sm max-w-none rounded-md border border-border bg-muted/20 p-4 text-foreground">
            <ReactMarkdown>{value || "暂无教案内容。"}</ReactMarkdown>
          </div>
        )}
      </div>
    </Card>
  );
}

function TextbookContentResult({
  projectId,
  stage,
  value,
}: {
  projectId: string;
  stage: WorkflowStage;
  value: string;
}) {
  const [preview, setPreview] = useState<"pdf" | "markdown" | null>(null);
  const summary = buildTextbookContentSummary(projectId, stage, value || stage.result);
  const previewMarkdown =
    summary.markdown.trim() ||
    "暂未读取到教材内容预览。请刷新状态，或稍后在开发诊断中查看生成详情。";

  return (
    <Card className="border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-module">教材解析与核验摘要</div>
          <p className="mt-1 t-caption text-muted-foreground">
            先核对课时、页码和知识点，再确认进入教案生成。
          </p>
        </div>
        <ToneBadge tone="info">待核验</ToneBadge>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <SummaryField label="课时标题" value={summary.title} />
        <SummaryField label="教材页码" value={summary.pages} />
        <SummaryField label="解析状态" value={summary.status} />
        <SummaryField label="教材依据" value={summary.basis} />
      </div>

      <div className="mt-4 rounded-md border border-border bg-card p-3">
        <div className="t-caption text-muted-foreground">本课要点</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {summary.knowledge.length > 0 ? (
            summary.knowledge.map((item) => (
              <span
                key={item}
                className="rounded-full border border-primary/20 bg-primary/5 px-2 py-1 t-caption text-primary"
              >
                {item}
              </span>
            ))
          ) : (
            <span className="t-body text-muted-foreground">等待教材解析结果。</span>
          )}
        </div>
      </div>

      {summary.markdown.trim() && (
        <div className="mt-4 rounded-md border border-border bg-card p-3">
          <div className="t-caption text-muted-foreground">教材内容预览</div>
          <div className="mt-2 max-h-32 overflow-hidden whitespace-pre-wrap t-body leading-relaxed text-foreground/90">
            {clipText(summary.markdown, 260)}
          </div>
        </div>
      )}

      <TextbookContentPreviewActions
        canOpenSlice={Boolean(summary.sliceUrl)}
        canOpenMarkdown={Boolean(summary.markdown.trim())}
        onOpenSlice={() => setPreview("pdf")}
        onOpenMarkdown={() => setPreview("markdown")}
      />

      <Dialog open={preview !== null} onOpenChange={(open) => !open && setPreview(null)}>
        <DialogContent className="max-h-[86vh] max-w-5xl overflow-hidden">
          <DialogHeader>
            <DialogTitle>
              {preview === "pdf" ? "教材页段预览" : "教材内容预览"}
            </DialogTitle>
            <DialogDescription>
              {preview === "pdf"
                ? `当前课时教材页 ${summary.pages}，通过项目预览入口打开。`
                : "当前课时的教材内容摘要，用于生成教案前核对。"}
            </DialogDescription>
          </DialogHeader>
          {preview === "pdf" ? (
            summary.sliceUrl ? (
              <iframe
                title="教材页段预览"
                src={summary.sliceUrl}
                className="h-[68vh] w-full rounded-md border border-border bg-muted"
              />
            ) : (
              <div className="rounded-md border border-border bg-muted/30 p-4 t-body text-muted-foreground">
                当前课时还没有可预览的教材页段。
              </div>
            )
          ) : (
            <ScrollArea className="max-h-[68vh] rounded-md border border-border bg-muted/30">
              <pre className="whitespace-pre-wrap p-4 font-sans text-sm leading-relaxed text-foreground">
                {previewMarkdown}
              </pre>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
}

function SummaryField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2.5">
      <div className="t-caption text-muted-foreground">{label}</div>
      <div className="mt-1 t-body text-foreground/90">{value || "待确认"}</div>
    </div>
  );
}

function TextbookContentPreviewActions({
  canOpenSlice,
  canOpenMarkdown,
  onOpenSlice,
  onOpenMarkdown,
}: {
  canOpenSlice: boolean;
  canOpenMarkdown: boolean;
  onOpenSlice: () => void;
  onOpenMarkdown: () => void;
}) {
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="gap-1.5"
        disabled={!canOpenSlice}
        onClick={onOpenSlice}
      >
        <Eye className="h-4 w-4" />
        查看教材页段
      </Button>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="gap-1.5"
        disabled={!canOpenMarkdown}
        onClick={onOpenMarkdown}
      >
        <FileText className="h-4 w-4" />
        查看教材内容
      </Button>
    </div>
  );
}

function PptxArtifactResult({
  stage,
  value,
}: {
  stage: WorkflowStage;
  value: string;
}) {
  const summary = buildPptxArtifactSummary(stage, value || stage.result);
  return (
    <Card className="border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <FileType2 className="h-4 w-4 text-primary" />
            <span className="t-module">PPTX 文件</span>
            <ToneBadge tone={summary.ready ? "success" : "info"}>
              {summary.ready ? "待确认" : "待生成"}
            </ToneBadge>
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            这里提供可下载的 PPTX 草稿。真实上课前仍需要逐页检查讲法、素材和排版。
          </p>
        </div>
        {summary.downloadHref && (
          <Button asChild size="sm" className="gap-1.5">
            <a href={summary.downloadHref} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" />
              下载 PPTX
            </a>
          </Button>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <SummaryField label="文件名" value={summary.filename} />
        <SummaryField label="当前状态" value={summary.ready ? "文件已生成，等待确认" : "还没有可下载文件"} />
      </div>
    </Card>
  );
}

function UserReadableEditableResult({
  stage,
  value,
  courseAnchor,
  saving,
  onChange,
  onSave,
}: {
  stage: WorkflowStage;
  value: string;
  courseAnchor: string;
  saving: boolean;
  onChange: (value: string) => void;
  onSave: () => void;
}) {
  const summary = buildEditableNodeSummary(stage, value || stage.result, courseAnchor);
  return (
    <div className="space-y-4">
      <UserReadableSummaryCard summary={summary} />
      <details className="rounded-md border border-border bg-card">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
          <span className="t-module">可编辑区域</span>
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        </summary>
        <div className="border-t border-border p-4">
          <Textarea
            value={value}
            onChange={(event) => onChange(event.target.value)}
            className="min-h-[260px] bg-card text-[0.9rem] leading-relaxed"
            placeholder={`生成${stage.title}后可在这里修改摘要内容...`}
          />
          <div className="mt-3 flex justify-end">
            <Button size="sm" className="gap-1.5" disabled={saving || !value.trim()} onClick={onSave}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              保存修改
            </Button>
          </div>
        </div>
      </details>
    </div>
  );
}

function UserReadableResult({
  stage,
  value,
  courseAnchor,
}: {
  stage: WorkflowStage;
  value: string;
  courseAnchor: string;
}) {
  if (!stage.result && !value) {
    return (
      <EmptyState
        title="当前还没有草稿"
        desc="点击下方主按钮生成这一阶段草稿。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  const summary = buildEditableNodeSummary(stage, value || stage.result, courseAnchor);
  return <UserReadableSummaryCard summary={summary} />;
}

function UserReadableSummaryCard({ summary }: { summary: EditableSummary }) {
  return (
    <Card className="border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-module">{summary.title}</div>
          <p className="mt-1 t-caption text-muted-foreground">{summary.desc}</p>
        </div>
        <ToneBadge tone="info">{summary.badge}</ToneBadge>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {summary.items.length > 0 ? summary.items.map((item, index) => (
          <div key={`${item.label}-${index}`} className="rounded-md border border-border bg-card px-3 py-2.5">
            <div className="t-caption text-muted-foreground">{item.label}</div>
            <div className="mt-1 t-body text-foreground/90">{item.value}</div>
          </div>
        )) : (
          <div className="rounded-md border border-dashed border-border bg-card px-3 py-6 text-center t-caption text-muted-foreground">
            暂无可读摘要。
          </div>
        )}
      </div>
    </Card>
  );
}

function DeveloperDiagnostics({
  dataMode,
  tab,
  stage,
  inputDraft,
  resultDraft,
  selectedNodeStatus,
  selectedNodeError,
  selectedActionStatus,
  selectedActionError,
  canSave,
  canRegenerate,
  canApprove,
  canReject,
  canNext,
  isRunning,
  isFinalVideoStage,
  videoPlans,
  compareIds,
  stages,
  projectId,
  projectTasks,
  projectTasksStatus,
  projectTasksError,
  pptExportStatus,
  pptExportError,
  pptExportResult,
  canEditSelectedStage,
  videoCapabilities,
  videoOption,
  onTabChange,
  onChangeInput,
  onChangeResult,
  onSave,
  onSaveResult,
  onRefresh,
  onRegenerate,
  onApprove,
  onReject,
  onNext,
  onChangeVideoOption,
  onToggleSelect,
  onAcceptVideoPlan,
  onCompare,
  onPreview,
  onRefreshTasks,
  onRefreshTask,
  onRetryTask,
  onExportPpt,
}: {
  dataMode: DataMode;
  tab: TabKey;
  stage?: WorkflowStage;
  inputDraft: string;
  resultDraft: string;
  selectedNodeStatus: "idle" | "loading" | "ready" | "error";
  selectedNodeError?: string | null;
  selectedActionStatus: "idle" | "loading" | "ready" | "error";
  selectedActionError?: string | null;
  canSave: boolean;
  canRegenerate: boolean;
  canApprove: boolean;
  canReject: boolean;
  canNext: boolean;
  isRunning: boolean;
  isFinalVideoStage: boolean;
  videoPlans: VideoIntroPlan[];
  compareIds: string[];
  stages: WorkflowStage[];
  projectId: string;
  projectTasks: ApiTask[];
  projectTasksStatus: LoadStatus;
  projectTasksError?: string | null;
  pptExportStatus: LoadStatus;
  pptExportError: string | null;
  pptExportResult: ApiPptExport | null;
  canEditSelectedStage: boolean;
  videoCapabilities: VideoCapability[];
  videoOption: VideoModelOption;
  onTabChange: (tab: TabKey) => void;
  onChangeInput: (value: string) => void;
  onChangeResult: (value: string) => void;
  onSave: () => void;
  onSaveResult: () => void;
  onRefresh: () => void;
  onRegenerate: () => void;
  onApprove: () => void;
  onReject: () => void;
  onNext: () => void;
  onChangeVideoOption: (option: VideoModelOption) => void;
  onToggleSelect: (id: string) => void;
  onAcceptVideoPlan: (id: string) => void;
  onCompare: () => void;
  onPreview: (file: string) => void;
  onRefreshTasks: () => void;
  onRefreshTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onRetryTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onExportPpt: () => void;
}) {
  return (
    <details className="rounded-md border border-border bg-muted/10">
      <summary className="mt-4 flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
        <span className="t-module">开发诊断</span>
        <ChevronDown className="h-4 w-4 text-muted-foreground" />
      </summary>
      <Card className="border-border bg-card p-0 shadow-soft">
        {dataMode === "api" && stage && <StateEngineDiagnostics stage={stage} />}
        <Tabs value={tab} onValueChange={(value) => onTabChange(value as TabKey)} className="gap-0">
          <div className="overflow-x-auto scroll-fine px-3 py-2 sm:px-5">
            <TabsList className="bg-muted/60">
              <TabsTrigger value="input">输入</TabsTrigger>
              <TabsTrigger value="run">运行</TabsTrigger>
              <TabsTrigger value="result">结果</TabsTrigger>
              <TabsTrigger value="evidence">依据</TabsTrigger>
              <TabsTrigger value="logs">日志</TabsTrigger>
            </TabsList>
          </div>
          <div className="px-4 pb-5 pt-4 sm:px-6">
            <TabsContent value="input" className="mt-0">
              {dataMode === "api" && <><ApiNodeNotice status={selectedNodeStatus} error={selectedNodeError} /><ApiActionNotice status={selectedActionStatus} error={selectedActionError} /></>}
              <InputTab stage={stage} value={inputDraft} onChange={onChangeInput} onSave={onSave} />
            </TabsContent>
            <TabsContent value="run" className="mt-0">
              {dataMode === "api" && <><ApiNodeNotice status={selectedNodeStatus} error={selectedNodeError} /><ApiActionNotice status={selectedActionStatus} error={selectedActionError} /></>}
              {stage?.key === "video-generation" ? (
                <VideoGenerationRunTab projectId={projectId} stage={stage} capabilities={videoCapabilities} option={videoOption} onChange={onChangeVideoOption} onRegenerate={onRegenerate} />
              ) : (
                <RunTab stage={stage} onRegenerate={onRegenerate} />
              )}
            </TabsContent>
            <TabsContent value="result" className="mt-0">
              {dataMode === "api" && <><ApiNodeNotice status={selectedNodeStatus} error={selectedNodeError} /><ApiActionNotice status={selectedActionStatus} error={selectedActionError} /></>}
              {dataMode === "demo" && stage?.key === "video-script" ? (
                <VideoPlanGrid plans={videoPlans} selectedIds={compareIds} onToggleSelect={onToggleSelect} onAccept={onAcceptVideoPlan} onEdit={() => toast.info("演示版暂不支持编辑")} onCompare={onCompare} onRegenerate={onRegenerate} />
              ) : dataMode === "api" && stage?.key === "video-design-import" ? (
                <IntroSelectionResult stage={stage} value={resultDraft || stage.result} lessonPlanResult={stages.find((item) => item.key === "open-lesson-plan")?.result || ""} onChange={onChangeResult} onSave={onSaveResult} saving={selectedActionStatus === "loading"} actionError={selectedActionError} />
              ) : dataMode === "api" && stage?.key === "video-generation" ? (
                <FinalVideoResult projectId={projectId} stage={stage} tasks={projectTasks} tasksStatus={projectTasksStatus} tasksError={projectTasksError} actionError={selectedActionError} pptExportStatus={pptExportStatus} pptExportError={pptExportError} pptExportResult={pptExportResult} onRefresh={onRefreshTasks} onRefreshTask={onRefreshTask} onRetryTask={onRetryTask} onExportPpt={onExportPpt} />
              ) : dataMode === "api" && stage?.key === "video-assets" ? (
                <VideoAssetResult projectId={projectId} stage={stage} value={resultDraft || stage.result} tasks={projectTasks} tasksStatus={projectTasksStatus} tasksError={projectTasksError} onChange={onChangeResult} onSave={onSaveResult} saving={selectedActionStatus === "loading"} onRefresh={onRefreshTasks} onRetryTask={onRetryTask} />
              ) : dataMode === "api" && stage && canEditSelectedStage ? (
                <EditableNodeResult stage={stage} value={resultDraft || stage.result} courseAnchor={resolveCourseAnchorForStage(stage.key, stages)} onChange={onChangeResult} onSave={onSaveResult} saving={selectedActionStatus === "loading"} />
              ) : (
                <ResultTab stage={stage} />
              )}
            </TabsContent>
            <TabsContent value="evidence" className="mt-0">
              <EvidenceTab stage={stage} onPreview={onPreview} />
            </TabsContent>
            <TabsContent value="logs" className="mt-0">
              <LogsTab stage={stage} />
            </TabsContent>
          </div>
        </Tabs>
        <div className="border-t border-border bg-muted/20 px-4 py-3 sm:px-6">
          <StageActions
            canSave={canSave}
            canRegenerate={canRegenerate}
            canApprove={canApprove}
            canReject={canReject}
            canNext={canNext}
            isRunning={isRunning}
            taskCreated={isFinalVideoStage && stage?.status === "running"}
            regenerateLabel={isFinalVideoStage ? "重新创建任务" : undefined}
            primaryRegenerateLabel={isFinalVideoStage ? "创建视频任务" : undefined}
            actionLoading={selectedActionStatus === "loading"}
            showRefresh={dataMode === "api"}
            onSave={onSave}
            onRefresh={onRefresh}
            onRegenerate={onRegenerate}
            onApprove={onApprove}
            onReject={onReject}
            onNext={onNext}
          />
        </div>
      </Card>
    </details>
  );
}

function ApiNodeNotice({
  status,
  error,
}: {
  status: "idle" | "loading" | "ready" | "error";
  error?: string | null;
}) {
  if (status === "loading") {
    return (
      <div className="mb-3 flex items-start gap-2 rounded-md border border-info/25 bg-info/5 px-3 py-2">
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-info" />
        <p className="t-body text-info">正在读取后端节点详情...</p>
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="mb-3 flex items-start gap-2 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
        <p className="t-body text-destructive">{error || "节点详情读取失败"}</p>
      </div>
    );
  }
  if (status === "ready") {
    return (
      <div className="mb-3 flex items-start gap-2 rounded-md border border-success/25 bg-success/5 px-3 py-2">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
        <p className="t-body text-success">已同步后端节点详情。</p>
      </div>
    );
  }
  return null;
}

function ApiActionNotice({
  status,
  error,
}: {
  status: "idle" | "loading" | "ready" | "error";
  error?: string | null;
}) {
  if (status === "loading") {
    return (
      <div className="mb-3 flex items-start gap-2 rounded-md border border-primary/20 bg-primary/5 px-3 py-2">
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
        <p className="t-body text-primary">正在执行后端节点动作...</p>
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="mb-3 flex items-start gap-2 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
        <div>
          <p className="t-body font-medium text-destructive">后端动作执行失败</p>
          <p className="mt-0.5 t-caption text-destructive/90">
            {formatApiActionError(error)}
          </p>
        </div>
      </div>
    );
  }
  return null;
}

function StateEngineDiagnostics({ stage }: { stage: WorkflowStage }) {
  const latestTransition = stage.latestTransition;
  const reviewReason = stage.reviewReason || latestTransition?.reason || "";
  const upstreamBlocked = isUpstreamBlocked(stage);
  const ruleWarning = isRuleWarning(stage);
  const ruleViolation = isRuleViolation(stage);

  if (!latestTransition && !stage.reviewReason && !stage.reviewTrigger) return null;

  return (
    <div className="border-b border-border bg-muted/20 px-4 py-3 sm:px-6">
      <div className="grid gap-3 lg:grid-cols-[1fr_1.2fr]">
        <div className="rounded-md border border-border bg-background/70 p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="t-caption text-muted-foreground">StateEngine 状态</p>
              <p className="mt-0.5 t-body font-medium">{formatStageStatusForDiagnostics(stage.status)}</p>
            </div>
            <StatusBadge status={stage.status} />
          </div>
          {stage.reviewTrigger && (
            <p className="mt-2 t-caption text-muted-foreground">触发器：{stage.reviewTrigger}</p>
          )}
        </div>
        <div className="rounded-md border border-border bg-background/70 p-3">
          <p className="t-caption text-muted-foreground">最近状态迁移</p>
          {latestTransition ? (
            <>
              <p className="mt-0.5 t-body">
                {latestTransition.from_status || "无"} → {latestTransition.to_status}
              </p>
              <p className="mt-1 t-caption text-muted-foreground">
                {latestTransition.trigger}
                {latestTransition.triggered_at ? ` · ${formatDateTimeForDiagnostics(latestTransition.triggered_at)}` : ""}
              </p>
            </>
          ) : (
            <p className="mt-0.5 t-body text-muted-foreground">后端暂未返回最近迁移记录</p>
          )}
        </div>
      </div>

      {(reviewReason || upstreamBlocked || ruleWarning || ruleViolation) && (
        <div className="mt-3 rounded-md border border-warning/25 bg-warning/5 p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <div className="min-w-0">
              <p className="t-body font-medium text-warning">
                {upstreamBlocked
                  ? "上游未确认"
                  : ruleViolation
                    ? "硬阻断不可继续"
                    : ruleWarning
                      ? "规则警告可覆盖"
                      : "状态诊断"}
              </p>
              <p className="mt-0.5 break-words t-caption text-muted-foreground">
                {upstreamBlocked
                  ? "请先确认依赖节点后再继续；后端已通过 StateEngine 记录本次依赖门禁。"
                  : ruleViolation
                    ? "需要修正内容或规则问题后再提交，当前不能直接继续。"
                    : ruleWarning
                      ? "可检查规则提示，必要时填写 override 原因后继续确认。"
                      : "后端返回了节点重审或状态迁移原因。"}
              </p>
              {reviewReason && (
                <p className="mt-2 break-words t-caption text-muted-foreground">详情：{reviewReason}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatApiActionError(error?: string | null): string {
  if (!error) return "请检查上游节点是否已确认，或确认后端服务状态。";
  if (error.includes("UPSTREAM_NOT_APPROVED")) {
    return `上游未确认：请先确认依赖节点后再继续。${extractApiDetailsText(error)}`;
  }
  if (error.includes("RULE_WARNING")) {
    return `规则警告：可检查提示后选择覆盖继续。${extractApiDetailsText(error)}`;
  }
  if (error.includes("RULE_VIOLATION")) {
    return `硬阻断不可继续：需修正内容后再提交。${extractApiDetailsText(error)}`;
  }
  return error;
}

function extractApiDetailsText(error: string): string {
  const index = error.indexOf("details:");
  if (index === -1) return "";
  return ` 后端详情：${error.slice(index + "details:".length).trim()}`;
}

function isUpstreamBlocked(stage: WorkflowStage): boolean {
  return hasStateEngineSignal(stage, ["UPSTREAM_NOT_APPROVED", "dependency_gate_blocked", "R010"]);
}

function isRuleWarning(stage: WorkflowStage): boolean {
  return hasStateEngineSignal(stage, ["RULE_WARNING"]);
}

function isRuleViolation(stage: WorkflowStage): boolean {
  return hasStateEngineSignal(stage, ["RULE_VIOLATION"]);
}

function hasStateEngineSignal(stage: WorkflowStage, signals: string[]): boolean {
  const source = [
    stage.reviewTrigger,
    stage.reviewReason,
    stage.latestTransition?.trigger,
    stage.latestTransition?.reason,
  ]
    .filter(Boolean)
    .join(" ");
  return signals.some((signal) => source.includes(signal));
}

function formatStageStatusForDiagnostics(status: WorkflowStage["status"]): string {
  const map: Record<WorkflowStage["status"], string> = {
    not_started: "未开始",
    input_required: "需要输入",
    ready: "可运行",
    running: "生成中",
    pending_confirm: "待确认",
    approved: "已确认",
    blocked: "已阻断",
    failed: "失败",
    skipped: "已跳过",
  };
  return map[status] || status;
}

function formatDateTimeForDiagnostics(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())} ${p(date.getHours())}:${p(
    date.getMinutes(),
  )}`;
}

/* ---------- 顶部 Header ---------- */

function WorkspaceHeader({
  project,
  stages = [],
  onBack,
  feedbackStatus = "idle",
  onSubmitFeedback,
  currentStepLabel,
  nextActionOverride,
}: {
  project: ProjectMeta;
  stages?: WorkflowStage[];
  onBack: () => void;
  feedbackStatus?: LoadStatus;
  onSubmitFeedback?: () => void;
  currentStepLabel?: string;
  nextActionOverride?: string;
}) {
  const stage =
    stages.find((item) => item.key === project.currentStage) ||
    stageDefByKey(project.currentStage);
  return (
    <Card className="border-border bg-card p-0 shadow-soft">
      <div className="p-4 sm:p-6">
        {/* 顶部行：返回 + 项目名 + 状态 */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <button
              type="button"
              onClick={onBack}
              className="-mx-2 -my-1 inline-flex items-center gap-1.5 rounded-md px-2 py-1 t-caption text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-ring"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              返回项目列表
            </button>
            <h1 className="mt-2 t-title">{project.name}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 t-body text-muted-foreground">
              <span>{project.subject}</span>
              <span className="h-3 w-px bg-border" />
              <span>{project.grade}</span>
              <span className="h-3 w-px bg-border" />
              <span>
                {project.textbookVersion} {project.volume}
              </span>
              <span className="h-3 w-px bg-border" />
              <span>{project.lessonType}</span>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {onSubmitFeedback && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-2"
                disabled={feedbackStatus === "loading"}
                onClick={onSubmitFeedback}
              >
                {feedbackStatus === "loading" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ListChecks className="h-4 w-4" />
                )}
                反馈
              </Button>
            )}
            <ProjectStatusBadge status={project.status} />
          </div>
        </div>

        {/* 底部 3 列：当前阶段 / 总进度 / 下一步动作 */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div>
            <div className="t-overline text-muted-foreground/70">当前阶段</div>
            <div className="mt-1.5 t-body font-medium text-foreground">
              {currentStepLabel || stage?.title || project.currentStage}
            </div>
          </div>
          <div>
            <div className="t-overline text-muted-foreground/70">总进度</div>
            <div className="mt-1.5 flex items-baseline gap-2">
              <span className="t-module">{project.progress}%</span>
            </div>
            <Progress
              value={project.progress}
              className="mt-2 h-1.5 bg-muted"
            />
          </div>
          <div>
            <div className="t-overline text-muted-foreground/70">下一步动作</div>
            <div className="mt-1.5 t-body font-medium text-foreground">
              {nextActionOverride || project.nextAction}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

/* ---------- 工作流节点轨 ---------- */

function WorkflowRail({
  stages,
  selectedKey,
  onSelect,
}: {
  stages: WorkflowStage[];
  selectedKey: string;
  onSelect: (key: string) => void;
}) {
  const orderedStages = stages.slice().sort((a, b) => a.order - b.order);
  return (
    <div className="overflow-x-auto scroll-fine pb-1">
      <div className="flex min-w-max items-stretch px-1 py-1">
        {orderedStages.map((stage, i) => {
          const status = stage.status;
          const isSelected = stage.key === selectedKey;
          const isApproved = status === "approved" || status === "skipped";
          const isRunning = status === "running";
          const isError = status === "failed" || status === "blocked";
          const isPending =
            status === "pending_confirm" ||
            status === "input_required" ||
            status === "ready";

          return (
            <div key={stage.key} className="flex items-stretch">
              <button
                type="button"
                onClick={() => onSelect(stage.key)}
                aria-current={isSelected ? "true" : undefined}
                className={cn(
                  "relative flex h-[88px] w-[88px] shrink-0 flex-col items-center gap-1 rounded-md border px-2 pt-2.5 pb-2 text-center transition-all focus-ring",
                  isSelected
                    ? "border-primary bg-primary/[0.04] shadow-soft"
                    : "border-transparent hover:bg-muted/60",
                )}
              >
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-[0.7rem] font-semibold",
                    isApproved && "bg-success/15 text-success",
                    isRunning && "bg-primary text-primary-foreground",
                    isError && "bg-destructive/10 text-destructive",
                    isPending && !isSelected && "bg-warning/15 text-warning",
                    isPending && isSelected && "bg-primary text-primary-foreground",
                    status === "not_started" &&
                      !isSelected &&
                      "bg-muted text-muted-foreground",
                    status === "not_started" &&
                      isSelected &&
                      "bg-primary text-primary-foreground",
                  )}
                >
                  {isApproved ? (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  ) : isRunning ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : isError ? (
                    <AlertTriangle className="h-3.5 w-3.5" />
                  ) : (
                    stage.order
                  )}
                </span>
                <span
                  className={cn(
                    "t-caption leading-tight",
                    isSelected
                      ? "font-medium text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  {stage.title}
                </span>
                <span
                  className={cn(
                    "t-overline text-[0.55rem] leading-none",
                    stage.branch === "common" && "text-muted-foreground/60",
                    stage.branch === "video" && "text-info",
                    stage.branch === "ppt" && "text-bronze",
                  )}
                >
                  {BRANCH_LABEL[stage.branch]}
                </span>
                {isRunning && (
                  <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                )}
                {stage.reviewTrigger === "cascade_invalidate" && !isRunning && (
                  <RefreshCw className="absolute right-1.5 top-1.5 h-3 w-3 text-warning" aria-label="上游变更后需重审" />
                )}
              </button>
              {i < orderedStages.length - 1 && (
                <div className="flex w-3 justify-center pt-6">
                  <span
                    className={cn(
                      "h-px w-full",
                      isApproved ? "bg-success/50" : "bg-border",
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- Tab: 输入 ---------- */

function InputTab({
  stage,
  value,
  onChange,
  onSave,
}: {
  stage?: WorkflowStage;
  value: string;
  onChange: (v: string) => void;
  onSave: () => void;
}) {
  if (!stage) return null;
  const needsInput =
    stage.status === "not_started" || stage.status === "input_required";
  return (
    <div className="space-y-3">
      {needsInput && (
        <div className="flex items-start gap-2 rounded-md border border-warning/25 bg-warning/5 px-3 py-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <p className="t-body text-warning">
            请填写该阶段的输入内容后保存，再触发运行。
          </p>
        </div>
      )}
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="输入该阶段需要的素材、要求或参数…"
        className="min-h-40 bg-card"
      />
      <div className="flex justify-end">
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={onSave}
          disabled={stage.status === "running"}
        >
          <Save className="h-4 w-4" />
          保存输入
        </Button>
      </div>
    </div>
  );
}

/* ---------- Tab: 运行 ---------- */

function RunTab({
  stage,
  onRegenerate,
}: {
  stage?: WorkflowStage;
  onRegenerate: () => void;
}) {
  if (!stage) return null;
  if (stage.status === "running") {
    return <LoadingState label="运行中，请稍候…" />;
  }
  const statusText: Record<WorkflowStage["status"], string> = {
    not_started: "尚未运行",
    input_required: "等待输入",
    ready: "可运行",
    running: "运行中",
    pending_confirm: "运行完成，待确认",
    approved: "已通过",
    skipped: "已跳过",
    blocked: "已阻塞",
    failed: "运行失败",
  };
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={stage.status} />
        <span className="t-body text-muted-foreground">
          {statusText[stage.status]}
        </span>
        {stage.duration && (
          <span className="ml-auto flex items-center gap-1.5 t-caption text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            上次耗时 {stage.duration}
          </span>
        )}
      </div>
      {stage.reviewReason && (
        <div className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-warning">
          <RefreshCw className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="t-body">{stage.reviewReason}</span>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" className="gap-1.5" onClick={onRegenerate}>
          <Play className="h-4 w-4" />
          {stage.status === "not_started" ? "开始运行" : "重新生成"}
        </Button>
      </div>
    </div>
  );
}

function VideoGenerationRunTab({
  projectId,
  stage,
  capabilities,
  option,
  onChange,
  onRegenerate,
}: {
  projectId: string;
  stage?: WorkflowStage;
  capabilities: VideoCapability[];
  option: VideoModelOption;
  onChange: (option: VideoModelOption) => void;
  onRegenerate: () => void;
}) {
  if (!stage) return null;
  const selectedCapability =
    capabilities.find((item) => item.model === option.model) || capabilities[0];
  const sizeOptions = selectedCapability?.resolution?.supported || ["1280x720"];
  const canUseReference = !!selectedCapability?.reference_image_support;
  const canUseFirstLast = !!selectedCapability?.first_last_frame;
  const canUseExtend = !!selectedCapability?.extend;

  return (
    <div className="space-y-5">
      <VideoWorkflowCanvas projectId={projectId} capabilities={capabilities} option={option} onChangeOption={onChange} />
      <div className="rounded-md border border-border bg-muted/20 p-4">
        <div className="mb-4 flex items-center gap-2">
          <Film className="h-4 w-4 text-primary" />
          <div>
            <div className="t-module">视频模型选择</div>
            <div className="t-caption text-muted-foreground">
              本地演示默认创建 6 个镜头任务；真实成片专项可按需要切换生成范围。
            </div>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-4">
          <div className="space-y-2">
            <Label className="t-caption text-muted-foreground">模型</Label>
            <Select
              value={option.model}
              onValueChange={(model) => {
                const next = capabilities.find((item) => item.model === model);
                onChange({
                  ...option,
                  model,
                  size: next?.resolution?.supported[0] || option.size,
                  mode: next?.first_last_frame ? "first_last_frame" : next?.extend ? "extend" : "text",
                });
              }}
            >
              <SelectTrigger className="h-10 bg-card">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {capabilities.map((item) => (
                  <SelectItem key={item.model} value={item.model}>
                    {item.model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="t-caption text-muted-foreground">尺寸</Label>
            <Select
              value={option.size}
              onValueChange={(size) => onChange({ ...option, size })}
            >
              <SelectTrigger className="h-10 bg-card">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {sizeOptions.map((size) => (
                  <SelectItem key={size} value={size}>
                    {size}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="t-caption text-muted-foreground">模式</Label>
            <Select
              value={option.mode}
              onValueChange={(mode) =>
                onChange({ ...option, mode: mode as VideoModelOption["mode"] })
              }
            >
              <SelectTrigger className="h-10 bg-card">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="text">文生视频</SelectItem>
                {canUseReference && <SelectItem value="reference">参考图</SelectItem>}
                {canUseFirstLast && <SelectItem value="first_last_frame">首尾帧</SelectItem>}
                {canUseExtend && <SelectItem value="extend">延长</SelectItem>}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="t-caption text-muted-foreground">生成范围</Label>
            <div className="flex h-10 items-center justify-between rounded-md border border-border bg-card px-3">
              <span className="t-body text-muted-foreground">
                {option.fullRun ? "完整 6 段" : "1 段 smoke"}
              </span>
              <Switch
                checked={option.fullRun}
                onCheckedChange={(fullRun) => onChange({ ...option, fullRun })}
              />
            </div>
          </div>
        </div>
        {selectedCapability && (
          <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_1.2fr]">
            <div className="rounded-md border border-border bg-card p-3">
              <div className="t-caption text-muted-foreground">能力限制</div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <ToneBadge tone={selectedCapability.reference_image_support ? "success" : "neutral"}>
                  {selectedCapability.reference_image_support
                    ? `参考图最多 ${selectedCapability.max_reference_images} 张`
                    : "无参考图"}
                </ToneBadge>
                {selectedCapability.first_last_frame && <ToneBadge tone="warning">首尾帧</ToneBadge>}
                {selectedCapability.video_edit && <ToneBadge tone="warning">视频修改</ToneBadge>}
                {selectedCapability.extend && <ToneBadge tone="warning">延长至 15s</ToneBadge>}
                <ToneBadge tone="success">查询带 token</ToneBadge>
              </div>
            </div>
            <div className="rounded-md border border-border bg-card p-3">
              <div className="t-caption text-muted-foreground">推荐用途</div>
              <p className="mt-1 t-body text-foreground/85">
                {selectedCapability.recommended_use}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Tab: 结果 ---------- */

function ResultTab({ stage }: { stage?: WorkflowStage }) {
  if (!stage) return null;
  if (!stage.result) {
    return (
      <EmptyState
        title="暂无结果"
        desc="运行完成后将在此显示该阶段的产出。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="space-y-3">
      <div className="t-overline text-muted-foreground/70">阶段产出</div>
      <div className="whitespace-pre-wrap rounded-md border border-border bg-muted/30 p-4 t-body text-foreground/90">
        {stage.result}
      </div>
    </div>
  );
}

function EditableNodeResult({
  stage,
  value,
  courseAnchor,
  onChange,
  onSave,
  saving,
}: {
  stage?: WorkflowStage;
  value: string;
  courseAnchor?: string;
  onChange: (value: string) => void;
  onSave: () => void;
  saving: boolean;
}) {
  if (!stage) return null;
  if (!stage.result) {
    return (
      <EmptyState
        title={`暂无${stage.title}`}
        desc="点击“生成草稿”后将在这里查看并轻量编辑当前节点产出。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  const isLessonPlan = stage.key === "open-lesson-plan";
  const structuredSummary = !isLessonPlan
    ? buildEditableNodeSummary(stage, value || stage.result, courseAnchor)
    : null;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-overline text-muted-foreground/70">
            {isLessonPlan ? "公开课教案编辑" : `${stage.title}内容核对`}
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            {isLessonPlan
              ? "在这里修改教案正文，保存后再确认进入下一步。"
              : "先用分区摘要核对当前产出；需要改复杂结构时，请在开发诊断中处理。"}
          </p>
        </div>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={onSave}
          disabled={saving || !value.trim()}
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? "保存中" : isLessonPlan ? "保存教案" : "保存产出"}
        </Button>
      </div>

      {isLessonPlan && <LessonPlanStructureSummary value={value || stage.result} />}

      {structuredSummary && (
        <div className="grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="border-border bg-muted/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="t-module">{structuredSummary.title}</div>
                <p className="mt-1 t-caption text-muted-foreground">
                  {structuredSummary.desc}
                </p>
              </div>
              <ToneBadge tone="info">{structuredSummary.badge}</ToneBadge>
            </div>
            <div className="mt-4 space-y-3">
              {structuredSummary.items.map((item, index) => (
                <div
                  key={`${item.label}-${index}`}
                  className="rounded-md border border-border bg-card px-3 py-2.5"
                >
                  <div className="t-caption text-muted-foreground">{item.label}</div>
                  <div className="mt-1 t-body text-foreground/90">{item.value}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="border-border bg-card p-4">
            <div className="t-module">编辑入口说明</div>
            <div className="mt-3 space-y-2 t-body text-foreground/85">
              <p>1. 先检查左侧摘要是否符合课堂导入视频意图。</p>
              <p>2. 需要调整时，优先改教师可读内容；复杂结构交给开发诊断处理。</p>
              <p>3. 保存后再确认通过，系统会推进到下一步。</p>
            </div>
            <div className="mt-4 rounded-md border border-warning/25 bg-warning/5 px-3 py-2 t-caption text-muted-foreground">
              如果出现字段级错误，页面会提示需要补充的具体内容。
            </div>
          </Card>
        </div>
      )}

      <details className="rounded-md border border-border bg-card" open>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
          <span className="t-module">
            {isLessonPlan ? "教案文本" : "高级内容编辑"}
          </span>
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        </summary>
        <div className="border-t border-border p-4">
      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-[360px] bg-card font-mono text-[0.82rem] leading-relaxed"
        placeholder={`生成${stage.title}后可在这里轻量编辑文本...`}
      />
        </div>
      </details>
    </div>
  );
}

function LessonPlanStructureSummary({ value }: { value: string }) {
  const content = parseJsonObject(value);
  const introDesigns = getArray(content.intro_designs).filter(isRecord);
  const requiredFields = [
    "video_theme",
    "eye_catch_tag",
    "anchor_to_lesson",
    "classroom_entry_question",
    "no_pre_teach",
    "entry_position",
    "recommend_reason",
  ];
  const filledIntroFields = introDesigns.reduce((count, design) => {
    return count + requiredFields.filter((field) => getStringValue(design[field]).trim()).length;
  }, 0);
  const totalIntroFields = Math.max(1, introDesigns.length * requiredFields.length);

  return (
    <div className="grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
      <Card className="border-border bg-muted/20 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="t-module">教案主结构</div>
            <p className="mt-1 t-caption text-muted-foreground">
              用于确认教案是否已具备后续导入视频链路所需输入。
            </p>
          </div>
          <ToneBadge tone={introDesigns.length >= 9 ? "success" : "warning"}>
            {introDesigns.length}/9 套
          </ToneBadge>
        </div>
        <div className="mt-4 space-y-3">
          {[
            ["教材锚点", getStringValue(content.textbook_anchor)],
            ["教学目标", getStringValue(content.teaching_objectives)],
            ["重难点", getStringValue(content.key_difficulty)],
            ["教学流程", getStringValue(content.teaching_flow)],
            ["板书设计", getStringValue(content.blackboard_design)],
          ].map(([label, raw]) => (
            <div key={label} className="rounded-md border border-border bg-card px-3 py-2.5">
              <div className="t-caption text-muted-foreground">{label}</div>
              <div className="mt-1 t-body text-foreground/90">{clipText(raw, 120)}</div>
            </div>
          ))}
        </div>
      </Card>
      <Card className="border-border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="t-module">导入视频候选方案</div>
            <p className="mt-1 t-caption text-muted-foreground">
              重点检查课程锚点、课堂落点问题和不提前讲解内容是否已填充。
            </p>
          </div>
          <ToneBadge tone={filledIntroFields === totalIntroFields ? "success" : "warning"}>
            {filledIntroFields}/{totalIntroFields} 字段
          </ToneBadge>
        </div>
        <div className="mt-4 grid gap-2">
          {introDesigns.slice(0, 9).map((design, index) => (
            <div key={getStringValue(design.design_id) || index} className="rounded-md border border-border bg-muted/20 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="t-body font-medium">
                  {getStringValue(design.title) || `导入方案 ${index + 1}`}
                </div>
                <ToneBadge tone="info">
                  {introTypeLabel(getStringValue(design.type))}
                </ToneBadge>
              </div>
              <div className="mt-2 grid gap-1.5 t-caption text-muted-foreground sm:grid-cols-2">
                <span>主题：{clipText(getStringValue(design.video_theme), 48)}</span>
                <span>吸睛点：{clipText(getStringValue(design.eye_catch_tag), 48)}</span>
                <span>课程锚点：{clipText(getStringValue(design.anchor_to_lesson), 64)}</span>
                <span>课堂落点问题：{clipText(getStringValue(design.classroom_entry_question), 64)}</span>
                <span>不提前讲解内容：{clipText(getStringValue(design.no_pre_teach), 64)}</span>
                <span>进入位置：{clipText(getStringValue(design.entry_position), 48)}</span>
              </div>
            </div>
          ))}
          {introDesigns.length === 0 && (
            <div className="rounded-md border border-dashed border-border bg-muted/20 px-3 py-4 text-center t-caption text-muted-foreground">
              还没有读到导入视频候选方案，请先生成或刷新教案内容。
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function IntroSelectionResult({
  stage,
  value,
  lessonPlanResult,
  onChange,
  onSave,
  saving,
  actionError,
  showAdvancedJson = true,
}: {
  stage?: WorkflowStage;
  value: string;
  lessonPlanResult: string;
  onChange: (value: string) => void;
  onSave: () => void;
  saving: boolean;
  actionError?: string | null;
  showAdvancedJson?: boolean;
}) {
  if (!stage) return null;
  if (!stage.result) {
    return (
      <EmptyState
        title="暂无视频导入方案"
        desc="点击“生成草稿”后将在这里展示科普类、应用类、故事类候选方案。"
        icon={<Film className="h-5 w-5" />}
      />
    );
  }
  const content = parseJsonObject(value || stage.result);
  const lessonPlanContent = parseJsonObject(lessonPlanResult);
  const designs = normalizeIntroDesigns(lessonPlanContent);
  const selectedIds = getStringArray(content.selected_design_ids);
  const selectedId = getStringValue(content.primary_design_id) || selectedIds[0] || designs[0]?.id || "";
  const selectedDesign = designs.find((design) => design.id === selectedId);
  const selectedAnchor = getStringValue(content[SELECTED_ANCHOR_KEY]);
  const anchorError = validateIntroSelectionAnchor(value || stage.result);

  function selectDesign(id: string) {
    const design = designs.find((item) => item.id === id);
    const next = {
      ...content,
      primary_design_id: id,
      selected_design_ids: [id],
      [SELECTED_ANCHOR_KEY]: design?.anchor || getStringValue(content[SELECTED_ANCHOR_KEY]),
      selection_reason:
        getStringValue(content.selection_reason) ||
        "已选择该方案作为导入视频主线，可继续生成视频剧本。",
    };
    onChange(JSON.stringify(next, null, 2));
  }

  function updateSelectedAnchor(anchor: string) {
    const next = {
      ...content,
      primary_design_id: selectedId,
      selected_design_ids: selectedId ? [selectedId] : selectedIds,
      [SELECTED_ANCHOR_KEY]: anchor,
      selection_reason:
        getStringValue(content.selection_reason) ||
        "教师已确认课程锚点，并将其作为导入视频和课堂衔接的硬约束。",
    };
    onChange(JSON.stringify(next, null, 2));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-overline text-muted-foreground/70">视频导入候选方案</div>
          <p className="mt-1 t-caption text-muted-foreground">
            选择方案后重点确认课程锚点、课堂落点问题和不提前讲解内容；课程锚点会作为视频结尾接回课堂的硬约束。
          </p>
        </div>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={onSave}
          disabled={saving || !value.trim() || Boolean(anchorError)}
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {saving ? "保存中" : "保存选择"}
        </Button>
      </div>

      {designs.length > 0 && (
        <div className="grid gap-3 lg:grid-cols-3">
          {designs.map((design) => {
            const selected = design.id === selectedId;
            return (
              <button
                key={design.id}
                type="button"
                onClick={() => selectDesign(design.id)}
                className={cn(
                  "rounded-md border bg-card p-4 text-left transition-colors focus-ring",
                  selected
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/30 hover:bg-muted/30",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <ToneBadge tone={selected ? "success" : "info"}>
                    {introTypeLabel(design.type)}
                  </ToneBadge>
                  <span className="t-caption text-muted-foreground">
                    推荐 {design.score}/5
                  </span>
                </div>
                <div className="mt-3 t-module">{design.title}</div>
                <p className="mt-2 t-body text-foreground/85">{design.hook}</p>
                <p className="mt-3 t-caption text-muted-foreground">
                  课程锚点：{design.anchor}
                </p>
                <p className="mt-1 t-caption text-muted-foreground">
                  课堂落点问题：{design.entryQuestion}
                </p>
                <p className="mt-1 t-caption text-muted-foreground">
                  不提前讲解内容：{design.noPreTeach}
                </p>
                {selected && (
                  <div className="mt-3 inline-flex items-center gap-1.5 t-caption font-medium text-primary">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    已选择
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}

      <Card className="border-border bg-muted/20 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="t-module">课程锚点确认</div>
            <p className="mt-1 t-caption text-muted-foreground">
              先从候选方案自动带入，也可以手工改成最终版；保存和确认前必须填写且不少于 10 个字。它只负责把独立视频自然接回课堂，不提前讲解本课知识点。
            </p>
          </div>
          {selectedDesign && (
            <ToneBadge tone="info">来自 {selectedDesign.title}</ToneBadge>
          )}
        </div>
        <div className="mt-3">
          <Label className="t-caption text-muted-foreground">课堂衔接点</Label>
          <Textarea
            value={selectedAnchor}
            onChange={(event) => updateSelectedAnchor(event.target.value)}
            className={cn(
              "mt-1 min-h-24 bg-card text-[0.9rem] leading-relaxed",
              anchorError && "border-destructive focus-visible:ring-destructive",
            )}
            placeholder="例如：小兔子数不清萝卜，引出数清楚才能解决问题"
          />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <p className={cn("t-caption", anchorError ? "text-destructive" : "text-muted-foreground")}>
              {anchorError || "用于说明导入视频最后如何自然接回本节课，后续脚本会沿用这句话。"}
            </p>
            <span className="t-caption text-muted-foreground">
              {selectedAnchor.trim().length} 字
            </span>
          </div>
        </div>
        {actionError && (
          <div className="mt-3 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2 t-caption text-destructive">
            {actionError}
          </div>
        )}
      </Card>

      {showAdvancedJson && (
        <details className="rounded-md border border-border bg-card">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
            <span className="t-module">JSON 高级编辑入口</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </summary>
          <div className="border-t border-border p-4">
            <Textarea
              value={value}
              onChange={(event) => onChange(event.target.value)}
              className="min-h-[260px] bg-card font-mono text-[0.82rem] leading-relaxed"
              placeholder="可轻量编辑选择结果 JSON..."
            />
          </div>
        </details>
      )}
    </div>
  );
}

function VideoAssetResult({
  projectId,
  stage,
  value,
  tasks,
  tasksStatus,
  tasksError,
  onChange,
  onSave,
  saving,
  onRefresh,
  onRetryTask,
  showAdvancedJson = true,
  showProviderDetails = true,
}: {
  projectId: string;
  stage?: WorkflowStage;
  value: string;
  tasks: ApiTask[];
  tasksStatus: LoadStatus;
  tasksError?: string | null;
  onChange: (value: string) => void;
  onSave: () => void;
  saving: boolean;
  onRefresh: () => void;
  onRetryTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  showAdvancedJson?: boolean;
  showProviderDetails?: boolean;
}) {
  if (!stage) return null;
  if (!stage.result) {
    return (
      <EmptyState
        title="暂无图片资产"
        desc="点击“生成草稿”后，这里会展示图片生成任务、预览、失败原因和重试入口。"
        icon={<FileImage className="h-5 w-5" />}
      />
    );
  }

  const content = parseJsonObject(value || stage.result);
  const assets = getArray(content.assets).filter(isRecord);
  const imageTasks = tasks.filter((task) => task[TASK_NODE_KEY] === "intro_video_asset");

  async function retryTask(taskId: string) {
    const res = await onRetryTask(projectId, taskId);
    if (!res.ok) {
      toast.error(safeProviderErrorMessage(res.msg || "图片任务重试失败"));
      return;
    }
    toast.success("已重新提交图片任务");
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-overline text-muted-foreground/70">资产与首帧状态</div>
          <p className="mt-1 t-caption text-muted-foreground">
            这里展示参考图、首帧方向、成功预览和失败原因；未真实生成时会显示等待或失败，不冒充完成素材。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={onRefresh}
            disabled={tasksStatus === "loading"}
          >
            {tasksStatus === "loading" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            刷新任务
          </Button>
          <Button
            size="sm"
            className="gap-1.5"
            onClick={onSave}
            disabled={saving || !value.trim()}
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {saving ? "保存中" : "保存资产"}
          </Button>
        </div>
      </div>

      {tasksStatus === "error" && (
        <ProviderFailureNotice message={tasksError || "任务列表读取失败"} />
      )}

      <div className="grid gap-3 lg:grid-cols-2">
        {(assets.length ? assets : imageTasks).map((item, index) => {
          const asset = isApiTask(item) ? taskToAssetRecord(item) : item;
          const assetId = getStringValue(asset.asset_id) || `asset_${index + 1}`;
          const task = imageTasks.find((candidate) => taskAssetId(candidate) === assetId);
          const imagePath =
            getStringValue(task?.image_path) ||
            getStringValue(task?.result.image_path) ||
            getStringValue(asset.image_path) ||
            normalizeImagePath(getStringValue(asset.storage_path));
          const imageHref = imagePath ? resolveProjectImageDownloadUrl(projectId, imagePath) : "";
          const status = task?.status || getStringValue(asset.status) || "pending";
          const failed = status === "failed";
          const providerId = providerTaskId(task);
          return (
            <Card key={assetId} className="overflow-hidden border-border bg-card">
              {imageHref && !failed ? (
                <div className="aspect-video border-b border-border bg-muted/30">
                  <img
                    src={imageHref}
                    alt={`${assetId} 预览`}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="flex aspect-video items-center justify-center border-b border-border bg-muted/30">
                  {statusInProgress(status) ? (
                    <div className="flex items-center gap-2 t-body text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      生成中
                    </div>
                  ) : failed ? (
                    <div className="flex items-center gap-2 t-body text-destructive">
                      <AlertTriangle className="h-4 w-4" />
                      生成失败
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 t-body text-muted-foreground">
                      <FileImage className="h-4 w-4" />
                      等待图片
                    </div>
                  )}
                </div>
              )}
              <div className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="t-module">{assetId}</div>
                    <div className="mt-1 break-all t-caption text-muted-foreground">
                      {getStringValue(asset.source_prompt_id) || getStringValue(task?.payload.prompt) || "素材任务"}
                    </div>
                  </div>
                  <ToneBadge tone={taskStatusTone(status)}>{taskStatusLabel(status)}</ToneBadge>
                </div>
                <div className="grid gap-2 t-caption text-muted-foreground sm:grid-cols-2">
                  <span>素材记录：{task?.task_id || "未创建"}</span>
                  <span>{showProviderDetails ? "服务记录" : "生成记录"}：{providerId && showProviderDetails ? maskProviderTaskId(providerId) : task?.task_id || "未返回"}</span>
                  <span>预览文件：{imagePath ? "已准备" : "待生成"}</span>
                  <span>{task?.retryable || task?.result.retryable ? "失败可重试" : "按状态处理"}</span>
                </div>
                {failed && (
                  <ProviderFailureNotice
                    message={taskFailureMessage(task) || "图片生成失败，可重试。"}
                  />
                )}
                {failed && task && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={() => void retryTask(task.task_id)}
                  >
                    <RotateCcw className="h-4 w-4" />
                    重试该图片
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {showAdvancedJson && (
        <details className="rounded-md border border-border bg-card">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
            <span className="t-module">JSON 高级编辑入口</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </summary>
          <div className="border-t border-border p-4">
            <Textarea
              value={value}
              onChange={(event) => onChange(event.target.value)}
              className="min-h-[300px] bg-card font-mono text-[0.82rem] leading-relaxed"
              placeholder="可轻量编辑图片资产 JSON..."
            />
          </div>
        </details>
      )}
    </div>
  );
}

function FinalVideoResult({
  projectId,
  stage,
  tasks,
  tasksStatus,
  tasksError,
  actionError,
  showProviderDetails = true,
  pptExportStatus,
  pptExportError,
  pptExportResult,
  onRefresh,
  onRefreshTask,
  onRetryTask,
  onExportPpt,
}: {
  projectId: string;
  stage?: WorkflowStage;
  tasks: ApiTask[];
  tasksStatus: LoadStatus;
  tasksError?: string | null;
  actionError?: string | null;
  showProviderDetails?: boolean;
  pptExportStatus: LoadStatus;
  pptExportError: string | null;
  pptExportResult: ApiPptExport | null;
  onRefresh: () => void;
  onRefreshTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onRetryTask: (projectId: string, taskId: string) => Promise<{ ok: boolean; msg?: string }>;
  onExportPpt: () => void;
}) {
  if (!stage) return null;
  const videoPath = getFinalVideoPath(stage, tasks, pptExportResult);
  const videoDownloadHref = videoPath
    ? resolveProjectOutputDownloadUrl(projectId, videoPath)
    : "";
  const providerUnavailable = isOctoProviderError(actionError);

  if (!stage.result) {
    return (
      <div className="space-y-4">
        {providerUnavailable && <FinalVideoProviderNotice error={actionError} />}
        <FinalVideoDownloadPanel
          href={videoDownloadHref}
          videoPath={videoPath}
          placeholderReady={Boolean(videoPath)}
        />
        <PptExportPanel
          status={pptExportStatus}
          error={pptExportError}
          result={pptExportResult}
          onExport={onExportPpt}
        />
        <EmptyState
        title="暂无视频生成任务"
          desc="配置画面比例和生成范围后点击“生成草稿”，这里只承诺创建本地演示任务，不代表真实成片质量。"
          icon={<Film className="h-5 w-5" />}
        />
      </div>
    );
  }
  const content = parseJsonObject(stage.result);
  const clips = getArray(content.clips);
  const placeholderReady = Boolean(videoPath);
  const videoTasks = tasks.filter((task) => task[TASK_NODE_KEY] === "final_video");

  async function refreshTask(taskId: string) {
    const res = await onRefreshTask(projectId, taskId);
    if (!res.ok) {
      toast.error(safeProviderErrorMessage(res.msg || "clip 状态刷新失败"));
      return;
    }
    toast.success("已刷新 clip 状态");
  }

  async function retryTask(taskId: string) {
    const res = await onRetryTask(projectId, taskId);
    if (!res.ok) {
      toast.error(safeProviderErrorMessage(res.msg || "clip 重试失败"));
      return;
    }
    toast.success("已重新提交 clip 任务");
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="t-overline text-muted-foreground/70">
            {placeholderReady ? "演示视频文件可下载" : "视频生成任务"}
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            {placeholderReady
              ? "这只是本地演示用视频文件，不代表真实成片质量。"
              : "当前只证明已创建视频片段任务和生成记录，不承诺真实成片质量。"}
            真实成片需要看到视频片段、中文旁白、字幕和合成文件都完成后再验收。
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onRefresh}
          disabled={tasksStatus === "loading"}
        >
          {tasksStatus === "loading" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          刷新任务
        </Button>
      </div>

      {tasksStatus === "error" && (
        <div className="rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2 t-body text-destructive">
          {tasksError || "任务列表读取失败"}
        </div>
      )}

      {providerUnavailable && <FinalVideoProviderNotice error={actionError} />}

      <FinalVideoDownloadPanel
        href={videoDownloadHref}
        videoPath={videoPath}
        placeholderReady={placeholderReady}
      />

      <PptExportPanel
        status={pptExportStatus}
        error={pptExportError}
        result={pptExportResult}
        onExport={onExportPpt}
      />

      <FinalVideoAudioPanel content={content} />

      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="border-border bg-muted/25 p-4">
          <div className="t-caption text-muted-foreground">生成状态</div>
          <div className="mt-1 t-module">{stage.status === "running" ? "任务已创建" : stage.status}</div>
        </Card>
        <Card className="border-border bg-muted/25 p-4">
          <div className="t-caption text-muted-foreground">镜头数量</div>
          <div className="mt-1 t-module">{formatUnknownCount(content.clip_count, clips.length)}</div>
        </Card>
        <Card className="border-border bg-muted/25 p-4">
          <div className="t-caption text-muted-foreground">任务数量</div>
          <div className="mt-1 t-module">{videoTasks.length}</div>
        </Card>
      </div>

      {videoTasks.length > 0 ? (
        <div className="space-y-2">
          {videoTasks.map((task) => {
            const downloadPath =
              getStringValue(task.download_path) ||
              getStringValue(task.result.download_path) ||
              getStringValue(task.clip_path) ||
              getStringValue(task.result.clip_path);
            const providerId = providerTaskId(task);
            const failed = task.status === "failed";
            const clipStatus = clipTaskStatusLabel(task);
            return (
              <div
                key={task.task_id}
                className="rounded-md border border-border bg-card p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <ListChecks className="h-4 w-4 shrink-0 text-primary" />
                    <span className="t-body font-medium">{task.task_id}</span>
                  </div>
                  <ToneBadge tone={taskStatusTone(task.status)}>
                    {clipStatus}
                  </ToneBadge>
                </div>
                <div className="mt-2 grid gap-2 t-caption text-muted-foreground sm:grid-cols-4">
                  <span>镜头：{String(task.payload.shot_id || "-")}</span>
                  <span>生成方案：{String(task.payload.model || "-")}</span>
                  <span>尺寸：{String(task.payload.size || "-")}</span>
                  <span>{showProviderDetails ? "服务记录" : "生成记录"}：{providerId && showProviderDetails ? maskProviderTaskId(providerId) : task.task_id}</span>
                </div>
                {downloadPath && (
                  <div className="mt-2 flex flex-wrap items-center gap-2 t-caption text-muted-foreground">
                    <span>片段文件：已准备</span>
                    {isMp4Path(downloadPath) && (
                      <a
                        className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                        href={resolveProjectOutputDownloadUrl(projectId, downloadPath)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <Download className="h-3.5 w-3.5" />
                        下载 MP4
                      </a>
                    )}
                  </div>
                )}
                {failed && (
                  <ProviderFailureNotice
                    message={taskFailureMessage(task) || "视频生成失败，可重试。"}
                  />
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={() => void refreshTask(task.task_id)}
                  >
                    <RefreshCw className="h-4 w-4" />
                    刷新该镜头
                  </Button>
                  {failed && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      onClick={() => void retryTask(task.task_id)}
                    >
                      <RotateCcw className="h-4 w-4" />
                      重试该镜头
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          title="任务列表为空"
          desc="如果刚触发生成，请点击刷新任务；演示环境通常会很快返回生成结果。"
          icon={<ListChecks className="h-5 w-5" />}
        />
      )}
    </div>
  );
}

function FinalVideoAudioPanel({ content }: { content: Record<string, unknown> }) {
  const audioVerified = content.audio_verified === true;
  const englishAudioDetected = content.english_audio_detected === true;
  const narrationAudioPath = getStringValue(content.narration_audio_path);
  const subtitleSrtPath = getStringValue(content.subtitle_srt_path);
  const concatManifestPath = getStringValue(content.concat_manifest_path);
  const voiceGender = getStringValue(content.voice_gender) || "待确认";
  const voiceLanguage = getStringValue(content.voice_language) || "待确认";

  return (
    <Card className="border-border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Film className="h-4 w-4 text-primary" />
            <span className="t-module">旁白与合成状态</span>
            <ToneBadge tone={audioVerified ? "success" : "warning"}>
              {audioVerified ? "音频已校验" : "待校验"}
            </ToneBadge>
            <ToneBadge tone={englishAudioDetected ? "warning" : "success"}>
              {englishAudioDetected ? "疑似英文音频" : "中文旁白"}
            </ToneBadge>
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            最终视频应使用中文旁白，声线可配置；视频原声在合成阶段丢弃或静音。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ToneBadge tone={voiceGender === "male" ? "success" : "warning"}>
            声线：{voiceGender}
          </ToneBadge>
          <ToneBadge tone={voiceLanguage === "zh-CN" ? "success" : "warning"}>
            语言：{voiceLanguage}
          </ToneBadge>
        </div>
      </div>
      <div className="mt-4 grid gap-2 t-caption text-muted-foreground md:grid-cols-3">
        <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
          <div className="font-medium text-foreground/85">旁白音频</div>
          <div className="mt-1 break-all">{narrationAudioPath || "待生成"}</div>
        </div>
        <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
          <div className="font-medium text-foreground/85">字幕 SRT</div>
          <div className="mt-1 break-all">{subtitleSrtPath || "待生成"}</div>
        </div>
        <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
          <div className="font-medium text-foreground/85">合成记录</div>
          <div className="mt-1 break-all">{concatManifestPath || "待生成"}</div>
        </div>
      </div>
    </Card>
  );
}

function FinalVideoProviderNotice({ error }: { error?: string | null }) {
  return (
    <div className="rounded-md border border-warning/30 bg-warning/10 px-3 py-2 t-body text-foreground">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
        <div>
          <div className="font-medium">真实视频服务暂不可用</div>
          <p className="mt-1 t-caption text-muted-foreground">
            可以先用本地演示文件走通下载和检查，也可以稍后重试；错误摘要：
            {safeProviderErrorMessage(error || "生成服务暂时不可用")}。
          </p>
        </div>
      </div>
    </div>
  );
}

function ProviderFailureNotice({ message }: { message: string }) {
  return (
    <div className="mt-2 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2 t-caption text-destructive">
      {safeProviderErrorMessage(message)} 可重试时请点击当前任务的重试按钮。
    </div>
  );
}

function FinalVideoDownloadPanel({
  href,
  videoPath,
  placeholderReady,
}: {
  href: string;
  videoPath: string;
  placeholderReady: boolean;
}) {
  return (
    <Card className="border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Film className="h-4 w-4 text-primary" />
            <span className="t-module">
              {placeholderReady ? "演示视频文件可下载" : "演示视频文件"}
            </span>
            <ToneBadge tone={placeholderReady ? "warning" : "neutral"}>
              {placeholderReady ? "演示文件可下载" : "等待生成记录"}
            </ToneBadge>
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            {placeholderReady
              ? "这只是本地演示用视频文件，不代表真实成片质量。"
              : "生成最终视频后，这里会显示 MP4 下载入口。"}
          </p>
          {videoPath && (
            <div className="mt-2 break-all t-caption text-muted-foreground">
              文件：已准备
            </div>
          )}
        </div>
        {href && (
          <Button asChild size="sm" className="shrink-0 gap-1.5">
            <a href={href} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" />
              下载 MP4
            </a>
          </Button>
        )}
      </div>
    </Card>
  );
}

function PptExportPanel({
  status,
  error,
  result,
  onExport,
}: {
  status: LoadStatus;
  error: string | null;
  result: ApiPptExport | null;
  onExport: () => void;
}) {
  const downloadHref = result?.download_url
    ? resolveApiDownloadUrl(result.download_url)
    : "";

  return (
    <Card className="border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <FileType2 className="h-4 w-4 text-primary" />
            <span className="t-module">PPTX 文件</span>
            {status === "ready" && (
              <ToneBadge tone="success">已生成</ToneBadge>
            )}
            {status === "error" && (
              <ToneBadge tone="danger">生成失败</ToneBadge>
            )}
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            生成可下载的 PPTX 草稿文件。真实上课前仍需要逐页检查讲法、素材和排版。
          </p>
          {result?.filename && (
            <div className="mt-2 t-caption text-muted-foreground">
              文件：{result.filename}
            </div>
          )}
          {error && (
            <div className="mt-2 rounded-md border border-destructive/25 bg-destructive/5 px-3 py-2 t-caption text-destructive">
              {error}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={onExport}
            disabled={status === "loading"}
          >
            {status === "loading" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileType2 className="h-4 w-4" />
            )}
            {status === "loading" ? "生成中..." : "生成 PPTX"}
          </Button>
          {downloadHref && (
            <Button asChild size="sm" className="gap-1.5">
              <a href={downloadHref} target="_blank" rel="noreferrer">
                <Download className="h-4 w-4" />
                下载 PPTX
              </a>
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

type UserStepView = {
  step: UserWorkspaceStep;
  state: UserStepState;
  stage?: WorkflowStage;
  completedCount: number;
  totalCount: number;
};

function buildUserStepViews(
  definitions: UserWorkspaceStep[],
  stages: WorkflowStage[],
): UserStepView[] {
  let previousComplete = true;
  let currentAssigned = false;
  return definitions.map((step) => {
    const stepStages = stages.filter((stage) => step.stageKeys.includes(stage.key));
    const totalCount = Math.max(1, stepStages.length);
    const completedCount = stepStages.filter(isStageComplete).length;
    const complete = stepStages.length > 0 && completedCount === stepStages.length;
    const activeStage =
      stepStages.find((stage) => !isStageComplete(stage)) ||
      stepStages[stepStages.length - 1];
    let state: UserStepState;
    if (complete) {
      state = "completed";
    } else if (previousComplete && !currentAssigned) {
      state = "current";
      currentAssigned = true;
    } else {
      state = "locked";
    }
    if (!complete) previousComplete = false;
    return {
      step,
      state,
      stage: activeStage,
      completedCount,
      totalCount,
    };
  });
}

function buildUserStepViewsFromWorkspace(
  definitions: UserWorkspaceStep[],
  workspace: { steps?: ApiWorkspaceStep[]; current_step_id?: string | null } | null,
  stages: WorkflowStage[],
): UserStepView[] | null {
  if (!workspace?.steps?.length) return null;
  const fallbackViews = buildUserStepViews(definitions, stages);
  return definitions.map((definition) =>
    workspaceStepToUserStepView(
      definition,
      findWorkspaceStepForUserStep(workspace, definition),
      workspace.current_step_id,
      stages,
      fallbackViews.find((view) => view.step.id === definition.id),
    ),
  );
}

function workspaceStepToUserStepView(
  definition: UserWorkspaceStep,
  workspaceStep: ApiWorkspaceStep | undefined,
  currentStepId: string | null | undefined,
  stages: WorkflowStage[],
  fallbackView?: UserStepView,
): UserStepView {
  const fallback = fallbackView || buildUserStepViews([definition], stages)[0];
  if (!workspaceStep) return fallback;
  const stepStages = stages.filter((stage) => definition.stageKeys.includes(stage.key));
  const totalCount = Math.max(1, workspaceStep.sub_gates?.length || stepStages.length);
  const completedCount = workspaceStep.sub_gates?.length
    ? workspaceStep.sub_gates.filter((gate) =>
        ["completed", "complete", "approved", "done", "passed"].includes(workspaceSubGateState(gate)),
      ).length
    : stepStages.filter(isStageComplete).length;
  return {
    step: definition,
    state: workspaceStepStateToUserStepState(workspaceStep, currentStepId),
    stage:
      stepStages.find((stage) => !isStageComplete(stage)) ||
      stepStages[stepStages.length - 1] ||
      fallback.stage,
    completedCount,
    totalCount,
  };
}

function workspaceStepStateToUserStepState(
  step: ApiWorkspaceStep,
  currentStepId: string | null | undefined,
): UserStepState {
  const state = String(step.state || "");
  if (["completed", "complete", "approved", "done", "passed"].includes(state)) return "completed";
  if (step.step_id === currentStepId) return "current";
  if (["current", "ready", "pending_confirm", "needs_review", "running"].includes(state)) return "current";
  return "locked";
}

function findUserStepViewForStage(
  views: UserStepView[],
  stageKey?: string,
): UserStepView | undefined {
  if (!stageKey) return undefined;
  return views.find((view) => view.step.stageKeys.includes(stageKey));
}

function findValidUserStepOverride(
  views: UserStepView[],
  stepId?: UserStepId | null,
): UserStepView | undefined {
  if (!stepId) return undefined;
  const view = views.find((item) => item.step.id === stepId);
  if (!view || view.state === "locked") return undefined;
  return view;
}

function findUserStepViewForWorkspaceStep(
  views: UserStepView[],
  workspaceStepId?: string | null,
): UserStepView | undefined {
  if (!workspaceStepId) return undefined;
  return views.find((view) => workspaceStepMatchesUserStep(workspaceStepId, view.step));
}

function findWorkspaceStepForUserStep(
  workspace: { steps?: ApiWorkspaceStep[] } | null,
  userStep: UserWorkspaceStep,
): ApiWorkspaceStep | undefined {
  return workspace?.steps?.find((step) => workspaceStepMatchesUserStep(step.step_id, userStep));
}

function workspaceStepMatchesUserStep(workspaceStepId: string, userStep: UserWorkspaceStep): boolean {
  const normalized = normalizeWorkspaceStepId(workspaceStepId);
  if (normalized === userStep.id) return true;
  return userStep.stageKeys.some((key) => normalizeWorkspaceStepId(key) === normalized);
}

function normalizeWorkspaceStepId(stepId: string): string {
  const normalized = stepId.replace(/_/g, "-");
  const aliases: Record<string, UserStepId> = {
    "project-meta": "project-info",
    "project-config": "project-info",
    "visual-contract": "project-info",
    "character-dict": "project-info",
    "textbook-parse": "textbook-content",
    "lesson-plan": "lesson-plan",
    "open-lesson-plan": "lesson-plan",
    "intro-selection": "intro-video-plan",
    "video-design-import": "intro-video-plan",
    "ppt-plan": "ppt-draft",
    "ppt-script": "ppt-draft",
    "ppt-assets": "ppt-draft",
    "pptx-generation": "ppt-draft",
    "pptx-artifact": "ppt-draft",
    "video-script": "video-generation",
    "intro-video-script": "video-generation",
    "video-screenplay": "video-generation",
    "intro-video-screenplay": "video-generation",
    "video-assets": "video-generation",
    "intro-video-asset": "video-generation",
    "storyboard": "video-generation",
    "final-video": "video-generation",
    "final-delivery": "final-delivery",
  };
  return aliases[normalized] || normalized;
}

function getDefaultStageKeyForUserStep(
  step: UserWorkspaceStep,
  stages: WorkflowStage[],
  currentStageKey?: string,
): string | null {
  if (currentStageKey && step.stageKeys.includes(currentStageKey)) {
    return currentStageKey;
  }
  const stepStages = stages.filter((stage) => step.stageKeys.includes(stage.key));
  return (
    stepStages.find((stage) => !isStageComplete(stage))?.key ||
    stepStages[stepStages.length - 1]?.key ||
    null
  );
}

function isStageComplete(stage: WorkflowStage): boolean {
  return stage.status === "approved" || stage.status === "skipped";
}

function getLockedStepMessage(target: UserStepView, views: UserStepView[]): string {
  const index = views.findIndex((view) => view.step.id === target.step.id);
  const previous = index > 0 ? views[index - 1] : undefined;
  if (previous) {
    return `请先完成【${previous.step.label}】后，再进入【${target.step.label}】。`;
  }
  return "请先完成上一阶段。";
}

function getPrimaryActionLabel(
  stepState: UserStepState,
  stage: WorkflowStage,
  actionStatus: LoadStatus,
  isFinalVideoStage: boolean,
): string {
  if (actionStatus === "loading" || (stage.status === "running" && !isFinalVideoStage)) {
    return "生成中";
  }
  if (stepState === "locked") return "暂未解锁";
  if (stepState === "completed") return "查看下一步";
  if (!stage.result || stage.status === "not_started") return "生成草稿";
  if (stage.status === "input_required") return "保存修改";
  if (stage.status === "running" && isFinalVideoStage) return "查看任务状态";
  if (stage.status === "failed" || stage.status === "blocked") return "重新生成";
  return "确认并进入下一步";
}

function formatUserFacingError(message: string): string {
  const generationInput = formatGenerationInputError(message);
  if (generationInput) return generationInput;
  const blocked = /UPSTREAM_NOT_APPROVED|dependency_gate_blocked|R010/i.test(message);
  if (blocked) return "请先确认上一阶段内容，再继续当前步骤。";
  const ruleViolation = /RULE_VIOLATION|hard_block/i.test(message);
  if (ruleViolation) return "当前内容没有通过质量检查，请按提示修改后再确认。";
  const provider = /provider|API|token|OCTO|MINIMAX/i.test(message);
  if (provider) return "生成服务暂时不可用，请稍后重试或联系开发人员查看诊断。";
  return clipText(message, 120);
}

function formatGenerationInputError(message: string): string | null {
  if (/GENERATION_INPUT_INVALID|Unsupported textbook type for MVP|No textbook uploaded/i.test(message)) {
    return "教材内容没有正确关联，请回到新建项目重新选择教材和本课内容，或刷新后重试。";
  }
  return null;
}

function getUserEvidenceLabel(file: string): string {
  if (/\.pdf$/i.test(file)) return "教材页段";
  if (/\.md$/i.test(file)) return "教材内容";
  if (/\.(png|jpe?g|webp)$/i.test(file)) return "图片";
  return "材料";
}

function resolveMarkdownForStage(stage: WorkflowStage, value: string): string {
  const raw = value || stage.result;
  if (!raw.trim()) return "";
  const content = parseJsonObject(raw);
  const directMarkdown =
    getStringValue(content.markdown) ||
    getStringValue(content.lesson_plan_markdown) ||
    getStringValue(content.content_markdown);
  if (directMarkdown) return directMarkdown;
  const sections = [
    ["# 公开课教案", getStringValue(content.title) || stage.title],
    ["## 教材锚点", getStringValue(content.textbook_anchor)],
    ["## 教学目标", getStringValue(content.teaching_objectives)],
    ["## 教学重难点", getStringValue(content.key_difficulty)],
    ["## 教学流程", getStringValue(content.teaching_flow)],
    ["## 板书设计", getStringValue(content.blackboard_design)],
  ];
  const markdown = sections
    .filter(([, body]) => body.trim())
    .map(([heading, body]) => `${heading}\n\n${body.trim()}`)
    .join("\n\n");
  return markdown || raw;
}

function parseEditableNodeContent(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) return { text: "" };
  try {
    return JSON.parse(trimmed) as unknown;
  } catch {
    return { text: value };
  }
}

type EditableSummary = {
  title: string;
  desc: string;
  badge: string;
  items: Array<{ label: string; value: string }>;
};

function buildEditableNodeSummary(
  stage: WorkflowStage,
  value: string,
  courseAnchor?: string,
): EditableSummary {
  const content = parseJsonObject(value);
  if (stage.key === "textbook-parse") {
    const summary = buildTextbookContentSummary("", stage, value);
    return {
      title: "教材解析与核验摘要",
      desc: "核对课时、教材页码、本课要点和解析状态。",
      badge: "教材内容",
      items: [
        { label: "课时标题", value: summary.title },
        { label: "教材页码", value: summary.pages },
        { label: "本课要点", value: summary.knowledge.join("、") || "待确认" },
        { label: "解析状态", value: summary.status },
        { label: "教材依据", value: summary.basis },
        { label: "页段预览", value: summary.sliceUrl ? "教材页段可预览" : "等待页段生成" },
      ],
    };
  }
  if (stage.key === "video-script") {
    const anchor =
      getStringValue(content[SELECTED_ANCHOR_KEY]) ||
      getStringValue(content.anchor_to_lesson);
    return {
      title: "视频文稿摘要",
      desc: "先看导入类型、课程锚点和完整旁白，再决定是否需要修改文稿。",
      badge: "文稿",
      items: [
        { label: "视频类型", value: introTypeLabel(getStringValue(content.video_type)) },
        { label: "课程锚点", value: anchor || "待补充" },
        {
          label: "旁白正文",
          value: clipText(getStringValue(content.narration_full_text), 160),
        },
        {
          label: "禁用元素",
          value: getStringArray(content.banned_elements).join("、") || "待补充",
        },
      ],
    };
  }

  if (stage.key === "video-screenplay") {
    const scenes = getArray(content.scenes).filter(isRecord);
    return {
      title: "分场剧本摘要",
      desc: "按场次查看画面、时长和旁白片段。",
      badge: `${scenes.length || 0} 场`,
      items: scenes.slice(0, 4).map((scene, index) => ({
        label: getStringValue(scene.scene_id) || `场次 ${index + 1}`,
        value: [
          formatSeconds(scene.duration_sec),
          getStringValue(scene.scene_description),
          clipText(getStringValue(scene.narration_segment), 72),
        ]
          .filter(Boolean)
          .join(" · ") || "待补充",
      })),
    };
  }

  if (stage.key === "video-assets") {
    const assets = getArray(content.assets).filter(isRecord);
    return {
      title: "视频资产摘要",
      desc: "检查参考图、首帧方向和素材状态，未真实生成时只作为占位。",
      badge: `${assets.length || 0} 项`,
      items: assets.slice(0, 6).map((asset, index) => ({
        label: getStringValue(asset.asset_id) || `素材 ${index + 1}`,
        value: [
          getStringValue(asset.source_prompt_id),
          getStringValue(asset.storage_path) ? "素材文件已准备" : "",
          getStringValue(asset.status),
        ]
          .filter(Boolean)
          .join(" · ") || "待补充",
      })),
    };
  }

  if (stage.key === "storyboard") {
    const shots = getArray(content.shots).filter(isRecord);
    const anchorItem = courseAnchor
      ? [{ label: "课程锚点", value: courseAnchor }]
      : [];
    return {
      title: "分镜脚本摘要",
      desc: "按镜头查看主体、时长、旁白和首帧状态，便于教师理解视频结构。",
      badge: `${shots.length || 0} 镜`,
      items: [
        ...anchorItem,
        ...shots.slice(0, 6).map((shot, index) => ({
          label: getStringValue(shot.shot_id) || `镜头 ${index + 1}`,
          value: [
            formatSeconds(shot.duration_sec),
            getStringValue(shot.main_subject),
            clipText(getStringValue(shot.subtitle) || getStringValue(shot.narration_slice), 72),
            getStringValue(shot.first_frame_test_status),
          ]
            .filter(Boolean)
            .join(" · ") || "待补充",
        })),
      ],
    };
  }

  if (stage.key === "final-delivery") {
    return buildFinalDeliverySummary(content);
  }

  return {
    title: `${stage.title}摘要`,
    desc: "当前内容已生成，详细结构请在开发诊断中查看。",
    badge: "内容摘要",
    items: Object.entries(content)
      .slice(0, 6)
      .map(([key, raw]) => ({
        label: `摘要 ${key.length + 1}`,
        value: clipText(formatPreviewValue(raw), 96),
      })),
  };
}

function buildFinalDeliverySummary(content: Record<string, unknown>): EditableSummary {
  const checks = getArray(content.checks).filter(isRecord);
  const readyCount = checks.filter((check) => {
    const passed = check.passed;
    return passed === true || passed === "true" || passed === "passed";
  }).length;
  const totalCount = checks.length;
  const fileItems = [
    {
      label: "教案材料",
      value: getStringValue(content.lesson_plan_path) ? "已整理，可下载核对" : "待整理",
    },
    {
      label: "PPT 文件",
      value: getStringValue(content.pptx_final_path) ? "已准备，可下载试讲" : "待生成",
    },
    {
      label: "导入视频",
      value: getStringValue(content.video_final_path) ? "已准备，可播放核对" : "待生成",
    },
  ];
  const reviewItems = [
    {
      label: "材料检查",
      value: totalCount > 0 ? `${readyCount}/${totalCount} 项已通过` : "等待检查结果",
    },
    {
      label: "交付状态",
      value: content.gate_passed === true ? "材料齐全，等待教师确认" : "还有材料需要补齐",
    },
    {
      label: "试讲提醒",
      value: "下载后请重点核对数学内容、PPT 页面和导入视频衔接。",
    },
  ];
  return {
    title: "最终交付摘要",
    desc: "核对教案、PPT、导入视频和检查结果是否齐全。",
    badge: content.gate_passed === true ? "待确认" : "待补齐",
    items: [...fileItems, ...reviewItems],
  };
}

function buildTextbookContentSummary(
  projectId: string,
  stage: WorkflowStage,
  value: string,
): TextbookContentSummary {
  const content = parseJsonObject(value);
  const meta = isRecord(content.textbook_meta) ? content.textbook_meta : {};
  const selected = isRecord(content.selected_knowledge_point)
    ? content.selected_knowledge_point
    : {};
  const selectedPages = isRecord(selected.source_pages) ? selected.source_pages : {};
  const selectedAsset = isRecord(selected.asset_package) ? selected.asset_package : {};
  const artifacts = isRecord(content.parse_artifacts) ? content.parse_artifacts : {};
  const title =
    getStringValue(selected.title) ||
    getStringValue(content.lesson_title) ||
    getStringValue(meta.title) ||
    stage.title;
  const pages = [
    userPageLabel(
      "教材页",
      getStringValue(selectedAsset.textbook_pages) ||
        getStringValue(selectedPages.textbook_pages),
    ),
    userPageLabel(
      "PDF 页",
      getStringValue(selectedAsset.pdf_pages) ||
        getStringValue(selectedPages.pdf_pages),
    ),
  ].filter(Boolean).join("；") || "待确认";
  const coreKnowledge =
    getStringArray(content.core_knowledge_points)
      .concat(getStringArray(selected.keywords))
      .map((item) => item.trim())
      .filter(Boolean);
  const status = [
    userStatusLabel(
      getStringValue(selectedAsset.parse_status) ||
        getStringValue(meta.review_status) ||
        getStringValue(content.parse_status),
    ),
    userStatusLabel(getStringValue(selectedAsset.review_status)),
  ].filter(Boolean).join(" / ") || "待确认";
  const basisParts = [
    pages !== "待确认" ? pages : "",
    getStringValue(selectedAsset.checksum) ? "已生成核验信息" : "",
    selectedHasMarkdown(selected, selectedAsset, artifacts) ? "教材内容已生成" : "",
  ].filter(Boolean);
  const markdown =
    getStringValue(selected.markdown) ||
    getStringValue(content.markdown) ||
    getStringValue(content.content_markdown);
  const assetDownloadUrls = isRecord(selectedAsset.download_urls)
    ? selectedAsset.download_urls
    : {};
  const slicePath =
    getStringValue(assetDownloadUrls.slice_pdf) ||
    getStringValue(selected.slice_pdf_path) ||
    getStringValue(artifacts.slice_pdf_path) ||
    getStringValue(selectedAsset.slice_pdf_path);

  return {
    title,
    pages,
    knowledge: Array.from(new Set(coreKnowledge)).slice(0, 8),
    status,
    basis: basisParts.join("；") || "来自教材库课时资产包、页段 PDF 和教材内容。",
    markdown,
    sliceUrl: resolveTextbookSlicePreviewUrl(projectId, slicePath),
  };
}

function buildPptxArtifactSummary(stage: WorkflowStage, value: string): {
  filename: string;
  downloadHref: string;
  ready: boolean;
} {
  const content = parseJsonObject(value || stage.result);
  const pptxPath = getStringValue(content.pptx_path);
  const downloadUrl = getStringValue(content.download_url);
  const filename =
    getStringValue(content.filename) ||
    pptxPath.split(/[\\/]/).pop() ||
    downloadUrl.split(/[\\/]/).pop() ||
    "PPTX 草稿文件";
  return {
    filename,
    downloadHref: downloadUrl ? resolveApiDownloadUrl(downloadUrl) : "",
    ready: Boolean(downloadUrl || pptxPath || filename !== "PPTX 草稿文件"),
  };
}

function selectedHasMarkdown(
  selected: Record<string, unknown>,
  asset: Record<string, unknown>,
  artifacts: Record<string, unknown>,
): boolean {
  return Boolean(
    getStringValue(selected.markdown) ||
      getStringValue(selected.markdown_path) ||
      getStringValue(selected.mineru_md_path) ||
      getStringValue(asset.mineru_md_path) ||
      getStringValue(asset.markdown_path) ||
      getStringValue(artifacts.mineru_md_path) ||
      getStringValue(artifacts.markdown_path),
  );
}

function userPageLabel(label: string, value: string): string {
  return value ? `${label} ${value}` : "";
}

function userStatusLabel(value: string): string {
  const map: Record<string, string> = {
    split_ready: "已切分",
    needs_review: "待确认",
    approved: "已确认",
    unreviewed: "待确认",
    failed: "解析失败",
    parsed: "已解析",
  };
  return value ? map[value] || value : "";
}

function resolveTextbookSlicePreviewUrl(projectId: string, path: string): string {
  if (!projectId || !path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/projects/")) return resolveApiDownloadUrl(path);
  const normalized = normalizeTextbookAssetPath(path);
  if (!normalized) return "";
  return resolveApiDownloadUrl(
    `/projects/${encodeURIComponent(projectId)}/files/${normalized
      .split("/")
      .map(encodeURIComponent)
      .join("/")}`,
  );
}

function normalizeTextbookAssetPath(path: string): string {
  const normalized = path.replaceAll("\\", "/").replace(/^\/+/, "");
  const knowledgePointIndex = normalized.indexOf("knowledge-points/");
  if (knowledgePointIndex >= 0) return normalized.slice(knowledgePointIndex);
  const filesIndex = normalized.indexOf("/files/");
  if (filesIndex >= 0) return normalized.slice(filesIndex + "/files/".length);
  return normalized;
}

function parseJsonObject(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value) as unknown;
    return isRecord(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function pptArtifactExportFromStage(stage: WorkflowStage): ApiPptExport | null {
  const content = parseJsonObject(stage.result);
  const downloadUrl = stage.artifact?.download_url || getStringValue(content.download_url);
  const pptxPath = stage.artifact?.pptx_path || getStringValue(content.pptx_path);
  if (!downloadUrl || !pptxPath) return null;
  const filename = getStringValue(content.filename) || pptxPath.split(/[\\/]/).pop() || "lesson-video-demo.pptx";
  return {
    filename,
    path: pptxPath,
    download_url: downloadUrl,
    video_path: stage.artifact?.video_path || getStringValue(content.video_path),
  };
}

function validateIntroSelectionAnchor(value: string): string | null {
  const content = parseJsonObject(value);
  const anchor = getStringValue(content[SELECTED_ANCHOR_KEY]).trim();
  if (!anchor) return "请先填写课程锚点";
  if (anchor.length < 10) return "课程锚点不能少于 10 个字";
  return null;
}

function resolveCourseAnchorForStage(stageKey: string, stages: WorkflowStage[]): string {
  if (!["video-script", "storyboard"].includes(stageKey)) return "";
  const introSelection = parseJsonObject(
    stages.find((item) => item.key === "video-design-import")?.result || "",
  );
  const script = parseJsonObject(
    stages.find((item) => item.key === "video-script")?.result || "",
  );
  return (
    getStringValue(introSelection[SELECTED_ANCHOR_KEY]) ||
    getStringValue(script[SELECTED_ANCHOR_KEY]) ||
    getStringValue(script.anchor_to_lesson)
  );
}

function getFinalVideoPath(
  stage: WorkflowStage,
  tasks: ApiTask[],
  pptExportResult: ApiPptExport | null,
): string {
  const content = parseJsonObject(stage.result);
  const contentVideoPath = getStringValue(content.video_path);
  if (contentVideoPath) return contentVideoPath;

  const contentDownloadPath = getStringValue(content.download_path);
  if (isMp4Path(contentDownloadPath)) return contentDownloadPath;

  for (const task of tasks) {
    const downloadPath = getStringValue(task.result.download_path);
    if (isMp4Path(downloadPath)) return downloadPath;
    const videoPath = getStringValue(task.result.video_path);
    if (isMp4Path(videoPath)) return videoPath;
  }

  return pptExportResult?.video_path || "";
}

function resolveProjectOutputDownloadUrl(projectId: string, path: string): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/projects/")) return resolveApiDownloadUrl(path);
  const normalized = path.replace(/^\/+/, "");
  const outputsIndex = normalized.indexOf("outputs/");
  const outputPath = outputsIndex >= 0
    ? normalized.slice(outputsIndex)
    : normalized;
  return resolveApiDownloadUrl(
    `/projects/${encodeURIComponent(projectId)}/${outputPath}`,
  );
}

function resolveProjectImageDownloadUrl(projectId: string, path: string): string {
  if (!path) return "";
  if (path.startsWith("/projects/")) return resolveApiDownloadUrl(path);
  const normalized = path.replace(/^\/+/, "");
  const filename = normalized.split(/[\\/]/).pop() || normalized;
  return resolveApiDownloadUrl(
    `/projects/${encodeURIComponent(projectId)}/images/${encodeURIComponent(filename)}`,
  );
}

function isMp4Path(value: string): boolean {
  return /\.mp4(?:$|\?)/i.test(value);
}

function isImagePath(value: string): boolean {
  return /\.(png|jpe?g|webp)(?:$|\?)/i.test(value);
}

function normalizeImagePath(value: string): string {
  return isImagePath(value) ? value : "";
}

function isApiTask(value: unknown): value is ApiTask {
  return isRecord(value) && typeof value.task_id === "string";
}

function taskToAssetRecord(task: ApiTask): Record<string, unknown> {
  return {
    asset_id: taskAssetId(task),
    source_prompt_id: task.payload.prompt,
    image_path: task.image_path || task.result.image_path,
    status: task.status,
  };
}

function taskAssetId(task: ApiTask): string {
  return getStringValue(task.payload.asset_id) || getStringValue(task.result.asset_id);
}

function providerTaskId(task?: ApiTask): string {
  if (!task) return "";
  return (
    getStringValue(task.provider_task_id) ||
    getStringValue(task.result.provider_task_id) ||
    getStringValue(task.payload.provider_task_id)
  );
}

function maskProviderTaskId(value: string): string {
  if (!value) return "";
  if (value.length <= 10) return `${value.slice(0, 2)}***${value.slice(-2)}`;
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

function taskFailureMessage(task?: ApiTask): string {
  if (!task) return "";
  const code =
    getStringValue(task.error_code) ||
    getStringValue(task.result.error_code) ||
    "PROVIDER_FAILED";
  const httpStatus = getStringValue(task.result.http_status);
  const retryable = task.retryable || task.result.retryable;
  const message = task.error_message || `${code}${httpStatus ? ` / HTTP ${httpStatus}` : ""}`;
  return `${code}: ${message}${retryable ? "，可重试" : ""}`;
}

function safeProviderErrorMessage(message: string): string {
  const withoutSecrets = message
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer <redacted>")
    .replace(/sk-[A-Za-z0-9._-]+/gi, "<redacted-key>")
    .replace(/api[_-]?key[\"'\s:=]+[^,\"'\s}]+/gi, "api_key=<redacted>");
  const codeMatch = withoutSecrets.match(/\b[A-Z][A-Z0-9_]{4,}\b/);
  const httpMatch = withoutSecrets.match(/HTTP\s*\d{3}|\b\d{3}\b/);
  const parts = [
    codeMatch?.[0],
    httpMatch?.[0]?.startsWith("HTTP") ? httpMatch[0] : httpMatch ? `HTTP ${httpMatch[0]}` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" / ") : clipText(withoutSecrets, 120);
}

function statusInProgress(status: string): boolean {
  return ["submitting", "queued", "processing", "running", "loading"].includes(status);
}

function taskStatusLabel(status: string): string {
  const map: Record<string, string> = {
    submitting: "生成中",
    queued: "生成中",
    processing: "生成中",
    running: "生成中",
    generated: "已完成",
    completed: "已完成",
    downloaded: "已完成",
    failed: "失败",
  };
  return map[status] || status || "未知";
}

function clipTaskStatusLabel(task: ApiTask): string {
  const downloadStatus = getStringValue(task.result.download_status);
  if (downloadStatus === "downloading") return "下载中";
  if (downloadStatus === "downloaded") return "已完成";
  if (downloadStatus === "failed") return "失败";
  return taskStatusLabel(task.status);
}

function taskStatusTone(status: string) {
  if (status === "failed") return "danger";
  if (statusInProgress(status)) return "warning";
  if (["completed", "downloaded", "generated"].includes(status)) return "success";
  return "info";
}

function isOctoProviderError(value?: string | null): boolean {
  return Boolean(value && value.includes("OCTO_REQUEST_FAILED"));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function getStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function getStringValue(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function formatUnknownCount(value: unknown, fallback = 0): string {
  if (typeof value === "number") return String(value);
  if (typeof value === "string" && value.trim()) return value;
  return String(fallback);
}

function formatSeconds(value: unknown): string {
  if (typeof value === "number") return `${value} 秒`;
  if (typeof value === "string" && value.trim()) return `${value} 秒`;
  return "";
}

function formatPreviewValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return `${value.length} 项`;
  if (isRecord(value)) return JSON.stringify(value);
  return "—";
}

function clipText(value: string, length: number): string {
  const trimmed = value.trim();
  if (!trimmed) return "待补充";
  return trimmed.length > length ? `${trimmed.slice(0, length)}...` : trimmed;
}

function introTypeLabel(value: string): string {
  const key = value as VideoIntroType;
  return VIDEO_TYPE_LABEL[key] || value || "方案";
}

function normalizeIntroDesigns(content: Record<string, unknown>): Array<{
  id: string;
  type: string;
  title: string;
  hook: string;
  anchor: string;
  entryQuestion: string;
  noPreTeach: string;
  score: number;
}> {
  const rawDesigns = getArray(content.intro_designs);
  return rawDesigns
    .map((item, index) => {
      if (!isRecord(item)) return null;
      return {
        id: getStringValue(item.design_id) || `design_${index + 1}`,
        type: getStringValue(item.type) || "application",
        title: getStringValue(item.title) || `候选方案 ${index + 1}`,
        hook: getStringValue(item.hook) || "待补充导入钩子。",
        anchor: getStringValue(item.anchor_to_lesson) || "待补充课程落点。",
        entryQuestion: getStringValue(item.classroom_entry_question) || "待补充课堂落点问题。",
        noPreTeach: getStringValue(item.no_pre_teach) || "待补充不提前讲解内容。",
        score:
          typeof item.recommend_score === "number"
            ? item.recommend_score
            : Number(item.recommend_score) || 0,
      };
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
}

/* ---------- Tab: 证据 ---------- */

function EvidenceTab({
  stage,
  onPreview,
}: {
  stage?: WorkflowStage;
  onPreview?: (file: string) => void;
}) {
  if (!stage) return null;
  if (!stage.evidence || stage.evidence.length === 0) {
    return (
      <EmptyState
        title="暂无证据文件"
        desc="该阶段尚无产出的文件或资产。"
        icon={<FileText className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="t-caption text-muted-foreground">
          共 {stage.evidence.length} 个文件，点击文件名可预览内容。
        </p>
      </div>
      <ul className="space-y-1.5">
        {stage.evidence.map((file, i) => {
          const meta = getFileMeta(file);
          const Icon = meta.Icon;
          return (
            <li key={i}>
              <button
                type="button"
                onClick={() => onPreview?.(file)}
                className="group flex w-full items-center gap-2.5 rounded-md border border-border bg-card px-3 py-2.5 text-left transition-colors hover:border-primary/30 hover:bg-muted/50 focus-ring"
              >
                <span className={cn("shrink-0", meta.tone)}>
                  <Icon className="h-4 w-4" />
                </span>
                <span className="t-body min-w-0 flex-1 truncate text-foreground">
                  {file}
                </span>
                <span className="t-caption shrink-0 text-muted-foreground group-hover:text-foreground">
                  {meta.label}
                </span>
                <Maximize2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50 transition-colors group-hover:text-primary" />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ---------- Tab: 日志 ---------- */

function LogsTab({ stage }: { stage?: WorkflowStage }) {
  if (!stage) return null;
  if (!stage.logs || stage.logs.length === 0) {
    return (
      <EmptyState
        title="暂无日志"
        desc="该阶段运行后日志将在此显示。"
        icon={<Info className="h-5 w-5" />}
      />
    );
  }
  return (
    <div className="max-h-96 overflow-y-auto scroll-fine rounded-md border border-border bg-muted/20">
      <ul className="divide-y divide-border">
        {stage.logs.map((log) => {
          const meta = LOG_LEVEL_META[log.level];
          const Icon = meta.Icon;
          return (
            <li key={log.id} className="flex items-start gap-2.5 px-3 py-2.5">
              <Icon
                className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", meta.color)}
              />
              <span className="w-20 shrink-0 font-mono t-caption text-muted-foreground">
                {log.time}
              </span>
              <span className="flex-1 t-body text-foreground/90">
                {log.message}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ---------- 视频方案卡片网格 ---------- */

function VideoPlanGrid({
  plans,
  selectedIds,
  onToggleSelect,
  onAccept,
  onEdit,
  onCompare,
  onRegenerate,
}: {
  plans: VideoIntroPlan[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onAccept: (planId: string) => void;
  onEdit: () => void;
  onCompare: () => void;
  onRegenerate: () => void;
}) {
  const selectedCount = selectedIds.length;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="t-overline text-muted-foreground/70">
            视频剧本方案
          </div>
          <p className="mt-1 t-caption text-muted-foreground">
            共 {plans.length} 套方案，按推荐分数排序。勾选 2-3 套可对比，采纳后可继续推进。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={selectedCount >= 2 ? "default" : "outline"}
            className="gap-1.5"
            onClick={onCompare}
            disabled={selectedCount < 2}
          >
            <GitCompare className="h-4 w-4" />
            对比{selectedCount > 0 ? ` (${selectedCount})` : ""}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={onRegenerate}
          >
            <RefreshCw className="h-4 w-4" />
            重新生成方案
          </Button>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {plans.map((plan) => (
          <VideoPlanCard
            key={plan.id}
            plan={plan}
            selected={selectedIds.includes(plan.id)}
            onToggleSelect={() => onToggleSelect(plan.id)}
            onAccept={onAccept}
            onEdit={onEdit}
          />
        ))}
      </div>
    </div>
  );
}

/* ---------- 视频方案卡片 ---------- */

function VideoPlanCard({
  plan,
  selected,
  onToggleSelect,
  onAccept,
  onEdit,
}: {
  plan: VideoIntroPlan;
  selected: boolean;
  onToggleSelect: () => void;
  onAccept: (planId: string) => void;
  onEdit: () => void;
}) {
  const isRecommended = plan.rank === 1;
  return (
    <Card
      className={cn(
        "relative border bg-card p-0 shadow-soft transition-all",
        plan.accepted
          ? "border-primary/40 bg-primary/[0.02] ring-1 ring-primary/20"
          : selected
            ? "border-primary/50 ring-1 ring-primary/20"
            : isRecommended
              ? "border-bronze/30"
              : "border-border",
      )}
    >
      {/* 推荐角标 */}
      {isRecommended && (
        <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-bronze/15 px-2 py-0.5 t-caption font-medium text-bronze">
          <Star className="h-3 w-3" />
          推荐
        </span>
      )}
      <div className="p-4 sm:p-5">
        {/* 选择条 */}
        <div className="flex items-center gap-2.5 border-b border-border pb-3">
          <Checkbox
            id={`sel-${plan.id}`}
            checked={selected}
            onCheckedChange={onToggleSelect}
            className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
          />
          <label
            htmlFor={`sel-${plan.id}`}
            className="t-caption cursor-pointer select-none text-muted-foreground"
          >
            加入对比
          </label>
        </div>
        {/* header row */}
        <div className="flex flex-wrap items-center gap-2 pr-16">
          <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 t-caption font-medium text-muted-foreground">
            #{plan.rank} 排序
          </span>
          <span className="inline-flex items-center rounded-md bg-success/10 px-2 py-0.5 t-caption font-medium text-success">
            {plan.score} 分
          </span>
          <span className="inline-flex items-center rounded-md bg-info/10 px-2 py-0.5 t-caption font-medium text-info">
            {VIDEO_TYPE_LABEL[plan.type]}
          </span>
          {plan.accepted && (
            <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 t-caption font-medium text-primary">
              <Check className="h-3 w-3" />
              已采纳
            </span>
          )}
        </div>

        {/* title */}
        <h4 className="mt-3 t-module">{plan.title}</h4>

        <Separator className="my-4" />

        {/* term rows */}
        <dl className="space-y-2.5">
          <TermRow label="吸睛点" value={plan.hook} />
          <TermRow label="课程锚点" value={plan.courseAnchor} />
          <TermRow
            label="课堂落点问题"
            value={plan.classroomLandingQuestion}
          />
          <TermRow
            label="不提前讲解的内容"
            value={plan.avoidTeaching}
          />
          <TermRow label="接入教案的位置" value={plan.lessonEntryPoint} />
        </dl>

        <Separator className="my-4" />

        {/* reason */}
        <div className="flex gap-3">
          <span className="w-32 shrink-0 pt-0.5 t-caption text-muted-foreground">
            推荐理由
          </span>
          <p className="flex-1 t-body text-foreground/90">{plan.reason}</p>
        </div>

        {/* actions */}
        <div className="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
          <Button
            size="sm"
            className="gap-1.5"
            onClick={() => onAccept(plan.id)}
            disabled={plan.accepted}
          >
            <Check className="h-4 w-4" />
            {plan.accepted ? "已采纳" : "采纳"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={onEdit}
          >
            编辑
          </Button>
        </div>
      </div>
    </Card>
  );
}

/* ---------- 视频方案对比 Dialog ---------- */

const COMPARE_FIELDS: {
  key: keyof Pick<
    VideoIntroPlan,
    | "type"
    | "score"
    | "hook"
    | "courseAnchor"
    | "classroomLandingQuestion"
    | "avoidTeaching"
    | "lessonEntryPoint"
    | "reason"
  >;
  label: string;
}[] = [
  { key: "type", label: "视频类型" },
  { key: "score", label: "推荐分数" },
  { key: "hook", label: "吸睛点" },
  { key: "courseAnchor", label: "课程锚点" },
  { key: "classroomLandingQuestion", label: "课堂落点问题" },
  { key: "avoidTeaching", label: "不提前讲解" },
  { key: "lessonEntryPoint", label: "接入教案位置" },
  { key: "reason", label: "推荐理由" },
];

function VideoPlanCompareDialog({
  open,
  onOpenChange,
  plans,
  onAccept,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  plans: VideoIntroPlan[];
  onAccept: (id: string) => void;
}) {
  const bestScore = Math.max(...plans.map((p) => p.score), 0);

  // 计算差异高亮：某方案在某字段的值是否唯一（其他方案都没有相同值）
  // 仅对文本类字段生效
  const TEXT_FIELDS: (typeof COMPARE_FIELDS)[number]["key"][] = [
    "hook",
    "courseAnchor",
    "classroomLandingQuestion",
    "avoidTeaching",
    "lessonEntryPoint",
    "reason",
  ];
  const isUnique = (fieldKey: string, planId: string): boolean => {
    if (!TEXT_FIELDS.includes(fieldKey as never)) return false;
    const target = plans.find((p) => p.id === planId);
    if (!target) return false;
    const val = target[fieldKey as keyof VideoIntroPlan];
    if (typeof val !== "string") return false;
    const sameCount = plans.filter(
      (p) => p[fieldKey as keyof VideoIntroPlan] === val,
    ).length;
    return sameCount === 1;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[1100px] gap-0 p-0 shadow-lift" aria-describedby={undefined}>
        <DialogTitle className="sr-only">视频方案对比</DialogTitle>
        <DialogDescription className="sr-only">
          并排对比已选中的视频方案字段，便于择优采纳。
        </DialogDescription>
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary">
              <GitCompare className="h-4 w-4" />
            </span>
            <div>
              <div className="t-module">视频方案对比</div>
              <div className="t-caption text-muted-foreground">
                共 {plans.length} 套方案，按字段并排展示
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => onOpenChange(false)}
            aria-label="关闭"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <ScrollArea className="max-h-[70vh]">
          <div className="overflow-x-auto scroll-fine">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="sticky left-0 z-10 w-28 bg-muted/30 px-4 py-3 text-left align-top t-caption font-medium text-muted-foreground">
                    对比项
                  </th>
                  {plans.map((p) => (
                    <th
                      key={p.id}
                      className="min-w-[220px] border-l border-border px-4 py-3 text-left align-top"
                    >
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 t-caption font-medium text-muted-foreground">
                          #{p.rank}
                        </span>
                        {p.rank === 1 && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-bronze/15 px-1.5 py-0.5 t-caption font-medium text-bronze">
                            <Star className="h-3 w-3" /> 推荐
                          </span>
                        )}
                      </div>
                      <div className="mt-1.5 t-body font-medium text-foreground">
                        {p.title}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPARE_FIELDS.map((field, idx) => (
                  <tr
                    key={field.key}
                    className={cn(
                      "border-b border-border",
                      idx % 2 === 1 && "bg-muted/20",
                    )}
                  >
                    <td className="sticky left-0 z-10 bg-inherit px-4 py-3 align-top t-caption font-medium text-muted-foreground">
                      {field.label}
                    </td>
                    {plans.map((p) => {
                      const val = p[field.key];
                      const isBest =
                        field.key === "score" && val === bestScore;
                      const unique = isUnique(field.key, p.id);
                      return (
                        <td
                          key={p.id}
                          className={cn(
                            "relative border-l border-border px-4 py-3 align-top t-body text-foreground/90",
                            unique && "border-l-2 border-l-bronze/60 bg-bronze/[0.04]",
                          )}
                        >
                          {field.key === "type" ? (
                            <span className="inline-flex items-center rounded-md bg-info/10 px-1.5 py-0.5 t-caption font-medium text-info">
                              {VIDEO_TYPE_LABEL[val as VideoIntroType]}
                            </span>
                          ) : field.key === "score" ? (
                            <span
                              className={cn(
                                "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 t-caption font-medium",
                                isBest
                                  ? "bg-success/15 text-success"
                                  : "bg-muted text-muted-foreground",
                              )}
                            >
                              {isBest && <Star className="h-3 w-3" />}
                              {val} 分
                            </span>
                          ) : (
                            <span className="whitespace-pre-wrap">
                              {val}
                              {unique && (
                                <span className="ml-1.5 inline-flex items-center rounded bg-bronze/15 px-1 py-0.5 align-middle t-caption font-medium text-bronze">
                                  独特
                                </span>
                              )}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/30">
                  <td className="sticky left-0 z-10 bg-muted/30 px-4 py-3" />
                  {plans.map((p) => (
                    <td
                      key={p.id}
                      className="border-l border-border px-4 py-3"
                    >
                      <Button
                        size="sm"
                        className="gap-1.5"
                        disabled={p.accepted}
                        onClick={() => onAccept(p.id)}
                      >
                        <Check className="h-4 w-4" />
                        {p.accepted ? "已采纳" : "采纳此方案"}
                      </Button>
                    </td>
                  ))}
                </tr>
              </tfoot>
            </table>
          </div>
        </ScrollArea>
        {/* 图例 */}
        <div className="flex flex-wrap items-center gap-4 border-t border-border bg-muted/20 px-5 py-2.5">
          <span className="t-caption text-muted-foreground">图例：</span>
          <span className="inline-flex items-center gap-1.5 t-caption text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded bg-bronze/15 px-1 py-0.5 text-bronze">
              独特
            </span>
            该方案独有内容
          </span>
          <span className="inline-flex items-center gap-1.5 t-caption text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded bg-success/15 px-1 py-0.5 text-success">
              <Star className="h-2.5 w-2.5" />
              最高分
            </span>
            推荐分数最高
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ---------- 证据文件预览 Dialog ---------- */

function getFileMeta(file: string): {
  Icon: React.ComponentType<{ className?: string }>;
  tone: string;
  label: string;
} {
  const ext = file.split(".").pop()?.toLowerCase();
  if (ext === "json")
    return { Icon: FileJson, tone: "text-info", label: "JSON 结构化数据" };
  if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext || ""))
    return { Icon: FileImage, tone: "text-bronze", label: "图片资源" };
  if (["pdf"].includes(ext || ""))
    return { Icon: FileType2, tone: "text-destructive", label: "PDF 文档" };
  if (["log", "txt"].includes(ext || ""))
    return { Icon: FileText, tone: "text-muted-foreground", label: "日志/文本" };
  return { Icon: FileText, tone: "text-muted-foreground", label: "文件" };
}

function mockPreviewContent(file: string): string {
  const ext = file.split(".").pop()?.toLowerCase();
  if (ext === "json") {
    return `{
  "stage": "textbook-parse",
  "version": "1.0",
  "parsedAt": "2026-06-12T09:25:00+08:00",
  "subject": "数学",
  "grade": "三年级",
  "lesson": "认识分数——分一分",
  "coreKnowledgePoints": [
    "二分之一的含义",
    "四分之一的含义",
    "分数各部分名称"
  ],
  "confidence": 0.94
}`;
  }
  if (ext === "log") {
    return `[2026-06-12 09:24:01] INFO  开始解析教材
[2026-06-12 09:24:14] INFO  识别 9 页，抽取结构化字段
[2026-06-12 09:25:00] INFO  解析完成，等待确认
[2026-06-12 09:30:12] INFO  教师确认解析结果`;
  }
  if (ext === "pdf") {
    return "该文件为 PDF 文档，演示环境暂不支持内嵌预览。\n实际环境中将在此处渲染文档内容。";
  }
  if (["png", "jpg", "jpeg"].includes(ext || "")) {
    return "该文件为图片资源，演示环境暂不支持内嵌预览。\n实际环境中将在此处显示缩略图。";
  }
  return "演示环境暂不支持该文件类型的内嵌预览。";
}

function EvidencePreviewDialog({
  file,
  onClose,
  stageTitle,
}: {
  file: string | null;
  onClose: () => void;
  stageTitle?: string;
}) {
  const meta = file ? getFileMeta(file) : null;
  const Icon = meta?.Icon || FileText;
  return (
    <Dialog open={!!file} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-[680px] gap-0 p-0 shadow-lift" aria-describedby={undefined}>
        <DialogTitle className="sr-only">证据文件预览</DialogTitle>
        <DialogDescription className="sr-only">
          预览阶段产出的证据文件内容。
        </DialogDescription>
        {file && meta && (
          <>
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex min-w-0 items-center gap-2.5">
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted",
                    meta.tone,
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <div className="t-module truncate">{file}</div>
                  <div className="t-caption text-muted-foreground">
                    {meta.label}
                    {stageTitle ? ` · ${stageTitle}` : ""}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-1.5 text-muted-foreground"
                  onClick={() => toast.info("演示版暂不支持下载")}
                >
                  <Download className="h-4 w-4" />
                  下载
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={onClose}
                  aria-label="关闭"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="bg-muted/20 p-5">
              <pre className="max-h-[55vh] overflow-auto scroll-fine rounded-md border border-border bg-card p-4 font-mono t-caption leading-relaxed text-foreground/85">
                <HighlightedPreview file={file} />
              </pre>
              <div className="mt-3 flex items-center gap-2 t-caption text-muted-foreground">
                <Eye className="h-3.5 w-3.5" />
                演示环境预览内容为模拟数据，仅作占位展示。
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function TermRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-32 shrink-0 pt-0.5 t-caption text-muted-foreground">
        {label}
      </dt>
      <dd className="flex-1 t-body text-foreground/90">{value}</dd>
    </div>
  );
}

/* ---------- 底部操作栏 ---------- */

function StageActions({
  canSave,
  canRegenerate,
  canApprove,
  canReject,
  canNext,
  isRunning,
  taskCreated = false,
  regenerateLabel = "重新生成",
  primaryRegenerateLabel = "生成草稿",
  actionLoading,
  showRefresh,
  onSave,
  onRefresh,
  onRegenerate,
  onApprove,
  onReject,
  onNext,
}: {
  canSave: boolean;
  canRegenerate: boolean;
  canApprove: boolean;
  canReject: boolean;
  canNext: boolean;
  isRunning: boolean;
  taskCreated?: boolean;
  regenerateLabel?: string;
  primaryRegenerateLabel?: string;
  actionLoading: boolean;
  showRefresh: boolean;
  onSave: () => void;
  onRefresh: () => void;
  onRegenerate: () => void;
  onApprove: () => void;
  onReject: () => void;
  onNext: () => void;
}) {
  const primaryAction = (() => {
    if (actionLoading) {
      return {
        label: "处理中",
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        onClick: onRegenerate,
        disabled: true,
      };
    }
    if (isRunning) {
      return {
        label: "运行中",
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        onClick: onRegenerate,
        disabled: true,
      };
    }
    if (taskCreated) {
      return {
        label: "查看任务状态",
        icon: <ListChecks className="h-4 w-4" />,
        onClick: onRefresh,
        disabled: actionLoading,
      };
    }
    if (canApprove) {
      return {
        label: "确认通过",
        icon: <Check className="h-4 w-4" />,
        onClick: onApprove,
        disabled: false,
      };
    }
    if (canNext) {
      return {
        label: "进入下一步",
        icon: <ArrowRight className="h-4 w-4" />,
        onClick: onNext,
        disabled: false,
      };
    }
    if (canRegenerate) {
      return {
        label: primaryRegenerateLabel,
        icon: <RefreshCw className="h-4 w-4" />,
        onClick: onRegenerate,
        disabled: false,
      };
    }
    return {
      label: "等待输入",
      icon: <Clock className="h-4 w-4" />,
      onClick: onSave,
      disabled: true,
    };
  })();

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onSave}
          disabled={!canSave || actionLoading}
        >
          <Save className="h-4 w-4" />
          保存
        </Button>
        {showRefresh && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={onRefresh}
            disabled={actionLoading}
          >
            <RefreshCw className="h-4 w-4" />
            刷新状态
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onRegenerate}
          disabled={!canRegenerate || actionLoading}
        >
          <RefreshCw
            className={cn("h-4 w-4", (isRunning || actionLoading) && "animate-spin")}
          />
          {isRunning || actionLoading ? "运行中" : regenerateLabel}
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={onReject}
          disabled={!canReject || actionLoading}
        >
          <RotateCcw className="h-4 w-4" />
          退回修改
        </Button>
        <Button
          size="sm"
          className="min-w-28 gap-1.5"
          onClick={primaryAction.onClick}
          disabled={primaryAction.disabled}
        >
          {primaryAction.icon}
          {primaryAction.label}
        </Button>
      </div>
    </div>
  );
}

/* ---------- 键盘快捷键提示 ---------- */

function KeyboardHint({ keys, label }: { keys: string[]; label: string }) {
  return (
    <div className="hidden items-center gap-1.5 sm:flex">
      <span className="t-caption text-muted-foreground">{label}</span>
      <span className="flex items-center gap-1">
        {keys.map((k) => (
          <kbd
            key={k}
            className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded border border-border bg-card px-1 font-mono text-[10px] text-muted-foreground shadow-sm"
          >
            {k}
          </kbd>
        ))}
      </span>
    </div>
  );
}

/* ---------- 语法高亮预览 ---------- */

/** 简易 JSON 语法高亮：用正则 tokenize，返回 React 节点数组。零外部依赖。 */
function highlightJson(jsonStr: string): React.ReactNode[] {
  // 按行处理，每行识别 key / string / number / boolean / null / punctuation
  const lines = jsonStr.split("\n");
  return lines.map((line, lineIdx) => {
    // 缩进
    const indentMatch = line.match(/^(\s*)/);
    const indent = indentMatch ? indentMatch[1] : "";
    const rest = line.slice(indent.length);
    // 匹配 "key": value 或 value
    const tokens: React.ReactNode[] = [];
    let key = 1;
    // key: "..." :
    const keyMatch = rest.match(/^"([^"\\]*(?:\\.[^"\\]*)*)"(\s*:\s*)/);
    if (keyMatch) {
      tokens.push(
        <span key={`k${key++}`} className="text-primary">{`"${keyMatch[1]}"`}</span>,
        <span key={`c${key++}`} className="text-muted-foreground">{keyMatch[2]}</span>,
      );
      const valuePart = rest.slice(keyMatch[0].length);
      tokens.push(...tokenizeValue(valuePart, key));
    } else {
      tokens.push(...tokenizeValue(rest, key));
    }
    return (
      <span key={lineIdx} className="block">
        {indent}
        {tokens}
      </span>
    );
  });
}

function tokenizeValue(s: string, keyBase: number): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  let key = keyBase * 100;
  // 简单分词：字符串、数字、布尔/null、标点
  const regex = /("(?:[^"\\]|\\.)*")|(\b-?\d+(?:\.\d+)?\b)|(\btrue\b|\bfalse\b|\bnull\b)|([{}\[\],])/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(s)) !== null) {
    if (m.index > last) {
      out.push(<span key={`t${key++}`}>{s.slice(last, m.index)}</span>);
    }
    if (m[1]) {
      // 字符串值
      out.push(<span key={`s${key++}`} className="text-success">{m[1]}</span>);
    } else if (m[2]) {
      out.push(<span key={`n${key++}`} className="text-bronze">{m[2]}</span>);
    } else if (m[3]) {
      out.push(<span key={`b${key++}`} className="text-info">{m[3]}</span>);
    } else if (m[4]) {
      out.push(<span key={`p${key++}`} className="text-muted-foreground">{m[4]}</span>);
    }
    last = regex.lastIndex;
  }
  if (last < s.length) {
    out.push(<span key={`t${key++}`}>{s.slice(last)}</span>);
  }
  return out;
}

/** 日志级别着色 */
function highlightLog(logStr: string): React.ReactNode[] {
  return logStr.split("\n").map((line, idx) => {
    const m = line.match(/^(\[[^\]]+\])\s+(INFO|WARN|ERROR|SUCCESS)\s+(.*)$/);
    if (m) {
      const [, ts, level, msg] = m;
      const levelColor =
        level === "ERROR"
          ? "text-destructive"
          : level === "WARN"
            ? "text-warning"
            : level === "SUCCESS"
              ? "text-success"
              : "text-info";
      return (
        <span key={idx} className="block">
          <span className="text-muted-foreground">{ts}</span>{" "}
          <span className={`font-semibold ${levelColor}`}>{level}</span>{" "}
          <span className="text-foreground/90">{msg}</span>
        </span>
      );
    }
    return <span key={idx} className="block">{line}</span>;
  });
}

function HighlightedPreview({ file }: { file: string }) {
  const ext = file.split(".").pop()?.toLowerCase();
  const content = mockPreviewContent(file);
  if (ext === "json") {
    return <>{highlightJson(content)}</>;
  }
  if (ext === "log" || ext === "txt") {
    return <>{highlightLog(content)}</>;
  }
  return <span className="whitespace-pre-wrap">{content}</span>;
}
