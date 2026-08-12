#!/usr/bin/env python3
"""Fix Mureș contract positions (follow-up from task t_84b29064 check).

The assign_course_frac.py run positioned Mureș I/II/IV using the FIRST
geometry-bearing member of the 'mures' group — 'Râul Mureș' (Alba), a
PARTIAL geometry (Alba county stretch only). Every contract projected to
frac 0.0, so clicks on the Mureș resolved to 'Râul Mureș' (Alba) for the
whole upper half of the river.

Fix: anchor each contract on its limite places, projected onto the FULL
Mureș course ('Râul Mureș' Arad geometry — 15k pts, source→mouth).

  Râul Mureș I    'Podul Borzont - Podul de fier Subcetate'  -> frac(Borzont)
  Râul Mureș II   'Podul de fier Subcetate - Limita județ Mureș' -> frac(Subcetate)
  Râul Mureș IV   'Tunel Sălard – pod Deda'                   -> frac(Deda)
  Râul Mureș Alba (partial geometry owner) -> project its own midpoint on full course
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import geocode_common as gc
from probe_buzau_places import fraction_at, order_parts

WATERS = ROOT / "public" / "data" / "waters.json"


def geocode_cached(db, query):
    import sqlite3
    row = db.execute(
        "SELECT result_json FROM geocode_cache WHERE query_string = ?", (query,)
    ).fetchone()
    if row is not None:
        if row[0]:
            data = json.loads(row[0])
            if data:
                return [float(data[0]["lon"]), float(data[0]["lat"])]
        return None
    results = gc.nominatim_search(query, countrycodes="ro")
    if results:
        first = results[0]
        db.execute(
            "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, osm_type, osm_id, geometry_type, bbox, source, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                query, "probe", "rau", json.dumps(results, ensure_ascii=False),
                first.get("osm_type"), str(first.get("osm_id")),
                first.get("geojson", {}).get("type") if isinstance(first.get("geojson"), dict) else None,
                json.dumps(first.get("boundingbox")), "nominatim", "medium",
            ),
        )
        db.commit()
        return [float(first["lon"]), float(first["lat"])]
    db.execute(
        "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, source) VALUES (?,?,?,NULL,?)",
        (query, "probe", "rau", "nominatim_negative"),
    )
    db.commit()
    return None


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))

    # Full Mureș course: the Arad 'Râul Mureș' geometry (source→mouth)
    arad = next(w for w in waters if w.get("name") == "Râul Mureș" and w.get("judet") == "Arad" and w.get("geometry"))
    parts = arad["geometry"]["coordinates"]
    print(f"full course: {len(parts)} parts, {sum(len(p) for p in parts)} pts")

    db = gc.get_db()
    queries = [
        ("Borzont", "Borzont, Harghita, România"),
        ("Subcetate", "Subcetate, Harghita, România"),
        ("Sălard", "Sălard, Mureș, România"),
        ("Deda", "Deda, Mureș, România"),
        ("Deva", "Deva, Hunedoara, România"),
    ]
    fracs = {}
    for label, q in queries:
        pt = geocode_cached(db, q)
        if not pt:
            print(f"  {label}: NO RESULT")
            continue
        fracs[label] = fraction_at(parts, pt)[0]
        print(f"  {label:12} ({pt[0]:.4f},{pt[1]:.4f}) -> frac {fracs[label]:.4f}")

    # Alba contract: project its own (partial) geometry midpoint onto the full course
    alba = next(w for w in waters if w.get("name") == "Râul Mureș" and w.get("judet") == "Alba" and w.get("geometry"))
    a_geom = alba["geometry"]
    a_coords = a_geom["coordinates"] if a_geom["type"] == "MultiLineString" else [a_geom["coordinates"]]
    a_mid = a_coords[0][len(a_coords[0]) // 2]
    alba_frac = fraction_at(parts, a_mid)[0]
    print(f"  Alba partial geom midpoint ({a_mid[0]:.4f},{a_mid[1]:.4f}) -> frac {alba_frac:.4f}")

    updates = {
        # contract placed at its DOWNSTREAM limit (where the next sector starts)
        "anpa-anpa-0337": fracs.get("Subcetate"),   # Râul Mureș I   (Borzont → Subcetate)
        "anpa-anpa-0323": fracs.get("Sălard"),      # Râul Mureș II  (Subcetate → Limita jud. Mureș = Tunel Sălard)
        "anpa-anpa-0453": fracs.get("Deda"),        # Râul Mureș IV  (Tunel Sălard → pod Deda)
        # Râul Mureș, cu afluenții (Hunedoara): was county-seat-projected onto
        # the PARTIAL Alba geometry (0.8734). Anchor it on Deva, the county
        # seat ON the river (full-course frac ~0.58).
        "Râul Mureș, cu afluenții": fracs.get("Deva"),
    }
    for slug, frac in updates.items():
        if frac is None:
            print(f"  SKIP {slug}: no anchor")
            continue
        if slug.startswith("Râul"):
            w = next(w for w in waters if w.get("name") == slug)
        else:
            w = next(w for w in waters if w.get("slug") == slug)
        w["course_frac"] = round(frac, 4)
        print(f"  -> {w['name']} ({w.get('judet')}) frac={w['course_frac']}")

    # Alba contract: representative position = its partial geometry midpoint
    # projected onto the full course (data-driven; no new geocode needed).
    alba = next(w for w in waters if w.get("name") == "Râul Mureș" and w.get("judet") == "Alba")
    if alba_frac is not None:
        alba["course_frac"] = round(alba_frac, 4)
        print(f"  -> {alba['name']} (Alba) frac={alba['course_frac']}")

    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n[done] Mureș contracts updated")


if __name__ == "__main__":
    main()
