#!/usr/bin/env python3
"""Check bistra + topa clusters near Alba/Bihor anchors."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms, geom_centroid
from fix_bbox_waters import geo_dist_km

name_index, geoms = load_osm_index()
waters = json.load(open('public/data/waters.json'))

def clusters_for(term):
    out = []
    for n, ids in name_index.items():
        if term in n:
            for g in make_cluster_geoms(ids, geoms):
                c = geom_centroid(g)
                if c:
                    out.append((n, c))
    return out

print("=== bistra clusters ===")
for n, c in clusters_for('bistra'):
    print(f"   '{n}' centroid={tuple(round(x,2) for x in c)}")

print("\n=== topa clusters ===")
for n, c in clusters_for('topa'):
    print(f"   '{n}' centroid={tuple(round(x,2) for x in c)}")

# anchors
for slug in ['ys4a4vw8', 'p3puv4bx', 'yjbfm1tc', 'zdjui15p', '1zqkhha4']:
    w = next(x for x in waters if x['slug']==slug)
    print(f"\n{w['name']} ({w['judet']}) coord={w['coordinates']}")
    for n, c in clusters_for('bistra') + clusters_for('topa'):
        d = geo_dist_km(w['coordinates'], c)
        if d < 200:
            print(f"   {n:25s} d={d:.1f}km centroid={tuple(round(x,2) for x in c)}")
