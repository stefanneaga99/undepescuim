# ADR 0001 — River network and pre-cut sectors

Status: accepted · Date: 2026-10-16
Full plan: [`docs/plans/river-geometry-v2.md`](../plans/river-geometry-v2.md)

## Context

River and sector geometry is the residue of ~45 scripts that edit `public/data/waters.json` in
place. There is no from-scratch geometry build, and the key OpenStreetMap inputs are gitignored.
Contracted sectors ("limite") are never parsed into endpoints: sectors are stored as fractions of a
river course whose ordering is guessed (PCA plus a latitude heuristic). A read-only audit found:

- only 68 of 1,013 waters have source-backed sector endpoints;
- only 22% of single-contract rivers are drawn within ±25% of the contracted length;
- chord edges up to 51 km (Barcău) and 229 gaps over 1 km between consecutive course parts;
- the M9 parse budget is at 5.72 MB of 6 MB.

## Decision

1. **OpenStreetMap is the only geometry source.** The input is a dated Geofabrik extract, normalised
   to JSONL, published as a release asset and pinned by SHA-256.
2. **Topology comes from shared OSM node IDs**, never from proximity, PCA or latitude.
3. **Linear referencing in metres** (EPSG:3844) along a *course*; a sector is
   `(course_id, m_from, m_to)` with resolved, evidenced endpoints.
4. **A rule-based `limite` parser** turns the legal text into endpoints; resolvers snap them to
   confluences, dams, bridges, localities, county limits. No external geocoder.
5. **Human decisions live in git** as JSON override registries with reason, reviewer and date.
6. **Sectors are pre-cut in the pipeline.** A water switches only if it passes every invariant
   ("never worse"); multi-contract river groups switch all-or-nothing.
7. **The renderer stays Leaflet** until a measured benchmark says otherwise.
8. Legal and contract data are never mutated by geometry work.

## Consequences

- Geometry becomes reproducible and reviewable; OSM edits show up as diffs, not silent changes.
- Unresolved sectors keep the existing "unverified" UI state — honesty over coverage.
- The `public/data` contract gains `geometryKind`, `sectorStatus`, `sectorConfidence` and a lazy
  `sector-evidence.json`; legacy fields remain until the cleanup phase.
- Large downloads run in GitHub Actions workflows triggered by the owner, not in agent sandboxes.
- The legacy mutation scripts are frozen, then archived once most rivers are pre-cut.
