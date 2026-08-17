/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §9 — TESTS, user mandate):
 *   1. SW registers and controls the page
 *   2. offline reload serves shell + data (Playwright offline mode)
 *   3. visited map tiles cached with a 7-day TTL (no prefetch)
 *   4. installability: manifest link + icons resolve
 *   5. "last updated" freshness visible in the header
 *
 * Deliberately does NOT extend the seeded app fixture (routeData intercepts
 * every /data/* fetch — the service worker must see REAL network responses to
 * populate its caches). Runs against the real prod build served by the
 * playwright webServer, and must override the global `serviceWorkers: 'block'`
 * config with `allow` (otherwise registration is suppressed).
 */
import { test, expect, type Page } from '@playwright/test';
import { Selectors } from '../../helpers/selectors';
import { waitForMapReady } from '../../helpers/map';

test.use({ serviceWorkers: 'allow' });

/** 1×1 transparent PNG — deterministic stand-in for real OSM tiles. */
const FAKE_TILE = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  'base64',
);

/** Stub OSM tiles so cache assertions never depend on external network. */
async function stubTiles(page: Page) {
  await page.route('**/tile.openstreetmap.org/**', (r) =>
    r.fulfill({ contentType: 'image/png', body: FAKE_TILE }),
  );
}

/** Wait until the service worker is active (registered + activated). */
async function waitForSwReady(page: Page): Promise<void> {
  await page.waitForFunction(() =>
    navigator.serviceWorker
      .getRegistration('/sw.js')
      .then((r) => r?.active != null),
  );
}

/** Reload so the SW controls the page (controller set on next navigation). */
async function ensureSwControls(page: Page): Promise<void> {
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForFunction(() => navigator.serviceWorker.controller != null);
}

async function cacheSummary(page: Page) {
  return page.evaluate(async () => {
    const out: Record<string, string[]> = {};
    for (const name of await caches.keys()) {
      const c = await caches.open(name);
      const keys = await c.keys();
      out[name] = keys.map((r) => r.url);
    }
    return out;
  });
}

test.describe('PWA light', () => {
  test('service worker registers and takes control', async ({ page }) => {
    const swEvents: string[] = [];
    page.on('console', (m) => {
      if (m.text().includes('serviceWorker') || m.text().includes('Service worker')) {
        swEvents.push(`[console] ${m.text()}`);
      }
    });
    await page.goto('/');
    await waitForSwReady(page);
    // Give the SW a moment to settle, then dump ALL registrations.
    await page.waitForTimeout(1500);
    const reg = await page.evaluate(async () => {
      const regs = await navigator.serviceWorker.getRegistrations();
      return {
        all: regs.map((r) => ({
          scope: r.scope,
          active: r.active?.state ?? null,
          installing: r.installing?.state ?? null,
          waiting: r.waiting?.state ?? null,
        })),
        controller: navigator.serviceWorker.controller?.scriptURL ?? null,
        swInNavigator: 'serviceWorker' in navigator,
        isSecure: window.isSecureContext,
        readyState: await Promise.race([
          navigator.serviceWorker.ready.then(() => 'resolved'),
          new Promise((res) => setTimeout(() => res('timeout'), 2000)),
        ]),
      };
    });
    expect(reg.all.length, `${JSON.stringify(reg)} | swEvents: ${swEvents.join(' ; ')}`).toBeGreaterThan(0);
    expect(reg.all.some((r) => r.active === 'activated'), JSON.stringify(reg)).toBe(true);
    expect(reg.all[0]?.scope).toMatch(/\/$/);

    // Second load must be controlled by the SW (clientsClaim).
    await ensureSwControls(page);
    const controlled = await page.evaluate(() => navigator.serviceWorker.controller != null);
    expect(controlled).toBe(true);
  });

  test('installability: manifest link + icons resolve', async ({ page }) => {
    await page.goto('/');

    // Next injects the manifest link when src/app/manifest.ts exists.
    const manifestHref = await page
      .locator('link[rel="manifest"]')
      .getAttribute('href');
    expect(manifestHref).toBe('/manifest.webmanifest');

    const resp = await page.request.get(manifestHref!);
    expect(resp.ok()).toBe(true);
    const manifest = (await resp.json()) as {
      name: string;
      short_name: string;
      display: string;
      start_url: string;
      icons: { src: string; sizes: string; purpose?: string }[];
    };
    expect(manifest.name).toBe('UndePescuim');
    expect(manifest.display).toBe('standalone');
    expect(manifest.start_url).toBe('/');

    // Every declared icon must resolve as a real PNG.
    expect(manifest.icons.length).toBeGreaterThanOrEqual(3);
    for (const icon of manifest.icons) {
      const iconResp = await page.request.get(icon.src);
      expect(iconResp.ok(), `icon ${icon.src} should resolve`).toBe(true);
      expect(iconResp.headers()['content-type']).toMatch(/image\/png/);
    }

    // iOS meta tags. Next 16 emits the modern name (mobile-web-app-capable),
    // legacy iOS also reads apple-mobile-web-app-capable — accept either.
    await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveCount(1);
    await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute(
      'content',
      '#171717',
    );
    const capabilityMeta = page.locator(
      'meta[name="mobile-web-app-capable"], meta[name="apple-mobile-web-app-capable"]',
    );
    await expect(capabilityMeta).toHaveAttribute('content', 'yes');
  });

  test('last updated freshness is visible in the header', async ({ page }, testInfo) => {
    await page.goto('/');
    await waitForMapReady(page);
    const chip = page.getByTestId(Selectors.lastUpdated);
    await expect(chip).toBeVisible();
    // Intl 'ro-RO' emits e.g. "17 aug. 2026" (abbreviated month + period).
    // The visible date is the mandate — on <sm the full "Date actualizate:"
    // prefix is hidden to fit the compact header, so assert the date for all
    // viewports and the full label only where it renders (sm+).
    await expect(chip).toContainText(/\d{1,2} \w+\.? \d{4}/);
    if (testInfo.project.name !== 'mobile') {
      await expect(chip).toContainText(/Date actualizate:/);
    }
  });

  test('offline reload serves shell + data from the SW cache', async ({ page }) => {
    await stubTiles(page);

    // First visit ONLINE: SW registers, data fetches populate app-data.
    await page.goto('/');
    await waitForSwReady(page);
    await waitForMapReady(page);

    // Second load is CONTROLLED by the SW (clientsClaim claims the page on
    // activation; the reload makes the controller observable) — this pass also
    // warms the cache via the SW's own network-first handler.
    await ensureSwControls(page);
    await waitForMapReady(page);

    // The data cache must have been populated.
    const onlineCaches = await cacheSummary(page);
    const dataCache = Object.keys(onlineCaches).find((n) => n.includes('app-data'));
    expect(dataCache, 'app-data cache should exist after online visit').toBeTruthy();
    const dataUrls = onlineCaches[dataCache!] ?? [];
    expect(dataUrls.some((u) => u.includes('/data/waters.json'))).toBe(true);

    // GO OFFLINE and reload — shell (precache) + data (app-data) must render.
    // CDP setOffline blocks network but does NOT flip navigator.onLine on
    // SW-served navigations; a real device going offline does. Emulate the
    // device state too so the banner (which reads navigator.onLine) renders.
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => false });
    });
    await page.context().setOffline(true);
    await page.reload({ waitUntil: 'domcontentloaded' }).catch((e) => {
      throw new Error(`offline reload failed: ${e.message.slice(0, 120)}`);
    });
    await waitForMapReady(page);

    const probe = await page.evaluate(() => ({
      onLine: navigator.onLine,
      bannerInDom: !!document.querySelector('[data-testid="offline-banner"]'),
      lastUpdatedChip: document.querySelector('[data-testid="last-updated"]')?.textContent ?? null,
    }));
    console.log('[pwa] offline probe:', JSON.stringify(probe));

    // Offline banner must be visible with the data date.
    await expect(page.getByTestId(Selectors.offlineBanner)).toBeVisible();
    await expect(page.getByTestId(Selectors.offlineBanner)).toContainText(
      /Fără conexiune/,
    );
    await page.context().setOffline(false);
  });

  test('visited tiles are cached with a 7-day TTL (no prefetch)', async ({ page }) => {
    await stubTiles(page);
    await page.goto('/');
    await waitForSwReady(page);
    await waitForMapReady(page);
    // IMPORTANT: tiles are only cached for CONTROLLED pages (fetch events only
    // fire for clients the SW controls). The first load registers but does not
    // control the page — reload once so the SW intercepts the tiles.
    await ensureSwControls(page);
    await waitForMapReady(page);

    // Let the controlled page load + cache its initial viewport tiles.
    await page.waitForFunction(async () => {
      const c = await caches.open('osm-tiles');
      return (await c.keys()).length > 0;
    });

    const summary = await cacheSummary(page);
    const tileUrls = summary['osm-tiles'] ?? [];
    expect(tileUrls.length).toBeGreaterThan(0);
    expect(tileUrls.every((u) => u.includes('tile.openstreetmap.org'))).toBe(true);

    // TTL: the deployed sw.js must carry the 7-day expiration (604800 s) for
    // the osm-tiles tier — the ExpirationPlugin enforces it at read time.
    const swText = await page.evaluate(() =>
      fetch('/sw.js').then((r) => r.text()),
    );
    expect(swText).toContain('604800');
    expect(swText).toContain('osm-tiles');

    // NO prefetch: the precache manifest must not contain any OSM tile URLs.
    const precacheKeys = Object.keys(summary).filter((n) => n.includes('precache'));
    for (const name of precacheKeys) {
      expect(summary[name].some((u) => u.includes('tile.openstreetmap.org'))).toBe(false);
    }

    // POST /api/report is NOT cached: serwist's default handler is
    // network-only for non-GET, and no runtime rule matches the POST — the
    // report-flow e2e (flows/report.spec.ts) exercises the real POST against
    // this same server, so interception would show up there. Here we only
    // assert the SW carries the tile TTL tier (done above).
  });
});
