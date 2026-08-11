#!/usr/bin/env python3
"""Shared helpers for the UndePescuim geocoding pipeline (Tiers 2-3).

Design: data/raw/geocoding-pipeline-proposal.md (sections 4-8).
Stdlib only: json, sqlite3, urllib, unicodedata.
"""
import json
import os
import sqlite3
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATERS_JSON = os.path.join(ROOT, "public", "data", "waters.json")
PREMAPPED_DIR = os.path.join(ROOT, "data", "premapped")
CACHE_DB = os.path.join(ROOT, "data", "cache", "geocode.db")
PRIVATE_SNAPSHOT = os.path.join(ROOT, "data", "raw", "arebaltapeste_probe", "snapshot_balti.json")
OUT_PUBLIC = os.path.join(ROOT, "data", "geocoded_public.geojson")
OUT_PRIVATE = os.path.join(ROOT, "data", "geocoded_private.geojson")
OUT_MERGED = os.path.join(ROOT, "data", "waters_geocoded.geojson")
OUT_PUBLIC_DATA = os.path.join(ROOT, "public", "data", "waters_geocoded.geojson")
NE_FILE = os.path.join(ROOT, "data", "sources", "ne_10m_rivers_europe.geojson")

# Romanian extent (lon 20.26-29.69, lat 43.62-48.27)
RO_BBOX = (20.26, 43.62, 29.69, 48.27)
USER_AGENT = "UndePescuimMap/1.0 (contact@undepescuim.ro)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_europe.geojson"

_last_req = 0.0


def norm(s):
    """Diacritic-strip + lowercase. 'Mureș' -> 'mures', 'Râul Fizeș' -> 'raul fizes'."""
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn"
    )


def strip_prefix(name, prefixes=("raul", "paraul")):
    """Remove a leading river prefix ('Râul X' -> 'X') for query construction."""
    n = norm(name).strip()
    for p in prefixes:
        if n.startswith(p + " "):
            return name.strip()[len(p) + 1:].strip()
    return name.strip()


def load_waters():
    """Return the public waters list. Tolerates both the refresh wrapper
    {generatedAt, count, items} and a bare list."""
    with open(WATERS_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return data.get("items") or []
    return data


def load_premaps():
    """Load data/premapped/*.geojson -> [{file, name, type, feature}]."""
    out = []
    for fn in sorted(os.listdir(PREMAPPED_DIR)):
        if not fn.endswith(".geojson"):
            continue
        with open(os.path.join(PREMAPPED_DIR, fn), encoding="utf-8") as fh:
            fc = json.load(fh)
        for feat in fc.get("features", []):
            out.append({"file": fn, "name": feat["properties"].get("name", ""),
                        "type": feat["properties"].get("type", ""), "feature": feat})
    return out


def premap_match(water, premaps):
    """Return the premap entry matching a water by name-token containment + subtype,
    or None. A water is SKIPPED by the batch when a premap matches."""
    wt = set(norm(water["name"]).replace("/", " ").replace("-", " ").split())
    want = "lake" if water.get("subtype") == "lac" else "river"
    for p in premaps:
        if p["type"] != want:
            continue
        pt = set(norm(p["name"]).replace("/", " ").replace("-", " ").split())
        if pt and pt <= wt:
            return p
    return None


def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def rate_limit(min_interval=1.0):
    """Enforce a hard minimum interval between outbound requests."""
    global _last_req
    dt = time.monotonic() - _last_req
    if dt < min_interval:
        time.sleep(min_interval - dt)
    _last_req = time.monotonic()


def nominatim_search(query, countrycodes=None, limit=5):
    """Nominatim /search. Retry 429/503 with 2/4/8s backoff (max 3)."""
    params = {"q": query, "format": "jsonv2", "polygon_geojson": 1, "limit": limit}
    if countrycodes:
        params["countrycodes"] = countrycodes
    url = NOMINATIM + "?" + urllib.parse.urlencode(params)
    for attempt, backoff in enumerate((2, 4, 8)):
        rate_limit()
        try:
            body = http_get(url, {"User-Agent": USER_AGENT, "Accept": "application/json"})
            return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < 3:
                time.sleep(backoff)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 3:
                time.sleep(backoff)
                continue
            raise
    return []


_last_good_mirror = 0  # index of the most recently working Overpass mirror


def overpass_query(q, timeout=8, mirrors=None, retries=2, min_elements=0):
    """POST an Overpass QL query; return parsed JSON or None.

    The public Overpass endpoints are flaky (504/read timeouts observed on all
    mirrors in 2026-08) and their health flips within minutes, and the fleet
    throttles busy IPs with dynamic slots. We rotate the last-working mirror
    to the front, give each mirror a short timeout, and retry the whole
    rotation with a 5s/10s backoff when every mirror fails. Pass mirrors=1 to
    try only the first mirror (tier-3 fallback, bounding cost).

    min_elements: when >0, a response with fewer than this many elements is
    treated as a mirror failure (some mirrors return fast EMPTY results for
    regional data they do not carry — e.g. overpass.osm.ch had no Romanian
    features — which must not poison the sticky-mirror pointer)."""
    global _last_good_mirror
    data = urllib.parse.urlencode({"data": q}).encode()
    for attempt in range(retries + 1):
        urls = list(OVERPASS_URLS)
        urls = urls[_last_good_mirror:] + urls[:_last_good_mirror]
        if mirrors is not None:
            urls = urls[:mirrors]
        for url in urls:
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8")
                parsed = json.loads(body)
                if min_elements and len(parsed.get("elements", [])) < min_elements:
                    continue  # regional/empty mirror — do NOT mark as good
                _last_good_mirror = OVERPASS_URLS.index(url)
                return parsed
            except Exception:
                continue
        if attempt < retries:
            time.sleep(5 * (attempt + 1))
    return None


def geom_to_mls(geom):
    """Coerce a GeoJSON geometry to MultiLineString (rivers)."""
    if not geom:
        return None
    t = geom.get("type")
    if t == "MultiLineString":
        return geom["coordinates"]
    if t == "LineString":
        return [geom["coordinates"]]
    return None


def geom_to_polygon(geom):
    """Coerce a GeoJSON geometry to Polygon or MultiPolygon (lakes)."""
    if not geom:
        return None
    t = geom.get("type")
    if t == "Polygon":
        return {"type": "Polygon", "coordinates": geom["coordinates"]}
    if t == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": geom["coordinates"]}
    return None


def bbox_rect_polygon(bbox):
    """Polygon ring from source bbox [minLon, minLat, maxLon, maxLat]."""
    minlon, minlat, maxlon, maxlat = bbox
    ring = [[minlon, minlat], [maxlon, minlat], [maxlon, maxlat], [minlon, maxlat], [minlon, minlat]]
    return {"type": "Polygon", "coordinates": [ring]}


def bbox_intersects_ro(bbox_snwe):
    """Nominatim boundingbox is [south, north, west, east] (strings)."""
    s, n, w, e = (float(x) for x in bbox_snwe)
    minlon, minlat, maxlon, maxlat = RO_BBOX
    return not (e < minlon or w > maxlon or n < minlat or s > maxlat)


def get_db():
    os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
    db = sqlite3.connect(CACHE_DB)
    db.execute("""CREATE TABLE IF NOT EXISTS geocode_cache (
        query_string   TEXT PRIMARY KEY,
        water_name     TEXT NOT NULL,
        water_type     TEXT NOT NULL,
        arebaltapeste_slug TEXT,
        result_json    TEXT,
        osm_type       TEXT,
        osm_id         TEXT,
        geometry_type  TEXT,
        geojson        TEXT,
        bbox           TEXT,
        importance     REAL,
        tier           TEXT DEFAULT 'tier2',
        source         TEXT,
        confidence     TEXT DEFAULT 'medium',
        hit_count      INTEGER DEFAULT 1,
        created_at     TEXT DEFAULT (datetime('now')),
        last_accessed  TEXT DEFAULT (datetime('now'))
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_water_name ON geocode_cache(water_name)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_slug ON geocode_cache(arebaltapeste_slug)")
    db.commit()
    return db
