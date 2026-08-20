# Repeatable mobile fixtures and commands

The seeded Playwright tier is deterministic and does not depend on the production dataset or report provider. `tests/e2e/fixtures/seed-data.ts` supplies contracted, uncontracted, locality, multi-county, association, and accessibility edge cases; `routes.ts` intercepts all data and tile requests. The mobile fixture clock is fixed at `2026-08-20T12:00:00.000Z`, with snapshots exactly 29 and 30 days old in `mobile-data.ts`.

## Clean run

```bash
npm ci
npm run build
npm run mobile:reset
E2E_PORT=3100 MOBILE_MATRIX_OUTPUT=test-results/mobile-matrix-$(date -u +%Y%m%dT%H%M%SZ) npm run mobile:matrix
```

The matrix runs serially on Chromium emulations for iPhone 15/14, Pixel 7/5, and Galaxy S24/S21, then runs the Fast-3G performance probe. It writes `summary.json`, `e2e.log`, `performance.log`, Playwright traces/screenshots/videos, and attached `mobile-metrics.json` files below the output directory. The metrics contain pathname/method/timestamp request metadata only; headers, bodies, credentials, and report tokens are never persisted.

For a fast deterministic contract check on representative iOS/Safari and Android/Chrome emulations:

```bash
npm run mobile:reset
npm run mobile:offline
```

The offline spec covers online→offline→online latency, zero offline `/data/*` requests, exact 29/30-day stale boundaries, visited-only tile cache growth, and the online-only report contract (offline network error, then exactly one successful POST after reconnect).

The cache fixture has a deterministic 32-entry bound (`MOBILE_TILE_CACHE_LIMIT`).
The progressive-cache case visits all twelve regions (eight unique URLs each),
then asserts that the oldest region is evicted while the newest remains. The
network profile constants in `tests/e2e/fixtures/mobile-network.ts` are the
source of truth for controlled Fast 3G (1,600/750 Kbps, 150 ms RTT, 4x CPU)
and Slow 2G (50/50 Kbps, 300 ms RTT, 4x CPU) device-lab setup.

## Reset and subsets

`npm run mobile:reset` removes prior matrix output and Playwright reports. Each Playwright context additionally clears cookies, local/session storage, IndexedDB, Cache Storage, permissions, and service-worker registrations. Run an individual target or flow with:

```bash
E2E_MOBILE_MATRIX=1 npx playwright test tests/e2e/specs/regression/mobile-offline-network.spec.ts --project=iphone-current --workers=1
E2E_MOBILE_MATRIX=1 npx playwright test tests/e2e/specs/accessibility.spec.ts --project=pixel-current --workers=1
PERF_THROTTLE=1 node scripts/_perf_map.mjs http://127.0.0.1:3100
```

## Native prerequisites and evidence

Chromium projects are lab evidence only; they do not certify native Safari, physical Android Chrome, OS cache pressure, or Slow 2G. Native validation requires an iPhone with current/previous Safari and a Pixel/Samsung with current/previous Chrome, a production build, and a network profiler capable of Fast 3G and Slow 2G. Before every device run clear site data and record model, OS, browser build, commit SHA, UTC timestamp, network profile, and whether each F1–F10 flow passed, failed, or was `not-run`. Use `tests/e2e/fixtures/mobile-release-result.schema.json`; an unavailable physical run must be `not-run` with a reason and follow-up owner, never `pass`.

Store native screenshots/recordings alongside the schema-valid JSON row. Store automated artifacts under `test-results/`; do not commit generated reports or secrets.
