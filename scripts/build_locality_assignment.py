#!/usr/bin/env python3
"""Assign every water a single primary UAT locality (t_dd918db7).

Semantics (USER DECISION 2026-08-16): ONE primary locality per water — not
the plan's multi-"touches" alternative. Source priority:

  1. Spatial anchor, best geometry first:
       a. `geometryByCounty[ownCounty]` — the contract's actual territory
          (per-county clip from build_county_clip_geoms.py; already
          sector-sliced for Olt-style multi-contract rivers)
       b. sector-sliced course (sectorStart/sectorEnd) for waters whose
          geometry lies fully inside their county (no clip entry)
       c. full `geometry`
     → representative point = geometry centroid; for lines, fall back to the
       50%-course point, then a point guaranteed inside the geometry.
  2. No geometry → `coordinates` point-in-polygon.
  3. No geometry/coordinates → bbox center point-in-polygon.
  4. Still unresolved (the 271 ungeocoded ANPA/Romsilva entries) → parse
     locality names out of `limite` text against the UAT index, county-scoped
     to the water's judet, preferring "comuna X"/"com. X" mentions.

UAT polygons: data/raw/localities/uat_boundaries.geojson (from
scripts/fetch_uat_boundaries.py — Overpass admin_level=8 + București).

Output: adds `locality: string|null` to every water in
  public/data/waters.json            (indent=1, ensure_ascii=False)
  public/data/uncontracted_rivers.json (compact)
  public/data/uncontracted_lakes.json  (compact)
and writes data/raw/localities/coverage_report.json (per-county % resolved).

Run: .venv/bin/python scripts/build_locality_assignment.py
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import Point, shape
from shapely.ops import substring
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
LOCALITIES_DIR = ROOT / "data/raw/localities"
UAT_BOUNDARIES = LOCALITIES_DIR / "uat_boundaries.geojson"
COVERAGE_REPORT = LOCALITIES_DIR / "coverage_report.json"
WATERS_JSON = ROOT / "public/data/waters.json"
UNCONTRACTED_RIVERS_JSON = ROOT / "public/data/uncontracted_rivers.json"
UNCONTRACTED_LAKES_JSON = ROOT / "public/data/uncontracted_lakes.json"

_ROMANIAN = [("ș", "s"), ("ţ", "t"), ("ț", "t"), ("ă", "a"), ("î", "i"), ("â", "a")]


def norm_name(s: str) -> str:
    t = s.lower()
    for a, b in _ROMANIAN:
        t = t.replace(a, b)
    return re.sub(r"[\s\-]+", "", t)


def norm_text(s: str) -> str:
    """Normalize free text for token matching (keeps spaces between tokens)."""
    t = s.lower()
    for a, b in _ROMANIAN:
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9 .\-]", " ", t)


# Tokens that never denote a locality (river descriptors etc.) — used only to
# keep the `limite` fallback from matching "Valea Drăganului" → "Drăganu".
_STOPWORDS = {
    "izvoare", "izvorul", "confluenta", "conf", "confl", "varsarea", "varsare",
    "județ", "județul", "jud", "artificial", "natural", "zona", "acumularea",
    "acumulare", "raul", "râul", "paraul", "pârâul", "valea", "lacul",
    "lac", "rau", "para", "pârâu", "râu", "vale", "amonte", "aval", "mal",
    "malul", "pe", "in", "la", "de", "al", "din", "cu", "si", "sau", "pana",
    "intre", "spre", "langa", "peste", "sub", "catre", "drept", "stang",
    "sat", "comuna", "com", "oras", "municipiul", "cartier", "punct",
}


class UatIndex:
    """STRtree over UAT polygons + county-scoped name index for text fallback."""

    def __init__(self, geojson_path: Path, index_path: Path):
        fc = json.loads(geojson_path.read_text(encoding="utf-8"))
        self.polys: list[Any] = []
        self.names: list[str] = []
        for f in fc["features"]:
            p = shape(f["geometry"])
            if p.is_empty:
                continue
            self.polys.append(p)
            self.names.append(f["properties"]["name"])
        self.tree = STRtree(self.polys)
        self.by_county: dict[str, dict[str, str]] = {}
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        for county_key, uats in idx.items():
            self.by_county[county_key] = {
                k: v["name"] for k, v in uats.items()
            }

    def resolve_point(self, pt: Point) -> Optional[str]:
        """First UAT (deterministic order) covering the point; boundary hits OK."""
        if pt is None or pt.is_empty:
            return None
        candidates = self.tree.query(pt)
        # STRtree order is not guaranteed — sort for determinism (by name, id).
        ordered = sorted(
            (self.names[i], i) for i in candidates
        )
        for _, i in ordered:
            poly = self.polys[i]
            if poly.contains(pt):
                return self.names[i]
        for _, i in ordered:
            poly = self.polys[i]
            if poly.covers(pt):
                return self.names[i]
        return None

    def resolve_locality_from_text(self, text: str, county: str) -> Optional[str]:
        """Best UAT-name match inside `limite` text, scoped to the water's county."""
        if not text:
            return None
        uat_names = self.by_county.get(norm_name(county), {})
        if not uat_names:
            return None
        tokens = [t for t in norm_text(text).split() if t and t not in _STOPWORDS]
        if not tokens:
            return None

        # 1) "comuna X" / "com. X" / "com X" — capture following 1-3 tokens.
        m = re.search(r"\bcom(?:una|)\.?\s+([a-z0-9 .\-]+)", norm_text(text))
        if m:
            cand = m.group(1).strip().split()
            best = _best_ngram(cand, uat_names)
            if best:
                return best
        # 2) General scan, longest n-gram first.
        return _best_ngram(tokens, uat_names)


def _best_ngram(tokens: list[str], uat_names: dict[str, str]) -> Optional[str]:
    for n in range(min(4, len(tokens)), 0, -1):
        for i in range(len(tokens) - n + 1):
            gram = tokens[i : i + n]
            key = norm_name(" ".join(gram))
            if key in uat_names:
                return uat_names[key]
    return None


def line_midpoint(geom):
    """Point at 50% of a (multi)line course by length."""
    try:
        res = substring(geom, 0.5, 0.5, normalized=True)
    except Exception:
        res = None
    if res is None or res.is_empty:
        res = geom.interpolate(0.5, normalized=True)
    if res.geom_type != "Point":
        res = res.centroid
    return res if res.geom_type == "Point" else None


def primary_point(geom) -> Optional[Point]:
    """Single representative point for a water geometry (centroid-first)."""
    if geom is None or geom.is_empty:
        return None
    # Lines: centroid = length-weighted mean position along the course.
    if geom.geom_type in ("LineString", "MultiLineString"):
        return geom.centroid
    # Polygons: centroid is usually inside; representative_point is guaranteed.
    return geom.centroid


def geometry_source(water: dict) -> Any:
    """Best geometry to derive the primary locality from (see module doc)."""
    gbc = water.get("geometryByCounty")
    if gbc:
        clip = gbc.get(norm_name(water.get("judet", "")))
        if clip is not None:  # null clip = geometry outside county → skip
            return shape(clip) if clip else None
    geom = water.get("geometry")
    if not geom:
        return None
    g = shape(geom)
    ss, se = water.get("sectorStart"), water.get("sectorEnd")
    if ss is not None and se is not None and g.geom_type in ("LineString", "MultiLineString"):
        try:
            sliced = substring(g, float(ss), float(se), normalized=True)
            if not sliced.is_empty:
                return sliced
        except Exception:
            pass
    return g


def fallback_points(water: dict, source: Any) -> list[Point]:
    """Ordered fallback points when the primary centroid misses every UAT."""
    pts: list[Point] = []
    if source is not None and not source.is_empty:
        if source.geom_type in ("LineString", "MultiLineString"):
            mid = line_midpoint(source)
            if mid is not None and not mid.is_empty:
                pts.append(mid)
        rep = source.representative_point()
        if rep is not None and not rep.is_empty:
            pts.append(rep)
    coords = water.get("coordinates")
    if coords:
        pts.append(Point(float(coords[0]), float(coords[1])))
    bbox = water.get("bbox")
    if bbox and all(v is not None for v in bbox):
        pts.append(Point((float(bbox[0]) + float(bbox[2])) / 2, (float(bbox[1]) + float(bbox[3])) / 2))
    return pts


def assign_locality(water: dict, uat: UatIndex) -> Optional[str]:
    source = geometry_source(water)
    # 1. centroid of the best geometry
    pt = primary_point(source) if source is not None else None
    name = uat.resolve_point(pt) if pt is not None else None
    if name:
        return name
    # 2. fallback points (line midpoint, representative point, coords, bbox)
    for p in fallback_points(water, source):
        name = uat.resolve_point(p)
        if name:
            return name
    # 3. limite-text fallback (the 271 ungeocoded contracted waters)
    return uat.resolve_locality_from_text(water.get("limite") or "", water.get("judet", ""))


def dump_json(data, path: Path, compact: bool = False) -> None:
    text = (
        json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        if compact
        else json.dumps(data, indent=1, ensure_ascii=False)
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    uat = UatIndex(UAT_BOUNDARIES, LOCALITIES_DIR / "uat_index.json")
    print(f"UAT polygons: {len(uat.polys)}", file=sys.stderr)

    pools = [
        ("waters", WATERS_JSON, False),
        ("uncontracted_rivers", UNCONTRACTED_RIVERS_JSON, True),
        ("uncontracted_lakes", UNCONTRACTED_LAKES_JSON, True),
    ]
    report: dict[str, dict] = {}
    total_resolved = total_all = 0
    for label, path, compact in pools:
        data = json.loads(path.read_text(encoding="utf-8"))
        resolved = 0
        for w in data:
            loc = assign_locality(w, uat)
            w["locality"] = loc
            if loc:
                resolved += 1
        dump_json(data, path, compact=compact)
        pct = resolved / len(data) * 100 if data else 0.0
        print(f"{label}: {resolved}/{len(data)} resolved ({pct:.1f}%)", file=sys.stderr)
        total_resolved += resolved
        total_all += len(data)

    # Per-county coverage (over ALL pools, keyed by water.judet).
    per_county: dict[str, list[int]] = {}
    for label, path, _ in pools:
        for w in json.loads(path.read_text(encoding="utf-8")):
            entry = per_county.setdefault(w.get("judet", "?"), [0, 0])
            entry[1] += 1
            if w.get("locality"):
                entry[0] += 1
    for county, (res, tot) in sorted(per_county.items()):
        report[county] = {"resolved": res, "total": tot, "pct": round(res / tot * 100, 1) if tot else 0.0}
    report["_overall"] = {
        "resolved": total_resolved,
        "total": total_all,
        "pct": round(total_resolved / total_all * 100, 1) if total_all else 0.0,
    }
    COVERAGE_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print("\nCoverage per county:", file=sys.stderr)
    for county, r in sorted(report.items()):
        if county == "_overall":
            continue
        print(f"  {county:18s} {r['resolved']:5d}/{r['total']:5d}  {r['pct']:5.1f}%", file=sys.stderr)
    print(f"  {'_overall':18s} {report['_overall']['resolved']:5d}/{report['_overall']['total']:5d}  {report['_overall']['pct']:5.1f}%", file=sys.stderr)
    print(f"wrote {COVERAGE_REPORT}", file=sys.stderr)


if __name__ == "__main__":
    main()
