#!/usr/bin/env python3
"""Debug remaining Olt reservoir lakes."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, match_lake, lake_core, lake_alts, geo_dist_km

lakes = load_hotosm_lakes()
waters = json.load(open('public/data/waters.json'))

for slug in ['urjxx6ca', 'dp9lbuy0', 'jw34gyf2', 'b0niobr0', 'pdf2udss', '5dsa9h8a', '8zv453rs',
             'gvxr867o', 'bc4yxt09', 'of2qtm1a', 'jni4xw19', '0tzvnk1y', 'aersxf9e', 'n4unwsj0',
             '8a8nlp4g', 'hiex82px', '6mk6gsnk', 's5eabntg', 'vcv45quw', '1naqeaio', 'pzvjb5io',
             '1zx8h34h', '879hgsjs', 'jn6h7vl1', '0xm8hfpq', 'e4ohjj3a', 'mmakw97b', '4fg24m45',
             'sk57b228', 'soxnke0k', 'm7tbtlwq', '315lt84w']:
    w = next((x for x in waters if x['slug']==slug), None)
    if not w: continue
    anchor = w.get('coordinates')
    if not anchor: continue
    print(f"\n### {w['name']} ({w['judet']}) core='{lake_core(w['name'])}'")
    # all named polys within 6km
    near = []
    for l in lakes:
        d = geo_dist_km(anchor, l['centroid'])
        if d < 6.0:
            near.append((d, l))
    near.sort(key=lambda x: x[0])
    for d, l in near[:6]:
        print(f"   d={d:4.1f}km | {l['name'][:55]:55s} | core='{l['core']}' | water={l['water']}")
