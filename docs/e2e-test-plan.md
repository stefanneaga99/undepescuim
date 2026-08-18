# UndePescuim.ro — E2E / Regression Test Plan

**Task:** t_30cc75ff (QA SPIKE — all critical user flows, mobile + desktop)
**Date:** 2026-08-16
**Author:** plan-maker
**Status:** Draft — review required before execution

---

## 1. Goal & Scope

Produce a **single, maintainable Playwright Test suite** that replaces the current
collection of 28 ad-hoc `_e2e_*.mjs` scripts and covers **every critical user flow**
on mobile + desktop, wired into **GitHub Actions**, with a deterministic data
strategy so it doesn't flake.

Out of scope (documented, not implemented):
- **Offline / PWA** — no service worker is built yet (ARCHITECTURE.md §8 is a plan, not code).
- **Dark map tiles** — dark UI ships over light OSM tiles in phase 1 (dark-mode-feasibility-plan.md §7,
  Option A approved); theme-aware tiles + palette re-tune are a separate phase-2 task.
- **Unit / component tests** (Vitest/RTL) — this plan is E2E; `src/utils/geo.ts` and the
  Zustand store are mentioned only as *optional* future tiers.

### Current app facts (verified against code, not the aspirational ARCHITECTURE.md)

| Fact | Value |
|------|-------|
| Framework | Next.js 16 App Router, React 19, TypeScript 5 |
| Map | react-leaflet v5 (ESM, client-only via `dynamic(ssr:false)`), Leaflet 1.9 |
| State | Zustand `src/stores/map-store.ts` (single store, all map UI state) |
| UI | shadcn/ui + radix + vaul (bottom sheet) + cmdk (command palette), Tailwind v4 |
| Package manager | **npm** (`package-lock.json`; no pnpm/yarn) |
| Routes | `/` (map), `/specii`, `/permis`, `POST /api/report` |
| Data (served from `/public/data/`) | `associations.json` (43 KB), `waters.json` (**38 MB**), `uncontracted_rivers.json` (2.3 MB), `uncontracted_lakes.json` (3.3 MB), `counties.geojson` (227 KB) |
| Playwright | `playwright@1.62.1` installed (raw `chromium` API only — **`@playwright/test` is NOT installed**) |
| CI | **none** (no `.github/` directory) |
| Report API | `POST /api/report` → GitHub issue on `neagastefan99/undepescuim` (label `report`); needs `REPORT_GITHUB_TOKEN`, else `503` |

The app is a **data directory** — data correctness *is* the product. Half the existing
tests are data-integrity assertions on the served JSON. The plan keeps that tier.

---

## 2. Historical inventory — superseded e2e scripts

> Migration completed 2026-08-18: the ad-hoc `scripts/_e2e_*.mjs` files were
> removed after their reusable assertions moved into `tests/e2e/`. The table
> below is retained only as migration history.

All 28 are **standalone Node scripts** using `import { chromium } from 'playwright'`
(no `@playwright/test`, no runner, no fixtures, no POM, no config, no retries, no HTML
report). They share a `check(cond, label)` helper and `process.exit(failures ? 1 : 0)`.

**How they run today:**
```
# browserless container (shared window) + dev server on LAN IP:
PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_<name>.mjs http://172.25.236.246:3100
# or local chromium (needs /tmp/asound audio-device workaround):
node scripts/_e2e_<name>.mjs http://localhost:3000
```
Screenshots land in `.e2e/*.png`. Two env-dependent paths exist because the browserless
CDP container can only reach the host via a LAN IP, while real geolocation needs a
secure context (`localhost`).

| # | Script | Feature / task | Covers |
|---|--------|----------------|--------|
| 1 | `_e2e_geolocation.mjs` | t_5ddc6022 | 3 passes: desktop grant (dot+radius+sheet), mobile grant (adaptive 25→50 km), deny (bubble, map untouched) |
| 2 | `_e2e_report.mjs` | F3 t_5b1250b3 | report dialog: 2 entry points, 5 reason radios, submit-disabled-until-reason, stub `/api/report` → success |
| 3 | `_e2e_specii.mjs` | t_43bf3295 | `/specii` render, search narrow+select+flash, size search "40", header link, `/permis` cross-link, card "Dimensiuni" link |
| 4 | `_e2e_menu_mobile.mjs` | t_f930e4f3 | mobile hamburger sheet (z-index, close-on-select, overlay-tap close) + desktop inline links |
| 5 | `_e2e_association_highlight.mjs` | t_b6a0e2fe | select association → all waters bold green (#22c55e), incl. sector slices |
| 6 | `_e2e_assoc_clear.mjs` | t_7a7192ea bug2 + t_abccfd6c + t_697ba939 | click water while assoc filter active (keep vs clear semantics) |
| 7 | `_e2e_assoc_mobile.mjs` | t_7a7192ea bug1 | mobile association select branch (icon button, vaul sheet) |
| 8 | `_e2e_assoc_nozoom.mjs` | t_abccfd6c + t_697ba939 | click selected-assoc water must NOT zoom out |
| 9 | `_e2e_assoc_search_nozoom.mjs` | t_d987cdb7 | assoc search must not zoom on focus/typing; sane confirm zoom (cap 12) |
| 10 | `_e2e_cerbul_verify.mjs` | t_5f5f2cce | Cerbul Carpatin / Jiu data fix |
| 11 | `_e2e_merge_snagov.mjs` | t_1b7c95a7 | AVPS ACVILA / Râul Snagov association click |
| 12 | `_e2e_county_clip.mjs` | t_117f0b99 | county-clip: `geometryByCounty` served + Brașov chip → correct clip rendered |
| 13 | `_e2e_locality.mjs` | t_dd918db7 | county→locality cascade, text-fallback locality, coverage floor |
| 14 | `_e2e_nearby_county.mjs` | t_6c2ac870 | nearby county attribution (4 wrong-centroid lakes + county chip) |
| 15 | `_e2e_lakes.mjs` | t_51e028c4 | uncontracted lakes/ponds overlay (Dumbrăvița Hălchiu) |
| 16 | `_e2e_point_fallback.mjs` | t_cdb614de | bbox-fallback waters render as violet dots, not rectangles |
| 17 | `_e2e_f1a_permit.mjs` | F1a | permit rows on card (Pecineagu has permitUrl, Agrement doesn't) |
| 18 | `_e2e_f2a_validity.mjs` | t_e6ec4b5f | permit-validity statement + persistent association chip (desktop+mobile) |
| 19 | `_e2e_permis_guide.mjs` | F5 t_286cf213 | `/permis` page + WaterDetailCard links |
| 20 | `_e2e_sheet_handle.mjs` | t_f21260ee | bottom-sheet drag handle (44px touch target, tap-to-cycle) |
| 21 | `_e2e_focus_careful.mjs` | t_b1547e24 | orange focus on contracted/uncontracted click (elementFromPoint) |
| 22 | `_e2e_focus_ponds.mjs` | t_b1547e24 | pond polygon orange highlight + Privat/Necontractat card |
| 23 | `_e2e_focus_ramna.mjs` | t_b1547e24 | Râmna uncontracted highlight |
| 24 | `_e2e_merge_sample.mjs` | t_1b7c95a7 | per-county sample of newly-merged waters render + card |
| 25 | `_e2e_fixed_groups.mjs` | t_1b7c95a7 | 9 fixed double-draw groups + dragan one-owner |
| 26 | `_e2e_verify_sebes_sweep.mjs` | t_e3ae3121 | sebes family county-correct geometry + 17 sweep fixes |
| 27 | `_e2e_verify_sweep.mjs` | t_68dabead | 2 run-127 fixes render as lines; rectangle-only waters stay bbox |
| 28 | `_e2e_pojorta.mjs` | t_a0e123da | Valea Pojorâtei geometry fixed (LineString, Făgăraș) |

### Coverage gap analysis

**Well covered** (green): association select/highlight/clear semantics, geolocation
(grant/deny/adaptive radius), report dialog, specii page + search, hamburger nav,
data-integrity (geometry, county attribution, merge/sweep).

**Under-covered / missing** (gaps the new suite must fill):
1. **No unified runner** — each script re-implements launch/wait/check; no shared
   fixtures, no parallel projects, no retry, no HTML report, no CI.
2. **Locality filter is only data-tested** — no UI interaction test (open dropdown,
   pick locality, clear).
3. **Empty-filter-result edge case** — no test asserts a county/type combo with zero
   waters renders an empty map without crashing.
4. **Long river / long name layout** — no truncation/layout test on the water card.
5. **Keyboard navigation** — only `Escape` in the specii search; no arrow-key +
   `Enter` selection test in either command palette.
6. **Tablet breakpoint** (768px) — only 390 and 1280 are exercised; the
   mobile↔desktop switch at `md` is untested at the boundary.
7. **Contract filter** (`Statusul contractului`, aria-pressed toggle) — exercised
   indirectly by focus scripts but has no dedicated spec.
8. **404 / back-nav / home** — no explicit `Înapoi la hartă` and logo-home assertions.
9. **Report 503 / honeypot** — server `not_configured` and honeypot paths are
   implemented but untested end-to-end.
10. **No data-testid attributes anywhere** (verified: zero matches in `src/`) — the
    current selectors couple to aria-labels, radix `data-slot`, and Leaflet internals.

---

## 3. Critical user flows → test matrix

Flows are mapped 1:1 to spec files. Every flow runs in **all three viewports** unless
noted. `@smoke` tags mark the fast subset for the PR path.

| ID | Flow (per task mandate) | Spec | Key assertions | Viewport |
|----|-------------------------|------|----------------|----------|
| F1 | Load app → map ready | `smoke/app-load.spec.ts` @smoke | header, map container, filter bar, vector paths drawn, no console errors | all |
| F2 | County filter | `flows/county-locality.spec.ts` | toggle chip filters waters; locality dropdown appears only when ≥1 county selected | all |
| F3 | Locality filter | `flows/county-locality.spec.ts` | pick locality narrows; clear resets; county change invalidates locality (store R) | all |
| F4 | Association search + select | `flows/association.spec.ts` | command palette opens; select → waters go green #22c55e / uncovered grey #9ca3af; chip appears; **no over-zoom** (zoom ≤ 12); search focus/typing does not zoom | all |
| F5 | Association highlight + detail | `flows/association.spec.ts` | chip → association detail sheet (name, counties, reciprocity) | all |
| F6 | Click water → detail card | `flows/water-detail.spec.ts` | card shows name, sector, size, association contact, permit row(s), validity, `Dimensiuni de reținere` + `Permis & Reguli 2026` links | all |
| F7 | Nearby waters (geolocation) | `flows/nearby-waters.spec.ts` | grant → user dot + radius circle + sheet rows with km/county; adaptive radius 25→50; row tap → card | all (real permission in local/CI chromium) |
| F8 | Report flow | `flows/report.spec.ts` | both entry points; 5 radios; submit disabled until reason; stub `/api/report` → confirmation with GitHub link; positive tap pre-selects `data_correct` | desktop + mobile |
| F9 | `/specii` search | `flows/specii.spec.ts` | render; search narrows (diacritic-insensitive); select scrolls + flashes; min-size `N cm`; sources block | all |
| F10 | `/permis` page | `flows/permis.spec.ts` | H1, sections, external links, cross-link to `/specii` | all |
| F11 | Hamburger menu nav | `flows/nav.spec.ts` | mobile: hamburger opens sheet, links navigate, overlay tap closes; desktop: inline links visible, hamburger hidden | mobile + desktop |
| F12 | Back / home | `flows/nav.spec.ts` | `Înapoi la hartă` returns to `/`; logo returns home | all |

**Edge cases** (separate `regression/edge-cases.spec.ts`):

| Case | Assertion |
|------|-----------|
| No geolocation permission | deny → localized bubble, no dot, no sheet, map zoom untouched |
| Empty filter results | county+type combo with zero waters → empty map, no crash, filter stays consistent |
| Long river / association name | card truncates (`truncate`) without overflow; sheet scrolls |
| Keyboard nav (specii + assoc search) | ArrowDown/ArrowUp/Enter selects; Escape closes |
| Tablet boundary 768px | exactly at `md` → desktop panel layout (no hamburger) |
| Contract filter toggle | `contractate` hides uncontracted; `necontractate` hides contracted; `all` shows both |
| Report 503 + honeypot | route-level test (no token → `not_configured`; `website` field → silent 200) |
| 404 | unknown route returns a Next 404 (no crash) |
| Dark mode | theme toggle rendered in header; clicking it toggles `.dark` on `<html>` and persists across reload (localStorage `theme`); system preference respected on first visit; no-FOUC (class applied before first paint); every page renders dark |

---

## 4. Target architecture — Playwright Test

### 4.1 Dependencies to add (`package.json`)

```jsonc
"scripts": {
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:e2e:headed": "playwright test --headed",
  "test:e2e:smoke": "playwright test --grep @smoke"
},
"devDependencies": {
  "@playwright/test": "^1.62.1"
}
```

### 4.2 `playwright.config.ts`

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e/specs',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Leaflet + a single dev server: keep sequential to avoid zoom/tile flake.
  fullyParallel: false,
  workers: process.env.CI ? 2 : 1,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }], ['github']]
    : [['list']],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    serviceWorkers: 'block',
  },
  projects: [
    { name: 'mobile',  use: { ...devices['iPhone 14'] } },        // 390×844
    { name: 'tablet',  use: { ...devices['iPad (gen 7)'] } },      // 768×1024 (md boundary)
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },    // 1280×720
  ],
  webServer: {
    // Build once, serve once — closer to prod than `next dev`, and stable.
    command: 'npm run build && npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 240_000,
  },
});
```

> **Why `build && start`, not `next dev`:** dev-mode HMR + on-demand compile is the #1
> source of timing flake. A production build is deterministic and exercises the real
> asset pipeline. `reuseExistingServer` keeps local iteration fast.

### 4.3 File structure

```
undepescuim/
├── playwright.config.ts
├── .github/workflows/e2e.yml
├── tests/
│   └── e2e/
│       ├── fixtures/
│       │   ├── app.ts                  # base test fixture: page + seed + mapReady helper
│       │   ├── seed-data.ts            # deterministic mini-dataset (typed vs src/types/data.ts)
│       │   └── routes.ts               # routeData(page, seed) — intercepts the 5 data endpoints
│       ├── pages/                      # Page Object Models (one per page/component)
│       │   ├── MapPage.ts
│       │   ├── FilterBar.ts            # county / locality / type / contract controls
│       │   ├── AssociationSearch.ts
│       │   ├── AssociationChip.ts
│       │   ├── WaterDetailCard.ts
│       │   ├── NearbyWatersSheet.ts
│       │   ├── ReportDialog.ts
│       │   ├── SpeciiPage.ts
│       │   ├── PermisPage.ts
│       │   └── Header.ts
│       ├── helpers/
│       │   ├── map.ts                  # clickWater(slug), tileZoom(), waitForWatersDrawn()
│       │   └── selectors.ts            # data-testid constants (single source of truth)
│       └── specs/
│           ├── smoke/app-load.spec.ts
│           ├── flows/                  # F2..F12 (one file per flow, see §3)
│           ├── regression/edge-cases.spec.ts
│           └── data-contract/data-integrity.spec.ts   # migrated from the 28 scripts
```

### 4.4 Fixture sketch (`tests/e2e/fixtures/app.ts`)

```ts
import { test as base, expect } from '@playwright/test';
import { seed } from './seed-data';
import { routeData } from './routes';

export const test = base.extend<{ mapReady: () => Promise<void> }>({
  page: async ({ page }, use) => {
    // Deterministic data for logic/UI tests; real data only in data-contract specs.
    await routeData(page, seed);
    await use(page);
  },
  mapReady: async ({ page }, use) => {
    await use(async () => {
      await page.goto('/');
      await page.getByTestId('map-root').waitFor();
      await page.getByTestId('waters-drawn').waitFor({ state: 'attached' });
    });
  },
});
export { expect };
```

### 4.5 Page Object Model sketch (`tests/e2e/pages/MapPage.ts`)

POMs own **only** `data-testid`/`aria-*` selectors (never Leaflet internals or pixel
math — that stays isolated in `helpers/map.ts`):

```ts
import type { Page } from '@playwright/test';

export class MapPage {
  constructor(private page: Page) {}
  get locateButton() { return this.page.getByTestId('locate-button'); }
  get filterBar() { return new FilterBar(this.page); }

  async clickWater(slug: string) {
    // helper isolates the SVG click math behind a stable slug → path contract
    await clickWaterBySlug(this.page, slug);
    await this.page.getByTestId('water-card').waitFor();
  }
}
```

---

## 5. Flake-resistance strategy

The current scripts are flaky because they rely on pixel math and fixed sleeps. The
new suite adopts, in priority order:

1. **`data-testid` attributes (primary).** Add stable IDs to every interactive
   surface. No more `getScreenCTM` + `elementFromPoint` except for the one water-click
   helper (which is unavoidable — Leaflet SVG paths are the map surface).

   Proposed IDs (add in the matching component, keep `aria-*` as-is):
   | Component | data-testid | notes |
   |-----------|-------------|-------|
   | `MapShell` root | `map-root` | ready signal |
   | `WaterFeatureLayer` overlay | `waters-drawn` | set on a hidden marker when the GeoJSON layer finishes (`onEachFeature`/`whenReady`) |
   | `LocateButton` | `locate-button` | already has `aria-label="Localizează-mă"` |
   | `CountyFilter` chip | `county-chip` (+ `data-county`) | also `aria-pressed` |
   | `LocalityFilter` | `locality-filter` / `locality-option` | |
   | `WaterTypeFilter` | `type-filter` | |
   | `ContractFilter` | `contract-filter` | already `aria-pressed` |
   | `AssociationSearch` | `assoc-search` / `assoc-option` | |
   | `AssociationChip` | `assoc-chip` | |
   | `WaterDetailCard` | `water-card` / `permit-row` | |
   | `NearbyWatersSheet` | `nearby-sheet` / `nearby-row` | already `data-nearby-sheet` |
   | `ReportForm` | `report-dialog` / `report-reason` | |
   | `Header` nav | `nav-specii` / `nav-permis` / `hamburger` | |

2. **Web-first assertions over `waitForTimeout`.** Replace every `page.waitForTimeout(N)`
   with `expect(locator).toBeVisible()` / `toHaveText()` / `toHaveAttribute()` (auto-wait
   + retry). Keep *one* bounded `waitForTimeout` only for leaflet `flyTo` animation.

3. **Deterministic data (see §6).** UI-flow tests never depend on the 38 MB live
   `waters.json` or its refresh cadence.

4. **Tile isolation.** Assert on the **vector overlay** (drawn from data), never on OSM
   tile bytes. In CI, optionally route `**/tile.openstreetmap.org/**` to a transparent
   1×1 PNG so slow/blocked tile hosts can't fail a run.

5. **Real geolocation, no CDP container.** `localhost` is a secure context, so
   `context.grantPermissions(['geolocation'])` + `setGeolocation()` work in CI's own
   Chromium. The browserless/LAN-IP dance disappears entirely.

6. **Retries + tracing** (`trace: on-first-retry`, `retries: 2` in CI) so a flake is
   diagnosable, not a mystery.

7. **Console-error gate** in the smoke spec — any `pageerror`/`console.error` during
   load fails the run (catches React hydration + Leaflet errors early).

---

## 6. Test data strategy

Two tiers, no overlap:

### 6.1 Deterministic seeds (logic & UI flows) — **default**

A hand-written mini-dataset in `tests/e2e/fixtures/seed-data.ts`, typed against
`src/types/data.ts` (`Water`, `Association`, `CountyFeature`). `routes.ts` intercepts
the five endpoints before the app boots:

```ts
export async function routeData(page: Page, seed: SeedData) {
  await page.route('**/data/associations.json', r => r.fulfill({ json: seed.associations }));
  await page.route('**/data/waters.json', r => r.fulfill({ json: seed.waters }));
  await page.route('**/data/uncontracted_rivers.json', r => r.fulfill({ json: seed.rivers }));
  await page.route('**/data/uncontracted_lakes.json', r => r.fulfill({ json: seed.lakes }));
  await page.route('**/data/counties.geojson', r => r.fulfill({ json: seed.counties }));
}
```

The seed MUST contain one instance of each edge case so every spec has a stable target:
- a contracted **river** with `geometry: LineString` + `asociatie.permitUrl`
- a contracted **lake** with `geometry: Polygon`, no permitUrl
- an **uncontracted** river (`uncontracted: true`) and lake
- a water with `locality: null` (locality-filter edge)
- a water with a deliberately **long name** (truncation test)
- an association with `reciprocity: 'neconfirmată'` and one with `'confirmată'`
- coordinates that exercise both the default (25 km, ≥3 nearby) and adaptive (50 km)
  radius branches around two fixed points (Bucharest, Iași)
- a `geometryByCounty` clip (county-filter render path)

Benefits: fast (no 38 MB fetch), deterministic, survives data refreshes, independent of
network. Risk: seeds can drift from real data shape — mitigated by tier 2.

### 6.2 Live-data contract tests (data integrity) — **separate spec**

`data-contract/data-integrity.spec.ts` runs against the **real served** `/public/data`
(no route interception). This is where the 28 scripts' data assertions migrate:
- served JSON parses and matches `Water`/`Association` types
- geometry is `LineString`/`Polygon` (not `null`) for the sweep-fixed entries
- county attribution (`judet`, `locality`, `geometryByCounty`) is internally consistent
- spot-check known fixtures (Pecineagu, Dumbrăvița ponds, Valea Pojorâtei, sebes family)

Run order: data-contract specs are the only ones touching real data, so they stay
`@smoke`-excluded and are tagged `@data` (run on a schedule / data refresh, not every PR
— see §7).

**Tradeoff accepted:** seeds give speed/determinism but could mask a real data regression;
the contract tier is the safety net. Keep the contract tier small (assert *shape* +
known fixtures), not exhaustive.

---

## 7. CI wiring — GitHub Actions (free tier)

New file `.github/workflows/e2e.yml`:

```yaml
name: e2e

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
  schedule:
    # Nightly data-contract sweep (catches upstream data regressions)
    - cron: '17 3 * * *'

concurrency:
  group: e2e-${{ github.ref }}
  cancel-in-progress: true

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install deps
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Build & run E2E (logic + flows, seeded data)
        run: npx playwright test --grep-invert @data
        env:
          CI: 'true'

      - name: Upload report (on failure)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7

  data-contract:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    # Only on main / schedule / manual — not on every PR.
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - name: Data-contract tests (real data)
        run: npx playwright test --grep @data
        env:
          CI: 'true'
      - uses: actions/upload-artifact@v4
        if: failure()
        with: { name: playwright-data-report, path: playwright-report/, retention-days: 7 }
```

**Report-token note:** no `REPORT_GITHUB_TOKEN` secret is required. The report spec
stubs `POST /api/report` (as `_e2e_report.mjs` already does), so CI never creates real
GitHub issues. If a real round-trip smoke is later wanted, add a `secrets.REPORT_GITHUB_TOKEN`
and one `@real-report` spec gated on `if: github.event_name == 'schedule'`.

**Vercel preview note (optional):** add a `vercel deploy --token` step to smoke-test the
preview URL with `PLAYWRIGHT_BASE_URL`, but that needs a Vercel token and preview URLs
are slow — defer until the local suite is green.

---

## 8. Migration plan (ordered, 2–5 min steps each)

Execute in dependency order; each step ends with a green command.

1. **Add deps + scripts.** `npm i -D @playwright/test` and add the four `test:e2e*`
   scripts (§4.1). Verify: `npx playwright --version`.
2. **Add `playwright.config.ts`** (§4.2) with the three projects + `webServer`.
   Verify: `npx playwright test --list` prints the (still-empty) project matrix.
3. **Add `data-testid` attributes** (§5.1) across the 12 components. This is the
   long pole — do it as its own commit. Verify: `npm run build` still passes; manual
   `npm run dev` spot-check the map still renders.
4. **Write fixtures + helpers** (`app.ts`, `seed-data.ts`, `routes.ts`, `map.ts`,
   `selectors.ts`). Verify: a throwaway spec logs seed data and draws a map.
5. **Write POMs** (one per page, `pages/`). Verify: `tsc --noEmit` clean.
6. **Port F1–F12 specs** (one file each) using POMs + seeds. Start with
   `smoke/app-load.spec.ts` (F1) as the CI canary. Verify: `npm run test:e2e:smoke`.
7. **Port edge-case spec** (§3 table) including geolocation deny, empty results,
   long names, keyboard nav, tablet boundary, 404, dark-mode (toggle+persist+system+no-FOUC+per-page rendering).
8. **Migrate data-contract spec** from the 28 scripts — consolidate the *data-shape*
   assertions into `data-integrity.spec.ts` (tag `@data`). Delete the superseded
   `scripts/_e2e_*.mjs` only **after** their assertions are covered (keep a mapping
   in the spec file header so nothing is lost).
9. **Add `.github/workflows/e2e.yml`** (§7). Verify: push a branch, watch the PR
   check go green.
10. **Remove old scripts.** Completed 2026-08-18 after the structured suite passed
    across mobile, tablet, and desktop.

---

## 9. Risks & tradeoffs

| Risk | Mitigation |
|------|------------|
| 38 MB `waters.json` makes tests slow / OOM in CI | Seeds replace it for all UI tests; only the `@data` tier loads it (and that tier is nightly/main-only) |
| react-leaflet v5 ESM + SSR hydration errors | Smoke spec gates on console errors; `webServer` uses a prod build (not dev HMR) |
| OSM tile host slow/blocked in CI | Assert on vector overlay, not tiles; optionally stub tile requests (§5.4) |
| Leaflet `flyTo` animation timing | Single bounded `waitForTimeout` for the fly, web-first assertions everywhere else |
| Seed drift from real data shape | Seeds are typed against `src/types/data.ts`; the `@data` contract tier is the shape guard |
| `data-testid` additions are invasive (12 components) | One isolated commit; IDs are additive (existing aria-labels untouched) |
| Geolocation needs secure context | `localhost` in CI/local chromium is secure — no CDP container needed |
| Report spec accidentally hits real GitHub | `/api/report` is always stubbed in CI; real round-trip is a separate opt-in `@real-report` tag |

---

## 10. Verification checklist (definition of done)

- [ ] `npm run test:e2e` is green locally across mobile + tablet + desktop.
- [ ] `npx playwright test --grep @smoke` completes in < 3 min (CI canary).
- [ ] `npx playwright test --grep @data` green against real `/public/data`.
- [ ] `.github/workflows/e2e.yml` runs on PR + main + nightly; report artifact uploads on failure.
- [ ] Zero remaining `waitForTimeout` outside `helpers/map.ts`.
- [x] Ad-hoc `_e2e_*.mjs` scripts removed after migration to the structured suite.
- [ ] A deliberately introduced regression in one flow (e.g. break county filter) fails exactly that spec.

---

## Appendix A — command cheatsheet

```bash
npm run test:e2e                 # full suite, all 3 viewports
npm run test:e2e:smoke           # @smoke only (fast CI canary)
npx playwright test --grep @data # data-contract tier (real data)
npx playwright test flows/nav.spec.ts --project=mobile  # single spec/viewport
npx playwright test --ui         # interactive debugger
npx playwright show-report       # open last HTML report
```
