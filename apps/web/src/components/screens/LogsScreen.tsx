"use client";

import { useMemo, useState } from "react";
import { useAppStore } from "@/lib/store";
import { MOCK_STAGE_LOGS } from "@/lib/mock-data";
import { STAGE_DEFS } from "@/lib/workflow";
import type { StageLog } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/common/StateViews";
import { toast } from "sonner";
import {
  RefreshCw,
  Download,
  Search,
  Info,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ---------------- 局部类型与映射 ---------------- */

type Level = StageLog["level"];

interface LogRow extends StageLog {
  projectId: string;
  projectName: string;
  stageTitle: string;
}

const LEVEL_LABEL: Record<Level | "all", string> = {
  all: "全部级别",
  info: "info",
  warn: "warn",
  error: "error",
  success: "success",
};

const LEVEL_TONE: Record<
  Level,
  { tone: "neutral" | "warning" | "danger" | "success"; icon: React.ReactNode; label: string }
> = {
  info: {
    tone: "neutral",
    icon: <Info className="h-3.5 w-3.5" />,
    label: "info",
  },
  warn: {
    tone: "warning",
    icon: <AlertTriangle className="h-3.5 w-3.5" />,
    label: "warn",
  },
  error: {
    tone: "danger",
    icon: <XCircle className="h-3.5 w-3.5" />,
    label: "error",
  },
  success: {
    tone: "success",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "success",
  },
};

const LEVEL_ICON_CLASS: Record<Level, string> = {
  info: "text-muted-foreground",
  warn: "text-warning",
  error: "text-destructive",
  success: "text-success",
};

/**
 * 把 MOCK_STAGE_LOGS 扩展为带项目与阶段信息的行。
 * 根据时间戳与项目状态对应：demo-001 视频剧本流程 + demo-003 失败日志。
 */
function buildLogRows(): LogRow[] {
  return MOCK_STAGE_LOGS.map((l, i) => {
    if (l.level === "error") {
      return {
        ...l,
        id: l.id || `r${i}`,
        projectId: "demo-003",
        projectName: "古诗文诵读——静夜思",
        stageTitle: "视频生成",
      };
    }
    return {
      ...l,
      id: l.id || `r${i}`,
      projectId: "demo-001",
      projectName: "认识分数——分一分",
      stageTitle: "视频剧本",
    };
  });
}

/* ---------------- 主组件 ---------------- */

export function LogsScreen() {
  const user = useAppStore((s) => s.user);
  const projects = useAppStore((s) => s.projects);
  const isAdmin = user?.role === "admin";

  const allRows = useMemo(() => buildLogRows(), []);

  const [stage, setStage] = useState<string>("all");
  const [level, setLevel] = useState<string>("all");
  const [projectId, setProjectId] = useState<string>("all");
  const [keyword, setKeyword] = useState<string>("");

  const filtered = useMemo(() => {
    return allRows.filter((r) => {
      if (stage !== "all" && r.stageTitle !== stage) return false;
      if (level !== "all" && r.level !== level) return false;
      if (projectId !== "all" && r.projectId !== projectId) return false;
      if (keyword.trim()) {
        const k = keyword.trim().toLowerCase();
        if (
          !r.message.toLowerCase().includes(k) &&
          !r.projectName.toLowerCase().includes(k) &&
          !r.stageTitle.toLowerCase().includes(k)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [allRows, stage, level, projectId, keyword]);

  const handleRefresh = () => {
    toast.success("日志已刷新");
  };
  const handleExport = () => {
    toast.message("演示版暂不支持导出");
  };
  const handleReset = () => {
    setStage("all");
    setLevel("all");
    setProjectId("all");
    setKeyword("");
  };

  // 教师视角：可访问，简化（隐藏导出按钮、不显示项目维度筛选）
  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      {/* 页头 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">运行日志</div>
          <h1 className="mt-2 t-title">日志</h1>
          <p className="mt-3 h-page-subtitle">
            查看各阶段运行日志与异常记录。第一阶段为 mock 数据。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="btn-cta-secondary gap-2 h-10"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4" />
            刷新
          </Button>
          {isAdmin && (
            <Button
              variant="outline"
              className="btn-cta-secondary gap-2 h-10"
              onClick={handleExport}
            >
              <Download className="h-4 w-4" />
              导出
            </Button>
          )}
        </div>
      </div>

      {/* 筛选器 */}
      <Card className="mt-6 border-border bg-card p-4 shadow-apple-sm sm:p-5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1.5">
            <Label className="t-caption text-muted-foreground">阶段</Label>
            <Select value={stage} onValueChange={setStage}>
              <SelectTrigger className="input-pro h-11 w-full bg-card">
                <SelectValue placeholder="全部阶段" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部阶段</SelectItem>
                {STAGE_DEFS.map((s) => (
                  <SelectItem key={s.key} value={s.title}>
                    {s.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="t-caption text-muted-foreground">级别</Label>
            <Select value={level} onValueChange={setLevel}>
              <SelectTrigger className="input-pro h-11 w-full bg-card">
                <SelectValue placeholder="全部级别" />
              </SelectTrigger>
              <SelectContent>
                {(["all", "info", "warn", "error", "success"] as const).map(
                  (lv) => (
                    <SelectItem key={lv} value={lv}>
                      {LEVEL_LABEL[lv]}
                    </SelectItem>
                  )
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="t-caption text-muted-foreground">项目</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="input-pro h-11 w-full bg-card">
                <SelectValue placeholder="全部项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="t-caption text-muted-foreground">搜索</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="搜索消息 / 项目 / 阶段"
                className="input-pro h-11 bg-card pl-9"
              />
            </div>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="t-caption text-muted-foreground">
            共 <span className="font-medium text-foreground">{filtered.length}</span> 条
            <span className="mx-2 text-muted-foreground/40">·</span>
            全部 <span className="font-medium text-foreground">{allRows.length}</span> 条
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={handleReset}
          >
            重置筛选
          </Button>
        </div>
      </Card>

      {/* 日志列表 */}
      <Card className="mt-4 border-border bg-card p-0 shadow-apple-sm">
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-muted-foreground" />
            <span className="t-module">日志列表</span>
          </div>
          <span className="t-caption text-muted-foreground/70">
            最近 7 条
          </span>
        </div>

        {filtered.length === 0 ? (
          <EmptyState
            icon={<Search className="h-5 w-5" />}
            title="未找到匹配的日志"
            desc="尝试调整筛选条件或清空搜索关键词。"
            className="py-10"
          />
        ) : (
          <>
            {/* 桌面：表格 */}
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow className="border-border">
                    <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                      时间
                    </TableHead>
                    <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                      级别
                    </TableHead>
                    <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                      项目 / 阶段
                    </TableHead>
                    <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                      消息
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((r) => {
                    const lv = LEVEL_TONE[r.level];
                    return (
                      <TableRow key={r.id} className="border-border">
                        <TableCell className="px-5 py-3 align-top">
                          <span className="t-body font-mono text-muted-foreground">
                            {r.time}
                          </span>
                        </TableCell>
                        <TableCell className="px-5 py-3 align-top">
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 t-caption",
                              lv.tone === "neutral" &&
                                "border-transparent bg-muted text-muted-foreground",
                              lv.tone === "warning" &&
                                "border-warning/25 bg-warning/10 text-warning",
                              lv.tone === "danger" &&
                                "border-destructive/25 bg-destructive/10 text-destructive",
                              lv.tone === "success" &&
                                "border-success/25 bg-success/10 text-success"
                            )}
                          >
                            {lv.icon}
                            {lv.label}
                          </span>
                        </TableCell>
                        <TableCell className="px-5 py-3 align-top">
                          <div className="t-body text-foreground">
                            {r.projectName}
                          </div>
                          <div className="t-caption text-muted-foreground">
                            {r.stageTitle}
                          </div>
                        </TableCell>
                        <TableCell className="px-5 py-3 align-top">
                          <span className="t-body text-foreground/90">
                            {r.message}
                          </span>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>

            {/* 移动端：卡片列表 */}
            <ul className="divide-y divide-border md:hidden">
              {filtered.map((r) => {
                const lv = LEVEL_TONE[r.level];
                return (
                  <li key={r.id} className="px-4 py-3.5">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 t-caption",
                          lv.tone === "neutral" &&
                            "border-transparent bg-muted text-muted-foreground",
                          lv.tone === "warning" &&
                            "border-warning/25 bg-warning/10 text-warning",
                          lv.tone === "danger" &&
                            "border-destructive/25 bg-destructive/10 text-destructive",
                          lv.tone === "success" &&
                            "border-success/25 bg-success/10 text-success"
                        )}
                      >
                        <span className={LEVEL_ICON_CLASS[r.level]}>
                          {lv.icon}
                        </span>
                        {lv.label}
                      </span>
                      <span className="t-caption font-mono text-muted-foreground">
                        {r.time}
                      </span>
                    </div>
                    <p className="mt-2 t-body text-foreground/90">
                      {r.message}
                    </p>
                    <p className="mt-1 t-caption text-muted-foreground">
                      {r.projectName} · {r.stageTitle}
                    </p>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </Card>

      <div className="h-2" />
    </div>
  );
}
