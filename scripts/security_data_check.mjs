// REM-5 / SEC-08: data-integrity scheme check (docs/security-test-plan.md).
//
// Walks every JSON file in public/data/ and fails if:
//  1. any string uses a dangerous URL scheme (javascript:, data:, vbscript:),
//  2. any *Url / siteUrl field is not http(s),
//  3. any telefon field is not "numeric-ish" (digits, spaces, (), -, +).
//
// Guard against a poisoned data-refresh/scrape slipping a javascript: href
// into the map's <a href={siteUrl}> renders.
//
// Run: node scripts/security_data_check.mjs  (exit 0 = PASS)

import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const DIR = fileURLToPath(new URL('../public/data/', import.meta.url));
const DANGEROUS_SCHEME = /^(javascript|data|vbscript):/i;
const HTTP_ONLY = /^https?:\/\//i;
const PHONE_OK = /^\+?[\d\s()./-]{6,}$/; // allows legacy "0238/710608" format

const bad = [];
const files = readdirSync(DIR).filter((f) => f.endsWith('.json'));
for (const file of files) {
  let json;
  try {
    json = JSON.parse(readFileSync(join(DIR, file), 'utf8'));
  } catch (err) {
    bad.push(`${file} :: unparseable JSON (${err.message})`);
    continue;
  }

  const walk = (o, path) => {
    if (o == null) return;
    if (typeof o === 'string') {
      const trimmed = o.trim();
      if (DANGEROUS_SCHEME.test(trimmed)) {
        bad.push(`${file} :: ${path} = ${o.slice(0, 100)} (dangerous URL scheme)`);
      }
      if ((path.endsWith('Url') || path.endsWith('siteUrl')) && trimmed && !HTTP_ONLY.test(trimmed)) {
        bad.push(`${file} :: ${path} = ${o.slice(0, 100)} (not http(s))`);
      }
      if (path.endsWith('telefon') && trimmed && !PHONE_OK.test(trimmed)) {
        bad.push(`${file} :: ${path} = ${o.slice(0, 100)} (not numeric-ish)`);
      }
    } else if (Array.isArray(o)) {
      o.forEach((v, i) => walk(v, `${path}[${i}]`));
    } else if (typeof o === 'object') {
      Object.entries(o).forEach(([k, v]) => walk(v, `${path}.${k}`));
    }
  };
  walk(json, '$');
}

if (bad.length) {
  console.error(`FAIL: data-integrity check — ${bad.length} issue(s):`);
  for (const line of bad) console.error('  ' + line);
  process.exit(1);
}
console.log(`PASS: data-integrity check — ${files.length} files, no dangerous URL schemes / junk values`);