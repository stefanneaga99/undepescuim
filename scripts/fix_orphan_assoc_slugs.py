#!/usr/bin/env python3
"""t_45a0beae / A2+A3 — resolve orphan association slugs + clean directory slugs.

A2 — 4 association slugs referenced by waters but missing from
associations.json:

  a.fly-fishing-club-sibiu  -> fly-fishing-club-sibiu   (SAME org; the 'A.' is
                              the legal-entity abbreviation, dropped by the
                              arebaltapeste slug derivation. Directory entry
                              exists with full contacts. Fix: re-point the 3
                              ANPA waters.)
  aps-pro-pescar            -> pro-pescar               (SAME org; ANPA name
                              'APS PRO PESCAR' vs arebaltapeste 'Pro Pescar /
                              APS Pro Pescar'. Directory entry exists with
                              siteUrl + permitUrl. Fix: re-point the 5 ANPA
                              waters + backfill adresa from the locuri probe.)
  asociatia-fly-fishing-rarau -> NEW directory entry    (ANPA contract
                              85/10.01.2024, address Pojorâta, str. Izvor
                              nr. 880, Suceava — from anpa_contracts.jsonl.)
  cs-hunedoara              -> NEW directory entry      (ANPA contract
                              60/26.07.2018, address Călan, sat Strei, Ferma
                              Piscicolă F.N., Hunedoara.)

A3 — directory slugs never referenced by any water:
  acvps-fagetel-mortonca-   -> acvps-fagetel-mortonca   (trailing-dash artifact)
  aps-salmo-carpatica-lupeni- -> aps-salmo-carpatica-lupeni (trailing dash)
  a-p-s--sovata-2008        -> a-p-s-sovata-2008        (double-dash artifact)
  ajvps-bacau-              -> ajvps-bacau              (trailing dash + IS
                              referenced by 18 waters — re-point them too)
  ajvps-campina / app-filiala-suceava / aps-hunedoara   (keep: real directory
                              entries with no currently-contracted waters)

After renames, `ape` counts and `counties[]` are recomputed for every
association so the directory matches the waters exactly.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
FE_WATERS = ROOT / "public" / "data" / "waters.json"
LOCURI_ASSOC = ROOT / "data" / "processed" / "locuri_associations.jsonl"

# waters.json asociatie.slug -> canonical slug
WATER_RENAME = {
    "a.fly-fishing-club-sibiu": "fly-fishing-club-sibiu",
    "aps-pro-pescar": "pro-pescar",
    "ajvps-bacau-": "ajvps-bacau",
    "d-s--cluj": "d-s-cluj",
}

# associations.json slug -> canonical slug (trailing/double dash artifacts)
ASSOC_RENAME = {
    "acvps-fagetel-mortonca-": "acvps-fagetel-mortonca",
    "aps-salmo-carpatica-lupeni-": "aps-salmo-carpatica-lupeni",
    "a-p-s--sovata-2008": "a-p-s-sovata-2008",
    "ajvps-bacau-": "ajvps-bacau",
    "d-s--cluj": "d-s-cluj",
}

# embedded asociatie.name snapshot -> canonical name shown in the directory
# (keeps the water card's embedded fallback consistent with associations.json)
WATER_NAME_FIX = {
    "A.FLY FISHING CLUB SIBIU": "FLY FISHING CLUB SIBIU",
    "APS PRO PESCAR": "Pro Pescar",
}


def main() -> None:
    assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    print(f"[a2] associations {len(assocs)}, waters {len(waters)}")

    # 1. Rename association slugs (A3 trailing/double dashes)
    renamed = 0
    for a in assocs:
        if a["slug"] in ASSOC_RENAME:
            a["slug"] = ASSOC_RENAME[a["slug"]]
            renamed += 1

    # 2. Re-point water asociatie slugs (A2) + fix embedded names
    water_renamed = 0
    for w in waters:
        assoc = w.get("asociatie") or {}
        if assoc.get("slug") in WATER_RENAME:
            assoc["slug"] = WATER_RENAME[assoc["slug"]]
            water_renamed += 1
        if assoc.get("name") in WATER_NAME_FIX:
            assoc["name"] = WATER_NAME_FIX[assoc["name"]]

    # 3. Add the two missing directory entries (from anpa_contracts.jsonl)
    known = {a["slug"] for a in assocs}
    if "asociatia-fly-fishing-rarau" not in known:
        assocs.append({
            "slug": "asociatia-fly-fishing-rarau",
            "name": "ASOCIAȚIA FLY FISHING RARĂU",
            "name_long": "Asociația Fly Fishing Rarău",
            "ape": 0,
            "adresa": "localitatea Pojorâta, str. Izvor, nr. 880, județ Suceava",
            "id": "anpa-contract-85/10.01.2024",
            "counties": [],
            "reciprocity": "neconfirmată",
            "permitIssuer": "asociatie",
        })
        print("[a2] added asociatia-fly-fishing-rarau (ANPA contract 85/10.01.2024)")
    if "cs-hunedoara" not in known:
        assocs.append({
            "slug": "cs-hunedoara",
            "name": "CS HUNEDOARA",
            "name_long": "Club Sportiv Hunedoara",
            "ape": 0,
            "adresa": "localitatea Călan, sat Strei, Ferma Piscicolă F.N., județ Hunedoara",
            "id": "anpa-contract-60/26.07.2018",
            "counties": [],
            "reciprocity": "neconfirmată",
            "permitIssuer": "asociatie",
        })
        print("[a2] added cs-hunedoara (ANPA contract 60/26.07.2018)")

    # 4. Backfill pro-pescar adresa from locuri (the directory entry came from
    # the arebaltapeste snapshot which has no street address)
    locuri_by_name = {}
    try:
        for line in LOCURI_ASSOC.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                locuri_by_name[(row.get("name_normalized") or "").strip()] = row
    except FileNotFoundError:
        pass
    for a in assocs:
        if a["slug"] == "pro-pescar" and not a.get("adresa"):
            row = locuri_by_name.get("aps pro pescar") or locuri_by_name.get("pro pescar")
            if row and row.get("address"):
                a["adresa"] = row["address"]
                print(f"[a4] backfilled pro-pescar adresa: {row['address']}")

    # 5. Recompute ape + counties from the fixed waters
    slug_of = {}
    for a in assocs:
        slug_of[a["slug"]] = a
    counts = Counter()
    counties = defaultdict(set)
    for w in waters:
        s = (w.get("asociatie") or {}).get("slug")
        if s:
            counts[s] += 1
            if w.get("judet"):
                counties[s].add(w["judet"])
    for a in assocs:
        a["ape"] = counts.get(a["slug"], 0)
        a["counties"] = sorted(counties.get(a["slug"], []), key=str.casefold)

    # 6. Safety: no water may reference an unknown slug; no known slug may
    # keep a trailing dash
    known = {a["slug"] for a in assocs}
    unknown = sorted(s for s in counts if s and s not in known)
    if unknown:
        raise SystemExit(f"ABORT: waters reference unknown slugs: {unknown}")
    trailing = [s for s in known if s.endswith("-") or "--" in s]
    if trailing:
        raise SystemExit(f"ABORT: directory still has dash artifacts: {trailing}")

    FE_ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
    FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[a2] associations.json: {len(assocs)} entries ({renamed} slug renames)")
    print(f"[a2] waters.json: {water_renamed} asociatie re-points")
    for slug in ("fly-fishing-club-sibiu", "pro-pescar", "asociatia-fly-fishing-rarau", "cs-hunedoara", "ajvps-bacau"):
        a = slug_of.get(slug) or next((x for x in assocs if x["slug"] == slug), None)
        print(f"  {slug}: ape={a['ape'] if a else 'MISSING'} counties={a['counties'] if a else '?'} tel={a.get('telefon') if a else '?'}")
    orphans = sorted(s for s in counts if s and s not in {"anpa", "romsilva"} and s not in known)
    print(f"[a2] remaining orphan slugs: {orphans or 'none'}")


if __name__ == "__main__":
    main()