#!/usr/bin/env python3
"""Match remaining unmatched rivers against HOTOSM waterways LineStrings."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')
from audit_missing_rivers import norm, core, load_osm_index

fc = json.load(open('data/sources/waterways.geojson'))
feats = fc['features']

# build HOTOSM line index by normalized name
line_names = {}
for f in feats:
    g = f.get('geometry')
    if g is None or g['type'] not in ('LineString', 'MultiLineString'):
        continue
    p = f.get('properties') or {}
    n = p.get('name') or p.get('name_ro') or ''
    if not n:
        continue
    line_names.setdefault(norm(n), []).append(f)

unmatched_rivers = [
    'Pârâul Lesuntu', 'Pârâul Nou Roman', 'Pârâul Râul Vadului', 'Pârâul Valea Leșului',
    'Pârâul Valea Rîndiboului', 'Pârâul Valea Strâmbii', 'Râul Grotului', 'Râul Holod',
    'Râul Jilț', 'Râul Măgura Cisnădiei', 'Râul Potop', 'Râul Râmești', 'Râul Tărcăița',
    'Râul Teleajen inferior - Bucov', 'Râul Valea Ilvei', 'Râul Volovăț', 'Râul Vorona',
    'Topa - Holod', 'Topa – Holod', 'Valea Bistrei', 'Valea Buduresei',
    'Valea Călinești cu pâraiele Călinești, Sulița, Soci', 'Valea Cârlibabei',
    'Valea Drăganului', 'Valea Gepiș', 'Valea Ierii Mijlocie', 'Valea Ierii Superioară',
    'Valea Ierului', 'Valea Lonei', 'Valea Mișidului', 'Valea Omului', 'Valea Răcătăului',
    'Valea Sighiștelului', 'Valea Şartăşului', 'Valea Șoimului', 'Valea Țibăului',
    'Valea Vadului', 'Râul Sabasa', 'Râul Izvorul Lotrului', 'Canalul Cefa IV',
    'Canalul colector Criș', 'Culișer', 'Izvoare – conf. pârâul Bumbului', 'Jelna',
    'Gârla Huțani', 'Dopca',
]

# build target list with cores
def probe(name):
    c = core(name)
    ct = set(c.split())
    hits = []
    for ln, fl in line_names.items():
        lc = core(ln)
        if not lc:
            continue
        lt = set(lc.split())
        inter = ct & lt
        if inter:
            hits.append((len(inter), ln, fl))
    hits.sort(key=lambda x: -x[0])
    return hits

for name in unmatched_rivers:
    hits = probe(name)
    if not hits:
        continue
    print(f"\n### {name} core='{core(name)}'")
    for sc, ln, fl in hits[:5]:
        p = fl[0]['properties']
        g = fl[0]['geometry']
        print(f"   {sc} | '{ln}' | {g['type']} | ww={p.get('waterway')}")
