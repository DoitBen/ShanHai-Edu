import { cp, mkdir } from "node:fs/promises";
import { join } from "node:path";

const root = process.cwd();
const standaloneNextDir = join(root, ".next", "standalone", ".next");

await mkdir(standaloneNextDir, { recursive: true });

await cp(join(root, ".next", "static"), join(standaloneNextDir, "static"), {
  recursive: true,
});

await cp(join(root, "public"), join(root, ".next", "standalone", "public"), {
  recursive: true,
});
