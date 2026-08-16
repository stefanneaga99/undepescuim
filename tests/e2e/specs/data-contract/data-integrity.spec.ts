/**
 * Data-contract tier — assertions against the REAL served /public/data
 * (docs/e2e-test-plan.md §6.2). NO route interception: this is where seed
 * drift is caught and the 28 legacy data-integrity `_e2e_*.mjs` checks live.
 *
 * Tagged @data → excluded from the PR e2e job (--grep-invert @data), run on
 * main / nightly / manual (see .github/workflows/playwright.yml).
 *
 * Port mapping: the legacy `_e2e_*.mjs` scripts are superseded per-flow —
 * see docs/e2e-test-plan.md §2 inventory (data-shape assertions consolidated
 * here; UI assertions live in specs/flows + specs/regression).
 */
import { test, expect } from '@playwright/test';

const WATERS_URL = '/data/waters.json';

async function fetchJson(page: import('@playwright/test').Page, url: string): Promise<unknown> {
  const resp = await page.request.get(url);
  expect(resp.ok(), `GET ${url}`).toBeTruthy();
  return resp.json();
}

function countyKey(county: string): string {
  return county
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\s-]+/g, '');
}

test.describe('data contract — real served /public/data @data', () => {
  test('waters.json parses and matches the Water shape', async ({ page }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    expect(Array.isArray(waters)).toBe(true);
    expect(waters.length).toBeGreaterThan(400);

    for (const w of waters.slice(0, 300)) {
      expect(typeof w.slug).toBe('string');
      expect(String(w.name).length).toBeGreaterThan(0);
      expect(['lac', 'rau']).toContain(w.subtype);
      expect(typeof w.judet).toBe('string');
      expect(Array.isArray(w.bbox)).toBe(true);
      const g = w.geometry as { type?: string; coordinates?: unknown[] } | undefined;
      if (g) {
        expect(['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']).toContain(g.type);
        expect((g.coordinates?.length ?? 0)).toBeGreaterThan(0);
      }
    }
  });

  test('sweep-fixed fixtures carry real geometry, not bbox fallbacks', async ({ page }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const byName = new Map(waters.map((w) => [String(w.name).toLowerCase(), w]));

    // t_a0e123da (Valea Pojorâtei), t_e3ae3121 (sebes family)
    for (const probe of ['valea pojorâtei', 'râul sebesul mijlociu']) {
      const w = byName.get(probe);
      expect(w, `fixture ${probe} present in waters.json`).toBeTruthy();
      const g = (w as Record<string, unknown>).geometry as { type?: string } | undefined;
      expect(g, `${probe} has real geometry`).toBeTruthy();
      expect(g?.type).toMatch(/LineString/);
    }
  });

  test('county attribution: geometryByCounty always keyed by the water own county', async ({
    page,
  }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const withClips = waters.filter((w) => w.geometryByCounty);
    expect(withClips.length).toBeGreaterThan(100);

    for (const w of withClips.slice(0, 200)) {
      const ownKey = countyKey(String(w.judet));
      expect((w.geometryByCounty as Record<string, unknown>), `own-county clip for ${w.slug}`).toHaveProperty(ownKey);
    }
  });

  test('associations.json parses with required fields', async ({ page }) => {
    const assoc = (await fetchJson(page, '/data/associations.json')) as Array<Record<string, unknown>>;
    expect(assoc.length).toBeGreaterThan(80);
    for (const a of assoc.slice(0, 96)) {
      expect(typeof a.slug).toBe('string');
      expect(String(a.name).length).toBeGreaterThan(0);
      expect(Array.isArray(a.bbox) || a.bbox === null).toBe(true);
      expect(typeof a.ape).toBe('number');
    }
    // spot-check the two canonical reciprocity regimes exist
    expect(assoc.some((a) => a.reciprocity === 'confirmată')).toBe(true);
    expect(assoc.some((a) => a.reciprocity === 'neconfirmată')).toBe(true);
  });

  test('uncontracted overlays parse and are tagged uncontracted', async ({ page }) => {
    const rivers = (await fetchJson(page, '/data/uncontracted_rivers.json')) as Array<Record<string, unknown>>;
    const lakes = (await fetchJson(page, '/data/uncontracted_lakes.json')) as Array<Record<string, unknown>>;
    expect(rivers.length).toBeGreaterThan(500);
    expect(lakes.length).toBeGreaterThan(500);
    for (const w of [...rivers.slice(0, 100), ...lakes.slice(0, 100)]) {
      expect(w.uncontracted).toBe(true);
      expect(w.asociatie).toBeNull();
      expect(['lac', 'rau']).toContain(w.subtype);
    }
  });

  test('counties.geojson is a valid FeatureCollection covering the counties', async ({
    page,
  }) => {
    const fc = (await fetchJson(page, '/data/counties.geojson')) as {
      type: string;
      features: Array<{ properties: { name: string } }>;
    };
    expect(fc.type).toBe('FeatureCollection');
    const names = fc.features.map((f) => f.properties.name);
    expect(names.length).toBeGreaterThanOrEqual(40);
    for (const probe of ['Cluj', 'Ilfov', 'Iași', 'Brașov']) {
      expect(names).toContain(probe);
    }
  });
});