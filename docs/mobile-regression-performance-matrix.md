# Mobile regression and performance matrix

This is the release-gate matrix for the PWA shell, offline data, map cache, and online-only reporting. The existing Playwright specs are the executable coverage; this document records the target profiles, budgets, commands, and known lab limitations.

For the consolidated result of the latest integrated run, see [Integrated mobile test report](mobile-integrated-test-report.md).

## Target matrix

| ID | Device/configuration | Automated evidence | Native release evidence |
|---|---|---|---|
| I1/I2 | iPhone 15 / 14, iOS Safari, 390x844 | `iphone-current` / `iphone-previous` Chromium emulation | physical Safari |
| A1/A2 | Pixel 7 / 5, Android Chrome | `pixel-current` / `pixel-previous` Chromium emulation | physical Chrome |
| A3/A4 | Galaxy S24 / S21, Android Chrome | `samsung-current` / `samsung-previous` Chromium emulation | physical Chrome |
| N3 | Pixel 7 + Pixel 5 Fast 3G | `_perf_map.mjs` | optional physical confirmation |
| N2/S2 | Android / iOS Slow 2G | no false automated claim | required physical evidence |

Chromium device projects are explicitly emulation and never substitute for native Safari, hardware cache pressure, or physical Slow-2G evidence. Record literal OS/browser versions at release time in the JSON schema.


## Deterministic fixtures and artifacts

`tests/e2e/fixtures/mobile-metrics.ts` records pathname/method/timing only, storage estimate, Cache Storage entry/byte counts, and provides `setDeviceOnline`/`waitForOnlineState` without sleeps. `mobile-data.ts` supplies exact 29-day and 30-day snapshots plus twelve cache regions (96 distinct tile URLs) for growth/eviction tests. `mobile-offline-network.spec.ts` covers transition/request and report network contracts. Failed runs should attach `mobile-metrics.json`; the runner preserves logs, HTML report, traces, screenshots, and `summary.json`.

Use `npm run mobile:reset` before a clean local run. It removes prior matrix artifacts; each Playwright context additionally clears cookies, IndexedDB, Cache Storage, and service-worker registrations via `resetBrowserState`.

## Coverage map

- Install/startup and first load: `smoke/app-load.spec.ts`, `regression/pwa.spec.ts`
- Offline reload, stale data banner, cache population, bounded tile cache, TTL, eviction, and no tile prefetch: `regression/pwa.spec.ts`, `regression/edge-cases.spec.ts`
- Dataset browsing/search, filters, county/locality, and map selection: `flows/water-detail.spec.ts`, `flows/association.spec.ts`, `flows/county-locality.spec.ts`, `regression/map-segment-qa.spec.ts`
- Online-only report success/failure and reconnect behavior: `flows/report.spec.ts`
- Accessibility landmarks, names, focus, and 44px touch targets: `accessibility.spec.ts`
- Network/data isolation and request contracts: `fixtures/routes.ts`, `data-contract/*.spec.ts`
- 3G responsiveness, long tasks, heap, data/JS transfer, map LOD, and CLS: `scripts/_perf_map.mjs`

## Budgets and baselines

The budgets are intentionally practical gates with headroom, not device claims:

| Metric | Gate | Source |
|---|---:|---|
| First map paint | < 5.0 s | performance plan M6 |
| Data fetch + parse | < 2.5 s | performance plan M11 |
| Initial JS transfer | < 300 KiB | performance plan M10 |
| Long task during zoom/pan | <= 100 ms | performance plan M12 |
| Peak Chromium JS heap | < 200 MiB | performance plan M13 |
| Overlay paths at zoom 7 | <= 1,000 | performance plan M14; 20% regression headroom |
| Unexpected CLS | <= 0.001 | performance plan M5 |
| Lighthouse LCP / TBT / CLS | 2.5 s / 200 ms / 0.1 | `lighthouserc.json` |
| Runtime tile cache | bounded by SW eviction policy; no precache tiles | PWA regression spec |

Every run records Playwright pass/skip/fail output and the performance script's measured values. A failure is actionable when it names the metric, observed value, profile, and artifact path; skipped native-browser checks must not be reported as passes.

## Repeatable commands

Fast unit/type/build gates:

```bash
npm test
npx tsc --noEmit
npm run build
```

Full emulated mobile matrix (production build, one server lifecycle):

```bash
npm run mobile:matrix
```

Equivalent explicit commands:

```bash
E2E_MOBILE_MATRIX=1 E2E_SERVER_READY=true E2E_PORT=3100 \
  npx playwright test --project=iphone-current --project=iphone-previous \
  --project=pixel-current --project=pixel-previous \
  --project=samsung-current --project=samsung-previous --workers=1
PERF_THROTTLE=1 node scripts/_perf_map.mjs http://localhost:3100
```

The runner builds once, starts one production server, runs the six device projects, then runs the performance suite. Set `PERF_THROTTLE=0` for a quick local smoke; the recorded lab condition is Fast 3G plus 4x CPU. The performance suite also reports request/resource transfer rows, which are the request-count baseline for comparing runs.

## Network and offline interpretation

The PWA tests stub OSM tiles and use Playwright offline mode after an online warm-up. Offline reload must render the shell and cached dataset; no unexpected data/API request is permitted by the route fixtures. Report POSTs are network-only and are tested through success, rejection, offline, and reconnect cases; a UI confirmation without a successful response is a defect.

2G is a manual/device follow-up because Chromium's CDP emulation is used for the automated 3G lab condition. Run the same matrix with Chrome DevTools Slow 2G (300ms RTT, 50 Kbps down, 50 Kbps up) on a physical current and previous Android device, recording startup, first map paint, offline transition, request count, and storage. iOS Safari requires Web Inspector/network-link-conditioner or a real device lab for equivalent 2G evidence.

## Limitations and follow-up issues

- CI has Chromium only; native Safari/WebKit and physical Android Chrome are release checks, not silently substituted by emulation.
- `performance.memory` is Chromium-specific; non-Chromium runs must mark heap as unavailable rather than pass it.
- Service-worker/cache tests use isolated contexts and deterministic tile responses; production CDN and OS eviction behavior need a periodic device run.
- The current map performance budgets are baselines from the approved performance plan. When a baseline changes, update both `scripts/_perf_map.mjs` and this table in the same commit.
- Attach the Playwright HTML report, `test-results`, and performance stdout to the release/CI run for defect triage.
