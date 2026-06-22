#!/usr/bin/env node
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  args.set(process.argv[index], process.argv[index + 1]);
}

const root = path.resolve(args.get("--root") || process.cwd());
const sentinels = [
  args.get("--sentinel"),
  process.env.DEEPSEEK_API_KEY,
  process.env.OCTO_API_KEY,
  process.env.IMAGEGEN_API_KEY,
  process.env.MINMAX_API_KEY,
  process.env.BACKEND_API_TOKEN,
].filter((value) => typeof value === "string" && value.length > 0);

const scanDirs = [
  ".next/static",
  ".next/standalone/.next/static",
  ".next/standalone/public",
  "public",
];
const textExtensions = new Set([
  ".js",
  ".mjs",
  ".cjs",
  ".css",
  ".html",
  ".json",
  ".txt",
  ".map",
  ".svg",
  ".xml",
  ".webmanifest",
]);

const findings = [];
for (const relDir of scanDirs) {
  const absDir = path.join(root, relDir);
  if (!existsSync(absDir)) {
    continue;
  }
  for (const file of walk(absDir)) {
    if (!textExtensions.has(path.extname(file).toLowerCase())) {
      continue;
    }
    const text = readFileSync(file, "utf8");
    for (const sentinel of sentinels) {
      if (text.includes(sentinel)) {
        findings.push({ file: path.relative(root, file), kind: "sentinel" });
        break;
      }
    }
    const publicSecretNames = text.match(/\bNEXT_PUBLIC_[A-Z0-9_]*(?:KEY|TOKEN|SECRET)[A-Z0-9_]*\b/g) || [];
    if (publicSecretNames.length > 0) {
      findings.push({ file: path.relative(root, file), kind: "public-secret-env-name" });
    }
  }
}

if (findings.length > 0) {
  console.error("Client-visible secret scan failed:");
  for (const finding of findings) {
    console.error(`- ${finding.kind}: ${finding.file}`);
  }
  process.exit(1);
}

console.log("Client-visible secret scan passed.");

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    const abs = path.join(dir, entry);
    const stat = statSync(abs);
    if (stat.isDirectory()) {
      yield* walk(abs);
    } else if (stat.isFile()) {
      yield abs;
    }
  }
}
