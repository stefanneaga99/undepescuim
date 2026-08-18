#!/usr/bin/env python3
"""Merge-task cleanup: strip degenerate (<4-pt) rings from contracted lake
geometries (t_1b7c95a7). Three batch-attached MultiPolygons carry a sliver
second part (2-3 pts, sub-meter) that breaks shapely LinearRing in
build_uncontracted_lakes.py. Drop those rings; collapse single-part
MultiPolygon to Polygon."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "public" / "data" / "waters.json"

TARGETS = {
    "anpa-anpa-0643",
    "anpa-anpa-0645",
    "romsilva-cluj-lacul-gilau",
}

def clean_geometry(g):
    if not g:
        return g
    if g["type"] == "Polygon":
        rings = [r for r in g["coordinates"] if len(r) >= 4]
        if not rings:
            return None
        g["coordinates"] = rings
        return g
    if g["type"] == "MultiPolygon":
        parts = []
        for p in g["coordinates"]:
            rings = [r for r in p if len(r) >= 4]
            if rings:
                parts.append(rings)
        if not parts:
            return None
        if len(parts) == 1:
            return {"type": "Polygon", "coordinates": parts[0]}
        return {"type": "MultiPolygon", "coordinates": parts}
    return g

def main():
    text = FE.read_text(encoding="utf-8")
    waters = json.loads(text)
    changed = {}
    for w in waters:
        if w["slug"] in TARGETS:
            before = json.dumps(w.get("geometry"), ensure_ascii=False)
            w["geometry"] = clean_geometry(w.get("geometry"))
            after = json.dumps(w.get("geometry"), ensure_ascii=False)
            if before != after:
                changed[w["slug"]] = w.get("geometry", {}).get("type")
    if not changed:
        print("no changes needed")
        return
    # serialization: indent=1, ensure_ascii=False, NO trailing newline (pitfall #23/#37)
    out = json.dumps(waters, indent=1, ensure_ascii=False)
    FE.write_text(out, encoding="utf-8")
    print("fixed:", changed)

if __name__ == "__main__":
    main()
