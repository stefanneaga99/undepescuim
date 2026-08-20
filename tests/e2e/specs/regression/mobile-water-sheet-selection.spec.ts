import { test, expect } from '../../fixtures/app';
import type { Page } from '@playwright/test';
import { MapPage } from '../../pages/MapPage';

test.describe('mobile water detail A→B selection', () => {
  test.skip(({ isMobile }) => !isMobile, 'Vaul drawer only exists below 1024px');

  async function expectUsablePeek(map: MapPage, page: Page, slug: string) {
    await expect.poll(async () => {
      const state = await map.waterCard.sheetSnapshot();
      const viewport = await page.evaluate(() => window.innerHeight);
      return state.selectedSlug === slug && state.scrollTop === 0 && state.handleRect.bottom <= viewport && state.handleHit;
    }).toBe(true);
    const state = await map.waterCard.sheetSnapshot();
    expect(state.selectedSlug).toBe(slug);
    expect(state.scrollTop).toBe(0);
    expect(state.handleRect.height).toBeGreaterThanOrEqual(44);
    expect(state.handleRect.width).toBeGreaterThanOrEqual(300);
    expect(state.handleRect.top).toBeGreaterThanOrEqual(state.sheetRect.top);
    expect(state.handleRect.bottom).toBeLessThanOrEqual(await page.evaluate(() => window.innerHeight));
    expect(state.handleHit).toBe(true);
  }

  test('resets B to an affordance-visible Peek after A is collapsed/scrolled', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);
    await map.clickWater('raul-somesul-test');
    await expect(map.waterCard.name).toHaveText('Râul Someșul Test');

    await map.waterCard.grabber.click();
    await map.waterCard.card.evaluate((card) => card.parentElement?.scrollTo({ top: 160 }));
    const a = await map.waterCard.sheetSnapshot();
    await expect.poll(() => map.waterCard.sheetSnapshot().then((s) => s.scrollTop)).toBeGreaterThan(0);

    await map.clickWater('raul-cu-nume-lung');
    await expect(map.waterCard.name).toContainText('Râul cu un nume foarte lung');
    const b = await map.waterCard.sheetSnapshot();
    await test.info().attach('mobile-water-sheet-a-b-snapshots.json', {
      body: JSON.stringify({ a, b }, null, 2),
      contentType: 'application/json',
    });

    await expectUsablePeek(map, page, 'raul-cu-nume-lung');
  });

  test('direct A→B selection stays at a usable Peek', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);
    await map.clickWater('raul-somesul-test');
    await map.clickWater('raul-cu-nume-lung');
    await expect(map.waterCard.name).toContainText('Râul cu un nume foarte lung');
    await expectUsablePeek(map, page, 'raul-cu-nume-lung');
  });

  test('close and reopen preserves map focus but resets the selected water to Peek', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);
    await map.clickWater('raul-somesul-test');
    await map.waterCard.grabber.click();
    await map.waterCard.sheet.locator('button[aria-label]').click();
    await expect(map.waterCard.sheet).toBeHidden();
    await map.clickWater('raul-somesul-test');
    await expectUsablePeek(map, page, 'raul-somesul-test');
  });

  test('rapid A→B→A leaves the final identity and handle usable', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);
    await map.clickWater('raul-somesul-test');
    await map.clickWater('raul-cu-nume-lung');
    await map.clickWater('raul-somesul-test');
    await expect(map.waterCard.name).toHaveText('Râul Someșul Test');
    await expectUsablePeek(map, page, 'raul-somesul-test');
  });
});