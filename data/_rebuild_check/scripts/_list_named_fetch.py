#!/usr/bin/env python3
"""List all named elements in the reservoir fetch."""
import json, unicodedata, re

def norm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()

data = json.load(open('data/raw/overpass_reservoir_fetch.json'))
els = data.get('elements', [])
seen = {}
for el in els:
    if el['type'] == 'node':
        continue
    t = el.get('tags', {})
    n = t.get('name') or t.get('name:ro') or ''
    if not n:
        continue
    key = (n, el['type'], el['id'])
    if key in seen:
        continue
    seen[key] = t
print(f"named top-level elements: {len(seen)}")
for (n, etype, eid), t in sorted(seen.items()):
    nc = t.get('natural'); w = t.get('water'); ww = t.get('waterway'); lu = t.get('landuse')
    print(f"   {etype}/{eid} | {n} | nat={nc} water={w} ww={ww} lu={lu}")
