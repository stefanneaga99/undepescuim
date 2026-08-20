# Mobile performance measurement and baseline comparison

The production-only probe records startup/first-map timing, data and JS transfer, resource/request counts, long tasks during map zoom, Chromium heap, Cache Storage entries/bytes, `navigator.storage.estimate()`, and offline transition/request activity. It writes a schema-versioned JSON artifact and compares numeric measurements with `docs/mobile-performance-baseline.json`.

## Fast 3G (approved CI/lab condition)

```bash
npm run build
PORT=3110 npm run start &
npm run mobile:reset
PERF_OUTPUT=test-results/perf-fast3g.json \
PERF_BASELINE=docs/mobile-performance-baseline.json \
PERF_NETWORK_PROFILE=fast3g PERF_THROTTLE=1 \
node scripts/_perf_map.mjs http://127.0.0.1:3110
```

Run this three times from clean state for a comparable median. Keep every JSON artifact. An approved gate must pass on every run, not only the median. `M6`, `M11`, and `M12` are currently known failing historical gates; the output still reports pass/fail rather than hiding those failures.

## Constrained Slow 2G (diagnostic only in Chromium)

```bash
npm run mobile:reset
PERF_OUTPUT=test-results/perf-slow2g.json \
PERF_NETWORK_PROFILE=slow2g PERF_THROTTLE=1 \
node scripts/_perf_map.mjs http://127.0.0.1:3110
```

This uses 50 Kbps down/up, 300 ms RTT, and 4x CPU. It is a repeatable diagnostic run, not native Safari/Android or physical cache-pressure evidence. Native device rows must be marked `pass`, `fail`, or `not-run` with literal OS/browser versions.

## Matrix integration and artifacts

`npm run mobile:matrix` passes a unique `mobile-performance.json` path into the probe. The matrix output directory therefore contains `summary.json`, `e2e.log`, `performance.log`, `mobile-performance.json`, and Playwright artifacts. The JSON stores pathname/method/resource timing only; it never stores headers, bodies, credentials, or report tokens.

The `measurements.baseline.deltas` map is a percentage change from the reference value (`positive` is slower/larger for timing, bytes, heap, or request counts). Storage occupancy is calculated as `usage / quota` when both values are available; investigate values above 0.80. `offline.newResourceRequests` must remain exactly zero, and cache entries must remain within the service-worker policy/fixture bound. A new request path, cache growth, quota change, or latency regression should be reported with the artifact path and target/profile.

## Interpretation

- Approved gates: M5 `<0.001`, M6 `<5s`, M10 `<300 KiB`, M11 `<2.5s`, M12 `<=100ms`, M13 `<200 MiB`, M14 `<=1000 paths`.
- Provisional contracts: offline transition `<=1000ms`, storage `<=80%` of reported quota, no unexpected offline requests, and bounded visited-only cache growth.
- Do not call unavailable `performance.memory` or native/device metrics a pass. The probe records unavailable heap as `null`; device-lab collection must supply the corresponding row separately.
