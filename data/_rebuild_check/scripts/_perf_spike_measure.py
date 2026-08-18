#!/usr/bin/env python3
"""SPIKE measurement (t_dd287ca9): quantify geometry simplification + round + split gains.

Measures, on the real public/data/waters.json:
  A. coordinate decimal precision histogram
  B. Douglas-Peucker vertex reduction at tol = 0.0005 / 0.001 / 0.002 deg
  C. full-file compact + gzip-9 size under several regimes:
       R0  = current (baseline)
       R1  = round coords to 5 dp
       R2  = R1 + simplify tol 0.001
       R3  = R2 + drop geometryByCounty
       R4  = R3 + short keys (GeoJSON t/c + a few) [approx]
"""
import json, gzip, io, math, collections
from shapely.geometry import shape

ROOT = "/home/stefan/undepescuim"
PATH = ROOT + "/public/data/waters.json"

def compact(x): return json.dumps(x, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def gz(b): return len(gzip.compress(b, 9))

def geom_vertex_count(g):
    t = g["type"]; c = g["coordinates"]
    if t == "LineString": return len(c)
    if t == "MultiLineString": return sum(len(p) for p in c)
    if t == "Polygon": return sum(len(r) for r in c)
    if t == "MultiPolygon": return sum(len(r) for poly in c for r in poly)
    return 0

data = json.load(open(PATH, encoding="utf-8"))

# ---- A. precision histogram ----
max_dp = 0
dp_hist = collections.Counter()
total_nums = 0
def walk(c):
    global max_dp
    if isinstance(c, list) and len(c) == 2 and all(isinstance(x, (int, float)) for x in c):
        for v in c:
            s = str(v)
            dp = len(s.split(".")[1]) if "." in s else 0
            dp_hist[dp] += 1
            if dp > max_dp: max_dp = dp
        return
    if isinstance(c, list):
        for x in c: walk(x)

for w in data:
    g = w.get("geometry")
    if g: walk(g["coordinates"])
print("A. coord precision: max dp =", max_dp, " histogram(dict):", dict(sorted(dp_hist.items())))

def geoms():
    for w in data:
        g = w.get("geometry")
        if g: yield g

# ---- B. DP vertex reduction ----
def simplify(g, tol):
    s = shape(g).simplify(tol, preserve_topology=True)
    return json.loads(json.dumps(s.__geo_interface__))

for tol in [0.0005, 0.001, 0.002]:
    vb = va = 0
    for g in geoms():
        vb += geom_vertex_count(g)
        va += geom_vertex_count(simplify(g, tol))
    print(f"B. DP tol={tol}: vertices {vb:,} -> {va:,}  ({100*va/vb:.1f}% kept, cut {100*(1-va/vb):.1f}%)")

# ---- C. size regimes ----
def round_coords(g, dp):
    def r(c):
        if isinstance(c, list):
            return [r(x) for x in c]
        return round(float(c), dp)
    g2 = dict(g)
    g2["coordinates"] = r(g["coordinates"])
    return g2

def build(round_dp=None, tol=None, drop_gbc=False, short_keys=False):
    out = []
    for w in data:
        w2 = dict(w)
        if round_dp is not None or tol is not None:
            g = w.get("geometry")
            if g:
                g2 = dict(g)
                if tol is not None:
                    g2 = simplify(g, tol)
                if round_dp is not None:
                    g2 = round_coords(g2, round_dp)
                w2["geometry"] = g2
            if w.get("geometryByCounty"):
                gbc = {}
                for k, clip in w["geometryByCounty"].items():
                    if clip is None:
                        gbc[k] = None
                        continue
                    c2 = dict(clip)
                    if tol is not None:
                        c2 = simplify(clip, tol)
                    if round_dp is not None:
                        c2 = round_coords(c2, round_dp)
                    gbc[k] = c2
                w2["geometryByCounty"] = gbc
        if drop_gbc:
            w2.pop("geometryByCounty", None)
        if short_keys:
            def sk(g):
                if isinstance(g, dict):
                    d = {}
                    for k, v in g.items():
                        nk = {"type": "t", "coordinates": "c"}.get(k, k)
                        d[nk] = sk(v)
                    return d
                if isinstance(g, list):
                    return [sk(x) for x in g]
                return g
            w2["geometry"] = sk(w2["geometry"]) if w2.get("geometry") else None
            if w2.get("geometry") and w2["geometry"] is None:
                w2.pop("geometry", None)
        out.append(w2)
    return out

def report(name, lst):
    b = compact(lst)
    print(f"C. {name:45s} compact={len(b):>10,}  gzip-9={gz(b):>10,}")

report("R0 baseline (current)", data)
report("R1 round 5dp", build(round_dp=5))
report("R2 round5 + DP 0.001", build(round_dp=5, tol=0.001))
report("R2b round5 + DP 0.0005", build(round_dp=5, tol=0.0005))
report("R3 R2 + drop geometryByCounty", build(round_dp=5, tol=0.001, drop_gbc=True))
report("R4 R3 + short keys", build(round_dp=5, tol=0.001, drop_gbc=True, short_keys=True))

# ---- D. geometryByCounty alone size (for the lazy-split scenario) ----
gbc_only = {}
for w in data:
    if w.get("geometryByCounty"):
        gbc_only[w["slug"]] = w["geometryByCounty"]
b = compact(gbc_only)
print(f"D. geometryByCounty standalone (327 clips): compact={len(b):,} gzip-9={gz(b):,}")
