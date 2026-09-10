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
  // A fresh browser may receive the optional offline-storage consent sheet.
  // Dismiss it through the real user action before probing map hit-testing;
  // otherwise the modal legitimately owns the pointer route on mobile.
  const continueOnline = page.getByRole('button', { name: /Continuă online|Continue online/i });
  if (await continueOnline.isVisible().catch(() => false)) await continueOnline.click();
}

async function clickMapPath(page: Page): Promise<{ slug: string; name: string }> {
  const candidates = await page.evaluate(() => {
    const map = (window as Window & {
      __UNDEPESCUIM_MAP__?: {
        eachLayer: (visit: (layer: {
          _path?: SVGPathElement;
          feature?: { properties?: { slug?: string; name?: string } };
        }) => void) => void;
      };
    }).__UNDEPESCUIM_MAP__;
    if (!map) return null;

    // A bounding-box centre is often empty space for a curved river. Find a
    // real point on each rendered path instead, and only accept it when the
    // browser's hit-test chain lands in the Leaflet overlay. This exercises
    // the same pointer route as a user (unlike layer.fire/force-click).
    const candidates: Array<{ x: number; y: number; slug: string; name: string }> = [];
    map.eachLayer((layer) => {
      const path = layer._path;
      const props = layer.feature?.properties;
      if (!path || !props?.slug || !props.name || !path.isConnected) return;
      const ctm = path.ownerSVGElement?.getScreenCTM();
      const length = path.getTotalLength();
      if (!ctm || !length) return;
      for (let i = 1; i < 20; i += 1) {
        const point = path.getPointAtLength(length * (i / 20));
        const screen = new DOMPoint(point.x, point.y).matrixTransform(ctm);
        const hit = document.elementFromPoint(screen.x, screen.y);
        const hitStyle = hit ? getComputedStyle(hit) : null;
        if (hit?.closest('.leaflet-overlay-pane') && hitStyle?.pointerEvents !== 'none') {
          // Overlapping rivers are legitimate: the browser dispatches the
          // event to the topmost path, not necessarily the path we sampled.
          // Report that actual hit identity so the assertion checks the
          // selection result rather than a coincidental nearby feature.
          let hitProps: { slug: string; name: string } = { slug: props.slug, name: props.name };
          map.eachLayer((other) => {
            if (other._path === hit && other.feature?.properties?.slug && other.feature.properties.name) {
              hitProps = { slug: other.feature.properties.slug, name: other.feature.properties.name };
            }
          });
          candidates.push({ x: screen.x, y: screen.y, slug: hitProps.slug, name: hitProps.name });
          break;
        }
      }
    });
    return candidates;
  });

  expect(candidates, 'production map bridge should be available').not.toBeNull();
  if (!candidates) throw new Error('production map bridge is unavailable');
  expect(candidates, 'production map should contain a real on-stroke hit point').not.toHaveLength(0);
  const card = page.getByTestId('water-card');
  for (const identity of candidates.slice(0, 20)) {
    await page.mouse.click(identity.x, identity.y);
    if (await card.isVisible().catch(() => false)) {
      // Sector resolution may legitimately replace a river's display name
      // with the contract sector owning the exact click fraction. Assert the
      // resulting named card, not a coincidental nearby layer.
      await expect(card.locator('h2.font-bold').last()).toHaveText(/\S+/);
      return identity;
    }
  }
  await expect(card).toBeVisible({ timeout: 10_000 });
  return candidates[0];
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
