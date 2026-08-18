#!/usr/bin/env python3
"""P1 §4.5 — build `uncontracted_majors.json` (rivers ≥ 30 km + lakes ≥ 100 ha).

This is exactly the zoom-7 LOD subset the UncontractedWaterLayer already draws
at the default national view (same thresholds as the shared FE LOD module,
src/utils/lod.ts). Shipping it as its own tiny file lets the map's first paint
be "majors-only" (plan §4.5): loadData() awaits associations + waters +
counties + majors, opens the data gate immediately, and streams the full
uncontracted_rivers.json + uncontracted_lakes.json in the background — so the
national view is visually complete on cold load without paying for the whole
9.9k-feature overlay in the critical path.

Thresholds: rivers lengthKm >= 30 km, lakes areaHa >= 100 ha (the zoom < 8
tier of the shared LOD — same constants as src/utils/lod.ts). Majors are a
STRICT SUBSET of the full pools (filter, no re-shaping), so when the full
files land they simply replace the majors in the store with no visual pop.

Usage: .venv/bin/python3 scripts/build_uncontracted_majors.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RIVERS = ROOT / "public/data/uncontracted_rivers.json"
LAKES = ROOT / "public/data/uncontracted_lakes.json"
OUT = ROOT / "public/data/uncontracted_majors.json"

# Same thresholds as src/utils/lod.ts zoom<8 tier. Keep in sync.
MIN_LENGTH_KM = 30.0
MIN_AREA_HA = 100.0


def main() -> None:
    rivers = json.loads(RIVERS.read_text(encoding="utf-8"))
    lakes = json.loads(LAKES.read_text(encoding="utf-8"))
    maj_rivers = [w for w in rivers if (w.get("lengthKm") or 0.0) >= MIN_LENGTH_KM]
    maj_lakes = [w for w in lakes if (w.get("areaHa") or 0.0) >= MIN_AREA_HA]
    out = maj_rivers + maj_lakes
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[majors] rivers >= {MIN_LENGTH_KM:.0f} km = {len(maj_rivers)}  "
          f"lakes >= {MIN_AREA_HA:.0f} ha = {len(maj_lakes)}  total = {len(out)}")
    print(f"[write] {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
