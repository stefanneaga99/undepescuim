#!/usr/bin/env python3
"""Check remaining rivers against HOTOSM lines + OSM rivers with relaxed matching."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')
from audit_missing_rivers import norm, core, load_osm_index, make_cluster_geoms, geom_centroid
from fix_bbox_waters import geo_dist_km, load_hotosm_lines

waters = json.load(open('public/data/waters.json'))
hot_lines = load_hotosm_lines()

def show(slug, keywords):
    w = next((x for x in waters if x['slug']==slug), None)
    if not w: return
    print(f"\n### {w['name']} ({w['judet']}) coord={w.get('coordinates')}")
    for kw in keywords:
        hits = [n for n in hot_lines if kw in n]
        for n in hits[:4]:
            c = geom_centroid(hot_lines[n][0]['geom'])
            d = geo_dist_km(w['coordinates'], c) if c and w.get('coordinates') else None
            print(f"   HOT {n:40s} d={d and round(d,1)}km")

show('ebhj5eyj', ['potop'])       # Potop
show('0rc761a8', ['hutani', 'huțani'])  # Gârla Huțani
show('gvhqgri8', ['cefa'])        # Cefa IV
show('uerba1xr', ['culiser'])     # Culișer
show('ewp217d3', ['jelna'])       # Jelna
show('uv7try13', ['bumbu', 'izvoare'])  # Izvoare conf Bumbului
show('z8u6g69z', ['geoagiu'])     # Geoagiu Superior
show('0a4d89le', ['prahova'])     # Prahova mijlocie
