# Pilot 2 report — reviewed Covasna Geofabrik geometry preview

Date: 2026-08-21
Route: `/pilot/geofabrik` (isolated, noindex); root `/` remains canonical.

## Inventory and review gate

The ordered five-record batch is unchanged: `anpa-anpa-0252` (bbox fallback),
`anpa-anpa-0261` (geometry-less child), `anpa-anpa-0264` (same-name collision),
`basca-mare-covasna` (real geometry gap), and `anpa-anpa-0253` (exact negative
control). The negative control is present in the ledger as
`UNRESOLVED_INSUFFICIENT_EVIDENCE` and is absent from accepted GeoJSON.

Discovery is candidate-only. The bounded artifact currently contains 0 candidates;
all five records remain explicitly unresolved. No alias, distance, OSM physical
course, or topology observation is treated as contract ownership or legal endpoint
evidence. `review-decisions.json` is manually authored and records the decision and
reason for each original slug.

## Reproducibility and measured results

Pinned source: Geofabrik Romania latest PBF, 326,388,442 bytes,
SHA-256 `707bbc4e8bf73ab39582cafa0d7e1c3f83b2281fb327f54714e803173ce02842`.
The PBF remains gitignored; the committed source metadata and derived artifacts
are the reproducibility record. Two complete local `rebuild` runs produced byte-identical
candidate discovery, ledger, and accepted GeoJSON artifacts.

| metric | measured value |
|---|---:|
| rebuild runs | 2 |
| candidate count | 0 |
| batch accepted | 0/5 |
| batch coverage before → after | 0.0% → 0.0% |
| unresolved batch | 5 |
| false positives | 0 |
| batch precision | N/A (0 accepted) |
| match runtime | 0.19 s wall |
| peak RSS | 87,484 KiB |
| pinned PBF bytes | 326,388,442 |
| pilot generated artifact bytes | 10,367 |

Artifact hashes are recorded in `artifacts/metrics.json`.

## Preview and isolation

`/pilot/geofabrik` loads only `/pilot/geofabrik/accepted_geometry.geojson` and
`pilot_ledger.json`, validates provenance fail-closed, and displays an always-visible
experimental badge. The current accepted feature collection is empty, so the badge
says no reviewed candidates cleared the gate. The route is not linked from Header,
PWA precache, or normal app data loading. Root route isolation is covered by the
regression spec and no canonical `public/data/*` file is modified.

## Verification

- `pytest -q pilot/geofabrik/tests/test_pilot.py`: 5 passed.
- `npm test`: 29 files, 250 tests passed.
- `npm test -- --run src/lib/pilot-geofabrik.test.ts`: 2 passed.
- `npm run lint`: exit 0; one pre-existing warning in `src/hooks/use-geolocation.test.ts` (pilot files clean).
- `npm run build`: passed twice after the route fix.
- Preview e2e spec added for desktop/mobile projects and root request isolation; execution requires the configured Playwright browser/server environment.

## Pilot 2B physical-course preview

The isolated preview now renders physically extractable candidate geometry even when
it does not clear the legal review gate. `public/pilot/geofabrik/physical_course_candidates.geojson`
contains the source-traceable Târnava Mare course candidate for `anpa-anpa-0333`:
source `data/premapped/tarnava-mare.geojson`, generated `2026-08-11T10:41:03.396575+00:00`,
geometry SHA-256 `e2bfc3709af8b3634afb38b0b731841eaf8afc4b67409122ab84374a294d25ed`,
and confidence `source-traceable physical-course candidate`. The preview labels it
`experimental physical course — legal sector unverified`, preserves the 5 Km contract
card and `Aval baraj lac Zetea – pod Desag` text, and never paints orange legal geometry.
The candidate remains excluded from canonical data, ownership, association, contract,
and Production paths.

## Decision

NO-GO for canonical integration, Production, ownership, contracts, or endpoint
claims. A separate authority/legal endpoint review is required before any canonical
change. The isolated preview is a usable physical-course visualization, not evidence
that the candidate is a verified legal sector.
