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
from audit_missing_rivers import build_county_centroids  # noqa: E402
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
) -> str:
    """County whose polygon contains the most sample points along the course.

    Falls back to the nearest county centroid when no point lands inside any
    polygon (river outside Romania / boundary noise).
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
    if counts:
        return max(counts, key=lambda k: (counts[k], k))
    # fallback: nearest county centroid
    cpt = (sum(p[0] for p in sample) / len(sample), sum(p[1] for p in sample) / len(sample))
    best, bd = "", 1e9
    for j, cc in fallback.items():
        d = (cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2
        if d < bd:
            bd, best = d, j
    return best or "?"


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

    from shapely.geometry import LineString  # noqa: F401  (import check)

    out: list[dict] = []
    skipped_short = 0
    for i, cl in enumerate(clusters):
        if i in matched:
            continue  # already contracted in waters.json
        geom = simplify_geometry(cl["geom"], SIMPLIFY_TOL_DEG, COORD_ROUND)
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
        # polygon (falls back to nearest county centroid).
        county = assign_county(coords, polygons, county_centroids)
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
    print(f"[skip] {skipped_short} too short (< {MIN_LENGTH_KM} km)")

    # sanity: Râmna must be present (user-reported example)
    ramna = [w for w in out if "ramna" in w["name"].lower() and "sat" not in w["name"].lower()]
    print(f"[check] Râmna-like: {[(w['name'], w['judet'], w['lengthKm']) for w in ramna[:5]]}")


if __name__ == "__main__":
    main()
