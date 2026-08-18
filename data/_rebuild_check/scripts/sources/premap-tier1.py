#!/usr/bin/env python3
"""Tier 1 manual pre-mapping: extract 13 rivers + 15 major lakes from
HOTOSM Waterways of Romania (HDX snapshot) and Overpass (Danube).

Output: data/premapped/<slug>.geojson — one FeatureCollection per feature.
Rivers -> MultiLineString, lakes -> Polygon. See
data/raw/geocoding-pipeline-proposal.md §3 (Tier 1) and §7.1 (schema).

Tooling choice: we use the HOTOSM GeoJSON export (same OSM data as the
GPKG, 30.6 MB, no GDAL/ogr2ogr needed) parsed with Python stdlib only.
"""

import json
import math
import os
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_GEOJSON = os.path.join(ROOT, "data", "sources", "waterways.geojson")
OUT_DIR = os.path.join(ROOT, "data", "premapped")

# Romanian extent (lon, lat)
RO_BBOX = (20.26, 43.62, 29.69, 48.27)  # minlon, minlat, maxlon, maxlat

USER_AGENT = "UndePescuimMap/1.0 (contact@undepescuim.ro)"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def norm(s):
    """Diacritic-normalize: lowercase + strip combining marks."""
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn"
    )


def tokens(s):
    """Normalized token set of a string, e.g. 'Crișul Alb / Fehér-Körös' -> {crisul, alb, feher, koros}."""
    return set(norm(s).replace("/", " ").replace("-", " ").split())


def name_fields(p):
    """All name-ish fields of a HOTOSM feature."""
    return [p.get("name"), p.get("name_ro"), p.get("name_en"), p.get("name_latin")]


def is_lake_feature(p):
    """Lakes/reservoirs: natural water polygons (water=lake/reservoir/pond or natural_class=water)."""
    nc = p.get("natural_class")
    w = p.get("water")
    return nc == "water" or w in ("lake", "reservoir", "pond", "lagoon")


# ---------------------------------------------------------------------------
# Target definitions
# ---------------------------------------------------------------------------
# Rivers: matched on waterway=river; aliases checked against all name fields.
# `src` = anchor coordinate used to disambiguate same-name rivers (4 Bistrița
# rivers exist in RO; the famous one is the Moldavian Bistrița that forms Lacul
# Bicaz — the arebaltapeste entry "Râul Bistrița" (Bistrița-Năsăud) is a
# different, smaller river, so we anchor to the Moldavian course).
RIVERS = [
    {"slug": "siret", "name": "Siret", "name_ro": "Siret", "aliases": [["siret"]]},
    {"slug": "olt", "name": "Olt", "name_ro": "Olt", "aliases": [["olt"]]},
    {"slug": "mures", "name": "Mureș", "name_ro": "Mureș", "aliases": [["mures"], ["maros"]]},
    {"slug": "prut", "name": "Prut", "name_ro": "Prut", "aliases": [["prut"]]},
    {"slug": "somes", "name": "Someș", "name_ro": "Someș", "aliases": [["somes"]]},
    {"slug": "jiu", "name": "Jiu", "name_ro": "Jiu", "aliases": [["jiu"]]},
    {"slug": "arges", "name": "Argeș", "name_ro": "Argeș", "aliases": [["arges"]]},
    {"slug": "bistrita", "name": "Bistrița", "name_ro": "Bistrița", "aliases": [["bistrita"]], "src": (26.4, 46.8), "max_dist_km": 90},
    {"slug": "crisul-repede", "name": "Crișul Repede", "name_ro": "Crișul Repede", "aliases": [["crisul", "repede"], ["sebes", "koros"]]},
    {"slug": "crisul-alb", "name": "Crișul Alb", "name_ro": "Crișul Alb", "aliases": [["crisul", "alb"], ["feher", "koros"]]},
    {"slug": "crisul-negru", "name": "Crișul Negru", "name_ro": "Crișul Negru", "aliases": [["crisul", "negru"], ["fekete", "koros"]]},
    {"slug": "tarnava-mare", "name": "Târnava Mare", "name_ro": "Târnava Mare", "aliases": [["tarnava", "mare"]]},
]

# Lakes: matched on lake/reservoir polygon features; contains-style alias match.
# `src` = anchor coordinate from public/data/waters.json (arebaltapeste.ro) used to
# disambiguate homonyms (multiple lakes share names like Lacul Roșu / Iezer).
LAKES = [
    {"slug": "lacul-razim", "name": "Lacul Razim", "name_ro": "Lacul Razim", "aliases": ["lacul razim", "razim"]},
    {"slug": "lacul-sinoe", "name": "Lacul Sinoe", "name_ro": "Lacul Sinoe", "aliases": ["lacul sinoe", "sinoe"]},
    {"slug": "lacul-bicaz", "name": "Lacul Bicaz (Izvorul Muntelui)", "name_ro": "Lacul Bicaz", "aliases": ["lacul izvorul muntelui", "izvorul muntelui", "lacul bicaz", "acumularea bicaz"], "src": (26.0169, 47.0275)},
    {"slug": "lacul-vidraru", "name": "Lacul Vidraru", "name_ro": "Lacul Vidraru", "aliases": ["lacul vidraru", "vidraru"]},
    {"slug": "lacul-snagov", "name": "Lacul Snagov", "name_ro": "Lacul Snagov", "aliases": ["lacul snagov", "snagov"]},
    {"slug": "lacul-rosu", "name": "Lacul Roșu", "name_ro": "Lacul Roșu", "aliases": ["lacul rosu", "lacu rosu"], "src": (25.7871, 46.7892)},
    {"slug": "lacul-sfanta-ana", "name": "Lacul Sfânta Ana", "name_ro": "Lacul Sfânta Ana", "aliases": ["lacul sfanta ana", "sfanta ana"]},
    {"slug": "lacul-techirghiol", "name": "Lacul Techirghiol", "name_ro": "Lacul Techirghiol", "aliases": ["lacul techirghiol", "techirghiol"]},
    {"slug": "lacul-siutghiol", "name": "Lacul Siutghiol", "name_ro": "Lacul Siutghiol", "aliases": ["lacul siutghiol", "siutghiol"]},
    {"slug": "lacul-bucura", "name": "Lacul Bucura", "name_ro": "Lacul Bucura", "aliases": ["lacul bucura", "bucura"], "src": (22.8748, 45.3603)},
    {"slug": "lacul-balea", "name": "Lacul Bâlea", "name_ro": "Lacul Bâlea", "aliases": ["lacul balea", "balea"], "src": (24.6172, 45.6033)},
    {"slug": "lacul-tarnita", "name": "Lacul Tarnița", "name_ro": "Lacul Tarnița", "aliases": ["lacul tarnita", "lacul de acumulare tarnita", "tarnita"], "src": (23.2745, 46.7159)},
    {"slug": "lacul-stanca-costesti", "name": "Lacul Stânca-Costești", "name_ro": "Lacul Stânca-Costești", "aliases": ["stanca costesti", "costesti stanca", "lacul de acumulare costesti"], "src": (27.1839, 47.9433)},
    {"slug": "lacul-iezer", "name": "Lacul Iezer (Iezerul Mare)", "name_ro": "Lacul Iezer", "aliases": ["lacul iezer", "iezerul mare"], "src": (23.8007, 45.5868)},
    {"slug": "lacul-iezerul-mic", "name": "Lacul Iezerul Mic", "name_ro": "Lacul Iezerul Mic", "aliases": ["iezerul mic"], "src": (23.7789, 45.5872)},
]


def match_aliases(name_vals, aliases):
    """Return True if any normalized alias token-set is a subset of any name field's tokens."""
    field_sets = [tokens(n) for n in name_vals if n]
    for alias in aliases:
        alias_set = set(alias)
        for fs in field_sets:
            if alias_set.issubset(fs):
                return True
    return False


def match_lake_alias(name_vals, aliases):
    """Contains-style match for lake names: normalized alias substring in normalized name."""
    for n in name_vals:
        if not n:
            continue
        nn = norm(n)
        for a in aliases:
            if norm(a) in nn:
                return True
    return False


def polygon_area(coords):
    """Shoelace area (WGS84 degrees^2, sign-normalized) for exterior ring."""
    ring = coords[0]
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def largest_polygon(feats):
    """Pick the polygon with the largest exterior-ring area (robust to duplicate
    OSM representations of the same water body)."""
    best, best_area = None, -1.0
    for f in feats:
        g = f["geometry"]
        polys = []
        if g["type"] == "Polygon":
            polys = [g["coordinates"]]
        elif g["type"] == "MultiPolygon":
            polys = g["coordinates"]
        for coords in polys:
            a = polygon_area(coords)
            if a > best_area:
                best_area = a
                best = (coords, f)
    return best, best_area


def merge_lines(feats):
    """Collect all LineString/MultiLineString coords into one MultiLineString."""
    out = []
    total_pts = 0
    for f in feats:
        g = f["geometry"]
        if g["type"] == "LineString":
            out.append(g["coordinates"])
            total_pts += len(g["coordinates"])
        elif g["type"] == "MultiLineString":
            for line in g["coordinates"]:
                out.append(line)
                total_pts += len(line)
    return out, total_pts


# ---------------------------------------------------------------------------
# Extraction from HOTOSM
# ---------------------------------------------------------------------------
def load_hotosm():
    with open(SOURCES_GEOJSON) as fh:
        return json.load(fh)["features"]


def geo_dist_km(a, b):
    """Approximate great-circle distance between (lon, lat) points in km."""
    lon1, lat1 = a
    lon2, lat2 = b
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def feature_center(f):
    """Centroid-ish center of a feature's geometry: bbox center."""
    g = f["geometry"]
    xs, ys = [], []
    if g["type"] == "LineString":
        coords = [g["coordinates"]]
    elif g["type"] == "MultiLineString":
        coords = g["coordinates"]
    elif g["type"] == "Polygon":
        coords = [g["coordinates"][0]]
    elif g["type"] == "MultiPolygon":
        coords = [p[0] for p in g["coordinates"]]
    else:
        return None
    for line in coords:
        for pt in line:
            xs.append(pt[0])
            ys.append(pt[1])
    if not xs:
        return None
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def anchor_filter(hits, spec):
    """If the spec has a `src` anchor, drop features farther than max_dist_km
    (default 25 km) from it — resolves homonyms (Lacul Roșu in the Delta vs
    Harghita, Iezer floodplain vs Iezerul Mare mountain lake, 4× Bistrița)."""
    if "src" not in spec:
        return hits
    max_km = spec.get("max_dist_km", 25)
    out = []
    for f in hits:
        c = feature_center(f)
        if c is not None and geo_dist_km(c, spec["src"]) <= max_km:
            out.append(f)
    return out


def extract_river(feats, spec):
    hits = []
    for f in feats:
        p = f["properties"]
        if p.get("waterway") != "river":
            continue
        if match_aliases(name_fields(p), spec["aliases"]):
            hits.append(f)
    return anchor_filter(hits, spec)


def extract_lake(feats, spec):
    hits = []
    for f in feats:
        p = f["properties"]
        if not is_lake_feature(p):
            continue
        if match_lake_alias(name_fields(p), spec["aliases"]):
            hits.append(f)
    return anchor_filter(hits, spec)


# ---------------------------------------------------------------------------
# Danube via Overpass + bbox clip
# ---------------------------------------------------------------------------
def clip_segment_to_bbox(p0, p1, bbox):
    """Liang-Barsky clip of segment [p0,p1] to bbox (minlon,minlat,maxlon,maxlat).
    Returns None if fully outside, else (q0, q1)."""
    x0, y0 = p0
    x1, y1 = p1
    minx, miny, maxx, maxy = bbox
    dx, dy = x1 - x0, y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - minx, maxx - x0, y0 - miny, maxy - y0]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        else:
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return None
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return None
                if t < u2:
                    u2 = t
    return ([x0 + u1 * dx, y0 + u1 * dy], [x0 + u2 * dx, y0 + u2 * dy])


def clip_linestring(coords, bbox):
    out = []
    cur = None
    for i in range(len(coords) - 1):
        seg = clip_segment_to_bbox(coords[i], coords[i + 1], bbox)
        if seg is None:
            cur = None
            continue
        if cur is not None and seg[0] == cur[-1]:
            cur.append(seg[1])
        else:
            if cur is not None:
                out.append(cur)
            cur = [seg[0], seg[1]]
    if cur is not None:
        out.append(cur)
    return out


def fetch_danube_overpass():
    """Fetch Danube main-stem ways via Overpass.

    OSM tags the Danube as name="Dunărea" (RO), name:en="Danube"; the plain
    name="Danube" query matches nothing in the RO window. We query the RO
    bounding window for name:en="Danube" OR name starting with "Dun"
    (catches Dunărea / Dunav / Дунав variants + delta branches), union them,
    then clip each way's geometry to the RO extent client-side.
    """
    q = (
        '[out:json][timeout:120];'
        '('
        'way["waterway"="river"]["name:en"="Danube"]'
        f'({RO_BBOX[1]},{RO_BBOX[0]},{RO_BBOX[3]},{RO_BBOX[2]});'
        'way["waterway"="river"]["name"~"^Dun",i]'
        f'({RO_BBOX[1]},{RO_BBOX[0]},{RO_BBOX[3]},{RO_BBOX[2]});'
        ');'
        'out geom;'
    )
    data = None
    last_err = None
    for endpoint in OVERPASS_MIRRORS:
        try:
            r = urllib.request.Request(
                endpoint,
                data=q.encode(),
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(r, timeout=150) as resp:
                payload = resp.read()
            # Guard against HTML error pages returned with 200
            if b"<html" in payload[:512].lower() or b"runtime error" in payload[:1024].lower():
                raise RuntimeError(f"{endpoint} returned error page")
            data = json.loads(payload)
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"    overpass endpoint {endpoint} failed: {exc}")
    if data is None:
        raise RuntimeError(f"all Overpass mirrors failed: {last_err}")
    ways = [el for el in data.get("elements", []) if el.get("type") == "way"]
    clipped = []
    src_ids = []
    seen = set()
    for w in ways:
        if w["id"] in seen:
            continue
        seen.add(w["id"])
        geom = w.get("geometry", [])
        coords = [[pt["lon"], pt["lat"]] for pt in geom]
        if not coords:
            continue
        pieces = clip_linestring(coords, RO_BBOX)
        for piece in pieces:
            if len(piece) >= 2:
                clipped.append(piece)
        if pieces:
            src_ids.append(f"way/{w['id']}")
    return clipped, src_ids


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def make_feature(slug, name, name_ro, ftype, geometry, osm_type, osm_id, source_detail):
    return {
        "type": "Feature",
        "id": slug,
        "geometry": geometry,
        "properties": {
            "name": name,
            "name_ro": name_ro,
            "type": ftype,
            "source": "manual_premap",
            "source_detail": source_detail,
            "osm_type": osm_type,
            "osm_id": osm_id,
            "geocode_tier": "tier1",
            "confidence": "high",
        },
    }


def write_feature(slug, feature):
    fc = {
        "type": "FeatureCollection",
        "metadata": {
            "pipeline": "tier1_premap",
            "pipeline_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "features": [feature],
    }
    path = os.path.join(OUT_DIR, f"{slug}.geojson")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False, separators=(",", ":"))
    return path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Loading {SOURCES_GEOJSON} ...")
    feats = load_hotosm()
    print(f"  {len(feats)} features")

    report = []

    # --- Rivers ---
    for spec in RIVERS:
        hits = extract_river(feats, spec)
        lines, npts = merge_lines(hits)
        if not lines:
            print(f"  RIVER MISS: {spec['slug']}")
            report.append((spec["slug"], "MISS"))
            continue
        src_ids = sorted({h["properties"]["id"] for h in hits})
        geometry = {"type": "MultiLineString", "coordinates": lines}
        detail = (
            f"HOTOSM Waterways HDX snapshot 2026-08-07, waterway=river name match "
            f"({len(hits)} segments, {npts} points), ANCPI validation: see README"
        )
        feat = make_feature(
            spec["slug"], spec["name"], spec["name_ro"], "river",
            geometry, "way", src_ids[0], detail,
        )
        path = write_feature(spec["slug"], feat)
        print(f"  RIVER {spec['slug']:16s} {len(hits):3d} segs {npts:6d} pts -> {os.path.basename(path)}")
        report.append((spec["slug"], "ok", len(hits), npts, len(src_ids)))

    # --- Danube (Overpass) ---
    print("Fetching Danube via Overpass ...")
    try:
        danube_lines, danube_ids = fetch_danube_overpass()
        if not danube_lines:
            raise RuntimeError("Overpass returned no Danube segments in RO bbox")
        geometry = {"type": "MultiLineString", "coordinates": danube_lines}
        detail = (
            "Overpass API way[waterway=river] name:en=Danube OR name~^Dun "
            "(OSM primary tag is Dunărea, not Danube), no country filter, "
            "clipped to RO bbox (20.26,43.62)-(29.69,48.27)"
        )
        feat = make_feature(
            "dunarea", "Dunărea", "Dunărea", "river",
            geometry, "way", danube_ids[0], detail,
        )
        path = write_feature("dunarea", feat)
        npts = sum(len(l) for l in danube_lines)
        print(f"  RIVER dunarea (Danube) {len(danube_lines):3d} segs {npts:6d} pts -> {os.path.basename(path)}")
        report.append(("dunarea", "ok", len(danube_lines), npts, len(danube_ids)))
    except Exception as exc:
        print(f"  DANUBE FAILED: {exc}")
        report.append(("dunarea", f"FAIL: {exc}"))

    # --- Lakes ---
    for spec in LAKES:
        hits = extract_lake(feats, spec)
        best, area = largest_polygon(hits)
        if best is None:
            print(f"  LAKE MISS: {spec['slug']}")
            report.append((spec["slug"], "MISS"))
            continue
        coords, src_feat = best
        geometry = {"type": "Polygon", "coordinates": coords}
        src_id = src_feat["properties"]["id"]
        detail = (
            f"HOTOSM Waterways HDX snapshot 2026-08-07, water=lake/reservoir name match "
            f"({len(hits)} candidate features, largest polygon selected)"
        )
        feat = make_feature(
            spec["slug"], spec["name"], spec["name_ro"], "lake",
            geometry, "way", src_id, detail,
        )
        path = write_feature(spec["slug"], feat)
        print(f"  LAKE  {spec['slug']:16s} area={area:.5f} -> {os.path.basename(path)}")
        report.append((spec["slug"], "ok", len(hits), round(area, 5)))

    print("\n=== SUMMARY ===")
    for row in report:
        print("  " + " | ".join(str(x) for x in row))
    n_ok = sum(1 for r in report if r[1] == "ok")
    print(f"{n_ok}/{len(report)} features written to {OUT_DIR}")
    return 0 if n_ok == len(report) else 1


if __name__ == "__main__":
    sys.exit(main())
