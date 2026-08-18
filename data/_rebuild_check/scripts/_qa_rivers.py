#!/usr/bin/env python3
"""QA: river match distance check using OSM index + HOTOSM lines."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms, geom_centroid
from fix_bbox_waters import geo_dist_km, load_hotosm_lines

waters = json.load(open('public/data/waters.json'))
rep = json.load(open('/tmp/bbox_fix_report.json'))

name_index, geoms = load_osm_index()
osm_geo = {}
for n, ids in name_index.items():
    gs = make_cluster_geoms(ids, geoms)
    if gs:
        osm_geo[n] = gs
hot_lines = load_hotosm_lines()

print("=== river matches: distance from anchor to geometry centroid ===")
for m in rep['matched']:
    if m['how'] not in ('prefix', 'override', 'hotosm', 'exact', 'token', 'char'):
        continue
    w = next((x for x in waters if x['name'] == m['name'] and x['judet'] == m['judet']), None)
    if not w or not w.get('coordinates'):
        continue
    if m['how'] == 'hotosm':
        fl = hot_lines.get(m['osm'], [])
        if not fl: continue
        c = geom_centroid(fl[0]['geom'])
    else:
        gs = osm_geo.get(m['osm'], [])
        if not gs: continue
        c = geom_centroid(gs[0])
    if not c: continue
    d = geo_dist_km(w['coordinates'], c)
    flag = "  <<< SUSPICIOUS" if d > 30 else ""
    print(f"   {d:6.1f}km | {m['name']} ({m['judet']}) -> {m['osm']} [{m['how']}]{flag}")
