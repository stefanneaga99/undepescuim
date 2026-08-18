#!/usr/bin/env python3
"""Check unnamed HOTOSM polygons near unmatched lake coordinates (Olt reservoirs etc.)."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import geo_dist_km

fc = json.load(open('data/sources/waterways.geojson'))
feats = fc['features']
# unnamed polygons
unnamed = [f for f in feats if f['geometry']['type'] in ('Polygon','MultiPolygon')
           and not (f.get('properties',{}).get('name') or f.get('properties',{}).get('name_ro'))]
print('unnamed polygons:', len(unnamed))

waters = json.load(open('public/data/waters.json'))
targets = ['Acumulare Canciu','Acumulare Mihoesti','Iezer – Ighel','Iezer – Șurianu','Balta Cicir',
'Lac acumulare Pitești','Acumulare Agrement','Acumulare Galbeni','Lac acumulare Arpașu','Lac acumulare Olteț',
'Lacul Bistra Iezer','Lacul Gura Golumbului','Prisaca Cerna','Lacul Săcălaia','Lac Cilieni I,II,III',
'Lac Pucioasa','Lac Zăvoiul Orbului','Lac Tismana','Lac Vâja','Lac Făerag','Lacul Câmpu lui Neag',
'Lacul Ostrov','Lacul Subcetate','Lacul de acumulare Hațeg','Oglinda Mândrii','Roşiile','Slăvei',
'Lacul Bentu Mare Bordușani','Lacul Bentu Mic Bordușani','Lacul Bentu lui Cotoi','Iezerul Pietrosu',
'Lacul Ivanul','Cuiejdel','Lac Bicaz','Lac Pangrati','Lac Reconstrucția','Acumularea Băbeni',
'Acumularea Cornetu','Acumularea Câineni','Acumularea Călimănești','Acumularea Drăgășani',
'Acumularea Dăești','Acumularea Gura Lotrului','Acumularea Ionești','Acumularea Robești',
'Lacul Muntinu','Lacul Vlădești','Acumularea Arcești','Acumularea Drăgănești','Acumularea Frunzaru',
'Acumularea Ipotești','Acumularea Rusănești','Acumularea Slatina','Acumularea Strejești',
'Lacul Pojorâta','Lacul Topolovățul','Lacul de acumulare Lățunaș','Acumularea Satchinez',
'Lacul Izvorul (Măgurii)','Acumularea Negreni','Lacul Cinciș','Lac Valea de Pești']

def poly_centroid(f):
    g = f['geometry']
    if g['type']=='Polygon':
        pts=[p for ring in g['coordinates'] for p in ring]
    else:
        pts=[p for part in g['coordinates'] for ring in part for p in ring]
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

for t in targets:
    w = next((x for x in waters if x['name'].strip()==t), None)
    if not w: continue
    anchor = w.get('coordinates')
    if not anchor: continue
    near = []
    for f in unnamed:
        c = poly_centroid(f)
        if c and geo_dist_km(anchor, c) < 3.0:
            # area
            g = f['geometry']
            area = 0.0
            if g['type']=='Polygon':
                ring = g['coordinates'][0]
                s=0.0
                for (x1,y1),(x2,y2) in zip(ring, ring[1:]):
                    s += x1*y2 - x2*y1
                area = abs(s)/2
            near.append((geo_dist_km(anchor,c), area, f['properties'].get('water'), f['properties'].get('natural_class')))
    if near:
        near.sort(key=lambda x: x[0])
        print(f"\n### {t} ({w['judet']}) anchor={anchor}")
        for d, area, water, nc in near[:4]:
            print(f"   UNNAMED poly d={d:.2f}km area={area:.5f} water={water} nc={nc}")
