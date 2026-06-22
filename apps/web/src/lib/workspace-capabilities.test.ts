import { canEditStageInWorkspace } from "./workspace-capabilities";
import type { WorkflowStage } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

function stage(patch: Partial<WorkflowStage>): WorkflowStage {
  return {
    key: "ppt-plan",
    apiNodeId: "ppt_assembly_plan",
    title: "PPT 总装方案",
    branch: "ppt",
    order: 2,
    status: "pending_confirm",
    summary: "",
    input: "",
    result: "{}",
    evidence: [],
    logs: [],
    ...patch,
  };
}

assert(
  canEditStageInWorkspace("api", stage({ key: "ppt-plan", capabilities: { can_generate: false, can_edit: true, can_approve: false, can_redo: false, can_skip: false } })) === true,
  "api mode must allow PPT editing when manifest capability can_edit is true",
);

assert(
  canEditStageInWorkspace("api", stage({ key: "pptx-generation", capabilities: { can_generate: false, can_edit: false, can_approve: true, can_redo: false, can_skip: false } })) === false,
  "api mode must block artifact editing when manifest capability can_edit is false",
);

assert(
  canEditStageInWorkspace("api", stage({ key: "open-lesson-plan" })) === false,
  "api mode must not fall back to hard-coded editable stage keys when capabilities are absent",
);
