#!/usr/bin/env python3
"""SPIKE measurement part 2 (t_dd287ca9): uncontracted files + LOD-subset sizes."""
import json, gzip, collections
from shapely.geometry import shape

ROOT = "/home/stefan/undepescuim"

def compact(x): return json.dumps(x, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def gz(b): return len(gzip.compress(b, 9))

def geom_vertex_count(g):
    t = g["type"]; c = g["coordinates"]
    if t == "LineString": return len(c)
    if t == "MultiLineString": return sum(len(p) for p in c)
    if t == "Polygon": return sum(len(r) for r in c)
    if t == "MultiPolygon": return sum(len(r) for poly in c for r in poly)
    return 0

for name in ["uncontracted_rivers", "uncontracted_lakes"]:
    p = f"{ROOT}/public/data/{name}.json"
    data = json.load(open(p, encoding="utf-8"))
    n = len(data)
    with_g = sum(1 for w in data if w.get("geometry"))
    with_gbc = sum(1 for w in data if w.get("geometryByCounty"))
    gbc_clips = sum(len([k for k,v in w["geometryByCounty"].items() if v is not None]) for w in data if w.get("geometryByCounty"))
    tot_v = sum(geom_vertex_count(w["geometry"]) for w in data if w.get("geometry"))
    tot_gbc_v = sum(geom_vertex_count(v) for w in data if w.get("geometryByCounty") for v in w["geometryByCounty"].values() if v)
    print(f"\n=== {name} ===")
    print(f"  entries={n}  with_geometry={with_g}  with_geometryByCounty={with_gbc}  gbc_clips={gbc_clips}")
    print(f"  total geom vertices={tot_v:,}  total gbc vertices={tot_gbc_v:,}")
    # keys
    keys = collections.Counter()
    for w in data:
        keys.update(w.keys())
    print(f"  field keys: {dict(keys)}")
    # length/area distribution
    if name == "uncontracted_rivers":
        lens = [w.get("lengthKm") for w in data if w.get("lengthKm") is not None]
        print(f"  lengthKm: n={len(lens)} min={min(lens):.1f} max={max(lens):.1f}")
        majors = [w for w in data if (w.get("lengthKm") or 0) >= 30]
        print(f"  rivers >= 30km (zoom<8 LOD subset): {len(majors)}")
        b = compact(majors)
        print(f"  majors-only compact={len(b):,} gzip-9={gz(b):,}")
    else:
        areas = [w.get("areaHa") for w in data if w.get("areaHa") is not None]
        print(f"  areaHa: n={len(areas)} min={min(areas):.1f} max={max(areas):.1f}")
        majors = [w for w in data if (w.get("areaHa") or 0) >= 100]
        print(f"  lakes >= 100ha (zoom<8 LOD subset): {len(majors)}")
        b = compact(majors)
        print(f"  majors-only compact={len(b):,} gzip-9={gz(b):,}")

    # coordinate precision
    max_dp = 0
    def walk(c):
        global max_dp
        if isinstance(c, list) and len(c) == 2 and all(isinstance(x, (int, float)) for x in c):
            for v in c:
                s = str(v); dp = len(s.split(".")[1]) if "." in s else 0
                if dp > max_dp: max_dp = dp
            return
        if isinstance(c, list):
            for x in c: walk(x)
    for w in data:
        g = w.get("geometry")
        if g: walk(g["coordinates"])
    print(f"  max coord dp = {max_dp}")

    # full file current compact/gzip
    b = compact(data)
    print(f"  current full: compact={len(b):,} gzip-9={gz(b):,}")
