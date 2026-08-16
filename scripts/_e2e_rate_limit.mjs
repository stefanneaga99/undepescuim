/**
 * REM-1 e2e: rate limiting on POST /api/report (docs/security-test-plan.md).
 *
 * Sends 7 rapid valid POSTs from a FRESH per-run IP (TEST-NET-3 203.0.113.x
 * via x-forwarded-for — never routed on the internet) and asserts:
 *   - requests 1-5 pass the limiter (locally: 503 not_configured since there
 *     is no REPORT_GITHUB_TOKEN; in prod: 200),
 *   - requests 6-7 are blocked with 429 { error: 'rate_limited' } + Retry-After,
 *   - the honeypot still returns its silent fake-200 on an exhausted IP
 *     (it is checked before the limiter so bots never learn they're blocked
 *     and never consume quota).
 *
 * Run against a running server (fresh `next start` — the limiter is in-memory):
 *   node scripts/_e2e_rate_limit.mjs http://localhost:3100
 */
import { randomBytes } from 'node:crypto';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3100';
const IP = `203.0.113.${(randomBytes(1)[0] % 200) + 10}`; // 203.0.113.10..209 (TEST-NET-3)

const post = async (body) => {
  const res = await fetch(`${BASE}/api/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-forwarded-for': IP },
    body: JSON.stringify(body),
  });
  let json = null;
  try { json = await res.json(); } catch { /* keep null */ }
  return { status: res.status, retryAfter: res.headers.get('retry-after'), json };
};

const valid = { reason: 'other', waterSlug: 'raul-basca', waterName: 'Râul Bâsca' };

let failures = 0;
const check = (cond, label) => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}`);
  if (!cond) failures += 1;
};

console.log(`rate-limit e2e on ${BASE} (as IP ${IP})`);

const results = [];
for (let i = 0; i < 7; i++) results.push(await post(valid));

const allowed = results.slice(0, 5);
const blocked = results.slice(5);

check(
  allowed.every((r) => r.status !== 429),
  `requests 1-5 pass the limiter (got ${allowed.map((r) => r.status).join(',')} — 503 w/o token, 200 with token)`,
);
check(
  allowed.filter((r) => r.status === 200).length === 0 || allowed.every((r) => r.status === 200),
  'no mixed success responses',
);
check(
  blocked.every((r) => r.status === 429 && r.json?.error === 'rate_limited'),
  `requests 6-7 blocked with 429 rate_limited (got ${blocked.map((r) => r.status).join(',')})`,
);
check(blocked.every((r) => !!r.retryAfter), '429 responses carry Retry-After');
check(!JSON.stringify(blocked.map((r) => r.json)).includes('stack'), '429 body is generic (no stack trace)');

const hp = await post({ ...valid, website: 'http://spam.example' });
check(
  hp.status === 200 && hp.json?.ok === true && hp.json?.issueUrl === null,
  'honeypot still returns silent fake-200 on an exhausted IP',
);

console.log(failures === 0 ? 'RATE-LIMIT E2E PASSED' : `RATE-LIMIT E2E FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);