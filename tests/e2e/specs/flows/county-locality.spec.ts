/**
 * F2 — county filter, F3 — locality filter (docs/e2e-test-plan.md §3).
 * Runs in all three viewports against the seeded mini-dataset.
 *
 * Seed geography: Cluj (Râul Someșul Test, long-name river, Valea Testului
 * uncontracted), Brașov (Lacul Test, Balta Privată Test uncontracted),
 * Ilfov (4 Bucharest lakes + bbox-fallback lake), Iași (2 rivers).
 */
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';

test.describe('F2 — county filter', () => {
  test('toggle chip narrows the map; untoggle restores', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);

    // "Toate județele" indicator before any selection
    await expect(page.getByText('Toate județele').filter({ visible: true })).toBeVisible();

    const before = await map.pathCount();

    await map.filterBar.toggleCounty('Cluj');
    await expect(map.filterBar.countyChip('Cluj')).toHaveAttribute('aria-pressed', 'true');
    // F2: locality dropdown appears only when >= 1 county is selected
    await expect(map.filterBar.localityTrigger).toBeVisible();
    // map narrowed
    await expect
      .poll(async () => map.pathCount())
      .toBeLessThan(before);
    expect(await map.pathCount()).toBeGreaterThan(0);

    // untoggle restores the full set
    await map.filterBar.toggleCounty('Cluj');
    await expect
      .poll(async () => map.pathCount())
      .toBe(before);
  });

  test('county filter still draws the county-clipped river geometry', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.filterBar.toggleCounty('Brașov');
    await expect(map.filterBar.countyChip('Brașov')).toHaveAttribute('aria-pressed', 'true');

    // The Brașov lake remains clickable and opens its card (F6 lean check).
    await map.clickWater('lacul-test-brasov');
    await expect(map.waterCard.name).toHaveText('Lacul Test');

    // A water outside the county must not be clickable (its layer is gone).
    await expect(map.clickWaterByGesture('raul-somesul-test')).rejects.toThrow();
  });
});

test.describe('F3 — locality filter', () => {
  test('pick locality narrows + zooms; clear resets; county change invalidates locality', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // locality control hidden until a county is selected
    await expect(map.filterBar.localityTrigger).toHaveCount(0);

    await map.filterBar.toggleCounty('Cluj');
    await expect(map.filterBar.localityTrigger).toBeVisible();

    // t_9529e678: picking a locality must VISIBLY change the map — it flies
    // to the filtered set (national view otherwise shows sub-pixel specks /
    // LOD-culled ponds, which was the reported "map doesn't change" bug).
    const before = await map.pathCount();
    await map.filterBar.selectLocality('Comuna Test');
    await expect.poll(async () => map.zoom()).toBeGreaterThan(7);
    // the locality-tagged water is present and clickable, the null-locality
    // water (raul-cu-nume-lung) is hidden by the filter
    await map.clickWater('raul-somesul-test');
    await expect(map.waterCard.name).toHaveText('Râul Someșul Test');
    await page.keyboard.press('Escape'); // close the card sheet
    await expect(map.clickWaterByGesture('raul-cu-nume-lung')).rejects.toThrow();

    // reset clears the locality filter AND restores the pre-locality view
    await map.filterBar.resetLocalities();
    await expect
      .poll(async () => map.pathCount())
      .toBe(before + 1); // t_21d2f68d: the clicked water stays SELECTED after
    // the card's Escape close (orange focus persists), so its focus-slice
    // feature adds exactly one extra rendered path vs the untouched view.

    // re-pick, then toggling ANOTHER county invalidates the locality (store R)
    await map.filterBar.selectLocality('Comuna Test');
    await map.filterBar.toggleCounty('Brașov');
    await expect(map.filterBar.localityTrigger).toContainText('Toate localitățile');
  });
});