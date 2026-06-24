"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  confirmTextbookKnowledgePointAsset,
  extractTextbookKnowledgePointAssets,
  fetchLessonPlanLibrary,
  fetchLessonPlanLibraryItem,
  fetchTextbookKnowledgePointAsset,
  fetchTextbookKnowledgePoints,
  fetchTextbookLibrary,
  fetchTextbookParseJob,
  splitTextbookKnowledgePointAssets,
  uploadLessonPlanToLibrary,
  uploadTextbookToLibrary,
} from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import type {
  ApiLessonPlanLibraryItem,
  ApiTextbookKnowledgePoint,
  ApiTextbookKnowledgePointAsset,
  ApiTextbookKnowledgePoints,
  ApiTextbookLibraryItem,
  ApiTextbookParseJob,
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/common/StateViews";
import { ToneBadge } from "@/components/common/StatusBadge";
import {
  BookOpenCheck,
  CheckCircle2,
  FileText,
  Layers3,
  LibraryBig,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Upload,
} from "lucide-react";
import { toast } from "sonner";

type LoadState = "idle" | "loading" | "ready" | "error";

interface ActionLog {
  id: string;
  time: string;
  action: string;
  detail: string;
  tone: "success" | "warning" | "neutral";
}

export function AdminTextbookLibraryScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";
  const [status, setStatus] = useState<LoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [textbooks, setTextbooks] = useState<ApiTextbookLibraryItem[]>([]);
  const [selectedTextbookId, setSelectedTextbookId] = useState("");
  const [knowledge, setKnowledge] = useState<ApiTextbookKnowledgePoints | null>(null);
  const [selectedKnowledgePointIds, setSelectedKnowledgePointIds] = useState<string[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<ApiTextbookKnowledgePointAsset | null>(null);
  const [lessonPlans, setLessonPlans] = useState<ApiLessonPlanLibraryItem[]>([]);
  const [selectedLessonPlan, setSelectedLessonPlan] = useState<ApiLessonPlanLibraryItem | null>(null);
  const [latestJob, setLatestJob] = useState<ApiTextbookParseJob | null>(null);
  const [textbookFile, setTextbookFile] = useState<File | null>(null);
  const [lessonPlanFile, setLessonPlanFile] = useState<File | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<ActionLog[]>([]);

  const selectedTextbook = useMemo(
    () => textbooks.find((item) => item.textbook_id === selectedTextbookId) || textbooks[0],
    [textbooks, selectedTextbookId],
  );

  const knowledgePoints = knowledge?.knowledge_points || [];
  const selectedPoint = useMemo(
    () =>
      knowledgePoints.find((point) => point.id === selectedKnowledgePointIds[0]) ||
      knowledgePoints[0],
    [knowledgePoints, selectedKnowledgePointIds],
  );

  useEffect(() => {
    if (!isAdmin) return;
    void refreshLibrary();
  }, [isAdmin]);

  useEffect(() => {
    if (!selectedTextbook?.textbook_id || !isAdmin) {
      setKnowledge(null);
      setLessonPlans([]);
      return;
    }
    void loadTextbookDetail(selectedTextbook);
  }, [selectedTextbook?.textbook_id, isAdmin]);

  async function refreshLibrary() {
    setStatus("loading");
    setError(null);
    try {
      const library = await fetchTextbookLibrary();
      setTextbooks(library.textbooks);
      if (!selectedTextbookId && library.textbooks[0]) {
        setSelectedTextbookId(library.textbooks[0].textbook_id);
      }
      setStatus("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "教材库读取失败");
      setStatus("error");
    }
  }

  async function loadTextbookDetail(textbook: ApiTextbookLibraryItem) {
    setBusyAction("detail");
    setError(null);
    try {
      const [nextKnowledge, nextLessonPlans] = await Promise.all([
        fetchTextbookKnowledgePoints(textbook.textbook_id),
        fetchLessonPlanLibrary({ textbookId: textbook.textbook_id }),
      ]);
      setKnowledge(nextKnowledge);
      setLessonPlans(nextLessonPlans.lesson_plans);
      setSelectedKnowledgePointIds((current) =>
        current.length
          ? current.filter((id) => nextKnowledge.knowledge_points.some((point) => point.id === id))
          : nextKnowledge.knowledge_points[0]
            ? [nextKnowledge.knowledge_points[0].id]
            : [],
      );
      setSelectedAsset(null);
      setSelectedLessonPlan(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "教材详情读取失败");
    } finally {
      setBusyAction(null);
    }
  }

  async function runAction<T>(action: string, task: () => Promise<T>, onSuccess?: (result: T) => void) {
    setBusyAction(action);
    try {
      const result = await task();
      onSuccess?.(result);
      appendLog(action, "操作已提交到后端", "success");
      toast.success(`${action}已完成`);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : `${action}失败`;
      appendLog(action, message, "warning");
      toast.error(message);
      return null;
    } finally {
      setBusyAction(null);
    }
  }

  async function uploadTextbook() {
    if (!textbookFile) {
      toast.error("请选择教材文件");
      return;
    }
    await runAction("上传教材", () => uploadTextbookToLibrary(textbookFile), async (result) => {
      setLatestJob(null);
      setTextbookFile(null);
      await refreshLibrary();
      setSelectedTextbookId(result.textbook_id);
      if (result.job_id) {
        const job = await fetchTextbookParseJob(result.job_id);
        setLatestJob(job);
      }
    });
  }

  async function refreshLatestJob() {
    if (!latestJob?.job_id) {
      toast.info("暂无可查询的教材任务");
      return;
    }
    await runAction("查询任务", () => fetchTextbookParseJob(latestJob.job_id), setLatestJob);
  }

  async function splitTextbook() {
    if (!selectedTextbook) return;
    await runAction("切分教材", () =>
      splitTextbookKnowledgePointAssets(selectedTextbook.textbook_id, actionKnowledgePointIds()),
    );
    await loadTextbookDetail(selectedTextbook);
  }

  async function extractTextbook() {
    if (!selectedTextbook) return;
    await runAction("解析教材内容", () =>
      extractTextbookKnowledgePointAssets(selectedTextbook.textbook_id, actionKnowledgePointIds()),
    );
    await loadTextbookDetail(selectedTextbook);
  }

  async function inspectAsset(point?: ApiTextbookKnowledgePoint) {
    if (!selectedTextbook || !point) return;
    await runAction(
      "查看资产",
      () => fetchTextbookKnowledgePointAsset(selectedTextbook.textbook_id, point.id),
      setSelectedAsset,
    );
  }

  async function confirmAsset() {
    const assetId =
      selectedAsset?.asset_id ||
      selectedPoint?.asset_package?.asset_id;
    if (!assetId) {
      toast.error("当前知识点还没有可确认资产");
      return;
    }
    await runAction("确认资产", () => confirmTextbookKnowledgePointAsset(assetId), setSelectedAsset);
    if (selectedTextbook) await loadTextbookDetail(selectedTextbook);
  }

  async function uploadLessonPlan() {
    if (!lessonPlanFile) {
      toast.error("请选择教案文件");
      return;
    }
    await runAction(
      "上传教案",
      () =>
        uploadLessonPlanToLibrary(lessonPlanFile, {
          textbook_id: selectedTextbook?.textbook_id,
          textbook_version_id: selectedTextbook?.textbook_version_id,
          knowledge_point_id: selectedPoint?.id,
          created_by: user?.username || "admin-ui",
        }),
      async (item) => {
        setLessonPlanFile(null);
        setSelectedLessonPlan(item);
        if (selectedTextbook) {
          const library = await fetchLessonPlanLibrary({
            textbookId: selectedTextbook.textbook_id,
            knowledgePointId: selectedPoint?.id,
          });
          setLessonPlans(library.lesson_plans);
        }
      },
    );
  }

  async function openLessonPlan(item: ApiLessonPlanLibraryItem) {
    await runAction("查看教案库", () => fetchLessonPlanLibraryItem(item.lesson_plan_id), setSelectedLessonPlan);
  }

  function actionKnowledgePointIds() {
    return selectedKnowledgePointIds.length ? selectedKnowledgePointIds : undefined;
  }

  function toggleKnowledgePoint(pointId: string) {
    setSelectedKnowledgePointIds((current) =>
      current.includes(pointId)
        ? current.filter((id) => id !== pointId)
        : [...current, pointId],
    );
  }

  function appendLog(action: string, detail: string, tone: ActionLog["tone"]) {
    setActionLog((current) => [
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        time: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        action,
        detail,
        tone,
      },
      ...current.slice(0, 7),
    ]);
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <EmptyState
          icon={<ShieldAlert className="h-5 w-5" />}
          title="资源不存在"
          desc="教材库管理仅管理员可见。"
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">管理员</div>
          <h1 className="mt-2 t-title">管理教材库</h1>
          <p className="mt-2 max-w-3xl t-body text-muted-foreground">
            在管理员侧维护教材、知识点资产和教案库。教师新建项目页只选择已整理好的教材和教案，不再承担教材加工动作。
          </p>
        </div>
        <Button variant="outline" className="gap-2" onClick={() => void refreshLibrary()}>
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </Button>
      </div>

      {error && (
        <Card className="mt-6 border-destructive/40 bg-destructive/5 p-4 text-destructive">
          {error}
        </Card>
      )}

      <div className="mt-8 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <section>
          <SectionHeader
            icon={<LibraryBig className="h-4 w-4" />}
            title="教材列表"
            desc="从后端教材库读取，选择后管理知识点资产"
          />
          <Card className="border-border bg-card p-0 shadow-soft">
            <div className="max-h-[520px] overflow-y-auto p-3">
              {textbooks.length ? (
                textbooks.map((item) => {
                  const active = item.textbook_id === selectedTextbook?.textbook_id;
                  return (
                    <button
                      key={item.textbook_id}
                      type="button"
                      onClick={() => setSelectedTextbookId(item.textbook_id)}
                      className={cn(
                        "mb-2 w-full rounded-md border p-3 text-left transition-colors focus-ring",
                        active
                          ? "border-primary/60 bg-primary/5"
                          : "border-border bg-background hover:border-primary/40 hover:bg-muted/40",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="t-body font-medium">{formatTextbookName(item)}</div>
                          <div className="mt-1 t-caption text-muted-foreground">
                            {item.subject || "未标注学科"} · {item.grade || "未标注年级"} · {item.volume || "未标注册次"}
                          </div>
                        </div>
                        <ToneBadge tone={item.status === "ready" ? "success" : "neutral"}>
                          {item.status || "library"}
                        </ToneBadge>
                      </div>
                      <div className="mt-2 t-caption text-muted-foreground">
                        知识点 {item.knowledge_point_count ?? 0} · {item.textbook_id}
                      </div>
                    </button>
                  );
                })
              ) : (
                <EmptyState
                  icon={<LibraryBig className="h-5 w-5" />}
                  title="暂无教材"
                  desc="上传教材后会进入后端教材库。"
                />
              )}
            </div>
          </Card>
        </section>

        <section>
          <SectionHeader
            icon={<Upload className="h-4 w-4" />}
            title="入库与任务"
            desc="上传教材后可查询后端解析任务状态"
          />
          <Card className="border-border bg-card p-5 shadow-soft">
            <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
              <div className="space-y-2">
                <Label>上传教材</Label>
                <Input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.md"
                  onChange={(event) => setTextbookFile(event.target.files?.[0] || null)}
                />
                <p className="t-caption text-muted-foreground">
                  支持真实后端入库，任务结果以教材库接口为准。
                </p>
              </div>
              <Button className="gap-2" onClick={() => void uploadTextbook()} disabled={!!busyAction}>
                {busyAction === "上传教材" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                上传教材
              </Button>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <Metric label="教材数量" value={String(textbooks.length)} />
              <Metric label="当前知识点" value={String(knowledgePoints.length)} />
              <Metric label="教案库条目" value={String(lessonPlans.length)} />
            </div>

            {latestJob && (
              <div className="mt-5 rounded-md border border-border bg-background p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="t-body font-medium">最近教材任务</div>
                    <div className="mt-1 t-caption text-muted-foreground">
                      {latestJob.job_id} · {latestJob.job_type} · {latestJob.provider}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <ToneBadge tone={latestJob.status === "succeeded" ? "success" : "warning"}>
                      {latestJob.status}
                    </ToneBadge>
                    <Button variant="outline" size="sm" onClick={() => void refreshLatestJob()}>
                      查询任务
                    </Button>
                  </div>
                </div>
                {latestJob.error_message && (
                  <div className="mt-3 t-caption text-destructive">{latestJob.error_message}</div>
                )}
              </div>
            )}
          </Card>
        </section>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <section>
          <SectionHeader
            icon={<Layers3 className="h-4 w-4" />}
            title="知识点与教材资产"
            desc="可全量或选中知识点执行切分教材、解析教材内容和确认资产"
          />
          <Card className="border-border bg-card p-0 shadow-soft">
            <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="t-body font-medium">
                  {selectedTextbook ? formatTextbookName(selectedTextbook) : "未选择教材"}
                </div>
                <div className="mt-1 t-caption text-muted-foreground">
                  已选 {selectedKnowledgePointIds.length || "全部"} 个知识点
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="gap-2" onClick={() => void splitTextbook()} disabled={!selectedTextbook || !!busyAction}>
                  {busyAction === "切分教材" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Layers3 className="h-4 w-4" />}
                  切分教材
                </Button>
                <Button variant="outline" className="gap-2" onClick={() => void extractTextbook()} disabled={!selectedTextbook || !!busyAction}>
                  {busyAction === "解析教材内容" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  解析教材内容
                </Button>
                <Button className="gap-2" onClick={() => void confirmAsset()} disabled={!selectedPoint || !!busyAction}>
                  {busyAction === "确认资产" ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  确认资产
                </Button>
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="px-5">知识点</TableHead>
                  <TableHead>页码</TableHead>
                  <TableHead>切分</TableHead>
                  <TableHead>解析</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {knowledgePoints.map((point) => (
                  <TableRow key={point.id}>
                    <TableCell className="px-5">
                      <button
                        type="button"
                        onClick={() => toggleKnowledgePoint(point.id)}
                        className={cn(
                          "rounded-md border px-2 py-1 text-left transition-colors focus-ring",
                          selectedKnowledgePointIds.includes(point.id)
                            ? "border-primary/60 bg-primary/5"
                            : "border-border bg-background hover:border-primary/40",
                        )}
                      >
                        <div className="t-body font-medium">{point.title}</div>
                        <div className="t-caption text-muted-foreground">{point.unit || point.id}</div>
                      </button>
                    </TableCell>
                    <TableCell>{formatPages(point)}</TableCell>
                    <TableCell>
                      <ToneBadge tone={point.asset_package?.slice_pdf_path ? "success" : "neutral"}>
                        {point.asset_package?.slice_pdf_path ? "已切分" : "未切分"}
                      </ToneBadge>
                    </TableCell>
                    <TableCell>
                      <ToneBadge tone={point.asset_package?.mineru_md_path ? "success" : "neutral"}>
                        {point.asset_package?.mineru_md_path ? "已解析" : "未解析"}
                      </ToneBadge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => void inspectAsset(point)}>
                        查看资产
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!knowledgePoints.length && (
                  <TableRow>
                    <TableCell colSpan={5} className="px-5 py-8">
                      <EmptyState
                        icon={<Layers3 className="h-5 w-5" />}
                        title="暂无知识点"
                        desc="教材入库解析完成后会显示目录和课时知识点。"
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </section>

        <section>
          <SectionHeader
            icon={<BookOpenCheck className="h-4 w-4" />}
            title="资产详情"
            desc="查看后端返回的切片、Markdown 和审核状态"
          />
          <Card className="border-border bg-card p-5 shadow-soft">
            {selectedAsset ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="t-module">{selectedAsset.title || selectedPoint?.title || "教材资产"}</div>
                    <div className="mt-1 t-caption text-muted-foreground">
                      {selectedAsset.knowledge_point_id} · {selectedAsset.asset_id || "未返回资产 ID"}
                    </div>
                  </div>
                  <ToneBadge tone={selectedAsset.review_status === "confirmed" ? "success" : "warning"}>
                    {selectedAsset.review_status || "needs_review"}
                  </ToneBadge>
                </div>
                <AssetLine label="切片 PDF" value={selectedAsset.slice_pdf_path} />
                <AssetLine label="解析 Markdown" value={selectedAsset.markdown_path || selectedAsset.mineru_md_path} />
                <AssetLine label="教材页码" value={selectedAsset.textbook_pages} />
                <AssetLine label="PDF 页码" value={selectedAsset.pdf_pages} />
                <Button className="gap-2" onClick={() => void confirmAsset()} disabled={!!busyAction}>
                  <CheckCircle2 className="h-4 w-4" />
                  确认资产
                </Button>
              </div>
            ) : (
              <EmptyState
                icon={<BookOpenCheck className="h-5 w-5" />}
                title="选择知识点资产"
                desc="点击知识点行的查看资产后，可在这里确认资产。"
              />
            )}
          </Card>

          <SectionHeader
            icon={<FileText className="h-4 w-4" />}
            title="教案库"
            desc="按当前教材和知识点筛选，支持上传教案"
          />
          <Card className="border-border bg-card p-5 shadow-soft">
            <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
              <div className="space-y-2">
                <Label>上传教案</Label>
                <Input
                  type="file"
                  accept=".md,.doc,.docx,.pdf,.txt"
                  onChange={(event) => setLessonPlanFile(event.target.files?.[0] || null)}
                />
              </div>
              <Button className="gap-2" onClick={() => void uploadLessonPlan()} disabled={!selectedTextbook || !!busyAction}>
                {busyAction === "上传教案" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                上传教案
              </Button>
            </div>

            <div className="mt-5 max-h-[320px] space-y-2 overflow-y-auto">
              {lessonPlans.length ? (
                lessonPlans.map((item) => (
                  <button
                    key={item.lesson_plan_id}
                    type="button"
                    onClick={() => void openLessonPlan(item)}
                    className="w-full rounded-md border border-border bg-background p-3 text-left transition-colors hover:border-primary/40 hover:bg-muted/40 focus-ring"
                  >
                    <div className="t-body font-medium">{item.title || item.lesson_plan_id}</div>
                    <div className="mt-1 t-caption text-muted-foreground">
                      {item.created_by || "library"} · {item.updated_at || item.created_at}
                    </div>
                  </button>
                ))
              ) : (
                <EmptyState
                  icon={<FileText className="h-5 w-5" />}
                  title="当前范围暂无教案"
                  desc="上传教案后会进入教案库。"
                />
              )}
            </div>

            {selectedLessonPlan && (
              <div className="mt-5 rounded-md border border-border bg-background p-4">
                <div className="t-body font-medium">{selectedLessonPlan.title}</div>
                <div className="mt-1 t-caption text-muted-foreground">{selectedLessonPlan.lesson_plan_id}</div>
                {selectedLessonPlan.markdown && (
                  <pre className="mt-3 max-h-36 overflow-auto whitespace-pre-wrap rounded-md bg-muted p-3 text-xs text-muted-foreground">
                    {selectedLessonPlan.markdown.slice(0, 900)}
                  </pre>
                )}
              </div>
            )}
          </Card>
        </section>
      </div>

      <section className="mt-8">
        <SectionHeader
          icon={<CheckCircle2 className="h-4 w-4" />}
          title="操作记录"
          desc="本页只记录当前浏览器会话的管理员操作反馈"
        />
        <Card className="border-border bg-card p-0 shadow-soft">
          <div className="max-h-[260px] overflow-y-auto p-4">
            {actionLog.length ? (
              <div className="space-y-3">
                {actionLog.map((item) => (
                  <div key={item.id} className="rounded-md border border-border bg-background p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="t-body font-medium">{item.action}</div>
                      <ToneBadge tone={item.tone}>{item.time}</ToneBadge>
                    </div>
                    <div className="mt-1 t-caption text-muted-foreground">{item.detail}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<CheckCircle2 className="h-5 w-5" />}
                title="暂无操作记录"
                desc="上传、切分、解析、确认或上传教案后会显示结果。"
              />
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}

function SectionHeader({
  icon,
  title,
  desc,
}: {
  icon: ReactNode;
  title: string;
  desc?: string;
}) {
  return (
    <div className="mb-4 mt-1 flex items-start justify-between gap-3 first:mt-0">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-bronze">{icon}</span>
          <h2 className="t-module">{title}</h2>
        </div>
        {desc && <p className="mt-1 t-caption text-muted-foreground">{desc}</p>}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <div className="t-caption text-muted-foreground">{label}</div>
      <div className="mt-1 t-module">{value}</div>
    </div>
  );
}

function AssetLine({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <div className="t-caption text-muted-foreground">{label}</div>
      <div className="mt-1 break-all t-body">{value || "未返回"}</div>
    </div>
  );
}

function formatTextbookName(item: ApiTextbookLibraryItem) {
  return item.title || [item.textbook_version || item.publisher, item.subject, item.grade, item.volume]
    .filter(Boolean)
    .join(" / ") || item.textbook_id;
}

function formatPages(point: ApiTextbookKnowledgePoint) {
  const textbookPages =
    point.page_start && point.page_end ? `${point.page_start}-${point.page_end}` : "未标注";
  const pdfPages =
    point.pdf_page_start && point.pdf_page_end ? `${point.pdf_page_start}-${point.pdf_page_end}` : "未标注";
  return `${textbookPages} / PDF ${pdfPages}`;
}
