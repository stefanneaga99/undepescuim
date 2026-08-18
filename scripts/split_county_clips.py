#!/usr/bin/env python3
"""P0 §4.2 — split geometryByCounty OUT of waters.json / uncontracted_rivers.json
into a single lazy-loaded county-clip file (plan §4.2, §4.2b).

The per-county clips (3.48 MB compact / 0.65 MB gzip contract + 587
uncontracted) are used ONLY when the county filter is active. Shipping them
inside waters.json blocks first paint for a feature the user may never touch.

Output: public/data/waters_county_clips.json  = { <slug>: <countyKey->geojson|null map> }
  - every contract slug with clips (from waters.json)
  - every uncontracted slug with clips (from uncontracted_rivers.json)
Both source files are re-written WITHOUT geometryByCounty (compact).

The FE (map-store.ts loadCountyClips) fetches this file on the FIRST county
activation (idempotent) and merges w.geometryByCounty = clips[w.slug] for each
water in the matching pool (waters / uncontracted).

Build order (pipeline): ... -> build_county_clip_geoms.py (or any clip producer)
-> split_county_clips.py -> simplify_waters_geometry.py -> rebuild_data.py
--manifest.

Usage: .venv/bin/python3 scripts/split_county_clips.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public/data/waters.json"
UNC_RIVERS = ROOT / "public/data/uncontracted_rivers.json"
UNC_LAKES = ROOT / "public/data/uncontracted_lakes.json"
CLIPS = ROOT / "public/data/waters_county_clips.json"


def compact(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def extract(pool: list, out: dict) -> int:
    n = 0
    for w in pool:
        gbc = w.get("geometryByCounty")
        if gbc:
            out[w["slug"]] = gbc
            n += 1
        w.pop("geometryByCounty", None)
    return n


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    clips: dict = {}
    n_water = extract(waters, clips)

    unc_rivers = None
    unc_lakes = None
    n_unc = 0
    if UNC_RIVERS.exists():
        unc_rivers = json.loads(UNC_RIVERS.read_text(encoding="utf-8"))
        n_unc += extract(unc_rivers, clips)
    if UNC_LAKES.exists():
        unc_lakes = json.loads(UNC_LAKES.read_text(encoding="utf-8"))
        for w in unc_lakes:
            w.pop("geometryByCounty", None)

    CLIPS.write_text(compact(clips), encoding="utf-8")
    WATERS.write_text(compact(waters), encoding="utf-8")
    if unc_rivers is not None:
        UNC_RIVERS.write_text(compact(unc_rivers), encoding="utf-8")
    if unc_lakes is not None:
        UNC_LAKES.write_text(compact(unc_lakes), encoding="utf-8")

    print(f"split_county_clips: {n_water} contracted + {n_unc} uncontracted -> {CLIPS.name}")


if __name__ == "__main__":
    main()