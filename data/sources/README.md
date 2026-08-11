# HOTOSM Waterways of Romania — source files

## Provenance

- **Dataset:** Waterways of Romania (HOTOSM / Humanitarian OpenStreetMap Team export)
- **Source:** https://data.humdata.org/dataset/hotosm_rou_waterways
- **Download URL (GeoJSON, 30.6 MB zip):**
  `https://production-raw-data-api.s3.amazonaws.com/ISO3/ROU/waterways/hotosm_rou_waterways_osm_geojson.zip`
- **Snapshot date:** 2026-08-07 (HDX monthly export)
- **Fetched:** 2026-08-11
- **License:** Open Database License (ODC-ODbL) — © OpenStreetMap contributors

## Files

The following large files are NOT committed to git (see `.gitignore`).
Re-download them to regenerate `data/premapped/*`:

- `hotosm_rou_waterways_osm_geojson.zip` — 30.6 MB zip from HDX
- `waterways.geojson` — extracted FeatureCollection (~150 MB, 98,713 features:
  79,672 LineString / 18,360 Polygon / 628 Point / 53 MultiPolygon)

## How the Tier 1 premap uses this data

`scripts/sources/premap-tier1.py` loads `waterways.geojson`, filters
`waterway=river` for the 13 pre-mapped rivers and `natural_class=water` /
`water=lake|reservoir` for the 15 pre-mapped lakes, matches names with
diacritic-normalized comparison, and writes one FeatureCollection per feature
to `data/premapped/<slug>.geojson`. The Danube is fetched separately via the
Overpass API (see `data/premapped/README.md`).

## Choice of GeoJSON over GPKG

The proposal suggested the GPKG (43 MB). ogr2ogr/GDAL is not installed in this
environment, so the HDX **GeoJSON export (30.6 MB, identical OSM data)** was
used instead — it parses with Python stdlib only (`json`), no GDAL/venv needed.
The GPKG remains a drop-in alternative if future steps require it.
