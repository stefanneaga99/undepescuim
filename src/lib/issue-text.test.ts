import { describe, it, expect } from 'vitest';
import { buildIssueText } from './issue-text';

const base = {
  reasonLabel: 'Altă problemă',
  reasonKey: 'other',
  waterName: 'Râul Bâsca',
  waterSlug: 'raul-basca',
  details: '',
  contactEmail: '',
};

describe('buildIssueText', () => {
  it('builds a clean title with the reason label and sanitized water name', () => {
    const { title } = buildIssueText(base);
    expect(title).toBe('[Raport] Altă problemă — Râul Bâsca');
  });

  it('strips markdown-active characters from the title', () => {
    const { title } = buildIssueText({
      ...base,
      waterName: '@ghost #123 ![x](https://evil/px.png) Bâsca',
    });
    // The fixed "[Raport]" prefix legitimately contains brackets; the
    // water-name segment after "— " must be free of markdown-active chars.
    const namePart = title.split('— ')[1] ?? title;
    expect(namePart).not.toMatch(/[@#<>[\]]/);
    expect(namePart).toContain('Bâsca');
    expect(namePart).not.toContain('@'); // mention sigil stripped
    expect(namePart).not.toContain('#'); // ref sigil stripped
  });

  it('wraps details in a fenced block so raw markdown cannot inject', () => {
    const details = '@someuser #123 ![x](https://attacker.example/px.png) [ ] task';
    const { body } = buildIssueText({ ...base, details });
    // the raw text is preserved inside the fence...
    expect(body).toContain(details);
    expect(body).toContain('```\n' + details + '\n```');
    // ...and nothing raw sits outside the fence
    const afterFence = body.split('```')[2] ?? '';
    expect(afterFence).not.toContain('@someuser');
  });

  it('never leaks the email as raw text / @mention vector', () => {
    const { body } = buildIssueText({ ...base, contactEmail: 'user@example.com' });
    // inline-code-wrapped, not raw
    expect(body).toContain('`user@example.com`');
    expect(body).not.toContain('\nuser@example.com\n');
  });

  it('neutralizes newline smuggling in the email field', () => {
    // "user@example.com\n@maintainer" -> control chars stripped -> two @s ->
    // fails the email sanity regex -> treated as anonymous, no mention anywhere.
    const { body } = buildIssueText({
      ...base,
      contactEmail: 'user@example.com\n@maintainer',
    });
    expect(body).not.toContain('@maintainer');
    expect(body).toContain('_(anonim)_');
  });

  it('marks anonymous contact explicitly', () => {
    const { body } = buildIssueText(base);
    expect(body).toContain('_(anonim)_');
  });

  it('contains the reason key and timestamp footer', () => {
    const { body } = buildIssueText(base);
    expect(body).toContain('`other`');
    expect(body).toContain('Trimis automat');
  });
});