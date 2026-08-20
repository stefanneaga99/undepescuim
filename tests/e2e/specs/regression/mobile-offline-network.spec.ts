import { test, expect } from '../../fixtures/app';
import {
  attachMobileMetrics,
  installRequestRecorder,
  setDeviceOnline,
  storageMetrics,
  transitionLatency,
  waitForOnlineState,
} from '../../fixtures/mobile-metrics';
import {
  CACHE_REGIONS,
  MOBILE_TILE_CACHE_LIMIT,
  MOBILE_FIXTURE_29_DAYS,
  MOBILE_FIXTURE_30_DAYS,
  offlineDataset,
  seedVisitedTileCache,
  clearVisitedTileCache,
  tileCacheSnapshot,
} from '../../fixtures/mobile-data';

/** Deterministic network contracts shared by the mobile matrix. */
test.describe('mobile offline/network contracts', () => {
  test('offline/reconnect transitions meet provisional latency budgets', async ({ page, mapReady }, testInfo) => {
    const recorder = await installRequestRecorder(page);
    await mapReady();
    const dataBeforeOffline = recorder.dataRequests().length;
    const offlineMs = await transitionLatency(page, false);
    expect(recorder.dataRequests().length).toBe(dataBeforeOffline);
    expect(offlineMs).toBeLessThanOrEqual(1000);

    const reconnectMs = await transitionLatency(page, true);
    expect(reconnectMs).toBeLessThanOrEqual(3000);
    await page.getByTestId('offline-banner').waitFor({ state: 'hidden' }).catch(() => undefined);
    expect((await storageMetrics(page)).cacheNames).toEqual(expect.any(Array));
    await attachMobileMetrics(page, testInfo, recorder);
  });

  test('staleness fixtures have an exact 29/30-day boundary', async ({ page }) => {
    await page.goto('/');
    const result = await page.evaluate(({ old, boundary }) => {
      const age = (value: string) => Date.parse('2026-08-20T12:00:00.000Z') - Date.parse(value);
      const threshold = 30 * 24 * 60 * 60 * 1000;
      return { old: age(old), boundary: age(boundary), threshold };
    }, { old: MOBILE_FIXTURE_29_DAYS, boundary: MOBILE_FIXTURE_30_DAYS });
    expect(result.old).toBeLessThan(result.threshold);
    expect(result.boundary).toBe(result.threshold);
    expect(offlineDataset(MOBILE_FIXTURE_30_DAYS).dataUpdatedAt).toBe(MOBILE_FIXTURE_30_DAYS);
  });

  test('cache fixture contains only visited regions and reports growth', async ({ page, mapReady }) => {
    await mapReady();
    await clearVisitedTileCache(page);
    await seedVisitedTileCache(page, ['region-01', 'region-12']);
    const snapshot = await tileCacheSnapshot(page);
    expect(snapshot.urls).toHaveLength(16);
    expect(snapshot.bytes).toBe(16 * 12);
    expect(snapshot.urls.every((url) => url.includes('/1/') || url.includes('/12/'))).toBe(true);
    expect(CACHE_REGIONS).toHaveLength(12);
  });

  test('cache fixture grows progressively and evicts oldest entries at the bound', async ({ page, mapReady }) => {
    await mapReady();
    await clearVisitedTileCache(page);
    for (const region of CACHE_REGIONS) {
      await seedVisitedTileCache(page, [region.id], { maxEntries: MOBILE_TILE_CACHE_LIMIT });
    }
    const snapshot = await tileCacheSnapshot(page);
    expect(snapshot.urls).toHaveLength(MOBILE_TILE_CACHE_LIMIT);
    expect(snapshot.urls.some((url) => url.includes('/1/'))).toBe(false);
    expect(snapshot.urls.filter((url) => url.includes('/12/'))).toHaveLength(8);
    expect(snapshot.bytes).toBe(MOBILE_TILE_CACHE_LIMIT * 12);
  });

  test('offline report cannot produce false success; reconnect permits one POST', async ({ page, mapReady }) => {
    let reportPosts = 0;
    await page.route('**/api/report', async (route) => {
      if (!await page.evaluate(() => navigator.onLine)) {
        await route.abort('failed');
        return;
      }
      reportPosts += 1;
      await route.fulfill({ json: { ok: true, issueUrl: 'https://example.invalid/test' } });
    });
    await mapReady();
    await setDeviceOnline(page, false);
    await waitForOnlineState(page, false);
    const offlineResult = await page.evaluate(() => fetch('/api/report', { method: 'POST', body: '{}' })
      .then(() => 'success' as const).catch(() => 'network-error' as const));
    expect(offlineResult).toBe('network-error');
    expect(reportPosts).toBe(0);

    await setDeviceOnline(page, true);
    await waitForOnlineState(page, true);
    const response = await page.evaluate(() => fetch('/api/report', { method: 'POST', body: '{}' }).then((r) => r.json()));
    expect(response.ok).toBe(true);
    expect(reportPosts).toBe(1);
  });
});
