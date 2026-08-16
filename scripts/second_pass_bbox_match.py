#!/usr/bin/env python3
"""SECOND-PASS MATCH for bbox-only waters (t_cdb614de).

Goal: retry the 96 bbox-only waters with a HARDER matcher than
sweep_remaining_geometry.py's conservative ladder, and document the rest.

INVESTIGATION FINDINGS (2026-08-16):
- The user's named examples (Râul Potop Dâmbovița, Râul Bahna Botoșani,
  Râul Jilț Gorj, Râul Holod Bihor) are REAL rivers (Wikipedia/e-calauza
  confirm: Holod mouth 22.0300/46.7708 == contract bbox; Jilț Raci-Turceni;
  Potop = Potopu-Cobia->Sabar system; Bahna Botoșani Dersca-Lunca) but OSM
  has NO way named Potop/Potopu/Jilț/Holod anywhere in Romania (verified
  live Overpass kumi.systems + the 258MB local dump). The matcher did NOT
  miss them — the names do not exist in OSM. They are genuine OSM data gaps,
  so they keep the point fallback (documented per-water).
- A strict fuzzy scan (diacritic fold â/î->a/i, genitive/article stems,
  bbox-overlap + county guard) over the 96 found ONLY 2 REAL matches:
  * romsilva-alba-viltori-fenes  <- OSM 'Vâltori' (64/64 Alba pts, bbox
    [23.21,46.11,23.22,46.17] == the contract bbox around Zlatna/Feneș)
  * anpa-anpa-0008 Mihoești      <- lake 'Lacul de acumulare Mihoești'
    (75/75 Alba pts, Polygon, Câmpeni area) — subtype lac, exact name.
  Everything else auto-matched by token/edit-distance was a FALSE POSITIVE
  (tributaries/dead-branches matched to their receiving main courses:
  Botiza->Iza, Ruoaia Lăpuș->Lăpuș, Brațul Închis Jijia->Jijia, Brațele
  secundare Negru->Negru, Șomko->Jombor) — pitfall #3/#66 class. NO generic
  auto-attach: only verified manual matches are applied.

Usage:
  python3 scripts/second_pass_bbox_match.py             # dry run
  python3 scripts/second_pass_bbox_match.py --write     # apply
  python3 scripts/second_pass_bbox_match.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
CLUSTER_PKL = ROOT / "data" / "cache" / "osm_river_clusters.pkl"
LAKES_JSON = ROOT / "data" / "processed" / "overpass_named_lakes.json"
LAKES2_JSON = ROOT / "data" / "processed" / "overpass_named_lakes2.json"
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


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


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


def geom_bbox(g: dict):
    pts = cluster_points(g)
    if not pts:
        return None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


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
            from shapely.geometry import shape
            geom = shape(g)
        except Exception:
            continue
        polys.append((name, prep(geom), geom.bounds))
    return polys


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


def order_linestring(geom):
    from _mapping_common import order_course_linestring
    return order_course_linestring(geom)


# --- verified manual matches (researched, county-guarded at apply time) -----
# slug -> dict(kind='river'|'lake', key=<cluster norm or lake name>, note=...)
MANUAL_MATCH = {
    "romsilva-alba-viltori-fenes": {
        "kind": "river", "key": "valtori",
        "note": "Râul Vîltori - Feneș (Zlatna) == OSM 'Vâltori' course 64/64 Alba (â/î spelling variant)",
    },
    "anpa-anpa-0008": {
        "kind": "lake", "key": "Lacul de acumulare Mihoești",
        "note": "Mihoești (lac, Câmpeni, Alba) == OSM reservoir polygon 'Lacul de acumulare Mihoești' 75/75 Alba",
    },
}

# slug -> (kind, note) — REAL river but OSM genuinely lacks the name/way;
# keep the bbox fallback rendered as a POINT (documented, not a matcher miss).
MANUAL_UNMATCHABLE = {
    "ebhj5eyj": ("osm-no-name", "Râul Potop Dâmbovița (45km, Ludești): real river (Potopu->Cobia->Sabar system) but OSM has NO way named Potop/Potopu/Cobia in the contract bbox — verified live Overpass + dump"),
    "g39ohi12": ("osm-no-name", "Râul Jilț Gorj (Raci-Turceni conf. Jiu): real river (Wikipedia) — OSM has no 'Jilț' way anywhere in the RO dump"),
    "0dsbiw28": ("osm-no-name", "Râul Holod Bihor (Copăceni-conf. Crișul Negru): real river (Wikipedia, mouth 22.0300/46.7708 == contract bbox) — OSM has no 'Holod' way (verified live Overpass + dump)"),
    "pgabr5sd": ("osm-no-name", "Râul Bahna Botoșani (Dersca-Lunca): only OSM 'Râul Bahna' is in Mehedinți (22.5E, wrong county); the Botoșani contract has no OSM way in its bbox"),
    "anpa-anpa-0393": ("tributary-deadbranch", "Brațul Închis(mort) al râului Jijia: a dead branch of the Jijia — attaching the main Jijia course would be wrong (pitfall #66); point at the braț"),
    "anpa-anpa-0252": ("tributary-branches", "Brațele secundare ale Râului Negru: secondary branches, not the main Negru course — attaching Râul Negru would be wrong"),
    "romsilva-maramures-botiza": ("tributary", "Râul Botiza is a TRIBUTARY of the Iza — the auto-matcher's Iza hit is the RECEIVING river (pitfall #3); no Botiza course in OSM"),
    "anpa-anpa-0416": ("tributary", "Râul Ruoaia Lăpuș: Ruoaia is a tributary — the Lăpuș hit is the RECEIVING river (pitfall #3); no Ruoaia course in OSM"),
    "anpa-anpa-0254": ("name-variant-unverified", "Pârâu Șomko vs OSM 'Pârâul Jombor': edit-distance 3 on short names is NOT a verified same-river match (Hungarian names, different streams)"),
    "anpa-anpa-0134": ("river-no-course", "Râul Colibița superioară: no named OSM river course; only the Colibița lake polygon + dam exist (KEEP_BBOX_PART2 t_68dabead)"),
    "anpa-anpa-0135": ("river-no-course", "Râul Colibița inferioară: no named OSM river course; only the Colibița lake polygon + dam exist (KEEP_BBOX_PART2 t_68dabead)"),
    "romsilva-alba-fenesasa": ("river-no-course", "Râul Fenesasa (25km, Feneș-Zlatna): OSM has only tiny Călineasa/Lunca streams + unnamed fragments at Feneș; no 25km named course (KEEP_BBOX_PART2 t_68dabead)"),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", type=str)
    args = ap.parse_args()

    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    polygons = load_county_polygons()
    with open(CLUSTER_PKL, "rb") as f:
        clusters, _cell = pickle.load(f)
    lakes = []
    for p in (LAKES_JSON, LAKES2_JSON):
        lakes += json.loads(p.read_text(encoding="utf-8"))
    print(f"[pass2] {len(waters)} waters, {len(clusters)} clusters, {len(lakes)} lakes")

    by_norm = defaultdict(list)
    for cl in clusters:
        by_norm[cl["norm"]].append(cl)
    lakes_by_name = defaultdict(list)
    for l in lakes:
        lakes_by_name[(l.get("name") or "").strip().lower()].append(l)

    bbox_only = [w for w in waters if w.get("bbox") and not w.get("geometry")]
    print(f"[pass2] target: {len(bbox_only)} bbox-only waters")

    report = {"matched": [], "unmatchable": [], "keep_point": []}
    changed = []

    def attach(w, out_geom, src, cname, in_dec, majority):
        w["geometry"] = out_geom
        bb = geom_bbox(out_geom)
        w["bbox"] = [round(v, 5) for v in bb] if bb else None
        w["source_detail"] = "second_pass:" + src
        w["geometryByCounty"] = {}
        w.pop("hidden", None)
        changed.append(w)
        return {"slug": w["slug"], "name": w["name"], "judet": w["judet"], "source": src,
                "osmc": cname, "in_county_pts": in_dec, "majority": majority}

    def document(w, kind, note):
        sd = w.get("source_detail") or ""
        w["bbox_render"] = "point"
        w["source_detail"] = sd + " | second_pass:" + kind
        report[kind].append({"slug": w["slug"], "name": w["name"], "judet": w["judet"], "note": note})
        changed.append(w)

    for w in sorted(bbox_only, key=lambda x: (x["judet"], x["name"])):
        slug = w["slug"]
        declared = w["judet"]
        name = w["name"]

        if slug in MANUAL_MATCH:
            spec = MANUAL_MATCH[slug]
            cand = None
            if spec["kind"] == "river":
                cand = by_norm.get(spec["key"], [None])[0]
                cname = (cand or {}).get("raw_name") or (cand or {}).get("name") or spec["key"]
            else:
                ls = lakes_by_name.get(spec["key"].lower(), [])
                cand = ls[0] if ls else None
                cname = spec["key"]
            if not cand:
                print(f"  !! {slug}: MANUAL_MATCH '{spec['key']}' not found")
                continue
            g = cand["geom"]
            pts = cluster_points(g)
            in_dec, majority, total = county_hits(pts, polygons, declared)
            if in_dec == 0:
                print(f"  !! {slug}: manual candidate '{cname}' has 0 in-county pts — skipping")
                report["keep_point"].append({"slug": slug, "name": name, "judet": declared,
                                             "note": f"manual candidate failed county guard ({spec['note']})"})
                continue
            out_geom = g if spec["kind"] == "lake" else order_linestring(g)
            entry = attach(w, out_geom, "manual-" + spec["kind"], cname, in_dec, majority)
            entry["note"] = spec["note"]
            report["matched"].append(entry)
            print(f"  FIX {declared:16s} {name[:44]:44s} <- [manual-{spec['kind']}] {cname} (in={in_dec})")
            continue

        if slug in MANUAL_UNMATCHABLE:
            reason, note = MANUAL_UNMATCHABLE[slug]
            document(w, "unmatchable", note)
            print(f"  KEEP {declared:16s} {name[:44]:44s} (documented unmatchable: {reason})")
            continue

        # Everything else: no verified candidate -> point fallback + document.
        document(w, "keep_point", "no verified OSM candidate after 2nd-pass investigation; bbox renders as point")
        print(f"  KEEP {declared:16s} {name[:44]:44s} (point)")

    n_match = len(report["matched"])
    n_unm = len(report["unmatchable"])
    n_keep = len(report["keep_point"])
    print(f"\n[pass2] matched: {n_match}, documented-unmatchable: {n_unm}, keep-point: {n_keep}")

    if args.write and changed:
        WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        with_bbox = sum(1 for x in waters if x.get("bbox"))
        neither = sum(1 for x in waters if not x.get("geometry") and not x.get("bbox"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} geom, {with_bbox} bbox, {neither} neither")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[report] -> {args.json}")


if __name__ == "__main__":
    main()
