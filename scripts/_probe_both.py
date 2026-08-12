#!/usr/bin/env python3
"""Search BOTH extracts for the still-unmatched lake/reservoir names."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')

def nrm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s.lower()).strip()

# HOTOSM named polygons
fc = json.load(open('data/sources/waterways.geojson'))
polys = [f for f in fc['features'] if f['geometry']['type'] in ('Polygon','MultiPolygon')
         and (f.get('properties',{}).get('name') or f.get('properties',{}).get('name_ro'))]
hot_names = []
for f in polys:
    p = f['properties']
    for n in (p.get('name'), p.get('name_ro')):
        if n:
            hot_names.append((nrm(n), n, f['geometry']['type']))

# Overpass extract elements (any element w/ name)
op = json.load(open('data/rivers_osm.geojson'))
op_names = []
for el in op.get('elements', []):
    t = el.get('tags', {})
    n = t.get('name')
    if n:
        op_names.append((nrm(n), n, el['type'], t.get('waterway'), t.get('natural'), t.get('water'), t.get('landuse')))

targets = ['Băbeni','Cornetu','Câineni','Călimănești','Drăgășani','Dăești','Gura Lotrului','Ionești',
'Robești','Muntinu','Vlădești','Arcești','Drăgănești','Frunzaru','Ipotești','Rusănești','Slatina',
'Strejești','Pojorâta','Topolovăț','Lățunaș','Satchinez','Izvorul Măgurii','Negreni','Pangrati',
'Reconstrucția','Vaduri','Cilieni','Zăvoiul Orbului','Pucioasa','Tismana','Vâja','Făerag','Ostrov',
'Subcetate','Hațeg','Oglinda Mândrii','Roșiile','Slăvei','Bentu','Ivanul','Cuiejdel','Bicaz',
'Câmpu lui Neag','Valea de Pești','Bistra Iezer','Gura Golumbului','Prisaca','Săcălaia','Știucilor',
'Iezer','Ighel','Șurianu','Cicir','Ghilin','Copilul','Mișca','Chișineu','Pâncota','Zădăreni',
'Cerbureni','Curtea de Argeș','Pitești','Zigoneni','Agrement','Galbeni','Gârleni','Lilieci',
'Bălăsan','Iezerul Pietrosu','Mesteacăn','Zetea','Bezid','Siriu','Bâtca Doamnei','Balta Gării',
'Cinciș','Oașa','Sadu','Urlea','Avrig','Racovița','Scoreiu','Olteț','Voila','Arpașu','Pecineagu',
'Râușor','Bolboci','Scropoasa','Dopca']

for t in targets:
    nt = nrm(t)
    hits = [h for h in hot_names if nt in h[0] or h[0] in nt]
    oph = [h for h in op_names if nt in h[0] or h[0] in nt]
    if hits or oph:
        print(f"\n### {t}:")
        for h in sorted(set(hits))[:6]:
            print(f"   HOTOSM: '{h[1]}' [{h[2]}]")
        for h in sorted(set(oph))[:6]:
            print(f"   OSM:    '{h[1]}' [{h[2]}] ww={h[3]} nat={h[4]} water={h[5]} lu={h[6]}")
