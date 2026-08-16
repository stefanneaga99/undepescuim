/**
 * Edge cases from docs/e2e-test-plan.md §3 (regression tier).
 * Each case is a normal seeded-data test unless noted; geolocation-deny uses
 * a navigator stub, report 503/honeypot hit the REAL /api/report route.
 */
import type { TestInfo } from '@playwright/test';
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { ReportDialog } from '../../pages/ReportDialog';
import { Selectors } from '../../helpers/selectors';

test.describe('edge cases', () => {
  test('geolocation denied → localized bubble, no dot, no sheet, zoom untouched', async ({
    page,
    mapReady,
  }) => {
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition: (_success: unknown, error: unknown) => {
            (error as (e: { code: number }) => void)?.({ code: 1 }); // PERMISSION_DENIED
          },
        },
        configurable: true,
      });
    });
    await mapReady();
    const map = new MapPage(page);
    const z0 = await map.zoom();

    await map.locateButton.click();

    await expect(map.geolocationBubble).toBeVisible();
    await expect(map.geolocationBubble).toContainText('Accesul la locație este blocat.');
    await expect(page.locator('.user-position-dot')).toHaveCount(0);
    await expect(map.nearbySheet.sheet).toHaveCount(0);
    expect(await map.zoom()).toBe(z0);
  });

  test('county+type combo with zero waters renders an empty map without crashing', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    // Brașov has only lakes — Râuri + Brașov = nothing to draw
    await map.filterBar.toggleCounty('Brașov');
    await map.filterBar.setType('rau');

    await expect(page.getByTestId(Selectors.watersDrawn)).toHaveCount(0);
    expect(await map.pathCount()).toBe(0);
    // filter state stays consistent
    await expect(map.filterBar.countyChip('Brașov')).toHaveAttribute('aria-pressed', 'true');
    await expect(map.filterBar.typeOption('rau')).toHaveAttribute('aria-pressed', 'true');

    // recovering the filter brings the waters back
    await map.filterBar.setType('all');
    await expect(page.getByTestId(Selectors.watersDrawn)).toBeAttached();
    expect(await map.pathCount()).toBeGreaterThan(0);
  });

  test('long water name renders fully, no horizontal overflow, sheet scrolls', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.clickWater('raul-cu-nume-lung');
    const card = map.waterCard;

    // full name present (wrapping is fine; truncation must not lose data)
    await expect(card.name).toContainText('un nume foarte lung');
    // no horizontal overflow inside the card
    const overflowPx = await card.card.evaluate(
      (el) => (el as HTMLElement).scrollWidth - (el as HTMLElement).clientWidth,
    );
    expect(overflowPx).toBeLessThanOrEqual(1);
  });

  test('keyboard nav in the association search: ArrowDown+Enter selects, Escape closes', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.associationSearch.open();
    await page.getByRole('combobox').fill('beta');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');

    await expect(map.associationChip.chip).toBeVisible();
    await expect(map.associationChip.chip).toContainText('Asociația Beta');

    // Escape closes the dropdown without changing the selection
    await map.associationSearch.open();
    await page.keyboard.press('Escape');
    await expect(
      page.getByTestId(Selectors.assocOption).filter({ visible: true }),
    ).toHaveCount(0);
    await expect(map.associationChip.chip).toContainText('Asociația Beta');
  });

  test('keyboard nav in the species search: ArrowDown+Enter selects the row', async ({ page }) => {
    await page.goto('/specii');
    await page.getByTestId(Selectors.speciesSearchMobile).or(
      page.getByTestId(Selectors.speciesSearch),
    ).filter({ visible: true }).click();
    await page.getByRole('combobox').fill('sturion');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expect(page.locator('#specii-sturion-de-dunare')).toHaveClass(/species-flash/);
  });

  test('768px boundary → desktop panel layout (no hamburger, inline links)', async (
    { mapReady, page },
    testInfo: TestInfo,
  ) => {
    test.skip(testInfo.project.name !== 'tablet', '768px boundary case (plan §3)');
    await mapReady();

    const map = new MapPage(page);
    await expect(map.header.hamburger).toBeHidden(); // sm:hidden at ≥640
    await expect(map.header.navSpecii).toBeVisible(); // sm:inline-flex at ≥640
    // md:flex desktop filter panel visible (and the mobile bar md:hidden)
    await expect(map.filterBar.allCountyChips()).toHaveCount(4);
  });

  test('contract filter: contractate hides uncontracted, necontractate hides contracted', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);
    // uncontracted overlay is LOD-culled at national zoom — zoom in first
    await map.zoomTo(8);

    const all = await map.pathCount();

    await map.filterBar.setContract('contractate');
    expect(await map.pathCount()).toBeLessThan(all);

    await map.filterBar.setContract('necontractate');
    expect(await map.pathCount()).toBeGreaterThan(0);
    expect(await map.pathsByColor(['#3b82f6'])).toBe(0); // no contracted blue left

    await map.filterBar.setContract('all');
    expect(await map.pathCount()).toBe(all);
  });

  test('report without a configured token surfaces the error state (503 not_configured)', async ({
    mapReady,
    page,
  }) => {
    // Real POST /api/report — no stub. Requires REPORT_GITHUB_TOKEN absent.
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await map.clickWater('raul-somesul-test');
    await map.waterCard.clickButton(map.waterCard.reportFlag);
    await dialog.pickReason('other');
    await dialog.submit();

    await expect(dialog.errorText).toBeVisible();
  });

  test('report honeypot: filled hidden website field is silently dropped (ok, no GitHub link)', async ({
    mapReady,
    page,
  }) => {
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await map.clickWater('raul-somesul-test');
    await map.waterCard.clickButton(map.waterCard.reportFlag);
    await dialog.pickReason('other');
    await dialog.dialog.locator('input[aria-hidden="true"]').fill('spam-bot', { force: true });
    await dialog.submit();

    await expect(dialog.successText).toBeVisible();
    await expect(dialog.githubLink).toHaveCount(0);
  });

  test('unknown route returns a proper 404', async ({ page }) => {
    const resp = await page.goto('/aceasta-pagina-nu-exista');
    expect(resp?.status()).toBe(404);
  });

  test('no dark-mode theme toggle is rendered (dark mode not implemented)', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(
      page.locator('[data-theme-toggle], button[aria-label*="temă" i], button[aria-label*="dark" i]'),
    ).toHaveCount(0);
  });
});