#!/usr/bin/env python3
"""List ALL named closed ways in the reservoir fetch (any tag)."""
import json, unicodedata, re

def nrm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()

data = json.load(open('data/raw/overpass_reservoir_fetch.json'))
els = data.get('elements', [])
nodes = {el['id']: (el.get('lat'), el.get('lon')) for el in els if el['type']=='node' and 'lat' in el}
seen = {}
for el in els:
    if el['type'] != 'way':
        continue
    coords = [[nodes[n][1], nodes[n][0]] for n in el.get('nodes', []) if n in nodes]
    if len(coords) < 4:
        continue
    closed = abs(coords[0][0]-coords[-1][0]) < 1e-9 and abs(coords[0][1]-coords[-1][1]) < 1e-9
    t = el.get('tags', {})
    n = t.get('name') or t.get('name:ro') or ''
    if not n:
        continue
    if n not in seen:
        seen[n] = (el['id'], closed, t.get('natural'), t.get('water'), t.get('waterway'), t.get('landuse'))

print(f"named ways: {len(seen)}")
for n, (wid, closed, nat, water, ww, lu) in sorted(seen.items()):
    print(f"   {n:50s} way/{wid} closed={closed} nat={nat} water={water} ww={ww} lu={lu}")
