#!/usr/bin/env python3
"""Extract named lake/reservoir polygons from the fresh Overpass download for unmatched lakes."""
import json, sys, unicodedata, re
from pathlib import Path

sys.path.insert(0, 'scripts')
from fix_bbox_waters import norm, lake_core, geo_dist_km

data = json.load(open('data/raw/overpass_water_all.json'))
els = data.get('elements', [])

# build node map
nodes = {el['id']: (el.get('lat'), el.get('lon')) for el in els if el['type'] == 'node' and 'lat' in el}
print(f"nodes: {len(nodes)}")

# ways: build geometry
ways = {}
for el in els:
    if el['type'] != 'way':
        continue
    coords = [[nodes[n][1], nodes[n][0]] for n in el.get('nodes', []) if n in nodes]
    if len(coords) < 2:
        continue
    ways[el['id']] = {
        'type': 'way',
        'id': el['id'],
        'tags': el.get('tags', {}),
        'coords': coords,
        'geom': {'type': 'LineString', 'coordinates': coords},
    }

# relations: combine member ways
rels = {}
for el in els:
    if el['type'] != 'relation':
        continue
    parts = []
    for m in el.get('members', []):
        if m['type'] == 'way' and m['ref'] in ways:
            parts.append(ways[m['ref']]['coords'])
    rels[el['id']] = {
        'type': 'relation',
        'id': el['id'],
        'tags': el.get('tags', {}),
        'parts': parts,
    }

# named polygons: ways that are closed (first==last) with water/natural tags, or
# relations (multipolygon)
def is_polygon_way(w):
    c = w['coords']
    if len(c) < 4:
        return False
    return abs(c[0][0] - c[-1][0]) < 1e-9 and abs(c[0][1] - c[-1][1]) < 1e-9

named_lakes = []
for wid, w in ways.items():
    t = w['tags']
    if not (t.get('name') or t.get('name:ro')):
        continue
    is_water = t.get('natural') == 'water' or t.get('water') or t.get('landuse') == 'reservoir'
    if not is_water:
        continue
    if not is_polygon_way(w):
        continue
    name = t.get('name') or t.get('name:ro')
    # skip if name is generic 'lac'/'balta' alone
    named_lakes.append({
        'name': name,
        'norm': norm(name),
        'core': lake_core(name),
        'geom': {'type': 'Polygon', 'coordinates': [w['coords']]},
        'tags': t,
        'osm_type': 'way',
        'osm_id': wid,
    })

for rid, r in rels.items():
    t = r['tags']
    if not (t.get('name') or t.get('name:ro')):
        continue
    is_water = t.get('natural') == 'water' or t.get('water') or t.get('landuse') == 'reservoir'
    if not is_water:
        continue
    if not r['parts']:
        continue
    name = t.get('name') or t.get('name:ro')
    # relation parts: treat as MultiPolygon-ish; for display, a MultiLineString
    # of outer rings works fine as a Polygon stand-in
    rings = [p for p in r['parts'] if is_polygon_way({'coords': p})]
    if not rings:
        rings = r['parts']
    named_lakes.append({
        'name': name,
        'norm': norm(name),
        'core': lake_core(name),
        'geom': {'type': 'MultiPolygon', 'coordinates': [[p] for p in rings]},
        'tags': t,
        'osm_type': 'relation',
        'osm_id': rid,
    })

print(f"named water polygons: {len(named_lakes)}")
# save compact index
out = []
for l in named_lakes:
    coords = l['geom']['coordinates']
    if l['geom']['type'] == 'Polygon':
        pts = [p for ring in coords for p in ring]
    else:
        pts = [p for part in coords for ring in part for p in ring]
    if not pts:
        continue
    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
    l['centroid'] = (sum(lons)/len(lons), sum(lats)/len(lats))
    out.append(l)

with open('data/processed/overpass_named_lakes.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print(f"saved {len(out)} named lake polygons -> data/processed/overpass_named_lakes.json")

# Also: what names do we have that are useful?
import collections
wanted = ['Arcești','Drăgănești','Frunzaru','Rusănești','Slatina','Băbeni','Cornetu','Câineni',
          'Gura Lotrului','Ionești','Robești','Vlădești','Sălățig','Topolovăț','Lățunaș',
          'Pojorâta','Căpâlna','Petrești','Câmpu lui Neag','Ostrov','Subcetate','Pangrati',
          'Reconstrucția','Negreni','Bentu','Pietrosu','Ivanul','Cuiejdel','Ghilin','Chișineu',
          'Copilul','Mișca','Pâncota','Zădăreni','Căpâlnaș','Cerbureni','Curtea de Argeș',
          'Pitești','Zigoneni','Galbeni','Gârleni','Lilieci','Agrement','Izvorul','Cilieni',
          'Cefa','Culișer','Huțani','Volovăț','Vorona','Holod','Tărcăița','Buduresei','Ierului',
          'Omului','Șoimului','Lesuntu','Ilvei','Potop','Jilț','Grotului','Râmești','Lonei',
          'Vadului','Gepiș','Sabasa']
found = collections.defaultdict(list)
for l in out:
    for w_ in wanted:
        if w_.lower() in l['norm']:
            found[w_].append((l['name'], l['osm_type'], l['osm_id'], l['centroid']))
            break
for w_ in sorted(wanted):
    if found[w_]:
        for name, otype, oid, cent in found[w_][:4]:
            print(f"   {w_:15s} | {name} | {otype}/{oid} | center={tuple(round(x,3) for x in cent)}")
    else:
        print(f"   {w_:15s} | (none)")
