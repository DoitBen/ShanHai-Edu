import { mapApiManifest } from "./api-mappers";
import type { ApiManifest } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const manifest: ApiManifest = {
  project: {
    project_id: "proj_manifest",
    name: "Manifest 契约测试",
    subject: "math",
    grade: "2",
    textbook_version: "renjiao",
    volume: "shang",
    lesson_type: "public",
    created_at: "2026-06-22T00:00:00Z",
    status: "active",
    project_dir: "storage/projects/proj_manifest",
  },
  nodes: [
    {
      project_id: "proj_manifest",
      node_id: "ppt_assembly_plan",
      title: "API 返回的 PPT 总装",
      step: 2,
      branch: "ppt",
      depends_on: ["lesson_plan"],
      schema: "schemas/ppt_assembly_plan.schema.json",
      status: "needs_review",
      current_version_id: "ver_manifest",
      updated_at: "2026-06-22T00:00:01Z",
      capabilities: {
        can_generate: true,
        can_edit: true,
        can_approve: true,
        can_redo: true,
        can_skip: false,
      },
      artifact: null,
      rule_summary: {
        hard_block_count: 0,
        warning_count: 1,
        failed_rule_ids: ["R023"],
        warning_rule_ids: ["R023"],
      },
    },
  ],
};

const mapped = mapApiManifest(manifest);
const stage = mapped.stages[0];

assert(stage.title === "API 返回的 PPT 总装", "stage title must come from API manifest");
assert(stage.order === 2, "stage order must come from API step");
assert(stage.branch === "ppt", "stage branch must come from API branch");
assert(stage.summary.includes("schemas/ppt_assembly_plan.schema.json"), "stage summary must expose API schema");
assert(stage.summary.includes("lesson_plan"), "stage summary must expose API dependencies");
assert(stage.capabilities?.can_edit === true, "stage capabilities must come from API manifest");
assert(stage.ruleSummary?.warning_rule_ids.includes("R023"), "stage rule summary must come from API manifest");
