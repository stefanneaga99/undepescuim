import { test, expect } from '@playwright/test';

/** Physical probes for the segment resolver. Tagged data so PR smoke does not
 * silently depend on a live map; the contract assertions remain browser-level. */
test.describe('river segment probes @data @river-segments', () => {
  test('published sectors are finite and ordered', async ({ page }) => {
    const response = await page.request.get('/data/waters.json');
    expect(response.ok()).toBeTruthy();
    const waters = (await response.json()) as Array<Record<string, unknown>>;
    const groups = new Map<string, Array<Record<string, unknown>>>();
    for (const water of waters) {
      if (typeof water.riverGroup !== 'string') continue;
      const list = groups.get(water.riverGroup) ?? [];
      list.push(water);
      groups.set(water.riverGroup, list);
      for (const key of ['sectorStart', 'sectorEnd', 'course_frac']) {
        if (key in water) {
          expect(typeof water[key]).toBe('number');
          expect(water[key] as number).toBeGreaterThanOrEqual(0);
          expect(water[key] as number).toBeLessThanOrEqual(1);
        }
      }
      if (typeof water.sectorStart === 'number' && typeof water.sectorEnd === 'number') {
        expect(water.sectorStart).toBeLessThan(water.sectorEnd);
      }
    }
    expect(groups.size).toBeGreaterThan(0);
  });
});
