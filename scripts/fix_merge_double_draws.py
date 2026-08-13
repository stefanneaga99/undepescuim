#!/usr/bin/env python3
"""Merge-task cleanup (t_1b7c95a7): collapse identical-geometry double-draws
deferred by the geometry batches.

- lotru: rw5qqi3t (Râul Lotru mijlociu) and teziodii (Râul Lotrul Inferior)
  both held the SAME full 1939-pt course -> course drew twice. Keep rw5qqi3t
  as the geometry owner (it already carries sectorStart/End for its contract),
  strip teziodii's geometry (keeps bbox + sector interval so the FE slices its
  reach from the group course).
- doamnei: 5pomav1f (inferior) and d5xhbhta (Superior) held the SAME full
  2824-pt course. Keep 5pomav1f as owner, strip d5xhbhta's geometry. Click
  resolution stays Voronoi over course_frac (Superior rank 0 / mijlociu 0.25 /
  inferior rank 2) — no behavior change, just one draw instead of two.

NOT touched (documented instead):
- sadu: ug8h7f1s river course + gff3cbfy headwater lake polygon = correct
  coexistence (FE exempts lake polygons from slicing, pitfall #51).
- romsilva-bihor-dragan: pre-existing subtype=lac holding a river course;
  needs human review (200 ha artificial lake vs 24-part course).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "public" / "data" / "waters.json"

STRIP = {
    "teziodii": ("lotru", "rw5qqi3t"),
    "d5xhbhta": ("doamnei", "5pomav1f"),
}

def main():
    text = FE.read_text(encoding="utf-8")
    waters = json.loads(text)
    by_slug = {w["slug"]: w for w in waters}
    changed = []
    for strip_slug, (group, owner_slug) in STRIP.items():
        w = by_slug[strip_slug]
        owner = by_slug[owner_slug]
        assert w.get("riverGroup") == group, (strip_slug, w.get("riverGroup"))
        assert owner.get("riverGroup") == group
        assert w.get("geometry") and owner.get("geometry")
        assert w["geometry"] == owner["geometry"], f"{strip_slug} != {owner_slug} geometry"
        if w.get("geometry") is not None:
            w["geometry"] = None
            changed.append(strip_slug)
    if not changed:
        print("nothing changed")
        return
    out = json.dumps(waters, indent=1, ensure_ascii=False)
    FE.write_text(out, encoding="utf-8")
    print("stripped duplicate geometry from:", changed)

if __name__ == "__main__":
    main()
