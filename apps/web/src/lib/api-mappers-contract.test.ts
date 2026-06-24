import { draftToCreateProjectPayload, mapApiManifest, mapTextbookParseContent } from "./api-mappers";
import type { ApiManifest, ApiTextbookParseContent, NewProjectDraft } from "./types";
import { readFileSync } from "node:fs";

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
      latest_transition: {
        transition_id: "trans_manifest",
        project_id: "proj_manifest",
        node_id: "ppt_assembly_plan",
        from_status: "drafted",
        to_status: "needs_review",
        trigger: "dependency_gate_blocked",
        triggered_at: "2026-06-22T00:00:02Z",
        triggered_by_user_id: null,
        version_id_before: "ver_before",
        version_id_after: "ver_manifest",
        reason: "rule_id=R010; handled_by=StateEngine; upstream lesson_plan status=needs_review",
      },
      review_reason: {
        trigger: "dependency_gate_blocked",
        reason: "rule_id=R010; handled_by=StateEngine; upstream lesson_plan status=needs_review",
        version_id_before: "ver_before",
        version_id_after: "ver_manifest",
      },
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
assert(stage.latestTransition?.trigger === "dependency_gate_blocked", "stage latest transition must come from API manifest");
assert(stage.reviewTrigger === "dependency_gate_blocked", "stage review trigger must come from API manifest");
assert(stage.reviewReason?.includes("StateEngine"), "stage review reason must come from API manifest");

const deliveryManifest: ApiManifest = {
  ...manifest,
  nodes: [
    {
      project_id: "proj_manifest",
      node_id: "final_delivery",
      title: "最终交付",
      step: 9,
      branch: "shared",
      depends_on: ["pptx_artifact", "final_video"],
      schema: "schemas/final_delivery.schema.json",
      status: "needs_review",
      current_version_id: "ver_delivery",
      updated_at: "2026-06-22T00:00:04Z",
      artifact: {
        lesson_plan_path: "exports/final_delivery/lesson_plan.md",
        pptx_final_path: "exports/final_delivery/deck.pptx",
        video_final_path: "exports/final_delivery/final_video.mp4",
        delivery_manifest_path: "exports/final_delivery/delivery_manifest.json",
        gate_result_json_path: "exports/final_delivery/gate_result.json",
      },
    },
  ],
};

const deliveryStage = mapApiManifest(deliveryManifest).stages[0];
assert(
  deliveryStage.artifact?.delivery_manifest_path === "exports/final_delivery/delivery_manifest.json",
  "final_delivery artifact paths must be preserved from API manifest",
);
assert(deliveryStage.artifact?.pptx_final_path?.endsWith(".pptx"), "final_delivery PPTX path must be preserved");
assert(deliveryStage.artifact?.video_final_path?.endsWith(".mp4"), "final_delivery video path must be preserved");

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
  nameEdited: true,
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
  selectedLessonReferenceId: "lp_demo",
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
assert(payload.reference_lesson_plan_id === "lp_demo", "reference lesson plan id must be sent to project API");

const parseFirstDraft: NewProjectDraft = {
  ...draft,
  name: "",
  nameEdited: false,
  subject: "数学",
  grade: "三年级",
  textbookVersion: "人教版",
  volume: "上册",
};
const parseFirstPayload = draftToCreateProjectPayload(parseFirstDraft, {
  fallbackName: "教材解析临时项目",
});
assert(parseFirstPayload.name === "教材解析临时项目", "textbook-first parse must be able to create a temporary backend project before project name prefill");

const textbookContent: ApiTextbookParseContent = {
  subject: "math",
  grade: "1",
  textbook_version: "renjiao",
  volume: "shang",
  lesson_title: "6-9的加、减法",
  textbook_id: "renjiao-grade1-volume1-2024",
  textbook_version_id: "renjiao-grade1-volume1-2024-v1",
  textbook_meta: {
    subject: "math",
    grade: "1",
    textbook_version: "renjiao",
    volume: "shang",
    title: "人教版小学数学一年级上册",
  },
  knowledge_points: [
    {
      id: "kp_001",
      title: "5以内数的认识",
      unit: "5以内数的认识和加、减法",
      page_start: 14,
      page_end: 23,
      pdf_page_start: 19,
      pdf_page_end: 28,
      keywords: ["1-5"],
    },
    {
      id: "kp_006",
      title: "6-9的加、减法",
      unit: "6-10的认识和加、减法",
      page_start: 44,
      page_end: 53,
      pdf_page_start: 49,
      pdf_page_end: 58,
      keywords: ["6和7", "8和9"],
      asset_package: {
        asset_id: "ta_kp006",
        slice_pdf_path: "knowledge-points/kp_006/source.pdf",
        mineru_md_path: "knowledge-points/kp_006/mineru.md",
        textbook_pages: "44-53",
        pdf_pages: "49-58",
        parse_status: "indexed",
        review_status: "needs_review",
        mineru_job_id: "tj_kp006",
        checksum: "sha256-demo",
        download_urls: {
          slice_pdf: "files/knowledge-points/kp_006/source.pdf",
          mineru_md: "files/knowledge-points/kp_006/mineru.md",
        },
      },
    },
  ],
  selected_knowledge_point_id: "kp_006",
  selected_knowledge_point: {
    knowledge_point_id: "kp_006",
    title: "6-9的加、减法",
    source_pages: {
      textbook_pages: "44-53",
      pdf_pages: "49-58",
    },
    markdown_path: "knowledge-points/kp_006.md",
    mineru_md_path: "knowledge-points/kp_006/mineru.md",
    slice_pdf_path: "knowledge-points/kp_006/source.pdf",
    asset_package: {
      asset_id: "ta_kp006",
      slice_pdf_path: "knowledge-points/kp_006/source.pdf",
      mineru_md_path: "knowledge-points/kp_006/mineru.md",
      textbook_pages: "44-53",
      pdf_pages: "49-58",
      parse_status: "indexed",
      review_status: "needs_review",
      mineru_job_id: "tj_kp006",
      checksum: "sha256-demo",
      download_urls: {
        slice_pdf: "files/knowledge-points/kp_006/source.pdf",
        mineru_md: "files/knowledge-points/kp_006/mineru.md",
      },
    },
    markdown: "# 《6-9的加、减法》教材内容整理\n\n待 MinerU 精抽。",
  },
};

const parsedTextbook = mapTextbookParseContent(textbookContent, draft);

assert(parsedTextbook.subject === "数学", "textbook parse mapper must localize subject");
assert(parsedTextbook.grade === "一年级", "textbook parse mapper must localize grade");
assert(parsedTextbook.textbookVersion === "人教版", "textbook parse mapper must localize textbook version");
assert(parsedTextbook.volume === "上册", "textbook parse mapper must localize volume");
assert(parsedTextbook.textbookTitle === "人教版小学数学一年级上册", "textbook title must come from API meta");
assert(parsedTextbook.textbookId === "renjiao-grade1-volume1-2024", "textbook id must be preserved");
assert(parsedTextbook.knowledgePoints?.length === 2, "multiple lesson-level knowledge points must be preserved");
assert(parsedTextbook.knowledgePoints?.[1].id === "kp_006", "knowledge point id must be preserved");
assert(parsedTextbook.knowledgePoints?.[1].pageStart === 44, "textbook page range must be preserved");
assert(parsedTextbook.knowledgePoints?.[1].pdfPageStart === 49, "pdf page range must be preserved");
assert(parsedTextbook.selectedKnowledgePointId === "kp_006", "selected knowledge point id must come from API");
assert(parsedTextbook.selectedKnowledgePointMarkdownPath === "knowledge-points/kp_006.md", "selected markdown path must be preserved");
assert(parsedTextbook.selectedKnowledgePointAssetPackage?.slicePdfPath === "knowledge-points/kp_006/source.pdf", "selected slice pdf path must be preserved");
assert(parsedTextbook.selectedKnowledgePointAssetPackage?.assetId === "ta_kp006", "selected asset id must be preserved");
assert(parsedTextbook.selectedKnowledgePointAssetPackage?.mineruMdPath === "knowledge-points/kp_006/mineru.md", "selected mineru md path must be preserved");
assert(parsedTextbook.selectedKnowledgePointAssetPackage?.mineruJobId === "tj_kp006", "selected mineru job id must be preserved");
assert(parsedTextbook.selectedKnowledgePointAssetPackage?.downloadUrls?.slicePdf === "files/knowledge-points/kp_006/source.pdf", "selected slice pdf download path must be preserved");
assert(parsedTextbook.selectedKnowledgePointPages?.textbookPages === "44-53", "selected textbook pages must be preserved");
assert(parsedTextbook.selectedKnowledgePointMarkdown?.includes("6-9的加、减法"), "selected markdown must be preserved");

const newProjectScreenSource = readFileSync("src/components/screens/NewProjectScreen.tsx", "utf8");
assert(
  newProjectScreenSource.includes("const chooseKnowledgePoint = (knowledgePointId: string) => {") &&
    newProjectScreenSource.includes("selectedKnowledgePointId: knowledgePointId") &&
    newProjectScreenSource.includes("onValueChange={chooseKnowledgePoint}"),
  "knowledge point switch must update the draft binding before project creation",
);
const storeSource = readFileSync("src/lib/store.ts", "utf8");
assert(
  storeSource.split("draftToCreateProjectPayload(nextDraft)").length - 1 >= 3,
  "textbook parse, library load, and knowledge point switch must persist project textbook binding immediately",
);
