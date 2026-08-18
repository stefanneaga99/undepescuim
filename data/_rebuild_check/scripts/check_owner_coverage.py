#!/usr/bin/env python3
"""Verify course-owner geometry coverage against the test click points."""
import json
from collections import defaultdict

waters = json.load(open('public/data/waters.json', encoding='utf-8'))
tests = json.load(open('scripts/test_points.json', encoding='utf-8'))

owners = {
    'olt': 'ehwpvgwh', 'mures': 'hmd3pa0v', 'siret': '9m2irr6m',
    'prut': 'o4sf1fah', 'somes': 'lagsqhtl', 'crisul-repede': 'xzrr6do0',
    'arges': '3614s8es', 'ialomita': '3ek8e82l', 'dambovita': 'fo3h8cp6',
    'jiu': 'qrjybswm',
}
by_slug = {w['slug']: w for w in waters}
for g, slug in owners.items():
    w = by_slug.get(slug)
    geom = w.get('geometry') if w else None
    if not geom:
        print(f'{g:14} NO GEOMETRY for owner {slug}')
        continue
    coords = geom['coordinates']
    if geom['type'] == 'LineString':
        coords = [coords]
    lats = [p[1] for part in coords for p in part]
    lons = [p[0] for part in coords for p in part]
    npts = sum(len(p) for p in coords)
    # test points for this river
    pts = tests.get(g, [])
    if not pts:
        print(f'{g:14} no test points')
        continue
    tmin_lat = min(t['lat'] for t in pts)
    tmax_lat = max(t['lat'] for t in pts)
    tmin_lon = min(t['lon'] for t in pts)
    tmax_lon = max(t['lon'] for t in pts)
    # approximate coverage: is the geometry bbox containing the test bbox?
    covers = (min(lats) <= tmin_lat and max(lats) >= tmax_lat
              and min(lons) <= tmin_lon and max(lons) >= tmax_lon)
    print(f'{g:14} owner={w["name"][:30]:32} {npts:5} pts  lat {min(lats):.2f}-{max(lats):.2f} lon {min(lons):.2f}-{max(lons):.2f}  test bbox lat {tmin_lat:.2f}-{tmax_lat:.2f} lon {tmin_lon:.2f}-{tmax_lon:.2f}  {"COVERS" if covers else "!! DOES NOT COVER test bbox"}')
