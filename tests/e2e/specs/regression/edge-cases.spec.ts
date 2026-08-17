/**
 * Edge cases from docs/e2e-test-plan.md §3 (regression tier).
 * Each case is a normal seeded-data test unless noted; geolocation-deny uses
 * a navigator stub, report 503/honeypot hit the REAL /api/report route.
 */
import type { TestInfo } from '@playwright/test';
import { readFileSync } from 'node:fs';
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
            // The app checks `e.code === e.PERMISSION_DENIED` — the browser
            // error object carries both; the stub must too ('denied' branch).
            (error as (e: { code: number; PERMISSION_DENIED?: number }) => void)?.({
              code: 1,
              PERMISSION_DENIED: 1,
            });
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
    await page.getByRole('combobox').fill('somn'); // single match — Enter is unambiguous
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expect(page.locator('#specii-somn')).toHaveClass(/species-flash/);
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
    // Uncontracted overlays are LOD-culled AND viewport-culled — pan to the
    // Cluj cluster (contracted somesul + uncontracted vale) so BOTH color
    // families render; assert by color, not raw path count (counts include
    // the invisible hit polylines and are viewport-dependent).
    await map.panTo(47.0, 23.2, 8);
    await expect.poll(async () => map.pathsByColor(['#14b8a6', '#2dd4bf'])).toBeGreaterThan(0);
    await expect.poll(async () => map.pathsByColor(['#3b82f6'])).toBeGreaterThan(0);

    await map.filterBar.setContract('contractate');
    // teal (uncontracted) disappears; contracted blue remains
    await expect.poll(async () => map.pathsByColor(['#14b8a6', '#2dd4bf'])).toBe(0);
    expect(await map.pathsByColor(['#3b82f6'])).toBeGreaterThan(0);

    await map.filterBar.setContract('necontractate');
    await expect.poll(async () => map.pathsByColor(['#3b82f6'])).toBe(0); // no contracted blue left
    await expect.poll(async () => map.pathsByColor(['#14b8a6', '#2dd4bf'])).toBeGreaterThan(0);

    await map.filterBar.setContract('all');
    await expect.poll(async () => map.pathsByColor(['#3b82f6'])).toBeGreaterThan(0);
    await expect.poll(async () => map.pathsByColor(['#14b8a6', '#2dd4bf'])).toBeGreaterThan(0);
  });

  test('report without a configured token surfaces the error state (503 not_configured)', async ({
      mapReady,
      page,
    }) => {
      // Real POST /api/report — no stub. The not_configured path only exists
      // when the server has NO REPORT_GITHUB_TOKEN. Locally .env.local sets one
      // (so this test would CREATE a real GitHub issue) — skip here; the path
      // is exercised in CI where no token is configured.
      const localToken = readFileSync('.env.local', 'utf8').includes('REPORT_GITHUB_TOKEN=');
      test.skip(localToken, 'REPORT_GITHUB_TOKEN configured locally — not_configured is a CI-only path');

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
    // React-controlled input: native value set + input event (a plain
    // .fill() on the hidden input never reaches onChange, so the honeypot
    // would stay empty and the report would NOT be dropped).
    await dialog.dialog
      .locator('input[aria-hidden]')
      .evaluate((el) => {
        const setter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          'value',
        )?.set;
        setter?.call(el, 'spam-bot');
        el.dispatchEvent(new Event('input', { bubbles: true }));
      });
    await dialog.submit();

    await expect(dialog.successText).toBeVisible();
    await expect(dialog.githubLink).toHaveCount(0);
  });

  test('unknown route returns a proper 404', async ({ page }) => {
    const resp = await page.goto('/aceasta-pagina-nu-exista');
    expect(resp?.status()).toBe(404);
  });

  test('dark mode: theme toggle is rendered and switches .dark on <html>', async ({
    page,
  }) => {
    await page.goto('/');
    const toggle = page.getByTestId(Selectors.themeToggle);
    await expect(toggle).toBeVisible();
    // Start from an explicit light state (clean localStorage + light color scheme)
    const wasDark = await page.evaluate(() =>
      document.documentElement.classList.contains('dark'),
    );
    if (wasDark) await toggle.click(); // normalise to light
    await expect(page.locator('html')).not.toHaveClass(/dark/);

    await toggle.click();
    await expect(page.locator('html')).toHaveClass(/dark/);
    // persists across reload (next-themes stores the choice in localStorage)
    await page.reload();
    await expect(page.locator('html')).toHaveClass(/dark/);
    // toggling back clears it
    await page.getByTestId(Selectors.themeToggle).click();
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });
});