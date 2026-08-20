# Integrated mobile regression and performance run

Run: 2026-08-20 15:12 UTC
Commit: `64c5d38f1d33f589d92a53d22b583f9409e9b41c`
Environment: WSL2, Node 22.23.2, npm 10.9.8, Playwright 1.62.1, production build, Chromium emulation.
Application URL: `http://127.0.0.1:3112`

## Commands

```text
E2E_PORT=3112 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-task-t_352fa39b PERF_THROTTLE=1 npm run mobile:matrix
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true PLAYWRIGHT_BASE_URL=http://127.0.0.1:3112 npx playwright test --project=iphone-current --project=iphone-previous --project=pixel-current --project=pixel-previous --project=samsung-current --project=samsung-previous tests/e2e/specs/regression/mobile-offline-network.spec.ts --workers=1 --reporter=line
```

The production build completed and the six profiles ran serially with one worker. Result: **446 passed, 2 failed, 32 intentional skips, 0 flaky** out of 480. The focused offline/network contract assertions passed **18/18**: offline request isolation (0 new requests), reconnect POST behavior, false-success prevention, exact staleness boundary, and bounded cache fixtures.

## Performance result

Fast 3G (1.638 Mbps down / 0.768 Mbps up, 150 ms RTT), 390x844, CPU 4x:

| Metric | Threshold | Observed | Result |
|---|---:|---:|---|
| M5 CLS | < 0.001 | 0.0000 | PASS |
| M6 first map paint | < 5.0 s | 11.93 s | FAIL |
| M10 JS transfer | < 300 KiB | 215.4 KiB | PASS |
| M11 fetch+parse | < 2.5 s | 9.68 s | FAIL |
| M12 long task | <= 100 ms | 265 ms | FAIL |
| M13 JS heap | < 200 MiB | 54 MB | PASS |
| M14 paths at z7 | <= 1,000 | 828 | PASS |

Storage occupancy was 0.50% (16,026,451 / 3,237,251,923 bytes), with 57 precache, 2 app-data, and 6 OSM-tile cache entries. M6/M11 are tied to the 1,485 KiB `waters.json` critical path; M12 has additional 198/166/164/131 ms tasks. These are actionable performance defects, not accepted failures.

## Failure disposition and limitations

The two `pixel-current` failures are `live-prod.spec.ts` checks against deployed production while this run used an isolated local server; they are environment-invalid and retained with screenshots/traces under the run's Playwright artifact directory. They must be rerun against the live URL.

A Slow 2G Chromium diagnostic (50 Kbps, 300 ms RTT, CPU 4x) was attempted but timed out after 180 seconds waiting for the data-ready signal; Playwright then reported the page closed. It is inconclusive/not-run, not a pass. Native iOS Safari, physical Android Chrome, physical Slow 2G, physical OS cache eviction, and hardware-memory tests are unavailable in WSL2 and remain release-blocking evidence gaps.

## Artifacts

All raw artifacts are under `test-results/mobile-matrix-task-t_352fa39b/`: `summary.json`, `e2e.log`, `performance.log`, `mobile-performance.json`, and `playwright/` report/traces/screenshots/videos.
