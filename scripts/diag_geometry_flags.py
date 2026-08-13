#!/usr/bin/env python3
"""Diagnostic: for each flagged water, list candidate OSM clusters AND lakes
with their majority county, so unresolved cases can be reviewed by hand."""
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_geometry_county import flag_waters
from fix_wrong_county_geometry import (
    load_county_polygons, county_of_cluster, name_variants, core,
)

waters = json.loads((ROOT / "public/data/waters.json").read_text(encoding="utf-8"))
polygons = load_county_polygons()
flagged, _ = flag_waters(waters, polygons)
slugs = {r["slug"] for r in flagged}

with open(ROOT / "data/cache/osm_river_clusters.pkl", "rb") as f:
    clusters, _ = pickle.load(f)
lakes = json.loads((ROOT / "data/processed/overpass_named_lakes.json").read_text(encoding="utf-8"))

from collections import defaultdict
by_norm = defaultdict(list)
for cl in clusters:
    by_norm[cl["norm"]].append(cl)
lakes_by_norm = defaultdict(list)
for l in lakes:
    lakes_by_norm[l.get("norm") or ""].append(l)

def candidates_for(variants, wcore, by_norm):
    cands = []
    seen = set()
    for v in variants:
        for cl in by_norm.get(v, []):
            if id(cl) not in seen:
                seen.add(id(cl))
                cands.append(cl)
    for nk, cls_ in by_norm.items():
        if nk in variants:
            continue
        if core(nk) == wcore and len(nk) >= 4:
            for cl in cls_:
                if id(cl) not in seen:
                    seen.add(id(cl))
                    cands.append(cl)
    return cands

for w in waters:
    if w["slug"] not in slugs:
        continue
    name = w.get("name") or ""
    declared = w.get("judet") or "?"
    variants = name_variants(name)
    wcore = core(name)
    print(f"\n=== {declared} | {name} | slug={w['slug']} | old_bbox={w.get('bbox')}")
    print(f"    variants={sorted(variants)} core={wcore}")
    rcands = candidates_for(variants, wcore, by_norm)
    print(f"    RIVER candidates:")
    for cl in rcands:
        county, hits = county_of_cluster(cl, polygons)
        print(f"      {cl.get('raw_name') or cl['name']:28} norm={cl['norm']:24} county={county!s:16} hits={hits:3} bbox={[round(v,2) for v in cl['bbox']]}")
    lcands = candidates_for(variants, wcore, lakes_by_norm)
    if lcands:
        print(f"    LAKE candidates:")
        for cl in lcands:
            county, hits = county_of_cluster(cl, polygons)
            bb = None
            try:
                from validate_geometry_county import bbox_of_points, water_points
                pts = water_points({"geometry": cl["geom"]})
                if pts:
                    bb = bbox_of_points(pts)
            except Exception:
                pass
            print(f"      {cl.get('name') or '?':28} norm={cl.get('norm','')[:24]:24} county={county!s:16} hits={hits:3} bbox={bb and [round(v,2) for v in bb]}")
