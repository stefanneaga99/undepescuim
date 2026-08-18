#!/usr/bin/env python3
"""Fix the ANPA subtype classification bug (t_242be1eb).

merge_anpa_waters.py mapped `water_type == "river"` → rau and EVERYTHING
else → lac, so 120 ANPA streams (Pârâu/Valea/Izvorul) and ~15 river-ish
'other' rows became subtype 'lac' — invisible in the 'Râuri' filter and
stylable as lakes. This script:

1. Fixes the mapping in scripts/merge_anpa_waters.py (so future merges are
   correct).
2. Rewrites subtype in public/data/waters.json for every ANPA-sourced water
   using the corrected rule.

Corrected rule:
  river  -> rau
  stream -> rau          (Pârâu X / Valea X / Izvorul X are all running waters)
  other  -> rau UNLESS the name is clearly a standing water / fish farm:
            Baraj*, Fondul piscicol*, CCRM*, CCPFB*, CP *stația*, Potcoava*
  lake/accumulation/pond/canal -> lac

Usage: python3 scripts/fix_stream_subtype.py [--write]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"
MERGE_SCRIPT = ROOT / "scripts" / "merge_anpa_waters.py"

OTHER_LAKE_RE = re.compile(
    r"^(?:baraj\s|fondul piscicol|ccrm\s|ccpfb\s|cp\s+\d|potcoava)", re.I
)


def anpa_subtype(w: dict) -> str:
    wt = w.get("water_type")
    if wt == "river" or wt == "stream" or wt == "canal":
        return "rau"
    if wt == "other":
        return "lac" if OTHER_LAKE_RE.match(w.get("water_name", "") or "") else "rau"
    return "lac"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    # 1. fix the merge script mapping
    src = MERGE_SCRIPT.read_text(encoding="utf-8")
    old = '"subtype": "rau" if w.get("water_type") == "river" else "lac",'
    new = '"subtype": anpa_subtype(w),'
    if old not in src:
        print("[!] merge_anpa_waters.py mapping line not found (already patched?)")
    else:
        src = src.replace(old, new)
        # add the helper above main()
        helper = (
            "OTHER_LAKE_RE = re.compile(\n"
            '    r"^(?:baraj\\s|fondul piscicol|ccrm\\s|ccpfb\\s|cp\\s+\\d|potcoava)", re.I\n'
            ")\n\n\n"
            "def anpa_subtype(w: dict) -> str:\n"
            '    wt = w.get("water_type")\n'
            '    if wt in ("river", "stream", "canal"):\n'
            '        return "rau"\n'
            '    if wt == "other":\n'
            '        return "lac" if OTHER_LAKE_RE.match(w.get("water_name", "") or "") else "rau"\n'
            '    return "lac"\n\n\n'
        )
        anchor = "def main() -> None:\n"
        src = src.replace(anchor, helper + anchor, 1)
        if args.write:
            MERGE_SCRIPT.write_text(src, encoding="utf-8")
            print("[merge-script] patched mapping + helper")
        else:
            print("[merge-script] would patch mapping + helper (dry run)")

    # 2. fix existing waters.json rows (by ANPA slug / name match)
    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    anpa = [json.loads(l) for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    anpa_by_id = {w["id"]: w for w in anpa}

    fixed = []
    for x in fe:
        slug = x.get("slug", "")
        if slug.startswith("anpa-"):
            aid = slug[len("anpa-"):]
            aw = anpa_by_id.get(aid)
            if aw:
                want = anpa_subtype(aw)
                if x.get("subtype") != want:
                    fixed.append((x.get("name"), x.get("subtype"), want))
                    if args.write:
                        x["subtype"] = want
    print(f"[waters.json] subtype fix: {len(fixed)} rows would change")
    for name, old_sub, new_sub in sorted(fixed):
        print(f"   {name:55s} {old_sub} -> {new_sub}")

    if args.write:
        FE_WATERS.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[write] waters.json updated")


if __name__ == "__main__":
    main()
