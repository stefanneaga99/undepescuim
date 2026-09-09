import { describe, expect, it } from 'vitest';
import { LEGAL_NAV_ITEMS, LEGAL_PLACEHOLDERS, legalSections } from './legal';

describe('legal information surface', () => {
  it('defines every legal route used by navigation', () => {
    expect(LEGAL_NAV_ITEMS.map((item) => item.href)).toEqual([
      '/confidentialitate',
      '/termeni',
      '/contact',
      '/licente',
    ]);
  });

  it('keeps operator facts as visible placeholders until verified', () => {
    for (const placeholder of Object.values(LEGAL_PLACEHOLDERS)) {
      expect(placeholder).toMatch(/^\[[A-Z ]+\]$/);
      expect(Object.values(legalSections).join(' ')).toContain(placeholder);
    }
  });

  it('covers the required Romanian-first disclosure topics', () => {
    const text = Object.values(legalSections).join(' ').toLowerCase();
    for (const topic of [
      'operator',
      'scop',
      'temei',
      'destinat',
      'transfer',
      'păstr',
      'drept',
      'anspdcp',
      'geoloca',
      'offline',
      'raport',
      'odbl',
      'fără garanții',
      'comercial',
    ]) {
      expect(text).toContain(topic);
    }
  });
});
