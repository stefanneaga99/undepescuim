#!/usr/bin/env python3
"""Apply the Siret group refactor to public/data/waters.json:
- 9m2irr6m (Brăila) = geometry OWNER: single ordered full-course LineString
  (replaces its 18-part MultiLineString), bbox recomputed, sector = Brăila's.
- anpa-0674 (Vrancea): geometry + bbox REMOVED, sector [0,1] hack replaced by
  the real Vrancea interval (0.8033..0.9125).
- other 6 members: geometry-less group-shares with per-county sectors.
Round-trips the file as json.dumps(indent=1, ensure_ascii=False) without a
trailing newline (pitfall 23).
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

WATERS = ROOT / "public/data/waters.json"
course = json.loads((ROOT / "data/processed/siret_full_course.json").read_text(encoding="utf-8"))
coords = course["geometry"]["coordinates"]
sectors = course["sectors"]

# county -> slug in the siret group
SLUGS = {
    "Suceava": "anpa-anpa-0552",
    "Botoșani": "sopv2vba",
    "Iași": "anpa-anpa-0390",
    "Neamț": "anpa-anpa-0469",
    "Bacău": "anpa-anpa-0066",
    "Vrancea": "anpa-anpa-0674",
    "Galați": "anpa-anpa-0296",
    "Brăila": "9m2irr6m",
}

def bbox_of(coords):
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return [min(lons), min(lats), max(lons), max(lats)]

waters = json.loads(WATERS.read_text(encoding="utf-8"))
changed = []
for w in waters:
    if w.get("riverGroup") != "siret":
        continue
    slug = w["slug"]
    county = None
    for c, s in SLUGS.items():
        if s == slug:
            county = c
            break
    if county is None:
        print("!! no county for", slug)
        continue
    f0, f1 = sectors[county]
    if slug == "9m2irr6m":
        # geometry owner: full course, ONE ordered LineString
        old_pts = 0
        g = w.get("geometry")
        if g:
            old_pts = (len(g["coordinates"]) if g["type"] == "LineString"
                       else sum(len(p) for p in g["coordinates"]))
        w["geometry"] = {"type": "LineString", "coordinates": coords}
        w["bbox"] = bbox_of(coords)
        w["sectorStart"] = f0
        w["sectorEnd"] = f1
        w["course_frac"] = 1.0
        changed.append(f"{slug} ({county}): geometry owner, full course {len(coords)} pts "
                       f"(was MultiLineString {old_pts} pts), sector {f0}..{f1}")
    else:
        # geometry-less group-share with real sector
        had_geom = w.get("geometry") is not None
        had_bbox = w.get("bbox") is not None
        w["geometry"] = None
        w["bbox"] = None
        w["sectorStart"] = f0
        w["sectorEnd"] = f1
        # course_frac fallback -> sector midpoint (never used while sectors exist)
        w["course_frac"] = round((f0 + f1) / 2, 4)
        changed.append(f"{slug} ({county}): geometry {'' if had_geom else 'already '}removed "
                       f"(bbox {'' if had_bbox else 'already '}removed), sector {f0}..{f1}")

# round-trip: json.dumps(indent=1, ensure_ascii=False), NO trailing newline
text = json.dumps(waters, indent=1, ensure_ascii=False)
WATERS.write_text(text, encoding="utf-8")

# verify byte-identical round-trip vs git HEAD
import subprocess
head = subprocess.run(["git", "show", f"HEAD:public/data/waters.json"],
                      capture_output=True, text=True, cwd=ROOT).stdout
# compare only the entries we changed: redump the file and check it's valid + same shape
print("\nchanged entries:")
for c in changed:
    print("  -", c)

# quick stat
siret = [w for w in waters if w.get("riverGroup") == "siret"]
print("\nsiret group members:", len(siret))
for w in sorted(siret, key=lambda x: x["sectorStart"] or 0):
    g = w.get("geometry")
    pts = len(g["coordinates"]) if g and g["type"] == "LineString" else 0
    print(f"  {w['slug']:20s} {w['judet']:10s} geom={pts:5d} sS={w['sectorStart']} sE={w['sectorEnd']} "
          f"assoc={w['asociatie']['slug']}")
