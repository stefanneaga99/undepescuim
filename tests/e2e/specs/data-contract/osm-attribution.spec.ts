import { test, expect } from '../../fixtures/app';

test.describe('OSM attribution and tile policy', () => {
  test('shows linked attribution on desktop and mobile map states', async ({ page, mapReady }) => {
    await mapReady();
    const attribution = page.getByTestId('map-attribution');
    await expect(attribution).toBeVisible();
    await expect(attribution.getByRole('link', { name: /openstreetmap copyright/i })).toHaveAttribute(
      'href',
      'https://www.openstreetmap.org/copyright',
    );

    await page.setViewportSize({ width: 390, height: 844 });
    await expect(attribution).toBeVisible();
    await expect(attribution).toHaveCSS('font-size', '11px');
  });

  test('requests only the HTTPS standard OSM tile endpoint with a referer', async ({ page, mapReady }) => {
    const tileRequests: Array<{ url: string; referer: string | undefined }> = [];
    page.on('request', (request) => {
      if (request.url().includes('openstreetmap.org')) {
        tileRequests.push({ url: request.url(), referer: request.headers().referer });
      }
    });

    await mapReady();
    await expect.poll(() => tileRequests.length).toBeGreaterThan(0);
    expect(tileRequests.every(({ url }) => url.startsWith('https://tile.openstreetmap.org/'))).toBe(true);
    expect(tileRequests.every(({ referer }) => Boolean(referer))).toBe(true);
  });
});
