#!/usr/bin/env python3
"""Merge ANPA canonical waters into the frontend dataset.

The frontend currently ships only the arebaltapeste snapshot (426 waters —
mostly lakes/reservoirs). The ANPA list (682 waters — the authoritative
contract list, including many rivers like Râul Buzău) is parsed but never
merged. This script merges ANPA waters missing from the frontend, attaches
OSM geometry where available, and writes the combined waters.json.

Usage: python3 scripts/merge_anpa_waters.py
"""

import json
import re
import sqlite3
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"
GEO_DB = ROOT / "data" / "cache" / "geocode.db"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def load_osm_index() -> dict:
    """name(norm) -> geometry from the bulk OSM download (rivers_osm.geojson)."""
    idx_file = ROOT / "data" / "rivers_osm.geojson"
    if not idx_file.exists():
        return {}
    data = json.loads(idx_file.read_text(encoding="utf-8"))

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
                "type": "LineString",
                "coordinates": coords,
                "name": el.get("tags", {}).get("name", ""),
            }

    rel_geoms = {}
    for el in data.get("elements", []):
        if el["type"] != "relation":
            continue
        coords = [ways[m["ref"]]["coordinates"] for m in el.get("members", [])
                  if m["type"] == "way" and m["ref"] in ways]
        if coords:
            rel_geoms[el["id"]] = {
                "kind": "relation",
                "type": "MultiLineString",
                "coordinates": coords,
                "name": el.get("tags", {}).get("name", ""),
            }

    index: dict[str, dict] = {}
    for g in {**ways, **rel_geoms}.values():
        n = norm(g["name"])
        if n and len(n) > 3:
            # Prefer relation (full course) over a single way segment
            existing = index.get(n)
            if existing is None or (g.get("kind") == "relation" and existing.get("kind") != "relation"):
                index[n] = g
    return index


def osm_geometry_for(name: str, osm_index: dict) -> dict | None:
    """Exact-norm match first, then token-overlap fuzzy."""
    n = norm(name)
    core = re.sub(r"^(raul|paraul|valea|lacul|balta)\s+", "", n)
    for key in (n, core):
        if key in osm_index:
            g = osm_index[key]
            return {"type": g["type"], "coordinates": g["coordinates"]}
    # fuzzy: token overlap >= 0.6
    best, best_score = None, 0.0
    nt = set(core.split())
    for key, g in osm_index.items():
        if not nt:
            continue
        inter = len(nt & set(key.split()))
        sc = inter / max(len(nt), len(key.split()))
        if sc > best_score:
            best_score, best = sc, g
    if best and best_score >= 0.6:
        return {"type": best["type"], "coordinates": best["coordinates"]}
    return None


OTHER_LAKE_RE = re.compile(
    r"^(?:baraj\s|fondul piscicol|ccrm\s|ccpfb\s|cp\s+\d|potcoava)", re.I
)


def anpa_subtype(w: dict) -> str:
    wt = w.get("water_type")
    if wt in ("river", "stream"):
        return "rau"
    if wt == "other":
        return "lac" if OTHER_LAKE_RE.match(w.get("water_name", "") or "") else "rau"
    return "lac"


def main() -> None:
    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    fe_by_name = {norm(x["name"]): x for x in fe}

    anpa = [json.loads(l) for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    osm_index = load_osm_index()
    print(f"[merge] frontend: {len(fe)} waters, ANPA: {len(anpa)}")

    added, skipped, updated = 0, 0, 0
    for w in anpa:
        name = w["water_name"]
        n = norm(name)
        geom = osm_geometry_for(name, osm_index)

        existing = fe_by_name.get(n)
        if existing is not None:
            # Already present — upgrade geometry when the new one is better:
            # full river course (MultiLineString from OSM relation) beats a
            # single LineString segment, and any geometry beats none.
            if geom and (
                existing.get("geometry") is None
                or (
                    geom["type"] == "MultiLineString"
                    and existing["geometry"].get("type") != "MultiLineString"
                )
            ):
                existing["geometry"] = geom
                updated += 1
            skipped += 1
            continue

        entry = {
            "slug": f"anpa-{w['id']}",
            "name": name,
            "judet": (w.get("county") or "").title(),
            "type": "ape",
            "subtype": anpa_subtype(w),
            "limite": w.get("limits_text") or "",
            "dimensiune": w.get("sector_raw") or "",
            "pescuit_interzis": False,
            "referinta": f"Contract {w.get('contract_number')} ({w.get('contract_date')})",
            "coordinates": None,
            "driving": None,
            "bbox": None,
            "asociatie": {
                "name": w.get("association", ""),
                "slug": norm(w.get("association", "")).replace(" ", "-"),
            },
            "geometry": geom,
        }
        fe.append(entry)
        fe_by_name[n] = entry
        added += 1

    FE_WATERS.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
    with_geom = sum(1 for x in fe if x.get("geometry"))
    print(f"[merge] added {added} ANPA waters, skipped {skipped} dupes, upgraded {updated} geometries")
    print(f"[merge] total: {len(fe)} waters, {with_geom} with real geometry")


if __name__ == "__main__":
    main()
