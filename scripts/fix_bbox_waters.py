#!/usr/bin/env python3
"""Fix bbox-rectangle waters (t_33533bc7): attach real OSM geometry.

Two rectangle classes are fixed:
  A. bbox-no-geometry  — geo.ts renders the bbox as a blue rectangle
  B. rect-polygon      — geometry is a degenerate 4-corner bbox Polygon

Matching:
  - Rivers (subtype=rau): conservative ladder from audit_missing_rivers.py
    (best_osm_match + try_manual_override) against data/rivers_osm.geojson,
    plus curated LAKE_LAKE / RIVER overrides below for known pairs.
  - Lakes (subtype=lac): HOTOSM waterways.geojson polygon features matched by
    normalized name (prefix/sector stripped) + anchor-distance (the water's
    arebaltapeste coordinate), picking the closest confident candidate.

Usage: python3 scripts/fix_bbox_waters.py [--write] [--json-report PATH]
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
OSM_FILE = ROOT / "data" / "rivers_osm.geojson"
HOTOSM = ROOT / "data" / "sources" / "waterways.geojson"

sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import (  # noqa: E402
    best_osm_match,
    build_county_centroids,
    core,
    load_osm_index,
    make_cluster_geoms,
    norm,
    try_manual_override,
    MANUAL_OVERRIDES,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def is_rect_poly(g):
    """True when geometry is a degenerate 4-corner bbox rectangle polygon."""
    if not g or g["type"] != "Polygon":
        return False
    ring = g["coordinates"][0]
    pts = set((round(p[0], 6), round(p[1], 6)) for p in ring)
    if len(pts) != 4:
        return False
    xs = sorted(p[0] for p in pts)
    ys = sorted(p[1] for p in pts)
    corners = {(xs[0], ys[0]), (xs[0], ys[-1]), (xs[-1], ys[0]), (xs[-1], ys[-1])}
    return pts == corners


def geom_centroid(g):
    coords = g["coordinates"]
    if g["type"] == "MultiPolygon":
        pts = [p for part in coords for ring in part for p in ring]
    elif g["type"] == "Polygon":
        pts = [p for ring in coords for p in ring]
    elif g["type"] == "MultiLineString":
        pts = [p for part in coords for p in part]
    else:
        pts = coords
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def geo_dist_km(a, b):
    """Approx great-circle km between (lon,lat) points."""
    lon1, lat1 = a
    lon2, lat2 = b
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def geom_bbox(g):
    coords = g["coordinates"]
    if g["type"] == "MultiPolygon":
        pts = [p for part in coords for ring in part for p in ring]
    elif g["type"] == "Polygon":
        pts = [p for ring in coords for p in ring]
    elif g["type"] == "MultiLineString":
        pts = [p for part in coords for p in part]
    else:
        pts = coords
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [round(min(lons), 6), round(min(lats), 6), round(max(lons), 6), round(max(lats), 6)]


def bbox_overlap_area(b1, b2):
    """Overlap area of two [lng_min, lat_min, lng_max, lat_max] boxes (deg^2)."""
    if not b1 or not b2:
        return 0.0
    dx = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    dy = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    return dx * dy


def bbox_gap_km(b1, b2):
    """Approx gap between two bboxes (0 when they overlap), in km."""
    if not b1 or not b2:
        return 1e9
    dx = max(0.0, max(b1[0], b2[0]) - min(b1[2], b2[2]))
    dy = max(0.0, max(b1[1], b2[1]) - min(b1[3], b2[3]))
    return 111.0 * (dx ** 2 + dy ** 2) ** 0.5


def is_tiny_bbox(bb):
    """True when a geometry bbox is a degenerate sliver (a node fragment)."""
    if not bb:
        return True
    return (bb[2] - bb[0]) < 0.003 and (bb[3] - bb[1]) < 0.003


def pick_cluster_by_bbox(water, geoms_list):
    """Choose the OSM cluster whose extent best matches the water's own bbox.

    best_osm_match picks clusters by proximity to the COUNTY centroid, which
    is right for distinguishing same-name rivers in different counties but
    can pick the WRONG cluster for a multi-cluster river: e.g. 'Râul Cibinul
    Inferior' (bbox 23.93–24.03) gets the east-Cibin cluster (24.17–24.29)
    because that one is nearer the Sibiu county centroid, and 'Teleajen'
    sometimes collapses onto a tiny node fragment. Here we re-rank by overlap
    with the water's bbox: the segment(s) that actually cover the reported
    area win, tiny slivers are skipped when a real cluster exists.
    """
    wb = water.get("bbox")
    if not wb:
        return None
    # drop tiny slivers unless that's all we have
    real = [g for g in geoms_list if not is_tiny_bbox(geom_bbox(g))]
    pool = real or geoms_list
    best, best_key = None, None
    for g in pool:
        gb = geom_bbox(g)
        if not gb:
            continue
        ov = bbox_overlap_area(wb, gb)
        gap = bbox_gap_km(wb, gb)
        garea = (gb[2] - gb[0]) * (gb[3] - gb[1])
        # prefer: any overlap (larger overlap better), then smaller gap, then
        # larger course extent (the full river beats a short fragment)
        key = (ov > 0.0, ov, -gap, garea)
        if best_key is None or key > best_key:
            best_key = key
            best = g
    return best


# ---------------------------------------------------------------------------
# Lake matching (HOTOSM polygons)
# ---------------------------------------------------------------------------
LAKE_PREFIX_RE = re.compile(
    r"^(lacul|lac|acumularea|acumulare|balta|baltile|balti|barajul|baraj|taul|taurile|"
    r"iaz|heleseteu|heleșteu|canalul|canal|bazinul|bazin|piscicola|deversor|captarea|"
    r"galerie|pr|p |v |val|paraul|parau|raul|rau|izvorul|izvor|garla)\s+"
)
LAKE_SECTOR_WORDS = {
    "montan", "montana", "montan", "superior", "superioara", "inferior", "inferioara",
    "mijlociu", "mijlocie", "mare", "mica", "mic", "micul", "marele", "i", "ii", "iii",
    "iv", "v", "vi", "vii", "de", "cu", "si", "nou", "noua", "vechi", "veche",
    "1", "2", "3", "4", "5", "lui", "la", "iezer", "iezeru", "iezere", "iezerele",
    "izvorul", "izvor", "acumularea", "acumulare", "barajul", "baraj",
    "baltile", "balta", "adiacente", "adiacenta", "sale",
}


def lake_core(name):
    """Normalized name stripped of stacked prefixes + sector words.

    'Lac acumulare Arpașu' -> 'arpasu'; 'Lacul montan Avrig' -> 'avrig'.
    """
    n = norm(name)
    prev = None
    while n != prev:
        prev = n
        n = LAKE_PREFIX_RE.sub("", n, count=1).strip()
    toks = [t for t in n.split() if t not in LAKE_SECTOR_WORDS]
    return " ".join(toks)


def lake_alts(name):
    """Alternate normalized search forms for a lake water name.

    Includes the parenthetical content when present (norm() strips it):
    'Lacul Săcălaia (Lacul Știucilor)' -> ['sacalaia', 'lacul stiucilor', 'stiucilor'].
    """
    out = []
    for form in [name, *re.findall(r"\(([^)]*)\)", name or "")]:
        c = lake_core(form)
        if c and c not in out:
            out.append(c)
        n = norm(form)
        if n and n not in out:
            out.append(n)
    return out


def article_variants(tokens):
    """Variants of the first token with the Romanian definite article removed.

    'arpasu' -> ['arpasu', 'arpas']  (strip trailing 'u' after consonant)
    'somesul' -> ['somesul', 'somes', 'somese'] (strip 'ul'/'l')
    'bondureasa' -> ['bondureasa', 'bondureas'] (strip trailing 'a')
    """
    if not tokens:
        return [tokens]
    t = tokens[0]
    out = {tuple(tokens)}
    if len(t) >= 5 and t.endswith("ul"):
        out.add(tuple([t[:-2], *tokens[1:]]))
        out.add(tuple([t[:-1], *tokens[1:]]))
    if len(t) >= 5 and t.endswith("u") and t[-2] not in "aeiou":
        out.add(tuple([t[:-1], *tokens[1:]]))
    if len(t) >= 5 and t.endswith("a") and t[-2] not in "aeiou":
        out.add(tuple([t[:-1], *tokens[1:]]))
    if len(t) >= 5 and t.endswith("l") and t[-2] in "aeiou" and not t.endswith("ul"):
        out.add(tuple([t[:-1], *tokens[1:]]))
    return [list(v) for v in out]


def token_sim(a, b):
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0.0
    return len(set(ta) & set(tb)) / max(len(ta), len(tb))


def char_sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def load_hotosm_lines():
    """Index of named LineString/MultiLineString features from HOTOSM waterways.

    Returns {norm_name: [feature, ...]} for lines with a name.
    """
    fc = json.loads(HOTOSM.read_text(encoding="utf-8"))
    out = {}
    for f in fc.get("features", []):
        g = f.get("geometry")
        if g is None or g["type"] not in ("LineString", "MultiLineString"):
            continue
        p = f.get("properties") or {}
        name = p.get("name") or p.get("name_ro") or ""
        if not name:
            continue
        out.setdefault(norm(name), []).append({
            "name": name,
            "norm": norm(name),
            "core": lake_core(name),
            "geom": g,
            "waterway": p.get("waterway"),
        })
    return out


def match_river_hotosm(water, hot_lines, county_centroids, max_dist_km=15.0):
    """Best HOTOSM line for a river water (fallback after OSM index).

    Uses the audit core+county logic, comparing the water core against HOTOSM
    line cores, penalizing far clusters. Returns (matched_name, geom, score).
    """
    wc = core(water.get("name", ""))
    if not wc:
        return None, None, 0.0
    wt = wc.split()
    wfirst = wt[0]
    judet = water.get("judet") or ""
    ccent = county_centroids.get(judet) if judet else None

    best, best_name, best_score = None, None, 0.0
    for lname, flist in hot_lines.items():
        lc = core(lname)
        if not lc:
            continue
        lt = lc.split()
        if not lt:
            continue
        # token overlap: >=2 shared tokens with ts>=0.6, OR single exact token
        shared = set(wt) & set(lt)
        ts = len(shared) / max(len(wt), len(lt))
        sc = 0.0
        if len(shared) >= 2 and ts >= 0.6:
            sc = ts
        elif len(shared) == 1 and len(wt) == 1 and len(lt) == 1:
            sc = 1.0
        elif shared and ts >= 0.6 and wfirst in shared:
            sc = ts
        # char-level only when the FULL core is very close (>=0.87) AND first
        # token agrees — 'izvorul lotrului' ~ 'izvorul ursului' (0.839, shared
        # only the genitive suffix) must NOT match.
        elif first_token_ok(wfirst, lt[0]) and char_sim(wc, lc) >= 0.87:
            sc = char_sim(wc, lc)
        if sc <= 0:
            continue
        # county penalty per cluster
        for f in flist:
            c = geom_centroid(f["geom"])
            if c is None:
                continue
            pen = 0.0
            if ccent:
                d = ((c[0] - ccent[0]) ** 2 + (c[1] - ccent[1]) ** 2) ** 0.5
                if d > 1.0:
                    pen = 0.15 if d <= 2.0 else 0.3
            score = sc - pen
            if score > best_score:
                best_score = score
                best = f
                best_name = lname
    if best and best_score >= 0.6:
        # merge all same-name lines within the cluster distance
        return best_name, best["geom"], best_score
    return None, None, 0.0


def first_token_ok(wfirst, ifirst):
    if wfirst == ifirst:
        return True
    if len(wfirst) >= 5 and len(ifirst) >= 5:
        if ifirst.startswith(wfirst) and ifirst[len(wfirst):] in ("ul", "l"):
            return True
        if wfirst.startswith(ifirst) and wfirst[len(ifirst):] in ("ul", "l"):
            return True
    return False


def load_hotosm_lakes():
    """Index of named polygon features from HOTOSM waterways.geojson.

    Returns list of {name, norm, core, geom, centroid, area_deg2}.
    """
    fc = json.loads(HOTOSM.read_text(encoding="utf-8"))
    out = []
    for f in fc.get("features", []):
        g = f.get("geometry")
        if g is None or g["type"] not in ("Polygon", "MultiPolygon"):
            continue
        p = f.get("properties") or {}
        name = p.get("name") or p.get("name_ro") or ""
        if not name:
            continue
        c = geom_centroid(g)
        if c is None:
            continue
        # area (approx deg^2) for tie-break / size sanity
        area = 0.0
        if g["type"] == "Polygon":
            ring = g["coordinates"][0]
            s = 0.0
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                s += x1 * y2 - x2 * y1
            area = abs(s) / 2.0
        out.append({
            "name": name,
            "norm": norm(name),
            "core": lake_core(name),
            "geom": g,
            "centroid": c,
            "area": area,
            "water": p.get("water"),
            "nc": p.get("natural_class"),
        })
    # merge the Overpass reservoir fetch (named closed ways + relations) —
    # these are reservoir outlines OSM keeps WITHOUT natural/water tags.
    over = ROOT / "data" / "raw" / "overpass_reservoir_fetch.json"
    if over.exists():
        data = json.loads(over.read_text(encoding="utf-8"))
        els = data.get("elements", [])
        nodes = {el["id"]: (el.get("lat"), el.get("lon"))
                 for el in els if el["type"] == "node" and "lat" in el}
        ways = {}
        for el in els:
            if el["type"] != "way":
                continue
            coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
            if len(coords) >= 4:
                ways[el["id"]] = (el.get("tags", {}), coords)
        rels = []
        for el in els:
            if el["type"] != "relation":
                continue
            parts = [ways[m["ref"]][1] for m in el.get("members", [])
                     if m["type"] == "way" and m["ref"] in ways]
            rels.append((el.get("tags", {}), parts))
        for tags, coords in ways.values():
            name = tags.get("name") or tags.get("name:ro") or ""
            if not name:
                continue
            if abs(coords[0][0]-coords[-1][0]) > 1e-9 or abs(coords[0][1]-coords[-1][1]) > 1e-9:
                continue  # not closed -> not a polygon
            g = {"type": "Polygon", "coordinates": [coords]}
            c = geom_centroid(g)
            if c is None:
                continue
            area = 0.0
            ring = coords
            s = 0.0
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                s += x1 * y2 - x2 * y1
            area = abs(s) / 2.0
            out.append({
                "name": name, "norm": norm(name), "core": lake_core(name),
                "geom": g, "centroid": c, "area": area,
                "water": tags.get("water"), "nc": None, "src": "overpass",
            })
        for tags, parts in rels:
            name = tags.get("name") or tags.get("name:ro") or ""
            if not name or not parts:
                continue
            rings = [p for p in parts if abs(p[0][0]-p[-1][0]) < 1e-9 and abs(p[0][1]-p[-1][1]) < 1e-9]
            if not rings:
                continue
            g = {"type": "MultiPolygon", "coordinates": [[p] for p in rings]}
            c = geom_centroid(g)
            if c is None:
                continue
            out.append({
                "name": name, "norm": norm(name), "core": lake_core(name),
                "geom": g, "centroid": c, "area": 0.0,
                "water": tags.get("water"), "nc": None, "src": "overpass",
            })
    # merge the full Overpass named-lake extract (data/processed/overpass_named_lakes.json)
    # — a broad Romania-wide pull of named water polygons from overpass_water_all.json.
    # These fill reservoirs HOTOSM draws only as dam walls (Măneciu, Beliș-Fântânele...).
    opnl = ROOT / "data" / "processed" / "overpass_named_lakes.json"
    if opnl.exists():
        for l in json.loads(opnl.read_text(encoding="utf-8")):
            g = l.get("geom")
            if g is None or g["type"] not in ("Polygon", "MultiPolygon"):
                continue
            c = l.get("centroid")
            if c is None:
                continue
            area = 0.0
            if g["type"] == "Polygon":
                ring = g["coordinates"][0]
                s = 0.0
                for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                    s += x1 * y2 - x2 * y1
                area = abs(s) / 2.0
            out.append({
                "name": l.get("name", ""), "norm": l.get("norm") or norm(l.get("name", "")),
                "core": l.get("core") or lake_core(l.get("name", "")),
                "geom": g, "centroid": c, "area": area,
                "water": (l.get("tags") or {}).get("water"), "nc": None,
                "src": "overpass_all",
            })
    # dedupe by (norm, rounded centroid)
    seen = set()
    dedup = []
    for l in out:
        key = (l["norm"], round(l["centroid"][0], 3), round(l["centroid"][1], 3))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(l)
    return dedup


# ---------------------------------------------------------------------------
# Curated lake overrides: water core (lake_core, prefix+sector stripped) ->
# HOTOSM polygon name, for well-known pairs the generic matcher cannot connect.
# Each is validated by anchor-distance before geometry is attached.
# ---------------------------------------------------------------------------
LAKE_OVERRIDES = {
    # Lac acumulare Olteț (Brașov) == OSM 'Acumularea Viștea' (Viștea-Olteț reservoir)
    "oltet": "acumularea vistea",
    # Lacul Gura Golumbului (Caraș-Severin) == OSM 'Lacul Miniș (Gura Golumbului)'
    # (parenthetical content is the real name)
    "gura golumbului": "lacul minis",
    # Prisaca Cerna (Caraș-Severin) == OSM 'Lacul de acumulare Prisaca'
    "prisaca cerna": "lacul de acumulare prisaca",
    # Lacul Săcălaia (Lacul Știucilor) (Cluj) == OSM 'Lacul Știucilor' (alternate name)
    "sacalaia": "lacul stiucilor",
    # Lacul Izvorul (Măgurii) (Bistrița-Năsăud) == OSM 'Lacul Anieș' (the lake at
    # Măgura/Anieș — Izvorul Măgurii is the Anieș lake's local name)
    "izvorul magurii": "lacul anies",
    # Lacul Bistra Iezer (Caraș-Severin) == OSM 'Lacul Bistra' (iezer is sector-ish)
    "bistra iezer": "lacul bistra",
    # Lacul Câmpu lui Neag (Hunedoara) == OSM 'Valea de Pești' reservoir (adjacent,
    # the Câmpu lui Neag reservoir is the Valea de Pești storage)
    "campu lui neag": "valea de pesti",
    # Oglinda Mândrii (Hunedoara) == OSM 'Lacul Mândra' (same glacial lake)
    "oglinda mandrii": "lacul mandra",
    # Roşiile (Tăul fără Fund) (Hunedoara) == OSM 'Tăul fără Fund' (parenthetical)
    "rosiile": "taul fara fund",
    # Slăvei (Hunedoara) == OSM 'Slăvelu' (diminutive variant)
    "slavei": "slavelu",
    # Lac Bicaz (Neamț) == OSM 'Lacul Izvorul Muntelui' (Bicaz reservoir official name)
    "bicaz": "lacul izvorul muntelui",
    # Lac Pangrati (Neamț) — reservoir west of Bâtca Doamnei; OSM has no named
    # Pangrati polygon, closest is Acumularea Bâtca Doamnei — leave unmatched.
    # Lacul de acumulare Hațeg (Hunedoara) == OSM 'Lac de Acumulare Sântămăria-Orlea'
    "acumulare hateg": "lac de acumulare santamaria orlea",
    # Lacul Vlădești (Vâlcea) — reservoir on Lotru; OSM named 'Vlădești' polygon
    # missing from extract — leave unmatched.
    # Lac Dognecea Mare (Caraș-Severin) == OSM 'Lacul Mare' (the Dognecea Mare lake)
    "lac dognecea mare": "lacul mare",
    "dognecea mare": "lacul mare",
    # Lac Dognecea Mică (Caraș-Severin) == OSM 'Lacul Mic' (the Dognecea Mică lake)
    "lac dognecea mica": "lacul mic",
    "dognecea mica": "lacul mic",
    # Iezer – Ighel (Alba) == OSM 'Lacul Ighiel' (vowel variant)
    "ighel": "lacul ighiel",
    # Iezer – Șurianu (Alba) == OSM 'Lacul Șureanu' (vowel variant)
    "surianu": "lacul sureanu",
    # Balta Cicir (Arad) == OSM 'Balastiera Cicir' (gravel-pit lake)
    "cicir": "balastiera cicir",
    # Acumulare Agrement (Bacău) == OSM 'Lacul de acumulare Bacău I' (the
    # Agrement reservoir is the Bacău I storage)
    "agrement": "lacul de acumulare bacau i",
    # Lacul Muntinu (Vâlcea) == OSM 'Iezeru Muntinu' (vowel variant)
    "muntinu": "iezeru muntinu",
    # Lac acumulare Arpașu (Brașov, AVPS Făgăraș) == OSM 'Acumularea Arpaș'
    # (same reservoir as the Sibiu twin; the arebaltapeste coordinate was
    # geocoded into the Făgăraș mountains ~22 km away)
    "lac acumulare arpasu": "acumularea arpas",
    "arpasu": "acumularea arpas",
    # Lacul Subcetate (Hunedoara) == OSM 'Lac Acumulare' (the Subcetate
    # reservoir, drawn unnamed; anchor sits on it at 0.1 km)
    "subcetate": "lac acumulare",
    # Lacul Bentu Mare Bordușani (Ialomița) == OSM 'Lacul bentul Lătenilor'
    # (the Bentu Mare pond; anchor 0.1 km)
    "lacul bentu mare bordusani": "lacul bentul latenilor",
    "bentu mare bordusani": "lacul bentul latenilor",
    # Lacul Bentu Mic Bordușani (Ialomița) == OSM 'Lacul Bentu Mic' (0.5 km)
    "lacul bentu mic bordusani": "lacul bentu mic",
    "bentu mic bordusani": "lacul bentu mic",
    # Lacul Ivanul (Mehedinți) == OSM 'Iovanu' (vowel variant, 0.3 km)
    "ivanul": "iovanu",
    "lacul ivanul": "iovanu",
    # Cuiejdel (Neamț) == OSM 'Lacul Cuejdel (Crucii)' (same lake, 0.0 km)
    "cuiejdel": "lacul cuejdel",
    # Iezerul Pietrosu (Maramureș) == OSM 'Lacul Iezer' (the Pietrosu glacial
    # lake is named 'Iezer' in OSM, 0.0 km)
    "iezerul pietrosu": "lacul iezer",
    # Lac Făerag (Hunedoara) == OSM 'Tău Făerag' (0.0 km)
    "faerag": "tau faerag",
    # Lacul Bentu lui Cotoi (Ialomița) == OSM 'Lacul Bentu Mic' (0.7 km, same
    # Bentu pond complex as Bentu Mic Bordușani). NB: 'lui' is stripped by
    # LAKE_SECTOR_WORDS so lake_core is 'bentu cotoi'.
    "bentu cotoi": "lacul bentu mic",
    # Lac Cilieni I,II,III (Dolj) == OSM 'Bălăsan' — the OSM polygon is tagged
    # 'Balasan (Cilieni, Moțăței)', i.e. the Cilieni ponds (0.9 km)
    "cilieni": "balasan",
}


def is_dam_name(name):
    """True when a lake polygon name denotes the dam structure, not the water."""
    n = norm(name)
    return n.startswith("baraj") or n.startswith("deversor") or " baraj" in n or "captarea" in n


def load_unnamed_reservoirs():
    """Unnamed reservoir/lake polygons from the Overpass water dump.

    OSM often draws reservoir outlines as closed ways WITHOUT a name tag
    (water=reservoir / natural=water). Contracted waters that name the
    reservoir ('Lac acumulare Cerbureni', 'Acumulare Căpâlna'...) then have
    no named polygon to match — but the unnamed outline sits right on the
    water's anchor. Return them for a position-based fallback.

    Returns list of {geom, centroid, area_deg2}.
    """
    over = ROOT / "data" / "raw" / "overpass_water_all.json"
    if not over.exists():
        return []
    data = json.loads(over.read_text(encoding="utf-8"))
    els = data.get("elements", [])
    nodes = {el["id"]: (el.get("lat"), el.get("lon"))
             for el in els if el["type"] == "node" and "lat" in el}
    out = []
    for el in els:
        if el["type"] != "way":
            continue
        t = el.get("tags", {})
        if t.get("name"):
            continue
        tag_hit = t.get("water") or t.get("natural") or t.get("landuse")
        if tag_hit not in ("reservoir", "lake", "pond", "basin", "water"):
            continue
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) < 4:
            continue
        if abs(coords[0][0] - coords[-1][0]) > 1e-9 or abs(coords[0][1] - coords[-1][1]) > 1e-9:
            continue  # not closed
        s = 0.0
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            s += x1 * y2 - x2 * y1
        area = abs(s) / 2.0
        if area < 0.00001:
            continue  # skip tiny ditches/puddles
        c = geom_centroid({"type": "Polygon", "coordinates": [coords]})
        if c is None:
            continue
        out.append({
            "geom": {"type": "Polygon", "coordinates": [coords]},
            "centroid": c,
            "area": area,
            "name": "",
            "norm": "",
            "core": "",
        })
    # dedupe by rounded centroid
    seen = set()
    dedup = []
    for l in out:
        key = (round(l["centroid"][0], 3), round(l["centroid"][1], 3))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(l)
    return dedup


def match_lake_unnamed(water, unnamed, max_dist_km=2.0):
    """Closest unnamed reservoir polygon to the water's anchor.

    Position-based last resort for contracted lakes whose reservoir OSM keeps
    unnamed. The arebaltapeste coordinate anchor usually sits ON the reservoir,
    so a single close unnamed outline is strong evidence. Returns the closest
    polygon within max_dist_km that is not tiny.
    """
    anchor = None
    c = water.get("coordinates")
    if c and len(c) >= 2:
        anchor = (c[0], c[1])
    elif water.get("bbox"):
        b = water["bbox"]
        anchor = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if not anchor:
        return None
    best, bd = None, 1e9
    for l in unnamed:
        d = geo_dist_km(anchor, l["centroid"])
        if d < bd and d <= max_dist_km:
            bd, best = d, l
    return best


def match_lake_override(water, lakes):
    """Curated lake fallback keyed by water name, validated by distance."""
    name = water.get("name", "")
    # try several key forms: full norm FIRST (most specific), then lake core,
    # then parenthetical cores
    keys = [norm(name), lake_core(name)]
    for p in re.findall(r"\(([^)]*)\)", name or ""):
        n = norm(p)
        if n and n not in keys:
            keys.append(n)
        c = lake_core(p)
        if c and c not in keys:
            keys.append(c)
    target = None
    for k in keys:
        if k in LAKE_OVERRIDES:
            target = LAKE_OVERRIDES[k]
            break
    if not target:
        return None
    anchor = None
    c = water.get("coordinates")
    if c and len(c) >= 2:
        anchor = (c[0], c[1])
    elif water.get("bbox"):
        b = water["bbox"]
        anchor = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if not anchor:
        return None
    tnorm = norm(target)
    best, bd = None, 1e9
    for lk in lakes:
        if norm(lk["name"]) != tnorm:
            continue
        d = geo_dist_km(anchor, lk["centroid"])
        if d < bd:
            bd, best = d, lk
    if best and bd <= 30.0:
        return best
    return None


def match_lake(water, lakes, max_dist_km=12.0):
    """Best HOTOSM polygon for a lake water, or None.

    Score = token overlap (>=0.6, at least one shared token) or char similarity
    of cores (>=0.8), then require centroid within max_dist_km of the water's
    coordinate anchor; prefer closest centroid, then largest area.
    """
    alts = lake_alts(water.get("name", ""))
    if not alts:
        return None
    anchor = None
    c = water.get("coordinates")
    if c and len(c) >= 2:
        anchor = (c[0], c[1])
    elif water.get("bbox"):
        b = water["bbox"]
        anchor = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if not anchor:
        return None

    best, best_key = None, None
    for lk in lakes:
        lcore = lk["core"]
        if not lcore:
            continue
        ltoks = lcore.split()
        lvariants = article_variants(ltoks)
        sc = 0.0
        for alt in alts:
            wvariants = article_variants(alt.split())
            for wv in wvariants:
                for lv in lvariants:
                    ws, ls = set(wv), set(lv)
                    shared = ws & ls
                    ts = len(shared) / max(len(ws), len(ls))
                    if shared and ts >= 0.6:
                        sc = max(sc, ts)
                    elif char_sim(" ".join(wv), " ".join(lv)) >= 0.8 and wv[0] == lv[0]:
                        sc = max(sc, char_sim(" ".join(wv), " ".join(lv)))
        if sc <= 0:
            continue
        d = geo_dist_km(anchor, lk["centroid"])
        if d > max_dist_km:
            continue
        # tie-break: prefer real water polygons over dam-structure polygons
        # ('Lacul de acumulare X' beats 'Barajul X' at the same name+score),
        # THEN closest centroid, then largest area. Dam walls are tiny point
        # features that sit next to the actual reservoir — distance alone is a
        # bad arbiter (the dam is always closer than the reservoir outline).
        key = (sc, 0 if is_dam_name(lk["name"]) else 1, -d, lk["area"])
        if best_key is None or key > best_key:
            best_key = key
            best = lk
    return best


# ---------------------------------------------------------------------------
# Curated river overrides for names the conservative ladder cannot connect
# (validated below by county centroid like MANUAL_OVERRIDES).
# ---------------------------------------------------------------------------
RIVER_OVERRIDES = {
    # Pârâul Lesuntu (Bacău) — OSM 'Lesu' is 268 km away (different river); the
    # real Lesuntu is absent from the extract — no override.
    # Pârâul Valea Leșului (Bistrița-Năsăud) == OSM 'Valea Lesilor' (4.8 km)
    "valea lesului": "valea lesilor",
    "lesului": "valea lesilor",
    # Valea Rîndiboului (Sibiu) == OSM 'Valea Rîndiboului' absent — no override.
    # Valea Strâmbii (Sibiu) == OSM 'Strâmba' cluster near the water (0.9 km)
    "valea strambii": "stramba",
    "strambii": "stramba",
    # Pârâul Valea Rîndiboului (Sibiu) == OSM 'Rândibou' (vowel variant, 1.8 km)
    "valea rindiboului": "randibou",
    "rindiboului": "randibou",
    # Râul Grotului (Vâlcea) — OSM absent, no override.
    # Râul Holod (Bihor) — OSM absent (only Homorod, different river).
    # Râul Jilț (Gorj) — OSM absent (Jieț is a different river).
    # Râul Măgura Cisnădiei (Sibiu) == OSM 'Cisnădie'
    "magura cisnadiei": "cisnadie",
    # Râul Potop (Dâmbovița) — OSM absent.
    # Râul Râmești (Vâlcea) — OSM absent.
    # Râul Tărcăița (Bihor) == OSM 'Tarcău'? different river (Neamț). no override.
    # Râul Teleajen inferior - Bucov (Prahova) == OSM 'Teleajen'
    "teleajen inferior bucov": "teleajen",
    # Râul Valea Ilvei (Bistrița-Năsăud) == OSM 'Tihul Ilvei'? no — Valea Ilvei is
    # the Ilva river; OSM 'Ilva' absent from extract.
    # Râul Volovăț (Botoșani) — OSM absent.
    # Râul Vorona (Botoșani) == OSM 'Voronet'? DIFFERENT river (Voronet is in
    # Suceava). no override.
    # Topa – Holod (Bihor) == OSM 'Valea Topa' (the Topa stream, 16 km from the
    # arebaltapeste anchor; 'Topa Mică' at 87 km is a DIFFERENT stream)
    "topa holod": "valea topa",
    # Valea Bistrei (Alba/Bihor) — 'Bistra' clusters exist; keep for county pick.
    "bistrei": "bistra",
    # Valea Buduresei (Bihor) — OSM 'Valea Budureasa'? absent. no override.
    # Valea Gepiș (Bihor) == OSM 'Pârâul Ghepiu' (vowel variant)
    "gepis": "paraul ghepiu",
    # Valea Ierului (Bihor) — OSM absent (Fierul is different).
    # Valea Mișidului (Bihor) == OSM 'Pârâul Mișid'
    "misidului": "paraul misid",
    # Valea Omului (Bihor) — OSM absent.
    # Valea Sighiștelului (Bihor) == OSM 'Sighiștel'
    "sighistelului": "sighistel",
    # Valea Șoimului (Bihor) — OSM absent.
    # Valea Cârlibabei (Suceava) == OSM 'Cârlibaba'
    "carlibabei": "cirlibaba",
    # Valea Drăganului (Cluj) == OSM 'Drăgan'
    "draganului": "dragan",
    # Valea Ierii Mijlocie/Superioară (Cluj) == OSM 'Iara' (same river: Valea Ierii
    # is the Iara valley)
    "ierii mijlocie": "iara",
    "ierii superioara": "iara",
    # Valea Lonei (Cluj) — OSM absent.
    # Valea Răcătăului (Cluj) == OSM 'Răcătău'
    "racataului": "racatau",
    # Valea Vadului (Cluj) — OSM absent.
    # Valea Șartășului (Alba) == OSM 'Șartăș'
    "sartasului": "sartas",
    # Valea Țibăului (Suceava) == OSM 'Țibău'
    "tibaului": "tibau",
    # Valea Călinești cu pâraiele... (Vâlcea) == OSM 'Călinești'
    "calinesti cu paraiele calinesti sulita soci": "calinesti",
    # Râul Sabasa (Neamț) — OSM absent (Sabasa appears as drain? probe said no).
    # Râul Izvorul Lotrului (Vâlcea) == OSM 'Valea Izvorul Lotrișor'? different.
    #   The real Izvorul Lotrului may be unmapped; skip.
}

# lake-like water names that should get a POLYGON even though subtype is rau
# (channels/reservoirs listed as rivers) — currently empty; handled by lake matcher
# for lac subtype only.

# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json-report", type=str)
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    rects = []
    for w in waters:
        if w.get("bbox") and not w.get("geometry"):
            rects.append((w, "bbox-no-geom"))
        elif is_rect_poly(w.get("geometry")):
            rects.append((w, "rect-poly"))
    print(f"[fix] {len(waters)} waters, {len(rects)} blue rectangles to fix")

    # ---- OSM river index ----
    print("[fix] loading OSM river index...")
    name_index, geoms = load_osm_index()
    osm_geo_by_norm = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_geo_by_norm[n] = gs
    county_centroids = build_county_centroids(waters)
    print(f"[fix] OSM clusters: {len(osm_geo_by_norm)}")

    # ---- HOTOSM lakes + lines ----
    print("[fix] loading HOTOSM lake polygons + lines...")
    lakes = load_hotosm_lakes()
    hot_lines = load_hotosm_lines()
    unnamed = load_unnamed_reservoirs()
    print(f"[fix] HOTOSM named polygons: {len(lakes)}, named lines: {len(hot_lines)}, unnamed reservoirs: {len(unnamed)}")

    # merge curated river overrides into the global override table
    merged_overrides = dict(MANUAL_OVERRIDES)
    merged_overrides.update(RIVER_OVERRIDES)

    # monkeypatch the module-level MANUAL_OVERRIDES so try_manual_override sees them
    import audit_missing_rivers as amr
    amr.MANUAL_OVERRIDES = merged_overrides

    matched = []
    unmatched = []
    for w, kind in rects:
        sub = w.get("subtype")
        name = w.get("name", "")
        if sub == "rau":
            best, geom, score, how = best_osm_match(w, osm_geo_by_norm, county_centroids)
            if not best:
                best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
                if best and geom:
                    # safety: overrides are keyed by name across counties; the
                    # same-name OSM cluster in a DIFFERENT county must not be
                    # attached when the water has a coordinate anchor far away
                    # (Alba 'Valea Bistrei' vs the Bihor Bistra, 100 km off).
                    anchor = w.get("coordinates")
                    if anchor and len(anchor) >= 2:
                        c = geom_centroid(geom)
                        if c and geo_dist_km(anchor, c) > 40.0:
                            best, geom, score, how = None, None, 0.0, "override-anchor-reject"
            if best and geom:
                # re-rank the matched name's clusters by overlap with the
                # water's OWN bbox (county-centroid ranking can pick a distant
                # cluster of the same river, or a tiny node fragment)
                gs_list = osm_geo_by_norm.get(best) or []
                repick = pick_cluster_by_bbox(w, gs_list)
                if repick:
                    geom = repick
                # reject a same-name cluster that does NOT touch the water's
                # bbox at all — it is a DIFFERENT river in another county
                # ('Râul Geoagiu Superior' Alba vs OSM Geoagiu in Hunedoara,
                # 21 km gap, zero overlap). Overrides (try_manual_override /
                # hotosm) carry their own documented validation and skip this.
                wb = w.get("bbox")
                gb = geom_bbox(geom) if geom else None
                if (how in ("prefix", "token", "exact", "char", "no-match")
                        and wb and gb
                        and bbox_overlap_area(wb, gb) == 0.0
                        and bbox_gap_km(wb, gb) > 15.0):
                    best, geom, score, how = None, None, 0.0, "far-cluster-reject"
            if not best:
                # HOTOSM line fallback (Sabasa, Canalul colector Criș, Topa Mică...)
                hname, hgeom, hscore = match_river_hotosm(w, hot_lines, county_centroids)
                if hgeom:
                    best, geom, score, how = hname, hgeom, hscore, "hotosm"
            if not best and kind == "rect-poly":
                # a rau with a degenerate bbox polygon is really a small
                # reservoir (Dopca, Bazin Acumulare Dopca) — try lake polygon
                lk = match_lake(w, lakes)
                if not lk:
                    lk = match_lake_override(w, lakes)
                if not lk:
                    lk = match_lake_unnamed(w, unnamed)
                if lk:
                    best, geom, score, how = lk["name"], lk["geom"], 0.0, "lake"
            if best and geom:
                w["geometry"] = geom
                bb = geom_bbox(geom)
                if bb:
                    w["bbox"] = bb
                w["source"] = w.get("source") or "osm_bulk"
                w["source_detail"] = f"bbox_fix:{how}"
                matched.append((name, w["judet"], best, round(score, 3), how, kind))
            else:
                unmatched.append((name, w["judet"], sub, kind, "no-osm-match"))
        elif sub == "lac":
            lk = match_lake(w, lakes)
            if not lk:
                lk = match_lake_override(w, lakes)
            if not lk:
                # last resort: unnamed reservoir outline sitting on the anchor
                unlk = match_lake_unnamed(w, unnamed)
                if unlk:
                    lk = unlk
            if lk:
                how_lake = "lake" if lk.get("name") else "lake-unnamed"
                # A "Barajul X" polygon can be the dam WALL, not the reservoir:
                # if it's tiny (a few hundred metres), attaching it would make
                # the reservoir disappear from the map — keep the bbox fallback
                # and document instead. Real reservoirs behind dams are large.
                bb0 = geom_bbox(lk["geom"])
                tiny = bool(
                    bb0
                    and (bb0[2] - bb0[0]) * (bb0[3] - bb0[1]) < 0.00005
                    and is_dam_name(lk["name"])
                )
                if tiny:
                    unmatched.append((name, w["judet"], sub, kind,
                                      f"dam-only-tiny:{lk['name']}"))
                else:
                    w["geometry"] = lk["geom"]
                    bb = geom_bbox(lk["geom"])
                    if bb:
                        w["bbox"] = bb
                    w["source"] = w.get("source") or "hotosm"
                    w["source_detail"] = f"bbox_fix:{how_lake}:{lk['name']}"
                    matched.append((name, w["judet"], lk["name"], 0.0, how_lake, kind))
            else:
                unmatched.append((name, w["judet"], sub, kind, "no-lake-polygon"))
        else:
            unmatched.append((name, w["judet"], sub, kind, "not-rau/lac"))

    print(f"\n[fix] matched {len(matched)}/{len(rects)}")
    print("[fix] MATCHED:")
    for name, jud, osm, score, how, kind in sorted(matched):
        print(f"   [{kind:11s}] {name} ({jud}) -> {osm} [{how}]")
    print(f"\n[fix] UNMATCHED ({len(unmatched)}):")
    for name, jud, sub, kind, why in sorted(unmatched):
        print(f"   [{kind:11s}] {name} ({jud}) [{sub}] {why}")

    if args.json_report:
        report = {
            "total_rects": len(rects),
            "matched": [{"name": n, "judet": j, "osm": o, "score": s, "how": h, "kind": k}
                        for n, j, o, s, h, k in matched],
            "unmatched": [{"name": n, "judet": j, "subtype": s, "kind": k, "why": w}
                          for n, j, s, k, w in unmatched],
        }
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[report] wrote {args.json_report}")

    if args.write:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
