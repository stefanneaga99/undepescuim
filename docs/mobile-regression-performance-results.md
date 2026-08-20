# Mobile matrix execution report

Run date: 2026-08-20 (UTC)

## Executed checks

The complete six-profile Chromium emulation matrix was run from commit `70aeee0911b6ac5c9cbfb226d767275bb7abedf0` on WSL/Node.js 22.23.2 using the production build and an isolated server at `http://127.0.0.1:3103`:

```text
E2E_PORT=3103 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-t_fa7e29f8 npm run mobile:matrix
```

Results:

| Check | Result |
|---|---:|
| Playwright matrix | **422 passed, 14 failed, 32 skipped** / 468 tests, 10.6m |
| Profiles | `iphone-current`, `iphone-previous`, `pixel-current`, `pixel-previous`, `samsung-current`, `samsung-previous` |
| Network mode | Chromium emulation; Fast 3G + 4x CPU for performance pass |
| Native iOS Safari / Android Chrome | **Not available in this WSL lab; no native pass is claimed** |

The run preserved evidence under `test-results/mobile-matrix-t_fa7e29f8/`: `summary.json`, `e2e.log`, `performance.log`, Playwright screenshots/videos/error contexts, and HTML/report output. The summary records `e2eExitCode: 1` and `performanceExitCode: 1`.

The 14 initial failures were:

- 12 offline/network tests (the same two tests on each of six profiles) failed because Chromium destroyed the page execution context while `setDeviceOnline` toggled CDP offline state before updating the page's `navigator.onLine` shim.
- 2 `live-prod.spec.ts` checks failed only on `pixel-current`; the matrix is a local production-server run and those live-production checks are not a supported local-matrix assertion.

The offline race was fixed in `tests/e2e/fixtures/mobile-metrics.ts` by updating the page-facing online state before toggling CDP connectivity. The focused rerun covered all six profiles and passed:

```text
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true PLAYWRIGHT_BASE_URL=http://127.0.0.1:3103 \
  npx playwright test --project=iphone-current --project=iphone-previous \
  --project=pixel-current --project=pixel-previous \
  --project=samsung-current --project=samsung-previous \
  tests/e2e/specs/regression/mobile-offline-network.spec.ts --workers=1 --reporter=line

18 passed (16.4s)
```

This focused rerun verifies the offline transition request contract, exact 29/30-day stale boundary, and online-only report behavior across all six emulated device profiles. The original screenshots/videos/error contexts remain available as regression evidence for the race.

## Performance budget evidence

The matrix performance pass used `scripts/_perf_map.mjs` with Fast 3G (1.6 Mbps, 150 ms RTT) and 4x CPU at 390x844:

| Metric | Gate | Observed | Result |
|---|---:|---:|---|
| M5 unexpected CLS | <= 0.001 | 0.0000 (0 shifts) | PASS |
| M6 first map paint | < 5.0 s | 11.93 s | FAIL |
| M10 initial JS gzip | < 300 KiB | 215.4 KiB | PASS |
| M11 data fetch + parse | < 2.5 s | 9.67 s | FAIL |
| M12 max long task | <= 100 ms | 324 ms | FAIL |
| M13 peak JS heap | < 200 MiB | 65 MiB | PASS |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | PASS |

Actionable performance defects: under Fast 3G/4x CPU, first map paint and data fetch/parse exceed their budgets; pan/zoom records a 324 ms long task (additional recorded long tasks: 261, 201, 156, and 149 ms). These are reproducible from `performance.log` and should be triaged separately from the passing functional matrix.

## M5 fix verification

The floating legend and geolocation controls keep stable `bottom` layout anchors and use a compositor-only `transform` for their intentional offset above the sheet. The matrix confirms the `<=0.001` CLS gate with zero unexpected layout shifts.

## Native and slow-network limitations

This environment provides Chromium emulation only. Chromium projects are evidence for responsive behavior and deterministic request contracts, not a substitute for native Safari/Chrome, hardware cache pressure, or physical Slow 2G. Native checks remain explicitly pending and must record literal OS/browser versions, startup/first-map-paint timing, offline request counts, reconnect behavior, and storage/cache observations on current and previous iPhone, Pixel, and Samsung hardware. The automated lab profile is Fast 3G; Slow 2G and iOS Web Inspector/network-link-conditioner evidence require a physical device lab.

## Follow-up execution: t_6e43b4f4

Run date: 2026-08-20 (UTC), commit `a9c977cd0b5ac043b7ade974d65bd732aeb6e922`, isolated production server `http://127.0.0.1:3114`.

```bash
E2E_PORT=3114 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-t_6e43b4f4-r2 npm run mobile:matrix
```

The six emulated profiles completed with **434 passed, 2 failed, 32 skipped** in 10.4 minutes. The two failures were the known `live-prod.spec.ts` assertions on `pixel-current`; those tests target the deployed production URL and are not valid assertions against the local matrix server. The 32 skips are intentional data-excluded cases. The offline/network focused contracts and PWA offline reload/cache checks passed; the run's reproducible artifacts are `test-results/mobile-matrix-t_6e43b4f4-r2/{summary.json,e2e.log,performance.log}`.

### Performance measurements and comparison

| Metric | Gate | Observed | Result |
|---|---:|---:|---|
| M5 unexpected CLS | <= 0.001 | 0.0000 (0 shifts) | PASS |
| M6 first map paint | < 5.0 s | 11.86 s | FAIL |
| M10 initial JS transfer | < 300 KiB | 215.4 KiB | PASS |
| M11 data fetch + parse | < 2.5 s | 9.62 s | FAIL |
| M12 max long task during zoom/pan | <= 100 ms | 320 ms | FAIL |
| M13 peak Chromium JS heap | < 200 MiB | 73 MiB | PASS |
| M14 overlay paths at zoom 7 | <= 1,000 | 828 | PASS |
| First-load data transfer | informational | 1,741 KiB | informational |

M12's largest additional long tasks were 253, 193, 153, and 147 ms. Reproduction for all three failures is the command above; inspect `performance.log`. Actionable triage is to reduce the 1,485 KiB `waters.json` load/parse on Fast 3G and profile the contracted/uncontracted map work responsible for the 320 ms zoom task. These are regressions against the approved thresholds, not native-device claims.

### Storage and offline request probe

Using `/tmp/mobile-storage-measure.mjs` against the production server at 390x844, after two online loads: Chromium reported quota 3,231,444,554 bytes and usage 10,219,082 bytes (IndexedDB 5,429,799; Cache Storage 4,789,283). The visible precache contained 55 entries and 178,015 response bytes. During an offline reload, the request delta was 2 with **zero `/data/` requests**; after reconnect, no `/data/` requests were emitted. This confirms the no-unexpected-data-request contract for the lab probe, but it does not measure physical OS eviction or progressive tile-cache growth; those remain native-device release evidence.

### Platform limitations

Current/previous iOS Safari and Android Chrome hardware runs, plus Slow 2G (2G: 300 ms RTT, 50 Kbps down/up), cannot be executed in this WSL Chromium-only lab. No native pass is claimed. Release follow-up must run the same scenarios on iPhone 15/14, Pixel 7/5, and Galaxy S24/S21, record literal OS/browser versions, and capture startup, first-map-paint, memory, storage/cache growth and eviction, offline transition latency, and online/offline/reconnect request counts. Mark unavailable metrics as platform-limited rather than passing them.
