# UndePescuim.ro — Unit & Integration Test Plan

**Date:** 2026-08-16
**Author:** plan-maker (t_127c3a36, SPIKE QA-5)
**Mandate:** USER MANDATE (2026-08-16) — test-before-merge for every future logic/data task.
**Status:** PLAN — awaiting human review before implementation.

---

## 1. Goal & Scope

Bring UndePescuim.ro to the same automated-test discipline as the sibling bot
repos (`kindle-deals-bot` = 147 tests, `kindle-deals-nonfiction` = 145 tests,
both pytest). Concretely:

1. **Unit + integration tests** for the app logic (TypeScript) and the data
   pipeline (Python) — the two places where silent regressions already bit us
   (zoom-out bbox rectangles, county clipping leaks, wrong `course_frac`
   ordering, overlay duplicate rivers).
2. **Framework setup** — `vitest` for the TS app, `pytest` for the scripts.
3. **Coverage gates** — ≥80% line coverage on touched modules, enforced in CI.

**Out of scope (explicitly excluded):** visual/leaflet rendering internals,
shadcn/ui primitives, CSS, generated JSON data files, and the ad-hoc
`scripts/_e2e_*.mjs` / `scripts/_qa_*.py` / `scripts/_diag_*.py` one-off
probes (they are promoted *selectively* into pytest where their assertions
are reusable — see §8).

---

## 2. Current State (inventory, verified 2026-08-16)

| Fact | Value |
|---|---|
| Automated tests today | **0** — no `*.test.*` / `*.spec.*` / `test_*.py` anywhere in the repo |
| TS test runner | none — `package.json` has no `test` script, no vitest/jest dep |
| Python test runner | none — no `pytest.ini` / `conftest.py` / `pyproject.toml` |
| Ad-hoc scripts | 122 `scripts/*.py` + 28 `scripts/_e2e_*.mjs` + 8 `scripts/verify_*.js` |
| Sibling convention | pytest, `tests/test_*.py` + `tests/fixtures/` (both bot repos) |
| Node / npm | v22.23.2 / 10.9.8 (package.json uses **npm**, not pnpm) |
| Python | 3.12.3. `.venv` has `shapely 2.1.2` + `numpy 2.5.2` but **no pytest / no requests**; system `python3` has `pytest 9.1.1` + `requests 2.33.0` but **no shapely** |
| tsconfig alias | `"@/*": ["./src/*"]` — vitest must mirror this |
| Git | `github.com/neagastefan99/undepescuim`, branch `main`, no `.github/workflows/` |

**Key gap:** there is *no single Python interpreter with every dependency*.
Pipeline tests need `shapely` (from `.venv`) AND `pytest`. Resolution in §4 —
standardize on `.venv` and add a dev requirements file.

---

## 3. Test Target Matrix

### 3.1 TypeScript — pure functions (vitest, `environment: node`)

| File | Functions to test | Key cases |
|---|---|---|
| `src/utils/geo.ts` | `haversineKm`, `distanceToWaterKm`, `waterToGeoJSON`, `nearestWaters`, `nearestWaterPoint`, `countyOfPoint`, `nearbyCounty`, `watersToFeatureCollection` | see §3.3 |
| `src/utils/county-clip.ts` | `countyClipKey`, `countyRenderGeometry` | diacritics/separator/case normalization; no `geometryByCounty` → full geom; `null` clip → `null` (hide); clip → clip |
| `src/utils/colors.ts` | `getFeatureStyle`, `getPointFallbackStyle`, `getUncontractedStyle`, `getUncontractedLakeStyle` + 8 color constants | the 3 coverage branches each (neutral / covered / uncovered) |
| `src/lib/utils.ts` | `cn` | clsx + tailwind-merge smoke |
| `src/lib/permit.ts` | `NATIONAL_PERMIT_URL`, `NATIONAL_PERMIT_LABEL` | constant smoke (guards accidental edits) |

### 3.2 TypeScript — river-course logic (vitest)

Currently these live in `src/components/map/WaterFeatureLayer.tsx` (a component
that imports `leaflet` + `react-leaflet`). **Exported** today and testable
directly (only `groupKeyOf`/`contractGroup` need a `Water[]`, no leaflet):

`waterKey`, `groupKeyOf`, `sameRiver`, `isMainCourse`, `courseRank`,
`contractGroup`, `contractAtFraction`, `contractInterval`.

**Not exported** today (must be extracted — §5): `orderParts`, `sliceMultiLine`,
`fractionAtPoint`, `partLength`, `haversineKm`.

### 3.3 TypeScript — store + hooks (vitest + jsdom)

| Target | What to assert |
|---|---|
| `src/stores/map-store.ts` | `isFilteredOut` (via actions); `selectAssociation` / `openAssociationSheet` / `selectWater` / `toggleCounty` / `toggleLocality` / `clearLocalities` / `setWaterTypeFilter` / `setContractFilter` / `applyUserPosition` / `clearUserPosition` / `loadData` |
| `src/hooks/use-filtered-waters.ts` | county AND type AND contract AND locality; county-clip `null` → hidden; `contractFilter='necontractate'` → `[]` |
| `src/hooks/use-filtered-uncontracted.ts` | same, plus `contractFilter='contractate'` → `[]` |
| `src/hooks/use-localities.ts` | county-scoped dedupe + `localeCompare('ro')` sort; empty when no county |
| `src/hooks/use-counties.ts` | dedupe + RO sort over both pools |

### 3.4 TypeScript — API route (vitest integration)

| Target | Cases |
|---|---|
| `src/app/api/report/route.ts` | `invalid_json` (400), `invalid_reason` (400), `missing_water` (400), honeypot `website` → silent `{ok:true,issueUrl:null}`, missing `REPORT_GITHUB_TOKEN` → 503, GitHub non-OK → 502, success → 200 `{ok:true,issueUrl}`. Mock `global.fetch`. |

### 3.5 Python — data pipeline (pytest)

The named "data chain" (per the SPIKE brief):

| Script | Pure functions to test | Notes |
|---|---|---|
| `scripts/_mapping_common.py` | `_county_key`, `canonical_county`, `slugify`, `assoc_slug`, `geom_bbox`, `merge_geoms`, `set_geometry`, `ordered_parts`, `order_course_linestring`, `ordered_fractions`, `km_to_frac`, `fraction_at_point`, `haversine_km`, `pick_cluster` | **shared by most scripts — highest-value module** |
| `scripts/match_small_rivers.py` | `norm`, `build_name_index`, `similarity`, `match_water`, `make_feature` | mock `requests`/Overpass; relation-vs-way preference; fuzzy ≥0.6 |
| `scripts/merge_anpa_waters.py` | `norm`, `anpa_subtype`, `osm_geometry_for`; merge add/upgrade/skip | idempotent rebuild (run twice → identical bytes) |
| `scripts/assign_course_frac.py` | `norm`, `haversine`, `order_parts`, `fraction_at`, `build_queries`, `county_seat`, `geocode_any` | mock Nominatim; county-seat fallback order |
| `scripts/sweep_uncontracted_overlay.py` | `river_core_name`, `name_match`, `classify_river_hit`, `classify_lake_hit`, `load_geoms` | every label + the 2-pt-chord guard + PARTIAL_DUPLICATE part logic |
| `scripts/build_county_clip_geoms.py` | clip builder (extract pure clip fn if not already) | **river on county border** boundary case |
| `scripts/build_locality_assignment.py` | locality-resolution chain | ungeocoded fallback order |

### 3.6 Cross-language parity (golden tests) — HIGH VALUE

The **same** geometry math is implemented twice:
- TS: `orderParts` / `sliceMultiLine` / `fractionAtPoint` (WaterFeatureLayer.tsx)
- Python: `ordered_parts` / `km_to_frac` / `fraction_at_point` (_mapping_common.py)

They MUST agree or a `course_frac` computed offline won't match the click a
user makes on the map. Add **shared fixture geometries** (a winding
MultiLineString, a fragmented river, a duplicated-way course) and assert both
implementations return identical `fraction_at_point` / ordered-part endpoints.
This is the single most valuable regression test in the plan — it directly
guards the `Pârâu Buzăul Mijlociu`-class ordering bugs (t_9a7cf783, t_f4ff3853).

---

## 4. Framework Setup

### 4.1 TypeScript — vitest

```bash
npm i -D vitest @vitest/coverage-v8 jsdom \
  @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

`vitest.config.ts` (repo root):

```ts
import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      include: ['src/utils/**', 'src/stores/**', 'src/hooks/**', 'src/lib/**', 'src/app/api/**'],
      thresholds: { lines: 80, functions: 80, statements: 80, branches: 75 },
    },
  },
});
```

`vitest.setup.ts`:

```ts
import '@testing-library/jest-dom/vitest';
```

Pure-function tests opt out of jsdom per-file: `// @vitest-environment node`
at the top of `src/utils/*.test.ts` and `src/lib/*.test.ts`.

`package.json` scripts:

```json
"test": "vitest run",
"test:watch": "vitest",
"test:coverage": "vitest run --coverage"
```

**Leaflet caveat:** do NOT import `leaflet`/`react-leaflet` in unit tests. This
is why §5 extracts the pure helpers out of `WaterFeatureLayer.tsx`. Component
tests that need `<MapContainer>` are deferred (out of scope) — they need a
`jsdom` + canvas/leaflet mock that adds noise for little signal right now.

### 4.2 Python — pytest

```bash
cd ~/undepescuim
.venv/bin/pip install pytest
# persist the dev deps so CI + future devs reproduce it:
.venv/bin/pip freeze > requirements-dev.txt   # or hand-write: pytest, shapely, numpy
```

Standardize on `.venv` for **all** pipeline runs and tests (it already has
shapely/numpy; add pytest there rather than splitting across system python).

`pyproject.toml` (repo root) — pytest config + import path for the shared
`scripts/` modules (`_mapping_common`, `audit_missing_rivers`):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["scripts"]
addopts = "-ra -q"
```

Layout (mirrors the bot-repo convention):

```
tests/
├── fixtures/                       # small sample GeoJSON / JSONL / OSM payloads
│   ├── waters_sample.json
│   ├── anpa_sample.jsonl
│   ├── osm_relation_fragment.json
│   └── winding_river.geojson
├── test_mapping_common.py
├── test_match_small_rivers.py
├── test_merge_anpa_waters.py
├── test_assign_course_frac.py
├── test_sweep_uncontracted_overlay.py
└── test_parity_vs_frontend.py      # cross-language golden tests (§3.6)
```

### 4.3 Determinism rule (all pipeline tests)

- **Never hit the network** — monkeypatch `requests.get`/`requests.post`,
  Nominatim, Overpass, GitHub. Use fixtures.
- **No wall clock** — `match_small_rivers` writes `generated_at` with
  `datetime.now()`; the determinism test must either patch it or compare only
  the `features` payload.
- **Hash-identical rebuild**: every merge/assign script must pass "run twice →
  `sha256` of output JSON unchanged" (idempotency).
- **No sqlite/geocode.db dependency** in unit tests — pass data in, assert
  results out. `geocode.db` is only exercised by an optional integration test.

---

## 5. Refactor Prerequisites (no behavior change)

These small extractions unblock direct testing and are required before the
corresponding tests can be written:

1. **Extract river-course math** from `WaterFeatureLayer.tsx` into a new
   `src/utils/river-course.ts`, exporting: `haversineKm`, `partLength`,
   `orderParts`, `sliceMultiLine`, `fractionAtPoint`, plus the already-public
   `waterKey`, `groupKeyOf`, `sameRiver`, `isMainCourse`, `courseRank`,
   `contractGroup`, `contractAtFraction`, `contractInterval`.
   `WaterFeatureLayer.tsx` re-imports them (no logic change).
2. **Export `geometryParts`** from `src/utils/geo.ts` (currently private) —
   needed to test `nearestWaterPoint` on Polygon/MultiPolygon directly.
3. **Keep `isFilteredOut` private** but cover it through the store actions
   (it's already exercised by `toggleCounty`/`toggleLocality`/`setWaterTypeFilter`).

---

## 6. Coverage Policy & Gates

- **≥80% line / function / statement** and **≥75% branch** on *touched*
  modules — the vitest config above enforces it as a hard CI gate.
- **Mandatory baseline:** `src/utils/**`, `src/stores/**`, `src/hooks/**`,
  `src/lib/**`, `src/app/api/**` and the named pipeline scripts
  (`_mapping_common`, `match_small_rivers`, `merge_anpa_waters`,
  `assign_course_frac`, `sweep_uncontracted_overlay`).
- **Excluded from coverage:** `src/components/**` rendering, shadcn/ui,
  `src/content/**`, generated `public/data/**`.
- **Test-before-merge (user mandate):** every future task that touches logic
  or the data pipeline ships tests in the same PR. No test = blocked at review.
- Python coverage via `pytest --cov` if the team wants a numeric gate there;
  minimum is "every named pipeline function has at least one case" (§3.5).

---

## 7. CI Integration

Add `.github/workflows/test.yml` (the repo has none today — the
`data-refresh.yml` in ARCHITECTURE.md was aspirational):

```yaml
name: test
on: [push, pull_request]
jobs:
  ts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npm test -- --coverage        # fails under the 80% threshold
  py:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements-dev.txt
      - run: pytest
```

---

## 8. Promote (absorb) existing ad-hoc checks

The throwaway scripts contain real assertions worth keeping:

- `scripts/_verify_county_clip.py` → become `tests/test_county_clip.py` cases.
- `scripts/validate_geometry_county.py`, `scripts/audit_regions.py` → invariants
  to encode as pytest tests over `public/data/*.json` (schema + county-consistency
  smoke, run on the committed snapshot).
- `scripts/collect_test_points.py` → seed for the parity fixtures (§3.6).
- The `_e2e_*.mjs` remain manual tooling for now (browser automation is a
  separate future spike); their assertions are *documented* but not ported.

---

## 9. Step-by-Step Execution Plan

Each step is small (2–5 min) and independently committable.

1. `npm i -D vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event`; add `vitest.config.ts`, `vitest.setup.ts`, the three `test*` scripts.
2. Add `.venv/bin/pip install pytest` + write `requirements-dev.txt` + `pyproject.toml [tool.pytest.ini_options]`; `mkdir tests tests/fixtures`.
3. Refactor §5.1 — extract `src/utils/river-course.ts`; re-import in `WaterFeatureLayer.tsx`; run `npm run build` to prove no breakage.
4. Refactor §5.2 — export `geometryParts` in `src/utils/geo.ts`.
5. Write `src/utils/geo.test.ts` (haversine known distances, `distanceToWaterKm` bbox/coords/Infinity/NaN, `waterToGeoJSON` geometry/bbox-fallback/hidden, `nearestWaters`, `nearestWaterPoint`, `countyOfPoint` in/out).
6. Write `src/utils/county-clip.test.ts` + `src/utils/colors.test.ts` + `src/lib/utils.test.ts` + `src/lib/permit.test.ts`.
7. Write `src/utils/river-course.test.ts` (`waterKey`/`groupKeyOf`/`sameRiver`/`isMainCourse`/`courseRank`/`contractGroup`/`contractAtFraction`/`contractInterval`, `orderParts`/`sliceMultiLine`/`fractionAtPoint`).
8. Write `src/stores/map-store.test.ts` (reset store via `useMapStore.setState(...)` between tests; cover R9/R10, `selectWater` belongs/outside + suppression flag, adaptive radius 25→50→fallback, `loadData` fetch mock).
9. Write hook tests (`use-filtered-waters`, `use-filtered-uncontracted`, `use-localities`, `use-counties`) with `renderHook` + `@testing-library/react`.
10. Write `src/app/api/report/route.test.ts` (mock `global.fetch`; all response codes).
11. Write `tests/test_mapping_common.py` (canonical_county 42-map, `ordered_parts`/`order_course_linestring` dedupe/orient/chain, `km_to_frac`, `fraction_at_point`).
12. Write `tests/test_match_small_rivers.py` + `tests/test_merge_anpa_waters.py` (idempotency) + `tests/test_assign_course_frac.py` + `tests/test_sweep_uncontracted_overlay.py`.
13. Write `tests/test_parity_vs_frontend.py` (shared fixture geoms → identical fractions both sides).
14. Add `.github/workflows/test.yml`.
15. Run the full suite locally; fix until green; confirm coverage ≥80%.

**Verify commands:**

```bash
npm test -- --coverage          # TS: all green + ≥80%
.venv/bin/python -m pytest      # Python: all green
npm run build                   # prove refactors didn't break the app
```

---

## 10. Risks & Tradeoffs

| Risk | Mitigation |
|---|---|
| Adding vitest to a Next 16 app (alias, jsdom, React 19) can be finicky | Keep pure tests on `node` env; alias in `vitest.config.ts`; component tests deferred |
| `WaterFeatureLayer` helpers not exported | §5 extraction — mechanical, verified by `npm run build` |
| Split Python env (venv ≠ system) | Standardize on `.venv`; `requirements-dev.txt` pins pytest+shapely+numpy |
| Pipeline scripts are network/DB-heavy | Test only the pure functions + fixtures; monkeypatch I/O; determinism rule (§4.3) |
| TS↔Python math drift | Parity golden tests (§3.6) make divergence impossible to ship silently |
| Zustand module singleton leaks state between tests | Explicit `useMapStore.setState(<initial>)` in `beforeEach` |
| Coverage gate too strict on day one | Threshold applies to *touched* modules only; excluded dirs listed in §6 |

---

## 11. Acceptance Criteria (for the reviewer)

- [ ] `npm test` green with `vitest` configured and `@` alias working.
- [ ] `.venv/bin/python -m pytest` green, `tests/fixtures/` populated.
- [ ] `src/utils/river-course.ts` exists and `WaterFeatureLayer.tsx` imports from it (no logic change).
- [ ] Store, hooks, geo, county-clip, colors, API-route, and all 5 named pipeline modules have tests.
- [ ] Parity test asserts TS == Python for at least one winding MultiLineString fixture.
- [ ] `.github/workflows/test.yml` runs both suites and enforces ≥80% coverage.
- [ ] `npm run build` still passes after the refactors.
