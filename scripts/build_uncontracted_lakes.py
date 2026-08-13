#!/usr/bin/env python3
"""Build public/data/uncontracted_lakes.json — every OSM water-body POLYGON in
Romania (natural=water / water=* / landuse=reservoir / natural=wetland) that is
NOT already contracted in public/data/waters.json (t_51e028c4).

Inputs:
  data/raw/overpass_water_polys.json   (fresh full-country Overpass dump:
    ways+relations with water-ish tags, recursed nodes; built by
    scripts/fetch_water_polygons.py)
  public/data/waters.json              (contracted waters; matched lakes excluded)
  data/raw/county_boundaries/*.json    (county polygons for county assignment)

Output:
  public/data/uncontracted_lakes.json — compact Water-shaped array:
    slug, name, judet, type, subtype='lac', coordinates, bbox, geometry
    (Polygon/MultiPolygon, size-proportional simplification + coords rounded
    to 5 decimals), uncontracted: true, areaHa, dimensiune.

Inclusion rules (user request: ALL ponds/lakes, not tens of thousands of
puddles):
  - NAMED water polygons (any size above 0.1 ha to kill sub-puddle noise).
  - UNNAMED polygons >= 0.5 ha (displayed as 'Iaz neidentificat').
  - Named wetlands only when the name/type reads as water ('balta', 'iaz',
    'lac', 'acumulare', 'heleșteu') or wetland=pond/lake/water — pure
    marsh/reedbed/bog is not a fishing pond.
  - Excluded: water=river/canal/harbour/dock/lock/boatyard/wastewater
    (not ponds/lakes), foreign polygons (zero sample points inside any
    Romanian county), and polygons already contracted in waters.json
    (name-core + proximity or centroid-inside-contracted-geometry match).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_missing_rivers import build_county_centroids, norm  # noqa: E402
from build_uncontracted_rivers import (  # noqa: E402
    COUNTY_SLUG_TO_NAME,
    assign_county,
    load_county_polygons,
)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "overpass_water_polys.json"
FE_WATERS = ROOT / "public" / "data" / "waters.json"
OUT_FILE = ROOT / "public" / "data" / "uncontracted_lakes.json"

# Minimum area (ha) for a NAMED polygon — kills sub-puddle noise (0.1 ha =
# ~30 m square; the smallest mapped named ponds are ~0.3 ha).
MIN_NAMED_AREA_HA = 0.1
# Minimum area (ha) for an UNNAMED polygon (user-suggested threshold).
MIN_UNNAMED_AREA_HA = 0.5
# Coordinate rounding (5 decimals ~ 1 m).
COORD_ROUND = 5
# Base simplification tolerance in degrees (~200 m) for the LARGEST lakes;
# scaled down proportionally to sqrt(area) so small ponds keep their shape.
MAX_SIMPLIFY_TOL_DEG = 0.002
MIN_SIMPLIFY_TOL_DEG = 0.00005  # ~5 m

# water=* / wetland=* values that are NOT ponds/lakes (excluded).
EXCLUDED_WATER_VALUES = {
    "river", "canal", "harbour", "dock", "lock", "boatyard",
    "wastewater", "ditch", "moat", "stream", "basin",
}
# natural=wetland values that are NOT standing fishing water.
EXCLUDED_WETLAND_VALUES = {
    "marsh", "reedbed", "bog", "wet_meadow", "swamp", "tidalflat",
    "saltmarsh", "mangrove", "string_bog", "fen", "seasonal",
}
# Name patterns that make a wetland acceptable even without a water-ish
# wetland= tag ('Balta X', 'Iazul X', 'Lacul X', 'Heleșteul X', ...).
WATER_NAME_RE = re.compile(r"(balta|iaz|lac|acumulare|heles?teu|piscicul|baraj|balti|balt)", re.I)


def haversine_km(a, b):
    R = 6371.0
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def poly_area_ha(geom, mean_lat):
    """Shapely polygon area (degrees²) -> hectares via cos-lat scaling."""
    a_deg2 = geom.area
    m2 = a_deg2 * (111320.0 ** 2) * math.cos(math.radians(mean_lat))
    return m2 / 10000.0


def load_raw():
    print(f"[raw] loading {RAW.name} ({RAW.stat().st_size / 1e6:.0f} MB)...", flush=True)
    data = json.loads(RAW.read_text(encoding="utf-8"))
    els = data["elements"]
    nodes = {el["id"]: (el["lat"], el["lon"]) for el in els if el["type"] == "node" and "lat" in el}
    ways = {}
    for el in els:
        if el["type"] != "way":
            continue
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) >= 2:
            ways[el["id"]] = {"tags": el.get("tags", {}), "coords": coords}
    rels = {}
    for el in els:
        if el["type"] != "relation":
            continue
        members = [
            {"type": m["type"], "ref": m["ref"], "role": m.get("role", "outer")}
            for m in el.get("members", [])
        ]
        rels[el["id"]] = {"tags": el.get("tags", {}), "members": members}
    print(f"[raw] {len(nodes)} nodes, {len(ways)} ways, {len(rels)} relations", flush=True)
    return nodes, ways, rels


def is_closed(coords, tol=1e-9):
    if len(coords) < 4:
        return False
    return abs(coords[0][0] - coords[-1][0]) < tol and abs(coords[0][1] - coords[-1][1]) < tol


def chain_ring(ways_list):
    """Chain member ways into one closed ring by endpoint connectivity.

    Returns (flat_coords, used_indices) or (None, []) if no ring closes.
    """
    coords = [w["coords"] for w in ways_list]
    if not coords:
        return None, []
    chain = [coords[0]]
    used = {0}
    changed = True
    while changed and len(chain) < len(coords):
        changed = False
        for i, c in enumerate(coords):
            if i in used:
                continue
            head, tail = chain[0][0], chain[-1][-1]
            if abs(c[0][0] - tail[0]) < 1e-6 and abs(c[0][1] - tail[1]) < 1e-6:
                chain.append(c[1:])
                used.add(i)
                changed = True
            elif abs(c[-1][0] - tail[0]) < 1e-6 and abs(c[-1][1] - tail[1]) < 1e-6:
                chain.append(list(reversed(c))[1:])
                used.add(i)
                changed = True
            elif abs(c[-1][0] - head[0]) < 1e-6 and abs(c[-1][1] - head[1]) < 1e-6:
                chain.insert(0, list(reversed(c))[1:])
                used.add(i)
                changed = True
            elif abs(c[0][0] - head[0]) < 1e-6 and abs(c[0][1] - head[1]) < 1e-6:
                chain.insert(0, c[1:])
                used.add(i)
                changed = True
    flat = [p for c in chain for p in c]
    if not is_closed(flat):
        return None, []
    return flat, used


def extract_polygons(ways, rels):
    """Return list of {name, tags, geom(geojson), is_named} polygons."""
    polys = []

    def waterish(tags):
        return (
            tags.get("natural") == "water"
            or tags.get("water")
            or tags.get("landuse") == "reservoir"
            or tags.get("natural") == "wetland"
        )

    # ways: closed rings
    for wid, w in ways.items():
        tags = w["tags"]
        if not waterish(tags):
            continue
        if not is_closed(w["coords"]):
            continue
        name = tags.get("name") or tags.get("name:ro")
        polys.append({
            "name": name,
            "tags": tags,
            "is_named": bool(name),
            "geom": {"type": "Polygon", "coordinates": [w["coords"]]},
        })

    # relations: multipolygons — chain outer ways into rings
    for rid, rel in rels.items():
        tags = rel["tags"]
        if not waterish(tags):
            continue
        name = tags.get("name") or tags.get("name:ro")
        outers = []
        for m in rel["members"]:
            if m["type"] == "way" and m["role"] != "inner":
                w = ways.get(m["ref"])
                if w:
                    outers.append(w)
        rings = []
        remaining = list(outers)
        while remaining:
            seed = remaining.pop(0)
            ring, used_idx = chain_ring([seed] + remaining)
            if ring is None and is_closed(seed["coords"]):
                ring, used_idx = seed["coords"], {0}
            if ring is None:
                continue
            rings.append(ring)
            # drop the ways this ring consumed (indices into [seed]+remaining)
            for idx in sorted(used_idx, reverse=True):
                if idx > 0:
                    remaining.pop(idx - 1)
        if not rings:
            continue
        if len(rings) == 1:
            geom = {"type": "Polygon", "coordinates": [rings[0]]}
        else:
            geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
        polys.append({
            "name": name,
            "tags": tags,
            "is_named": bool(name),
            "geom": geom,
        })
    return polys


def lake_core_name(n):
    """Strip lake-name prefixes from a NORMALIZED name for dedupe matching:
    'lacul vidraru'/'lac de acumulare vidraru'/'acumularea vidraru' -> 'vidraru'."""
    for prefix in ("lac de acumulare", "lac de acumularea", "lacul de acumulare",
                   "acumularea", "acumulare", "lacul", "lac baraj", "barajul", "baraj",
                   "iazul", "iaz", "balta", "heleseteul", "heleseteu", "heleșteul", "heleșteu"):
        if n.startswith(prefix + " "):
            n = n[len(prefix):].strip()
            break
    return n


def main() -> None:
    import json as _json
    from shapely.geometry import shape

    nodes, ways, rels = load_raw()
    polys = extract_polygons(ways, rels)
    print(f"[extract] {len(polys)} water polygons (named+unnamed, ways+rels)", flush=True)

    waters = _json.loads(FE_WATERS.read_text(encoding="utf-8"))
    county_centroids = build_county_centroids(waters)
    polygons = load_county_polygons()
    print(f"[waters] {len(waters)} contracted, {len(polygons)} county polygons", flush=True)

    # Contracted lake lookup: core name + county + centroid, for dedupe.
    contracted_lakes = []
    for w in waters:
        if w.get("subtype") != "lac":
            continue
        bbox = w.get("bbox")
        cpt = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2) if bbox else None
        contracted_lakes.append({
            "slug": w["slug"],
            "core": lake_core_name(norm(w["name"])),
            "county": norm(w.get("judet", "")),
            "cpt": cpt,
            "name": w["name"],
            "geom": shape(w["geometry"]) if w.get("geometry") else None,
        })
    print(f"[dedupe] {len(contracted_lakes)} contracted lakes to avoid", flush=True)

    def is_contracted(name, county, cpt, geom):
        if not name:
            return False
        core = lake_core_name(norm(name))
        if len(core) < 3:
            core = norm(name)
        for cl in contracted_lakes:
            if not cl["core"] or cl["core"] != core:
                continue
            # same core name: decisive when the county matches (disambiguates
            # Lacul Roșu Harghita vs Tulcea vs Argeș). Without a county match,
            # accept only when the centroids are within 10 km (border lakes) or
            # the contracted geometry contains the OSM centroid.
            if cl["county"] == norm(county):
                return True
            if cl["cpt"] and haversine_km(cpt, cl["cpt"]) < 10.0:
                return True
            if cl["geom"] is not None and cl["geom"].contains(shape({"type": "Point", "coordinates": cpt})):
                return True
        # centroid inside any contracted lake geometry → same body regardless of name
        for cl in contracted_lakes:
            if cl["geom"] is not None and cl["geom"].contains(shape({"type": "Point", "coordinates": cpt})):
                return True
        return False

    out = []
    skipped = {"foreign": 0, "unnamed_small": 0, "named_small": 0, "contracted": 0,
               "excluded_type": 0, "no_geom": 0, "wetland_skip": 0}
    named_n = 0
    for p in polys:
        tags = p["tags"]
        wv = tags.get("water")
        if wv and wv in EXCLUDED_WATER_VALUES:
            skipped["excluded_type"] += 1
            continue
        if tags.get("natural") == "wetland":
            wl = tags.get("wetland")
            if wl in EXCLUDED_WETLAND_VALUES:
                skipped["wetland_skip"] += 1
                continue
            if not p["is_named"]:
                skipped["wetland_skip"] += 1
                continue
            if not (wl in ("pond", "lake", "water") or WATER_NAME_RE.search(p["name"] or "")):
                skipped["wetland_skip"] += 1
                continue

        geom = shape(p["geom"])
        if geom.is_empty or geom.area <= 0:
            skipped["no_geom"] += 1
            continue
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            skipped["no_geom"] += 1
            continue
        centroid = geom.representative_point()
        area_ha = poly_area_ha(geom, centroid.y)
        if not p["is_named"]:
            if area_ha < MIN_UNNAMED_AREA_HA:
                skipped["unnamed_small"] += 1
                continue
        else:
            if area_ha < MIN_NAMED_AREA_HA:
                skipped["named_small"] += 1
                continue

        # county: majority of sample points on the polygon boundary inside a
        # county polygon. total_hits == 0 → entirely outside Romania.
        bbox = geom.bounds
        sample = []
        from typing import Any
        g_any: Any = geom
        rings_iter = [g_any.exterior] if geom.geom_type == "Polygon" else [g.exterior for g in g_any.geoms]
        for ring in rings_iter:
            coords = list(ring.coords)
            step = max(1, len(coords) // 12)
            sample.extend(coords[::step][:13])
        county, total_hits = assign_county(sample, polygons, county_centroids)
        if total_hits == 0:
            skipped["foreign"] += 1
            continue

        name = p["name"] or "Iaz neidentificat"
        cpt = (round(centroid.x, 5), round(centroid.y, 5))
        if is_contracted(p["name"], county, cpt, geom):
            skipped["contracted"] += 1
            continue

        # size-proportional simplification: tol = 5% of linear size, capped.
        linear_deg = math.sqrt(geom.area)
        tol = min(MAX_SIMPLIFY_TOL_DEG, max(MIN_SIMPLIFY_TOL_DEG, linear_deg * 0.05))
        simple = geom.simplify(tol, preserve_topology=True)
        if simple.is_empty or simple.area <= 0:
            skipped["no_geom"] += 1
            continue
        simple_gj = _json.loads(_json.dumps(simple.__geo_interface__))

        def clean_ring(ring):
            outr = []
            for lon, lat in ring:
                pt = (round(lon, COORD_ROUND), round(lat, COORD_ROUND))
                if not outr or pt != outr[-1]:
                    outr.append(pt)
            return outr

        if simple_gj["type"] == "Polygon":
            rings = [clean_ring(r) for r in simple_gj["coordinates"]]
            rings = [r for r in rings if len(r) >= 4]
            if not rings:
                skipped["no_geom"] += 1
                continue
            geom_out = {"type": "Polygon", "coordinates": rings}
        else:  # MultiPolygon
            parts = []
            for poly in simple_gj["coordinates"]:
                rings = [clean_ring(r) for r in poly]
                rings = [r for r in rings if len(r) >= 4]
                if rings:
                    parts.append(rings)
            if not parts:
                skipped["no_geom"] += 1
                continue
            if len(parts) == 1:
                geom_out = {"type": "Polygon", "coordinates": parts[0]}
            else:
                geom_out = {"type": "MultiPolygon", "coordinates": parts}

        slug = "uncl-" + hashlib.md5(
            f"{name}|{county}|{bbox[0]:.4f}|{bbox[1]:.4f}".encode()
        ).hexdigest()[:10]
        dimensiune = f"{area_ha:.1f} ha" if area_ha >= 10 else f"{area_ha:.2f} ha"
        out.append({
            "slug": slug,
            "name": name,
            "judet": county,
            "type": "ape",
            "subtype": "lac",
            "coordinates": [cpt[0], cpt[1]],
            "bbox": [round(v, 5) for v in bbox],
            "geometry": geom_out,
            "uncontracted": True,
            "areaHa": round(area_ha, 2),
            "dimensiune": dimensiune,
        })
        if p["is_named"]:
            named_n += 1

    out.sort(key=lambda w: w["name"].lower())
    OUT_FILE.write_text(
        _json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    size_mb = OUT_FILE.stat().st_size / 1e6
    print(f"[write] {len(out)} uncontracted lakes ({named_n} named, "
          f"{len(out) - named_n} unnamed) -> {OUT_FILE} ({size_mb:.2f} MB)")
    print(f"[skip] {skipped}")

    # sanity: Dumbrăvița Hălchiu ponds must be present
    dumb = [w for w in out if "dumbravita" in norm(w["name"]) and 25.3 < w["coordinates"][0] < 25.6]
    print(f"[check] Dumbrăvița (Brașov/Hălchiu): {len(dumb)}")
    for d in dumb[:12]:
        print(f"   {d['name']} | {d['judet']} | {d['areaHa']} ha | {d['coordinates']}")
    total_ha = sum(w["areaHa"] for w in out)
    print(f"[stats] total area {total_ha:.0f} ha across {len(out)} polygons")


if __name__ == "__main__":
    main()
