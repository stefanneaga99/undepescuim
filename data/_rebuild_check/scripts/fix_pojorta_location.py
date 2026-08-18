#!/usr/bin/env python3
"""Fix 'Valea Pojorâtei' (anpa-anpa-0188, Brașov, AVPS FĂGĂRAȘ) location bug
(t_a0e123da).

USER REPORT: the water rendered near Săcele/Bunloc (25.674-25.682E /
45.603-45.611N) — user: "nu are ce căuta asta aici" (nothing like that belongs
there).

ROOT CAUSE: the geocoder's fallback chain queried 'Izvoare, Brașov' (from the
contract limits 'Izvoare-Drum N.I.- vărsare și afluenții') and matched an
UNRELATED way near Săcele (way/225148394 at 25.677E/45.605N) — a stale
residential/stream point in the wrong part of the county (data/cache/geocode.db
shows the nominatim tier2 fallback). The water had NO real geometry — only the
poisoned bbox + coordinates.

THE REAL WATER: the ANPA contract row (anpa-0188, source_row 401) sits inside
the AVPS FĂGĂRAȘ block of the Făgăraș Country contracts (Valea Sâmbetei, Valea
Viștea Mare, Valea Ucea Mare, Valea Sebeșului, Râul Veneția, Valea Lisei...).
'Valea Pojorâtei' = the valley of the village Pojorta (comuna Lisa, Brașov,
45.748N/24.869E — the namesake village, on the Făgăraș Mts. north slope).
OSM relation 6257258 'Pojorta' (wikipedia ro:Râul Pojorta — one of the two
branches forming the Râul Breaza/Voila system) runs from the mountain source
(45.6034N) north to the Brescioara junction (45.6786N); the continuation
(OSM 'Voila') runs to the Olt at 45.818N. The contract limits
'Izvoare-Drum N.I.- vărsare și afluenții' = sources → national road → mouth
(the Olt), so the attached course spans Pojorta + Voila to the Olt confluence.

FIX: attach the chained Pojorta + Voila OSM course as ONE ordered LineString
(source→mouth), recompute bbox from the geometry, set coordinates to an
on-course point, set locality to the UAT (Lisa), clear geometryByCounty so the
county-clip builder recomputes, and drop the stale fallback source_detail.

Usage:
    python3 scripts/fix_pojorta_location.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
CLUSTER_PKL = ROOT / "data" / "cache" / "osm_river_clusters.pkl"

SLUG = "anpa-anpa-0188"  # Valea Pojorâtei (Brașov, AVPS FĂGĂRAȘ)
CHAIN = ["pojorta", "voila"]  # OSM cluster names in source→mouth order


def load_clusters() -> dict[str, dict]:
    with open(CLUSTER_PKL, "rb") as f:
        clusters, _ = pickle.load(f)
    by_name: dict[str, dict] = {}
    for c in clusters:
        by_name.setdefault(c["name"].lower(), c)
    return by_name


def dedupe_parts(parts: list[list[list[float]]]) -> list[list[list[float]]]:
    """Drop duplicate parts (same first+last endpoints) — OSM maps some ways
    twice (Pojorta's own cluster has two identical 160-pt parts)."""
    seen: set[tuple] = set()
    out = []
    for p in parts:
        if not p:
            continue
        ep = (tuple(p[0]), tuple(p[-1]))
        if ep in seen:
            continue
        seen.add(ep)
        out.append(p)
    return out


def haversine_km(a, b) -> float:
    R = 6371.0
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def chain_course(parts: list[list[list[float]]], bridge_km: float = 1.0) -> list[list[float]]:
    """Chain ordered source→mouth parts into one LineString, deduping shared
    junction points and bridging small mouth gaps (documented, Siret-style)."""
    out: list[list[float]] = []
    for p in parts:
        if not p:
            continue
        if out:
            last = out[-1]
            gap = haversine_km(last, p[0])
            if gap <= bridge_km and last != p[0]:
                # tiny gap at the mouth (Voila 11-pt end piece is 0.62 km from
                # the main course end) — bridge as a straight segment
                pass
            if last == p[0]:
                out.extend(p[1:])
            else:
                out.extend(p)
        else:
            out.extend(p)
    return out


def bbox_of(coords: list[list[float]]) -> list[float]:
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return [min(lons), min(lats), max(lons), max(lats)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    target = next((w for w in waters if w["slug"] == SLUG), None)
    if target is None:
        print(f"ERROR: water {SLUG} not found")
        sys.exit(1)
    if not target["judet"].startswith("Brașov") or not target["name"].startswith("Valea Pojorâtei"):
        print(f"ERROR: unexpected target: {target['name']} / {target['judet']}")
        sys.exit(1)

    clusters = load_clusters()
    parts: list[list[list[float]]] = []
    for name in CHAIN:
        c = clusters.get(name)
        if c is None:
            print(f"ERROR: cluster '{name}' missing")
            sys.exit(1)
        g = c["geom"]
        if g["type"] == "LineString":
            parts.append(g["coordinates"])
        else:
            parts.extend(g["coordinates"])
    parts = dedupe_parts(parts)
    print(f"[fix] clusters: {CHAIN}, parts after dedupe: {len(parts)}")

    # sanity: parts chain source→mouth (Pojorta stored south→north already;
    # the FE/pipeline wants source→mouth order).
    for i in range(1, len(parts)):
        gap = haversine_km(parts[i - 1][-1], parts[i][0])
        print(f"[fix] part {i-1}->{i} junction gap: {gap:.3f} km")

    course = chain_course(parts)
    print(f"[fix] chained course pts: {len(course)}")

    geometry = {"type": "LineString", "coordinates": course}
    bbox = bbox_of(course)
    print(f"[fix] new bbox: {bbox}")
    # coordinates: on-course point (midpoint of the chained course)
    mid = course[len(course) // 2]
    print(f"[fix] new coordinates: {mid}")

    if args.dry_run:
        print("[fix] DRY-RUN — no changes written")
        return

    target["geometry"] = geometry
    target["bbox"] = bbox
    target["coordinates"] = mid
    target["locality"] = "Lisa"
    target["geometryByCounty"] = {}
    target["source_detail"] = "t_a0e123da:pojorta+voila-osm-course"

    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fix] wrote {WATERS}")


if __name__ == "__main__":
    main()
