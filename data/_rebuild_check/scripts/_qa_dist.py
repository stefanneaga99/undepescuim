#!/usr/bin/env python3
"""Quality check: distance between each matched water anchor and its new geometry centroid."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, geo_dist_km, geom_centroid

waters = json.load(open('public/data/waters.json'))
rep = json.load(open('/tmp/bbox_fix_report.json'))

# reload waters with the matched geometry? No — report has names only. Instead
# recompute by simulating: we need water -> geometry. Use the report + waters.json
# to compute distances from anchor to the matched lake centroid.
lakes = load_hotosm_lakes()
lake_by_name = {}
for l in lakes:
    lake_by_name.setdefault(l['name'], []).append(l)

print("=== MATCHED lakes with distance > 12km (suspicious) ===")
for m in rep['matched']:
    if m['how'] != 'lake':
        continue
    w = next((x for x in waters if x['name'] == m['name'] and x['judet'] == m['judet']), None)
    if not w or not w.get('coordinates'):
        continue
    cands = lake_by_name.get(m['osm'], [])
    if not cands:
        continue
    d = min(geo_dist_km(w['coordinates'], l['centroid']) for l in cands)
    if d > 12:
        print(f"   {d:6.1f}km | {m['name']} ({m['judet']}) -> {m['osm']}")
