#!/usr/bin/env python3
"""Fix the Vrancea lowland rivers reported around Panciu/Odobești/Focșani
(t_9a7cf783).

Audit result: every contracted river in the Vrancea cells is already 'present'
in waters.json — but three had broken geometry:

1. Râul Siret (VRANCEA, anpa-0674): contracted by AJVPS VRANCEA but had NO
   geometry and NO bbox → invisible (the thick blue Siret east of Focșani
   rendered basemap-only). Attach the Vrancea-sector course computed by
   scripts/_diag_siret_sector2.py (intersection of the OSM Siret course with
   the Vrancea county boundary ring; south end = Râmnicu Sărat confluence).

2. Râul Râmnicu Sărat (VRANCEA, anpa-vrancea-ramnicu-sarat): geometry was a
   MultiLineString with DUPLICATED parts (OSM way mapped twice → the course
   drew twice). Rebuild as ONE ordered LineString (headA+headB+main chained at
   shared endpoints, deduped). The Buzău entry (anpa-anpa-0215) held the SAME
   lower-course geometry (wrong — that stretch is Vrancea's) → drop its
   geometry so it becomes a group-share like the Romsilva members.

3. Râul Zăbala mijlocie (anpa-anpa-0676): geometry was duplicated parts AND
   truncated — it only covered the lower 26.52-26.78E stretch, so the Zăbala
   Superioară (RNP Romsilva, D.S. Vrancea, 25 km) sector never rendered.
   Rebuild the geometry as ONE chained LineString of the FULL Vrancea Zăbala
   course (26.39-26.78E, source at 26.3871,45.8338 → Putna confluence at
   26.7722,45.8576).

Not fixable (no OSM named geometry): Râul Zăbăluța (anpa-0680) and the Doaga
pond (anpa-0675) — both contracted AJVPS VRANCEA but invisible; documented as
no-OSM-match.

Siret click-resolution note: the Siret group (9 county contracts, Voronoi over
course_frac) is a pre-existing group-wide design limitation; this task only
makes the Vrancea sector VISIBLE + CLICKABLE. A full Siret shared-course
refactor (one geometry owner + per-county sectorStart/sectorEnd) is tracked
separately.
"""
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import core  # noqa: E402

FE_WATERS = ROOT / "public" / "data" / "waters.json"
SECTOR_FILE = ROOT / "data" / "processed" / "siret_vrancea_sector.json"
CLUSTER_CACHE = ROOT / "data" / "cache" / "osm_river_clusters.pkl"


def dedupe_parts(parts):
    """Drop parts with identical rounded (first,last) endpoints."""
    seen = set()
    out = []
    for p in parts:
        key = (round(p[0][0], 5), round(p[0][1], 5), round(p[-1][0], 5), round(p[-1][1], 5))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def chain_parts(parts):
    """Chain LineString parts by endpoint connectivity (1e-5 deg), returning
    the longest chain (flow order as stored; caller orients)."""
    parts = [list(p) for p in parts]
    used = [False] * len(parts)
    chains = []

    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    for i in range(len(parts)):
        if used[i]:
            continue
        used[i] = True
        chain = list(parts[i])
        while True:  # grow forward
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
        while True:  # grow backward
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


def orient_source_mouth(course):
    """Orient a chained course source->mouth (pitfall 15): east-flowing
    rivers (lon_span >= lat_span) have their source at smaller lon; otherwise
    the source sits at higher latitude (Romanian rivers flow from the
    mountains N/center toward S/E)."""
    if len(course) < 2:
        return course
    lons = [p[0] for p in course]
    lats = [p[1] for p in course]
    if (max(lons) - min(lons)) >= (max(lats) - min(lats)):
        if course[0][0] > course[-1][0]:
            course = course[::-1]
    else:
        if course[0][1] < course[-1][1]:
            course = course[::-1]
    return course


def linestring_bounds(coords):
    lats = [p[1] for p in coords]
    lons = [p[0] for p in coords]
    return [min(lons), min(lats), max(lons), max(lats)]


def main() -> None:
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    by_slug = {w["slug"]: w for w in waters}

    # ---------------------------------------------------------------- Siret
    sector = json.loads(SECTOR_FILE.read_text(encoding="utf-8"))
    w = by_slug["anpa-anpa-0674"]
    assert w["name"] == "Râul Siret" and w["judet"] == "Vrancea", w["name"]
    geom = sector["geometry"]
    coords = geom["coordinates"]
    w["geometry"] = geom
    w["bbox"] = linestring_bounds(coords)
    # The Siret group has 9 county entries with per-county partial geometries;
    # the group Voronoi (whole-course course_frac) can't resolve clicks on a
    # partial geometry, so declare the sector as an exact interval of its OWN
    # geometry → every click on the Vrancea Siret resolves to AJVPS VRANCEA.
    w["sectorStart"] = 0
    w["sectorEnd"] = 1
    print(f"siret-vrancea: geometry {len(coords)} pts, bbox {w['bbox']}, "
          f"first=({coords[0][0]:.4f},{coords[0][1]:.4f}) last=({coords[-1][0]:.4f},{coords[-1][1]:.4f})")

    # ----------------------------------------------------- Râmnicu Sărat
    wv = by_slug["anpa-vrancea-ramnicu-sarat"]
    assert wv["name"] == "Râul Râmnicu Sărat" and wv["judet"] == "Vrancea"
    parts = wv["geometry"]["coordinates"]
    unique = dedupe_parts(parts)
    chains = chain_parts(unique)
    course = orient_source_mouth(chains[0])
    wv["geometry"] = {"type": "LineString", "coordinates": course}
    wv["bbox"] = linestring_bounds(course)
    wv["sectorStart"] = 0
    wv["sectorEnd"] = 1
    print(f"ramnicu-sarat-vrancea: {len(course)} pts (from {len(parts)} raw incl. "
          f"{len(parts) - len(unique)} dupes), bbox {wv['bbox']}")

    wb = by_slug["anpa-anpa-0215"]
    assert wb["name"] == "Râul Râmnicu Sărat" and wb["judet"] == "Buzău"
    wb.pop("geometry", None)
    wb.pop("bbox", None)
    wb["sectorStart"] = None
    wb["sectorEnd"] = None
    print("ramnicu-sarat-buzau: geometry dropped (group-share; its old geometry "
          "was the Vrancea stretch, drawn twice)")

    # -------------------------------------------------------------- Zăbala
    clusters, _ = pickle.load(open(CLUSTER_CACHE, "rb"))
    zabala_parts = []
    for cl in clusters:
        if core(cl["name"]) != "zabala":
            continue
        # keep only clusters that touch Vrancea (excludes the Covasna Zăbala at 26.09E)
        bb = cl["bbox"]
        if bb[0] < 26.3 or bb[2] < 26.3:
            continue
        g = cl["geom"]
        if g["type"] == "MultiLineString":
            zabala_parts.extend(g["coordinates"])
        else:
            zabala_parts.append(g["coordinates"])
    unique = dedupe_parts(zabala_parts)
    chains = chain_parts(unique)
    wz = by_slug["anpa-anpa-0676"]
    assert wz["name"] == "Râul Zăbala mijlocie" and wz["judet"] == "Vrancea"
    # lon_span (0.40) >= lat_span (0.20) → source at smaller lon; the Zăbala
    # bends NE at the end (mouth lat > source lat), so a latitude heuristic
    # would wrongly flip it
    course = orient_source_mouth(chains[0])
    wz["geometry"] = {"type": "LineString", "coordinates": course}
    wz["bbox"] = linestring_bounds(course)
    print(f"zabala-mijlocie: full course {len(course)} pts "
          f"({len(zabala_parts)} raw incl. {len(zabala_parts) - len(unique)} dupes), "
          f"bbox {wz['bbox']}, first=({course[0][0]:.4f},{course[0][1]:.4f}) "
          f"last=({course[-1][0]:.4f},{course[-1][1]:.4f})")

    FE_WATERS.write_text(
        json.dumps(waters, ensure_ascii=False, indent=1) + "", encoding="utf-8")
    print(f"\nwrote {FE_WATERS} ({len(waters)} waters)")


if __name__ == "__main__":
    main()
