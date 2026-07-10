import { execFileSync } from "node:child_process";
import { cp, mkdir, rm } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const env = {
  ...process.env,
  SITES_BUILD: "true",
  NEXT_PUBLIC_USE_MOCK: "true",
};

execFileSync(npm, ["--prefix", "frontend", "run", "build:clean"], {
  cwd: root,
  env,
  shell: process.platform === "win32",
  stdio: "inherit",
});

const dist = resolve(root, "dist");
await rm(dist, { recursive: true, force: true });
await mkdir(resolve(dist, "server"), { recursive: true });
await mkdir(resolve(dist, "client"), { recursive: true });
await cp(resolve(root, "frontend", "out"), resolve(dist, "client"), {
  recursive: true,
});
await cp(
  resolve(root, "scripts", "site-worker.mjs"),
  resolve(dist, "server", "index.js"),
);

const python = process.platform === "win32" ? "python.exe" : "python3";
execFileSync(python, ["scripts/optimize-site-assets.py", resolve(dist, "client")], {
  cwd: root,
  stdio: "inherit",
});

console.log(`[site-build] prepared ${dist}`);
