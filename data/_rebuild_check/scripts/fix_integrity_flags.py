#!/usr/bin/env python3
"""t_45a0beae — align data with the approved data-correctness plan after the
Layer-5 integrity audit flagged residual issues:

1. species.json: the 3 protected species that carried an annexed min_cm
   (Caracudă 17, Lipan 25, Coregon 22) now carry min_cm: null per plan §3.5
   guard ("protected species carry min_cm: null + retention: interzis"). The
   annexed dimension is preserved in seasonal_notes (never lost, never shown
   as a number — the /specii page keys on retention).
2. associations.json: directia-silvica-harghita carried a malformed 11-digit
   phone (02660313222 — Romanian landlines are 0+9); removed as unusable
   rather than guessing a real number.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
ASSOC = ROOT / "public" / "data" / "associations.json"

PROTECTED_WITH_SIZE = {
    "Caracudă": 17,
    "Lipan": 25,
    "Coregon": 22,
}


def main() -> None:
    species = json.loads(SPECIES.read_text(encoding="utf-8"))
    for s in species:
        if s["species"] in PROTECTED_WITH_SIZE and s.get("min_cm") is not None:
            cm = s["min_cm"]
            s["min_cm"] = None
            note = s.get("seasonal_notes") or ""
            if "Dimensiunea din anexă" not in note and "dimensiune" not in note.lower():
                note = (note + " " if note else "") + \
                    f"Dimensiunea din anexă ({cm} cm) rămâne în vigoare, dar reținerea este interzisă tot anul."
            s["seasonal_notes"] = note
            print(f"[fix] {s['species']}: min_cm {cm} -> null (retention interzis), note kept")
    SPECIES.write_text(json.dumps(species, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    assocs = json.loads(ASSOC.read_text(encoding="utf-8"))
    for a in assocs:
        if a.get("slug") == "directia-silvica-harghita" and (a.get("telefon") or "").strip():
            removed = a.pop("telefon", None)
            print(f"[fix] {a['slug']}: removed malformed telefon {removed!r} "
                  f"(siteUrl stays: {a.get('siteUrl')})")
    ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()