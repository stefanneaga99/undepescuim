/**
 * F1 — app load smoke (docs/e2e-test-plan.md §3, @smoke = CI canary).
 * Runs in all three viewports. Asserts: header, map container, filter bar,
 * vector paths drawn, zero console/page errors (hydration + Leaflet gate).
 */
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { Header } from '../../pages/Header';

test.describe('F1 — app load', () => {
  test('map boots with header, filters and vector paths — no console errors', async ({
    mapReady,
    page,
    collectedErrors,
  }) => {
    await mapReady();

    const map = new MapPage(page);
    await expect(map.root).toBeVisible();
    await expect(map.leafletContainer).toBeVisible();

    const header = new Header(page);
    await expect(header.logo).toBeVisible();

    // Filter bar derives county chips from the seed (4 counties).
    await expect(map.filterBar.allCountyChips()).toHaveCount(4);

    // Vector overlay drawn (contracted + uncontracted).
    expect(await map.pathCount()).toBeGreaterThan(0);

    // Hydration/Leaflet console gate — fail on ANY error during load.
    expect(collectedErrors).toEqual([]);
  });
});