#!/usr/bin/env python3
"""Parse the ANPA Romsilva mountain-waters list into processed data.

Source: data/raw/anpa_probe/Lista-habitate-Romsilva.txt (official ANPA
document — "Lista habitatelor piscicole naturale din apele de munte rămase
în administrarea directă a Regiei Naționale a Pădurilor - ROMSILVA",
ANEXA 1, Iulie 2013). Covers rivers and lakes in mountain waters administered
directly by RNP-Romsilva via Protocol 12935/LAV/17.09.2013 (successor of
Protocol 10711/19.04.2010), grouped by Direcția Silvică (county).

Output: data/processed/anpa_romsilva_waters.jsonl — one JSON record per
habitat (river sector or lake), with the same schema shape as
anpa_waters.jsonl so downstream merge scripts can consume it uniformly.

Usage: python3 scripts/parse_anpa_romsilva.py [--write]
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "anpa_probe" / "Lista-habitate-Romsilva.txt"
OUT = ROOT / "data" / "processed" / "anpa_romsilva_waters.jsonl"

DS_HEADER_RE = re.compile(r"^\s*DIRECȚIA SILVICĂ\s+(.+?)\s*$")
SECTION_RE = re.compile(r"^\s*(I+)\.\s*(RÂURI|LACURI)\s*$")
# Row: nr. name limits km [gestionar...] — name/limits separated by 2+ spaces,
# limits ends with a standalone number (km or ha), then 2+ spaces + gestionar.
ROW_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s{2,}(\d+(?:[.,]\d+)?)\s{2,}(.*)$")
NEGATIVE_CACHE_RE = re.compile(r"Nu au rămas|nu au rămas")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def split_name_limits(col: str):
    """Split the 'name + limits' column at the first run of 2+ spaces."""
    m = re.split(r"\s{2,}", col.strip(), maxsplit=1)
    name = m[0].strip()
    limits = m[1].strip() if len(m) > 1 else ""
    return name, limits


def split_gestionar(rest: str):
    """rest = 'D.S. X   [AJVPS]   rămâne în gestiunea RNP' (columns variable).
    Returns (ds, ajvps, cleaned_rest, obs) — cleaned_rest has the trailing
    observation text removed so callers can treat it as an O.S. name."""
    rest = rest.strip()
    obs = ""
    m = re.search(r"(rămâne în gestiunea RNP)", rest)
    if m:
        obs = m.group(1)
        rest = rest[: m.start()].strip()
    ds = ""
    ajvps = ""
    # D.S. column (may contain spaces, e.g. 'D.S. CS - Severin')
    mds = re.search(r"(D\s*\.\s*S\.?[\w\s\.\-–]*)", rest)
    if mds:
        ds = re.sub(r"\s{2,}", " ", mds.group(1)).strip()
        rest = rest.replace(mds.group(1), " ", 1)
    rest = re.sub(r"\s{2,}", " ", rest).strip()
    if re.search(r"(A\.?J\.?V?\.?P\.?S\.?|A\.?P\.?S\.?)", rest):
        ajvps = rest
    return ds, ajvps, rest, obs


COUNTY_MAP = {
    "alba": "ALBA", "arad": "ARAD", "arges": "ARGEȘ", "bacau": "BACĂU",
    "bihor": "BIHOR", "bistrita": "BISTRIȚA-NĂSĂUD", "brasov": "BRAȘOV",
    "buzau": "BUZĂU", "caras severin": "CARAȘ-SEVERIN", "cs severin": "CARAȘ-SEVERIN",
    "cluj": "CLUJ", "covasna": "COVASNA", "dambovita": "DÂMBOVIȚA",
    "gorj": "GORJ", "harghita": "HARGHITA", "hunedoara": "HUNEDOARA",
    "maramures": "MARAMUREȘ", "mehedinti": "MEHEDINȚI", "mures": "MUREȘ",
    "neamt": "NEAMȚ", "prahova": "PRAHOVA", "salaj": "SĂLAJ", "sibiu": "SIBIU",
    "suceava": "SUCEAVA", "timis": "TIMIȘ", "valcea": "VÂLCEA", "vrancea": "VRANCEA",
}


def county_from_name(name: str) -> str:
    """Map a D.S./section name ('D.S. CS-Severin', 'CARAȘ - SEVERIN', 'Timiș')
    to a canonical county string. Best effort; falls back to the raw name."""
    if not name:
        return ""
    n = norm(name.replace(".", " ").replace("-", " "))
    n = re.sub(r"^d s ", "", n).strip()
    n = re.sub(r"\s+", " ", n).strip()
    for key, county in COUNTY_MAP.items():
        if key in n:
            return county
    return name.strip().upper()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    lines = SRC.read_text(encoding="utf-8").splitlines()
    records = []
    skipped = []
    ds_current = ""
    section = ""
    for ln, line in enumerate(lines, 1):
        if NEGATIVE_CACHE_RE.search(line):
            continue
        m = DS_HEADER_RE.match(line)
        if m:
            ds_current = re.sub(r"\s{2,}", " ", m.group(1)).strip()
            continue
        m = SECTION_RE.match(line)
        if m:
            section = "lac" if "LACURI" in m.group(2) else "rau"
            continue
        m = ROW_RE.match(line)
        if not m:
            # skip headers/preamble/page numbers/empty
            if line.strip() and not line.strip().isdigit() and len(line.strip()) > 2:
                # only flag if it looks like a data row that failed
                if re.match(r"^\s*\d+\s+\S", line):
                    skipped.append((ln, line.strip()[:80]))
            continue
        nr, name_limits, size_str, rest = m.groups()
        # The column-legend line (" 0                 1 ... 6") parses like a row
        # with name '1' and rest '3 4 5 6' — skip digit-only names.
        if re.fullmatch(r"[\d\s]+", name_limits.strip()):
            continue
        name, limits = split_name_limits(name_limits)
        if not name:
            skipped.append((ln, line.strip()[:80]))
            continue
        ds_g, ajvps_g, rest_clean, obs = split_gestionar(rest)
        size = float(size_str.replace(",", "."))
        unit = "ha" if section == "lac" else "km"
        if ds_g:
            gestionar = ds_g
            admin = "romsilva"
            assoc_name = f"ROMSILVA – {ds_current}" if ds_current else "ROMSILVA"
        elif ajvps_g:
            gestionar = ajvps_g
            admin = "ajvps"
            assoc_name = ajvps_g
        else:
            # Bare O.S. name in the Gestionar column (e.g. 'Gîrda', 'Cugir') —
            # an Ocol Silvic subunit of Romsilva.
            gestionar = rest_clean
            admin = "romsilva"
            assoc_name = f"ROMSILVA – {ds_current}" if ds_current else "ROMSILVA"
        county = county_from_name(ds_g) or county_from_name(ds_current)
        rec = {
            "id": f"anpa-romsilva-{ln:04d}",
            "source": "anpa_romsilva",
            "file": SRC.name,
            "source_row": ln,
            "county": county,
            "association": assoc_name,
            "water_name": name,
            "name_normalized": norm(name),
            "water_type": section,
            "limits_text": limits,
            "sector_km": size if unit == "km" else None,
            "sector_ha": size if unit == "ha" else None,
            "sector_unit": unit,
            "sector_raw": f"{size_str} {'Km' if unit=='km' else 'Ha'}",
            "contract_number": None,
            "contract_date": None,
            "act_aditional": None,
            "is_contracted": False,
            "admin": admin,
            "gestionar_ds": ds_g,
            "gestionar_assoc": ajvps_g if admin == "ajvps" else "",
            "gestionar_ocol": gestionar if (admin == "romsilva" and not ds_g) else ("" if admin == "ajvps" else ds_g),
            "obs": obs,
            "directia_silvica": ds_current,
            "flags": [] if (ds_g or admin == "ajvps") else ["gestionar_ocol"],
        }
        records.append(rec)

    # Bâsca rows sanity check
    basca = [r for r in records if "basca" in r["name_normalized"]]
    print(f"[parse] {len(records)} records, {len(basca)} Bâsca-related:")
    for r in basca:
        print(f"  {r['water_name']!r} | {r['limits_text']!r} | {r['sector_raw']} | {r['association']} | {r['county']}")
    print(f"[parse] skipped {len(skipped)} odd lines:")
    for ln, text in skipped[:20]:
        print(f"  L{ln}: {text}")

    if args.write:
        with OUT.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[write] {OUT} — {len(records)} records")


if __name__ == "__main__":
    main()
