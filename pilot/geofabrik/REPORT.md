# Pilot report — Geofabrik Romania geometry coverage

Date: 2026-08-21
Branch: `pilot/geofabrik-geometry-coverage`
Environment: local build only; no Vercel preview and no Production deployment.

## Scope and before inventory

Bounded region: Covasna county, source extract bbox `[25.43,45.75,26.20,46.35]`.
The exact five-record batch is fixed and recorded in `artifacts/inventory.json`:

| slug | case | before |
|---|---|---|
| `anpa-anpa-0252` | bbox/dot fallback | no geometry, bbox present |
| `anpa-anpa-0261` | geometry-less shared-course child | no geometry, no bbox, riverGroup `buzau` |
| `anpa-anpa-0264` | same-name collision | no geometry, no bbox, riverGroup `negru` |
| `basca-mare-covasna` | real geometry gap | no geometry, no bbox, riverGroup `basca-mare` |
| `anpa-anpa-0253` | unresolved/negative control | no geometry, bbox present |

No canonical record is changed. All five remain explicit unresolved cases after
this strict pilot; no guessed lines replace placeholders.

## Pinned source and extraction

- URL: `https://download.geofabrik.de/europe/romania-latest.osm.pbf`
- PBF retrieval size: 326,388,442 bytes (312 MiB on disk)
- SHA-256: `707bbc4e8bf73ab39582cafa0d7e1c3f83b2281fb327f54714e803173ce02842`
- Retrieval timestamp and legal note: `artifacts/source.json`; OSM ODbL 1.0 and Geofabrik terms apply.
- Extract: 582 named waterway ways, preserving OSM way IDs, names, tags, and node coordinates in `covasna_named_waterways.jsonl`.
- Rebuild: deterministic byte-identical JSONL on repeat.
- Runtime: 18.28 s wall time (22.81 s user + 1.20 s system).
- Peak RSS: 1,094,792 kB (~1.04 GiB), measured with `/usr/bin/time -v`.
- Pilot artifact disk: 1,209,237 bytes excluding the ignored PBF.

## Matching and measurements

The only automatic acceptance gate is a unique normalized exact-name match. Name
normalization removes diacritics and generic river prefixes. Candidate source IDs,
geometry hash/type, endpoint node count, confidence, classification, and checkedAt
are written to `artifacts/pilot_ledger.json`.

- Pilot batch accepted: 0/5 (coverage 0% under this deliberately conservative gate).
- Known-positive control (`romsilva-covasna-aita`, existing verified geometry): 1/1
  accepted; measured precision 1.0, recall 1.0.
- Same-name and no-match records remain `UNRESOLVED_NO_EXACT_NAME`; ambiguous
  candidates are never selected. The accepted control is the only feature in
  `accepted_geometry.geojson` and carries source IDs and its geometry hash.
- False-positive count: 0 in the batch and known-positive control.

This is evidence for a reviewed candidate pipeline, not evidence that automatic
scaling can reach 90/95/99% coverage. The next experiment needs county-aware
aliases, topology/endpoints, relation extraction, and manual review fixtures.

## Rendering/test gates

- `pytest -q pilot/geofabrik/tests/test_pilot.py`: 5 passed.
- `npm run build`: passed (Next.js production build, TypeScript completed).
- Existing map app smoke on mobile and desktop: 2 passed (`app-load.spec.ts`).
- Pilot renderer contract: accepted GeoJSON is a separate artifact; unresolved
  rows have null geometry and are required by tests to remain so. No application
  layer loads it by default, so the current app remains the rollback behavior.

## Go/no-go and rollback

GO only for a second isolated, manually reviewed candidate experiment. NO-GO for
merging pilot geometry, changing canonical data, or scaling automatically to any
90/95/99% target. Rollback is deleting/ignoring `pilot/geofabrik` and removing the
pilot branch; canonical data and Production are untouched. No credentials,
provider, DNS, payment, Firecrawl, or Vercel changes were made.
