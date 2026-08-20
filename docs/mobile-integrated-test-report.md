# Integrated mobile regression and performance report

Run date: 2026-08-20 (UTC)
Tested commit: `64c5d38f1d33f589d92a53d22b583f9409e9b41c`
Environment: WSL2 (`Linux DESKTOP-J7FOLV9`), x86_64, Node 22.23.2, npm 10.9.8, Playwright 1.62.1, production Next build, Chromium emulation.
Application: isolated production server at `http://127.0.0.1:3112`

## Decision

Functional Chromium-emulation coverage is acceptable with two explicitly environment-invalid live-production checks. Release acceptance is **not met**: M6, M11, and M12 exceed their approved budgets, and native-device, physical Slow 2G, physical cache-pressure/eviction, and hardware-memory evidence is unavailable. No unavailable target is reported as passing.

## Coverage and commands

Six serial Chromium profiles (one worker) represent current/previous iPhone 15/14, Pixel 7/5, and Galaxy S24/S21 configurations:

```text
E2E_PORT=3112 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-task-t_352fa39b PERF_THROTTLE=1 npm run mobile:matrix
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true PLAYWRIGHT_BASE_URL=http://127.0.0.1:3112 \
  npx playwright test --project=iphone-current --project=iphone-previous \
  --project=pixel-current --project=pixel-previous \
  --project=samsung-current --project=samsung-previous \
  tests/e2e/specs/regression/mobile-offline-network.spec.ts --workers=1 --reporter=line
```

The integrated run executed 480 tests: **446 passed, 2 failed, 32 intentional skips, 0 flaky**. The 32 skips are data-excluded cases, not passes. The focused offline/network assertions are included for all six profiles: offline/reconnect, exact 29/30-day staleness, bounded visited-region cache growth/eviction, offline request isolation, offline report false-success prevention, and one reconnect POST; all 18/18 checks passed.

Coverage includes startup/map rendering, filters and map selection, county/locality, association and nearby flows, report validation/success/rejection/offline/reconnect, navigation, i18n, dark mode, PWA, data contracts, landmarks/focus/44px targets, service-worker freshness/cache policy, and no tile prefetch.

## Performance gates

Condition: 390x844, Fast 3G (1.638 Mbps down / 0.768 Mbps up, 150 ms RTT), CPU 4x.

| Metric | Threshold | Observed | Result |
|---|---:|---:|---|
| M5 unexpected interaction CLS | < 0.001 | 0.0000 (0 shifts) | PASS |
| M6 first map paint | < 5.0 s | 11.93 s | FAIL — High |
| M10 initial JS transfer | < 300 KiB | 215.4 KiB | PASS |
| M11 data fetch + parse | < 2.5 s | 9.68 s | FAIL — High |
| M12 largest pan/zoom long task | <= 100 ms | 265 ms | FAIL — Medium |
| M13 peak Chromium JS heap | < 200 MiB | 54 MB | PASS |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | PASS |

On-wire data transfer was 1,783,175 bytes (1,741 KiB), including `waters.json` 1,485 KiB, `uncontracted_majors.json` 168 KiB, and `counties.geojson` 77 KiB. Storage was 16,026,451 / 3,237,251,923 bytes (0.50%); cache counts were precache 57, app-data 2, and OSM tiles 6, with 475,433 response bytes. Offline transition took 25 ms and generated **zero new resource requests**.

## Failures and dispositions

1. **High / actionable: M6 first-map paint.** 11.93 s vs <5.0 s. Reproduce with the matrix command and inspect `performance.log`/`mobile-performance.json`; prioritize reducing or deferring the 1,485 KiB `waters.json` critical path.
2. **High / actionable: M11 data fetch+parse.** 9.68 s vs <2.5 s. Profile fetch, JSON parse/normalization, and layer construction using the same matrix/performance command; optimize data loading independently of M6.
3. **Medium / actionable: M12 pan/zoom jank.** 265 ms vs <=100 ms, with additional 198/166/164/131 ms tasks. Reproduce with the performance probe and profile zoom 7→11; batch/defer synchronous layer/style work, then rerun M12 and M14.
4. **Environment-invalid, not a product regression:** the two `pixel-current` `live-prod.spec.ts` failures (`sampled water paths` and `report-dialog ... API safely stubbed`) target the deployed production URL while the integrated run intentionally used the isolated local server. Evidence is retained under `test-results/mobile-matrix-task-t_352fa39b/playwright/`; rerun against the live URL before release.

## 2G and unavailable targets

A constrained Chromium Slow 2G diagnostic was attempted with `PERF_NETWORK_PROFILE=slow2g PERF_THROTTLE=1 node scripts/_perf_map.mjs http://127.0.0.1:3113` (50 Kbps, 300 ms RTT, CPU 4x). It did not produce a valid measurement: the probe exceeded the 180-second execution limit while waiting for `__perfDataLoaded`, and Playwright then reported the page had closed. This is recorded as **not-run/inconclusive**, not a pass.

The following remain not-run and release-blocking: native iOS Safari on iPhone 15/14; physical Android Chrome on Pixel 7/5 and Galaxy S24/S21; physical Slow 2G on iOS/Android; physical OS cache-pressure/eviction; and hardware memory. WSL2 has no attached devices and cannot establish native browser, physical network, OS eviction, or hardware-memory behavior. Run F1–F10 on each device, recording literal OS/browser versions and pass/fail/not-run for unavailable metrics.

## Artifacts

- `test-results/mobile-matrix-task-t_352fa39b/summary.json`
- `test-results/mobile-matrix-task-t_352fa39b/e2e.log`
- `test-results/mobile-matrix-task-t_352fa39b/performance.log`
- `test-results/mobile-matrix-task-t_352fa39b/mobile-performance.json`
- `test-results/mobile-matrix-task-t_352fa39b/playwright/` (HTML/report traces, screenshots, and videos)
- `test-results/mobile-matrix-task-t_352fa39b/perf-slow2g.json` was not produced because the diagnostic timed out.

Acceptance can be reopened after M6/M11/M12 are triaged or explicitly waived and native/physical evidence gaps are completed or dispositioned.
