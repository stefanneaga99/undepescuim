#!/usr/bin/env python3
"""Test a single Overpass query for Acumularea Arcești."""
import json, urllib.request

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)"}

for test_name in ["Acumularea Arcești", "Arcești"]:
    QUERY = f"""
    [out:json][timeout:60];
    (
      way["name"="{test_name}"](43.5,20.0,48.5,30.0);
      relation["name"="{test_name}"](43.5,20.0,48.5,30.0);
    );
    out body;
    >;
    out skel qt;
    """
    print(f"=== query name={test_name} ===")
    for url in OVERPASS_URLS:
        try:
            req = urllib.request.Request(url, data=QUERY.encode(), headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read()
            data = json.loads(payload)
            els = data.get("elements", [])
            print(f"[{url}] {len(els)} elements")
            for el in els[:5]:
                t = el.get("tags", {})
                print(f"   {el['type']} {el['id']} name={t.get('name')} natural={t.get('natural')} water={t.get('water')} ww={t.get('waterway')}")
            if els:
                with open("data/raw/overpass_test.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            break
        except Exception as e:
            print(f"[warn] {url} failed: {e}")
