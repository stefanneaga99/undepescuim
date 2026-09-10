# Acceptance candidate validation — `824933557cd038777047b6a625ace31edbd02ab4`

Status: **candidate for independent review only**. This is not an acceptance or deployment authorization.

Rollback mapping: Production rollback remains `e85b1f3867f87fb6ed33b3f1e73606d8e8a767b7`.
Branch: `wt/t_8ec005f9`

## Browser acceptance

- Live suite, exact desktop/mobile projects, workers=1, retries=0: **8/8 passed** in each of three consecutive runs.
  - Run 1: `test-results/acceptance-live-1`
  - Run 2: `test-results/acceptance-live-2`
  - Run 3: `test-results/acceptance-live-3`
- Live report API test uses Playwright route interception; no real report is created.
- Local report flow at 390x844 and 1280x800, workers=1, retries=0: **20 passed, 2 intentional desktop mobile-only skips**. All six A→B transition scenarios passed (single/multi contract × direct/close/success).
- The live map probe uses connected SVG stroke sampling, browser hit-chain validation, real mouse input, and named water identity assertions. The before/after investigation traces and screenshots are retained by the upstream evidence commit `d7612a902e8dbd0ab59ff7e5a8a4de635d4baac6` (`docs/investigations/map-dead-zone.md`, `map-dead-zone-trace.json`, and four viewport screenshots).
- Hydration/error behavior: the three live runs completed without test failures, console exceptions, or hydration errors.

## Automated gates

- `npm test -- --coverage`: **260 passed**; statements 86.88%, branches 77.34%, functions 85.41%, lines 88.38%.
- `python3 -m pytest`: **174 passed**.
- `npx tsc --noEmit`: **passed**.
- `npm run lint`: **passed**, one pre-existing unused `PositionError` warning.
- `npm run build`: **passed** (Next.js 16.3.1 webpack production build).
- `npm run perf:budget`: **passed** (M7 1.47 MB gzip, M8 1.23 MB gzip, M9 5.72 MB compact).

## Canonical data hashes

Verified in this checkout; the canonical water/association/ownership payload hashes match the upstream candidate handoff:

```text
public/data/waters.json              56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0
public/data/associations.json        388ff8ef7efc267914d3a67a20f2f5a9230dd6bc0a0fdf9b87188b8f2fbaafa9
public/data/uncontracted_rivers.json 06414eb6c569770513c10d90d8a68d3338d7f4508ef5c7d76cb20add195db4dd
public/data/uncontracted_lakes.json  59c9b9969f3c501e06bdabc2cf33d06e4ccf1c055680169264cbce636e17f44e
public/data/uncontracted_majors.json d3a0d657d28fa74cadbd8e0ab28ae78f15eac756993e4190071d94889101256c
public/data/association_locations.json bc54ab5ce74c07e282ac2d1f51b16247180d2d5bfd5e3389f2c11735a9c6b9a7
public/data/counties.geojson         3b6c0dc382db4d61707f133db7d9876c80981a9f3d74e84ed19651c298d81ac5
public/data/meta.json                0b13b2e44d474b5c21589b467a5fba2e658aff5cfadfec9cc431113d92419974
```

The repository has no file named `geometry-ledger`; no hash is fabricated. The tracked deterministic geometry fixture is `tests/fixtures/same_day_regression_ledger.json` (SHA-256 `fcf43bda3f7fe68e6cef36ef2a2f289cf19e643091f9860ff4c524508b8bb0b3` on both consecutive reads); the full pytest suite passed its ledger/parity tests.

## Candidate scope

The candidate contains only the live map targeting and asynchronous preview/consent-test isolation changes from commits `98b956e` and `8249335`; no production hydration suppression, blanket client-only conversion, arbitrary delay, legal baseline, ownership data, canonical geometry, or report endpoint change was added.
