#!/usr/bin/env python3
"""Add per-association `counties` and default `reciprocity` to associations.json (F2a).

F2a permit validity statement (docs/f2a-permit-validity.md §4, step 1):
- `counties`: sorted distinct judet values of the waters whose contracts reference
  the association slug (association → waters → counties), computed from
  public/data/waters.json. Display-ready, diacritics preserved.
- `reciprocity`: constant "neconfirmată" — research (plan §2) found NO public
  per-pair reciprocity registry, so every association defaults to neconfirmată
  until manually curated via public/data/reciprocity.json.

Idempotent: re-running rewrites the same values. Does NOT touch `ape` (that's
scripts/recompute_assoc_counts.py's job).
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"

waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))

counties = defaultdict(set)
for w in waters:
    a = w.get("asociatie") or {}
    if a.get("slug"):
        counties[a["slug"]].add(w["judet"])

for a in assocs:
    a["counties"] = sorted(counties.get(a["slug"], ()))
    a["reciprocity"] = "neconfirmată"  # constant until curated (§2)

FE_ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"associations.json: {len(assocs)} entries, counties + reciprocity added")
multi = [a["slug"] for a in assocs if len(a["counties"]) > 1]
print("multi-county:", ", ".join(f"{s}={len([x for x in assocs if x['slug']==s][0]['counties'])}" for s in multi) or "none")
empty = [a["slug"] for a in assocs if not a["counties"]]
print(f"empty-county ({len(empty)}):", ", ".join(empty))
