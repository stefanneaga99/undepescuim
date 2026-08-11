#!/usr/bin/env python3
"""Bulk-match small rivers/streams from a single Overpass download.

Why: per-water Nominatim queries miss small rivers with generic names
('Pârâul X', 'Valea Y', 'Acumulare Agrement'). Instead, download ALL
waterways of Romania in ONE Overpass query (a few thousand features),
then match our remaining un-geocoded waters against them locally with
fuzzy name matching. No rate limits, covers small streams too.

Output: data/rivers_osm.geojson (raw download, cached)
        data/matched_small_geocoded.geojson (matched waters with geometry)

Usage: python3 scripts/match_small_rivers.py [--force-download]
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_OUT = ROOT / "data" / "rivers_osm.geojson"
MATCHED_OUT = ROOT / "data" / "matched_small_geocoded.geojson"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {
    "User-Agent": "UndePescuimDataBot/1.0 (fishing waters map; contact: admin@undepescuim.ro)",
    "Accept": "application/json",
}

# Romania bbox: lat 43.6..48.3, lon 20.2..29.8 (slightly padded)
RO_BBOX = "(43.6,20.2,48.3,29.8)"

OVERPASS_QUERY = f"""
[out:json][timeout:180];
(
  way["waterway"~"^(river|stream)$"]({RO_BBOX});
  relation["waterway"~"^(river|stream)$"]({RO_BBOX});
);
out body;
>;
out skel qt;
"""


def norm(s: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def download_osm() -> dict:
    print(f"[osm] downloading Romanian waterways from Overpass...")
    last_err = None
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(url, data={"data": OVERPASS_QUERY}, headers=HEADERS, timeout=420)
            resp.raise_for_status()
            data = resp.json()
            RAW_OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            print(f"[osm] downloaded {len(data.get('elements', []))} elements from {url}")
            return data
        except Exception as e:
            last_err = e
            print(f"  [warn] {url} failed: {e}")
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")


def build_name_index(data: dict) -> tuple[dict, dict]:
    """Map normalized-name -> [element ids]. Builds id->geometry maps.

    Classic Overpass output: ways carry `nodes` refs, nodes carry lat/lon,
    relations carry `members`. Geometries are assembled here.
    """
    # node id -> (lat, lon)
    nodes = {
        el["id"]: (el.get("lat"), el.get("lon"))
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }
    # way id -> geometry (LineString)
    ways = {}
    name_index: dict[str, list[int]] = {}

    for el in data.get("elements", []):
        if el["type"] != "way":
            continue
        refs = el.get("nodes", [])
        coords = []
        for nid in refs:
            if nid in nodes:
                coords.append([nodes[nid][1], nodes[nid][0]])  # lon, lat
        if len(coords) >= 2:
            ways[el["id"]] = {
                "geometry": {"type": "LineString", "coordinates": coords},
                "name": el.get("tags", {}).get("name", ""),
                "waterway": el.get("tags", {}).get("waterway", ""),
            }
            nm = norm(el.get("tags", {}).get("name", ""))
            if nm:
                name_index.setdefault(nm, []).append(el["id"])

    # Relations: combine member way geometries into MultiLineString
    rel_geoms = {}
    for el in data.get("elements", []):
        if el["type"] != "relation":
            continue
        coords = []
        for m in el.get("members", []):
            if m["type"] == "way" and m["ref"] in ways:
                coords.append(ways[m["ref"]]["geometry"]["coordinates"])
        if coords:
            rel_geoms[el["id"]] = {
                "geometry": {"type": "MultiLineString", "coordinates": coords},
                "name": el.get("tags", {}).get("name", ""),
                "waterway": el.get("tags", {}).get("waterway", ""),
            }
            nm = norm(el.get("tags", {}).get("name", ""))
            if nm:
                name_index.setdefault(nm, []).append(el["id"])

    return name_index, {**ways, **rel_geoms}


def similarity(a: str, b: str) -> float:
    """Simple token-overlap similarity in [0,1]."""
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0.0
    inter = len(set(ta) & set(tb))
    return inter / max(len(ta), len(tb))


def match_water(water: dict, name_index: dict, geoms: dict) -> dict | None:
    """Find the best OSM geometry for a water. Returns feature dict or None."""
    name = water.get("name", "")
    nm = norm(name)
    # Strip generic prefixes like 'Raul', 'Parau', 'Valea', 'Lacul'
    core = re.sub(r"^(raul|paraul|valea|lacul|balta)\s+", "", nm)
    if not core:
        return None

    # Exact normalized match first
    exact = name_index.get(nm) or name_index.get(core)
    if exact:
        gid = exact[0]
        g = geoms.get(gid)
        if g:
            return make_feature(water, g, "osm_exact")

    # Fuzzy: token overlap >= 0.6 over all index entries
    best, best_score = None, 0.0
    for idx_name, ids in name_index.items():
        sc = similarity(core, idx_name)
        if sc > best_score:
            best_score = sc
            best = ids[0]
    if best is not None and best_score >= 0.6:
        g = geoms.get(best)
        if g:
            return make_feature(water, g, f"osm_fuzzy_{best_score:.2f}")

    return None


def make_feature(water: dict, g: dict, source: str) -> dict:
    return {
        "type": "Feature",
        "id": water.get("slug"),
        "properties": {
            "arebaltapeste_slug": water.get("slug"),
            "name": water.get("name"),
            "name_ro": water.get("name"),
            "type": water.get("type", "ape"),
            "source": "osm_bulk",
            "source_detail": source,
            "osm_id": None,
            "geocode_tier": "tier3_osm_bulk",
            "confidence": "medium" if source == "osm_exact" else "low",
            "judet": water.get("judet"),
        },
        "geometry": g["geometry"],
    }


def load_waters() -> list[dict]:
    snap = json.loads(
        (ROOT / "data" / "raw" / "arebaltapeste_probe" / "snapshot_waters.json").read_text(encoding="utf-8")
    )
    return snap if isinstance(snap, list) else snap.get("waters", [])


def already_covered() -> set[str]:
    """Slugs already having geometry (premapped + geocoded_public + private)."""
    covered = set()
    for p in (ROOT / "data" / "premapped").glob("*.geojson"):
        if p.name == "README.md":
            continue
        fc = json.loads(p.read_text(encoding="utf-8"))
        for f in fc.get("features", []):
            s = (f.get("properties") or {}).get("arebaltapeste_slug")
            if s:
                covered.add(s)
    for path in (ROOT / "data" / "geocoded_public.geojson", ROOT / "data" / "geocoded_private.geojson"):
        if path.exists():
            fc = json.loads(path.read_text(encoding="utf-8"))
            for f in fc.get("features", []):
                s = (f.get("properties") or {}).get("arebaltapeste_slug")
                if s:
                    covered.add(s)
    return covered


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-download", action="store_true", help="re-download OSM data")
    args = ap.parse_args()

    if RAW_OUT.exists() and not args.force_download:
        data = json.loads(RAW_OUT.read_text(encoding="utf-8"))
        print(f"[osm] using cached download ({len(data.get('elements', []))} elements)")
    else:
        data = download_osm()

    name_index, geoms = build_name_index(data)
    print(f"[osm] index: {len(name_index)} named waterways, {len(geoms)} geometries")

    waters = load_waters()
    covered = already_covered()
    todo = [w for w in waters if w.get("slug") not in covered and w.get("subtype") == "rau"]
    print(f"[match] {len(waters)} waters, {len(covered)} already covered, {len(todo)} rivers to try")

    matched = []
    for w in todo:
        f = match_water(w, name_index, geoms)
        if f:
            matched.append(f)

    MATCHED_OUT.write_text(json.dumps({
        "type": "FeatureCollection",
        "metadata": {
            "pipeline": "osm_bulk_small_rivers",
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "tried": len(todo),
            "matched": len(matched),
        },
        "features": matched,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"[match] matched {len(matched)}/{len(todo)} small rivers -> {MATCHED_OUT}")


if __name__ == "__main__":
    main()
