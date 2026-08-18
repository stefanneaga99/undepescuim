#!/usr/bin/env python3
"""Fix stale lake centroids — `coordinates` in the WRONG county (t_6c2ac870).

Reported bug: 'Ape în apropiere' showed 'Lacul Dumbrăvița' (Timiș) at
18.2 km from Poiana Brașov. Root cause: the arebaltapeste snapshot's
`coordinates` for a handful of lakes is a STALE centroid from a bad OSM
match — for some it lands in a different county, far from the lake's real
geometry/bbox (same class as t_e3ae3121 / t_874e8569):

  - Lacul Dumbrăvița (Timiș):      coords [25.478, 45.760]=Brașov,   bbox [21.264, 45.805]=Timiș
  - Lac Pangrati (Neamț):          coords [26.323, 46.934],          geometry [26.194-26.215, 46.920-46.929]
  - Lacul Toplița (Bihor):         coords [26.421, 46.593],          geometry [22.306, 46.86] (Vida reservoir)
  - Lac acumulare Arpașu (Brașov): coords [24.694, 45.605],          geometry [24.593-24.675, 45.786-45.803]

The OSM geometry attached by the geometry sweep is CORRECT (right county);
only the legacy `coordinates` centroid was never recomputed. This script
recomputes `coordinates` from the attached geometry for every lake whose
centroid is missing or inconsistent with its geometry/bbox.

Only subtype=='lac' is touched: for rivers `coordinates` is the areba
reference point (may be the full-course reference while the geometry is
just the contracted sector) and neither distance nor the nearby county
chip uses it.

Usage:
    .venv/bin/python scripts/fix_lake_centroids.py [--dry-run] [--json OUT.json]
"""

import argparse
import json
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"

# Latitude tolerance (°): how far a centroid may sit from the geometry bbox
# before we consider it stale. ~2.2 km lat / ~1.6 km lon at 45°N — catches
# wrong-county and far-off centroids without churning sub-kilometre drift.
TOL_DEG = 0.02


def geom_bbox(g):
    """[minLon, minLat, maxLon, maxLat] of a GeoJSON geometry."""
    if g["type"] == "Polygon":
        pts = [p for ring in g["coordinates"] for p in ring]
    elif g["type"] == "MultiPolygon":
        pts = [p for poly in g["coordinates"] for ring in poly for p in ring]
    elif g["type"] == "LineString":
        pts = g["coordinates"]
    elif g["type"] == "MultiLineString":
        pts = [p for part in g["coordinates"] for p in part]
    else:
        pts = g.get("coordinates", [])
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


def reference_point(geom):
    """[lon, lat] reference point of a lake geometry (centroid for polygons).

    Some sweep-attached polygons are INVALID (self-intersecting rings, e.g.
    romsilva-cluj-1-lacul-fantanele) — shapely's centroid of an invalid
    polygon can land OUTSIDE the geometry's own bounds. Guard: accept the
    centroid only when it falls inside the geometry bounds, else fall back to
    representative_point() (guaranteed inside a valid polygon), else the
    geometry bbox center.
    """
    s = shape(geom)
    bb = s.bounds  # (minx, miny, maxx, maxy)
    def inside(lon, lat):
        return bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]
    c = s.centroid
    if inside(c.x, c.y):
        return [c.x, c.y]
    rp = s.representative_point()
    if inside(rp.x, rp.y):
        return [rp.x, rp.y]
    return [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]


def point_outside_bbox(lon, lat, bb, tol=TOL_DEG):
    if not bb:
        return False
    min_lon, min_lat, max_lon, max_lat = bb
    return not (min_lon - tol <= lon <= max_lon + tol and min_lat - tol <= lat <= max_lat + tol)


def extents_agree(gbb, wbb, tol=0.05):
    """Geometry bbox vs the water's own bbox agree (centers within ~5 km)?

    The geometry sweep sometimes attaches an OSM feature of the SAME NAME
    far from the water's registered location (Bodi: geometry at 23.60,47.69
    vs bbox at 23.77,47.67 — 12 km apart). When they disagree, the water's
    own bbox is the authoritative extent (it is what distance uses), so the
    reference point must come from the bbox, NOT the geometry.
    """
    if not gbb or not wbb:
        return True
    gc = ((gbb[0] + gbb[2]) / 2, (gbb[1] + gbb[3]) / 2)
    wc = ((wbb[0] + wbb[2]) / 2, (wbb[1] + wbb[3]) / 2)
    return abs(gc[0] - wc[0]) <= tol and abs(gc[1] - wc[1]) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only, no write")
    ap.add_argument("--json", type=str, help="write fix report JSON to this path")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    fixed, skipped = [], []
    for w in waters:
        if w.get("subtype") != "lac":
            continue
        slug, name, judet = w["slug"], w.get("name", ""), w.get("judet", "")
        geom = w.get("geometry")
        bb = w.get("bbox")
        coords = w.get("coordinates")

        # Reference point: geometry centroid when the geometry agrees with the
        # water's own bbox (or no bbox to compare); otherwise — geometry and
        # bbox pointing at different features — trust the water's bbox.
        new_coords = None
        src = None
        gbb = geom_bbox(geom) if (geom and geom.get("coordinates")) else None
        if gbb and extents_agree(gbb, bb):
            new_coords = [round(v, 7) for v in reference_point(geom)]
            src = "geometry"
        elif bb:
            new_coords = [round((bb[0] + bb[2]) / 2, 7), round((bb[1] + bb[3]) / 2, 7)]
            src = "bbox"
        elif gbb:
            new_coords = [round(v, 7) for v in reference_point(geom)]
            src = "geometry"

        if new_coords is None:
            skipped.append({"slug": slug, "name": name, "reason": "no geometry/bbox"})
            continue

        if coords is None:
            reason = "missing"
        elif src == "geometry":
            reason = "outside-geometry" if point_outside_bbox(coords[0], coords[1], gbb) else None
        else:
            reason = "outside-bbox" if point_outside_bbox(coords[0], coords[1], bb) else None
        if reason is None:
            continue

        fixed.append({
            "slug": slug, "name": name, "judet": judet,
            "reason": reason, "source": src,
            "old_coords": coords, "new_coords": new_coords,
            "bbox": bb,
        })
        print(f"  FIX  {judet:12} {name[:44]:46} [{reason:>16}] {coords} -> {new_coords}")
        if not args.dry_run:
            w["coordinates"] = new_coords

    print(f"\n[fix] {len(fixed)} lakes fixed, {len(skipped)} skipped (no geometry/bbox)")
    if not args.dry_run and fixed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[fix] wrote waters.json")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"fixed": fixed, "skipped": skipped}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"[fix] report -> {args.json}")


if __name__ == "__main__":
    main()
