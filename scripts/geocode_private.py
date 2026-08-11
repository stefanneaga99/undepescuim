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


def fetch_geometry(osmid):
    """Overpass {type}(id); out geom; -> Polygon/MultiPolygon geometry or None.

    By-ID lookups are fast on the first mirror; a miss costs at most ~10s
    (mirrors=1) instead of up to 60s trying every flaky mirror."""
    parsed = parse_osmid(osmid)
    if not parsed:
        return None
    otype, oid = parsed
    q = f'[out:json][timeout:10];{otype}({oid});out geom;'
    data = gc.overpass_query(q, timeout=10, mirrors=1)
    if not data:
        return None
    for el in data.get("elements", []):
        if el.get("type") != otype:
            continue
        geom = el.get("geometry")
        if not geom:
            continue
        coords = [[p["lon"], p["lat"]] for p in geom]
        if not coords:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        if len(coords) < 4:
            continue
        return {"type": "Polygon", "coordinates": [coords]}
    return None


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

    print(f"[private] {len(lakes)} lakes")
    features = []
    ok = 0
    for i, lake in enumerate(lakes, 1):
        geom = fetch_geometry(lake.get("osmid"))
        if geom:
            ok += 1
        features.append(make_feature(lake, geom))
        time.sleep(1.0)  # be gentle with Overpass dynamic slots
        if i % 25 == 0 or i == len(lakes):
            print(f"  [{i}/{len(lakes)}] geometry ok={ok}")

    fc = {
        "type": "FeatureCollection",
        "metadata": {"pipeline": "private_lakes", "pipeline_version": "1.0",
                     "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                     "input": len(lakes), "geometry_ok": ok, "geometry_missing": len(lakes) - ok},
        "features": features,
    }
    with open(gc.OUT_PRIVATE, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)
    print(f"[private] wrote {gc.OUT_PRIVATE} ({len(features)} features, {ok} with real geometry)")


if __name__ == "__main__":
    main()
