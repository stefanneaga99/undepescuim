#!/usr/bin/env python3
"""Sweep: waters whose geometry is a single OSM way while OSM splits the same
river into multiple ways (Năruja class of bug, t_00319387).

For each water with a LineString geometry, look up all OSM geometries sharing
its name, find the spatially-matching cluster, and if that cluster has >1 part,
rebuild the course as ONE chained, ordered LineString (source→mouth):

  - dedupe duplicated ways (same first/last endpoints — OSM maps some ways twice)
  - chain parts by endpoint connectivity (gaps <= eps), not latitude — E-W
    rivers (Năruja flows east into Zăbala) break the latitude heuristic
  - orient source→mouth using, in order of strength:
      1. the existing water geometry's own first coordinate (preserve the
         digitization direction of the OSM way the water already carries)
      2. course-direction rule: E-W dominated course → source at smaller lon
         (Carpathians W/N, Danube/Siret S/E); N-S dominated → source at
         higher lat
  - emit a SINGLE LineString so the FE's PCA orderParts is a no-op and
    fractionAtPoint / click-resolution walk the course monotonically.

Usage:
  python3 scripts/sweep_multiway_rivers.py            # diagnostic report
  python3 scripts/sweep_multiway_rivers.py --write    # apply to waters.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"

sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import load_osm_index, make_cluster_geoms, norm  # noqa: E402

EPS = 1e-5  # degrees — shared junction tolerance


def geom_parts(g: dict) -> list[list[list[float]]]:
    if g["type"] == "LineString":
        return [g["coordinates"]]
    return g["coordinates"]


def chain_parts(parts: list[list[list[float]]]) -> list[list[list[float]]] | None:
    """Dedupe + order parts into a single connected chain. Returns None when the
    parts don't form one contiguous path (parallel/braided or disconnected)."""
    # Dedupe: identical (first,last) endpoints = same way mapped twice.
    seen: set[tuple] = set()
    unique = []
    for p in parts:
        ep = (tuple(p[0]), tuple(p[-1]))
        rev = (tuple(p[-1]), tuple(p[0]))
        if ep in seen or rev in seen:
            continue
        seen.add(ep)
        unique.append([list(c) for c in p])
    if len(unique) == 1:
        return unique

    def near(a, b) -> bool:
        return abs(a[0] - b[0]) <= EPS and abs(a[1] - b[1]) <= EPS

    def endpoints(p) -> tuple[list, list]:
        return p[0], p[-1]

    # Build adjacency by endpoint proximity. Each part has two endpoints; a
    # connected chain of N parts must have exactly 2 degree-1 ends.
    used = [False] * len(unique)
    chain = [unique[0]]
    used[0] = True
    # grow from both ends of the current chain
    while len(chain) < len(unique):
        head, tail = chain[0][0], chain[-1][-1]
        progressed = False
        for i, p in enumerate(unique):
            if used[i]:
                continue
            a, b = endpoints(p)
            if near(a, tail):          # p starts where chain ends
                chain.append(p)
                used[i] = True
                progressed = True
                break
            if near(b, tail):          # p is reversed
                chain.append(list(reversed(p)))
                used[i] = True
                progressed = True
                break
            if near(b, head):          # p ends where chain starts
                chain.insert(0, p)
                used[i] = True
                progressed = True
                break
            if near(a, head):          # p reversed at head
                chain.insert(0, list(reversed(p)))
                used[i] = True
                progressed = True
                break
        if not progressed:
            return None  # disconnected parts (braided river, different basins)
    return chain


def orient_chain(chain: list[list[list[float]]], anchor_first=None,
                 anchor_last=None) -> list[list[list[float]]]:
    """Orient the chained parts source→mouth.

    Locates the old geometry's first/last coordinates along the natural
    (connectivity) chain and keeps natural order iff old_first precedes
    old_last — the old geometry already encodes the OSM digitization direction
    of the way(s) the water carries. When no anchor matches, falls back to a
    course-direction rule (E-W → source at smaller lon; N-S → source at higher
    lat, Romanian orography)."""
    if len(chain) <= 1:
        return chain
    flat = flatten(chain)["coordinates"]

    def nearest_idx(pt):
        if pt is None:
            return None
        best, bd = 0, 1e18
        for i, c in enumerate(flat):
            d = (c[0] - pt[0]) ** 2 + (c[1] - pt[1]) ** 2
            if d < bd:
                bd, best = d, i
        return best

    i0 = nearest_idx(anchor_first)
    i1 = nearest_idx(anchor_last)
    if i0 is not None and i1 is not None and i0 != i1:
        # keep natural order iff old geometry points toward the chain end
        return chain if i0 < i1 else list(reversed(chain))
    s = chain[0][0]
    t = chain[-1][-1]
    all_pts = [c for p in chain for c in p]
    lon_span = max(c[0] for c in all_pts) - min(c[0] for c in all_pts)
    lat_span = max(c[1] for c in all_pts) - min(c[1] for c in all_pts)
    if lon_span >= lat_span:
        return chain if s[0] <= t[0] else list(reversed(chain))
    return chain if s[1] >= t[1] else list(reversed(chain))


def flatten(chain: list[list[list[float]]]) -> dict:
    out: list[list[float]] = []
    for p in chain:
        if out and out[-1] == p[0]:
            out.extend(p[1:])
        else:
            out.extend(p)
    return {"type": "LineString", "coordinates": out}


def geom_bbox(g: dict) -> list[float] | None:
    coords = g["coordinates"] if g["type"] == "LineString" else [
        p for part in g["coordinates"] for p in part]
    if not coords:
        return None
    return [min(c[0] for c in coords), min(c[1] for c in coords),
            max(c[0] for c in coords), max(c[1] for c in coords)]


def bbox_overlap(a: list[float], b: list[float]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    name_index, geoms = load_osm_index()
    osm_by_norm = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_by_norm[n] = gs
    print(f"[sweep] OSM index: {len(name_index)} names -> clusters ready")

    fixed = []
    checked = 0
    for w in waters:
        g = w.get("geometry")
        if not g or g["type"] != "LineString" or not g.get("coordinates"):
            continue
        checked += 1
        clusters = osm_by_norm.get(norm(w.get("name", "")))
        if not clusters:
            continue
        wbb = geom_bbox(g)
        # find the cluster matching this water's geometry
        match = None
        for cl in clusters:
            cl_parts = geom_parts(cl)
            if len(cl_parts) < 2:
                continue
            cbb = geom_bbox(cl)
            if wbb and cbb and bbox_overlap(wbb, cbb):
                match = cl
                break
        if match is None:
            continue
        parts = geom_parts(match)
        chain = chain_parts(parts)
        if chain is None or len(chain) <= 1:
            continue
        anchor = g["coordinates"][0]
        anchor_last = g["coordinates"][-1]
        chain = orient_chain(chain, anchor_first=anchor, anchor_last=anchor_last)
        new_geom = flatten(chain)
        # only replace when the new course actually covers MORE of the river
        if len(new_geom["coordinates"]) <= len(g["coordinates"]):
            continue
        old_last = g["coordinates"][-1]
        new_last = new_geom["coordinates"][-1]
        w["geometry"] = new_geom
        bb = geom_bbox(new_geom)
        if bb and (bb[2] - bb[0]) > 1e-9 and (bb[3] - bb[1]) > 1e-9:
            w["bbox"] = [round(v, 6) for v in bb]
        w["source_detail"] = "multiway_chain"
        fixed.append({
            "slug": w["slug"], "name": w["name"], "judet": w.get("judet"),
            "old_pts": len(g["coordinates"]), "new_pts": len(new_geom["coordinates"]),
            "parts": len(parts), "old_last": old_last, "new_last": new_last,
        })

    print(f"[sweep] waters with LineString geometry checked: {checked}")
    print(f"[sweep] fixed {len(fixed)} multi-way rivers:")
    for f in sorted(fixed, key=lambda x: x["name"]):
        print(f"   {f['name']} ({f['judet']})  {f['old_pts']} -> {f['new_pts']} pts "
              f"({f['parts']} OSM parts); old last {f['old_last']} -> new last {f['new_last']}")

    if args.write and fixed:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
