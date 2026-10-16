# River geometry v2 — implementation plan

Status: ready for execution · Author: planning session 2026-10-16 · Repo: `stefanneaga99/undepescuim` at `e85b1f3`
Background: `claude/precise-river-geometry-research.md` and `claude/repo-overview.md` in the "Unde pescuim" project.

This plan is written for executor agents (Claude Sonnet sessions in Claude Code). Each task is one branch and one PR. Do the tasks in dependency order. Do not redesign anything that is decided here. If a decision turns out to be impossible, stop and write up the blocker in the PR description instead of improvising.

---

## 0. Rules for every executor

1. **Read first.** `AGENTS.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, then this whole file. Before writing any Next.js code, read the relevant guide in `node_modules/next/dist/docs/` (AGENTS.md requires it).
2. **One task = one branch = one PR.** Branch name `geo/<task-id>-<short-name>`, e.g. `geo/t2.1-graph`. The PR title starts with the task ID. The PR description has three parts: what changed, how you tested it (exact commands with their output summary), and anything left over.
3. **Tests are mandatory** (owner mandate, AGENTS.md). Python logic goes under `tests/` and runs with `python -m pytest`. TS logic goes in `*.test.ts` beside the code. Keep coverage at ≥80% lines/functions/statements and ≥75% branches on `src/utils|stores|hooks|lib|app/api`. Tests never touch the network, never use the wall clock, and never read gitignored files.
4. **Never mutate the legal surface.** Leave these byte-identical: `data/processed/anpa_*`, `arebaltapeste_*`, `locuri_*`, `permit_*`, `public/data/associations.json`, and the `limite`, `dimensiune`, `asociatie`, `referinta`, `pescuit_interzis`, `name`, `judet`, `slug` fields in `waters.json`. Geometry work may only change the fields listed in §3.6.
5. **Determinism.** Every generator sorts its output (by slug or id), writes JSON with `sort_keys=True, ensure_ascii=False`, rounds coordinates explicitly, and produces byte-identical output on re-run. Add a test that runs it twice and compares.
6. **Network access.** The sandbox usually cannot reach Geofabrik, Overpass, the EEA, or sometimes even PyPI. All downloads happen in **GitHub Actions** workflows, which the owner triggers. Executors write the workflows and the code, and test against committed fixtures. If `pip install` fails in your sandbox, say so in the PR and rely on CI.
7. **Do not touch:** legacy `scripts/fix_*`, `geometry_batch*`, `sweep_*`, or `_diag/_qa/_probe*` scripts, except where a task says to. Cleanup comes in P8.
8. **Keep these green:** `npm test -- --coverage`, `npm run lint`, `npm run build`, `python -m pytest`, every step of `.github/workflows/data-integrity.yml`, and `node scripts/check-data-budget.mjs`.
9. **Commit attribution:** follow the attribution lines your session gives you.

---

## 1. Goal and how we measure it

Each contracted river sector should be drawn as the stretch between its two legal endpoints ("limite"). Each endpoint is resolved to an OpenStreetMap feature, with evidence and a confidence level. Anything that cannot be resolved should be shown honestly as unverified.

| Metric | Today (audit) | Target after P4 | Target after P5 review loop |
|---|---|---|---|
| River waters with source-backed endpoints (`sectorStatus = resolved`) | 68 / 761 | ≥ 350 | ≥ 550 |
| Resolved sectors with drawn km within ±25% of contracted km | 22% (single-contract), 38% (explicit) | ≥ 75% of resolved | ≥ 80% |
| Straight "chord" edges > 1 km in published river geometry | 33 over 5 km; 229 part gaps over 1 km | 0 in `geometryKind=sector` waters | 0 |
| M9 compact parse budget | 5.72 / 6 MB | ≤ 5.0 MB | ≤ 5.0 MB |
| Waters whose sector state is undefined | most | 0 (every river is `resolved`, `review`, or legacy-unverified) | 0 |

The targets are estimates. The tool `rivernet report` (T3.5) measures all of them, and every PR from P3 onwards pastes its output into the description.

---

## 2. Decisions (do not re-open)

| # | Decision | Why |
|---|---|---|
| D1 | **OpenStreetMap is the only geometry source** for P1–P5. The input is a dated Geofabrik `romania-latest.osm.pbf`, filtered and normalised into one JSONL file, published as a GitHub Release asset, and pinned by SHA-256. | It is the only large-scale, current, named, ODbL source; the site already uses ODbL. |
| D2 | **Topology comes from shared OSM node IDs**, never from coordinate proximity, PCA, or latitude. Coordinate snapping is used only to create *flagged* synthetic connectors (≤ 250 m, see T2.2). | This removes the chords and mis-ordering. |
| D3 | **Linear referencing in metres along a "course"**, with `m = 0` at the upstream (source) end, increasing downstream. A sector is `(course_id, m_from, m_to)`. All metric work is done in **EPSG:3844 (Stereo70)** through `pyproj`, and output is transformed back to EPSG:4326. | It matches today's `sectorStart`/`sectorEnd` convention (0 = source, 1 = mouth). |
| D4 | **Sectors are keyed by water `slug`.** Inputs come from `public/data/waters.json` (`name`, `judet`, `limite`, `dimensiune`, `subtype`). Nothing in `data/processed/anpa_*` is read for writing. | Slugs are the stable public key, and every slug already traces to a source row (`traceability_report.json`). |
| D5 | **The `limite` parser is a pure, rule-based Python function** with a table-driven test suite built from real strings. No ML, no external geocoders (no Nominatim) for endpoint resolution. Places, dams, and bridges come from the same OSM extract. | Results must be reproducible and auditable. |
| D6 | **Human decisions live in git** as JSON registries (`data/sectors/endpoint_overrides.json`, `data/sectors/course_overrides.json`). Every entry has `reason`, `reviewer`, and `date`. | The PR diff is the review tool; JSON matches the existing repo registries. |
| D7 | **Sectors are pre-cut in the pipeline.** River waters that resolve get their own sector `geometry` plus `geometryKind: "sector"`. The frontend renders that geometry directly. The owner/fraction model stays only for waters that don't resolve. | It removes the frontend fraction math for resolved waters and frees payload. |
| D8 | **All-or-nothing per `riverGroup`.** A multi-contract river group switches to pre-cut sectors only when **every** member resolves (`resolved`, or `review` with an accepted override). Otherwise the whole group stays legacy. Single-contract rivers switch individually. | Legacy members rely on the owner's full-course geometry; cutting the owner would break them. |
| D9 | **"Never worse" publishing.** A water switches only if its new geometry passes all invariants (§3.5). Otherwise it keeps its current legacy geometry and fields unchanged. | The cutover cannot reduce coverage. |
| D10 | **The renderer stays Leaflet through P6.** PMTiles/MapLibre is decided only by the P7 benchmark. | The research shows the renderer is not the cause of the imprecision. |
| D11 | **EEA WISE and EU-Hydro are optional enrichment (P6)**: official IDs, Strahler order, fallback geometry. They are not on the critical path. | Their value is IDs and topology; OSM gives better lines. |
| D12 | **New Python code lives in the package `scripts/rivernet/`.** It is importable in tests because `pyproject.toml` already sets `pythonpath = ["scripts"]`. The CLI is `PYTHONPATH=scripts python -m rivernet <cmd>`. | One home instead of 45 scripts. |
| D13 | **Dependencies** added to `requirements-dev.txt`: `networkx`, `pyproj`, `osmium` (pyosmium). Pin the latest stable versions at implementation time (`pip index versions <pkg>`) and record them in the PR. `shapely==2.1.2` and `numpy` are already pinned. | |

---

## 3. Target architecture

### 3.1 Data flow

```
[GitHub Actions: osm-extract.yml]   (owner triggers, network allowed)
  Geofabrik PBF ──osmium tags-filter──► filtered.pbf ──rivernet extract──► ro-water-YYYYMMDD.jsonl.gz
                                                                            └─► GitHub Release asset + sha256
[GitHub Actions: rivernet-build.yml]  (owner triggers or monthly; downloads the pinned asset)
  extract ──rivernet build──► network (in memory) ──► data/rivernet/qa.json, data/rivernet/courses.jsonl.gz
  waters.json + courses ──rivernet parse/match/resolve──► data/sectors/*.jsonl  (+ overrides)
  ──rivernet publish──► public/data/waters.json (sector waters only), public/data/sector-evidence.json
  ──legacy tail (build_locality_assignment, build_county_clip_geoms, split_county_clips, simplify_waters_geometry,
    build_geometry_ledger, build_class2_aggregate) ──► the rest of public/data
  → opens a PR with the diff and the `rivernet report` output
[PR CI: data-integrity.yml + test.yml]  (offline)
  validates the committed data/rivernet + data/sectors + public/data against the invariants; never rebuilds from OSM
```

### 3.2 Package layout (`scripts/rivernet/`)

```
scripts/rivernet/
  __init__.py
  __main__.py          # argparse CLI: extract | build | parse | match | resolve | publish | report | review-page
  textnorm.py          # Romanian normalisation (diacritics, ş/ș, ţ/ț, å→â, case, whitespace), name keys
  extract.py           # PBF/OSM-XML → normalised JSONL (pyosmium)       [T1.1]
  extract_schema.py    # dataclasses + loader for the JSONL records       [T1.1]
  graph.py             # directed waterway graph from JSONL               [T2.1]
  courses.py           # course stitching, measures, tributary junctions  [T2.2]
  qa.py                # loops, sinks, gaps, chords, stats                 [T2.3]
  lr.py                # linear referencing helpers (locate, substring, project) in EPSG:3844 [T2.2]
  limits_parser.py     # limite text → LimitSpec                          [T3.1]
  matcher.py           # water → course candidates                        [T3.2]
  resolvers.py         # EndpointSpec → candidate measures, per kind      [T3.3]
  sectors.py           # assemble, validate, status, overrides            [T3.4]
  publish.py           # write sector geometry/fields into waters.json    [T4.2]
  evidence.py          # public/data/sector-evidence.json                 [T4.3]
  report.py            # progress metrics                                 [T3.5]
  review_page.py       # standalone HTML review map (not shipped)         [T3.5]
```

### 3.3 Normalised extract — `ro-water-YYYYMMDD.jsonl.gz` (schema v1)

One JSON object per line. Coordinates are `[lon, lat]` rounded to 7 decimals. Only whitelisted tags are kept: `name, name:ro, alt_name, old_name, official_name, waterway, wikidata, ref, highway, railway, bridge, bridge:name, tunnel, intermittent, place, water, natural, landuse, boundary, admin_level, ref:siruta, ele`.

```jsonc
{"t":"meta","schema":1,"source":"geofabrik","osm_timestamp":"2026-10-15T20:21:00Z","pbf_sha256":"…","filters":"…"}
{"t":"way","id":123,"nodes":[1,2,3],"coords":[[..],[..],[..]],"tags":{"waterway":"river","name":"Mureș"}}
{"t":"node","id":456,"coord":[lon,lat],"tags":{"place":"village","name":"Băcăinți"}}
{"t":"rel","id":789,"tags":{"type":"waterway","waterway":"river","name":"Mureș"},"members":[{"type":"w","ref":123,"role":"main_stream"}]}
{"t":"area","id":"w555","tags":{"natural":"water","water":"reservoir","name":"Lacul Vidraru"},"geometry":{GeoJSON Polygon|MultiPolygon}}
```

What goes in:
- **Waterway ways:** `waterway ∈ {river, stream, canal}`. Ditches and drains are excluded.
- **Waterway relations:** all `type=waterway` relations, with their members.
- **Dams and weirs:** `waterway ∈ {dam, weir, waterfall}` as nodes and ways.
- **Bridges:** ways with `bridge=*` and `highway|railway`, kept if their bbox intersects the bbox of any waterway way. To keep it cheap, do this in the extractor by building an STRtree of waterway bboxes.
- **Places:** `place ∈ {city, town, village, hamlet, suburb, locality, isolated_dwelling}`.
- **Springs:** `natural=spring` nodes.
- **Water and reservoir areas:** `natural=water` or `landuse=reservoir`.
- **Admin areas:** `boundary=administrative`, `admin_level ∈ {2, 4, 8}` (country, județ, UAT).
- **Bbox:** clip everything to Romania's bbox expanded by 0.3° so the border rivers (Prut, Danube, Tisa) stay whole.

### 3.4 Course record — `data/rivernet/courses.jsonl.gz` (committed; only courses that are candidates for some water; see T2.4 for size rules)

```jsonc
{
  "course_id": "rel:123456" | "name:mures:n987654321",   // relation id, or name key + outlet node id
  "name": "Mureș", "name_key": "mures", "aliases": ["Maros"], "wikidata": "Q…" | null,
  "relation_id": 123456 | null,
  "way_ids": [..ordered upstream→downstream..],
  "length_m": 761234.5,
  "geometry": {"type":"LineString","coordinates":[[lon,lat],...]},   // 6 dp, upstream→downstream, NOT simplified
  "vertex_m": [0.0, 12.3, ...],                                        // cumulative metres per vertex (1 dp)
  "outlet_node": 987654321, "receives_into": "rel:…" | null,           // course the outlet joins
  "junctions": [{"node": 42, "m": 1234.5, "tributary_course_id": "name:…", "side": "in"}],
  "synthetic": [{"m_from": 100.0, "m_to": 260.0, "kind": "gap_bridge" | "reservoir_crossing", "gap_m": 160.0}],
  "braids_dropped_m": 3400.0,
  "counties": [{"county": "Alba", "m_from": 0.0, "m_to": 50213.0}],
  "qa": ["has_synthetic", "relation_member_missing", ...]
}
```

### 3.5 Sector record — `data/sectors/sectors.jsonl` (committed)

```jsonc
{
  "slug": "4pouq9sd", "name": "Râul Geoagiu Inferior", "judet": "Alba",
  "limite": "Cheile Râmet - conf. Cu Råul Mureş", "contract_km": 28.0, "includes_tributaries": false,
  "parse": {"scope": "interval", "from": {EndpointSpec}, "to": {EndpointSpec}},
  "course": {"course_id": "name:geoagiu:n…", "match_score": 0.93, "method": "name+county" | "override"},
  "from": {"m": 1234.5, "kind": "LOCALITY", "anchor": {"type":"node","id":456,"name":"Râmeț"}, "confidence": 0.7, "method": "place_projection", "dist_m": 840.0},
  "to":   {"m": 29876.0, "kind": "CONFLUENCE", "anchor": {"type":"node","id":42,"name":"Mureș"}, "confidence": 0.95, "method": "outlet_into_named"},
  "length_m": 28642.5, "km_ratio": 1.02,
  "status": "resolved" | "review" | "unresolved",
  "confidence": "high" | "medium" | "low",
  "reasons": ["km_ratio_out_of_band", "endpoint_ambiguous:from", ...],
  "override_ids": [],
  "network_version": "ro-water-20261015"
}
```

**Invariants** (checked by `rivernet.sectors.validate()` and by PR CI):
- `0 ≤ from.m < to.m ≤ course.length_m`, and `length_m = to.m − from.m`.
- A CONFLUENCE endpoint lies within 1 m of a junction node or of the outlet node of its course.
- The sector geometry has no segment longer than 1,000 m, except inside a recorded `synthetic` span.
- The sector intersects the polygon of its own `judet` (buffered 500 m). Sectors that cross a county limit are allowed when either endpoint is a COUNTY_LIMIT.
- A `resolved` status requires both endpoint confidences ≥ 0.6, and `km_ratio` in [0.6, 1.6]. When `includes_tributaries` is true, only the upper bound applies.
- `high` confidence requires min endpoint confidence ≥ 0.8 and `km_ratio` in [0.8, 1.25]. `medium` requires ≥ 0.6 and [0.6, 1.6]. Everything else is `low`.

### 3.6 Fields that geometry work may write in `public/data/waters.json`

For a water that switches to a pre-cut sector:
- **Set:** `geometry` (LineString or MultiLineString, 5 dp), `bbox`, `lengthKm`, `geometryKind: "sector"`, `sectorStatus: "resolved" | "review"`, `sectorConfidence`, `sectorStart`, `sectorEnd` (= m / course length, 4 dp; kept for compatibility until P8), `source: "rivernet"`, `source_detail: "rivernet:<network_version>"`.
- **Remove:** `course_frac`, `bbox_render`, `fallback`.
- **Keep:** `riverGroup` (unchanged) and `coordinates` / `driving` (unchanged unless null; if null, use the sector midpoint).

No other fields may change. A test enforces this (T4.2).

---

## 4. Tasks

Legend: **Dep** = must be merged first. **Size**: S ≤ 2 h, M ≤ 1 day, L ≤ 2 days for one executor. Tasks marked 👤 are for the owner.

### Parallel tracks

```
P0: T0.1 ─ T0.2 ─ T0.3 ─ T0.4 ─ T0.5        (all independent; do them first)
Track A (network):   T1.1 → T1.2 → 👤O2 → T2.1 → T2.2 → T2.3 → T2.4 → 👤O3
Track B (text):      T3.1 (start right after T0.5) ─────────────┐
Track C (frontend):  T4.1 (start right after T0.5) ──────────┐  │
                                         T3.2 → T3.3 → T3.4 → T3.5 → 👤O4 → T4.2 → T4.3 → T4.4 → 👤O5
After cutover: P5 (review loop) · P6 (enrichment) · P7 (rendering) · P8 (cleanup + drift)
```

---

### P0 — Stabilise

#### T0.1 Commit this plan and an ADR · Size S · Dep none
- Add this file as `docs/plans/river-geometry-v2.md`.
- Add `docs/adr/0001-river-network-and-precut-sectors.md`. It is a one-page summary of D1–D13: context, decision, consequences.
- Add one line to `docs/ARCHITECTURE.md` under "Pipeline și automatizare" pointing to the plan.
- **Accept:** docs only; CI green.

#### T0.2 Stop the monthly refresh from overwriting `public/data` · Size M · Dep none
**Problem:** `scripts/refresh-data.mjs` writes source outputs straight into `public/data/`. `scripts/sources/arebaltapeste.mjs:153-157` emits `waters.json` and `associations.json` as `{generatedAt,count,items}` wrappers plus `waters.geojson`. The frontend reads a bare `Water[]` (`src/stores/map-store.ts:242-246`).
- In `refresh-data.mjs`, change the output root from `public/data` to `data/raw/refresh/` (create it, and gitignore everything except a `.gitkeep`). Keep the "keeping last good data" behaviour.
- In `.github/workflows/data-refresh.yml`, stop committing `public/data/`. The job now only proves the scrapers still work, and uploads `data/raw/refresh/` as a workflow artifact (`actions/upload-artifact`, retention 30 days). Rename the job step to "Scrape sources (no publish)".
- Add a contract test `scripts/refresh-data.test.mjs`, or a vitest test in `src/lib/` if Node scripts aren't covered by vitest — check `vitest.config.mts` include globs and pick the one that runs in CI. The test asserts that the computed output directory is not under `public/`.
- **Accept:** `npm test` green. Running the workflow manually (👤) no longer changes `public/data`.

#### T0.3 Payload allowlist and remove the dead backup · Size S · Dep none
- `git rm public/data/waters.json.audit-backup.json`. Then grep `src/`, `scripts/`, and `tests/` for `audit-backup` and fix any reference.
- In `scripts/check-data-budget.mjs`, replace the `DEAD_WEIGHT` denylist with an **allowlist** of the files that may exist in `public/data/`: `.gitkeep`, `association_locations.json`, `associations.json`, `counties.geojson`, `geometry-ledger-manifest.json`, `geometry-ledger.json`, `osm-lineage.json`, `preview_class2_physical.json`, `uncontracted_lakes.json`, `uncontracted_majors.json`, `uncontracted_rivers.json`, `waters.json`, `waters_county_clips.json`, `meta.json` (generated by prebuild), `sector-evidence.json` (added later in T4.3; allow it now). Any other file is a FAIL.
- Add lazy-file budgets that report but do not block yet: gzip of `preview_class2_physical.json`, `geometry-ledger.json`, `waters_county_clips.json`, and `sector-evidence.json`. Print them as `INFO`.
- **Accept:** `node scripts/check-data-budget.mjs` passes. A test or fixture proves that an unknown file fails. If no test harness exists for the `.mjs` file, add `scripts/check-data-budget.test.mjs`, run by vitest if its config includes it, or factor the check into `src/lib/data-budget.ts` with a test.

#### T0.4 Make the legacy rebuild fail loudly · Size S · Dep none
- `scripts/rebuild_data.py` `cmd_to`: on a non-zero step exit, print `FAIL` and `sys.exit(1)` after the hash diff. Add a `--keep-going` flag that preserves the old behaviour.
- `scripts/merge_anpa_waters.py` `load_osm_index`: if `data/rivers_osm.geojson` is missing, raise `SystemExit("rivers_osm.geojson missing — legacy matcher cannot run")`. Add an `--allow-missing-index` flag for the old behaviour.
- **Tests:** extend `tests/test_rebuild_data.py` (the step runner is monkeypatched to return 1, so it asserts exit 1) and `tests/test_merge_anpa_waters.py` (missing file → SystemExit).
- **Accept:** `python -m pytest` green.

#### T0.5 Package skeleton, dependencies, CI wiring · Size S · Dep none
- Create `scripts/rivernet/__init__.py` (with `__version__ = "0.1.0"`), `__main__.py` (argparse with the subcommands from §3.2; every subcommand prints "not implemented" and exits 2 until its task lands), and `textnorm.py`.
- `textnorm.py`, fully implemented now, with tests in `tests/rivernet/test_textnorm.py`:
  - `fold(s) -> str`: NFC, then map `ş→ș, ţ→ț, Ş→Ș, Ţ→Ț, å→â, Å→Â`, then lowercase, then strip diacritics (NFKD and drop combining marks), then collapse whitespace, then strip punctuation except spaces and hyphens.
  - `river_key(name) -> str`: `fold`, drop the leading generic words `râul|raul|rau|râu|pârâul|paraul|pârâu|parau|pr|r|fluviul|canalul|valea*|vl` (\*`valea` is dropped **only** when the next token isn't itself a generic word), drop trailing qualifiers `superior|mijlociu|inferior|amonte|aval|i|ii|iii|iv|sector .*|zona .*`, and drop `de est|de vest` only if a course with the shorter key exists (handled by the matcher, not here: return both keys via `river_keys(name) -> list[str]`, most specific first).
  - Tests: ≥ 25 cases, including `"Råul Geoagiu Inferior"→"geoagiu"`, `"Crișul Repede Mijlociu"→"crisul repede"`, `"Valea Iadului"→["valea iadului","iadului"]`, `"Jiul de Vest"→["jiul de vest","jiul"]`, `"Pârâul Buzăul Mijlociu"→"buzaul"`, and Cyrillic input (passes through folded, no crash).
- Add to `requirements-dev.txt`: `networkx`, `pyproj`, `osmium` (pinned; see D13). In `.github/workflows/data-integrity.yml`, change the install step to `pip install -r requirements-dev.txt`.
- Create the empty dirs (with `.gitkeep`): `data/rivernet/`, `data/sectors/`, `tests/rivernet/`, `tests/fixtures/rivernet/`.
- **Accept:** `PYTHONPATH=scripts python -m rivernet --help` lists the subcommands. pytest green.

---

### P1 — Pinned OSM input

#### T1.1 Extractor: PBF/OSM → normalised JSONL · Size M · Dep T0.5
- Implement `rivernet/extract_schema.py`: frozen dataclasses `Way`, `Node`, `Rel`, `Area`, `Meta`, plus `load_extract(path) -> Extract`. `load_extract` reads `.jsonl` or `.jsonl.gz` and returns dicts keyed by id: `ways`, `nodes`, `rels`, `areas`, and `meta`.
- Implement `rivernet/extract.py` with `extract(input_path, output_path, *, bbox) -> Meta`, using pyosmium. It must accept `.osm.pbf` and `.osm` (XML) so tests can use XML fixtures.
  - Use `osmium.FileProcessor(...).with_locations()` for way node coordinates, and `.with_areas()` for polygons. Check the pyosmium docs for the version you pin; the API changed in 4.x.
  - Apply the inclusion rules and tag whitelist from §3.3. For the bridge filter, build a `shapely.STRtree` of waterway way bboxes in a first pass.
  - Write records sorted by (`t` order: meta, rel, way, node, area; then id). Write area geometry via `shapely.geometry.mapping`, rounded to 7 dp.
- CLI: `python -m rivernet extract --in X --out Y [--bbox minlon,minlat,maxlon,maxlat]`.
- **Tests** (`tests/rivernet/test_extract.py`), with a handcrafted `tests/fixtures/rivernet/mini.osm` (≈ 40 nodes):
  - two rivers meeting at a shared node, plus a stream;
  - a `type=waterway` relation;
  - a dam way crossing the river;
  - one bridge that crosses a river (kept) and one far away (dropped);
  - a village node, a spring node, and a reservoir multipolygon;
  - an `admin_level=4` boundary relation;
  - a way tagged `waterway=ditch` (dropped) and a tag outside the whitelist (dropped).
  - Assert record counts, that tags are whitelisted, that coordinates are rounded, and that the output is byte-identical across two runs.
- **Accept:** pytest green. In the PR description, document the expected size of a full-Romania run as "unknown until T1.2".

#### T1.2 Workflow `osm-extract.yml` + input manifest · Size M · Dep T1.1
- New `.github/workflows/osm-extract.yml`, triggered by `workflow_dispatch` only, with `permissions: contents: write`. Steps:
  1. `sudo apt-get install -y osmium-tool`, then set up Python 3.12 and `pip install -r requirements-dev.txt`.
  2. `curl -fL -o romania.osm.pbf https://download.geofabrik.de/europe/romania-latest.osm.pbf`, and record its sha256 and `osmium fileinfo -e` (for the timestamp).
  3. Pre-filter for speed: `osmium tags-filter romania.osm.pbf w/waterway=river,stream,canal nwr/waterway=dam,weir,waterfall r/type=waterway n/place=city,town,village,hamlet,suburb,locality,isolated_dwelling n/natural=spring nwr/natural=water nwr/landuse=reservoir r/boundary=administrative w/bridge -o filtered.osm.pbf`. Check the expression syntax against the osmium-tool docs.
  4. Run `PYTHONPATH=scripts python -m rivernet extract --in filtered.osm.pbf --out ro-water-$DATE.jsonl.gz`, where `$DATE` is the OSM data date as `YYYYMMDD`.
  5. Create a GitHub Release `osm-input-$DATE` with `gh release create` and attach the jsonl.gz and the raw PBF sha256 in a text file. Do not attach the PBF itself.
  6. Write `data/rivernet/input_manifest.json`: `{schema:1, network_version:"ro-water-$DATE", asset:{release_tag, file, sha256, bytes}, pbf:{url, sha256, osm_timestamp}, extract_schema:1, created_by_run:<run url>}`. Open a PR with only this file changed, using `peter-evans/create-pull-request`. Pin the action by version, check the latest at implementation time, and record it in the PR.
- Add `scripts/rivernet/fetch_input.py`: `python -m rivernet fetch-input` downloads the release asset named in the manifest using `gh release download`, verifies the sha256, and saves it under `data/cache/rivernet/` (gitignored). Add this subcommand to `__main__`.
- **Tests:** manifest schema validation (`tests/rivernet/test_input_manifest.py`): validate the committed manifest when present, otherwise a fixture manifest. Also test that `fetch_input` refuses a sha mismatch, with `subprocess.run` monkeypatched.
- **Accept:** the workflow passes `actionlint` if it's available, and the YAML is valid. 👤 **O2** runs it.

#### 👤 O1 / O2 — Owner actions
- **O1** (before any executor starts): give executor sessions push access to the repo (in Claude Code: attach the repo with push access), and enable Actions to create releases and PRs (Settings → Actions → Workflow permissions → read and write; allow GitHub Actions to create PRs).
- **O2** (after T1.2 merges): run "osm-extract" from the Actions tab, then merge the manifest PR it opens. Report the asset size in the PR.

---

### P2 — River network

#### T2.1 Directed graph · Size L · Dep T1.1 (code), O2 (only for the full-run numbers)
- `rivernet/graph.py`:
  - `build_graph(extract) -> WaterGraph`, where `WaterGraph` wraps `networkx.MultiDiGraph`.
  - **Nodes** are OSM node ids that are way endpoints, or that appear in ≥ 2 included waterway ways (junctions).
  - **Edges:** split every waterway way at its junction nodes. Each piece is one directed edge `u→v` in way direction. Edge attributes: `way_id, seq` (piece index), `waterway, name, name_key, wikidata, intermittent, tunnel`, `coords` (list), `length_m` (geodesic via `pyproj.Geod(ellps="WGS84").line_length`).
  - Helpers: `out_edges(node)`, `in_edges(node)`, `edges_by_name_key(key)`, `node_coord(id)`.
- Deterministic construction: iterate ways sorted by id.
- **Tests** (`tests/rivernet/test_graph.py`), on synthetic JSONL fixtures written inline in the test (helper `make_extract(ways=[...])`):
  - a Y confluence: 3 nodes have degree 3, and the edges keep direction;
  - a way crossing another way at a shared inner node gets split into 2 + 2 edges;
  - a way crossing another *without* a shared node does not create a junction (a "no proximity topology" test);
  - lengths within 0.1% of hand-computed geodesic values;
  - determinism.

#### T2.2 Courses, measures, synthetic connectors · Size L · Dep T2.1
- `rivernet/lr.py` (everything here works in EPSG:3844 via `pyproj.Transformer.from_crs(4326, 3844, always_xy=True)`):
  - `to_metric(coords)`, `to_wgs(coords)`;
  - `vertex_measures(coords_m) -> list[float]`;
  - `locate(course, lon, lat) -> (m, dist_m)`, using `shapely.line_locate_point` on the metric line;
  - `point_at(course, m) -> (lon, lat)`;
  - `substring(course, m_from, m_to) -> LineString(wgs)`, using `shapely.ops.substring`, which interpolates at the exact measure rather than snapping to a vertex.
- `rivernet/courses.py`:
  - `build_courses(graph, extract) -> list[Course]`, using this algorithm. Follow it exactly.
    1. **Relation courses.** For each `rel` with `tags.type=waterway` and `tags.waterway ∈ {river, stream, canal}`, sorted by id: take the member ways whose role is in {`main_stream`, `""`}, and their edges in the graph. Form the sub-DiGraph. Sources are nodes with in-degree 0 in the subgraph, sinks have out-degree 0.
       - If the subgraph is weakly connected and has one sink, the course is the **longest path** (weighted by `length_m`) from any source to the sink. Use `networkx.dag_longest_path` on the subgraph with sink-reachability enforced; if there's a cycle, see QA in T2.3 and break it by dropping the cycle's shortest edge, recording `qa: cycle_broken`. Edges not on the path become `braids_dropped_m`.
       - If there are several weakly connected components, order the components by connecting component *i*'s sink to the nearest source of another component. Add a **synthetic connector** if the gap is ≤ 250 m (`kind: gap_bridge`), or ≤ 5,000 m when both ends lie on or within 50 m of the same `area` with `water=reservoir|lake` or `landuse=reservoir` (`kind: reservoir_crossing`). Otherwise, split into separate courses `rel:<id>:<k>`, with `qa: relation_split`.
    2. **Name courses.** For every edge not used by a relation course, group by `wikidata` if set, else by `name_key` (edges with an empty name are not grouped). Within a group, take the weakly connected components, then apply step 1's chaining and longest-path logic. Course id = `name:<name_key>:n<outlet node id>`.
    3. **Unnamed edges** are not courses. They exist only as graph topology for junction detection.
    4. **Measures:** concatenate the edge coordinates of the chosen path, upstream to downstream, de-duplicating shared nodes. Synthetic connectors are straight segments. Compute `vertex_m` in EPSG:3844.
    5. **Outlet and receiving course:** `outlet_node` is the last node. `receives_into` is the course that contains the outlet node anywhere other than at its own end, or that continues downstream via an out-edge. The first match wins, by course id order.
    6. **Junctions:** every interior node of the path that has an in-edge not on the path gets a junction entry `{node, m, tributary_course_id}`. The tributary is the course containing that in-edge, or null for unnamed edges.
    7. **Counties:** intersect the course with each `admin_level=4` area and record the `[m_from, m_to]` intervals, merging touching ones.
- **Tests** (`tests/rivernet/test_courses.py`), on synthetic fixtures:
  - relation with a braid: the longest path is chosen and `braids_dropped_m` is right;
  - relation with a 100 m gap: one `gap_bridge`;
  - relation with a 3 km gap through a reservoir polygon: `reservoir_crossing`;
  - relation with a 3 km gap and no reservoir: split courses;
  - name course with a tributary: one junction at the right `m`;
  - measure monotonicity, and that the last `vertex_m` equals `length_m`;
  - `substring` endpoints are exactly at the requested measures (≤ 0.01 m);
  - `locate` on an off-line point returns the perpendicular foot;
  - a cycle is broken and flagged;
  - determinism.

#### T2.3 QA layer and real-river regression fixtures · Size M · Dep T2.2
- `rivernet/qa.py`: `qa_report(graph, courses) -> dict`, with counts and lists (lists truncated to the first 200, sorted):
  - `cycles` (strongly connected components larger than one node);
  - `sinks_inland` (sinks not on the Danube, the Black Sea coast, or the country border — use the `admin_level=2` area buffered 2 km, plus the Danube course);
  - `relation_splits`;
  - `synthetic_connectors` (count, total km, max gap);
  - `max_segment_m` per course (must be ≤ 1,000 outside synthetic spans);
  - `courses_total`, `km_total`.
  - Written to `data/rivernet/qa.json`.
- **Real fixtures from the committed index** (no network needed). Write `scripts/rivernet/fixtures_from_v1.py`. It reads `data/cache/osm_river_segments_v1.jsonl.gz`, which holds ways with `node_ids`, `coordinates`, and `name`, plus relations with ordered members, and turns a selection into normalised extract JSONL with `waterway=river` assumed. Generate and commit:
  - `tests/fixtures/rivernet/ialomita.jsonl.gz`: every way whose name folds to `ialomita`, plus its relation. This is the regression for the 49.9 km chord.
  - `tests/fixtures/rivernet/barcau.jsonl.gz`: names `barcau`. This is the regression for the 51.4 km chord.
  - `tests/fixtures/rivernet/bistrita.jsonl.gz`: the main Bistrița (Moldavia); filter by relation id, which you can find in the index.
  - `tests/fixtures/rivernet/olt_reach.jsonl.gz`: the Olt between lon 24.0 and 24.5. It has a reservoir chain, but the index has no areas, so assert gaps are reported, not bridged.
  - Keep each fixture under 1.5 MB gzip; clip by bbox if needed.
- **Tests** (`tests/rivernet/test_real_fixtures.py`):
  - for each fixture, the course builds, `max_segment_m ≤ 1000` outside synthetic spans, and length is within ±2% of a value recorded the first time the test is written (record it in the test with a comment saying how it was obtained);
  - Ialomița and Barcău have no edge > 1 km;
  - the outputs are deterministic.
- **Accept:** pytest green, and the fixture sizes are reported in the PR.

#### T2.4 `rivernet-build.yml` and committed course subset · Size M · Dep T2.3, O2
- `python -m rivernet build --extract <cached asset> --out-dir data/rivernet/` writes `qa.json` and `courses_all.jsonl.gz` (gitignored; for the review page and debugging).
- `courses.jsonl.gz` is committed. It contains only the courses that are a match candidate for at least one water. Until T3.2 exists, use this rule: any course whose `name_key` equals any `river_keys(water.name)` entry, for river waters. In T3.2, switch to the matcher's candidate set.
- **Size rule:** if `courses.jsonl.gz` exceeds 25 MB, stop committing it. Instead publish it as an asset on the same `osm-input-*` release, record its sha256 in `input_manifest.json` (`courses_asset`), and have PR CI read only `sectors.jsonl`, `qa.json`, and the published `waters.json`. Report which branch applies in the PR.
- New workflow `.github/workflows/rivernet-build.yml`, triggered by `workflow_dispatch`. It checks out, installs dependencies, runs `fetch-input` then `build` (later also `parse`, `match`, `resolve`, `report`; extend this workflow in each later task), and opens a PR with the changed `data/rivernet/**` and `data/sectors/**`.
- **Accept:** the workflow file is valid, and unit tests cover the CLI argument plumbing. 👤 **O3:** run it and merge the PR. Check that `qa.json` shows `cycles` and `sinks_inland` counts; investigating them is a P5 job, not a blocker.

---

### P3 — Sectors from `limite`

#### T3.1 `limite` parser · Size L · Dep T0.5 (parallel with Track A)
- `rivernet/limits_parser.py` exposes `parse_limits(text: str, *, water_name: str) -> LimitSpec`. It is pure and has no I/O.
- Types:
  ```python
  Kind = Literal["SOURCE","MOUTH","CONFLUENCE","DAM","LAKE_UPSTREAM","LAKE_DOWNSTREAM","BRIDGE",
                 "LOCALITY","COUNTY_LIMIT","BORDER","WATERFALL","ROAD","UNKNOWN"]
  @dataclass(frozen=True)
  class EndpointSpec: kind: Kind; target: str | None; qualifier: Literal["at","upstream","downstream"]
                      locality_hint: str | None; road_ref: str | None; raw: str
  @dataclass(frozen=True)
  class LimitSpec: scope: Literal["interval","whole_county","whole_course","locality_list","empty","unparsed"]
                   from_: EndpointSpec | None; to: EndpointSpec | None; localities: tuple[str,...]
                   county: str | None; includes_tributaries: bool; raw: str
  ```
- **Normalisation:** run `textnorm.fold` for matching, but keep the original-case substrings for `target`, with diacritics fixed via the ş→ș map.
- **Scope rules,** checked in order:
  1. Empty, `-`, or `—` → `empty`.
  2. `^(județ(ul)?|jud\.?)\s+X$`, `^pe raza (județului|jud\.?)\s+X`, or `^(intrare|limita) (în )?județ X\s*[-–]\s*(ieșire|limita) (din )?județ X` → `whole_county` with `county=X`. Map abbreviations: `HD→Hunedoara, AB→Alba, CJ→Cluj, …` — use the full 41+B county code table; put it in `textnorm.COUNTY_CODES`.
  3. `toat[ăa] lungimea`, `pe toat[ăa] lungimea`, or `integral` → `whole_course`.
  4. A list of ≥ 3 comma-separated toponyms with no dash → `locality_list`.
  5. Otherwise split into from/to (see below) → `interval`. If no split works → `unparsed`.
- **Splitting from/to:** remove leading `de la|între` and the connector `până la|pana la|la`. Candidate separators are `–`, `—`, ` - `, and a `-` that has a letter on both sides **only when** the right side starts with a recognised keyword (`conf`, `pod`, `baraj`, `izvo`, `vărsare`, `limit`, `ieșire`, `intrare`, `loc`, `sat`, `com`, `aval`, `amonte`, `lac`). This protects hyphenated toponyms like "Bumbești-Jiu" and "Valea Mare-Pravăț". If there are several candidates, choose the split where both sides classify to a non-UNKNOWN kind; if still tied, the first `–`, then the first ` - `.
- **Endpoint classification** (on the folded side; first match wins):

  | Pattern (folded) | Kind | target / notes |
  |---|---|---|
  | `^izvo(r\|are\|arele\|rul)` or `^de la izvo` | SOURCE | — |
  | `varsare( in)? (r\|raul\|lac(ul)?\|fluviul)? X` | CONFLUENCE | X; bare `varsare` → MOUTH |
  | `^(conf\|confl\|confluent[ae]\|gura)\.?( cu)?( r\.?\|raul\|paraul\|pr\.?\|valea\|vl\.?\|lac(ul)?)? X` | CONFLUENCE | X (if X starts with `lac` → LAKE_UPSTREAM, target the lake) |
  | `(coada\|intrare( in)?\|amonte( de)?) (lac(ul)?\|acumul\w*\|baraj(ul)?) X` | LAKE_UPSTREAM | X |
  | `(iesire( din)?\|aval( de)?) (lac(ul)?\|acumul\w*\|baraj(ul)?) X` | LAKE_DOWNSTREAM | X |
  | `^(limita )?baraj(ul)? X` / `^(lac(ul)?\|acumulare(a)?) X` | DAM / LAKE_DOWNSTREAM | X |
  | `pod(ul)?( rutier\| cfr\| de \w+)?( dn ?\d+\w*)?( (din\|de la\|la))?( loc\.?\|localitatea\|com\.?\|comuna\|sat)? X?` | BRIDGE | `road_ref` = `DN 67D` etc.; `locality_hint` = X; `cfr` → rail |
  | `^(drum\|dn\|dj)\s*[\w\.]+` | ROAD | `road_ref` |
  | `limita (jud\.?\|judetului) X` / `(intrare\|iesire)( din\| in)? judet(ul)? X` | COUNTY_LIMIT | county X (code table) |
  | `frontier[aă]\|granit[aă]\|ungaria\|serbia\|ucraina\|moldova\|bulgaria` (as a whole endpoint) | BORDER | country |
  | `cascad[aă] X` | WATERFALL | X |
  | `(aval\|amonte)( de)? X` | (re-classify X) | qualifier = downstream/upstream |
  | `^(loc\.?\|localitatea\|sat(ul)?\|com\.?\|comuna\|orasul\|municipiul)? X` where X is a toponym | LOCALITY | X |
  | anything else | UNKNOWN | raw |

- `includes_tributaries = bool(re.search(r"\b(si|cu) afluent", folded))`.
- **Test suite** (`tests/rivernet/test_limits_parser.py`) is table-driven from `tests/fixtures/rivernet/limits_cases.json`, with **≥ 150 real cases**:
  1. Generate candidates with a throwaway script: every distinct river `limite` from `public/data/waters.json` (663 distinct), stratified across all the token types in the vocabulary analysis (izvoare, conf., pod, baraj, lac, loc., limita jud., frontieră, aval/amonte, DN/CFR, cascada, lists, empty).
  2. **Hand-label the expected `LimitSpec`** for each. Never generate expectations from the parser's own output.
  3. Must include these real strings: `Nedelea – ieșire din județ Prahova`, `Baraj Baciu - Pod Stefan din loc.Slatina`, `izvoare- conf. Râul Trotuș`, `Pe raza județului Dâmbovița`, `De la izvoare pana la Paraul Iza`, `Izvoare - Amonte Lac Bondureasa`, `pod DN Moisei – pod Slătioara`, `Izvoare - confl. Lac Beliș`, `Canal artificial, din Râul Crișul Alb`, `Drum N.I. - vărsare`, `Izvoare – Pod CFR`, `între loc. Săpata - loc. Măceșu de Jos loc. Catane - loc. Bistreț` (expected `unparsed`; it's two intervals), `Izvoare – comuna Valea Mare–Pravăț`, `Aval sat Preoteasa - confluența Valea Iazului`, `Județ Arad`, `confl. pr. Brateș - la confl. cu pîrîul Bistrița`, `limită Baraj Zugreni – pod Mălișor`, `toata lungimea canalului`, `-`, `Limita jud. HD - localitatea Bumbești Jiu`, `Izvoare-DN 67 D Tg. Jiu-Baia de Aramă`, `Vorona – Teodoru – Joldești`, `Surcea, Sântionlunca, Ozun, Comandău`, `Intrare județ Buzău – ieșire județ Buzău.`, `Izvoare - vârsare în råul Arieş`, `Cheile Râmet - conf. Cu Råul Mureş`.
- Also add `python -m rivernet parse`. It writes `data/sectors/limits_parsed.jsonl` for all river waters (slug, raw, spec as a dict) and a summary `data/sectors/limits_parsed_summary.json` with counts per scope and per kind. Commit both.
- **Accept:** ≥ 95% of the labelled cases pass. The remaining failures are listed in the PR and marked `xfail` with a reason. `unparsed` + `UNKNOWN` endpoints are < 10% of all river waters (report the number).

#### T3.2 Course matcher · Size M · Dep T2.4, T3.1
- `rivernet/matcher.py` exposes `match(water, courses, county_polygons, overrides) -> MatchResult{course_id|None, score, method, candidates:[(id,score,reason)]}`.
  1. If `course_overrides.json` has the slug, use that course with `method="override"`.
  2. Candidates are courses whose `name_key`, any alias key, or `wikidata` label key equals one of `river_keys(water.name)`. If there are none, use fuzzy matching: `difflib.SequenceMatcher` ratio ≥ 0.88 on `name_key`.
  3. Hard filter: the course must intersect the water's `judet` polygon buffered 2 km. Use the course's `counties` intervals; if the polygon is missing, use `public/data/counties.geojson`.
  4. Score = `0.6·name_score + 0.2·(1 if the parsed endpoints mention a tributary or locality that exists on this course else 0) + 0.2·length_fit`, where `length_fit = 1` if course length ≥ 0.8 × contract km, else (course length / contract km).
  5. If the top score − second score < 0.1 → `method="ambiguous"`, `course_id=None`.
- **Create the registries:** `data/sectors/course_overrides.json` = `{"schema":1,"overrides":[{"slug","course_id","reason","reviewer","date"}]}`, and `endpoint_overrides.json` = `{"schema":1,"overrides":[{"slug","end":"from|to","anchor":{"type":"node|way|area|measure","id"?,"m"?},"reason","reviewer","date"}]}`. Both start empty, and both get a JSON-schema validation test.
- **Tests:** synthetic courses covering name collisions (Siret vs Sirețel, Someș vs Someșul Mic, Bistrița ×3 in different counties, Jiu vs Jiul de Vest), the county filter, an override, and the ambiguous case.
- Extend `rivernet-build.yml` to run `match`, and write `data/sectors/matches.jsonl`.

#### T3.3 Endpoint resolvers · Size L · Dep T3.2
- `rivernet/resolvers.py` exposes `resolve_endpoint(spec, course, ctx) -> list[Candidate{m, confidence, method, anchor, dist_m}]`, sorted by confidence. `ctx` holds the graph, all courses by id, spatial indexes (STRtree) of places, dams, bridges, areas, and county areas, plus the water's `judet`.
- Resolver rules (confidence values are fixed constants in the module; tests assert them):

  | Kind | Rule | Confidence |
  |---|---|---|
  | SOURCE | `m = 0` | 0.9; 0.75 if the course has `braids_dropped_m > 10%` of length |
  | MOUTH | `m = length` | 0.95 |
  | CONFLUENCE X | (a) if `course.receives_into` has a name key matching X → `m = length`, method `outlet_into_named`; (b) a junction whose tributary course name matches X → that `m`, method `tributary_junction`; (c) a course named X whose outlet node lies within 50 m of this course → project → `m`, method `near_outlet` | a 0.95, b 0.95, c 0.8 |
  | LAKE_UPSTREAM / LAKE_DOWNSTREAM X | area named X (fuzzy ≥ 0.85) intersecting the course → the intersection's upstream-most `m` (UPSTREAM) or downstream-most `m` (DOWNSTREAM) | 0.9; 0.7 if the area is unnamed but is the only reservoir crossed within 10 km of a place matching X |
  | DAM X | dam/weir way or node named X, or within 1 km of a place X, intersecting or within 100 m of the course → `m` | 0.9 named, 0.7 by place |
  | BRIDGE (ref / locality) | bridge ways crossing the course: filter by `ref` (DN/DJ number) or `railway` when given; if `locality_hint`, choose the crossing nearest that place (≤ 3 km) | 0.85 with ref+place, 0.75 with one of them, 0.5 if it's the only crossing within the sector's search window |
  | ROAD ref | as BRIDGE, without the `bridge` requirement (highway way crossing the course with that ref) | 0.7 |
  | LOCALITY X | place node named X (fuzzy ≥ 0.9; same county preferred); if an `admin_level=8` area named X intersects the course, use its entry `m` for a `from` endpoint and its exit `m` for a `to` endpoint (this is decided by the assembler, which passes `role`); else project the place node and require dist ≤ 3 km | 0.8 UAT intersection; 0.7 projection ≤ 1 km; 0.55 ≤ 3 km |
  | COUNTY_LIMIT X | intersection of the course with the `admin_level=4` boundary of county X (or of the water's county) → `m`; if several crossings, the one consistent with the other endpoint | 0.9 single crossing; 0.65 multiple |
  | BORDER | intersection with the `admin_level=2` boundary | 0.85 |
  | WATERFALL X | `waterway=waterfall` named X within 200 m | 0.85 |
  | UNKNOWN | no candidates | — |

- Qualifier `upstream` / `downstream` shifts nothing geometrically; record it in `method`.
- **Tests** (`tests/rivernet/test_resolvers.py`): one synthetic fixture per row, plus negative cases (a place 5 km away → no candidate; a name collision in another county → filtered; two bridges → the one nearest the hint wins).

#### T3.4 Sector assembly, status, overrides · Size M · Dep T3.3
- `rivernet/sectors.py` exposes `resolve_sector(water, limit_spec, match, ctx, overrides) -> SectorRecord` (§3.5).
  - **interval:** resolve `from` with role="from" and `to` with role="to". Take the best candidate of each. If `from.m > to.m`, swap (texts aren't always upstream-first) and add the reason `swapped_order`. If both candidates are the same point (length < 200 m), try the second-best for the lower-confidence end.
  - **whole_county:** the sector is the course's county interval for that county. If there are several intervals, take the longest and add the reason `county_interval_multiple`.
  - **whole_course:** `[0, length]`.
  - **locality_list:** resolve each as LOCALITY, then take min and max `m`. Confidence = min of the two extreme endpoints.
  - **empty / unparsed:** status `unresolved`, with reason `limite_unusable`.
  - **Endpoint overrides** replace the resolved endpoint (`method="override"`, confidence 1.0).
  - Compute `length_m`, `km_ratio` (contract km parsed from `dimensiune`, e.g. `"28 km"`; a number with a `ha` unit means it's not a river sector → `reasons += ["contract_unit_ha"]`, skip the km check), `status`, and `confidence` per §3.5.
  - Run `validate(record, course)` with the §3.5 invariants. Any failure → status `review`, with the failed invariant in `reasons`.
- **Overlap check** within one course: overlapping sectors of different slugs are flagged `overlap:<slug>` on both. This doesn't change status, unless the overlap is > 50% of the shorter sector *and* neither is `whole_county` → `review`.
- CLI `python -m rivernet resolve` writes `data/sectors/sectors.jsonl`. Extend the workflow.
- **Tests:** an end-to-end synthetic case for each scope; the swap; overrides; the km band edges (0.6, 0.8, 1.25, 1.6); `ha` units; an overlap; and determinism.

#### T3.5 Report, shadow comparison, review page · Size M · Dep T3.4
- `python -m rivernet report` writes `data/sectors/progress.json` and prints a markdown table:
  - counts by status and confidence;
  - `km_ratio` histogram buckets (<0.5, 0.5–0.8, 0.8–1.25, 1.25–2, >2);
  - top 15 `reasons`;
  - per-county resolved/total;
  - the chord check (max segment of each resolved sector);
  - **shadow comparison** against the current `public/data/waters.json`: for each slug, old drawn length (legacy: own geometry, or the owner slice for `sectorStart/End`), new length, and the Hausdorff distance between old and new (in EPSG:3844, after densifying to 50 m).
- `python -m rivernet review-page --county <name>|--all` writes `data/sectors/review/<county>.html`, which is gitignored. It is a self-contained Leaflet page (Leaflet from cdnjs, pinned version) showing for each water: the old geometry (grey), the new sector (red, or orange for `review`), endpoint markers with popups (kind, anchor, confidence, method), the `limite` text, contract km, drawn km, and the reasons. A list on the left is filterable by status. This is the owner's review tool.
- **Tests:** report numbers on a small fixture `sectors.jsonl`; the review page renders valid HTML that contains every slug.
- 👤 **O4:** run `rivernet-build` and open the review pages for two or three counties you know well. File overrides (or ask an executor to) for wrong anchors. Go/no-go for P4: proceed if, in your spot check, ≥ 80% of `resolved` sectors look right.

---

### P4 — Cutover

#### T4.1 Frontend support for pre-cut sectors (no data change) · Size L · Dep T0.5 (parallel)
- `src/types/data.ts` `Water`: add `geometryKind?: 'sector'`, `sectorStatus?: 'resolved' | 'review'`, `sectorConfidence?: 'high' | 'medium' | 'low'`, with doc comments referencing this plan.
- New `src/utils/precut-sector.ts`:
  - `isPrecutSector(w): boolean` (`geometryKind === 'sector'` and the geometry is a line);
  - `precutFocus(w)`: returns the same discriminated union that `resolveMapSelectionFocus` in `src/utils/contract-sector.ts` returns. That is `verified-sector-focus` covering the whole own geometry when `sectorStatus === 'resolved'`, and the existing unverified variant (own geometry outline plus the "Geometria exactă a sectorului nu este verificată" label) when `review`. **Read `contract-sector.ts` and reuse its types; do not invent a new focus kind.**
- `contract-sector.ts`: at the top of `resolveMapSelectionFocus` (and of whatever computes the interval for highlighting), short-circuit to `precutFocus` when `isPrecutSector(selected)`.
- `src/components/map/WaterFeatureLayer.tsx`:
  - when the clicked feature's water `isPrecutSector`, select that water directly. Do not call `contractAtFraction` or `contractInterval`, and do not look up the group owner;
  - render pre-cut sectors sorted by geometry length **descending**, so short sectors sit on top and win clicks where they overlap.
- `src/components/map/PhysicalPreviewLayer.tsx`: skip any water that `isPrecutSector` when resolving preview clicks. Pre-cut sectors are rendered by the main layer.
- `src/utils/county-clip.ts`: no change needed (the clips are regenerated in T4.2), but add a test that a pre-cut water with a clip renders the clip.
- **Tests (vitest):** `precut-sector.test.ts`; new cases in `contract-sector.test.ts` (resolved → verified focus; review → unverified; legacy unchanged); a component test for click selection, if a WaterFeatureLayer test harness exists (if not, test the extracted pure function that decides the selection — extract it into `src/utils/` if needed).
- **Playwright:** add `tests/e2e/specs/precut-sector.spec.ts`, using a **fixture data mode** if the e2e suite supports one (check `docs/e2e-test-plan.md` and `docs/mobile-test-fixtures.md`). If it doesn't, mark the spec `@data` and skip it until T4.4. Existing specs must stay green, especially `tarnava-mare-mijlocie-sector.spec.ts`.
- **Accept:** `npm test -- --coverage`, lint, build, and e2e smoke are green. No data files change.

#### T4.2 `rivernet publish` + legacy tail adjustments · Size L · Dep T3.5, T4.1
- `rivernet/publish.py` exposes `publish(waters, sectors, courses, *, mode: "shadow"|"write") -> (new_waters, report)`.
  1. Select the switching set. A water is eligible if it is a river, its status is `resolved`, or `review` with all reasons covered by overrides, and its validations pass. Then apply D8 per `riverGroup`: if any member of the group isn't eligible, no member of that group switches.
  2. For a switching water:
     - `geometry` = `substring(course, from.m, to.m)`, simplified with `shapely.simplify(tolerance=0.00005, preserve_topology=True)` (≈ 5 m), rounded to 5 dp. If the sector spans a `synthetic` span, emit a MultiLineString split at it.
     - Recompute `bbox` and `lengthKm` (1 dp).
     - Write the §3.6 fields, and remove the fields §3.6 says to remove.
  3. `mode="shadow"` writes `data/sectors/waters.shadow.json` and `data/sectors/publish_report.json` (switched, kept-legacy with reason, D8 blocked groups). `mode="write"` overwrites `public/data/waters.json`.
- **Field guard:** `publish` builds the output by copying each input water and applying only the allowed keys. A pytest asserts that, for every water, `set(changed_keys) ⊆ ALLOWED` and that every non-geometry field is byte-equal to the input (`test_publish_only_touches_geometry_fields`).
- **Legacy tail changes:**
  - `scripts/simplify_waters_geometry.py`: skip waters with `geometryKind == "sector"` (they're already simplified). Add a test.
  - `scripts/build_county_clip_geoms.py`: for sector waters, the clip is `intersection(sector_geometry, county_polygon.buffer(0.002))`, simplified at 0.0001° (not 0.002°). Do not use the course slicing code. Add a test.
  - `scripts/build_geometry_ledger.py`: for sector waters, set `endpointEvidence.status = "resolved-limite"` (new enum value) and `classification = "repaired"`, with a variant whose geometryHash is computed the existing way. Update `src/types/geometry-ledger.ts` and the validator in `src/utils/geometry-ledger.ts` plus their tests to accept the new value, keeping `schemaVersion` 1.
  - `scripts/build_class2_aggregate.py` (preview): for D8-switched groups, emit the group's **rivernet course** (simplified at 0.0005°) as the physical full-course preview instead of the legacy owner geometry. Keep the disclosure text.
  - `scripts/rebuild_data.py`: add `rivernet publish --mode write` to `FULL_STEPS` right after `merge_anpa_waters` and before `build_locality_assignment`. Add the new inputs (`data/sectors/sectors.jsonl`, the overrides, `data/rivernet/input_manifest.json`) to the pinned inputs.
- **Tests** on a mini fixture set (copy 6 real waters from `waters.json` into `tests/fixtures/rivernet/waters_mini.json`, plus synthetic courses and sectors): a switched single, a blocked group, a switched group, a legacy-kept water, and determinism.

#### T4.3 Sector evidence file + card UI · Size M · Dep T4.2
- `rivernet/evidence.py` writes `public/data/sector-evidence.json` = `{"schema":1,"network_version":…,"osm_timestamp":…,"sectors":{slug:{from:{kind,label,anchor:{type,id},confidence},to:{…},lengthKm,contractKm,status,confidence}}}`, only for switched waters. `label` is a short Romanian description, e.g. `"confluența cu Mureș"`, `"podul DN 1 la Băcăinți"`, `"izvoare"`. Generate it from the kind and target with a template table, and test the table.
- **Budget:** add the file to the allowlist (done in T0.3) and set a **blocking** gzip cap of 300 KB in `check-data-budget.mjs`.
- **Frontend:**
  - `src/lib/sector-evidence.ts` lazy-loads and caches the file (use `src/lib/bounded-cache.ts`, following the existing lazy-load pattern in `map-store.ts`), with tests.
  - `src/components/waters/WaterDetailCard.tsx`: for a pre-cut water, show a "Limitele sectorului" block: "De la: {from.label} · Până la: {to.label} · {lengthKm} km desenați / {contractKm} km în contract". Add a small "Cum am stabilit?" disclosure showing the confidence, "OpenStreetMap ({osm date})", and a link to the existing report form prefilled with "sector greșit". All strings go in `src/i18n/messages.ts` in RO and EN.
  - `public/data/osm-lineage.json`: add a transformation entry `rivernet-v2` (inputs: the release tag and sha256; transformations: graph build, course stitching, limite resolution, substring, simplify 5 m). Extend its test if one exists.
- **Tests:** vitest for the loader and the card block (resolved, review, missing evidence → block hidden).

#### T4.4 The cutover PR · Size M · Dep T4.3, O4
- Run the full pipeline (in the `rivernet-build` workflow or locally with the fetched asset): `parse → match → resolve → report → publish --mode write → legacy tail` (`build_locality_assignment, build_county_clip_geoms, split_county_clips, simplify_waters_geometry, build_geometry_ledger, build_class2_aggregate`). Then `rebuild_data.py --manifest`, deliberately regenerating the pinned hashes.
- The PR must include:
  - the `rivernet report` table;
  - `publish_report.json` counts;
  - budget output (M7/M8/M9 and lazy files);
  - a before/after M9;
  - five screenshots from `npm run dev` of resolved sectors you can identify (e.g. Târnava Mare, Ampoi, Geoagiu, Olt in Vâlcea, Arieș).
- Unskip `precut-sector.spec.ts` with a real resolved slug, and update `tests/test_parity_vs_frontend.py` only if it breaks — the legacy TS/Python math is still used by legacy waters, so it should not.
- **Accept:** all CI green, M9 ≤ 5.0 MB (if not, report it and stop; do not loosen budgets), and the legal-surface hash assertion in the ledger manifest still passes. 👤 **O5:** review the PR on the Vercel preview deployment and merge.

---

### P5 — Review loop (ongoing, county by county)
- **T5.x** (one PR per 1–3 counties, Size S–M): open the review page for the county, fix wrong matches and endpoints via `course_overrides.json` / `endpoint_overrides.json` (with a reason and the source of the decision, e.g. "ANPA list 23.02.2026 row 44, confluence visible on OSM"), re-run the workflow, and attach the report delta. The owner reviews and merges.
- **Improve the resolvers** where a pattern recurs (≥ 5 waters with the same reason): change code + tests rather than adding overrides.
- Track progress against §1 in `data/sectors/progress.json`; the owner decides when coverage is enough.

### P6 — Enrichment (optional; after P4)
- **T6.1 WISE IDs.** A workflow `wise-fetch.yml` pages the EEA REST endpoint `WISE_WFD/WFD2022_SurfaceWaterBodyCentreline_WM/MapServer/0/query?where=countryCode='RO'` (`f=geojson`, `resultOffset` paging) and publishes the result as a release asset, with a manifest and sha256. `rivernet conflate-wise` attaches `euSurfaceWaterBodyCode` to course intervals where the buffered (75 m) overlap is ≥ 70% of the WISE segment length. Output `data/rivernet/wise_links.jsonl`. Add the CC BY 4.0 credit to `MapAttribution.tsx` and `osm-lineage.json` (or a new `data-lineage.json`) in the same PR. Tests use a small fixture.
- **T6.2 Strahler for LOD.** Compute Strahler order on the OSM graph itself (deterministic; no EU-Hydro needed), store it per course, and use it in `build_uncontracted_*` for zoom tiers instead of length thresholds. Keep `lod.ts` thresholds in sync and test both sides.
- **T6.3 Uncontracted overlay from the network.** Rebuild `uncontracted_rivers.json` and `uncontracted_majors.json` from rivernet courses minus the published sector intervals (the uncovered remainder of each named course), simplified 0.0005°. Keep the existing schema and the `sweep_uncontracted_overlay.py --gate` green. This also removes most AMBIGUOUS/NAME_COLLISION sweep hits.
- **T6.4 Lakes.** Replace the 25 bbox-rectangle lake geometries and the 62 four-vertex polygons: find an `area` from the extract with a matching name key that contains or is within 500 m of the water's `coordinates`; otherwise leave it and set `fallback`. Same field guard as T4.2.
- **T6.5 Romanian official layer** (only if 👤 confirms data.gov.ro "Confluente si izvoare" is open and usable): add it as an optional anchor source for CONFLUENCE/SOURCE with confidence +0.05.

### P7 — Rendering (decide by measurement)
- **T7.1 Canvas renderer experiment.** Behind `?renderer=canvas`, pass `preferCanvas` / `L.canvas({ padding: 0.5 })` to the river layers. Run `npm run perf:map` and the Lighthouse job in both modes and record M6/M12/M13 in `docs/perf/2026-xx-canvas.md`. Make canvas the default only if it's better on mobile with no hit-testing regressions (click a short sector on top of a long one in e2e).
- **T7.2 PMTiles benchmark** (no product change): build `rivers.pmtiles` with felt/tippecanoe `-pn` (layers: courses with Strahler-filtered zooms; sectors with stable numeric ids) and test it in a throwaway page with `protomaps-leaflet` and with MapLibre. Measure bytes and time-to-first-render on a throttled mobile profile. Write `docs/perf/pmtiles-benchmark.md`. 👤 decides on adopting it (which needs Cloudflare R2 or a verified Vercel 206 range test).

### P8 — Cleanup and drift
- **T8.1 Retire legacy math for switched waters.** Once ≥ 90% of rivers are pre-cut (or the owner decides), move the legacy mutation scripts to `scripts/legacy/` with a README naming the tasks that produced them. Delete the duplicated `order_parts`/`fraction_at` copies outside `river-course.ts`/`_mapping_common.py`, and plan the removal of `sectorStart`/`sectorEnd`/`course_frac` from the schema. That removal needs its own ADR, because it changes the `public/data` contract.
- **T8.2 Monthly drift workflow.** Extend `osm-extract.yml` + `rivernet-build.yml` into a monthly scheduled chain. Re-resolve every sector with the new extract, compare to the committed `sectors.jsonl`, and open a PR with a drift table: slug, Δm_from, Δm_to, Δlength, anchor changes, status changes. Thresholds: |Δm| > 500 m or a status downgrade → label `needs-review`. Never auto-merge.
- **T8.3 Segment audit.** Extend `scripts/audit_river_segments.py`, or replace its gate, to use rivernet courses. Retire the two expiring exceptions in `river_segment_exceptions.json` when they're no longer needed.

---

## 5. Owner checklist (👤)

| When | Action |
|---|---|
| Now | **O1:** give executor sessions push access; allow Actions to create releases and PRs. |
| Anytime, cheap | Open https://data.gov.ro/dataset/hidrografie in a normal browser. Note the licence, format, and scale of "Cursuri de apa rauri" and "Confluente si izvoare", and paste them into a GitHub issue labelled `data-source`. |
| After T1.2 | **O2:** run "osm-extract", then merge the manifest PR. |
| After T2.4 | **O3:** run "rivernet-build", then merge. |
| After T3.5 | **O4:** spot-check review pages for 2–3 counties; go/no-go for P4. |
| T4.4 | **O5:** review the cutover on the Vercel preview, then merge. |
| P5 | Review override PRs; decide when coverage is enough. |
| P7 | Decide on PMTiles/MapLibre from the benchmark. |

---

## 6. Risks and what to do

| Risk | Signal | Response |
|---|---|---|
| OSM lacks many small trout streams | Many `matcher` results with no candidates in mountain counties (report: per-county) | Add a P6 task to use WISE geometry as a flagged fallback course (`source: wise`, never `high` confidence). |
| The full course file is too big for git | `courses.jsonl.gz` > 25 MB | Use the release-asset branch in T2.4. |
| The parser misreads hyphenated toponyms | Many `LOCALITY` endpoints with no place match | Add the failing strings to `limits_cases.json` first, then fix the rules. |
| D8 blocks big rivers (Mureș, Olt, Siret) forever | `publish_report` shows large blocked groups | Prioritise those groups in P5 overrides; do not weaken D8. |
| M9 doesn't drop enough | T4.4 budget output | Raise the simplify tolerance for sectors > 50 km to 10 m; never loosen the budget. |
| Executor sandbox has no PyPI/GitHub access | `pip` or `gh` fail | Push the branch and rely on CI; say so in the PR. |
| The pyosmium or osmium-tool API differs from this plan | Errors at T1.1/T1.2 | Follow the official docs for the pinned version; keep the output schema §3.3 unchanged. |

---

## 7. Prompt template for an executor session

> You are implementing task **{ID} — {title}** from `docs/plans/river-geometry-v2.md` in `stefanneaga99/undepescuim`. Read `AGENTS.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md` and the whole plan first, then the task section again. Follow §0 rules strictly. Work on branch `geo/{id}-{slug}`. Implement exactly what the task specifies; if something in the plan is impossible or contradicts the code, stop and explain in the PR instead of redesigning. Ship tests with the code. Run `python -m pytest`, `npm test -- --coverage`, `npm run lint`, and (if you touched the frontend) `npm run build`, and paste the results into the PR description. Open the PR when done.
