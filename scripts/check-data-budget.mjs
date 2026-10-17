#!/usr/bin/env node
/**
 * Data payload budget gate — M7/M8/M9 of docs/performance-test-plan.md §4.
 *
 *   M7  Total data JSON transferred (gzip)        < 2.5 MB
 *   M8  waters.json gzip size (compact)           < 1.65 MB (owner override 2026-10-17)
 *   M9  JSON text parsed on main thread (compact) < 7 MB (owner override 2026-10-17, river geometry v2)
 *   +   Allowlist: public/data may contain ONLY the files listed in
 *       scripts/lib/data-budget.mjs (anything else is shipped to every
 *       visitor but never fetched — e.g. backups, geocoder intermediates).
 *   +   INFO: gzip size of the lazily-loaded files (reported, not blocking).
 *
 * Measured on the same 5 files the app fetches in loadData() (map-store.ts):
 * associations.json, waters.json, uncontracted_rivers.json,
 * uncontracted_lakes.json, counties.geojson.
 *
 * EXPECTED-FAIL today (2026-08-16): total ~6.0 MB gzip / waters.json
 * 4.75 MB gzip / 22.6 MB parsed — the data optimization task flips these
 * green (see docs/performance-optimization-plan.md). CI wires this script
 * with `continue-on-error: true` until then (perf.yml).
 *
 * Exit code 0 = all budgets PASS, 1 = any FAIL.
 */
import { readFileSync, existsSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { LAZY_DATA_FILES, LAZY_GZIP_CAPS, findUnexpectedFiles, lazyCapViolation } from './lib/data-budget.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = join(root, 'public', 'data');

// First-load = the files loadData() AWAITS before first paint (map-store.ts):
// associations + waters + counties + the P1 §4.5 "majors" subset of the
// uncontracted overlay (rivers ≥30km + lakes ≥100ha). The FULL uncontracted
// rivers/lakes (streamed in the background after dataLoaded) and the county
// clips (waters_county_clips.json, lazy on first county activation) are NOT
// part of the critical path.
const FETCHED = [
  'associations.json',
  'waters.json',
  'counties.geojson',
  'uncontracted_majors.json',
];
const MB = 1024 * 1024;
const LIMITS = {
  M7: 2.5 * MB,
  // Raised from 1.5 MB by explicit owner decision (2026-10-17), same reason as M9.
  M8: 1.65 * MB,
  // Raised from 6 MB by explicit owner decision (2026-10-17): pre-cut river
  // sectors keep the 5 m simplification (cutover 6.40 MB; with the D8 partial
  // switch 6.58 MB), with headroom for the next big-river batches.
  M9: 7 * MB,
};

/** Minified serialization — the bytes JSON.parse actually walks. */
function compactBytes(parsed) {
  return Buffer.byteLength(JSON.stringify(parsed, null, 0));
}

let failures = 0;
const check = (ok, label, detail) => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${label}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

console.log('Data payload budgets (docs/performance-test-plan.md M7/M8/M9)\n');

const rows = [];
let totalGzip = 0;
let totalCompact = 0;
for (const file of FETCHED) {
  const path = join(dataDir, file);
  if (!existsSync(path)) {
    check(false, `${file}`, 'MISSING — app loadData() expects it in public/data/');
    continue;
  }
  const raw = readFileSync(path);
  const parsed = JSON.parse(raw.toString('utf8'));
  const compact = compactBytes(parsed);
  const gzip = gzipSync(Buffer.from(JSON.stringify(parsed, null, 0)), { level: 9 }).length;
  totalGzip += gzip;
  totalCompact += compact;
  rows.push({ file, raw: raw.length, compact, gzip });
}

for (const r of rows) {
  console.log(
    `  ${r.file.padEnd(26)} raw=${(r.raw / MB).toFixed(2).padStart(7)} MB  ` +
      `compact=${(r.compact / MB).toFixed(2).padStart(7)} MB  gzip-9=${(r.gzip / MB).toFixed(2).padStart(7)} MB`,
  );
}

console.log('\nBudgets:');
check(
  totalGzip < LIMITS.M7,
  `M7 total gzip < ${(LIMITS.M7 / MB).toFixed(1)} MB`,
  `${(totalGzip / MB).toFixed(2)} MB`,
);
check(
  rows.find((r) => r.file === 'waters.json')?.gzip < LIMITS.M8,
  `M8 waters.json gzip < ${(LIMITS.M8 / MB).toFixed(2)} MB`,
  `${((rows.find((r) => r.file === 'waters.json')?.gzip ?? 0) / MB).toFixed(2)} MB`,
);
check(
  totalCompact < LIMITS.M9,
  `M9 main-thread parse (compact) < ${(LIMITS.M9 / MB).toFixed(1)} MB`,
  `${(totalCompact / MB).toFixed(2)} MB`,
);

console.log('\nAllowlist (public/data/ may only contain files listed in scripts/lib/data-budget.mjs):');
const unexpected = findUnexpectedFiles(dataDir);
check(
  unexpected.length === 0,
  'no unexpected files in public/data/',
  unexpected.length === 0
    ? 'ok'
    : `UNEXPECTED: ${unexpected.join(', ')} — shipped to every visitor; remove them or add them to the allowlist deliberately`,
);

console.log('\nLazy files (INFO — not part of M7-M9):');
for (const file of LAZY_DATA_FILES) {
  const path = join(dataDir, file);
  if (!existsSync(path)) {
    console.log(`  INFO  ${file.padEnd(32)} not present`);
    continue;
  }
  const raw = readFileSync(path);
  const gzip = gzipSync(raw, { level: 9 }).length;
  console.log(
    `  INFO  ${file.padEnd(32)} raw=${(raw.length / MB).toFixed(2).padStart(6)} MB  gzip-9=${(gzip / MB).toFixed(2).padStart(6)} MB`,
  );
  if (file in LAZY_GZIP_CAPS) {
    const violation = lazyCapViolation(file, gzip);
    check(violation === null, `${file} gzip < ${(LAZY_GZIP_CAPS[file] / 1024).toFixed(0)} KB (blocking)`, violation ?? 'ok');
  }
}

console.log(failures === 0 ? '\nDATA BUDGET PASSED' : `\nDATA BUDGET FAILED (${failures} failing)`);
process.exit(failures === 0 ? 0 : 1);
