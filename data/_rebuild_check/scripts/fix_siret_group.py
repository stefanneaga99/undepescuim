#!/usr/bin/env python3
"""Siret group refactor (t_ebd873fe) — build ONE chained full-course LineString
for the CONTRACTED (Romanian) Siret: all 'siret' OSM cluster parts chained,
trimmed to start where the river enters Romania (the Siret's OSM headwater is
in Ukraine), bridged across the ~7km Răcăciuni OSM gap, ending at the mouth.

Per-county sectors are computed by point-in-polygon on Nominatim county
boundaries (buffered 200m to catch on-border river points). Overlapping
border stretches resolve via the FE's smallest-interval rule.

Output: data/processed/siret_full_course.json
"""
import json, pickle, sys, math
from pathlib import Path
from shapely.geometry import shape, Point

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import core  # noqa: E402

COUNTIES = ["Suceava", "Botoșani", "Iași", "Neamț", "Bacău", "Galați", "Vrancea", "Brăila"]
SLUG = lambda c: c.lower().replace("ș", "s").replace("ț", "t").replace("ă", "a").replace("î", "i").replace("â", "a")

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def _hav(a, b):
    """Haversine distance in km (same as FE partLength)."""
    R = 6371
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def dedupe_parts(parts):
    seen = set()
    out = []
    for p in parts:
        key = (round(p[0][0], 5), round(p[0][1], 5), round(p[-1][0], 5), round(p[-1][1], 5))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def chain_parts(parts, tol=1e-5):
    parts = dedupe_parts([list(p) for p in parts])
    used = [False] * len(parts)
    chains = []
    for i in range(len(parts)):
        if used[i]:
            continue
        used[i] = True
        chain = list(parts[i])
        while True:
            tail = chain[-1]
            nxt = None
            for j in range(len(parts)):
                if used[j]:
                    continue
                p = parts[j]
                if dist(p[0], tail) < tol:
                    nxt = (j, p, False); break
                if dist(p[-1], tail) < tol:
                    nxt = (j, p, True); break
            if nxt is None:
                break
            j, p, rev = nxt
            used[j] = True
            chain.extend(reversed(p) if rev else p)
        while True:
            head = chain[0]
            prv = None
            for j in range(len(parts)):
                if used[j]:
                    continue
                p = parts[j]
                if dist(p[-1], head) < tol:
                    prv = (j, p, False); break
                if dist(p[0], head) < tol:
                    prv = (j, p, True); break
            if prv is None:
                break
            j, p, rev = prv
            used[j] = True
            chain = list(reversed(p) if rev else p) + chain
        chains.append(chain)
    chains.sort(key=len, reverse=True)
    return chains

def main():
    clusters, _ = pickle.load(open(ROOT / "data/cache/osm_river_clusters.pkl", "rb"))
    parts = []
    for c in clusters:
        if core(c["name"]) != "siret":
            continue
        g = c["geom"]
        ps = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        parts.extend(list(p) for p in ps)

    chains = chain_parts(parts)
    c0 = chains[0]   # upper course
    c1 = chains[1]   # lower course

    # orient source->mouth (source = higher latitude for the Siret)
    for ch in (c0, c1):
        if ch[0][1] < ch[-1][1]:
            ch.reverse()

    # bridge the Răcăciuni gap: c0 tail -> c1 head
    print("gap bridge: %.2f km" % (dist(c0[-1], c1[0]) * 111))
    course = c0 + [c1[0]] + c1

    # ---- trim to Romania: first point inside any county polygon ----
    polys = {}
    for c in COUNTIES:
        res = json.loads((ROOT / "data/raw/county_boundaries" / (SLUG(c) + ".json")).read_text(encoding="utf-8"))
        polys[c] = shape(res[0]["geojson"])
    all_ro = {c: polys[c].buffer(0.002) for c in COUNTIES}

    start = None
    for i, pt in enumerate(course):
        p = Point(pt)
        if any(b.contains(p) for b in all_ro.values()):
            start = i
            break
    print("first point inside Romania at idx", start, course[start] if start else None)
    if start and start > 0:
        course = course[start:]
    print("trimmed course pts:", len(course))

    out = {
        "river": "Râul Siret",
        "geometry": {"type": "LineString", "coordinates": course},
        "sectors": {},
    }
    out_path = ROOT / "data/processed/siret_full_course.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    # ---- sectors: min/max haversine-length fraction of course inside each
    # county (buffered). MUST match the FE's fractionAtPoint metric (haversine
    # cumulative length), not point indices — OSM node density varies. ----
    n = len(course)
    # cumulative haversine length at each point
    cum = [0.0] * n
    for i in range(1, n):
        cum[i] = cum[i - 1] + _hav(a := course[i - 1], b := course[i])
    total = cum[-1]

    sectors = {}
    for c in COUNTIES:
        b = all_ro[c]
        idxs = [i for i, pt in enumerate(course) if b.contains(Point(pt))]
        if not idxs:
            print(f"{c}: NO inside points")
            continue
        f0, f1 = cum[idxs[0]] / total, cum[idxs[-1]] / total
        sectors[c] = [round(f0, 4), round(f1, 4)]
        # lat/lon span for sanity
        lats = [course[i][1] for i in idxs]; lons = [course[i][0] for i in idxs]
        print(f"{c:10s} {f0:.4f}..{f1:.4f}  pts={len(idxs):5d} lat {min(lats):.3f}..{max(lats):.3f} lon {min(lons):.3f}..{max(lons):.3f}")
    out["sectors"] = sectors
    # ---- fill gaps: make the union of sectors cover [0,1] continuously ----
    # gaps arise when two county polygons leave a sub-km stretch uncovered.
    # Extend the LEFT sector's end to cover the gap (or the right start if
    # the left has no end).
    ordered = sorted(sectors.items(), key=lambda kv: kv[1][0])
    if ordered[0][1][0] > 0.0:
        sectors[ordered[0][0]][0] = 0.0
    for i in range(len(ordered) - 1):
        name_l, (s_l, e_l) = ordered[i]
        name_r, (s_r, e_r) = ordered[i + 1]
        if e_l < s_r:
            sectors[name_l][1] = round(s_r, 4)
    last_name, (s_l, e_l) = ordered[-1]
    if e_l < 1.0:
        sectors[last_name][1] = 1.0
    out["sectors"] = sectors
    print("\nfinal sectors (gap-filled):")
    for c, (f0, f1) in sorted(sectors.items(), key=lambda kv: kv[1][0]):
        print(f"  {c:10s} {f0:.4f} .. {f1:.4f}")
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("\nwrote", out_path)

if __name__ == "__main__":
    main()
