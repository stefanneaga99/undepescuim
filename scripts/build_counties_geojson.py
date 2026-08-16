#!/usr/bin/env python3
"""Build public/data/counties.geojson — simplified county boundary polygons.

Serves the "nearby waters" county chip (t_6c2ac870): the nearby list must
show the county of the water's ACTUAL segment near the user (from its
geometry/bbox), not the contract county (which for multi-county rivers like
Dâmbovița is the association's seat — 'Ilfov' for headwaters near Brașov).

Input: data/raw/county_boundaries/*.json — one Nominatim response per county
(list of results; the geojson polygon(s) are unioned). Output is simplified
(shapely simplify, tolerance 0.005° ≈ 500 m) to keep the client payload
small (~220 KB for all 42 counties).

Usage: .venv/bin/python scripts/build_counties_geojson.py
"""

import json
import os
import re
import unicodedata
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "county_boundaries"
OUT = ROOT / "public" / "data" / "counties.geojson"

SIMPLIFY_TOL = 0.005  # degrees (~500 m) — plenty for a county chip


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def main() -> None:
    counties = []
    for path in sorted(SRC.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else [data]
        name = next((e.get("name") for e in entries if e.get("name")), path.stem)
        geoms = []
        for e in entries:
            g = e.get("geojson")
            if g and g.get("coordinates"):
                try:
                    geoms.append(shape(g))
                except Exception:
                    pass
        if not geoms:
            print(f"[skip] {path.name}: no usable geojson")
            continue
        union = unary_union(geoms)
        # MultiPolygon with many small fragments (islands etc.) — keep only
        # the largest part when the union is fragmented (Nominatim responses
        # are usually a single Polygon already).
        if union.geom_type == "MultiPolygon":
            largest = max(union.geoms, key=lambda p: p.area)
            union = largest if largest.area / union.area > 0.5 else union
        simplified = union.simplify(SIMPLIFY_TOL, preserve_topology=True)
        counties.append({
            "type": "Feature",
            "properties": {"name": name},
            "geometry": mapping(simplified),
        })

    counties.sort(key=lambda f: norm(f["properties"]["name"]))
    fc = {"type": "FeatureCollection", "features": counties}
    OUT.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"[build] {len(counties)} counties -> {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
