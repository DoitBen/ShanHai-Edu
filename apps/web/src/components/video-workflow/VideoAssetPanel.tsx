"use client";

import { useRef, useState } from "react";
import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  type DragEndEvent,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  horizontalListSortingStrategy,
  sortableKeyboardCoordinates,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { toast } from "sonner";
import { CheckCircle2, CircleAlert, GripVertical, ImagePlus, Loader2, RotateCcw, Trash2, Upload } from "lucide-react";
import { videoWorkflowAssetContent } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { VideoReferenceAsset, VideoWorkflowUploadError } from "@/lib/types";
import {
  createVideoWorkflowUploadItems,
  markVideoWorkflowUploadFailure,
  markVideoWorkflowUploadUploaded,
  markVideoWorkflowUploadUploading,
  retryableVideoWorkflowUploadFiles,
  type VideoWorkflowUploadItem,
} from "@/lib/video-workflow-upload-queue";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface VideoAssetPanelProps {
  projectId: string;
  assets: VideoReferenceAsset[];
  selectedIds: string[];
  maxSelected: number;
  maxAssetBytes: number;
  busy: boolean;
  onUpload: (files: File[]) => Promise<{ ok: boolean; msg?: string; errors?: VideoWorkflowUploadError[] }>;
  onToggle: (assetId: string) => void;
  onReorder: (ids: string[]) => void;
  onDelete: (assetId: string) => Promise<void>;
}

function SortableSelectedItem({
  asset,
  projectId,
  index,
}: {
  asset: VideoReferenceAsset;
  projectId: string;
  index: number;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: asset.asset_id,
  });
  const { role, tabIndex, ...handleDragAttributes } = attributes;
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        "relative flex h-16 w-16 shrink-0 overflow-hidden rounded-md border border-border bg-muted",
        isDragging && "z-10 opacity-80 shadow-lg",
      )}
    >
      <img
        src={videoWorkflowAssetContent(projectId, asset.asset_id)}
        alt={asset.filename}
        loading="lazy"
        className="h-full w-full object-cover"
      />
      <span className="absolute left-1 top-1 rounded bg-background/90 px-1.5 py-0.5 text-[0.65rem] font-semibold">
        {index + 1}
      </span>
      <button
        type="button"
        aria-label={`排序参考图 ${asset.filename}`}
        className="absolute bottom-1 right-1 flex h-6 w-6 items-center justify-center rounded bg-background/90 text-muted-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        {...handleDragAttributes}
        {...listeners}
      >
        <GripVertical className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function VideoAssetPanel({
  projectId,
  assets,
  selectedIds,
  maxSelected,
  maxAssetBytes,
  busy,
  onUpload,
  onToggle,
  onReorder,
  onDelete,
}: VideoAssetPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [uploadItems, setUploadItems] = useState<VideoWorkflowUploadItem[]>([]);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );
  const assetsById = new Map(assets.map((asset) => [asset.asset_id, asset]));
  const selectedAssets = selectedIds
    .map((assetId) => assetsById.get(assetId))
    .filter((asset): asset is VideoReferenceAsset => Boolean(asset));

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    const { items, validFiles } = createVideoWorkflowUploadItems(Array.from(files), maxAssetBytes);
    setUploadItems(items);
    if (inputRef.current) inputRef.current.value = "";
    for (const file of validFiles) {
      await uploadSingleFile(file);
    }
    setUploadItems((current) => {
      const hasUploaded = current.some((item) => item.status === "uploaded");
      const hasError = current.some((item) => item.status === "error");
      if (!hasUploaded || !hasError) return current;
      return current.map((item) =>
        item.status === "uploaded"
          ? { ...item, message: "部分参考图已上传" }
          : item,
      );
    });
  }

  async function uploadSingleFile(file: File) {
    setUploadItems((current) => markVideoWorkflowUploadUploading(current, [file]));
    try {
      const result = await onUpload([file]);
      const serverError = result.errors?.find((item) => item.filename === file.name);
      if (!result.ok || serverError) {
        setUploadItems((current) =>
          markVideoWorkflowUploadFailure(current, [file], serverError?.message || result.msg || "网络失败，请重试"),
        );
        return;
      }
      setUploadItems((current) => markVideoWorkflowUploadUploaded(current, [file]));
    } catch {
      setUploadItems((current) =>
        markVideoWorkflowUploadFailure(current, [file], "网络失败，请重试"),
      );
    }
  }

  async function retryUpload(itemId: string) {
    const files = retryableVideoWorkflowUploadFiles(uploadItems, itemId);
    if (!files.length) return;
    setRetryingId(itemId);
    try {
      await uploadSingleFile(files[0]);
    } finally {
      setRetryingId(null);
    }
  }

  function handleToggle(assetId: string) {
    if (!selectedIds.includes(assetId) && selectedIds.length >= maxSelected) {
      toast.warning("Omni 最多使用 7 张参考图");
      return;
    }
    onToggle(assetId);
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const from = selectedIds.indexOf(String(active.id));
    const to = selectedIds.indexOf(String(over.id));
    if (from < 0 || to < 0) return;
    onReorder(arrayMove(selectedIds, from, to));
  }

  async function confirmDelete(assetId: string) {
    setDeletingId(assetId);
    await onDelete(assetId);
    setDeletingId(null);
  }

  return (
    <section className="rounded-md border border-border bg-card p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="t-module">项目素材</h3>
          <p className="mt-1 t-caption text-muted-foreground">已选 {selectedIds.length} / {maxSelected}</p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="gap-1.5"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          <Upload className="h-4 w-4" />
          上传
        </Button>
      </div>
      <input
        ref={inputRef}
        aria-label="上传参考图"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        multiple
        className="hidden"
        onChange={(event) => void handleFiles(event.target.files)}
      />

      <div className="mb-4 min-h-20 rounded-md border border-dashed border-border bg-muted/20 p-2">
        {selectedAssets.length ? (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={selectedIds} strategy={horizontalListSortingStrategy}>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {selectedAssets.map((asset, index) => (
                  <SortableSelectedItem key={asset.asset_id} asset={asset} projectId={projectId} index={index} />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        ) : (
          <div className="flex h-16 items-center justify-center gap-2 text-muted-foreground">
            <ImagePlus className="h-4 w-4" />
            <span className="t-caption">可直接文生视频</span>
          </div>
        )}
      </div>

      {uploadItems.length > 0 && (
        <div className="mb-4 space-y-2" aria-live="polite">
          {uploadItems.map((item) => (
            <div
              key={item.id}
              className={cn(
                "flex items-center gap-2 rounded-md border px-2 py-1.5 t-caption",
                item.status === "error"
                  ? "border-destructive/30 bg-destructive/5 text-destructive"
                  : "border-border bg-muted/20",
              )}
            >
              {item.status === "uploading" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : item.status === "error" ? (
                <CircleAlert className="h-3.5 w-3.5" />
              ) : item.status === "uploaded" ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
              ) : (
                <Upload className="h-3.5 w-3.5" />
              )}
              <span className="min-w-0 flex-1 truncate">{item.filename}</span>
              <span className="shrink-0 text-muted-foreground">
                {item.message || (item.status === "waiting" ? "等待上传" : "上传中")}
              </span>
              {item.status === "error" && (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-7 gap-1 px-2"
                  disabled={retryingId === item.id}
                  onClick={() => void retryUpload(item.id)}
                >
                  {retryingId === item.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <RotateCcw className="h-3.5 w-3.5" />
                  )}
                  重试
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        {assets.map((asset) => {
          const order = selectedIds.indexOf(asset.asset_id);
          const selected = order >= 0;
          return (
            <div
              key={asset.asset_id}
              className={cn(
                "group relative overflow-hidden rounded-md border bg-background",
                selected ? "border-primary ring-1 ring-primary/25" : "border-border",
              )}
            >
              <button
                type="button"
                className="block w-full text-left"
                onClick={() => handleToggle(asset.asset_id)}
              >
                <div className="aspect-video w-full overflow-hidden bg-muted">
                  <img
                    src={videoWorkflowAssetContent(projectId, asset.asset_id)}
                    alt={asset.filename}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform group-hover:scale-[1.02]"
                  />
                </div>
                <div className="min-w-0 px-2 py-2">
                  <div className="truncate t-caption text-foreground">{asset.filename}</div>
                  <div className="mt-0.5 t-caption text-muted-foreground">{asset.width}x{asset.height}</div>
                </div>
              </button>
              {selected && (
                <Badge className="absolute left-2 top-2 bg-primary text-primary-foreground">
                  {order + 1}
                </Badge>
              )}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    type="button"
                    size="icon"
                    variant="secondary"
                    className="absolute right-2 top-2 h-7 w-7"
                    disabled={deletingId === asset.asset_id}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>移除参考图</AlertDialogTitle>
                    <AlertDialogDescription>
                      该素材会从当前项目素材库移除，历史任务仍保留生成时的引用快照。
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction onClick={() => void confirmDelete(asset.asset_id)}>
                      移除
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          );
        })}
      </div>
    </section>
  );
}
