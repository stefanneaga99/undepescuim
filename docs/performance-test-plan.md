# Performance & Load-Time Test Plan — UndePescuim.ro

> QA SPIKE (t_8810ff88) — test plan only, no implementation.
> Scope: Core Web Vitals, bundle size, data payload, map render, geolocation MVP, species/permis pages.
> Status: **proposed — pending review** (review-required block).

---

## 1. Goal

Define a repeatable, budget-backed performance gate for the UndePescuim.ro fishing map
(Next.js 16 + Leaflet + zustand). Every future task must not regress the numbers below, and
the current known hotspots (the 36 MB `waters.json` payload and un-culled contracted geometry)
must be measurable so their fixes can be proven.

**Definition of done for this spike:** the checks, budgets, tooling setup, run commands, and a
CI integration proposal below are agreed as the project's performance contract. No code changes yet.

---

## 2. Architecture summary (what is actually measured)

Load path, from `src/components/map/MapShell.tsx` + `src/stores/map-store.ts`:

1. `MapShell` mounts → `useEffect` → `loadData()`.
2. `loadData()` fires `Promise.all` of **5 fetches** and `JSON.parse`s them all on the main thread:
   `associations.json`, `waters.json`, `uncontracted_rivers.json`, `uncontracted_lakes.json`, `counties.geojson`.
3. Only when `dataLoaded === true` does `<MapView/>` replace `<MapSkeleton/>`.

**Consequence:** time-to-first-map-paint and TTI are gated behind *fetch + parse of the entire
dataset*, not just what is visible. This is the dominant risk (see §7).

Rendering:
- **Uncontracted overlay** (`UncontractedWaterLayer.tsx`) already has viewport culling + zoom LOD
  (length ≥30 km / area ≥100 ha at zoom <8). This is the "LOD/culling already exist" surface —
  the plan verifies it *actually reduces layer count*, it is not assumed.
- **Contracted layer** (`WaterFeatureLayer.tsx`) has **no culling and no LOD**. It renders the full
  1013-feature collection (including a 15,220-vertex Mureș polyline) at every zoom, **plus a second
  invisible hit-layer** (weight 16) that doubles line geometry, plus optional focus/association
  slice layers. This is the second major risk.

---

## 3. Performance surface inventory (measured 2026-08-16)

### 3.1 Static data payloads — `public/data/`

| File | Entries | Raw (MB) | Compact (MB) | gzip (MB) | Fetched by app? |
|---|---|---|---|---|---|
| `waters.json` | 1013 (714 w/ geometry) | **36.26** | 16.93 | **4.75** | yes |
| `uncontracted_rivers.json` | 4166 | 2.23 | 2.26 | 0.45 | yes |
| `uncontracted_lakes.json` | 5712 | 3.19 | 3.22 | 0.71 | yes |
| `counties.geojson` | 42 | 0.22 | 0.20 | 0.07 | yes |
| `associations.json` | ~90 | 0.04 | 0.04 | 0.01 | yes |
| `waters_geocoded.geojson` | — | 9.66 | 8.92 | 2.88 | **no (dead weight)** |
| `waters.geojson` | — | 0.16 | 0.10 | 0.02 | **no (dead weight)** |

**Client-fetched totals:** ~42 MB raw / **~6 MB gzip transferred** / **~22.6 MB JSON text parsed
on the main thread** before first paint.

`waters.json` field breakdown (why it is 36 MB):
- `geometry` — 13.96 MB (full OSM courses, un-simplified; max single feature 15,220 vertices = Râul Mureș).
- `geometryByCounty` — 3.64 MB (**redundant** per-county clips; only used when a county filter is active, yet shipped always).
- file is pretty-printed (2.14× whitespace) — 36.26 MB on disk → 16.93 MB compact.

### 3.2 Initial bundle

- Next.js 16.3.0 app-router; map island is `dynamic(ssr:false)` (Leaflet + react-leaflet v5 are
  lazily loaded). No bundle analyzer installed yet.
- Fonts: `next/font/google` Geist + Geist_Mono (self-hosted, no CLS from font swap expected).
- No `fuse.js` (stale in spike brief) — species search uses `cmdk`; ~21 species, trivial.

### 3.3 Map tile loading

- `TileLayer` → `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` (standard OSM raster).
- Zoom 7 national ≈ ~24 tiles; zoom 12 ≈ ~200+ tiles in viewport. Browser HTTP/2 + edge CDN.

### 3.4 Geolocation MVP

- `use-geolocation.ts`: one-shot `getCurrentPosition` (no `watchPosition`).
- `applyUserPosition` → `nearestWaters` = linear scan + sort over 1013 waters (fine at 1k, <1 ms),
  then `nearbyCounty` point-in-ring over 42 counties per nearby water (cheap).
- No spatial index needed at current scale — verify, don't over-engineer.

### 3.5 Species / Permis pages

- `/specii` and `/permis` are server-rendered static content (`src/content/*.ts`, 198 + 224 lines).
- Low risk. Only checks: no layout shift, no layout-thrashing scroll on `scrollIntoView`.

---

## 4. Metrics & budgets (PASS / FAIL)

Reference device tiers (Web Vitals convention):
- **Mobile**: Moto G Power (2019 class) or equivalent — Lighthouse "mobile" emulation, CPU 4× throttle, network "Fast 3G" (1.6 Mbps / 150 ms RTT).
- **Desktop**: Lighthouse "desktop" emulation, no throttle (used only as a sanity bound).

| # | Metric | Target (PASS) | Warn | FAIL | Where measured |
|---|---|---|---|---|---|
| M1 | **LCP** (mobile, Fast 3G) | < 2.5 s | 2.5–4.0 s | > 4.0 s | Lighthouse CI / Playwright trace |
| M2 | **INP** (mobile, p75) | < 200 ms | 200–500 ms | > 500 ms | Field (if available) / lab TBT proxy |
| M3 | **TBT** (mobile, lab) | < 200 ms | 200–600 ms | > 600 ms | Lighthouse CI |
| M4 | **CLS** | < 0.1 | 0.1–0.25 | > 0.25 | Lighthouse CI |
| M5 | CLS on filter/sheet change (targeted) | **0.00** | ≤ 0.05 | > 0.05 | Playwright `page.evaluate` CLS sampler |
| M6 | Time-to-first-map-paint (Fast 3G) | < 5.0 s | 5–10 s | > 10 s | Playwright trace / `dataLoaded` marker |
| M7 | Total data JSON transferred (gzip) | < 2.5 MB | 2.5–3.0 MB | > 3.0 MB | `curl -I` + `Content-Encoding` check / build script |
| M8 | `waters.json` gzip size | < 1.5 MB | 1.5–2.0 MB | > 2.0 MB | `gzip -9` of compact file |
| M9 | JSON text parsed on main thread | < 6 MB | 6–10 MB | > 10 MB | build/CI script (sum of compact sizes) |
| M10 | Initial JS (gzip, home route) | < 300 KB | 300–400 KB | > 400 KB | `@next/bundle-analyzer` / `next build` size output |
| M11 | Data fetch + parse (first-load, no cache) | < 2.5 s | 2.5–5 s | > 5 s | Playwright `performance.getEntriesByType('resource')` |
| M12 | Tile render at zoom 7 → 12 | no long task > 100 ms on pan/zoom | — | any > 100 ms | Playwright trace (long tasks) |
| M13 | Peak JS heap (full dataset, zoom 12) | < 200 MB | 200–300 MB | > 300 MB | `performance.memory` / CDP `HeapProfiler` |
| M14 | LOD/culling effectiveness | uncontracted layer ≤ 500 features at zoom 7 | 500–2000 | > 2000 | Playwright `count` of `.leaflet-overlay-pane path` |

Budgets M6–M14 are **lab-only gates** (deterministic, run in CI). M1–M5 are the user-facing
contract and are the ones reported to stakeholders.

---

## 5. Measurement approach

### 5.1 Tooling to add (implementation backlog — not installed yet)

| Tool | Purpose | Install |
|---|---|---|
| `@lhci/cli` | Lighthouse CI, budget assertions, trend tracking | `npm i -D @lhci/cli` |
| `lighthouse` | local ad-hoc audits | `npm i -D lighthouse` |
| `@next/bundle-analyzer` | JS bundle budget | `npm i -D @next/bundle-analyzer` |
| `playwright` | perf traces, CLS sampler, interaction INP proxy | **already present** (1.62.1, extraneous — promote to devDependency) |

No Jest/Vitest — the existing 28 `scripts/_e2e_*.mjs` Playwright scripts are the established
pattern; performance traces should follow the same script style.

### 5.2 Lighthouse CI (local + CI)

`lighthouserc.json` (proposed):

```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000/", "http://localhost:3000/specii", "http://localhost:3000/permis"],
      "numberOfRuns": 3,
      "settings": {
        "preset": "desktop",
        "onlyCategories": ["performance", "accessibility", "best-practices"]
      }
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["warn", { "minScore": 0.75 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 3000 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 4000 }],
        "total-blocking-time": ["error", { "maxNumericValue": 600 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-byte-weight": ["error", { "maxNumericValue": 3000000 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

Mobile pass (the one that matters) is run as a separate command with the `mobile` preset +
Fast 3G throttling (Lighthouse's "mobile" preset already applies 4× CPU + simulated Fast 3G).

### 5.3 Playwright performance traces (map-specific)

Follow the existing `_e2e_*.mjs` pattern. Example skeleton:

```js
import { chromium } from 'playwright';
const BASE = process.argv[2] || 'http://localhost:3000';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

await page.goto(BASE, { waitUntil: 'domcontentloaded' });
// wait for the map island's dataLoaded gate, instrumented via a window flag (see §9)
await page.waitForFunction(() => window.__perfDataLoaded === true, { timeout: 45000 });

const nav = await page.evaluate(() => {
  const e = performance.getEntriesByType('navigation')[0];
  return { domContentLoaded: e.domContentLoadedEventEnd, load: e.loadEventEnd };
});
const big = await page.evaluate(() => performance
  .getEntriesByType('resource')
  .filter(r => r.name.includes('/data/'))
  .map(r => ({ name: r.name, transfer: r.transferSize, duration: r.duration })));
console.log({ nav, big });
```

For full traces (long tasks, INP proxy) use `page.tracing.start({ categories: ['devtools.timeline'] })`
and parse with `trace_events` — or reuse Chrome DevTools Performance panel manually for spot checks.

### 5.4 Bundle analyzer

```bash
ANALYZE=true npm run build   # requires next.config.ts to gate @next/bundle-analyzer on env
```
Produces per-chunk interactive report; assert the home route's first-load JS stays under M10.

### 5.5 Manual throttling profile (Fast 3G)

Standard profile for reproducibility (Chrome DevTools → Network → Custom / Playwright CDP):
- Download 1.6 Mbps (200 KB/s), Upload 750 Kbps, Latency 150 ms, CPU 4× slowdown.
- Playwright: `browser.newContext()` with `{ ... }` then `cdpSession.send('Network.emulateNetworkConditions', …)`
  and `Emulation.setCPUThrottlingRate`.

---

## 6. Test cases (checks)

Each TC lists setup → action → measurement → PASS condition. TCs map to budgets in §4.

### Initial load & payload

**TC-01 — First-load payload budget**
- Setup: clean cache, Fast 3G throttle, cold `next start` (production build) or a Vercel preview URL.
- Action: load `/`, wait for `dataLoaded`.
- Measure: sum of `transferSize` for `*/data/*` resources (gzip on-wire).
- PASS: M7 (< 2.5 MB). FAIL if the un-split 36 MB `waters.json` is still fetched verbatim.

**TC-02 — Time-to-first-map-paint (Fast 3G)**
- Action: load `/`, time from `navigationStart` to `window.__perfDataLoaded` (or first non-skeleton map node).
- PASS: M6 (< 5 s). **Expected to FAIL today** (≈6 MB @ 200 KB/s ≈ 30 s + parse).

**TC-03 — Main-thread JSON parse size**
- Action: static/CI check — sum of compact bytes of the 5 fetched files.
- PASS: M9 (< 6 MB). Currently ~22.6 MB → **fails today**; this is the budget that forces the split.

**TC-04 — `waters.json` gzip size**
- Action: `gzip -9` the compact file in CI.
- PASS: M8 (< 1.5 MB). Currently 4.75 MB → **fails today**.

### Bundle & render

**TC-05 — Initial JS budget**
- Action: `ANALYZE=true npm run build`, read home-route first-load JS gzip.
- PASS: M10 (< 300 KB). Verify Leaflet + react-leaflet stay in the lazy map chunk.

**TC-06 — LOD/culling effectiveness (uncontracted)**
- Action: load `/` at zoom 7 (default), count SVG paths in the uncontracted overlay pane;
  zoom to 12 and count again; assert the count grows but stays bounded.
- PASS: M14 (≤ 500 features at zoom 7). Confirms existing culling actually prunes.

**TC-07 — Contracted-layer geometry at national zoom**
- Action: at zoom 7, count contracted-layer paths; capture long tasks during the initial render.
- PASS: M12 (no > 100 ms long task attributable to contracted layer render).
  **Expected to fail today** — full 1013 features + hit layer render with no culling.

**TC-08 — Tile render zoom 7 → 12**
- Action: pan/zoom 7→12 on a 390×844 viewport; record long tasks + dropped frames (trace).
- PASS: M12 (no > 100 ms long task).

### Interaction / stability

**TC-09 — No layout shift on filter change**
- Action: toggle county filter, water-type filter, and open/close the vaul detail sheet on mobile.
- Measure: CLS sampler (`new PerformanceObserver('layout-shift')`) across the interaction window.
- PASS: M5 (0.00). Guard against sheet/filter mutations pushing the map.

**TC-10 — INP proxy on interactions**
- Action: repeatedly (10×) click a river, open association sheet, toggle a county chip.
- Measure: event-handler duration via trace (or `PerformanceObserver('event')` with interactionId).
- PASS: M2 (< 200 ms p75). Focus on `contractAtFraction`/`fractionAtPoint` walk cost on big polylines.

**TC-11 — Geolocation MVP responsiveness**
- Action: grant position (CDP `Emulation.setGeolocationOverride`), trigger locate, measure time to
  nearby list + circle render.
- PASS: < 300 ms compute (nearest-waters scan is 1013 items; must stay linear).

**TC-12 — Memory with full dataset**
- Action: load at zoom 12 with no filter (all 10,891 features), read `performance.memory.usedJSHeapSize`
  (CDP `Runtime.getHeapUsage`), then add + clear a county filter 5× to check for leaks.
- PASS: M13 (< 200 MB, no monotonic growth).

### Content pages

**TC-13 — /specii and /permis**
- Action: Lighthouse mobile audit of both routes.
- PASS: LCP < 2.5 s, CLS < 0.1, no long task on `scrollIntoView` species jump.

---

## 7. Risk ranking (most likely slow → least)

1. **36 MB `waters.json` fetched + parsed before first paint (P0).** `loadData()` blocks the map on
   the whole file; `geometryByCounty` (3.64 MB) is redundant and always shipped. On Fast 3G this is
   ~30 s to first paint. *Fix direction (backlog):* split `geometryByCounty` into a lazy county file;
   strip the pretty-printing (2.14×); simplify `geometry` (target < 1.5 MB gzip); consider serving
   simplified vs full geometry per zoom.
2. **Un-culled contracted geometry + doubled hit-layer (P0/P1).** 1013 features incl. 15k-vertex
   polylines render at every zoom with no viewport culling — unlike the uncontracted layer which
   already culls. *Fix direction:* apply the same bbox culling + zoom LOD to `WaterFeatureLayer`;
   drop the invisible hit-layer at low zoom where it is pointless.
3. **Big JSON parse on 1-core phone (P1).** ~22.6 MB compact JSON parsed on the main thread at once.
   *Fix direction:* lazy-load rivers/lakes after contracted waters; parse in smaller chunks / a web
   worker; drop unused `waters_geocoded.geojson` (9.66 MB) and `waters.geojson` from `public/`.
4. **Tile load at high zoom (P2).** Standard OSM raster; many tiles at zoom 12. Mitigations later:
   caching header already set (vercel.json `max-age=86400`); consider a vector tile source only if
   TC-08 shows real jank.
5. **Geolocation + locality scans (P3).** Linear scans are fine at current scale; revisit only if
   waters grow by an order of magnitude.
6. **Species/permis pages (P4).** Static, low risk — regression guard only.

---

## 8. CI integration (proposal)

Two new workflow files, additive to the existing `data-refresh.yml`.

### 8.1 Lighthouse CI gate — `.github/workflows/lighthouse.yml`

```yaml
name: Lighthouse CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  lhci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run build
      - name: Run Lighthouse CI (mobile budget)
        run: |
          npm run start & LH_WAIT=15 npx wait-on http://localhost:3000
          npx lhci autorun --config=lighthouserc.json
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

### 8.2 Data payload budget — add to `data-refresh.yml` (or new `data-budget.yml`)

```yaml
      - name: Enforce data payload budgets
        run: |
          node scripts/check-data-budget.mjs   # asserts M7/M8/M9, exits 1 on FAIL
```

`scripts/check-data-budget.mjs` (to be written in implementation):
- sum gzip sizes of the 5 fetched files → assert < 2.5 MB (M7);
- assert `waters.json` gzip < 1.5 MB (M8);
- assert compact JSON sum < 6 MB (M9);
- assert `waters_geocoded.geojson` / `waters.geojson` are NOT in `public/data/` (dead weight).

Suggested review gate: **PR blocks on Lighthouse CI mobile budget + data budget**, not just on build.

---

## 9. How to run (quick start)

```bash
cd /home/stefan/undepescuim
npm ci
npm run build && npm run start          # production build (perf must be measured on prod build, not dev)

# Local Lighthouse (one-off)
npx lighthouse http://localhost:3000/ --preset=perf --output=html --output-path=./.e2e/lh-home.html

# Existing e2e script pattern (Playwright, against the running server)
PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_menu_mobile.mjs http://localhost:3000

# Bundle analyzer
ANALYZE=true npm run build
```

### Instrumentation needed for automation (backlog)

Expose a stable first-paint signal for Playwright to await. Options:
- a `window.__perfDataLoaded = true` set inside `loadData()`'s success path, or
- `data-performance-mark="loaded"` attribute on the map container once `dataLoaded` flips true.

Either gives TC-02/TC-06/TC-12 a deterministic wait target instead of `waitForTimeout`.

---

## 10. Verification steps (does this plan hold?)

1. `npm run build` succeeds today → confirms the CI path is real.
2. `curl -sI https://undepescuim.vercel.app/data/waters.json` → confirm `Content-Encoding: gzip`/`br`
   and the ~5 MB transfer (not 36 MB) so budget M7 measures the right number.
3. Run one `_e2e_*.mjs` script against a local prod build to confirm the Playwright harness pattern.
4. Spot-check TC-02 manually in Chrome DevTools (Network throttled Fast 3G): the map should
   currently take > 25 s to first paint — confirming the P0 risk and validating the budget.

---

## 11. Out of scope for this spike

- Any code/data changes (split files, simplification, worker) — those are follow-up implementation
  tasks gated by this plan's budgets.
- Field (RUM) Core Web Vitals — lab-only until a Web Vitals reporter is added; note M2 needs a RUM
  source (or `@vercel/speed-insights`) to measure INP in production.
- Vector tiles / tile server swap — only if TC-08 proves raster jank.

---

## Appendix A — Correction to spike brief

- `fuse.js` is **not** used (not in `package.json`); species search is `cmdk` (`SpeciesSearch.tsx`).
- `waters.json` is **1013 entries but 36 MB** (not a few MB) because of full un-simplified OSM
  geometry (13.96 MB) + redundant `geometryByCounty` (3.64 MB) + 2.14× pretty-print whitespace.
- "10k features" is accurate: 1013 contracted + 4166 rivers + 5712 lakes = **10,891 features**.
- LOD/culling exists **only** in `UncontractedWaterLayer`; the contracted layer does not cull.
