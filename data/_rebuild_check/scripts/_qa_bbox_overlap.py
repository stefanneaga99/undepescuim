#!/usr/bin/env python3
"""Verify far matches: does the attached geometry bbox overlap the water's original bbox?."""
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

def bbox_overlap(b1, b2):
    """[lng_min, lat_min, lng_max, lat_max] overlap area approx."""
    if not b1 or not b2:
        return 0.0
    dx = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    dy = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    return dx * dy

rects = []
for w in waters:
    if w.get('bbox') and not w.get('geometry'):
        rects.append((w, 'bbox-no-geom'))
    elif is_rect_poly(w.get('geometry')):
        rects.append((w, 'rect-poly'))

print(f'QA bbox-overlap on {len(rects)} rects')
issues = []
for w, kind in rects:
    sub = w.get('subtype')
    geom = None
    if sub == 'rau':
        best, geom, score, how = best_osm_match(w, osm_geo_by_norm, county_centroids)
        if not best:
            best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
        if not best:
            hname, hgeom, hscore = match_river_hotosm(w, hot_lines, county_centroids)
            if hgeom:
                best, geom, score, how = hname, hgeom, hscore, 'hotosm'
        if not best and kind == 'rect-poly':
            lk = match_lake(w, lakes)
            if not lk:
                lk = match_lake_override(w, lakes)
            if not lk:
                lk = match_lake_unnamed(w, unnamed)
            if lk:
                best, geom, score, how = lk['name'], lk['geom'], 0.0, 'lake'
    elif sub == 'lac':
        lk = match_lake(w, lakes)
        if not lk:
            lk = match_lake_override(w, lakes)
        if not lk:
            lk = match_lake_unnamed(w, unnamed)
        if lk:
            geom = lk['geom']
    if not geom:
        continue
    gb = geom_bbox(geom)
    wb = w.get('bbox')
    ov = bbox_overlap(wb, gb)
    anchor = w.get('coordinates')
    a = None
    if anchor and len(anchor) >= 2:
        a = (anchor[0], anchor[1])
    elif wb:
        a = ((wb[0]+wb[2])/2, (wb[1]+wb[3])/2)
    c = geom_centroid(geom)
    d = geo_dist_km(a, c) if a and c else 0
    if d > 12:
        print(f'  d={d:6.1f}km overlap={ov:.5f} {w["name"][:34]:34s} | {w["judet"]:10s} | {w.get("slug")}')
        if ov < 0.01:
            issues.append((round(d,1), w['name'], w['judet'], w.get('slug'), round(ov,5)))
print(f'\nNO-OVERLAP ISSUES (>12km AND bbox overlap <0.01): {len(issues)}')
for i in issues:
    print('  ', i)
