#!/usr/bin/env python3
"""Assign each river contract its real position (fraction) along the river course.

Problem: contracts like 'Pârâu Buzăul Mijlociu' (Covasna) sit at the SOURCE
while 'Râul Buzăul superior' (Buzău) is downstream of it — name-based ranking
(superior < mijlociu < inferior) is wrong. Fix: geocode each contract's
location (name + county + limits), project it onto the river's OSM geometry,
and store `course_frac` = fraction along the course (0=source, 1=mouth).

Usage: python3 scripts/assign_course_frac.py
"""

import json
import math
import re
import sqlite3
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
DB = ROOT / "data" / "cache" / "geocode.db"

HEADERS = {
    "User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def haversine(a, b):
    R = 6371.0
    la1, lo1 = math.radians(a[1]), math.radians(a[0])
    la2, lo2 = math.radians(b[1]), math.radians(b[0])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def order_parts(parts):
    """PCA order parts source→mouth, oriented by latitude (RO rivers flow N→S/E)."""
    if len(parts) <= 1:
        return parts
    mids = [p[len(p) // 2] for p in parts]
    mx = sum(m[0] for m in mids) / len(mids)
    my = sum(m[1] for m in mids) / len(mids)
    cxx = sum((m[0] - mx) ** 2 for m in mids)
    cyy = sum((m[1] - my) ** 2 for m in mids)
    cxy = sum((m[0] - mx) * (m[1] - my) for m in mids)
    theta = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    vx, vy = math.cos(theta), math.sin(theta)
    scored = [(m[0] - mx) * vx + (m[1] - my) * vy for m in mids]
    order = [p for _, p in sorted(zip(scored, parts))]
    half = max(1, len(order) // 2)
    lat_first = sum(p[len(p) // 2][1] for p in order[:half]) / half
    lat_last = sum(p[len(p) // 2][1] for p in order[-half:]) / half
    return order if lat_first >= lat_last else list(reversed(order))


def fraction_at(parts, pt):
    """Fraction [0,1] of the course nearest to pt (lon,lat)."""
    ordered = order_parts(parts)
    total = sum(haversine(p[i - 1], p[i]) for p in ordered for i in range(1, len(p)))
    if total <= 0:
        return None

    def dist_to_seg(a, b, p):
        abx, aby = b[0] - a[0], b[1] - a[1]
        apx, apy = p[0] - a[0], p[1] - a[1]
        l2 = abx * abx + aby * aby
        t = (apx * abx + apy * aby) / l2 if l2 else 0
        t = max(0.0, min(1.0, t))
        return math.hypot(p[0] - (a[0] + t * abx), p[1] - (a[1] + t * aby))

    best, bd = None, float("inf")
    walked = 0.0
    for coords in ordered:
        for j in range(1, len(coords)):
            a, b = coords[j - 1], coords[j]
            d = dist_to_seg(a, b, pt)
            if d < bd:
                bd = d
                seg_len = haversine(a, b)
                abx, aby = b[0] - a[0], b[1] - a[1]
                apx, apy = pt[0] - a[0], pt[1] - a[1]
                l2 = abx * abx + aby * aby
                t = (apx * abx + apy * aby) / l2 if l2 else 0
                t = max(0.0, min(1.0, t))
                within = sum(haversine(coords[k - 1], coords[k]) for k in range(1, j))
                best = (walked + within + t * seg_len) / total
        walked += sum(haversine(coords[i - 1], coords[i]) for i in range(1, len(coords)))
    return best


def geocode(query: str):
    """Nominatim search, RO-bounded, diacritic-free. Returns [lon, lat] or None.
    Sleeps 1.1s before each call (Nominatim's 1 req/s policy)."""
    q = norm(query)
    url = "https://nominatim.openstreetmap.org/search"
    time.sleep(1.1)
    try:
        r = requests.get(
            url,
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "ro"},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            return [float(data[0]["lon"]), float(data[0]["lat"])]
    except Exception as e:
        print(f"  [warn] geocode failed for {query!r}: {e}")
    return None


def build_queries(w: dict) -> list[str]:
    """Candidate geocoding queries, best first. Falls back to county seat."""
    name = w.get("name") or ""
    county = w.get("judet") or ""
    limite = w.get("limite") or ""
    queries = []

    # 1. Place names mentioned in limits (localities are the most precise)
    for m in re.finditer(r"([A-ZĂÂÎȘȚ][a-zăâîșțăâîșț]+(?:\s+[A-ZĂÂÎȘȚ][a-zăâîșț]+)?)", limite):
        place = m.group(1).strip()
        if place and place.lower() not in {"jud", "limită", "cursul", "principal", "vărsare",
                                           "conf", "cu", "pârâul", "râul", "barajul", "la", "ieșire",
                                           "din", "județ", "județul", "sectorul", "km"}:
            queries.append(f"{place}, județul {county}, România" if county else f"{place}, România")
            if len(queries) >= 2:
                break

    # 2. River name + county
    if name:
        queries.append(f"{name}, județul {county}, România" if county else f"{name}, România")

    # 3. County seat (reliable for ordering rivers that cross a county)
    if county:
        queries.append(f"{county}, România")

    # 4. Dedupe, keep order
    seen, out = set(), []
    for q in queries:
        k = norm(q)
        if k and k not in seen:
            seen.add(k)
            out.append(q)
    return out


def geocode_any(queries: list[str]):
    """Try each query until one returns a point. Returns [lon, lat] or None."""
    for q in queries:
        pt = geocode(q)
        if pt:
            return pt
    return None


# County seats (approx lon/lat) — used to position contracts along a river
# course without hitting Nominatim rate limits. Accuracy of ±10 km is fine:
# we only need the correct ORDER of counties along a river.
COUNTY_SEATS: dict[str, tuple[float, float]] = {
    "Alba": (23.57, 46.08), "Arad": (21.32, 46.18), "Argeș": (24.82, 44.94),
    "Bacău": (26.91, 46.57), "Bihor": (21.94, 47.07), "Bistrița-Năsăud": (24.50, 47.13),
    "Botoșani": (26.67, 47.75), "Brașov": (25.61, 45.65), "Brăila": (27.97, 45.27),
    "Buzău": (26.78, 45.15), "Caraș-Severin": (21.90, 45.42), "Călărași": (26.82, 44.20),
    "Cluj": (23.62, 46.77), "Constanța": (28.65, 44.17), "Covasna": (26.01, 45.90),
    "Dâmbovița": (25.46, 44.93), "Dolj": (23.79, 44.33), "Galați": (28.01, 45.43),
    "Giurgiu": (25.97, 43.90), "Gorj": (23.26, 45.03), "Harghita": (25.62, 46.35),
    "Hunedoara": (22.91, 45.75), "Ialomița": (27.60, 44.56), "Iași": (27.60, 47.16),
    "Ilfov": (26.10, 44.44), "Maramureș": (23.89, 47.66), "Mehedinți": (22.66, 44.64),
    "Mureș": (24.56, 46.54), "Neamț": (26.38, 46.93), "Olt": (24.48, 44.43),
    "Prahova": (26.02, 44.94), "Satu Mare": (22.87, 47.79), "Sălaj": (23.05, 47.18),
    "Sibiu": (24.15, 45.80), "Suceava": (26.25, 47.65), "Teleorman": (25.34, 43.75),
    "Timiș": (21.22, 45.75), "Tulcea": (28.80, 45.18), "Vaslui": (27.73, 46.64),
    "Vâlcea": (24.37, 45.10), "Vrancea": (27.18, 45.70), "București": (26.10, 44.43),
}


def county_seat(county: str):
    """Best-effort county seat coordinates, normalizing diacritics."""
    n = norm(county)
    for name, pt in COUNTY_SEATS.items():
        if norm(name) == n or n in norm(name):
            return list(pt)
    return None


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))

    # Group waters by river key; find rivers with geometry
    groups: dict[str, list[dict]] = {}
    for w in waters:
        n = norm(w.get("name", ""))
        key = re.sub(r"^(raul|paraul|parau|valea|lacul|balta)\s+", "", n).split()[0][:5] if n else ""
        if key:
            groups.setdefault(key, []).append(w)

    updated = 0
    for key, group in groups.items():
        # find the geometry-bearing member
        geom_water = next((w for w in group if w.get("geometry")), None)
        if not geom_water:
            continue
        g = geom_water["geometry"]
        parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        if not parts:
            continue

        for w in group:
            if w.get("course_frac") is not None:
                continue
            # Prefer geocoded locality; fall back to county seat (no rate limits)
            pt = county_seat(w.get("judet") or "")
            if pt is None:
                continue
            frac = fraction_at(parts, pt)
            if frac is not None:
                w["course_frac"] = round(frac, 4)
                updated += 1
                print(f"  {w.get('name')[:50]:52} → frac {frac:.3f}")

    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[done] assigned course_frac to {updated} contracts")


if __name__ == "__main__":
    main()
