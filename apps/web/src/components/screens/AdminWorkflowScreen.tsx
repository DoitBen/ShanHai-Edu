"use client";

import { useEffect, useMemo, useState } from "react";
import {
  activateAdminRuleVersion,
  createAdminRuleVersion,
  fetchAdminRule,
  fetchAdminRuleAudit,
  fetchAdminRules,
  fetchAdminWorkflowGraph,
  rollbackAdminRuleVersion,
} from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import type {
  AdminRule,
  AdminRuleAuditLog,
  AdminRuleSeverity,
  AdminWorkflowGraph,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
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
import { ToneBadge } from "@/components/common/StatusBadge";
import {
  GitBranch,
  History,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  ShieldAlert,
  SlidersHorizontal,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const DEFAULT_CHECK_JSON = `{
  "type": "field_compare",
  "field": "page_type_quota.blackboard_summary",
  "op": ">=",
  "value": 1
}`;

export function AdminWorkflowScreen() {
  const user = useAppStore((s) => s.user);
  const isAdmin = user?.role === "admin";
  const [graph, setGraph] = useState<AdminWorkflowGraph | null>(null);
  const [rules, setRules] = useState<AdminRule[]>([]);
  const [audit, setAudit] = useState<AdminRuleAuditLog[]>([]);
  const [selectedRuleId, setSelectedRuleId] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [severity, setSeverity] = useState<AdminRuleSeverity>("warning");
  const [enabled, setEnabled] = useState(true);
  const [actionMessage, setActionMessage] = useState("");
  const [checkJson, setCheckJson] = useState(DEFAULT_CHECK_JSON);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const selectedRule = useMemo(
    () => rules.find((item) => item.rule_id === selectedRuleId) || rules[0],
    [rules, selectedRuleId],
  );

  useEffect(() => {
    if (!isAdmin) return;
    void refresh();
  }, [isAdmin]);

  useEffect(() => {
    if (!selectedRule) return;
    const active = selectedRule.active_version;
    setSelectedRuleId(selectedRule.rule_id);
    setSeverity(active?.severity || "warning");
    setEnabled(active?.enabled ?? true);
    setActionMessage(active?.action_message || "");
    setCheckJson(JSON.stringify(active?.check_json || {}, null, 2));
    setNotes("");
  }, [selectedRule?.rule_id]);

  async function refresh() {
    setStatus("loading");
    setError(null);
    try {
      const [nextGraph, nextRules, nextAudit] = await Promise.all([
        fetchAdminWorkflowGraph(),
        fetchAdminRules(),
        fetchAdminRuleAudit(),
      ]);
      setGraph(nextGraph);
      setRules(nextRules);
      setAudit(nextAudit.slice().reverse());
      if (!selectedRuleId && nextRules[0]) {
        setSelectedRuleId(nextRules[0].rule_id);
      }
      setStatus("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "规则控制面读取失败");
      setStatus("error");
    }
  }

  async function reloadRule(ruleId: string) {
    const rule = await fetchAdminRule(ruleId);
    setRules((current) => current.map((item) => (item.rule_id === ruleId ? rule : item)));
    setSelectedRuleId(ruleId);
  }

  async function createVersion() {
    if (!selectedRule) return;
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(checkJson) as Record<string, unknown>;
    } catch {
      toast.error("check_json 不是合法 JSON");
      return;
    }
    setSaving(true);
    try {
      await createAdminRuleVersion(selectedRule.rule_id, {
        severity,
        enabled,
        action_message: actionMessage,
        check_json: parsed,
        created_by: user?.username || "admin-ui",
        notes,
      });
      await reloadRule(selectedRule.rule_id);
      setAudit((await fetchAdminRuleAudit()).slice().reverse());
      toast.success("规则草稿版本已创建");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "规则版本创建失败");
    } finally {
      setSaving(false);
    }
  }

  async function activate(versionId: string, rollback = false) {
    if (!selectedRule) return;
    setSaving(true);
    try {
      if (rollback) {
        await rollbackAdminRuleVersion(selectedRule.rule_id, versionId, "admin-ui rollback");
        toast.success("规则已回滚");
      } else {
        await activateAdminRuleVersion(selectedRule.rule_id, versionId, "admin-ui activate");
        toast.success("规则已发布");
      }
      await Promise.all([reloadRule(selectedRule.rule_id), refresh()]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "规则发布失败");
    } finally {
      setSaving(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
        <EmptyState
          icon={<ShieldAlert className="h-5 w-5" />}
          title="资源不存在"
          desc="规则控制面仅管理员可见。"
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="t-overline text-muted-foreground/70">控制面</div>
          <h1 className="mt-2 t-title">工作流规则控制面</h1>
          <p className="mt-3 max-w-3xl h-page-subtitle">
            一期只允许管理员治理质量门禁规则。DAG、节点依赖、schema 和状态机保持只读，新规则发布后只影响新项目。
          </p>
        </div>
        <Button variant="outline" className="gap-2" onClick={() => void refresh()}>
          {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </Button>
      </div>

      {error && (
        <Card className="mt-6 border-destructive/40 bg-destructive/5 p-4 text-destructive">
          {error}
        </Card>
      )}

      <div className="mt-8 grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section>
          <SectionHeader icon={<GitBranch className="h-4 w-4" />} title="只读 DAG" desc={graph?.edit_scope || "rules_and_prompts_only"} />
          <Card className="border-border bg-card p-0 shadow-apple-sm">
            <div className="grid max-h-[560px] gap-3 overflow-y-auto p-4">
              {(graph?.nodes || []).map((node) => (
                <button
                  key={node.id}
                  type="button"
                  className="rounded-md border border-border bg-background p-3 text-left transition-colors hover:border-primary/50 hover:bg-muted/40 focus-ring"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="t-body font-medium">{node.title || node.id}</div>
                      <div className="mt-1 t-caption text-muted-foreground">
                        {node.id} · 依赖 {node.depends_on.length ? node.depends_on.join(" / ") : "无"}
                      </div>
                    </div>
                    <ToneBadge tone={node.rules.length ? "warning" : "neutral"}>
                      {node.rules.length} 条规则
                    </ToneBadge>
                  </div>
                  {node.rules.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {node.rules.map((rule) => (
                        <span
                          key={rule.rule_id}
                          className="rounded border border-border bg-card px-2 py-1 t-caption text-muted-foreground"
                        >
                          {rule.rule_id}
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </Card>
        </section>

        <section>
          <SectionHeader icon={<SlidersHorizontal className="h-4 w-4" />} title="规则治理" desc="表单编辑条件、严重级别、提示文案和启停状态" />
          <div className="grid gap-4 lg:grid-cols-[0.42fr_0.58fr]">
            <Card className="border-border bg-card p-0 shadow-apple-sm">
              <div className="max-h-[560px] overflow-y-auto p-3">
                {rules.map((rule) => {
                  const active = rule.rule_id === selectedRule?.rule_id;
                  return (
                    <button
                      key={rule.rule_id}
                      type="button"
                      onClick={() => setSelectedRuleId(rule.rule_id)}
                      className={cn(
                        "mb-2 w-full rounded-md border p-3 text-left transition-colors focus-ring",
                        active
                          ? "border-primary/60 bg-primary/5"
                          : "border-border bg-background hover:border-primary/40 hover:bg-muted/40",
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="t-body font-medium">{rule.rule_id}</span>
                        <ToneBadge tone={rule.active_version?.severity === "hard_block" ? "warning" : "neutral"}>
                          {rule.active_version?.severity || "unknown"}
                        </ToneBadge>
                      </div>
                      <div className="mt-1 line-clamp-2 t-caption text-muted-foreground">
                        {rule.title}
                      </div>
                    </button>
                  );
                })}
              </div>
            </Card>

            <Card className="border-border bg-card p-5 shadow-apple-sm">
              {selectedRule ? (
                <div className="space-y-5">
                  <div>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="t-module">{selectedRule.rule_id} · {selectedRule.title}</div>
                        <div className="mt-1 t-caption text-muted-foreground">
                          {selectedRule.trigger_node} / {selectedRule.trigger_event}
                        </div>
                      </div>
                      <ToneBadge tone={selectedRule.active_version?.enabled ? "success" : "neutral"}>
                        {selectedRule.active_version?.enabled ? "active" : "disabled"}
                      </ToneBadge>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>严重级别</Label>
                      <Select value={severity} onValueChange={(value) => setSeverity(value as AdminRuleSeverity)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hard_block">hard_block</SelectItem>
                          <SelectItem value="warning">warning</SelectItem>
                          <SelectItem value="info">info</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2">
                      <div>
                        <Label>启用规则</Label>
                        <p className="mt-1 t-caption text-muted-foreground">关闭后只保留版本记录</p>
                      </div>
                      <Switch checked={enabled} onCheckedChange={setEnabled} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>提示文案</Label>
                    <Textarea
                      value={actionMessage}
                      onChange={(event) => setActionMessage(event.target.value)}
                      className="min-h-20"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>check_json</Label>
                    <Textarea
                      value={checkJson}
                      onChange={(event) => setCheckJson(event.target.value)}
                      className="min-h-44 font-mono text-xs"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>备注</Label>
                    <Textarea
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      className="min-h-16"
                      placeholder="说明本次规则修改原因"
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button className="gap-2" onClick={() => void createVersion()} disabled={saving}>
                      {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                      创建草稿版本
                    </Button>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={<SlidersHorizontal className="h-5 w-5" />}
                  title="暂无规则"
                  desc="后端控制面 seed 完成后会显示规则列表。"
                />
              )}
            </Card>
          </div>
        </section>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <section>
          <SectionHeader icon={<History className="h-4 w-4" />} title="版本历史" desc="发布和回滚会重建 active rule set，只影响之后新建项目" />
          <Card className="border-border bg-card p-0 shadow-apple-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="px-5">版本</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>级别</TableHead>
                  <TableHead>作者</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(selectedRule?.versions || []).map((version) => (
                  <TableRow key={version.version_id}>
                    <TableCell className="px-5">
                      <div className="t-body font-medium">v{version.version_number}</div>
                      <div className="t-caption text-muted-foreground">{version.version_id}</div>
                    </TableCell>
                    <TableCell>
                      <ToneBadge tone={version.status === "active" ? "success" : "neutral"}>{version.status}</ToneBadge>
                    </TableCell>
                    <TableCell>{version.severity}</TableCell>
                    <TableCell>{version.created_by}</TableCell>
                    <TableCell className="text-right">
                      {version.status === "active" ? (
                        <span className="t-caption text-muted-foreground">当前发布</span>
                      ) : (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => void activate(version.version_id)} disabled={saving}>
                            发布
                          </Button>
                          <Button size="sm" variant="ghost" className="gap-1" onClick={() => void activate(version.version_id, true)} disabled={saving}>
                            <RotateCcw className="h-3.5 w-3.5" />
                            回滚
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </section>

        <section>
          <SectionHeader icon={<History className="h-4 w-4" />} title="审计日志" desc="所有规则发布、回滚、seed 和 rule set 激活留痕" />
          <Card className="border-border bg-card p-0 shadow-apple-sm">
            <div className="max-h-[420px] overflow-y-auto p-4">
              {audit.length ? (
                <div className="space-y-3">
                  {audit.map((item) => (
                    <div key={item.audit_id} className="rounded-md border border-border bg-background p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="t-body font-medium">{item.action}</div>
                        <span className="t-caption text-muted-foreground">{item.actor}</span>
                      </div>
                      <div className="mt-1 t-caption text-muted-foreground">
                        {item.rule_id || item.rule_set_version_id || "rule_set"} · {item.created_at}
                      </div>
                      {item.notes && (
                        <div className="mt-2 t-caption text-muted-foreground">{item.notes}</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<History className="h-5 w-5" />}
                  title="暂无审计记录"
                  desc="seed、发布和回滚后会写入审计日志。"
                />
              )}
            </div>
          </Card>
        </section>
      </div>
    </div>
  );
}

function SectionHeader({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc?: string;
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-bronze">{icon}</span>
          <h2 className="t-module font-semibold text-foreground">{title}</h2>
        </div>
        {desc && <p className="mt-1 t-caption text-muted-foreground">{desc}</p>}
      </div>
    </div>
  );
}
