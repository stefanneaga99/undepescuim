import { NextResponse } from 'next/server';

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
  // Honeypot: bots fill the hidden "website" field — silently drop.
  if (honeypot) {
    return NextResponse.json({ ok: true, issueUrl: null });
  }

  const token = process.env.REPORT_GITHUB_TOKEN;
  if (!token) {
    return NextResponse.json({ ok: false, error: 'not_configured' }, { status: 503 });
  }

  const title = `[Raport] ${REASON_LABELS[reason]} — ${waterName}`;
  const bodyText = [
    `**Motiv:** ${REASON_LABELS[reason]} (\`${reason}\`)`,
    `**Apă:** ${waterName} — \`${waterSlug}\``,
    '',
    '**Detalii:**',
    details || '_(nespecificat)_',
    '',
    `**Contact:** ${contactEmail || '_(anonim)_'}`,
    '',
    `**Trimis automat:** ${new Date().toISOString()}`,
  ].join('\n');

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
    console.error('[report] create issue failed', res.status, await res.text());
    return NextResponse.json({ ok: false, error: 'github_error' }, { status: 502 });
  }

  const issue = (await res.json()) as { html_url: string };
  return NextResponse.json({ ok: true, issueUrl: issue.html_url });
}

// Only POST is meaningful here.
export async function GET() {
  return NextResponse.json({ ok: false, error: 'method_not_allowed' }, { status: 405 });
}
