import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(process.cwd(), "src/components/screens/NewProjectScreen.tsx"), "utf-8");

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const forbiddenTeacherCopy = [
  "导入教材",
  "切分教材",
  "解析教材内容",
  "重新解析",
  "重新导入教材",
  "教材切分",
  "教材解析",
];
for (const copy of forbiddenTeacherCopy) {
  assert(!source.includes(copy), `new project page ordinary flow must not expose backend processing copy: ${copy}`);
}

const requiredTeacherCopy = [
  "选择起点/资料来源",
  "使用教材库",
  "直接使用教案",
  "从教案库选择",
  "上传教案文件",
  "人教版 / 小学数学 / 一年级 / 上册",
  "选择知识点",
  "可选教案参考",
];
for (const copy of requiredTeacherCopy) {
  assert(source.includes(copy), `new project page must expose teacher source-choice copy: ${copy}`);
}

assert(!source.includes("parseDraftTextbook"), "new project page must not bind teacher flow to textbook parsing action");
assert(!source.includes("splitDraftTextbookAssets"), "new project page must not bind teacher flow to textbook splitting action");
assert(!source.includes("extractDraftTextbookAssets"), "new project page must not bind teacher flow to textbook content extraction action");
assert(!source.includes("uploadTextbookToLibrary"), "new project page must not upload textbooks from the teacher creation flow");
assert(source.includes("uploadLessonPlanToLibrary"), "new project page must upload teacher lesson-plan files to the lesson-plan library before project creation");
assert(source.includes("selectedLessonReferenceId: uploaded?.lesson_plan_id"), "uploaded lesson-plan files must become reference_lesson_plan_id for direct lesson projects");
assert(!source.includes("generateProjectNode"), "new project page must not generate backend nodes from the teacher creation flow");

assert(source.includes("查看核心知识点"), "core knowledge points must open from an action, not be permanently expanded");
assert(source.includes("关键词标签"), "keywords must be presented as selectable tags");
assert(source.includes("自定义时长"), "duration must support custom input");
assert(source.includes("PPT 结构模板"), "PPT structure must be selected from fixed templates");
assert(!source.includes('FieldGroup label="输出路径"'), "ordinary UI must not expose output path field");
assert(!source.includes("FieldLabel>安全模式"), "ordinary UI must not expose safe mode field");

const ordinaryUiForbiddenTerms = [
  "JSON",
  "storage",
  "API",
  "provider",
  "manifest",
  "node_id",
  "StateEngine",
  "schema",
  "R010",
];
const ordinaryCopyMatches = Array.from(
  source.matchAll(
    /(?:title|desc|label|placeholder|toast\.(?:success|error|info)\(|>\s*)(["'`])([^"'`{}<>]*(?:JSON|storage|API|provider|manifest|node_id|StateEngine|schema|R010)[^"'`{}<>]*)\1?/g,
  ),
).map((match) => match[2]);
for (const term of ordinaryUiForbiddenTerms) {
  assert(
    !ordinaryCopyMatches.some((copy) => copy.includes(term)),
    `new project ordinary UI must not expose technical redline term: ${term}`,
  );
}
