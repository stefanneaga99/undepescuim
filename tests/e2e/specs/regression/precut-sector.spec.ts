import { test, expect } from '@playwright/test';
import { routeData } from '../../fixtures/routes';
import {
  PRECUT_LONG_SLUG,
  PRECUT_REVIEW_SLUG,
  PRECUT_SHORT_SLUG,
  PRECUT_WATERS,
  seed,
} from '../../fixtures/seed-data';
import { clickWaterBySlugAtFraction, clickWaterBySlugAtFractionWithProbe, waitForMapReady } from '../../helpers/map';
import { MapPage } from '../../pages/MapPage';

/**
 * River geometry v2 pre-cut sectors (docs/plans/river-geometry-v2.md T4.1),
 * on seeded fixture data: a pre-cut water is selected and focused as its own
 * geometry. Unskip against a real resolved slug at cutover (T4.4).
 */
test.describe('pre-cut river sectors @seeded', () => {
  test.skip(!!process.env.LIVE_PROD, 'seeded fixture only');

  test.beforeEach(async ({ page }) => {
    await routeData(page, { ...seed, waters: [...seed.waters, ...PRECUT_WATERS] });
    await page.goto('/');
    await waitForMapReady(page);
    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: { fitBounds: (b: number[][]) => void } }).__UNDEPESCUIM_MAP__;
      map?.fitBounds([[45.4, 24.15], [45.8, 24.85]]);
    });
    await page.waitForTimeout(500);
  });

  test('a click where sectors overlap selects the short sector drawn on top', async ({ page }) => {
    const map = new MapPage(page);
    const probe = await clickWaterBySlugAtFractionWithProbe(page, PRECUT_SHORT_SLUG, 0.5);
    expect(probe.pane).toContain('leaflet-overlay-pane');
    await expect(map.waterCard.card).toBeVisible();
    await expect(map.waterCard.card).toContainText('Râul Precut Scurt');
    expect((await map.focusSnapshot()).slug).toBe(PRECUT_SHORT_SLUG);
  });

  test('a resolved sector is focused as its own geometry only', async ({ page }) => {
    const map = new MapPage(page);
    await clickWaterBySlugAtFraction(page, PRECUT_LONG_SLUG, 0.1);
    await expect(map.waterCard.card).toContainText('Râul Precut Lung');
    const snapshot = await map.focusSnapshot();
    expect(snapshot.kind).toBe('verified-sector-focus');
    expect(snapshot.slug).toBe(PRECUT_LONG_SLUG);
    // One orange path: the legacy group slicing would paint BOTH members of
    // the river group (long + short) with the [0, 1] interval.
    expect(snapshot.orangePaths).toBe(1);
    expect(snapshot.unverifiedMarkerCount).toBe(0);
  });

  test('a review sector keeps the unverified presentation', async ({ page }) => {
    const map = new MapPage(page);
    await clickWaterBySlugAtFraction(page, PRECUT_REVIEW_SLUG, 0.5);
    await expect(map.waterCard.card).toContainText('Râul Precut Neverificat');
    const snapshot = await map.focusSnapshot();
    expect(snapshot.kind).toBe('feature-selected-unverified-sector');
    expect(snapshot.unverifiedMarkerCount).toBe(1);
    expect(snapshot.orangePaths).toBe(0);
    await expect(page.getByTestId('water-focus-status')).toContainText('Geometria exactă a sectorului nu este verificată');
  });
});
