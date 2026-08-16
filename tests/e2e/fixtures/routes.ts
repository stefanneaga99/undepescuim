/**
 * Route interception for the seeded tier (docs/e2e-test-plan.md §6.1).
 * Routes the five app data endpoints to the deterministic seed and stubs the
 * OSM tile host with a transparent 1×1 PNG so slow/blocked tiles can never
 * fail a run (plan §5.4 — assertions only ever look at the vector overlay).
 */
import type { Page } from '@playwright/test';
import type { SeedData } from './seed-data';

/** 1×1 transparent PNG (base64). */
const TRANSPARENT_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  'base64',
);

export async function routeData(page: Page, seed: SeedData): Promise<void> {
  await page.route('**/data/associations.json', (r) => r.fulfill({ json: seed.associations }));
  await page.route('**/data/waters.json', (r) => r.fulfill({ json: seed.waters }));
  await page.route('**/data/uncontracted_rivers.json', (r) => r.fulfill({ json: seed.rivers }));
  await page.route('**/data/uncontracted_lakes.json', (r) => r.fulfill({ json: seed.lakes }));
  await page.route('**/data/counties.geojson', (r) => r.fulfill({ json: seed.counties }));
  // Tile hosts — the map draws vector data regardless; tiles are scenery.
  await page.route('**/tile.openstreetmap.org/**', (r) =>
    r.fulfill({ contentType: 'image/png', body: TRANSPARENT_PNG }),
  );
}