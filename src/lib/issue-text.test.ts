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

  it('publishes only the enumerated reason and canonical water identity', () => {
    const { body } = buildIssueText({
      ...base,

    });
    expect(body).toContain('`other`');
    expect(body).toContain('Râul Bâsca — `raul-basca`');
    expect(body).not.toContain('secret@example.com');
    expect(body).not.toContain('45.1');
    expect(body).not.toContain('ghp_very-secret');
    expect(body).not.toContain('Detalii');
    expect(body).not.toContain('Context');
  });

  it('contains the reason key and public-field disclosure', () => {
    const { body } = buildIssueText(base);
    expect(body).toContain('`other`');
    expect(body).toContain('Date publicate');
  });
});