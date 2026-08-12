#!/usr/bin/env python3
"""Attach the missing upper course (Siriul Mic + headwaters) to Râul Siriul.

Investigation (t_8c4b2d08): the map sector near 'Stearpa' (Buzău/Prahova
border) renders as a thin basemap stream — not clickable, no association.
It is the SIRIUL MIC, the source branch of the contracted Râul Siriul
(ANPA list: 'Râul Siriul — izvoare-conf. cu râul Buzău — 38 Km', AJVPS
BUZĂU, contract 22/19.09.2017). The waters.json entry anpa-anpa-0208 only
carried the OSM way 221432312 ('Siriu', 8.47 km lower course from the
Stearpa junction to the Buzău); the upper course mapped in OSM as
way 1496880283 ('Siriul Mic', 8.66 km) plus its two headwater ways
1496880788 + 1496880644 was never attached.

Fix: convert the entry geometry to a MultiLineString containing the full
course (headwaters → Siriul Mic → Siriu → Buzău), so the whole contracted
river renders and is clickable with AJVPS BUZĂU.

Usage: python3 scripts/fix_siriul_geometry.py [--write]
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
OSM_FILE = ROOT / "data" / "rivers_osm.geojson"

SLUG = "anpa-anpa-0208"
# OSM ways forming the Râul Siriul course, ordered source -> mouth:
#   1496880788 (unnamed headwater, W) + 1496880644 (unnamed headwater, N)
#     -> merge at node 13710395855 -> Siriul Mic 1496880283
#     -> junction at Stearpa (2304740870) -> Siriu 221432312 -> Buzău
WAY_PARTS = [1496880788, 1496880644, 1496880283, 221432312]


def load_osm_ways() -> dict:
    data = json.loads(OSM_FILE.read_text(encoding="utf-8"))
    nodes = {
        el["id"]: (el.get("lat"), el.get("lon"))
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }
    ways = {}
    for el in data.get("elements", []):
        if el["type"] != "way":
            continue
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) >= 2:
            ways[el["id"]] = {
                "geometry": {"type": "LineString", "coordinates": coords},
                "name": el.get("tags", {}).get("name", ""),
            }
    return ways


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    ways = load_osm_ways()
    entry = next((w for w in fe if w.get("slug") == SLUG), None)
    if entry is None:
        print(f"[error] entry {SLUG} not found")
        return

    parts = []
    missing = []
    for wid in WAY_PARTS:
        w = ways.get(wid)
        if w is None:
            missing.append(wid)
            continue
        parts.append(w["geometry"]["coordinates"])
    if missing:
        print(f"[error] missing OSM ways: {missing}")
        return

    old_len_km = sum(
        len(p) for p in (entry["geometry"]["coordinates"] if entry.get("geometry", {}).get("type") == "MultiLineString" else [entry.get("geometry", {}).get("coordinates", [])])
    )
    entry["geometry"] = {"type": "MultiLineString", "coordinates": parts}
    entry["source_detail"] = "siriul_mic_attach (t_8c4b2d08)"
    npts = sum(len(p) for p in parts)
    print(f"[fix] {entry['name']}: geometry -> MultiLineString with {len(parts)} parts, {npts} pts (was {old_len_km} pts LineString)")
    print(f"[fix] course: {entry['limite']} | {entry['dimensiune']} | {entry['asociatie']['name']}")

    if args.write:
        FE_WATERS.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[write] waters.json: {len(fe)} waters")


if __name__ == "__main__":
    main()
