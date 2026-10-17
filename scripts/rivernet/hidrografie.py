"""Fallback geometry layer: the ANAR "Hidrografie" cadastral river network.

Source: data.gov.ro dataset ``hidrografie`` (Administrația Națională Apele
Române), resource "Cursuri de apa rauri", CC BY 4.0. See
docs/data-sources/hidrografie.md.

OpenStreetMap stays the primary geometry (plan D1). This layer only fills
courses OSM lacks: the matcher tries it last (``matcher.match`` tier 3), and a
sector on an ANAR course is never ``high`` confidence.

Two steps, both deterministic:

* ``normalise-hidrografie`` (needs ``pyshp``, run once per dataset version):
  shapefile (EPSG:3844) -> extract-schema JSONL (one ``way`` per cadastral
  course, ``tags.ref`` = cadastral code), simplified at ``SIMPLIFY_M`` in
  EPSG:3844, coordinates in EPSG:4326 rounded to ``COORD_DP``. The output is
  pinned as a release asset by ``data/rivernet/fallback_manifest.json``.
* ``fallback``: normalised JSONL -> course records (``course_id`` =
  ``anar:<code>``, ``source`` = ``anar``) for the courses some water may need,
  merged into ``courses.jsonl.gz`` and ``course_index.json``.

Topology comes from the cadastral code, not from geometry: ``RO12-1-17-24-3-0-0``
flows into ``RO12-1-17-24-0-0-0``. Courses are digitised source -> mouth (99 %
of tributaries end at their parent); the rest are flipped so that the end
nearest the parent is the outlet.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .courses import county_intervals
from .extract_schema import Extract, load_extract
from .lr import Line
from .planar import PolygonIndex
from .textnorm import fix_diacritics, fold, river_key, river_keys, stem_key

SOURCE = "anar"
PREFIX = "anar:"
SIMPLIFY_M = 2.0
COORD_DP = 6
GAP_BRIDGE_M = 250.0  # multipart courses: parts closer than this are joined
JUNCTION_MAX_M = 500.0  # a tributary outlet this close to its parent is a junction
DEFAULT_MANIFEST = Path("data/rivernet/fallback_manifest.json")

_PAREN_RE = re.compile(r"^(.*?)\s*\((.*)\)\s*$")


# ------------------------------------------------------------------ names/codes


def parent_code(code: str) -> str | None:
    """Cadastral parent: the last non-zero level set to 0 (``None`` at the top)."""
    head, sep, rest = code.partition("RO")
    parts = (rest if sep else code).split("-")
    for i in range(len(parts) - 1, 1, -1):  # level 0 is the basin, level 1 the main river
        if parts[i] != "0":
            parts[i] = "0"
            return "RO" + "-".join(parts) if sep else "-".join(parts)
    return None


def split_names(*values: str | None) -> list[str]:
    """``"Baboia (Eruga, Baboias)"`` -> ``["Baboia", "Eruga", "Baboias"]``; dupes dropped."""
    out: list[str] = []
    for v in values:
        v = (v or "").strip()
        if not v:
            continue
        m = _PAREN_RE.match(v)
        names = [m.group(1), *m.group(2).split(",")] if m else [v]
        for n in names:
            n = fix_diacritics(n.strip())
            if n and fold(n) not in {fold(x) for x in out}:
                out.append(n)
    return out


# ------------------------------------------------------------- normalisation


def _join_parts(parts: list[list[tuple[float, float]]]) -> tuple[list[tuple[float, float]], bool]:
    """Chain parts end-to-start in file order when the gap is <= GAP_BRIDGE_M
    (metric coordinates); otherwise keep the longest chain. Returns (coords, dropped)."""
    import math

    chains: list[list[tuple[float, float]]] = []
    for p in parts:
        if len(p) < 2:
            continue
        if chains:
            a = chains[-1][-1]
            if math.hypot(p[0][0] - a[0], p[0][1] - a[1]) <= GAP_BRIDGE_M:
                chains[-1] = chains[-1] + (p[1:] if p[0] == a else p)
                continue
        chains.append(list(p))
    if not chains:
        return [], False

    def length(c):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(c, c[1:]))

    best = max(chains, key=length)
    return best, len(chains) > 1


def normalise_rows(rows: Iterable[tuple[Mapping[str, Any], list[list[tuple[float, float]]]]]) -> Iterator[dict[str, Any]]:
    """(attributes, metric parts) -> extract ``way`` records, unsorted."""
    from pyproj import Transformer
    from shapely.geometry import LineString

    tf = Transformer.from_crs(3844, 4326, always_xy=True)
    for attrs, parts in rows:
        code = (attrs.get("codcadas_1") or "").strip()
        names = split_names(attrs.get("denumire"), attrs.get("denumire2"), attrs.get("denumirein"))
        coords, dropped = _join_parts(parts)
        if not code or not names or len(coords) < 2:
            continue
        simple = LineString(coords).simplify(SIMPLIFY_M, preserve_topology=False)
        pts = [tf.transform(x, y) for x, y in simple.coords]
        wgs = [[round(x, COORD_DP), round(y, COORD_DP)] for x, y in pts]
        wgs = [c for i, c in enumerate(wgs) if i == 0 or c != wgs[i - 1]]
        if len(wgs) < 2:
            continue
        tags = {"waterway": "canal" if attrs.get("canal") else "river", "name": names[0], "ref": code}
        if len(names) > 1:
            tags["alt_name"] = ";".join(names[1:])
        if dropped:
            tags["fixme"] = "multipart"
        yield {"t": "way", "id": int(attrs["objectid_1"]), "nodes": [], "coords": wgs, "tags": tags}


def write_extract(path: str | Path, meta: Mapping[str, Any], ways: Iterable[dict[str, Any]]) -> int:
    """Deterministic gzip JSONL (meta first, ways by id); returns the way count."""
    recs = sorted(ways, key=lambda r: r["id"])
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
        with io.BufferedWriter(gz) as out:  # type: ignore[arg-type]
            for rec in [dict(meta), *recs]:
                out.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    return len(recs)


def read_shapefile(shp: str | Path) -> Iterator[tuple[dict[str, Any], list[list[tuple[float, float]]]]]:
    import shapefile  # pyshp; only needed for normalisation

    r = shapefile.Reader(str(shp), encoding="utf-8")
    for s, rec in zip(r.iterShapes(), r.iterRecords()):
        bounds = list(s.parts) + [len(s.points)]
        parts = [[(float(x), float(y)) for x, y in s.points[a:b]] for a, b in zip(bounds, bounds[1:])]
        yield rec.as_dict(), parts


# ------------------------------------------------------------- course records


def _orient(ways: Mapping[str, list[tuple[float, float]]]) -> dict[str, list[tuple[float, float]]]:
    """Flip a course whose *first* vertex is nearer its parent than its last."""
    from shapely.geometry import LineString, Point

    lines = {c: LineString(xy) for c, xy in ways.items()}
    out: dict[str, list[tuple[float, float]]] = {}
    for code, xy in ways.items():
        pc = parent_code(code)
        pl = lines.get(pc) if pc else None
        if pl is not None and pl.distance(Point(xy[0])) < pl.distance(Point(xy[-1])):
            out[code] = list(reversed(xy))
        else:
            out[code] = list(xy)
    return out


def _counties(line: Line, polys: Mapping[str, PolygonIndex]) -> list[dict[str, Any]]:
    out = []
    for name in sorted(polys):
        for a, b in county_intervals(line, polys[name]):
            out.append({"county": name, "m_from": round(a, 1), "m_to": round(b, 1)})
    out.sort(key=lambda c: (c["m_from"], c["county"]))
    return out


def course_id(code: str) -> str:
    return PREFIX + code


def build_records(
    extract: Extract,
    counties_geojson: Mapping[str, Any] | None,
    keep: Callable[[list[str], set[str]], bool] | None = None,
) -> list[dict[str, Any]]:
    """Course records for the kept cadastral courses, sorted by course_id.

    ``keep(names, counties)`` selects the courses to emit (``counties`` = the
    county names the course crosses); junctions and ``receives_into`` still
    see every course in the extract.
    """
    by_code: dict[str, Any] = {}
    for w in extract.ways.values():
        code = w.tags.get("ref")
        if code:
            by_code[code] = w
    coords = _orient({c: list(w.coords) for c, w in by_code.items()})
    children: dict[str, list[str]] = {}
    for code in sorted(by_code):
        pc = parent_code(code)
        if pc in by_code:
            children.setdefault(pc, []).append(code)
    polys = {
        f["properties"]["name"]: PolygonIndex(f["geometry"])
        for f in (counties_geojson or {}).get("features", [])
        if f.get("properties", {}).get("name")
    }
    out: list[dict[str, Any]] = []
    for code in sorted(by_code):
        w = by_code[code]
        names = names_of(w.tags)
        if keep is not None and not keep(names, set()):
            continue  # cheap name pre-filter before the measures are computed
        line = Line.from_coords(coords[code])
        counties = _counties(line, polys)
        if keep is not None and not keep(names, {c["county"] for c in counties}):
            continue
        junctions = []
        for ch in children.get(code, []):
            m, d = line.locate(*coords[ch][-1])
            if d <= JUNCTION_MAX_M:
                junctions.append({"m": round(m, 1), "node": None, "side": "in", "tributary_course_id": course_id(ch)})
        junctions.sort(key=lambda j: (j["m"], j["tributary_course_id"]))
        pc = parent_code(code)
        qa = ["fallback_source"] + (["multipart_dropped"] if w.tags.get("fixme") == "multipart" else [])
        out.append({
            "course_id": course_id(code),
            "source": SOURCE,
            "ref": code,
            "name": names[0],
            "name_key": river_key(names[0]),
            "stem_key": stem_key(names[0]),
            "aliases": names[1:],
            "wikidata": None,
            "relation_id": None,
            "way_ids": [w.id],
            "length_m": round(line.length_m, 1),
            "geometry": {"type": "LineString", "coordinates": [list(c) for c in line.coords]},
            "vertex_m": [round(m, 1) for m in line.vertex_m],
            "outlet_node": None,
            "receives_into": course_id(pc) if pc in by_code else None,
            "junctions": junctions,
            "synthetic": [],
            "braids_dropped_m": 0.0,
            "counties": counties,
            "qa": sorted(qa),
        })
    return out


def names_of(tags: Mapping[str, str]) -> list[str]:
    alts = [a for a in (tags.get("alt_name") or "").split(";") if a]
    return [tags["name"], *alts]


def index_entries(extract: Extract) -> dict[str, list[str]]:
    """course_id -> name keys for every ANAR course (for ``course_index.json``)."""
    out: dict[str, list[str]] = {}
    for w in extract.ways.values():
        code = w.tags.get("ref")
        if not code:
            continue
        keys: list[str] = []
        for n in names_of(w.tags):
            keys += [k for k in river_keys(n) if k not in keys]
        out[course_id(code)] = keys
    return out


def osm_coverage(courses: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], float]:
    """(stem, folded county) -> length (m) of the longest OSM course answering it."""
    out: dict[tuple[str, str], float] = {}
    for c in courses:
        if c.get("source") == SOURCE:
            continue
        stems = {stem_key(c.get("name"))} | {stem_key(a) for a in c.get("aliases") or []}
        for iv in c.get("counties") or []:
            county = fold(iv.get("county"))
            for st in stems:
                if st:
                    out[(st, county)] = max(out.get((st, county), 0.0), float(c.get("length_m") or 0.0))
    return out


def wanted(
    waters: Iterable[Mapping[str, Any]],
    parsed: Mapping[str, Mapping[str, Any]],
    covered: Mapping[tuple[str, str], float] | None = None,
) -> Callable[[list[str], set[str]], bool]:
    """Keep a course whose stem or key matches a river water's name, or a
    CONFLUENCE target in its ``limite``, in that water's county - unless an
    OSM course already answers that name there (``covered``, see
    ``osm_coverage``): the matcher never reaches the fallback then. For a
    water's own name the OSM course must also not be a fragment (shorter than
    ``matcher.FRAGMENT_FIT`` x contract km), which the matcher would replace.

    Called with an empty county set it is a pure name pre-filter."""
    from .matcher import FRAGMENT_FIT, contract_km

    covered = covered or {}
    stems: dict[str, set[str]] = {}
    keys: dict[str, set[str]] = {}

    def add(name: str | None, county: str, with_keys: bool, need_m: float = 0.0) -> None:
        st = stem_key(name)
        have = covered.get((st, county))
        if not st or (have is not None and have >= need_m):
            return
        stems.setdefault(st, set()).add(county)
        if with_keys:
            for k in river_keys(name):
                keys.setdefault(k, set()).add(county)

    for w in waters:
        if w.get("subtype") != "rau":
            continue
        county = fold(w.get("judet"))
        km = contract_km(w.get("dimensiune"))
        add(w.get("name"), county, False, FRAGMENT_FIT * km * 1000 if km else 0.0)
        spec = parsed.get(w.get("slug")) or {}
        for end in ("from", "to"):
            e = spec.get(end) or {}
            if e.get("kind") == "CONFLUENCE" and e.get("target"):
                add(e["target"], county, True)

    def keep(names: list[str], counties: set[str]) -> bool:
        want: set[str] = set()
        for n in names:
            want |= stems.get(stem_key(n), set())
            for k in river_keys(n):
                want |= keys.get(k, set())
        if not counties:
            return bool(want)
        return bool(want & {fold(c) for c in counties})

    return keep


# ----------------------------------------------------------------------- merge


def merge_courses(path: str | Path, records: Sequence[dict[str, Any]]) -> int:
    """Replace every ``anar:*`` record in a courses file with ``records``
    (appended after the OSM records, in course_id order). Returns the size."""
    from .build import write_jsonl_gz

    p = Path(path)
    with gzip.open(p, "rt", encoding="utf-8") as f:
        osm = [r for r in (json.loads(x) for x in f if x.strip()) if not r["course_id"].startswith(PREFIX)]
    return write_jsonl_gz(p, [*osm, *sorted(records, key=lambda r: r["course_id"])])


def merge_index(path: str | Path, entries: Mapping[str, list[str]]) -> None:
    p = Path(path)
    idx = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    idx = {k: v for k, v in idx.items() if not k.startswith(PREFIX)}
    idx.update(entries)
    p.write_text(json.dumps(idx, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------------- CLI


def cli_normalise(argv: Sequence[str]) -> int:
    """`python -m rivernet normalise-hidrografie`: shapefile -> extract JSONL."""
    from .fetch_input import sha256_file

    ap = argparse.ArgumentParser(prog="rivernet normalise-hidrografie")
    ap.add_argument("--shp", required=True, help="CursuriApaRauri.shp (EPSG:3844)")
    ap.add_argument("--zip", default=None, help="the downloaded resource zip, to record its sha256")
    ap.add_argument("--modified", default=None, help="resource date (YYYY-MM-DD) for the meta record")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(list(argv))
    meta = {
        "t": "meta", "schema": 1, "source": "anar-hidrografie",
        "osm_timestamp": ns.modified, "pbf_sha256": sha256_file(ns.zip) if ns.zip else None,
        "filters": f"CursuriApaRauri; simplify {SIMPLIFY_M} m EPSG:3844; {COORD_DP} dp EPSG:4326",
        "extractor_version": "hidrografie-1",
    }
    n = write_extract(ns.out, meta, normalise_rows(read_shapefile(ns.shp)))
    print(json.dumps({"ways": n, "out": ns.out}), file=sys.stderr)
    return 0


def cli_fallback(argv: Sequence[str]) -> int:
    """`python -m rivernet fallback`: merge ANAR courses into the course files."""
    from .fetch_input import ManifestError, fetch

    ap = argparse.ArgumentParser(prog="rivernet fallback")
    ap.add_argument("--extract", default="data/cache/rivernet/anar-hidrografie.jsonl.gz",
                    help="normalised ANAR JSONL; downloaded from the manifest when missing")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--courses", default="data/rivernet/courses.jsonl.gz")
    ap.add_argument("--course-index", default="data/rivernet/course_index.json")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--parsed", default="data/sectors/limits_parsed.jsonl")
    ap.add_argument("--counties", default="public/data/counties.geojson")
    ns = ap.parse_args(list(argv))

    ex_path = Path(ns.extract)
    if not ex_path.exists():
        man = json.loads(Path(ns.manifest).read_text(encoding="utf-8"))
        try:
            fetch(man["asset"]["url"], ex_path, man["asset"]["sha256"])
        except ManifestError as exc:
            print(f"rivernet fallback: {exc}", file=sys.stderr)
            return 1
    if not Path(ns.courses).exists():
        print(f"rivernet fallback: {ns.courses} missing - run `rivernet build` first", file=sys.stderr)
        return 1
    extract = load_extract(ex_path)
    with gzip.open(ns.courses, "rt", encoding="utf-8") as f:
        covered = osm_coverage(json.loads(x) for x in f if x.strip())
    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    parsed: dict[str, Any] = {}
    if Path(ns.parsed).exists():
        for line in Path(ns.parsed).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            parsed[r["slug"]] = r["spec"]
    cj = json.loads(Path(ns.counties).read_text(encoding="utf-8")) if Path(ns.counties).exists() else None
    records = build_records(extract, cj, wanted(waters, parsed, covered))
    size = merge_courses(ns.courses, records)
    merge_index(ns.course_index, index_entries(extract))
    print(json.dumps({"anar_courses": len(records), "courses_bytes": size}))
    return 0
