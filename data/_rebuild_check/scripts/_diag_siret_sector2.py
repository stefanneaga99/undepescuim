#!/usr/bin/env python3
"""Compute the Siret Vrancea sector (v2): chain OSM ways into one ordered
course, then cut the part that runs along Vrancea county.

The Siret is Vrancea's eastern boundary — the river coincides with the county
edge, so we intersect the ordered course with the county ring, project the
contact points onto the course, and keep the span between the two outermost
contacts. Output: data/processed/siret_vrancea_sector.json.
"""
import json, sys, pickle, math
from pathlib import Path
from shapely.geometry import shape, LineString, Point
from shapely.ops import substring

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import core  # noqa: E402

def dedupe_parts(parts):
    """Drop parts with identical (first,last) endpoints (duplicated ways)."""
    seen = set()
    out = []
    for p in parts:
        key = (round(p[0][0], 5), round(p[0][1], 5), round(p[-1][0], 5), round(p[-1][1], 5))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def chain_parts(parts):
    """Chain LineString parts by endpoint connectivity (within 1e-5 deg),
    following the pattern from sweep_multiway_rivers.py."""
    parts = dedupe_parts([list(p) for p in parts])
    used = [False] * len(parts)
    chains = []
    for i in range(len(parts)):
        if used[i]:
            continue
        used[i] = True
        chain = list(parts[i])
        # grow forward
        while True:
            tail = chain[-1]
            nxt = None
            for j in range(len(parts)):
                if used[j]:
                    continue
                p = parts[j]
                if dist(p[0], tail) < 1e-5:
                    nxt = (j, p, False)
                    break
                if dist(p[-1], tail) < 1e-5:
                    nxt = (j, p, True)
                    break
            if nxt is None:
                break
            j, p, rev = nxt
            used[j] = True
            chain.extend(reversed(p) if rev else p)
        # grow backward
        while True:
            head = chain[0]
            prv = None
            for j in range(len(parts)):
                if used[j]:
                    continue
                p = parts[j]
                if dist(p[-1], head) < 1e-5:
                    prv = (j, p, False)
                    break
                if dist(p[0], head) < 1e-5:
                    prv = (j, p, True)
                    break
            if prv is None:
                break
            j, p, rev = prv
            used[j] = True
            chain = list(reversed(p) if rev else p) + chain
        chains.append(chain)
    chains.sort(key=len, reverse=True)
    return chains

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def main():
    vj = json.loads((ROOT / "data/raw/vrancea_boundary.geojson").read_text(encoding="utf-8"))
    poly = shape(vj[0]["geojson"])
    ring = LineString(poly.exterior.coords)
    print("Vrancea polygon bounds:", poly.bounds)

    clusters, _ = pickle.load(open(ROOT / "data/cache/osm_river_clusters.pkl", "rb"))
    cl = next(c for c in clusters if core(c["name"]) == "siret")
    g = cl["geom"]
    parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    print("raw parts:", len(parts), "total pts:", sum(len(p) for p in parts))

    chains = chain_parts(parts)
    print("chains:", len(chains), "longest:", len(chains[0]) if chains else 0)
    for i, ch in enumerate(chains[:5]):
        print(f"  chain{i}: {len(ch)} pts, bounds "
              f"({min(p[0] for p in ch):.3f},{min(p[1] for p in ch):.3f})-"
              f"({max(p[0] for p in ch):.3f},{max(p[1] for p in ch):.3f}) "
              f"first=({ch[0][0]:.4f},{ch[0][1]:.4f}) last=({ch[-1][0]:.4f},{ch[-1][1]:.4f})")

    # pick the chain whose bounds overlap Vrancea county
    vj_bounds = poly.bounds  # (minx, miny, maxx, maxy)
    chain = None
    for ch in chains:
        cminx = min(p[0] for p in ch); cminy = min(p[1] for p in ch)
        cmaxx = max(p[0] for p in ch); cmaxy = max(p[1] for p in ch)
        if cminx <= vj_bounds[2] and cmaxx >= vj_bounds[0] and cminy <= vj_bounds[3] and cmaxy >= vj_bounds[1]:
            chain = ch
            break
    if chain is None:
        raise RuntimeError("no chain overlaps Vrancea")
    print("using chain bounds:",
          f"({min(p[0] for p in chain):.3f},{min(p[1] for p in chain):.3f})-({max(p[0] for p in chain):.3f},{max(p[1] for p in chain):.3f})")
    course = LineString(chain)
    # orient source->mouth: Siret flows south, so source is at HIGHER latitude
    if course.coords[0][1] < course.coords[-1][1]:
        course = LineString(list(course.coords)[::-1])
    print("oriented first:", tuple(round(c, 4) for c in course.coords[0]),
          "last:", tuple(round(c, 4) for c in course.coords[-1]))

    inter = course.intersection(ring)
    pts = []
    def collect(g):
        if g.geom_type == "Point":
            pts.append((g.x, g.y))
        elif g.geom_type in ("MultiPoint", "GeometryCollection", "MultiLineString", "LineString"):
            for gg in g.geoms if hasattr(g, "geoms") else [g]:
                collect(gg)
    collect(inter)
    print("contact points:", len(pts))
    projs = sorted(course.project(Point(p)) for p in pts)
    print("projections: min=%.4f max=%.4f of len=%.4f" % (projs[0], projs[-1], course.length))
    f0, f1 = projs[0] / course.length, projs[-1] / course.length
    print("fractions: %.4f .. %.4f" % (f0, f1))

    sector = substring(course, projs[0], projs[-1])
    print("sector:", sector.geom_type, "pts:", len(sector.coords), "bounds:", sector.bounds)
    print("sector first:", sector.coords[0], "last:", sector.coords[-1])

    out = {
        "river": "Râul Siret",
        "county": "Vrancea",
        "fraction_start": round(f0, 4),
        "fraction_end": round(f1, 4),
        "geometry": {"type": "LineString", "coordinates": list(sector.coords)},
    }
    out_path = ROOT / "data/processed/siret_vrancea_sector.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("wrote", out_path)

if __name__ == "__main__":
    main()
