#!/usr/bin/env python3
"""Probe OSM index for near-matches of unmatched bbox rivers."""
import json, sys, difflib
sys.path.insert(0, 'scripts')
from audit_missing_rivers import norm, core, load_osm_index

waters = json.load(open('public/data/waters.json'))
bbox_no_geom = [w for w in waters if w.get('bbox') and not w.get('geometry')]
raus = [w for w in bbox_no_geom if w.get('subtype') == 'rau']

name_index, geoms = load_osm_index()
all_names = list(name_index.keys())

unmatched_names = ['Pârâul Lesuntu','Pârâul Nou Roman','Pârâul Râul Vadului','Pârâul Valea Leșului',
'Pârâul Valea Rîndiboului','Pârâul Valea Strâmbii','Râul Grotului','Râul Holod','Râul Jilț',
'Râul Măgura Cisnădiei','Râul Potop','Râul Râmești','Râul Tărcăița','Râul Teleajen inferior - Bucov',
'Râul Valea Ilvei','Râul Volovăț','Râul Vorona','Topa - Holod','Valea Bistrei','Valea Buduresei',
'Valea Călinești cu pâraiele Călinești, Sulița, Soci','Valea Cârlibabei','Valea Drăganului','Valea Gepiș',
'Valea Ierii Mijlocie','Valea Ierii Superioară','Valea Ierului','Valea Lonei','Valea Mișidului',
'Valea Omului','Valea Răcătăului','Valea Sighiștelului','Valea Şartăşului','Valea Șoimului',
'Valea Țibăului','Valea Vadului','Râul Sabasa','Râul Izvorul Lotrului']

def tokens(s):
    return set(core(s).split())

for nm in unmatched_names:
    c = core(nm)
    ct = tokens(nm)
    cands = []
    for on in all_names:
        oc = core(on)
        if not oc:
            continue
        ot = set(oc.split())
        inter = ct & ot
        if inter:
            cands.append((len(inter), oc, on))
        else:
            # fuzzy first token match
            first_w = next(iter(ct))
            if len(first_w) >= 4 and difflib.SequenceMatcher(None, first_w, oc).ratio() > 0.6:
                cands.append((0.5, oc, on))
    cands.sort(reverse=True)
    print(f"\n### {nm}  core='{c}'")
    for sc, oc, on in cands[:6]:
        print(f"   {sc} | OSM: '{on}'")
