import { createHash } from 'node:crypto';
import { NextResponse } from 'next/server';
import { getClientIp, reportRateLimiter } from '@/lib/rate-limit';
import { buildIssueText } from '@/lib/issue-text';
import { reportDeduper } from '@/lib/report-dedupe';
import { parseReportContext } from '@/lib/report-context';

const REPO = 'neagastefan99/undepescuim';

const REASON_LABELS: Record<string, string> = {
  data_correct: 'Datele sunt corecte (am pescuit aici)',
  water_invalid: 'Această apă nu mai există / nu se poate pescui',
  association_changed: 'Asociația s-a schimbat',
  wrong_coordinates: 'Coordonatele sunt greșite',
  other: 'Altă problemă',
};
const REASONS = new Set(Object.keys(REASON_LABELS));

function reportDigest(fields: [string, string, string, string, string]): string {
  return createHash('sha256').update(JSON.stringify(fields), 'utf8').digest('hex');
}

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
  const parsedContext = parseReportContext(b.reportContext);
  // The public context must describe the same water as the canonical report
  // fields; stale A→B payloads degrade to a base report, never a mixed issue.
  const reportContext = parsedContext &&
    parsedContext.subject.water.slug === waterSlug &&
    parsedContext.subject.water.name === waterName
    ? parsedContext : null;

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

  const digest = reportDigest([reason, waterSlug, waterName, details, contactEmail]);

  // Validated human request → dedupe/coalesce → first request uses the rate
  // limit → GitHub issue creation. Duplicate joins do not consume quota.
  let result: { issueUrl: string | null };
  try {
    result = await reportDeduper.run(digest, async () => {
    // REM-1: in-memory per-IP sliding window (~5 req / 10 min). Runs before
    // the token check so the 429 path is reachable without a token.
    const clientIp = getClientIp(request);
    const limit = reportRateLimiter.check(clientIp);
    if (!limit.allowed) {
      const retryAfter = String(limit.retryAfterSec ?? 600);
      throw new ReportHttpError('rate_limited', 429, { 'Retry-After': retryAfter });
    }

    const token = process.env.REPORT_GITHUB_TOKEN;
    if (!token) throw new ReportHttpError('not_configured', 503);

    const { title, body: bodyText } = buildIssueText({
      reasonLabel: REASON_LABELS[reason], reasonKey: reason, waterName,
      waterSlug, details, contactEmail, reportContext,
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
      console.error('[report] create issue failed', res.status);
      throw new ReportHttpError('github_error', 502);
    }
    const issue = (await res.json()) as { html_url: string };
    return { issueUrl: issue.html_url };
    });
  } catch (error) {
    if (error instanceof ReportHttpError) {
      return NextResponse.json({ ok: false, error: error.code }, { status: error.status, headers: error.headers });
    }
    throw error;
  }

  return NextResponse.json({ ok: true, issueUrl: result.issueUrl });
}

class ReportHttpError extends Error {
  constructor(readonly code: string, readonly status: number, readonly headers: Record<string, string> = {}) {
    super(code);
  }
}

// Only POST is meaningful here.
export async function GET() {
  return NextResponse.json({ ok: false, error: 'method_not_allowed' }, { status: 405 });
}