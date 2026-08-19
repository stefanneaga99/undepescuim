# Mobile matrix execution report

Run date: 2026-08-19 (UTC)

## Executed checks

| Check | Profile | Result |
|---|---|---|
| Playwright accessibility + app-load smoke | `iphone-current` (390x844 Chromium emulation) | 3 passed in 24.8s |
| Performance budget suite, unthrottled | 390x844 Chromium | 5 metrics passed, 1 failed |

Command evidence:

```text
E2E_MOBILE_MATRIX=1 npx playwright test --project=iphone-current --grep 'app load|accessibility' --workers=1 --reporter=line
3 passed (24.8s)
```

```text
PERF_THROTTLE=0 node scripts/_perf_map.mjs http://localhost:3102
M6 0.61s PASS; M11 0.42s PASS; M10 215.4KB PASS;
M14 828 paths PASS; M13 78MB PASS; M12 80ms PASS;
M5 unexpected CLS 0.0164 FAIL (2 shifts)
```

## Defect / follow-up

`M5` currently fails the approved `<=0.001` unexpected-CLS gate. Both shifts were `0.0082` and occurred on map-touch buttons during the filter/sheet interaction (`17926ms` and `17941ms`). This is actionable: inspect the map-touch control's layout/visibility transition and add a focused regression before changing the budget. No other measured performance budget regressed in this run.

The full six-device matrix is exposed by `npm run mobile:matrix` and produces `summary.json`, `e2e.log`, `performance.log`, Playwright results, and an HTML report under `test-results/mobile-matrix-<timestamp>/`. Native iOS Safari and physical Android checks remain explicitly pending because this WSL/CI environment provides Chromium emulation only.
