# Geofabrik Romania geometry pilot

This is an isolated, pilot-only layer on branch `pilot/geofabrik-geometry-coverage`.
It does not modify `public/data/waters.json`, ownership, contracts, associations,
or county clips. The PBF is deliberately gitignored because it is a 312 MB
reproducible download; `artifacts/source.json` records the retrieval and SHA-256.

## Rebuild

```bash
python3 -m venv /tmp/geofabrik-venv
/tmp/geofabrik-venv/bin/pip install osmium
curl -L --fail -o pilot/geofabrik/data/romania-latest.osm.pbf \
  https://download.geofabrik.de/europe/romania-latest.osm.pbf
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py inventory
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py source
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py extract
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py match
```

The bounded region is Covasna (bbox 25.43,45.75–26.20,46.35), and the exact
five-record batch is fixed in the script: one bbox fallback, one geometry-less
shared-course child, one same-name collision, one real geometry gap, and one
unresolved negative control. Matching is candidate-only: unique normalized exact
name is the only accepted gate; ambiguity and no-match remain review/unresolved.

## Artifacts

- `inventory.json`: exact batch and before-state from canonical data (read-only).
- `source.json`: URL, retrieval timestamp, size, SHA-256, and ODbL/Geofabrik note.
- `covasna_named_waterways.jsonl`: 582 named local OSM ways with way IDs/tags.
- `pilot_ledger.json`: source IDs, geometry hashes, confidence, endpoint evidence,
  classification, and checkedAt for all five batch records plus one known-positive
  validation control (`romsilva-covasna-aita`).
- `accepted_geometry.geojson`: pilot-only normalized geometry for accepted controls.

Measured extract runtime is recorded by the script; the 312 MB PBF is not served
or copied into the app. The known-positive control is accepted with precision and
recall 1.0. All five pilot batch records remain unresolved under the intentionally
strict exact-name gate; none receives a guessed line. This is a GO for a larger
reviewed candidate experiment, not a GO for automatic scaling to 90/95/99%.

## Rendering and rollback

No app source or canonical data was changed, so the existing local app remains the
rollback state. A future preview renderer must load `accepted_geometry.geojson`
under an explicit pilot flag and render only `ACCEPTED_DETERMINISTIC` features;
unresolved records must remain dots/placeholders. No Vercel deployment was made.
