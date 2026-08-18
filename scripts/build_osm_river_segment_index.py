#!/usr/bin/env python3
"""Build a deterministic, offline index for an Overpass JSON snapshot.

The command never downloads data.  The index is JSONL (gzip by default): one
record per way followed by one record per relation, with relation membership
kept in source order and all records sorted by OSM id.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def load_snapshot(path: Path) -> tuple[dict[int, dict], dict[int, dict], list[dict]]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise ValueError("snapshot must contain an elements array")
    nodes = {int(e["id"]): e for e in elements if e.get("type") == "node"}
    ways = {int(e["id"]): e for e in elements if e.get("type") == "way"}
    relations = [e for e in elements if e.get("type") == "relation"]
    return nodes, ways, relations

def aliases(tags: dict[str, Any]) -> list[str]:
    keys = ("name", "alt_name", "loc_name", "official_name", "old_name")
    out: set[str] = set()
    for key in keys:
        value = tags.get(key)
        if isinstance(value, str) and value.strip():
            out.add(value.strip())
        elif isinstance(value, list):
            out.update(str(v).strip() for v in value if str(v).strip())
    return sorted(out)

def way_record(way: dict, nodes: dict[int, dict]) -> dict:
    node_ids = [int(x) for x in way.get("nodes", [])]
    coords = []
    missing = []
    for node_id in node_ids:
        node = nodes.get(node_id)
        if not node or "lon" not in node or "lat" not in node:
            missing.append(node_id)
        else:
            coords.append([node["lon"], node["lat"]])
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "way",
        "osm_id": int(way["id"]),
        "node_ids": node_ids,
        "coordinates": coords,
        "tags": dict(sorted((way.get("tags") or {}).items())),
        "named_aliases": aliases(way.get("tags") or {}),
        "missing_node_ids": sorted(set(missing)),
    }

def relation_record(rel: dict, way_ids: set[int]) -> dict:
    members = []
    missing = []
    for member in rel.get("members", []):
        if member.get("type") != "way":
            continue
        ref = int(member["ref"])
        members.append({"way_id": ref, "role": member.get("role", "")})
        if ref not in way_ids:
            missing.append(ref)
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "relation",
        "osm_id": int(rel["id"]),
        "members": members,
        "all_way_ids": sorted({m["way_id"] for m in members}),
        "tags": dict(sorted((rel.get("tags") or {}).items())),
        "named_aliases": aliases(rel.get("tags") or {}),
        "missing_way_ids": sorted(set(missing)),
        "source_incomplete": bool(missing),
    }

def build(input_path: Path, out_path: Path, manifest_path: Path) -> dict:
    nodes, ways, relations = load_snapshot(input_path)
    way_records = [way_record(ways[i], nodes) for i in sorted(ways)]
    relation_records = [relation_record(r, set(ways)) for r in sorted(relations, key=lambda x: int(x["id"]))]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix == ".gz":
        raw = out_path.open("wb")
        compressed = gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0)
        fh = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
    else:
        raw = out_path.open("w", encoding="utf-8", newline="\n")
        fh = raw
    with fh:
        for record in way_records + relation_records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "index_schema": "osm_river_segments_v1",
        "snapshot": {"path": str(input_path), "sha256": sha256(input_path)},
        "index": {"path": str(out_path), "sha256": sha256(out_path)},
        "counts": {"nodes": len(nodes), "ways": len(ways), "relations": len(relations)},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--no-network", action="store_true", help="required compatibility flag; network is never used")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"snapshot does not exist: {args.input}")
    manifest = build(args.input, args.out, args.manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
