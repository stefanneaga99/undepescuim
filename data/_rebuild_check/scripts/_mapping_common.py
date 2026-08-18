#!/usr/bin/env python3
"""Shared helpers for Bistrița-basin + full-sweep river mapping (t_66b48ee0).

Reuses the conservative matcher from audit_missing_rivers.py and adds:
  - pick_cluster(): choose the right OSM cluster among same-name ones by
    county-centroid proximity (the Bistrița/Bistra, Cerna, Crasna, Sebeș
    name collisions).
  - ordered_fractions(): upstream→mouth cumulative length fractions of a
    MultiLineString (PCA part ordering, mirrors WaterFeatureLayer.orderParts)
    so sectorStart/sectorEnd can be computed from official km.
  - assoc_slug(): canonical association slug for a new water.
  - geom_bbox / merge_geoms / set_geometry helpers.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"

syspath = str(ROOT / "scripts")
if syspath not in __import__("sys").path:
    __import__("sys").path.insert(0, syspath)

from audit_missing_rivers import (  # noqa: E402
    build_county_centroids,
    county_penalty_for,
    load_osm_index,
    make_cluster_geoms,
    norm,
    core,
)


def load_fe():
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    return waters, assocs


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")


# Canonical county names as shown in the FE county filter (t_c5bc15f9).
# Keyed by fully-normalized alnum form so ANY source spelling — case
# ('BACĂU'), separators ('Bistrița - Năsăud' vs 'Bistrița-Năsăud'),
# diacritics — resolves to exactly one name. Must cover all 42 counties
# (mirrors fetch_all_county_boundaries.COUNTIES).
CANONICAL_COUNTIES = {
    "alba": "Alba", "arad": "Arad", "arges": "Argeș", "bacau": "Bacău",
    "bihor": "Bihor", "bistritanasaud": "Bistrița-Năsăud", "botosani": "Botoșani",
    "brasov": "Brașov", "braila": "Brăila", "bucuresti": "București",
    "buzau": "Buzău", "carasseverin": "Caraș-Severin", "calarasi": "Călărași",
    "cluj": "Cluj", "constanta": "Constanța", "covasna": "Covasna",
    "dambovita": "Dâmbovița", "dolj": "Dolj", "galati": "Galați",
    "giurgiu": "Giurgiu", "gorj": "Gorj", "harghita": "Harghita",
    "hunedoara": "Hunedoara", "ialomita": "Ialomița", "iasi": "Iași",
    "ilfov": "Ilfov", "maramures": "Maramureș", "mehedinti": "Mehedinți",
    "mures": "Mureș", "neamt": "Neamț", "olt": "Olt", "prahova": "Prahova",
    "satumare": "Satu Mare", "salaj": "Sălaj", "sibiu": "Sibiu",
    "suceava": "Suceava", "teleorman": "Teleorman", "timis": "Timiș",
    "tulcea": "Tulcea", "valcea": "Vâlcea", "vaslui": "Vaslui",
    "vrancea": "Vrancea",
}


def _county_key(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def canonical_county(s: str) -> str:
    """Map ANY county spelling to the canonical FE name.

    'BISTRIȚA - NĂSĂUD' / 'Bistrița - Năsăud' / 'Bistrița-Năsăud' /
    'Bistrita-Nasaud' all resolve to 'Bistrița-Năsăud', so the county
    filter shows exactly one chip (t_c5bc15f9).
    """
    if not s:
        return s
    return CANONICAL_COUNTIES.get(_county_key(s), s.strip().title())


def assoc_slug(name: str, waters: list[dict], assocs: list[dict]) -> str:
    """Canonical FE association slug for an association NAME."""
    for a in assocs:
        if a["name"] == name:
            return a["slug"]
    for a in assocs:
        if (a["name"] or "").strip() == (name or "").strip():
            return a["slug"]
    counts = Counter(
        (w.get("asociatie") or {}).get("slug")
        for w in waters
        if (w.get("asociatie") or {}).get("name", "").strip().lower() == (name or "").strip().lower()
    )
    if counts:
        return str(counts.most_common(1)[0][0])
    return slugify(name or "")


def geom_bbox(g: dict | None):
    if not g:
        return None
    coords = g["coordinates"] if g["type"] == "LineString" else [
        p for part in g["coordinates"] for p in part
    ]
    if not coords:
        return None
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return [round(min(lons), 6), round(min(lats), 6), round(max(lons), 6), round(max(lats), 6)]


def merge_geoms(geoms: list[dict]) -> dict:
    """Merge several LineString/MultiLineString into one MultiLineString."""
    parts: list[list] = []
    for g in geoms:
        if not g:
            continue
        if g["type"] == "LineString":
            parts.append(list(g["coordinates"]))
        else:
            parts.extend(list(p) for p in g["coordinates"])
    if not parts:
        return {"type": "LineString", "coordinates": []}
    if len(parts) == 1:
        return {"type": "LineString", "coordinates": parts[0]}
    return {"type": "MultiLineString", "coordinates": parts}


def set_geometry(water: dict, geom: dict | None) -> None:
    """Attach geometry + bbox to a water (bbox None for empty geoms)."""
    if geom is None:
        return
    water["geometry"] = geom
    bb = geom_bbox(geom)
    if bb and (bb[2] - bb[0]) > 1e-9 and (bb[3] - bb[1]) > 1e-9:
        water["bbox"] = bb


def build_osm_index():
    """name_index + {norm_name: [cluster geoms]} for matching."""
    name_index, geoms = load_osm_index()
    osm_geo_by_norm: dict[str, list[dict]] = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_geo_by_norm[n] = gs
    return osm_geo_by_norm


def pick_cluster(targets: list[str], county: str, osm_geo_by_norm: dict,
                 county_centroids: dict) -> tuple[dict | None, str, float]:
    """Best OSM cluster geometry for targets (norm names), scored by county
    proximity so same-name rivers in different counties resolve correctly.

    Returns (geometry, cluster_name, score).
    """
    ccent = county_centroids.get(county) if county else None
    best: dict | None = None
    best_name: str = ""
    best_score = -1.0
    for t in targets:
        for geom in osm_geo_by_norm.get(t, []):
            bb = geom_bbox(geom)
            if not bb:
                continue
            score = 1.0 - county_penalty_for(geom, ccent)
            if score > best_score:
                best, best_name, best_score = geom, t, score
    return best, best_name, best_score


def ordered_parts(geom: dict) -> list[list[tuple[float, float]]]:
    """Order MultiLineString parts source→mouth (mirrors FE orderParts)."""
    parts = (
        [list(p) for p in geom["coordinates"]]
        if geom["type"] == "MultiLineString"
        else [list(geom["coordinates"])]
    )
    if len(parts) <= 1:
        return parts
    mids = [p[len(p) // 2] for p in parts]
    mx = sum(m[0] for m in mids) / len(mids)
    my = sum(m[1] for m in mids) / len(mids)
    cxx = cyy = cxy = 0.0
    for m in mids:
        cxx += (m[0] - mx) ** 2
        cyy += (m[1] - my) ** 2
        cxy += (m[0] - mx) * (m[1] - my)
    theta = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    vx, vy = math.cos(theta), math.sin(theta)
    scored = sorted(
        parts,
        key=lambda p: ((p[len(p) // 2][0] - mx) * vx + (p[len(p) // 2][1] - my) * vy),
    )
    half = max(1, len(scored) // 2)
    lat_first = sum(p[len(p) // 2][1] for p in scored[:half]) / half
    lat_last = sum(p[len(p) // 2][1] for p in scored[-half:]) / half
    return list(reversed(scored)) if lat_first < lat_last else scored


def order_course_linestring(geom: dict) -> dict:
    """Return the course as a SINGLE LineString with coordinates in source→mouth
    order.

    Romanian rivers flow predominantly southward, so each part is oriented with
    its higher-latitude end first, and parts are chained by descending midpoint
    latitude. Storing ONE ordered LineString sidesteps the FE's PCA part
    re-ordering (orderParts no-ops on a single part), so fractionAtPoint /
    click-resolution walk the course monotonically — required for the winding
    Bistrița, whose fragmented ways PCA scrambles.
    """
    parts = (
        [list(p) for p in geom["coordinates"]]
        if geom["type"] == "MultiLineString"
        else [list(geom["coordinates"])]
    )
    # Dedupe parts whose first+last endpoints match exactly (OSM often maps the
    # same river way twice, e.g. the Bistrița Iacobeni→Bicaz stretch appears
    # twice — duplicated parts inflate length and skew source→mouth fractions).
    seen_endpoints: set[tuple] = set()
    unique_parts = []
    for p in parts:
        if not p:
            continue
        ep = (tuple(p[0]), tuple(p[-1]))
        if ep in seen_endpoints:
            continue
        seen_endpoints.add(ep)
        unique_parts.append(p)
    parts = unique_parts

    oriented = []
    for p in parts:
        if len(p) >= 2 and p[0][1] < p[-1][1]:
            p = list(reversed(p))
        oriented.append(p)
    oriented.sort(key=lambda p: p[len(p) // 2][1], reverse=True)
    out: list[tuple[float, float]] = []
    for p in oriented:
        if not p:
            continue
        if out and out[-1] == p[0]:
            out.extend(p[1:])
        else:
            out.extend(p)
    if not out:
        return {"type": "LineString", "coordinates": []}
    return {"type": "LineString", "coordinates": out}


def haversine_km(a, b) -> float:
    R = 6371.0
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def ordered_fractions(geom: dict) -> list[tuple[float, float, float, float]]:
    """Cumulative source→mouth fractions per ordered part.

    Returns [(part_frac_start, part_frac_end, lon_start, lat_start), ...]
    so a km-based sector [cum0, cum1] maps to fractions via total length.
    """
    parts = ordered_parts(geom)
    lengths = []
    total = 0.0
    for p in parts:
        L = sum(haversine_km(p[i - 1], p[i]) for i in range(1, len(p)))
        lengths.append(L)
        total += L
    if total <= 0:
        return []
    out = []
    walked = 0.0
    for p, L in zip(parts, lengths):
        out.append((walked / total, (walked + L) / total, p[0][0], p[0][1]))
        walked += L
    return out


def km_to_frac(geom: dict, km_from_source: float) -> float:
    """Fraction of the course at km_from_source km from the source (via ordered
    cumulative length). Returns 0..1 (clamped)."""
    parts = ordered_parts(geom)
    lengths = [sum(haversine_km(p[i - 1], p[i]) for i in range(1, len(p))) for p in parts]
    total = sum(lengths)
    if total <= 0:
        return 0.0
    target = km_from_source
    walked = 0.0
    for L in lengths:
        if walked + L >= target:
            return (walked + L) / total if L == 0 else (walked + target) / total
        walked += L
    return 1.0


def fraction_at_point(geom: dict, pt) -> float | None:
    """Fraction [0,1] along an ordered course nearest to a [lon, lat] point
    (mirrors WaterFeatureLayer.fractionAtPoint)."""
    parts = ordered_parts(geom)
    total = 0.0
    for p in parts:
        for i in range(1, len(p)):
            total += haversine_km(p[i - 1], p[i])
    if total <= 0:
        return None

    def dist_to_seg(a, b, p):
        abx, aby = b[0] - a[0], b[1] - a[1]
        apx, apy = p[0] - a[0], p[1] - a[1]
        l2 = abx * abx + aby * aby
        t = (apx * abx + apy * aby) / l2 if l2 else 0.0
        t = max(0.0, min(1.0, t))
        return math.hypot(p[0] - (a[0] + t * abx), p[1] - (a[1] + t * aby))

    best, bd, walked = None, 1e18, 0.0
    for coords in parts:
        for j in range(1, len(coords)):
            a, b = coords[j - 1], coords[j]
            d = dist_to_seg(a, b, pt)
            if d < bd:
                bd = d
                seg_len = haversine_km(a, b)
                abx, aby = b[0] - a[0], b[1] - a[1]
                apx, apy = pt[0] - a[0], pt[1] - a[1]
                l2 = abx * abx + aby * aby
                t = (apx * abx + apy * aby) / l2 if l2 else 0.0
                t = max(0.0, min(1.0, t))
                within = sum(haversine_km(coords[k - 1], coords[k]) for k in range(1, j))
                best = (walked + within + t * seg_len) / total
        for i in range(1, len(coords)):
            walked += haversine_km(coords[i - 1], coords[i])
    return best
