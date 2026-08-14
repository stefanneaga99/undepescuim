#!/usr/bin/env python3
"""GEOMETRY FINAL fixes (t_1b7c95a7 run 2) — apply the 4 user decisions:

1. romsilva-bihor-dragan: flip subtype lac -> rau (keep 24-part course geometry).
2. 9 double-draw groups -> ONE geometry owner per group (Siret/Buzău pattern);
   the other members become geometry-less sector members (geometry:null,
   bbox:null + sectorStart/sectorEnd) so the FE base layer draws the course
   once while contractAtFraction/coverage slicing still resolve per contract.
3. Someșul Cald duplicate contracts: remove m19ue32m/nwa37i1j (areba-probe
   duplicates) — keep official romsilva-cluj-1/2 (source anpa_romsilva).
4. Botoșani 13 unmatchables: keep bbox fallback (no change, documented).

Owner-course strategy per group:
  - N-S rivers (argesel, prahova, targului, teleajen): order_course_linestring
    (dedupes identical-endpoint parts, keeps the FULL course, orients
    higher-lat-first — correct for south-flowing Romanian rivers).
  - E-W rivers (budacul, crisul-negru, valea-robesti): endpoint-connectivity
    chaining (chain_tolerant / chain_all_clusters) + explicit source anchor
    (higher-lon end) via orient_course.
  - somesu-rece: source at LOWER lat (flows north into lacul Gilău) — chain
    then orient by min-lat end.
Every owner course is verified (bbox + max jump) before sectors are computed.

Writes public/data/waters.json (indent=1, ensure_ascii=False, no trailing
newline) + data/processed/merge_fixes_report.json.
Run: python3 scripts/merge_fixes_final.py
"""
import json
import math
import pickle
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from geometry_batch4_attach import chain_tolerant, chain_all_clusters, orient_course  # noqa: E402
from sweep_multiway_rivers import chain_parts, flatten, geom_parts  # noqa: E402
from _mapping_common import order_course_linestring  # noqa: E402

WATERS = ROOT / "public" / "data" / "waters.json"
CLUSTERS = ROOT / "data" / "cache" / "osm_river_clusters.pkl"
REPORT = ROOT / "data" / "processed" / "merge_fixes_report.json"

# ---------------- helpers ----------------
def haversine_m(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    dlat = la2 - la1
    dlon = lo2 - lo1
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


def frac_of_point(coords, pt):
    if not coords:
        return None
    best_i, best_d = 0, 1e18
    for i, c in enumerate(coords):
        d = (c[0] - pt[0]) ** 2 + (c[1] - pt[1]) ** 2
        if d < best_d:
            best_i, best_d = i, d
    cum = [0.0]
    for i in range(len(coords) - 1):
        cum.append(cum[-1] + haversine_m(coords[i], coords[i + 1]))
    total = cum[-1]
    if total <= 0:
        return None
    i = best_i
    if i >= len(coords) - 1:
        return 1.0
    d0 = haversine_m(coords[i], pt)
    seg = haversine_m(coords[i], coords[i + 1])
    f = (cum[i] + min(seg, d0)) / total
    return max(0.0, min(1.0, f))


def geocode(query):
    url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
           + urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "undepescuim-merge-fixes"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            hits = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"    !! geocode {query!r} failed: {e}")
        return None
    if not hits:
        print(f"    !! geocode {query!r}: no result")
        return None
    return (float(hits[0]["lon"]), float(hits[0]["lat"]))


def load_clusters():
    with open(CLUSTERS, "rb") as f:
        obj = pickle.load(f)
    return obj[0] if isinstance(obj, tuple) else obj


def to_linestring(coords):
    return {"type": "LineString", "coordinates": coords}


def geom_bbox(g):
    coords = []
    def walk(x):
        t = x["type"]
        if t == "LineString":
            coords.extend(x["coordinates"])
        elif t == "MultiLineString":
            for p in x["coordinates"]:
                coords.extend(p)
        elif t == "Polygon":
            for r in x["coordinates"]:
                coords.extend(r)
        elif t == "MultiPolygon":
            for poly in x["coordinates"]:
                for r in poly:
                    coords.extend(r)
    walk(g)
    if not coords:
        return None
    return [min(c[0] for c in coords), min(c[1] for c in coords),
            max(c[0] for c in coords), max(c[1] for c in coords)]


def max_jump_km(coords):
    m = 0.0
    for i in range(len(coords) - 1):
        m = max(m, haversine_m(coords[i], coords[i + 1]) / 1000.0)
    return m


# ---------------- load ----------------
waters = json.loads(WATERS.read_text(encoding="utf-8"))
clusters = load_clusters()
by_slug = {w["slug"]: w for w in waters}

report = {"changes": [], "sectors": {}, "counts": {}, "owner_courses": {}}

def touch(w, note):
    w["geometryByCounty"] = {}
    report["changes"].append({"slug": w["slug"], "name": w["name"], "note": note})


def build_ns_course(geom, slug):
    """order_course_linestring: N-S rivers (full course kept, higher-lat first)."""
    out = order_course_linestring(geom)
    coords = out["coordinates"]
    report["owner_courses"][slug] = {
        "builder": "order_course_linestring",
        "pts": len(coords),
        "bbox": geom_bbox(out),
        "max_jump_km": round(max_jump_km(coords), 3),
        "first": coords[0], "last": coords[-1],
    }
    return coords


def build_ew_course(geom, slug, source_side="max_lon"):
    """Endpoint-connectivity chaining for E-W rivers + explicit source anchor."""
    parts = geom_parts(geom)
    chain = chain_parts(parts)
    if chain is None:
        chain = chain_tolerant(parts)
    if chain is None:
        chain = [max(parts, key=len)]
    out = flatten(chain)
    coords = out["coordinates"]
    if source_side == "max_lon":
        anchor = max(coords, key=lambda c: c[0])
    elif source_side == "min_lon":
        anchor = min(coords, key=lambda c: c[0])
    elif source_side == "min_lat":
        anchor = min(coords, key=lambda c: c[1])
    elif source_side == "max_lat":
        anchor = max(coords, key=lambda c: c[1])
    else:
        anchor = source_side
    out = orient_course(out, anchor)
    coords = out["coordinates"]
    report["owner_courses"][slug] = {
        "builder": "connectivity+" + source_side,
        "pts": len(coords),
        "bbox": geom_bbox(out),
        "max_jump_km": round(max_jump_km(coords), 3),
        "first": coords[0], "last": coords[-1],
    }
    return coords


def build_multi_course(geoms, slug, source_side="max_lon"):
    """Chain multiple geometry dicts (clusters / superior+inferior)."""
    parts = []
    for g in geoms:
        parts.extend(geom_parts(g))
    seen = set()
    uniq = []
    for p in parts:
        key = (tuple(p[0]), tuple(p[-1]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(list(p))
    chain = chain_parts(uniq)
    if chain is None:
        chain = chain_tolerant(uniq)
    if chain is None:
        chain = [max(uniq, key=len)]
    out = flatten(chain)
    coords = out["coordinates"]
    if source_side == "max_lon":
        anchor = max(coords, key=lambda c: c[0])
    elif source_side == "min_lat":
        anchor = min(coords, key=lambda c: c[1])
    elif source_side == "max_lat":
        anchor = max(coords, key=lambda c: c[1])
    else:
        anchor = source_side
    out = orient_course(out, anchor)
    coords = out["coordinates"]
    report["owner_courses"][slug] = {
        "builder": "multi_connectivity+" + source_side,
        "pts": len(coords),
        "bbox": geom_bbox(out),
        "max_jump_km": round(max_jump_km(coords), 3),
        "first": coords[0], "last": coords[-1],
    }
    return coords


# ============================================================
# FIX 1: dragan subtype flip
# ============================================================
d = by_slug["romsilva-bihor-dragan"]
old_sub = d.get("subtype")
d["subtype"] = "rau"
touch(d, f"subtype {old_sub}->rau (user decision #1, keep 24-part course geometry)")

# ============================================================
# FIX 3: Someșul Cald dedup — remove probe duplicates
# ============================================================
for dup in ["m19ue32m", "nwa37i1j"]:
    w = by_slug.get(dup)
    if w:
        waters.remove(w)
        report["changes"].append({"slug": dup, "name": w["name"], "note": "REMOVED (probe duplicate of official romsilva-cluj-*; user decision #3)"})
        del by_slug[dup]

# ============================================================
# FIX 2: 9 double-draw groups -> one owner per group
# ============================================================
GEO_CACHE = {}

def f_on(coords, query):
    if query not in GEO_CACHE:
        GEO_CACHE[query] = geocode(query)
    pt = GEO_CACHE[query]
    if pt is None:
        return None
    return frac_of_point(coords, pt)


def set_sector(w, s):
    w["sectorStart"], w["sectorEnd"] = s


# ---- argesel (N-S) ----
g = "argesel"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["0hxo4zi3"]
coords = build_ns_course(owner["geometry"], owner["slug"])
owner["geometry"] = to_linestring(coords)
f_pravat = f_on(coords, "Valea Mare Pravăț, Argeș")
report["sectors"][g] = {"f_valea_mare_pravat": f_pravat}
touch(owner, f"group {g}: geometry owner (full course {len(coords)} pts)")
set_sector(owner, (f_pravat, 1.0) if f_pravat is not None else (None, None))
for w in members:
    if w["slug"] == owner["slug"]:
        continue
    w["geometry"] = None
    w["bbox"] = None
    set_sector(w, (0.0, f_pravat) if f_pravat is not None else (None, None))
    touch(w, f"group {g}: geometry-less sector member (superior [0,{f_pravat}])")

# ---- budacul (E-W, source at max lon) ----
g = "budacul"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["u1frrl08"]
coords = build_ew_course(owner["geometry"], owner["slug"], source_side="max_lon")
owner["geometry"] = to_linestring(coords)
f_budacu = f_on(coords, "Budacu de Sus, Bistrița-Năsăud")
report["sectors"][g] = {"f_budacu_de_sus": f_budacu}
touch(owner, f"group {g}: geometry owner (full course {len(coords)} pts)")
set_sector(owner, (f_budacu, 1.0) if f_budacu is not None else (None, None))
for w in members:
    if w["slug"] == owner["slug"]:
        continue
    w["geometry"] = None
    w["bbox"] = None
    set_sector(w, (0.0, f_budacu) if f_budacu is not None else (None, None))
    touch(w, f"group {g}: geometry-less sector member (superior [0,{f_budacu}])")

# ---- crisul-negru (rebuild FULL course from the two OSM clusters; E-W, source max lon) ----
g = "crisul-negru"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["9mfds2yv"]
cls_list = [c for c in clusters if str(c.get("name") or "").lower() == "crisul negru"]
geoms = [c["geom"] for c in cls_list]
coords = build_multi_course(geoms, owner["slug"], source_side="max_lon")
owner["geometry"] = to_linestring(coords)
print(f"  crisul-negru full course: {len(coords)} pts, bbox {geom_bbox(owner['geometry'])}, max_jump {max_jump_km(coords):.2f} km")
touch(owner, f"group {g}: geometry owner (FULL chained course {len(coords)} pts, was 435-pt fragment)")
anchors = {
    "mijlociu_start": f_on(coords, "Valea Băița, Bihor") or f_on(coords, "Ștei, Bihor"),
    "crisul_pietros": f_on(coords, "Crișul Pietros"),
    "finis": f_on(coords, "Finiș, Bihor"),
    "beius": f_on(coords, "Beiuș, Bihor"),
    "vanatori": f_on(coords, "Vânători, Arad"),
}
report["sectors"][g] = anchors
print(f"  crisul-negru anchors: {anchors}")
sector_map = {
    "7ull4jnk": (anchors["mijlociu_start"], anchors["crisul_pietros"]),
    "jw9il5yo": (anchors["crisul_pietros"], anchors["finis"]),
    "w69nse7i": (anchors["beius"], 1.0),
}
for w in members:
    if w["slug"] == owner["slug"]:
        set_sector(owner, (anchors["vanatori"], 1.0) if anchors["vanatori"] is not None else (None, None))
        continue
    s = sector_map.get(w["slug"])
    if s and s[0] is not None and s[1] is not None:
        w["geometry"] = None
        w["bbox"] = None
        set_sector(w, s)
        touch(w, f"group {g}: geometry-less sector member [{s[0]:.4f},{s[1]:.4f}]")
    else:
        print(f"  !! {g} {w['slug']} missing sector anchors — geometry null fallback")
        w["geometry"] = None
        w["bbox"] = None
        touch(w, f"group {g}: geometry-less (anchors unavailable)")

# ---- malaia (lake polygon owner + river line owner; aty62qwm loses the duplicated river line) ----
g = "malaia"
members = [w for w in waters if w.get("riverGroup") == g]
for w in members:
    if w["slug"] == "aty62qwm":
        w["geometry"] = None
        w["bbox"] = None
        touch(w, f"group {g}: duplicate of Râul Malaia line removed (uncontracted ANPA lake)")
    elif w["slug"] == "0d29kh5i":
        set_sector(w, (0.0, 1.0))
        touch(w, f"group {g}: river line owner, sector [0,1]")
    else:
        touch(w, f"group {g}: lake polygon owner kept")

# ---- prahova (N-S, full course kept) ----
g = "prahova"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["53mzatrd"]
parts = geom_parts(owner["geometry"])
coords = build_ns_course(owner["geometry"], owner["slug"])
owner["geometry"] = to_linestring(coords)
print(f"  prahova: {sum(len(p) for p in parts)} pts -> full course {len(coords)} pts, bbox {geom_bbox(owner['geometry'])}")
f_vf = f_on(coords, "Valea Fetei, Bușteni")
f_nedelea = f_on(coords, "Nedelea, Prahova")
report["sectors"][g] = {"f_valea_fetii": f_vf, "f_nedelea": f_nedelea}
touch(owner, f"group {g}: geometry owner (full course {len(coords)} pts)")
set_sector(owner, (f_nedelea, 1.0) if f_nedelea is not None else (None, None))
sector_map = {
    "0a4d89le": (f_vf, f_nedelea),
    "2g9hg98a": (0.0, f_vf),
}
for w in members:
    if w["slug"] == owner["slug"]:
        continue
    s = sector_map.get(w["slug"])
    w["geometry"] = None
    w["bbox"] = None
    if s and s[0] is not None and s[1] is not None:
        set_sector(w, s)
        touch(w, f"group {g}: geometry-less sector member [{s[0]:.4f},{s[1]:.4f}]")
    else:
        set_sector(w, (None, None))
        touch(w, f"group {g}: geometry-less (boundary geocode unavailable)")

# ---- somesu-rece (source at LOWER lat — flows north into Gilău; owner 89j19sek) ----
g = "somesu-rece"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["89j19sek"]
coords = build_ew_course(owner["geometry"], owner["slug"], source_side="min_lat")
owner["geometry"] = to_linestring(coords)
touch(owner, f"group {g}: geometry owner (full course {len(coords)} pts, source at lower lat)")
F_SUP_END = 64.0 / 103.0
F_MIJ_END = 85.0 / 103.0
report["sectors"][g] = {"official_km_ratio_superior_end": F_SUP_END,
                        "official_km_ratio_mijlociu_end": F_MIJ_END,
                        "geocoded_valea_baii_UNRELIABLE": f_on(coords, "Valea Băii, Cluj"),
                        "geocoded_racatau_UNRELIABLE": f_on(coords, "Răcătău, Cluj")}
sector_map = {
    "9y116j3m": (F_SUP_END, F_MIJ_END),
    "i9uffwbx": (0.0, F_SUP_END),
}
for w in members:
    if w["slug"] == owner["slug"]:
        set_sector(owner, (F_MIJ_END, 1.0))
        continue
    if w["slug"] in sector_map:
        s = sector_map[w["slug"]]
        w["geometry"] = None
        w["bbox"] = None
        set_sector(w, s)
        touch(w, f"group {g}: geometry-less probe sector member [{s[0]:.4f},{s[1]:.4f}]")
    else:
        touch(w, f"group {g}: official Romsilva member kept (course_frac {w.get('course_frac')})")

# ---- targului (N-S) ----
g = "targului"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["rv08w2ty"]
coords = build_ns_course(owner["geometry"], owner["slug"])
owner["geometry"] = to_linestring(coords)
f_rausor = f_on(coords, "Baraj Râușor, Argeș")
f_campulung = f_on(coords, "Câmpulung, Argeș")
report["sectors"][g] = {"f_rausor": f_rausor, "f_campulung": f_campulung}
touch(owner, f"group {g}: geometry owner (full course {len(coords)} pts)")
set_sector(owner, (f_campulung, 1.0) if f_campulung is not None else (None, None))
sector_map = {
    "2dxykcpr": (f_rausor, f_campulung),
    "k44320iw": (0.0, f_rausor),
}
for w in members:
    if w["slug"] == owner["slug"]:
        continue
    s = sector_map.get(w["slug"])
    w["geometry"] = None
    w["bbox"] = None
    if s and s[0] is not None and s[1] is not None:
        set_sector(w, s)
        touch(w, f"group {g}: geometry-less sector member [{s[0]:.4f},{s[1]:.4f}]")
    else:
        set_sector(w, (None, None))
        touch(w, f"group {g}: geometry-less (boundary geocode unavailable)")

# ---- teleajen (owner gets the FULL chained course: superior 1202 + inferior 884; N-S) ----
g = "teleajen"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["0wn4yfsa"]
upper = geom_parts(by_slug["0wn4yfsa"]["geometry"])
lower = geom_parts(by_slug["c1gifahb"]["geometry"])
all_geoms = [{"type": "MultiLineString", "coordinates": upper + lower}]
coords = build_multi_course(all_geoms, owner["slug"], source_side="max_lat")
owner["geometry"] = to_linestring(coords)
print(f"  teleajen: full course {len(coords)} pts (upper {sum(len(p) for p in upper)} + lower {sum(len(p) for p in lower)})")
f_maneciu = f_on(coords, "Barajul Măneciu")
f_zamfira = f_on(coords, "Zamfira, Prahova")
f_bucov = f_on(coords, "Bucov, Prahova")
report["sectors"][g] = {"f_maneciu": f_maneciu, "f_zamfira": f_zamfira, "f_bucov": f_bucov}
touch(owner, f"group {g}: geometry owner (FULL chained course {len(coords)} pts)")
set_sector(owner, (0.0, f_zamfira) if f_zamfira is not None else (None, None))
sector_map = {
    "44plkztf": (f_maneciu, f_zamfira),
    "yfzdgchv": (f_zamfira, f_bucov),
    "c1gifahb": (f_bucov, 1.0),
}
for w in members:
    if w["slug"] == owner["slug"]:
        continue
    s = sector_map.get(w["slug"])
    w["geometry"] = None
    w["bbox"] = None
    if s and s[0] is not None and s[1] is not None:
        set_sector(w, s)
        touch(w, f"group {g}: geometry-less sector member [{s[0]:.4f},{s[1]:.4f}]")
    else:
        set_sector(w, (None, None))
        touch(w, f"group {g}: geometry-less (boundary geocode unavailable)")

# ---- valea-robesti (E-W? actually tiny stream: keep as-is; one owner) ----
g = "valea-robesti"
members = [w for w in waters if w.get("riverGroup") == g]
owner = by_slug["zryn07zh"]
for w in members:
    if w["slug"] == owner["slug"]:
        touch(w, f"group {g}: geometry owner kept")
        continue
    w["geometry"] = None
    w["bbox"] = None
    touch(w, f"group {g}: geometry-less duplicate removed (same contract)")

# ============================================================
# counts + write
# ============================================================
report["counts"]["total"] = len(waters)
report["counts"]["with_geometry"] = sum(1 for w in waters if w.get("geometry"))
report["counts"]["with_bbox"] = sum(1 for w in waters if w.get("bbox"))
report["counts"]["no_geometry_no_bbox"] = sum(1 for w in waters if not w.get("geometry") and not w.get("bbox"))

WATERS.write_text(json.dumps(waters, indent=1, ensure_ascii=False), encoding="utf-8")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n=== SUMMARY ===")
print(f"total waters: {report['counts']['total']} (was 1015; -2 removed by somesul-cald dedup)")
print(f"with geometry: {report['counts']['with_geometry']}")
print(f"with bbox: {report['counts']['with_bbox']}")
print(f"no geometry+no bbox (hidden sector members): {report['counts']['no_geometry_no_bbox']}")
print(f"changes: {len(report['changes'])}")
print(f"owner courses: {json.dumps(report['owner_courses'], ensure_ascii=False, indent=1)}")
print(f"sectors: {json.dumps(report['sectors'], ensure_ascii=False)}")
print(f"report: {REPORT}")
