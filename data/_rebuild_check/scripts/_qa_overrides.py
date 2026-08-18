#!/usr/bin/env python3
"""Verify suspicious override matches with county-aware cluster pick."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import (build_county_centroids, load_osm_index, make_cluster_geoms,
                                   geom_centroid, try_manual_override, core, county_penalty_for)
from fix_bbox_waters import geo_dist_km

waters = json.load(open('public/data/waters.json'))
name_index, geoms = load_osm_index()
osm_geo_by_norm = {}
for n, ids in name_index.items():
    gs = make_cluster_geoms(ids, geoms)
    if gs:
        osm_geo_by_norm[n] = gs
county_centroids = build_county_centroids(waters)

# replicate the merged overrides
import fix_bbox_waters as fbx
import audit_missing_rivers as amr
merged = dict(amr.MANUAL_OVERRIDES)
merged.update(fbx.RIVER_OVERRIDES)
amr.MANUAL_OVERRIDES = merged

cases = ['1xe7y7xg', 'ys4a4vw8', 'p3puv4bx', 'yjbfm1tc', 'zdjui15p', '1zqkhha4', 'z6x8mxh5', '20u2sj3u']
for slug in cases:
    w = next(x for x in waters if x['slug']==slug)
    best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
    if best and geom:
        c = geom_centroid(geom)
        d = geo_dist_km(w.get('coordinates'), c) if w.get('coordinates') and c else None
        print(f"{w['name']:28s} ({w['judet']}) -> {best} d={d and round(d,1)}km score={score:.2f} how={how}")
    else:
        print(f"{w['name']:28s} ({w['judet']}) -> NO MATCH ({how})")
