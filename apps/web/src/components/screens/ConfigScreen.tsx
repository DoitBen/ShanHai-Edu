"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
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
import { ToneBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/StateViews";
import { toast } from "sonner";
import {
  RefreshCw,
  ShieldCheck,
  Cpu,
  KeyRound,
  SlidersHorizontal,
  Eye,
  EyeOff,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ---------------- 局部 mock 数据（第一阶段） ---------------- */

type ModelStatus = "ready" | "placeholder" | "unconfigured";

interface ModelRow {
  id: string;
  name: string;
  usage: string;
  status: ModelStatus;
}

const MOCK_MODELS: ModelRow[] = [
  { id: "m1", name: "教材解析模型", usage: "解析教材结构、抽取知识点与教学目标", status: "ready" },
  { id: "m2", name: "视频剧本模型", usage: "生成视频导入方案与分镜脚本", status: "ready" },
  { id: "m3", name: "视频生成模型", usage: "依据分镜资产生成课堂导入视频", status: "placeholder" },
  { id: "m4", name: "PPT 方案模型", usage: "规划 PPT 结构、风格与页数", status: "ready" },
  { id: "m5", name: "PPTX 生成模型", usage: "组装最终 PPTX 文件并校对排版", status: "placeholder" },
  { id: "m6", name: "教案完善模型", usage: "结合视频与 PPT 反馈完善教案终稿", status: "unconfigured" },
];

const MODEL_STATUS_META: Record<
  ModelStatus,
  { label: string; tone: "success" | "warning" | "neutral" }
> = {
  ready: { label: "就绪", tone: "success" },
  placeholder: { label: "占位", tone: "warning" },
  unconfigured: { label: "未配置", tone: "neutral" },
};

type KeyState = "configured" | "unconfigured";

interface KeyRow {
  id: string;
  name: string;
  desc: string;
  state: KeyState;
  masked: string;
  updatedAt: string;
}

const MOCK_KEYS: KeyRow[] = [
  {
    id: "k1",
    name: "API 密钥",
    desc: "工作台调度服务调用凭据",
    state: "configured",
    masked: "••••••••••••3a9f",
    updatedAt: "2026-06-12 09:10",
  },
  {
    id: "k2",
    name: "存储密钥",
    desc: "对象存储读写凭据",
    state: "configured",
    masked: "••••••••••••7c2d",
    updatedAt: "2026-06-08 14:42",
  },
  {
    id: "k3",
    name: "模型密钥",
    desc: "外部模型服务调用凭据",
    state: "unconfigured",
    masked: "—",
    updatedAt: "—",
  },
];

/* ---------------- 主组件 ---------------- */

export function ConfigScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";

  // 安全模式：mock 本地 state
  const [safeMode, setSafeMode] = useState(true);
  // 全局参数：mock 本地 state
  const [concurrency, setConcurrency] = useState("2");
  const [timeout, setTimeout] = useState("120");
  const [retry, setRetry] = useState("3");
  const [outputFormat, setOutputFormat] = useState("json");

  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  const handleRefresh = () => {
    toast.success("配置已刷新");
  };

  const handleSafeModeChange = (v: boolean) => {
    setSafeMode(v);
    toast.success(v ? "安全模式已开启" : "安全模式已关闭");
  };

  // 教师视角：只展示与业务相关的安全模式与说明
  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <PageHeader
          overline="配置中心"
          title="配置中心"
          desc="系统级配置仅对管理员可见。教师视角下仅展示与教学业务相关的开关。"
        />

        <section className="mt-8">
          <SectionHeader
            index="01"
            title="安全模式"
            desc="与教学业务直接相关的内容确认开关"
          />
          <Card className="border-border bg-card p-6 shadow-soft">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <span className="t-module">安全模式</span>
                </div>
                <p className="t-body max-w-xl text-muted-foreground">
                  开启后所有生成内容需人工确认后才会进入下一阶段。建议公开课与
                  教研场景保持开启。
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "t-caption",
                    safeMode ? "text-success" : "text-muted-foreground"
                  )}
                >
                  {safeMode ? "已开启" : "已关闭"}
                </span>
                <Switch checked={safeMode} onCheckedChange={handleSafeModeChange} />
              </div>
            </div>
          </Card>

          <Card className="mt-4 border-dashed bg-card p-0">
            <EmptyState
              icon={<Cpu className="h-5 w-5" />}
              title="教师视角不展示系统配置"
              desc="模型配置、全局参数与密钥状态属于系统底层配置，仅管理员可见。如需调整，请联系管理员。"
            />
          </Card>
        </section>
        <div className="h-2" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <PageHeader
        overline="配置中心"
        title="配置中心"
        desc="集中维护模型、安全模式、全局参数与密钥状态。第一阶段为占位展示，不写入实际配置。"
        action={
          <Button variant="outline" className="gap-2" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            刷新
          </Button>
        }
      />

      {/* 01 模型配置 */}
      <section className="mt-8">
        <SectionHeader
          index="01"
          title="模型配置"
          desc="各阶段使用的模型与状态占位"
        />
        <Card className="border-border bg-card p-0 shadow-soft">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  模型名称
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  用途
                </TableHead>
                <TableHead className="px-5 py-3 text-right t-caption text-muted-foreground">
                  状态
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {MOCK_MODELS.map((m) => {
                const meta = MODEL_STATUS_META[m.status];
                return (
                  <TableRow key={m.id} className="border-border">
                    <TableCell className="px-5 py-3.5">
                      <div className="t-body font-medium text-foreground">
                        {m.name}
                      </div>
                    </TableCell>
                    <TableCell className="px-5 py-3.5">
                      <div className="t-body text-muted-foreground">
                        {m.usage}
                      </div>
                    </TableCell>
                    <TableCell className="px-5 py-3.5 text-right">
                      <ToneBadge tone={meta.tone}>{meta.label}</ToneBadge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      </section>

      {/* 02 安全模式 + 03 全局参数 双栏（lg） */}
      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        {/* 02 安全模式 */}
        <section>
          <SectionHeader
            index="02"
            title="安全模式"
            desc="人工确认开关"
          />
          <Card className="border-border bg-card p-6 shadow-soft">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <span className="t-module">安全模式</span>
                </div>
                <p className="t-body text-muted-foreground">
                  开启后所有生成内容需人工确认。
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "t-caption",
                    safeMode ? "text-success" : "text-muted-foreground"
                  )}
                >
                  {safeMode ? "已开启" : "已关闭"}
                </span>
                <Switch
                  checked={safeMode}
                  onCheckedChange={handleSafeModeChange}
                />
              </div>
            </div>
            <Separator className="my-4 bg-border" />
            <div className="rounded-md border border-border bg-muted/40 p-3">
              <div className="t-caption text-muted-foreground">
                当前模式说明
              </div>
              <p className="mt-1 t-body text-foreground/80">
                {safeMode
                  ? "所有生成阶段产出均需教师或管理员确认后才进入下一步，确保教学合规。"
                  : "生成内容会自动流转至下一阶段，仅异常时阻断。仅建议在调试期使用。"}
              </p>
            </div>
          </Card>
        </section>

        {/* 03 全局参数 */}
        <section>
          <SectionHeader
            index="03"
            title="全局参数"
            desc="调度与输出默认值（占位）"
          />
          <Card className="border-border bg-card p-6 shadow-soft">
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2">
                <Label className="t-caption text-muted-foreground">
                  并发数
                </Label>
                <Input
                  type="number"
                  min={1}
                  max={8}
                  value={concurrency}
                  onChange={(e) => setConcurrency(e.target.value)}
                  className="h-11 bg-card"
                />
                <p className="t-caption text-muted-foreground/80">
                  同时运行的最大阶段任务数
                </p>
              </div>

              <div className="space-y-2">
                <Label className="t-caption text-muted-foreground">
                  超时（秒）
                </Label>
                <Select value={timeout} onValueChange={setTimeout}>
                  <SelectTrigger className="h-11 w-full bg-card">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="60">60</SelectItem>
                    <SelectItem value="120">120</SelectItem>
                    <SelectItem value="300">300</SelectItem>
                    <SelectItem value="600">600</SelectItem>
                  </SelectContent>
                </Select>
                <p className="t-caption text-muted-foreground/80">
                  单个阶段最长运行时间
                </p>
              </div>

              <div className="space-y-2">
                <Label className="t-caption text-muted-foreground">
                  重试次数
                </Label>
                <Input
                  type="number"
                  min={0}
                  max={5}
                  value={retry}
                  onChange={(e) => setRetry(e.target.value)}
                  className="h-11 bg-card"
                />
                <p className="t-caption text-muted-foreground/80">
                  失败后自动重试次数
                </p>
              </div>

              <div className="space-y-2">
                <Label className="t-caption text-muted-foreground">
                  输出格式
                </Label>
                <Select value={outputFormat} onValueChange={setOutputFormat}>
                  <SelectTrigger className="h-11 w-full bg-card">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="md">Markdown</SelectItem>
                    <SelectItem value="docx">DOCX</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                  </SelectContent>
                </Select>
                <p className="t-caption text-muted-foreground/80">
                  交付物默认输出格式
                </p>
              </div>
            </div>

            <Separator className="my-5 bg-border" />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 t-caption text-muted-foreground">
                <SlidersHorizontal className="h-3.5 w-3.5" />
                参数仅作展示，不会写入实际配置
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => toast.success("参数已保存（演示版）")}
              >
                保存参数
              </Button>
            </div>
          </Card>
        </section>
      </div>

      {/* 04 密钥状态 */}
      <section className="mt-10">
        <SectionHeader
          index="04"
          title="密钥状态"
          desc="仅显示配置状态与最后更新时间，不展示明文密钥"
        />
        <Card className="border-border bg-card p-0 shadow-soft">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  密钥
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  说明
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  凭据
                </TableHead>
                <TableHead className="px-5 py-3 t-caption text-muted-foreground">
                  最后更新
                </TableHead>
                <TableHead className="px-5 py-3 text-right t-caption text-muted-foreground">
                  状态
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {MOCK_KEYS.map((k) => {
                const isRevealed = revealed[k.id];
                const configured = k.state === "configured";
                return (
                  <TableRow key={k.id} className="border-border">
                    <TableCell className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <KeyRound className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="t-body font-medium text-foreground">
                          {k.name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="px-5 py-3.5">
                      <span className="t-body text-muted-foreground">
                        {k.desc}
                      </span>
                    </TableCell>
                    <TableCell className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <code
                          className="t-body font-mono text-foreground/80"
                          style={{ letterSpacing: "0.04em" }}
                        >
                          {configured
                            ? isRevealed
                              ? "shanhai_demo_key"
                              : k.masked
                            : "—"}
                        </code>
                        {configured && (
                          <button
                            type="button"
                            aria-label={isRevealed ? "隐藏密钥" : "显示密钥"}
                            onClick={() =>
                              setRevealed((p) => ({ ...p, [k.id]: !p[k.id] }))
                            }
                            className="text-muted-foreground transition-colors hover:text-foreground focus-ring rounded"
                          >
                            {isRevealed ? (
                              <EyeOff className="h-3.5 w-3.5" />
                            ) : (
                              <Eye className="h-3.5 w-3.5" />
                            )}
                          </button>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="px-5 py-3.5">
                      <span className="t-body text-muted-foreground">
                        {k.updatedAt}
                      </span>
                    </TableCell>
                    <TableCell className="px-5 py-3.5 text-right">
                      <ToneBadge tone={configured ? "success" : "neutral"}>
                        {configured ? "已配置" : "未配置"}
                      </ToneBadge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
        <p className="mt-3 t-caption text-muted-foreground/80">
          演示版密钥均为占位凭据，不会发起任何外部请求。
        </p>
      </section>

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
        <p className="mt-2 t-body text-muted-foreground">{desc}</p>
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
}

function SectionHeader({
  index,
  title,
  desc,
}: {
  index: string;
  title: string;
  desc?: string;
}) {
  return (
    <div className="mb-4 flex items-baseline gap-3">
      <span className="t-overline text-bronze">{index}</span>
      <div>
        <h2 className="t-module">{title}</h2>
        {desc && (
          <p className="mt-0.5 t-caption text-muted-foreground">{desc}</p>
        )}
      </div>
    </div>
  );
}
