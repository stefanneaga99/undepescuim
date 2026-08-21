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
import sameDayLedger from '../../../fixtures/same_day_regression_ledger.json';

const WATERS_URL = '/data/waters.json';

type RegressionEntry = {
  id: string;
  description: string;
  category: string;
  test?: string;
  status?: string;
  issueKey?: string | null;
  comment?: string;
  dataPath?: string;
  slugs?: string[];
  names?: Record<string, string>;
  county?: string;
  counties?: Record<string, string>;
  geometryTypes?: string[];
};

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
  test('same-day regression ledger is complete and geometry probes are explicit', async ({ page }) => {
    const ledger = sameDayLedger as RegressionEntry[];
    expect(ledger).toHaveLength(18);
    expect(new Set(ledger.map((entry) => entry.id)).size).toBe(18);
    expect(ledger.filter((entry) => entry.status === 'PENDING')).toHaveLength(1);
    const pending = ledger.find((entry) => entry.status === 'PENDING');
    expect(pending).toMatchObject({ category: 'unknown', issueKey: null });
    expect(pending?.comment).toContain('original bug issue key');
    expect(ledger.filter((entry) => entry.status !== 'PENDING').every((entry) => (entry.test?.length ?? 0) > 0)).toBe(true);

    const geometryEntries = ledger.filter((entry) => entry.category === 'geometry');
    expect(geometryEntries).toHaveLength(5);
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const bySlug = new Map(waters.map((water) => [String(water.slug), water]));

    for (const entry of geometryEntries) {
      expect(entry.dataPath).toBe('waters.json');
      for (const slug of entry.slugs ?? []) {
        const water = bySlug.get(slug);
        expect(water, `${entry.id}: ${slug} present in waters.json`).toBeTruthy();
        expect(water?.name, `${entry.id}: ${slug} exact name mapping`).toBe(entry.names?.[slug]);
        expect(water?.judet).toBe(entry.counties?.[slug] ?? entry.county);
        const geometry = water?.geometry as
          | { type?: string; coordinates?: unknown }
          | null
          | undefined;
        expect(geometry, `${entry.id}: ${slug} has real geometry`).toBeTruthy();
        expect(entry.geometryTypes).toContain(geometry?.type);
        // A bbox alone is not a geometry regression fix: coordinates must be
        // present and non-empty for every explicitly mapped water.
        expect(Array.isArray(geometry?.coordinates)).toBe(true);
        expect((geometry?.coordinates as unknown[]).length).toBeGreaterThan(0);
        expect(water?._bboxFallback, `${entry.id}: ${slug} must not use bbox fallback`).not.toBe(true);
      }
    }
  });

  test('waters.json parses and matches the Water shape', async ({ page }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    expect(Array.isArray(waters)).toBe(true);
    expect(waters.length).toBeGreaterThan(400);

    for (const w of waters.slice(0, 300)) {
      expect(typeof w.slug).toBe('string');
      expect(String(w.name).length).toBeGreaterThan(0);
      expect(['lac', 'rau']).toContain(w.subtype);
      expect(typeof w.judet).toBe('string');
      // bbox is OPTIONAL and nullable: river-group sector waters (no own
      // geometry) carry `riverGroup` + `course_frac` instead and emit either
      // `bbox: null` or no bbox key at all (WaterFeatureLayer.tsx:179).
      expect(w.bbox == null || Array.isArray(w.bbox)).toBe(true);
      const g = w.geometry as { type?: string; coordinates?: unknown[] } | undefined;
      if (g) {
        expect(['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']).toContain(g.type);
        expect((g.coordinates?.length ?? 0)).toBeGreaterThan(0);
      }
    }
  });

  test('Târnava Mare mijlocie preserves the contract while endpoints remain unproven', async ({ page }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const selected = waters.find((water) => water.slug === 'anpa-anpa-0333');
    expect(selected).toMatchObject({
      slug: 'anpa-anpa-0333',
      name: 'Râul Târnava Mare mijlocie',
      judet: 'Harghita',
      dimensiune: '5 Km',
      limite: 'Aval baraj lac Zetea – pod Desag',
      riverGroup: 'tarnava-mare',
      course_frac: 0.1072,
      referinta: 'Contract 46/15.01.2018 (2018-01-15)',
    });
    // course_frac is only a fallback location. It must not be promoted to a
    // contractual endpoint until first-party evidence supplies both bounds.
    expect(selected?.sectorStart).toBeUndefined();
    expect(selected?.sectorEnd).toBeUndefined();
  });

  test('sweep-fixed fixtures carry real geometry, not bbox fallbacks', async ({ page }) => {
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const bySlug = new Map(waters.map((w) => [w.slug, w]));

    // t_a0e123da (Valea Pojorâtei), t_e3ae3121 (sebes family) — probed by
    // SLUG: the by-name lookup is ambiguous now that a Romsilva-administered
    // 'Râul Sebesul Mijlociu' (romsilva-alba-sebesul-mijlociu, no geometry,
    // bbox fallback) exists alongside the sweep-fixed family.
    for (const probe of ['anpa-anpa-0188', 'qsvhz93s', 'f02xtxw1', 'uyzo7o3j']) {
      const w = bySlug.get(probe);
      expect(w, `fixture ${probe} present in waters.json`).toBeTruthy();
      const g = (w as Record<string, unknown>).geometry as { type?: string } | undefined;
      expect(g, `${probe} has real geometry`).toBeTruthy();
      expect(g?.type).toMatch(/LineString/);
    }
  });

  test('county attribution: clips live in waters_county_clips.json keyed by the water own county', async ({
    page,
  }) => {
    // P0 §4.2: geometryByCounty was split OUT of waters.json into
    // public/data/waters_county_clips.json (lazy on county activation).
    const clips = (await fetchJson(page, '/data/waters_county_clips.json')) as Record<
      string,
      Record<string, unknown>
    >;
    const slugs = Object.keys(clips);
    expect(slugs.length).toBeGreaterThan(100);
    // Map each clip owner back to its water to check the OWN-county key rule.
    const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
    const bySlug = new Map(waters.map((w) => [String(w.slug), w]));
    let checked = 0;
    for (const slug of slugs) {
      if (checked >= 200) break;
      const w = bySlug.get(slug);
      if (!w) continue; // uncontracted slugs (unc-*) aren't in waters.json
      checked += 1;
      const ownKey = countyKey(String(w.judet));
      expect(clips[slug], `own-county clip for ${slug}`).toHaveProperty(ownKey);
    }
    expect(checked).toBeGreaterThan(50);
    // waters.json itself carries NO inline clips (split).
    expect(waters.some((w) => (w as Record<string, unknown>).geometryByCounty)).toBe(false);
    // Both pools present: contracted slugs + uncontracted (unc-*) slugs.
    expect(slugs.some((s) => s.startsWith('unc-'))).toBe(true);
  });

  test('associations.json parses with required fields', async ({ page }) => {
    const assoc = (await fetchJson(page, '/data/associations.json')) as Array<Record<string, unknown>>;
    expect(assoc.length).toBeGreaterThan(80);
    for (const a of assoc.slice(0, 96)) {
      expect(typeof a.slug).toBe('string');
      expect(String(a.name).length).toBeGreaterThan(0);
      // bbox is OPTIONAL: absent, null (no geocoded region), or a BBox tuple.
      // MapView.tsx guards `!assoc.bbox` → skip zoom for these associations.
      expect(a.bbox == null || Array.isArray(a.bbox)).toBe(true);
      expect(typeof a.ape).toBe('number');
      // reciprocity is a closed enum; 'neconfirmată' is the documented default
      // (AssociationValidity.tsx) and the current real dataset has no confirmed
      // one — assert membership, not presence of a particular regime.
      expect(a.reciprocity === undefined || a.reciprocity === 'confirmată' || a.reciprocity === 'neconfirmată').toBe(true);
    }
    expect(assoc.some((a) => a.reciprocity === 'neconfirmată')).toBe(true);
  });

  test('uncontracted overlays parse and are tagged uncontracted', async ({ page }) => {
    const rivers = (await fetchJson(page, '/data/uncontracted_rivers.json')) as Array<Record<string, unknown>>;
    const lakes = (await fetchJson(page, '/data/uncontracted_lakes.json')) as Array<Record<string, unknown>>;
    expect(rivers.length).toBeGreaterThan(500);
    expect(lakes.length).toBeGreaterThan(500);
    for (const w of [...rivers.slice(0, 100), ...lakes.slice(0, 100)]) {
      expect(w.uncontracted).toBe(true);
      // The overlay builder omits the `asociatie` key entirely (undefined) —
      // the app treats undefined and null identically (`w.asociatie` falsy).
      expect(w.asociatie == null).toBe(true);
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