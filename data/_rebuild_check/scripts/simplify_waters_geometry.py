#!/usr/bin/env python3
"""P0 §4.1 — Douglas-Peucker simplify + 5dp round of waters.json geometry.

Decision (USER APPROVED 2026-08-17): tolerance 0.001° (~110 m) with
preserve_topology, AND keep FULL resolution (unsimplified) for any water
carrying a `riverGroup` whose geometry is a line — multi-contract sector
slicing (contractInterval / sectorStart..sectorEnd / course_frac) needs the
exact full-course fractions, and simplification on those would introduce
fraction error on the shortest multi-contract rivers.

Applied to:
  - waters.json `geometry` (contracted): DP 0.001° + round 5dp, EXCEPT
    riverGroup line owners which are only rounded to 5dp (full vertex count
    preserved). Polygon/MultiPolygon geometry (lakes) is simplified too.
  - waters.json / uncontracted_rivers.json / uncontracted_lakes.json
    `geometryByCounty` clips: already 0.002°-simplified; re-round to 5dp
    (idempotent).
  - uncontracted pools: ROUND-only to 5dp, never re-DP at 0.001° — they are
    already simplified (rivers 0.002°, lakes size-proportional per pitfall 42:
    a flat 0.001° on small ponds would destroy them). Shipped compact.

Writes COMPACT JSON (separators=(",",":"), ensure_ascii=False) — §4.6 — for
every file it touches. The check-data-budget.mjs gate measures the compact
on-wire bytes, so this is the serialization the budget asserts on.

Normalize the FE commodity: click-resolution (fractionAtPoint) walks the FULL
(riverGroup) course unchanged, so Buzău/Brăila sector resolution is preserved.

Usage: .venv/bin/python3 scripts/simplify_waters_geometry.py
"""
import json
import math
import sys
from pathlib import Path
from typing import Optional
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public/data/waters.json"
UNC_RIVERS = ROOT / "public/data/uncontracted_rivers.json"
UNC_LAKES = ROOT / "public/data/uncontracted_lakes.json"

TOLERANCE_DEG = 0.001   # ~110 m
ROUND_DP = 5

# P1 §4.4: contracted waters are given lengthKm (line geometry) / areaHa
# (polygon geometry) so the FE WaterFeatureLayer can apply the SAME zoom-LOD
# thresholds as the uncontracted overlay (plan §4.4). Geodesic length uses the
# same haversine accumulating the uncontracted rivers builder uses; polygon
# area uses the same cos-lat scaling as build_uncontracted_lakes.
R_KM = 6371.0


def _haversine_km(a, b):
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R_KM * math.asin(math.sqrt(h))


def line_length_km(coords):
    """Sum of haversine segment lengths over a list of [lon, lat] points."""
    return sum(_haversine_km(coords[i - 1], coords[i]) for i in range(1, len(coords)))


def poly_area_ha(geom, mean_lat):
    a_deg2 = geom.area
    m2 = a_deg2 * (111320.0 ** 2) * math.cos(math.radians(mean_lat))
    return m2 / 10000.0


def annotate_size(w, g):
    """Set lengthKm (lines) or areaHa (polygons) on a contracted water from its
    geometry. Waters without line/polygon geometry (bbox-fallback points)
    keep no size field — the FE treats a missing size as 'always pass LOD' so
    discrete dots still render at any zoom (plan §4.4: culling is the win)."""
    t = g.get("type")
    lat = (w.get("coordinates") or [25.0, 45.8])[1]
    if t in ("LineString", "MultiLineString"):
        coords = g.get("coordinates", [])
        total = 0.0
        for part in (coords if t == "MultiLineString" else [coords]):
            total += line_length_km(part)
        w["lengthKm"] = round(total, 1)
    elif t in ("Polygon", "MultiPolygon"):
        s = shape(g)
        w["areaHa"] = round(poly_area_ha(s, lat), 2)


stats = {"simplified": 0, "kept_full_res": 0, "polys_simplified": 0,
         "round_only": 0, "no_geom": 0, "annotated_size": 0}


def _round_coords(c):
    if isinstance(c, list):
        if c and isinstance(c[0], (int, float)):
            return [round(float(c[0]), ROUND_DP), round(float(c[1]), ROUND_DP)]
        return [_round_coords(x) for x in c]
    return round(float(c), ROUND_DP)


def simplify_geometry(g: dict, keep_full_res: bool) -> dict:
    """Return rounded GeoJSON; DP-simplify unless keep_full_res."""
    t = g.get("type")
    if t not in ("LineString", "MultiLineString", "Polygon", "MultiPolygon"):
        # Point / unknown — just round.
        stats["round_only"] += 1
        return {"type": t, "coordinates": _round_coords(g.get("coordinates", []))}
    s = shape(g)
    if keep_full_res:
        stats["kept_full_res"] += 1
        out = s
    else:
        try:
            out = s.simplify(TOLERANCE_DEG, preserve_topology=True)
        except Exception as e:  # defensive: never let one bad geom abort
            print(f"  WARN simplify failed ({t}): {e}", file=sys.stderr)
            out = s
        if t in ("LineString", "MultiLineString"):
            stats["simplified"] += 1
        else:
            stats["polys_simplified"] += 1
    gj = json.loads(json.dumps(out.__geo_interface__))
    gj["coordinates"] = _round_coords(gj["coordinates"])
    return gj


def round_only_geometry(g: dict) -> dict:
    """Uncontracted pools: already simplified — round coords to 5dp only."""
    stats["round_only"] += 1
    return {"type": g.get("type"), "coordinates": _round_coords(g.get("coordinates", []))}


def process_pool(pool: list, simplify: bool = True, multi_rg: Optional[dict] = None) -> None:
    """simplify=True → the CONTRACTED pool: geometry simplified/rounded AND each
    water with line/polygon geometry gets a P1 §4.4 lengthKm/areaHa annotation.
    simplify=False → the uncontracted pools (already simplified): round-only,
    never re-annotate (they already carry lengthKm/areaHa from their builders)."""
    multi_rg = multi_rg or {}
    for w in pool:
        g = w.get("geometry")
        if not g:
            stats["no_geom"] += 1
            continue
        if not simplify:
            w["geometry"] = round_only_geometry(g)
        else:
            annotate_size(w, g)
            stats["annotated_size"] += 1
            rg = w.get("riverGroup")
            keep = bool(rg) and multi_rg.get(rg, 1) > 1 and g.get("type") in ("LineString", "MultiLineString")
            w["geometry"] = simplify_geometry(g, keep)
        gbc = w.get("geometryByCounty")
        if gbc:
            for k in gbc:
                if gbc[k]:
                    gbc[k] = round_only_geometry(gbc[k])


def compact(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    # riverGroup -> member count (a full-res owner only needs preserving when
    # its group is genuinely multi-contract: sector interval / Voronoi
    # fraction slicing. Collision-prone SINGLETON riverGroups have no other
    # member to slice against, so course_frac resolution returns the water's
    # own slug — simplifying them is safe.)
    group_members = {}
    for x in waters:
        rg = x.get("riverGroup")
        if rg:
            group_members[rg] = group_members.get(rg, 0) + 1
    process_pool(waters, simplify=True, multi_rg=group_members)

    unc_rivers = None
    unc_lakes = None
    if UNC_RIVERS.exists():
        unc_rivers = json.loads(UNC_RIVERS.read_text(encoding="utf-8"))
        process_pool(unc_rivers, simplify=False)
    if UNC_LAKES.exists():
        unc_lakes = json.loads(UNC_LAKES.read_text(encoding="utf-8"))
        process_pool(unc_lakes, simplify=False)

    WATERS.write_text(compact(waters), encoding="utf-8")
    if unc_rivers is not None:
        UNC_RIVERS.write_text(compact(unc_rivers), encoding="utf-8")
    if unc_lakes is not None:
        UNC_LAKES.write_text(compact(unc_lakes), encoding="utf-8")

    print("simplify_waters_geometry:", stats)


if __name__ == "__main__":
    main()
