/**
 * REM-3: neutralize user-supplied text before it lands in a public GitHub
 * issue. GitHub renders markdown in issue bodies, so raw user text can inject
 * @mentions, #refs, images (tracking pixels), task lists and blockquotes.
 * We neutralize rather than discard (docs/security-test-plan.md §8): the
 * reporter's details are preserved verbatim inside a fenced code block, and
 * free-text rendered outside a fence is prefix-escaped.
 */

export const MAX_WATER_NAME = 128;
export const MAX_DETAILS = 2000;

/**
 * Title-safe water name: strips every character outside Unicode letters
 * (including Romanian diacritics), digits, space, '.' and '-'. Markdown-active
 * characters (# @ ! [ ] etc.) never reach the issue title. The allowlist is
 * intentionally Unicode-aware so "Bâsca Mare" survives as-is.
 */
const WATER_NAME_ALLOWED = /[^\p{L}\p{N} .\-]/gu;

export function sanitizeWaterName(raw: string): string {
  return raw
    .trim()
    .replace(WATER_NAME_ALLOWED, '')
    .replace(/\s+/g, ' ')
    .slice(0, MAX_WATER_NAME);
}

/**
 * Slug-safe identifier: letters, digits, '.', '_', '-'. Slugs come from
 * trusted static data, but the API is public — never trust the wire format.
 */
export function sanitizeSlug(raw: string): string {
  return raw.trim().replace(/[^\p{L}\p{N}._-]/gu, '').slice(0, 128);
}

/** Longest run of backticks in a string (0 when none). */
function maxBacktickRun(s: string): number {
  let max = 0;
  let cur = 0;
  for (const ch of s) {
    if (ch === '`') {
      cur += 1;
      if (cur > max) max = cur;
    } else {
      cur = 0;
    }
  }
  return max;
}

/**
 * Wrap user details in a fenced code block. The fence is one backtick longer
 * than the longest run in the text, so a user-supplied ``` can never break
 * out of the fence to re-enable markdown. Returns a placeholder for empty
 * input so the section header still reads cleanly.
 */
export function fenceDetails(raw: string): string {
  const text = raw.trim().slice(0, MAX_DETAILS);
  if (!text) return '_(nespecificat)_';
  const fence = '`'.repeat(Math.max(3, maxBacktickRun(text) + 1));
  return `${fence}\n${text}\n${fence}`;
}

/**
 * Prefix-escape markdown-active characters on every line of free text that is
 * rendered OUTSIDE a fenced block: leading '#', '@', '![' and blockquote '>'.
 */
export function neutralizeInline(raw: string): string {
  return raw
    .split('\n')
    .map((line) => {
      let l = line;
      // leading ATX heading markers: "## x" -> "\#\# x"
      l = l.replace(/^(\s*)(#{1,6})(?=\s|$)/, (m, ws, hashes) => ws + hashes.replace(/#/g, '\\#'));
      // leading @mention: "@user" -> "\@user"
      l = l.replace(/^(\s*)@(?=\S)/, (m, ws) => `${ws}\\@`);
      // leading image: "![alt](url)" -> "!\[alt](url)"
      l = l.replace(/^(\s*)!\[/, (m, ws) => `${ws}!\\[`);
      // leading blockquote: "> quote" -> "\> quote"; ">> nested" -> "\>\> nested"
      l = l.replace(/^(\s*)(>+)(\s|$)/, (m, ws, gts, rest) => ws + gts.replace(/>/g, '\\>') + rest);
      return l;
    })
    .join('\n');
}

/** Strip control characters that could corrupt the issue body (newlines in
 *  an email address let a reporter smuggle @mentions / headings through). */
export function stripControl(raw: string): string {
  return raw.replace(/[\u0000-\u001f\u007f]/g, '').trim();
}