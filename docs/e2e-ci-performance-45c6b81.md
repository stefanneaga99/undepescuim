# Playwright CI performance investigation — commit 45c6b81

Date: 2026-08-19 (WSL reproduction; timings are local evidence, not GitHub-host guarantees)

## Scope and commands

The target commit is `45c6b81` (`git worktree add --detach /tmp/undepescuim-45c6b81 45c6b81`). The worktree used the repository's existing `node_modules` and a local Chromium wrapper because this WSL image lacks `libasound.so.2` for Playwright's bundled browser.

Reproduction commands:

```bash
cd /tmp/undepescuim-45c6b81
npm run build
PORT=3120 npm run start
# in another shell, with local Chromium:
env -u PLAYWRIGHT_CDP /tmp/asound-run.sh \
  npx playwright test --grep-invert @data --workers=2 --reporter=line
env -u PLAYWRIGHT_CDP /tmp/asound-run.sh \
  npx playwright test --grep @data \
    --project=mobile --project=tablet --project=desktop \
    --workers=2 --reporter=line
```

`/tmp/asound-run.sh` exports the locally unpacked ALSA library and execs its arguments. On GitHub Actions this workaround is not needed because `playwright install --with-deps chromium` installs the system dependencies.

## Measured timings

| Stage / selection | Result |
|---|---:|
| `npm run build` (including `prebuild`) | 13.76 s |
| seeded suite, all 3 projects, 195 scheduled tests, 2 workers | 2.9 min wall; 176 passed, 19 skipped |
| seeded mobile alone | 1:10.97 wall; 63 passed, 2 skipped |
| seeded tablet alone | 1:09.23 wall; 52 passed, 13 skipped |
| seeded desktop alone | 1:09.30 wall; 61 passed, 4 skipped |
| `@data`, all 3 projects, 24 scheduled tests, 2 workers | 22.57 s wall; 24 passed |

The per-project test sums are approximately 114.8 s mobile, 108.6 s tablet, and 100.2 s desktop. The wall time is lower when projects are in one invocation because Playwright shares the web server and schedules work across two workers; running projects as separate jobs would otherwise repeat setup.

The slowest individual specs from the JSON reporter were:

- `regression/map-segment-qa.spec.ts`: ~7.8–8.0 s per project.
- PWA offline reload: ~4.1–6.7 s per project.
- PWA service-worker registration: ~4.5–6.5 s per project.
- PWA visited-tile cache: ~3.6–5.9 s per project.
- Report transition cases: up to ~3.2 s (mobile).

The report flow intentionally skips tablet; this is why the scheduled 195 tests become 176 actual passes plus 19 skips.

## Exact bottleneck and duplication findings

1. The workflow's `Build & run E2E` step invokes `npx playwright test`; `playwright.config.ts` starts `webServer.command`, which is `npm run build && PORT=... npm run start`. Therefore the first test invocation performs the build and server startup before tests.
2. The workflow then invokes a second, independent `npx playwright test` for `@data`. In CI `reuseExistingServer: false`, so this second invocation starts another server process and runs **another full build**. The measured build is ~14 s each time before any `@data` test (the @data browser work itself is ~22.6 s).
3. There is no `globalSetup`, `storageState`, or shared fixture setup that materially dominates. Seed routes are per-page (`page.route`), and report routes are per-test (`beforeEach`). The @data river fixture is also installed per test via `beforeEach`; it is tiny and deterministic, but it does add redundant route registration to each of the 24 project/test executions.
4. The workflow installs dependencies and Playwright browsers in separate steps. `npm ci` is a cold-cache/network-sensitive install of a large lockfile (401 packages added / 881 changed in the local npm dry-run output). `npx playwright install --with-deps chromium` installs Chromium plus OS dependencies; the local Playwright cache is 656 MB and contains Chromium, headless shell, and ffmpeg. These steps are likely the largest variance on a fresh GitHub runner, although they cannot be timed faithfully from this offline/local reproduction.
5. `fullyParallel: false` preserves file ordering, while `workers: 2` allows two test workers. The seeded run used two worker processes, but all three projects still exercise the same suite (65 scheduled entries per project; project-specific skips account for the difference in executed counts). No test writes a shared filesystem fixture or shared port. The only fixed port is the one server from `webServer`; a matrix of jobs must give each job its own port or isolated runner.

## @data/offline behavior

`tests/e2e/fixtures/routes.ts` intercepts the app's data endpoints and OSM tile host with deterministic JSON/transparent PNG responses. `river-segment-samples.spec.ts` additionally aborts every non-localhost request and serves its fixture through a per-page route. Consequently @data is offline by contract: it must not contact production waters, OSM, or API endpoints. It is safe to run in parallel across projects as long as each worker has its own browser context; do not replace this with production data or remove the external-request assertion.

The live data-contract spec reads served `/public/data` files and is intentionally separate from the seeded tier. Keep it as a separate check, but avoid making it launch a second build/server in the same workflow.

## Proposed under-25-minute CI model

Conservative option (lowest race risk): keep one runner and one Playwright invocation for the seeded tier, then select the offline tests in that same server lifecycle if the runner can pass both grep selections through a single command. The simplest robust implementation is to make the two suites explicit projects or tags and run one `npx playwright test` process; this removes the duplicate build/server startup. Keep `workers: 2` initially and retain retries only for CI failures. Based on local evidence: ~14 s build + ~175 s seeded wall + ~23 s @data, leaving ample margin for server startup and normal CI variance.

If more parallelism is required, use a matrix with three jobs (`mobile`, `tablet`, `desktop`) and one optional data job, but first build once and transfer the exact `.next` output (or use a cache keyed by lockfile + source commit). Each matrix job starts one server on its own runner; never have matrix jobs race for one shared port or shared `playwright-report` directory. Use artifact names containing the project/shard and merge reports in a final job.

A practical budget for a warm-cache GitHub runner is:

- dependency cache/install: 2–5 min (cold network can be higher; enforce a job timeout and cache npm)
- browser/system dependency install: 1–4 min (cold; cache Playwright browsers where policy permits)
- one build/server startup: 1 min budget (measured build is 14 s)
- seeded tests: 3–5 min budget at two workers; ~2 min per project in isolated matrix jobs
- @data: 1 min budget (measured 23 s including browser setup)
- artifact/report overhead: 1–2 min budget

This totals roughly 8–18 minutes with a single lifecycle, below the 25-minute job limit. A cold dependency/browser install should be monitored separately because it is the largest unmeasured variable.

## Race-condition and sharding risks

- The app's Leaflet map and tile state are not a reason to share a browser context. Use Playwright's default isolated context per test and do not raise workers without a stability run.
- Service-worker/offline tests intentionally mutate network behavior in their own context. Sharing contexts or storage state between tests could leak offline mode and make later tests hang or fail.
- Report tests stub `/api/report` and use per-test route handlers. Keep them isolated; never run them against the real endpoint.
- The @data route aborts external requests. It is safe in parallel only with separate contexts; sharing a page would make route ordering and abort behavior race.
- Multiple CI jobs must not share `PORT=3000`, `.next`, `playwright-report`, or `test-results` without isolation/merge steps. If sharding by file, preserve the project matrix and use `--shard=N/M`; do not shard the same stateful spec across workers unless its fixtures remain context-local.

## Conclusion

The reproducible application-side slow phase is test execution, not a hang: the full seeded tier is ~2.9 minutes locally and each project is ~1.1 minutes. The clearest avoidable CI cost is the second Playwright invocation rebuilding and restarting the app for @data. Eliminate that duplicate lifecycle first; then optimize install/browser caching or introduce isolated project matrix jobs. No test was changed to hide a failure, and the commit worktree completed the build plus 195 seeded and 24 offline test listings/runs as recorded above.
