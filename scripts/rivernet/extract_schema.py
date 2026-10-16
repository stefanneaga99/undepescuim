"""Schema and loader for the normalised OSM water extract (schema v1).

The extract is one JSON object per line (``.jsonl`` or ``.jsonl.gz``), sorted
by record type (meta, rel, way, node, area) and then by id. See
docs/plans/river-geometry-v2.md §3.3. Standard library only.

Records::

    {"t":"meta","schema":1,"source":"geofabrik","osm_timestamp":...,"pbf_sha256":...,...}
    {"t":"way","id":123,"nodes":[1,2,3],"coords":[[lon,lat],...],"tags":{...}}
    {"t":"node","id":456,"coord":[lon,lat],"tags":{...}}
    {"t":"rel","id":789,"tags":{...},"members":[{"type":"w","ref":123,"role":"main_stream"}]}
    {"t":"area","id":"w555","tags":{...},"geometry":{GeoJSON Polygon|MultiPolygon}}
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping

SCHEMA_VERSION = 1

LonLat = tuple[float, float]


@dataclass(frozen=True)
class Meta:
    schema: int
    source: str
    osm_timestamp: str | None
    pbf_sha256: str | None
    filters: str | None
    extractor_version: str | None
    bbox: tuple[float, float, float, float] | None


@dataclass(frozen=True)
class Way:
    id: int
    nodes: tuple[int, ...]
    coords: tuple[LonLat, ...]
    tags: Mapping[str, str]


@dataclass(frozen=True)
class Node:
    id: int
    coord: LonLat
    tags: Mapping[str, str]


@dataclass(frozen=True)
class Member:
    type: str  # "n" | "w" | "r"
    ref: int
    role: str


@dataclass(frozen=True)
class Rel:
    id: int
    tags: Mapping[str, str]
    members: tuple[Member, ...]


@dataclass(frozen=True)
class Area:
    id: str  # "w<way id>" or "r<relation id>"
    tags: Mapping[str, str]
    geometry: Mapping[str, Any]  # GeoJSON Polygon | MultiPolygon


@dataclass
class Extract:
    meta: Meta
    ways: dict[int, Way] = field(default_factory=dict)
    nodes: dict[int, Node] = field(default_factory=dict)
    rels: dict[int, Rel] = field(default_factory=dict)
    areas: dict[str, Area] = field(default_factory=dict)


def open_text(path: str | Path, mode: str = "rt"):
    """Open a possibly gzip-compressed text file as UTF-8."""
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8")
    return open(path, mode, encoding="utf-8")


def iter_records(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield the raw JSON records of an extract file."""
    with open_text(path) as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON ({exc.msg})") from exc


def _lonlat(value: Any) -> LonLat:
    return (float(value[0]), float(value[1]))


def load_extract(path: str | Path) -> Extract:
    """Load an extract file fully into memory.

    Raises ``ValueError`` for a missing/duplicate meta record, an unsupported
    schema version, or an unknown record type.
    """
    meta: Meta | None = None
    out: Extract | None = None
    for rec in iter_records(path):
        kind = rec.get("t")
        if kind == "meta":
            if meta is not None:
                raise ValueError(f"{path}: more than one meta record")
            if rec.get("schema") != SCHEMA_VERSION:
                raise ValueError(
                    f"{path}: unsupported extract schema {rec.get('schema')!r} "
                    f"(expected {SCHEMA_VERSION})"
                )
            bbox = rec.get("bbox")
            meta = Meta(
                schema=rec["schema"],
                source=rec.get("source", ""),
                osm_timestamp=rec.get("osm_timestamp"),
                pbf_sha256=rec.get("pbf_sha256"),
                filters=rec.get("filters"),
                extractor_version=rec.get("extractor_version"),
                bbox=tuple(float(v) for v in bbox) if bbox else None,  # type: ignore[arg-type]
            )
            out = Extract(meta=meta)
            continue
        if out is None:
            raise ValueError(f"{path}: first record must be the meta record")
        if kind == "way":
            out.ways[rec["id"]] = Way(
                id=rec["id"],
                nodes=tuple(rec["nodes"]),
                coords=tuple(_lonlat(c) for c in rec["coords"]),
                tags=dict(rec.get("tags", {})),
            )
        elif kind == "node":
            out.nodes[rec["id"]] = Node(
                id=rec["id"], coord=_lonlat(rec["coord"]), tags=dict(rec.get("tags", {}))
            )
        elif kind == "rel":
            out.rels[rec["id"]] = Rel(
                id=rec["id"],
                tags=dict(rec.get("tags", {})),
                members=tuple(
                    Member(type=m["type"], ref=m["ref"], role=m.get("role", ""))
                    for m in rec.get("members", [])
                ),
            )
        elif kind == "area":
            out.areas[rec["id"]] = Area(
                id=rec["id"], tags=dict(rec.get("tags", {})), geometry=rec["geometry"]
            )
        else:
            raise ValueError(f"{path}: unknown record type {kind!r}")
    if out is None:
        raise ValueError(f"{path}: empty extract (no meta record)")
    return out
