# ANAR „Hidrografie” (data.gov.ro) — fallback geometry layer

Checked 2026-10-17 via the CKAN API (`https://data.gov.ro/api/3/action/package_show?id=hidrografie`).

| | |
|---|---|
| Dataset | <https://data.gov.ro/dataset/hidrografie> |
| Publisher | Administrația Națională Apele Române (ANAR) |
| Licence | **CC BY 4.0** (`license_id: CC-BY-4.0`) — reuse allowed with attribution |
| Attribution text | „© Administrația Națională Apele Române (ANAR), data.gov.ro — CC BY 4.0” |
| Metadata last modified | 2026-09-16 |
| CRS | EPSG:3844 (Pulkovo 1942(58) / Stereo70); `.cpg` = UTF-8 |
| Scale | Not stated in the metadata. It is the digital cadastral network (*cadastrul apelor*); vertex density is sub-metre (≈ 15 M vertices for 4,917 courses). Measured against OSM after `EPSG:3844 → 4326` (pyproj default transformation): median offset **6–7 m** (Cibin, Ampoi, Lotru), so no datum correction is needed. |

## Resources

| Resource | Format | Size | Used |
|---|---|---|---|
| **Cursuri de apa rauri** (`cursuriaparauri.zip`) | Shapefile, PolyLine | 160 MB zip (249 MB `.shp`), 4,917 records, files dated 2025-02-12 | **yes** — one record per cadastral watercourse |
| Segmente de cursuri de apa rauri | Shapefile | 161 MB | no (same lines, split into segments) |
| **Confluente si izvoare retea hidrografică** (`izvoareconfluente.zip`) | 2 Shapefiles, Point | 1.1 MB; `Confluente` 4,822 pts, `Izvoare` 5,150 pts (2025-05-06) | not yet — see below |
| Bazine / Sub bazine hidrografice, Lacuri naturale, Lacuri de acumulare, Baraje, Diguri | Shapefile | 0.2–16 MB | no (candidates for lakes / dams later) |

### `CursuriApaRauri` attributes that matter

* `codcadas_1` — cadastral code, e.g. `RO12-1-17-24-3-0-0`. Unique per record. **Topology comes from it**: the parent is the code with its last non-zero level set to 0 (`RO12-1-17-24-0-0-0`). Lettered levels (`0a`, `5b`) are side branches.
* `denumire` (display name, diacritics mostly present), `denumireal` (ASCII), `denumire_1` (upper case), `denumire2`, `denumirein`. Alternative names appear in parentheses: `Viseu (Borsa)`, `Baboia (Eruga, Baboias)`.
* `canal`, `derivatie` flags; `ordin` (stream order in the cadastral hierarchy); `st_length_` (m); `codaba` / `denumireab` (basin authority).
* Direction: lines are digitised **source → mouth**. Measured: for 4,776 of 4,814 tributaries the last vertex is the one nearest the parent course; the remaining 38 are flipped by the adapter.
* 13 records are multipart; parts closer than 250 m are joined, otherwise the longest chain is kept (`qa: multipart_dropped`).

### `Confluente si izvoare`

* `Confluente`: `id_localid` encodes `<tributary code>_S<seg>/<main code>_S<seg>/<main code>_S<seg>_<x>_<y>`, `node = Jonction`.
* `Izvoare`: one point per source, with the old cadastral code (`cod` `1.1.1 .13 .0 .0 .0`), `nume`, length/altitude/slope/basin statistics.
* Not needed by the adapter today: junction positions are computed by projecting each tributary's outlet onto its parent course, and SOURCE is `m = 0`. They would matter for plan T6.5's "+0.05 anchor confidence" idea and for distinguishing same-named springs.

## How the pipeline uses it (plan T6.5)

OSM stays primary (plan D1). The ANAR layer only fills what OSM lacks:

1. `rivernet normalise-hidrografie --shp CursuriApaRauri.shp --zip cursuriaparauri.zip --modified 2025-02-12 --out anar-hidrografie.jsonl.gz` → extract-schema JSONL: one `way` per course, `tags.ref` = cadastral code, `name` / `alt_name`; simplified at 2 m in EPSG:3844, 6 dp WGS84 (12 MB). Published as release asset `anar-hidrografie-20250212`, pinned by `data/rivernet/fallback_manifest.json` (kept separate from `input_manifest.json` so the geometry ledger's manifest hash does not change).
2. `rivernet fallback` (after `build` and `parse`) builds `anar:<code>` course records — `receives_into` and `junctions` from the code hierarchy, county intervals from `public/data/counties.geojson` — for the courses a water can actually reach (name/stem of a river water, or a CONFLUENCE target, in that water's county, and not already answered by an OSM course there), and merges them into `courses.jsonl.gz` / `course_index.json` with `source: "anar"`.
3. `rivernet match` tries ANAR last (tier 3), after OSM by name key (tier 1) and OSM by inflection-insensitive stem (tier 2).
4. `rivernet resolve`: a CONFLUENCE endpoint whose tributary is missing from OSM can be anchored at an ANAR tributary's outlet within 300 m (`anar_outlet`, confidence 0.75). A sector on an ANAR course is capped at `medium` confidence; a fuzzy-name ANAR match is always `review`.

Attribution: when sectors built on ANAR geometry are published (cutover, T4.4), add the attribution above to `public/data/osm-lineage.json` and `MapAttribution.tsx` in the same PR.

## Coverage measured before building (2026-10-17)

Of the waters the OSM matcher could not place (`data/sectors/matches.jsonl` at `f08886a`: 235 `no_candidate` + 30 `no_county_match` = 265):

| ANAR course in the water's county, by | waters |
|---|---|
| exact name key (`river_match_keys`) | 59 |
| stem equality or fuzzy stem ≥ 0.8 (upper bound, includes wrong hits) | 115 |
| none | 150 (canals and drainage networks, "X și afluenții", hyphenated multi-river names, streams below the cadastral threshold) |

## Official cadastral network (not open)

The full *cadastrul apelor* river network with official lengths is held by ANAR. A Law 544/2001 request is drafted in [`anar-request-ro.md`](anar-request-ro.md).
