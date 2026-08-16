# County + Locality Filter — SPIKE Research & Implementation Plan

**Task:** t_5ca02b4a
**Author:** plan-maker
**Date:** 2026-08-16
**Status:** Plan — awaiting review (blocked `review-required`)

---

## 1. Goal

Add a **locality (localitate)** filter to UndePescuim, layered on top of the
existing county (județ) filter. User flow: pick a county → pick a locality
inside it → map shows only waters touching that locality.

The county filter already exists (41 counties, multi-select chips, per-county
clipped geometry). Locality is new.

---

## 2. What exists today (verified against the repo)

### 2.1 County filter architecture (the pattern to parallel)

| Piece | File | Role |
|-------|------|------|
| Store state | `src/stores/map-store.ts` | `countyFilter: string[]`, `toggleCounty()` |
| Derived county list | `src/hooks/use-counties.ts` | dedupes `w.judet` over contracted + uncontracted |
| Filter application | `src/hooks/use-filtered-waters.ts`, `src/hooks/use-filtered-uncontracted.ts` | county ∩ type ∩ contract (AND), with clip |
| Per-county clip | `src/utils/county-clip.ts` | `countyClipKey()`, `countyRenderGeometry()` |
| Clip build (offline) | `scripts/build_county_clip_geoms.py` | shapely point-in-polygon / clip vs county polys |
| Boundary data | `data/raw/county_boundaries/*.json` | 41 Nominatim GeoJSON polygons |
| UI | `src/components/map/CountyFilter.tsx` | multi-select chips, mobile scroll / desktop wrap |
| Container | `src/components/map/FilterBar.tsx` | mobile bar + desktop overlay panel |

### 2.2 Data — is locality already present? (No.)

Every water source was inspected. **There is no `localitate` field anywhere.**
The only locality-ish signal is free text:

- `waters.json` `limite` (1004/1013 non-empty) — e.g. `"Băbeni"`,
  `"Sascut - Berești"`, `"Mihoești, comuna Câmpeni"`, `"în proximitatea
  orașului Botoșani"` — but also **`"Artificial"`, `"Natural"`, `"Județ
  Vâlcea"`, `"Izvoare – conf. cu râul Olt"`, `"Confl. Valea Drăganului -
  Confl. Valea Iadului"`, `"zona de acumulare"`**.
- `anpa_romsilva_waters.jsonl` `limits_text` (289) — same mix, dominated by
  river-confluence descriptors.
- `arebaltapeste_waters.jsonl` `limits_text` (426) — `"zona de acumulare"` etc.
- `locuri_waters.jsonl` (626) — `limits_text` mostly **null**.
- `associations.json` `adresa` — the association's **HQ street address** (not
  a per-water locality).

**Conclusion:** `limite` text is the *only* in-repo signal, and it is fragile.

### 2.3 `limite` text quality (measured)

Over the 1004 waters with a non-empty `limite`:

| Category | Count | Locality-resolvable? |
|----------|-------|----------------------|
| Confluence / source / mouth descriptor (`conf`, `izvoare`, `vărsare`) | **484 (~48%)** | No |
| `Județ X` (county-only) | 45 | No |
| `Artificial` / `Natural` / `zona de acumulare` | 65 | No |
| Empty / null | 9 | No |
| Genuine locality name(s) | **~400 (~40%)** | Yes (needs gazetteer + parse) |

Even the "genuine" bucket needs a Romanian locality gazetteer and fuzzy
matching to disambiguate `Băbeni` (town) from `Băbeni` (commune), diacritics
(`Răcăciuni` vs `Racaciuni`), and multi-locality strings (`"Sascut - Berești"`).

**Verdict: `limite` parsing alone would cap locality coverage at ~40% of
contracted waters, with a noisy tail.** Not viable as the primary source.

### 2.4 Spatial anchors (for a geometry-based approach)

| Pool | Count | Has `coordinates` or `geometry` |
|------|-------|---------------------------------|
| Contracted (`waters.json`) | 1,013 | **742 (73%)** |
| Uncontracted rivers (`uncontracted_rivers.json`) | 4,179 | 4,179 (100%) |
| Uncontracted lakes (`uncontracted_lakes.json`) | 5,712 | 5,712 (100%) |
| **Total** | **10,904** | **10,633 (98%)** |

The 271 contracted waters lacking both are ANPA/Romsilva entries that were
never geocoded (bbox-only or nothing, slugs like `anpa-anpa-0008`). These are
exactly the ones whose `limite` is a confluence descriptor, so no approach
recovers them cleanly.

---

## 3. Data source — three options, one recommendation

### Option A — Geometry: point-in-polygon vs UAT (admin_level=8) boundaries ✅ RECOMMENDED

Assign each water to the Romanian **UAT** (unitate administrativ-teritorială =
municipiu / oraș / comună; OSM `admin_level=8`) whose polygon it intersects.

- **Source of boundaries:** one-time bulk fetch of Romania's ~3,200 UAT
  polygons. In order of preference:
  1. **Overpass** (matches the repo's existing Overpass usage —
     `overpass_water_all.json` is a 258 MB Overpass dump):
     `area["ISO3166-1"="RO"]->.ro; rel(area.ro)["boundary"="administrative"]["admin_level"="8"]; out geom;`
  2. **Geofabrik Romania** `.osm.pbf` extract (admin boundaries pre-baked).
  3. **ANCPI** (official cadastre) — authoritative but harder to fetch
     programmatically.
- **Pros:** ~98% coverage of all waters; deterministic; offline build; exactly
  parallels the existing `build_county_clip_geoms.py` pattern; the boundary
  payload stays server-side (like the county clips).
- **Cons:** one new data dependency (~100–200 MB raw, reduced to a compact
  assignment map on disk); must decide river (multi-locality) semantics (§4).
- **Effort:** the bulk of the work is a ~100-line offline script + a
  build-time lookup; low risk because the county clip already proves the
  shapely pipeline.

### Option B — `limite` text + gazetteer ❌ (fallback only)

Parse locality names out of `limite` and match against a Romanian gazetteer.

- **Pros:** no new geometry dependency; fast.
- **Cons:** ~40% coverage, heavy noise (confluences, `Județ X`, `Natural`),
  needs a gazetteer + diacritic/normalization/fuzzy matching, and still fails
  on the 271 ungeocoded ANPA entries.
- **Verdict:** keep as a *supplement* to label the 271 geometry-less waters,
  never as the primary source.

### Option C — Nominatim batch reverse-geocode ❌

- **Pros:** zero boundary fetch.
- **Cons:** 1 req/s rate limit → ~1,000 contracted waters ≈ 17 min + retries;
  usage policy restricts bulk; reverse-geocoding a river *line* returns an
  arbitrary point's locality, not the set it crosses; non-deterministic.
- **Verdict:** reject as primary. (Nominatim is already used for *county*
  polygons, but that was 41 calls, not thousands.)

---

## 4. Locality assignment semantics (the key design decision)

County is **one-to-one** (every water has exactly one `judet`). Locality is
**one-to-many** for rivers: a river *sector* in Cluj crosses 5–15 communes.
This is the single most important difference and it drives both the data model
and the UI.

Three candidate semantics:

1. **"Touches" (multi-assignment) — RECOMMENDED.** A water is listed under
   every UAT its geometry intersects. A lake → the 1 UAT(s) it lies in; a
   river → every UAT its line passes through. Matches user intuition ("where
   can I fish in Comuna Florești?" shows the Someș sector that passes
   Florești). `localitati: string[]` (array) on each water.
2. **"Primary" (single)** — assign the UAT of the centroid / downstream end.
   Simpler data (one string), but lossy and hard to explain ("why does the
   Florești sector show under Cluj-Napoca?").
3. **"Start point" (from `limite`)** — fragile, ties locality to the same
   broken text we rejected in §3.

**Recommendation: option 1 (`localitati: string[]`).** The UAT-name grain is
right: fishermen search by commune/city, not by village (OSM `admin_level=10`).
Where a water's geometry is missing (the 271), fall back to a *single* parsed
locality from `limite` (Option B) or leave the array empty (water simply never
appears under any locality — it stays reachable via the county filter).

---

## 5. Scope decision (coverage estimate)

| Scope | Waters covered | Notes |
|-------|----------------|-------|
| Contracted only (1,013) | 742 (73%) via geometry + ~150 via `limite` fallback ≈ **~890 (88%)** | The 271 geometry-less ANPA entries are mostly unresolvable |
| Contracted + uncontracted (10,904) | **10,633 (98%)** via geometry | Uncontracted lakes are 5,712 — locality filter over them is high-value ("find a pond near my village") |

**Recommendation: build the assignment for ALL pools** (contracted +
uncontracted). The offline script is a single pass; the marginal cost of
including the 9,891 uncontracted waters is near-zero, and the filter's real
killer feature is "find water near me" which is exactly the uncontracted pond
case. The UI naturally degrades: a locality with only uncontracted ponds just
shows those.

---

## 6. Data pipeline plan (offline, mirrors `build_county_clip_geoms.py`)

New files under `data/raw/localities/` + `scripts/`.

```
data/raw/localities/
  uat_boundaries.geojson      # ~3,200 UAT polygons (raw, committed or .gitignore'd)
  uat_index.json              # { normName: {name, county} } for UI labels
scripts/
  fetch_uat_boundaries.py     # Overpass → data/raw/localities/uat_boundaries.geojson
  build_locality_assignment.py # adds `localitati: string[]` to waters + uncontracted
```

`build_locality_assignment.py` logic (shapely, ~100 lines):

```python
# for each pool (waters.json, uncontracted_rivers.json, uncontracted_lakes.json):
#   candidate geom = w["geometry"] or Point(w["coordinates"]) or skip
#   for line rivers: buffer ~150m so a border stream isn't split down its middle
#     (same trick as BUFFER_DEG=0.002 in build_county_clip_geoms.py)
#   hits = [uat for uat in index if geom.intersects(uat.poly)]
#   w["localitati"] = sorted(dedupe(hits))   # [] when none
#   # fallback (optional, second pass) for geometry-less contracted waters:
#   #   w["localitati"] = [parse_locality(w["limite"])]  if resolvable
```

Output: adds `localitati: string[]` (and `localitati_norm: string[]` for
diacritic-free lookups) to `public/data/waters.json`,
`public/data/uncontracted_rivers.json`, `public/data/uncontracted_lakes.json`,
preserving the committed serialization (indent=1, `ensure_ascii=False`, no
trailing newline — same as the county-clip writer).

A separate small `public/data/localities.json` is NOT needed — the locality
list is derived client-side from `w.localitati`, exactly like `useCounties`
derives counties today.

---

## 7. UI plan

### 7.1 Interaction model

- **Hierarchy, not flat.** Locality is only meaningful *within* a county
  (duplicate locality names exist across counties — e.g. multiple
  "Valea ..."/"Fântânele"). So:
  1. User toggles a county (existing chip).
  2. When ≥1 county is selected, a **"Localitate"** row appears beneath,
     listing the localities present in the selected counties' waters.
  3. Selecting a locality ANDs with the county/type/contract filters.
- **Widget:** a searchable **dropdown/popover** (shadcn `Popover` +
  `Command`), not chips — a single county can expose 40–100 localities, which
  is too many for the chip row (mobile-first constraint). The existing
  `src/components/ui/command.tsx` + `popover.tsx` are already in the tree.
- **Mobile:** the dropdown opens as a bottom sheet consistent with the
  existing `vaul` sheet (`WaterDetailSheet`). Desktop: anchored popover.
- **Empty state:** selecting a county with no locality-filterable waters shows
  "Fără localități" and the county filter still works alone.

### 7.2 Component sketch

```tsx
// src/components/map/LocalityFilter.tsx  (new)
interface LocalityFilterProps {
  localities: string[];              // deduped, sorted — from useLocalities()
  selected: string[];                // from store
  onToggle: (locality: string) => void;
  onClear: () => void;
}
// Renders a labeled popover: "Localitate" + current selection as a pill
// ("Toate localitățile" when empty). Body = Command search + checkbox list.
```

```tsx
// FilterBar.tsx — insert between CountyFilter and the type/contract group:
<CountyFilter ... />
{countyFilter.length > 0 && <LocalityFilter ... />}   // only when a county is picked
<div className="...">
  <WaterTypeFilter ... />
  <ContractFilter ... />
</div>
```

### 7.3 Store & hook changes (mirror county)

```ts
// map-store.ts
localityFilter: string[];
toggleLocality: (l: string) => void;
clearLocalities: () => void;
// R9 parity: toggling locality re-checks selectedWaterSlug survival.

// src/hooks/use-localities.ts  (new) — mirror use-counties.ts
//   derive localities from the waters matching the current countyFilter:
//   [...waters, ...uncontracted]
//     .filter(w => countyFilter.length===0 || countyFilter.includes(w.judet))
//     .flatMap(w => w.localitati) → dedupe → sort

// use-filtered-waters.ts / use-filtered-uncontracted.ts:
//   add: if (localityFilter.length > 0)
//          result = result.filter(w => w.localitati?.some(l => localityFilter.includes(l)))
```

No geometry clipping is needed for locality (the water is either in or out),
so `countyRenderGeometry` is untouched.

### 7.4 Filter semantics recap

`county` AND `locality` AND `type` AND `contract` — locality is a *refinement*
of county, applied only when a county is selected (a locality selection with
no county is not exposed; if the county is later deselected, localities clear).

---

## 8. Step-by-step implementation tasks

> Estimated 2–5 min each once the boundary data lands; the boundary fetch is
> the one long pole (~1–2 min over the network, then cached).

1. **Fetch UAT boundaries.** Write `scripts/fetch_uat_boundaries.py`
   (Overpass `admin_level=8` → `data/raw/localities/uat_boundaries.geojson`).
   Run it. Verify ~3,000+ features, each with `name` + `is_in:county`/county
   tag. *(Effort: S)*
2. **Build the locality index.** Extend the script to emit
   `data/raw/localities/uat_index.json` keyed by `countyClipKey(name)` →
   `{name, county}` for UI labels. *(Effort: XS)*
3. **Assignment script.** Write `scripts/build_locality_assignment.py`
   (§6). Run over all three pools. Verify `localitati` lands on ~98% of
   waters and is `[]` only where expected. *(Effort: M)*
4. **Type contract.** Add `localitati?: string[]` to `Water` in
   `src/types/data.ts`; add `Locality = string` alias. *(Effort: XS)*
5. **Store.** Add `localityFilter` + `toggleLocality`/`clearLocalities` +
   R9 survival re-check in `map-store.ts`. *(Effort: S)*
6. **Hook.** Add `use-localities.ts` (county-scoped derivation). *(Effort: S)*
7. **Filter application.** Add the locality predicate to
   `use-filtered-waters.ts` and `use-filtered-uncontracted.ts`. *(Effort: XS)*
8. **UI component.** Add `LocalityFilter.tsx` (popover + command search) and
   wire into `FilterBar.tsx` behind the `countyFilter.length > 0` gate.
   *(Effort: M)*
9. **i18n + empty state.** Add RO/EN labels ("Localitate"/"Locality",
   "Toate localitățile"/"All localities", "Fără localități"/"No localities").
   *(Effort: XS)*
10. **e2e.** Extend the existing Playwright pattern
    (`scripts/_e2e_county_clip.mjs`) with a locality case: select Cluj →
    locality dropdown lists Cluj-Napoca/Florești; toggling filters the map;
    R9 dismisses the sheet when the selected water leaves the filter.
    *(Effort: M)*

**Verification commands:**
```bash
python3 scripts/fetch_uat_boundaries.py          # one-time
python3 scripts/build_locality_assignment.py     # adds localitati to 3 JSONs
npx tsc --noEmit                                 # typecheck
npm run lint
node scripts/_e2e_locality.mjs                   # new Playwright e2e
npm run build && npm run start                    # manual smoke test
```

---

## 9. Effort estimate

| Component | Effort |
|-----------|--------|
| UAT boundary fetch + index | S (½ day) |
| Assignment script + run | M (1 day) |
| FE store + hooks + filter predicate | S (½ day) |
| LocalityFilter UI + popover/search + i18n | M (1 day) |
| e2e + review | S (½ day) |
| **Total** | **~3–4 engineer-days** |

Risks that could move this: Overpass UAT data quality (missing/duplicate
names, counties vs UAT nesting), the 271 geometry-less contracted waters
(needs the `limite` fallback or explicit exclusion), and payload size growth
on `waters.json` (each water gains a small string array — negligible, but the
uncontracted lakes file is already large; `localitati` adds ~50 KB there).

---

## 10. Risks & tradeoffs

1. **Many-to-many river semantics** — a river appears under many localities;
   must be communicated (a subtle "acest sector traversează N localități" note
   on the water card) or users will think locality = water's home town.
2. **UAT name collisions across counties** — handled by scoping the dropdown
   to the selected county; the store must store a *county-scoped* key, not a
   bare name, if two selected counties share a locality name. Simpler: clear
   localities whenever the county selection changes.
3. **Boundary source license/attribution** — OSM requires attribution (already
   present via OSM tiles); ANCPI terms need checking if we switch.
4. **Payload growth** — string arrays are cheap; monitor `waters.json` +
   `uncontracted_lakes.json` bundle size in CI after the build.
5. **The 271 ungeocoded waters** — decide: `limite`-parse fallback, manual
   curation, or exclude. Recommendation: exclude from locality (still
   reachable by county) + open a follow-up to geocode them.

---

## 11. Open questions for the reviewer

1. **Scope:** contracted-only, or all 10,904 waters (recommended: all)?
2. **Semantics:** "touches" multi-assignment (recommended) vs single primary
   locality?
3. **Boundary source:** Overpass UAT dump (recommended) vs Geofabrik vs ANCPI?
4. **The 271 geometry-less waters:** exclude (recommended) or invest in a
   `limite`-parse fallback now?
5. **Locality grain:** UAT / comună (admin_level=8, recommended) vs village /
   sat (admin_level=10, finer, ~13,000 features)?
