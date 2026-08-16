<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## QA Gate — test-before-merge (USER MANDATE, 2026-08-16)

Every task that touches **logic** (src/utils, src/stores, src/hooks, src/lib,
src/app/api) or the **data pipeline** (scripts/*.py) must ship tests in the
same PR/commit. No test = blocked at review.

- **TS (app):** `npm test` — vitest; `npm test -- --coverage` enforces the
  hard gate: ≥80% lines/functions/statements, ≥75% branches on
  src/utils|stores|hooks|lib|api (see vitest.config.mts).
- **Python (pipeline):** `.venv/bin/python -m pytest` — unit/integration
  tests under tests/, fixtures under tests/fixtures/. Never hit the network
  (monkeypatch requests/Nominatim/Overpass/GitHub), no wall clock, no
  data/cache/geocode.db dependency (plan §4.3).
- **Parity:** `tests/test_parity_vs_frontend.py` +
  `src/utils/river-course.test.ts` assert the SHARED golden fixture
  (tests/fixtures/winding_river.geojson + parity_expectations.json) produces
  identical course fractions on BOTH sides — TS↔Python math drift fails CI.
- **CI:** `.github/workflows/test.yml` runs both suites with the coverage
  thresholds on push/PR.
- Manual/browser probes (`scripts/_e2e_*.mjs`, `scripts/_qa_*.py`) are
  intentionally NOT part of the gate (testing-plan §1).
