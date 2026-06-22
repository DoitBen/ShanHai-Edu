import type { DataMode, WorkflowStage } from "./types";

export function canEditStageInWorkspace(dataMode: DataMode, stage?: WorkflowStage | null): boolean {
  if (!stage) return false;
  if (dataMode === "demo") return true;
  return stage.capabilities?.can_edit === true;
}
