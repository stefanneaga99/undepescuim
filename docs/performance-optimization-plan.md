# Performance Optimization Plan — UndePescuim.ro

> SPIKE (t_dd287ca9) — analysis + plan, no implementation.
> Follows the approved performance test plan (`docs/performance-test-plan.md`, t_8810ff88, budgets M1–M14).
> All numbers below are **measured on the actual repo files** on 2026-08-16 (not estimates), using
> `scripts/_perf_spike_measure.py` and `scripts/_perf_spike_measure2.py` (committed with this plan as the re-measure harness).

---

## 1. Goal

Meet budgets M6–M9 (the ones that FAIL today) with the smallest, lowest-risk set of changes:

| # | Budget | Target (PASS) | Measured today | Status |
|---|---|---|---|---|
| M6 | First-map-paint (Fast 3G) | < 5.0 s | ≈ 30 s | ❌ FAIL |
| M7 | Total data JSON gzip (first load) | < 2.5 MB | ≈ 7.0 MB | ❌ FAIL |
| M8 | `waters.json` gzip (compact) | < 1.5 MB | 4.99 MB | ❌ FAIL |
| M9 | JSON parsed on main thread | < 6 MB | ≈ 23.7 MB | ❌ FAIL |

M1–M5, M10–M14 are not addressed directly here except M12/M13/M14, which improve as a side effect
(render long-tasks, heap, LOD effectiveness).

---

## 2. Measured reality (baseline)

### 2.1 `public/data/` files (all git-tracked)

| File | Entries | Raw | Compact | gzip -9 | Fetched by app? |
|---|---|---|---|---|---|
| `waters.json` | 1013 (714 w/ geometry) | 38.0 MB | **17.7 MB** | **4.99 MB** | yes |
| `uncontracted_rivers.json` | 4166 | 2.34 MB | 2.34 MB | 0.48 MB | yes |
| `uncontracted_lakes.json` | 5712 | 3.34 MB | 3.34 MB | 0.75 MB | yes |
| `counties.geojson` | 42 | 0.23 MB | 0.21 MB | 0.08 MB | yes |
| `associations.json` | ~90 | 0.04 MB | 0.04 MB | 0.009 MB | yes |
| `waters_geocoded.geojson` | — | 10.1 MB | 9.35 MB | 3.04 MB | **no (dead)** |
| `waters.geojson` | — | 0.16 MB | 0.10 MB | 0.02 MB | **no (dead)** |
| `reciprocity.json` | — | 0.0003 MB | — | — | **no (dead)** |

**First-load totals today:** ~44 MB raw / ~7.0 MB gzip transferred / ~23.7 MB compact JSON parsed on the main thread.

Note: the test plan (written earlier the same day) quoted 36.26 MB / 4.75 MB; geometry attachment continued
through the day, so current is 38.0 MB / 4.99 MB. This plan uses the **current** numbers.

### 2.2 Why `waters.json` is huge — field breakdown (compact bytes)

| Field | Compact bytes | Share |
|---|---|---|
| `geometry` (714 features, **566,773 vertices**, full OSM precision, **7 dp**, un-simplified) | 13.50 MB | 77.3 % |
| `geometryByCounty` (327 clips, 167,183 vertices — already 0.002°-simplified + 5 dp) | 3.48 MB | 19.9 % |
| everything else (slug/name/judet/asociatie/referinta/limite/bbox/coordinates/locality) | ~0.7 MB | 2.8 % |

The **data** fields are ~0.7 MB. The file is ~97 % geometry. The entire win is in geometry.

Coordinate precision histogram: 7 dp dominates (1,013,732 of 1,133,543 numbers), i.e. OSM's ~1 cm
precision is shipped verbatim. A fishing map viewed at zoom 7–14 needs ~5 dp (~1 m) at most.

### 2.3 Douglas-Peucker simplification (measured on the real geometry)

| Tolerance | Vertices after | Vertex cut |
|---|---|---|
| 0.0005° (~55 m) | 103,710 | 81.7 % |
| 0.001° (~110 m) | 72,781 | 87.2 % |
| 0.002° (~220 m) | 52,773 | 90.7 % |

The uncontracted overlay already renders at 0.002° with no visible loss, and the county clips are already
built at 0.002° — so simplification is a proven, safe pattern in this codebase.

### 2.4 The uncontracted files are already optimal per-feature

- `uncontracted_rivers.json`: 4166 features, **46,343 vertices** (~11/feature), already 5 dp, 589 `geometryByCounty` clips.
  - LOD subset (length ≥ 30 km, the zoom-7 default view) = **395 features → 0.76 MB compact / 0.14 MB gzip**.
- `uncontracted_lakes.json`: 5712 features, **80,681 vertices** (~14/feature), already 5 dp, no clips.
  - LOD subset (area ≥ 100 ha) = **221 features → 0.17 MB compact / 0.05 MB gzip**.

These files cannot be shrunk much by simplification — they are already simplified. The only remaining lever
for them is **not shipping the whole thing on first load** (see §4.5).

---

## 3. Summary of the fixes (impact × effort)

| # | Change | Impact | Effort | Priority |
|---|---|---|---|---|
| 1 | Simplify + round `waters.json` geometry (DP 0.001° + 5 dp) | **-77 %** of `waters.json` gzip (4.99 → 1.16 MB); clears M8; fixes TC-07 render jank | Low | **P0** |
| 2 | Split `geometryByCounty` into a lazy file | first-load -0.65 MB gzip / -3.48 MB compact / -167 k vertices | Medium | **P0** |
| 3 | Remove dead weight (`waters_geocoded`, `waters.geojson`, `reciprocity`) | repo/deploy -9.8 MB; enables a CI gate | Trivial | **P0** |
| 4 | Add viewport culling + zoom LOD + drop low-zoom hit-layer to `WaterFeatureLayer` | fixes TC-07 long tasks; fewer live SVG nodes (M14) | Medium | **P1** |
| 5 | Split uncontracted into "majors" (first-paint) + full (lazy on zoom) | first-load -1.04 MB gzip / -4.75 MB compact; M6/M7/M9 margin | Medium | **P1** |
| 6 | Write compact JSON (no pretty-print) | -0.7 MB on-wire (4.99 → 4.3 MB gzip even with zero geometry change) | Trivial | **P1** |
| 7 | Web-worker `JSON.parse` | main-thread parse → 0 | Medium | **P2** (optional) |
| — | Shorter JSON keys (`t`/`c` for GeoJSON) | **~8 KB** — not worth it | — | **Skip** |

---

## 4. The changes in detail

### 4.1 [P0] Simplify + round `waters.json` geometry — expected **4.99 → 1.16 MB gzip**

**What.** In the pipeline, after `attach_geometry.py` copies OSM geometry into `waters.json`, run a
simplify + round pass. Round every coordinate to 5 dp and Douglas-Peucker-simplify at **0.001°** with
`preserve_topology=True`.

**Why this tolerance.** 0.001° ≈ 110 m. A pixel is ≈ 1.5 km at zoom 7, ≈ 38 m at zoom 12, ≈ 9 m at zoom 14.
110 m is invisible through zoom ~14 and only starts to show sub-pixel wobble at zoom 15+ (a fishing map is
read at zoom 7–13). `preserve_topology` guarantees rivers never self-intersect and lakes never collapse.
0.0005° (~55 m) is the conservative fallback: **1.34 MB gzip, still under M8** — use it if review worries
about click accuracy (see Risks §7).

**Where.** Add `scripts/simplify_waters_geometry.py` (or fold into `attach_geometry.py`). Both `geometry`
and the existing `geometryByCounty` clips get the same round (clips are already simplified, but re-rounding
to 5 dp after simplify is idempotent).

```python
# scripts/simplify_waters_geometry.py (core)
from shapely.geometry import shape
import json

TOLERANCE_DEG = 0.001   # ~110 m; 0.0005 for the conservative variant
ROUND_DP = 5

def simplify_geometry(g: dict) -> dict:
    s = shape(g).simplify(TOLERANCE_DEG, preserve_topology=True)
    return round_coords(json.loads(json.dumps(s.__geo_interface__)), ROUND_DP)

# apply to w["geometry"] and to every non-null clip in w["geometryByCounty"]
```

Re-run order after any data refresh (document in `scripts/`):
`extract-map-data.mjs` → `attach_geometry.py` → `build_county_clip_geoms.py` → **`simplify_waters_geometry.py`**.

**Measured outcome (verified on current file):**

| Regime | Compact | gzip -9 |
|---|---|---|
| baseline | 17.71 MB | 4.99 MB |
| round 5 dp only | 15.45 MB | 3.58 MB |
| round 5 dp + DP 0.001° | 5.68 MB | **1.16 MB** |
| round 5 dp + DP 0.0005° | 6.29 MB | **1.34 MB** |

**Budgets unlocked:** M8 (PASS, 1.16 < 1.5); M12/TC-07 (render work drops 7.8× — 566 k → 73 k vertices);
M13 (heap); M14 (fewer path points per layer).

**Verification:** re-run `scripts/_perf_spike_measure.py` and confirm the R2 row; `gzip -9` the compact file and assert < 1.5 MB.

---

### 4.2 [P0] Split `geometryByCounty` into a lazy file — expected **-0.65 MB gzip first-load**

**What.** Move the `geometryByCounty` map out of `waters.json` into `public/data/waters_county_clips.json`
(keyed by `slug` → clip map), and fetch it only when the user first activates the county filter.

**Why.** `geometryByCounty` is 3.48 MB compact / 0.65 MB gzip (19.9 % of the file), but is used **only**
when `countyFilter.length > 0` (`use-filtered-waters.ts` → `countyRenderGeometry`). Shipping it blocks
first paint for a feature the user may never touch.

**Measured standalone size:** `waters_county_clips.json` = 3.49 MB compact / **0.65 MB gzip** (327 clips).
(Plus the 589 uncontracted-river clips — see 4.2b.)

**Where — build.** In `build_county_clip_geoms.py`, after computing clips, write them to
`waters_county_clips.json` and strip `geometryByCounty` from `waters.json` (the FE merge is lossless).

**Where — FE.** In `map-store.ts`:
- `loadData()` no longer expects `geometryByCounty` on the waters (it's absent from the shipped file).
- Add a `countyClipsLoaded` flag + `loadCountyClips()` action that fetches `waters_county_clips.json`,
  merges `w.geometryByCounty = clips[w.slug]` for each water, then sets the flag.
- `CountyFilter` (or the `toggleCounty` action) calls `loadCountyClips()` (idempotent) before applying the
  filter; while loading, the county chip can show a spinner (0.65 MB ≈ 3 s Fast 3G, ≈ 50 ms broadband).

**Why not compute clips client-side.** It needs a robust line↔polygon intersection (new dep, e.g. turf
`@turf/line-clip`, +~50–100 KB gzip) plus per-filter runtime on low-end phones, for no first-paint benefit
over the lazy file. **Decision: ship-on-demand beats client-side clip.** (Recorded as a rejected alternative.)

**4.2b** The 589 uncontracted-river clips (13,525 vertices) live in `uncontracted_rivers.json`; move them to
the same `waters_county_clips.json` (or a sibling) for symmetry — same lazy trigger.

**Budgets unlocked:** M6/M7 first-load (-0.65 MB gzip, -3.48 MB compact); keeps county-filter correctness (t_117f0b99) intact.

---

### 4.3 [P0] Remove dead weight — expected **-9.8 MB from repo/deploy**

`waters_geocoded.geojson` (10.1 MB), `waters.geojson` (0.16 MB), `reciprocity.json` (266 B) are **not referenced
by any code** (grep confirmed zero hits outside their own filenames). They are git-tracked and deployed to
`public/`.

**Action.**
1. `git rm public/data/waters_geocoded.geojson public/data/waters.geojson public/data/reciprocity.json`.
2. Add to `.gitignore` (they are regenerated intermediates — `waters_geocoded.geojson` is rebuilt by
   `merge_geocoded.py`+`regenerate_from_cache.py`, and only ever consumed by `attach_geometry.py`, which
   should read it from `data/` instead of `public/`):
   ```
   # geocoding intermediates — must NOT ship to the client
   /public/data/waters_geocoded.geojson
   /public/data/waters.geojson
   ```
3. Point `attach_geometry.py` at a non-public path (e.g. `data/processed/waters_geocoded.geojson`) so the
   intermediate never lands under `public/` again.

**Budgets unlocked:** none at runtime (already not fetched) — this is deploy hygiene and the precondition
for the CI data-budget gate (§6) that *prevents regression*.

---

### 4.4 [P1] Culling + zoom LOD + low-zoom hit-layer drop in `WaterFeatureLayer`

**What.** Mirror `UncontractedWaterLayer.tsx` (the already-proven pattern) onto the contracted layer:

1. **Viewport culling** — capture `{ zoom, bounds }` on `moveend` (`useMapEvents`), filter
   `featureCollection` to features whose `bbox` intersects `bounds.pad(0.25)`, re-key the layer on zoom+bounds.
2. **Zoom LOD** — contracted waters lack `lengthKm`/`areaHa` (those are uncontracted-only fields). Add them
   in the pipeline (cheap: `lengthKm`/`areaHa` are already computed for uncontracted; compute the same for
   contracted `geometry` during `simplify_waters_geometry.py`). Then apply thresholds — but note contracted
   waters are only 1013 features and **after simplification each averages ~100 vertices**, so LOD is optional;
   culling is the meaningful win.
3. **Drop the invisible hit-layer at low zoom** — `GeoJSONHits` doubles every line's geometry (weight 16).
   At zoom < 10 rivers are too dense to tap individually anyway; render the hit-layer only when `view.zoom >= 10`.

**Interaction risks to handle (this is why it's P1, not P0):**

- **Focus slice + association slice** currently iterate the *rendered* `featureCollection` / `waters` prop
  (`focusFeatures` iterates `featureCollection.features`; `assocHighlightFeatures` iterates `waters`). If
  culling drops a feature, its focus/assoc slice vanishes. **Fix:** compute both slices from `allWaters`
  (unfiltered, unculled) — they already resolve via `contractGroup`/`contractInterval` against `allWaters`,
  so this is a small, localized change (see the `focusFeatures`/`assocHighlightFeatures` `useMemo`s).
- **County-clip geometry** (`useFilteredWaters` replaces `w.geometry` with the clip) has the *full-course*
  `bbox`, so bbox-culling keeps a river whose clip is actually off-screen — conservative, safe, acceptable.
- **Click resolution** (`fractionAtPoint`) reads `allWaters` full geometry, unaffected by culling.

**Budgets unlocked:** M12/TC-07 (no >100 ms long task from the contracted layer); M14 (bounded SVG node
count). With simplification alone the render already drops 7.8×; culling adds viewport-bounded growth on pan/zoom.

---

### 4.5 [P1] Split uncontracted into "majors" + full — expected **-1.04 MB gzip first-load**

**What.** Ship a tiny `uncontracted_majors.json` (rivers ≥ 30 km + lakes ≥ 100 ha — exactly the zoom-7 LOD
set) for first paint, and lazy-load the full `uncontracted_rivers.json` + `uncontracted_lakes.json` in the
background (fire-and-forget once `dataLoaded`), or on `zoom >= 8` where the LOD threshold already drops to
10 km / 10 ha.

**Measured:**

| Payload | Features | Compact | gzip |
|---|---|---|---|
| majors (rivers ≥ 30 km) | 395 | 0.76 MB | 0.14 MB |
| majors (lakes ≥ 100 ha) | 221 | 0.17 MB | 0.05 MB |
| **`uncontracted_majors.json`** | **616** | **0.93 MB** | **0.19 MB** |
| full rivers + lakes (lazy) | 9878 | 5.68 MB | 1.23 MB |

**Why majors.** At the default zoom 7 the uncontracted layer only draws the majors anyway (its own LOD
already hides the rest). Loading majors first gives a **visually complete** map immediately; the full
dataset streams in behind it so zooming never hits a "missing overlay" gap. Simpler alternative if effort
is a concern: defer *all* uncontracted to post-first-paint (the teal overlay pops in a beat later).

**Where — FE.** `map-store.ts`: split the uncontracted fetches out of the first `Promise.all`; `loadData()`
awaits only `waters.json` + `associations.json` + `counties.geojson` + `uncontracted_majors.json`, sets
`dataLoaded`, then background-loads the full uncontracted files and merges them (existing merge logic for
rivers+lakes stays).

**Where — build.** New `scripts/build_uncontracted_majors.py` (or extend `build_uncontracted_rivers.py` /
`build_uncontracted_lakes.py`) to emit the majors subset.

**Budgets unlocked:** M6 (first paint ~0.80 MB instead of ~1.84 MB), M7, M9 (see §5).

---

### 4.6 [P1] Write compact JSON (no pretty-print) — expected **-0.7 MB on-wire**

`waters.json` is serialized with `indent=1` (38.0 MB on disk). gzip of the compact form is **0.70 MB smaller**
than gzip of the pretty-printed form (4.99 vs 5.69 MB) — whitespace is not free even under gzip. All build
scripts that write `public/data/*.json` should serialize compact (`separators=(",", ":")` in Python, no
`space` arg in Node `JSON.stringify`). The `refresh-data.mjs` orchestrator already pretty-prints
(`JSON.stringify(value, null, 2)`) — switch it to compact. **No client change** (JSON.parse doesn't care).

---

### 4.7 [P2, optional] Web-worker `JSON.parse`

After 4.1–4.5 the first-load parse is only ~3.37 MB compact (~0.3–0.5 s on a low-end phone). Moving it to a
worker (or using `new Response(res).json()` / streaming parse) shaves that off the main thread but adds
worker plumbing + structured-clone cost. **Recommended only if** M9 is later re-defined to cover the *full*
dataset (which totals ~9 MB compact incl. lazy files). Leave out of the first implementation pass.

**Not needed:** code-splitting `/specii` and `/permis` — they are already server-rendered static routes
(Next route-splits them automatically), and the map island is already `dynamic(ssr:false)`. No action.

---

## 5. Projected post-fix budget outcomes

### First-load payload (the set `loadData()` awaits)

| File | Compact | gzip -9 |
|---|---|---|
| `waters.json` (simplified, no `geometryByCounty`) | 2.19 MB | 0.52 MB |
| `associations.json` | 0.04 MB | 0.009 MB |
| `counties.geojson` | 0.21 MB | 0.08 MB |
| `uncontracted_majors.json` | 0.93 MB | 0.19 MB |
| **Total first-load** | **3.37 MB** | **0.80 MB** |

### Lazy (post first paint)

| File | Trigger | gzip |
|---|---|---|
| full uncontracted (rivers+lakes) | background after `dataLoaded` / zoom ≥ 8 | 1.23 MB |
| `waters_county_clips.json` | first county filter | 0.65 MB |

### Budget mapping (the deliverable the spike asked for)

| Budget | Today | After | Verdict |
|---|---|---|---|
| M6 first-map-paint < 5 s | ~30 s | ~0.80 MB @ 200 KB/s ≈ 4 s + parse + tiles | **PASS** |
| M7 total gzip < 2.5 MB | ~7.0 MB | **0.80 MB** | **PASS** |
| M8 `waters.json` gzip < 1.5 MB | 4.99 MB | 0.52 MB (1.16 if GBC kept; 1.34 if 0.0005°) | **PASS** |
| M9 main-thread parse < 6 MB | ~23.7 MB | **3.37 MB** first-load | **PASS** |
| M12 no >100 ms long task | fail (TC-07) | simplification 7.8× + culling + no low-zoom hit-layer | **PASS** (expected) |
| M13 heap < 200 MB | untested | retained geometry −87 % | improved |
| M14 LOD ≤ 1000 paths @ zoom 7 | fail (contracted) | measured ~828 after shared culling/LOD | **PASS** |

**Per-change expected gains (task item 5):**

| Change | `waters.json` gzip | first-load gzip | first-load parse | M6/M7/M8/M9 unlocked |
|---|---|---|---|---|
| 4.1 simplify+round | -3.83 MB | -3.83 MB | -12.0 MB | M8 |
| 4.2 split GBC | -0.65 MB | -0.65 MB | -3.48 MB | M7 |
| 4.5 split uncontracted | — | -1.04 MB | -4.75 MB | M6, M9 |
| 4.6 compact JSON | -0.70 MB | -0.70 MB | — | M7 |
| 4.3 dead weight | — (not fetched) | — | — | CI gate only |
| 4.4 culling/LOD | — | — | — | M12, M14 |
| 4.7 worker (opt.) | — | — | -3.37 MB main-thread | M9 (strict) |

---

## 6. CI data-budget gate (regression guard)

Extend `.github/workflows/data-refresh.yml` (and add to the proposed `lighthouse.yml` PR gate from the test
plan) with `scripts/check-data-budget.mjs` (new):

```js
// scripts/check-data-budget.mjs — assert M7/M8/M9, exit 1 on FAIL
import { gzipSync } from 'node:zlib';
// 1. gzip sum of the FIRST-LOAD files  < 2.5 MB        (M7)
// 2. gzip of compact waters.json       < 1.5 MB        (M8)
// 3. compact sum of first-load files   < 6.0 MB        (M9)
// 4. waters_geocoded.geojson / waters.geojson absent from public/data/  (dead weight)
```

Add the same assertions to the data-refresh workflow's post-`data:refresh` step so a monthly refresh that
re-introduces un-simplified geometry **fails the job** before it can commit.

---

## 7. Risks, tradeoffs, decisions for review

1. **Click-fraction accuracy under simplification (decision needed).** `fractionAtPoint` walks the simplified
   course; at 0.001° the fraction error is ≤ ~110 m / river-length — negligible on the Mureș (~700 km,
   0.016 %) but up to ~2 % on a 5 km multi-contract river, which could flip a tight sector boundary on the
   shortest rivers. Mitigation options: (a) accept 0.001° (a 100 m shift on a fishing map is invisible in
   practice); (b) use 0.0005° (~55 m, still under M8 at 1.34 MB); (c) keep full-resolution geometry **only**
   for the small set of `riverGroup`-bearing multi-contract waters. **Recommend (a) with (c) as a
   low-effort hedge** — flag for review.
2. **County-filter latency after GBC split.** County filter now waits for a 0.65 MB fetch on first use.
   Acceptable (≈ 50 ms broadband, ≈ 3 s Fast 3G), with a spinner on the chip. Alternative rejected
   (client-side clip = new dep + low-end-phone runtime).
3. **Focus/association slice regression under culling.** Must re-source those slices from `allWaters`
   (not the culled collection) or selecting an association off-screen breaks its highlight. Explicitly
   scoped into the 4.4 task.
4. **LOD threshold duplication.** The "majors" subset (30 km / 100 ha) duplicates the FE LOD constants.
   Keep both in one place (export the thresholds from a shared module) to avoid drift.
5. **Effort vs. certainty.** 4.1 + 4.2 + 4.3 + 4.6 alone clear M7/M8 and most of M6/M9 with low risk; 4.4
   and 4.5 add the render- and first-paint margin at medium risk. Recommend sequencing P0 first, measure,
   then do P1.

---

## 8. Implementation task breakdown (for the execution phase)

1. **`simplify_waters_geometry.py` + pipeline wiring** (P0, ~2 h) — DP 0.001° + 5 dp on `geometry`; add
   `lengthKm`/`areaHa` to contracted waters; re-run `scripts/_perf_spike_measure.py` to confirm M8.
2. **Split `geometryByCounty` → `waters_county_clips.json` + lazy load in `map-store.ts`** (P0, ~2 h).
3. **Dead-weight removal + `.gitignore` + `attach_geometry.py` path fix** (P0, ~15 min).
4. **Compact serialization across build scripts + `refresh-data.mjs`** (P1, ~30 min).
5. **`WaterFeatureLayer` culling/LOD/hit-layer + slice re-sourcing from `allWaters`** (P1, ~3 h).
6. **`uncontracted_majors.json` + split load in `map-store.ts`** (P1, ~2 h).
7. **`scripts/check-data-budget.mjs` + wire into `data-refresh.yml`** (P1, ~1 h).
8. **(Optional) web-worker parse** (P2, ~3 h) — only if M9 re-scoped.

Each item is independently verifiable via the existing `scripts/_e2e_*.mjs` Playwright pattern
(notably `_e2e_county_clip.mjs`, `_e2e_focus_*.mjs`, `_e2e_association_highlight.mjs`) plus the new
`check-data-budget.mjs` and `_perf_spike_measure*.py`.

---

## 9. Verification (how to re-measure everything)

```bash
cd /home/stefan/undepescuim
.venv/bin/python3 scripts/_perf_spike_measure.py    # waters.json regimes R0..R4
.venv/bin/python3 scripts/_perf_spike_measure2.py   # uncontracted + LOD subsets
node scripts/check-data-budget.mjs                  # M7/M8/M9 + dead-weight gate (after implementation)
gzip -9 -c public/data/waters.json | wc -c          # M8 spot-check
npm run build && npm run start                      # then run the perf trace scripts from the test plan
```

The `window.__perfDataLoaded` instrumentation proposed in the test plan §9 is the trigger to add alongside
the 4.5 split so TC-02 measures the *new* first-paint boundary (majors-only), not the old full-load boundary.
