# Integrated mobile test report

Run date: 2026-08-20 (UTC)
Tested commit: `a9c977cd0b5ac043b7ade974d65bd732aeb6e922`
Environment: WSL2, Node.js 22.23.2, npm, Chromium emulation, Playwright/@playwright-test 1.62.1
Application: production build served at `http://127.0.0.1:3114`

This report consolidates the functional, offline/PWA, accessibility, storage/request, and performance evidence from the integrated mobile run. It supersedes the earlier first-pass counts in [mobile-regression-performance-results.md](mobile-regression-performance-results.md) for release-gate status; the later run is the authoritative result for this tested commit.

## Executive result

The functional acceptance criteria pass for the supported Chromium-emulation matrix. The overall mobile release gate does **not** pass: three supported-lab performance budgets fail. Native-device, physical Slow 2G, physical cache-pressure, and OS-eviction criteria remain unverified rather than being treated as passes.

| Area | Result | Evidence |
|---|---|---|
| Six-profile functional/regression matrix | **434 passed, 2 known environment-invalid failures, 32 intentional skips** / 468 | `test-results/mobile-matrix-t_6e43b4f4-r2/e2e.log` |
| Focused offline/network contracts | **18 passed** across all six profiles | `tests/e2e/specs/regression/mobile-offline-network.spec.ts` rerun |
| Accessibility and touch targets | **Pass** in the matrix | `tests/e2e/specs/accessibility.spec.ts` |
| Offline/PWA/cache contracts | **Pass** in supported emulation | `test-results/mobile-matrix-t_6e43b4f4-r2/e2e.log` |
| Performance budgets | **Fail: M6, M11, M12; pass: M5, M10, M13, M14** | `performance.log` |
| Native iOS/Android and physical Slow 2G | **Not run** | WSL target limitation |

## Target and browser coverage

The matrix ran each area against these six emulated projects:

- `iphone-current` — iPhone 15 target profile, Chromium emulation
- `iphone-previous` — iPhone 14 target profile, Chromium emulation
- `pixel-current` — Pixel 7 target profile, Chromium emulation
- `pixel-previous` — Pixel 5 target profile, Chromium emulation
- `samsung-current` — Galaxy S24 target profile, Chromium emulation
- `samsung-previous` — Galaxy S21 target profile, Chromium emulation

The performance probe used a 390x844 viewport, Fast 3G (1.6 Mbps, 150 ms RTT), and 4x CPU throttling. The matrix also exercises the repository's tablet and desktop projects as part of the configured run, but this report makes no native-browser claim for any project.

Unavailable targets: native iOS Safari, physical Android Chrome, physical Slow 2G (300 ms RTT / 50 Kbps down and up), physical OS cache eviction/pressure, and hardware memory measurements.

## Commands and fixture versions

The reproducible integrated command was:

```bash
E2E_PORT=3114 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-t_6e43b4f4-r2 npm run mobile:matrix
```

The runner executes the six projects with one worker, then the performance probe. The equivalent focused contract rerun was:

```bash
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true PLAYWRIGHT_BASE_URL=http://127.0.0.1:3114 \
  npx playwright test --project=iphone-current --project=iphone-previous \
  --project=pixel-current --project=pixel-previous \
  --project=samsung-current --project=samsung-previous \
  tests/e2e/specs/regression/mobile-offline-network.spec.ts --workers=1 --reporter=line
```

The performance conditions and command were:

```bash
PERF_THROTTLE=1 node scripts/_perf_map.mjs http://127.0.0.1:3114
```

Relevant fixture versions are source-controlled in `tests/e2e/fixtures/mobile-data.ts` and `mobile-metrics.ts`: schema version is read from `OFFLINE_SCHEMA_VERSION`; fixture clock is `2026-08-20T12:00:00.000Z`; stale snapshots are exactly 29 days (`2026-07-22T12:00:00.000Z`) and 30 days (`2026-07-21T12:00:00.000Z`); twelve cache regions contain eight deterministic tile URLs each. The tested application dependencies include Next 16.3.1, React 19.2.8, Leaflet 1.9.4, and Playwright 1.62.1.

## Functional coverage and status

All supported functional areas passed in the final matrix. This includes app/map startup and no-console-error smoke, county/locality and contract filters, association search/highlight/detail/clear semantics, water detail and map-segment hit coverage, nearby/geolocation flows, report success/rejection/reconnect contracts, `/specii`, `/permis`, navigation, Romanian/English switching, dark mode, 404 and edge cases, PWA installability/offline reload/freshness/cache behavior, data-contract checks, and mobile accessibility.

The accessibility suite passed its named-landmark/control and keyboard-focus checks plus the 44px touch-target checks for every emulated profile. The offline/network suite passed all 18 focused checks: online-to-offline transition observation, exact 29/30-day staleness behavior, no false offline report success, and one permitted report POST after reconnect.

The two failed tests are not defects in the tested changes:

- `pixel-current` `live-prod.spec.ts` map/dead-zone check
- `pixel-current` `live-prod.spec.ts` report-dialog check

They target the deployed production URL while this run was intentionally against the isolated local matrix server. They are therefore invalid local-environment assertions, not supported-target failures. The 32 skips are intentional data-excluded cases recorded by the runner, not passes or failures.

## Performance, storage, and request findings

| Metric | Gate/baseline | Observed | Status |
|---|---:|---:|---|
| M5 unexpected CLS | <= 0.001 | 0.0000; 0 shifts | **PASS** |
| M6 first map paint | < 5.0 s | 11.86 s | **FAIL** |
| M10 initial JS gzip | < 300 KiB | 215.4 KiB | **PASS** |
| M11 data fetch + parse | < 2.5 s | 9.62 s | **FAIL** |
| M12 max pan/zoom long task | <= 100 ms | 320 ms | **FAIL** |
| M13 peak Chromium JS heap | < 200 MiB | 73 MiB | **PASS** |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | **PASS** |

The performance resource baseline was 1,741 KiB on wire: `waters.json` 1,485 KiB / 8.90 s, `uncontracted_majors.json` 168 KiB / 2.31 s, `counties.geojson` 77 KiB / 1.39 s, and smaller metadata/association resources. The M12 run recorded additional long tasks of 253, 193, 153, and 147 ms.

The storage probe after two online loads measured quota 3,231,444,554 bytes and total usage 10,219,082 bytes: IndexedDB 5,429,799 bytes and Cache Storage 4,789,283 bytes. The visible precache contained 55 entries and 178,015 response bytes. Offline reload caused two total requests, with zero `/data/` requests; reconnect caused zero `/data/` requests. These are Chromium-lab measurements, not physical-device eviction evidence.

## Actionable follow-up issues

1. **High — first map paint regression (M6).** Observed 11.86 s versus the <5.0 s gate under Fast 3G/4x CPU. Reproduce with the integrated command, then inspect `performance.log` and the browser trace for the startup critical path. Prioritize reducing or deferring the 1,485 KiB `waters.json` transfer/parse and measure again on all six profiles.
2. **High — data fetch/parse regression (M11).** Observed 9.62 s versus the <2.5 s gate. Reproduce with `PERF_THROTTLE=1 node scripts/_perf_map.mjs http://127.0.0.1:3114`; profile fetch, JSON parsing, normalization, and map-layer construction separately. Compare the resulting trace against the 2.5 s baseline.
3. **Medium — pan/zoom main-thread jank (M12).** Observed 320 ms maximum long task versus <=100 ms, with additional 253/193/153/147 ms tasks. Reproduce the same performance command and profile the zoom from 7 to 11; reduce synchronous layer/style work or batch it, then rerun M12 and M14 together.
4. **Release-blocking evidence gap — native targets.** Run the checklist on iPhone 15/14 Safari, Pixel 7/5 Chrome, and Galaxy S24/S21 Chrome. Record literal OS/browser versions, startup/first-map-paint, request counts, offline/reconnect behavior, storage/cache growth, and unavailable metrics as `not-run` rather than pass.
5. **Release-blocking evidence gap — Slow 2G and cache pressure.** Repeat network-sensitive flows at 300 ms RTT/50 Kbps and exercise physical cache eviction/growth. The current WSL run cannot establish these results.

## Acceptance decision

The supported Chromium-emulation functional criteria are met, and the artifacts are reproducible and linked from the mobile matrix documentation. The integrated mobile release acceptance criteria are **not met** because M6, M11, and M12 exceed their approved budgets and required native/Slow-2G evidence is absent. Reopen acceptance after the three performance issues are triaged or waived by the release owner and the native evidence gaps are completed or explicitly dispositioned.

Artifacts: `test-results/mobile-matrix-t_6e43b4f4-r2/{summary.json,e2e.log,performance.log,report}`.
