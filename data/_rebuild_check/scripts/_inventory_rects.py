#!/usr/bin/env python3
"""Inventory: all blue-rectangle waters (bbox-no-geom + fake rect-polygon) with anchors."""
import json

with open('public/data/waters.json') as f:
    waters = json.load(f)

def is_rect_poly(g):
    if not g or g['type'] != 'Polygon':
        return False
    ring = g['coordinates'][0]
    pts = set((round(p[0], 6), round(p[1], 6)) for p in ring)
    if len(pts) != 4:
        return False
    xs = sorted(p[0] for p in pts)
    ys = sorted(p[1] for p in pts)
    corners = {(xs[0], ys[0]), (xs[0], ys[-1]), (xs[-1], ys[0]), (xs[-1], ys[-1])}
    return pts == corners

rects = []
for w in waters:
    if w.get('bbox') and not w.get('geometry'):
        rects.append((w, 'bbox-no-geom'))
    elif is_rect_poly(w.get('geometry')):
        rects.append((w, 'rect-poly'))

print(f"TOTAL blue rectangles: {len(rects)}")
for w, kind in sorted(rects, key=lambda x: (x[0]['judet'], x[0]['name'])):
    c = w.get('coordinates')
    print(f"{kind:12s} | {w['slug']} | {w['judet']} | {w['name']} | {w.get('subtype')} | coord={c}")
