import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

function readProjectFile(path: string): string {
  return readFileSync(join(root, path), "utf-8");
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const workspace = readProjectFile("src/components/screens/ProjectWorkspaceScreen.tsx");
const apiClient = readProjectFile("src/lib/api-client.ts");
const store = readProjectFile("src/lib/store.ts");
const types = readProjectFile("src/lib/types.ts");

assert(types.includes("interface ApiProjectWorkspace"), "types must define ApiProjectWorkspace");
assert(types.includes("current_step_id"), "workspace type must include current_step_id");
assert(types.includes("sub_gates"), "workspace type must include step sub_gates");
assert(types.includes("developer_diagnostics"), "workspace type must include developer_diagnostics");

assert(apiClient.includes("fetchProjectWorkspace"), "api client must expose fetchProjectWorkspace");
assert(
  apiClient.includes("/projects/${encodeURIComponent(projectId)}/workspace"),
  "fetchProjectWorkspace must call /projects/{projectId}/workspace",
);

assert(store.includes("workspaceByProject"), "store must cache workspaceByProject");
assert(store.includes("workspaceStatusByProject"), "store must track workspace load status");
assert(store.includes("loadProjectWorkspace"), "store must expose loadProjectWorkspace");
assert(store.includes("fetchProjectWorkspace"), "store must call fetchProjectWorkspace");
assert(
  store.includes("await get().loadProjectWorkspace(projectId)"),
  "store must load workspace with project workspace entry points",
);

assert(
  workspace.includes("workspaceByProject"),
  "workspace screen must read workspaceByProject before deriving user steps",
);
assert(
  workspace.includes("buildUserStepViewsFromWorkspace"),
  "workspace screen must prefer backend workspace steps for user-step states",
);
assert(
  workspace.includes("workspaceStepToUserStepView"),
  "workspace screen must map API workspace step states into user steps",
);
assert(
  workspace.includes("workspaceStepSubGates"),
  "workspace screen must pass API workspace sub_gates into ordinary sub-status lists",
);
assert(
  workspace.includes("selectedStepStage"),
  "workspace screen must select the active stage from the backend workspace step before rendering the task card",
);
assert(
  workspace.includes("explicitOverrideStepView ? selectedStage?.key : undefined"),
  "workspace step selection must use selectedStage only for explicit user override",
);
assert(
  (workspace.match(/currentStepLabel=\{workspaceHeaderCurrentStepLabel\}/g) || []).length >= 2,
  "workspace header must show the backend workspace user step instead of stale manifest stage",
);
assert(
  (workspace.match(/nextActionOverride=\{workspaceHeaderNextAction\}/g) || []).length >= 2,
  "workspace header next action must follow the backend workspace task stage",
);
assert(
  workspace.includes("subGates={workspaceStepSubGates"),
  "PPT/video sub-status lists must receive workspace sub_gates before manifest fallback",
);

for (const label of [
  "项目信息",
  "教材内容",
  "教案生成",
  "导入视频方案",
  "PPT 草稿",
  "视频生成",
  "最终交付",
]) {
  assert(workspace.includes(`label: "${label}"`), `workspace must define user step ${label}`);
}

assert(workspace.includes("UserStepRail"), "workspace must render user-facing 7-step rail");
assert(workspace.includes("WorkspaceTaskCard"), "workspace must render a user-facing task card");
assert(workspace.includes("LockedStepCard"), "workspace must render locked step guidance");
assert(workspace.includes("LessonPlanMarkdownEditor"), "lesson plan must use Markdown edit/preview component");
assert(workspace.includes("Markdown 预览"), "lesson plan must expose Markdown preview");
assert(workspace.includes("<details className=\"rounded-md border border-border bg-muted/10\""), "developer diagnostics must be collapsed by default");
assert(workspace.includes(">开发诊断<"), "developer diagnostics title must be standardized");
assert(workspace.includes("showAdvancedJson={false}"), "ordinary workspace result panels must hide advanced JSON editors");
assert(workspace.includes("showProviderDetails={false}"), "ordinary workspace result panels must hide provider details");
assert(workspace.includes("课堂衔接点"), "ordinary workspace must use teacher-facing course-anchor wording");
assert(workspace.includes("buildTextbookContentSummary"), "textbook_parse must use a teacher-facing textbook summary");
assert(workspace.includes("TextbookContentPreviewActions"), "textbook_parse must expose textbook preview actions in the ordinary task card");
assert(workspace.includes("resolveTextbookSlicePreviewUrl"), "textbook slice PDF preview must use a user-facing proxy URL");
assert(workspace.includes("教材页段可预览"), "ordinary textbook summary must show PDF slice availability in teacher-facing wording");
assert(workspace.includes("buildPptxArtifactSummary"), "pptx artifact must use a teacher-facing PPTX summary");
assert(workspace.includes("PptxArtifactResult"), "pptx artifact must render a dedicated ordinary result card");
assert(
  workspace.includes("stage.key === \"pptx-generation\""),
  "pptx-generation must be handled before generic ordinary summary fallback",
);

for (const label of [
  "结构方案",
  "逐页脚本",
  "视觉资产",
  "PPTX 文件",
  "文稿",
  "分场剧本",
  "资产与首帧",
  "分镜",
  "clip/TTS/合成",
]) {
  assert(workspace.includes(label), `workspace must expose T142 user-facing sub status ${label}`);
}

for (const label of [
  "PptDraftSubStatusList",
  "VideoGenerationSubStatusList",
]) {
  assert(workspace.includes(label), `workspace must render ${label} in ordinary task card`);
}

for (const label of [
  "课程锚点",
  "课堂落点问题",
  "不提前讲解内容",
]) {
  assert(workspace.includes(label), `intro video plan must emphasize ${label}`);
}

assert(
  workspace.includes("这只是本地演示用视频文件，不代表真实成片质量。"),
  "ordinary video result must distinguish local placeholder/fake video from real final video",
);
assert(
  workspace.includes("真实成片需要看到视频片段、中文旁白、字幕和合成文件都完成后再验收。"),
  "ordinary video result must explain real-video completion criteria in teacher-facing wording",
);

const mainBeforeDiagnostics = workspace.split("function DeveloperDiagnostics")[0] || workspace;
const editableSummaryBody =
  workspace.match(/function buildEditableNodeSummary[\s\S]*?function buildTextbookContentSummary/)?.[0] ||
  "";
const genericSummaryBody =
  workspace.match(/return \{\s*title: `\$\{stage\.title\}摘要`[\s\S]*?\n  \};\n}/)?.[0] ||
  "";
const selectedStepViewBody =
  workspace.match(/const selectedStepView =[\s\S]*?userStepViews\[0\];/)?.[0] ||
  "";
const redlineTerms = [
  "JSON",
  "provider",
  "manifest",
  "node_id",
  "StateEngine",
  "schema",
  "R010",
  "输出路径",
  "安全模式",
  "storage",
];

assert(!mainBeforeDiagnostics.includes("title=\"流程节点\""), "main workspace must not present technical node rail title");
assert(!mainBeforeDiagnostics.includes("title=\"节点详情\""), "main workspace must not present technical node detail title");
assert(!mainBeforeDiagnostics.includes("后端 manifest 节点，点击节点读取详情"), "main workspace must not describe backend manifest nodes");
assert(!mainBeforeDiagnostics.includes("selected_anchor"), "main workspace must not expose internal anchor field names");
assert(!mainBeforeDiagnostics.includes("完整内容仍在下方 JSON 中编辑"), "ordinary workspace must not tell teachers to edit JSON");
const ordinaryTextSnippets = [
  workspace.match(/const USER_WORKSPACE_STEPS[\s\S]*?\/\* ============================================================/)?.[0] || "",
  workspace.match(/function WorkspaceTaskCard[\s\S]*?function InfoBlock/)?.[0] || "",
  workspace.match(/function PptDraftSubStatusList[\s\S]*?function UserActionNotice/)?.[0] || "",
  workspace.match(/function CurrentResultPanel[\s\S]*?function LessonPlanMarkdownEditor/)?.[0] || "",
  workspace.match(/function LessonPlanStructureSummary[\s\S]*?function IntroSelectionResult/)?.[0] || "",
  workspace.match(/function IntroSelectionResult[\s\S]*?function VideoAssetResult/)?.[0] || "",
  workspace.match(/function VideoAssetResult[\s\S]*?function FinalVideoResult/)?.[0] || "",
  workspace.match(/function FinalVideoResult[\s\S]*?function FinalVideoAudioPanel/)?.[0] || "",
  workspace.match(/function FinalVideoDownloadPanel[\s\S]*?function PptExportPanel/)?.[0] || "",
  workspace.match(/function PptExportPanel[\s\S]*?type UserStepView/)?.[0] || "",
].join("\n");

for (const term of [
  "真实 API 模式",
  "演示模式",
  "fake provider",
  "PPTX artifact",
  "manifest artifact",
  "OCTO_REQUEST_FAILED",
  "请先填写课程锚点 selected_anchor",
]) {
  assert(
    !ordinaryTextSnippets.includes(term),
    `ordinary workspace text must not expose ${term}`,
  );
}
for (const term of redlineTerms) {
  assert(
    !genericSummaryBody.includes(term),
    `generic ordinary summary before developer diagnostics must not expose redline term ${term}`,
  );
}
for (const term of ["JSON", "provider", "fake", "artifact", "manifest", "selected_anchor"]) {
  assert(
    !editableSummaryBody.includes(term),
    `ordinary editable summary before developer diagnostics must not expose engineering term ${term}`,
  );
}
assert(
  editableSummaryBody.includes("if (stage.key === \"textbook-parse\")"),
  "textbook_parse must be handled before generic ordinary summary fallback",
);
assert(
  editableSummaryBody.includes("if (stage.key === \"final-delivery\")"),
  "final_delivery must be handled before generic ordinary summary fallback",
);
assert(
  workspace.includes("function buildFinalDeliverySummary"),
  "final_delivery must use a dedicated teacher-facing delivery summary",
);
assert(
  !workspace.includes("key={item.label}"),
  "teacher-facing summary items must use stable unique keys, not label-only keys",
);
assert(
  workspace.includes("selectedUserStepOverride"),
  "completed step review must use an explicit user override instead of stale selectedKey",
);
assert(
  workspace.includes("findValidUserStepOverride(userStepViews, selectedUserStepOverride)"),
  "workspace step selection must validate explicit user override",
);
assert(
  selectedStepViewBody.includes("explicitOverrideStepView ||") &&
    selectedStepViewBody.includes("workspaceCurrentStepView ||") &&
    selectedStepViewBody.indexOf("explicitOverrideStepView ||") <
      selectedStepViewBody.indexOf("workspaceCurrentStepView ||"),
  "selectedStepView priority must be explicit override before workspace current step",
);
assert(
  workspace.includes("setSelectedUserStepOverride(target.step.id)"),
  "handleSelectUserStep must set explicit user override only after user click",
);
assert(
  (workspace.match(/setSelectedUserStepOverride\(null\)/g) || []).length >= 3,
  "workspace must clear user override when returning to current step, refreshing, or progressing",
);
assert(
  workspace.includes("const shouldShowOrdinaryEvidence = stepView.step.id !== \"final-delivery\""),
  "final delivery ordinary task card must hide raw evidence preview buttons",
);
assert(
  workspace.includes("shouldShowOrdinaryEvidence && stage.evidence.length > 0"),
  "ordinary evidence preview must be gated and unavailable for final delivery",
);
