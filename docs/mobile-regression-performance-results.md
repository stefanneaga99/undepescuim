# Mobile matrix execution report

Run date: 2026-08-19 (UTC)

## Executed checks

| Check | Profile | Result |
|---|---|---|
| Playwright accessibility + app-load smoke | `iphone-current` (390x844 Chromium emulation) | 3 passed in 24.8s |
| Performance budget suite, unthrottled | 390x844 Chromium | 7 metrics passed |

Command evidence:

```text
E2E_MOBILE_MATRIX=1 npx playwright test --project=iphone-current --grep 'app load|accessibility' --workers=1 --reporter=line
3 passed (24.8s)
```

```text
PERF_THROTTLE=0 node scripts/_perf_map.mjs http://localhost:3102
M6 0.58s PASS; M11 0.40s PASS; M10 215.4KB PASS;
M14 828 paths PASS; M13 78MB PASS; M12 72ms PASS;
M5 unexpected CLS 0.0000 PASS (0 shifts)
```

## M5 fix verification

The floating legend and geolocation controls keep stable `bottom` layout anchors
and use a compositor-only `transform` for their intentional offset above the
sheet. This removes the delayed layout shifts observed after the sheet snap
settled. The approved `<=0.001` gate now passes with `unexpected=0.0000` and
zero shift entries.

The full six-device matrix is exposed by `npm run mobile:matrix` and produces `summary.json`, `e2e.log`, `performance.log`, Playwright results, and an HTML report under `test-results/mobile-matrix-<timestamp>/`. Native iOS Safari and physical Android checks remain explicitly pending because this WSL/CI environment provides Chromium emulation only.
