# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: data-contract/data-integrity.spec.ts >> data contract — real served /public/data @data >> associations.json parses with required fields
- Location: tests/e2e/specs/data-contract/data-integrity.spec.ts:78:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Test source

```ts
  1   | /**
  2   |  * Data-contract tier — assertions against the REAL served /public/data
  3   |  * (docs/e2e-test-plan.md §6.2). NO route interception: this is where seed
  4   |  * drift is caught and the 28 legacy data-integrity `_e2e_*.mjs` checks live.
  5   |  *
  6   |  * Tagged @data → excluded from the PR e2e job (--grep-invert @data), run on
  7   |  * main / nightly / manual (see .github/workflows/playwright.yml).
  8   |  *
  9   |  * Port mapping: the legacy `_e2e_*.mjs` scripts are superseded per-flow —
  10  |  * see docs/e2e-test-plan.md §2 inventory (data-shape assertions consolidated
  11  |  * here; UI assertions live in specs/flows + specs/regression).
  12  |  */
  13  | import { test, expect } from '@playwright/test';
  14  | 
  15  | const WATERS_URL = '/data/waters.json';
  16  | 
  17  | async function fetchJson(page: import('@playwright/test').Page, url: string): Promise<unknown> {
  18  |   const resp = await page.request.get(url);
  19  |   expect(resp.ok(), `GET ${url}`).toBeTruthy();
  20  |   return resp.json();
  21  | }
  22  | 
  23  | function countyKey(county: string): string {
  24  |   return county
  25  |     .toLowerCase()
  26  |     .normalize('NFD')
  27  |     .replace(/[\u0300-\u036f]/g, '')
  28  |     .replace(/[\s-]+/g, '');
  29  | }
  30  | 
  31  | test.describe('data contract — real served /public/data @data', () => {
  32  |   test('waters.json parses and matches the Water shape', async ({ page }) => {
  33  |     const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
  34  |     expect(Array.isArray(waters)).toBe(true);
  35  |     expect(waters.length).toBeGreaterThan(400);
  36  | 
  37  |     for (const w of waters.slice(0, 300)) {
  38  |       expect(typeof w.slug).toBe('string');
  39  |       expect(String(w.name).length).toBeGreaterThan(0);
  40  |       expect(['lac', 'rau']).toContain(w.subtype);
  41  |       expect(typeof w.judet).toBe('string');
  42  |       expect(Array.isArray(w.bbox)).toBe(true);
  43  |       const g = w.geometry as { type?: string; coordinates?: unknown[] } | undefined;
  44  |       if (g) {
  45  |         expect(['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']).toContain(g.type);
  46  |         expect((g.coordinates?.length ?? 0)).toBeGreaterThan(0);
  47  |       }
  48  |     }
  49  |   });
  50  | 
  51  |   test('sweep-fixed fixtures carry real geometry, not bbox fallbacks', async ({ page }) => {
  52  |     const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
  53  |     const byName = new Map(waters.map((w) => [String(w.name).toLowerCase(), w]));
  54  | 
  55  |     // t_a0e123da (Valea Pojorâtei), t_e3ae3121 (sebes family)
  56  |     for (const probe of ['valea pojorâtei', 'râul sebesul mijlociu']) {
  57  |       const w = byName.get(probe);
  58  |       expect(w, `fixture ${probe} present in waters.json`).toBeTruthy();
  59  |       const g = (w as Record<string, unknown>).geometry as { type?: string } | undefined;
  60  |       expect(g, `${probe} has real geometry`).toBeTruthy();
  61  |       expect(g?.type).toMatch(/LineString/);
  62  |     }
  63  |   });
  64  | 
  65  |   test('county attribution: geometryByCounty always keyed by the water own county', async ({
  66  |     page,
  67  |   }) => {
  68  |     const waters = (await fetchJson(page, WATERS_URL)) as Array<Record<string, unknown>>;
  69  |     const withClips = waters.filter((w) => w.geometryByCounty);
  70  |     expect(withClips.length).toBeGreaterThan(100);
  71  | 
  72  |     for (const w of withClips.slice(0, 200)) {
  73  |       const ownKey = countyKey(String(w.judet));
  74  |       expect((w.geometryByCounty as Record<string, unknown>), `own-county clip for ${w.slug}`).toHaveProperty(ownKey);
  75  |     }
  76  |   });
  77  | 
  78  |   test('associations.json parses with required fields', async ({ page }) => {
  79  |     const assoc = (await fetchJson(page, '/data/associations.json')) as Array<Record<string, unknown>>;
  80  |     expect(assoc.length).toBeGreaterThan(80);
  81  |     for (const a of assoc.slice(0, 96)) {
  82  |       expect(typeof a.slug).toBe('string');
  83  |       expect(String(a.name).length).toBeGreaterThan(0);
> 84  |       expect(Array.isArray(a.bbox) || a.bbox === null).toBe(true);
      |                                                        ^ Error: expect(received).toBe(expected) // Object.is equality
  85  |       expect(typeof a.ape).toBe('number');
  86  |     }
  87  |     // spot-check the two canonical reciprocity regimes exist
  88  |     expect(assoc.some((a) => a.reciprocity === 'confirmată')).toBe(true);
  89  |     expect(assoc.some((a) => a.reciprocity === 'neconfirmată')).toBe(true);
  90  |   });
  91  | 
  92  |   test('uncontracted overlays parse and are tagged uncontracted', async ({ page }) => {
  93  |     const rivers = (await fetchJson(page, '/data/uncontracted_rivers.json')) as Array<Record<string, unknown>>;
  94  |     const lakes = (await fetchJson(page, '/data/uncontracted_lakes.json')) as Array<Record<string, unknown>>;
  95  |     expect(rivers.length).toBeGreaterThan(500);
  96  |     expect(lakes.length).toBeGreaterThan(500);
  97  |     for (const w of [...rivers.slice(0, 100), ...lakes.slice(0, 100)]) {
  98  |       expect(w.uncontracted).toBe(true);
  99  |       expect(w.asociatie).toBeNull();
  100 |       expect(['lac', 'rau']).toContain(w.subtype);
  101 |     }
  102 |   });
  103 | 
  104 |   test('counties.geojson is a valid FeatureCollection covering the counties', async ({
  105 |     page,
  106 |   }) => {
  107 |     const fc = (await fetchJson(page, '/data/counties.geojson')) as {
  108 |       type: string;
  109 |       features: Array<{ properties: { name: string } }>;
  110 |     };
  111 |     expect(fc.type).toBe('FeatureCollection');
  112 |     const names = fc.features.map((f) => f.properties.name);
  113 |     expect(names.length).toBeGreaterThanOrEqual(40);
  114 |     for (const probe of ['Cluj', 'Ilfov', 'Iași', 'Brașov']) {
  115 |       expect(names).toContain(probe);
  116 |     }
  117 |   });
  118 | });
```