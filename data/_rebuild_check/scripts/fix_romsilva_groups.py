#!/usr/bin/env python3
"""Fix riverGroup for multi-sector Romsilva rivers (t_1f8b1b06).

The Romsilva list splits one course into several contracts (superior /
mijlociu / inferior). Those entries must share ONE riverGroup so a click on
the shared course resolves to the right sector via course_frac (Voronoi) —
not three overlapping orange lines from three separate groups.

Rules (conservative):
  * Group ONLY entries of the SAME county AND the same stripped base name.
  * Keep ONE geometry owner per group (the lowest sector rank); the other
    members become 'group-shares-course' copies that resolve by click.
  * Join Romsilva sectors onto an EXISTING ANPA group only when the base
    name + county match exactly (e.g. Romsilva Sadu Superior joins the ANPA
    'sadu' group of Râul Sadu in Sibiu; Romsilva Sebeșul Superior joins the
    ANPA 'sebes' group in Alba).
  * NEVER merge across counties (Vâlcea Cerna != Caraș-Severin Cerna,
    Sibiu Bistra != Mureș Bistra, Suceava Putna != Vrancea Putna,
    Harghita Cașin != Bacău Cașinul Superior).

Usage: python3 scripts/fix_romsilva_groups.py [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"

SECTOR_WORDS = {"superior", "superioara", "superioară", "mijlociu",
                "mijlocie", "inferior", "inferioara", "inferioară", "tronson",
                "i", "ii", "iii", "iv", "v"}
SECTOR_RANK = {"superior": 0, "superioara": 0, "superioară": 0,
               "mijlociu": 1, "mijlocie": 1, "inferior": 2, "inferioara": 2,
               "inferioară": 2, "tronson": 3}
ARTICLE_RE = re.compile(r"^(.*?)(ul|le|l)$")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def base_name(name: str) -> str:
    """Stripped base: 'Râul Barcăul Superior' -> 'barcau'."""
    n = norm(name)
    for p in ("raul ", "rau ", "paraul ", "parau ", "valea ", "vale ", "lacul "):
        if n.startswith(p):
            n = n[len(p):]
            break
    tokens = [t for t in n.split() if t not in SECTOR_WORDS]
    base = " ".join(tokens)
    # strip definite article on first token: 'barcaul' -> 'barcau'
    parts = base.split()
    if parts:
        t0 = parts[0]
        m = ARTICLE_RE.match(t0)
        if m and len(m.group(1)) >= 4:
            parts[0] = m.group(1)
    return " ".join(parts)


def sector_rank(name: str) -> int:
    n = norm(name)
    for word, rank in SECTOR_RANK.items():
        if word in n:
            return rank
    return 9


def county_key(judet: str) -> str:
    return norm(judet)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))

    # ---- 1. join Romsilva sectors onto existing ANPA groups (same county) ----
    anpa_by_base: dict[tuple[str, str], str] = {}  # (county, base) -> group
    for w in waters:
        if w.get("source") == "anpa_romsilva":
            continue
        g = w.get("riverGroup")
        if not g:
            continue
        anpa_by_base.setdefault((county_key(w.get("judet", "")), base_name(w["name"])), g)

    # ---- 2. group Romsilva entries by (county, base) ----
    rs_by_base: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for w in waters:
        if w.get("source") != "anpa_romsilva":
            continue
        key = (county_key(w.get("judet", "")), base_name(w["name"]))
        rs_by_base[key].append(w)

    changed = 0
    for (ckey, base), members in sorted(rs_by_base.items()):
        if len(members) < 2:
            # single Romsilva member: still join the matching ANPA group when
            # the SAME river already exists there (e.g. Râul Cașinul Superior
            # Bacău joins the 'casinul' group of Râul Casinul inferior Bacău —
            # same OSM course, upstream sector). Never merge across counties
            # (Vâlcea Cerna != Caraș-Severin Cerna).
            gk = anpa_by_base.get((ckey, base))
            if gk:
                m = members[0]
                m["riverGroup"] = gk
                m["geometry"] = None
                m["source_detail"] = "romsilva_map:group-shares-course"
                # Voronoi position: a sector named superior/mijlociu sits
                # UPSTREAM (lower frac) of the ANPA owner; an inferior sector
                # sits downstream (higher frac).
                low = m["name"].lower()
                owner_frac = None
                for w in waters:
                    if w.get("riverGroup") == gk and w.get("geometry") and w.get("source") != "anpa_romsilva":
                        owner_frac = w.get("course_frac")
                        break
                owner_frac = owner_frac if isinstance(owner_frac, (int, float)) else 0.5
                if "superior" in low or "superioar" in low or "mijlociu" in low or "mijlocie" in low:
                    m["course_frac"] = round(owner_frac / 2, 4)
                elif "inferior" in low or "inferioar" in low:
                    m["course_frac"] = round((owner_frac + 1.0) / 2, 4)
                else:
                    m["course_frac"] = round((owner_frac or 0.5) / 2, 4)
                changed += 1
                print(f"[fix] {base} ({members[0].get('judet')}): single sector joins ANPA group '{gk}' frac={m['course_frac']}")
            continue
        # generic bases ('mare', 'mica', 'mic', 'reau', 'rece', 'vechi') can
        # merge DISTINCT rivers that happen to strip to the same word
        # ('Valea Mare' vs 'Raul Mare' in Alba). Only group when the base is
        # distinctive.
        if base in {"mare", "mica", "mic", "reau", "rece", "vechi", "nou",
                    "noua", "sec", "seaca", "seacă", "mijlociu", "inferior",
                    "superior"} or len(base) < 4:
            print(f"[skip] {base} ({members[0].get('judet')}): generic base, keeping separate")
            continue
        # shared group: existing ANPA group if the base+county matches,
        # else slug of the base
        gk = anpa_by_base.get((ckey, base))
        if not gk:
            gk = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or members[0]["slug"]
        # one geometry owner: lowest sector rank (plain names first)
        members_sorted = sorted(members, key=lambda m: (sector_rank(m["name"]), m["slug"]))
        owner = members_sorted[0]
        n = len(members_sorted)
        anpa_owner_has_geom = any(
            w.get("riverGroup") == gk and w.get("geometry") and w.get("source") != "anpa_romsilva"
            for w in waters
        )
        for i, m in enumerate(members_sorted):
            m["riverGroup"] = gk
            # when an existing ANPA water already draws the course, the
            # Romsilva members only RESOLVE clicks (no duplicate line)
            if m is not owner or anpa_owner_has_geom:
                m["geometry"] = None
                m["source_detail"] = "romsilva_map:group-shares-course"
            m["course_frac"] = round((i + 1) / (n + 1), 4)
            changed += 1
        print(f"[fix] {base} ({members[0].get('judet')}): {n} sectors -> group '{gk}', "
              f"owner {owner['name']}{' (ANPA draws)' if anpa_owner_has_geom else ''}")

    print(f"[fix] updated {changed} riverGroup/course_frac fields")

    if args.write:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
