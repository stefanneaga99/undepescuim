#!/usr/bin/env python3
"""Systematic per-area river audit (t_242be1eb).

Walks Romania in a ~0.5-deg grid. For every cell it lists every NAMED OSM
river crossing the cell and classifies it against the contracted sources:

    present      — already in public/data/waters.json (association shown)
    anpa-missing — in the ANPA contracted list but NOT in waters.json (FIXABLE)
    areba-missing- in the arebaltapeste list but NOT in waters.json (FIXABLE)
    romsilva     — in ANPA's Romsilva-administered list (report only,
                   RNP manages it, not an AJVPS/APS contract)
    uncontracted — not in any contract source (report only)

Unnamed OSM streams are skipped entirely (per plan step 4c).

Outputs:
  docs/audit_regions_report.md      — human-readable per-area report
  data/audit_regions.json           — structured per-cell data
  data/audit_regions_summary.json   — per-county/per-class counts

Usage:
  python3 scripts/audit_regions.py [--osm-index CACHE.pkl]
  python3 scripts/audit_regions.py --reload-osm
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_missing_rivers import (  # noqa: E402
    SECTOR_WORDS,
    norm,
    core,
    build_county_centroids,
    cluster_parts,
    load_osm_index,
    make_cluster_geoms,
)

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"
AREBALTAPESTE_SNAP = ROOT / "data" / "raw" / "arebaltapeste_probe" / "snapshot_waters.json"
ROMSILVA_FILE = ROOT / "data" / "raw" / "anpa_probe" / "Lista-habitate-Romsilva.txt"
OSM_INDEX_CACHE = ROOT / "data" / "cache" / "osm_river_clusters.pkl"

# Romania bounding box + grid
MIN_LAT, MAX_LAT = 43.4, 48.5
MIN_LON, MAX_LON = 20.0, 30.0
STEP = 0.5


# --------------------------------------------------------------------------
# Romsilva list parser (ANPA's Romsilva-administered mountain waters)
# --------------------------------------------------------------------------
ROMSILVA_DS_RE = re.compile(r"^\s*DIRECȚIA SILVICĂ\s+(.+?)\s*$", re.I)
ROMSILVA_SECTION_RE = re.compile(r"^\s*([IVX]+)\.\s*(RÂURI|LACURI)")
ROMSILVA_ROW_RE = re.compile(
    r"^\s*(?:\d+\s+)?(?P<name>[A-Za-z0-9ȘșȚțĂăÂâÎî\-–—'’. ]+?)\s+"
    r"(?P<km>\d+(?:[.,]\d+)?)\s+(?P<manager>[A-Za-z.\-–— ]+?)\s+rămâne",
    re.I,
)


def parse_romsilva(path: Path) -> list[dict]:
    """Load Romsilva-administered mountain waters.

    Prefers the cleanly-parsed processed JSONL (scripts/parse_anpa_romsilva.py,
    289 rows, water_name WITHOUT the limits text). Falls back to the raw txt
    regex only when the processed file is missing (kept for reference; the
    regex form wrongly captured the limits text into the name, which broke
    name-matching — e.g. 'Dofteana de la izvoare - la confl. cu raul Trotuș').
    """
    processed = ROOT / "data" / "processed" / "anpa_romsilva_waters.jsonl"
    if processed.exists():
        out = []
        for line in processed.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            out.append({
                "county": r.get("county", ""),
                "name": r.get("water_name", ""),
                "km": r.get("sector_km"),
                "manager": r.get("gestionar_ocol") or r.get("gestionar_ds") or "",
                "kind": "rau" if r.get("water_type") == "rau" else "lac",
            })
        return out

    rows = []
    county = None
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        dm = ROMSILVA_DS_RE.match(line)
        if dm:
            county = dm.group(1).strip()
            continue
        sm = ROMSILVA_SECTION_RE.match(line)
        if sm:
            section = sm.group(2).strip()
            continue
        if county is None:
            continue
        rm = ROMSILVA_ROW_RE.match(line)
        if rm:
            rows.append({
                "county": county,
                "name": rm.group("name").strip(),
                "km": float(rm.group("km").replace(",", ".")),
                "manager": rm.group("manager").strip(),
                "kind": "rau" if section == "RÂURI" else "lac",
            })
    return rows


# --------------------------------------------------------------------------
# OSM named-river clusters, each assigned to the grid cells it crosses
# --------------------------------------------------------------------------
def cell_key(lat: float, lon: float) -> tuple[int, int]:
    return (int((lat - MIN_LAT) // STEP), int((lon - MIN_LON) // STEP))


def build_clusters(reload: bool = False) -> tuple[list[dict], dict[tuple[int, int], list[int]]]:
    """Return (clusters, cell_index).

    cluster = {name, norm, geom, bbox, cells:[(ri,ci), ...]}
    cell_index[(ri,ci)] -> [cluster_idx, ...]
    """
    cache = OSM_INDEX_CACHE
    if not reload and cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)

    print("[osm] loading OSM index...", flush=True)
    name_index, geoms = load_osm_index()
    print(f"[osm] {len(name_index)} named waterways, {len(geoms)} geometries", flush=True)

    clusters: list[dict] = []
    cell_index: dict[tuple[int, int], list[int]] = defaultdict(list)

    for name, ids in sorted(name_index.items()):
        # raw (un-normalized) OSM name of the first geometry for this key —
        # needed by build_uncontracted_rivers.py for the FE card title.
        raw_name = ""
        for gid in ids:
            raw_name = (geoms.get(gid) or {}).get("name") or ""
            if raw_name:
                break
        for g in make_cluster_geoms(ids, geoms):
            coords = g["coordinates"] if g["type"] == "LineString" else [
                p for part in g["coordinates"] for p in part
            ]
            if not coords:
                continue
            lats = [p[1] for p in coords]
            lons = [p[0] for p in coords]
            bbox = (min(lons), min(lats), max(lons), max(lats))
            if bbox[1] > MAX_LAT or bbox[3] < MIN_LAT or bbox[0] > MAX_LON or bbox[2] < MIN_LON:
                continue
            cells: set[tuple[int, int]] = set()
            # sample every segment at ~0.05-deg steps to find crossed cells
            for i in range(1, len(coords)):
                x0, y0 = coords[i - 1]
                x1, y1 = coords[i]
                steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / 0.05))
                for s in range(steps + 1):
                    t = s / steps
                    lat = y0 + (y1 - y0) * t
                    lon = x0 + (x1 - x0) * t
                    if MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON:
                        cells.add(cell_key(lat, lon))
            if not cells:
                continue
            cidx = len(clusters)
            clusters.append({"name": name, "raw_name": raw_name, "norm": norm(name), "geom": g, "bbox": bbox,
                             "cells": sorted(cells)})
            for c in cells:
                cell_index[c].append(cidx)

    print(f"[osm] {len(clusters)} named river clusters", flush=True)
    with open(cache, "wb") as f:
        pickle.dump((clusters, dict(cell_index)), f)
    return clusters, cell_index


# --------------------------------------------------------------------------
# Source loaders
# --------------------------------------------------------------------------
def load_waters() -> list[dict]:
    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    return fe


def load_anpa() -> list[dict]:
    return [json.loads(l) for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_arebaltapeste() -> list[dict]:
    s = json.loads(AREBALTAPESTE_SNAP.read_text(encoding="utf-8"))
    return s if isinstance(s, list) else s.get("waters", [])


# --------------------------------------------------------------------------
# Matching: OSM cluster -> waters.json entry (name-based, county-aware)
# --------------------------------------------------------------------------
def token_core_match(a_core: str, b_core: str) -> bool:
    """True when two CORES name the same river, token-aware.

    'parau' must NOT match 'paraul lesuntu' (water-type word prefix); but
    'basca' matches 'basca mare' when the extra token is a sector word, and
    'raul turia' (core 'turia') matches a bare OSM 'turia' via equality.
    """
    ta = a_core.split()
    tb = b_core.split()
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    # token-prefix: the longer's extra tokens are all SECTOR_WORDS
    shorter, longer = (ta, tb) if len(ta) < len(tb) else (tb, ta)
    if shorter == longer[: len(shorter)]:
        extra = set(longer[len(shorter):])
        if extra and extra <= SECTOR_WORDS:
            return True
    # token overlap >= 0.6 with >= 2 shared tokens (or single exact token)
    shared = set(ta) & set(tb)
    ts = len(shared) / max(len(ta), len(tb))
    if len(shared) >= 2 and ts >= 0.6:
        return True
    if len(shared) == 1 and len(ta) == 1 and len(tb) == 1:
        return True
    return False


def match_waters(clusters, waters, county_centroids) -> dict[int, dict]:
    """cluster_idx -> best waters.json entry whose NAME matches the OSM name.

    Ladder: exact norm match; else best token-core match among waters whose
    judet centroid is near the cluster centroid (same-name rivers in
    different counties — Turia in Covasna vs Turia in Satu Mare — resolve to
    the closest county, so a far-away contract is never claimed).
    """
    by_core: dict[str, list[dict]] = defaultdict(list)
    for w in waters:
        by_core[core(w.get("name", ""))].append(w)

    matched: dict[int, dict] = {}
    for i, cl in enumerate(clusters):
        c = core(cl["name"])
        if not c:
            continue
        cpt = ((cl["bbox"][0] + cl["bbox"][2]) / 2, (cl["bbox"][1] + cl["bbox"][3]) / 2)

        def score(w: dict) -> tuple[float, float]:
            wc = core(w.get("name", ""))
            exact = 1.0 if wc == c else 0.0
            cc = county_centroids.get(w.get("judet") or "")
            d = 1e9
            if cc:
                d = ((cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2) ** 0.5
            return (exact, -d)

        best: dict | None = None
        best_score = (-1.0, 1e9)
        for key, ws in by_core.items():
            if not token_core_match(c, key):
                continue
            for w in ws:
                s = score(w)
                if s > best_score:
                    best_score, best = s, w
        if best is not None:
            matched[i] = best
    return matched


# --------------------------------------------------------------------------
# Audit
# --------------------------------------------------------------------------
def _county_dist(row_county: str, cluster: dict, county_centroids: dict) -> float:
    """Distance in degrees from cluster centroid to a county centroid (1e9 if unknown)."""
    # Sources spell counties 'BACĂU' / 'Bistrița - Năsăud' / 'Bistrița-Năsăud'
    # while waters.json uses title case 'Bacău' — match case-insensitively and
    # ignore separator differences so the county proximity bonus actually works.
    key = norm(row_county).replace(" - ", " ").replace("-", " ")
    cc = None
    for k, v in county_centroids.items():
        if norm(k).replace(" - ", " ").replace("-", " ") == key:
            cc = v
            break
    if not cc:
        return 1e9
    bbox = cluster["bbox"]
    cpt = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    return ((cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2) ** 0.5


LAKE_PREFIX_RE = re.compile(r"^(lac|lacul|acumulare|acumularea|balta|baltile|balti|baraj|iaz|heleșteu|heleseteu)", re.I)


def _is_lake_name(name: str) -> bool:
    return bool(LAKE_PREFIX_RE.match(norm(name)))


def _row_matches_cluster_type(row_name: str, cluster_name: str) -> bool:
    """Reject lake-name rows matching river clusters and vice versa.

    'Lacul Roșu' (lake row) must NOT match OSM cluster 'Valea Lacul Roșu'
    (a stream feeding the lake) — their cores coincide only because the
    stream is named after the lake. A lake row only matches when the OSM
    cluster is itself lake-named.
    """
    row_lake = _is_lake_name(row_name)
    cluster_lake = _is_lake_name(cluster_name)
    return row_lake == cluster_lake


def classify(cluster: dict, matched_water: dict | None, anpa_names: dict,
             areba_names: dict, romsilva_names: dict,
             county_centroids: dict, group_has_geom: set[str]) -> dict:
    """Return {class, association?, source?, detail, geometry}."""
    if matched_water is not None:
        assoc = (matched_water.get("asociatie") or {}).get("name", "")
        has_geom = bool(matched_water.get("geometry"))
        # group-rendered: another member of the same riverGroup draws the course
        if not has_geom and matched_water.get("riverGroup") in group_has_geom:
            has_geom = True
        if has_geom:
            return {"class": "present", "association": assoc,
                    "slug": matched_water.get("slug"),
                    "geometry": True,
                    "detail": matched_water.get("source_detail") or ""}
        # no real geometry: frontend falls back to a bbox rectangle when a
        # bbox exists; only waters with NO geometry AND NO bbox are invisible.
        vis = bool(matched_water.get("bbox"))
        cls = "present-bbox" if vis else "present-hidden"
        return {"class": cls, "association": assoc,
                "slug": matched_water.get("slug"),
                "geometry": False,
                "detail": matched_water.get("source_detail") or ""}

    n = cluster["norm"]
    c = core(cluster["name"])

    # ANPA: token-core match, prefer the row in the nearest county
    anpa_best = None
    anpa_dist = 1e9
    for key, rows in anpa_names.items():
        if not token_core_match(c, key):
            continue
        for row in rows:
            if not _row_matches_cluster_type(row.get("water_name", ""), cluster["name"]):
                continue
            d = _county_dist(row.get("county") or "", cluster, county_centroids)
            if d < anpa_dist:
                anpa_dist, anpa_best = d, row
    if anpa_best is not None:
        return {"class": "anpa-missing",
                "association": anpa_best.get("association", ""),
                "source": "anpa",
                "county": anpa_best.get("county", ""),
                "detail": anpa_best.get("water_name", ""),
                "geometry": False}

    # arebaltapeste: token-core match, nearest county
    areba_best = None
    areba_dist = 1e9
    for key, s in areba_names.items():
        if not token_core_match(c, key):
            continue
        if not _row_matches_cluster_type(s.get("name", ""), cluster["name"]):
            continue
        d = _county_dist(s.get("judet") or "", cluster, county_centroids)
        if d < areba_dist:
            areba_dist, areba_best = d, s
    if areba_best is not None:
        return {"class": "areba-missing",
                "association": (areba_best.get("asociatie") or {}).get("name", ""),
                "source": "arebaltapeste",
                "county": areba_best.get("judet", ""),
                "detail": areba_best.get("name", ""),
                "geometry": False}

    # Romsilva: token-core match, nearest county
    rs_best = None
    rs_dist = 1e9
    for key, r in romsilva_names.items():
        if not token_core_match(c, key):
            continue
        if not _row_matches_cluster_type(r.get("name", ""), cluster["name"]):
            continue
        d = _county_dist(r.get("county") or "", cluster, county_centroids)
        if d < rs_dist:
            rs_dist, rs_best = d, r
    if rs_best is not None:
        return {"class": "romsilva",
                "association": f"RNP Romsilva — {rs_best['county']}",
                "source": "romsilva",
                "county": rs_best.get("county", ""),
                "detail": rs_best.get("name", ""),
                "geometry": False}

    return {"class": "uncontracted", "association": "", "source": None, "detail": "",
            "geometry": False}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reload-osm", action="store_true", help="rebuild the OSM cluster cache")
    args = ap.parse_args()

    print("[1/5] building OSM river clusters (cached)...", flush=True)
    clusters, cell_index = build_clusters(reload=args.reload_osm)

    print("[2/5] loading waters.json + sources...", flush=True)
    waters = load_waters()
    anpa = load_anpa()
    areba = load_arebaltapeste()
    romsilva = parse_romsilva(ROMSILVA_FILE)
    print(f"      waters.json={len(waters)}  anpa={len(anpa)}  arebaltapeste={len(areba)}  romsilva={len(romsilva)}", flush=True)

    anpa_names: dict[str, list] = defaultdict(list)
    for w in anpa:
        anpa_names[norm(w["water_name"])].append(w)
    areba_names = {norm(s["name"]): s for s in areba}
    romsilva_names = {}
    for r in romsilva:
        romsilva_names.setdefault(norm(r["name"]), r)

    county_centroids = build_county_centroids(waters)

    print("[3/5] matching OSM clusters to waters.json...", flush=True)
    matched = match_waters(clusters, waters, county_centroids)
    print(f"      matched {len(matched)}/{len(clusters)} clusters", flush=True)

    print("[4/5] classifying per cell...", flush=True)
    cell_rows: dict[tuple[int, int], list[dict]] = {}
    class_counts: Counter = Counter()
    county_counts: Counter = Counter()
    class_by_county: dict[str, Counter] = defaultdict(Counter)

    # county for unmatched clusters: nearest county centroid (approx)
    def approx_county(cl):
        bbox = cl["bbox"]
        cpt = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        best, bd = None, 1e9
        for j, cc in county_centroids.items():
            d = ((cpt[0] - cc[0]) ** 2 + (cpt[1] - cc[1]) ** 2) ** 0.5
            if d < bd:
                bd, best = d, j
        return best or "?"

    # classify each DISTINCT cluster once; count distinct per county
    group_has_geom = {w["riverGroup"] for w in waters
                      if w.get("riverGroup") and w.get("geometry")}
    cluster_info: dict[int, dict] = {}
    for i, cl in enumerate(clusters):
        info = classify(cl, matched.get(i), anpa_names, areba_names, romsilva_names,
                         county_centroids, group_has_geom)
        cluster_info[i] = info
        cl_class = info["class"]
        class_counts[cl_class] += 1
        county = ""
        if matched.get(i):
            county = matched[i].get("judet") or ""
        else:
            county = info.get("county", "") or ""
        if not county:
            county = approx_county(cl)
        info["county"] = county
        county_counts[county] += 1
        class_by_county[county][cl_class] += 1

    # per-cell listing references the precomputed classification
    for (ri, ci), idxs in sorted(cell_index.items()):
        lat0 = MIN_LAT + ri * STEP
        lon0 = MIN_LON + ci * STEP
        rows = []
        seen_names: set[str] = set()
        for i in idxs:
            cl = clusters[i]
            if cl["name"] in seen_names:
                continue
            seen_names.add(cl["name"])
            info = cluster_info[i]
            rows.append({
                "river": cl["name"],
                "class": info["class"],
                "association": info.get("association", ""),
                "detail": info.get("detail", ""),
                "geometry": info.get("geometry", False),
                "slug": info.get("slug", ""),
                "county": info.get("county", ""),
                "bbox": cl["bbox"],
            })
        cell_rows[(ri, ci)] = rows

    print("[5/5] writing reports...", flush=True)
    # structured JSON
    cells_out = []
    for (ri, ci), rows in sorted(cell_rows.items()):
        cells_out.append({
            "cell": f"{MIN_LAT + ri * STEP:.1f}-{MIN_LAT + (ri + 1) * STEP:.1f}N, "
                    f"{MIN_LON + ci * STEP:.1f}-{MIN_LON + (ci + 1) * STEP:.1f}E",
            "ri": ri, "ci": ci,
            "rivers": rows,
        })
    summary = {
        "total_clusters": len(clusters),
        "class_counts": dict(class_counts),
        "county_counts": {k: v for k, v in sorted(county_counts.items())},
        "class_by_county": {k: dict(v) for k, v in sorted(class_by_county.items())},
    }
    (ROOT / "data" / "audit_regions.json").write_text(
        json.dumps({"cells": cells_out, "summary": summary}, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "data" / "audit_regions_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # human-readable markdown
    md = ["# Audit pe zone — râuri OSM vs. date contractate", ""]
    md.append(f"Total grupuri de râuri OSM cu nume: **{len(clusters)}**  ")
    md.append("Clasificare globală:")
    for cls, n in sorted(class_counts.items(), key=lambda x: -x[1]):
        md.append(f"- **{cls}**: {n}")
    md.append("")
    md.append("## Zona raportată: Covasna / Târgu Secuiesc (DN11, DN13E)")
    md.append("")
    md.append("Toate cele 16 ape contractate AJVPS COVASNA există în waters.json. După audit:")
    md.append("- **Pârâu Cașin, Ghelința, Pădureni, Vârghiș, Baraolt inferior** — erau `subtype=lac` și fără geometrie → invizibile; acum `rau` + curs OSM complet (fixate).")
    md.append("- **Râul Negru I / Râul Olt / Pârâu Buzăul Mijlociu** — nu au geometrie proprie, dar sunt grup-rendered: cursul e desenat de partenerul de grup (Râul Negru II / Râul Olt și afluenții / Râul Buzău) → click funcționează.")
    md.append("- **Pârâu Szaldoboș / Pârâu Șomko / Brațele secundare ale Râului Negru** — contractate dar fără curs OSM identificabil (pâraie mici / brațe secundare) → raportate doar, nu se inventează geometrie.")
    md.append("- Râurile vizibile fără card în zonă (Turia, Cernat, Estelnic etc.) sunt **necontractate** — nu apar în ANPA/arebaltapeste/Romsilva → corect să nu aibă card.")
    md.append("")
    md.append("## Pe județ")
    md.append("| Județ | total | prezent | anpa-missing | areba-missing | romsilva | uncontracted |")
    md.append("|---|---|---|---|---|---|---|")
    for j in sorted(class_by_county):
        c = class_by_county[j]
        md.append(f"| {j} | {sum(c.values())} | {c.get('present',0)} | {c.get('anpa-missing',0)} | "
                  f"{c.get('areba-missing',0)} | {c.get('romsilva',0)} | {c.get('uncontracted',0)} |")
    md.append("")
    md.append("## Pe celulă (0.5°×0.5°)")
    for cell in cells_out:
        rows = cell["rivers"]
        if not rows:
            continue
        md.append(f"\n### Celulă {cell['cell']}")
        md.append("| Râu | Clasă | Asociație | Detalii |")
        md.append("|---|---|---|---|")
        for r in rows:
            md.append(f"| {r['river']} | {r['class']} | {r['association']} | {r['detail']} |")
    md.append("")
    md.append("## Legenda claselor")
    md.append("- **present** — există în waters.json CU geometrie → click → card, curs desenat.")
    md.append("- **present-bbox** — există în waters.json, fără geometrie dar CU bbox → se afișează ca dreptunghi (aprox.), click → card.")
    md.append("- **present-hidden** — există în waters.json, fără geometrie ȘI fără bbox → INVIZIBIL pe hartă, deși e contractat → de reparat (bug de clasificare sau lipsă geometrie).")
    md.append("- **anpa-missing** — este în lista ANPA de contracte, dar LIPSEȘTE din waters.json → de adăugat (fixable).")
    md.append("- **areba-missing** — este în lista arebaltapeste.ro, dar LIPSEȘTE din waters.json → de adăugat (fixable).")
    md.append("- **romsilva** — administrat de RNP-Romsilva (listă ANPA separată); NU este contract AJVPS/APS → doar raportat.")
    md.append("- **uncontracted** — nu apare în nicio sursă contractată → doar raportat, NU se inventează contract.")
    out_md = ROOT / "docs" / "audit_regions_report.md"
    out_md.parent.mkdir(exist_ok=True)
    out_md.write_text("\n".join(md), encoding="utf-8")

    print("\n=== SUMMARY ===")
    for cls, n in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls:15s} {n}")
    print(f"\nReport: {out_md}")
    print(f"JSON:   {ROOT / 'data' / 'audit_regions.json'}")


if __name__ == "__main__":
    main()
