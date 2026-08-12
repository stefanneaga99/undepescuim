#!/usr/bin/env python3
"""Targeted Overpass fetch for named reservoirs (any tag), no $ anchor."""
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
    "Dopca", "Jelna", "Izvoare – conf. pârâul Bumbului",
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
                with urllib.request.urlopen(req, timeout=180) as resp:
                    payload = resp.read()
                if b"<html" in payload[:512].lower():
                    raise RuntimeError("error page")
                return json.loads(payload)
            except Exception as e:
                last_err = e
                time.sleep(6)
    raise RuntimeError(f"failed: {last_err}")

# Build one query: all ways/relations named exactly like the targets (normalized
# diacritic-insensitive comparison can't be done in Overpass, so fetch by regex
# of the base name and filter client-side).
bases = sorted({re.sub(r"^(Acumularea|Acumulare|Lacul|Lac|Balta|Iezerul|Râul|Valea|Pârâul|Canalul|Gârla|Cuiejdel|Dopca|Jelna)\s+", "", n) for n in NAMES})
bases = [b for b in bases if len(b) >= 4]
alt = "|".join(re.escape(b) for b in bases)
QUERY = f"""
[out:json][timeout:240];
(
  way["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
  relation["name"~"({' + alt + r'})",i](43.5,20.0,48.5,30.0);
);
out body;
>;
out skel qt;
"""
print(f"querying {len(bases)} base names...", flush=True)
data = run_query(QUERY)
els = data.get("elements", [])
print(f"raw elements: {len(els)}", flush=True)

# client-side filter: normalized name equals one of the target norm forms
norm_targets = {norm(n) for n in NAMES}
def strip_pref(n):
    n = norm(n)
    return re.sub(r"^(acumularea|acumulare|lacul|lac|balta|iezerul|raul|valea|paraul|canalul|garla)\s+", "", n)

keep = []
for el in els:
    t = el.get("tags", {})
    nm = norm(t.get("name") or "")
    if not nm:
        continue
    sp = strip_pref(nm)
    for tn in norm_targets:
        tbase = strip_pref(tn)
        if nm == tn or sp == tbase or (len(tbase) >= 6 and tbase in nm):
            keep.append(el)
            break
print(f"kept: {len(keep)}", flush=True)
for el in keep[:60]:
    t = el.get("tags", {})
    print(f"   {el['type']} {el['id']} name={t.get('name')!r} nat={t.get('natural')} water={t.get('water')} ww={t.get('waterway')} lu={t.get('landuse')}")

with open("data/raw/overpass_reservoir_fetch.json", "w", encoding="utf-8") as f:
    json.dump({"elements": keep}, f, ensure_ascii=False)
print("saved -> data/raw/overpass_reservoir_fetch.json")
