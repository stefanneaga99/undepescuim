#!/usr/bin/env python3
"""Fetch ALL Romanian county boundary polygons from Nominatim.

Query pattern: '<County>, România' -> admin relation with polygon_geojson.
Caches to data/raw/county_boundaries/<slug>.json (list[0] = result dict).
Used by build_uncontracted_rivers.py for point-in-polygon county assignment
(centroids are unreliable for border counties — see t_471dad64).
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COUNTIES = [
    "Alba", "Arad", "Argeș", "Bacău", "Bihor", "Bistrița-Năsăud", "Botoșani",
    "Brașov", "Brăila", "Buzău", "Caraș-Severin", "Călărași", "Cluj",
    "Constanța", "Covasna", "Dâmbovița", "Dolj", "Galați", "Giurgiu", "Gorj",
    "Harghita", "Hunedoara", "Ialomița", "Iași", "Ilfov", "Maramureș",
    "Mehedinți", "Mureș", "Neamț", "Olt", "Prahova", "Satu Mare", "Sălaj",
    "Sibiu", "Suceava", "Teleorman", "Timiș", "Tulcea", "Vaslui", "Vâlcea",
    "Vrancea", "București",
]
OUT = ROOT / "data/raw/county_boundaries"
OUT.mkdir(parents=True, exist_ok=True)


def slugify(name: str) -> str:
    return name.lower().replace("ș", "s").replace("ț", "t").replace("ă", "a") \
        .replace("î", "i").replace("â", "a").replace("-", "_")


def fetch(q: str) -> list[dict]:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": q, "format": "jsonv2", "polygon_geojson": 1, "limit": 5,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "undepescuim-fix/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


missing = []
for c in COUNTIES:
    out = OUT / f"{slugify(c)}.json"
    if out.exists():
        print(f"{c}: cached", flush=True)
        continue
    results = fetch(f"{c}, România")
    best = None
    for r in results:
        if not (r.get("type") == "administrative" and r.get("osm_type") == "relation"):
            continue
        if not (r.get("geojson") and r["geojson"]["type"] in ("Polygon", "MultiPolygon")):
            continue
        dn = r.get("display_name", "")
        if "Zona Metropolitană" in dn or "Municipiul" in dn and "București" not in dn:
            continue
        if r.get("place_rank", 99) > 12:
            continue
        best = r
        break
    if best is None and results:
        best = results[0]
    if best is None:
        print(f"{c}: NO RESULT", flush=True)
        missing.append(c)
        continue
    out.write_text(json.dumps([best], ensure_ascii=False), encoding="utf-8")
    g = best["geojson"]
    n = sum(len(r) for r in g["coordinates"]) if g["type"] == "Polygon" \
        else sum(len(p[0]) for p in g["coordinates"])
    print(f"{c}: osm_id={best.get('osm_id')} rank={best.get('place_rank')} "
          f"type={g['type']} pts={n}", flush=True)
    time.sleep(1.2)

print("MISSING:", missing or "none", flush=True)
