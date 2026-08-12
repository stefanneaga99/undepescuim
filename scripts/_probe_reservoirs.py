#!/usr/bin/env python3
"""Find Olt reservoir polygons anywhere in both extracts."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')

def nrm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s.lower()).strip()

fc = json.load(open('data/sources/waterways.geojson'))
polys = [f for f in fc['features'] if f['geometry']['type'] in ('Polygon','MultiPolygon')]
named = [f for f in polys if (f.get('properties',{}).get('name') or f.get('properties',{}).get('name_ro'))]

targets = ['arcesti', 'draganesti', 'frunzaru', 'rusanesti', 'slatina', 'babeni', 'cornetu',
           'caineni', 'gura lotrului', 'ionesti', 'robesti', 'vladesti', 'pojorata', 'salatig',
           'satchinez', 'topolovat', 'latunas', 'sacele', 'strambu', 'bentu', 'pangrati',
           'reconstruct', 'negreni', 'huțani', 'hutani', 'voltovat', 'vorona', 'holod', 'tarcaita',
           'buduresei', 'ierului', 'omului', 'soimului', 'lesuntu', 'ilvei', 'cefa', 'culiser',
           'potop', 'jilt', 'grotului', 'ramesti', 'lonei', 'vadului']

def geom_center(f):
    g = f['geometry']
    if g['type']=='Polygon':
        pts=[p for ring in g['coordinates'] for p in ring]
    elif g['type']=='MultiPolygon':
        pts=[p for part in g['coordinates'] for ring in part for p in ring]
    else:
        return None
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

print("=== named polygons matching targets ===")
for t in targets:
    hits = []
    for f in named:
        p = f['properties']
        nm = (p.get('name') or '') + ' ' + (p.get('name_ro') or '')
        if t in nrm(nm):
            c = geom_center(f)
            hits.append((f['properties'].get('name') or f['properties'].get('name_ro'), f['geometry']['type'], c, p.get('water'), p.get('natural_class')))
    if hits:
        print(f"\n### {t}:")
        for h in sorted(set(hits))[:8]:
            print(f"   {h[0]} | {h[1]} | center={h[2]} | water={h[3]} nc={h[4]}")
