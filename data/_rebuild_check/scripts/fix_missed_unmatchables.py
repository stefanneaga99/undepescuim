#!/usr/bin/env python3
"""Targeted fixes for t_68dabead re-run (run 127): two misses found by a
fuzzy re-scan of the 22 'documented unmatchable' bbox-only waters.

1. Pârâul Murgoci (ii25s9zo, Vâlcea) <- OSM 'Valea Murgaciu' cluster
   (15-pt LineString 24.218-24.222E / 45.479-45.484N, fully inside the
   water's bbox, 100% in Vâlcea; contract limits 'izvoare - conf. Râul Uria'
   and the sister contract anpa-0644 'Valea Urii cu pâraiele Uria și Murgoci'
   ends at (24.2275, 45.4834) — the Murgaciu course ends at (24.2222,45.4838),
   ~0.5 km from the Uria mouth. Same stream, OSM name variant.)

2. Valea Curpenului (anpa-anpa-0631, Vâlcea) <- OSM 'Curpănu' cluster
   (291-pt course, bbox 24.2725-24.3359E / 45.5338-45.5712N, contains the
   water bbox; village Curpănu (Câineni, Vâlcea) sits on the course at
   45.5366,24.3096; Wikipedia's Râul Olt tributary list includes 'Curpănu'
   matching the contract 'Afluent Râul Olt'. OSM name variant of
   'Valea Curpenului'.)

Both were missed by the sweep's name ladder (Murgoci vs Murgaciu, Curpenului
vs Curpănu are not token/prefix matches). Validator must report 0 flags after.
"""
from __future__ import annotations
import json, math, pickle, sys
from pathlib import Path
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
CLUSTER_PKL = ROOT / "data" / "cache" / "osm_river_clusters.pkl"
COUNTY_DIR = ROOT / "data" / "raw" / "county_boundaries"
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_remaining_geometry import (  # reuse helpers
    norm, core, cluster_points, geom_bbox, county_hits, order_linestring,
    load_county_polygons,
)

FIXES = {
    "ii25s9zo": "valea murgaciu",          # Pârâul Murgoci, Vâlcea
    "anpa-anpa-0631": "curpanu",           # Valea Curpenului, Vâlcea (OSM norm)
}

def main():
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    with open(CLUSTER_PKL, "rb") as f:
        clusters, _cell = pickle.load(f)
    by_norm = {}
    for cl in clusters:
        by_norm.setdefault(cl["norm"], []).append(cl)

    # county polygons
    polygons = load_county_polygons()

    changed = []
    for slug, target_norm in FIXES.items():
        w = next((x for x in waters if x["slug"] == slug), None)
        if w is None:
            print(f"!! {slug} not found")
            continue
        cands = by_norm.get(target_norm, [])
        if not cands:
            print(f"!! {slug}: cluster '{target_norm}' not found")
            continue
        cl = cands[0]
        cname = cl.get("raw_name") or cl["name"]
        g = cl["geom"]
        pts = cluster_points(g)
        in_dec, majority, total = county_hits(pts, polygons, w["judet"])
        print(f"{w['name']} [{w['judet']}] <- '{cname}' in-county {in_dec}/{total} majority {majority}")
        if in_dec == 0 or norm(majority or "") != norm(w["judet"]):
            print(f"  !! county guard FAILED — skipping {slug}")
            continue
        out_geom = order_linestring(g) if g.get("type") in ("LineString", "MultiLineString") else g
        w["geometry"] = out_geom
        bb = geom_bbox(out_geom)
        w["bbox"] = [round(v, 5) for v in bb] if bb else None
        w["source_detail"] = "sweep_remaining:manual-miss-fix"
        w["geometryByCounty"] = {}
        w.pop("hidden", None)
        changed.append(w)
        print(f"  FIXED {slug}: geom={out_geom['type']} pts={len(out_geom['coordinates']) if out_geom['type']=='LineString' else [len(p) for p in out_geom['coordinates']]} bbox={w['bbox']}")

    if not changed:
        print("nothing changed")
        return

    WATERS.write_text(
        json.dumps(waters, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"wrote {WATERS} ({len(changed)} waters changed)")

if __name__ == "__main__":
    main()
