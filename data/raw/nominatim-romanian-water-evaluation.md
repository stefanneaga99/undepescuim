# Nominatim Evaluation for Romanian Water Geocoding

**Date:** 2026-08-11
**Evaluator:** plan-maker (Hermes agent)
**Task:** Evaluate whether Nominatim/OpenStreetMap can reliably batch-geocode Romanian river and lake names.

---

## 1. Usage Policy Summary

| Rule | Detail |
|------|--------|
| **Rate limit** | Max **1 request/second** (absolute hard limit) |
| **Bulk geocoding** | Discouraged but small one-time tasks OK; single thread, single machine only |
| **Long-running scripts** | Scripts running >1 day or at regular intervals: restricted to **4 requests/minute** |
| **Caching** | Results **MUST be cached** client-side; repeat queries may trigger blocks |
| **Attribution** | Must display OSM attribution clearly |
| **User-Agent** | Must identify application (no stock library UAs) |
| **License** | ODbL — share-alike; small extractions likely fair use |
| **Cost** | Free (donated servers) |

**Verdict:** A batch geocoding pipeline for Romanian water bodies is viable under the policy _if_ it runs as a single-threaded, rate-limited, one-time (or cached) operation. A pipeline of ~100 queries would take ~2 minutes.

---

## 2. River Spot-Checks (10 Major Romanian Rivers)

All queries used `format=jsonv2&polygon_geojson=1`. For rivers within Romanian borders, `countrycodes=ro` was used unless noted.

| # | River | Query Used | Found? | OSM Type | Importance | Geometry | Notes |
|---|-------|-----------|--------|----------|------------|----------|-------|
| 1 | **Siret** | `Siret` (RO filter) | ✓ | relation (river) | 0.545 | **MultiLineString** | Excellent — full course in RO |
| 2 | **Olt** | `Olt` (RO filter) | ✓ | relation (river) | 0.558 | **MultiLineString** | Top result is river; 2nd is county boundary |
| 3 | **Mureș** | `Mureș` (RO filter) | ✓ | relation (river) | 0.550 | **MultiLineString** | Works with and without diacritic |
| 4 | **Prut** | `Prut` (RO filter) | ✓ | relation (river) | 0.579 | **MultiLineString** | Name shows bilingual: "Prut / Прут" |
| 5 | **Dunărea** | `Dunărea` (RO filter) | ✗ | — | — | — | Returns village/peak in Constanța, NOT the river |
| 5b | **Dunărea** | `Dunărea` (no filter) | ✓ | relation (river) | 0.734 | **MultiLineString** | Top result = Danube (English name). RO name triggers match but filtered out by countrycodes=ro because Danube spans 10+ countries |
| 5c | **Danube** | `Danube` (no filter) | ✓ | relation (river) | 0.734 | **MultiLineString** | Best query: highest importance of all results |
| 6 | **Someș** | `Somes` (RO filter) | ✓ | relation (river) | 0.496 | **MultiLineString** | Returns as "Șomeș" (diacritic normalized) |
| 7 | **Jiu** | `Jiu` (RO filter) | ✓ | relation (river) | 0.508 | **MultiLineString** | Clean result |
| 8 | **Argeș** | `Argeș` (RO filter) | ✓ | relation (river) | 0.512 | **MultiLineString** | Works with & without diacritic; county also returned |
| 9 | **Bistrița** | `Bistrița` (RO filter) | ✓ | relation (river) | 0.479 | **MultiLineString** | 1st result = city; 2nd = river. Add "river" to query for disambiguation |
| 10 | **Criș** | `Criș` (RO filter) | ✗ | — | — | — | Returns 2 villages named Criș, not the river |
| 10b | **Crișul Repede** | `Crișul Repede` (RO filter) | ✓ | relation (river) | 0.462 | **MultiLineString** | Works; main tributary |
| 10c | **Crișul Alb** | `Crișul Alb` (RO filter) | ✓ | relation (river) | 0.412 | **MultiLineString** | OSM name = "Fehér-Körös" (Hungarian) |

### River Summary

| Status | Count | Details |
|--------|-------|---------|
| **Direct match** | 8/10 | Siret, Olt, Mureș, Prut, Someș, Jiu, Argeș, Bistrița |
| **Needs name variant** | 2/10 | Dunărea → use "Danube"; Criș → use "Crișul Repede" + "Crișul Alb" + "Crișul Negru" |
| **Geometry type** | MultiLineString | All river relations return detailed polylines (not points) |
| **Importance range** | 0.46–0.73 | Danube highest (0.73), Crișul Repede lowest (0.46) |

---

## 3. Lake Spot-Checks (11 Romanian Lakes)

All queries used `format=jsonv2&polygon_geojson=1&countrycodes=ro`.

| # | Lake | Query | Found? | OSM Type | Geometry | Importance |
|---|------|-------|--------|----------|----------|------------|
| 1 | Lacul Roșu | `Lacul Rosu` | ✓ | way (lake) | **Polygon** | 0.388 |
| 2 | Lacul Bicaz | `Lacul Bicaz` | ✓ | way (lake) | **Polygon** | 0.393 |
| 3 | Lacul Vidraru | `Lacul Vidraru` | ✓ | way (lake) | **Polygon** | 0.376 |
| 4 | Lacul Sfânta Ana | `Lacul Sfanta Ana` | ✓ | way (lake) | **Polygon** | 0.423 |
| 5 | Lacul Snagov | `Lacul Snagov` | ✓ | relation (lake) | **Polygon** | 0.377 |
| 6 | Lacul Razim | `Lacul Razim` | ✓ | relation (lake) | **Polygon** | 0.133 |
| 7 | Lacul Sinoe | `Lacul Sinoe` | ✓ | relation (lake) | **Polygon** | 0.133 |
| 8 | Lacul Techirghiol | `Lacul Techirghiol` | ✓ | relation (lake) | **Polygon** | 0.379 |
| 9 | Lacul Siutghiol | `Lacul Siutghiol` | ✓ | relation (lake) | **Polygon** | 0.133 |
| 10 | Lacul Bucura | `Lacul Bucura` | ✓ | way (lake) | **Polygon** | 0.372 |
| 11 | Lacul Bâlea | `Lacul Bâlea` | ✓ | way (lake) | **Polygon** | — |

### Lake Summary

| Status | Count | Details |
|--------|-------|---------|
| **Direct match** | 11/11 | 100% success rate |
| **Omission** | 0 | Every lake query returned the correct body |
| **Geometry type** | Polygon | All lakes return area polygons (usable for display) |
| **Diacritics** | Tolerant | "Rosu" → "Roșu", "Sfanta Ana" → "Sfânta Ana" all work |
| **Name variants** | Minor | "Lacul Bicaz" → official name "Lacul Izvorul Muntelui" |

---

## 4. Diacritic Sensitivity Analysis

| Query Type | Behavior | Example |
|-----------|----------|---------|
| With diacritics (Ș, Ț, Ă, Â, Î) | Matches directly | `Mureș` → Mureș river |
| Without diacritics | Nominatim normalizes and matches | `Mures` → Mureș river |
| Added context helps | `Bistrita river Romania` disambiguates from city | City Bistrița vs River Bistrița |
| Romanian prefix "Râul" | Does NOT help | `Râul Siret` → no results; use just `Siret` |
| Suffix "river"/"Romania" | Helps disambiguation | `Mures river Romania` → clean river match |

**Recommendation:** Query without diacritics but add `, Romania` or `river` suffix for disambiguation. Don't prefix with "Râul".

---

## 5. Transnational River Handling

The **Danube/Dunărea** is a special case:
- The Danube OSM relation spans 10 countries
- Querying `Dunărea` with `countrycodes=ro` **fails** because the relation's country is not exclusively Romania
- Workaround: query `Danube` **without** `countrycodes` filter, then filter results by bounding box intersection with Romania
- Alternative: use Overpass API to extract the Romanian segment specifically

The **Prut** (border river with Moldova/Ukraine) works fine with `countrycodes=ro` — OSM apparently tags border rivers to both countries.

---

## 6. Criș River System Handling

The "Criș" is not a single river in OSM but a system of tributaries:
- **Crișul Repede** (main northern branch)
- **Crișul Alb** (middle branch, Hungarian name "Fehér-Körös")
- **Crișul Negru** (southern branch)

To represent "Criș" in a batch pipeline, query all three tributaries and either display separately or compute a combined extent.

---

## 7. Geometry Quality

| Feature | River Relations | Lake Ways/Relations |
|---------|----------------|-------------------|
| **Type** | MultiLineString | Polygon |
| **Detail level** | High — hundreds/thousands of coordinate pairs | Good — detailed shoreline |
| **Suitability for display** | ✓ Polylines | ✓ Filled areas |
| **Suitability for spatial queries** | ✓ (point-in-buffer, length) | ✓ (point-in-polygon, area) |
| **Coarse bbox** | Available via `boundingbox` field | Same |

---

## 8. Suitability Verdict

### As Primary Batch Geocoder: **YES, with caveats**

| Aspect | Rating | Detail |
|--------|--------|--------|
| **Coverage** | ★★★★☆ | 8/10 rivers direct match; 2 need name variants. 11/11 lakes perfect |
| **Geometry quality** | ★★★★★ | MultiLineString for rivers, Polygon for lakes — both directly usable |
| **Diacritic robustness** | ★★★★★ | Works with and without Romanian diacritics |
| **Ambiguity handling** | ★★★☆☆ | "Criș", "Bistrița", "Olt" return non-water results; need disambiguation |
| **Transnational features** | ★★☆☆☆ | Danube requires special handling (no RO country filter) |
| **API ease of use** | ★★★★★ | Simple REST API, JSON output, polygon geometry included |
| **Rate limit adequacy** | ★★★★☆ | 1 req/sec = ~60 queries/min; batch of 100 water bodies ≈ 2 min |

### Pipeline Design Recommendations

1. **Query format:** `https://nominatim.openstreetmap.org/search?q={name}&format=jsonv2&polygon_geojson=1&countrycodes=ro&limit=3`
2. **Rate limit:** 1-second delay between requests
3. **Result filtering:** Keep only results with `category=waterway` and `type=river` (for rivers) or `type=lake` (for lakes)
4. **Fallback for Danube:** Query `Danube` without country filter, post-filter by bounding box intersection with Romanian territory
5. **Criș handling:** Query all three: "Crișul Repede", "Crișul Alb", "Crișul Negru"
6. **Name normalization:** Strip "Râul" prefix; query bare river name + optional "Romania" suffix
7. **Caching:** Store results by query string in a local JSON file or SQLite DB
8. **No code approach:** This can be done with ~20 curl commands and manual filtering, but for 100+ water bodies, a script is justified

---

## 9. Reference: API Call Template

```
curl -s -A "MyAppName/1.0" \
  "https://nominatim.openstreetmap.org/search?\
q=Siret&format=jsonv2&polygon_geojson=1&countrycodes=ro&limit=3"
```

Response fields of interest:
- `name` — canonical OSM name
- `display_name` — full address string
- `category` — "waterway" (rivers) or "water" (lakes)
- `type` — "river" or "lake"
- `osm_type` — "relation" (preferred) or "way"
- `geojson` — MultiLineString (rivers) or Polygon (lakes)
- `boundingbox` — [south, north, west, east]
- `importance` — 0–1 ranking score
- `addresstype` — "river" or "lake"

---

*End of evaluation. No code was written. These notes are sufficient for synthesis into a batch geocoding pipeline design.*
