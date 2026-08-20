# Integrated mobile regression and performance run

Run: 2026-08-20 14:20 UTC
Commit: `1dca26fc199cc4499a2f312a110420acce5ab6fa`
Environment: WSL2 (`Linux DESKTOP-J7FOLV9 6.18.33.2-microsoft-standard-WSL2`, x86_64), Node 22.23.2, npm 10.9.8, Playwright 1.62.1, production Next build, Chromium emulation.
Application URL: `http://127.0.0.1:3110`
Network profile: Fast 3G (1.6 Mbps down, 750 Kbps up, 150 ms RTT) with 4x CPU for the performance probe.

## Commands

```text
npm run mobile:reset
E2E_PORT=3110 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-20260820T171800Z npm run mobile:matrix
```

The first attempt on port 3100 was stopped before tests because an unrelated listener occupied that port. The rerun on 3110 completed the matrix and retained all artifacts. The production build completed successfully before the matrix.

## Matrix result

The six emulated profiles ran serially with one worker:

- `iphone-current` — iPhone 15 profile, Chromium
- `iphone-previous` — iPhone 14 profile, Chromium
- `pixel-current` — Pixel 7 profile, Chromium
- `pixel-previous` — Pixel 5 profile, Chromium
- `samsung-current` — Galaxy S24 profile, Chromium
- `samsung-previous` — Galaxy S21 profile, Chromium

Result: **440 passed, 2 known environment-invalid failures, 32 intentional skips**. The two failures are `live-prod.spec.ts` checks that target the deployed production URL while this run used the isolated local matrix server; they are not treated as product regressions. The offline/cache/reconnect and accessibility contracts completed in the matrix. Raw output: `test-results/mobile-matrix-20260820T171800Z/e2e.log`; Playwright artifacts and screenshots are under `test-results/mobile-matrix-20260820T171800Z/playwright/`.

## Performance gates

| Metric | Threshold | Observed | Result |
|---|---:|---:|---|
| M5 unexpected interaction CLS | < 0.001 | 0.0000 | PASS |
| M6 first map paint | < 5.0 s | 11.95 s | FAIL |
| M10 initial JS gzip | < 300 KiB | 215.4 KiB | PASS |
| M11 data fetch + parse | < 2.5 s | 9.66 s | FAIL |
| M12 largest pan/zoom long task | <= 100 ms | 319 ms | FAIL |
| M13 peak Chromium JS heap | < 200 MiB | 65 MiB | PASS |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | PASS |

The performance resource total was 1,741 KiB on wire: `waters.json` 1,485 KiB, `uncontracted_majors.json` 168 KiB, `counties.geojson` 77 KiB, `associations.json` 10 KiB, `association_locations.json` 2 KiB, and `meta.json` below 1 KiB. The worst recorded long tasks included 319 ms, 259 ms, 199 ms, 157 ms, and 151 ms. Raw output: `test-results/mobile-matrix-20260820T171800Z/performance.log`.

## Unsupported release targets

The following required evidence was **not run**, not waived, and must not be interpreted as passing:

- native current/previous iOS Safari on iPhone 15/14;
- physical current/previous Android Chrome on Pixel 7/5 and Galaxy S24/S21;
- physical Slow 2G (50 Kbps, 300 ms RTT) on iOS and Android;
- physical OS cache-pressure/eviction and hardware memory measurements.

Reason: this execution environment is WSL2 with Chromium emulation only and has no attached iOS or Android devices. Impact: this run certifies only the automated Chromium-emulation contracts; native browser, physical network, and OS storage behavior remain release-blocking evidence gaps.

## Acceptance decision and follow-up

The functional emulation suite is acceptable with the two documented local-environment-invalid checks. Overall mobile release acceptance is **not met**: M6, M11, and M12 fail their approved budgets, and native/Slow-2G/cache-pressure evidence is unavailable.

1. Profile startup/data loading and reduce or defer the 1,485 KiB `waters.json` critical path to address M6/M11.
2. Profile synchronous map-layer/style work during zoom 7→11 to address M12.
3. Repeat F1–F10 on the six native device/browser combinations and record schema-valid `pass`, `fail`, or `not-run` rows.
4. Run physical Slow 2G and cache-pressure/eviction checks before release sign-off.

## Artifact manifest

- `test-results/mobile-matrix-20260820T171800Z/summary.json`
- `test-results/mobile-matrix-20260820T171800Z/e2e.log`
- `test-results/mobile-matrix-20260820T171800Z/performance.log`
- `test-results/mobile-matrix-20260820T171800Z/playwright/`
