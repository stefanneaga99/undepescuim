import { test, expect } from '@playwright/test';

const accepted = {
  type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'LineString', coordinates: [[25.5, 45.9], [25.6, 46.0]] }, properties: {
    slug: 'pilot-control', pilotStatus: 'accepted-reviewed', confidence: 'reviewed-physical-course', osmIds: ['way/123'], geometryHash: 'fixture-hash', sourceUrl: 'https://www.openstreetmap.org/way/123', snapshotSha256: '1234567890abcdef', legalContractGeometry: false,
  } }],
};
const ledger = { records: [{ slug: 'pilot-control', geometryHash: 'fixture-hash', osm: { ways: [123] }, review: { status: 'ACCEPTED_REVIEWED' } }, { slug: 'negative-control', review: { status: 'UNRESOLVED_INSUFFICIENT_EVIDENCE' } }] };

async function fixture(page: import('@playwright/test').Page) {
  await page.route('**/pilot/geofabrik/accepted_geometry.geojson', (route) => route.fulfill({ json: accepted }));
  await page.route('**/pilot/geofabrik/pilot_ledger.json', (route) => route.fulfill({ json: ledger }));
  await page.route('**/tile.openstreetmap.org/**', (route) => route.abort());
}

test.describe('isolated Geofabrik preview', () => {
  test('renders reviewed geometry and explicit non-legal provenance', async ({ page }) => {
    await fixture(page);
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/pilot/geofabrik');
    await expect(page.getByTestId('pilot-experimental-badge')).toBeVisible();
    await expect(page.getByText(/not legal contract\/ownership\/endpoints/i)).toBeVisible();
    await expect(page.locator('[data-pilot-slug="pilot-control"]')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('root route never loads pilot assets', async ({ page }) => {
    const pilotRequests: string[] = [];
    page.on('request', (request) => { if (request.url().includes('/pilot/geofabrik/')) pilotRequests.push(request.url()); });
    await page.goto('/');
    await page.waitForTimeout(1000);
    expect(pilotRequests).toEqual([]);
    await expect(page.getByTestId('pilot-experimental-badge')).toHaveCount(0);
  });
});
