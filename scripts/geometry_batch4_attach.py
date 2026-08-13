#!/usr/bin/env python3
"""GEOMETRY batch 4/6 (t_8d2e4541): attach OSM geometry to the 58 contracted
waters without geometry in Timiș/Sibiu/Brașov/Neamț/Bistrița-Năsăud.

Strategy per water (same as batch 3, scripts/geometry_batch3_attach.py):
  A. Group member whose riverGroup ALREADY has a geometry owner -> stays
     geometry-less by design (one-owner-per-group, skill pitfall #4).
  B. SECTOR_PREPASS for the ownerless-in-effect somesul-mare group: the only
     geometry holder (wv8ykggg, Cluj) covers a 7-km tail at Dej, so the whole
     B-N reach is undrawn. Chain ALL in-county 'somesul mare' clusters onto
     ONE full-course owner and set sector intervals for the 3 B-N members
     from geocoded contract-boundary localities (Catibav/Șanț, Feldru,
     Ciceu Mihăiești) projected on the course (haversine, pitfall #27).
     FULL_COURSE_UPGRADE: 7oju77qb (Bistrița B-N) keeps only the lower/middle
     course; chain the full B-N 'bistrita' course onto it (the ANPA 28-km
     contract reach extends into the Bârgău valley, up to Mijlocenii
     Bârgăului) — still ONE owner.
  C. Otherwise: county-guarded candidate scoring over OSM river clusters
     (data/cache/osm_river_clusters.pkl) + Overpass lake polygons
     (data/processed/overpass_named_lakes*.json), attaching the best
     candidate that TOUCHES the declared county polygon. Rivers become a
     single ordered LineString; lakes keep their Polygon/MultiPolygon.
     subtype=='lac' prefers lake polygons over same-name river clusters
     (Lac Urlea vs stream Urlea; Baraj Salcia vs river Salcia).
  D. Unmatchable -> keep bbox fallback, document in the report. KEEP_BBOX
     entries are the deliberate ones (course already drawn under another
     contract, or no in-county named OSM feature).

Usage:
  python3 scripts/geometry_batch4_attach.py            # dry run (report only)
  python3 scripts/geometry_batch4_attach.py --write    # apply to waters.json
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import re
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

sys.path.insert(0, str(ROOT / "scripts"))

BATCH_COUNTIES = ["Timiș", "Sibiu", "Brașov", "Neamț", "Bistrița-Năsăud"]

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
    "Timiș": (21.22, 45.75), "Sibiu": (24.15, 45.80),
    "Brașov": (25.61, 45.65), "Neamț": (26.38, 46.93),
    "Bistrița-Năsăud": (24.50, 47.13),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)

# Romsilva lake/river names carry a list index prefix ('1 Lacul Fântânele',
# '8 Lacul Valea Calului', 'Râul 1 Someșul Cald superior') that would pollute
# the core name. Strip a leading 'N ' before core/lake_core matching.
INDEX_RE = re.compile(r"^\d+\s+")

def strip_index(s: str) -> str:
    return INDEX_RE.sub("", s, count=1)

# Batch-specific OSM-name overrides: core(water name) -> OSM index name to look
# up. Every attach is still county-polygon-guarded (pitfall #30).
NAME_OVERRIDES = {
    # Bistrița-Năsăud
    "valea ilvei": "ilva",                    # Râul Valea Ilvei == OSM Ilva (Ilva Mare/Ilva Mică basin, bbox match)
    # Brașov
    "sambetei": "sambata",                    # Valea Sâmbetei == OSM Sâmbăta (Făgăraș, tributary of Olt at Ucea)
    "sebesului": "raul sebes",                # Valea Sebeșului == OSM Râul Sebeș (Codlea/Olt, NOT the Alba Sebeș)
    "lisei": "lisa",                          # Valea Lisei == OSM Lisa (tributary of Sâmbăta)
    "sbircioara": "valea zbarcioarei",        # Romsilva Sbircioara == OSM Valea Zbârcioarei (Moieciu/Piatra Craiului; partial 2-km fragment of 45-km contract)
    # Neamț
    "pangrati": "acumularea pangarati",       # Lac Pangrati == OSM Acumularea Pângărați (Bistrița reservoir)
    # Sibiu
    "montan podragu mic": "podragel",         # Lacul montan Podragu Mic == OSM lake Podrăgel (Făgăraș, Sibiu side; the Brașov-side 'Lacul Podragu' is a DIFFERENT lake)
    "talmaciu": "talmacut",                   # Pârâul Tălmaciu == OSM Talmăcuț (lower 2-km fragment of the 5-km stream near Tălmaciu)
    # Timiș
    "baraj salcia": "barajul salcia",         # Baraj Salcia == OSM lake Barajul Salcia (Buziaș reservoir)
    "iercici": "iercicu",                     # Pârâul Iercici == OSM Iercicu (Orțișoara–Becicherecu Mic, partial)
    "lunca birda": "birda veche",             # Pârâul Lunca Birda == OSM Birda Veche (lower Birda channel near mouth; partial of 53-km contract)
}

# Rivers whose OSM ways are split into MULTIPLE same-named clusters: merge ALL
# matching clusters' parts into ONE chained course.
MULTI_CHAIN = {
}

# Full-course upgrade: group has ONE geometry owner whose course only covers
# part of the river; replace its geometry with the FULL chained in-county
# course (the group's other members share it). slug -> list of cluster norms
# to chain (county-guarded).
FULL_COURSE_UPGRADE = {
    # Bistrița B-N: 7oju77qb held only the lower/middle course (24.43-24.69E);
    # the ANPA 28-km contract reach (Pietroasa→Mijlocenii Bârgăului) extends to
    # ~24.94E. Chain the full B-N course so the whole Someș-basin Bistrița draws.
    "7oju77qb": ["bistrita"],
}

# Sector prepass for an ownerless-in-effect multi-sector group: the group's
# only geometry owner (wv8ykggg, Cluj) covers a 7-km tail at Dej, so the whole
# B-N reach of the Someșul Mare is undrawn. Chain ALL in-county 'somesul mare'
# clusters onto the owner and set sector intervals for the B-N members.
# Boundaries from the CONTRACT LIMITS texts, projected on the chained course
# (haversine fractions, geocoded localities):
#   superior (Romsilva 59 km): Izvoare - pod Catibav (Șanț)      -> [0, f(catibav)]      = [0, 0.1548]
#   inferior (a2qs9hkg 41 km): Pod Cartibav - conf. Ilva Mică     -> [f(catibav), f(ilva_mica)] = [0.1548, 0.3807]
#   anpa-bn-somesul-mare-61 (61 km): Pod Feldru - Ciceu Mihăiești -> [f(feldru), f(ciceu)] = [0.4335, 0.9582]
# (the Ilva Mică->Feldru gap ~6.7 km is unowned; FE Voronoi fallback covers it)
SECTOR_PREPASS = {
    "owner": "wv8ykggg",
    "cluster_norm": "somesul mare",
    "sectors": {
        "romsilva-bistrita-nasaud-somesul-mare-superior": (None, "catibav"),
        "a2qs9hkg": ("catibav", "ilva_mica"),
        "anpa-bn-somesul-mare-61": ("feldru", "ciceu"),
    },
    "anchors": {
        # locality -> Nominatim query; projected onto the chained course
        "catibav": "Șanț, Bistrița-Năsăud",
        "ilva_mica": "Ilva Mică, Bistrița-Năsăud",
        "feldru": "Feldru, Bistrița-Năsăud",
        "ciceu": "Ciceu Mihăiești, Bistrița-Năsăud",
    },
    "source_anchor": (24.90, 47.52),  # Someșul Mare headwater (Rodna/Șanț)
}

# Deliberate keep-bbox: a candidate EXISTS (or the river is already mapped)
# but attaching would double-draw or misrepresent the contract.
KEEP_BBOX = {
    # Timiș
    "anpa-anpa-0615": "Pârâul Birdanca (Sculea–Deta, 22 km): no OSM named river in Timiș",
    "anpa-anpa-0609": "Pârâul Cernabora (Dragomirești–VVD, 23 km): no OSM named river in Timiș",
    "anpa-anpa-0611": "Pârâul Cherestau (Darova–Boldur, 15 km): no OSM named river in Timiș",
    "anpa-anpa-0612": "Pârâul Iarcoș (Topolovăț–Bazoșu Nou, 22 km): no OSM named river in Timiș",
    "anpa-anpa-0614": "Pârâul Voiteg (zona Voiteg, 20 km): no OSM named river in Timiș",
    "anpa-anpa-0606": "Pârâul Ier (zona Biled, 24 km): only OSM 'Ier' clusters are the Bihor/Satu-Mare Ier (different river); no in-county course",
    "315lt84w": "Lacul de acumulare Lățunaș (Buziaș area): no OSM lake polygon with this name in Timiș dump",
    # Sibiu
    "romsilva-sibiu-bistra": "Bistra (Sibiu, 22 km, Izvoare–Lacul Tău): OSM 'Bistra' clusters are Neamț/Mureș/Bihor/CS — no Sibiu course named Bistra",
    "romsilva-sibiu-ciban": "Ciban (25 km, Izvoare–conf. Râul Sebeș): no OSM 'Ciban'/'Cibanul' cluster; the Sibiu Sebeș itself is unnamed in the OSM dump",
    "gxjd56ii": "Pârâul Nou Roman: no OSM candidate near its bbox (24.57E/45.80N, Cibin valley)",
    "1f162p36": "Pârâul Râul Vadului: no OSM 'Valea/Vadului' cluster in the Olt-valley bbox (24.13-24.27E/45.54N)",
    "anpa-anpa-0530": "Valea Stegii: the only 'Stegii' cluster is Pârâul Stegii in Bistrița-Năsăud (wrong county)",
    "anpa-anpa-0539": "Valea Strâmbei (10 km, izvoare–conf. Olt): only candidate 'Valea Strâmbanului' is a Vâlcea-majority Lotru-basin stream (45.573-45.581N/24.33E), not the Sibiu Olt tributary — would misdraw",
    # Brașov
    "anpa-anpa-0184": "Râul Șercaia inferioară (27 km): no OSM 'Șercaia' river; 'Șercăiței' is a different small stream 15 km west",
    "anpa-anpa-0185": "Valea Șercaia (15 km): no OSM 'Șercaia' river cluster in Brașov",
    "anpa-anpa-0188": "Valea Pojorâtei (40 km): only OSM 'Pojorâta' is in Suceava (different river)",
    "anpa-anpa-0179": "Valea Mare – Crizbav (16 km, izvoare–conf. Olt): no OSM candidate near Crizbav",
    # Neamț
    "mmakw97b": "Lac Reconstrucția: no OSM named lake polygon (fish-pond complex E of Piatra Neamț); bbox fallback",
    "anpa-anpa-0464": "Lac Reconstrucția (1): duplicate contract of mmakw97b; no OSM polygon",
    # Bistrița-Năsăud
    "7yg1hoia": "Lacul Izvorul (Măgurii) 0.2 Ha: no OSM lake named 'Izvorul Măgurii'; the B-N 'Măgura' clusters are 25 km away (different stream)",
    "anpa-anpa-0120": "Lacul Izvorul(Măgurii): duplicate contract of 7yg1hoia; no OSM polygon",
    "anpa-anpa-0131": "Pârâul Iliuța (17 km, izvoare–conf. Valea Ilvei): no OSM named river",
    "anpa-anpa-0134": "Râul Colibița superioară (21 km): OSM only maps the 'Colibița' RESERVOIR polygon, not the river course above the dam",
    "anpa-anpa-0135": "Râul Colibița inferioară (31 km): same — only the reservoir polygon exists in the OSM dump",
}

# Source anchors for rivers whose course the generic latitude ordering would
# invert (pitfall #18b). After chaining, orient so the end nearest the source
# anchor comes FIRST.
ORIENT_SOURCE = {
    "xd7hnzzl": (24.99, 47.38),     # Valea Ilvei headwater (Ilva Mică area, N)
    "anpa-anpa-0182": (25.05, 45.84),  # Valea Sebeșului (Brașov): source at N end (Făgăraș), flows S... anchor at mouth-side is wrong: use max-lat end
    "anpa-anpa-0189": (24.78, 45.61),  # Sâmbăta: source at S end (Făgăraș ridge), flows N to Olt
    "anpa-anpa-0194": (24.83, 45.65),  # Lisa: source at S end, flows N to Sâmbăta
    "anpa-anpa-0605": (21.05, 45.97),  # Iercici: source at N (Orțișoara), flows S
    "anpa-anpa-0592": (21.07, 45.45),  # Birda Veche: mouth at Timiș (W end), source at E
    "anpa-anpa-0539": (24.33, 45.58),  # Valea Strâmbanului: source at N end, flows S to Olt
    "anpa-anpa-0538": (24.24, 45.65),  # Talmăcuț: source at S/E end, flows NW to Olt/Cibin
    "romsilva-brasov-sbircioara": (25.29, 45.48),  # Zbârcioara fragment
}

# Part indices to DROP before chaining (parallel duplicated ways / interior
# stubs that break single-path connectivity).
MANUAL_DROP = {
}

# Chaining tolerance for near-but-not-exact way junctions (OSM splits ways at
# slightly moved nodes).
CHAIN_TOL = 0.006


def geom_parts(g: dict):
    if g.get("type") == "LineString":
        return [g["coordinates"]]
    return g.get("coordinates", [])


def chain_tolerant(parts, tol=CHAIN_TOL):
    """Chain parts by near-endpoint connectivity (tolerance for moved nodes).

    Returns the chained part list or None when parts don't form one path.
    """
    def near(a, b):
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

    used = [False] * len(parts)
    chain = [parts[0]]
    used[0] = True
    while len(chain) < len(parts):
        head, tail = chain[0][0], chain[-1][-1]
        progressed = False
        best_i, best_kind, best_d = None, None, 1e18
        for i, p in enumerate(parts):
            if used[i]:
                continue
            a, b = p[0], p[-1]
            for kind, pt in (("tail_a", a), ("tail_b", b), ("head_b", b), ("head_a", a)):
                target = tail if kind.startswith("tail") else head
                d = abs(pt[0] - target[0]) + abs(pt[1] - target[1])
                if d < best_d and near(pt, target):
                    best_d, best_i, best_kind = d, i, kind
        if best_i is None:
            # leftover parts are disconnected side-branches / parallel
            # channels (duplicated-ways class, pitfall #19): keep the chained
            # prefix instead of discarding the whole course
            return chain
        p = parts[best_i]
        if best_kind == "tail_a":
            chain.append(p)
        elif best_kind == "tail_b":
            chain.append(list(reversed(p)))
        elif best_kind == "head_b":
            chain.insert(0, p)
        else:  # head_a
            chain.insert(0, list(reversed(p)))
        used[best_i] = True
    return chain


def chain_course(cluster_geom, slug):
    """One ordered LineString for a river cluster: dedupe, chain (exact then
    tolerant), drop documented parallel ways, fall back to the longest part."""
    from sweep_multiway_rivers import chain_parts, flatten

    parts = geom_parts(cluster_geom)
    if slug in MANUAL_DROP:
        drop = set(MANUAL_DROP[slug])
        parts = [p for i, p in enumerate(parts) if i not in drop]
    chain = chain_parts(parts)
    if chain is None:
        chain = chain_tolerant(parts)
    if chain is None:
        # disconnected/braided: keep the longest part (documented fallback)
        longest = max(parts, key=len)
        chain = [longest]
    return flatten(chain)


def chain_all_clusters(cls_list, slug):
    """Merge ALL clusters' parts (same river split across multiple OSM
    clusters, e.g. the Someșul Cald's 3 clusters around the reservoirs) into
    ONE chained LineString. Dedupe by (first,last) endpoints, then chain."""
    from sweep_multiway_rivers import chain_parts, flatten

    seen = set()
    parts = []
    for cl in cls_list:
        for p in geom_parts(cl["geom"]):
            key = (tuple(p[0]), tuple(p[-1]))
            if key in seen:
                continue
            seen.add(key)
            parts.append(list(p))
    if not parts:
        return None
    chain = chain_parts(parts)
    if chain is None:
        chain = chain_tolerant(parts, tol=CHAIN_TOL * 2)
    if chain is None:
        longest = max(parts, key=len)
        chain = [longest]
    return flatten(chain)


def orient_course(out_geom, source_anchor):
    """Reverse a LineString so the end nearest the source anchor comes first."""
    if out_geom.get("type") != "LineString":
        return out_geom
    coords = out_geom["coordinates"]
    if len(coords) < 2:
        return out_geom
    d_first = (coords[0][0] - source_anchor[0]) ** 2 + (coords[0][1] - source_anchor[1]) ** 2
    d_last = (coords[-1][0] - source_anchor[0]) ** 2 + (coords[-1][1] - source_anchor[1]) ** 2
    if d_first > d_last:
        out_geom["coordinates"] = list(reversed(coords))
    return out_geom


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def core(name: str) -> str:
    # strip the list-index prefix FIRST, then the type prefix
    return PREFIX_RE.sub("", strip_index(norm(name)), count=1).strip()


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
    n = strip_index(n)  # '1 Lacul Fântânele' -> 'Lacul Fântânele'
    n = PREFIX_RE.sub("", n, count=1)
    n = re.sub(r"^de\s+acumulare\s+", "", n, count=1)  # 'Lacul de acumulare X' -> 'X'
    n = re.sub(r"\s+cu\s+baltile\s+adiacente.*$", "", n)
    n = re.sub(r"\s+si\s+valea\s+.*$", "", n)
    toks = n.split()
    return toks[0] if toks else n


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


def seat_dist(declared, bb):
    seat = COUNTY_SEATS.get(declared)
    if not seat or not bb:
        return None
    cpt = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
    return math.hypot(cpt[0] - seat[0], cpt[1] - seat[1])


def pick_best(candidates, declared, polygons):
    scored = []
    for src, name, geom, bb in candidates:
        pts = cluster_points(geom)
        if not pts or not bb:
            continue
        in_dec, majority, total = county_hits(pts, polygons, declared)
        if in_dec == 0 and majority != declared:
            continue
        sd = seat_dist(declared, bb) or 99.0
        score = 1000.0 * in_dec + (10.0 if majority == declared else 0.0) - sd
        scored.append((score, in_dec, majority, sd, src, name, geom, bb))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


def order_linestring(geom):
    from _mapping_common import order_course_linestring
    return order_course_linestring(geom)


def haversine_m(a, b):
    """Haversine distance in metres (R=6371, FE metric, pitfall #27)."""
    import math as _m
    R = 6371000.0
    la1, lo1, la2, lo2 = map(_m.radians, (a[1], a[0], b[1], b[0]))
    dlat = la2 - la1
    dlon = lo2 - lo1
    h = _m.sin(dlat / 2) ** 2 + _m.cos(la1) * _m.cos(la2) * _m.sin(dlon / 2) ** 2
    return 2 * R * _m.asin(min(1.0, _m.sqrt(h)))


def geocode_frac(query, coords):
    """Geocode a contract-boundary locality via Nominatim and return its
    haversine fraction along the course (cum[i]/cum[-1], FE metric)."""
    import urllib.parse
    import urllib.request

    url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
           + urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "undepescuim-geometry-batch4"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            hits = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"    !! geocode {query!r} failed: {e}")
        return None
    if not hits:
        print(f"    !! geocode {query!r}: no result")
        return None
    pt = (float(hits[0]["lon"]), float(hits[0]["lat"]))
    # nearest course point (linear scan; coarse is fine for locality anchors)
    best_i, best_d = 0, 1e18
    for i, c in enumerate(coords):
        d = (c[0] - pt[0]) ** 2 + (c[1] - pt[1]) ** 2
        if d < best_d:
            best_i, best_d = i, d
    cum = 0.0
    segs = []
    for i in range(len(coords) - 1):
        segs.append((coords[i], coords[i + 1]))
    target = best_i
    frac = 0.0
    for i, (a, b) in enumerate(segs):
        m = haversine_m(a, b)
        if i < target:
            frac += m
        elif i == target:
            # interpolate within the segment at the nearest point
            d0 = haversine_m(a, pt)
            frac += min(m, d0)
            break
    total = sum(haversine_m(a, b) for a, b in segs)
    return frac / total if total else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply changes to waters.json")
    ap.add_argument("--json", type=str, help="write report JSON to this path")
    ap.add_argument("--geocode", action="store_true",
                    help="geocode SECTOR_PREPASS locality anchors via Nominatim")
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    polygons = load_county_polygons()
    with open(CLUSTER_PKL, "rb") as f:
        clusters, _cell = pickle.load(f)
    lakes = json.loads(LAKES_JSON.read_text(encoding="utf-8"))
    lakes2 = json.loads(LAKES2_JSON.read_text(encoding="utf-8"))
    all_lakes = lakes + lakes2
    print(f"[batch4] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

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

    target = [w for w in waters if w.get("judet") in BATCH_COUNTIES and w.get("geometry") is None]
    print(f"[batch4] target: {len(target)} waters")

    report = {"fixed": [], "unmatchable": [], "group_shared": [], "sector_fixed": [], "sector_cleared": []}
    changed = []
    handled = set()

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    # ---- pre-pass: somesul-mare sector prepass ---------------------------
    if SECTOR_PREPASS:
        sp = SECTOR_PREPASS
        owner = w_by_slug(sp["owner"])
        if owner is None:
            raise SystemExit(f"missing SECTOR_PREPASS owner {sp['owner']}")
        cls_all = []
        for cl in by_norm.get(sp["cluster_norm"], []):
            pts = cluster_points(cl["geom"])
            ind, maj, tot = county_hits(pts, polygons, "Bistrița-Năsăud")
            if ind > 0 or maj == "Bistrița-Năsăud":
                cls_all.append(cl)
        allpts = [p for cl in cls_all for p in cluster_points(cl["geom"])]
        in_dec, majority, total = county_hits(allpts, polygons, "Bistrița-Năsăud")
        if cls_all and (in_dec > 0 or majority == "Bistrița-Năsăud"):
            out_geom = chain_all_clusters(cls_all, owner["slug"])
            if out_geom is not None:
                out_geom = orient_course(out_geom, sp["source_anchor"])
                course_coords = out_geom["coordinates"]
                owner["geometry"] = out_geom
                owner["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
                owner["geometryByCounty"] = {}
                owner["source_detail"] = "geometry_batch4:somesul-mare-full-course"
                print(f"  PREPASS owner {owner['name'][:40]:42} <- [{sp['cluster_norm']} x{len(cls_all)}] "
                      f"in={in_dec} maj={majority} FULL COURSE bbox={[round(v,2) for v in owner['bbox']]}")
                # geocode anchors -> haversine fractions on the course
                fracs = {}
                if args.geocode:
                    for key, q in sp["anchors"].items():
                        f = geocode_frac(q, course_coords)
                        fracs[key] = f
                        print(f"    anchor {key:8} -> frac {f if f is None else round(f, 4)}")
                else:
                    print("    (--geocode not passed; skipping anchor projection)")
                for slug, (a1, a2) in sp["sectors"].items():
                    mem = w_by_slug(slug)
                    if mem is None:
                        raise SystemExit(f"missing SECTOR_PREPASS member {slug}")
                    handled.add(slug)
                    f1 = 0.0 if a1 is None else fracs.get(a1)
                    f2 = 1.0 if a2 is None else fracs.get(a2)
                    if f1 is None or f2 is None:
                        print(f"    !! sector for {slug} skipped (anchor frac missing)")
                        continue
                    mem["sectorStart"], mem["sectorEnd"] = round(f1, 4), round(f2, 4)
                    mem["geometryByCounty"] = {}
                    mem["source_detail"] = "geometry_batch4:somesul-mare-sector"
                    report["sector_fixed"].append({
                        "slug": slug, "name": mem["name"], "judet": mem["judet"],
                        "group": mem.get("riverGroup"),
                        "sectorStart": round(f1, 4), "sectorEnd": round(f2, 4),
                        "owner": False,
                        "anchors": {"start": a1, "end": a2},
                    })
                    print(f"    SECTOR {slug:46} [{f1:.4f}, {f2:.4f}]")
                    changed.append(mem)
                report["sector_fixed"].append({
                    "slug": owner["slug"], "name": owner["name"], "judet": owner["judet"],
                    "group": owner.get("riverGroup"), "sectorStart": None, "sectorEnd": None,
                    "owner": True, "note": "full-course owner (was 7-km tail)",
                })
                changed.append(owner)
            else:
                print(f"  !! PREPASS somesul-mare: chain failed")
        else:
            print(f"  !! PREPASS somesul-mare: no in-county cluster (in={in_dec} maj={majority})")

    # ---- pre-pass: full-course upgrades -----------------------------------
    for slug, norms in FULL_COURSE_UPGRADE.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing FULL_COURSE_UPGRADE water {slug}")
        cls_list = []
        seen_ids = set()
        for nk in norms:
            for cl in by_norm.get(nk, []):
                if id(cl) in seen_ids:
                    continue
                seen_ids.add(id(cl))
                # per-cluster county guard: only B-N in-county clusters chain
                pts = cluster_points(cl["geom"])
                ind, maj, tot = county_hits(pts, polygons, w["judet"])
                if ind > 0 or maj == w["judet"]:
                    cls_list.append(cl)
        allpts = [p for cl in cls_list for p in cluster_points(cl["geom"])]
        in_dec, majority, total = county_hits(allpts, polygons, w["judet"])
        if cls_list and (in_dec > 0 or majority == w["judet"]):
            out_geom = chain_all_clusters(cls_list, slug)
            if out_geom:
                old_bb = w.get("bbox")
                out_geom = orient_course(out_geom, (24.90, 47.23))
                w["geometry"] = out_geom
                w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
                w["geometryByCounty"] = {}
                w["source_detail"] = "geometry_batch4:full-course-upgrade"
                report["sector_fixed"].append({
                    "slug": slug, "name": w["name"], "judet": w["judet"],
                    "group": w.get("riverGroup"), "sectorStart": None, "sectorEnd": None,
                    "owner": True, "note": "full-course upgrade (was partial lower/middle course)",
                    "old_bbox": old_bb,
                })
                print(f"  UPGRADE {w['judet']:10} {w['name'][:44]:46} <- full B-N course "
                      f"(clusters={len(cls_list)}) in={in_dec} maj={majority}")
                changed.append(w)
            else:
                print(f"  !! UPGRADE {slug}: chain failed")
        else:
            print(f"  !! UPGRADE {slug}: no in-county cluster (in={in_dec} maj={majority})")

    # ---- main loop --------------------------------------------------------
    def collect(name, slug):
        """[(kind, name, geom, bbox)] river clusters + lakes for a water."""
        variants = name_variants(name)
        wcore = core(name)
        wlake = lake_core(name)
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
        if wcore in NAME_OVERRIDES:
            keys.add(NAME_OVERRIDES[wcore])
        for k in keys:
            add_cluster(k)
        for nk, cls_ in by_norm.items():
            if nk in keys:
                continue
            if core(nk) == wcore and len(nk) >= 4:
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

    for w in sorted(target, key=lambda x: (x["judet"], x["name"])):
        slug = w["slug"]
        declared = w.get("judet") or "?"
        name = w.get("name") or ""
        g = w.get("riverGroup")

        if slug in handled:
            continue

        if slug in KEEP_BBOX:
            report["unmatchable"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                "old_bbox": w.get("bbox"), "note": KEEP_BBOX[slug],
            })
            print(f"  KEEP  {declared:10} {name[:44]:46} (documented KEEP_BBOX)")
            continue

        # A. group member with an owner -> stays geometry-less
        owners = [m for m in by_group.get(g, []) if m.get("geometry")] if g else []
        if owners:
            report["group_shared"].append({
                "slug": slug, "name": name, "judet": declared, "group": g,
                "note": f"group '{g}' has {len(owners)} geometry owner(s); member shares course",
            })
            print(f"  SHARE {declared:10} {name[:44]:46} (group {g}, {len(owners)} owner)")
            continue

        cands = collect(name, slug)
        # multi-cluster rivers: merge ALL matching clusters before scoring
        if slug in MULTI_CHAIN:
            norms = MULTI_CHAIN[slug]
            multi_cls = []
            seen_ids = set()
            for norm_key in norms:
                for cl in by_norm.get(norm_key, []):
                    if id(cl) in seen_ids:
                        continue
                    seen_ids.add(id(cl))
                    multi_cls.append(cl)
            if multi_cls:
                allpts = [p for cl in multi_cls for p in cluster_points(cl["geom"])]
                in_dec, majority, total = county_hits(allpts, polygons, declared)
                if in_dec > 0 or majority == declared:
                    out_geom = chain_all_clusters(multi_cls, slug)
                    if slug in ORIENT_SOURCE and out_geom:
                        out_geom = orient_course(out_geom, ORIENT_SOURCE[slug])
                    if out_geom:
                        w["geometry"] = out_geom
                        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
                        w["source_detail"] = "geometry_batch4:multichain"
                        w["geometryByCounty"] = {}
                        report["fixed"].append({
                            "slug": slug, "name": name, "judet": declared, "source": "river",
                            "osmc": "+".join(norms), "in_county_pts": in_dec,
                            "majority": majority, "multi_chain": True,
                        })
                        print(f"  FIX   {declared:10} {name[:44]:46} <- [multichain] "
                              f"{'+'.join(norms)} (in={in_dec} maj={majority})")
                        changed.append(w)
                        continue
        best = pick_best(cands, declared, polygons)
        if w.get("subtype") == "lac":
            # lakes prefer the lake polygon over a same-name river cluster
            # (Lac Urlea vs stream Urlea; Baraj Salcia vs river Salcia)
            lake_best = pick_best([c for c in cands if c[0] == "lake"], declared, polygons)
            if lake_best:
                best = lake_best
        if best:
            score, in_dec, majority, sd, src, cname, geom, bb = best
            if src == "river":
                out_geom = chain_course(geom, slug)
                if slug in ORIENT_SOURCE:
                    out_geom = orient_course(out_geom, ORIENT_SOURCE[slug])
            else:
                out_geom = geom
            w["geometry"] = out_geom
            w["bbox"] = [round(v, 5) for v in bb]
            w["source_detail"] = "geometry_batch4:" + src
            w["geometryByCounty"] = {}
            report["fixed"].append({
                "slug": slug, "name": name, "judet": declared, "source": src,
                "osmc": cname, "in_county_pts": in_dec, "majority": majority,
            })
            print(f"  FIX   {declared:10} {name[:44]:46} <- [{src}] {cname} (in={in_dec} maj={majority})")
            changed.append(w)
        else:
            report["unmatchable"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                "old_bbox": w.get("bbox"),
                "candidates": [{"kind": c[0], "name": c[1], "bb": c[3]} for c in cands[:4]],
                "note": "no OSM candidate touching declared county (or no candidate at all)",
            })
            print(f"  KEEP  {declared:10} {name[:44]:46} (no in-county candidate; keep bbox fallback)")

    fixed = len(report["fixed"])
    unm = len(report["unmatchable"])
    shared = len(report["group_shared"])
    sectors = len(report["sector_fixed"])
    cleared = len(report["sector_cleared"])
    print(f"\n[batch4] fixed={fixed} sector_fixed={sectors} sector_cleared={cleared} group_shared={shared} unmatchable={unm}")
    print(f"[batch4] TOTAL handled={fixed + unm + shared + sectors + cleared}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
