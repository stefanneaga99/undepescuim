#!/usr/bin/env python3
"""Tier: private lakes pipeline (proposal s8).

Parse osmid from the arebaltapeste private-lakes snapshot, query Overpass
directly ({type}(id:{id}); out geom;), extract Polygon geometry.
~201 queries, no Nominatim rate limit consumed.

Output: data/geocoded_private.geojson
Usage: python3 scripts/geocode_private.py [--limit N]
"""
import argparse
import json
import time

import geocode_common as gc


def parse_osmid(osmid):
    """'way/177167861' -> ('way', 177167861); 'relation/13004279' -> ('relation', 13004279)."""
    if not osmid or "/" not in str(osmid):
        return None
    t, _, i = str(osmid).partition("/")
    if t not in ("way", "relation", "node") or not i.isdigit():
        return None
    return t, int(i)


def fetch_geometry(db, osmid):
    """Overpass {type}(id); out geom; -> Polygon/MultiPolygon geometry or None.

    Cache-first (private_cache table): a successful geometry is stored under
    its osmid so re-runs and monthly refreshes never touch Overpass again.
    Full mirror rotation with the sticky last-good pointer and min_elements=1
    (a mirror that answers fast with ZERO elements for data it does not carry
    — e.g. the Swiss regional extract — is skipped, not recorded as good).
    Relations: 'out geom' returns member geometries (role='outer'); we build
    one ring per outer member -> Polygon, or MultiPolygon for multiple rings.

    Falls back to bbox rect in make_feature when Overpass is down."""
    row = db.execute("SELECT geojson FROM private_cache WHERE osmid=?", (osmid,)).fetchone()
    if row and row[0]:
        return json.loads(row[0])
    parsed = parse_osmid(osmid)
    if not parsed:
        return None
    otype, oid = parsed
    q = f'[out:json][timeout:10];{otype}({oid});out geom;'
    data = gc.overpass_query(q, timeout=10, min_elements=1)
    if not data:
        return None
    for el in data.get("elements", []):
        if el.get("type") != otype:
            continue
        if otype == "relation":
            rings = []
            for m in el.get("members", []):
                if m.get("role") != "outer":
                    continue
                ring = _closed_ring(m.get("geometry"))
                if ring:
                    rings.append(ring)
            if not rings:
                continue
            if len(rings) == 1:
                geom = {"type": "Polygon", "coordinates": rings}
            else:
                geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
            db.execute("INSERT OR REPLACE INTO private_cache(osmid, geojson) VALUES (?,?)",
                       (osmid, json.dumps(geom)))
            db.commit()
            return geom
        ring = _closed_ring(el.get("geometry"))
        if ring:
            geom = {"type": "Polygon", "coordinates": [ring]}
            db.execute("INSERT OR REPLACE INTO private_cache(osmid, geojson) VALUES (?,?)",
                       (osmid, json.dumps(geom)))
            db.commit()
            return geom
    return None


def _closed_ring(pts):
    """[[{lat,lon},...]] -> closed [[lng,lat],...] ring, or None."""
    if not pts:
        return None
    coords = [[p["lon"], p["lat"]] for p in pts]
    if not coords:
        return None
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    if len(coords) < 4:
        return None
    return coords


def make_feature(lake, geometry):
    props = {
        "name": lake.get("name") or lake.get("osmName"),
        "name_ro": lake.get("name") or lake.get("osmName"),
        "type": "lake",
        "source": "overpass" if geometry else "bbox",
        "source_detail": "Overpass direct OSM lookup via osmid (private lakes pipeline)" if geometry
                         else "bbox rectangle fallback (OSM geometry unavailable)",
        "osm_type": lake.get("osmid", "").split("/")[0] if lake.get("osmid") else None,
        "osm_id": lake.get("osmid"),
        "importance": None,
        "arebaltapeste_slug": str(lake.get("slug")),
        "judet": lake.get("judet") or lake.get("judetOsm"),
        "asociatie": None,
        "dimensiune": f"{lake.get('suprafata', '')} Ha" if lake.get("suprafata") else None,
        "geocode_tier": "tier3_overpass" if geometry else "tier3_bbox",
        "confidence": "high" if geometry else "low",
    }
    if not geometry:
        geometry = gc.bbox_rect_polygon(lake["bbox"])
    return {"type": "Feature", "id": f"private-{lake.get('slug')}", "geometry": geometry, "properties": props}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    with open(gc.PRIVATE_SNAPSHOT, encoding="utf-8") as fh:
        lakes = json.load(fh)
    if args.limit:
        lakes = lakes[: args.limit]

    db = gc.get_db()
    print(f"[private] {len(lakes)} lakes")
    features = []
    ok = 0
    cached = 0
    for i, lake in enumerate(lakes, 1):
        osmid = lake.get("osmid")
        from_cache = db.execute("SELECT 1 FROM private_cache WHERE osmid=? AND geojson IS NOT NULL", (osmid,)).fetchone()
        geom = fetch_geometry(db, osmid)
        if geom:
            ok += 1
            if from_cache:
                cached += 1
        features.append(make_feature(lake, geom))
        if not from_cache:
            time.sleep(2.0)  # be gentle with Overpass dynamic slots
        if i % 25 == 0 or i == len(lakes):
            print(f"  [{i}/{len(lakes)}] geometry ok={ok} (cached={cached})")

    fc = {
        "type": "FeatureCollection",
        "metadata": {"pipeline": "private_lakes", "pipeline_version": "1.0",
                     "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                     "input": len(lakes), "geometry_ok": ok, "geometry_missing": len(lakes) - ok,
                     "geometry_cached": cached},
        "features": features,
    }
    with open(gc.OUT_PRIVATE, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)
    print(f"[private] wrote {gc.OUT_PRIVATE} ({len(features)} features, {ok} with real geometry, {cached} cached)")
    db.close()


if __name__ == "__main__":
    main()
