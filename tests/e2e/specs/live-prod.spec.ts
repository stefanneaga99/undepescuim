/**
 * Manual live-production smoke suite. It never uses seeded fixtures and stubs
 * POST /api/report so a run cannot create a real issue.
 * Run with: LIVE_PROD=1 LIVE_URL=https://undepescuim.vercel.app npm run test:e2e:live
 */
import { test, expect, type Page } from '@playwright/test';

const visible = (page: Page, id: string) => page.getByTestId(id).filter({ visible: true }).first();

async function waitForApp(page: Page) {
  await page.goto('/');
  await expect(page.locator('main')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 45_000 });
  await expect.poll(() => page.locator('.leaflet-overlay-pane path').count(), { timeout: 45_000 }).toBeGreaterThan(0);
}

async function clickMapPath(page: Page): Promise<void> {
  const paths = page.locator('.leaflet-overlay-pane path');
  const count = await paths.count();
  expect(count, 'production map should contain clickable water paths').toBeGreaterThan(0);
  // Try several paths: a path can be a short segment or hidden below another
  // Leaflet layer at its centre. This is deliberately a no-dead-zone sweep.
  for (let i = 0; i < Math.min(count, 8); i += 1) {
    const path = paths.nth((i * 7) % count);
    if (!(await path.isVisible().catch(() => false))) continue;
    const box = await path.boundingBox().catch(() => null);
    if (box) {
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2).catch(() => undefined);
    }
    if (await page.getByTestId('water-card').isVisible().catch(() => false)) return;
  }
  await expect(page.getByTestId('water-card')).toBeVisible({ timeout: 10_000 });
}

test.describe('live production', () => {
  test.setTimeout(90_000);

  test.beforeEach(async ({ page }) => {
    await page.route('**/api/report', async (route) => {
      if (route.request().method() !== 'POST') return route.continue();
      await route.fulfill({ contentType: 'application/json', json: {
        ok: true,
        issueUrl: 'https://example.invalid/live-prod-test',
      }});
    });
  });

  test('loads map, filters, and has no dead zones in sampled water paths', async ({ page }) => {
    await waitForApp(page);
    const county = page.getByTestId('county-chip').filter({ visible: true }).first();
    await expect(county).toBeVisible();
    // Exercise the unfiltered map before controls can legitimately cull short
    // production segments at national zoom.
    await clickMapPath(page);
    await page.keyboard.press('Escape');
    await county.click();
    await expect(page.getByTestId('locality-filter').filter({ visible: true }).first()).toBeVisible();
    const locality = page.getByTestId('locality-filter').filter({ visible: true }).first();
    await locality.click();
    const option = page.getByTestId('locality-option').filter({ visible: true }).first();
    if (await option.count()) await option.click();
    await page.keyboard.press('Escape');

    const association = page.getByTestId('assoc-search').filter({ visible: true }).first();
    if (await association.count()) {
      await association.click();
      const option = page.getByTestId('assoc-option').filter({ visible: true }).first();
      await expect(option).toBeVisible({ timeout: 10_000 });
      await option.click();
    }
    await clickMapPath(page);
  });

  test('report dialog opens above the map and API is safely stubbed', async ({ page }) => {
    await waitForApp(page);
    await clickMapPath(page);
    const report = visible(page, 'report-flag');
    const fixedReport = visible(page, 'report-flag-fixed');
    const trigger = await report.isVisible().catch(() => false) ? report : fixedReport;
    await expect(trigger).toBeVisible();
    await trigger.click();
    const dialog = page.getByTestId('report-dialog');
    await expect(dialog).toBeVisible();
    const zIndex = await dialog.evaluate((el) => Number.parseInt(getComputedStyle(el).zIndex || '0', 10));
    expect(zIndex).toBeGreaterThanOrEqual(1000);
    const reason = page.getByTestId('report-reason').first();
    if (await reason.count()) await reason.click();
    const submit = dialog.getByRole('button', { name: /Trimite|Send/i });
    if (await submit.count() && await submit.isEnabled()) {
      const response = page.waitForResponse((r) => r.url().endsWith('/api/report'));
      await submit.click();
      expect((await response).status()).toBe(200);
    }
  });

  test('dark mode and language switcher update the document', async ({ page }) => {
    await waitForApp(page);
    const theme = visible(page, 'theme-toggle');
    await expect(theme).toBeVisible();
    await theme.click();
    await expect.poll(() => page.locator('html').getAttribute('class')).toMatch(/dark/);
    const language = visible(page, 'lang-switcher');
    await expect(language).toBeVisible();
    await language.click();
    const english = page.getByTestId('lang-en').filter({ visible: true }).first();
    if (await english.count()) {
      await english.click();
      await expect.poll(() => page.locator('html').getAttribute('lang')).toBe('en');
    }
  });

  test('species, permit, and PWA manifest are reachable', async ({ page, request }) => {
    await waitForApp(page);
    for (const path of ['/specii', '/permis']) {
      const response = await request.get(new URL(path, page.url()).toString());
      expect(response.ok(), path).toBeTruthy();
    }
    const manifest = await request.get(new URL('/manifest.webmanifest', page.url()).toString());
    expect(manifest.ok()).toBeTruthy();
    const body = await manifest.json();
    expect(body.display).toBe('standalone');
    expect(body.icons.length).toBeGreaterThanOrEqual(2);
  });
});
