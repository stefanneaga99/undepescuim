#!/usr/bin/env python3
"""Inspect suspicious far matches: water bbox vs matched geometry bbox."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import (load_hotosm_lakes, match_lake, match_lake_override, geo_dist_km,
                             geom_centroid, match_river_hotosm, load_hotosm_lines,
                             is_rect_poly, geom_bbox, match_lake_unnamed, load_unnamed_reservoirs)
from audit_missing_rivers import (build_county_centroids, load_osm_index, make_cluster_geoms,
                                  best_osm_match, try_manual_override, MANUAL_OVERRIDES)
import fix_bbox_waters as fbx

waters = json.load(open('public/data/waters.json'))
name_index, geoms = load_osm_index()
osm_geo_by_norm = {}
for n, ids in name_index.items():
    gs = make_cluster_geoms(ids, geoms)
    if gs:
        osm_geo_by_norm[n] = gs
county_centroids = build_county_centroids(waters)
lakes = load_hotosm_lakes()
hot_lines = load_hotosm_lines()
unnamed = load_unnamed_reservoirs()

merged = dict(MANUAL_OVERRIDES)
merged.update(fbx.RIVER_OVERRIDES)
import audit_missing_rivers as amr
amr.MANUAL_OVERRIDES = merged

slugs = ['gutqod71','d5xhbhta','z8u6g69z','2g9hg98a','2dxykcpr','k44320iw','c1gifahb','0wn4yfsa','yfzdgchv','20u2sj3u']
for slug in slugs:
    w = next((x for x in waters if x['slug']==slug), None)
    if not w:
        print(f'--- {slug}: NOT FOUND'); continue
    wb = w.get('bbox')
    print(f'=== {w["name"]} ({w["judet"]}) anchor={w.get("coordinates")} bbox={[round(v,3) for v in wb]}')
    sub = w.get('subtype')
    geom = None; how = '?'
    if sub == 'rau':
        best, geom, score, how = best_osm_match(w, osm_geo_by_norm, county_centroids)
        if not best:
            best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
            if best and geom:
                anchor = w.get('coordinates')
                if anchor and len(anchor) >= 2:
                    c = geom_centroid(geom)
                    if c and geo_dist_km(anchor, c) > 40.0:
                        best, geom, score, how = None, None, 0.0, 'override-anchor-reject'
        if not best:
            hname, hgeom, hscore = match_river_hotosm(w, hot_lines, county_centroids)
            if hgeom:
                best, geom, score, how = hname, hgeom, hscore, 'hotosm'
        print(f'   matched: {best} [{how}] score={score}')
    if geom:
        gb = geom_bbox(geom)
        c = geom_centroid(geom)
        print(f'   geom bbox: {[round(v,3) for v in gb]} centroid={[round(x,3) for x in c]}')
        ov_dx = max(0.0, min(wb[2],gb[2])-max(wb[0],gb[0]))
        ov_dy = max(0.0, min(wb[3],gb[3])-max(wb[1],gb[1]))
        print(f'   overlap: {ov_dx*ov_dy:.5f} water-bbox {[round(v,2) for v in wb]}')
    else:
        print('   -> NO MATCH in real fixer logic')
