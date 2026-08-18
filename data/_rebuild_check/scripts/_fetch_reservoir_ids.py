#!/usr/bin/env python3
"""Fetch specific reservoir way IDs with geometry."""
import json, time, urllib.request

OVERPASS_URLS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

# way IDs found by the earlier exact-name query
WAY_IDS = [185038875, 183828451, 88342826, 183313632, 88342740, 184713142, 187008935]

# also try named ways for the other reservoirs with a compact regex (contains match)
bases = ["Cornetu", "Câineni", "Ionești", "Robești", "Lotrului", "Vlădești", "Cerbureni",
         "Zigoneni", "Galbeni", "Gârleni", "Lilieci", "Negreni", "Subcetate", "Pangrati",
         "Reconstrucția", "Sălățig", "Topolovăț", "Lățunaș", "Pojorâta", "Căpâlna",
         "Petrești", "Ostrov", "Ivanul", "Cuiejdel", "Pietrosu", "Anieș", "Măgurii",
         "Pitești", "Cilieni", "Pâncota", "Zădăreni", "Ghilin", "Copilul", "Mișca",
         "Chișineu-Criș", "Căpâlnaș", "Agrement", "Bentu"]
alt = "|".join(bases)
QUERY = f"""
[out:json][timeout:180];
(
  way(id:{','.join(str(i) for i in WAY_IDS)});
  way["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
  relation["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
);
out body;
>;
out skel qt;
"""

last_err = None
for url in OVERPASS_URLS:
    for attempt in range(4):
        try:
            print(f"querying {url} (attempt {attempt+1})...", flush=True)
            req = urllib.request.Request(url, data=QUERY.encode(),
                                         headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = resp.read()
            if b"<html" in payload[:512].lower():
                raise RuntimeError("error page")
            data = json.loads(payload)
            els = data.get("elements", [])
            print(f"[ok] {len(els)} elements", flush=True)
            with open("data/raw/overpass_reservoir_fetch.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            print("saved -> data/raw/overpass_reservoir_fetch.json", flush=True)
            raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            last_err = e
            print(f"   [retry] {e}", flush=True)
            time.sleep(15)
print(f"[FAIL] {last_err}")
