"use client";

import { useAppStore } from "@/lib/store";
import { MOCK_SCRIPTS } from "@/lib/mock-data";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToneBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/StateViews";
import { toast } from "sonner";
import {
  RefreshCw,
  TerminalSquare,
  Eye,
  RotateCw,
  FileCode2,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ---------------- 类型与映射 ---------------- */

type ScriptType = "解析" | "生成" | "归档";
type ScriptStatus = "成功" | "失败" | "待运行";

const TYPE_TONE: Record<ScriptType, "info" | "brand" | "neutral"> = {
  解析: "info",
  生成: "brand",
  归档: "neutral",
};

const STATUS_TONE: Record<
  ScriptStatus,
  "success" | "danger" | "warning"
> = {
  成功: "success",
  失败: "danger",
  待运行: "warning",
};

/* ---------------- 主组件 ---------------- */

export function ScriptsScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";

  const handleRefresh = () => {
    toast.success("脚本记录已刷新");
  };

  const handleViewDetail = (name: string) => {
    toast.message(`查看「${name}」详情`, {
      description: "演示版暂不提供脚本详情页",
    });
  };

  const handleRerun = (name: string) => {
    toast.message(`已请求重跑「${name}」`, {
      description: "演示版不会实际执行脚本",
    });
  };

  // 教师视角：EmptyState
  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <PageHeader
          overline="脚本运行记录"
          title="脚本"
          desc="查看各阶段脚本运行历史与状态。"
        />
        <Card className="mt-8 border-dashed bg-card p-0">
          <EmptyState
            icon={<TerminalSquare className="h-5 w-5" />}
            title="教师视角不展示脚本记录"
            desc="脚本运行记录属于系统运维信息，仅管理员可见。如需查看，请联系管理员或切换为管理员账号。"
            className="py-16"
          />
        </Card>
        <div className="h-2" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <PageHeader
        overline="脚本运行记录"
        title="脚本"
        desc="查看各阶段脚本的类型、状态、耗时与备注。第一阶段为 mock 数据，重跑仅作演示。"
        action={
          <Button variant="outline" className="gap-2" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            刷新
          </Button>
        }
      />

      {/* 脚本列表 */}
      <Card className="mt-8 border-border bg-card p-0 shadow-apple-sm">
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="flex items-center gap-2">
            <FileCode2 className="h-4 w-4 text-muted-foreground" />
            <span className="t-module">脚本列表</span>
          </div>
          <span className="t-caption text-muted-foreground/70">
            共 {MOCK_SCRIPTS.length} 个脚本
          </span>
        </div>

        {/* 桌面：表格 */}
        <div className="hidden md:block">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  脚本名称
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  类型
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  状态
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  耗时
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  最后运行
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  备注
                </TableHead>
                <TableHead className="px-5 py-3 text-right t-caption text-muted-foreground">
                  操作
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {MOCK_SCRIPTS.map((s) => (
                <TableRow key={s.id} className="border-border align-top">
                  <TableCell className="px-5 py-3.5">
                    <div className="t-body font-medium text-foreground">
                      {s.name}
                    </div>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <ToneBadge tone={TYPE_TONE[s.type as ScriptType]}>
                      {s.type}
                    </ToneBadge>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <ToneBadge tone={STATUS_TONE[s.status as ScriptStatus]}>
                      {s.status}
                    </ToneBadge>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <span className="t-body font-mono text-muted-foreground">
                      {s.duration}
                    </span>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <span className="t-body font-mono text-muted-foreground">
                      {s.lastRun}
                    </span>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <span className="t-body text-muted-foreground">
                      {s.note}
                    </span>
                  </TableCell>
                  <TableCell className="px-5 py-3.5">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5"
                        onClick={() => handleViewDetail(s.name)}
                      >
                        <Eye className="h-3.5 w-3.5" />
                        详情
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                          "gap-1.5",
                          s.status === "待运行"
                            ? "text-muted-foreground"
                            : "text-primary hover:text-primary"
                        )}
                        onClick={() => handleRerun(s.name)}
                        disabled={s.status === "待运行"}
                      >
                        <RotateCw className="h-3.5 w-3.5" />
                        重跑
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* 移动端：卡片列表 */}
        <ul className="divide-y divide-border md:hidden">
          {MOCK_SCRIPTS.map((s) => (
            <li key={s.id} className="px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="t-body font-medium text-foreground">
                    {s.name}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <ToneBadge tone={TYPE_TONE[s.type as ScriptType]}>
                      {s.type}
                    </ToneBadge>
                    <ToneBadge tone={STATUS_TONE[s.status as ScriptStatus]}>
                      {s.status}
                    </ToneBadge>
                  </div>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 t-body">
                <div>
                  <span className="t-caption text-muted-foreground">耗时</span>
                  <div className="font-mono text-foreground/90">
                    {s.duration}
                  </div>
                </div>
                <div>
                  <span className="t-caption text-muted-foreground">
                    最后运行
                  </span>
                  <div className="font-mono text-foreground/90">
                    {s.lastRun}
                  </div>
                </div>
              </div>

              <Separator className="my-3 bg-border" />

              <div className="flex items-center justify-between gap-2">
                <p className="t-caption text-muted-foreground line-clamp-1">
                  {s.note}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={() => handleViewDetail(s.name)}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    详情
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={cn(
                      "gap-1.5",
                      s.status === "待运行"
                        ? "text-muted-foreground"
                        : "text-primary hover:text-primary"
                    )}
                    onClick={() => handleRerun(s.name)}
                    disabled={s.status === "待运行"}
                  >
                    <RotateCw className="h-3.5 w-3.5" />
                    重跑
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <p className="mt-3 t-caption text-muted-foreground/80">
        演示版脚本均为 mock 记录，重跑请求不会实际执行。
      </p>

      <div className="h-2" />
    </div>
  );
}

/* ---------------- 局部组件 ---------------- */

function PageHeader({
  overline,
  title,
  desc,
  action,
}: {
  overline: string;
  title: string;
  desc: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="t-overline text-muted-foreground/70">{overline}</div>
        <h1 className="mt-2 t-title">{title}</h1>
        <p className="mt-3 h-page-subtitle">{desc}</p>
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
}
