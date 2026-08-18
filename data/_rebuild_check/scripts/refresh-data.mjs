#!/usr/bin/env node
/**
 * UndePescuim.ro — monthly data refresh orchestrator.
 *
 * Pipeline:
 *   1. Load every source module in scripts/sources/*.mjs
 *   2. Each source fetches fresh data and returns a map of
 *      { "relative/path/under/public/data.json": <JSON-serializable value> }
 *   3. Validate outputs (non-empty, JSON-serializable, GeoJSON-valid when .geojson)
 *   4. Write outputs to public/data/
 *   5. Print summary: files written, record counts, failures
 *
 * Failure policy: a source that throws is logged and skipped (last good data
 * on disk is kept). If EVERY source fails, exit non-zero so the GitHub Actions
 * run surfaces as failed and triggers a notification.
 *
 * Usage: node scripts/refresh-data.mjs
 */
import { mkdir, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SOURCES_DIR = path.join(__dirname, 'sources');
const DATA_DIR = path.join(ROOT, 'public', 'data');

const encoder = new TextEncoder();

/** Validate a single output value. Throws on invalid data. */
function validateOutput(relPath, value) {
  if (value === null || value === undefined) {
    throw new Error(`${relPath}: output is null/undefined`);
  }
  if (typeof value === 'object') {
    const isEmptyArray = Array.isArray(value) && value.length === 0;
    const isEmptyObject = !Array.isArray(value) && Object.keys(value).length === 0;
    if (isEmptyArray || isEmptyObject) {
      throw new Error(`${relPath}: output is empty — refusing to overwrite good data`);
    }
  }
  // Round-trip check: must be JSON-serializable (rejects NaN, Infinity, BigInt, cycles).
  JSON.stringify(value);
  if (relPath.endsWith('.geojson')) {
    const geojson = value;
    if (geojson.type !== 'FeatureCollection' && geojson.type !== 'Feature') {
      throw new Error(`${relPath}: not a GeoJSON FeatureCollection/Feature`);
    }
  }
}

/** Pretty-print with a trailing newline. */
function serialize(value) {
  return JSON.stringify(value, null, 2) + '\n';
}

async function loadSources() {
  const files = (await readdir(SOURCES_DIR)).filter((f) => f.endsWith('.mjs'));
  const sources = [];
  for (const file of files) {
    const mod = await import(path.join(SOURCES_DIR, file));
    if (typeof mod.collect === 'function' && typeof mod.name === 'string') {
      sources.push({ name: mod.name, collect: mod.collect });
    } else {
      console.warn(`[refresh] skipping ${file}: missing "name" or "collect" export`);
    }
  }
  return sources;
}

async function main() {
  const sources = await loadSources();
  if (sources.length === 0) {
    console.warn('[refresh] no source modules found in scripts/sources/ — nothing to do');
    process.exit(0);
  }

  const summary = { startedAt: new Date().toISOString(), sources: [] };
  let wroteAny = false;
  let failedAny = false;

  for (const source of sources) {
    const entry = { name: source.name, files: [], error: null };
    try {
      const outputs = await source.collect();
      if (!outputs || typeof outputs !== 'object') {
        throw new Error('collect() must return an object map of relPath -> value');
      }
      for (const [relPath, value] of Object.entries(outputs)) {
        if (!relPath.endsWith('.json') && !relPath.endsWith('.geojson')) {
          console.warn(`[refresh] ${source.name}: skipping non-JSON output "${relPath}"`);
          continue;
        }
        validateOutput(relPath, value);
        const target = path.join(DATA_DIR, relPath);
        await mkdir(path.dirname(target), { recursive: true });
        await writeFile(target, encoder.encode(serialize(value)));
        const count = Array.isArray(value) ? value.length
          : (value.items ? value.items.length : (value.features ? value.features.length : Object.keys(value).length));
        entry.files.push({ path: relPath, records: count });
        wroteAny = true;
        console.log(`[refresh] ${source.name}: wrote ${relPath} (${count} records)`);
      }
    } catch (err) {
      entry.error = err.message;
      failedAny = true;
      console.error(`[refresh] ${source.name}: FAILED — ${err.message} (keeping last good data)`);
    }
    summary.sources.push(entry);
  }

  summary.finishedAt = new Date().toISOString();
  console.log(`\n[refresh] summary: ${summary.sources.filter((s) => !s.error).length}/${sources.length} sources OK, wrote=${wroteAny}, failed=${failedAny}`);

  if (failedAny && !wroteAny) {
    console.error('[refresh] all sources failed — exiting 1 so the workflow surfaces the failure');
    process.exit(1);
  }
  process.exit(0);
}

main().catch((err) => {
  console.error(`[refresh] fatal: ${err.stack || err.message}`);
  process.exit(1);
});
