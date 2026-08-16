#!/usr/bin/env python3
"""Fix the 'sebes' same-name family (t_e3ae3121).

The family has 8 waters; several carry ANOTHER county's same-name course
(the Homorodul-Nou / Doftana bug class):

  uyzo7o3j      Râul Sebeș (Alba)          had OSM 'raul sebes' (Brașov Valea
                                           Sebeșului course, 507 pts)  → now the
                                           real Alba Sebeș = 'sebes' cluster1
                                           (Cindrel source → Mureș, 1962 pts).
  qsvhz93s      Râul Sebeșul de Sus (Sibiu) had OSM 'oabanul de sus' (Poiana
                                           Brașov, 45 pts)  → now the unnamed
                                           Sebeș chain through Sebeșu de Sus
                                           village (ways 507047452+507047449+
                                           507047445, 427 pts) — bbox matches
                                           the contract bbox exactly.
  f02xtxw1      Râul Sebeșul de Jos (Sibiu) had OSM 'latorita de jos' (Vâlcea,
                                           262 pts)  → now the OSM named way
                                           495030900 'Sebeș' through Sebeșu de
                                           Jos village (302 pts, 100% Sibiu).
  romsilva-sibiu-sebesul-superior (Sibiu)  had the Olt-valley named way (the
                                           same 302-pt course as Sebeșul de Jos)
                                           → now JOINs riverGroup 'sebes' as the
                                           headwater sector (sectorStart 0,
                                           sectorEnd frac(Lac Oașa) = 0.2520),
                                           geometry-less (group-share pattern,
                                           like romsilva-brasov-buzaul-superior).

Unchanged (verified correct):
  anpa-anpa-0182  Valea Sebeșului (Brașov) — 'raul sebes' course, 100% Brașov ✓
  romsilva-alba-sebesul-mijlociu / -inferior — geometry-less group members ✓
  anpa-mures-sebes-21  Râul Sebeș (Mureș, Sovata) — 'sebes' cluster3 ✓

Also clears geometryByCounty on every changed water (stale clips from the
wrong-geometry era would otherwise hide the fixed course under the county
filter — pitfall #36).

Usage:
    python3 scripts/fix_sebes_family.py [--dry-run]
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
sys.path.insert(0, str(ROOT / "scripts"))

from audit_missing_rivers import load_osm_index, make_cluster_geoms  # noqa: E402
from sweep_multiway_rivers import chain_parts  # noqa: E402


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def flat_coords(geom):
    if geom["type"] == "LineString":
        return geom["coordinates"]
    return [p for part in geom["coordinates"] for p in part]


def bbox_of(coords):
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return [min(lons), min(lats), max(lons), max(lats)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    name_index, geoms = load_osm_index()

    # --- build the correct courses -------------------------------------
    # 1. Alba Sebeș = 'sebes' cluster1 (dedupe + chain into one LineString)
    cl1 = make_cluster_geoms(name_index["sebes"], geoms)[1]
    parts1 = (
        cl1["coordinates"] if cl1["type"] == "MultiLineString" else [cl1["coordinates"]]
    )
    chain1 = chain_parts(parts1)
    assert chain1 is not None, "sebes cluster1 must chain"
    alba_sebes_coords = [p for part in chain1 for p in part]

    # 2. Sebeșul de Sus (Sibiu) = unnamed chain through Sebeșu de Sus village
    sus_parts = [
        geoms[w]["geometry"]["coordinates"] for w in (507047452, 507047449, 507047445)
    ]
    # ways chain node-to-node already; concatenate
    sus_coords = sus_parts[0] + sus_parts[1][1:] + sus_parts[2][1:]
    # source→mouth: source at (24.405,45.591), mouth at (24.315,45.668)
    if sus_coords[0] != [24.404996, 45.5907305]:
        sus_coords = list(reversed(sus_coords))

    # 3. Sebeșul de Jos (Sibiu) = OSM named way 495030900 'Sebeș'
    jos_coords = geoms[495030900]["geometry"]["coordinates"]
    # source at (24.350,45.624) → mouth at (24.318,45.668); keep digitized order
    if jos_coords[0] != [24.3502575, 45.6236501]:
        jos_coords = list(reversed(jos_coords))

    fixes = {
        "uyzo7o3j": {
            "geom": {"type": "LineString", "coordinates": alba_sebes_coords},
            "bbox": bbox_of(alba_sebes_coords),
            "note": "Alba Râul Sebeș: detached Brașov 'raul sebes' course; attached real Alba Sebeș ('sebes' cluster1, Cindrel→Mureș, 1962 pts)",
        },
        "qsvhz93s": {
            "geom": {"type": "LineString", "coordinates": sus_coords},
            "bbox": bbox_of(sus_coords),
            "note": "Sebeșul de Sus (Sibiu): detached Poiana Brașov 'oabanul de sus'; attached unnamed Sebeș chain through Sebeșu de Sus village (427 pts, 100% Sibiu)",
        },
        "f02xtxw1": {
            "geom": {"type": "LineString", "coordinates": jos_coords},
            "bbox": bbox_of(jos_coords),
            "note": "Sebeșul de Jos (Sibiu): detached Vâlcea 'latorita de jos'; attached OSM named way 495030900 'Sebeș' through Sebeșu de Jos village (302 pts, 100% Sibiu)",
        },
    }

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    by_slug = {w["slug"]: w for w in waters}
    changed = []

    for slug, fix in fixes.items():
        w = by_slug.get(slug)
        if not w:
            print(f"[skip] {slug} not found")
            continue
        old_geom = bool(w.get("geometry"))
        print(f"[fix] {w['name']} ({w['judet']}) — {fix['note']}")
        if not args.dry_run:
            w["geometry"] = fix["geom"]
            w["bbox"] = [round(v, 5) for v in fix["bbox"]]
            w["geometryByCounty"] = {}
            w["source_detail"] = "sebes_family_fix:county_correct_course"
        changed.append(slug)

    # Sebeșul Superior: join riverGroup 'sebes' as the headwater sector,
    # geometry-less (group-share). sectorEnd = frac(Lac Oașa) on the shared course.
    sup = by_slug.get("romsilva-sibiu-sebesul-superior")
    if sup:
        print(f"[fix] {sup['name']} ({sup['judet']}) — join group 'sebes' as headwater sector (0 → 0.2520), geometry-less")
        if not args.dry_run:
            sup["riverGroup"] = "sebes"
            sup["sectorStart"] = 0.0
            sup["sectorEnd"] = 0.2520
            sup["geometry"] = None
            sup["bbox"] = None
            sup["geometryByCounty"] = {}
            sup["source_detail"] = "sebes_family_fix:join_sebes_group_headwater"
        changed.append(sup["slug"])

    print(f"\n[fix] {len(changed)} waters changed: {changed}")

    if not args.dry_run and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[fix] wrote waters.json")


if __name__ == "__main__":
    main()
