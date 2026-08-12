#!/usr/bin/env python3
"""Check Izvorul Lotrului HOTOSM match quality."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lines, match_river_hotosm, geom_centroid, geo_dist_km
from audit_missing_rivers import build_county_centroids

waters = json.load(open('public/data/waters.json'))
hot_lines = load_hotosm_lines()
county_centroids = build_county_centroids(waters)

w = next(x for x in waters if x['slug'] == 'romsilva-valcea-izvorul-lotrului')
print("water:", w['name'], w['judet'], "coord:", w.get('coordinates'))
hname, hgeom, hscore = match_river_hotosm(w, hot_lines, county_centroids)
print(f"matched: {hname} score={hscore}")
if hgeom:
    print("centroid:", geom_centroid(hgeom))

# list all candidates containing 'izvorul'
for lname, fl in sorted(hot_lines.items()):
    if 'izvorul' in lname:
        c = geom_centroid(fl[0]['geom'])
        d = geo_dist_km(w.get('coordinates') or (24.5, 45.4), c) if c else None
        print(f"   {lname}: centroid={c} dist={d and round(d,1)}km")
