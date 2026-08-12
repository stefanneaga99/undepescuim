#!/usr/bin/env python3
"""Recompute each association's `ape` count from waters.json (t_66b48ee0).

The FE filter dropdown shows association.ape = number of waters referencing
the association slug; it goes stale whenever waters are added/removed.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"

waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))

counts = Counter((w.get("asociatie") or {}).get("slug") for w in waters)
changed = 0
for a in assocs:
    new = counts.get(a["slug"], 0)
    if a.get("ape") != new:
        a["ape"] = new
        changed += 1

FE_ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"associations.json: {len(assocs)} entries, {changed} ape counts updated")
print("top:", ", ".join(f"{a['slug']}={a['ape']}" for a in sorted(assocs, key=lambda x: -x['ape'])[:8]))
