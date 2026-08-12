#!/usr/bin/env python3
"""Find OSM streams near Topa commune (Bihor)."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms, geom_centroid
from fix_bbox_waters import geo_dist_km

name_index, geoms = load_osm_index()
anchor = (22.2471748, 46.9319458)  # Topa-Holod
hits = []
for n, ids in name_index.items():
    for g in make_cluster_geoms(ids, geoms):
        c = geom_centroid(g)
        if c:
            d = geo_dist_km(anchor, c)
            if d < 30:
                hits.append((d, n))
hits.sort()
print("=== OSM rivers within 30km of Topa commune ===")
for d, n in hits[:20]:
    print(f"   {d:5.1f}km | {n}")
