#!/usr/bin/env python3
"""QA: for each water the fixer matched, compute anchor -> matched-geometry centroid distance."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import (load_hotosm_lakes, match_lake, match_lake_override, geo_dist_km,
                             geom_centroid, match_river_hotosm, load_hotosm_lines,
                             is_rect_poly, geom_bbox)
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

print(f'QA on {len(rects)} rects')
far = []
for w, kind in rects:
    sub = w.get('subtype')
    anchor = w.get('coordinates')
    geom = None
    if sub == 'rau':
        best, geom, score, how = best_osm_match(w, osm_geo_by_norm, county_centroids)
        if not best:
            best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
            if best and geom:
                c = geom_centroid(geom)
                if anchor and len(anchor) >= 2 and c and geo_dist_km(anchor, c) > 40.0:
                    best, geom, score, how = None, None, 0.0, 'override-anchor-reject'
        if not best:
            hname, hgeom, hscore = match_river_hotosm(w, hot_lines, county_centroids)
            if hgeom:
                best, geom, score, how = hname, hgeom, hscore, 'hotosm'
        if not best and kind == 'rect-poly':
            lk = match_lake(w, lakes)
            if not lk:
                lk = match_lake_override(w, lakes)
            if lk:
                best, geom, score, how = lk['name'], lk['geom'], 0.0, 'lake'
    elif sub == 'lac':
        lk = match_lake(w, lakes)
        if not lk:
            lk = match_lake_override(w, lakes)
        if lk:
            geom = lk['geom']
    if not geom:
        continue
    c = geom_centroid(geom)
    if not c:
        continue
    # anchor: coordinates or bbox center
    a = None
    if anchor and len(anchor) >= 2:
        a = (anchor[0], anchor[1])
    elif w.get('bbox'):
        b = w['bbox']
        a = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    if not a:
        continue
    d = geo_dist_km(a, c)
    flag = '<<<' if d > 12 else ''
    if d > 12:
        far.append((round(d,1), w['name'], w['judet'], w.get('slug'), flag))
    print(f'  {d:6.1f}km {flag} {w["name"][:38]:38s} | {w["judet"]:10s} | {w.get("slug"):30s}')
print(f'\nFAR (>12km): {len(far)}')
for f in sorted(far, reverse=True):
    print('  ', f)
