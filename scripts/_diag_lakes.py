#!/usr/bin/env python3
"""Diagnose specific lake matching failures."""
import json, sys
sys.path.insert(0, 'scripts')
from fix_bbox_waters import load_hotosm_lakes, geo_dist_km, lake_core, norm, article_variants

lakes = load_hotosm_lakes()
waters = json.load(open('public/data/waters.json'))

cases = [
    ('anpa-brasov-arpasu', 'Lac acumulare Arpașu (Brașov)'),
    ('5l9byf37', 'Lac acumulare Olteț (Brașov)'),
    ('2vlxdbig', 'Lacul Bistra Iezer (CS)'),
    ('0qrpg5nz', 'Lacul Gura Golumbului (CS)'),
    ('sctzx1ju', 'Prisaca Cerna (CS)'),
    ('99auwn3e', 'Lacul Săcălaia (Cluj)'),
    ('arrd8tai', 'Lac Pucioasa (DB)'),
    ('n4unwsj0', 'Lac Tismana (GJ)'),
    ('8a8nlp4g', 'Lac Vâja (GJ)'),
    ('6mk6gsnk', 'Lacul Câmpu lui Neag (HD)'),
    ('s5eabntg', 'Lacul Ostrov (HD)'),
    ('i1bfvtsv', 'Lacul de acumulare Hațeg (HD)'),
    ('u9dkcz46', 'Oglinda Mândrii (HD)'),
    ('u90zfl7t', 'Roşiile (Tăul fără Fund) (HD)'),
    ('a40gmg2l', 'Slăvei (HD)'),
    ('dvuloxj7', 'Lac Bicaz (NT)'),
    ('e4ohjj3a', 'Lac Pangrati (NT)'),
    ('mmakw97b', 'Lac Reconstrucția (NT)'),
    ('m603pbea', 'Lac Vaduri (NT)'),
    ('m7tbtlwq', 'Lacul Topolovățul (TM)'),
    ('315lt84w', 'Lacul de acumulare Lățunaș (TM)'),
    ('5u62qpuc', 'Lacul Muntinu (VL)'),
    ('0tzvnk1y', 'Lacul Vlădești (VL)'),
    ('sc2dvrmj', 'Petrimanu (VL)'),
    ('7z7cq445', 'Vidra (VL)'),
    ('4s86ejf1', 'Lacul Urlea (BV)'),
    ('awpqafbr', 'Lacul montan Podrăgel (SB)'),
    ('acfnf1vr', 'Podragu Mare (SB)'),
    ('34ethptl', 'Oașa (SB)'),
    ('7yg1hoia', 'Lacul Izvorul (Măgurii) (BN)'),
]

for slug, label in cases:
    w = next(x for x in waters if x['slug']==slug)
    anchor = w.get('coordinates')
    print(f"\n### {label} coord={anchor}")
    print(f"   water core: '{lake_core(w['name'])}' norm: '{norm(w['name'])}'")
    # all candidate polygons within 8km sorted by distance
    near = []
    for l in lakes:
        d = geo_dist_km(anchor, l['centroid'])
        if d < 8.0:
            near.append((d, l))
    near.sort(key=lambda x: x[0])
    for d, l in near[:8]:
        print(f"   d={d:4.1f}km | {l['name'][:50]:50s} | core='{l['core']}' | water={l['water']} nc={l['nc']}")
