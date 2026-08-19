/**
 * Builds the GitHub issue title/body for the report endpoint from
 * user-supplied fields. Pure function — no I/O — so the sanitization contract
 * (REM-3/REM-4) is unit-testable in isolation.
 *
 * Rules:
 *  - title: water name is allowlist-sanitized (no markdown-active characters).
 *  - body: `details` is preserved verbatim inside a fenced code block;
 *          `contactEmail` is stripped of control characters and rendered as
 *          inline code (never raw), so an address can't become an @mention.
 */
import { sanitizeWaterName, sanitizeSlug, fenceDetails, stripControl } from './sanitize';
import type { ReportContextV1 } from '@/types/report-context';

export interface IssueTextInput {
  reasonLabel: string;
  reasonKey: string;
  waterName: string;
  waterSlug: string;
  details: string;
  contactEmail: string;
  reportContext?: ReportContextV1 | null;
}

export interface IssueText {
  title: string;
  body: string;
}

export function buildIssueText({
  reasonLabel,
  reasonKey,
  waterName,
  waterSlug,
  details,
  contactEmail,
  reportContext = null,
}: IssueTextInput): IssueText {
  const safeWaterName = sanitizeWaterName(waterName);
  const safeSlug = sanitizeSlug(waterSlug);

  const title = `[Raport] ${reasonLabel} — ${safeWaterName}`;

  // Only a plausible email address is rendered; anything else (newline
  // smuggling, "not really an email") is treated as anonymous.
  const strippedEmail = stripControl(contactEmail).slice(0, 254);
  const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(strippedEmail) ? strippedEmail : '';
  const contactLine = email
    ? `**Contact (vizibil public, cu acord):** \`${email}\``
    : '**Contact:** _(anonim)_';

  const contextLines = reportContext ? [
    '## Context hartă (schema v1, redactat)',
    `- Apă selectată: \`${sanitizeSlug(reportContext.subject.water.slug)}\` — ${sanitizeWaterName(reportContext.subject.water.name)}`,
    `- Vizualizare aproximativă: ${reportContext.map?.center ? `centru ${reportContext.map.center.lat}, ${reportContext.map.center.lon}; zoom ${reportContext.map.zoom ?? '—'}` : 'nepartajată'}`,
    `- Filtre: județe \`${reportContext.filters.counties.join(', ')}\`; localități \`${reportContext.filters.localities.join(', ')}\`; tip \`${reportContext.filters.waterType}\`; contract \`${reportContext.filters.contractStatus}\``,
    `- Pagină / dispozitiv: \`${reportContext.page.pathname}\`; \`${reportContext.client.formFactor}\``,
    `- Poziție dispozitiv: ${reportContext.preciseLocation ? `${reportContext.preciseLocation.lat}, ${reportContext.preciseLocation.lon}` : 'nepartajată'}`,
    `- Captură hartă: ${reportContext.consent.screenshot ? 'nepartajată (nu este încărcată automat)' : 'nepartajată'}`,
  ] : ['## Context hartă', '_(nepartajat sau indisponibil la trimitere)_'];
  const body = [
    `**Motiv:** ${reasonLabel} (\`${reasonKey}\`)`,
    `**Apă:** ${safeWaterName} — \`${safeSlug}\``,
    '',
    '**Detalii:**',
    fenceDetails(details),
    '',
    contactLine,
    '',
    ...contextLines,
    '',
    `**Trimis automat:** ${new Date().toISOString()}`,
  ].join('\n');

  return { title, body };
}