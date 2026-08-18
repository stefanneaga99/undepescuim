#!/usr/bin/env python3
"""Check Rausor/Drăgășani/Turnu reservoir polygons in the Overpass fetch."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')

def nrm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()

data = json.load(open('data/raw/overpass_reservoir_fetch.json'))
els = data.get('elements', [])
nodes = {el['id']: (el.get('lat'), el.get('lon')) for el in els if el['type']=='node' and 'lat' in el}

ways = {}
for el in els:
    if el['type'] != 'way':
        continue
    coords = [[nodes[n][1], nodes[n][0]] for n in el.get('nodes', []) if n in nodes]
    if len(coords) < 2:
        continue
    ways[el['id']] = (el.get('tags', {}), coords)

for wid, (t, coords) in ways.items():
    n = t.get('name') or ''
    if not n:
        continue
    nn = nrm(n)
    if any(k in nn for k in ['rausor', 'dragasani', 'turnu', 'maneciu', 'izbiceni', 'oltet', 'vistea']):
        closed = len(coords) >= 4 and abs(coords[0][0]-coords[-1][0])<1e-9 and abs(coords[0][1]-coords[-1][1])<1e-9
        lons = [p[0] for p in coords]; lats = [p[1] for p in coords]
        print(f"way/{wid} | {n} | closed={closed} | npts={len(coords)} | bbox=({min(lons):.3f},{min(lats):.3f})-({max(lons):.3f},{max(lats):.3f}) | nat={t.get('natural')} water={t.get('water')} ww={t.get('waterway')} lu={t.get('landuse')}")
