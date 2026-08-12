#!/usr/bin/env python3
"""Locate paraul ghepiu + vale stramba clusters."""
import json, sys
sys.path.insert(0, 'scripts')
from audit_missing_rivers import load_osm_index, make_cluster_geoms, geom_centroid

name_index, geoms = load_osm_index()
for n in ['paraul ghepiu', 'valea stramba', 'stramba']:
    if n in name_index:
        for g in make_cluster_geoms(name_index[n], geoms):
            print(f"'{n}' centroid: {geom_centroid(g)}")
    else:
        print(f"'{n}' NOT in index")
