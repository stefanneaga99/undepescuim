# Native mobile release checklist

Native runs are required evidence, not Chromium emulation. Record one JSON result row per device/network combination using `tests/e2e/fixtures/mobile-release-result.schema.json`.

## Before each run

1. Record device model, OS version, browser name/version, date, and `git rev-parse HEAD`.
2. Remove the installed PWA/site data (Safari: Settings > Safari > Advanced > Website Data; Chrome: site storage).
3. Disable VPN/ad blockers and grant location only if the flow requires it. Never record credentials or report tokens.
4. Start with the device online and capture a screen recording or screenshots under the run artifact directory.

## Flow matrix

Run these flows on each current/previous iPhone and Pixel/Samsung target: startup/first map paint, browse/search, accessibility smoke, online report, warm online → offline reload, stale marker at 30 days, map cache growth/eviction/no prefetch, offline report rejection, reconnect and one successful report. Repeat the network-sensitive flows under Fast 3G and Slow 2G.

Slow 2G is 300 ms RTT and 50 Kbps down/up. Use Chrome DevTools on Android and Network Link Conditioner/Web Inspector equivalent on iOS. Do not label a missing native run as pass: use `status: "not-run"` and an actionable `reason`.

## Evidence and metrics

For every flow record duration, request count, storage/cache metrics where exposed, and artifact paths (screenshots, trace, recording). `performance.memory` is Chromium-only; native rows must use `null`/`unavailable`, never an invented value. Native quota and OS cache-pressure eviction are measured observations, not fixed assumptions.

## Repeatable local commands

```bash
npm ci
npm run build
npm run mobile:reset
npm run mobile:matrix
E2E_MOBILE_MATRIX=1 npx playwright test tests/e2e/specs/regression/mobile-offline-network.spec.ts --project=iphone-current --project=pixel-current --workers=1
```

The matrix runner writes `summary.json`, `e2e.log`, `performance.log`, and Playwright artifacts below `test-results/mobile-matrix-<timestamp>/`. Set `MOBILE_MATRIX_OUTPUT` to retain results at a known path. Keep device-specific URLs and credentials in environment variables or the lab device, never in git.
