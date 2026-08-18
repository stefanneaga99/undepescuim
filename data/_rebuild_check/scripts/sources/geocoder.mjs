/**
 * Source: geocoder — Tiers 2-3 geocoding pipeline (Python).
 *
 * Runs the three geocoding stages against the freshly-refreshed
 * public/data/waters.json and the committed private-lakes snapshot:
 *   1. scripts/geocode_private.py  (201 private lakes via Overpass, s8)
 *   2. scripts/geocode_batch.py    (public waters via Nominatim batch, s4-5)
 *   3. scripts/merge_geocoded.py   (premapped + batch + private -> one GeoJSON)
 *
 * Outputs:
 *   waters_geocoded.geojson — FeatureCollection per proposal s7.1 (the merge
 *   script also writes data/waters_geocoded.geojson as the canonical artifact).
 *
 * Failure policy: any stage failure throws, the orchestrator logs it and keeps
 * the last good data on disk (per refresh-data.mjs contract). Cache in
 * data/cache/geocode.db is cache-first, so repeat runs hit the SQLite cache
 * instead of re-querying Nominatim/Overpass.
 */
import { execFile } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const SCRIPTS = ['geocode_private.py', 'geocode_batch.py', 'merge_geocoded.py'];

function run(cmd, args, cwd, timeoutMs) {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { cwd, timeout: timeoutMs }, (err, stdout, stderr) => {
      if (err) {
        reject(new Error(`${cmd} ${args.join(' ')} failed: ${err.message}\n${stderr}`));
      } else {
        resolve(stdout);
      }
    });
  });
}

export const name = 'geocoder';

export async function collect() {
  // Generous per-stage headroom: Nominatim 1 req/s for ~400 waters with
  // multi-query fallback chains plus Overpass tier-3 fallbacks can take
  // 30-60+ minutes on a cold cache. A warm cache (data/cache/geocode.db)
  // makes repeat runs fast again.
  const stageTimeout = 2 * 60 * 60 * 1000;
  for (const script of SCRIPTS) {
    const out = await run('python3', [path.join('scripts', script)], ROOT, stageTimeout);
    // echo the script's own progress lines into the refresh log
    for (const line of out.split('\n').filter((l) => l.trim())) {
      console.log(`[geocoder] ${line}`);
    }
  }
  const merged = JSON.parse(await readFile(path.join(ROOT, 'data', 'waters_geocoded.geojson'), 'utf-8'));
  return { 'waters_geocoded.geojson': merged };
}
