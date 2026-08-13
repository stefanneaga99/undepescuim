#!/usr/bin/env python3
"""GEOMETRY batch 1/6 (t_21fd2a04): attach OSM geometry to the 88 contracted
waters without geometry in Suceava/Vâlcea/Maramureș/Alba.

Strategy per water:
  A. Group member whose riverGroup ALREADY has a geometry owner -> stays
     geometry-less by design (one-owner-per-group, skill pitfall #4).
     The two broken groups in this batch (iza, geoagiu — no sector data, Iza
     owner holds a 2-point stub) get fixed in a pre-pass: full-course re-attach
     + official-km sector intervals (pitfall #5).
  B. Otherwise: county-guarded candidate scoring over OSM river clusters
     (data/cache/osm_river_clusters.pkl) + Overpass lake polygons
     (data/processed/overpass_named_lakes*.json), attaching the best
     candidate that TOUCHES the declared county polygon. Rivers become a
     single ordered LineString; lakes keep their Polygon/MultiPolygon.
  C. Unmatchable -> keep bbox fallback, document in the report.

Usage:
  python3 scripts/geometry_batch1_attach.py            # dry run (report only)
  python3 scripts/geometry_batch1_attach.py --write    # apply to waters.json
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

BATCH_COUNTIES = ["Suceava", "Vâlcea", "Maramureș", "Alba"]

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
    "Alba": (23.57, 46.08), "Maramureș": (23.89, 47.66), "Suceava": (26.25, 47.65),
    "Vâlcea": (24.37, 45.10),
}

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)

# Batch-specific OSM-name overrides: core(water name) -> OSM index name to look
# up. Same philosophy as audit_missing_rivers.MANUAL_OVERRIDES; every attach is
# still county-polygon-guarded.
NAME_OVERRIDES = {
    "mogos cotu": "valea mogosului",          # Râul Mogoș-Cotu (Alba) == OSM Valea Mogoșului
    "salane": "salanele",                     # Râul Salane (Alba, izvoare->lac Oașa) == OSM Sălanele
    "marele novat": "novat",                  # Marele Novat (MM) == OSM Novăț (Vaser trib)
    "baita nistru": "baita",                  # Râul Băița Nistru (MM) == OSM Băița
    "calinesti cu paraiele calinesti sulita soci si lotrisor": "calinesti",
    "urii cu paraiele uria si murgoci": "uria",
    "lotrisor draganesti": "lotrisor",
}

# Waters with a KNOWN no-in-county-course outcome (verified against the current
# extract in this batch): keep bbox fallback, no geometry.
KEEP_BBOX = {
    "anpa-anpa-0559",  # Acumulare Dragomira — only a STREAM named Dragomirna in OSM, no reservoir polygon
    "romsilva-suceava-afluentii-suhei",  # named Suha Mare/Mică in OSM are Moldova-basin streams, not Suha tributaries
    "romsilva-suceava-izvoarele-dornei",  # main Dorna course already drawn under 'Râul Dorna inferioară' (ANPA)
    "romsilva-suceava-valea-putnei",  # same course already drawn under 'Râul Putna' (Suceava, Romsilva)
    "romsilva-alba-izvoarele-ampoiului",  # upper Ampoi above Zlatna not mapped under that name; ANPA Ampoi draws the lower course only
    "romsilva-valcea-izvoarele-latoritei",  # overlaps the existing latorita group sectors (Superioară owns the course)
    "anpa-anpa-0574",  # Izvoarele Moldovei și Sucevei — composite of two already-drawn rivers (Moldova group + Râul Suceava)
}

# Waters already FORCE_DROP'd in fix_wrong_county_geometry.py (same-name OSM
# river exists ONLY in another county) — verified against the current extract.
FORCE_DROP = {
    "fee3lhad",      # Râul Valea Morilor Alba — no OSM Morii near Huda lui Papară
    "ii25s9zo",      # Pârâul Murgoci Vâlcea — OSM Murgoci in Neamț
    "anpa-anpa-0422",  # Valea Rotundă Maramureș — OSM Rotunda in Vâlcea
}

# Official-km sector splits for the two broken groups in this batch (skill
# pitfall #5: upstream sector = lower fraction). Slugs of the group members.
#   Iza: izvorul 10km + superioară 40km + (rest) 33km = 83km
IZA_SECTORS = {
    "anpa-anpa-0407": (0.0, 10 / 83, "iza"),          # Izvorul Izei (joins iza group)
    "anpa-anpa-0408": (10 / 83, 50 / 83, "iza"),      # Râul Iza superioară
    "anpa-anpa-0405": (50 / 83, 1.0, "iza"),          # Râul Iza (geometry owner)
}
#   Geoagiu: superior 9km + inferior 28km = 37km
GEOAGIU_SECTORS = {
    "z8u6g69z": (0.0, 9 / 37, "geoagiu"),             # Râul Geoagiu Superior
    "4pouq9sd": (9 / 37, 1.0, "geoagiu"),             # Råul Geoagiu Inferior (geometry owner)
}

# The Iza owner holds a 2-point stub; re-attach the full course chained by
# endpoint connectivity, oriented source->mouth with the Moisei anchor
# (the Iza flows NW — the latitude heuristic inverts it).
IZA_OWNER_REATTACH = "anpa-anpa-0405"
IZA_SOURCE_ANCHOR = (24.53, 47.66)  # Moisei bridge (pod DN Moisei, contract boundary)

# Composite river attach for 'Râul Canciu- Bosorogu' (O.S. Cugir): the two
# named valleys (Valea Canciului + Boșorogul) near the Acumulare Canciu.
# The Canciu LAKE polygon is excluded — it belongs to the separate
# 'Acumulare Canciu' contract (hdqe290r).
CANCIU_RIVER_NAMES = ["valea canciului", "bosorogul"]


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
    """Core name for reservoir/accumulation contracts.

    'Acumularea Băbeni cu bălțile adiacente' -> 'babeni'
    'Acumulare Dragomira' -> 'dragomira'
    'Lacul Vlădești' -> 'vladesti'
    """
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


def seat_dist(declared, bb):
    seat = COUNTY_SEATS.get(declared)
    if not seat or not bb:
        return None
    cpt = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
    return math.hypot(cpt[0] - seat[0], cpt[1] - seat[1])


def pick_best(candidates, declared, polygons):
    """Best candidate touching the declared county (fix_wrong_county pattern)."""
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


def reverse_chain(chain):
    """Reverse a chained part list (order AND each part's direction)."""
    return [list(reversed(p)) for p in reversed(chain)]


def chain_iz_course(by_norm):
    """Full Iza course as ONE ordered LineString (source -> mouth).

    The cluster is a MultiLineString with the same ways mapped twice; dedupe
    by endpoint connectivity (sweep_multiway_rivers.chain_parts), then orient
    source->mouth with the Moisei bridge as the source anchor (the Iza flows
    NW, so the generic latitude heuristic would invert it).
    """
    from sweep_multiway_rivers import chain_parts, flatten

    iza_clusters = [cl for cl in by_norm.get("iza", [])
                    if cl["geom"]["type"] == "MultiLineString"]
    if not iza_clusters:
        return None
    parts = [list(p) for p in iza_clusters[0]["geom"]["coordinates"]]
    chain = chain_parts(parts)
    if not chain:
        return None
    start = chain[0][0]
    end = chain[-1][-1]
    d_start = (start[0] - IZA_SOURCE_ANCHOR[0]) ** 2 + (start[1] - IZA_SOURCE_ANCHOR[1]) ** 2
    d_end = (end[0] - IZA_SOURCE_ANCHOR[0]) ** 2 + (end[1] - IZA_SOURCE_ANCHOR[1]) ** 2
    if d_start > d_end:
        chain = reverse_chain(chain)
    return flatten(chain)


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
    print(f"[batch1] {len(waters)} waters, {len(clusters)} clusters, {len(all_lakes)} lakes")

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
    print(f"[batch1] target: {len(target)} waters")

    report = {"fixed": [], "unmatchable": [], "group_shared": [], "sector_fixed": []}
    changed = []
    handled = set()

    def w_by_slug(slug):
        for w in waters:
            if w["slug"] == slug:
                return w
        return None

    # ---- pre-pass: broken groups (iza, geoagiu) ---------------------------
    iza_course = chain_iz_course(by_norm)
    if iza_course:
        owner = w_by_slug(IZA_OWNER_REATTACH)
        if owner is None:
            raise SystemExit(f"missing water {IZA_OWNER_REATTACH}")
        owner["geometry"] = iza_course
        bb = geom_bbox(iza_course)
        owner["bbox"] = [round(v, 5) for v in bb]
        owner["geometryByCounty"] = {}
        owner["source_detail"] = "geometry_batch1:iza_full_course"
        report["fixed"].append({
            "slug": IZA_OWNER_REATTACH, "name": owner["name"], "judet": owner["judet"],
            "source": "owner_reattach", "osmc": "Iza (full course)", "in_county_pts": None,
            "majority": None,
        })
        print(f"  REATTACH {owner['judet']:10} {owner['name'][:44]:46} <- Iza full course "
              f"({len(iza_course['coordinates'])} pts)")
        changed.append(owner)
    else:
        print("  !! Iza full-course chain failed")

    for slug, (ss, se, grp) in {**IZA_SECTORS, **GEOAGIU_SECTORS}.items():
        w = w_by_slug(slug)
        if w is None:
            continue
        w["sectorStart"], w["sectorEnd"] = round(ss, 4), round(se, 4)
        if w.get("riverGroup") != grp:
            w["riverGroup"] = grp
        report["sector_fixed"].append({
            "slug": slug, "name": w["name"], "judet": w["judet"], "group": grp,
            "sectorStart": round(ss, 4), "sectorEnd": round(se, 4),
        })
        print(f"  SECTOR {w['judet']:10} {w['name'][:44]:46} -> {grp} [{ss:.3f}, {se:.3f}]")
        changed.append(w)
        handled.add(slug)

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

        # composite: Râul Canciu- Bosorogu (two valleys, NO lake polygon)
        if slug == "romsilva-alba-canciu-bosorogu":
            parts = []
            ok_names = []
            for nk in CANCIU_RIVER_NAMES:
                for cl in by_norm.get(nk, []):
                    in_dec, majority, total = county_hits(cluster_points(cl["geom"]), polygons, declared)
                    if in_dec > 0 or majority == declared:
                        parts.append(cl["geom"])
                        ok_names.append(cl.get("raw_name") or cl["name"])
            if parts:
                from _mapping_common import merge_geoms
                geom = merge_geoms(parts)
                bb = geom_bbox(geom)
                w["geometry"] = geom
                w["bbox"] = [round(v, 5) for v in bb]
                w["source_detail"] = "geometry_batch1:canciu_composite"
                w["geometryByCounty"] = {}
                report["fixed"].append({
                    "slug": slug, "name": name, "judet": declared, "source": "river",
                    "osmc": " + ".join(ok_names), "in_county_pts": None, "majority": None,
                })
                print(f"  FIX   {declared:10} {name[:44]:46} <- [river] {', '.join(ok_names)}")
                changed.append(w)
            else:
                report["unmatchable"].append({
                    "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                    "old_bbox": w.get("bbox"),
                    "note": "no in-county candidate for Canciu/Bosorogu valleys",
                })
                print(f"  KEEP  {declared:10} {name[:44]:46} (no in-county Canciu/Bosorogu valley)")
            continue

        if slug in KEEP_BBOX:
            report["unmatchable"].append({
                "slug": slug, "name": name, "judet": declared, "action": "keep-bbox",
                "old_bbox": w.get("bbox"),
                "note": "no attachable geometry (see KEEP_BBOX rationale)",
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

        if slug in FORCE_DROP:
            report["unmatchable"].append({
                "slug": slug, "name": name, "judet": declared, "action": "drop-geometry",
                "old_bbox": w.get("bbox"),
                "note": "no credible in-county OSM course (same-name river exists in another county)",
            })
            print(f"  DROP  {declared:10} {name[:44]:46} (forced drop, keep bbox)")
            continue

        cands = collect(name, slug)
        best = pick_best(cands, declared, polygons)
        if best:
            score, in_dec, majority, sd, src, cname, geom, bb = best
            if src == "river":
                out_geom = order_linestring(geom)
            else:
                out_geom = geom
            w["geometry"] = out_geom
            w["bbox"] = [round(v, 5) for v in bb]
            w["source_detail"] = "geometry_batch1:" + src
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
    print(f"\n[batch1] fixed={fixed} sector_fixed={sectors} group_shared={shared} unmatchable={unm}")
    print(f"[batch1] TOTAL handled={fixed + unm + shared + sectors}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
