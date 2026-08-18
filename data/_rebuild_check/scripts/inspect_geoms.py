#!/usr/bin/env python3
"""Inspect geometries of key multi-group members."""
import json

waters = json.load(open('public/data/waters.json', encoding='utf-8'))
slugs = ['jfwp7w1y', '7oju77qb', 'ey1b2yfy', '2uxod40o', 'anpa-anpa-0391',
         'anpa-anpa-0326', 'anpa-anpa-0332', 'anpa-anpa-0333', 'anpa-anpa-0334',
         'n0810toy', 'wmx33tho', 'aoja7n5d', 'f553avch', 'djkvkzv6', '9mfds2yv',
         'w69nse7i', 'qtebe8c3', '9h06oubr', 'anpa-anpa-0446', '0yftnvx2',
         'nwa37i1j', 'm19ue32m', '9y116j3m', 'i9uffwbx', '89j19sek', 'wv8ykggg',
         'a2qs9hkg', 'hao8h0b2', 'b3r64r3x']
by_slug = {w['slug']: w for w in waters}
for slug in slugs:
    w = by_slug.get(slug)
    if not w:
        print(f'{slug} NOT FOUND')
        continue
    g = w.get('geometry')
    name = (w.get('name') or '')[:36]
    judet = (w.get('judet') or '')[:12]
    if not g:
        print(f'{slug} {name:38} [{judet:12}] NO GEOM')
        continue
    def flat(g):
        t = g['type']
        c = g['coordinates']
        if t == 'MultiLineString':
            return [p for part in c for p in part]
        if t == 'LineString':
            return c
        if t == 'Polygon':
            return c[0]
        if t == 'MultiPolygon':
            return c[0][0]
        return []
    pts = flat(g)
    lats = [p[1] for p in pts]
    lons = [p[0] for p in pts]
    npts = len(pts)
    print(f'{slug} {name:38} [{judet:12}] {g["type"]:15} {npts:5} pts  lat {min(lats):.2f}-{max(lats):.2f} lon {min(lons):.2f}-{max(lons):.2f}')
