export type VideoWorkflowUploadItemStatus = "waiting" | "uploading" | "uploaded" | "error";

export interface VideoWorkflowUploadItem {
  id: string;
  filename: string;
  status: VideoWorkflowUploadItemStatus;
  message?: string;
  file: File;
}

export function createVideoWorkflowUploadItems(files: File[], maxAssetBytes: number): {
  items: VideoWorkflowUploadItem[];
  validFiles: File[];
} {
  const items = files.map((file, index) => {
    const base = {
      id: uploadItemId(file, index),
      filename: file.name,
      file,
    };
    if (file.size > maxAssetBytes) {
      return {
        ...base,
        status: "error" as const,
        message: `超过 ${formatMegabytes(maxAssetBytes)}`,
      };
    }
    return {
      ...base,
      status: "waiting" as const,
      message: "等待上传",
    };
  });
  return {
    items,
    validFiles: items.filter((item) => item.status !== "error").map((item) => item.file),
  };
}

export function markVideoWorkflowUploadUploading(
  items: VideoWorkflowUploadItem[],
  files: File[],
): VideoWorkflowUploadItem[] {
  const ids = new Set(files.map((file) => uploadItemId(file, findFileIndex(items, file))));
  return items.map((item) =>
    ids.has(item.id)
      ? { ...item, status: "uploading", message: "上传中" }
      : item,
  );
}

export function markVideoWorkflowUploadUploaded(
  items: VideoWorkflowUploadItem[],
  files: File[],
): VideoWorkflowUploadItem[] {
  const ids = new Set(files.map((file) => uploadItemId(file, findFileIndex(items, file))));
  return items.map((item) =>
    ids.has(item.id)
      ? { ...item, status: "uploaded", message: "已加入素材库" }
      : item,
  );
}

export function markVideoWorkflowUploadFailure(
  items: VideoWorkflowUploadItem[],
  files: File[],
  message: string,
): VideoWorkflowUploadItem[] {
  const ids = new Set(files.map((file) => uploadItemId(file, findFileIndex(items, file))));
  return items.map((item) =>
    ids.has(item.id)
      ? { ...item, status: "error", message }
      : item,
  );
}

export function retryableVideoWorkflowUploadFiles(items: VideoWorkflowUploadItem[], itemId: string): File[] {
  const item = items.find((candidate) => candidate.id === itemId);
  return item?.status === "error" ? [item.file] : [];
}

export function uploadItemId(file: File, index: number): string {
  return `${index}:${file.name}:${file.size}:${file.lastModified}`;
}

function findFileIndex(items: VideoWorkflowUploadItem[], file: File): number {
  const index = items.findIndex((item) => item.file === file);
  return index >= 0 ? index : 0;
}

function formatMegabytes(bytes: number): string {
  return `${Math.max(1, Math.floor(bytes / 1024 / 1024))}MB`;
}
