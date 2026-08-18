#!/usr/bin/env python3
"""Re-attach correct OSM geometry for waters whose geometry lies in the wrong
county (data-integrity sweep, Homorodul Nou class of bug).

Strategy per flagged water (from validate_geometry_county.py):
  1. Collect candidates: OSM river clusters AND lake polygons whose name
     matches (exact variant, core-equal, or an explicit override target).
  2. Keep candidates that actually TOUCH the declared county (any dense sample
     point inside the county polygon, OR majority county == declared).
  3. Attach the best candidate (highest in-county points, then closest to the
     county seat) as a single ordered LineString (rivers) or the raw Polygon
     (lakes). Multi-county clusters (Crasna: Sălaj+Satu Mare) are accepted as
     long as they touch the declared county.
  4. No candidate -> drop geometry (bbox fallback).

Usage:
    python3 scripts/fix_wrong_county_geometry.py [--dry-run] [--json OUT.json]
"""

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
COUNTY_DIR = ROOT / "data" / "raw" / "county_boundaries"

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
    "Alba": (23.57, 46.08), "Arad": (21.32, 46.18), "Argeș": (24.82, 44.94),
    "Bacău": (26.91, 46.57), "Bihor": (21.94, 47.07), "Bistrița-Năsăud": (24.50, 47.13),
    "Botoșani": (26.67, 47.75), "Brașov": (25.61, 45.65), "Brăila": (27.97, 45.27),
    "Buzău": (26.78, 45.15), "Caraș-Severin": (21.90, 45.42), "Călărași": (26.82, 44.20),
    "Cluj": (23.62, 46.77), "Constanța": (28.65, 44.17), "Covasna": (26.01, 45.90),
    "Dâmbovița": (25.46, 44.93), "Dolj": (23.79, 44.33), "Galați": (28.01, 45.43),
    "Giurgiu": (25.97, 43.90), "Gorj": (23.26, 45.03), "Harghita": (25.62, 46.35),
    "Hunedoara": (22.91, 45.75), "Ialomița": (27.60, 44.56), "Iași": (27.60, 47.16),
    "Ilfov": (26.10, 44.44), "Maramureș": (23.89, 47.66), "Mehedinți": (22.66, 44.64),
    "Mureș": (24.56, 46.54), "Neamț": (26.38, 46.93), "Olt": (24.48, 44.43),
    "Prahova": (26.02, 44.94), "Satu Mare": (22.87, 47.79), "Sălaj": (23.05, 47.18),
    "Sibiu": (24.15, 45.80), "Suceava": (26.25, 47.65), "Teleorman": (25.34, 43.75),
    "Timiș": (21.22, 45.75), "Tulcea": (28.80, 45.18), "Vaslui": (27.73, 46.64),
    "Vâlcea": (24.37, 45.10), "Vrancea": (27.18, 45.70), "București": (26.10, 44.43),
}

SEAT_DIST_MAX_DEG = 1.5

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)

# water name (core) -> OSM name to look up when the extract's naming differs
# (mirrors MANUAL_OVERRIDES in audit_missing_rivers.py, county-guarded here)
NAME_OVERRIDES = {
    "morilor": "paraul morii",        # Valea Morilor (Alba, Huda lui Papară)
    "baicu": "izvorul baicului",      # Râul Baicu (Maramureș) — OSM source name
    "apa calda cernavoda": "apa calda",
    "stegii": "paraul stegii",
    "tau": "lacul de acumulare tau",  # Acumulare Tău (Alba, O.S. Sebeș) — reservoir
    "saliste": "raul negru",          # Râul Săliște (Sibiu) — OSM names the Săliște course Râul Negru (Sibiu clusters)
    "almasului": "almas",             # Valea Almașului (Sălaj) — OSM names the Almaș valley river 'almas' (Sălaj cluster)
    "motru mare": "motru",            # Râul Motru Mare (Gorj) — OSM 'motru' cluster touches Gorj (headwaters at D.N. 67D)
    "vasluiet": "vaslui",             # Râul Vasluieț (Vaslui) — OSM names the Vasluieț course 'vaslui' (Vaslui cluster)
    "geoagiu inferior": "stremt",     # Råul Geoagiu Inferior (Alba) — areba bbox matches OSM 'stremt' course exactly
                                      # (Cheile Râmeț → conf. Mureș); the Alba Geoagiu is OSM-named Stremț
    "gradistea inferioara": "orastie", # Grădiștea inferioară (Hunedoara) — cabana Costești→Mureș is the Orăștie course
}

# slug -> OSM lake name when the ANPA/Romsilva name differs from OSM entirely
LAKE_NAME_BY_SLUG = {
    "gizkgxdq": "lacul de acumulare vida",  # Lacul Toplița (Bihor) == Vida reservoir
    "romsilva-hunedoara-papusa": "taul papusii",  # Păpușa (D.S. Hunedoara, Țarcu) == Tăul Păpușii, not the Gorj Păpușa lake
}

# flagged waters whose geometry should be dropped entirely (no credible OSM
# course in the declared county — checked against the extract, documented in
# the task report). Keyed by slug.
FORCE_DROP = {
    "anpa-anpa-0159",  # Râul Sărata Botoșani — OSM Sărata only in other counties
    "pgabr5sd",        # Râul Bahna Botoșani — OSM Bahna only in Neamț/Mehedinți
    "anpa-anpa-0354",  # Valea Corbului Harghita — OSM Valea Corbului in Maramureș
    "anpa-anpa-0422",  # Valea Rotundă Maramureș — OSM Rotunda in Vâlcea
    "ii25s9zo",        # Pârâul Murgoci Vâlcea — OSM Murgoci in Neamț
    "anpa-anpa-0606",  # Pârâul Ier Timiș — OSM Ier only in Bihor/Satu Mare
    "anpa-anpa-0249",  # Canal apă caldă Cernavodă — no OSM canal in Constanța
    "anpa-anpa-0233",  # Balta Valea Mare Călărași — OSM Balta Valea Mare in Covasna
    "dre11dij",        # Râul Poiana Bihor — OSM Poiana in Maramureș/B-N
    "romsilva-sibiu-bistra",  # Râul Bistra Sibiu — no OSM Bistra in Sibiu
    "fee3lhad",        # Râul Valea Morilor Alba — no OSM Morii near Huda lui Papară
    "anpa-anpa-0227",  # Valea Mare CS (Ilidia) — OSM Valea Mare in CS is 40km E of Ilidia; actual Ilidia course unnamed
}

# slug -> water whose current geometry is CORRECT and must be KEPT even though
# the strict county-polygon test flags it: border-attribution artifacts where
# the OSM course is the right feature but sits just across the county line
# (e.g. Râul Șugo Covasna — Romsilva D.S. Covasna manages it, flows into the
# Vîrghiș border stream, OSM Pârâul Șugo is 0.4 km from the Covasna boundary).
KEEP_GEOMETRY = {
    "romsilva-covasna-sugo",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def core(name):
    return PREFIX_RE.sub("", norm(name), count=1).strip()


def strip_article(tok):
    if len(tok) >= 5 and tok.endswith("ul"):
        return {tok, tok[:-2], tok[:-1]}
    if len(tok) >= 5 and tok.endswith("l") and tok[-2] in "aeiou":
        return {tok, tok[:-1]}
    if len(tok) >= 5 and tok.endswith("u") and tok[-2] not in "aeiou":
        return {tok, tok[:-1]}
    return {tok}


def name_variants(name):
    c = core(name)
    toks = c.split()
    if not toks:
        return set()
    first_variants = strip_article(toks[0])
    out = set()
    for fv in first_variants:
        out.add(" ".join([fv, *toks[1:]]))
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


def cluster_points(cluster):
    g = cluster["geom"]
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
    """(hits_in_declared, majority_county, total_hits) for ≤61 sample points."""
    cn = norm(county)
    target = None
    for name, pgeom, pbbox in polygons:
        if norm(name) == cn:
            target = (pgeom, pbbox)
            break
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


def seat_dist(declared, bbox):
    seat = COUNTY_SEATS.get(declared)
    if not seat:
        return None
    cpt = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    return math.hypot(cpt[0] - seat[0], cpt[1] - seat[1])


def order_linestring(geom):
    from _mapping_common import order_course_linestring
    return order_course_linestring(geom)


def geom_bbox(g):
    pts = cluster_points({"geom": g})
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


def pick_best(candidates, declared, polygons):
    """Return the candidate that best fits the declared county.

    candidate: (source_kind, name, geom, bbox)
    Score: candidates that touch the declared county (in_declared>0) first,
    then majority-county == declared, then closest to the county seat.
    """
    scored = []
    for src, name, geom, bb in candidates:
        pts = cluster_points({"geom": geom})
        if not pts or not bb:
            continue
        in_dec, majority, total = county_hits(pts, polygons, declared)
        if in_dec == 0 and majority != declared:
            continue  # doesn't touch the declared county at all
        sd = seat_dist(declared, bb) or 99.0
        score = 1000.0 * in_dec + (10.0 if majority == declared else 0.0) - sd
        scored.append((score, in_dec, majority, sd, src, name, geom, bb))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


# slug -> manual course build (way ids in order; the last bridge is drawn as
# a straight segment when endpoints don't touch). Used when OSM has the real
# river split across unnamed ways + a canal with a different name (Homorodul
# Nou = unnamed upper stream + Canalul Homorod, documented bridge at Tătărești
# → Hrip, ~3.3 km gap).
MANUAL_COURSE_BY_SLUG = {
    "anpa-anpa-0503": {
        "name": "Homorodul Nou (upper unnamed + Canalul Homorod, OSM)",
        "ways": [183051827, 76736507],   # upper stream; canal (Hrip→Ambud part)
        "canal_start_index": 76,          # index in way 76736507 == Hrip
        "bridge_note": "OSM gap Tătărești (23.000,47.694) → Hrip (22.998,47.722): straight bridge ~3.3 km; source stretch Solduba→Homorodu de Sus unmapped in extract",
    },
}


def build_manual_course(slug, ways_with_coords):
    """Concatenate way coords (given as [[(lon,lat),...], ...]) into one
    ordered LineString, bridging endpoint gaps with straight segments."""
    out = []
    for i, coords in enumerate(ways_with_coords):
        if not coords:
            continue
        if out and out[-1] != coords[0]:
            out.append(coords[0])  # bridge
        out.extend(coords)
    if not out:
        return None
    return {"type": "LineString", "coordinates": out}


_OSM_CACHE = {"nodes": {}, "ways": {}}


def load_way_coords(wid):
    """[(lon,lat), ...] for one way from the bulk extract (cached per run)."""
    if not _OSM_CACHE["ways"]:
        _d = json.loads((ROOT / "data" / "rivers_osm.geojson").read_text(encoding="utf-8"))
        _OSM_CACHE["nodes"] = {
            el["id"]: (el.get("lat"), el.get("lon"))
            for el in _d.get("elements", []) if el["type"] == "node" and "lat" in el
        }
        _OSM_CACHE["ways"] = {
            el["id"]: el for el in _d.get("elements", []) if el["type"] == "way"
        }
    el = _OSM_CACHE["ways"].get(wid)
    if not el:
        return []
    return [[_OSM_CACHE["nodes"][n][1], _OSM_CACHE["nodes"][n][0]]
            for n in el.get("nodes", []) if n in _OSM_CACHE["nodes"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only, no write")
    ap.add_argument("--json", type=str, help="write fix report JSON to this path")
    args = ap.parse_args()

    from validate_geometry_county import flag_waters

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    polygons = load_county_polygons()

    flagged_recs, _all = flag_waters(waters, polygons)
    flagged_slugs = {r["slug"] for r in flagged_recs}
    flagged = [w for w in waters if w["slug"] in flagged_slugs]
    print(f"[fix] flagged {len(flagged)} waters")

    with open(CLUSTER_PKL, "rb") as f:
        clusters, _cell = pickle.load(f)
    lakes = json.loads(LAKES_JSON.read_text(encoding="utf-8"))
    print(f"[fix] {len(clusters)} OSM clusters, {len(lakes)} lakes")

    by_norm = defaultdict(list)
    for cl in clusters:
        by_norm[cl["norm"]].append(cl)
    lakes_by_norm = defaultdict(list)
    for l in lakes:
        lakes_by_norm[l.get("norm") or ""].append(l)

    def collect(name):
        """[(kind, name, geom, bbox)] from river clusters + lakes + overrides."""
        variants = name_variants(name)
        wcore = core(name)
        cands = []
        seen = set()
        keys = set(variants)
        if wcore in NAME_OVERRIDES:
            keys.add(NAME_OVERRIDES[wcore])
        if w["slug"] in LAKE_NAME_BY_SLUG:
            keys.add(LAKE_NAME_BY_SLUG[w["slug"]])
        # rivers
        for k in keys:
            for cl in by_norm.get(k, []):
                if id(cl) not in seen:
                    seen.add(id(cl))
                    bb = cl.get("bbox")
                    cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"], list(bb) if bb else None))
        # loose core-equal for rivers (article variants)
        for nk, cls_ in by_norm.items():
            if nk in keys:
                continue
            if core(nk) == wcore and len(nk) >= 4:
                for cl in cls_:
                    if id(cl) not in seen:
                        seen.add(id(cl))
                        bb = cl.get("bbox")
                        cands.append(("river", cl.get("raw_name") or cl["name"], cl["geom"], list(bb) if bb else None))
        # lakes (norm key or core-equal)
        for k in keys:
            for l in lakes_by_norm.get(k, []):
                if id(l) not in seen:
                    seen.add(id(l))
                    cands.append(("lake", l.get("name") or "?", l["geom"], geom_bbox(l["geom"])))
        for nk, ls_ in lakes_by_norm.items():
            if nk in keys:
                continue
            if core(nk) == wcore and len(nk) >= 4:
                for l in ls_:
                    if id(l) not in seen:
                        seen.add(id(l))
                        cands.append(("lake", l.get("name") or "?", l["geom"], geom_bbox(l["geom"])))
        return cands

    fixed = []
    unresolved = []
    for w in flagged:
        declared = w.get("judet") or "?"
        name = w.get("name") or ""
        slug = w["slug"]

        if slug in KEEP_GEOMETRY:
            # border-attribution artifact: the attached course IS the correct
            # feature (Romsilva/areba manage it on the county line); keep it as-is
            # and do not flag it for a fix/drop cycle.
            print(f"  KEEP {declared:14} {name[:42]:44} (border-attribution artifact)")
            continue

        if slug in MANUAL_COURSE_BY_SLUG:
            spec = MANUAL_COURSE_BY_SLUG[slug]
            coords_list = []
            for i, wid in enumerate(spec["ways"]):
                c = load_way_coords(wid)
                if i == 0 and spec.get("canal_start_index") is not None and wid == spec["ways"][0]:
                    # for the canal way, start at the Hrip junction (index N)
                    pass
                if not c:
                    continue
                if spec.get("canal_start_index") is not None and i == len(spec["ways"]) - 1:
                    c = c[spec["canal_start_index"]:]
                coords_list.append(c)
            geom = build_manual_course(slug, coords_list)
            if geom:
                from validate_geometry_county import bbox_of_points
                pts = [p for p in geom["coordinates"] if len(p) >= 2]
                bb = bbox_of_points(pts)
                fixed.append({
                    "slug": slug, "name": name, "judet": declared,
                    "source": "manual", "osmc": spec["name"],
                    "in_county_pts": None, "majority": None,
                    "seat_d": seat_dist(declared, bb),
                    "old_bbox": w.get("bbox"),
                    "new_bbox": [round(v, 4) for v in bb],
                    "bridge_note": spec.get("bridge_note"),
                })
                print(f"  FIX  {declared:14} {name[:42]:44} <- [manual] {spec['name']}")
                if not args.dry_run:
                    w["geometry"] = geom
                    w["bbox"] = [round(v, 5) for v in bb]
                    w["source_detail"] = "geometry_sweep:manual_course"
                    w["geometryByCounty"] = {}
            else:
                unresolved.append({
                    "slug": slug, "name": name, "judet": declared,
                    "old_bbox": w.get("bbox"), "action": "manual-failed",
                })
                print(f"  DROP {declared:14} {name[:42]:44} (manual course build failed)")
                if not args.dry_run:
                    w["geometry"] = None
                    w["bbox"] = None
                    w["geometryByCounty"] = {}
                    w["source_detail"] = "geometry_sweep:dropped_no_county_course"
            continue

        if slug in FORCE_DROP:
            unresolved.append({
                "slug": slug, "name": name, "judet": declared,
                "old_bbox": w.get("bbox"), "action": "drop-geometry",
            })
            print(f"  DROP {declared:14} {name[:42]:44} (forced drop, no credible in-county course)")
            if not args.dry_run:
                w["geometry"] = None
                # keep the water's own geocoded bbox/coordinates as fallback
                # (they are the correct in-county position; only the attached
                # OSM course was from another county)
                if not w.get("bbox"):
                    w["bbox"] = None
                w["geometryByCounty"] = {}
                w["source_detail"] = "geometry_sweep:dropped_no_county_course"
            continue

        cands = collect(name)
        best = pick_best(cands, declared, polygons)
        if best:
            score, in_dec, majority, sd, src, cname, geom, bb = best
            if src == "river":
                out_geom = order_linestring(geom)
            else:
                out_geom = geom
            fixed.append({
                "slug": slug, "name": name, "judet": declared,
                "source": src, "osmc": cname, "in_county_pts": in_dec,
                "majority": majority, "seat_d": round(sd, 3) if sd else None,
                "old_bbox": w.get("bbox"),
                "new_bbox": [round(v, 4) for v in bb] if bb else None,
            })
            print(f"  FIX  {declared:14} {name[:42]:44} <- [{src}] {cname}"
                  f" (in={in_dec}pts maj={majority} seat_d={sd and round(sd,2)})")
            if not args.dry_run:
                w["geometry"] = out_geom
                w["bbox"] = [round(v, 5) for v in bb] if bb else None
                w["source_detail"] = "geometry_sweep:county_fix"
                # stale geometryByCounty from a previous (wrong-geometry) run
                # must not hide the corrected course under the county filter
                # (countyRenderGeometry returns null on a null clip entry)
                w["geometryByCounty"] = {}
        else:
            unresolved.append({
                "slug": slug, "name": name, "judet": declared,
                "old_bbox": w.get("bbox"), "action": "drop-geometry",
                "candidates": [{"kind": c[0], "name": c[1], "bb": c[3]}
                               for c in cands[:4]],
            })
            print(f"  DROP {declared:14} {name[:42]:44} (no candidate touching declared county)")
            if not args.dry_run:
                w["geometry"] = None
                if not w.get("bbox"):
                    w["bbox"] = None
                w["geometryByCounty"] = {}
                w["source_detail"] = "geometry_sweep:dropped_no_county_course"

    print(f"\n[fix] {len(fixed)} fixed, {len(unresolved)} unresolved")

    if not args.dry_run and (fixed or unresolved):
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[fix] wrote waters.json")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"fixed": fixed, "unresolved": unresolved}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"[fix] report -> {args.json}")


if __name__ == "__main__":
    main()
