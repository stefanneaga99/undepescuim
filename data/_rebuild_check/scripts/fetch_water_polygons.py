#!/usr/bin/env python3
"""Fetch ALL water-body polygons (named + unnamed) for the Romania bbox from
Overpass — ways/relations with natural=water, water=*, landuse=reservoir or
natural=wetland, plus recursed member ways/nodes (t_51e028c4).

Saves data/raw/overpass_water_polys.json (full Overpass JSON).
"""
import json
import time
import urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

# ways + relations: natural=water, water=*, landuse=reservoir, natural=wetland.
# Include unnamed (the 0.5 ha size threshold is applied at build time).
QUERY = """
[out:json][timeout:600];
(
  way["natural"="water"](43.5,20.0,48.5,30.0);
  way["water"](43.5,20.0,48.5,30.0);
  way["landuse"="reservoir"](43.5,20.0,48.5,30.0);
  way["natural"="wetland"](43.5,20.0,48.5,30.0);
  relation["natural"="water"](43.5,20.0,48.5,30.0);
  relation["water"](43.5,20.0,48.5,30.0);
  relation["landuse"="reservoir"](43.5,20.0,48.5,30.0);
  relation["natural"="wetland"](43.5,20.0,48.5,30.0);
);
out body;
>;
out skel qt;
"""

OUT = "data/raw/overpass_water_polys.json"


def run():
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(4):
            try:
                req = urllib.request.Request(
                    url, data=QUERY.encode(),
                    headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
                )
                with urllib.request.urlopen(req, timeout=560) as resp:
                    payload = resp.read()
                if b"<html" in payload[:512].lower():
                    raise RuntimeError("error page")
                data = json.loads(payload)
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"[ok] {url}: {len(data.get('elements', []))} elements, "
                      f"{len(payload)/1e6:.1f} MB -> {OUT}", flush=True)
                return 0
            except Exception as e:
                last_err = e
                print(f"   [retry {attempt}] {url}: {e}", flush=True)
                time.sleep(15)
    print(f"[FAIL] {last_err}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
