import { describe, expect, it } from 'vitest';
import { safeEmail, safeExternalUrl, safeTelephone } from './safe-url';

describe('safe external link helpers', () => {
  it('accepts only https URLs and rejects malformed or unsafe values', () => {
    expect(safeExternalUrl(' https://example.com/path ')).toBe('https://example.com/path');
    expect(safeExternalUrl('http://example.com')).toBeNull();
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull();
    expect(safeExternalUrl('not a url')).toBeNull();
    expect(safeExternalUrl('')).toBeNull();
    expect(safeExternalUrl(null)).toBeNull();
  });

  it('normalizes valid phone numbers and rejects invalid values', () => {
    expect(safeTelephone('+40 721 234 567')).toBe('tel:+40721234567');
    expect(safeTelephone('0238-500-948')).toBe('tel:0238-500-948');
    expect(safeTelephone('123')).toBeNull();
    expect(safeTelephone(40721234567)).toBeNull();
  });

  it('accepts valid email addresses only', () => {
    expect(safeEmail('contact@example.com')).toBe('mailto:contact@example.com');
    expect(safeEmail('not-an-email')).toBeNull();
    expect(safeEmail('a@b')).toBeNull();
    expect(safeEmail(null)).toBeNull();
  });
});
