#!/usr/bin/env python3
"""Verify RIVER_OVERRIDES merge works with try_manual_override."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import (build_county_centroids, load_osm_index,
                                   make_cluster_geoms, try_manual_override)
import fix_bbox_waters as fbx

waters = json.load(open('public/data/waters.json'))
name_index, geoms = load_osm_index()
osm_geo_by_norm = {}
for n, ids in name_index.items():
    gs = make_cluster_geoms(ids, geoms)
    if gs:
        osm_geo_by_norm[n] = gs
county_centroids = build_county_centroids(waters)

# simulate main()'s merge
merged = dict(fbx.MANUAL_OVERRIDES)
merged.update(fbx.RIVER_OVERRIDES)
import audit_missing_rivers as amr
amr.MANUAL_OVERRIDES = merged

for slug in ['gunskubl', 'm2x1jtkp', '1xe7y7xg']:
    w = next(x for x in waters if x['slug']==slug)
    best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
    print(f"{w['name']} -> {best} score={score:.3f} how={how}")
