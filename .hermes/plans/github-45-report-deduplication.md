# GitHub #45 — deduplicare rapoarte `/api/report`

## Goal

Prevent the duplicate observed in GitHub issues #35 and #36: the same `data_correct` report for `basca-mare` was created twice 28 seconds apart. A rapid double click, a retry after a lost response, or two overlapping requests with the same normalized report must result in one GitHub issue during a short deduplication window. A report submitted again after that window remains legitimate.

## Evidence and constraints

- `src/components/verification/ReportForm.tsx` already renders a `submitting` phase and disables its submit button, but `setPhase` is asynchronous. A synchronous guard is still needed to close the interval before React re-renders / to protect programmatic duplicate submit events.
- `src/app/api/report/route.ts` validates and normalizes the payload, rate-limits by IP, then directly posts to GitHub. It has no idempotency state.
- #35 and #36 have identical visible report fields and timestamps 28 seconds apart; the varying `Trimis automat` timestamp is generated only after request processing and must not participate in the dedupe key.
- `AGENTS.md` requires tests for `src/lib` and `src/app/api` logic. `npm test -- --coverage` must retain at least 80% lines/functions/statements and 75% branches over the configured scope. No test may call GitHub.
- The application has no database and must add no external service. Existing GitHub POST remains the only outside API used by the production route.

## Architecture / decision

Use two complementary in-process protections:

1. **Client submission latch**: one form instance can have one in-flight call. The existing disabled button remains the visible/accessibility behavior; a `useRef` latch is the synchronous correctness guard.
2. **Server report-payload deduper**: an in-memory, module-scoped promise cache keyed by a SHA-256 digest of the already normalized, report-semantic fields. Inserting the pending promise synchronously before any `await` coalesces simultaneous `POST`s. On success, retain the issue URL for a deliberately short TTL (recommended `60_000` ms); identical retries return the same success JSON. On error, evict immediately so a real retry can try GitHub again.

The server deduper must run after JSON/schema/honeypot validation but before the rate limiter. Duplicate joins neither create another GitHub issue nor consume more per-IP quota; distinct payloads still pass through the existing abuse protection.

Do not add a client-generated idempotency-key protocol in this change. The canonical semantic-payload key directly meets issue #45's requirement to deduplicate independently submitted identical reports (not merely retries from one browser). Do not use the issue title or generated timestamp as the key.

### Important deployment boundary

A module-scoped map is atomic only inside one warm Node/serverless instance. It is fully testable and handles the normal double-click/overlapping-request path, but cannot provide mathematically global exactly-once creation when two cold/serverless instances race: GitHub Issues has no create-idempotency-key or unique-constraint API. Do not claim otherwise in code/docs. If a later production requirement mandates cross-instance exactly-once semantics, it needs a durable transactional coordinator (database/KV) or a product-approved backend change, which is explicitly out of scope for “no new external services”. Add this limitation as a concise source comment beside the singleton.

## Implementation steps

### 1. Add an isolated, testable coalescing cache

Create `src/lib/report-dedupe.ts`.

Expose a small generic class plus the endpoint singleton/test reset hook, following `rate-limit.ts`'s injectable-time/reset pattern:

```ts
export interface ReportDedupeOptions {
  ttlMs?: number; // default: 60_000
  now?: () => number;
}

type Completed = { issueUrl: string | null; expiresAt: number };

export class ReportDeduper {
  private readonly pending = new Map<string, Promise<{ issueUrl: string | null }>>();
  private readonly completed = new Map<string, Completed>();

  async run(
    key: string,
    create: () => Promise<{ issueUrl: string | null }>,
  ): Promise<{ issueUrl: string | null }> {
    // purge/return a completed result only while now < expiresAt
    // return an existing pending promise before invoking create
    // call create exactly once and put its promise in pending synchronously
    // on success: move result to completed with now() + ttlMs
    // on rejection: do not cache; rethrow
    // always remove the pending entry only if it is this call's promise
  }

  reset(): void { /* clear both maps */ }
}

export const reportDeduper = new ReportDeduper();
export function resetReportDeduper(): void { reportDeduper.reset(); }
```

Use a `finally`/identity check so an older completion cannot erase a newer reservation for the same key. The cache must not retain failures, tokens, raw payloads, IPs, or email addresses—only the opaque digest and GitHub-provided issue URL. Ensure expired completed entries are deleted opportunistically; retain at most the configured TTL.

Keep `node:crypto` hashing in the route (the route is a Node serverless route today; no Edge runtime is declared). Add a private function in `route.ts`, near payload normalization, which hashes an explicit length-delimited JSON array of:

```ts
[reason, waterSlug, waterName, details, contactEmail]
```

These values are already trimmed and capped by the route. Including every report-visible semantic field prevents merging a report whose reason/details/contact differ; excluding `website` is correct because honeypot traffic exits earlier. Use `createHash('sha256').update(JSON.stringify(fields), 'utf8').digest('hex')`. The digest must never be returned to the browser or logged.

### 2. Route the existing GitHub creation through the deduper

Modify `src/app/api/report/route.ts` only after current validation/honeypot checks:

- Import `createHash` from `node:crypto` and `reportDeduper` from `@/lib/report-dedupe`.
- Extract the current rate-limit, token check, `buildIssueText`, GitHub `fetch`, generic `502`, and successful `{ ok: true, issueUrl }` flow into the callback supplied to `reportDeduper.run(digest, callback)`.
- Return the same public success contract for a newly-created or cached report:

```ts
return NextResponse.json({ ok: true, issueUrl: result.issueUrl });
```

- Preserve all existing error codes/statuses and token-safe logging. A rejected GitHub operation must propagate to the existing `502` response and must not populate the completed cache.
- Keep the server response backwards-compatible: no required header, no changed response shape, and no extra service/config variable.
- Make the ordering explicit in a comment: validated human request → dedupe/coalesce → first request uses rate limit → GitHub issue creation. Do not move schema validation behind cache lookup.

### 3. Make the form’s double-submit protection synchronous and preserve retry UX

Modify `src/components/verification/ReportForm.tsx`:

- Import `useRef` and create `const isSubmittingRef = useRef(false)`.
- At the top of `submit`, return when `!reason || isSubmittingRef.current`; otherwise set the ref before `setPhase('submitting')`.
- Leave the button disabled when `phase === 'submitting'`; add `aria-busy={phase === 'submitting'}` to the form or submit button if it fits the component’s existing semantics.
- Clear the ref only on the failure path (non-OK response, JSON/parsing failure, or thrown fetch). Do not clear it after successful submission: the success screen replaces the form, so the dialog session remains terminal until Close/reset.
- In `reset`, set the ref back to `false`, so closing/reopening starts a genuinely new report session. Do not clear the latch just because a stale request completes after the dialog has been closed; use a local `submitted`/mounted-safe flow if needed so the existing component never calls state setters after dismissal.
- Preserve the exact JSON request shape; this change is UI coalescing, not a new client/server protocol.

### 4. Add deterministic unit coverage for cache behavior and the API integration

Create `src/lib/report-dedupe.test.ts` with no timers/network:

1. Two `run()` calls for the same key before a deferred `create` promise resolves receive the same result and invoke `create` once.
2. A second identical call after success within TTL returns the cached issue URL and still invokes `create` once.
3. Advance injected `now()` beyond TTL; the next same-key call invokes `create` again (the legitimate later-report acceptance criterion).
4. A rejected create is evicted; a subsequent call invokes a new successful create (retry remains possible).
5. Different keys do not merge.

Update `src/app/api/report/route.test.ts`:

- Import and call both `resetReportRateLimiter()` and `resetReportDeduper()` in `beforeEach`; this prevents module singleton state from leaking between tests.
- Add a deferred mocked GitHub `fetch`, start two valid `POST(request(samePayload))` calls without awaiting either, resolve the deferred response once, then assert both route responses are `200` with the same `issueUrl` and `fetchMock` was called exactly once.
- Add a sequential same-payload retry test within the TTL with the same single-fetch assertion.
- Add a payload-difference test (e.g. `details: 'A'` vs `details: 'B'`) asserting two GitHub creates, so the dedupe is not overly broad.
- Retain existing validation, honeypot, `503`, `502`, and authorization-header tests. All GitHub behavior remains `vi.stubGlobal('fetch', ...)`; no token or real HTTP call.

Optionally extend `tests/e2e/specs/flows/report.spec.ts` (not a substitute for the unit tests): make the mocked `/api/report` response wait on a promise, double-click/attempt a second submit, assert the button becomes disabled while pending, release the response, and assert exactly one intercepted POST plus the existing confirmation state. Keep the route stubbed.

### 5. Verify in the required order

From `/home/stefan/undepescuim`, with no real GitHub token required:

```bash
npm test -- src/lib/report-dedupe.test.ts src/app/api/report/route.test.ts
npm test
npm test -- --coverage
npm run lint
npm run build
```

If the execution task modifies client E2E coverage, run its focused test after the unit/coverage gate:

```bash
npm run test:e2e -- tests/e2e/specs/flows/report.spec.ts
```

Report the actual coverage output and inspect `git diff --check` / `git status --short` before committing. Do not run any command that creates a real GitHub issue; test fetches must remain mocked.

## Risks and trade-offs

- A 60-second TTL deliberately prevents immediate accidental duplicates while allowing a user to submit the same observation later. Treat it as a named constant with a comment, not magic inline arithmetic. Product can adjust the window after observing use.
- Canonicalizing only the route-normalized fields makes whitespace-only differences merge and meaningful field differences remain distinct. This matches the #35/#36 failure mode.
- Deduping before rate-limit accounting lets harmless same-payload retries succeed without self-throttling. It does not weaken flood protection for distinct payloads.
- The in-memory map is bounded in time but not globally durable. It is the strongest coordination available under the stated no-new-service constraint; do not silently turn it into a false durable-idempotency promise.
- The existing rate limiter has the same per-instance caveat. The implementation should use a module singleton consistently rather than exposing cache internals to components.

## Acceptance verification matrix

| Scenario | Expected proof |
|---|---|
| User double-clicks submit | Form button/latch allows one fetch; pending state is visible; success is terminal. |
| Two same payload requests overlap | Route test: two `POST` promises, one mocked GitHub `fetch`, same `issueUrl`. |
| Browser retries after a successful response was lost | Route test: same normalized payload within TTL yields cached URL and one create. |
| GitHub create fails | Existing `502`; cache eviction test proves retry can call GitHub again. |
| Same payload after TTL | Unit test with injected time makes a second create. |
| Different report details | Route test proves two creates. |
| Existing endpoint/security contract | Existing route tests remain green; no API response/schema change; token never logged. |

## Out of scope

- Closing or modifying historical issues #35/#36.
- A durable multi-instance idempotency store, new hosted service, database migration, GitHub search-based reconciliation, or changing GitHub token scopes.
- Automatic client retry logic. The server makes a manual retry safe within the warm-instance TTL; automatic retry policy needs a separately specified UX/network policy.
