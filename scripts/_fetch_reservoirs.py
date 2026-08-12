#!/usr/bin/env python3
"""Fetch missing reservoir/lake polygons via Overpass — precise name matches with retries."""
import json, re, time, unicodedata, urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

# Reservoir/lake names we still need polygons for (full names, exact-ish)
NAMES = [
    "Acumularea Arcești", "Acumularea Drăgănești", "Acumularea Frunzaru",
    "Acumularea Rusănești", "Acumularea Slatina", "Acumularea Băbeni",
    "Acumularea Cornetu", "Acumularea Câineni", "Acumularea Gura Lotrului",
    "Acumularea Ionești", "Acumularea Robești", "Lacul Vlădești",
    "Acumularea Sălățig", "Lacul Topolovăț", "Lacul de acumulare Lățunaș",
    "Lacul Pojorâta", "Acumularea Căpâlna", "Acumularea Petrești",
    "Lacul Câmpu lui Neag", "Lacul Ostrov", "Lacul Subcetate",
    "Lacul Pangrati", "Lac Reconstrucția", "Lacul Negreni",
    "Lacul Bentu Mare", "Lacul Bentu lui Cotoi", "Iezerul Pietrosu",
    "Lacul Ivanul", "Cuiejdel", "Balta Ghilin", "Lac Chișineu-Criș",
    "Lac Copilul", "Lac Mișca", "Lac Pâncota", "Lac Zădăreni",
    "Balta Căpâlnaș", "Acumulare Cerbureni", "Acumulare Curtea de Argeș",
    "Acumulare Pitești", "Acumulare Zigoneni", "Acumulare Galbeni",
    "Acumulare Gârleni", "Acumulare Lilieci", "Acumulare Agrement",
    "Lacul Izvorul (Măgurii)", "Acumularea Cilieni",
]

def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

# Query elements whose name (normalized, diacritics-stripped) equals one of the
# targets (also strip definite article suffixes), keeping it strict.
norm_names = {norm(n) for n in NAMES}

# Overpass: fetch ways+relations with name containing 'acumulare'/'lacul' near the
# target zones — simpler: fetch by each name exactly, in small batches.
def run_query(query):
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, data=query.encode(),
                                             headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req, timeout=240) as resp:
                    payload = resp.read()
                if b"<html" in payload[:512].lower() or b"rate" in payload[:1024].lower():
                    raise RuntimeError("rate-limited or error page")
                return json.loads(payload)
            except Exception as e:
                last_err = e
                print(f"   [retry] {url}: {e}")
                time.sleep(8)
    raise RuntimeError(f"all endpoints failed: {last_err}")

all_els = []
for name in NAMES:
    # fetch any way/relation whose normalized name matches exactly
    q = f"""
    [out:json][timeout:60];
    (
      way["name"](43.5,20.0,48.5,30.0);
      relation["name"](43.5,20.0,48.5,30.0);
    );
    out body;
    >;
    out skel qt;
    """
    # too big; instead do per-name queries with name~ regex (case-insensitive, diacritic-insensitive)
    base = re.sub(r"^(Acumularea|Acumulare|Lacul|Lac|Balta|Iezerul|Cuiejdel)\s+", "", name)
    base = re.sub(r"\s*\(.*\)$", "", base).strip()
    # build a diacritic-insensitive regex
    def diacritic_re(s):
        out = []
        for ch in s:
            nf = unicodedata.normalize("NFD", ch)
            base_ch = nf[0] if nf else ch
            out.append(f"[{re.escape(base_ch)}{re.escape(nf)}]")
        return "".join(out)
    rx = diacritic_re(base)
    q = f"""
    [out:json][timeout:60];
    (
      way["name"~"{rx}$",i](43.5,20.0,48.5,30.0);
      relation["name"~"{rx}$",i](43.5,20.0,48.5,30.0);
    );
    out body;
    >;
    out skel qt;
    """
    try:
        data = run_query(q)
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        continue
    els = data.get("elements", [])
    # keep only elements whose normalized name matches the target
    keep = []
    for el in els:
        t = el.get("tags", {})
        nm = norm(t.get("name") or "")
        if nm == norm_names and False:
            pass
        if any(nm == nn or nm.startswith(nn) or nn in nm for nn in {norm(base), norm(name)}):
            keep.append(el)
    print(f"[{name}] {len(keep)} matching elements (raw {len(els)})")
    for el in keep[:4]:
        t = el.get("tags", {})
        print(f"   {el['type']} {el['id']} name={t.get('name')!r} nat={t.get('natural')} water={t.get('water')} ww={t.get('waterway')} lu={t.get('landuse')}")
    all_els.extend(keep)
    time.sleep(2)

with open("data/raw/overpass_reservoir_fetch.json", "w", encoding="utf-8") as f:
    json.dump({"elements": all_els}, f, ensure_ascii=False)
print(f"\nTOTAL kept: {len(all_els)} -> data/raw/overpass_reservoir_fetch.json")
