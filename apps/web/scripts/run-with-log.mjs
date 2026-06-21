import { createWriteStream } from "node:fs";
import { spawn } from "node:child_process";

const [, , logFile, ...rest] = process.argv;

const separatorIndex = rest.indexOf("--");
const envPairs = separatorIndex >= 0 ? rest.slice(0, separatorIndex) : [];
const commandParts = separatorIndex >= 0 ? rest.slice(separatorIndex + 1) : rest;
const [command, ...args] = commandParts;

if (!logFile || !command) {
  console.error(
    "Usage: bun scripts/run-with-log.mjs <log-file> [KEY=value ...] -- <command> [...args]"
  );
  process.exit(1);
}

const env = { ...process.env };
for (const pair of envPairs) {
  const splitAt = pair.indexOf("=");
  if (splitAt <= 0) continue;
  env[pair.slice(0, splitAt)] = pair.slice(splitAt + 1);
}

const log = createWriteStream(logFile, { flags: "a" });
const child = spawn(command, args, {
  env,
  shell: true,
  stdio: ["inherit", "pipe", "pipe"],
});

child.stdout.on("data", (chunk) => {
  process.stdout.write(chunk);
  log.write(chunk);
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
  log.write(chunk);
});

child.on("close", (code, signal) => {
  log.end();
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
