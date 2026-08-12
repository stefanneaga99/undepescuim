#!/usr/bin/env python3
"""Final check: any feature (line/polygon/point) in HOTOSM with these names."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')

def nrm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()

fc = json.load(open('data/sources/waterways.geojson'))
feats = fc['features']

targets = ['potop', 'jilt', 'holod', 'volovat', 'vorona', 'lesuntu', 'cefa', 'culiser',
           'hutani', 'bumbului', 'jelna', 'grotului', 'ramesti', 'lonei', 'vadului',
           'buduresei', 'gepis', 'ierului', 'omului', 'soimului', 'tarcaita', 'ilvei',
           'pangrati', 'reconstructia', 'topolovat', 'latunas', 'salatig', 'satchinez',
           'pojorata', 'vladesti', 'cilieni', 'zavoiul', 'campu lui neag', 'ostrov',
           'bentu', 'izvorul magurii', 'galbeni', 'garleni', 'lilieci', 'negreni',
           'cerbureni', 'curtea de arges', 'pitesti', 'zigoneni', 'cornetu', 'caineni',
           'lotrului', 'ionesti', 'robesti']

found = {}
for f in feats:
    p = f.get('properties', {})
    names = [p.get('name'), p.get('name_ro'), p.get('name_en'), p.get('name_latin')]
    for n in names:
        if not n: continue
        nn = nrm(n)
        for t in targets:
            if t in nn:
                found.setdefault(t, []).append((n, f['geometry']['type'], p.get('waterway')))
                break

for t in sorted(targets):
    if found.get(t):
        uniq = sorted(set(found[t]))[:3]
        print(f"{t:15s}: {uniq}")
