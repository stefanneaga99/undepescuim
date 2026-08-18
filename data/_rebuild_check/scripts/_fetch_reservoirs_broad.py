#!/usr/bin/env python3
"""Single broad Overpass query for ALL named reservoirs + lakes we need."""
import json, re, time, urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

# base names (last token of each needed reservoir/lake), deduped
bases = [
    "Arcești", "Drăgănești", "Frunzaru", "Rusănești", "Slatina", "Băbeni",
    "Cornetu", "Câineni", "Lotrului", "Ionești", "Robești", "Vlădești",
    "Sălățig", "Topolovăț", "Lățunaș", "Pojorâta", "Căpâlna", "Petrești",
    "Neag", "Ostrov", "Subcetate", "Pangrati", "Reconstrucția", "Negreni",
    "Cerbureni", "Argeș", "Pitești", "Zigoneni", "Galbeni", "Gârleni",
    "Lilieci", "Agrement", "Ghilin", "Chișineu-Criș", "Copilul", "Mișca",
    "Pâncota", "Zădăreni", "Căpâlnaș", "Cilieni", "Cefa", "Culișer",
    "Huțani", "Volovăț", "Vorona", "Holod", "Tărcăița", "Buduresei",
    "Ierului", "Omului", "Șoimului", "Lesuntu", "Ilvei", "Potop", "Jilț",
    "Grotului", "Râmești", "Lonei", "Vadului", "Sabasa", "Pietrosu",
    "Ivanul", "Cuiejdel", "Măgurii", "Anieș", "Dopca", "Jelna", "Bumbului",
    "Făerag",
]

# fetch ways+relations whose name CONTAINS any of these tokens (regex, i flag)
alt = "|".join(re.escape(b) for b in bases)
QUERY = f"""
[out:json][timeout:300];
(
  way["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
  relation["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
);
out body;
>;
out skel qt;
"""

last_err = None
for url in OVERPASS_URLS:
    for attempt in range(5):
        try:
            print(f"querying {url} (attempt {attempt+1})...", flush=True)
            req = urllib.request.Request(url, data=QUERY.encode(),
                                         headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=400) as resp:
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
            time.sleep(20)
print(f"[FAIL] {last_err}")
