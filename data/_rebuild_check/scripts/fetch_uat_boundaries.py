#!/usr/bin/env python3
"""Fetch Romania UAT (comună/municipiu/oraș) boundaries from Overpass (t_dd918db7).

SOURCE DECISION (county+locality filter, t_dd918db7 — plan §3):
  Overpass is the chosen boundary source:
  - Quality: OSM admin_level=8 relations = the canonical UAT set; 3,180 of the
    ~3,181 official UATs present, all with clean `name` tags ("Florești",
    "Cluj-Napoca" — no "Comuna"/"Municipiul" prefix), closed outer rings.
  - Effort: one query, ~8 s / ~82 MB raw; matches the repo's existing Overpass
    usage (data/raw/overpass_water_all.json).
  - Alternatives evaluated: Geofabrik .osm.pbf (same OSM data but needs an
    osmium tag-filter pass + polygon export — heavier tooling, no quality
    gain); ANCPI (authoritative but no programmatic bulk API). Both rejected
    on effort/quality tradeoff. OSM attribution is already present via the
    map's OSM tiles.

Pipeline:
  1. Query all admin_level=8 relations in RO with full member geometry.
  2. Assemble each relation's outer ways into a polygon (chain by endpoints,
     auto-close, largest ring wins).
  3. Assign each UAT its county by max-area intersection vs the repo's 41
     Nominatim county polygons (data/raw/county_boundaries/).
  4. Write:
       data/raw/localities/uat_boundaries.geojson  — simplified polygons
       data/raw/localities/uat_index.json          — { normName: {name, county, osm_id} }

Run: .venv/bin/python scripts/fetch_uat_boundaries.py
"""
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/raw/localities"
COUNTY_DIR = ROOT / "data/raw/county_boundaries"
OUT_BOUNDARIES = RAW_DIR / "uat_boundaries.geojson"
OUT_INDEX = RAW_DIR / "uat_index.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY = (
    '[out:json][timeout:600];'
    'area["ISO3166-1"="RO"]->.ro;'
    'rel(area.ro)["boundary"="administrative"]["admin_level"="8"];'
    'out geom;'
)

# Simplify tolerance for the stored polygons (~50 m) — plenty for point-in-polygon.
SIMPLIFY_DEG = 0.0005
ROUND_DP = 5

_ROMANIAN = [("ș", "s"), ("ţ", "t"), ("ț", "t"), ("ă", "a"), ("î", "i"), ("â", "a")]


def norm_name(s: str) -> str:
    t = s.lower()
    for a, b in _ROMANIAN:
        t = t.replace(a, b)
    return re.sub(r"[\s\-]+", "", t)


def _close(a, b, tol=1e-7) -> bool:
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def _flip(ways) -> None:
    for w in ways:
        w.reverse()


def chain_ways(way_coords) -> list:
    """Order a relation's outer way geometries into one ring (endpoint chaining)."""
    if not way_coords:
        return []
    # Fast path: a single already-closed way.
    for w in way_coords:
        if len(w) >= 4 and _close(w[0], w[-1]):
            return w

    chains = [[w] for w in way_coords]

    def merge_into(a, b):
        """Try to append/prepend chain b to chain a. Returns True on success."""
        if not b:
            return False
        fa, la = a[0][0], a[-1][-1]
        fb, lb = b[0][0], b[-1][-1]
        if _close(fa, lb):          # b attaches before a, reversed
            b.reverse(); _flip(b)
            a[:0] = b
            return True
        if _close(fa, fb):          # b attaches before a, same dir -> flip b
            _flip(b)
            a[:0] = b
            return True
        if _close(la, fb):          # b attaches after a
            a.extend(b)
            return True
        if _close(la, lb):          # b attaches after a, reversed
            b.reverse(); _flip(b)
            a.extend(b)
            return True
        return False

    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(chains):
            j = i + 1
            while j < len(chains):
                if merge_into(chains[i], chains[j]):
                    chains.pop(j)
                    changed = True
                else:
                    j += 1
            i += 1

    best = max(chains, key=lambda c: sum(len(w) for w in c))
    ring: list = []
    for w in best:
        if not ring:
            ring = list(w)
        elif _close(ring[-1], w[0]):
            ring.extend(w[1:])
        elif _close(ring[-1], w[-1]):
            ring.extend(reversed(w[:-1]))
        elif _close(ring[0], w[-1]):
            ring = w[:-1] + ring
        elif _close(ring[0], w[0]):
            ring = list(reversed(w[1:])) + ring
        else:
            ring.extend(w)
    return ring


def assemble_polygon(members) -> Polygon | None:
    """Build the UAT polygon from a relation's outer way geometries."""
    ways = []
    for m in members:
        if m.get("type") != "way":
            continue
        role = m.get("role", "")
        if role not in ("outer", ""):
            continue
        geom = m.get("geometry")
        if not geom:
            continue
        coords = [(float(p["lon"]), float(p["lat"])) for p in geom]
        if len(coords) >= 4:
            ways.append(coords)
    if not ways:
        return None
    ring = chain_ways(ways)
    if len(ring) < 4:
        return None
    poly = Polygon(ring)  # auto-closes the ring
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    # Largest ring wins (handles islands/exclaves in the same relation).
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    return poly


def load_county_polys() -> dict[str, Polygon]:
    out = {}
    for f in sorted(COUNTY_DIR.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))[0]
        name = r.get("name") or f.stem
        g = shape(r["geojson"])
        if g.geom_type == "MultiPolygon":
            g = unary_union(g)
        out[name] = g
    return out


def county_of(poly: Polygon, county_polys: dict[str, Polygon]) -> str | None:
    """County by max intersection area; fallback centroid point-in-polygon."""
    best_name, best_area = None, 0.0
    for name, cp in county_polys.items():
        inter = poly.intersection(cp)
        if inter.is_empty:
            continue
        area = inter.area
        if area > best_area:
            best_area, best_name = area, name
    if best_name:
        return best_name
    pt = poly.representative_point()
    for name, cp in county_polys.items():
        if cp.covers(pt):
            return name
    return None


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("fetching UAT relations from Overpass...", file=sys.stderr)
    req = urllib.request.Request(
        OVERPASS_URL, data=QUERY.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "undepescuim-locality-pipeline/1.0 (data pipeline for UndePescuim.ro)",
        },
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        data = json.loads(resp.read())
    elements = data["elements"]
    print(f"relations: {len(elements)}", file=sys.stderr)

    print("loading county polygons...", file=sys.stderr)
    county_polys = load_county_polys()
    print(f"county polygons: {len(county_polys)}", file=sys.stderr)

    features = []
    # County-scoped lookup: { normCounty: { normName: {name, county, osm_id} } } —
    # same-name UATs in different counties (Călărași ×4, Unirea ×4...) never collide,
    # and the FE/limite-fallback always resolves a locality within a known county.
    index: dict[str, dict[str, dict]] = {}
    no_poly = 0
    no_county = 0
    name_counts: Counter = Counter()
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if not name:
            no_poly += 1
            continue
        poly = assemble_polygon(el.get("members", []))
        if poly is None:
            no_poly += 1
            continue
        poly = poly.simplify(SIMPLIFY_DEG, preserve_topology=True)
        county = county_of(poly, county_polys)
        if not county:
            no_county += 1
        name_counts[norm_name(name)] += 1
        # round coordinates to 5 dp
        poly = _round_poly(poly, ROUND_DP)
        props = {"name": name, "county": county, "osm_id": el["id"]}
        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": mapping(poly),
        })
        index.setdefault(norm_name(county or ""), {})[norm_name(name)] = {
            "name": name, "county": county, "osm_id": el["id"],
        }

    dupes = {k: v for k, v in name_counts.items() if v > 1}
    if dupes:
        print(f"WARNING duplicate normalized UAT names: {len(dupes)}", file=sys.stderr)
        for k, v in list(dupes.items())[:10]:
            print(f"  {k}: {v}", file=sys.stderr)

    # OSM models Municipiul București at admin_level=6 (not 8), so the
    # admin_level=8 query above covers 3,180 of the 3,181 official UATs.
    # Add București itself (its county polygon from the repo) as one UAT so
    # the 48 București-tagged lakes get a locality too.
    buc_file = COUNTY_DIR / "bucuresti.json"
    if buc_file.exists():
        r = json.loads(buc_file.read_text(encoding="utf-8"))[0]
        buc_poly = shape(r["geojson"])
        if buc_poly.geom_type == "MultiPolygon":
            buc_poly = unary_union(buc_poly)
        buc_poly = _round_poly(buc_poly.simplify(SIMPLIFY_DEG, preserve_topology=True), ROUND_DP)
        features.append({
            "type": "Feature",
            "properties": {"name": "București", "county": "București", "osm_id": r.get("osm_id")},
            "geometry": mapping(buc_poly),
        })
        index.setdefault("bucuresti", {})["bucuresti"] = {
            "name": "București", "county": "București", "osm_id": r.get("osm_id"),
        }
        print("added Municipiul București as a single UAT", file=sys.stderr)
    else:
        print("WARNING: bucuresti.json not found — București waters will have no locality", file=sys.stderr)

    fc = {"type": "FeatureCollection", "features": features}
    OUT_BOUNDARIES.write_text(
        json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    OUT_INDEX.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"wrote {OUT_BOUNDARIES} ({OUT_BOUNDARIES.stat().st_size/1e6:.1f} MB, {len(features)} UATs)", file=sys.stderr)
    print(f"wrote {OUT_INDEX} ({OUT_INDEX.stat().st_size/1e6:.1f} MB, {len(index)} entries)", file=sys.stderr)
    print(f"no polygon: {no_poly}, no county: {no_county}", file=sys.stderr)

    # Summary
    per_county = Counter(f["properties"]["county"] for f in features)
    print("UATs per county (sample):", file=sys.stderr)
    for c, n in sorted(per_county.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {c}: {n}", file=sys.stderr)
    print(f"total with county: {sum(1 for f in features if f['properties']['county'])}/{len(features)}", file=sys.stderr)


def _round_poly(poly: Polygon, dp: int) -> Polygon:
    from shapely.geometry import Polygon as _P
    def r2(p):
        return (round(p[0], dp), round(p[1], dp))
    if poly.geom_type == "Polygon":
        return _P([r2(p) for p in poly.exterior.coords],
                  [[r2(p) for p in ring.coords] for ring in poly.interiors])
    if poly.geom_type == "MultiPolygon":
        from shapely.geometry import MultiPolygon as _MP
        return _MP([_round_poly(p, dp) for p in poly.geoms])
    return poly


if __name__ == "__main__":
    main()
