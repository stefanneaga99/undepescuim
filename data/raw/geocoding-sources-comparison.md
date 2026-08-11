# Alternative Geocoding Sources for Romanian Waters — Comparison

Evaluated: 2026-08-11

## Task Context
Goal: identify non-Nominatim geocoding and geometry sources for Romanian rivers and lakes. Each source is evaluated for data access method, license, rate limits, geometry support (point vs polyline/polygon), coverage of Romanian river/lake names, and suitability as a Nominatim complement or for pre-mapping the 10 biggest rivers.

---

## Summary Table

| Source | Access | License | Geometry | Rate Limits | Name Coverage (RO) | Recommendation |
|---|---|---|---|---|---|---|
| **Overpass API (OSM)** | HTTP API, free | ODbL | ✅ Polylines, polygons | Dynamic slot-based; 429 on overload | Strong — 3,768 named "river" ways; ~80K linestrings total | **YES** — best polyline source |
| **HOTOSM Waterways (HDX)** | File download (GPKG, SHP, GeoJSON) | ODbL | ✅ Polylines, polygons | None (static download, updated monthly) | Strong — same OSM data, 17.8% named | **YES** — best for batch pre-mapping |
| **GeoNames** | HTTP API / full DB dump | CC-BY 4.0 | ❌ Points only (lat/lng) | 10K/day free, 1K/hr | 1,159 streams + 317 lakes = 2,570 H-class features | **MAYBE** — good for name lookup, no geometry |
| **ANCPI TOPRO5 Hydrography** | INSPIRE WFS / ArcGIS Hub | Romanian Open Data (INSPIRE) | ✅ Polylines (rivers), polygons (lakes) | Unknown — likely generous for open data | Official Romanian names; national coverage | **YES** — authoritative source |
| **ANCPI River Basin Districts** | INSPIRE WFS | Romanian Open Data | ✅ Polygons (basins) | Unknown | Danube basin + sub-basins | **MAYBE** — supplementary context only |
| **Natural Earth (rivers)** | File download (SHP) | Public Domain | ✅ Polylines (centerlines) | None (static) | Major rivers only (1:10m scale); includes names | **MAYBE** — good for biggest rivers, not detailed |
| **Natural Earth Europe Supplement** | File download (SHP) | Public Domain | ✅ Polylines | None (static) | 4x more features than base; derived from CCM/JRC | **YES** — great for mid-scale river detail |
| **Google Geocoding API** | HTTP API | Proprietary (ToS) | ❌ Points only | $200/mo free = ~40K geocodes; 3K QPM | Good for named water bodies as place results | **NO** — no polyline geometry, not free at scale |
| **Esri ArcGIS Geocoding** | HTTP API | Proprietary | ❌ Points only | 20K free, then $0.50/1K | Comparable to Google, general-purpose | **NO** — same limits as Google, no polyline |
| **HERE Geocoding** | HTTP API | Proprietary | ❌ Points only | 30K/month free | General-purpose, no water-specific geometry | **NO** — no polyline geometry |
| **DanubeGIS (ICPDR)** | Web map / likely downloadable | Public | ✅ Polylines (Danube + tributaries) | N/A | Danube + major tributaries | **MAYBE** — niche, Danube-only |
| **CCM River Database (JRC)** | File download | Non-commercial (upstream of Natural Earth) | ✅ Polylines | None (static) | Full European river network at 100m resolution | **YES** — if non-commercial license acceptable |

---

## Detailed Notes

### 1. Overpass API over OSM
- **Access**: `https://overpass-api.de/api/interpreter` — POST queries in Overpass QL
- **Query example for Romanian rivers**: `area["ISO3166-1"="RO"]->.a; way["waterway"="river"](area.a); out geom;`
- **Geometry**: Returns full WGS84 coordinates for every way node — polylines for rivers, polygons for lakes
- **License**: ODbL (requires attribution to OpenStreetMap contributors)
- **Rate limits**: Dynamic, slot-based per IP. Heavy usage may be throttled; for bulk extraction prefer planet dumps
- **Names**: Romanian river names in `name` / `name:ro` tags. Coverage map: urban/central areas well-mapped, remote Carpathian valleys sparser
- **Complement to Nominatim**: YES. Overpass is the same OSM database but returns raw geometry, while Nominatim returns point centroids. Use Overpass for polylines, Nominatim for search/geocoding
- **Pre-mapping 10 biggest rivers**: Strong candidate — query by river name, get complete polyline

### 2. HOTOSM Waterways of Romania (HDX)
- **Access**: Direct download from https://data.humdata.org/dataset/hotosm_rou_waterways
- **Files**: GPKG (43 MB), SHP (41.6 MB), GeoJSON (30.6 MB), KML (29.7 MB)
- **Content**: 98,713 features total — 79,672 LINESTRING (80.7%), 18,360 POLYGON (18.6%), 628 POINT (0.6%)
- **Breakdown by waterway type**: stream 47,025, drain 11,288, ditch 10,212, canal 6,783, **river 3,768**
- **Names**: 17.8% of features have name; 7,081 distinct names. Has `name_ro` column (Romanian names: 304 values, e.g. Dunărea, Prut, Târnava Mare)
- **Update frequency**: Monthly (latest snapshot: 2026-08-07)
- **License**: ODbL (same as OSM)
- **Complement to Nominatim**: YES. Pre-packaged, consistent snapshot — no API rate limits. Filterable by waterway type, admin region
- **Pre-mapping 10 biggest rivers**: Ideal — download once, filter for `waterway=river`, sort by length/importance

### 3. GeoNames
- **Access**: Web services at api.geonames.org, or full DB dump from download.geonames.org
- **Romania H-class features**: 2,570 total — 1,159 streams, 317 lakes, 248 intermittent streams, 45 reservoirs, 28 canals
- **Geometry**: Points only (single lat/lng centroid per feature). No polyline or polygon support
- **License**: CC-BY 4.0 — free, commercial use allowed with attribution
- **Rate limits**: 10,000 credits/day, 1,000/hour (free tier). Premium available
- **Name quality**: Romanian names present (from multiple aggregated sources), but no `name_ro` separate column in the dump
- **Complement to Nominatim**: PARTIALLY. Good for cross-referencing river/lake name existence and alternate names. Cannot provide geometry. Use for name validation, not mapping
- **Pre-mapping 10 biggest rivers**: No — points only, not useful for polyline mapping

### 4. ANCPI (Romanian Cadastre Agency) — TOPRO5 Hydrography
- **Access**: Via INSPIRE WFS services or ArcGIS Hub. Dataset: "Hydrography TOPRO5" — hydrographic network of rivers and lakes
- **Issued**: 2012-12-09
- **Geometry**: Polylines for rivers, polygons for lakes. Official national mapping at 1:5,000 scale
- **License**: Romanian open data (INSPIRE directive) — free for any use, attribution typically required
- **Rate limits**: WFS service — likely generous; INSPIRE mandates open access
- **Name coverage**: Official Romanian river and lake names, authoritative
- **Additional ANCPI datasets**: "River basin districts" (Danube basin + sub-basins, 2017), "Lakes" (natural + reservoir), "Digs" (embankment arrangements)
- **Complement to Nominatim**: YES. Authoritative official source. Can fill gaps where OSM coverage is sparse. Excellent for verifying/correcting Nominatim results
- **Pre-mapping 10 biggest rivers**: Strong candidate — official hydrographic network at detailed scale

### 5. Natural Earth
- **Access**: ne_10m_rivers_lake_centerlines.zip (1.98 MB) + ne_10m_rivers_europe.zip (585 KB supplement)
- **Scale**: 1:10 million — suitable for small-scale maps
- **Europe supplement**: 4x more river features than base, derived from CCM Database 2.1 (JRC). Includes Romania
- **Geometry**: Polyline centerlines. Named, with scale ranks and line width attributes for tapered rendering
- **License**: Public Domain — no restrictions
- **Name coverage**: Major rivers named. Base set has fewer names; Europe supplement adds CCM-derived names. Not comprehensive for small Romanian rivers
- **Complement to Nominatim**: PARTIALLY. Excellent for the biggest 10-20 rivers (Danube, Mureș, Olt, Prut, Siret, Târnava, etc.). Not detailed enough for smaller streams
- **Pre-mapping 10 biggest rivers**: YES — good fit. Public domain, named, pre-generalized centerlines

### 6. Google / Esri / HERE Geocoding APIs
- **All three**: Proprietary, point-only geometry (lat/lng centroid), no river polylines
- **Google**: $200/mo free credit ≈ 40K geocodes. 3,000 QPM rate limit. Good for "Dunărea River" → point. No polyline
- **Esri ArcGIS**: 20K free geocodes, then $0.50/1K. Similar to Google
- **HERE**: 30K free/month. Also point-only
- **Verdict**: None provide water polyline geometry. Not suitable for river mapping. Only useful as fallback geocoders for place/address lookup, not water geometry

### 7. DanubeGIS (ICPDR)
- **Access**: https://www.danubegis.org/maps — public web GIS for the Danube River Basin
- **Coverage**: Danube main stem + major tributaries across 14 countries including Romania
- **Data**: Hydrography, water quality, flood risk, navigation
- **License**: Public access; terms need verification for extraction
- **Usefulness**: Niche — only covers the Danube basin. Useful if the project focuses specifically on Danube-adjacent waters
- **Pre-mapping**: Only for Danube and its immediate major tributaries (Siret, Prut, Olt, Argeș)

### 8. CCM River and Catchment Database (JRC)
- **Access**: http://ccm.jrc.ec.europa.eu — European Commission Joint Research Centre
- **Resolution**: 100m, topologically consistent river network for all of Europe
- **Geometry**: Polylines. Romania fully covered
- **License**: Non-commercial use for the original 100m data. Natural Earth's derived version is public domain
- **Coverage**: Complete European river network with Strahler order, names, catchment attribution
- **Pre-mapping**: Excellent if the non-commercial license is acceptable. Natural Earth Europe supplement is the public-domain derived alternative

---

## Recommendations

### For complementing Nominatim (search/geocoding):
| Source | Verdict |
|---|---|
| Overpass API | **YES** — same OSM data, different access pattern (geometry-first) |
| GeoNames | **MAYBE** — good for name cross-referencing, no geometry |
| ANCPI TOPRO5 | **YES** — authoritative Romanian names, fills OSM gaps |

### For polyline pre-mapping of 10 biggest rivers:
| Source | Verdict |
|---|---|
| HOTOSM Waterways HDX | **YES** — download once, filter for rivers, ready geometry |
| Overpass API (on-demand) | **YES** — query specific rivers by name, get full polylines |
| Natural Earth + Europe suppl. | **YES** — public domain, pre-generalized, named |
| ANCPI TOPRO5 Hydrography | **YES** — authoritative official data |
| CCM (JRC) | **MAYBE** — best resolution but non-commercial upstream |

### Recommended Mix
1. **Primary geometry**: HOTOSM HDX download (batch) + Overpass API (spot queries)
2. **Official validation**: ANCPI TOPRO5 — cross-check names and coverage
3. **Public-domain fallback**: Natural Earth Europe supplement — for the biggest rivers
4. **Name reference**: GeoNames — verify river/lake name existence and alternate names
