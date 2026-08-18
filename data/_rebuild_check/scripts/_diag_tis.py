#!/usr/bin/env python3
"""Debug Tismana/Vaja matching."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, match_lake, lake_core, lake_alts, article_variants, norm, char_sim

lakes = load_hotosm_lakes()
waters = json.load(open('public/data/waters.json'))

for slug in ['n4unwsj0', '8a8nlp4g', 'z8u6g69z']:
    w = next(x for x in waters if x['slug']==slug)
    print(f"\n### {w['name']} ({w['judet']}) core='{lake_core(w['name'])}' alts={lake_alts(w['name'])}")
    lk = match_lake(w, lakes)
    print(f"   match -> {lk['name'] if lk else None}")
    for l in lakes:
        if l['core'] and lake_core(l['core']) == lake_core(w['name']):
            print(f"   EXACT-CORE cand: {l['name']} core='{l['core']}'")
    # check what the candidate's core variants look like
    for l in lakes:
        if l['name'] and 'tismana' in l['norm']:
            print(f"   tismana: {l['name']} core='{l['core']}' variants={article_variants(l['core'].split())}")
        if l['name'] and 'vaja' in l['norm']:
            print(f"   vaja: {l['name']} core='{l['core']}' variants={article_variants(l['core'].split())}")
