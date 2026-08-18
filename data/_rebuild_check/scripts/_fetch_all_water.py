#!/usr/bin/env python3
"""Fetch all named lake/reservoir-ish elements in one Overpass query (background job)."""
import json, re, urllib.request, time

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

# query natural=water / water=* / landuse=reservoir + named 'Acumularea/Lacul/...'
QUERY = """
[out:json][timeout:300];
(
  way["natural"="water"](43.5,20.0,48.5,30.0);
  way["water"](43.5,20.0,48.5,30.0);
  way["landuse"="reservoir"](43.5,20.0,48.5,30.0);
  way["waterway"="river"](43.5,20.0,48.5,30.0);
  relation["natural"="water"](43.5,20.0,48.5,30.0);
  relation["water"](43.5,20.0,48.5,30.0);
  relation["landuse"="reservoir"](43.5,20.0,48.5,30.0);
);
out body;
>;
out skel qt;
"""

def run():
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, data=QUERY.encode(),
                                             headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req, timeout=400) as resp:
                    payload = resp.read()
                if b"<html" in payload[:512].lower():
                    raise RuntimeError("error page")
                data = json.loads(payload)
                out = "data/raw/overpass_water_all.json"
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"[ok] {url}: {len(data.get('elements', []))} elements -> {out}", flush=True)
                return 0
            except Exception as e:
                last_err = e
                print(f"   [retry {attempt}] {url}: {e}", flush=True)
                time.sleep(10)
    print(f"[FAIL] {last_err}", flush=True)
    return 1

if __name__ == "__main__":
    raise SystemExit(run())
