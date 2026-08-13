#!/usr/bin/env python3
"""Build public/data/uncontracted_rivers.json — every NAMED OSM river that is
NOT already contracted in public/data/waters.json (t_471dad64).

Inputs:
  data/cache/osm_river_clusters.pkl  (built by audit_regions.build_clusters —
    now carries raw_name; rebuild with `--reload-clusters` if missing/stale)
  public/data/waters.json            (contracted waters; matched clusters excluded)

Output:
  public/data/uncontracted_rivers.json — compact Water-shaped array:
    slug, name, judet, type, subtype, coordinates, bbox, geometry
    (LineString/MultiLineString, Douglas-Peucker-simplified ~200 m + coords
    rounded to 5 decimals), uncontracted: true, lengthKm.

The bulk 320 MB data/rivers_osm.geojson is never served raw; this file is
the compact per-river subset the FE loads as a separate overlay layer.

Usage:
  python3 scripts/build_uncontracted_rivers.py [--reload-clusters]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_missing_rivers import build_county_centroids, norm  # noqa: E402
from audit_regions import build_clusters  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
OUT_FILE = ROOT / "public" / "data" / "uncontracted_rivers.json"
OSM_INDEX_CACHE = ROOT / "data" / "cache" / "osm_river_clusters.pkl"

# Douglas-Peucker tolerance in degrees (~200 m) — invisible at the zoom levels
# the overlay is drawn at, but cuts the point count by ~10x.
SIMPLIFY_TOL_DEG = 0.002
# round coords to 5 decimals (~1 m) to save bytes
COORD_ROUND = 5

# Feature length (km) below which a river is dropped entirely (too tiny to be
# useful on the map; keeps the file compact).
MIN_LENGTH_KM = 0.5

# Duplicate-of-contracted test (t_0ca43d1a): a cluster whose course lies
# (near-)entirely on an already-contracted water's geometry is a DUPLICATE of
# that contract — an OSM way or name variant the name matcher cannot tie to the
# water ('Siriu' vs 'Râul Siriul', 'Maros' vs 'Mureș', 'Lăpușnicu Mic' vs
# 'Lăpușnicul Mic'). It must NOT appear in the teal overlay, or it draws a
# second teal stream on top of the contracted blue course (user report:
# duplicate 'Siriu' near Gura Siriului).
DUP_EPS_DEG = 0.0008  # ~90 m
# fraction of sampled cluster points that must lie within DUP_EPS_DEG of the
# contracted course for the cluster to be considered a duplicate
DUP_MIN_FRAC = 0.9
# PARTIAL-overlap trim (t_f4ff3853): a contiguous run of a cluster's points
# lying on a contracted course is cut out only when its length exceeds this
# (haversine km). Genuine tributaries touch the contracted river in a short
# confluence zone (< 2 km); a run this long IS the contracted course.
TRIM_MIN_RUN_KM = 2.0


def duplicate_of_contracted(cluster: dict, water_geoms: list) -> str | None:
    """Return the slug of a contracted water whose course CONTAINS this
    cluster's geometry (within DUP_EPS_DEG), else None.

    Both endpoints must also lie on the course: a genuine tributary touches
    the contracted river only at its mouth and fails that check, so it stays
    in the overlay.
    """
    from shapely.geometry import LineString, MultiLineString, Point

    geom = cluster["geom"]
    if geom["type"] == "LineString":
        course = LineString(geom["coordinates"])
    else:
        course = MultiLineString(geom["coordinates"])
    if course.geom_type == "LineString":
        coords = list(course.coords)
    else:
        coords = [c for part in course.geoms for c in part.coords]
    if len(coords) < 2:
        return None
    bx0, by0, bx1, by1 = cluster["bbox"]
    x0, y0, x1, y1 = (bx0 - DUP_EPS_DEG, by0 - DUP_EPS_DEG,
                      bx1 + DUP_EPS_DEG, by1 + DUP_EPS_DEG)
    sample = [Point(c) for c in coords[:: max(1, len(coords) // 40)]]
    first, last = Point(coords[0]), Point(coords[-1])
    for slug, wb, wmls in water_geoms:
        if not (wb[0] - DUP_EPS_DEG <= x1 and wb[2] + DUP_EPS_DEG >= x0 and
                wb[1] - DUP_EPS_DEG <= y1 and wb[3] + DUP_EPS_DEG >= y0):
            continue
        near = sum(1 for p in sample if wmls.distance(p) <= DUP_EPS_DEG)
        if near / len(sample) >= DUP_MIN_FRAC:
            if (wmls.distance(first) <= DUP_EPS_DEG and
                    wmls.distance(last) <= DUP_EPS_DEG):
                return slug
    return None


def _near_flags(part: list, water_geoms: list, eps: float) -> list:
    """Boolean per point: lies within eps of ANY contracted course."""
    from shapely.geometry import Point

    near = []
    for lon, lat in part:
        is_near = False
        for _slug, wb, wmls in water_geoms:
            if not (wb[0] - eps <= lon <= wb[2] + eps and
                    wb[1] - eps <= lat <= wb[3] + eps):
                continue
            if wmls.distance(Point(lon, lat)) <= eps:
                is_near = True
                break
        near.append(is_near)
    return near


def trim_contracted_runs(geom: dict, water_geoms: list,
                         eps: float = DUP_EPS_DEG) -> dict | None:
    """Cut out any STRETCH of a cluster that lies on a contracted water's
    course — the PARTIAL-overlap duplicate class (t_f4ff3853: the Prahova
    'Doftana' cluster whose UPPER course is the Romsilva '4 Doftana
    Superioara' contract while its LOWER course is genuinely uncontracted).

    Whole-cluster tests (duplicate_of_contracted) can't catch these: the
    overlapping part is diluted by the uncontracted parts (frac ~0.1), so the
    cluster survives and draws a teal copy over a blue contracted stretch.

    A contiguous run of points within eps of a contracted course is removed
    ONLY when it is long enough (>= TRIM_MIN_RUN_KM) to BE the contracted
    course; short confluence-zone touches are kept so genuine tributaries
    don't lose their mouth. Parts are deduped by their FULL rounded
    coordinate sequence (the OSM extract maps some ways twice) — NOT by
    endpoints, which would collapse different braids sharing the same
    endpoints (e.g. the Lom).

    Returns a NEW geometry dict (LineString/MultiLineString of the remaining
    stretches) or None when nothing uncontracted remains.
    """
    from shapely.geometry import Point

    parts = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
    # Fast path: if NO part has a long enough run on a contracted course, the
    # cluster is untouched (dedupe would otherwise alter unrelated rivers'
    # geometry — e.g. foreign 'Лом' parts that merely repeat). Only clusters
    # with a real partial-overlap get deduped + cut.
    has_long_run = False
    for part in parts:
        if len(part) < 2:
            continue
        near = _near_flags(part, water_geoms, eps)
        i = 0
        n = len(part)
        while i < n:
            if near[i]:
                j = i
                while j < n and near[j]:
                    j += 1
                run_len_km = sum(
                    haversine_km(part[k], part[k + 1]) for k in range(i, j - 1)
                )
                if run_len_km >= TRIM_MIN_RUN_KM:
                    has_long_run = True
                    break
                i = j
            else:
                i += 1
        if has_long_run:
            break
    if not has_long_run:
        return geom

    out_parts = []
    seen = set()
    for part in parts:
        if len(part) < 2:
            continue
        key = tuple(round(c, 5) for p in part for c in p)
        if key in seen:
            continue
        seen.add(key)
        # point -> is it near ANY contracted course?
        near = _near_flags(part, water_geoms, eps)
        # split into maximal runs; drop only LONG near-runs, keep short
        # (confluence-zone) near-runs INLINE so a tributary's mouth point is
        # not isolated and dropped
        n = len(part)
        kept = []
        cur = []
        i = 0
        while i < n:
            if near[i]:
                j = i
                while j < n and near[j]:
                    j += 1
                # cumulative along-course length of the run (chord would
                # under-measure a winding overlap)
                run_len_km = sum(
                    haversine_km(part[k], part[k + 1]) for k in range(i, j - 1)
                )
                if run_len_km >= TRIM_MIN_RUN_KM:
                    # long overlap IS the contracted course — cut it out,
                    # closing the current kept segment at the run start
                    if len(cur) >= 2:
                        kept.append(cur)
                    cur = []
                else:
                    # short confluence touch — keep the points inline
                    cur.extend(part[i:j])
                i = j
            else:
                cur.append(part[i])
                i += 1
        if len(cur) >= 2:
            kept.append(cur)
        for seg in kept:
            if len(seg) >= 2:
                out_parts.append(seg)
    if not out_parts:
        return None
    if len(out_parts) == 1:
        return {"type": "LineString", "coordinates": out_parts[0]}
    # Chain the remaining stretches by endpoint connectivity into ONE ordered
    # LineString when they form a single course (the trimmed Doftana lower
    # course). A single LineString makes the FE's PCA orderParts a no-op and
    # keeps line_length (concatenated coords) honest.
    chain = chain_parts_by_connectivity(out_parts)
    if len(chain) == 1:
        return {"type": "LineString", "coordinates": chain[0]}
    return {"type": "MultiLineString", "coordinates": chain}


def chain_parts_by_connectivity(parts: list) -> list:
    """Grow chains from parts that share junction points (within 1e-5 deg).
    Returns a list of chained coordinate lists (each a single LineString)."""
    parts = [list(p) for p in parts]
    used = [False] * len(parts)

    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    chains = []
    for i in range(len(parts)):
        if used[i]:
            continue
        used[i] = True
        chain = list(parts[i])
        # grow forward
        changed = True
        while changed:
            changed = False
            for j in range(len(parts)):
                if used[j]:
                    continue
                if dist(chain[-1], parts[j][0]) <= 1e-5:
                    chain.extend(parts[j][1:])
                    used[j] = True
                    changed = True
                elif dist(chain[-1], parts[j][-1]) <= 1e-5:
                    chain.extend(reversed(parts[j][:-1]))
                    used[j] = True
                    changed = True
        # grow backward
        changed = True
        while changed:
            changed = False
            for j in range(len(parts)):
                if used[j]:
                    continue
                if dist(chain[0], parts[j][-1]) <= 1e-5:
                    chain = list(parts[j][:-1]) + chain
                    used[j] = True
                    changed = True
                elif dist(chain[0], parts[j][0]) <= 1e-5:
                    chain = list(reversed(parts[j][1:])) + chain
                    used[j] = True
                    changed = True
        chains.append(chain)
    return chains


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    R = 6371.0
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def line_length(coords: list) -> float:
    return sum(haversine_km(coords[i - 1], coords[i]) for i in range(1, len(coords)))


def simplify_geometry(geom: dict, tol: float, rnd: int) -> dict | None:
    """Simplify a LineString/MultiLineString, round coords, drop degenerate parts.

    Returns None when nothing usable remains (after min-length filtering).
    """
    from shapely.geometry import LineString, MultiLineString

    def clean(coords: list) -> list:
        out = []
        for lon, lat in coords:
            p = (round(lon, rnd), round(lat, rnd))
            if not out or p != out[-1]:
                out.append(p)
        return out

    if geom["type"] == "LineString":
        ls = LineString(geom["coordinates"]).simplify(tol, preserve_topology=False)
        coords = clean(list(ls.coords))
        if len(coords) < 2:
            return None
        return {"type": "LineString", "coordinates": coords}

    parts = []
    for part in geom["coordinates"]:
        ls = LineString(part).simplify(tol, preserve_topology=False)
        coords = clean(list(ls.coords))
        if len(coords) >= 2:
            parts.append(coords)
    if not parts:
        return None
    if len(parts) == 1:
        return {"type": "LineString", "coordinates": parts[0]}
    return {"type": "MultiLineString", "coordinates": parts}


def approx_county(cluster: dict, county_centroids: dict) -> str:
    bbox = cluster["bbox"]
    cpt = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    best, bd = "", 1e9
    for j, cc in county_centroids.items():
        d = (cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2
        if d < bd:
            bd, best = d, j
    return best or "?"


# slug (county-boundary cache filename) -> canonical county name (as shown on
# the card / used by the county filter). Matches waters.json conventions.
COUNTY_SLUG_TO_NAME = {
    "alba": "Alba", "arad": "Arad", "arges": "Argeș", "bacau": "Bacău",
    "bihor": "Bihor", "bistrita_nasaud": "Bistrița-Năsăud", "botosani": "Botoșani",
    "brasov": "Brașov", "braila": "Brăila", "buzau": "Buzău",
    "caras_severin": "Caraș-Severin", "calarasi": "Călărași", "cluj": "Cluj",
    "constanta": "Constanța", "covasna": "Covasna", "dambovita": "Dâmbovița",
    "dolj": "Dolj", "galati": "Galați", "giurgiu": "Giurgiu", "gorj": "Gorj",
    "harghita": "Harghita", "hunedoara": "Hunedoara", "ialomita": "Ialomița",
    "iasi": "Iași", "ilfov": "Ilfov", "maramures": "Maramureș",
    "mehedinti": "Mehedinți", "mures": "Mureș", "neamt": "Neamț", "olt": "Olt",
    "prahova": "Prahova", "satu_mare": "Satu Mare", "salaj": "Sălaj",
    "satu mare": "Satu Mare",  # slugify() keeps the space — legacy cache name
    "sibiu": "Sibiu", "suceava": "Suceava", "teleorman": "Teleorman",
    "timis": "Timiș", "tulcea": "Tulcea", "vaslui": "Vaslui",
    "valcea": "Vâlcea", "vrancea": "Vrancea", "bucuresti": "București",
}


def load_county_polygons() -> list[tuple[str, object, tuple[float, float, float, float]]]:
    """[(name, shapely geometry, bbox)] from data/raw/county_boundaries/*.json."""
    from shapely.geometry import shape
    polys = []
    for path in sorted((ROOT / "data/raw/county_boundaries").glob("*.json")):
        name = COUNTY_SLUG_TO_NAME.get(path.stem)
        if not name:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        g = data[0].get("geojson") if isinstance(data, list) else data.get("geojson")
        if not g:
            continue
        try:
            geom = shape(g)
        except Exception:
            continue
        bbox = geom.bounds
        polys.append((name, geom, bbox))
    return polys


def assign_county(
    coords: list[tuple[float, float]],
    polygons: list[tuple[str, object, tuple[float, float, float, float]]],
    fallback: dict[str, tuple[float, float]],
) -> tuple[str, int]:
    """County whose polygon contains the most sample points along the course.

    Returns (county, total_hits). total_hits == 0 means the river is entirely
    OUTSIDE Romania (the bulk OSM extract includes foreign border rivers:
    Dniester/Nistru, Hungarian Tisza, Ukrainian/Hungarian/Serbian streams) —
    callers should drop those; a majority-county is meaningless there.
    """
    from shapely.geometry import Point
    from shapely.prepared import prep

    sample = coords[:: max(1, len(coords) // 40)]  # ≤ 41 sample points
    prepared = [(name, prep(geom), bbox) for name, geom, bbox in polygons]
    counts: dict[str, int] = {}
    for lon, lat in sample:
        pt = Point(lon, lat)
        best = None
        for name, pgeom, pbbox in prepared:
            if not (pbbox[0] <= lon <= pbbox[2] and pbbox[1] <= lat <= pbbox[3]):
                continue
            if pgeom.contains(pt):
                best = name
                break  # counties are disjoint; first bbox hit is fine
        if best:
            counts[best] = counts.get(best, 0) + 1
    total = sum(counts.values())
    if counts:
        return max(counts, key=lambda k: (counts[k], k)), total
    # fallback: nearest county centroid (used only for display of foreign rivers
    # that slip through; callers normally drop total_hits == 0 entries).
    cpt = (sum(p[0] for p in sample) / len(sample), sum(p[1] for p in sample) / len(sample))
    best, bd = "", 1e9
    for j, cc in fallback.items():
        d = (cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2
        if d < bd:
            bd, best = d, j
    return best or "?", total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reload-clusters", action="store_true",
                    help="rebuild the OSM cluster pickle from the bulk file")
    args = ap.parse_args()

    from audit_regions import match_waters

    if args.reload_clusters or not OSM_INDEX_CACHE.exists():
        print("[osm] (re)building cluster cache...", flush=True)
        build_clusters(reload=True)
    with open(OSM_INDEX_CACHE, "rb") as f:
        clusters, _cell_index = pickle.load(f)
    print(f"[osm] {len(clusters)} named river clusters", flush=True)

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    county_centroids = build_county_centroids(waters)
    polygons = load_county_polygons()
    print(f"[waters] {len(waters)} contracted waters, {len(county_centroids)} counties, "
          f"{len(polygons)} county polygons", flush=True)

    matched = match_waters(clusters, waters, county_centroids)
    print(f"[match] {len(matched)}/{len(clusters)} clusters already contracted → excluded", flush=True)

    # geometry index of contracted waters (courses only) for the
    # duplicate-of-contracted check — clusters whose course already lies on a
    # contracted water must not render again in the teal overlay
    from shapely.geometry import MultiLineString  # noqa: F401  (import check)

    water_geoms: list[tuple[str, tuple, MultiLineString]] = []
    for w in waters:
        g = w.get("geometry")
        if not g or g.get("type") in ("Polygon", "MultiPolygon"):
            continue
        parts = (g["coordinates"] if g["type"] == "MultiLineString"
                 else [g["coordinates"]])
        try:
            mls = MultiLineString(parts)
        except Exception:
            continue
        water_geoms.append((w.get("slug"), mls.bounds, mls))
    print(f"[geom] {len(water_geoms)} contracted waters with course geometry", flush=True)

    from shapely.geometry import LineString  # noqa: F401  (import check)

    out: list[dict] = []
    skipped_short = 0
    dup_skipped = 0
    trimmed_skipped = 0
    for i, cl in enumerate(clusters):
        if i in matched:
            continue  # already contracted in waters.json
        dup_slug = duplicate_of_contracted(cl, water_geoms)
        if dup_slug is not None:
            dup_skipped += 1
            print(f"[dup] {(cl.get('raw_name') or cl['name'])!r} "
                  f"is the course of {dup_slug} → excluded", flush=True)
            continue
        # PARTIAL overlap: a stretch of the cluster lies on a contracted
        # course (e.g. the Prahova 'Doftana' upper course == the Romsilva
        # '4 Doftana Superioara' contract) while the rest is genuinely
        # uncontracted. Cut the overlapping runs out (t_f4ff3853).
        geom = trim_contracted_runs(cl["geom"], water_geoms)
        if geom is None:
            trimmed_skipped += 1
            print(f"[trim] {(cl.get('raw_name') or cl['name'])!r} "
                  f"fully covered by contracted courses → excluded", flush=True)
            continue
        geom = simplify_geometry(geom, SIMPLIFY_TOL_DEG, COORD_ROUND)
        if not geom:
            continue
        coords = geom["coordinates"] if geom["type"] == "LineString" else [
            p for part in geom["coordinates"] for p in part
        ]
        length = line_length(coords)
        if length < MIN_LENGTH_KM:
            skipped_short += 1
            continue
        bbox = cl["bbox"]
        # county: majority of sample points along the course inside the county
        # polygon. total_hits == 0 → river is entirely OUTSIDE Romania (the OSM
        # extract leaks foreign border rivers) — drop it.
        county, total_hits = assign_county(coords, polygons, county_centroids)
        if total_hits == 0:
            skipped_short += 1
            continue
        slug = "unc-" + hashlib.md5(
            f"{cl['name']}|{bbox[0]:.4f}|{bbox[1]:.4f}".encode()
        ).hexdigest()[:10]
        out.append({
            "slug": slug,
            "name": cl.get("raw_name") or cl["name"],
            "judet": county,
            "type": "ape",
            "subtype": "rau",
            "coordinates": [round((bbox[0] + bbox[2]) / 2, 5),
                            round((bbox[1] + bbox[3]) / 2, 5)],
            "bbox": [round(v, 5) for v in bbox],
            "geometry": geom,
            "uncontracted": True,
            "lengthKm": round(length, 1),
        })

    out.sort(key=lambda w: w["name"].lower())
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = OUT_FILE.stat().st_size / 1e6
    print(f"[write] {len(out)} uncontracted rivers → {OUT_FILE} ({size_mb:.1f} MB)")
    print(f"[skip] {skipped_short} dropped (too short or entirely outside Romania)")
    print(f"[skip] {dup_skipped} dropped (duplicate of an already-contracted course)")
    print(f"[skip] {trimmed_skipped} dropped (fully covered after partial-overlap trim)")

    # sanity: Râmna must be present (user-reported example)
    ramna = [w for w in out if norm(w["name"]) == "ramna"]
    print(f"[check] Râmna: {[(w['name'], w['judet'], w['lengthKm']) for w in ramna]}")


if __name__ == "__main__":
    main()
