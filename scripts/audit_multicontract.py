#!/usr/bin/env python3
"""Audit inventory: replicate the frontend waterKey/sameRiver grouping and
list every multi-contract river group (2+ members), with course_frac values
and geometry ownership. Mirrors WaterFeatureLayer.tsx logic exactly."""
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
waters = json.loads((ROOT / "public" / "data" / "waters.json").read_text(encoding="utf-8"))


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def water_key(name: str) -> str:
    lower = strip_accents((name or "").lower())
    for p in ("raul ", "paraul ", "parau ", "valea ", "lacul ", "balta ", "acumularea ", "acumulare "):
        if lower.startswith(p):
            lower = lower[len(p):]
            break
    return lower.replace("(", "").replace(")", "").strip().split()[0] if lower.strip() else ""


def same_river(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a[:5] == b[:5]


def is_main_course(name: str) -> bool:
    return not __import__("re").match(r"^(valea|paraul|parau|pârâu|pârâul)\s", (name or ""), __import__("re").I)


# Build groups using the same filter as contractAtFraction
groups: dict[str, list] = {}
for w in waters:
    if not is_main_course(w.get("name", "")) and w.get("mainCourse") is not True:
        continue
    k = water_key(w.get("name", ""))
    if not k:
        continue
    # attach to any existing group whose key sameRiver matches
    matched = next((g for g in groups if same_river(g, k)), None)
    if matched is None:
        matched = k
    groups.setdefault(matched, []).append(w)

print(f"{'GROUP KEY':12} {'#':>2}  contracts (slug | name | judet | assoc | frac | geom-pts)")
print("-" * 120)
multi = sorted([(k, v) for k, v in groups.items() if len(v) >= 2], key=lambda kv: kv[0])
for k, members in multi:
    print(f"{k:12} {len(members):2}  ")
    for w in sorted(members, key=lambda x: (x.get("course_frac") is None, x.get("course_frac") or 0)):
        g = w.get("geometry")
        npts = 0
        if g:
            if g["type"] == "MultiLineString":
                npts = sum(len(p) for p in g["coordinates"])
            elif g["type"] == "LineString":
                npts = len(g["coordinates"])
            elif g["type"] in ("Polygon", "MultiPolygon"):
                coords = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
                npts = len(coords)
        frac = w.get("course_frac")
        frac_s = f"{frac:.4f}" if isinstance(frac, (int, float)) else "None "
        assoc = (w.get("asociatie") or {}).get("name", "?")
        print(f"    {w['slug']:16} {w.get('name','')[:36]:38} [{w.get('judet',''):10}] {assoc:18} frac={frac_s} geom={npts}")

print()
print("Total multi-contract groups:", len(multi))
