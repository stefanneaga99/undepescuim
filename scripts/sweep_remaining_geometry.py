#!/usr/bin/env python3
"""SWEEP remaining waters (t_68dabead): 32 bbox-only rectangles + 147 waters
with NO geometry AND NO bbox (truly invisible, no group owner).

PART 1 — bbox-only (32):
  A. Group member whose riverGroup HAS a geometry owner -> DROP the bbox so it
     renders via the owner's course + coverage slices (one-owner-per-group,
     skill pitfall #4). The rectangle is the artifact the user reported.
  B. Name+county OSM match (river clusters + lake polygons, county-guarded).
  C. Unmatchable -> keep bbox fallback + document (task: 'Document unmatchable').

PART 2 — truly-invisible (147):
  A. Name+county OSM match (prefix-core, len>=3, county-guarded; lakes first
     for subtype 'lac' — pitfall #18c).
  B. Locality-anchored: geocode the ANPA limits_text locality (Nominatim,
     cache-first), then pick OSM clusters/lakes near that point.
  C. bbox from source data: arebaltapeste record (name+county) with bbox, else
     a small bbox around the geocoded locality point (water renders as a
     marker rectangle instead of being invisible).
  D. No source -> keep hidden + document.

Waters in a group WITH a geometry owner (159) are skipped by design — they
render via the owner's course / coverage slices (one-owner-per-group).

Usage:
  python3 scripts/sweep_remaining_geometry.py             # dry run
  python3 scripts/sweep_remaining_geometry.py --write     # apply to waters.json
  python3 scripts/sweep_remaining_geometry.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
CLUSTER_PKL = ROOT / "data" / "cache" / "osm_river_clusters.pkl"
LAKES_JSON = ROOT / "data" / "processed" / "overpass_named_lakes.json"
LAKES2_JSON = ROOT / "data" / "processed" / "overpass_named_lakes2.json"
COUNTY_DIR = ROOT / "data" / "raw" / "county_boundaries"
CACHE_DB = ROOT / "data" / "cache" / "geocode.db"
WATER_ALL_JSON = ROOT / "data" / "raw" / "overpass_water_all.json"
WATER_POLYS_JSON = ROOT / "data" / "raw" / "overpass_water_polys.json"

sys.path.insert(0, str(ROOT / "scripts"))

COUNTY_SLUG_TO_NAME = {
    "alba": "Alba", "arad": "Arad", "arges": "Argeș", "bacau": "Bacău",
    "bihor": "Bihor", "bistrita_nasaud": "Bistrița-Năsăud", "botosani": "Botoșani",
    "brasov": "Brașov", "braila": "Brăila", "buzau": "Buzău",
    "caras_severin": "Caraș-Severin", "calarasi": "Călărași", "cluj": "Cluj",
    "constanta": "Constanța", "covasna": "Covasna", "dambovita": "Dâmbovița",
    "dolj": "Dolj", "galati": "Galați", "giurgiu": "Giurgiu", "gorj": "Gorj",
    "harghita": "Harghita", "hunedoara": "Hunedoara", "ialomita": "Ialomița",
    "iasi": "Iași", "ilfov": "Ilfov", "maramures": "Maramureș",
    "mehedinti": "Mehedinți", "mures": "Mureș", "neamt": "Neamț", "olt": "Olt",
    "prahova": "Prahova", "satu_mare": "Satu Mare", "salaj": "Sălaj",
    "satu mare": "Satu Mare",
    "sibiu": "Sibiu", "suceava": "Suceava", "teleorman": "Teleorman",
    "timis": "Timiș", "tulcea": "Tulcea", "vaslui": "Vaslui",
    "valcea": "Vâlcea", "vrancea": "Vrancea", "bucuresti": "București",
}

COUNTY_SEATS = {
    "Alba": (23.57, 46.08), "Arad": (21.32, 46.18), "Argeș": (24.82, 44.93),
    "Bihor": (21.93, 47.06), "Bistrița-Năsăud": (24.50, 47.13), "Botoșani": (26.67, 47.75),
    "Brașov": (25.61, 45.65), "Brăila": (27.95, 45.27), "Buzău": (26.82, 45.15),
    "Caraș-Severin": (21.90, 45.36), "Călărași": (27.31, 44.20), "Cluj": (23.60, 46.77),
    "Constanța": (28.65, 44.17), "Covasna": (26.18, 45.85), "Dâmbovița": (25.46, 44.93),
    "Dolj": (23.87, 44.33), "Galați": (28.02, 45.44), "Giurgiu": (25.95, 43.90),
    "Gorj": (23.36, 45.04), "Harghita": (25.64, 46.36), "Hunedoara": (22.90, 45.77),
    "Ialomița": (27.83, 44.56), "Iași": (27.60, 47.16), "Maramureș": (23.89, 47.66),
    "Mehedinți": (22.87, 44.63), "Mureș": (24.56, 46.54), "Neamț": (26.38, 46.93),
    "Olt": (24.48, 44.43), "Prahova": (26.01, 44.94), "Satu Mare": (22.89, 47.79),
    "Sălaj": (23.05, 47.19), "Sibiu": (24.15, 45.80), "Suceava": (26.25, 47.65),
    "Teleorman": (25.31, 43.98), "Timiș": (21.23, 45.75), "Vâlcea": (24.37, 45.10),
    "Vaslui": (27.73, 46.64), "Vrancea": (26.81, 45.82),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa|heles teul|heles teu|heles tei)\s+"
)
INDEX_RE = re.compile(r"^\d+\s+")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def core(name: str) -> str:
    return PREFIX_RE.sub("", norm(name), count=1).strip()


def strip_index(s: str) -> str:
    return INDEX_RE.sub("", s, count=1)


def strip_article(tok: str) -> set:
    if len(tok) >= 5 and tok.endswith("ul"):
        return {tok, tok[:-2], tok[:-1]}
    if len(tok) >= 5 and tok.endswith("l") and tok[-2] in "aeiou":
        return {tok, tok[:-1]}
    if len(tok) >= 5 and tok.endswith("u") and tok[-2] not in "aeiou":
        return {tok, tok[:-1]}
    return {tok}


def name_variants(name: str) -> set:
    c = core(name)
    toks = c.split()
    if not toks:
        return set()
    out = set()
    for fv in strip_article(toks[0]):
        out.add(" ".join([fv, *toks[1:]]))
    return out


def lake_core(name: str) -> str:
    n = norm(name)
    prev = None
    while prev != n:
        prev = n
        n = PREFIX_RE.sub("", n, count=1).strip()
    n = re.sub(r"\s+cu\s+baltile\s+adiacente.*$", "", n)
    n = re.sub(r"\s+si\s+valea\s+.*$", "", n)
    n = re.sub(r"\s*\(.*?\)\s*$", "", n).strip()
    toks = n.split()
    return toks[0] if toks else n


def load_raw_waterways():
    """way_id -> {coords, bbox} for ALL waterway ways (named + unnamed) from
    the 258MB Overpass dump. Named ones duplicate the cluster index; unnamed
    ones are the pitfall-#62 candidates (a village's stream with no name tag)."""
    d = json.loads(WATER_ALL_JSON.read_text(encoding="utf-8"))
    nodes = {el["id"]: (el["lon"], el["lat"]) for el in d["elements"] if el["type"] == "node"}
    out = {}
    for el in d["elements"]:
        if el["type"] != "way":
            continue
        tags = el.get("tags") or {}
        if not tags.get("waterway"):
            continue
        pts = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if len(pts) < 2:
            continue
        lons = [p[0] for p in pts]
        lats = [p[1] for p in pts]
        out[el["id"]] = {
            "coords": pts,
            "bbox": [min(lons), min(lats), max(lons), max(lats)],
            "name": tags.get("name", ""),
            "waterway": tags.get("waterway", ""),
        }
    return out


def load_raw_polygons():
    """way_id -> {coords (closed ring), bbox} for water/wetland/reservoir
    polygons from the 235MB water-polys dump. Unnamed ones are the lake
    candidates the named index misses (Vlădești reservoir, Lățunaș)."""
    d = json.loads(WATER_POLYS_JSON.read_text(encoding="utf-8"))
    nodes = {el["id"]: (el["lon"], el["lat"]) for el in d["elements"] if el["type"] == "node"}
    out = []
    for el in d["elements"]:
        if el["type"] != "way":
            continue
        tags = el.get("tags") or {}
        pts = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if len(pts) < 4:
            continue
        lons = [p[0] for p in pts]
        lats = [p[1] for p in pts]
        bb = [min(lons), min(lats), max(lons), max(lats)]
        if (bb[2] - bb[0]) < 0.001 or (bb[3] - bb[1]) < 0.001:
            continue  # tiny pond slivers
        if (bb[2] - bb[0]) > 0.15 or (bb[3] - bb[1]) > 0.15:
            continue  # too big for a contracted pond/lake (river floodplains, whole Danube wetlands)
        out.append({
            "coords": pts,
            "bbox": bb,
            "name": tags.get("name", ""),
            "kind": tags.get("natural") or tags.get("water") or tags.get("landuse", ""),
        })
    return out


def load_county_polygons():
    polys = []
    for path in sorted(COUNTY_DIR.glob("*.json")):
        name = COUNTY_SLUG_TO_NAME.get(path.stem)
        if not name:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        g = data[0].get("geojson") if isinstance(data, list) else data.get("geojson")
        if not g:
            continue
        try:
            geom = shape(g)
        except Exception:
            continue
        polys.append((name, prep(geom), geom.bounds))
    return polys


def cluster_points(g: dict):
    coords = g["coordinates"]
    t = g.get("type")
    if t == "MultiLineString":
        return [p for part in coords for p in part]
    if t == "Polygon":
        return [p for ring in coords for p in ring]
    if t == "MultiPolygon":
        return [p for poly in coords for ring in poly for p in ring]
    return coords


def county_hits(points, polygons, county):
    cn = norm(county)
    sample = points[:: max(1, len(points) // 60)]
    counts = {}
    in_declared = 0
    for lon, lat in sample:
        pt = Point(lon, lat)
        for name, pgeom, pbbox in polygons:
            if not (pbbox[0] <= lon <= pbbox[2] and pbbox[1] <= lat <= pbbox[3]):
                continue
            if pgeom.contains(pt):
                counts[name] = counts.get(name, 0) + 1
                if name == county:
                    in_declared += 1
                break
    total = sum(counts.values())
    majority = max(counts, key=lambda k: (counts[k], k)) if counts else None
    return in_declared, majority, total


def geom_bbox(g: dict):
    pts = cluster_points(g)
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


def point_in_county(point, polygons, county, buffer_deg=0.05):
    """True when the point is inside (or within a small buffer of) the county."""
    lon, lat = point
    target = None
    for name, pgeom, pbbox in polygons:
        if name != county:
            continue
        target = (pgeom, pbbox)
        break
    if not target:
        return False
    pgeom, pbbox = target
    if pgeom.contains(Point(lon, lat)):
        return True
    # buffer check: near the border (river-course locality points sit on the ring)
    bb = [pbbox[0] - buffer_deg, pbbox[1] - buffer_deg, pbbox[2] + buffer_deg, pbbox[3] + buffer_deg]
    return bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]


def seat_dist(declared, bb):
    seat = COUNTY_SEATS.get(declared)
    if not seat or not bb:
        return None
    cpt = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
    return math.hypot(cpt[0] - seat[0], cpt[1] - seat[1])


def pick_best(candidates, declared, polygons, prefer_lake=False):
    scored = []
    for src, name, geom, bb in candidates:
        pts = cluster_points(geom)
        if not pts or not bb:
            continue
        in_dec, majority, total = county_hits(pts, polygons, declared)
        if in_dec == 0 and majority != declared:
            continue
        sd = seat_dist(declared, bb) or 99.0
        bonus = 100.0 if prefer_lake and src == "lake" else 0.0
        score = 1000.0 * in_dec + bonus + (10.0 if majority == declared else 0.0) - sd
        scored.append((score, in_dec, majority, sd, src, name, geom, bb))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


def order_linestring(geom):
    from _mapping_common import order_course_linestring
    return order_course_linestring(geom)


# --- geocode cache ----------------------------------------------------------
def cache_get(db, query):
    row = db.execute(
        "SELECT result_json, osm_type, osm_id, geojson, bbox, importance, tier, source, confidence, hit_count "
        "FROM geocode_cache WHERE query_string=?", (query,)
    ).fetchone()
    if row:
        db.execute(
            "UPDATE geocode_cache SET hit_count=hit_count+1, last_accessed=datetime('now') WHERE query_string=?",
            (query,),
        )
        db.commit()
    return row


def cache_put(db, query, result, water_name="", water_type="ape", slug=""):
    rj = None
    osm_type = osm_id = geometry_type = geojson = bbox = importance = None
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
        (query, water_name, water_type, slug, rj,
         osm_type, osm_id, geometry_type, geojson, bbox, importance, tier, source, confidence),
    )
    db.commit()


def geocode_locality(query, db, water_name="", water_type="ape", slug=""):
    """Cache-first Nominatim /search for a locality. Returns (lon, lat) or None."""
    row = cache_get(db, query)
    if row:
        res = json.loads(row[0]) if row[0] else None
        if res:
            return float(res["lon"]), float(res["lat"])
        return None
    from geocode_common import nominatim_search, rate_limit
    try:
        res = nominatim_search(query, countrycodes="ro", limit=3)
        rate_limit()
    except Exception as e:
        print(f"    [geocode] {query} error: {e}")
        return None
    if res:
        ranked = sorted(res, key=lambda r: 0 if r.get("type") in ("administrative", "village", "town", "city") else 1)
        best = ranked[0]
        best["tier"] = "tier2"
        cache_put(db, query, best, water_name, water_type, slug)
        return float(best["lon"]), float(best["lat"])
    cache_put(db, query, None, water_name, water_type, slug)
    return None


# Waters whose name match attaches a course that spans MULTIPLE contracts /
# counties and the contract is only a SECTOR of it — a full-course attach
# would be wrong-sector (pitfall #20 class). Keep them on the locality-bbox
# path (or hidden) and document; a proper sector split is a separate fix.
SKIP_FULL_ATTACH = {
    "romsilva-bihor-valea-draganului",  # Drăgan upper 13km (Izvorul-Sebișel); full course is 40km+ Cluj
}

# Waters whose subtype/name would attach a WRONG feature class (a river
# cluster to a lake water, pitfall #18c). Keep bbox + document.
KEEP_BBOX_PART2 = {
    "4fg24m45",  # Lacul Pojorâta (Iezer) Suceava — only a Pojorâta RIVER cluster exists, no lake polygon
    "anpa-anpa-0134",  # Râul Colibița superioară — no named OSM river; only the Colibița LAKE polygon + dam
    "anpa-anpa-0135",  # Râul Colibița inferioară — same: no river course in OSM
    "romsilva-alba-fenesasa",  # Râul Fenesasa — Feneș clusters are in Cluj/Olt-valley, no 25km Alba course
}

GENERIC_LOCALITY = {
    "artificial", "natural", "izvoare", "izvorul", "izvoarele", "zona",
    "zona de acumulare", "acumulare", "baraj", "intregul", "pe raza",
    "sector", "sectoare", "aval", "amonte", "confluenta", "varsarea",
    "de la izvoare", "de la izvoarele", "izvoarele", "izvoare lor",
    "mal drept", "mal stang", "toata lungimea", "intre loc", "paralel",
}


def extract_locality(limits_text: str) -> str | None:
    """First geocodable locality from an ANPA limits_text.

    Splits on any dash/em-dash and takes the first non-generic, non-river
    part (e.g. 'Runcu - Rogojel' -> 'Runcu'; 'izvoare – conf. cu Râul Olt'
    -> None because the only usable token is a river name).
    """
    if not limits_text:
        return None
    lt = limits_text.strip()
    if not lt or lt.lower().startswith("jude") or lt.lower() in ("natural",):
        return None
    parts = re.split(r"\s*[–—-]\s*|\s*[,;]\s*", lt)
    for p in parts:
        p = p.strip(" ,;–-")
        if not p or len(p) < 2:
            continue
        low = p.lower()
        if low in GENERIC_LOCALITY:
            continue
        if re.match(r"^(conf\.?|confluen|varsare|vărsare)", low):
            continue
        if re.match(r"^(raul|paraul|valea|râul|pârâul|rau|parau|vale)\s", low):
            continue
        if re.match(r"^(pod|drum|drumul)\s", low):
            # 'pod Groșii' / 'Drum N.I.' — take the noun after the bridge
            rest = re.sub(r"^(pod|drum|drumul)\s+", "", p).strip()
            if rest and len(rest) >= 2 and rest.lower() not in GENERIC_LOCALITY:
                return rest
            continue
        # strip leading connector words: 'intrare Zlatna' -> 'Zlatna',
        # 'de la Pietroasa' -> 'Pietroasa', 'sat Fenes' -> 'Fenes',
        # 'localitatea X' / 'zona X' / 'loc. X' -> 'X'
        p = re.sub(
            r"^(intrare|de la|la|din|sat|satul|comuna|com\.|localitatea|zona|loc\.|pe raza|malul|in zona|pana la|pana in|amonte de|aval de)\s+",
            "", p, flags=re.I,
        ).strip(" ,;–-")
        if not p or len(p) < 2:
            continue
        low2 = p.lower()
        if low2 in GENERIC_LOCALITY:
            continue
        if re.match(r"^(conf\.?|confluen|varsare|vărsare)", low2):
            continue
        return p
    return None


def load_areba_index():
    idx = {}
    for l in open(ROOT / "data" / "processed" / "arebaltapeste_waters.jsonl"):
        r = json.loads(l)
        key = (norm(r["water_name"]), norm(r.get("county") or ""))
        idx.setdefault(key, []).append(r)
    return idx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply changes to waters.json")
    ap.add_argument("--json", type=str, help="write report JSON to this path")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    polygons = load_county_polygons()
    with open(CLUSTER_PKL, "rb") as f:
        clusters, _cell = pickle.load(f)
    lakes = json.loads(LAKES_JSON.read_text(encoding="utf-8"))
    lakes2 = json.loads(LAKES2_JSON.read_text(encoding="utf-8"))
    all_lakes = lakes + lakes2
    print(f"[sweep] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

    by_norm = defaultdict(list)
    for cl in clusters:
        by_norm[cl["norm"]].append(cl)
    lakes_by_norm = defaultdict(list)
    for l in all_lakes:
        lakes_by_norm[l.get("norm") or ""].append(l)
    by_group = defaultdict(list)
    for w in waters:
        if w.get("riverGroup"):
            by_group[w["riverGroup"]].append(w)
    areba_idx = load_areba_index()

    db = sqlite3.connect(CACHE_DB)
    db.execute("PRAGMA busy_timeout = 5000")
    print("[sweep] loading raw waterways (258MB dump)...", flush=True)
    raw_ways = load_raw_waterways()
    print(f"[sweep] {len(raw_ways)} waterway ways loaded", flush=True)
    print("[sweep] loading raw polygons (235MB dump)...", flush=True)
    raw_polys = load_raw_polygons()
    print(f"[sweep] {len(raw_polys)} polygon rings loaded", flush=True)

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    def already_swept(w):
        sd = w.get("source_detail") or ""
        return sd.startswith("sweep_remaining:")

    bbox_only = [w for w in waters if w.get("bbox") and not w.get("geometry") and not already_swept(w)]
    neither = [w for w in waters if not w.get("bbox") and not w.get("geometry") and not already_swept(w)]
    truly = []
    for w in neither:
        g = w.get("riverGroup")
        owners = [m for m in by_group.get(g, []) if m.get("geometry")] if g else []
        if not owners:
            truly.append(w)
    print(f"[sweep] target: {len(bbox_only)} bbox-only + {len(truly)} truly-invisible")

    report = {"part1_bbox_only": [], "part2_truly": [], "group_shared_skipped": 0, "double_owner_groups": []}
    changed = []
    handled = set()

    def collect(name, wcore, wlake, min_len=4):
        """[(kind, name, geom, bbox)] river clusters + lakes for a water."""
        variants = name_variants(name)
        cands = []
        seen = set()

        def add_cluster(key):
            for cl in by_norm.get(key, []):
                if id(cl) in seen:
                    continue
                seen.add(id(cl))
                bb = cl.get("bbox")
                cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"],
                              list(bb) if bb else None))

        def add_lake(key):
            for l in lakes_by_norm.get(key, []):
                if id(l) in seen:
                    continue
                seen.add(id(l))
                cands.append(("lake", l.get("name") or "?", l["geom"], geom_bbox(l["geom"])))

        keys = set(variants)
        for k in keys:
            add_cluster(k)
        for nk, cls_ in by_norm.items():
            if nk in keys:
                continue
            ck = core(nk)
            if len(ck) >= min_len and (ck == wcore or ck.startswith(wcore) or wcore.startswith(ck)):
                for cl in cls_:
                    if id(cl) in seen:
                        continue
                    seen.add(id(cl))
                    bb = cl.get("bbox")
                    cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"],
                                  list(bb) if bb else None))
        for k in keys:
            add_lake(k)
        for nk, ls_ in lakes_by_norm.items():
            if nk in keys:
                continue
            if lake_core(nk) == wlake and len(nk) >= 4:
                for l in ls_:
                    if id(l) in seen:
                        continue
                    seen.add(id(l))
                    cands.append(("lake", l.get("name") or "?", l["geom"], geom_bbox(l["geom"])))
        return cands

    def collect_near(point, wcore, wlake, span=0.02):
        """Clusters/lakes whose bbox overlaps a small window around a point."""
        lon, lat = point
        win = [lon - span, lat - span, lon + span, lat + span]
        cands = []
        seen = set()

        def add_cluster(key):
            for cl in by_norm.get(key, []):
                if id(cl) in seen:
                    continue
                seen.add(id(cl))
                bb = cl.get("bbox")
                cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"],
                              list(bb) if bb else None))

        def add_lake(key):
            for l in lakes_by_norm.get(key, []):
                if id(l) in seen:
                    continue
                seen.add(id(l))
                cands.append(("lake", l.get("name") or "?", l["geom"], geom_bbox(l["geom"])))

        keys = {wcore, wlake}
        for k in keys:
            add_cluster(k)
        for nk, cls_ in by_norm.items():
            if nk in keys:
                continue
            ck = core(nk)
            if len(ck) >= 4 and (ck == wcore or ck.startswith(wcore) or wcore.startswith(ck)):
                for cl in cls_:
                    if id(cl) in seen:
                        continue
                    seen.add(id(cl))
                    bb = cl.get("bbox")
                    if bb and not (bb[2] < win[0] or bb[0] > win[2] or bb[3] < win[1] or bb[1] > win[3]):
                        cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"],
                                      list(bb) if bb else None))
        for k in keys:
            add_lake(k)
        for nk, ls_ in lakes_by_norm.items():
            if nk in keys:
                continue
            if lake_core(nk) == wlake and len(nk) >= 4:
                for l in ls_:
                    if id(l) in seen:
                        continue
                    seen.add(id(l))
                    bb = geom_bbox(l["geom"])
                    if bb and not (bb[2] < win[0] or bb[0] > win[2] or bb[3] < win[1] or bb[1] > win[3]):
                        cands.append(("lake", l.get("name") or "?", l["geom"], bb))
        return cands

    def collect_raw_ways_near(point, span=0.02):
        """Unnamed waterway ways whose bbox overlaps a small window around the
        point — the pitfall-#62 candidate for rivers whose real OSM course has
        no name tag (Botiza, Beliu, Coza...). Chained into one LineString."""
        if not raw_ways:
            return []
        lon, lat = point
        win = [lon - span, lat - span, lon + span, lat + span]
        parts = []
        names = []
        for wid, w in raw_ways.items():
            bb = w["bbox"]
            if bb[2] < win[0] or bb[0] > win[2] or bb[3] < win[1] or bb[1] > win[3]:
                continue
            if w["name"]:
                continue  # named ways are handled by the cluster index
            parts.append(list(w["coords"]))
        if not parts:
            return []
        from sweep_multiway_rivers import chain_parts, flatten
        chain = chain_parts(parts)
        if not chain:
            return []
        total_pts = sum(len(p) for p in chain)
        if total_pts < 8:
            return []  # tiny sliver, not a course
        geom = flatten(chain)
        return [("river", "unnamed-way(s)", geom, geom_bbox(geom))]

    def collect_raw_polygons_near(point, span=0.02):
        """Unnamed water/wetland/reservoir polygons overlapping a window around
        the point — the pitfall-#62 lake candidate for reservoirs the named
        index misses (Vlădești, Lățunaș). Returns Polygon geometries."""
        if not raw_polys:
            return []
        lon, lat = point
        win = [lon - span, lat - span, lon + span, lat + span]
        cands = []
        seen = set()
        for p in raw_polys:
            bb = p["bbox"]
            if bb[2] < win[0] or bb[0] > win[2] or bb[3] < win[1] or bb[1] > win[3]:
                continue
            if p["name"]:
                continue  # named polygons handled by the lake index
            if id(p) in seen:
                continue
            seen.add(id(p))
            ring = list(p["coords"]) + [list(p["coords"][0])]
            cands.append(("lake", f"unnamed-{p['kind']}", {"type": "Polygon", "coordinates": [ring]}, list(bb)))
        return cands

    def attach(w, out_geom, src, cname, in_dec, majority):
        w["geometry"] = out_geom
        bb = geom_bbox(out_geom)
        w["bbox"] = [round(v, 5) for v in bb] if bb else None
        w["source_detail"] = "sweep_remaining:" + src
        w["geometryByCounty"] = {}
        w.pop("hidden", None)
        changed.append(w)
        return {
            "slug": w["slug"], "name": w["name"], "judet": w["judet"], "source": src,
            "osmc": cname, "in_county_pts": in_dec, "majority": majority,
        }

    # ---- PART 1: bbox-only ----------------------------------------------
    for w in sorted(bbox_only, key=lambda x: (x["judet"], x["name"])):
        slug = w["slug"]
        declared = w["judet"]
        name = w["name"]
        wcore = core(name)
        wlake = lake_core(name)
        if slug in handled:
            continue

        g = w.get("riverGroup")
        owners = [m for m in by_group.get(g, []) if m.get("geometry")] if g else []
        if owners:
            # A. group member with an owner — rectangle is the artifact
            old_bb = w.get("bbox")
            w["bbox"] = None
            w["geometryByCounty"] = {}
            report["part1_bbox_only"].append({
                "slug": slug, "name": name, "judet": declared, "action": "bbox-dropped-group-shared",
                "group": g, "old_bbox": old_bb,
                "note": f"group '{g}' has {len(owners)} geometry owner(s); renders via owner course",
            })
            print(f"  DROP  {declared:18s} {name[:42]:44s} (group {g}, {len(owners)} owner)")
            changed.append(w)
            continue

        if slug in KEEP_BBOX_PART2:
            report["part1_bbox_only"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                "note": "KEEP_BBOX_PART2: would attach wrong feature class (river cluster to a lake)",
            })
            print(f"  KEEP  {declared:18s} {name[:42]:44s} (KEEP_BBOX_PART2 wrong feature class)")
            continue

        cands = collect(name, wcore, wlake, min_len=3)
        best = pick_best(cands, declared, polygons, prefer_lake=(w.get("subtype") == "lac"))
        if best:
            score, in_dec, majority, sd, src, cname, geom, bb = best
            out_geom = geom if src == "lake" else order_linestring(geom)
            entry = attach(w, out_geom, src, cname, in_dec, majority)
            report["part1_bbox_only"].append({"slug": slug, "name": name, "judet": declared,
                                              "action": "matched", **entry})
            print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} (in={in_dec} maj={majority})")
        else:
            # raw unnamed polygon near the bbox center (lakes the named index misses)
            if w.get("subtype") == "lac" and w.get("bbox"):
                bbc = [(w["bbox"][0] + w["bbox"][2]) / 2, (w["bbox"][1] + w["bbox"][3]) / 2]
                poly_cands = collect_raw_polygons_near(bbc, span=0.02)
                best = pick_best(poly_cands, declared, polygons, prefer_lake=True) if poly_cands else None
                if best:
                    score, in_dec, majority, sd, src, cname, geom, bb = best
                    entry = attach(w, geom, src, cname, in_dec, majority)
                    report["part1_bbox_only"].append({"slug": slug, "name": name, "judet": declared,
                                                      "action": "matched-raw-poly", **entry})
                    print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} (in={in_dec} maj={majority})")
                    continue
            report["part1_bbox_only"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                "candidates": [{"kind": c[0], "name": c[1], "bb": c[3]} for c in cands[:4]],
                "note": "no in-county candidate; keep bbox fallback",
            })
            print(f"  KEEP  {declared:18s} {name[:42]:44s} (no in-county candidate)")

    # ---- PART 2: truly-invisible -----------------------------------------
    for w in sorted(truly, key=lambda x: (x["judet"], x["name"])):
        slug = w["slug"]
        declared = w["judet"]
        name = w["name"]
        wcore = core(name)
        wlake = lake_core(name)
        if slug in handled:
            continue

        source_row = None
        rid = slug[len("anpa-"):] if slug.startswith("anpa-anpa-") else slug
        for l in open(ROOT / "data" / "processed" / "anpa_waters.jsonl"):
            r = json.loads(l)
            if r["id"] == rid:
                source_row = r
                break
        if source_row is None:
            for l in open(ROOT / "data" / "processed" / "anpa_romsilva_waters.jsonl"):
                r = json.loads(l)
                if r["id"] == rid:
                    source_row = r
                    break
        limits = (source_row or {}).get("limits_text") or w.get("limite") or ""

        # A. name match
        skip_geom = slug in KEEP_BBOX_PART2
        if skip_geom:
            report["part2_truly"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-hidden",
                "note": "KEEP_BBOX_PART2: would attach wrong feature class (river cluster to a lake)",
            })
            print(f"  SKIP  {declared:18s} {name[:42]:44s} (KEEP_BBOX_PART2 wrong feature class)")
        elif slug in SKIP_FULL_ATTACH:
            report["part2_truly"].append({
                "slug": slug, "name": name, "judet": declared, "action": "skip-full-attach",
                "note": "name matches a multi-contract course; contract is only a sector (SKIP_FULL_ATTACH)",
            })
            print(f"  SKIP  {declared:18s} {name[:42]:44s} (sector-only contract, skip full attach)")
            continue
        else:
            cands = collect(name, wcore, wlake, min_len=3)
            best = pick_best(cands, declared, polygons, prefer_lake=(w.get("subtype") == "lac"))
            if best:
                score, in_dec, majority, sd, src, cname, geom, bb = best
                out_geom = geom if src == "lake" else order_linestring(geom)
                entry = attach(w, out_geom, src, cname, in_dec, majority)
                report["part2_truly"].append({"slug": slug, "name": name, "judet": declared,
                                              "action": "matched", **entry})
                print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} (in={in_dec} maj={majority})")
                continue

        # B. locality-anchored: geocode limits_text -> point -> near match
        # (skipped for KEEP_BBOX_PART2 — those must not attach ANY geometry)
        point = None
        locality = None
        locality_cands = []
        if not skip_geom:
            # Try, in order: (1) the cleaned limits locality, (2) each dash-part
            # of the limits, (3) the water's own name (many Romsilva/ANPA rivers
            # ARE the village: Beliu, Botiza, Zimbru, Toc, Stejar...). Use the
            # first point that lands in the declared county.
            locality_cands = []
            first = extract_locality(limits)
            if first:
                locality_cands.append(first)
            for part in re.split(r"\s*[–—-]\s*|\s*[,;]\s*", limits):
                p = part.strip(" ,;–-")
                if p and len(p) >= 2 and p != first:
                    locality_cands.append(p)
            # water-name-as-locality: strip river prefixes but keep the core
            nm_core = core(name)
            if nm_core and nm_core != first:
                locality_cands.append(nm_core)
            for cand in locality_cands:
                if point:
                    break
                p = geocode_locality(f"{cand}, {declared}", db, water_name=name,
                                     water_type=w.get("subtype") or "ape", slug=slug)
                if p and point_in_county(p, polygons, declared):
                    point, locality = p, cand
            near_cands = collect_near(point, wcore, wlake, span=0.02) if point else []
            best = pick_best(near_cands, declared, polygons, prefer_lake=(w.get("subtype") == "lac")) if point else None
            if best:
                score, in_dec, majority, sd, src, cname, geom, bb = best
                out_geom = geom if src == "lake" else order_linestring(geom)
                entry = attach(w, out_geom, src, cname, in_dec, majority)
                report["part2_truly"].append({"slug": slug, "name": name, "judet": declared,
                                              "action": "matched-locality", "locality": locality,
                                              "point": point, **entry})
                print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} near '{locality}' (in={in_dec})")
                continue

            # B2. unnamed raw ways near the locality point (pitfall #62): a river
            # whose real OSM course has no name tag (village stream) — chain the
            # unnamed waterway ways in a small window around the point. LAKES skip
            # this (a pond must not get a stream course — pitfall #18c).
            raw_cands = collect_raw_ways_near(point, span=0.02) if point and w.get("subtype") != "lac" else []
            best = pick_best(raw_cands, declared, polygons) if raw_cands else None
            if best:
                score, in_dec, majority, sd, src, cname, geom, bb = best
                out_geom = order_linestring(geom)
                entry = attach(w, out_geom, src, cname, in_dec, majority)
                report["part2_truly"].append({"slug": slug, "name": name, "judet": declared,
                                              "action": "matched-raw", "locality": locality,
                                              "point": point, **entry})
                print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} near '{locality}' (in={in_dec})")
                continue

            # B3. unnamed raw polygons near the locality point (lakes/reservoirs
            # the named index misses — Vlădești, Lățunaș).
            if w.get("subtype") == "lac" and point:
                poly_cands = collect_raw_polygons_near(point, span=0.02)
                best = pick_best(poly_cands, declared, polygons, prefer_lake=True) if poly_cands else None
                if best:
                    score, in_dec, majority, sd, src, cname, geom, bb = best
                    entry = attach(w, geom, src, cname, in_dec, majority)
                    report["part2_truly"].append({"slug": slug, "name": name, "judet": declared,
                                                  "action": "matched-raw-poly", "locality": locality,
                                                  "point": point, **entry})
                    print(f"  FIX   {declared:18s} {name[:42]:44s} <- [{src}] {cname} near '{locality}' (in={in_dec})")
                    continue

        # C. bbox from source data
        areba_hits = areba_idx.get((norm(name), norm(declared)), [])
        if areba_hits and areba_hits[0].get("bbox"):
            bb = areba_hits[0]["bbox"]
            w["bbox"] = [round(v, 6) for v in bb]
            w["coordinates"] = [areba_hits[0]["coordinates_lon"], areba_hits[0]["coordinates_lat"]]
            w["source_detail"] = "sweep_remaining:areba_bbox"
            w["geometryByCounty"] = {}
            w.pop("hidden", None)
            report["part2_truly"].append({
                "slug": slug, "name": name, "judet": declared, "action": "bbox-added",
                "source": "areba", "bbox": w["bbox"],
                "note": f"areba record '{areba_hits[0]['water_name']}'",
            })
            print(f"  BBOX  {declared:18s} {name[:42]:44s} <- areba bbox {[round(v,2) for v in bb]}")
            changed.append(w)
            continue

        if point:
            pad = 0.004
            bb = [point[0] - pad, point[1] - pad, point[0] + pad, point[1] + pad]
            w["bbox"] = [round(v, 6) for v in bb]
            w["coordinates"] = [round(point[0], 6), round(point[1], 6)]
            w["source_detail"] = "sweep_remaining:locality_bbox"
            w["geometryByCounty"] = {}
            w.pop("hidden", None)
            report["part2_truly"].append({
                "slug": slug, "name": name, "judet": declared, "action": "bbox-added",
                "source": "locality", "locality": locality, "point": point, "bbox": w["bbox"],
            })
            print(f"  BBOX  {declared:18s} {name[:42]:44s} <- locality '{locality}' {tuple(round(v,3) for v in point)}")
            changed.append(w)
            continue

        # D. keep hidden + document
        report["part2_truly"].append({
            "slug": slug, "name": name, "judet": declared, "action": "hidden",
            "limits": limits, "locality_tried": locality,
            "locality_cands": locality_cands[:6],
            "note": "no OSM match, no areba record, no geocodable locality",
        })
        print(f"  HIDE  {declared:18s} {name[:42]:44s} (no source to place it)")

    # ---- diagnostics ------------------------------------------------------
    for g, members in sorted(by_group.items()):
        owners = [m for m in members if m.get("geometry")]
        if len(owners) > 1:
            report["double_owner_groups"].append({
                "group": g,
                "owners": [{"slug": m["slug"], "name": m["name"], "geom_type": m["geometry"].get("type")} for m in owners],
                "members": [m["slug"] for m in members],
            })
    report["group_shared_skipped"] = sum(
        1 for w in neither
        if w.get("riverGroup") and any(m.get("geometry") for m in by_group.get(w["riverGroup"], []))
    )

    n1 = len(report["part1_bbox_only"])
    n2 = len(report["part2_truly"])
    fixed1 = sum(1 for r in report["part1_bbox_only"] if r.get("action") in ("matched", "bbox-dropped-group-shared"))
    fixed2 = sum(1 for r in report["part2_truly"] if r.get("action", "").startswith("matched"))
    bbox2 = sum(1 for r in report["part2_truly"] if r.get("action") == "bbox-added")
    hidden2 = sum(1 for r in report["part2_truly"] if r.get("action") == "hidden")
    print(f"\n[sweep] part1: {fixed1}/{n1} fixed (matched or bbox-dropped), {n1 - fixed1} keep-bbox")
    print(f"[sweep] part2: {fixed2} matched, {bbox2} bbox-added, {hidden2} hidden, "
          f"{n2 - fixed2 - bbox2 - hidden2} other")
    print(f"[sweep] group-shared skipped: {report['group_shared_skipped']}, double-owner groups: {len(report['double_owner_groups'])}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        with_bbox = sum(1 for x in waters if x.get("bbox"))
        neither_now = sum(1 for x in waters if not x.get("geometry") and not x.get("bbox"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} geom, {with_bbox} bbox, {neither_now} neither")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
