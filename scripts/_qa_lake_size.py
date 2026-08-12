#!/usr/bin/env python3
"""Spot check: sample of matched lakes with polygon size + distance."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, geo_dist_km, geom_bbox

waters = json.load(open('public/data/waters.json'))
rep = json.load(open('/tmp/bbox_fix_report.json'))
lakes = load_hotosm_lakes()
by_name = {}
for l in lakes:
    by_name.setdefault(l['name'], []).append(l)

print(f"{'name':45s} {'osm':40s} {'dist':>6s} {'area':>9s}")
for m in sorted(rep['matched'], key=lambda x: x['name']):
    if m['how'] != 'lake':
        continue
    w = next((x for x in waters if x['name']==m['name'] and x['judet']==m['judet']), None)
    if not w or not w.get('coordinates'):
        continue
    cands = by_name.get(m['osm'], [])
    if not cands:
        continue
    l = min(cands, key=lambda l: geo_dist_km(w['coordinates'], l['centroid']))
    d = geo_dist_km(w['coordinates'], l['centroid'])
    bb = geom_bbox(l['geom'])
    w_deg = bb[2]-bb[0] if bb else 0
    h_deg = bb[3]-bb[1] if bb else 0
    print(f"{m['name'][:44]:45s} {m['osm'][:39]:40s} {d:5.1f} {w_deg*h_deg*12300:8.0f} km2")
