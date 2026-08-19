# Offline OSM river segment index

`build_osm_river_segment_index.py` consumes an already downloaded Overpass JSON
snapshot and never performs network access. It writes deterministic JSONL (gzip
when the output ends in `.gz`) containing every way's node IDs, resolved
coordinates, tags and missing nodes, followed by every relation's ordered way
members, aliases and missing-member diagnostics. The companion manifest records
snapshot/index SHA-256 values, schema version and element counts.

Example:

```bash
.venv/bin/python scripts/build_osm_river_segment_index.py \
  --input data/raw/overpass_water_all.json \
  --out data/cache/osm_river_segments_v1.jsonl.gz \
  --manifest data/processed/osm_river_snapshot_manifest.json \
  --no-network
```

The command is read-only with respect to the snapshot and public data unless
`--repair` is explicitly supplied. With `--repair`, only the approved
Cerna–Vâlcea, Ialomița, Șieu and Timiș scope is considered. A repair requires
one complete, unambiguous OSM relation per owner and geometry-only findings;
ambiguous or incomplete evidence remains blocking. Repairs preserve
`public/data/waters.json.audit-backup.json`, emit a before/after JSON diff and
OSM provenance, and re-run the audit before evaluating the gate. Contract
ownership, association, source rows and contractual fractions are never
modified.

component, main-stem, sampling and bidirectional coverage primitives. It uses
endpoint connectivity rather than the legacy degree-based matching gaps.

Verification:

```bash
.venv/bin/python -m pytest tests/test_river_segment_audit.py -q
sha256sum data/cache/osm_river_segments_v1.jsonl.gz
```

Run the index twice into separate paths and compare the SHA-256 values to check
reproducibility. The large pinned index is generated explicitly by the data
refresh workflow; normal tests use the compact fixtures in
`tests/fixtures/osm_segment_cases.json` and `osm_relation_members.json`.
