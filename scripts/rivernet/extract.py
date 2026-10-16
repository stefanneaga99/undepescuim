"""Normalise an osmium-tool water extract into the schema-v1 JSONL (T1.1).

Inputs (both produced by osmium-tool in the ``osm-extract`` workflow, T1.2)::

    osmium tags-filter -R input.osm.pbf <filters> -o water.osm.pbf
    osmium cat -f opl water.osm.pbf -o water.opl
    osmium export water.osm.pbf -f geojsonseq --add-unique-id=type_id \
        -o water-areas.geojsonseq

Output: ``water-extract.jsonl.gz`` (see ``extract_schema``): deterministic
(sorted, fixed gzip mtime, 7-decimal coordinates), whitelisted tags only.

Deviation from the plan: it names pyosmium; the pipeline uses the osmium-tool
CLI instead (nothing to compile, locally testable) and parses its text output
here with the standard library only.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from . import __version__
from .extract_schema import SCHEMA_VERSION, open_text

COORD_DECIMALS = 7

# Exact tag keys kept; ``name:*`` / ``alt_name:*`` / ``old_name:*`` are kept by prefix.
TAG_WHITELIST = frozenset(
    {
        "name", "alt_name", "old_name", "official_name", "short_name", "int_name",
        "ref", "ref:cadastre", "ref:cadastral", "ref:wise", "wikidata",
        "waterway", "natural", "water", "landuse", "intermittent", "tunnel",
        "culvert", "boat", "salt", "type", "boundary", "admin_level", "place",
        "man_made", "bridge", "dam", "weir", "power", "ford", "lock", "layer",
        "start_date", "population", "is_in", "is_in:county",
    }
)
TAG_PREFIXES = ("name:", "alt_name:", "old_name:")

# way filters
WATERWAY_KEEP_ALL = True  # any ``waterway=*`` way is kept
BRIDGE_MAX_DISTANCE_M = 40.0
_GRID_CELL_DEG = 0.001  # ~111 m of latitude

_ESC_RE = re.compile(r"%([0-9a-fA-F]+)%")
_AREA_TAGS_KEEP = (
    ("natural", {"water", "wetland"}),
    ("waterway", {"riverbank", "dock"}),
    ("landuse", {"reservoir", "basin"}),
    ("boundary", {"administrative"}),
)


# --------------------------------------------------------------------------- OPL


def unescape_opl(text: str) -> str:
    """Decode OPL ``%hex%`` escapes (space, comma, equals, percent, ...)."""
    if "%" not in text:
        return text
    return _ESC_RE.sub(lambda m: chr(int(m.group(1), 16)), text)


def parse_tags(field: str) -> dict[str, str]:
    """Parse the payload of an OPL ``T`` field (``k=v,k2=v2``)."""
    tags: dict[str, str] = {}
    if not field:
        return tags
    for part in field.split(","):
        if not part:
            continue
        key, sep, value = part.partition("=")
        if not sep:
            continue
        tags[unescape_opl(key)] = unescape_opl(value)
    return tags


def parse_opl_line(line: str) -> dict[str, Any] | None:
    """Parse one OPL object line.

    Returns ``None`` for blank/comment lines and deleted objects. Result keys:
    ``kind`` ('n'|'w'|'r'), ``id``, ``tags`` and, per kind, ``lon``/``lat``,
    ``nodes`` or ``members`` (list of ``(type, ref, role)``).
    """
    line = line.rstrip("\n")
    if not line or line.startswith("#"):
        return None
    tokens = line.split(" ")
    head = tokens[0]
    kind = head[0]
    if kind not in "nwr":
        raise ValueError(f"unknown OPL object type in line: {line[:60]!r}")
    obj: dict[str, Any] = {"kind": kind, "id": int(head[1:]), "tags": {}}
    lon = lat = None
    for tok in tokens[1:]:
        if not tok:
            continue
        code, payload = tok[0], tok[1:]
        if code == "d":
            if payload == "D":
                return None  # deleted
        elif code == "T":
            obj["tags"] = parse_tags(payload)
        elif code == "x":
            lon = float(payload) if payload else None
        elif code == "y":
            lat = float(payload) if payload else None
        elif code == "N":
            obj["nodes"] = [int(p[1:]) for p in payload.split(",") if p]
        elif code == "M":
            members = []
            for p in payload.split(","):
                if not p:
                    continue
                ref, _, role = p.partition("@")
                members.append((ref[0], int(ref[1:]), unescape_opl(role)))
            obj["members"] = members
    if kind == "n":
        if lon is None or lat is None:
            return None  # node without location (deleted/invisible)
        obj["lon"], obj["lat"] = lon, lat
    return obj


def iter_opl(path: str | Path) -> Iterator[dict[str, Any]]:
    with open_text(path) as fh:
        for line in fh:
            obj = parse_opl_line(line)
            if obj is not None:
                yield obj


# ----------------------------------------------------------------------- helpers


def filter_tags(tags: dict[str, str]) -> dict[str, str]:
    return {
        k: v
        for k, v in sorted(tags.items())
        if k in TAG_WHITELIST or k.startswith(TAG_PREFIXES)
    }


def _round(value: float) -> float:
    return round(value, COORD_DECIMALS)


def _round_coords(obj: Any) -> Any:
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [_round(float(obj[0])), _round(float(obj[1]))]
        return [_round_coords(o) for o in obj]
    return obj


def _is_bridge(tags: dict[str, str]) -> bool:
    return tags.get("man_made") == "bridge" or "bridge" in tags


def _cell(lon: float, lat: float) -> tuple[int, int]:
    return (math.floor(lon / _GRID_CELL_DEG), math.floor(lat / _GRID_CELL_DEG))


class GridIndex:
    """Tiny point index (pure Python) to ask 'is any point within d metres?'."""

    def __init__(self) -> None:
        self._cells: dict[tuple[int, int], list[tuple[float, float]]] = {}

    def add(self, lon: float, lat: float) -> None:
        self._cells.setdefault(_cell(lon, lat), []).append((lon, lat))

    def near(self, lon: float, lat: float, max_m: float) -> bool:
        cx, cy = _cell(lon, lat)
        kx = 1 + int(max_m / (111_320.0 * math.cos(math.radians(lat)) * _GRID_CELL_DEG))
        ky = 1 + int(max_m / (110_574.0 * _GRID_CELL_DEG))
        m_lon = 111_320.0 * math.cos(math.radians(lat))
        for dx in range(-kx, kx + 1):
            for dy in range(-ky, ky + 1):
                for plon, plat in self._cells.get((cx + dx, cy + dy), ()):
                    if math.hypot((plon - lon) * m_lon, (plat - lat) * 110_574.0) <= max_m:
                        return True
        return False


# ------------------------------------------------------------------------ areas


def _area_wanted(tags: dict[str, str]) -> bool:
    return any(tags.get(key) in values for key, values in _AREA_TAGS_KEEP)


def iter_areas(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield normalised ``area`` records from an osmium geojsonseq export."""
    with open_text(path) as fh:
        for line in fh:
            line = line.strip().lstrip("\x1e").strip()
            if not line:
                continue
            feat = json.loads(line)
            geom = feat.get("geometry") or {}
            if geom.get("type") not in ("Polygon", "MultiPolygon"):
                continue
            props = feat.get("properties") or {}
            tags = filter_tags({k: str(v) for k, v in props.items() if not k.startswith("@")})
            if not _area_wanted(tags):
                continue
            raw_id = feat.get("id", props.get("@id"))
            if raw_id is None:
                continue
            yield {
                "t": "area",
                "id": str(raw_id),
                "tags": tags,
                "geometry": {
                    "type": geom["type"],
                    "coordinates": _round_coords(geom["coordinates"]),
                },
            }


# ---------------------------------------------------------------------- extract


def build_records(
    opl_path: str | Path, areas_path: str | Path | None
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build the sorted list of (non-meta) records and some counters."""
    # pass 1: ways and relations (nodes are skipped cheaply)
    ways: dict[int, dict[str, Any]] = {}
    rels: dict[int, dict[str, Any]] = {}
    with open_text(opl_path) as fh:
        for line in fh:
            if line[:1] == "n":
                continue
            obj = parse_opl_line(line)
            if obj is None:
                continue
            if obj["kind"] == "w":
                ways[obj["id"]] = obj
            elif obj["kind"] == "r":
                rels[obj["id"]] = obj

    kept_rels = {
        rid: r for rid, r in rels.items() if r["tags"].get("type") == "waterway"
    }
    member_ways = {
        ref for r in kept_rels.values() for (t, ref, _role) in r.get("members", []) if t == "w"
    }

    # pass 2: node coordinates for the ways we may keep, plus tagged nodes
    needed = {n for w in ways.values() for n in w.get("nodes", [])}
    coords: dict[int, tuple[float, float]] = {}
    tagged_nodes: dict[int, dict[str, Any]] = {}
    with open_text(opl_path) as fh:
        for line in fh:
            if line[:1] != "n":
                continue
            obj = parse_opl_line(line)
            if obj is None:
                continue
            nid = obj["id"]
            if nid in needed:
                coords[nid] = (obj["lon"], obj["lat"])
            tags = filter_tags(obj["tags"])
            if tags:
                tagged_nodes[nid] = {
                    "t": "node",
                    "id": nid,
                    "coord": [_round(obj["lon"]), _round(obj["lat"])],
                    "tags": tags,
                }

    def way_record(w: dict[str, Any]) -> dict[str, Any] | None:
        ids = [n for n in w.get("nodes", []) if n in coords]
        if len(ids) < 2:
            return None
        return {
            "t": "way",
            "id": w["id"],
            "nodes": ids,
            "coords": [[_round(coords[n][0]), _round(coords[n][1])] for n in ids],
            "tags": filter_tags(w["tags"]),
        }

    kept_ways: dict[int, dict[str, Any]] = {}
    bridge_candidates: list[dict[str, Any]] = []
    for wid, w in ways.items():
        tags = w["tags"]
        if "waterway" in tags or wid in member_ways:
            rec = way_record(w)
            if rec:
                kept_ways[wid] = rec
        elif _is_bridge(tags):
            bridge_candidates.append(w)

    # bridges only matter next to a waterway
    if bridge_candidates:
        index = GridIndex()
        for rec in kept_ways.values():
            for lon, lat in rec["coords"]:
                index.add(lon, lat)
        for w in bridge_candidates:
            rec = way_record(w)
            if rec and any(index.near(lon, lat, BRIDGE_MAX_DISTANCE_M) for lon, lat in rec["coords"]):
                kept_ways[w["id"]] = rec

    rel_records = []
    for rid, r in kept_rels.items():
        rel_records.append(
            {
                "t": "rel",
                "id": rid,
                "tags": filter_tags(r["tags"]),
                "members": [
                    {"type": t, "ref": ref, "role": role}
                    for (t, ref, role) in r.get("members", [])
                ],
            }
        )

    area_records = list(iter_areas(areas_path)) if areas_path else []

    out: list[dict[str, Any]] = []
    out += sorted(rel_records, key=lambda r: r["id"])
    out += [kept_ways[i] for i in sorted(kept_ways)]
    out += [tagged_nodes[i] for i in sorted(tagged_nodes)]
    out += sorted(area_records, key=lambda r: r["id"])
    stats = {
        "rels": len(rel_records),
        "ways": len(kept_ways),
        "nodes": len(tagged_nodes),
        "areas": len(area_records),
    }
    return out, stats


def make_meta(
    *,
    osm_timestamp: str | None = None,
    pbf_sha256: str | None = None,
    filters: str | None = None,
    bbox: Sequence[float] | None = None,
    source: str = "geofabrik",
) -> dict[str, Any]:
    return {
        "t": "meta",
        "schema": SCHEMA_VERSION,
        "source": source,
        "osm_timestamp": osm_timestamp,
        "pbf_sha256": pbf_sha256,
        "filters": filters,
        "extractor_version": __version__,
        "bbox": list(bbox) if bbox else None,
    }


def write_extract(path: str | Path, meta: dict[str, Any], records: Iterable[dict[str, Any]]) -> None:
    """Write a deterministic extract (gzip when the name ends in .gz)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def dump(rec: dict[str, Any]) -> bytes:
        return (json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    with open(path, "wb") as raw:
        if path.suffix == ".gz":
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
                with io.BufferedWriter(gz) as out:  # type: ignore[arg-type]
                    out.write(dump(meta))
                    for rec in records:
                        out.write(dump(rec))
        else:
            raw.write(dump(meta))
            for rec in records:
                raw.write(dump(rec))


def extract(
    opl_path: str | Path,
    areas_path: str | Path | None,
    out_path: str | Path,
    **meta_kwargs: Any,
) -> dict[str, int]:
    records, stats = build_records(opl_path, areas_path)
    write_extract(out_path, make_meta(**meta_kwargs), records)
    return stats


# --------------------------------------------------------------------------- CLI


def cli(argv: Sequence[str]) -> int:
    p = argparse.ArgumentParser(prog="rivernet extract", description=__doc__.split("\n")[0])
    p.add_argument("--opl", required=True, help="osmium cat -f opl output")
    p.add_argument("--areas", help="osmium export -f geojsonseq output (water/boundary areas)")
    p.add_argument("--out", required=True, help="output .jsonl or .jsonl.gz")
    p.add_argument("--osm-timestamp")
    p.add_argument("--pbf-sha256")
    p.add_argument("--filters")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"))
    ns = p.parse_args(list(argv))
    stats = extract(
        ns.opl,
        ns.areas,
        ns.out,
        osm_timestamp=ns.osm_timestamp,
        pbf_sha256=ns.pbf_sha256,
        filters=ns.filters,
        bbox=ns.bbox,
    )
    print(
        "extract: {ways} ways, {rels} relations, {nodes} tagged nodes, {areas} areas -> {out}".format(
            out=ns.out, **stats
        ),
        file=sys.stderr,
    )
    return 0
