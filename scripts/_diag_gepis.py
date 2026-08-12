#!/usr/bin/env python3
"""Debug Gepis + remaining river overrides."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import (best_osm_match, build_county_centroids, load_osm_index,
                                   make_cluster_geoms, try_manual_override, core, norm)

waters = json.load(open('public/data/waters.json'))
name_index, geoms = load_osm_index()
osm_geo_by_norm = {}
for n, ids in name_index.items():
    gs = make_cluster_geoms(ids, geoms)
    if gs:
        osm_geo_by_norm[n] = gs
county_centroids = build_county_centroids(waters)

for slug, over in [('gunskubl', 'gepis:paraul ghepiu'), ('nb7yzcmh', 'buduresei'), ('m2x1jtkp', 'sighistelului:sighistel')]:
    w = next(x for x in waters if x['slug']==slug)
    print(f"\n### {w['name']} ({w['judet']}) core='{core(w['name'])}'")
    # is target in index?
    print("   'paraul ghepiu' in index:", 'paraul ghepiu' in osm_geo_by_norm)
    print("   'sighistel' in index:", 'sighistel' in osm_geo_by_norm)
    best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
    print(f"   override -> {best} score={score} how={how}")
    # county centroid
    cc = county_centroids.get(w['judet'])
    print(f"   county centroid {w['judet']}: {cc}")
    if best:
        from audit_missing_rivers import geom_centroid
        print(f"   matched centroid: {geom_centroid(geom)}")
