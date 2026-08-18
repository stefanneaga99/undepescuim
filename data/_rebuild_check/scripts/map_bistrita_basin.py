#!/usr/bin/env python3
"""Map the reported Bistrița basin (Broșteni/Borsec/Ceahlău) — t_66b48ee0 phase 1.

Fixes the exact area the user reported on mobile:
1. group 'bistrita' was keyed on the WRONG river: its geometry owner was
   'Râul Bistrița | Bistrița-Năsăud' (the Someșul-Mare-basin Bistrița, lon
   24.4-24.6) while the Suceava/Neamț/Bacău Bistrița (lon 25.0-26.6) had no
   drawn course at all. Now:
   - the B-N river gets its own group ('bistrita-bn');
   - the legacy duplicate 'Bistra Aurie II' is merged into
     'Râul Bistrița Aurie II' and removed;
   - the Siret-basin course (OSM 'bistrita' + 'bistrita'#4 clusters) is
     attached to ONE group owner (Râul Bistrița Aurie II);
   - every member gets an upstream→mouth course_frac so clicks resolve to
     the right contract (Voronoi).
2. Adds the missing ANPA contracts for the basin:
   - Râul Bistrița NEAMȚ (32 km, AJVPS NEAMȚ) — Baraj Reconstrucția→jud. Bacău
   - Râul Bistrița BACĂU (39 km, AJVPS BACĂU)
   - Râul Moldova NEAMȚ (40 km, AVPS BRADUL PIATRA NEAMȚ)
   - Râul Moldova NEAMȚ (40 km, AVPS ROMAN)
   - Râul Moldova SUCEAVA (59 km, AJVPS BOTOȘANI)
   - Râul Bistrița BISTRIȚA-NĂSĂUD (28 km — the second B-N contract, the
     25 km one is already mapped as 7oju77qb)
   - Râul Târnava Mică HARGHITA (5 km) + MUREȘ (96 km) -> tarnava-mica group
3. Attaches OSM geometry to Romsilva rows of the basin that were geometry-less:
   - Râul Bistricioara tronson I/II (Harghita) — 'bistricioara' cluster
   - Izvoarele Cracăului (Neamț) — 'cracau' cluster
4. Romsilva Sabasa (Neamț): no named OSM course — geocoded bbox fallback.

Usage: python3 scripts/map_bistrita_basin.py [--write] [--json-report PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _mapping_common import (  # noqa: E402
    FE_ASSOC,
    FE_WATERS,
    assoc_slug,
    build_county_centroids,
    build_osm_index,
    canonical_county,
    core,
    fraction_at_point,
    geom_bbox,
    load_fe,
    merge_geoms,
    order_course_linestring,
    pick_cluster,
    set_geometry,
    slugify,
)

ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"

# ANPA row lookup: (norm(water_name), norm(county)) -> [rows] (a county can
# have several contracts on the same river: Moldova Neamț BRADUL + ROMAN,
# Bistrița B-N 25 km + 28 km).
def load_anpa_index():
    idx = {}
    for line in ANPA_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        idx.setdefault((core(r.get("water_name", "")), core(r.get("county", ""))), []).append(r)
    return idx


def make_anpa_water(row: dict, county_title: str, assocs: list[dict],
                    waters: list[dict], slug_hint: str) -> dict:
    """Build a waters.json entry from an ANPA row (format matches existing)."""
    name = row["water_name"].strip()
    assoc_name = row.get("association", "")
    km = row.get("sector_km")
    ref = ""
    if row.get("contract_number"):
        ref = f"Contract {row['contract_number']}"
        if row.get("contract_date"):
            ref += f" ({row['contract_date']})"
    return {
        "slug": slug_hint,
        "name": name,
        "judet": county_title,
        "type": "ape",
        "subtype": "rau",
        "limite": (row.get("limits_text") or "").strip(),
        "dimensiune": f"{km:g} km" if isinstance(km, (int, float)) else (row.get("sector_raw") or ""),
        "pescuit_interzis": False,
        "referinta": ref,
        "coordinates": None,
        "driving": None,
        "bbox": None,
        "asociatie": {"name": assoc_name, "slug": assoc_slug(assoc_name, waters, assocs)},
        "source": "anpa",
        "source_detail": "anpa_map:bistrita-basin",
        "geometry": None,
    }


def add_water(waters: list[dict], w: dict, used_slugs: set[str]) -> None:
    base = w["slug"]
    slug = base
    i = 2
    while slug in used_slugs:
        slug = f"{base}-{i}"
        i += 1
    w["slug"] = slug
    used_slugs.add(slug)
    waters.append(w)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json-report", type=str)
    args = ap.parse_args()

    waters, assocs = load_fe()
    waters0 = [dict(w) for w in waters]  # pre-existing snapshot for dedupe
    used_slugs = {w["slug"] for w in waters}
    anpa_idx = load_anpa_index()
    county_centroids = build_county_centroids(waters)
    osm = build_osm_index()
    report = {"groups_fixed": [], "waters_added": [], "geometry_attached": [],
              "merged": [], "geocoded": [], "no_geometry": []}

    # ---------------------------------------------------------------
    # 1. Fix group 'bistrita' — wrong geometry owner (B-N river) and a
    #    legacy duplicate; attach the REAL Siret-basin course.
    # ---------------------------------------------------------------
    # (a) B-N Bistrița (Someșul-Mare basin) -> its own group.
    bn = next((w for w in waters if w["slug"] == "7oju77qb"), None)
    if bn:
        bn["riverGroup"] = "bistrita-bn"
        report["groups_fixed"].append("7oju77qb -> bistrita-bn (wrong river in 'bistrita' group)")
    # (b) legacy duplicate 'Bistra Aurie II' merged into 'Râul Bistrița Aurie II'
    dupe = next((w for w in waters if w["slug"] == "jfwp7w1y"), None)
    target = next((w for w in waters if w["slug"] == "2uxod40o"), None)
    if dupe and target:
        waters.remove(dupe)
        report["merged"].append("jfwp7w1y (Bistra Aurie II) -> 2uxod40o (Râul Bistrița Aurie II)")

    # (c) attach the real course to the group owner 2uxod40o: the Siret-basin
    # 'bistrita' clusters — the main Iacobeni→Piatra Neamț course (25.0-26.3)
    # PLUS the lower Piatra Neamț→Siret course (26.3-27.0, which the extract
    # stores as a separate cluster). Merged + ordered into ONE LineString so
    # the FE's orderParts no-ops and fractionAtPoint walks source→mouth.
    if target:
        course_parts = []
        for g in osm.get("bistrita", []):
            bb = geom_bbox(g)
            if not bb:
                continue
            # Siret-basin: main cluster starts < 25.5, lower cluster starts >= 26.3
            if bb[0] >= 24.95 and bb[1] < 47.7 and (bb[0] < 25.5 or bb[0] >= 26.3):
                course_parts.append(g)
        if course_parts:
            set_geometry(target, order_course_linestring(merge_geoms(course_parts)))
            target["source_detail"] = "anpa_map:full-course"
            report["geometry_attached"].append(
                f"2uxod40o (Râul Bistrița Aurie II) <- 'bistrita' Siret-basin clusters ({len(course_parts)})"
            )
        else:
            print("[warn] no Siret-basin Bistrița cluster found", file=sys.stderr)

    # (d) upstream→mouth rank across ALL 'bistrita' members (source first).
    members = [w for w in waters if w.get("riverGroup") == "bistrita"]
    order_names = [
        "Râul Bistrița Aurie I", "Râul Bistrița Aurie II", "Râul Bistrița Aurie III",
        "Râul Bistrița I Zugreni", "Râul Bistrița II", "Râul Bistrița IV",
        "Râul Bistrița V", "Râul Bistrița VI", "Râul Bistrița",
    ]
    def order_key(w):
        try:
            return order_names.index(w["name"])
        except ValueError:
            return len(order_names)
    members.sort(key=order_key)
    n = len(members)
    for i, m in enumerate(members):
        m["course_frac"] = round(i / (n - 1), 4) if n > 1 else None
    print(f"[bistrita] group now {n} members, fracs assigned "
          + ", ".join(f"{m['name']}={m['course_frac']}" for m in members))

    # ---------------------------------------------------------------
    # 2. Add the missing ANPA contracts.
    # ---------------------------------------------------------------
    def existing_km(name: str, county: str):
        """Km values of pre-existing waters with this exact name+county."""
        import re as _re
        for w in waters0:
            if w.get("name") == name and w.get("judet") == county:
                m = _re.match(r"([\d.]+)", w.get("dimensiune") or "")
                if m:
                    yield float(m.group(1))

    def row_already_present(row: dict, county_title_s: str) -> bool:
        name = row["water_name"].strip()
        km = row.get("sector_km")
        ekm = list(existing_km(name, county_title_s))
        if km is None:
            return bool(ekm)
        return any(abs(km - k) < 0.01 for k in ekm)

    new_specs = [
        # (name, county_raw, association filter or None, slug)
        ("Râul Bistrița", "NEAMȚ", None, "anpa-neamt-bistrita-32"),
        ("Râul Bistrița", "BACĂU", None, "anpa-bacau-bistrita-39"),
        ("Râul Moldova", "NEAMȚ", "AVPS BRADUL PIATRA NEAMȚ", "anpa-neamt-moldova-bradul"),
        ("Râul Moldova", "NEAMȚ", "AVPS ROMAN", "anpa-neamt-moldova-roman"),
        ("Râul Moldova", "SUCEAVA", None, "anpa-suceava-moldova-59"),
        ("Râul Bistrița", "BISTRIȚA - NĂSĂUD", None, "anpa-bn-bistrita-28"),
        ("Râul Târnava Mică", "HARGHITA", None, "anpa-harghita-tarnava-mica-5"),
        ("Râul Târnava Mică", "MUREȘ", None, "anpa-mures-tarnava-mica-96"),
    ]
    for wname, county_raw, assoc_filter, slug in new_specs:
        rows = anpa_idx.get((core(wname), core(county_raw)), [])
        if assoc_filter:
            rows = [r for r in rows if r.get("association") == assoc_filter]
        if not rows:
            print(f"[skip] no ANPA row for {wname} {county_raw} assoc={assoc_filter}")
            continue
        j = canonical_county(county_raw)
        for row in rows:
            if row_already_present(row, j):
                print(f"[skip] {wname} {j} km={row.get('sector_km')} already present")
                continue
            w = make_anpa_water(row, j, assocs, waters0, slug)
            add_water(waters, w, used_slugs)
            report["waters_added"].append(
                f"{wname} | {j} | {row.get('association')} | {row.get('sector_km')} km"
            )

    # group the new Bistrița contracts into 'bistrita' (Siret basin) — the B-N
    # 28 km contract joins the B-N river group 'bistrita-bn'; Moldova into
    # 'moldova'; Târnava Mică into 'tarnava-mica'
    for w in waters:
        if w["slug"] in ("anpa-neamt-bistrita-32", "anpa-bacau-bistrita-39"):
            w["riverGroup"] = "bistrita"
        elif w["slug"] == "anpa-bn-bistrita-28":
            w["riverGroup"] = "bistrita-bn"
        elif w["slug"] in ("anpa-neamt-moldova-bradul", "anpa-neamt-moldova-roman", "anpa-suceava-moldova-59"):
            w["riverGroup"] = "moldova"
        elif w["slug"] in ("anpa-harghita-tarnava-mica-5", "anpa-mures-tarnava-mica-96"):
            w["riverGroup"] = "tarnava-mica"

    # B-N river group: owner is 7oju77qb (25 km, has geometry); the new 28 km
    # contract is its downstream sector.
    for w in waters:
        if w.get("riverGroup") == "bistrita-bn":
            if w["slug"] == "anpa-bn-bistrita-28":
                w["course_frac"] = 0.75
            else:
                w["course_frac"] = 0.4

    # (d) exact sector intervals along the real course, measured by
    # fractionAtPoint on the ordered geometry at the ANPA/Romsilva limit
    # landmarks (Cârlibaba, Mestecăniș, conf. Dorna, baraj Zugreni, pod
    # Mălișor, Lunca, Fărcașa, pod Zahorna, Baraj Bicaz, Baraj Reconstrucția,
    # limită jud. Bacău). This tiles the whole course so clicks resolve to the
    # exact contract, incl. the reported area (Broșteni/Bicaz/Piatra Neamț).
    course_geom = target.get("geometry") if target else None

    def frac_at(lon, lat):
        if not course_geom:
            return None
        f = fraction_at_point(course_geom, [lon, lat])
        return None if f is None else round(f, 4)

    lm = {
        "carllibaba": frac_at(25.12, 47.56),
        "mestecanis": frac_at(25.28, 47.44),
        "dorna": frac_at(25.36, 47.35),
        "zugreni": frac_at(25.47, 47.30),
        "malisor": frac_at(25.85, 47.05),
        "lunca": frac_at(25.98, 47.08),
        "farceasa": frac_at(26.05, 46.96),
        "zahorna": frac_at(26.12, 46.94),
        "dam": frac_at(26.103, 46.938),
        "reconstrucia": frac_at(26.36, 46.92),
        "bacau_border": frac_at(26.55, 46.79),
    }
    print("[bistrita] landmark fracs: " + ", ".join(f"{k}={v}" for k, v in lm.items()))

    def sec_of(a, b):
        if a is None or b is None:
            return None
        return (min(a, b), max(a, b))

    SECTORS = {
        "anpa-anpa-0570": sec_of(0.0, lm["carllibaba"]),      # Aurie I
        "2uxod40o": sec_of(lm["carllibaba"], lm["mestecanis"]),  # Aurie II
        "anpa-anpa-0562": sec_of(lm["mestecanis"], lm["dorna"]),  # Aurie III
        "anpa-anpa-0563": sec_of(lm["dorna"], lm["zugreni"]),  # I Zugreni
        "anpa-anpa-0569": sec_of(lm["zugreni"], lm["malisor"]),  # II (48 km)
        "romsilva-neamt-bistrita-iv": sec_of(lm["lunca"], lm["farceasa"]),  # IV
        "anpa-anpa-0463": sec_of(lm["farceasa"], lm["zahorna"]),  # V
        "anpa-anpa-0455": sec_of(lm["dam"], lm["reconstrucia"]),  # VI
        "anpa-neamt-bistrita-32": sec_of(lm["reconstrucia"], lm["bacau_border"]),  # NEAMȚ 32
    }
    members = [w for w in waters if w.get("riverGroup") == "bistrita"]
    for m in members:
        sec = SECTORS.get(m["slug"])
        if sec and sec[0] is not None and sec[1] is not None and sec[1] > sec[0]:
            m["sectorStart"], m["sectorEnd"] = sec
            m["course_frac"] = round((sec[0] + sec[1]) / 2, 4)
        elif m["slug"] == "anpa-bacau-bistrita-39":
            m["course_frac"] = 1.0
            if lm["bacau_border"] is not None:
                m["sectorStart"] = lm["bacau_border"]
                m["sectorEnd"] = 1.0
            else:
                m.pop("sectorStart", None)
                m.pop("sectorEnd", None)
    print("[bistrita] final sectors:")
    for m in sorted(members, key=lambda x: (x.get("course_frac") or 0)):
        print(f"    {m['name']} | {m['judet']} | frac={m.get('course_frac')} | sec={m.get('sectorStart')}-{m.get('sectorEnd')}")

    # Moldova fracs: Suceava sectors keep their real positions; the new
    # contracts slot in — BRADUL (Boroaia→Tupilați) upstream of ROMAN
    # (Tupilați→Siret confluence), which owns the mouth.
    for w in waters:
        if w["slug"] == "anpa-suceava-moldova-59":
            w["course_frac"] = 0.45
        elif w["slug"] == "anpa-neamt-moldova-bradul":
            w["course_frac"] = 0.72
        elif w["slug"] == "anpa-neamt-moldova-roman":
            w["course_frac"] = 0.92

    # Târnava Mică fracs: Harghita = source sector, Mureș = middle
    for w in waters:
        if w["slug"] == "anpa-harghita-tarnava-mica-5":
            w["course_frac"] = 0.02
        elif w["slug"] == "anpa-mures-tarnava-mica-96":
            w["course_frac"] = 0.45

    # ---------------------------------------------------------------
    # 3. Romsilva geometry for the basin: Bistricioara (Harghita) + Cracău
    # ---------------------------------------------------------------
    # Bistricioara tronsoane — attach the Harghita cluster to tronson I
    tr1 = next((w for w in waters if w["slug"] == "romsilva-harghita-bistricioara-tronson-i"), None)
    if tr1:
        geom, cl, score = pick_cluster(["bistricioara"], "Harghita", osm, county_centroids)
        if geom:
            bb = geom_bbox(geom)
            # must be the Harghita one (lon 25.4-26.0), not Vâlcea (23.9-24.1)
            if bb and bb[0] > 25.0:
                set_geometry(tr1, geom)
                tr1["source_detail"] = "romsilva_map:bistrita-basin"
                report["geometry_attached"].append(f"romsilva-harghita-bistricioara-tronson-i <- '{cl}' (score {score:.2f})")
    tr2 = next((w for w in waters if w["slug"] == "romsilva-harghita-bistricioara-tronson-ii"), None)
    if tr2:
        tr2["course_frac"] = 0.75
    if tr1:
        tr1["course_frac"] = 0.25

    # Izvoarele Cracăului — 'cracau' cluster
    cr = next((w for w in waters if w["slug"] == "romsilva-neamt-izvoarele-cracaului"), None)
    if cr:
        geom, cl, score = pick_cluster(["cracau"], "Neamț", osm, county_centroids)
        if geom:
            set_geometry(cr, geom)
            cr["source_detail"] = "romsilva_map:bistrita-basin"
            report["geometry_attached"].append(f"romsilva-neamt-izvoarele-cracaului <- '{cl}' (score {score:.2f})")

    # ---------------------------------------------------------------
    # 4. Sabasa (Neamț) — no named OSM course; geocode for a clickable bbox
    # ---------------------------------------------------------------
    sab = next((w for w in waters if w["slug"] == "romsilva-neamt-sabasa"), None)
    if sab:
        try:
            q = urllib.parse.quote("Sabasa, Neamț, România")
            req = urllib.request.Request(
                f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={q}",
                headers={"User-Agent": "undepescuim-map/1.0 (river mapping)"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data:
                lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
                bb = data[0].get("boundingbox")
                if bb:
                    sab["bbox"] = [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]
                sab["coordinates"] = [lon, lat]
                sab["source_detail"] = "romsilva_map:geocode"
                report["geocoded"].append(f"romsilva-neamt-sabasa -> {lat:.4f},{lon:.4f}")
            else:
                report["no_geometry"].append("romsilva-neamt-sabasa (no OSM course, geocode empty)")
        except Exception as e:  # noqa: BLE001
            report["no_geometry"].append(f"romsilva-neamt-sabasa (geocode failed: {e})")

    # ---------------------------------------------------------------
    # report + write
    # ---------------------------------------------------------------
    print("\n=== REPORT ===")
    for k, v in report.items():
        if v:
            print(f"{k}:")
            for x in v:
                print(f"  - {x}")
    if args.json_report:
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[report] {args.json_report}")

    if args.write:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
