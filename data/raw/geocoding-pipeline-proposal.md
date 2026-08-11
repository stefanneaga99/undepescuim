# Proposed Geocoding Pipeline for Romanian Waters

**Date:** 2026-08-11
**Status:** Proposal — awaiting user review
**Based on:** Nominatim evaluation (t_0b9426b4), alternative-source comparison (t_5d59fdea), data requirements note (t_972abeae)

---

## 1. Overview

**Goal:** Transform a list of Romanian water body names (rivers and lakes) into a GeoJSON FeatureCollection with accurate polyline (MultiLineString) geometry for rivers and polygon geometry for lakes, suitable for display on a Leaflet map on UndePescuim.ro.

**Input:**
- 426 public waters from arebaltapeste.ro (mixed rivers + lakes, center points only)
- 201 private lakes (have `osmid` references — direct OSM lookup possible)
- Data includes: `name`, `subtype` (lac/rau), `coordinates` (center point), `bbox`, `judet`, `asociatie`

**Output:** GeoJSON FeatureCollection with MultiLineString (rivers) / Polygon (lakes) geometry, joined with source metadata (slug, judet, asociatie), confidence tier, and provenance tracking.

---

## 2. Three-Tier Strategy

The pipeline uses a hybrid approach: manual pre-mapping for high-visibility features, automated batch geocoding for the bulk, and structured fallbacks for the remainder.

```
┌─────────────────┐
│ Water names     │
│ (type: lac/rau) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────────┐
│Tier 1 │ │ Tier 2    │
│Manual │ │ Nominatim │
│~25    │ │ batch     │
│feat.  │ │ ~350 feat.│
└───┬───┘ └─────┬─────┘
    │            │
    └─────┬──────┘
          ▼
   ┌──────────────┐
   │ Tier 3       │
   │ Fallbacks    │
   │ ~50 feat.    │
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │ Merge +      │
   │ Validate     │ ◄── ANCPI, Natural Earth
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │ GeoJSON      │
   │ FeatureColl  │
   └──────────────┘
```

| Tier | Features | Method | Geometry Source | Coverage Est. | Quality |
|------|----------|--------|-----------------|---------------|---------|
| **Tier 1** | ~10 biggest rivers + ~15 major lakes | Manual pre-mapping | HOTOSM HDX + ANCPI TOPRO5 | 100% | ★★★★★ |
| **Tier 2** | ~350 named smaller waters | Nominatim batch geocoding | OSM Nominatim API | 80-95% | ★★★★☆ |
| **Tier 3** | ~50 unnamed/ambiguous/failed | Fallback chain | Overpass, NE, bbox | 60-70% polyline; 100% bbox | ★★☆☆☆–★★★★☆ |

---

## 3. Tier 1: Manual Pre-Mapping

### 3.1 Features to Pre-Map

**Rivers (10, as 13 polyline queries):**

| River | OSM Query | Notes |
|-------|-----------|-------|
| Siret | HOTOSM filter: `waterway=river, name=Siret` | Direct match |
| Olt | HOTOSM filter: `waterway=river, name=Olt` | Direct match |
| Mureș | HOTOSM filter: `waterway=river, name=Mureș` | Diacritic-tolerant |
| Prut | HOTOSM filter: `waterway=river, name=Prut` | Border river; works with RO tag |
| Dunărea | Overpass: no RO filter; clip to RO bbox | Transnational — "Danube" needed |
| Someș | HOTOSM filter: `waterway=river, name=Someș` | Normalized from Șomeș |
| Jiu | HOTOSM filter: `waterway=river, name=Jiu` | Direct match |
| Argeș | HOTOSM filter: `waterway=river, name=Argeș` | Direct match |
| Bistrița | HOTOSM filter: `waterway=river, name=Bistrița` | Disambiguate from city |
| Crișul Repede | HOTOSM filter: `waterway=river, name=Crișul Repede` | Tributary 1/3 |
| Crișul Alb | HOTOSM filter: `waterway=river, name=Crișul Alb` | Tributary 2/3 (OSM: "Fehér-Körös") |
| Crișul Negru | HOTOSM filter: `waterway=river, name=Crișul Negru` | Tributary 3/3 |

**Major lakes (~15):** Lacul Razim, Lacul Sinoe, Lacul Bicaz (Izvorul Muntelui), Lacul Vidraru, Lacul Snagov, Lacul Roșu, Lacul Sfânta Ana, Lacul Techirghiol, Lacul Siutghiol, Lacul Bucura, Lacul Bâlea, lacul Tarnița, etc.

### 3.2 Pre-Mapping Workflow

1. Download **HOTOSM Waterways HDX** GPKG (43 MB, monthly snapshot from HDX)
2. Filter by `waterway=river` for rivers, `water=lake/reservoir` for lakes
3. Match by name (diacritic-normalized comparison)
4. For Danube: query Overpass API with `way["waterway"="river"]["name"="Danube"]` and clip to Romanian extent (lon 20.26–29.69, lat 43.62–48.27)
5. For Criș: extract all three tributaries separately
6. Validate names against **ANCPI TOPRO5** (INSPIRE WFS) for official naming
7. Validate geometries against **Natural Earth Europe Supplement** for the largest features
8. Store as individual GeoJSON files in `data/premapped/`

### 3.3 Rationale

| Reason | Detail |
|--------|--------|
| Guaranteed quality | Most visible features — worth manual effort |
| Handle special cases | Danube (transnational), Criș (tributary system) are unreliable via batch |
| Set provenance baseline | Geometry from authoritative HOTOSM + ANCPI |
| Effort | ~25 features, ~1–2 hours one-time; ~30 min per refresh |

---

## 4. Tier 2: Nominatim Batch Geocoding

### 4.1 Pipeline Algorithm

```
for each water in remaining_waters (~350):
  1. Look up cache (SQLite, by query_string)
  2. If cache hit:
       return cached result (no API call)
  3. Construct query:
       lake: "{name}" + countrycodes=ro
       river: "{name} river Romania" + countrycodes=ro
  4. GET https://nominatim.openstreetmap.org/search
       ?q={query}&format=jsonv2&polygon_geojson=1
       &countrycodes=ro&limit=3
     Headers: User-Agent: UndePescuimMap/1.0 (contact@undepescuim.ro)
  5. SLEEP 1 second
  6. Filter results:
       - lake: keep if type="lake"
       - river: keep if category="waterway" AND type="river"
  7. If match found:
       extract geojson geometry, bbox, osm_type, osm_id, importance
  8. If no match → try fallback queries (see §4.2)
  9. Store in cache (including negative cache for misses)
```

### 4.2 Query Strategy Per Water Type

| Water Type | Primary Query | Fallback 1 | Fallback 2 |
|------------|--------------|------------|------------|
| **River** | `{name} Romania` + RO filter | `{name} river Romania` + RO filter | `{name}` no filter (post-filter by RO bbox) |
| **Lake** | `{name}` + RO filter | `Lacul {name}` + RO filter | `{name} Romania` + RO filter |

**Diacritic notes:**
- Query WITHOUT diacritics (Nominatim normalizes: `Mures` → `Mureș`)
- Add `river` suffix for disambiguation (e.g., `Bistrita river Romania` to avoid city match)
- Do NOT prefix with "Râul" (fails — use bare name)

### 4.3 Special Cases

| Case | Detection | Action |
|------|-----------|--------|
| Danube/Dunărea | name matches "Dunărea"/"Danube" | Pre-mapped (Tier 1) — skip batch |
| Criș | name matches "Criș" | Pre-mapped (Tier 1) — skip batch |
| Bistrița | top result is city, not river | Use "Bistrita river Romania" suffix |
| Olt | 2nd result is county boundary | Filter: `category=waterway` only |
| Transnational river | Nominatim returns no result with RO filter | Query without `countrycodes`, intersect bbox with Romanian extent |
| Multiple river segments | Multiple results with different OSM IDs | Take highest importance, or highest by `osm_type` (relation > way) |

### 4.4 Rate Limiting & Timing

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Request rate | 1 req/sec | Nominatim hard limit |
| Batch size (~350) | ~350 seconds ≈ 6 minutes | Plus retries |
| Retry on 429/503 | Exponential backoff: 2s, 4s, 8s | Max 3 retries, then flag as failed |
| User-Agent | `UndePescuimMap/1.0 (contact@undepescuim.ro)` | Required by Nominatim policy |
| Caching | Mandatory | Repeat queries may trigger blocks |

### 4.5 Expected Nominatim Coverage

Extrapolating from 21 spot-checks (10 rivers + 11 lakes):

| Category | Direct Match | With Fallback Queries | Likely Miss |
|----------|-------------|----------------------|-------------|
| Named lakes | ~95% | ~98% | ~2% |
| Named rivers (small/medium) | ~75% | ~90% | ~10% |
| Unnamed/obscure rivers | ~50% | ~65% | ~35% |

For ~350 Tier 2 features (assuming ~60% lakes, ~40% rivers based on typical Romanian fishing water distribution):

- Lakes (~210): ~206 matches (98%)
- Rivers (~140): ~126 matches (90%)
- **Total Tier 2 success: ~332 (95%)**
- **Tier 2 failures → Tier 3: ~18 features**

---

## 5. Tier 3: Fallback Chain

For features that Nominatim cannot geocode (~18 from Tier 2, plus ~30 pre-classified as ambiguous):

### 5.1 Ordered Fallback

| Step | Source | Method | Geometry Quality |
|------|--------|--------|-----------------|
| 1 | **Overpass API** | `area["ISO3166-1"="RO"]->.a; way["waterway"="river"]["name"="{name}"](area.a); out geom;` | ★★★★★ |
| 2 | **Natural Earth Europe Suppl.** | Check name match in public-domain dataset (1:10M scale, CCM-derived) | ★★★☆☆ |
| 3 | **bbox rectangle** | Compute polygon from source data `bbox [minLon, minLat, maxLon, maxLat]` | ★★☆☆☆ |
| 4 | **Manual review queue** | Flag for human geocoding | — |

### 5.2 Overpass API Details

- **Endpoint:** `https://overpass-api.de/api/interpreter`
- **Rate limit:** Dynamic (slot-based). Light use is fine; heavy batch may be throttled
- **Use:** For failed Nominatim queries, try exact name match with Romanian area filter
- **Advantage over Nominatim:** Returns raw OSM way geometry; no search ranking ambiguity
- **Disadvantage:** No fuzzy matching — exact name required

---

## 6. Cache Design

### 6.1 Schema (SQLite)

```sql
CREATE TABLE geocode_cache (
    query_string   TEXT PRIMARY KEY,
    water_name     TEXT NOT NULL,
    water_type     TEXT NOT NULL,           -- 'river' | 'lake'
    arebaltapeste_slug TEXT,               -- join key to source data
    result_json    TEXT,                    -- NULL = cache miss (negative cache)
    osm_type       TEXT,                    -- 'relation' | 'way'
    osm_id         TEXT,                    -- e.g. 'relation/12345'
    geometry_type  TEXT,                    -- 'MultiLineString' | 'Polygon' | 'Point'
    geojson        TEXT,                    -- raw GeoJSON geometry string
    bbox           TEXT,                    -- JSON array [s, n, w, e]
    importance     REAL,
    tier           TEXT DEFAULT 'tier2',    -- 'tier1' | 'tier2' | 'tier3_*'
    source         TEXT,                    -- 'nominatim' | 'overpass' | 'ne' | 'bbox'
    confidence     TEXT DEFAULT 'medium',   -- 'high' | 'medium' | 'low'
    hit_count      INTEGER DEFAULT 1,
    created_at     TEXT DEFAULT (datetime('now')),
    last_accessed  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_water_name ON geocode_cache(water_name);
CREATE INDEX idx_slug ON geocode_cache(arebaltapeste_slug);
```

### 6.2 Cache Policy

| Rule | Detail |
|------|--------|
| **Positive cache** | Store full Nominatim response → instant return on repeat |
| **Negative cache** | Store NULL result → prevents repeat API calls for known misses |
| **Pre-warming** | Run batch ahead of deployment; cache persists across sessions |
| **Invalidation** | Manual — re-run batch when: (a) source data changes, (b) OSM geometry update desired (90-day TTL recommended) |
| **Storage** | ~5 KB per feature → ~2.5 MB for full 426 + negative entries |
| **File location** | `data/cache/geocode.db` |

---

## 7. Output Schema

### 7.1 GeoJSON FeatureCollection

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "pipeline_version": "1.0",
    "generated_at": "2026-08-11T15:00:00Z",
    "total_input_waters": 426,
    "total_output_features": 410,
    "private_lakes_separate": 201,
    "coverage": {
      "tier1_manual": 25,
      "tier2_nominatim_hit": 310,
      "tier2_nominatim_miss": 40,
      "tier3_overpass_hit": 28,
      "tier3_ne_hit": 12,
      "tier3_bbox_only": 35,
      "tier4_failed": 16
    }
  },
  "features": [
    {
      "type": "Feature",
      "id": "siret",
      "geometry": {
        "type": "MultiLineString",
        "coordinates": [[[26.12, 45.40], [26.34, 45.52], "..."]]
      },
      "properties": {
        "name": "Siret",
        "name_ro": "Siret",
        "type": "river",
        "source": "manual_premap",
        "source_detail": "HOTOSM Waterways HDX, validated against ANCPI TOPRO5",
        "osm_type": "relation",
        "osm_id": "2718743",
        "importance": 0.545,
        "arebaltapeste_slug": "abc123",
        "judet": "Bacău",
        "asociatie": "AJVPS Bacău",
        "dimensiune": "559 km",
        "geocode_tier": "tier1",
        "confidence": "high"
      }
    },
    {
      "type": "Feature",
      "id": "lacul-rosu",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[25.78, 46.78], [25.80, 46.79], "..."]]
      },
      "properties": {
        "name": "Lacul Roșu",
        "name_ro": "Lacul Roșu",
        "type": "lake",
        "source": "nominatim",
        "source_detail": "Nominatim batch geocoding, polygon_geojson=1",
        "osm_type": "way",
        "osm_id": "177167861",
        "importance": 0.388,
        "arebaltapeste_slug": "xyz789",
        "judet": "Harghita",
        "asociatie": "AJVPS Harghita",
        "dimensiune": "12 Ha",
        "geocode_tier": "tier2",
        "confidence": "high"
      }
    }
  ]
}
```

### 7.2 Property Fields Reference

| Field | Source | Type | Description |
|-------|--------|------|-------------|
| `name` | OSM canonical | string | Display name on map |
| `name_ro` | OSM `name:ro` / HOTOSM | string | Romanian-language name |
| `type` | OSM `waterway`/`water` | string | `river` or `lake` |
| `source` | Pipeline | string | `manual_premap`, `nominatim`, `overpass`, `ne`, `bbox_fallback` |
| `source_detail` | Pipeline | string | Human-readable provenance |
| `osm_type` | Nominatim/OSM | string | `relation`, `way` |
| `osm_id` | Nominatim/OSM | string | Stable OSM reference |
| `importance` | Nominatim | float | 0–1 search ranking |
| `arebaltapeste_slug` | arebaltapeste.ro | string | Join key back to source data |
| `judet` | arebaltapeste.ro | string | County (România) |
| `asociatie` | arebaltapeste.ro | string | Managing fishing association |
| `dimensiune` | arebaltapeste.ro | string | Size (e.g., "240 Ha", "35 km") |
| `geocode_tier` | Pipeline | string | `tier1`, `tier2`, `tier3_overpass`, `tier3_ne`, `tier3_bbox`, `failed` |
| `confidence` | Pipeline | string | `high` (manual or perfect match), `medium` (fallback query match), `low` (bbox rectangle), `none` |

---

## 8. Private Lakes Pipeline (201 features)

These have `osmid` references — direct OSM lookup, no Nominatim needed.

```
for each private_lake:
  1. Parse osmid: "way/177167861" → type=way, id=177167861
                  "relation/13004279" → type=relation, id=13004279
  2. Query Overpass API:
       {type}(id:{id}); out geom;
  3. Extract Polygon geometry
  4. Expected coverage: ~98%+ (OSM IDs are stable)
```

Private lakes go through a separate pipeline because:
- They already have `osmid` → 100% deterministic lookup
- They are typically smaller, man-made reservoirs
- No Nominatim rate limit consumed

**Recommendation:** Process private lakes first (fast, deterministic), then use the main pipeline for the 426 public waters.

---

## 9. Coverage Estimate

### 9.1 Public Waters (426 features)

| Tier | Count | Success Rate | Features with Geometry | Geometry Quality |
|------|-------|-------------|----------------------|-----------------|
| Tier 1 (manual pre-map) | 25 | 100% | 25 | ★★★★★ (polylines/polygons) |
| Tier 2 (Nominatim hit) | ~310 | 88% | ~272 | ★★★★☆ (OSM polylines/polygons) |
| Tier 2 → Tier 3 (fallback needed) | ~90 | — | — | — |
| Tier 3a (Overpass API) | — | ~70% of 90 | ~63 | ★★★★☆ (OSM polylines) |
| Tier 3b (Natural Earth) | — | ~15% of remaining | ~4 | ★★★☆☆ (generalized) |
| Tier 3c (bbox rectangle) | — | 100% of remaining | ~23 | ★★☆☆☆ (axis-aligned rect) |
| **Tier 4 (failed)** | — | — | 0 | — |

**Rolling total:**

| Outcome | Features | % of 426 |
|---------|----------|----------|
| High-quality geometry (Tier 1 + Tier 2 hits) | ~297 | ~70% |
| Good geometry (Overpass fallback) | ~63 | ~15% |
| Coarse geometry (NE + bbox) | ~27 | ~6% |
| No geometry (failed) | ~39 | ~9% |
| **Any geometry at all** | **~387** | **~91%** |
| **High/Good geometry** | **~360** | **~85%** |

### 9.2 Private Lakes (201 features)

| Outcome | Features | % of 201 |
|---------|----------|----------|
| Direct OSM geometry via Overpass | ~197 | ~98% |
| Failed (OSM ID stale/broken) | ~4 | ~2% |

### 9.3 Combined Total

| Category | Total | With High-Quality Geometry | With Any Geometry |
|----------|-------|---------------------------|-------------------|
| Public waters | 426 | ~360 (85%) | ~387 (91%) |
| Private lakes | 201 | ~197 (98%) | ~197 (98%) |
| **Combined** | **627** | **~557 (89%)** | **~584 (93%)** |

---

## 10. Implementation Plan

### Phase 1: Setup (1–2 hours)

- [ ] Download HOTOSM Waterways HDX GPKG → `data/sources/hotosm_rou_waterways.gpkg`
- [ ] Create SQLite cache DB with schema from §6.1
- [ ] Write Python batch script (`scripts/geocode_batch.py`):
  - Load water list from `data/waters.json`
  - Tier classification: flag 10 biggest rivers + ~15 major lakes
  - Cache-first lookup, Nominatim query, 1s delay, result filtering
  - Fallback chain on miss
  - Output: `data/geocoded_public.geojson`
- [ ] Write private lakes script (`scripts/geocode_private.py`):
  - Parse osmid, query Overpass, extract geometry
  - Output: `data/geocoded_private.geojson`
- [ ] Configure `User-Agent: UndePescuimMap/1.0 (contact@undepescuim.ro)`

### Phase 2: Manual Pre-Map (1–2 hours)

- [ ] Extract 10 biggest rivers from HOTOSM by name filter
- [ ] Query Danube via Overpass, clip to Romanian bbox
- [ ] Query Criș system (3 tributaries) from HOTOSM
- [ ] Extract ~15 major lakes from HOTOSM or Nominatim
- [ ] Cross-validate names against ANCPI TOPRO5 WFS
- [ ] Store in `data/premapped/`

### Phase 3: Batch Geocode (~10 min runtime)

- [ ] Classify remaining waters: named rivers, named lakes, ambiguous
- [ ] Run Nominatim batch (automated, ~6 min for 350 features at 1 req/sec)
- [ ] For failures: run Overpass fallback
- [ ] For remaining failures: compute bbox rectangles from source data
- [ ] Flag hard failures for manual review

### Phase 4: Merge & Validate (1 hour)

- [ ] Merge Tier 1 + Tier 2 + Tier 3 results into `data/waters_geocoded.geojson`
- [ ] Join with arebaltapeste.ro metadata fields (slug, judet, asociatie, dimensiune)
- [ ] Visual spot-check: load in QGIS or geojson.io
- [ ] Fix obvious mismatches (wrong river assigned, off-by-one name match)

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Name mismatch (arebaltapeste → OSM)** | High (~15%) | Wrong river/lake returned | Result filtering by `category`/`type`; bbox proximity check; flag `confidence=low` if mismatch suspected |
| **Nominatim IP throttle** | Low | Pipeline stalls | 1 req/sec is well within policy limits; exponential backoff if 429 received |
| **OSM gaps in remote Carpathian areas** | Medium | Small mountain streams unmapped | Accept bbox fallback; flag for future enrichment; most fishing-accessible waters are in mapped areas |
| **ANCPI WFS unreliable** | Low–Medium | Can't validate pre-mapped data | HOTOSM is primary; ANCPI is validation-only. Degrade gracefully — skip validation, note in metadata |
| **HOTOSM data staleness** | Low | Monthly snapshot acceptable | Re-download from HDX monthly; diff geometry changes |
| **Overpass API throttle** | Low | Tier 3 fallback blocked | Overpass is only used for ~100 queries max; well within fair use |
| **Danube geometry — wrong segment** | Medium | Clipped segment may not align with the Romanian portion users expect | Manually verify bounding-box clip; consider using DanubeGIS as alternative |
| **Criș tributary confusion** | Low | User expects "Criș" as one river, not three | Label all three as "Criș (sistem)" with subtributary labels in popup |

---

## 12. Open Questions for User Review

| # | Question | Recommendation |
|---|----------|---------------|
| 1 | **Exact river/lake split in 426 public waters?** Need to count from arebaltapeste.ro `subtype` field. Lakes ~100% coverage; rivers ~90%. The split determines the overall coverage percentage. | Count subtypes before running pipeline |
| 2 | **ANCPI TOPRO5 license — OK alongside ODbL?** INSPIRE mandates open access; attribution TBD. Two licenses on one map — need to check compatibility. | Verify INSPIRE attribution terms; display dual attribution if needed |
| 3 | **Map tile attribution display?** OSM (ODbL) + ANCPI (INSPIRE) both require visible attribution credits. | Add attribution bar: "© OpenStreetMap contributors (ODbL) | Agenția Națională de Cadastru (INSPIRE)" |
| 4 | **Pipeline refresh cadence?** arebaltapeste.ro data changes periodically (new waters, association changes). | Re-run on each data refresh (monthly recommended) |
| 5 | **Cache TTL?** OSM names rarely change but geometry improves over time. | 90-day forced cache refresh; earlier if source data changes |
| 6 | **River confluence display?** Should Mureș polyline stop at the Hungarian border or continue to the Tisa confluence? | Display full named segment within Romanian territory (don't clip at arbitrary confluence) |
| 7 | **Cost / budget?** All sources are free. | $0 — no budget needed |
| 8 | **Bbox rectangles — acceptable as MVP?** 23 features (~5%) would display as axis-aligned rectangles instead of true shapes. | Acceptable for MVP; flag these clearly in metadata |

---

## 13. Summary

| Aspect | Recommendation |
|--------|---------------|
| **Primary geocoder** | Nominatim at 1 req/sec with mandatory SQLite caching |
| **Geometry source** | OSM ecosystem: HOTOSM HDX (batch) + Nominatim (search) + Overpass (fallback queries) |
| **Manual pre-mapping** | 10 biggest rivers + ~15 major lakes via HOTOSM + ANCPI validation |
| **Private lakes** | Direct Overpass lookup via existing `osmid` — separate fast pipeline |
| **Fallback chain** | Overpass API → Natural Earth Europe → bbox rectangles → manual review |
| **Output** | Single GeoJSON FeatureCollection with join keys to arebaltapeste.ro metadata |
| **Coverage** | ~89% high-quality geometry; ~93% any geometry (public + private combined) |
| **Effort** | ~3 hours manual (one-time) + ~10 min automated per pipeline run |
| **Cost** | $0 — all sources are free/open |
| **Code to write** | Two Python scripts (~200 lines total): batch geocoder + private lake processor |

---

*Proposal prepared for user review. No implementation code written — this document is the design artifact for confirmation before development begins.*
