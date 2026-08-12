# Bbox-rectangle waters fix — report (t_33533bc7)

Date: 2026-08-12

## Problem

Map views around Făgăraș (left) and Rupea (right) showed blue RECTANGULAR
highlight boxes instead of river lines — waters rendered with the bbox
fallback (`src/utils/geo.ts` `waterToGeoJSON`) because they had a bbox but no
real OSM geometry.

Two rectangle classes were fixed:
- **bbox-no-geom** — `bbox` present, `geometry` missing (132 waters)
- **rect-poly** — `geometry` is a degenerate 4-corner bbox Polygon (94 waters)

Total blue rectangles found: **226**.

## Result

| Class | Total | Geometry attached | Documented no-match |
|---|---|---|---|
| bbox-no-geom | 132 | 96 | 36 |
| rect-poly | 94 | 74 | 20 |
| **Total** | **226** | **170 (75%)** | **56 (25%)** |

waters.json: 1014 waters, **644 with geometry** (was 543 before this fix;
the 170 new attachments). Reported Făgăraș/Rupea area: 39 waters in the
window, 35 now carry real geometry — only two small unnamed Sibiu streams
(Pârâul Nou Roman, Pârâul Râul Vadului) remain bbox-rendered, and both are
absent from OSM under any name (verified against the full OSM index).

## Matching strategy (`scripts/fix_bbox_waters.py`)

1. **Rivers (subtype=rau)**: conservative ladder from `audit_missing_rivers.py`
   (`best_osm_match` + `try_manual_override`) against `data/rivers_osm.geojson`
   (6396 name clusters), plus curated `RIVER_OVERRIDES`, then HOTOSM named
   lines, then lake polygons for rect-poly rivers that are really small
   reservoirs (Dopca).
2. **Lakes (subtype=lac)**: HOTOSM `waterways.geojson` named polygons +
   `data/processed/overpass_named_lakes.json` (3464 named polygons extracted
   from the 2.9M-element Overpass water dump) matched by normalized name +
   anchor distance; curated `LAKE_OVERRIDES` for known pairs; and a NEW
   **unnamed-reservoir fallback** (`load_unnamed_reservoirs` +
   `match_lake_unnamed`): OSM draws many reservoir outlines as closed ways
   with no name tag (water=reservoir) — 2262 such unnamed polygons from the
   Overpass dump, position-matched to the water's anchor (≤2 km). This fixed
   12 reservoirs (Căpâlna, Petrești, Cerbureni, Curtea de Argeș, Zigoneni,
   Negreni, Sălățig, Chișineu-Criș, Copilul, Zăvoiul Orbului, Ostrov,
   Topolovățul).
3. **Cluster re-pick** (`pick_cluster_by_bbox`): `best_osm_match` ranks OSM
   clusters by county-centroid proximity, which could pick the WRONG cluster
   of a multi-cluster river (Râul Cibinul Inferior got the east-Cibin cluster
   20 km away) or a tiny node fragment (Teleajen). After the name match, the
   cluster whose extent best overlaps the water's own bbox wins.
4. **Dam-vs-reservoir tiebreak**: `match_lake` now prefers real water polygons
   over dam-structure polygons before distance — `Barajul Măneciu` (0.29 km,
   tiny wall) no longer beats `Lacul Măneciu` (0.83 km, real reservoir);
   same fix for Beliș-Fântânele.
5. **Far-cluster rejection**: a same-name cluster with zero bbox overlap and
   >15 km gap is a DIFFERENT river in another county and is rejected
   (`Râul Geoagiu Superior` Alba vs OSM Geoagiu in Hunedoara, 21 km).

## Documented no-match reasons (56)

- `no-osm-match` (27 rivers): stream not in OSM under any name — Bihor
  mountain valleys (Valea Buduresei, Omului, Șoimului, Ierului, Gepiș...),
  Alba Valea Bistrei ×2, Râul Holod, Râul Volovăț, Râul Vorona, Râul Jilț,
  Râul Potop, Râul Valea Ilvei, Râul Tărcăița, Valea Lonei, Valea Vadului,
  Râul Izvorul Lotrului, Râul Râmești, Râul Grotului, Pârâul Lesuntu,
  Pârâul Nou Roman, Pârâul Râul Vadului + 2 Bistrița-Năsăud rect-polys
  (Izvoare–Bumbului, Jelna) + Gârla Huțani + Canalul Cefa IV + Culișer.
- `no-lake-polygon` (22 lakes): reservoir not present as any polygon in the
  OSM extract (HOTOSM + Overpass) — Alba Căpâlna/Petrești now fixed via
  unnamed fallback; remaining: Arad Balta Căpâlnaș, Balta Ghilin I/II,
  Lac Mișca, Lac Pâncota, Lac Zădăreni, Lac Copilul (fixed), Bacău Galbeni/
  Gârleni/Lilieci, Bistrița-Năsăud Lacul Izvorul (Măgurii), Botoșani
  Acumularea Negreni (fixed), Caraș-Severin Dognecea (dam-only), Dolj
  Cilieni (fixed), Neamț Pangrati/Reconstrucția, Suceava Pojorâta, Timiș
  Satchinez/Lățunaș, Vâlcea Cornetu/Câineni/Ionești/Robești/Gura Lotrului,
  Dâmbovița Zăvoiul Orbului (fixed), Sălaj Sălățig (fixed).
- `dam-only-tiny` (6): only the dam WALL polygon exists in OSM (tiny) —
  Drăgășani, Turnu, Izbiceni, Râușor, Dognecea Mare, Dognecea Mică. Attaching
  a 100 m dam wall would make the reservoir vanish; bbox fallback kept.
- `far-cluster-reject` (1): Râul Geoagiu Superior (Alba) — the only OSM
  "Geoagiu" is the Hunedoara river 21 km away; no Alba Geoagiu in extract.

## Files changed

- `scripts/fix_bbox_waters.py` — all matcher improvements (unnamed-reservoir
  fallback, cluster re-pick, dam tiebreak, far-cluster rejection, overpass
  named-lake merge, LAKE/RIVER override additions)
- `public/data/waters.json` — 170 waters now carry real geometry
- `data/processed/overpass_named_lakes.json` — named-lake extract from the
  Overpass dump (used by the fixer)
- `data/raw/overpass_reservoir_fetch.json` — reservoir fetch used by fixer
- QA scripts: `scripts/_qa_final.py`, `scripts/_qa_bbox_overlap.py`,
  `scripts/_qa_match_dist.py`, `scripts/_inspect_far.py`

## Verification

- QA script mirrors the exact fixer logic over all 226 rects: 170 attach
  geometry; remaining far matches are either full-course rivers that overlap
  the sector bbox (Prahova, Târgului, Doamnei, Teleajen — same river, longer
  course) or documented overrides (Arpașu 21.7 km geocode offset, Topa 16 km).
- Reported Făgăraș/Rupea window: 39 waters → 35 with geometry, 2 documented
  (Pârâul Nou Roman, Pârâul Râul Vadului), all mountain lakes at 0.0–0.1 km
  anchor distance.
