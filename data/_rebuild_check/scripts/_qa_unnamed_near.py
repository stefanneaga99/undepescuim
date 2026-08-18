#!/usr/bin/env python3
"""Check for unnamed natural=water polygons near dam-matched reservoirs."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import geo_dist_km

fc = json.load(open('data/sources/waterways.geojson'))
feats = fc['features']
unnamed = [f for f in feats if f['geometry']['type'] in ('Polygon','MultiPolygon')
           and not (f.get('properties',{}).get('name') or f.get('properties',{}).get('name_ro'))
           and (f.get('properties',{}).get('natural_class') == 'water'
                or f.get('properties',{}).get('water') in ('lake','reservoir','pond'))]
print(f"unnamed water polygons: {len(unnamed)}")

def centroid(f):
    g = f['geometry']
    if g['type']=='Polygon':
        pts=[p for ring in g['coordinates'] for p in ring]
    else:
        pts=[p for part in g['coordinates'] for ring in part for p in ring]
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

def area(f):
    g = f['geometry']
    s = 0.0
    if g['type']=='Polygon':
        ring = g['coordinates'][0]
        for (x1,y1),(x2,y2) in zip(ring, ring[1:]):
            s += x1*y2 - x2*y1
    elif g['type']=='MultiPolygon':
        for part in g['coordinates']:
            ring = part[0]
            for (x1,y1),(x2,y2) in zip(ring, ring[1:]):
                s += x1*y2 - x2*y1
    return abs(s)/2

anchors = {
    'Râușor (Argeș)': (25.053212862691034, 45.40972824086533),
    'Drăgășani (Vâlcea)': (24.28172318678542, 44.72566186498826),
    'Turnu (Vâlcea)': (24.30328481675034, 45.28498767675537),
    'Măneciu (Prahova)': (25.986455, 45.331153),
    'Izbiceni (Olt)': (24.655742424315687, 43.86450650168711),
}
for name, anchor in anchors.items():
    print(f"\n### {name} anchor={anchor}")
    near = []
    for f in unnamed:
        c = centroid(f)
        if c and geo_dist_km(anchor, c) < 3.0:
            near.append((geo_dist_km(anchor,c), area(f), f['properties'].get('water')))
    near.sort()
    for d, a, w in near[:6]:
        print(f"   d={d:.2f}km area={a:.6f} water={w}")
