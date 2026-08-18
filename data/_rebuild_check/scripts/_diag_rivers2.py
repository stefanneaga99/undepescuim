#!/usr/bin/env python3
"""Check proximity of OSM 'Lesu'/'Lesul' to Pârâul Lesuntu (Bacău) + other rivers."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms, geom_centroid
from fix_bbox_waters import geo_dist_km

name_index, geoms = load_osm_index()
waters = json.load(open('public/data/waters.json'))

def show_water(slug, oterm):
    w = next((x for x in waters if x['slug']==slug), None)
    if not w or not w.get('coordinates'): return
    print(f"\n### {w['name']} ({w['judet']}) coord={w['coordinates']}")
    for n, ids in name_index.items():
        if oterm in n:
            for g in make_cluster_geoms(ids, geoms):
                c = geom_centroid(g)
                if c:
                    d = geo_dist_km(w['coordinates'], c)
                    print(f"   '{n}' d={d:.1f}km centroid={tuple(round(x,2) for x in c)}")

show_water('19468k28', 'lesu')       # Lesuntu
show_water('0dsbiw28', 'holod')      # Holod
show_water('g39ohi12', 'jil')        # Jilț
show_water('ebhj5eyj', 'potop')      # Potop
show_water('w9ifusdl', 'voron')      # Vorona
show_water('eebjo69e', 'volov')      # Volovăț
show_water('ab4t7anb', 'tarca')      # Tărcăița
show_water('nb7yzcmh', 'budur')      # Buduresei
show_water('aksrc2lo', 'grot')       # Grotului
show_water('tozghzao', 'ramesti')    # Râmești
show_water('nalohz4y', 'lona')       # Valea Lonei
show_water('1i81o3wj', 'vad')        # Valea Vadului
show_water('xypzp6q7', 'les')        # Valea Leșului
show_water('xd7hnzzl', 'ilva')       # Valea Ilvei
show_water('c1gifahb', 'teleajen')   # already matched - skip
