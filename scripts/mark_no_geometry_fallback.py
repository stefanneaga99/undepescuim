#!/usr/bin/env python3
"""t_45a0beae / A5 — explicit fallback markers for undocumented no-geometry waters.

Baseline: 166 waters in waters.json have no geometry / coordinates / bbox.
  - 139 carry a `riverGroup` (the documented "one geometry owner per group,
    sector copies stay geometry-free" pattern — already a documented
    fallback; the integrity gate treats riverGroup as such).
  - 27 have NEITHER geometry nor riverGroup. Investigated against the OSM
    bulk index (data/rivers_osm.geojson): no reliable exact-name matches —
    the near-misses (valisoara, paraul stegii, paraul racova, iazul morilor)
    are ambiguous same-name streams in other counties, and the wrong-county
    fuzzy-attach class is exactly what t_a0e123da fixed. The 27 are mostly
    canals / japșa / unnamed hydromelioration works with no map feature.

Resolution (plan §7): mark them `"fallback": "no_geometry"` — an explicit,
documented gap that the integrity gate accepts as a deliberate fallback (not
a silent hole). Any future geometry comes from the geocoding pipeline only.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"


def main() -> None:
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    marked = 0
    for w in waters:
        has_space = bool(w.get("geometry") or w.get("coordinates") or w.get("bbox"))
        if has_space or w.get("riverGroup") or w.get("fallback"):
            continue
        w["fallback"] = "no_geometry"
        marked += 1
        print(f"  {w['slug']} | {w['name'][:45]} | {w.get('judet')}")

    FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(1 for w in waters if not (w.get("geometry") or w.get("coordinates") or w.get("bbox")))
    grouped = sum(1 for w in waters if not (w.get("geometry") or w.get("coordinates") or w.get("bbox")) and w.get("riverGroup"))
    print(f"[a5] marked {marked} waters with fallback=no_geometry; "
          f"{total} total no-space waters ({grouped} riverGroup-documented + {total - grouped} fallback-documented)")


if __name__ == "__main__":
    main()