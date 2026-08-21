# Geofabrik Romania geometry pilot

Pilot 2 is a review-gated, isolated Covasna physical-course experiment. It never
mutates `public/data/waters.json`, county clips, contracts, associations, ownership,
endpoints, or `riverGroup`. OSM geometry is physical-course evidence only and is
not legal contract/ownership/endpoint evidence.

## Rebuild

```bash
python3 -m venv /tmp/geofabrik-venv
/tmp/geofabrik-venv/bin/pip install osmium
curl -L --fail -o pilot/geofabrik/data/romania-latest.osm.pbf https://download.geofabrik.de/europe/romania-latest.osm.pbf
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py inventory
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py source
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py extract
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py discover
/tmp/geofabrik-venv/bin/python scripts/pilot_geofabrik_geometry.py match
```

`discover` writes candidate-only records. `match` joins those records to the
manually authored `review-decisions.json`; only provenance-complete
`ACCEPTED_REVIEWED` rows with exact OSM IDs can enter `accepted_geometry.geojson`.
The current five-record batch has zero accepted candidates. The exact negative
control `anpa-anpa-0253` is unresolved and absent from the artifact.

## Preview

An explicit copy step publishes the generated artifacts under
`public/pilot/geofabrik/`, then `/pilot/geofabrik` renders only accepted reviewed
features. The page is noindex/nofollow, visibly experimental, and not in normal
navigation or PWA precache. The current preview is intentionally empty and says so.

See `REPORT.md` and `artifacts/metrics.json` for measured results, hashes, and the
final NO-GO recommendation for canonical integration.
