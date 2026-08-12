#!/usr/bin/env python3
"""Final QA mirroring the REAL fixer logic: distance + bbox-overlap checks."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import (load_hotosm_lakes, match_lake, match_lake_override, geo_dist_km,
                             geom_centroid, match_river_hotosm, load_hotosm_lines,
                             is_rect_poly, geom_bbox, match_lake_unnamed, load_unnamed_reservoirs,
                             pick_cluster_by_bbox, bbox_overlap_area, bbox_gap_km, is_dam_name)
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

rects = []
for w in waters:
    if w.get('bbox') and not w.get('geometry'):
        rects.append((w, 'bbox-no-geom'))
    elif is_rect_poly(w.get('geometry')):
        rects.append((w, 'rect-poly'))

print(f'QA final on {len(rects)} rects')
ok, far, no_ov = 0, [], []
for w, kind in rects:
    sub = w.get('subtype')
    geom = None
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
        if best and geom:
            gs_list = osm_geo_by_norm.get(best) or []
            repick = pick_cluster_by_bbox(w, gs_list)
            if repick:
                geom = repick
            wb = w.get('bbox')
            gb = geom_bbox(geom) if geom else None
            if (how in ('prefix','token','exact','char','no-match') and wb and gb
                    and bbox_overlap_area(wb, gb) == 0.0 and bbox_gap_km(wb, gb) > 15.0):
                best, geom, score, how = None, None, 0.0, 'far-cluster-reject'
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
            how_lake = 'lake' if lk.get('name') else 'lake-unnamed'
            bb0 = geom_bbox(lk['geom'])
            tiny = bool(bb0 and (bb0[2]-bb0[0])*(bb0[3]-bb0[1]) < 0.00005 and is_dam_name(lk['name']))
            if not tiny:
                geom = lk['geom']
    if not geom:
        continue
    gb = geom_bbox(geom)
    wb = w.get('bbox')
    c = geom_centroid(geom)
    anchor = w.get('coordinates')
    a = None
    if anchor and len(anchor) >= 2:
        a = (anchor[0], anchor[1])
    elif wb:
        a = ((wb[0]+wb[2])/2, (wb[1]+wb[3])/2)
    d = geo_dist_km(a, c) if a and c else 0
    ov = bbox_overlap_area(wb, gb) if wb and gb else 0
    ok += 1
    if d > 12:
        far.append((round(d,1), w['name'], w['judet'], w.get('slug')))
    if ov == 0 and d > 8:
        no_ov.append((round(d,1), w['name'], w['judet'], w.get('slug'), round(ov,5)))
print(f'matched-with-geometry: {ok}')
print(f'FAR (>12km): {len(far)}')
for f in sorted(far, reverse=True):
    print('  ', f)
print(f'NO-OVERLAP & >8km: {len(no_ov)}')
for f in sorted(no_ov, reverse=True):
    print('  ', f)
