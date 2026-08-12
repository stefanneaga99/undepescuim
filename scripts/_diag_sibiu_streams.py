#!/usr/bin/env python3
"""Check OSM river ways near the reported Fagaras-area stream coordinates."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms
from fix_bbox_waters import geo_dist_km

name_index, geoms = load_osm_index()
waters = json.load(open('public/data/waters.json'))

# the 4 Sibiu streams in the report area
for slug in ['gxjd56ii', '1f162p36', 'fzusfkv6', '1xe7y7xg']:
    w = next(x for x in waters if x['slug']==slug)
    print(f"\n### {w['name']} coord={w['coordinates']}")
    # find all named OSM clusters within 3km
    hits = []
    for n, ids in name_index.items():
        for g in make_cluster_geoms(ids, geoms):
            coords = g['coordinates'] if g['type']=='LineString' else [p for part in g['coordinates'] for p in part]
            if not coords: continue
            lats=[p[1] for p in coords]; lons=[p[0] for p in coords]
            c = (sum(lons)/len(lons), sum(lats)/len(lats))
            d = geo_dist_km(w['coordinates'], c)
            if d < 3.0:
                hits.append((d, n, g['type']))
    hits.sort()
    for d, n, t in hits[:10]:
        print(f"   d={d:4.1f}km | {n} | {t}")
