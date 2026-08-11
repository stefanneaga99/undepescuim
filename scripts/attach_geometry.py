#!/usr/bin/env python3
"""Attach real geometry from waters_geocoded.geojson into public/data/waters.json.

The frontend renders real river/lake shapes when Water.geometry is present and
falls back to bbox rectangles otherwise. This script is the bridge between the
geocoding pipeline output and the frontend data file.

Run AFTER scripts/merge_geocoded.py (which regenerates waters_geocoded.geojson):
    python3 scripts/attach_geometry.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
GEOCODED = ROOT / "public" / "data" / "waters_geocoded.geojson"


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    geocoded = json.loads(GEOCODED.read_text(encoding="utf-8"))

    geo_map = {}
    for f in geocoded.get("features", []):
        slug = (f.get("properties") or {}).get("arebaltapeste_slug")
        if slug:
            geo_map[slug] = {
                "type": f["geometry"]["type"],
                "coordinates": f["geometry"]["coordinates"],
            }

    matched = 0
    for w in waters:
        geom = geo_map.get(w["slug"])
        if geom:
            w["geometry"] = geom
            matched += 1
        else:
            w.pop("geometry", None)

    WATERS.write_text(
        json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"waters.json: {matched}/{len(waters)} waters have real geometry")


if __name__ == "__main__":
    main()
