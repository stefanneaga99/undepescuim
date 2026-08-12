#!/usr/bin/env python3
"""Fetch named reservoir ways/relations by exact name (works reliably)."""
import json, re, time, unicodedata, urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

NAMES = [
    "Acumularea Arcești", "Acumularea Drăgănești", "Acumularea Frunzaru",
    "Acumularea Rusănești", "Acumularea Slatina", "Acumularea Băbeni",
    "Acumularea Cornetu", "Acumularea Câineni", "Acumularea Gura Lotrului",
    "Acumularea Ionești", "Acumularea Robești", "Lacul Vlădești",
    "Acumularea Sălățig", "Lacul Topolovăț", "Lacul de acumulare Lățunaș",
    "Lacul Pojorâta", "Acumularea Căpâlna", "Acumularea Petrești",
    "Lacul Câmpu lui Neag", "Lacul Ostrov", "Lacul Subcetate",
    "Lacul Pangrati", "Lac Reconstrucția", "Lacul Negreni",
    "Acumulare Cerbureni", "Acumulare Curtea de Argeș", "Acumulare Pitești",
    "Acumulare Zigoneni", "Acumulare Galbeni", "Acumulare Gârleni",
    "Acumulare Lilieci", "Acumulare Agrement", "Balta Ghilin",
    "Lac Chișineu-Criș", "Lac Copilul", "Lac Mișca", "Lac Pâncota",
    "Lac Zădăreni", "Balta Căpâlnaș", "Acumularea Cilieni",
    "Canalul Cefa IV", "Culișer", "Gârla Huțani", "Râul Volovăț",
    "Râul Vorona", "Râul Holod", "Râul Tărcăița", "Valea Buduresei",
    "Valea Ierului", "Valea Omului", "Valea Șoimului", "Pârâul Lesuntu",
    "Râul Valea Ilvei", "Râul Potop", "Râul Jilț", "Râul Grotului",
    "Râul Râmești", "Valea Lonei", "Valea Vadului", "Râul Sabasa",
    "Iezerul Pietrosu", "Lacul Ivanul", "Cuiejdel", "Lacul Izvorul (Măgurii)",
    "Dopca", "Jelna", "Izvoare", "Lacul Făerag", "Lacul Anieș",
]

def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

def run_query(query):
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, data=query.encode(),
                                             headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    payload = resp.read()
                if b"<html" in payload[:512].lower():
                    raise RuntimeError("error page")
                return json.loads(payload)
            except Exception as e:
                last_err = e
                time.sleep(5)
    print(f"   [WARN] query failed: {last_err}")
    return {"elements": []}

all_els = []
seen = set()
for i, name in enumerate(NAMES):
    q = f"""
    [out:json][timeout:60];
    (
      way["name"="{name}"](43.5,20.0,48.5,30.0);
      relation["name"="{name}"](43.5,20.0,48.5,30.0);
    );
    out body;
    >;
    out skel qt;
    """
    data = run_query(q)
    els = data.get("elements", [])
    keep = []
    for el in els:
        if el["id"] in seen:
            continue
        seen.add(el["id"])
        keep.append(el)
    all_els.extend(keep)
    # print only top-level elements
    tops = [el for el in keep if el["type"] != "node"]
    if tops:
        for el in tops:
            t = el.get("tags", {})
            print(f"[{name}] {el['type']}/{el['id']} nat={t.get('natural')} water={t.get('water')} ww={t.get('waterway')} lu={t.get('landuse')} name={t.get('name')!r}", flush=True)
    if (i + 1) % 5 == 0:
        print(f"... {i+1}/{len(NAMES)} (total {len(all_els)} els)", flush=True)
        time.sleep(2)

with open("data/raw/overpass_reservoir_fetch.json", "w", encoding="utf-8") as f:
    json.dump({"elements": all_els}, f, ensure_ascii=False)
print(f"TOTAL: {len(all_els)} elements -> data/raw/overpass_reservoir_fetch.json")
