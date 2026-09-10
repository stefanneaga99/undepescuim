# Hydration #418 report-transition investigation

Date: 2026-09-10
Task: `t_7121e188`

## Reproduction basis

The clean comparison checkout is `origin/main` at `e85b1f3867f87fb6ed33b3f1e73606d8e8a767b7`, the requested Production rollback commit. It was built with `npm run build` and served as a production build on port 3122. The investigation checkout used a detached git worktree so the current map/data worktree did not contaminate the result.

Commands:

```text
git worktree add --detach /tmp/undepescuim-hydration-clean origin/main
npm run build
PORT=3122 npm run start
E2E_SERVER_READY=1 E2E_PORT=3122 npx playwright test tests/e2e/specs/flows/report.spec.ts --project=mobile --project=desktop
```

Build result: passed (Next 16.3.1 / webpack, TypeScript, static generation, Serwist worker bundle).

## Earliest observed divergence

On the clean production build, the initial page load and the first report entry flows do not emit a page error. The first failing transition is the A→B selection update in the transition scenarios. It is emitted after the second water selection, before the final assertion, and is identical for direct, report-close, and report-success phases. The six transition cases are:

- single A→B: direct, report-close, report-success
- multi-contract A→B: direct, report-close, report-success

The browser reports:

```text
pageerror: Minified React error #418; visit https://react.dev/errors/418?args[]=HTML&args[]=
```

Captured stack (production build):

```text
r1 -> ih -> sy -> <anonymous> -> so -> sG -> MessagePort.C
/_next/static/chunks/95c46d1c-d4993b56ef4942f3.js
/_next/static/chunks/237-8b1153ebdbf2d352.js
```

This is a React hydration mismatch, not a fetch/API exception or Leaflet click exception. It is not present on the initial load, on the first A selection, or while opening the report dialog. The failure is reproducible with both 390x844 (`mobile`) and 1280x800 (`desktop`).

Clean run result: 4 passed, 14 failed, 2 skipped. The 14 failures include all six A→B cases plus two mobile focus-preservation checks; the latter fail because `focusSnapshot()` includes asynchronous physical-preview layer owners after the snapshot, not because the report request lost selection. The A→B failures contain the #418 page error.

Failure screenshots and videos from this run are retained under:

```text
/tmp/undepescuim-hydration-clean/test-results/115399/
/tmp/undepescuim-hydration-clean/test-results/115484/
/tmp/undepescuim-hydration-clean/test-results/115569/
```

The exact stack repro was rerun with a temporary, uncommitted pageerror listener; no extra exception or console error was reported.

## Source trace and hypotheses

Relevant path:

```text
WaterDetailSheet -> ReportForm -> DialogContent -> Radix DialogPortal
MapView -> MapTestBridge / physical-preview and focus state
I18nProvider -> useSyncExternalStore (server snapshot: ro)
ServiceWorkerRegister -> effect-only /sw.js registration
```

The report component's state transitions (`idle`/`submitting`/`success`) are not the first divergence: direct transitions fail too. The report POST is intercepted by the test and is not involved in direct failures. The service worker is blocked by the default seeded Playwright fixture, so stale SW asset mixing is not the cause of this clean-build reproduction. `useMediaQuery` and i18n both provide SSR snapshots; changing either without a before/after proof would be speculative.

The highest-confidence boundary is the client-only map/detail transition which causes React to hydrate or reconcile the Radix/vaul portal subtree after the A→B selection. The current evidence does not prove whether the first differing node is the portal content, the compact/desktop branch, or an html attribute changed by persisted state. A blanket client-only conversion, warning suppression, delay, or portal rewrite would therefore violate the investigation constraints and was not made.

## Current integrated worktree comparison

The task worktree was also built successfully. Running the same report spec there produced 18 passed, 2 failed, 2 skipped; the two failures were the mobile focus snapshots, whose expected/actual difference was the newly integrated Class2 preview layer owner list. No #418 page error occurred in that run. This confirms that the failure is sensitive to the exact integrated source/data state and that the clean rollback checkout is the required repro basis.

## Data integrity

SHA-256 values observed in the task worktree:

```text
public/data/waters.json             56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0
public/data/associations.json       388ff8ef7efc267914d3a67a20f2f5a9230dd6bc0a0fdf9b87188b8f2fbaafa9
public/data/uncontracted_rivers.json 06414eb6c569770513c10d90d8a68d3338d7f4508ef5c7d76cb20add195db4dd
public/data/uncontracted_lakes.json  59c9b9969f3c501e06bdabc2cf33d06e4ccf1c055680169264cbce636e17f44e
```

`public/data/geometry-ledger.json` is not present in this checkout, so no hash is fabricated. No canonical data file was modified. No production source correction is justified by this evidence alone; the implementation task should use this as a red reproduction and add instrumentation or a narrowly scoped fix only after identifying the differing DOM node.
