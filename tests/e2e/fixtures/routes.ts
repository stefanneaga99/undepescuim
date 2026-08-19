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
  await page.route('**/data/association_locations.json', (r) =>
    r.fulfill({ json: { schemaVersion: 1, locations: seed.associations.flatMap((association) => association.locations ?? []) } }),
  );
  await page.route('**/data/waters.json', (r) => r.fulfill({ json: seed.waters }));
  await page.route('**/data/uncontracted_rivers.json', (r) => r.fulfill({ json: seed.rivers }));
  await page.route('**/data/uncontracted_lakes.json', (r) => r.fulfill({ json: seed.lakes }));
  // P1 §4.5: first-paint awaits the "majors" subset of the uncontracted pool.
  // The seed's uncontracted waters are a handful already below the zoom-7 LOD
  // threshold, so serve the full seed pool as the majors response — identical
  // net effect to the old single background load (all uncontracted present).
  await page.route('**/data/uncontracted_majors.json', (r) =>
    r.fulfill({ json: [...seed.rivers, ...seed.lakes] }),
  );
  await page.route('**/data/counties.geojson', (r) => r.fulfill({ json: seed.counties }));
  // Tile hosts — the map draws vector data regardless; tiles are scenery.
  await page.route('**/tile.openstreetmap.org/**', (r) =>
    r.fulfill({ contentType: 'image/png', body: TRANSPARENT_PNG }),
  );
  // No favicon in this app — a 404 would trip the smoke console-error gate.
  await page.route('**/favicon.ico', (r) => r.fulfill({ status: 204 }));
}