#!/usr/bin/env node
/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §6): build-time data freshness.
 * Runs via the `prebuild` hook — writes public/data/meta.json so the UI can
 * show "Date actualizate: <date>" and the offline banner can say "data as of".
 *
 * dataUpdatedAt = the git commit date of the last change touching public/data
 * (the single source of truth across manual fix_*.py edits AND the
 * refresh-data.mjs workflow). Falls back to "now" when git is unavailable
 * (CI tarball checkout, no .git).
 */
import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "public", "data", "meta.json");

const dataUpdatedAt = (() => {
  try {
    return execSync("git log -1 --format=%cI -- public/data", {
      encoding: "utf8",
      cwd: root,
    }).trim();
  } catch {
    return new Date().toISOString();
  }
})();

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify({ generatedAt: new Date().toISOString(), dataUpdatedAt }, null, 2) + "\n");
console.log(`[gen-meta] wrote ${out} (data updated ${dataUpdatedAt})`);
