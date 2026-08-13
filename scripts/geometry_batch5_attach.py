#!/usr/bin/env python3
"""GEOMETRY batch 5/6 (t_a15dac21): attach OSM geometry to the 60 contracted
waters without geometry in Gorj/Călărași/Covasna/Dolj/Argeș/Buzău/Sălaj.

Strategy per water (same as batch 3/4, scripts/geometry_batch{3,4}_attach.py):
  A. Group member whose riverGroup ALREADY has a geometry owner -> stays
     geometry-less by design (one-owner-per-group, skill pitfall #4).
  B. FULL_COURSE_UPGRADE for groups whose only owner holds a PARTIAL course
     while other members' contract reaches are undrawn:
       - arges: owner 3614s8es (AJVPS Dâmbovița) held only the Dâmbovița
         stretch; chain ALL 'arges' clusters (source->Danube) + county-polygon
         sector intervals for the 4 county members (Argeș/Dâmbovița/Giurgiu/
         Călărași) — the Siret pattern (#28/#29).
       - dambovita: owner fo3h8cp6 (Ilfov) held only the lower course; chain
         the Dâmbovița from the Pecineagu lake tail (25.171E) to the Argeș
         confluence + county sectors. The headwater above the lake is attached
         DIRECTLY to romsilva-arges-izvoarele-dambovitei (own group) so the
         two groups don't double-draw the source reach.
       - buzau: owner ufdigh4c (Brăila) held only the lower course; chain all
         'buzau' clusters (Întorsura Buzăului source -> Siret mouth) + county
         sectors for Covasna/Buzău/Brăila members.
       - barca: owner romsilva-salaj-barcaul-superior held a degenerate 9-pt
         stub; chain the SĂLAJ-clipped 'barcau' course + Romsilva km sectors
         (Superior 15.6 / Mijlociu 17.6 / Inferior 30 km -> fractions).
       - oltet: owner dvhkx2a2 held only the middle/lower course; chain all
         'oltet' clusters (Polovragi headwater -> Olt) + Gorj county sector.
  C. Otherwise: county-guarded candidate scoring over OSM river clusters
     (data/cache/osm_river_clusters.pkl) + Overpass lake polygons. Rivers
     become a single ordered LineString; lakes keep their Polygon.
     subtype=='lac' prefers lake polygons over same-name river clusters.
  D. Unmatchable -> keep bbox fallback, document in the report. KEEP_BBOX
     entries are the deliberate ones (canals/balti without OSM names, no
     in-county named feature, or a course already drawn under another group).

Usage:
  python3 scripts/geometry_batch5_attach.py            # dry run (report only)
  python3 scripts/geometry_batch5_attach.py --write    # apply to waters.json
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

BATCH_COUNTIES = ["Gorj", "Călărași", "Covasna", "Dolj", "Argeș", "Buzău", "Sălaj"]

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
    "Gorj": (23.27, 45.04), "Călărași": (27.32, 44.21),
    "Covasna": (26.18, 45.85), "Dolj": (23.82, 44.32),
    "Argeș": (24.82, 44.94), "Buzău": (26.83, 45.15), "Sălaj": (23.05, 47.18),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)
INDEX_RE = re.compile(r"^\d+\s+")

def strip_index(s: str) -> str:
    return INDEX_RE.sub("", s, count=1)

# Batch-specific OSM-name overrides: core(water name) -> OSM index name to look
# up. Every attach is still county-polygon-guarded (pitfall #30).
NAME_OVERRIDES = {
    # Argeș
    "vidraru": "lacul vidraru",            # Vidraru == OSM reservoir Lacul Vidraru
    # Gorj
    "sadului": "sadu",                     # Valea Sadului == OSM Sadu (Gorj, Jiu tributary)
    "susita seaca": "susita",              # Râul Șușița Seacă == OSM Șușița (Gorj, main stem)
    # Buzău
    "valea slanicului": "slanic",          # Valea Slănicului == OSM Slănic (Buzău, Buzău-river tributary)
    # Călărași
    "balta potcoava": "lacul potcoava",    # Balta Potcoava == OSM Lacul Potcoava (Călărași, near Danube)
}

# Rivers whose OSM ways are split into MULTIPLE same-named clusters: merge ALL
# matching clusters' parts into ONE chained course.
MULTI_CHAIN = {
    "anpa-anpa-0216": ["slanic", "paraul slanic"],   # Valea Slănicului: main + headwater cluster
}

# Direct attach for a water in its OWN ownerless group, with a part filter to
# carve out a headwater stretch (kept separate from the full-course upgrade of
# the downstream group so the two don't double-draw).
DIRECT_ATTACH = {
    # Dâmbovița headwater: the Romsilva contract is "Izvoare - Coada Lac
    # Pecineagu" (20 km) — the stretch ABOVE the Pecineagu reservoir
    # (upstream of ~25.09E, the dam at Barajul Pecineagu). Parts with
    # first-lon < 25.09 = the headwater fan; the dambovita group's
    # full-course upgrade chains from 25.09E downstream.
    "romsilva-arges-izvoarele-dambovitei": {
        "norms": ["dambovita"],
        "keep_first_lon_lt": 25.09,
        "source_anchor": (24.96, 45.58),
    },
}

# Full-course upgrade: group has ONE geometry owner whose course only covers
# part of the river; replace its geometry with the FULL chained in-county
# course (the group's other members share it). slug -> list of cluster norms
# to chain (county-guarded). Sector intervals for the group members are set
# from COUNTY polygons (buffered, Siret pattern #28).
FULL_COURSE_UPGRADE = {
    # Argeș: 3614s8es (AJVPS Dâmbovița) held only the Dâmbovița stretch
    # (25.19-25.59E); the Argeș (fouqynmq) and Călărași (anpa-anpa-0230)
    # contract reaches were undrawn. Full course: 24.61E (Făgăraș) -> 26.64E
    # (Danube).
    "arges": {
        "owner": "3614s8es",
        "norms": ["arges"],
        "source_anchor": (24.63, 45.36),   # Făgăraș headwater
        "members": ["fouqynmq", "3614s8es", "anpa-anpa-0298", "anpa-anpa-0230"],
    },
    # Dâmbovița: fo3h8cp6 (Ilfov) held only the lower course (25.9-26.28E).
    # Chain from the Pecineagu reservoir (~25.09E, downstream of the dam) to
    # the Argeș confluence (26.472,44.227). The headwater ABOVE the reservoir
    # is attached directly to romsilva-arges-izvoarele-dambovitei (separate
    # group). The two Argeș members are split at Dragoslavele (25.169,45.348):
    # Superioară above, mijlocie (Dragoslavele–Malul cu Flori) below.
    "dambovita": {
        "owner": "fo3h8cp6",
        "norms": ["dambovita"],
        "source_anchor": (25.09, 45.55),   # below the dam -> downstream
        "members": ["2tehod7w", "anpa-anpa-0056", "ggka27ea", "fo3h8cp6"],
        "keep_first_lon_ge": 25.09,        # drop the headwater fan above the reservoir
        "anchor_split": {                   # Argeș members split at Dragoslavele
            "2tehod7w": (None, "Dragoslavele, Argeș"),       # [0, f_dragoslavele]
            "anpa-anpa-0056": ("Dragoslavele, Argeș", None),  # [f_dragoslavele, county_end]
        },
    },
    # Buzău: ufdigh4c (Brăila) held only the lower course (27.22-27.74E); the
    # Covasna (Întorsura) and Buzău county reaches were undrawn. Full course:
    # 26.03E (Vama Buzăului/Întorsura) -> 27.74E (Siret mouth).
    "buzau": {
        "owner": "ufdigh4c",
        "norms": ["buzau"],
        "source_anchor": (26.03, 45.50),   # Întorsura Buzăului headwater
        "members": ["romsilva-brasov-buzaul-superior", "anpa-anpa-0261",
                    "ufdigh4c"],
        # The 4 AJVPS BUZĂU contracts (0207/0210/0211/0214) overlap on the same
        # county reach with unresolvable limits (vărsare/conf. texts without
        # geocodable localities) — leave them sector-less group members; the
        # full-course upgrade makes the whole river draw for them.
    },
    # Barcău (Sălaj): romsilva-salaj-barcaul-superior held a degenerate 9-pt
    # stub at 22.62E. Chain the SĂLAJ-clipped Barcău course; sectors from the
    # Romsilva official km (15.6/17.6/30) as course fractions (pitfall #5).
    "barca": {
        "owner": "romsilva-salaj-barcaul-superior",
        "norms": ["barcau", "barcau/berettyo"],
        "source_anchor": (22.74, 47.34),   # Sălaj source side (E end)
        "members": ["romsilva-salaj-barcaul-superior",
                    "romsilva-salaj-barcaul-mijlociu",
                    "romsilva-salaj-barcaul-inferior"],
        "clip_county": "Sălaj",
        "min_part_pts": 30,                 # drop the degenerate 9-pt stub cluster
        "km_sectors": {                     # official Romsilva km -> fractions
            "romsilva-salaj-barcaul-superior": (0.0, 15.6),
            "romsilva-salaj-barcaul-mijlociu": (15.6, 33.2),
            "romsilva-salaj-barcaul-inferior": (33.2, 63.2),
        },
    },
    # Olteț (Gorj): dvhkx2a2 held only the middle/lower course (23.8-24.0E);
    # the Gorj headwater (Polovragi, 23.76-23.8E) was undrawn. Full course:
    # 23.76E (Novaci/Polovragi) -> 24.43E (Olt confluence).
    "oltet": {
        "owner": "dvhkx2a2",
        "norms": ["oltet"],
        "source_anchor": (23.79, 45.34),   # Polovragi headwater
        "members": ["romsilva-gorj-oltet", "dvhkx2a2", "e8r6r01g"],
    },
}

# Deliberate keep-bbox: a candidate EXISTS (or the river is already mapped)
# but attaching would double-draw or misrepresent the contract.
KEEP_BBOX = {
    # Gorj
    "anpa-anpa-0310": "Râul Jaleș (Runcu–Rogojel, 15 km): no OSM cluster named Jaleș in Gorj",
    "g39ohi12": "Râul Jilț (Fărcășești area, bbox 23.25-23.40E): no OSM cluster named Jilț in Gorj",
    "romsilva-gorj-valea-bratcului": "Valea Bratcului (12 km, izvoare–conf. Jiu): no OSM 'Bratc*' cluster in Gorj (Bratcov is Teleorman, Brătcuța is Caraș-Severin)",
    "anpa-anpa-0304": "Râul Șușița Verde (izvoare–sat Vaidei): the OSM 'Șușița' course is attached to the Seacă contract (same river system); a second owner would double-draw",
    # Călărași
    "anpa-anpa-0233": "Balta Valea Mare (Ulmeni, 7 ha): no OSM 'Valea Mare' water in Călărași (all same-name clusters are other counties)",
    "anpa-anpa-0234": "Balta ecluza Oltenița (Oltenița–Port, 2 ha): no OSM named lake at the Oltenița lock",
    "anpa-anpa-0231": "Canal irigații Jirlău (30 km): no OSM 'Jirlău' canal in Călărași (the Jirlău LAKE is in Brăila county)",
    "anpa-anpa-0236": "Canalul Milotina (50 ha): no OSM 'Milotina' water in Călărași",
    "anpa-anpa-0235": "Canalul Scoiceni (Mânăstirea–Chiselet, 6 km): no OSM 'Scoiceni' water in Călărași",
    "anpa-anpa-0228": "Canalul Siderurgic (9 km): no OSM 'Siderurgic' water in Călărași",
    "anpa-anpa-0229": "Rețeaua de canale de irigații (jud. Călărași): generic irrigation network, no single OSM feature",
    # Covasna
    "anpa-anpa-0252": "Brațele secundare ale Râului Negru (Surcea/Sântionlunca/Ozun/Comandău): secondary branches, no single OSM named feature",
    "anpa-anpa-0253": "Pârâu Szaldoboș (izvoare–conf. Olt): no OSM cluster with this Hungarian name",
    "anpa-anpa-0254": "Pârâu Șomko (izvoare–conf. Olt): no OSM cluster with this Hungarian name",
    # Dolj
    "anpa-anpa-0285": "Balta Geormane (Teasc–Bădoși, 58 ha): no OSM 'Geormane' lake in Dolj",
    "anpa-anpa-0286": "Balta Marica (Bratovoești–Prunet, 31 ha): no OSM 'Marica' lake in Dolj",
    "anpa-anpa-0289": "Baraj Ișalnița (Craiova, 138 ha): no OSM 'Ișalnița' reservoir in Dolj (CET cooling lake unnamed in dump)",
    "anpa-anpa-0278": "Canal Săpata (7 km, paralel DN 55A): no OSM 'Săpata' canal in Dolj",
    "anpa-anpa-0295": "Canalul CET Ișalnița – apă caldă (4 km): no OSM named canal",
    "anpa-anpa-0293": "Canalul Dăbuleni CO (10 km): no OSM 'Dăbuleni' canal in Dolj",
    "anpa-anpa-0279": "Canalul Ianoși (10 km, Săpata–Bistreț): no OSM 'Ianoși' canal in Dolj",
    "anpa-anpa-0287": "Gârla Mălăieni (5.5 km, polder Dunăreni): no OSM 'Mălăieni' water in Dolj (Mălaia/Mălăiești are Vâlcea)",
    # Sălaj
    "anpa-anpa-0515": "Năpradea – braț mort Someșul Mare (3 ha): dead branch of the Someș at Năpradea, no OSM named feature",
    "anpa-anpa-0508": "Sonia (Gostila–Gâlgău, 13 km): no OSM cluster named Sonia in Sălaj",
    "anpa-anpa-0514": "Valea Barcăului (45 km, Barcăul de jos): the Barcău Sălaj course is drawn under the Romsilva barca group; a separate owner would double-draw",
    "anpa-anpa-0512": "Valea Sălajului (Gârceiu–Cehu Silvaniei, 22 km): no OSM cluster named Sălajului in Sălaj",
}

# Source anchors for rivers whose course the generic latitude ordering would
# invert (pitfall #18b). After chaining, orient so the end nearest the source
# anchor comes FIRST.
ORIENT_SOURCE = {
    "anpa-anpa-0216": (26.56, 45.62),        # Slănic: source at N end (Sibiciu mts), flows S to Buzău
    "romsilva-gorj-valea-sadului": (23.55, 45.32),  # Sadu: source at NE, flows W/SW to Jiu
    "anpa-anpa-0303": (23.22, 45.29),        # Șușița: source at N, flows S to Jiu
    "romsilva-arges-izvoarele-dambovitei": (24.96, 45.58),  # Dâmbovița headwater: source at NW
}

CHAIN_TOL = 0.006


def geom_parts(g: dict):
    if g.get("type") == "LineString":
        return [g["coordinates"]]
    return g.get("coordinates", [])


def chain_tolerant(parts, tol=CHAIN_TOL):
    """Chain parts by near-endpoint connectivity (tolerance for moved nodes).

    Returns the chained part list (may drop disconnected side-branches).
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
            return chain
        p = parts[best_i]
        if best_kind == "tail_a":
            chain.append(p)
        elif best_kind == "tail_b":
            chain.append(list(reversed(p)))
        elif best_kind == "head_b":
            chain.insert(0, p)
        else:
            chain.insert(0, list(reversed(p)))
        used[best_i] = True
    return chain


def chain_course(cluster_geom, slug):
    from sweep_multiway_rivers import chain_parts, flatten
    parts = geom_parts(cluster_geom)
    chain = chain_parts(parts)
    if chain is None:
        chain = chain_tolerant(parts)
    if chain is None:
        longest = max(parts, key=len)
        chain = [longest]
    return flatten(chain)


def chain_all_clusters(cls_list, slug, part_filter=None, min_part_pts=5):
    """Merge ALL clusters' parts into ONE chained LineString. Dedupe by
    (first,last) endpoints, then chain. part_filter(points) can drop parts
    (e.g. headwater above a lake tail); parts shorter than min_part_pts are
    dropped (degenerate stub clusters, duplicated tiny ways)."""
    from sweep_multiway_rivers import chain_parts, flatten
    seen = set()
    parts = []
    for cl in cls_list:
        for p in geom_parts(cl["geom"]):
            if len(p) < min_part_pts:
                continue
            if part_filter is not None and not part_filter(p):
                continue
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
    n = strip_index(n)
    n = PREFIX_RE.sub("", n, count=1)
    n = re.sub(r"^de\s+acumulare\s+", "", n, count=1)
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
        polys.append((name, prep(geom), geom, geom.bounds))
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
        for name, pgeom, _g, pbbox in polygons:
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


def haversine_m(a, b):
    import math as _m
    R = 6371000.0
    la1, lo1, la2, lo2 = map(_m.radians, (a[1], a[0], b[1], b[0]))
    dlat = la2 - la1
    dlon = lo2 - lo1
    h = _m.sin(dlat / 2) ** 2 + _m.cos(la1) * _m.cos(la2) * _m.sin(dlon / 2) ** 2
    return 2 * R * _m.asin(min(1.0, _m.sqrt(h)))


def course_fractions(coords, polygons, county, buffer_deg=0.002):
    """Min/max haversine fraction of course points inside the county polygon
    buffered by buffer_deg (Siret pattern, pitfall #28)."""
    cum = [0.0]
    for i in range(len(coords) - 1):
        cum.append(cum[-1] + haversine_m(coords[i], coords[i + 1]))
    total = cum[-1]
    if total <= 0:
        return None, None
    target = next((n for n, p, g, b in polygons if n == county), None)
    if target is None:
        return None, None
    raw_geom = next((g for n, p, g, b in polygons if n == county), None)
    pbbox = next((b for n, p, g, b in polygons if n == county), None)
    if raw_geom is None or pbbox is None:
        return None, None
    buffered = raw_geom.buffer(buffer_deg)
    fracs = []
    for i, c in enumerate(coords):
        lon, lat = c
        if not (pbbox[0] - buffer_deg <= lon <= pbbox[2] + buffer_deg
                and pbbox[1] - buffer_deg <= lat <= pbbox[3] + buffer_deg):
            continue
        if buffered.contains(Point(lon, lat)):
            fracs.append(cum[i] / total)
    if not fracs:
        return None, None
    return min(fracs), max(fracs)


def geocode_frac(query, coords):
    """Geocode a contract-boundary locality via Nominatim and return its
    haversine fraction along the course (cum[i]/cum[-1], FE metric)."""
    import urllib.parse
    import urllib.request

    url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
           + urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "undepescuim-geometry-batch5"})
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
    best_i, best_d = 0, 1e18
    for i, c in enumerate(coords):
        d = (c[0] - pt[0]) ** 2 + (c[1] - pt[1]) ** 2
        if d < best_d:
            best_i, best_d = i, d
    segs = [(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
    frac = 0.0
    for i, (a, b) in enumerate(segs):
        m = haversine_m(a, b)
        if i < best_i:
            frac += m
        elif i == best_i:
            d0 = haversine_m(a, pt)
            frac += min(m, d0)
            break
    total = sum(haversine_m(a, b) for a, b in segs)
    return frac / total if total else None


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
    print(f"[batch5] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

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
    print(f"[batch5] target: {len(target)} waters")

    report = {"fixed": [], "unmatchable": [], "group_shared": [],
              "sector_fixed": [], "sector_cleared": []}
    changed = []
    handled = set()

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    # ---- pre-pass: direct headwater attaches (ownerless groups) ------------
    for slug, dcfg in DIRECT_ATTACH.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing DIRECT_ATTACH water {slug}")
        cls_list = []
        seen_ids = set()
        for nk in dcfg["norms"]:
            for cl in by_norm.get(nk, []):
                if id(cl) in seen_ids:
                    continue
                seen_ids.add(id(cl))
                pts = cluster_points(cl["geom"])
                ind, maj, tot = county_hits(pts, polygons, w["judet"])
                if ind > 0 or maj == w["judet"]:
                    cls_list.append(cl)
        if not cls_list:
            print(f"  !! DIRECT {slug}: no cluster")
            continue
        thr = dcfg.get("keep_first_lon_lt")
        def d_filter(p, _thr=thr):
            if _thr is None:
                return True
            return p[0][0] < _thr
        allpts = [p for cl in cls_list for p in cluster_points(cl["geom"])]
        out_geom = chain_all_clusters(cls_list, slug, part_filter=d_filter)
        if out_geom is None:
            print(f"  !! DIRECT {slug}: chain failed")
            continue
        out_geom = orient_course(out_geom, dcfg["source_anchor"])
        w["geometry"] = out_geom
        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        w["geometryByCounty"] = {}
        w["source_detail"] = "geometry_batch5:direct-headwater"
        handled.add(slug)
        ind, maj, tot = county_hits(cluster_points(out_geom), polygons, w["judet"])
        report["fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "source": "river",
            "osmc": "+".join(dcfg["norms"]), "in_county_pts": ind, "majority": maj,
            "direct_headwater": True,
        })
        print(f"  FIX   {w['judet']:10} {w['name'][:44]:46} <- [direct-headwater] "
              f"{'+'.join(dcfg['norms'])} (in={ind} maj={maj}) bbox={[round(x,2) for x in w['bbox']]}")
        changed.append(w)

    # ---- pre-pass: full-course upgrades with county/km sectors --------------
    for key, cfg in FULL_COURSE_UPGRADE.items():
        owner = w_by_slug(cfg["owner"])
        if owner is None:
            raise SystemExit(f"missing FULL_COURSE_UPGRADE owner {cfg['owner']}")
        # county guard: cluster must touch the OWNER's county OR be part of the
        # same river system (border counties). Collect from ALL member counties
        # (the full course of a multi-county river may not touch the owner's).
        member_counties = set()
        for slug in [cfg["owner"]] + list(cfg.get("members", [])):
            m = w_by_slug(slug)
            if m and m.get("judet"):
                member_counties.add(m["judet"])
        cls_list = []
        seen_ids = set()
        for nk in cfg["norms"]:
            for cl in by_norm.get(nk, []):
                if id(cl) in seen_ids:
                    continue
                seen_ids.add(id(cl))
                pts = cluster_points(cl["geom"])
                ind, maj, tot = county_hits(pts, polygons, owner["judet"])
                if ind > 0 or maj in member_counties:
                    cls_list.append(cl)
        allpts = [p for cl in cls_list for p in cluster_points(cl["geom"])]
        in_dec, majority, total = county_hits(allpts, polygons, owner["judet"])
        any_member = any(
            county_hits(allpts, polygons, mc)[0] > 0 or
            county_hits(allpts, polygons, mc)[1] in member_counties
            for mc in member_counties
        )
        if not cls_list or not any_member:
            print(f"  !! UPGRADE {key}: no in-county cluster (in={in_dec} maj={majority})")
            continue

        lon_ge = cfg.get("keep_first_lon_ge")
        def part_filter(p, _lon_ge=lon_ge):
            if _lon_ge is None:
                return True
            return p[0][0] >= _lon_ge

        out_geom = chain_all_clusters(cls_list, owner["slug"], part_filter=part_filter,
                                      min_part_pts=cfg.get("min_part_pts", 5))
        if out_geom is None:
            print(f"  !! UPGRADE {key}: chain failed")
            continue
        out_geom = orient_course(out_geom, cfg["source_anchor"])
        course_coords = out_geom["coordinates"]

        # optional county clip (barca: keep only Sălaj course)
        clip_county = cfg.get("clip_county")
        if clip_county:
            cgeom = next((g for n, p, g, b in polygons if n == clip_county), None)
            cbbox = next((b for n, p, g, b in polygons if n == clip_county), None)
            if cgeom is not None and cbbox is not None:
                clipped = []
                for c in course_coords:
                    lon, lat = c
                    if (cbbox[0] - 0.01 <= lon <= cbbox[2] + 0.01
                            and cbbox[1] - 0.01 <= lat <= cbbox[3] + 0.01
                            and cgeom.buffer(0.01).contains(Point(lon, lat))):
                        clipped.append(c)
                if len(clipped) >= 4:
                    course_coords = clipped
                    out_geom["coordinates"] = clipped
                print(f"    clip {clip_county}: course -> {len(course_coords)} pts")

        owner["geometry"] = out_geom
        owner["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        owner["geometryByCounty"] = {}
        owner["source_detail"] = "geometry_batch5:full-course-upgrade"
        report["sector_fixed"].append({
            "slug": owner["slug"], "name": owner["name"], "judet": owner["judet"],
            "group": owner.get("riverGroup"), "sectorStart": None, "sectorEnd": None,
            "owner": True, "note": f"full-course upgrade [{key}], "
                                    f"{len(course_coords)} pts",
            "bbox": owner["bbox"],
        })
        print(f"  UPGRADE {key:10} {owner['name'][:40]:42} <- full course "
              f"(clusters={len(cls_list)}) in={in_dec} maj={majority} "
              f"bbox={[round(x,2) for x in owner['bbox']]}")
        changed.append(owner)

        # sector intervals for group members
        if "km_sectors" in cfg:
            km = cfg["km_sectors"]
            total_km = max(v[1] for v in km.values())
            for slug, (k0, k1) in km.items():
                mem = w_by_slug(slug)
                if mem is None:
                    raise SystemExit(f"missing sector member {slug}")
                handled.add(slug)
                f0, f1 = k0 / total_km, k1 / total_km
                mem["sectorStart"], mem["sectorEnd"] = round(f0, 4), round(f1, 4)
                mem["geometryByCounty"] = {}
                mem["source_detail"] = "geometry_batch5:barca-km-sector"
                report["sector_fixed"].append({
                    "slug": slug, "name": mem["name"], "judet": mem["judet"],
                    "group": mem.get("riverGroup"), "sectorStart": round(f0, 4),
                    "sectorEnd": round(f1, 4), "owner": False,
                    "note": f"Romsilva km {k0}-{k1} of {total_km}",
                })
                print(f"    SECTOR {slug:42} [{f0:.4f}, {f1:.4f}] (km {k0}-{k1})")
                changed.append(mem)
        else:
            # county-polygon sectors; optional locality anchors split members
            # that share the same county (e.g. two Argeș Dâmbovița contracts
            # split at Dragoslavele).
            anchor_frac = {}
            for slug, (a_start, a_end) in (cfg.get("anchor_split") or {}).items():
                f = {}
                for tag, q in (("start", a_start), ("end", a_end)):
                    if q:
                        fr = geocode_frac(q, course_coords)
                        f[tag] = fr
                        print(f"    anchor {slug} {tag}={q!r} -> {fr if fr is None else round(fr,4)}")
                anchor_frac[slug] = f
            for slug in cfg.get("members", []):
                mem = w_by_slug(slug)
                if mem is None:
                    continue
                f0, f1 = course_fractions(course_coords, polygons, mem["judet"])
                if f0 is None:
                    print(f"    !! sector {slug}: no {mem['judet']} pts on course")
                    continue
                if slug in anchor_frac:
                    af = anchor_frac[slug]
                    if af.get("start") is not None:
                        f0 = af["start"]
                    if af.get("end") is not None:
                        f1 = af["end"]
                handled.add(slug)
                mem["sectorStart"], mem["sectorEnd"] = round(f0, 4), round(f1, 4)
                mem["geometryByCounty"] = {}
                mem["source_detail"] = "geometry_batch5:county-sector"
                report["sector_fixed"].append({
                    "slug": slug, "name": mem["name"], "judet": mem["judet"],
                    "group": mem.get("riverGroup"), "sectorStart": round(f0, 4),
                    "sectorEnd": round(f1, 4), "owner": slug == cfg["owner"],
                    "note": "county-polygon sector"
                            + (" + locality anchor" if slug in anchor_frac else ""),
                })
                print(f"    SECTOR {slug:42} [{f0:.4f}, {f1:.4f}] ({mem['judet']})")
                changed.append(mem)

    # ---- main loop ----------------------------------------------------------
    def collect(name, slug):
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
        if slug in MULTI_CHAIN:
            norms = MULTI_CHAIN[slug]
            multi_cls = []
            seen_ids = set()
            for norm_key in norms:
                for cl in by_norm.get(norm_key, []):
                    if id(cl) in seen_ids:
                        continue
                    seen_ids.add(id(cl))
                    # county guard per cluster: only chain clusters that touch
                    # the declared county (same-name clusters in OTHER counties
                    # must not contaminate the course — Valea Slănicului Buzău
                    # vs Slănic Vâlcea).
                    pts = cluster_points(cl["geom"])
                    ind, maj, tot = county_hits(pts, polygons, declared)
                    if ind > 0 or maj == declared:
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
                        w["source_detail"] = "geometry_batch5:multichain"
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
            w["source_detail"] = "geometry_batch5:" + src
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
    print(f"\n[batch5] fixed={fixed} sector_fixed={sectors} group_shared={shared} unmatchable={unm}")
    print(f"[batch5] TOTAL handled={fixed + unm + shared + sectors}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
