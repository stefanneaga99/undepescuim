#!/usr/bin/env python3
"""Fetch county boundary polygons from Nominatim for the 8 Siret counties.
Query pattern: '<County>, România' -> admin relation with polygon_geojson.
Caches to data/raw/county_boundaries/<slug>.json (list[0] = result dict)."""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

COUNTIES = ["Suceava", "Botoșani", "Iași", "Neamț", "Bacău", "Galați", "Vrancea", "Brăila"]
OUT = ROOT / "data/raw/county_boundaries"
OUT.mkdir(parents=True, exist_ok=True)

def fetch(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": q, "format": "jsonv2", "polygon_geojson": 1, "limit": 5,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "undepescuim-fix/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

for c in COUNTIES:
    slug = c.lower().replace("ș", "s").replace("ț", "t").replace("ă", "a").replace("î", "i").replace("â", "a")
    out = OUT / f"{slug}.json"
    if out.exists():
        print(f"{c}: cached")
        continue
    results = fetch(f"{c}, România")
    # prefer county-level admin relation: place_rank <= 12 (county ~8), and
    # display_name that is NOT 'Zona Metropolitană' (city metro) and has few parts.
    best = None
    for r in results:
        if not (r.get("type") == "administrative" and r.get("osm_type") == "relation"):
            continue
        if not (r.get("geojson") and r["geojson"]["type"] in ("Polygon", "MultiPolygon")):
            continue
        dn = r.get("display_name", "")
        if "Zona Metropolitană" in dn:
            continue
        if r.get("place_rank", 99) > 12:
            continue
        best = r
        break
    if best is None and results:
        best = results[0]
    if best is None:
        print(f"{c}: NO RESULT")
        continue
    out.write_text(json.dumps([best], ensure_ascii=False), encoding="utf-8")
    g = best["geojson"]
    n = sum(len(r) for r in g["coordinates"]) if g["type"] == "Polygon" else sum(len(p[0]) for p in g["coordinates"])
    print(f"{c}: osm_id={best.get('osm_id')} place_rank={best.get('place_rank')} type={g['type']} "
          f"name={best.get('display_name','')[:60]} pts={n}")
    time.sleep(1.2)
