#!/usr/bin/env python3
"""Probe geocoding for Buzău contract limit places (task t_84b29064).

Geocodes the limit place names via Nominatim (cached in geocode.db) and
computes the fraction each projects to on the Râul Buzău course.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import geocode_common as gc

WATERS = ROOT / "public" / "data" / "waters.json"


def haversine(a, b):
    R = 6371.0
    la1, lo1 = math.radians(a[1]), math.radians(a[0])
    la2, lo2 = math.radians(b[1]), math.radians(b[0])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def order_parts(parts):
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
    ordered = order_parts(parts)
    total = sum(haversine(p[i - 1], p[i]) for p in ordered for i in range(1, len(p)))
    if total <= 0:
        return None, None

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
    return best, bd


def geocode_cached(db, query):
    """Return [lon, lat] from cache, else query Nominatim and store. None on miss."""
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
        return None  # negative-cached
    results = gc.nominatim_search(query, countrycodes="ro")
    if results:
        first = results[0]
        db.execute(
            "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, osm_type, osm_id, geometry_type, bbox, source, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                query, "probe", "rau", json.dumps(results, ensure_ascii=False),
                first.get("osm_type"), str(first.get("osm_id")),
                first.get("geojson", {}).get("type") if isinstance(first.get("geojson"), dict) else None,
                json.dumps(first.get("boundingbox")), "nominatim", "medium",
            ),
        )
        db.commit()
        return [float(first["lon"]), float(first["lat"])]
    db.execute(
        "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, source) VALUES (?,?,?,NULL,?)",
        (query, "probe", "rau", "nominatim_negative"),
    )
    db.commit()
    return None


def main():
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    buzau = next(w for w in waters if w["name"] == "Râul Buzău" and w.get("geometry"))
    parts = buzau["geometry"]["coordinates"]

    db = gc.get_db()
    queries = [
        ("Siriu (comuna)", "Siriu, Buzău, România"),
        ("Barajul Siriu", "Barajul Siriu, Buzău, România"),
        ("Lacul Siriu", "Lacul Siriu, Buzău, România"),
        ("Sibiciu de Sus", "Sibiciu de Sus, Pătârlagele, Buzău, România"),
        ("Sibiciu de Jos", "Sibiciu de Jos, Buzău, România"),
        ("Sibiciu", "Sibiciu, Pătârlagele, Buzău, România"),
        ("Crasna", "Crasna, Buzău, România"),
        ("Grămăticu", "Grămăticu, România"),
        ("Grămăticu (stream)", "Grămăticu, Siriu, Buzău, România"),
        ("Jirlău", "Jirlău, Buzău, România"),
        ("Voinești (BR)", "Voinești, Brăila, România"),
        ("Nehoiu", "Nehoiu, Buzău, România"),
        ("Pătârlagele", "Pătârlagele, Buzău, România"),
        ("Cislău", "Cislău, Buzău, România"),
        ("Întorsura Buzăului", "Întorsura Buzăului, Covasna, România"),
        ("Berca", "Berca, Buzău, România"),
    ]
    print(f"{'place':24} {'lon':>10} {'lat':>9} {'frac':>8} {'dist_km':>8}  name")
    for label, q in queries:
        pt = geocode_cached(db, q)
        if not pt:
            print(f"{label:24} {'—':>10} {'—':>9} {'—':>8} {'—':>8}  (no result)")
            continue
        frac, dist = fraction_at(parts, pt)
        display = ""
        row = db.execute(
            "SELECT result_json FROM geocode_cache WHERE query_string = ?", (q,)
        ).fetchone()
        if row and row[0]:
            try:
                display = json.loads(row[0])[0].get("display_name", "")[:60]
            except Exception:
                pass
        print(f"{label:24} {pt[0]:>10.4f} {pt[1]:>9.4f} {frac:>8.4f} {dist:>8.1f}  {display}")


if __name__ == "__main__":
    main()
