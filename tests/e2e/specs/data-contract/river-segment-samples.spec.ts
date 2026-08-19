import { test, expect } from '@playwright/test';
import fixture from '../../fixtures/river-segments.json';

test.describe('offline river segment probes @data @river-segments', () => {
  test.beforeEach(async ({ page }) => {
    // The @data tier is deliberately local: no OSM, API, tile, or remote
    // fixture is allowed to make a contract assertion nondeterministic.
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname === '/data/waters.json') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(fixture),
        });
        return;
      }
      if (url.hostname !== 'localhost' && url.hostname !== '127.0.0.1') {
        await route.abort();
        return;
      }
      await route.continue();
    });
  });

  test('all mandatory findings remain explicit and blocking', async ({ page }) => {
    await page.goto('/');
    const result = await page.evaluate(async () => {
      const response = await fetch('/data/waters.json');
      return response.json();
    });
    expect(result.schema_version).toBe(1);
    expect(result.cases).toHaveLength(6);
    const byId = new Map<string, { status: string; finding_codes: string[] }>(
      result.cases.map((item: { id: string; status: string; finding_codes: string[] }) => [item.id, item]),
    );
    expect(byId.get('pass')).toMatchObject({ status: 'PASS_CONTRACTED', finding_codes: [] });
    for (const id of ['missing-segment', 'truncation', 'sector-mismatch', 'duplicate', 'tarnava-gap']) {
      expect(byId.get(id)?.status, `${id} must block`).toBe('BLOCKED');
      expect(byId.get(id)?.finding_codes.length, `${id} must report a finding`).toBeGreaterThan(0);
    }
  });

  test('fixture is served without an external request', async ({ page }) => {
    const external: string[] = [];
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (!['localhost', '127.0.0.1'].includes(url.hostname)) external.push(request.url());
    });
    await page.goto('/');
    await expect.poll(() => external.length).toBe(0);
    await expect.poll(async () => page.evaluate(() => document.readyState)).toBe('complete');
  });
});
