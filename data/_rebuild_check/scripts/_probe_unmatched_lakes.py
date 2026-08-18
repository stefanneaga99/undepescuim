#!/usr/bin/env python3
"""Check unnamed/nearby polygon candidates for unmatched lakes."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, geo_dist_km, lake_core, norm

lakes = load_hotosm_lakes()
waters = json.load(open('public/data/waters.json'))

# slugs to inspect: unmatched lac waters
unmatched_lac = ['hdqe290r','lpfud98o','igheqrti','hvdfyvij','3cffswnd','dkyhyd7w',
'f2wdjbfr','6btfaim0','1srym7dd','u9i0nipn','h0h6821t','8pel9fyb','093wq4lp','u74mudgv','v568f04x',
'kmxvcyrc','7bs2dlc0','w3jwqryr','i5wd80if','jrlgyh2h','eovhns40','hvy996q6','ttge8n5u',
'7yg1hoia','mkp5r52j','anpa-brasov-arpasu','5l9byf37','2vlxdbig','0qrpg5nz','sctzx1ju',
'99auwn3e','aersxf9e','arrd8tai','v9q2bw1j','n4unwsj0','8a8nlp4g','hiex82px','6mk6gsnk',
's5eabntg','vcv45quw','i1bfvtsv','u9dkcz46','u90zfl7t','a40gmg2l','1naqeaio','pzvjb5io',
'1zx8h34h','879hgsjs','jn6h7vl1','0xm8hfpq','dvuloxj7','e4ohjj3a','mmakw97b','urjxx6ca',
'dp9lbuy0','jw34gyf2','o90pkf03','b0niobr0','pdf2udss','4fg24m45','sk57b228','soxnke0k',
'm7tbtlwq','315lt84w','5dsa9h8a','8zv453rs','gvxr867o','n2cn2gu7','usposk6o','trcvabp1',
'bc4yxt09','of2qtm1a','jni4xw19','5u62qpuc','0tzvnk1y']

for slug in unmatched_lac:
    w = next((x for x in waters if x['slug']==slug), None)
    if not w: continue
    anchor = w.get('coordinates')
    if not anchor: continue
    # find polygons within 5km, regardless of name
    near = [l for l in lakes if geo_dist_km(anchor, l['centroid']) < 5.0]
    if near:
        print(f"\n### {w['name']} ({w['judet']}) coord={anchor}")
        for l in sorted(near, key=lambda l: geo_dist_km(anchor, l['centroid']))[:5]:
            print(f"   {l['name']:45s} d={geo_dist_km(anchor, l['centroid']):5.1f}km water={l['water']} nc={l['nc']}")
    else:
        # check for river geometry near (could be a lake on the river)
        pass
