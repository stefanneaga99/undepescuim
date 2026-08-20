# Mobile coverage, results, and follow-up report

Run date: 2026-08-20 (UTC)
Tested commit: `1dca26fc199cc4499a2f312a110420acce5ab6fa`
Environment: WSL2 (`Linux DESKTOP-J7FOLV9 6.18.33.2-microsoft-standard-WSL2`, x86_64), Node 22.23.2, npm 10.9.8, Playwright 1.62.1, production Next build, Chromium emulation.
Application: isolated production server at `http://127.0.0.1:3110`

This is the authoritative report for the latest integrated run. The run-specific matrix record is [mobile-regression-matrix-run-2026-08-20.md](mobile-regression-matrix-run-2026-08-20.md); the release-gate definitions and target mapping are in [mobile-regression-performance-matrix.md](mobile-regression-performance-matrix.md).

## Executive decision

The six supported Chromium-emulation profiles pass the functional, offline/PWA, accessibility, data-contract, and report-flow coverage. Overall mobile release acceptance is **not met**: M6, M11, and M12 exceed their approved budgets, and native-device, physical Slow 2G, physical cache-pressure/eviction, and hardware-memory evidence is unavailable. No unsupported target is presented as passing.

## Target and scenario coverage

| Target | Automated configuration | Result |
|---|---|---|
| iPhone 15 (`iphone-current`) | Chromium emulation | Pass; intentional data-excluded skips only |
| iPhone 14 (`iphone-previous`) | Chromium emulation | Pass; intentional data-excluded skips only |
| Pixel 7 (`pixel-current`) | Chromium emulation | Pass for supported local matrix; two local-invalid live-production checks recorded below |
| Pixel 5 (`pixel-previous`) | Chromium emulation | Pass; intentional data-excluded skips only |
| Galaxy S24 (`samsung-current`) | Chromium emulation | Pass; intentional data-excluded skips only |
| Galaxy S21 (`samsung-previous`) | Chromium emulation | Pass; intentional data-excluded skips only |

The matrix ran 474 tests serially with one worker: **440 passed, 2 known environment-invalid failures, and 32 intentional skips**. The skips are data-excluded cases, not passes or product failures. Each profile exercised the configured functional suite; the failures were isolated to `pixel-current` and did not affect the supported local assertions.

Covered scenarios include:

- startup/map rendering, no-console-error smoke, filters, county/locality, map-segment hit coverage, and water detail;
- association search, highlight, detail, clear/no-zoom semantics, nearby/geolocation, and navigation;
- report success, validation, rejection, offline denial, reconnect, and focus preservation;
- `/specii`, `/permis`, 404/edge cases, Romanian/English switching, dark mode, and PWA installability;
- service-worker offline reload, freshness/staleness boundaries, visited-only tile caching, TTL/eviction policy, and no tile prefetch;
- data contracts, mobile landmarks/keyboard focus, and 44px touch targets.

The focused offline/network contract completed **18/18 checks across all six profiles**, including the exact 29/30-day stale boundary, offline request isolation, cache-growth reporting, prevention of false success for offline report submissions, and the online-only report contract.

## Commands and environment

```bash
npm run mobile:reset
E2E_PORT=3110 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-20260820T171800Z npm run mobile:matrix
```

The runner built the production app, started one isolated server, ran the six projects, and executed the performance probe. The first port-3100 attempt was stopped before tests because an unrelated listener occupied that port; the port-3110 rerun is the retained result. The performance condition was 390x844, Fast 3G (1.6 Mbps down, 750 Kbps up, 150 ms RTT), and 4x CPU.

Focused contract reproduction:

```bash
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true PLAYWRIGHT_BASE_URL=http://127.0.0.1:3110 \
  npx playwright test --project=iphone-current --project=iphone-previous \
  --project=pixel-current --project=pixel-previous \
  --project=samsung-current --project=samsung-previous \
  tests/e2e/specs/regression/mobile-offline-network.spec.ts --workers=1 --reporter=line
```

## Performance and storage compliance

| Metric | Approved gate | Observed | Status |
|---|---:|---:|---|
| M5 unexpected interaction CLS | < 0.001 | 0.0000 (0 shifts) | **PASS** |
| M6 first map paint | < 5.0 s | 11.95 s | **FAIL** |
| M10 initial JS gzip | < 300 KiB | 215.4 KiB | **PASS** |
| M11 data fetch + parse | < 2.5 s | 9.66 s | **FAIL** |
| M12 largest pan/zoom long task | <= 100 ms | 319 ms | **FAIL** |
| M13 peak Chromium JS heap | < 200 MiB | 65 MiB | **PASS** |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | **PASS** |

The on-wire resource total was 1,741 KiB: `waters.json` 1,485 KiB, `uncontracted_majors.json` 168 KiB, `counties.geojson` 77 KiB, and smaller association/meta resources. Recorded long tasks included 319, 259, 199, 157, and 151 ms. These are reproducible in `performance.log` and are regressions against the approved budgets, not native-device claims.

The supported emulation suite passed bounded visited-only cache behavior, no tile prefetch, TTL/eviction rules, and offline request isolation. The accompanying Chromium storage probe measured quota 3,231,444,554 bytes and usage 10,219,082 bytes after two online loads (IndexedDB 5,429,799 bytes; Cache Storage 4,789,283 bytes), with 55 visible precache entries and 178,015 response bytes. Offline reload made two total requests with zero `/data/` requests; reconnect made zero `/data/` requests. These are lab measurements and do not establish physical OS eviction behavior.

## Actionable defects and follow-up

1. **High — M6 first-map-paint budget failure.** Observed 11.95 s versus `<5.0 s` under Fast 3G/4x CPU. Reproduce with the matrix command and inspect the trace/performance log. Prioritize reducing or deferring the 1,485 KiB `waters.json` critical path. Suggested owner: map/data startup performance.
2. **High — M11 data fetch/parse budget failure.** Observed 9.66 s versus `<2.5 s`. Reproduce with `PERF_THROTTLE=1 node scripts/_perf_map.mjs http://127.0.0.1:3110`; profile fetch, JSON parse/normalization, and layer construction separately. Suggested owner: data loading/map initialization.
3. **Medium — M12 pan/zoom jank.** Observed 319 ms versus `<=100 ms`, with additional 259/199/157/151 ms tasks. Reproduce the same performance command, profile zoom 7→10, and batch or defer synchronous layer/style work; rerun M12 and M14 together. Suggested owner: map rendering.
4. **Release-blocking evidence gap — native targets.** Run F1–F10 on iPhone 15/14 Safari, Pixel 7/5 Chrome, and Galaxy S24/S21 Chrome. Record literal OS/browser versions, request counts, offline/reconnect behavior, storage/cache growth, and `not-run` for unavailable metrics. Suggested owner: device-lab/release QA.
5. **Release-blocking evidence gap — physical Slow 2G and cache pressure.** Repeat network-sensitive scenarios at 300 ms RTT/50 Kbps and exercise physical cache eviction/growth. The WSL2 lab cannot establish these results. Suggested owner: device-lab/release QA.

## Known invalid, flaky, and inconclusive results

- The two failures are `pixel-current` `tests/e2e/specs/live-prod.spec.ts` checks: sampled water path/card and report-dialog setup. They target the deployed production URL while this run used the isolated local server, so they are **environment-invalid**, not product regressions. Evidence: `playwright/live-prod-*pixel-current/{error-context.md,test-failed-1.png,video.webm}`.
- No product flake was identified in the retained run. The earlier offline CDP race was fixed before this run; the focused offline rerun passed 18/18.
- Native Safari, physical Android Chrome, physical Slow 2G, physical cache-pressure/eviction, and hardware memory are unavailable in WSL2 and require reruns on devices. They remain inconclusive, not passed.

## Artifacts

- Matrix summary: `test-results/mobile-matrix-20260820T171800Z/summary.json`
- Full functional output: `test-results/mobile-matrix-20260820T171800Z/e2e.log`
- Performance output: `test-results/mobile-matrix-20260820T171800Z/performance.log`
- Playwright HTML report, traces, screenshots, and videos: `test-results/mobile-matrix-20260820T171800Z/playwright/`

Acceptance can be reopened after M6/M11/M12 are triaged or explicitly waived and the native, Slow 2G, and physical cache evidence gaps are completed or dispositioned.
