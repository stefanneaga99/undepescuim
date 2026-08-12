#!/usr/bin/env python3
"""Fix remaining multi-contract river groups (follow-up to fix_river_contracts.py, t_ac697770).

The named 10 rivers (olt/mures/siret/prut/somes/crisul-repede/arges/ialomita/
dambovita/jiu) were fixed + verified (51/51 clicks). This pass fixes the REST:

1. Group collisions:
   - Gorj 'Râul Bistrița' (a Jiu tributary, anpa-0309) was grouped with the
     Moldavian Bistrița contracts -> split into 'bistrita-gorj'.
   - 'Râul Bistra Ardealului, mijlociu' (Caraș-Severin) grouped with the Mureș
     'Râul Bistra' -> split into 'bistra-ardealului'.

2. Collapsed course_frac on groups WITH a real full course: geocode the ANPA
   limite places and project on the fullest geometry member:
   - moldova (I-IV all 0.5206) -> anchors Prisaca Dornei / Giumalău / Dobra / Umor
   - tarnava-mare (4 members all 0.147) + ADD missing Mureș/Sibiu contracts
   - colentina (0.0/0.0) -> Buftea / Cernica
   - aries (0.988/1.0) -> Baia de Arieș / Gligorești
   - somesul-mic (0.1836/0.1836) -> Gilău / Dej
   - somesul-mare (0.1836/0.0) -> Feldru / Dej
   - barzava (0.7643/0.7643) + ADD missing Timiș contract -> Breaza / frontieră

3. Fragment-only groups (crisul-alb, crisul-negru, cibin, talna, somesu-rece,
   somesul-cald, malaia, valea-robesti, jijia): the collapsed identical fracs
   made the first sorted contract win EVERY click. Remove them so the frontend
   falls back to name-rank ordering (superior<mijlociu<inferior), which is the
   correct along-course order for these named-sector contracts.
"""
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import geocode_common as gc
from probe_buzau_places import fraction_at

WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def norm_flat(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def geocode_cached(db, query: str):
    row = db.execute(
        "SELECT result_json FROM geocode_cache WHERE query_string = ?", (query,)
    ).fetchone()
    if row is not None:
        if row[0]:
            try:
                data = json.loads(row[0])
                if data:
                    return [float(data[0]["lon"]), float(data[0]["lat"])]
            except Exception:
                pass
        return None
    results = gc.nominatim_search(query, countrycodes="ro")
    if results:
        first = results[0]
        db.execute(
            "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, osm_type, osm_id, geometry_type, bbox, source, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (query, "fix_remaining", "rau", json.dumps(results, ensure_ascii=False),
             first.get("osm_type"), str(first.get("osm_id")),
             first.get("geojson", {}).get("type") if isinstance(first.get("geojson"), dict) else None,
             json.dumps(first.get("boundingbox")), "nominatim", "medium"),
        )
        db.commit()
        return [float(first["lon"]), float(first["lat"])]
    db.execute(
        "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, source) VALUES (?,?,?,NULL,?)",
        (query, "fix_remaining", "rau", "nominatim_negative"),
    )
    db.commit()
    return None


def geocode_any(db, queries):
    for q in queries:
        if not q:
            continue
        pt = geocode_cached(db, q)
        if pt:
            return pt, q
    return None, None


def full_course(w):
    g = w.get("geometry")
    if not g:
        return None
    if g["type"] == "MultiLineString":
        return g["coordinates"]
    if g["type"] == "LineString":
        return [g["coordinates"]]
    return None


def npts(g):
    if not g:
        return 0
    if g["type"] == "MultiLineString":
        return sum(len(p) for p in g["coordinates"])
    if g["type"] == "LineString":
        return len(g["coordinates"])
    return 0


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    by_slug = {w["slug"]: w for w in waters}
    anpa = {json.loads(l)["id"]: json.loads(l)
            for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
    db = gc.get_db()

    # ------------------------------------------------------------------
    # 1. Split collided groups + add missing group members
    # ------------------------------------------------------------------
    print("== group collisions ==")
    for slug, name, judet, newg in [
        ("ey1b2yfy", "Râul Bistrița", "Gorj", "bistrita-gorj"),
        ("anpa-anpa-0226", "Râul Bistra Ardealului, mijlociu", "Caraș-Severin", "bistra-ardealului"),
        ("ks2vsbaf", "Râul Târnava Mare", "Alba", "tarnava-mare"),  # Alba contract joins the group
    ]:
        w = by_slug.get(slug)
        if w and w.get("riverGroup") != newg:
            w["riverGroup"] = newg
            print(f"  {slug} {name} [{judet}] -> {newg}")
    # Târnava Mică: Alba contract must NOT share the Târnava Mare group (it
    # already has no riverGroup; ensure it stays out by giving it its own)
    hj = by_slug.get("hj594dti")
    if hj and hj.get("riverGroup") is None:
        hj["riverGroup"] = "tarnava-mica"
        print(f"  hj594dti Râul Târnava Mică [Alba] -> tarnava-mica")

    # ------------------------------------------------------------------
    # 2. Anchored fracs for full-course groups
    # ------------------------------------------------------------------
    # (group, owner_slug, [(slug|'ANPA:id', anchor_queries...)])
    ANCHORED = [
        ("moldova", "anpa-anpa-0391", [
            ("anpa-anpa-0566", ["Giumalău, Suceava, România", "Câmpulung Moldovenesc, România"]),  # I (source sector)
            ("anpa-anpa-0567", ["Câmpulung Moldovenesc, România", "Gura Humorului, Suceava, România"]),  # II (Giumalău-Hurghiș)
            ("anpa-anpa-0565", ["Prisaca Dornei, Suceava, România", "Câmpulung Moldovenesc, România"]),  # III
            ("anpa-anpa-0568", ["Dobra, Suceava, România", "Frasin, Suceava, România"]),  # IV (Dobra-Umor)
            ("anpa-anpa-0391", ["Miroslovești, Iași, România", "Pașcani, Iași, România"]),  # Iași (lower)
        ]),
        ("colentina", "djkvkzv6", [
            ("f553avch", ["Vlădeni, Dâmbovița, România", "Ciocănești, Dâmbovița, România"]),  # Dâmbovița (upper, source)
            ("djkvkzv6", ["Cernica, Ilfov, România", "București, România"]),  # Ilfov (lower)
        ]),
        ("aries", "qtebe8c3", [
            ("qtebe8c3", ["Baia de Arieș, Alba, România", "Câmpeni, Alba, România"]),  # Alba (upper)
            ("9h06oubr", ["Gligorești, Cluj, România", "Turda, Cluj, România"]),  # Cluj (lower)
        ]),
        ("somesul-mic", "b3r64r3x", [
            ("b3r64r3x", ["Gilău, Cluj, România", "Someșul Rece, Cluj, România"]),  # upper (Gilău-V. Orman)
            ("hao8h0b2", ["Dej, Cluj, România", "Apahida, Cluj, România"]),  # lower (V. Orman-Dej)
        ]),
        ("somesul-mare", "wv8ykggg", [
            ("a2qs9hkg", ["Feldru, Bistrița-Năsăud, România", "Ciceu Mihăiești, Bistrița-Năsăud, România"]),  # BN (upper)
            ("wv8ykggg", ["Dej, Cluj, România", "Beclean, Bistrița-Năsăud, România"]),  # Cluj (lower)
        ]),
        ("barzava", "wmx33tho", [
            ("anpa-anpa-0220", ["Breaza, Caraș-Severin, România", "Anina, Caraș-Severin, România"]),  # inferioară (upper: Breaza-Secu)
            ("wmx33tho", ["Bocșa, Caraș-Severin, România", "Gătaia, Timiș, România"]),  # AP BANATUL (middle: Secu-border)
        ]),
        ("tarnava-mare", "ks2vsbaf", [
            ("anpa-anpa-0332", ["Zetea, Harghita, România", "Odorheiu Secuiesc, Harghita, România"]),  # superior
            ("anpa-anpa-0333", ["Desag, Harghita, România", "Zetea, Harghita, România"]),  # mijlocie (pod Desag, Harghita)
            ("anpa-anpa-0334", ["Odorheiu Secuiesc, Harghita, România", "Cristuru Secuiesc, Harghita, România"]),  # inferior
            ("anpa-anpa-0326", ["Brădești, Harghita, România", "Cristuru Secuiesc, Harghita, România"]),  # Târnava Mare
            ("ks2vsbaf", ["Blaj, Alba, România", "Mediaș, Sibiu, România"]),  # Alba (lower)
        ]),
    ]

    print("\n== anchored fracs ==")
    for group, owner_slug, pairs in ANCHORED:
        owner = by_slug.get(owner_slug)
        parts = full_course(owner) if owner else None
        if not parts:
            print(f"  [skip] {group}: no owner geometry ({owner_slug})")
            continue
        # strip duplicate geometries from non-owner members (share the course)
        members = [w for w in waters if w.get("riverGroup") == group]
        for m in members:
            if m["slug"] != owner_slug and m.get("geometry"):
                m.pop("geometry", None)
                m.pop("bbox", None)
        for slug, queries in pairs:
            if slug.startswith("ANPA:"):
                continue
            w = by_slug.get(slug)
            if not w:
                print(f"  [warn] {group}/{slug}: missing water")
                continue
            pt, used = geocode_any(db, queries)
            if not pt:
                print(f"  [warn] {group}/{w['name']}: NO geocode for {queries[0]!r}")
                continue
            frac, dist = fraction_at(parts, pt)
            if frac is None:
                print(f"  [warn] {group}/{w['name']}: fraction failed")
                continue
            w["course_frac"] = round(frac, 4)
            print(f"  {group:14} {w['name'][:36]:38} ({pt[0]:.4f},{pt[1]:.4f}) -> frac {frac:.4f} [via {used}]")

    # ------------------------------------------------------------------
    # 2b. Add missing Târnava Mare (Mureș, Sibiu) + Bârzava (Timiș) contracts
    # ------------------------------------------------------------------
    print("\n== missing contracts ==")
    MISSING = [
        # (anpa id, group, owner_slug, anchor queries)
        ("anpa-0454", "tarnava-mare", "ks2vsbaf", ["Daneș, Mureș, România", "Sângeorgiu de Pădure, Mureș, România"]),  # AJVPS MUREȘ
        ("anpa-0521", "tarnava-mare", "ks2vsbaf", ["Dumbrăveni, Sibiu, România", "Mediaș, Sibiu, România"]),  # AJVPS SIBIU
        ("anpa-0585", "barzava", "wmx33tho", ["Jamu Mare, Timiș, România", "Deta, Timiș, România"]),  # AJVPS TIMIȘ (frontieră)
    ]
    for anpa_id, group, owner_slug, queries in MISSING:
        slug = f"anpa-anpa-{anpa_id.replace('anpa-', '')}"
        if slug in by_slug:
            print(f"  [skip] {slug} already exists")
            continue
        row = anpa[anpa_id]
        assoc = (row.get("association") or "").strip()
        owner = by_slug.get(owner_slug)
        parts = full_course(owner) if owner else None
        frac = None
        pt, used = None, None
        if parts:
            pt, used = geocode_any(db, queries)
            if pt:
                f, _d = fraction_at(parts, pt)
                if f is not None:
                    frac = round(f, 4)
        entry = {
            "slug": slug,
            "name": row["water_name"],
            "judet": row["county"].title(),
            "type": "ape",
            "subtype": "rau" if row.get("water_type") == "river" else "lac",
            "limite": row.get("limits_text") or "",
            "dimensiune": row.get("sector_raw") or "",
            "pescuit_interzis": False,
            "referinta": f"Contract {row.get('contract_number')} ({row.get('contract_date')})",
            "coordinates": None,
            "driving": None,
            "bbox": None,
            "asociatie": {"name": assoc, "slug": norm(assoc).replace(" ", "-")},
            "geometry": None,
            "riverGroup": group,
        }
        if frac is not None:
            entry["course_frac"] = frac
        waters.append(entry)
        by_slug[slug] = entry
        print(f"  + {slug:16} {entry['name'][:40]:42} [{entry['judet']}] {assoc} frac={frac} [via {used}]")

    # ------------------------------------------------------------------
    # 3. Fragment-only groups: drop collapsed fracs -> name-rank fallback
    # ------------------------------------------------------------------
    print("\n== drop collapsed fracs (fragment groups) ==")
    # These groups have NO full course in the data (tiny fragments only, or no
    # geometry at all). Their course_frac values are stale county-seat
    # projections that collapse every member to one point. Dropping them lets
    # the frontend fall back to name-rank ordering (superior<mijlociu<inferior),
    # which IS the correct along-course order for these named-sector contracts.
    FRAGMENT_GROUPS = ["crisul-alb", "crisul-negru", "cibin", "talna", "somesu-rece",
                       "somesul-cald", "malaia", "valea-robesti", "jijia",
                       "budacul", "colibita", "doamnei", "geoagiu", "iza",
                       "izvorul", "lotru", "negru", "prahova", "sadu",
                       "salauta", "steiul", "streiul", "targului", "teleajen",
                       "tur", "uzul", "zabala", "somesul-mic-dup"]
    dropped = 0
    for w in waters:
        g = w.get("riverGroup")
        if g in FRAGMENT_GROUPS and w.get("course_frac") is not None:
            w.pop("course_frac", None)
            dropped += 1
    print(f"  dropped course_frac from {dropped} fragment-group members")

    # ------------------------------------------------------------------
    # 4. Jijia: keep fracs (they differ) — nothing to do
    # ------------------------------------------------------------------
    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[done] {len(waters)} waters written")


if __name__ == "__main__":
    main()
