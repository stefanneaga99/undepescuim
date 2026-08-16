#!/usr/bin/env python3
"""Validate every water's geometry against its declared county.

For each water in waters.json WITH geometry, compute:
  1. distance from the geometry centroid to the declared county SEAT
     (COUNTY_SEATS — the sane-distance signal the task asks for), and
  2. which Romanian county actually contains its course (majority of ≤41
     sample points inside the county boundary polygons cached in
     data/raw/county_boundaries/*.json).

Classification (per water):
  ok                 — geometry within ~1.5° of the county seat AND (if the
                       polygon test disagrees) the declared county still
                       contains ≥1 sample point.
  multi-county-share — geometry is far from the seat BUT it crosses the
                       declared county polygon AND the water belongs to a
                       riverGroup whose members span multiple counties: this
                       is the legitimate "one geometry owner, full course"
                       pattern (e.g. Brăila Siret owns the shared course).
  wrong-county       — FLAG: zero sample points inside the declared county
                       AND centroid far from its seat. The attached geometry
                       is another county's same-name river (Homorodul Nou /
                       Brașov Homorod is the canonical case).
  outside-romania    — FLAG: zero points inside ANY county polygon and no
                       declared-county overlap. Foreign leak or the course is
                       drawn from outside the country.

Usage:
    python3 scripts/validate_geometry_county.py [--json REPORT.json]

Exit code 0. Writes the report to stdout and optionally to a JSON file.
"""

import argparse
import json
import math
import unicodedata
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
COUNTY_DIR = ROOT / "data" / "raw" / "county_boundaries"

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
    "satu mare": "Satu Mare",
    "sibiu": "Sibiu", "suceava": "Suceava", "teleorman": "Teleorman",
    "timis": "Timiș", "tulcea": "Tulcea", "vaslui": "Vaslui",
    "valcea": "Vâlcea", "vrancea": "Vrancea", "bucuresti": "București",
}

COUNTY_SEATS = {
    "Alba": (23.57, 46.08), "Arad": (21.32, 46.18), "Argeș": (24.82, 44.94),
    "Bacău": (26.91, 46.57), "Bihor": (21.94, 47.07), "Bistrița-Năsăud": (24.50, 47.13),
    "Botoșani": (26.67, 47.75), "Brașov": (25.61, 45.65), "Brăila": (27.97, 45.27),
    "Buzău": (26.78, 45.15), "Caraș-Severin": (21.90, 45.42), "Călărași": (26.82, 44.20),
    "Cluj": (23.62, 46.77), "Constanța": (28.65, 44.17), "Covasna": (26.01, 45.90),
    "Dâmbovița": (25.46, 44.93), "Dolj": (23.79, 44.33), "Galați": (28.01, 45.43),
    "Giurgiu": (25.97, 43.90), "Gorj": (23.26, 45.03), "Harghita": (25.62, 46.35),
    "Hunedoara": (22.91, 45.75), "Ialomița": (27.60, 44.56), "Iași": (27.60, 47.16),
    "Ilfov": (26.10, 44.44), "Maramureș": (23.89, 47.66), "Mehedinți": (22.66, 44.64),
    "Mureș": (24.56, 46.54), "Neamț": (26.38, 46.93), "Olt": (24.48, 44.43),
    "Prahova": (26.02, 44.94), "Satu Mare": (22.87, 47.79), "Sălaj": (23.05, 47.18),
    "Sibiu": (24.15, 45.80), "Suceava": (26.25, 47.65), "Teleorman": (25.34, 43.75),
    "Timiș": (21.22, 45.75), "Tulcea": (28.80, 45.18), "Vaslui": (27.73, 46.64),
    "Vâlcea": (24.37, 45.10), "Vrancea": (27.18, 45.70), "București": (26.10, 44.43),
}

# beyond this distance (deg) from the county seat the geometry needs
# polygon-level confirmation (Homorodul Nou: 3.3° → flagged)
SEAT_DIST_MAX_DEG = 1.5


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def load_county_polygons():
    """[(name, prepared_geom, bbox)] from the cached Nominatim boundaries."""
    polys = []
    for path in sorted(COUNTY_DIR.glob("*.json")):
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
        polys.append((name, prep(geom), geom.bounds))
    return polys


def water_points(w, include_fallback=True):
    """Flat [(lon, lat), ...] coordinate list of a water's geometry.

    With include_fallback (default), a water with NO geometry but a stored
    `coordinates`/`bbox` (the stale-fallback geocode class, t_a0e123da) yields
    its stored point + bbox corners/centroid so the county check catches
    poisoned fallbacks (Valea Pojorâtei pointed at Săcele while the contract
    county was Brașov-Făgăraș). Pure geocode points land in exactly one county
    — the wrong-county rule (zero points in the declared county + far from the
    seat) flags them the same way as wrong geometry.
    """
    g = w.get("geometry")
    if g:
        t = g.get("type")
        coords = g["coordinates"]
        if t == "MultiLineString":
            flat = [p for part in coords for p in part]
        elif t == "LineString":
            flat = coords
        elif t == "Polygon":
            flat = [p for ring in coords for p in ring]
        elif t == "MultiPolygon":
            flat = [p for poly in coords for ring in poly for p in ring]
        else:
            flat = coords
        return [p for p in flat if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not include_fallback:
        return []
    pts: list[tuple[float, float]] = []
    c = w.get("coordinates")
    if isinstance(c, (list, tuple)) and len(c) >= 2 and all(isinstance(v, (int, float)) for v in c[:2]):
        pts.append((c[0], c[1]))
    b = w.get("bbox")
    if isinstance(b, (list, tuple)) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b):
        min_lon, min_lat, max_lon, max_lat = b
        pts.append(((min_lon + max_lon) / 2, (min_lat + max_lat) / 2))
        pts += [(min_lon, min_lat), (max_lon, min_lat), (max_lon, max_lat), (min_lon, max_lat)]
    return pts


def centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def bbox_of_points(pts):
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


def classify(points, polygons):
    """Return (counts_by_county, total_hits) for ≤41 sample points."""
    sample = points[:: max(1, len(points) // 40)]
    counts = {}
    for lon, lat in sample:
        pt = Point(lon, lat)
        for name, pgeom, pbbox in polygons:
            if not (pbbox[0] <= lon <= pbbox[2] and pbbox[1] <= lat <= pbbox[3]):
                continue
            if pgeom.contains(pt):
                counts[name] = counts.get(name, 0) + 1
                break
    total = sum(counts.values())
    return counts, total


def any_point_in_county(points, polygons, county):
    """Dense test: does ANY sampled point of the course fall inside the
    declared county polygon? Uses every 3rd point (capped ~2000) — catches
    shared full-course owners whose mouth touches the county (Brăila Siret)
    while rejecting a course that is entirely in another county."""
    cn = norm(county)
    target = None
    for name, pgeom, pbbox in polygons:
        if norm(name) == cn:
            target = (pgeom, pbbox)
            break
    if not target:
        return 0
    pgeom, pbbox = target
    step = max(1, len(points) // 2000)
    n = 0
    for lon, lat in points[::step]:
        if not (pbbox[0] <= lon <= pbbox[2] and pbbox[1] <= lat <= pbbox[3]):
            continue
        if pgeom.contains(Point(lon, lat)):
            n += 1
    return n


def seat_dist(declared, cpt):
    seat = COUNTY_SEATS.get(declared)
    if not seat:
        return None
    return math.hypot(cpt[0] - seat[0], cpt[1] - seat[1])


def flag_waters(waters, polygons):
    """Return (flagged_records, records) using the same classification as main().

    Exposed so the fixer can reuse the exact flag logic without re-running
    the script.
    """
    from collections import defaultdict
    group_judets = defaultdict(set)
    for w in waters:
        if w.get("riverGroup") and w.get("judet"):
            group_judets[w["riverGroup"]].add(w["judet"])

    flagged = []
    all_recs = []
    for w in waters:
        pts = water_points(w)
        if not pts:
            continue
        declared = w.get("judet") or "?"
        cpt = centroid(pts)
        sd = seat_dist(declared, cpt)
        counts, total = classify(pts, polygons)
        declared_n = norm(declared)
        declared_key = next((k for k in counts if norm(k) == declared_n), None)
        in_declared = counts.get(declared_key, 0) if declared_key else 0
        actual = max(counts, key=lambda k: (counts[k], k)) if counts else None
        bbox = bbox_of_points(pts)
        group = w.get("riverGroup")
        multi_county_group = bool(group and len(group_judets.get(group, set())) > 1)

        dense_in = any_point_in_county(pts, polygons, declared)

        if total == 0:
            cls = "wrong-county" if dense_in == 0 and sd is not None and sd > SEAT_DIST_MAX_DEG else "ok"
        elif in_declared == 0 and sd is not None and sd > SEAT_DIST_MAX_DEG and dense_in == 0:
            cls = "wrong-county"
        elif in_declared == 0 and sd is not None and sd <= SEAT_DIST_MAX_DEG and dense_in == 0:
            # seat-distance shortcut: the geometry is within 1.5° of the seat
            # BUT has ZERO dense points inside the declared county polygon.
            # Tolerated when (a) the water is a legit multi-county group member
            # (shared full-course owners / border rivers like Bărzăuța
            # Bacău+Covasna, Crasna Maramureș+Sălaj whose polygon-following
            # course sits on the county line), or (b) the geometry sits EXACTLY
            # where the source data geocoded the water (stored bbox centroid
            # within ~0.2° of the geometry centroid) — a border-attribution
            # artifact (Romsilva-managed lakes on the Făgăraș crest like
            # Podragu Mare, administered by D.S. Sibiu even though the OSM
            # boundary puts the polygon in Brașov), NOT a wrong attachment.
            # Everything else with zero in-county points is a same-name
            # cross-county attachment (Sebeșul de Sus class) even when the
            # wrong course is only ~1.4° from the seat.
            src_bb = w.get("bbox")
            src_matches = False
            if src_bb:
                sc = ((src_bb[0] + src_bb[2]) / 2, (src_bb[1] + src_bb[3]) / 2)
                src_matches = math.hypot(cpt[0] - sc[0], cpt[1] - sc[1]) <= 0.2
            cls = "ok" if (multi_county_group or src_matches) else "wrong-county"
        elif in_declared == 0 and sd is None and dense_in == 0:
            cls = "ok" if actual else "outside-romania"
        elif in_declared > 0 and sd is not None and sd > SEAT_DIST_MAX_DEG:
            cls = "ok" if multi_county_group else "multi-county-share"
        else:
            cls = "ok"

        rec = {
            "slug": w.get("slug"),
            "name": w.get("name"),
            "judet": declared,
            "asociatie": (w.get("asociatie") or {}).get("name"),
            "riverGroup": group,
            "bbox": [round(v, 4) for v in bbox],
            "centroid": [round(cpt[0], 4), round(cpt[1], 4)],
            "seat_dist_deg": round(sd, 3) if sd is not None else None,
            "counts": counts,
            "total_hits": total,
            "in_declared": in_declared,
            "dense_in_declared": dense_in,
            "actual_county": actual,
            "classification": cls,
        }
        all_recs.append(rec)
        if cls in ("wrong-county", "outside-romania"):
            # final gate: border-attribution artifacts whose OSM course is the
            # correct feature but sits just across the county line (Romsilva /
            # areba manage it on the border, e.g. Râul Șugo Covasna at 0.4 km
            # from the Covasna boundary, flowing into the Vîrghiș border
            # stream). The fixer's KEEP_GEOMETRY set is the source of truth.
            from fix_wrong_county_geometry import KEEP_GEOMETRY

            if w.get("slug") in KEEP_GEOMETRY:
                cls = "ok-border-artifact"
                rec["classification"] = cls
            else:
                flagged.append(rec)
    return flagged, all_recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=str, help="write full report JSON to this path")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    polygons = load_county_polygons()

    flagged, all_recs = flag_waters(waters, polygons)
    checked = len(all_recs)

    print(f"[validate] {len(waters)} waters, {len(polygons)} county polygons")
    print(f"[validate] waters with locatable points (geometry or coords/bbox fallback): {checked}")
    print(f"[validate] FLAGGED (wrong-county + outside-romania): {len(flagged)}")
    print()
    for r in sorted(flagged, key=lambda r: (r["judet"], r["name"])):
        print(f"  {r['classification']:16} {r['judet']:16} {r['name'][:40]:42} "
              f"actual={r['actual_county']!s:12} seat_d={r['seat_dist_deg']} "
              f"bbox={r['bbox']}")
    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {"checked": checked, "flagged": flagged, "all": all_recs},
                ensure_ascii=False, indent=1,
            ),
            encoding="utf-8",
        )
        print(f"\n[report] wrote {args.json}")


if __name__ == "__main__":
    main()
