import { draftToCreateProjectPayload, mapApiManifest } from "./api-mappers";
import type { ApiManifest, NewProjectDraft } from "./types";

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

const skippedManifest: ApiManifest = {
  ...manifest,
  nodes: [
    {
      project_id: "proj_manifest",
      node_id: "lesson_plan",
      title: "公开课教案",
      step: 1,
      branch: "shared",
      depends_on: [],
      schema: "schemas/lesson_plan.schema.json",
      status: "approved",
      current_version_id: "ver_lesson",
      updated_at: "2026-06-22T00:00:01Z",
    },
    {
      project_id: "proj_manifest",
      node_id: "intro_selection",
      title: "导入设计选择集",
      step: 1.5,
      branch: "intro_video",
      depends_on: ["lesson_plan"],
      schema: "schemas/intro_selection.schema.json",
      status: "skipped",
      current_version_id: null,
      updated_at: "2026-06-22T00:00:02Z",
    },
    {
      project_id: "proj_manifest",
      node_id: "ppt_assembly_plan",
      title: "PPT 总装方案",
      step: 2,
      branch: "ppt",
      depends_on: ["lesson_plan"],
      schema: "schemas/ppt_assembly_plan.schema.json",
      status: "not_started",
      current_version_id: null,
      updated_at: "2026-06-22T00:00:03Z",
    },
  ],
};

const skippedMapped = mapApiManifest(skippedManifest);
const skippedStages = Object.fromEntries(skippedMapped.stages.map((item) => [item.apiNodeId, item]));

assert(skippedStages.intro_selection.status === "skipped", "skipped backend status must be preserved as UI skipped");
assert(skippedMapped.project.progress === 67, "approved and skipped stages must both count toward progress");
assert(skippedMapped.project.currentStage === "ppt-plan", "current stage must skip approved/skipped nodes");
assert(skippedMapped.project.nextAction.includes("PPT 总装方案"), "next action must point to first non-passable stage");

const draft: NewProjectDraft = {
  step: 1,
  name: "  角色视觉契约项目  ",
  subject: "数学",
  grade: "二年级",
  textbookVersion: "人教版",
  volume: "上册",
  lessonType: "公开课",
  characterProfile: "小山是非写实卡通数学引导员",
  characterSafetyRule: "禁真人、photorealistic、real child",
  visualPalette: "暖纸白 #F6F5F1、深青灰 #2D4356、古铜金 #9C7C4E",
  visualStyleKeywords: "温润、克制、真实生活情境",
  fontPreference: "系统无衬线中文优先",
  complianceNotes: "所有儿童角色必须为非写实卡通或剪影风格。",
  apiProjectId: null,
  textbookFileName: "",
  textbookContent: "",
  parseResult: null,
  parseStatus: "idle",
  parseError: null,
  selectedKnowledgePointId: "",
  videoPurpose: "",
  videoTypes: [],
  videoCountPerType: 1,
  videoTheme: "",
  audience: "",
  duration: "",
  creativeBrief: "",
  pptStyle: "",
  pptSlides: 8,
  pptStructure: "",
  outputPath: "",
  constraints: "",
  safeMode: true,
};

const payload = draftToCreateProjectPayload(draft);

assert(payload.name === "角色视觉契约项目", "project name must be trimmed");
assert(payload.character_profile === draft.characterProfile, "character profile must be sent to create project API");
assert(payload.character_safety_rule === draft.characterSafetyRule, "character safety rule must be sent to create project API");
assert(payload.visual_palette === draft.visualPalette, "visual palette must be sent to create project API");
assert(payload.visual_style_keywords === draft.visualStyleKeywords, "visual style keywords must be sent to create project API");
assert(payload.font_preference === draft.fontPreference, "font preference must be sent to create project API");
assert(payload.compliance_notes === draft.complianceNotes, "compliance notes must be sent to create project API");
