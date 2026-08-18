#!/usr/bin/env python3
"""Debug specific failing lake matches."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, match_lake, lake_core, lake_alts, norm, geo_dist_km

lakes = load_hotosm_lakes()
waters = json.load(open('public/data/waters.json'))

for slug in ['5u62qpuc', '3cffswnd', 'dkyhyd7w', 'f2wdjbfr', 'jrlgyh2h']:
    w = next(x for x in waters if x['slug']==slug)
    print(f"\n### {w['name']} ({w['judet']})")
    print(f"   core='{lake_core(w['name'])}' alts={lake_alts(w['name'])}")
    lk = match_lake(w, lakes)
    print(f"   match_lake -> {lk['name'] if lk else None}")
    for l in lakes:
        if l['core'] and set(l['core'].split()) & set(lake_core(w['name']).split()):
            d = geo_dist_km(w['coordinates'], l['centroid'])
            if d < 12:
                print(f"     cand: {l['name']:45s} core='{l['core']}' d={d:.1f}km")
