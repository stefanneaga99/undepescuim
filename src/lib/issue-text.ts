/**
 * Builds the GitHub issue title/body for the report endpoint from
 * user-supplied fields. Pure function — no I/O — so the sanitization contract
 * (REM-3/REM-4) is unit-testable in isolation.
 *
 * Rules:
 *  - title: water name is allowlist-sanitized (no markdown-active characters).
 *  - body: contains only the enumerated reason and canonical water identity.
 */
import { sanitizeWaterName, sanitizeSlug } from './sanitize';

export interface IssueTextInput {
  reasonLabel: string;
  reasonKey: string;
  waterName: string;
  waterSlug: string;
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
}: IssueTextInput): IssueText {
  const safeWaterName = sanitizeWaterName(waterName);
  const safeSlug = sanitizeSlug(waterSlug);

  const title = `[Raport] ${reasonLabel} — ${safeWaterName}`;

  const body = [
    `**Motiv:** ${reasonLabel} (\`${reasonKey}\`)`,
    `**Apă:** ${safeWaterName} — \`${safeSlug}\``,
    '',
    '**Date publicate:** doar motivul enumerat și identificatorul canonic al apei.',
  ].join('\n');

  return { title, body };
}