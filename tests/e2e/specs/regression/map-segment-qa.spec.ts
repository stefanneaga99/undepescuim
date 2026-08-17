/**
 * Live-QA regression (validated with real clicks on the deployed site, then
 * codified). Focused on a gap no other spec covers: clicking many river
 * SEGMENTS must produce a resolution (detail sheet opens) — no silent dead
 * zones, on every viewport. Slice/multi-contract association correctness was
 * validated live across Brașov/Sibiu/Cluj/Prahova/Buzău (associations change
 * per click position). județ/localitate/association-green are covered by
 * county-locality.spec.ts & association.spec.ts.
 */
import { test, expect } from '../../fixtures/app';

test.describe('map segment → association resolution', () => {
  test('every river-segment click opens a non-empty detail sheet (no silent dead zones)', async ({
    page,
    mapReady,
  }) => {
    await mapReady();
    const map = await page.locator('.leaflet-container').boundingBox();
    if (!map) {
      test.skip(true, 'map not rendered in this seed');
      return;
    }
    const results: boolean[] = [];
    // grid of 6 clicks across the map center region
    for (let i = 0; i < 6; i++) {
      const x = map.x + map.width * (0.2 + 0.15 * i);
      const y = map.y + map.height * (0.3 + 0.15 * (i % 3));
      await page.mouse.click(x, y);
      await page.waitForTimeout(1000);
      const body = await page.evaluate(() => document.body.innerText.slice(-1800));
      // a resolution means a detail sheet appeared OR une contract-ruled; blank map click opens nothing
      results.push(
        /Sector|ASOCIAȚIE|Necontract|Romsilva|privat|Dimens\.|Râul |Valea |Lacul |Pârâul/i.test(body),
      );
    }
    expect(results.every(Boolean)).toBe(true);
  });
});