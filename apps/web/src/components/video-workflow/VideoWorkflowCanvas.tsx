"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import { toast } from "sonner";
import { ImagePlus, Loader2, Play, RefreshCw, Save, Video } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { downloadVideoWorkflowRun } from "@/lib/api-client";
import type {
  LoadStatus,
  VideoCapability,
  VideoGenerationMode,
  VideoModelOption,
  VideoWorkflowEdge,
  VideoWorkflowNode,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

function toFlowNodes(nodes: VideoWorkflowNode[]): Node[] {
  return nodes.map((node) => ({
    id: node.id,
    type: "default",
    position: node.position,
    data: {
      label: (
        <div className="min-w-36">
          <div className="t-caption text-muted-foreground">{node.type}</div>
          <div className="t-module">{String(node.data?.label || node.id)}</div>
        </div>
      ),
    },
  }));
}

function toFlowEdges(edges: VideoWorkflowEdge[]): Edge[] {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    animated: edge.id === "model-output",
  }));
}

function fromFlowNodes(nodes: Node[]): VideoWorkflowNode[] {
  return nodes.map((node) => {
    const label = typeof node.data?.label === "string" ? node.data.label : node.id;
    return {
      id: node.id,
      type: node.id === "prompt" ? "prompt_input" : node.id === "references" ? "reference_input" : node.id === "model" ? "omni_model" : "video_output",
      position: node.position,
      data: { label },
    };
  });
}

export function VideoWorkflowCanvas({
  projectId,
  capabilities,
  option,
  onChangeOption,
}: {
  projectId: string;
  capabilities: VideoCapability[];
  option: VideoModelOption;
  onChangeOption: (option: VideoModelOption) => void;
}) {
  const workflow = useAppStore((s) => s.videoWorkflowByProject[projectId]);
  const status = useAppStore((s) => s.videoWorkflowStatusByProject[projectId] || "idle");
  const error = useAppStore((s) => s.videoWorkflowErrorByProject[projectId]);
  const loadVideoWorkflow = useAppStore((s) => s.loadVideoWorkflow);
  const saveVideoWorkflowGraph = useAppStore((s) => s.saveVideoWorkflowGraph);
  const uploadVideoWorkflowReferences = useAppStore((s) => s.uploadVideoWorkflowReferences);
  const createVideoWorkflowRun = useAppStore((s) => s.createVideoWorkflowRun);
  const syncVideoWorkflowRun = useAppStore((s) => s.syncVideoWorkflowRun);
  const [prompt, setPrompt] = useState("");
  const [selectedReferenceIds, setSelectedReferenceIds] = useState<string[]>([]);
  const [busy, setBusy] = useState<LoadStatus>("idle");

  useEffect(() => {
    if (status === "idle" || status === "error") {
      void loadVideoWorkflow(projectId);
    }
  }, [loadVideoWorkflow, projectId, status]);

  const graph = workflow?.graph;
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (!graph) return;
    setNodes(toFlowNodes(graph.nodes));
    setEdges(toFlowEdges(graph.edges));
    onChangeOption({
      ...option,
      model: graph.selected_model,
      mode: graph.mode,
      size: graph.size,
      durationSec: graph.duration_sec,
      fullRun: false,
    });
  }, [graph?.selected_model, graph?.mode, graph?.size, graph?.duration_sec]);

  const models = workflow?.capabilities.models.length ? workflow.capabilities.models : capabilities;
  const selectedCapability =
    models.find((item) => item.model === option.model) ||
    models.find((item) => item.model === "omni_flash-10s") ||
    models[0];
  const sizeOptions = selectedCapability?.resolution?.supported || ["1280x720"];
  const maxReferences = selectedCapability?.max_reference_images || 0;
  const assets = workflow?.assets || [];
  const latestRun = workflow?.latest_run || null;
  const tooManyReferences = selectedReferenceIds.length > maxReferences;
  const canSubmit = prompt.trim().length > 0 && !tooManyReferences && (option.mode === "text" || selectedReferenceIds.length > 0);

  const availableModes = useMemo(() => {
    const modes: Array<{ value: VideoGenerationMode; label: string }> = [{ value: "text", label: "文生视频" }];
    if (selectedCapability?.reference_image_support) modes.push({ value: "reference", label: "参考图" });
    if (selectedCapability?.first_last_frame) modes.push({ value: "first_last_frame", label: "首尾帧" });
    if (selectedCapability?.extend) modes.push({ value: "extend", label: "延长" });
    return modes;
  }, [selectedCapability]);

  async function handleSaveGraph() {
    if (!graph) return;
    setBusy("loading");
    const result = await saveVideoWorkflowGraph(projectId, {
      ...graph,
      nodes: fromFlowNodes(nodes),
      edges: edges.map((edge) => ({ id: edge.id, source: edge.source, target: edge.target })),
      selected_model: option.model,
      mode: option.mode,
      size: option.size,
      duration_sec: option.durationSec,
    });
    setBusy(result.ok ? "ready" : "error");
    if (result.ok) toast.success("视频画布已保存");
    else toast.error(result.msg || "视频画布保存失败");
  }

  async function handleUpload(files: FileList | null) {
    if (!files?.length) return;
    setBusy("loading");
    const result = await uploadVideoWorkflowReferences(projectId, Array.from(files));
    setBusy(result.ok ? "ready" : "error");
    if (result.ok) toast.success("参考图已上传");
    else toast.error(result.msg || "参考图上传失败");
  }

  async function handleCreateRun() {
    if (!canSubmit) {
      toast.warning(option.mode === "text" ? "请先填写提示词" : "请填写提示词并选择参考图");
      return;
    }
    setBusy("loading");
    const result = await createVideoWorkflowRun(projectId, {
      prompt: prompt.trim(),
      model: option.model,
      mode: option.mode,
      size: option.size,
      duration_sec: option.durationSec,
      reference_asset_ids: option.mode === "text" ? [] : selectedReferenceIds,
    });
    setBusy(result.ok ? "ready" : "error");
    if (result.ok) toast.success("视频画布任务已创建");
    else toast.error(result.msg || "视频画布任务创建失败");
  }

  async function handleSyncRun() {
    if (!latestRun?.run_id) return;
    setBusy("loading");
    const result = await syncVideoWorkflowRun(projectId, latestRun.run_id);
    setBusy(result.ok ? "ready" : "error");
    if (result.ok) toast.success("视频任务状态已同步");
    else toast.error(result.msg || "视频任务同步失败");
  }

  return (
    <div className="space-y-4">
      <div className="grid min-h-[560px] gap-4 xl:grid-cols-[280px_minmax(420px,1fr)_320px]">
        <section className="rounded-md border border-border bg-card p-4">
          <div className="mb-3 flex items-center gap-2">
            <Video className="h-4 w-4 text-primary" />
            <div>
              <div className="t-module">视频输入</div>
              <div className="t-caption text-muted-foreground">提示词与参考图</div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label className="t-caption text-muted-foreground">提示词</Label>
              <Textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="写清楚课堂导入画面、镜头运动和氛围。"
                className="min-h-32 resize-none bg-background"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <Label className="t-caption text-muted-foreground">参考图</Label>
                <Badge variant={tooManyReferences ? "destructive" : "secondary"}>参考图最多 {maxReferences} 张</Badge>
              </div>
              <label className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-border bg-muted/30 px-3 py-4 t-body text-muted-foreground hover:bg-muted/50">
                <ImagePlus className="h-4 w-4" />
                上传参考图
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  multiple
                  className="hidden"
                  onChange={(event) => void handleUpload(event.target.files)}
                />
              </label>
              <div className="space-y-2">
                {assets.map((asset) => {
                  const checked = selectedReferenceIds.includes(asset.asset_id);
                  return (
                    <label key={asset.asset_id} className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 t-caption">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          setSelectedReferenceIds((current) =>
                            event.target.checked
                              ? [...current, asset.asset_id]
                              : current.filter((id) => id !== asset.asset_id),
                          );
                        }}
                      />
                      <span className="truncate">{asset.filename}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section className="overflow-hidden rounded-md border border-border bg-[#f9f8f3]">
          <div className="flex items-center justify-between border-b border-border bg-card px-4 py-3">
            <div>
              <div className="t-module">视频画布</div>
              <div className="t-caption text-muted-foreground">输入 → 模型 → 输出</div>
            </div>
            <Button variant="outline" size="sm" className="gap-2" onClick={() => void handleSaveGraph()} disabled={busy === "loading"}>
              <Save className="h-4 w-4" />
              保存画布
            </Button>
          </div>
          <div className="h-[500px]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              minZoom={0.5}
              maxZoom={1.6}
            >
              <Background gap={18} size={1} />
              <MiniMap pannable zoomable />
              <Controls />
            </ReactFlow>
          </div>
        </section>

        <section className="rounded-md border border-border bg-card p-4">
          <div className="mb-4">
            <div className="t-module">模型与输出</div>
            <div className="t-caption text-muted-foreground">默认 Omni · 10 秒 · 1280x720</div>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="t-caption text-muted-foreground">模型</Label>
              <Select
                value={option.model}
                onValueChange={(model) => {
                  const next = models.find((item) => item.model === model);
                  onChangeOption({
                    ...option,
                    model,
                    size: next?.resolution?.supported[0] || option.size,
                    mode: next?.reference_image_support ? option.mode : "text",
                  });
                }}
              >
                <SelectTrigger className="bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {models.filter((item) => item.model !== "task-query").map((item) => (
                    <SelectItem key={item.model} value={item.model}>
                      {item.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="t-caption text-muted-foreground">模式</Label>
              <Select value={option.mode} onValueChange={(mode) => onChangeOption({ ...option, mode: mode as VideoGenerationMode })}>
                <SelectTrigger className="bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModes.map((mode) => (
                    <SelectItem key={mode.value} value={mode.value}>{mode.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="t-caption text-muted-foreground">尺寸</Label>
              <Select value={option.size} onValueChange={(size) => onChangeOption({ ...option, size })}>
                <SelectTrigger className="bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {sizeOptions.map((size) => (
                    <SelectItem key={size} value={size}>{size}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="rounded-md border border-border bg-muted/25 p-3">
              <div className="t-caption text-muted-foreground">输出时长</div>
              <div className="mt-1 t-title text-foreground">{option.durationSec} 秒</div>
              <div className="mt-1 t-caption text-muted-foreground">{selectedCapability?.recommended_use || "按当前模型能力生成视频。"}</div>
            </div>
            <Button className="w-full gap-2" onClick={() => void handleCreateRun()} disabled={busy === "loading" || !canSubmit}>
              {busy === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              创建 10 秒视频任务
            </Button>
            {latestRun && (
              <div className="space-y-3 rounded-md border border-border bg-muted/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="t-caption text-muted-foreground">最近任务</div>
                    <div className="t-module">{latestRun.status}</div>
                  </div>
                  <Button variant="outline" size="sm" className="gap-2" onClick={() => void handleSyncRun()} disabled={busy === "loading"}>
                    <RefreshCw className="h-4 w-4" />
                    同步
                  </Button>
                </div>
                {latestRun.download_path && (
                  <Button asChild variant="secondary" size="sm" className="w-full">
                    <a href={downloadVideoWorkflowRun(projectId, latestRun.run_id)}>下载视频</a>
                  </Button>
                )}
              </div>
            )}
            {status === "error" && <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 t-caption text-destructive">{error}</div>}
          </div>
        </section>
      </div>
    </div>
  );
}
