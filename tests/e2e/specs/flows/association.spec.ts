/**
 * F4 — association search + select/highlight, F5 — association detail
 * (docs/e2e-test-plan.md §3). Runs in all three viewports.
 */
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { waitForMapIdle } from '../../helpers/map';

// Coverage color contract (src/utils/colors.ts getFeatureStyle):
const NEUTRAL_COLOR = '#3b82f6'; // no association selected — blue
const COVERED_COLOR = '#22c55e'; // belongs to the selected association — bold green
const UNCOVERED_COLOR = '#9ca3af'; // not covered — dimmed grey

test.describe('F4 — association select + highlight', () => {
  test('selecting an association highlights its waters green, others grey, no over-zoom', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // Neutral view: waters blue.
    expect(await map.pathsByColor([NEUTRAL_COLOR])).toBeGreaterThan(0);

    await map.associationSearch.select('asociatia-alpha');

    // Chip appears with the association name + water count.
    await expect(map.associationChip.chip).toBeVisible();
    await expect(map.associationChip.chip).toContainText('Asociația Alpha');

    // Coverage: alpha's waters bold green, everything else dimmed grey.
    expect(await map.pathsByColor([COVERED_COLOR])).toBeGreaterThan(0);
    expect(await map.pathsByColor([UNCOVERED_COLOR])).toBeGreaterThan(0);
    expect(await map.pathsByColor([NEUTRAL_COLOR])).toBe(0);

    // FlyTo cap: the fitBounds must never over-zoom past 12 (t_d987cdb7).
    expect(await map.zoom()).toBeLessThanOrEqual(12);

    // "Toate asociațiile" clears back to the neutral blue view.
    await map.associationSearch.clearSelection();
    await expect(map.associationChip.chip).toHaveCount(0);
    expect(await map.pathsByColor([NEUTRAL_COLOR])).toBeGreaterThan(0);
  });

  test('search focus/typing never zooms the map (t_d987cdb7)', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);

    const z0 = await map.zoom();
    await map.associationSearch.open();
    await page.getByRole('combobox').fill('alpha');
    expect(await map.zoom()).toBe(z0);
    await page.keyboard.press('Escape');
    expect(await map.zoom()).toBe(z0);
  });

  test('clicking a water outside the association clears the chip but keeps the zoom (t_697ba939/t_abccfd6c)', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.associationSearch.select('asociatia-alpha');
    await waitForMapIdle(page);
    await expect(map.associationChip.chip).toBeVisible();
    const zoomSelected = await map.zoom();

    // lacul-buc-1 belongs to beta → the click must clear alpha WITHOUT the
    // map flying back to the national view (suppressAssociationFlyTo).
    await map.clickWater('lacul-buc-1');
    await waitForMapIdle(page);
    await expect(map.associationChip.chip).toHaveCount(0);
    await expect(map.waterCard.name).toHaveText('Lacul București 1');
    expect(await map.zoom()).toBe(zoomSelected);
  });
});

test.describe('F5 — association detail sheet', () => {
  test('chip opens the detail sheet with counties, validity and reciprocity', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.associationSearch.select('asociatia-alpha');
    await map.associationChip.openDetail();

    await expect(map.associationChip.detailSheet).toBeVisible();
    await expect(map.associationChip.detailName).toHaveText('Asociația Alpha');
    await expect(map.associationChip.detailSheet).toContainText('este valabil pe 3 ape');
    await expect(map.associationChip.detailSheet).toContainText('în județele: Brașov, Cluj');
    await expect(map.associationChip.detailSheet).toContainText('Reciprocitate: confirmată.');

    // Escape closes the sheet.
    await page.keyboard.press('Escape');
    await expect(map.associationChip.detailSheet).toHaveCount(0);
  });

  test('association, location, provenance and contact links use safe destinations and labels', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);
    await map.associationSearch.select('asociatia-alpha');
    await map.associationChip.openDetail();

    const sheet = map.associationChip.detailSheet;
    await expect(sheet).toContainText('Sediu test');
    await expect(sheet.getByRole('link', { name: 'Sursa oficială' })).toHaveAttribute(
      'href',
      'https://source.alpha.example.ro/locations',
    );
    await expect(sheet.getByRole('link', { name: 'Site contact' })).toHaveAttribute(
      'href',
      'https://office.alpha.example.ro/',
    );
    await expect(sheet.getByRole('link', { name: 'contact@alpha.example.ro' })).toHaveAttribute(
      'href',
      'mailto:contact@alpha.example.ro',
    );

    const externalLinks = sheet.locator('a[target="_blank"]');
    await expect(externalLinks).not.toHaveCount(0);
    for (const link of await externalLinks.all()) {
      await expect(link).toHaveAttribute('rel', /(^|\s)noopener(\s|$)/);
      await expect(link).toHaveAttribute('rel', /(^|\s)noreferrer(\s|$)/);
      await expect(link).toHaveAttribute('href', /^https:\/\//);
    }
    // The fixture includes an unsafe javascript: contact URL; it must not
    // become a clickable destination.
    await expect(sheet.locator('a[href^="javascript:"]')).toHaveCount(0);
  });
});