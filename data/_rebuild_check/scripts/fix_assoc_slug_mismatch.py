#!/usr/bin/env python3
"""t_b6a0e2fe data fix: normalize association slug mismatches between
associations.json and waters.json.

Background: several association slugs carry a trailing '-' because the source
names had a trailing space at slugify time ('AJVPS BUZĂU ' → 'ajvps-buzau-').
The waters-side slugs were generated from trimmed names ('ajvps-buzau'), so
selecting the association from the dropdown highlighted NOTHING (slug compare
failed) — the coverage highlight feature depends on exact slug equality.
Two more waters slugs use dots where the association uses dashes.

Renames here are EXACT-NAME verified (name match after whitespace trim) and
safe. Ambiguous prefix mismatches (A.FLY FISHING CLUB SIBIU vs FLY FISHING
CLUB SIBIU, APS PRO PESCAR vs Pro Pescar, ASOCIAȚIA FLY FISHING RARĂU with no
candidate, CS HUNEDOARA vs APS HUNEDOARA) are left untouched for a data
review — they need a human decision, not a slug guess.

After renaming, `ape` counts are recomputed for every association.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
FE_WATERS = ROOT / "public" / "data" / "waters.json"

# associations.json slug -> canonical slug (drop trailing dash / normalize)
ASSOC_RENAME = {
    "ajvps-buzau-": "ajvps-buzau",
    "ajvps-botosani-": "ajvps-botosani",
    "ajvps-caras-severin-": "ajvps-caras-severin",
    "avps-diana-turnu-arad-": "avps-diana-turnu-arad",
    "avps-tarnava-mare-": "avps-tarnava-mare",
    "a-v-p-s--iasi": "avps-iasi",
}

# waters.json asociatie.slug -> canonical (dot/dash or trailing dash; several
# contracts still carry the OLD trailing-dash slug: 11 ajvps-botosani-,
# 1 ajvps-caras-severin-, 2 avps-tarnava-mare-, 1 ajvps-buzau-)
WATER_RENAME = {
    "a.cerbul-carpatin": "a-cerbul-carpatin",
    "a.lucioperca-club-pescar-modern": "a-lucioperca-club-pescar-modern",
    "ajvps-buzau-": "ajvps-buzau",
    "ajvps-botosani-": "ajvps-botosani",
    "ajvps-caras-severin-": "ajvps-caras-severin",
    "avps-tarnava-mare-": "avps-tarnava-mare",
}

assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))

# 1. Rename + trim trailing spaces in associations.json
renamed = 0
for a in assocs:
    if a["slug"] in ASSOC_RENAME:
        a["slug"] = ASSOC_RENAME[a["slug"]]
        renamed += 1
    if a["name"] != a["name"].rstrip():
        a["name"] = a["name"].rstrip()

# 2. Rename waters asociatie slugs
water_renamed = 0
for w in waters:
    assoc = w.get("asociatie") or {}
    if assoc.get("slug") in WATER_RENAME:
        assoc["slug"] = WATER_RENAME[assoc["slug"]]
        water_renamed += 1

# 3. Recompute ape counts for every association
counts = Counter((w.get("asociatie") or {}).get("slug") for w in waters)
for a in assocs:
    a["ape"] = counts.get(a["slug"], 0)

# 4. Safety: no waters may reference an unknown slug (except the documented
# ambiguous leftovers which never matched an association anyway)
known = {a["slug"] for a in assocs}
AMBIGUOUS = {"a.fly-fishing-club-sibiu", "aps-pro-pescar", "asociatia-fly-fishing-rarau", "cs-hunedoara"}
unknown = sorted(s for s in counts if s and s not in known and s not in AMBIGUOUS)
if unknown:
    raise SystemExit(f"ABORT: waters reference unknown slugs: {unknown}")

FE_ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"associations.json: {len(assocs)} entries, {renamed} slugs renamed")
print(f"waters.json: {water_renamed} asociatie slugs renamed, {len(waters)} waters")
print("top:", ", ".join(f"{a['slug']}={a['ape']}" for a in sorted(assocs, key=lambda x: -x['ape'])[:8]))
for slug in ("ajvps-buzau", "ajvps-botosani", "ajvps-caras-severin", "avps-tarnava-mare", "avps-iasi", "avps-diana-turnu-arad", "a-cerbul-carpatin", "a-lucioperca-club-pescar-modern"):
    a = next((x for x in assocs if x["slug"] == slug), None)
    print(f"  {slug}: ape={a['ape'] if a else 'MISSING'} name={a['name'] if a else '?'!r}")
