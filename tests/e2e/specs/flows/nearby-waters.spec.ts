/**
 * F7 — nearby waters via geolocation (docs/e2e-test-plan.md §3).
 * Runs in all three viewports. Local chromium + localhost = secure context →
 * real `grantPermissions` + `setGeolocation` work (plan §5.5 — no CDP).
 */
import { test, expect } from '../../fixtures/app';
import { GEO_POINTS } from '../../fixtures/seed-data';
import { MapPage } from '../../pages/MapPage';

test.describe('F7 — nearby waters (geolocation grant)', () => {
  test('grant near Bucharest → dot + radius + sheet rows with km/county; default 25 km', async ({
    context,
    page,
    mapReady,
  }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({
      latitude: GEO_POINTS.bucharest.lat,
      longitude: GEO_POINTS.bucharest.lon,
    });
    await mapReady();

    const map = new MapPage(page);
    await map.locateButton.click();

    // user dot + radius circle on the overlay (t_5ddc6022)
    await expect(page.locator('.user-position-dot')).toBeVisible();
    expect(await map.pathsByColor(['#2563eb'])).toBeGreaterThan(0);

    const sheet = map.nearbySheet;
    await expect(sheet.sheet).toBeVisible();
    // default radius stays 25 km (≥3 contracted waters within it)
    await expect(sheet.sheet).toContainText('Rază: 25 km');
    // rows carry distance + county (Ilfov polygon in the counties seed)
    await expect(sheet.rows).toHaveCount(5);
    await expect(sheet.row('Lacul București 1')).toBeVisible();
    await expect(sheet.row('Lacul București 1')).toContainText('Ilfov');
    await expect(sheet.sheet).toContainText('· Asociația Beta');
  });

  test('adaptive radius expands 25 → 50 km when <3 nearby (Iași) and row opens the card', async ({
    context,
    page,
    mapReady,
  }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({
      latitude: GEO_POINTS.iasi.lat,
      longitude: GEO_POINTS.iasi.lon,
    });
    await mapReady();

    const map = new MapPage(page);
    await map.locateButton.click();

    const sheet = map.nearbySheet;
    await expect(sheet.sheet).toBeVisible();
    await expect(sheet.sheet).toContainText('Rază: 50 km');

    // row tap → the water's detail card opens
    await sheet.openRow('Râul Bahlui Test');
    await expect(map.waterCard.name).toHaveText('Râul Bahlui Test');
  });
});