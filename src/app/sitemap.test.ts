import { describe, expect, it } from 'vitest';
import sitemap from './sitemap';

describe('sitemap legal surface', () => {
  it('publishes every legal information route', () => {
    const urls = sitemap().map((entry) => entry.url);
    for (const path of ['/confidentialitate', '/termeni', '/contact', '/licente']) {
      expect(urls.some((url) => url.endsWith(path))).toBe(true);
    }
  });
});
