/**
 * F6 — click water → detail card (docs/e2e-test-plan.md §3): name, sector,
 * size, association contact, permit row(s), validity, species/permis links.
 * Runs in all three viewports (vaul drawer <1024px, side panel ≥1024px).
 */
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { Selectors } from '../../helpers/selectors';

test.describe('F6 — water detail card', () => {
  test('contracted river shows sector, size, association, 2 permit rows, validity, links', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.clickWater('raul-somesul-test');
    const card = map.waterCard;

    await expect(card.card).toBeVisible();
    await expect(card.name).toHaveText('Râul Someșul Test');
    await expect(card.card).toContainText('Sector');
    await expect(card.card).toContainText('35 km');
    await expect(card.card).toContainText('Asociația Alpha');
    // national permit + association online permit (alpha has permitUrl)
    await expect(card.permitRows).toHaveCount(2);
    // explicit validity framing for THIS sector (F2a)
    await expect(card.card).toContainText('Permisul Asociația Alpha este valabil pe acest sector.');
    await expect(card.permisLink).toBeVisible();
    await expect(card.speciiLink).toBeVisible();
  });

  test('contracted water without an online permit shows "verifică cu asociația"', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // bbox-fallback lake under beta (no permitUrl) — violet dot, card opens.
    await map.clickWater('lacul-beta-fara-permis');
    const card = map.waterCard;

    await expect(card.name).toHaveText('Lacul Beta Fără Permis Online');
    await expect(card.permitRows).toHaveCount(1); // national permit only
    await expect(card.card).toContainText('Permis: verifică cu asociația');
  });

  test('real pointer click on a water path opens its card (hit pipeline)', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // Full user gesture through Leaflet's hit-testing (visible/hit layer).
    await map.clickWaterByGesture('lacul-test-brasov');
    await expect(map.waterCard.name).toHaveText('Lacul Test');
  });

  test('uncontracted water opens the "Apă necontractată" notice + permit guide link', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // Uncontracted overlay is LOD-culled at national zoom AND viewport-culled —
    // zoom in and center on the river before clicking (12.3 km river, Cluj),
    // then WAIT for the teal layer to actually render (viewport culling +
    // layer rebuild is async — waters-drawn is the contracted layer only).
    await map.panTo(47.0, 23.2, 8);
    await expect
      .poll(async () => map.pathsByColor(['#14b8a6', '#2dd4bf']))
      .toBeGreaterThan(0);
    await map.clickWater('valea-testului-necontractata');
    const card = map.waterCard;

    await expect(card.name).toHaveText('Valea Testului');
    await expect(card.card).toContainText('Apă necontractată');
    await expect(card.permisLink).toBeVisible();
  });
});