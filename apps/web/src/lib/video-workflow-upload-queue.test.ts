import {
  createVideoWorkflowUploadItems,
  markVideoWorkflowUploadFailure,
  markVideoWorkflowUploadUploading,
  markVideoWorkflowUploadUploaded,
  retryableVideoWorkflowUploadFiles,
} from "./video-workflow-upload-queue";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function file(name: string, size: number, lastModified: number): File {
  return new File(["x".repeat(size)], name, { type: "image/png", lastModified });
}

const files = [file("same.png", 16, 1000), file("same.png", 16, 2000), file("bad.png", 32, 3000)];
const created = createVideoWorkflowUploadItems(files, 20);

assert(created.validFiles.length === 2, "only files within the size limit should be uploadable");
assert(created.items.length === 3, "every selected file must get a visible queue item");
assert(new Set(created.items.map((item) => item.id)).size === 3, "queue ids must distinguish same-name files");
const oversized = created.items[2];
assert(oversized, "oversized row must exist");
assert(oversized.status === "error", "oversized files must be marked as failed immediately");
assert(oversized.message?.includes("超过"), "oversized files need a clear message");

const uploading = markVideoWorkflowUploadUploading(created.items, [files[0]]);
const firstUpload = uploading[0];
const secondUpload = uploading[1];
assert(firstUpload && secondUpload, "same-name upload rows must exist");
assert(firstUpload.status === "uploading", "first matching file should enter uploading");
assert(secondUpload.status === "waiting", "same-name files must not be updated by filename only");

const partial = markVideoWorkflowUploadFailure(uploading, [files[0]], "文件不是有效图片");
const failedUpload = partial[0];
assert(failedUpload, "failed upload row must exist");
assert(failedUpload.status === "error", "failed upload must remain visible");
assert(failedUpload.message === "文件不是有效图片", "failed upload must keep server message");
assert(failedUpload.file === files[0], "failed upload must retain file for retry");

const retryFiles = retryableVideoWorkflowUploadFiles(partial, failedUpload.id);
assert(retryFiles.length === 1 && retryFiles[0] === files[0], "retry must return the original failed file only");

const uploaded = markVideoWorkflowUploadUploaded(partial, [files[1]]);
const firstResult = uploaded[0];
const secondResult = uploaded[1];
assert(firstResult && secondResult, "upload result rows must exist");
assert(secondResult.status === "uploaded", "successful same-name file must be marked independently");
assert(firstResult.status === "error", "successful same-name file must not clear another failed row");
