#!/usr/bin/env python3
"""Map Romsilva-administered mountain rivers (task t_1f8b1b06).

The ANPA "Lista habitatelor piscicole naturale din apele de munte rămase în
administrarea directă a RNP - Romsilva" (Protocol 12935/LAV/17.09.2013,
ANEXA 1) lists 289 mountain waters administered by RNP-Romsilva through its
Direcții Silvice. These are real fishing waters (ANPA permit + Romsilva
zonal permit), so they must be visible + clickable on the map with the right
Direcția Silvică association — exactly like the Bâsca Mare/Mică fix
(t_67d8a9a3) did.

What this script does:
1. Loads all 289 Romsilva rows (data/processed/anpa_romsilva_waters.jsonl).
2. For every row MISSING from public/data/waters.json (by name+county),
   creates a water entry with the Direcția Silvică association and an OSM
   geometry when a course can be matched (reuses the conservative matcher
   from audit_missing_rivers.py + curated overrides).
3. Groups multi-sector rivers (Vișeul superior/mijlociu/inferior, Barcăul,
   Neagra, Sadu, Latorița, Putna, Ruscova, ...) under one riverGroup with
   ONE geometry owner and rank-based course_frac on the sector copies, so a
   click on the shared course resolves to the right sector.
4. Adds missing Direcția Silvică associations to the FE + processed
   registries.

Usage: python3 scripts/map_romsilva_rivers.py [--write] [--json-report PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
PROC_ASSOC = ROOT / "data" / "processed" / "arebaltapeste_associations.jsonl"
ROMSILVA_FILE = ROOT / "data" / "processed" / "anpa_romsilva_waters.jsonl"
SOURCES = ROOT / "data" / "processed" / "sources.jsonl"

sys.path.insert(0, str(ROOT / "scripts"))
from _mapping_common import canonical_county  # noqa: E402
from audit_missing_rivers import (  # noqa: E402
    best_osm_match,
    build_county_centroids,
    core,
    load_osm_index,
    make_cluster_geoms,
    norm,
    try_manual_override,
)

REFERINTA = (
    "Administrat de RNP-Romsilva – ape de munte în administrare directă "
    "(Protocol 12935/LAV/17.09.2013, ANEXA 1 – Lista habitatelor piscicole "
    "naturale din apele de munte)"
)

# Multi-sector Romsilva rivers: the row list splits one course into several
# contracts (superior/mijlociu/inferior). These get grouped under one
# riverGroup; geometry is attached to ONE member, the rest resolve by click.
# Group key = core slug of the plain river name.
MULTI_SECTOR = {
    "vișeul", "ruscova", "barcăul", "barcau", "neagra", "sadu", "latorița",
    "putna", "gurghiul", "bistrița", "tarcău", "mureş", "mures", "bega",
    "zăbala", "cerna", "strei", "latorita", "somesul", "nirajul", "moldovița",
}

# Words that mark a SECTOR of a longer river (same as audit_missing_rivers).
SECTOR_WORDS = {"superior", "superioara", "mijlociu", "mijlocie", "inferior",
                "inferioara", "montan", "montana", "mare", "mica", "mic", "nou",
                "noua", "vechi", "veche", "i", "ii", "iii", "iv", "v", "vi",
                "vii", "viii", "a", "b", "c", "de", "cu", "si", "sau", "ale",
                "afluentii", "afluenti", "superioare", "inferioare", "mijlocii",
                "marele", "micul", "curs", "principal", "obarsia", "izvoare",
                "izvoarele", "tronson", "i", "ii"}

SECTOR_RANK = {"superior": 0, "superioara": 0, "mijlociu": 1, "mijlocie": 1,
               "inferior": 2, "inferioara": 2}

COUNTY_TITLE = {
    "BISTRIȚA-NĂSĂUD": "Bistrița-Năsăud", "BISTRIȚA - NĂSĂUD": "Bistrița-Năsăud",
    "CARAȘ-SEVERIN": "Caraș-Severin", "DÂMBOVIȚA": "Dâmbovița",
    "MARAMUREȘ": "Maramureș", "MEHEDINȚI": "Mehedinți", "MUREȘ": "Mureș",
    "NEAMȚ": "Neamț", "SĂLAJ": "Sălaj", "SUCEAVA": "Suceava", "TIMIȘ": "Timiș",
    "VÂLCEA": "Vâlcea", "VRANCEA": "Vrancea", "ARGES": "Argeș",
    "ARGEȘ": "Argeș", "BACĂU": "Bacău", "BRAȘOV": "Brașov", "BIHOR": "Bihor",
    "BUZĂU": "Buzău", "CLUJ": "Cluj", "COVASNA": "Covasna", "GORJ": "Gorj",
    "HARGHITA": "Harghita", "HUNEDOARA": "Hunedoara", "ALBA": "Alba",
    "ARAD": "Arad", "PRAHOVA": "Prahova", "SIBIU": "Sibiu",
}


def county_title(c: str) -> str:
    return COUNTY_TITLE.get(c.strip().upper(), canonical_county(c))


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s


def ds_slug(county: str) -> str:
    """Direcția Silvică association slug for a county.

    Special case: Cluj's existing registry entry is 'd-s--cluj' (D.S. Cluj).
    """
    if county_title(county) == "Cluj":
        return "d-s--cluj"
    return "directia-silvica-" + slugify(county_title(county))


def ds_name(county: str) -> str:
    return "Direcția Silvică " + county_title(county)


def sector_rank_of(name: str) -> int:
    low = name.lower()
    for word, rank in SECTOR_RANK.items():
        if word in low:
            return rank
    return 3


def is_sector_name(name: str) -> bool:
    return sector_rank_of(name) < 3


def load_romsilva() -> list[dict]:
    return [json.loads(l) for l in ROMSILVA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]


def existing_coverage(waters: list[dict]) -> tuple[set[tuple[str, str]], dict[str, list[dict]]]:
    """(core-name + county normalized) coverage set + name -> [waters] index.

    Matching on CORE (prefix-stripped) name so a Romsilva row 'Bâsca Mare'
    correctly matches the existing water 'Râul Bâsca Mare' (added by
    t_67d8a9a3) instead of creating a duplicate.
    """
    covered = set()
    by_norm: dict[str, list[dict]] = defaultdict(list)
    for w in waters:
        key = (core(w.get("name", "")), norm(county_title(w.get("judet", ""))))
        covered.add(key)
        by_norm[norm(w.get("name", ""))].append(w)
    return covered, by_norm


def find_group_key(name: str, waters: list[dict], by_norm: dict) -> str | None:
    """Existing riverGroup for a river name, or None.

    Used to join Romsilva sectors onto the ANPA group of the same river
    (e.g. Romsilva 'Putna Superioara' joins the group of the existing
    ANPA 'Râul Putna').
    """
    c = core(name)
    for w in by_norm.get(c, []):
        if w.get("riverGroup"):
            return w["riverGroup"]
    # also try the sector-stripped core: 'Putna Superioara' -> 'putna'
    c_tokens = c.split()
    stripped = " ".join(t for t in c_tokens if t not in SECTOR_WORDS)
    if stripped and stripped != c:
        for w in by_norm.get(stripped, []):
            if w.get("riverGroup"):
                return w["riverGroup"]
    return None


def group_key_for(name: str) -> str:
    """Shared riverGroup for a Romsilva river name.

    Multi-sector rivers ('Vișeul superior/mijlociu/inferior', 'Barcăul
    Superior/Mijlociu/Inferior') must share ONE group so a click on the
    shared course resolves to the right sector. The group key is the core
    name with sector words stripped AND the definite-article suffix removed
    ('barcaul' -> 'barcau'), so it also aligns with the ANPA water
    ('Râul Barcău' -> 'barcau').
    """
    c = core(name)
    tokens = [t for t in c.split() if t not in SECTOR_WORDS]
    base = " ".join(tokens) if tokens else c
    # strip definite article on the first token: 'barcaul' -> 'barcau',
    # 'viseul' -> 'viseu'
    parts = base.split()
    t0 = parts[0]
    if len(t0) >= 5 and t0.endswith("ul"):
        parts[0] = t0[:-2]
    elif len(t0) >= 5 and t0.endswith("l") and t0[-2] in "aeiou":
        parts[0] = t0[:-1]
    return slugify(" ".join(parts))


def build_new_assocs(rows: list[dict]) -> dict[str, dict]:
    """Direcția Silvică associations needed by the rows (missing from FE)."""
    fe = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    existing = {a["slug"] for a in fe}
    needed: dict[str, dict] = {}
    for r in rows:
        ct = county_title(r.get("county", ""))
        slug = ds_slug(ct)
        if slug in existing or slug in needed:
            continue
        needed[slug] = {
            "slug": slug,
            "name": ds_name(ct),
            "name_long": f"{ds_name(ct)} – Regia Națională a Pădurilor Romsilva",
            "type": "ds",
            "ape": 0,
            "adresa": None,
            "telefon": None,
            "siteUrl": f"https://{slugify(ct)}.rosilva.ro/",
            "permitIssuer": "romsilva",
            "bbox": None,
            "id": f"anpa-romsilva-ds-{slugify(ct)}",
        }
    return needed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json-report", type=str)
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    covered, by_norm = existing_coverage(waters)
    rows = load_romsilva()
    print(f"[romsilva] {len(rows)} rows, {len(waters)} existing waters")

    # OSM index
    print("[osm] loading index...")
    name_index, geoms = load_osm_index()
    osm_geo_by_norm = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_geo_by_norm[n] = gs
    county_centroids = build_county_centroids(waters)
    print(f"[osm] {len(osm_geo_by_norm)} named clusters")

    todo = [r for r in rows
            if (core(r.get("water_name", "")), norm(county_title(r.get("county", "")))) not in covered]
    print(f"[map] {len(todo)} Romsilva rows missing from waters.json")

    new_waters: list[dict] = []
    matched, unmatched = [], []

    for r in todo:
        ct = county_title(r.get("county", ""))
        wtype = r.get("water_type", "rau")
        raw_name = r.get("water_name", "")
        # Display name: rivers get the 'Râul ' prefix for consistency with the
        # ANPA entries; lakes keep their source name.
        if wtype == "rau" and not re.match(r"^(raul|rau|paraul|parau|valea|lacul)\b", raw_name.lower()):
            display = "Râul " + raw_name
        else:
            display = raw_name
        display = display.strip()

        entry = {
            "slug": f"romsilva-{slugify(ct)}-{slugify(raw_name)}",
            "name": display,
            "judet": ct,
            "type": "ape",
            "subtype": wtype,
            "limite": (r.get("limits_text") or "").strip(),
            "dimensiune": f"{r.get('sector_km'):g} Km" if isinstance(r.get("sector_km"), (int, float)) else (r.get("sector_raw") or ""),
            "pescuit_interzis": False,
            "referinta": REFERINTA + f"; O.S. {r.get('gestionar_ocol') or '—'}",
            "coordinates": None,
            "driving": None,
            "bbox": None,
            "asociatie": {
                "name": ds_name(ct),
                "name_long": f"{ds_name(ct)} – Regia Națională a Pădurilor Romsilva",
                "slug": ds_slug(ct),
                "permitIssuer": "romsilva",
            },
            "source": "anpa_romsilva",
            "source_detail": "romsilva_map",
        }

        # geometry match
        best, geom, score, how = best_osm_match(entry, osm_geo_by_norm, county_centroids)
        if not best:
            best, geom, score, how = try_manual_override(entry, osm_geo_by_norm, county_centroids)
        if best and geom:
            entry["geometry"] = geom
            entry["source_detail"] = f"romsilva_map:{how}"
            matched.append((ct, raw_name, best, round(score, 2), how))
        else:
            unmatched.append((ct, raw_name))

        new_waters.append(entry)

    print(f"[map] geometry matched: {len(matched)}/{len(todo)}")
    print(f"[map] no OSM match: {len(unmatched)}")

    # ---- grouping: one geometry owner per riverGroup, sectors get frac ----
    # group new waters by group key (existing group or core name)
    group_members: dict[str, list[dict]] = defaultdict(list)
    for w in new_waters:
        gk = find_group_key(w["name"], waters, by_norm) or w.get("riverGroup")
        if not gk:
            gk = group_key_for(w["name"]) if is_sector_name(w["name"]) else None
        if not gk:
            c = core(w["name"])
            gk = slugify(c) if c else w["slug"]
        w["riverGroup"] = gk
        group_members[gk].append(w)

    for gk, members in group_members.items():
        with_geom = [m for m in members if m.get("geometry")]
        if len(with_geom) <= 1:
            continue
        # multiple members matched geometry on the same course — keep only the
        # MAIN course member (lowest sector rank; plain names first), strip the rest
        with_geom.sort(key=lambda m: (sector_rank_of(m["name"]), len(m["name"])))
        owner = with_geom[0]
        for m in with_geom[1:]:
            m["geometry"] = None
            m["source_detail"] = "romsilva_map:group-shares-course"
        # assign course_frac by sector rank for all members
        ranked = sorted(members, key=lambda m: sector_rank_of(m["name"]))
        n = len(ranked)
        for i, m in enumerate(ranked):
            m["course_frac"] = round((i + 1) / (n + 1), 4)

    # ---- merge into waters.json ----
    existing_slugs = {w["slug"] for w in waters}
    # dedupe slugs among the new waters themselves (the Romsilva list contains
    # duplicate rows: Tăria Mare ×2, Bâlea ×2, Râușor ×2, Firiza ×2 ...)
    used = set(existing_slugs)
    added = 0
    for w in new_waters:
        base = w["slug"]
        slug = base
        i = 2
        while slug in used:
            slug = f"{base}-{i}"
            i += 1
        w["slug"] = slug
        used.add(slug)
        if base in existing_slugs:
            continue  # was already mapped by a previous run
        waters.append(w)
        added += 1

    # ---- associations ----
    new_assocs = build_new_assocs(todo)
    fe_assoc = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    fe_slugs = {a["slug"] for a in fe_assoc}
    for a in new_assocs.values():
        if a["slug"] not in fe_slugs:
            fe_assoc.append({k: a.get(k) for k in ("slug", "name", "name_long", "ape", "adresa", "telefon", "siteUrl", "permitUrl", "permitIssuer", "bbox", "id")})
            fe_slugs.add(a["slug"])

    proc_assoc = [json.loads(l) for l in PROC_ASSOC.read_text(encoding="utf-8").splitlines() if l.strip()]
    proc_slugs = {a["slug"] for a in proc_assoc}
    for a in new_assocs.values():
        if a["slug"] in proc_slugs:
            continue
        proc_assoc.append({
            "id": a["id"], "source": "anpa_romsilva", "file": "Lista-habitate-Romsilva.txt",
            "source_row": None, "name": a["name"], "name_long": a["name_long"],
            "name_normalized": a["slug"].replace("-", " "), "type": "ds",
            "slug": a["slug"], "address": a["adresa"], "phone": a["telefon"],
            "website": a["siteUrl"], "permit_url": a.get("permit_url") or None,
            "permit_issuer": "romsilva", "bbox": a["bbox"],
            "adrese": [], "water_count": 0, "flags": [],
        })

    print(f"[write] waters.json: {len(waters)} waters (+{added})")
    print(f"[write] associations.json: {len(fe_assoc)} entries (+{len(new_assocs)})")

    if args.json_report:
        report = {
            "rows_total": len(rows),
            "rows_missing": len(todo),
            "added_waters": added,
            "matched": [{"county": c, "name": n, "osm": o, "score": s, "how": h} for c, n, o, s, h in matched],
            "unmatched": [{"county": c, "name": n} for c, n in unmatched],
            "new_associations": sorted(new_assocs.keys()),
        }
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[report] wrote {args.json_report}")

    if args.write:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        FE_ASSOC.write_text(json.dumps(fe_assoc, ensure_ascii=False, indent=1), encoding="utf-8")
        PROC_ASSOC.write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in proc_assoc), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
