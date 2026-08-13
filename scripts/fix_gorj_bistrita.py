#!/usr/bin/env python3
"""t_5f5f2cce — fix Râul Bistrița (Gorj) geometry.

anpa-0309 "Râul Bistrița" AJVPS GORJ (Peștișani - Rogojel, 20 km) carried the
VÂLCEA Bistrița course (24.03-24.28E — the Pârâul Bistrița / D.S. Vâlcea
contract) instead of its own course: under AJVPS GORJ the whole Vâlcea river
lit up green, and clicks resolved to the Vâlcea contract (same-name match bug
class, pitfall #30). The real Gorj course is the OSM 'bistrita' cluster at
(22.99-23.13E, 44.96-45.17N) — Peștișani → Rogojel. Attach part 0 of that
cluster trimmed at Peștișani (the contract's upper limit); fix the bbox.
"""
import json
import math
import pickle

WATERS = 'public/data/waters.json'


def haversine(a, b):
    R = 6371
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a[1])) * math.cos(math.radians(b[1]))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def bbox_of_geom(geom):
    coords = geom['coordinates']
    if geom['type'] == 'LineString':
        coords = [coords]
    lons = [c[0] for p in coords for c in p]
    lats = [c[1] for p in coords for c in p]
    return [min(lons), min(lats), max(lons), max(lats)]


def main():
    with open(WATERS) as f:
        waters = json.load(f)
    by_slug = {w['slug']: w for w in waters}
    w = by_slug['ey1b2yfy']
    assert (w.get('name') or '').strip() == 'Râul Bistrița' and w.get('judet') == 'Gorj'

    # load the OSM 'bistrita' cluster near Peștișani
    with open('data/cache/osm_river_clusters.pkl', 'rb') as f:
        clusters = pickle.load(f)
    if isinstance(clusters, tuple):
        clusters = clusters[0]
    cluster = None
    for c in clusters:
        bb = c.get('bbox')
        if (c.get('name') or '').lower() == 'bistrita' and bb and 22.9 <= bb[0] <= 23.2:
            cluster = c
            break
    assert cluster, 'gorj bistrita cluster not found'
    parts = cluster['geom']['coordinates']
    # part 0: Peștișani area (45.15) → Rogojel area (44.96); part 1: headwater above Peștișani
    main = parts[0]
    # trim at Peștișani (the contract upper limit)
    pestisani = (23.0154018, 45.1266574)
    idx = min(range(len(main)), key=lambda i: haversine(main[i], pestisani))
    trimmed = main[idx:]
    geom = {'type': 'LineString', 'coordinates': trimmed}
    print(f'old geom bbox: {bbox_of_geom(w["geometry"])}')
    print(f'new geom: {len(trimmed)} pts, first={trimmed[0]}, last={trimmed[-1]}, bbox={bbox_of_geom(geom)}')
    w['geometry'] = geom
    w['bbox'] = bbox_of_geom(geom)
    w.pop('geometryByCounty', None)

    with open(WATERS, 'w') as f:
        f.write(json.dumps(waters, indent=1, ensure_ascii=False))
    print('written', WATERS)


if __name__ == '__main__':
    main()
