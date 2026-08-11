# Data Requirements Note: UndePescuim.ro Map UI

**Date:** 2026-08-11
**Based on:** Probe data from arebaltapeste.ro, locuridepescuit.ro, ANPA
**Purpose:** Map every UI requirement to concrete data fields for the component designer.

---

## 1. Data Sources & Volume

| Source | Entity | Count |
|--------|--------|-------|
| arebaltapeste.ro | Associations | 82 |
| arebaltapeste.ro | Public waters (lac/rau) | 426 |
| arebaltapeste.ro | Private lakes (balti) | 201 |
| ANPA text | Contracted waters | ~640 entries |
| ANPA text | Non-contracted waters | ~few dozen |
| locuridepescuit.ro | Waters (same DB) | ~426 public + 201 private |

**Primary source for the map UI:** arebaltapeste.ro (structured JSON in SSR `__INITIAL_STATE__`).

---

## 2. UI Element → Data Field Mapping

### 2.1 Searchable Association Selector

**Data source:** `GET /asociatii` (SSR page with `window.__INITIAL_STATE__`)

**List endpoint fields:**
```
asociatii[].name        → "AJVPS VÂLCEA"           [display name]
asociatii[].name_long   → "Asociaţia Judeţeană..."  [full name]
asociatii[].slug        → "ajvps-valcea"             [unique key]
asociatii[].ape         → 46                         [water count]
```

**Detail fields (embedded in each water body):**
```
asociatie.adresa        → "Strada Bartók Béla..."   [address]
asociatie.telefon       → "0264 420 908"            [phone]
asociatie.siteUrl       → "http://cluj.rosilva.ro/" [website]
asociatie.id            → "6440f473476607000974d494" [MongoDB ObjectId]
```

**Note:** All 82 associations fit in a single page load (~240KB). Client-side search/filter is viable. No API autocomplete endpoint was observed; a backend search endpoint may be needed for character-by-character autocomplete (or implement with a small JSON file + fuse.js).

**Coverage relationship:** Selecting an association should filter the map to waters where `water.asociatie.slug === selectedAssociation.slug`.

---

### 2.2 Leaflet Map — Water Features (Polylines/Polygons)

**Data source:** `GET /ape` (SSR page, paginated — 15 per page, 426 total)

**Water fields:**
```
slug              → "iwrd2dxy"                       [unique ID]
name              → "Lacul Tarnița"                  [label]
judet             → "Cluj"                           [county]
type              → "ape"                            [always "ape" for public]
subtype           → "lac" | "rau"                    [water type: lake/river]
limite            → "zona de acumulare"              [sector boundary text]
dimensiune        → "240 Ha" | "35 km"               [size with unit]
pescuit_interzis  → false                            [fishing banned flag]
referinta         → "Lista habitatelor..."           [legal reference doc]
coordinates       → [23.2745, 46.71585]              [center point lon,lat]
driving           → [23.2745, 46.71585]              [directions point]
bbox              → [minLon, minLat, maxLon, maxLat]  [bounding box]
asociatie         → { name, slug, telefon, ... }     [nested association]
```

#### GAP: NO POLYLINE/POLYGON GEOMETRY

The data contains ONLY:
- `coordinates`: single center point `[lon, lat]` (WGS84)
- `bbox`: bounding box `[minLon, minLat, maxLon, maxLat]`

**There are no river polylines or lake polygon boundaries.** This is the most critical gap.

**Potential workarounds (in priority order):**

1. **OSM-based geometry retrieval** — For private lakes, the `osmid` field exists (`"relation/13004279"`, `"way/177167861"`). For public waters (426), there is NO `osmid`. You would need to match water names to OSM features via Nominatim or Overpass API, which is slow, unreliable, and not acceptable for a production map.

2. **Bounding-box rectangles** — Use `bbox` to draw rectangular polygons as a fallback. Rivers would appear as axis-aligned rectangles, which is crude but functional. Lakes would be rectangular approximations.

3. **Center-point markers** — Use `coordinates` as circle markers, sized by water area. Simplest option but loses the "polyline/polygon" visual promise.

4. **Pre-computed GeoJSON** — Manually create or source GeoJSON files for all 426 waters. High effort, not automatable from probe data.

**Recommendation:** Start with option 2 (bbox rectangles) + option 3 (sized circles) as a proof of concept. Plan to add real geometries in a future data-enrichment pass.

---

### 2.3 Map Coloring: Green (covered) / Grey (not covered)

**Logic:** 
- When an association is selected → waters with `water.asociatie.slug === selectedSlug` are GREEN, all others are GREY.
- When NO association is selected → all waters are displayed in a neutral color (e.g., blue), or all are shown as "not covered."

**Data needed:** `water.asociatie.slug` — AVAILABLE on every water body.

**Implementation:** Client-side filter + CSS class toggle on Leaflet layers. No additional endpoint needed.

---

### 2.4 Water Detail Card

**Required fields:**
| Card Element | Field | Available? | Value Example |
|---|---|---|---|
| Sector km | `limite` + `dimensiune` | YES | "De la Steaua - la Pârâul Alb" + "35 km" |
| Water type | `subtype` | YES | "lac" / "rau" |
| Association contact | `asociatie.telefon` | YES | "0264 420 908" |
| Association contact | `asociatie.adresa` | YES | "Strada Bartók Béla, Nr. 27..." |
| Association contact | `asociatie.siteUrl` | YES | "http://cluj.rosilva.ro/" |
| Water name | `name` | YES | "Lacul Tarnița" |
| County | `judet` | YES | "Cluj" |
| Fishing banned | `pescuit_interzis` | YES | true/false |
| Size | `dimensiune` | YES | "240 Ha" |
| **Permit note** | — | **GAP** | See below |

#### GAP: "Permit Note" Field

The `referinta` field contains a document reference (e.g., "Lista habitatelor piscicole naturale din apele de munte..."), NOT a permit/contract note.

The ANPA data contains **contract numbers** (e.g., "42/14.11.2017", "39/18.10.2017") — these are the closest analog to a "permit note."

**Options:**
1. Display `referinta` with label "Referință legală" (legal reference) — available but not exactly a "permit note."
2. Integrate ANPA contract numbers — requires cross-referencing ANPA text data with arebaltapeste.ro water names (fuzzy matching needed).
3. Add a custom `nota_permis` field later through manual data entry.

**Recommendation:** Use `referinta` as a fallback. Flag "permit note" as a field to be enriched in a future data pass (possibly via ANPA cross-reference or manual entry).

---

### 2.5 County Filter

**Data field:** `water.judet` — AVAILABLE on every water body.

**Counties represented in probe sample:** Alba, Arad, Argeș, Bacău, Bihor, Bistrița-Năsăud, Botoșani, Brașov, Brăila, Buzău, Caraș-Severin, Călărași, Cluj, Constanța, Covasna, Dâmbovița, Dolj, Galați, Giurgiu, Gorj, Harghita, Hunedoara, Ialomița, Iași, Ilfov, Maramureș, Mehedinți, Mureș, Neamț, Olt, Prahova, Satu Mare, Sălaj, Sibiu, Suceava, Teleorman, Timiș, Vaslui, Vâlcea, Vrancea (+ București).

**Implementation:** Client-side deduplication from loaded water data. No server-side filter endpoint needed for initial version (426 items is small enough for client-side filtering).

---

### 2.6 Water-Type Filter

**Data field:** `water.subtype` — AVAILABLE.
- `"lac"` — lake (standing water)
- `"rau"` — river (flowing water)

**Implementation:** Client-side filter on `subtype`.

---

### 2.7 Color Legend

**Static UI element.** No data dependency — display a fixed legend:
- Green polygon/line = covered by selected permit
- Grey polygon/line = not covered by selected permit
- (Optional) Blue = no association selected / neutral view

**Note:** If using bbox rectangles as fallback for geometry, the legend should reflect that distinction (rectangle vs. actual polygon).

---

## 3. Data Access Strategy

### Option A: Static JSON Files (Recommended for MVP)

Pre-extract all data from the probe HTML files into static JSON files served alongside the app:
```
/data/associations.json   — 82 associations (name, slug, name_long, ape)
/data/waters.json          — 426 public waters (all fields)
/data/balti.json           — 201 private lakes (optional)
```

- No backend needed
- All filtering is client-side
- Data is ~500KB-1MB total (acceptable for first load)
- Data freshness: manual refresh via scrape cron

### Option B: Live API Proxy

Proxy requests to `api.arebaltapeste.ro` (discovered from image URLs):
- Base URL: `https://api.arebaltapeste.ro/api/`
- Requires reverse-engineering the API (observed endpoints not included in probe)
- Risk: API may change, require auth, or block CORS

### Option C: Custom Backend

Build a lightweight backend that:
- Stores extracted data in SQLite/PostgreSQL
- Provides REST endpoints: `/api/associations?q=`, `/api/waters?judet=&subtype=&asociatie=`
- Serves GeoJSON with computed bbox polygons

**Recommendation:** Start with Option A (static JSON). Move to Option C only when data volume or update frequency demands it.

---

## 4. Geometry Format Summary

| Format | Where Used | Notes |
|--------|-----------|-------|
| `[lon, lat]` | `coordinates`, `driving` | WGS84, GeoJSON convention |
| `[minLon, minLat, maxLon, maxLat]` | `bbox` | Bounding box, WGS84 |
| GeoJSON (desired) | polyline/polygon | NOT AVAILABLE |
| OSM reference | `osmid` ("way/...", "relation/...") | Available for private lakes only |

**For Leaflet:** Convert `coordinates` `[lon, lat]` to Leaflet `[lat, lon]`. Convert `bbox` `[minLon, minLat, maxLon, maxLat]` to Leaflet bounds `[[minLat, minLon], [maxLat, maxLon]]`.

---

## 5. Summary of Gaps

| Gap | Severity | Workaround |
|-----|----------|------------|
| **No polyline/polygon geometry** | CRITICAL | Use bbox rectangles + center-point circles as MVP fallback |
| **No "permit note" field** | MEDIUM | Use `referinta` field; plan ANPA cross-reference for contract numbers |
| **No autocomplete/search API endpoint** | LOW | Load all 82 associations client-side; use fuse.js for fuzzy search |
| **No server-side filter endpoints** | LOW | Client-side filtering on 426 items is sufficient |
| **No `osmid` for public waters** | MEDIUM | Blocks OSM geometry retrieval for 426 waters |
| **ANPA data has no geometry at all** | HIGH | ANPA is authoritative but unusable for maps without spatial enrichment |
| **Data freshness** | MEDIUM | Static files need periodic re-extraction; live API would auto-update |

---

## 6. Recommended Data Pipeline

```
1. EXTRACT: Parse __INITIAL_STATE__ from arebaltapeste.ro HTML pages
2. TRANSFORM: Normalize fields, flatten nested association data where needed
3. ENRICH (future): Cross-reference ANPA contract numbers, add OSM geometries
4. SERVE: As static JSON files for MVP, or via lightweight API for production
```

**For the component designer:** All UI elements EXCEPT polygon/polyline geometry and permit note have direct data field mappings. The geometry gap is the most important — the component should be designed to accept both bbox-rectangles (MVP) and true GeoJSON polygons/polylines (future), with the same Leaflet rendering pipeline.
