#!/usr/bin/env python3
"""Fix Bâsca Mare / Bâsca Mică associations (task t_67d8a9a3).

Verification result: the user report is CONFIRMED. The ANPA contracted list
has NO Bâsca Mare / Bâsca Mică rows — those rivers are NOT AJVPS Buzău
waters. The official ANPA "Lista habitatelor piscicole naturale din apele de
munte rămase în administrarea directă a RNP - Romsilva" (Protocol
12935/LAV/17.09.2013, ANEXA 1) administers them to Romsilva, split by
Direcția Silvică:

  Bâsca Mare   D.S. Covasna  "Izvoare - la confl cu pârâul Paltinu"        18 Km  (O.S. Comandău)
  Bâsca Mare   D.S. Buzău    "Pct. Paltenul Unguresc - la confluența cu
                              Bâsca Mare [Mică]"                            45 Km  (O.S. Gura Teghii)
  Bâsca Mică   D.S. Covasna  "Izvoare - la confl.cu pârâul Colobuci"       15 Km  (O.S. Comandău)
  Bâsca Mică   D.S. Buzău    "De la izvoare - la confl.cu Bâsca Mare"      68 Km  (O.S. Gura Teghii)

This script:
1. Splits the basca-mare water into TWO sector waters sharing the OSM course:
   - basca-mare (geometry owner) = D.S. Buzău sector [0.670, 1]
   - basca-mare-covasna (no geometry) = D.S. Covasna sector [0, 0.670)
   The split fraction 0.670 = the Covasna/Buzău county border crossing on the
   OSM course (authoritative OSM admin boundary, relation 2248621; the river
   leaves Covasna for good at that point — the "Paltenul Unguresc" area).
2. Reassigns basca-mica to D.S. Buzău (the mapped OSM course is entirely in
   Buzău county; the 15 km D.S. Covasna headwater above Pârâul Colobuci is
   not mapped in OSM and is noted in the referinta).
3. Adds the two Direcția Silvică associations to the registry.

Usage: python3 scripts/fix_basca_contracts.py [--write]
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
ASSOC_FE = ROOT / "public" / "data" / "associations.json"
ASSOC_PROC = ROOT / "data" / "processed" / "arebaltapeste_associations.jsonl"
SOURCES = ROOT / "data" / "processed" / "sources.jsonl"

SPLIT_FRAC = 0.670  # Covasna→Buzău border crossing on the Bâsca Mare course

REFERINTA = (
    "Administrat de RNP-Romsilva – ape de munte în administrare directă "
    "(Protocol 12935/LAV/17.09.2013, ANEXA 1 – Lista habitatelor piscicole "
    "naturale din apele de munte)"
)

NEW_ASSOC = [
    {
        "slug": "directia-silvica-covasna",
        "name": "Direcția Silvică Covasna",
        "name_long": "Direcția Silvică Covasna – Regia Națională a Pădurilor Romsilva",
        "type": "ds",
        "ape": 1,
        "adresa": None,
        "telefon": "0267351890",
        "siteUrl": "https://sfgh.rosilva.ro/",
        "bbox": None,
        "id": "anpa-romsilva-ds-covasna",
    },
    {
        "slug": "directia-silvica-buzau",
        "name": "Direcția Silvică Buzău",
        "name_long": "Direcția Silvică Buzău – Regia Națională a Pădurilor Romsilva",
        "type": "ds",
        "ape": 2,
        "adresa": "str. Mareșal Averescu, nr. 5, Buzău",
        "telefon": None,
        "siteUrl": "https://buzau.rosilva.ro/",
        "bbox": None,
        "id": "anpa-romsilva-ds-buzau",
    },
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))

    def find(slug: str):
        return next(w for w in waters if w["slug"] == slug)

    bm = find("basca-mare")
    bmica = find("basca-mica")

    # --- 1. Bâsca Mare: geometry owner becomes the D.S. Buzău sector ---
    bm.update({
        "judet": "Buzău",
        "limite": "Pct. Paltenul Unguresc – confluența cu Bâsca Mică",
        "dimensiune": "45 Km",
        "referinta": REFERINTA,
        "asociatie": {
            "name": "Direcția Silvică Buzău",
            "name_long": "Direcția Silvică Buzău – Regia Națională a Pădurilor Romsilva",
            "slug": "directia-silvica-buzau",
        },
        "sectorStart": SPLIT_FRAC,
        "sectorEnd": 1.0,
        "course_frac": round((SPLIT_FRAC + 1.0) / 2, 4),
        "riverGroup": "basca-mare",
        "source": "anpa_romsilva",
        "source_detail": "romsilva_sector_split",
    })

    # --- 2. Bâsca Mare: new D.S. Covasna headwater sector (no geometry) ---
    covasna = {
        "slug": "basca-mare-covasna",
        "name": "Râul Bâsca Mare",
        "judet": "Covasna",
        "type": "ape",
        "subtype": "rau",
        "limite": "Izvoare – confluența cu pârâul Paltinu",
        "dimensiune": "18 Km",
        "pescuit_interzis": False,
        "referinta": REFERINTA,
        "coordinates": None,
        "driving": None,
        "bbox": None,
        "asociatie": {
            "name": "Direcția Silvică Covasna",
            "name_long": "Direcția Silvică Covasna – Regia Națională a Pădurilor Romsilva",
            "slug": "directia-silvica-covasna",
        },
        "geometry": None,
        "source": "anpa_romsilva",
        "source_detail": "romsilva_sector_split",
        "riverGroup": "basca-mare",
        "sectorStart": 0.0,
        "sectorEnd": SPLIT_FRAC,
        "course_frac": round(SPLIT_FRAC / 2, 4),
    }
    if not any(w["slug"] == "basca-mare-covasna" for w in waters):
        waters.append(covasna)

    # --- 3. Bâsca Mică: whole mapped course = D.S. Buzău sector ---
    bmica.update({
        "judet": "Buzău",
        "limite": "De la izvoare – la confluența cu Bâsca Mare",
        "dimensiune": "68 Km",
        "referinta": (
            REFERINTA + "; sectorul de izvoare (15 km, până la Pârâul Colobuci) "
            "este administrat de D.S. Covasna / O.S. Comandău"
        ),
        "asociatie": {
            "name": "Direcția Silvică Buzău",
            "name_long": "Direcția Silvică Buzău – Regia Națională a Pădurilor Romsilva",
            "slug": "directia-silvica-buzau",
        },
        "riverGroup": "basca-mica",
        "source": "anpa_romsilva",
        "source_detail": "romsilva_sector_split",
    })
    # keep geometry; single-member group resolves to the water itself on click

    # --- 4. Association registry (FE + processed) ---
    assoc_fe = json.loads(ASSOC_FE.read_text(encoding="utf-8"))
    existing_slugs = {a["slug"] for a in assoc_fe}
    for a in NEW_ASSOC:
        fe_entry = {k: a.get(k) for k in ("slug", "name", "name_long", "ape", "adresa", "telefon", "siteUrl", "bbox", "id")}
        if a["slug"] not in existing_slugs:
            assoc_fe.append(fe_entry)
        else:
            print(f"[skip] association {a['slug']} already in associations.json")

    assoc_proc = [json.loads(l) for l in ASSOC_PROC.read_text(encoding="utf-8").splitlines() if l.strip()]
    proc_slugs = {a["slug"] for a in assoc_proc}
    for a in NEW_ASSOC:
        if a["slug"] in proc_slugs:
            continue
        proc_entry = {
            "id": a["id"],
            "source": "anpa_romsilva",
            "file": "Lista-habitate-Romsilva.txt",
            "source_row": None,
            "name": a["name"],
            "name_long": a["name_long"],
            "name_normalized": a["slug"].replace("-", " "),
            "type": "ds",
            "slug": a["slug"],
            "address": a["adresa"],
            "phone": a["telefon"],
            "website": a["siteUrl"],
            "permit_url": None,
            "bbox": a["bbox"],
            "adrese": [],
            "water_count": a["ape"],
            "flags": [],
        }
        assoc_proc.append(proc_entry)

    # --- 5. Record the Romsilva source ---
    sources = [json.loads(l) for l in SOURCES.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not any(s.get("source_name") == "anpa_romsilva" for s in sources):
        sources.append({
            "id": "anpa-romsilva-2013-07",
            "source_name": "anpa_romsilva",
            "raw_file_path": "data/raw/anpa_probe/Lista-habitate-Romsilva.txt",
            "raw_file_url": None,
            "source_date": "2013-07",
            "ingested_at": "2026-08-12T00:00:00Z",
            "record_count": 289,
            "schema_version": "1.0.0",
        })

    print(f"[fix] Bâsca Mare (basca-mare): D.S. Buzău sector [{SPLIT_FRAC}, 1] — 45 Km")
    print(f"[fix] Bâsca Mare (basca-mare-covasna): D.S. Covasna sector [0, {SPLIT_FRAC}) — 18 Km")
    print(f"[fix] Bâsca Mică (basca-mica): D.S. Buzău — 68 Km (whole mapped course)")
    print(f"[fix] associations.json: {len(assoc_fe)} entries (+{sum(1 for a in NEW_ASSOC if a['slug'] not in existing_slugs)})")

    if args.write:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        ASSOC_FE.write_text(json.dumps(assoc_fe, ensure_ascii=False, indent=1), encoding="utf-8")
        ASSOC_PROC.write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in assoc_proc), encoding="utf-8")
        SOURCES.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in sources), encoding="utf-8")
        print(f"[write] waters.json: {len(waters)} waters | associations.json: {len(assoc_fe)}")


if __name__ == "__main__":
    main()
