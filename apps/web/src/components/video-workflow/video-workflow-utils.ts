import type { VideoWorkflowRun } from "@/lib/types";

export function isActiveVideoRun(run: Pick<VideoWorkflowRun, "status">): boolean {
  return (
    run.status === "submitting" ||
    run.status === "queued" ||
    run.status === "processing" ||
    run.status === "completed_pending_download"
  );
}

export function addReference(current: string[], assetId: string, limit: number): string[] {
  if (current.includes(assetId) || current.length >= limit) return current;
  return [...current, assetId];
}

export function moveReference(current: string[], from: number, to: number): string[] {
  if (from === to || from < 0 || to < 0 || from >= current.length || to >= current.length) return current;
  const next = [...current];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}

export function reusableReferenceIds(ids: string[], activeIds: Set<string>): string[] {
  return ids.filter((id) => activeIds.has(id));
}
