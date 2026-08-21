import { test, expect } from '@playwright/test';
import { focusSnapshot, waitForMapReady } from '../../helpers/map';
import { test as seededTest } from '../../fixtures/app';
import { clickWaterBySlugAtFraction } from '../../helpers/map';
import { MapPage } from '../../pages/MapPage';
import { UNVERIFIED_FOCUS_SELECTED_SLUG } from '../../fixtures/seed-data';

test.describe('Târnava Mare mijlocie sector integrity', () => {
  test.skip(!process.env.LIVE_PROD, 'production evidence capture only');

  test('captures the immutable contract record and live map diagnostics', async ({ page }, testInfo) => {
    const watersResponse = await page.request.get('/data/waters.json');
    expect(watersResponse.ok()).toBeTruthy();
    const waters = (await watersResponse.json()) as Array<Record<string, unknown>>;
    const selected = waters.find((water) => water.slug === 'anpa-anpa-0333');
    expect(selected).toMatchObject({
      slug: 'anpa-anpa-0333',
      name: 'Râul Târnava Mare mijlocie',
      judet: 'Harghita',
      dimensiune: '5 Km',
      limite: 'Aval baraj lac Zetea – pod Desag',
      riverGroup: 'tarnava-mare',
      course_frac: 0.1072,
    });

    const clipsResponse = await page.request.get('/data/waters_county_clips.json');
    expect(clipsResponse.ok()).toBeTruthy();
    const clips = (await clipsResponse.json()) as Record<string, unknown>;
    expect(clips).toHaveProperty('anpa-anpa-0333');

    await page.goto('/');
    await waitForMapReady(page);
    const diagnostics = await focusSnapshot(page);
    await testInfo.attach('tarnava-mare-mijlocie-production-repro.json', {
      body: JSON.stringify({
        project: testInfo.project.name,
        selected,
        countyClipPresent: true,
        diagnostics,
      }, null, 2),
      contentType: 'application/json',
    });
  });
});

seededTest.describe('Târnava-like unverified sector focus @seeded', () => {
  seededTest('renders one violet reference marker on the selected owner course', async ({ mapReady, page }) => {
    seededTest.skip(!!process.env.LIVE_PROD, 'seeded fixture only');
    await mapReady();
    const map = new MapPage(page);
    await clickWaterBySlugAtFraction(page, 'tarnava-like-owner', 0.5);
    await expect(map.waterCard.card).toBeVisible();
    await expect(map.waterCard.card).toContainText('5 Km');
    const snapshot = await map.focusSnapshot();
    expect(snapshot.kind).toBe('feature-selected-unverified-sector');
    expect(snapshot.orangePaths).toBe(0);
    expect(snapshot.unverifiedMarkerCount).toBe(1);
    expect(snapshot.markerAriaLabels[0]).toContain('Geometria exactă a sectorului nu este verificată');
    await expect(page.getByTestId('water-focus-status')).toContainText('Geometria exactă a sectorului nu este verificată');
    await page.locator('.water-unverified-focus-pane path').click();
    await expect(map.waterCard.card).toBeVisible();
    expect((await map.focusSnapshot()).slug).toBe(UNVERIFIED_FOCUS_SELECTED_SLUG);
  });
});
