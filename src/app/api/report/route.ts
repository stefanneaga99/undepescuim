import { NextResponse } from 'next/server';
import { getClientIp, reportRateLimiter } from '@/lib/rate-limit';
import { buildIssueText } from '@/lib/issue-text';

const REPO = 'neagastefan99/undepescuim';

const REASON_LABELS: Record<string, string> = {
  data_correct: 'Datele sunt corecte (am pescuit aici)',
  water_invalid: 'Această apă nu mai există / nu se poate pescui',
  association_changed: 'Asociația s-a schimbat',
  wrong_coordinates: 'Coordonatele sunt greșite',
  other: 'Altă problemă',
};
const REASONS = new Set(Object.keys(REASON_LABELS));

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'invalid_json' }, { status: 400 });
  }

  const b = (body ?? {}) as Record<string, unknown>;
  const reason = typeof b.reason === 'string' ? b.reason : '';
  const waterSlug = typeof b.waterSlug === 'string' ? b.waterSlug.trim().slice(0, 128) : '';
  const waterName = typeof b.waterName === 'string' ? b.waterName.trim().slice(0, 256) : '';
  const details = typeof b.details === 'string' ? b.details.trim().slice(0, 2000) : '';
  const contactEmail = typeof b.contactEmail === 'string' ? b.contactEmail.trim().slice(0, 254) : '';
  const honeypot = typeof b.website === 'string' ? b.website.trim() : '';

  if (!REASONS.has(reason)) {
    return NextResponse.json({ ok: false, error: 'invalid_reason' }, { status: 400 });
  }
  if (!waterSlug || !waterName) {
    return NextResponse.json({ ok: false, error: 'missing_water' }, { status: 400 });
  }
  // Honeypot: bots fill the hidden "website" field — silently drop WITHOUT
  // consuming rate-limit quota (they never come back either way).
  if (honeypot) {
    return NextResponse.json({ ok: true, issueUrl: null });
  }

  // REM-1: in-memory per-IP sliding window (~5 req / 10 min). Runs before the
  // token check so the 429 path is reachable even when REPORT_GITHUB_TOKEN is
  // unset (e.g. local e2e). Serverless caveat: per-instance, not global — see
  // src/lib/rate-limit.ts.
  const clientIp = getClientIp(request);
  const limit = reportRateLimiter.check(clientIp);
  if (!limit.allowed) {
    const retryAfter = String(limit.retryAfterSec ?? 600);
    return NextResponse.json(
      { ok: false, error: 'rate_limited' },
      { status: 429, headers: { 'Retry-After': retryAfter } },
    );
  }

  const token = process.env.REPORT_GITHUB_TOKEN;
  if (!token) {
    return NextResponse.json({ ok: false, error: 'not_configured' }, { status: 503 });
  }

  // REM-3/REM-4: build the issue text through the sanitizer (markdown-
  // neutralized title/body, fenced details, control-char-stripped email).
  const { title, body: bodyText } = buildIssueText({
    reasonLabel: REASON_LABELS[reason],
    reasonKey: reason,
    waterName,
    waterSlug,
    details,
    contactEmail,
  });

  const res = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, body: bodyText, labels: ['report'] }),
  });

  if (!res.ok) {
    // Log status only; the response body never contains the token, and logging
    // the request/response headers could — keep error logging body-free.
    console.error('[report] create issue failed', res.status);
    return NextResponse.json({ ok: false, error: 'github_error' }, { status: 502 });
  }

  const issue = (await res.json()) as { html_url: string };
  return NextResponse.json({ ok: true, issueUrl: issue.html_url });
}

// Only POST is meaningful here.
export async function GET() {
  return NextResponse.json({ ok: false, error: 'method_not_allowed' }, { status: 405 });
}