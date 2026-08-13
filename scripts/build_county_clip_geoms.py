#!/usr/bin/env python3
"""Compute per-county geometry clips for the county filter (t_117f0b99).

Problem: a water's OSM geometry spans the FULL river course, which crosses
several counties, but the map filters by w.judet (contract county). Selecting
Brașov therefore drew the entire Olt (Harghita→Teleorman).

Fix: for every water whose geometry crosses its own county border, store
`geometryByCounty: { <normCountyKey>: <GeoJSON> }` — the geometry clipped to
the water's OWN county, buffered ~200 m (0.002°) so border rivers that ARE the
county border (Siret, Prut, Danube branches) are not chopped by the boundary
ring running down their middle.

Rules:
- Source geometry = the water's own `geometry`, or (for contracted sector
  entries that are geometry-less) the geometry of a same-subtype member of the
  same riverGroup (Olt Vâlcea, Siret Galați, Buzău county...).
- When the water has sectorStart/sectorEnd, the course is FIRST sliced to that
  full-course fraction interval (FE-equivalent haversine walk), THEN clipped to
  the county — so multiple contracts in the same county render their own
  sectors instead of overlapping full-passage lines.
- Waters entirely inside their county (every point within the buffered
  polygon) get NO entry — the FE falls back to the full geometry.
- Waters whose geometry does not touch their own county get `null` — the FE
  renders nothing for them when the county is selected (misattributed geometry
  can't leak outside the county anymore).

Key format: normalized county name — lowercase, diacritics stripped, all
separators removed ('Bistrița-Năsăud' → 'bistritanasaud', matching the FE's
countyClipKey()).

Writes to public/data/waters.json and public/data/uncontracted_rivers.json
preserving the committed serialization (indent=1, ensure_ascii=False, NO
trailing newline).
"""
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import MultiLineString, MultiPoint, MultiPolygon, Point, Polygon, shape
from shapely.geometry.base import BaseGeometry

ROOT = Path(__file__).resolve().parent.parent
BOUNDARY_DIR = ROOT / "data/raw/county_boundaries"
WATERS_JSON = ROOT / "public/data/waters.json"
UNCONTRACTED_JSON = ROOT / "public/data/uncontracted_rivers.json"

# ~200 m buffer so border rivers (whose centerline IS the county ring) stay whole.
BUFFER_DEG = 0.002
# Douglas-Peucker tolerance for stored clips — the clips are RENDER-only
# (click resolution always uses the ORIGINAL full-course geometry), so they can
# be simplified at the same 0.002° (~200 m) used by the uncontracted overlay
# without any visible loss. Cuts the clip payload ~50%.
SIMPLIFY_DEG = 0.002
# Coordinate rounding for stored clips (5 dp ≈ 1 m — plenty for a fishing map).
ROUND_DP = 5

_ROMANIAN = [("ș", "s"), ("ţ", "t"), ("ț", "t"), ("ă", "a"), ("î", "i"), ("â", "a")]


def norm_county(s: str) -> str:
    t = s.lower()
    for a, b in _ROMANIAN:
        t = t.replace(a, b)
    return re.sub(r"[\s\-]+", "", t)


def load_boundaries() -> dict[str, BaseGeometry]:
    """normCountyKey -> shapely polygon (unbuffered)."""
    out: dict[str, BaseGeometry] = {}
    for f in sorted(BOUNDARY_DIR.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))[0]
        name = r.get("name") or f.stem
        out[norm_county(name)] = shape(r["geojson"])
    return out


def haversine_km(a: Any, b: Any) -> float:
    R = 6371.0
    dlat = math.radians(float(b[1]) - float(a[1]))
    dlon = math.radians(float(b[0]) - float(a[0]))
    la1 = math.radians(float(a[1]))
    la2 = math.radians(float(b[1]))
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def part_length(coords: list) -> float:
    return sum(haversine_km(coords[i - 1], coords[i]) for i in range(1, len(coords)))


def order_parts(parts: list) -> list:
    """Faithful port of WaterFeatureLayer.orderParts (PCA + latitude orient)."""
    if len(parts) <= 1:
        return parts
    mids = [p[len(p) // 2] for p in parts]
    mx = sum(m[0] for m in mids) / len(mids)
    my = sum(m[1] for m in mids) / len(mids)
    cxx = sum((m[0] - mx) ** 2 for m in mids)
    cyy = sum((m[1] - my) ** 2 for m in mids)
    cxy = sum((m[0] - mx) * (m[1] - my) for m in mids)
    theta = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    vx, vy = math.cos(theta), math.sin(theta)
    scored = sorted(parts, key=lambda p: (p[len(p) // 2][0] - mx) * vx + (p[len(p) // 2][1] - my) * vy)
    half = max(1, len(scored) // 2)
    lat_first = sum(p[len(p) // 2][1] for p in scored[:half]) / half
    lat_last = sum(p[len(p) // 2][1] for p in scored[-half:]) / half
    return list(reversed(scored)) if lat_first < lat_last else scored


def slice_multiline(parts: list, f0: float, f1: float) -> list:
    """Faithful port of WaterFeatureLayer.sliceMultiLine (haversine walk)."""
    ordered = order_parts(parts)
    lengths = [part_length(p) for p in ordered]
    total = sum(lengths)
    if total <= 0:
        return []
    d0, d1 = f0 * total, f1 * total
    out: list = []
    walked = 0.0
    for coords, ln in zip(ordered, lengths):
        seg_start, seg_end = walked, walked + ln
        walked = seg_end
        if seg_end <= d0 or seg_start >= d1:
            continue
        trimmed: list = []
        acc = seg_start
        for j, pt in enumerate(coords):
            if j > 0:
                acc += haversine_km(coords[j - 1], pt)
            if acc < d0:
                if trimmed:
                    trimmed[-1] = pt
                continue
            if acc > d1:
                if not trimmed or trimmed[-1] != coords[j - 1]:
                    trimmed.append(coords[j - 1])
                trimmed.append(pt)
                break
            trimmed.append(pt)
        if len(trimmed) >= 2:
            out.append(trimmed)
    return out


def geometry_to_parts(g: dict) -> list:
    t = g["type"]
    if t == "LineString":
        return [g["coordinates"]]
    if t == "MultiLineString":
        return g["coordinates"]
    raise ValueError(f"not a line geometry: {t}")


def _as_lines(g: BaseGeometry) -> Optional[BaseGeometry]:
    if g.is_empty:
        return None
    if g.geom_type in ("LineString", "MultiLineString"):
        return g
    if g.geom_type == "GeometryCollection":
        lines = [_as_lines(x) for x in g.geoms]
        lines = [x for x in lines if x is not None]
        if not lines:
            return None
        geoms = [ln for x in lines for ln in (list(x.geoms) if x.geom_type == "MultiLineString" else [x])]
        return MultiLineString(geoms) if len(geoms) > 1 else geoms[0]
    return None


def _as_polys(g: BaseGeometry) -> Optional[BaseGeometry]:
    if g.is_empty:
        return None
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    if g.geom_type == "GeometryCollection":
        polys = [_as_polys(x) for x in g.geoms]
        polys = [x for x in polys if x is not None]
        if not polys:
            return None
        geoms = [p for x in polys for p in (list(x.geoms) if x.geom_type == "MultiPolygon" else [x])]
        return MultiPolygon(geoms) if len(geoms) > 1 else geoms[0]
    return None


def _dedupe_consecutive(line: list) -> list:
    out: list = []
    for p in line:
        if out and out[-1][0] == p[0] and out[-1][1] == p[1]:
            continue
        out.append(p)
    return out


def lines_to_geojson(lines: list) -> Optional[dict]:
    cleaned: list = []
    for ln in lines:
        rounded = [[round(float(x), ROUND_DP), round(float(y), ROUND_DP)] for x, y in ln]
        dedup = _dedupe_consecutive(rounded)
        if len(dedup) >= 2:
            cleaned.append(dedup)
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return {"type": "LineString", "coordinates": cleaned[0]}
    return {"type": "MultiLineString", "coordinates": cleaned}


def _round_coords(c: Any) -> Any:
    if isinstance(c, list):
        return [_round_coords(x) for x in c]
    return round(float(c), ROUND_DP)


def poly_to_geojson(p: BaseGeometry) -> dict:
    coords = json.loads(json.dumps(p.__geo_interface__, allow_nan=False))
    coords["coordinates"] = _round_coords(coords["coordinates"])
    return coords


def all_points(g: BaseGeometry):
    if g.geom_type == "Point":
        yield g
    elif g.geom_type == "MultiPoint":
        yield from g.geoms
    elif hasattr(g, "geoms"):
        for sub in g.geoms:
            yield from all_points(sub)
    elif g.geom_type in ("LineString", "LinearRing"):
        yield from [Point(c) for c in g.coords]
    elif g.geom_type == "Polygon":
        yield from [Point(c) for c in g.exterior.coords]
        for ring in g.interiors:
            yield from [Point(c) for c in ring.coords]


def _total_length_km(mls: BaseGeometry) -> float:
    if mls.geom_type == "LineString":
        return part_length(list(mls.coords))
    if mls.geom_type == "MultiLineString":
        return sum(part_length(list(p.coords)) for p in mls.geoms)
    return 0.0


# Tri-state clip result: (key, geojson) | (key, None)=store-null | None=skip.
def build_clip_for_water(w: dict, source_geom: dict, county_polys: dict, buffered: dict, skip_if_inside: bool):
    own = norm_county(w.get("judet", ""))
    if own not in county_polys:
        return None
    try:
        parts = geometry_to_parts(source_geom)
    except ValueError:
        return None
    shapely_line = shape(source_geom)

    s0, s1 = w.get("sectorStart"), w.get("sectorEnd")
    has_sector = isinstance(s0, (int, float)) and isinstance(s1, (int, float))
    if has_sector:
        sliced = slice_multiline(parts, float(s0), float(s1))
        if not sliced:
            return (own, None)
        line = MultiLineString(sliced)
    else:
        line = shapely_line

    clip = line.intersection(buffered[own])

    # Fully inside its county (incl. border buffer) → no clip needed: the FE
    # falls back to the full geometry. Measured by length coverage so border
    # rivers (whose centerline IS the county ring) are skipped rather than
    # stored as near-duplicate geometry.
    if (
        skip_if_inside
        and not has_sector
        and source_geom["type"] in ("LineString", "MultiLineString")
        and line.geom_type in ("LineString", "MultiLineString")
    ):
        src_len = _total_length_km(line)
        clip_len = _total_length_km(clip) if clip.geom_type in ("LineString", "MultiLineString") else 0.0
        if src_len > 0 and clip_len / src_len >= 0.995:
            return None

    # Render-only clips are simplified (click resolution uses the ORIGINAL
    # geometry) — same 0.002° tolerance as the uncontracted overlay.
    if source_geom["type"] in ("LineString", "MultiLineString"):
        clip = clip.simplify(SIMPLIFY_DEG, preserve_topology=True)
        out = _as_lines(clip)
        if out is None:
            return (own, None)
        geoms = list(out.geoms) if out.geom_type == "MultiLineString" else [out]
        gj = lines_to_geojson([list(p.coords) for p in geoms])
    else:
        out = _as_polys(clip)
        if out is None:
            return (own, None)
        gj = poly_to_geojson(out)
    return (own, gj)


def find_group_owner(waters_by_slug: dict, water: dict) -> Optional[dict]:
    rg = water.get("riverGroup")
    if not rg:
        return None
    want_line = water.get("subtype") != "lac"
    fallback = None
    for w in waters_by_slug.values():
        g = w.get("geometry")
        if w.get("riverGroup") != rg or not g:
            continue
        is_line = g.get("type") in ("LineString", "MultiLineString")
        if want_line and is_line:
            return w
        if not want_line and g.get("type") in ("Polygon", "MultiPolygon"):
            return w
        if fallback is None:
            fallback = w
    return fallback


def process_pool(pool: list, waters_by_slug: dict, county_polys: dict, buffered: dict, allow_group_owner: bool):
    stats = {"with_geometry": 0, "clips": 0, "nulls": 0, "skips": 0, "no_source": 0}
    for w in pool:
        source = w.get("geometry")
        owner = None
        if not source:
            if allow_group_owner:
                owner = find_group_owner(waters_by_slug, w)
                source = owner.get("geometry") if owner else None
            if not source:
                stats["no_source"] += 1
                continue
        stats["with_geometry"] += 1
        res = build_clip_for_water(
            w, source, county_polys, buffered, skip_if_inside=(owner is None)
        )
        if res is None:
            stats["skips"] += 1
            # skip = geometry lies (≥99.5%) INSIDE its own county → no clip
            # needed, the FE falls back to the full geometry. A stale
            # geometryByCounty entry from a previous (wrong-geometry) run
            # would make countyRenderGeometry return null and HIDE the water
            # — drop the own-county key so the fallback applies.
            own_key = norm_county(w.get("judet", ""))
            gbc = w.get("geometryByCounty")
            if gbc and own_key in gbc:
                del gbc[own_key]
                if not gbc:
                    w["geometryByCounty"] = {}
            continue
        key, gj = res
        if gj is None:
            stats["nulls"] += 1
        else:
            stats["clips"] += 1
        w.setdefault("geometryByCounty", {})[key] = gj
    return stats


def dump_json(data, path: Path, compact: bool = False):
    if compact:
        text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    else:
        text = json.dumps(data, indent=1, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")


def main():
    county_polys = load_boundaries()
    print(f"county boundaries: {len(county_polys)}", file=sys.stderr)
    buffered = {k: v.buffer(BUFFER_DEG) for k, v in county_polys.items()}

    waters = json.loads(WATERS_JSON.read_text(encoding="utf-8"))
    uncontracted = json.loads(UNCONTRACTED_JSON.read_text(encoding="utf-8"))
    waters_by_slug = {w["slug"]: w for w in waters}

    print("processing contracted waters...", file=sys.stderr)
    stats_c = process_pool(waters, waters_by_slug, county_polys, buffered, allow_group_owner=True)
    print("processing uncontracted rivers...", file=sys.stderr)
    stats_u = process_pool(uncontracted, {}, county_polys, buffered, allow_group_owner=False)

    dump_json(waters, WATERS_JSON)
    dump_json(uncontracted, UNCONTRACTED_JSON, compact=True)

    print("contracted:", stats_c, file=sys.stderr)
    print("uncontracted:", stats_u, file=sys.stderr)
    n_c = sum(1 for w in waters if w.get("geometryByCounty"))
    n_u = sum(1 for w in uncontracted if w.get("geometryByCounty"))
    print(f"waters with geometryByCounty: contracted={n_c} uncontracted={n_u}")


if __name__ == "__main__":
    main()
