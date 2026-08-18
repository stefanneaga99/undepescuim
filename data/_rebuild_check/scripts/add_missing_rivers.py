#!/usr/bin/env python3
"""Add rivers that are entirely missing from waters.json (Bâsca Mare, Bâsca Mică).

Audit finding: the ANPA + arebaltapeste contract lists are FULLY covered in
waters.json (0 ANPA missing; the 1 arebaltapeste 'missing' — Râul Dâmbovița
mijlociu — is a grammatical-variant duplicate of 'Râul Dâmbovița mijlocie'
whose riverGroup already has a geometry owner). The genuinely missing rivers
are the Bâsca headwaters: Bâsca Mare + Bâsca Mică join at the Bâsca Rozilei
sector start (limite: 'conf. Basca Mare - conf. cu râul Buzău') but are not
listed as contracted sectors themselves.

These join the same AJVPS BUZĂU contract area (contract 22/19.09.2017) and
render with full OSM courses so the whole Bâsca basin is visible.

Geometry sources (data/rivers_osm.geojson):
  - Bâsca Mare: relation 8438302 (river)
  - Bâsca Mică: relation 18012045 (river)
The main 'Bâsca' course downstream of the confluence is OSM way 24332687
('Bâsca Rosiliei') — attached to the existing 'Râul Bâsca Rozilei' contract
by scripts/audit_missing_rivers.py.

Usage: python3 scripts/add_missing_rivers.py [--write]
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
OSM_FILE = ROOT / "data" / "rivers_osm.geojson"

NEW_RIVERS = [
    {
        "slug": "basca-mare",
        "name": "Râul Bâsca Mare",
        "judet": "Buzău",
        "subtype": "rau",
        "osm_name": "Bâsca Mare",
        "referinta": "Afluent principal al râului Bâsca (bazin AJVPS BUZĂU, contract 22/19.09.2017)",
        "limite": "Izvoare – confluența cu Bâsca Mică",
        "riverGroup": "basca-mare",
    },
    {
        "slug": "basca-mica",
        "name": "Râul Bâsca Mică",
        "judet": "Buzău",
        "subtype": "rau",
        "osm_name": "Bâsca Mică",
        "referinta": "Afluent principal al râului Bâsca (bazin AJVPS BUZĂU, contract 22/19.09.2017)",
        "limite": "Izvoare – confluența cu Bâsca Mare",
        "riverGroup": "basca-mica",
    },
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def load_osm() -> dict:
    """way-id -> way dict. Duplicate ids (same way in multiple overpass
    chunks, one tagged one not) keep the TAGGED copy — otherwise names like
    'Bâsca Mare' silently vanish from the index."""
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
        if len(coords) < 2:
            continue
        w = {
            "geometry": {"type": "LineString", "coordinates": coords},
            "name": el.get("tags", {}).get("name", ""),
        }
        prev = ways.get(el["id"])
        if prev is None or (not prev.get("name") and w.get("name")):
            ways[el["id"]] = w
    return ways


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    ways = load_osm()
    existing_names = {norm(x["name"]) for x in fe}

    added, skipped = [], []
    for spec in NEW_RIVERS:
        if norm(spec["name"]) in existing_names:
            skipped.append(spec["name"])
            print(f"[skip] {spec['name']} already present")
            continue
        # Gather all OSM geometry under the target name
        osm_parts = [w["geometry"]["coordinates"] for w in ways.values() if norm(w["name"]) == norm(spec["osm_name"])]
        if not osm_parts:
            skipped.append(spec["name"])
            print(f"[skip] {spec['name']}: no OSM geometry named '{spec['osm_name']}'")
            continue
        geometry = (
            {"type": "LineString", "coordinates": osm_parts[0]}
            if len(osm_parts) == 1
            else {"type": "MultiLineString", "coordinates": osm_parts}
        )
        entry = {
            "slug": spec["slug"],
            "name": spec["name"],
            "judet": spec["judet"],
            "type": "ape",
            "subtype": spec["subtype"],
            "limite": spec["limite"],
            "dimensiune": "",
            "pescuit_interzis": False,
            "referinta": spec["referinta"],
            "coordinates": None,
            "driving": None,
            "bbox": None,
            "asociatie": {
                "name": "AJVPS BUZĂU",
                "name_long": "Asociația Județeană a Vănătorilor și Pescarilor Sportivi Buzău",
                "slug": "ajvps-buzau",
            },
            "geometry": geometry,
            "source": "osm_bulk",
            "source_detail": "manual_audit_add",
            "riverGroup": spec.get("riverGroup"),
        }
        fe.append(entry)
        existing_names.add(norm(spec["name"]))
        added.append(spec["name"])
        npts = sum(len(p) for p in (osm_parts if isinstance(geometry["coordinates"][0][0], list) else [geometry["coordinates"]]))
        print(f"[add] {spec['name']}: {geometry['type']} ({npts} pts)")

    print(f"[add] added {len(added)}, skipped {len(skipped)}")
    if args.write:
        FE_WATERS.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[write] waters.json: {len(fe)} waters")


if __name__ == "__main__":
    main()
