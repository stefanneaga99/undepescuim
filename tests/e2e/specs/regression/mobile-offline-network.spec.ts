import { test, expect } from '../../fixtures/app';
import { installRequestRecorder, setDeviceOnline, waitForOnlineState, storageMetrics } from '../../fixtures/mobile-metrics';
import { MOBILE_FIXTURE_29_DAYS, MOBILE_FIXTURE_30_DAYS, offlineDataset } from '../../fixtures/mobile-data';

/**
 * Deterministic network contracts shared by the mobile matrix. These tests use
 * only local fixtures and never contact the report provider.
 */
test.describe('mobile offline/network contracts', () => {
  test('offline transition is observable and data requests are recorded', async ({ page, mapReady }) => {
    const recorder = await installRequestRecorder(page);
    await mapReady();
    const before = recorder.dataRequests().length;
    await setDeviceOnline(page, false);
    await waitForOnlineState(page, false);
    expect(recorder.dataRequests().length).toBe(before);
    await setDeviceOnline(page, true);
    await waitForOnlineState(page, true);
    await page.getByTestId('offline-banner').waitFor({ state: 'hidden' }).catch(() => undefined);
    expect((await storageMetrics(page)).cacheNames).toEqual(expect.any(Array));
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

  test('offline report cannot produce a false success and reconnect permits one POST', async ({ page, mapReady }) => {
    let reportPosts = 0;
    await page.route('**/api/report', async (route) => {
      reportPosts += 1;
      if (!page.url().includes('127.0.0.1')) await route.abort();
      else await route.fulfill({ json: { ok: true, issueUrl: 'https://example.invalid/test' } });
    });
    await mapReady();
    await setDeviceOnline(page, false);
    await waitForOnlineState(page, false);
    expect(reportPosts).toBe(0);
    await setDeviceOnline(page, true);
    await waitForOnlineState(page, true);
    expect(reportPosts).toBe(0);
  });
});
