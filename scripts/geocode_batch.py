#!/usr/bin/env python3
"""Tier 2 + Tier 3 geocoder for public waters (UndePescuim).

Tier 2: for each public water NOT covered by data/premapped/:
  cache lookup -> Nominatim query (1 req/sec hard limit) -> filter -> cache write.
  Query strategy (proposal s4.2), WITHOUT diacritics, never prefix "Râul".
Tier 3 fallback chain (proposal s5) for misses:
  Overpass exact-name -> Natural Earth Europe name match -> bbox rectangle.

Output: data/geocoded_public.geojson (features for non-premapped waters).
Cache: data/cache/geocode.db (schema s6.1, negative cache for misses).

Usage: python3 scripts/geocode_batch.py [--limit N] [--skip-tier3]
"""
import argparse
import json
import sys

import geocode_common as gc


def cache_get(db, query):
    row = db.execute("SELECT result_json, osm_type, osm_id, geojson, bbox, importance, tier, source, confidence, hit_count FROM geocode_cache WHERE query_string=?", (query,)).fetchone()
    if not row:
        return None
    db.execute("UPDATE geocode_cache SET hit_count=hit_count+1, last_accessed=datetime('now') WHERE query_string=?", (query,))
    db.commit()
    return row


def cache_put(db, query, water, result):
    """Write a cache row. result=None -> negative cache (miss)."""
    rj = None
    osm_type = osm_id = geometry_type = geojson = bbox = None
    importance = None
    tier = "tier2"
    source = "nominatim"
    confidence = "medium"
    if result is not None:
        rj = json.dumps(result, ensure_ascii=False)
        osm_type = result.get("osm_type")
        osm_id = f"{result.get('osm_type')}/{result.get('osm_id')}" if result.get("osm_id") else None
        geom = result.get("geojson") or {}
        geometry_type = geom.get("type")
        geojson = json.dumps(geom, ensure_ascii=False) if geom else None
        bbox = json.dumps(result.get("boundingbox"))
        importance = result.get("importance")
    else:
        tier = "tier2_miss"
        source = "nominatim_negative"
    db.execute(
        """INSERT OR REPLACE INTO geocode_cache
           (query_string, water_name, water_type, arebaltapeste_slug, result_json,
            osm_type, osm_id, geometry_type, geojson, bbox, importance, tier, source, confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (query, water["name"], water["subtype"], water["slug"], rj,
         osm_type, osm_id, geometry_type, geojson, bbox, importance, tier, source, confidence),
    )
    db.commit()


def build_queries(water):
    """Query strategy per proposal s4.2, in exact order. No diacritics; never
    prefix 'Râul'. Returns [(query, use_ro_filter), ...]:
      river: "{name} Romania" RO -> "{name} river Romania" RO -> "{name}" no-filter
      lake:  "{name}" RO -> "Lacul {name}" RO -> "{name} Romania" RO"""
    subtype = water["subtype"]
    base = gc.strip_prefix(water["name"])            # 'Râul X' -> 'X'
    base_norm = gc.norm(base).strip()                # diacritic-free
    head = base_norm.split("(")[0].strip()           # drop parenthetical
    candidates = []
    if subtype == "rau":
        for c in (f"{head} Romania", f"{base_norm} Romania",
                  f"{head} river Romania", f"{base_norm} river Romania"):
            candidates.append((c, True))
        candidates.append((head, False))             # transnational last resort
    else:
        candidates.append((head, True))
        if not head.startswith("lacul"):
            candidates.append((f"Lacul {head}", True))
        candidates.append((f"{head} Romania", True))
        if base_norm != head:
            candidates.append((f"{base_norm} Romania", True))
    seen, out = set(), []
    for c, ro in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append((c, ro))
    return out


def filter_result(r, water, no_filter=False):
    """Proposal s4.1/4.3: lake -> type='lake'; river -> category='waterway' AND type='river'.
    Drop county/city (boundary/administrative) matches. For no-filter queries
    (transnational), require bbox intersection with Romanian extent."""
    cat = r.get("category")
    typ = r.get("type")
    if no_filter and not gc.bbox_intersects_ro(r.get("boundingbox") or []):
        return False
    if water["subtype"] == "rau":
        return cat == "waterway" and typ == "river"
    # lake: accept type=lake (water/lake or natural/lake); fall back to natural=water
    return typ == "lake" or (typ == "water" and cat == "natural")


def pick_best(hits, water):
    """Highest importance, tie-break relation > way."""
    def score(r):
        return (r.get("importance") or 0.0, 1 if r.get("osm_type") == "relation" else 0)
    return max(hits, key=score) if hits else None


def tier2_nominatim(db, water):
    """Return (result|None, query_used|None). Cache-first, negative cache honored."""
    for q, ro in build_queries(water):
        result = _try_query(db, water, q, countrycodes="ro" if ro else None, no_filter=not ro)
        if result:
            return result, q + ("" if ro else " (no country filter)")
    return None, None


def _try_query(db, water, q, countrycodes, no_filter):
    row = cache_get(db, q)
    if row is not None:
        if row[0] is not None:  # positive cache
            result = json.loads(row[0])
            result["_query"] = q
            return result
        return None  # negative cache -> try next query
    results = gc.nominatim_search(q, countrycodes=countrycodes)
    hits = [r for r in results if filter_result(r, water, no_filter=no_filter)]
    if hits:
        result = pick_best(hits, water)
        cache_put(db, q, water, result)
        result["_query"] = q
        return result
    cache_put(db, q, water, None)  # negative cache
    return None


# ---------------------------------------------------------------------------
# Tier 3 fallbacks
# ---------------------------------------------------------------------------
def overpass_exact_name(water, timeout=8):
    """Tier 3: exact-name Overpass match (proposal s5.2), RO bbox restricted.

    Single composite query (way + relation) so a miss costs at most `timeout`
    seconds on one mirror — the public Overpass endpoints are flaky (504/timeout
    on name searches observed 2026-08), so we bound the cost and fall through
    to NE/bbox rather than hanging the batch.

    Returns (geometry, osm_id) or (None, None)."""
    name = gc.strip_prefix(water["name"])            # 'Râul X' -> 'X'
    name = name.split("(")[0].strip()
    minlon, minlat, maxlon, maxlat = gc.RO_BBOX
    if water["subtype"] == "rau":
        tag = 'way["waterway"="river"]["name"="%s"]' % name
    else:
        tag = 'way["natural"="water"]["name"="%s"]' % name
    q = (
        '[out:json][timeout:%d];(' % timeout
        + tag + ';'
        + f'relation["name"="{name}"]({minlat},{minlon},{maxlat},{maxlon});'
        + ');out geom;'
    )
    data = gc.overpass_query(q, timeout=timeout, mirrors=1, min_elements=1)
    if not data:
        return None, None
    for el in data.get("elements", []):
        if el.get("type") == "relation":
            # 'out geom' puts geometry on the members; take all member lines
            lines = []
            for m in el.get("members", []):
                g = m.get("geometry")
                if not g or len(g) < 2:
                    continue
                lines.append([[p["lon"], p["lat"]] for p in g])
            if not lines:
                continue
            if water["subtype"] == "rau":
                return {"type": "MultiLineString", "coordinates": lines}, f"relation/{el['id']}"
            # lake: close each member ring into a polygon
            polygons = []
            for line in lines:
                if line[0] != line[-1]:
                    line.append(line[0])
                if len(line) >= 4:
                    polygons.append([line])
            if polygons:
                geom = {"type": "Polygon", "coordinates": polygons[0]} if len(polygons) == 1 \
                    else {"type": "MultiPolygon", "coordinates": polygons}
                return geom, f"relation/{el['id']}"
            continue
        geom = el.get("geometry")
        if not geom:
            continue
        coords = [[p["lon"], p["lat"]] for p in geom]
        if not coords:
            continue
        if water["subtype"] == "rau":
            if len(coords) >= 2:
                return {"type": "MultiLineString", "coordinates": [coords]}, f"{el['type']}/{el['id']}"
        else:
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            if len(coords) >= 4:
                return {"type": "Polygon", "coordinates": [coords]}, f"{el['type']}/{el['id']}"
    return None, None


def natural_earth_match(water):
    """NE Europe supplement: download once, match by name (proposal s5.1 step 2)."""
    if not gc.os.path.exists(gc.NE_FILE):
        try:
            print(f"  [ne] downloading {gc.NE_URL}")
            body = gc.http_get(gc.NE_URL)
            gc.os.makedirs(gc.os.path.dirname(gc.NE_FILE), exist_ok=True)
            with open(gc.NE_FILE, "w", encoding="utf-8") as fh:
                fh.write(body)
        except Exception as exc:
            print(f"  [ne] download failed: {exc} (skipping NE tier)")
            return None
    try:
        with open(gc.NE_FILE, encoding="utf-8") as fh:
            fc = json.load(fh)
    except Exception:
        return None
    want = gc.norm(gc.strip_prefix(water["name"])).split("(")[0].strip()
    if not want:
        return None
    for feat in fc.get("features", []):
        nm = gc.norm(feat["properties"].get("name") or "")
        if nm == want or nm == want + " river" or nm.split() == want.split():
            g = feat.get("geometry")
            if g and g.get("type") in ("LineString", "MultiLineString"):
                return gc.geom_to_mls(g), "natural_earth"
    return None


def tier3_fallback(db, water, skip_ne=False):
    """Return (feature_properties) dict with geometry + tier/confidence.

    Tier 3 results are cached too (key 'tier3:<slug>') so a re-run that finds
    every Nominatim query negative-cached does not re-hit Overpass/NE."""
    cache_key = "tier3:" + water["slug"]
    row = db.execute("SELECT result_json, osm_id, tier, source, confidence, geojson FROM geocode_cache WHERE query_string=?", (cache_key,)).fetchone()
    if row:
        return {"geometry": json.loads(row[5]) if row[5] else None, "osm_id": row[1],
                "geocode_tier": row[2], "source": row[3], "confidence": row[4]}

    if water["subtype"] == "rau":
        geom, src = overpass_exact_name(water)
        if geom:
            res = {"geometry": geom, "osm_id": src, "geocode_tier": "tier3_overpass",
                   "source": "overpass", "confidence": "medium"}
            _cache_tier3(db, cache_key, water, res)
            return res
        if not skip_ne:
            geom, _ = natural_earth_match(water)
            if geom:
                res = {"geometry": {"type": "MultiLineString", "coordinates": geom},
                       "osm_id": None, "geocode_tier": "tier3_ne",
                       "source": "natural_earth", "confidence": "low"}
                _cache_tier3(db, cache_key, water, res)
                return res
    else:
        geom, src = overpass_exact_name(water)
        if geom:
            res = {"geometry": geom, "osm_id": src, "geocode_tier": "tier3_overpass",
                   "source": "overpass", "confidence": "medium"}
            _cache_tier3(db, cache_key, water, res)
            return res
    # bbox rectangle fallback (proposal s5.1 step 3)
    if water.get("bbox"):
        res = {"geometry": gc.bbox_rect_polygon(water["bbox"]), "osm_id": None,
               "geocode_tier": "tier3_bbox", "source": "bbox", "confidence": "low"}
    else:
        res = {"geometry": None, "osm_id": None, "geocode_tier": "failed",
               "source": "none", "confidence": "none"}
    _cache_tier3(db, cache_key, water, res)
    return res


def _cache_tier3(db, cache_key, water, res):
    geom = res["geometry"]
    db.execute(
        """INSERT OR REPLACE INTO geocode_cache
           (query_string, water_name, water_type, arebaltapeste_slug, result_json,
            osm_type, osm_id, geometry_type, geojson, bbox, importance, tier, source, confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (cache_key, water["name"], water["subtype"], water["slug"], None,
         None, res["osm_id"], geom["type"] if geom else None,
         json.dumps(geom, ensure_ascii=False) if geom else None, None, None,
         res["geocode_tier"], res["source"], res["confidence"]),
    )
    db.commit()


def make_feature(water, result, tier3):
    """Assemble the s7.1 property set for a public water."""
    props = {
        "name": water["name"],
        "name_ro": water["name"],
        "type": "river" if water["subtype"] == "rau" else "lake",
        "source": None, "source_detail": None,
        "osm_type": None, "osm_id": None, "importance": None,
        "arebaltapeste_slug": water["slug"],
        "judet": water.get("judet"),
        "asociatie": (water.get("asociatie") or {}).get("name"),
        "dimensiune": water.get("dimensiune"),
        "geocode_tier": None, "confidence": None,
    }
    if result is not None:
        props.update({
            "source": "nominatim",
            "source_detail": "Nominatim batch geocoding, polygon_geojson=1",
            "osm_type": result.get("osm_type"),
            "osm_id": f"{result.get('osm_type')}/{result.get('osm_id')}" if result.get("osm_id") else None,
            "importance": result.get("importance"),
            "geocode_tier": "tier2",
            "confidence": "medium",
        })
        geom = result.get("geojson") or {}
        if water["subtype"] == "rau":
            coords = gc.geom_to_mls(geom)
            geometry = {"type": "MultiLineString", "coordinates": coords} if coords else None
        else:
            polygon = gc.geom_to_polygon(geom)
            geometry = polygon
    else:
        geometry = tier3["geometry"]
        props.update({
            "source": tier3["source"],
            "source_detail": f"Tier 3 fallback ({tier3['geocode_tier']})",
            "osm_id": tier3["osm_id"],
            "geocode_tier": tier3["geocode_tier"],
            "confidence": tier3["confidence"],
        })
    return {"type": "Feature", "id": water["slug"], "geometry": geometry, "properties": props}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-tier3", action="store_true")
    args = ap.parse_args()

    waters = gc.load_waters()
    premaps = gc.load_premaps()
    db = gc.get_db()

    to_process, skipped = [], []
    for w in waters:
        if gc.premap_match(w, premaps):
            skipped.append(w)
        else:
            to_process.append(w)
    if args.limit:
        to_process = to_process[: args.limit]

    print(f"[batch] {len(waters)} waters; {len(skipped)} premapped (skipped); {len(to_process)} to geocode")
    features = []
    counts = {"tier2_hit": 0, "tier2_miss": 0, "t3_overpass": 0, "t3_ne": 0, "t3_bbox": 0, "failed": 0}
    for i, w in enumerate(to_process, 1):
        result, _ = tier2_nominatim(db, w)
        if result is not None:
            feat = make_feature(w, result, None)
            counts["tier2_hit"] += 1
        else:
            counts["tier2_miss"] += 1
            tier3 = {"geometry": None, "osm_id": None, "geocode_tier": "failed",
                     "source": "none", "confidence": "none"}
            if not args.skip_tier3:
                tier3 = tier3_fallback(db, w, skip_ne=False)
            feat = make_feature(w, None, tier3)
            t = tier3["geocode_tier"]  # tier3_overpass | tier3_ne | tier3_bbox | failed
            if t in ("tier3_overpass", "tier3_ne", "tier3_bbox"):
                counts["t3_" + t[6:]] += 1
            else:
                counts["failed"] += 1
        features.append(feat)
        if i % 25 == 0 or i == len(to_process):
            print(f"  [{i}/{len(to_process)}] hits={counts['tier2_hit']} misses={counts['tier2_miss']}")

    fc = {
        "type": "FeatureCollection",
        "metadata": {"pipeline": "tier2_tier3_batch", "pipeline_version": "1.0",
                     "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                     "processed": len(to_process), "skipped_premapped": len(skipped), "counts": counts},
        "features": features,
    }
    with open(gc.OUT_PUBLIC, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)
    print(f"[batch] wrote {gc.OUT_PUBLIC} ({len(features)} features)")
    print(f"[batch] counts={counts}")
    db.close()


if __name__ == "__main__":
    main()
