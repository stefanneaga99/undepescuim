#!/usr/bin/env python3
"""GEOMETRY batch 2/6 (t_0d20d433): attach OSM geometry to the 73 contracted
waters without geometry in Hunedoara/Arad/Bihor/Harghita.

Strategy per water (same as batch 1, scripts/geometry_batch1_attach.py):
  A. Group member whose riverGroup ALREADY has a geometry owner -> stays
     geometry-less by design (one-owner-per-group, skill pitfall #4).
  B. Ownerless multi-sector groups (nucsor, moneasa, iadului) get a pre-pass:
     ONE geometry owner + official-km sector intervals for both members
     (pitfall #5: upstream sector = lower fraction).
  C. Otherwise: county-guarded candidate scoring over OSM river clusters
     (data/cache/osm_river_clusters.pkl) + Overpass lake polygons
     (data/processed/overpass_named_lakes*.json), attaching the best
     candidate that TOUCHES the declared county polygon. Rivers become a
     single ordered LineString; lakes keep their Polygon/MultiPolygon.
  D. Unmatchable -> keep bbox fallback, document in the report. KEEP_BBOX
     entries are the deliberate ones (course already drawn under another
     contract, or no in-county named OSM feature).

Usage:
  python3 scripts/geometry_batch2_attach.py            # dry run (report only)
  python3 scripts/geometry_batch2_attach.py --write    # apply to waters.json
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

BATCH_COUNTIES = ["Hunedoara", "Arad", "Bihor", "Harghita"]

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
    "Hunedoara": (22.91, 45.87), "Arad": (21.32, 46.18),
    "Bihor": (21.93, 47.07), "Harghita": (25.79, 46.36),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)

# Batch-specific OSM-name overrides: core(water name) -> OSM index name to look
# up. Every attach is still county-polygon-guarded (pitfall #30).
NAME_OVERRIDES = {
    "dobrei": "dobra",              # Valea Dobrei (HD) == OSM Dobra river
    "luncanilor": "luncani",        # Valea Luncanilor (HD) == OSM Luncani
    "vermet": "paraul vermed",      # Pârâul Vermet (HR) == OSM Pârâul Vermed
    "aszo mitacs": "paraul mitaci", # Pârâul Aszo Mitacs (HR) == OSM Pârâul Mitaci (Olt trib, Tușnad)
    "leuca": "valea leucii",        # Râul Leuca (AR) == OSM Valea Leucii
    "halmagiu": "halmagel",         # Râul Hălmagiu (AR) == OSM Hălmăgel (upper course)
    "vl finis finisului": "finis",  # Râul Vl. Finiş (Finişului) (BH) == OSM Finiș
}

# Ownerless multi-sector groups -> ONE geometry owner + official-km sectors.
# slug: (cluster_norm_or_None, sectorStart, sectorEnd)
#   Nucșorul (HD): Superior 21 km izvoare->Cârnic, Inferior 34 km Cârnic->Valea Streiului (55 total)
#   Moneasa (AR): Superioară 41 km izvoare->aval Dezna, Inferioară 17 km Dezna->Crișul Alb (58 total)
#   Iadului (BH): Superior 23 km Izvorul Minunilor->Lac Leșu, Inferior 21 km Baraj Leșu->Crișul Repede (44 total)
GROUP_PREPASS = {
    "romsilva-hunedoara-nucsorul-superior": ("nucsoara", 0.0, 21 / 55),
    "romsilva-hunedoara-nucsorul-inferior": (None, 21 / 55, 1.0),
    "romsilva-arad-moneasa-superioara": ("valea monesei", 0.0, 41 / 58),
    "romsilva-arad-moneasa-inferioara": (None, 41 / 58, 1.0),
    "romsilva-bihor-valea-iadului-superior": ("iada", 0.0, 23 / 44),
    "romsilva-bihor-valea-iadului-inferior": (None, 23 / 44, 1.0),
}

# Deliberate keep-bbox: a candidate EXISTS (or the river is already mapped)
# but attaching would double-draw or misrepresent the contract.
KEEP_BBOX = {
    "anpa-anpa-0356": "Râul Mare course already drawn under 'Râul Mare Superior' (romsilva-hunedoara-raul-mare-superior); attaching would double-draw",
    "0b5imfgi": "Ier course already drawn under 'Râul Ierul' (anpa-anpa-0040); full-cluster attach would overlap",
    "romsilva-bihor-valea-draganului": "Drăgan course already drawn under 'Drăgan' (romsilva-bihor-dragan); sector-join deferred to merge task",
    "romsilva-harghita-lac-baraj-paraul-rosu": "Lacul Roșu polygon already drawn under 'Lacul Roșu' (3klq13bv); no separate 3 Ha barrage polygon in OSM",
    "anpa-anpa-0363": "no named Ostrov reservoir polygon in OSM dump; OSM 'Ostrov' lake is in Hungary",
}

# Source anchors for rivers whose course the generic latitude ordering would
# invert (pitfall #18b). After chaining, orient so the end nearest the source
# anchor comes FIRST. Critical for the multi-member sector groups (nucsor,
# moneasa, iadului); kept for single-member Valea Dobrei as a safety net.
ORIENT_SOURCE = {
    "romsilva-hunedoara-nucsorul-superior": (22.9063, 45.4770),   # headwater north of Cârnic
    "romsilva-arad-moneasa-superioara": (22.2983, 46.4721),       # Moneasa springs
    "romsilva-bihor-valea-iadului-superior": (22.6235, 46.6894),  # Izvorul Minunilor / Stâna de Vale
    "romsilva-hunedoara-valea-dobrei": (22.5282, 45.7179),        # headwater south of Dobra
}

# Part indices to DROP before chaining (parallel duplicated ways / interior
# stubs that break single-path connectivity):
#   Vl. Finiş (BH): part 1 is a parallel duplicate of the middle reach
#                   (shares the (22.2921,46.6219) junction with the main way).
#   Pârâul Vermet (HR): part 1 is an interior stub overlapping the main way.
MANUAL_DROP = {
    "romsilva-bihor-vl-finis-finisului": [1],
    "anpa-anpa-0348": [1],
}

# Chaining tolerance for near-but-not-exact way junctions (OSM splits ways at
# slightly moved nodes). The Iada's 4 parts connect within ~0.003 deg (~300 m);
# bridges are documented straight segments (Siret Răcăciuni precedent, #25).
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
            return None
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
    return PREFIX_RE.sub("", norm(name), count=1).strip()


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
    n = PREFIX_RE.sub("", n, count=1)
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
    print(f"[batch2] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

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
    print(f"[batch2] target: {len(target)} waters")

    report = {"fixed": [], "unmatchable": [], "group_shared": [], "sector_fixed": []}
    changed = []
    handled = set()

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    # ---- pre-pass: ownerless multi-sector groups -------------------------
    for slug, (cluster_norm, ss, se) in GROUP_PREPASS.items():
        w = w_by_slug(slug)
        if w is None:
            raise SystemExit(f"missing water {slug}")
        handled.add(slug)
        w["sectorStart"], w["sectorEnd"] = round(ss, 4), round(se, 4)
        if cluster_norm:
            cls_ = by_norm.get(cluster_norm, [])
            in_dec, majority, total = county_hits(
                cluster_points(cls_[0]["geom"]) if cls_ else [], polygons, w["judet"])
            if cls_ and (in_dec > 0 or majority == w["judet"]):
                out_geom = chain_course(cls_[0]["geom"], slug)
                if slug in ORIENT_SOURCE:
                    out_geom = orient_course(out_geom, ORIENT_SOURCE[slug])
                w["geometry"] = out_geom
                w["bbox"] = [round(v, 5) for v in geom_bbox(out_geom)]
                w["geometryByCounty"] = {}
                w["source_detail"] = "geometry_batch2:prepass:" + cluster_norm
                print(f"  PREPASS {w['judet']:10} {w['name'][:44]:46} <- [{cluster_norm}] "
                      f"in={in_dec} maj={majority} sector=[{ss:.4f},{se:.4f}]")
            else:
                print(f"  !! PREPASS {w['judet']:10} {w['name'][:44]:46} no in-county cluster "
                      f"'{cluster_norm}' (in={in_dec} maj={majority})")
                report["unmatchable"].append({
                    "slug": slug, "name": w["name"], "judet": w["judet"], "action": "keep-bbox",
                    "note": f"prepass owner cluster '{cluster_norm}' not in county",
                })
                continue
        else:
            print(f"  PREPASS {w['judet']:10} {w['name'][:44]:46} sector=[{ss:.4f},{se:.4f}] "
                  f"(shares group course)")
        report["sector_fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"],
            "group": w.get("riverGroup"),
            "sectorStart": round(ss, 4), "sectorEnd": round(se, 4),
            "owner": bool(cluster_norm),
        })
        changed.append(w)

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
        best = pick_best(cands, declared, polygons)
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
            w["source_detail"] = "geometry_batch2:" + src
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
    print(f"\n[batch2] fixed={fixed} sector_fixed={sectors} group_shared={shared} unmatchable={unm}")
    print(f"[batch2] TOTAL handled={fixed + unm + shared + sectors}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
