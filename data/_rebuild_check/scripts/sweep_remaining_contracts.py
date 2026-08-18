#!/usr/bin/env python3
"""Full sweep of remaining contracted waters (t_66b48ee0 phase 2).

Maps every remaining 'anpa-missing'/'areba-missing' contracted row across all
counties, plus geometry for the last Romsilva rows that were mapped as
name-bug duplicates ('Râul Râul X' -> 'Râul X') without geometry, and fixes
the audit's present-hidden groups.

ANPA rows added (with OSM geometry where a named course exists):
  Someșul Mare B-N (61 km) -> somesul-mare group
  Someșul Mare SĂLAJ (93 km) -> somes group (the Sălaj stretch of the Someș)
  Crasna SĂLAJ (65 km) -> crasna group (owner: Râul Crasna (Frumușaua))
  Crasna VASLUI (43 km) -> own group (Vaslui Crasna, different river)
  Sebeș MUREȘ (21 km) -> own group (nearest Sebeș cluster, county-guarded)
  Miletin IAȘI (35 km), Țibleș MARAMUREȘ (27 km), Neajlov GIURGIU,
  Câlniștea TELEORMAN, Călmățui TELEORMAN, Șușița VRANCEA (61 km),
  Râmnicu Sărat VRANCEA, Pârâul Pământ Alb TIMIȘ (the audit's last
  anpa-missing — matched to the WRONG county cluster before).

Romsilva renames + geometry (rows were present as 'Râul Râul X' without geom):
  Râul Şes, Râul Mare Superior, Râul Bărbat Superior/Inferior (sectors),
  Râul Mare Porumbacu, Pârâul Bistrița (Vâlcea), Izvorul Lotrului (-> lotru
  group, source sector).

Present-hidden fixes: cerna-herculane group geometry, veriga, valea stanca,
bega luncani, valea iadului (if a Bihor cluster exists).

Usage: python3 scripts/sweep_remaining_contracts.py [--write] [--json-report PATH]
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
    pick_cluster,
    set_geometry,
    slugify,
)

ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"


def county_title(c: str) -> str:
    return canonical_county(c)


def make_anpa_water(row: dict, ct: str, assocs: list[dict], waters: list[dict],
                    slug_hint: str) -> dict:
    name = row["water_name"].strip()
    km = row.get("sector_km")
    ref = ""
    if row.get("contract_number"):
        ref = f"Contract {row['contract_number']}"
        if row.get("contract_date"):
            ref += f" ({row['contract_date']})"
    return {
        "slug": slug_hint,
        "name": name,
        "judet": ct,
        "type": "ape",
        "subtype": "rau",
        "limite": (row.get("limits_text") or "").strip(),
        "dimensiune": f"{km:g} km" if isinstance(km, (int, float)) else (row.get("sector_raw") or ""),
        "pescuit_interzis": False,
        "referinta": ref,
        "coordinates": None,
        "driving": None,
        "bbox": None,
        "asociatie": {"name": row.get("association", ""), "slug": assoc_slug(row.get("association", ""), waters, assocs)},
        "source": "anpa",
        "source_detail": "anpa_map:sweep",
        "geometry": None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json-report", type=str)
    args = ap.parse_args()

    waters, assocs = load_fe()
    waters0 = [dict(w) for w in waters]
    used_slugs = {w["slug"] for w in waters}
    county_centroids = build_county_centroids(waters)
    osm = build_osm_index()
    report = {"waters_added": [], "renamed": [], "geometry_attached": [],
              "sectors_set": [], "geocoded": [], "skipped": [], "no_geometry": []}

    # County-proximity guard for OSM cluster picks: score < MIN_SCORE means the
    # best cluster is > ~2 deg from the county centroid (wrong county).
    MIN_SCORE = 0.85
    # Clusters that exist in the extract but in the WRONG county (verified):
    # the only 'valea iadului' is in Covasna, the only 'botiza' is in the
    # south, the only 'dragomira' is near Focșani — none match the Bihor /
    # Maramureș / Botoșani waters of the same name. Keep those invisible
    # rather than drawing a wrong-place course.
    REJECT_GEOM = {
        "romsilva-bihor-valea-iadului-superior",
        "romsilva-maramures-botiza",
        "anpa-anpa-0559",
    }

    anpa = [json.loads(l) for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    def anpa_rows(wname, county_norm):
        return [r for r in anpa
                if core(r.get("water_name", "")) == core(wname)
                and core(r.get("county", "")) == core(county_norm)]

    def existing_km(name, ct):
        import re as _re
        for w in waters0:
            if w.get("name") == name and w.get("judet") == ct:
                m = _re.match(r"([\d.]+)", w.get("dimensiune") or "")
                if m:
                    yield float(m.group(1))

    def row_present(row, ct):
        km = row.get("sector_km")
        ekm = list(existing_km(row["water_name"].strip(), ct))
        if km is None:
            return bool(ekm)
        return any(abs(km - k) < 0.01 for k in ekm)

    def add_from_anpa(wname, county_raw, slug, group=None, geom_targets=None,
                      course_frac=None, assoc_filter=None):
        ct = county_title(county_raw)
        rows = anpa_rows(wname, county_raw)
        if assoc_filter:
            rows = [r for r in rows if r.get("association") == assoc_filter]
        for row in rows:
            if row_present(row, ct):
                report["skipped"].append(f"{wname} {ct} km={row.get('sector_km')} (already present)")
                continue
            w = make_anpa_water(row, ct, assocs, waters0, slug)
            if group:
                w["riverGroup"] = group
            if course_frac is not None:
                w["course_frac"] = course_frac
            if geom_targets:
                geom, cl, score = pick_cluster(geom_targets, ct, osm, county_centroids)
                if geom and score >= MIN_SCORE:
                    set_geometry(w, geom)
                    w["source_detail"] = f"anpa_map:sweep:{cl}"
                    report["geometry_attached"].append(f"{w['name']} {ct} <- '{cl}' (score {score:.2f})")
                else:
                    report["no_geometry"].append(
                        f"{w['name']} {ct} (no OSM cluster in county {geom_targets}, best score {score:.2f})"
                    )
            # slug dedupe
            base = w["slug"]
            slug2 = base
            i = 2
            while slug2 in used_slugs:
                slug2 = f"{base}-{i}"
                i += 1
            w["slug"] = slug2
            used_slugs.add(slug2)
            waters.append(w)
            report["waters_added"].append(f"{w['name']} | {ct} | {row.get('association')} | {row.get('sector_km')} km")

    # ------------------------------------------------------------------
    # DATA BUG FIX: 'Râul Călmățui | Brăila' carried the TELEORMAN Călmățui
    # geometry (lon 24.6-25.2 — a wrong-county pick from an earlier run),
    # skewing Brăila's county centroid. Re-attach the Buzău/Brăila Călmățui
    # cluster (lon > 26) that matches the water's own bbox.
    # ------------------------------------------------------------------
    calmatui_braila = next((w for w in waters if w.get("judet") == "Brăila" and w.get("name") == "Râul Călmățui"), None)
    if calmatui_braila:
        for g in osm.get("calmatui", []):
            bb = geom_bbox(g)
            if bb and bb[0] > 26.0:
                set_geometry(calmatui_braila, g)
                calmatui_braila["source_detail"] = "sweep:fix-wrong-county-geom"
                report["geometry_attached"].append(
                    "Râul Călmățui (Brăila): re-attached Buzău/Brăila cluster (was Teleorman geometry)"
                )
                break

    # rebuild county centroids now that Brăila's geometry is sane
    county_centroids = build_county_centroids(waters)

    # ------------------------------------------------------------------
    # ANPA rows
    # ------------------------------------------------------------------
    add_from_anpa("Râul Someșul Mare", "BISTRIȚA - NĂSĂUD", "anpa-bn-somesul-mare-61",
                  group="somesul-mare", course_frac=0.2)
    add_from_anpa("Râul Someșul Mare", "SĂLAJ", "anpa-salaj-somesul-mare-93",
                  group="somes", course_frac=0.3)
    add_from_anpa("Râul Crasna", "SĂLAJ", "anpa-salaj-crasna-65",
                  group="crasna", course_frac=0.5)
    add_from_anpa("Râul Crasna", "VASLUI", "anpa-vaslui-crasna-43",
                  group="crasna-vaslui", geom_targets=["crasna"])
    add_from_anpa("Râul Sebeș", "MUREȘ", "anpa-mures-sebes-21",
                  group="sebes-mures", geom_targets=["sebes"])
    add_from_anpa("Râul Miletin", "IAȘI", "anpa-iasi-miletin-35",
                  group="miletin", geom_targets=["miletin"])
    add_from_anpa("Râul Țibleș", "MARAMUREȘ", "anpa-maramures-tibles-27",
                  group="tibles", geom_targets=["tibles"])
    add_from_anpa("Râul Neajlov", "GIURGIU", "anpa-giurgiu-neajlov",
                  group="neajlov", geom_targets=["neajlov"])
    add_from_anpa("Râul Câlniștea", "TELEORMAN", "anpa-teleorman-calnistea",
                  group="calnistea", geom_targets=["calnistea"])
    add_from_anpa("Râul Călmățui", "TELEORMAN", "anpa-teleorman-calmatui",
                  group="calmatui-teleorman", geom_targets=["calmatui"])
    add_from_anpa("Râul Șușița", "VRANCEA", "anpa-vrancea-susita-61",
                  group="susita-vrancea", geom_targets=["susita"])
    add_from_anpa("Râul Râmnicu Sărat", "VRANCEA", "anpa-vrancea-ramnicu-sarat",
                  group="ramnicu-sarat", geom_targets=["ramnicu sarat"])
    add_from_anpa("Pârâul Pământ Alb", "TIMIȘ", "anpa-timis-pamant-alb",
                  group="pamant-alb", geom_targets=["pamant alb"])

    # Lac acumulare Arpașu (Brașov) — lake, no river geometry; geocode a bbox
    arpasu_row = anpa_rows("Lac acumulare Arpașu", "BRAȘOV")
    if arpasu_row and not row_present(arpasu_row[0], "Brașov"):
        w = make_anpa_water(arpasu_row[0], "Brașov", assocs, waters0, "anpa-brasov-arpasu")
        w["subtype"] = "lac"
        try:
            q = urllib.parse.quote("Lacul Arpașu, Brașov, România")
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
                    w["bbox"] = [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]
                w["coordinates"] = [lon, lat]
                w["source_detail"] = "anpa_map:geocode"
                report["geocoded"].append(f"Lac acumulare Arpașu -> {lat:.4f},{lon:.4f}")
            else:
                report["no_geometry"].append("Lac acumulare Arpașu (geocode empty)")
        except Exception as e:  # noqa: BLE001
            report["no_geometry"].append(f"Lac acumulare Arpașu (geocode failed: {e})")
        waters.append(w)
        used_slugs.add(w["slug"])
        report["waters_added"].append("Lac acumulare Arpașu | Brașov | AVPS FĂGĂRAȘ")

    # ------------------------------------------------------------------
    # Romsilva renames + geometry (name-bug duplicates from t_1f8b1b06)
    # ------------------------------------------------------------------
    def romsilva_fix(slug, new_name, geom_targets, group=None, sector=None):
        w = next((x for x in waters if x["slug"] == slug), None)
        if not w:
            return
        if new_name and w["name"] != new_name:
            report["renamed"].append(f"{w['name']} -> {new_name}")
            w["name"] = new_name
        if geom_targets:
            geom, cl, score = pick_cluster(geom_targets, w["judet"], osm, county_centroids)
            if geom and score >= MIN_SCORE:
                set_geometry(w, geom)
                w["source_detail"] = f"romsilva_map:sweep:{cl}"
                report["geometry_attached"].append(f"{w['name']} <- '{cl}' (score {score:.2f})")
            else:
                report["no_geometry"].append(
                    f"{w['name']} (no OSM cluster in county {geom_targets}, best {score:.2f})"
                )
        if sector:
            w["sectorStart"], w["sectorEnd"] = sector
            w["course_frac"] = round((sector[0] + sector[1]) / 2, 4)
            report["sectors_set"].append(f"{w['name']} {sector}")

    romsilva_fix("romsilva-hunedoara-raul-ses", "Râul Şes", ["ses", "raul ses", "paraul ses"])
    romsilva_fix("romsilva-hunedoara-raul-mare-superior", "Râul Mare Superior", ["raul mare"])
    romsilva_fix("romsilva-sibiu-raul-mare-porumbacu", "Râul Mare Porumbacu", ["porumbacu"])
    romsilva_fix("romsilva-valcea-paraul-bistrita", "Pârâul Bistrița", ["bistrita"])
    romsilva_fix("romsilva-valcea-izvorul-lotrului", None, ["lotru"], group="lotru")

    # Bărbat Superior/Inferior — same course, split by km (17/42, 25/42)
    barbat_geom, barbat_cl, barbat_score = pick_cluster(["barbat"], "Hunedoara", osm, county_centroids)
    sup = next((x for x in waters if x["slug"] == "romsilva-hunedoara-raul-barbat-superior"), None)
    inf = next((x for x in waters if x["slug"] == "romsilva-hunedoara-raul-barbat-inferior"), None)
    if barbat_geom and sup and inf:
        from _mapping_common import km_to_frac
        f_sup_end = km_to_frac(barbat_geom, 17.0)
        if f_sup_end is None or not (0 < f_sup_end < 1):
            f_sup_end = 17.0 / 42.0
        for w, sec in ((sup, (0.0, f_sup_end)), (inf, (f_sup_end, 1.0))):
            w["sectorStart"], w["sectorEnd"] = sec
            w["course_frac"] = round((sec[0] + sec[1]) / 2, 4)
        set_geometry(sup, barbat_geom)
        sup["source_detail"] = "romsilva_map:sweep:barbat"
        report["geometry_attached"].append(f"Râul Bărbat Superior <- '{barbat_cl}' (km split 17/42)")
        report["sectors_set"].append(f"Bărbat Superior [0,{f_sup_end:.3f}] / Inferior [{f_sup_end:.3f},1]")
        # ensure the group is 'raul-barbat' (existing) with ONE owner
        inf["geometry"] = None
        inf["source_detail"] = "romsilva_map:group-shares-course"
        for w in (sup, inf):
            w["riverGroup"] = "raul-barbat"
    elif sup and inf:
        report["no_geometry"].append("Râul Bărbat Superior/Inferior (no 'barbat' cluster)")

    # Izvorul Lotrului -> lotru group (source sector; the lotru group owner has
    # the full course). Sector [0, 0.47] = izvoare→Lac Vidra (42/90 km approx).
    izv = next((x for x in waters if x["slug"] == "romsilva-valcea-izvorul-lotrului"), None)
    if izv:
        izv["riverGroup"] = "lotru"
        izv["sectorStart"], izv["sectorEnd"] = 0.0, 0.47
        izv["course_frac"] = 0.2
        izv["geometry"] = None
        izv["source_detail"] = "romsilva_map:group-shares-course"
        # also give the other lotru members explicit sectors so clicks tile
        for w in waters:
            if w.get("riverGroup") == "lotru" and w["slug"] != "romsilva-valcea-izvorul-lotrului":
                if w["name"] == "Râul Lotru Superior":
                    w["sectorStart"], w["sectorEnd"] = 0.47, 0.65
                    w["course_frac"] = 0.56
                elif w["name"] == "Râul Lotru mijlociu":
                    w["sectorStart"], w["sectorEnd"] = 0.65, 0.85
                    w["course_frac"] = 0.75
                elif w["name"] == "Râul Lotrul Inferior":
                    w["sectorStart"], w["sectorEnd"] = 0.85, 1.0
                    w["course_frac"] = 0.92
        report["sectors_set"].append("Izvorul Lotrului -> lotru group [0,0.47]; Lotru S/M/I tiled")

    # ------------------------------------------------------------------
    # present-hidden fixes (audit): attach geometry where a cluster exists
    # ------------------------------------------------------------------
    def attach_if_possible(slug, targets):
        w = next((x for x in waters if x["slug"] == slug), None)
        if not w:
            return
        if slug in REJECT_GEOM:
            report["no_geometry"].append(
                f"{w['name']} ({w['judet']}) hidden — only OSM '{targets}' cluster is in the wrong county"
            )
            return
        geom, cl, score = pick_cluster(targets, w["judet"], osm, county_centroids)
        if geom and score >= MIN_SCORE:
            set_geometry(w, geom)
            w["source_detail"] = f"sweep:hidden:{cl}"
            report["geometry_attached"].append(f"{w['name']} ({w['judet']}) <- '{cl}' (score {score:.2f})")
        else:
            report["no_geometry"].append(
                f"{w['name']} ({w['judet']}) hidden — no OSM cluster in county {targets} (best {score:.2f})"
            )

    attach_if_possible("anpa-anpa-0202", ["veriga"])                    # Japșa Veriga, Brăila
    attach_if_possible("anpa-anpa-0204", ["valea stanca", "stanca"])    # Japșa Stanca, Brăila
    attach_if_possible("romsilva-timis-bega-superior-luncani", ["bega luncani"])
    attach_if_possible("romsilva-bihor-valea-iadului-superior", ["valea iadului", "iad", "paraul iadului"])
    attach_if_possible("romsilva-maramures-botiza", ["botiza"])
    attach_if_possible("anpa-anpa-0559", ["dragomira"])                 # Acumulare Dragomira, Botoșani

    # cerna-herculane group (Caraș-Severin + Mehedinți Romsilva rows) — the
    # Herculane Cerna course ('cerna' cluster at lon 22.38-22.79).
    cerna_geom, cerna_cl, cerna_score = pick_cluster(
        ["cerna", "raul cerna"], "Mehedinți", osm, county_centroids)
    if cerna_geom:
        group_members = [w for w in waters if w.get("riverGroup") == "cerna-herculane"]
        ordered = sorted(group_members, key=lambda w: 0 if "Superioară" in w["name"] else (1 if "mijlocie" in w["name"] else 2))
        owner = ordered[0] if ordered else None
        if owner:
            set_geometry(owner, cerna_geom)
            owner["source_detail"] = f"sweep:hidden:{cerna_cl}"
            report["geometry_attached"].append(f"{owner['name']} <- '{cerna_cl}' (group owner)")
        for i, w in enumerate(ordered):
            if w is not owner:
                w["geometry"] = None
                w["source_detail"] = "sweep:hidden:group-shares-course"
            w["course_frac"] = round((i + 1) / (len(ordered) + 1), 4)
    else:
        report["no_geometry"].append("cerna-herculane group (no Cerna cluster near Mehedinți)")

    # ------------------------------------------------------------------
    # report + write
    # ------------------------------------------------------------------
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
