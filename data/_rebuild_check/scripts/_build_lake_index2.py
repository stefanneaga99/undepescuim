#!/usr/bin/env python3
"""Build named lake/reservoir polygon index from overpass_reservoir_fetch.json."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')
from fix_bbox_waters import norm, lake_core

data = json.load(open('data/raw/overpass_reservoir_fetch.json'))
els = data.get('elements', [])

nodes = {el['id']: (el.get('lat'), el.get('lon')) for el in els if el['type'] == 'node' and 'lat' in el}
ways = {}
for el in els:
    if el['type'] != 'way':
        continue
    coords = [[nodes[n][1], nodes[n][0]] for n in el.get('nodes', []) if n in nodes]
    if len(coords) < 2:
        continue
    ways[el['id']] = {'id': el['id'], 'tags': el.get('tags', {}), 'coords': coords}

rels = {}
for el in els:
    if el['type'] != 'relation':
        continue
    parts = []
    for m in el.get('members', []):
        if m['type'] == 'way' and m['ref'] in ways:
            parts.append(ways[m['ref']]['coords'])
    rels[el['id']] = {'id': el['id'], 'tags': el.get('tags', {}), 'parts': parts}

def is_closed(c):
    return len(c) >= 4 and abs(c[0][0]-c[-1][0]) < 1e-9 and abs(c[0][1]-c[-1][1]) < 1e-9

def centroid_of(coords):
    pts = [p for ring in coords for p in ring] if isinstance(coords[0], list) and isinstance(coords[0][0], list) else coords
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

out = []
# closed named ways (reservoir outlines often drawn as closed ways without tags)
for wid, w in ways.items():
    t = w['tags']
    name = t.get('name') or t.get('name:ro')
    if not name:
        continue
    if not is_closed(w['coords']):
        continue
    c = centroid_of([w['coords']])
    if not c: continue
    out.append({
        'name': name, 'norm': norm(name), 'core': lake_core(name),
        'geom': {'type': 'Polygon', 'coordinates': [w['coords']]},
        'centroid': c, 'osm_type': 'way', 'osm_id': wid, 'tags': t,
    })
# relations
for rid, r in rels.items():
    t = r['tags']
    name = t.get('name') or t.get('name:ro')
    if not name:
        continue
    if not r['parts']:
        continue
    rings = [p for p in r['parts'] if is_closed(p)]
    if not rings:
        continue
    c = centroid_of(rings)
    if not c: continue
    out.append({
        'name': name, 'norm': norm(name), 'core': lake_core(name),
        'geom': {'type': 'MultiPolygon', 'coordinates': [[p] for p in rings]},
        'centroid': c, 'osm_type': 'relation', 'osm_id': rid, 'tags': t,
    })

with open('data/processed/overpass_named_lakes2.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print(f"saved {len(out)} named polygons -> data/processed/overpass_named_lakes2.json")
for l in sorted(out, key=lambda x: x['name']):
    t = l['tags']
    print(f"   {l['name']:45s} | {l['osm_type']}/{l['osm_id']} | center={tuple(round(x,3) for x in l['centroid'])} | nat={t.get('natural')} water={t.get('water')}")
