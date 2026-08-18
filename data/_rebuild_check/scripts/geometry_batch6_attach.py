#!/usr/bin/env python3
"""GEOMETRY batch 6/6 (t_3fc96b80): attach OSM geometry to the 52 contracted
waters without geometry in Vrancea/Satu Mare/Dâmbovița/Bacău/Olt/Iași + rest.

Strategy per water (same as batch 5, scripts/geometry_batch5_attach.py):
  A. Group member whose riverGroup ALREADY has a geometry owner -> stays
     geometry-less by design (one-owner-per-group, skill pitfall #4).
  B. NAME_OVERRIDES -> OSM-name differences (Brătei == Valea Brăteiului,
     Brebena-Bulba == Brebina, Valea Azugii == Azuga).
  C. RAW_WAYS -> unnamed OSM courses reconstructed from the waterway dump
     (Lesuntu = 2 chained unnamed ways in the contract bbox; Comasca =
     unnamed stream at the Comasca village).
  D. LAKE_MERGE -> merge multiple lake polygons of the same reservoir into a
     MultiPolygon (Acumularea Frunzaru = 2 parts).
  E. RESERVOIR_REACH -> the Izbiceni accumulation = the two southern outer
     rings (43.81-44.04N) of the Olt reservoir multipolygon relation.
  F. DIRECT_LAKE -> exact named lake attaches (Canalul Dunăre-Marea Neagră,
     Lacul Snagov) even for subtype rau when the contract limits span it.
  G. Unmatchable -> keep bbox fallback, document in the report.

Usage:
  python3 scripts/geometry_batch6_attach.py            # dry run (report only)
  python3 scripts/geometry_batch6_attach.py --write    # apply to waters.json
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
WATER_ALL_JSON = ROOT / "data" / "raw" / "overpass_water_all.json"
WATER_POLYS_JSON = ROOT / "data" / "raw" / "overpass_water_polys.json"

sys.path.insert(0, str(ROOT / "scripts"))

BATCH_COUNTIES = ["Vrancea", "Satu Mare", "Dâmbovița", "Bacău", "Olt", "Iași",
                  "Brăila", "Constanța", "Giurgiu", "Ialomița", "Galați",
                  "Vaslui", "Mehedinți", "Prahova", "Ilfov", "Teleorman"]

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
    "Vrancea": (26.81, 45.82), "Satu Mare": (22.89, 47.79),
    "Dâmbovița": (25.46, 44.93), "Bacău": (26.91, 46.57), "Olt": (24.48, 44.43),
    "Iași": (27.60, 47.16), "Brăila": (27.95, 45.27), "Constanța": (28.65, 44.17),
    "Giurgiu": (25.95, 43.90), "Ialomița": (27.83, 44.56), "Galați": (28.02, 45.44),
    "Vaslui": (27.73, 46.64), "Mehedinți": (22.87, 44.63), "Prahova": (26.01, 44.94),
    "Ilfov": (26.13, 44.56), "Teleorman": (25.31, 43.98),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)
INDEX_RE = re.compile(r"^\d+\s+")

def strip_index(s: str) -> str:
    return INDEX_RE.sub("", s, count=1)

NAME_OVERRIDES = {
    # Dâmbovița
    "bratei": "valea brateiului",        # Râul Brătei == OSM Valea Brăteiului (Ialomița tributary)
    # Prahova
    "azugii": "azuga",                    # Valea Azugii == OSM Azuga (flows into Prahova)
    # Mehedinți
    "brebena bulba": "brebina",           # Râul Brebena - Bulba == OSM Brebina (source name in Romsilva limits)
}

# Direct named-lake attaches (contract limits span the lake even when subtype
# says rau — e.g. 'Canal Dunăre – Marea Neagră' is the whole canal polygon).
DIRECT_LAKE = {
    "anpa-anpa-0247": "canalul dunare marea neagra",   # Canal Dunăre – Marea Neagră (Constanța)
    "anpa-anpa-0397": "lacul snagov",                  # Râul Snagov (Ilfov) — limits Periș–Gruiu span the lake
}

# Merge ALL lake polygons with these norms into ONE MultiPolygon (reservoir
# split into parts by OSM).
LAKE_MERGE = {
    "anpa-anpa-0473": "acumularea frunzaru",  # Lac acumulare Frunzaru (Olt) — 2 parts
}

# Izbiceni accumulation: the southern reach of the Olt reservoir multipolygon
# relation 2435464 (outer ways between the Izbiceni dam and the Frunzaru dam at
# ~44.04N). Contract limits: "Loc. Izbiceni - Loc. Rusănești".
RESERVOIR_REACH = {
    "anpa-anpa-0471": {
        "ways": [182932745, 88342740],   # Olt relation 2435464 outer rings
        "min_lat": 43.70, "max_lat": 44.06,
    },
}

# Unnamed OSM courses reconstructed from the waterway dump (way ids in order).
# Lesuntu: 2 chained unnamed ways in the exact contract bbox (26.565-26.583E /
# 46.16-46.20N), tributary of the Oituz. Comasca: unnamed stream at the Comasca
# village (Giurgiu, near Oinacu). Both are in-county (Bacău / Giurgiu).
RAW_WAYS = {
    "19468k28": {"ways": [434756492, 434756493], "judet": "Bacău",
                 "note": "unnamed OSM river at Lesuntu bbox (tributary of Oituz)"},
    "anpa-anpa-0301": {"ways": [15943446], "judet": "Giurgiu",
                       "note": "unnamed OSM stream at Comasca village (Oinacu)"},
}

# Deliberate keep-bbox: candidates examined and rejected / absent.
KEEP_BBOX = {
    # Vrancea
    "romsilva-vrancea-coza": "Râul Coza (9 km, izvoare–conf. Putna): no named OSM 'Coza' way; only unnamed headwater fragments not attributable with confidence",
    "anpa-anpa-0680": "Râul Zăbăluța (16 km, izvoare–pod Florean): no named OSM 'Zăbăluța' way; Zăbala clusters are the main stem, not the tributary",
    "anpa-anpa-0675": "Doaga (18 ha, Doaga village): only unnamed reservoir (985 ha, way 352574401) at the village — size mismatch vs contract, no OSM name",
    # Satu Mare
    "anpa-anpa-0498": "CCPFB Paulian (11.4 km, frontieră Berveni): unnamed fish-pond complex at Berveni (40+ unnamed ways 22.66-22.76E/47.85-47.93N); no named OSM feature",
    "anpa-anpa-0497": "CCRM Ruseni (36.8 km, Moftin): no named OSM water at Rușeni/Moftin (Lacul Moftinu is 17 ha, not the 36.8 km contract)",
    "anpa-anpa-0499": "CP 9 stația mică (36.19 km): cryptic fish-farm code, no limits text, no OSM candidate",
    # Dâmbovița
    "ebhj5eyj": "Râul Potop (45 km, Dâmbovița): no OSM 'Potop' way/cluster in Dâmbovița (Overpass 0 hits); bbox fallback from areba",
    # Bacău
    # (19468k28 fixed via RAW_WAYS)
    # Olt
    # (0471/0473 fixed via RESERVOIR_REACH / LAKE_MERGE)
    # Iași
    "anpa-anpa-0393": "Brațul Închis(mort) al râului Jijia (Cârniceni–Gorban): OSM 'jijia veche' cluster is IDENTICAL to the main Jijia course (133/133 pts within 0.003°); attaching would double-draw with the jijia group owner",
    # Brăila
    "anpa-anpa-0203": "Japșa Corotisca (3 ha, mal drept Dunăre km 171): no named OSM lake at the Brăila Danube right bank",
    "anpa-anpa-0205": "Japșa Poala Albă (8 ha, braț mort al Buzăului UAT Ibrianu): no named OSM lake near Ibrianu",
    "anpa-anpa-0206": "Valea Encii (5 km, ANIF desecare Comăneasca): drainage network, no OSM named water",
    # Constanța
    "anpa-anpa-0248": "Canal Poarta Albă – Midia Năvodari: no named OSM way/lake for the PAMN canal in the dump",
    "anpa-anpa-0249": "Canal apă caldă Cernavodă: no named OSM way for the hot-water discharge canal",
    # Giurgiu
    "anpa-anpa-0302": "Râul Șaica (10 ha, 'Vedea' limits): no OSM candidate; limits text appears to be a data error",
    # Ialomița
    "anpa-anpa-0387": "Canalul Saltava (70 ha, desecare IAS Făcăieni): no OSM 'Saltava' waterway in Ialomița",
    "anpa-anpa-0386": "Potcoava Bordușani (10 ha, mal drept baraj Borcea): only unnamed lakes at Bordușani (ways 86127473/88363518, no name tags); no named OSM match",
    # Vaslui
    "anpa-anpa-0627": "Pârâu Elan (67 km, Ivănești Huși–conf. Prut): no OSM 'Elan' way in the extract (only Prut/Bârlad/Vaslui/Tigheci named in the valley)",
}

CHAIN_TOL = 0.006


def geom_parts(g: dict):
    if g.get("type") == "LineString":
        return [g["coordinates"]]
    return g.get("coordinates", [])


def chain_tolerant(parts, tol=CHAIN_TOL):
    """Chain parts by near-endpoint connectivity (tolerance for moved nodes)."""
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


def load_raw_ways():
    """way_id -> [(lon, lat), ...] from the waterway dump."""
    d = json.loads(WATER_ALL_JSON.read_text(encoding="utf-8"))
    nodes = {el["id"]: (el["lon"], el["lat"]) for el in d["elements"] if el["type"] == "node"}
    out = {}
    for el in d["elements"]:
        if el["type"] != "way":
            continue
        pts = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if pts:
            out[el["id"]] = pts
    return out


def load_poly_rings():
    """way_id -> closed ring [(lon,lat),...] from the water-polygons dump."""
    d = json.loads(WATER_POLYS_JSON.read_text(encoding="utf-8"))
    nodes = {el["id"]: (el["lon"], el["lat"]) for el in d["elements"] if el["type"] == "node"}
    out = {}
    for el in d["elements"]:
        if el["type"] != "way":
            continue
        pts = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if len(pts) >= 4:
            out[el["id"]] = pts
    return out


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
    print(f"[batch6] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

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
    print(f"[batch6] target: {len(target)} waters")

    report = {"fixed": [], "unmatchable": [], "group_shared": []}
    changed = []
    handled = set()

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    raw_ways = load_raw_ways()
    poly_rings = load_poly_rings()

    # ---- pre-pass: RAW_WAYS (unnamed OSM courses) -------------------------
    for slug, cfg in RAW_WAYS.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing RAW_WAYS water {slug}")
        parts = []
        for wid in cfg["ways"]:
            pts = raw_ways.get(wid)
            if pts:
                parts.append(list(pts))
        if not parts:
            print(f"  !! RAW {slug}: no ways found")
            continue
        from sweep_multiway_rivers import chain_parts, flatten
        chain = chain_parts(parts)
        if chain is None:
            chain = chain_tolerant(parts)
        if chain is None:
            chain = [max(parts, key=len)]
        out_geom = flatten(chain)
        # orient source-first: Lesuntu flows south into Oituz (source = higher lat)
        if slug == "19468k28":
            coords = out_geom["coordinates"]
            if coords[0][1] < coords[-1][1]:
                out_geom["coordinates"] = list(reversed(coords))
        w["geometry"] = out_geom
        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        w["geometryByCounty"] = {}
        w["source_detail"] = "geometry_batch6:raw-ways"
        handled.add(slug)
        ind, maj, tot = county_hits(cluster_points(out_geom), polygons, w["judet"])
        report["fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "source": "river",
            "osmc": "+".join(f"way{wid}" for wid in cfg["ways"]),
            "in_county_pts": ind, "majority": maj, "note": cfg["note"],
        })
        print(f"  FIX   {w['judet']:10} {w['name'][:44]:46} <- [raw-ways] "
              f"{cfg['note'][:40]} (in={ind} maj={maj}) bbox={[round(x,2) for x in w['bbox']]}")
        changed.append(w)

    # ---- pre-pass: RESERVOIR_REACH (Izbiceni) -----------------------------
    for slug, cfg in RESERVOIR_REACH.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing RESERVOIR_REACH water {slug}")
        rings = []
        for wid in cfg["ways"]:
            pts = poly_rings.get(wid)
            if not pts:
                print(f"  !! RESERVOIR {slug}: way {wid} missing")
                continue
            # clip to the reach band and close the ring
            clipped = [p for p in pts if cfg["min_lat"] <= p[1] <= cfg["max_lat"]]
            if len(clipped) < 4:
                continue
            if clipped[0] != clipped[-1]:
                clipped.append(clipped[0])
            rings.append(clipped)
        if not rings:
            print(f"  !! RESERVOIR {slug}: no rings")
            continue
        out_geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
        w["geometry"] = out_geom
        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        w["geometryByCounty"] = {}
        w["source_detail"] = "geometry_batch6:reservoir-reach"
        handled.add(slug)
        ind, maj, tot = county_hits(cluster_points(out_geom), polygons, w["judet"])
        report["fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "source": "lake",
            "osmc": "Olt-reservoir-relation-2435464", "in_county_pts": ind,
            "majority": maj, "note": f"{len(rings)} outer rings, {cfg['min_lat']}-{cfg['max_lat']}N reach",
        })
        print(f"  FIX   {w['judet']:10} {w['name'][:44]:46} <- [reservoir-reach] "
              f"{len(rings)} rings (in={ind} maj={maj}) bbox={[round(x,2) for x in w['bbox']]}")
        changed.append(w)

    # ---- pre-pass: LAKE_MERGE (Frunzaru) -----------------------------------
    for slug, lake_norm in LAKE_MERGE.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing LAKE_MERGE water {slug}")
        entries = lakes_by_norm.get(lake_norm, [])
        polys = []
        for l in entries:
            g = l["geom"]
            if g["type"] == "Polygon":
                polys.append(g["coordinates"])
            elif g["type"] == "MultiPolygon":
                polys.extend(g["coordinates"])
        if not polys:
            print(f"  !! LAKE_MERGE {slug}: no polygons for {lake_norm}")
            continue
        out_geom = {"type": "MultiPolygon", "coordinates": polys}
        w["geometry"] = out_geom
        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        w["geometryByCounty"] = {}
        w["source_detail"] = "geometry_batch6:lake-merge"
        handled.add(slug)
        ind, maj, tot = county_hits(cluster_points(out_geom), polygons, w["judet"])
        report["fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "source": "lake",
            "osmc": lake_norm, "in_county_pts": ind, "majority": maj,
            "note": f"merged {len(polys)} polygon parts",
        })
        print(f"  FIX   {w['judet']:10} {w['name'][:44]:46} <- [lake-merge] "
              f"{lake_norm} ({len(polys)} parts, in={ind} maj={maj}) bbox={[round(x,2) for x in w['bbox']]}")
        changed.append(w)

    # ---- pre-pass: DIRECT_LAKE ---------------------------------------------
    for slug, lake_norm in DIRECT_LAKE.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing DIRECT_LAKE water {slug}")
        entries = lakes_by_norm.get(lake_norm, [])
        if not entries:
            print(f"  !! DIRECT_LAKE {slug}: no lake {lake_norm}")
            continue
        out_geom = entries[0]["geom"]
        w["geometry"] = out_geom
        w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
        w["geometryByCounty"] = {}
        w["source_detail"] = "geometry_batch6:direct-lake"
        handled.add(slug)
        ind, maj, tot = county_hits(cluster_points(out_geom), polygons, w["judet"])
        report["fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "source": "lake",
            "osmc": lake_norm, "in_county_pts": ind, "majority": maj,
            "note": "contract limits span the lake",
        })
        print(f"  FIX   {w['judet']:10} {w['name'][:44]:46} <- [direct-lake] "
              f"{lake_norm} (in={ind} maj={maj}) bbox={[round(x,2) for x in w['bbox']]}")
        changed.append(w)

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
        best = pick_best(cands, declared, polygons)
        if w.get("subtype") == "lac":
            lake_best = pick_best([c for c in cands if c[0] == "lake"], declared, polygons)
            if lake_best:
                best = lake_best
        if best:
            score, in_dec, majority, sd, src, cname, geom, bb = best
            if src == "river":
                out_geom = chain_course(geom, slug)
            else:
                out_geom = geom
            w["geometry"] = out_geom
            w["bbox"] = [round(v, 5) for v in bb]
            w["source_detail"] = "geometry_batch6:" + src
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
    print(f"\n[batch6] fixed={fixed} group_shared={shared} unmatchable={unm}")
    print(f"[batch6] TOTAL handled={fixed + unm + shared} (target={len(target)})")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
