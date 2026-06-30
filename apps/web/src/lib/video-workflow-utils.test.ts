import {
  addReference,
  isActiveVideoRun,
  moveReference,
  reusableReferenceIds,
} from "@/components/video-workflow/video-workflow-utils";

function assert(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}

assert(isActiveVideoRun({ status: "processing" } as never), "processing is active");
assert(isActiveVideoRun({ status: "completed_pending_download" } as never), "pending download is active");
assert(!isActiveVideoRun({ status: "completed" } as never), "completed is terminal");
assert(
  JSON.stringify(addReference(["a", "b"], "c", 7)) === JSON.stringify(["a", "b", "c"]),
  "selection preserves order",
);
assert(addReference(["a", "b", "c", "d", "e", "f", "g"], "h", 7).length === 7, "limit is enforced");
assert(
  JSON.stringify(moveReference(["a", "b", "c"], 2, 0)) === JSON.stringify(["c", "a", "b"]),
  "drag reorder works",
);
assert(
  JSON.stringify(reusableReferenceIds(["a", "deleted"], new Set(["a"]))) === JSON.stringify(["a"]),
  "deleted assets are excluded from reuse",
);
