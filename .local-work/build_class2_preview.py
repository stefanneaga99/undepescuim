#!/usr/bin/env python3
"""Build the isolated Class-2 physical geometry Preview artifact.

This is deliberately read-only with respect to canonical data: it copies physical
candidate evidence into a separate namespace and never edits waters.json.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Shared source evidence lives outside this isolated worktree. Generated
# artifacts remain local to the worktree and never mutate canonical data.
LOCAL_WORK_ROOT = ROOT.parent.parent / ".local-work"
INVENTORY = LOCAL_WORK_ROOT / "unresolved-geometry-inventory.json"
OUTPUT = ROOT / "public" / "data" / "preview_class2_physical.json"
CHUNKS = LOCAL_WORK_ROOT / "class2-chunks.json"


def stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def chunk_slugs(chunk_id: str, chunks_path: Path = CHUNKS) -> list[str]:
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    for chunk in chunks["chunks"]:
        if chunk["id"] == chunk_id:
            return chunk["slugs"]
    raise ValueError(f"unknown Class-2 chunk: {chunk_id}")


def build(input_path: Path = INVENTORY, chunk_id: str | None = None) -> dict:
    inventory = json.loads(input_path.read_text(encoding="utf-8"))
    selected_slugs = chunk_slugs(chunk_id) if chunk_id else None
    selected = set(selected_slugs or ())
    records = []
    for row in inventory["records"]:
        if row.get("class") != 2:
            continue
        if selected_slugs is not None and row["slug"] not in selected:
            continue
        identity = row["identity"]
        candidates = []
        for index, candidate in enumerate(row.get("physicalCourseCandidates", [])):
            geometry = candidate.get("geometry") or {}
            if not geometry.get("type") or geometry.get("coordinates") is None:
                continue
            candidates.append({
                "id": candidate.get("id") or f"{row['slug']}-physical-{index + 1}",
                "kind": candidate.get("kind"),
                "rating": candidate.get("rating"),
                "source": candidate.get("source"),
                "sourceId": candidate.get("sourceId"),
                "physicalSourceUrl": candidate.get("physicalSourceUrl"),
                "osmId": candidate.get("osmId"),
                "geofabrikId": candidate.get("geofabrikId"),
                "geometryHash": geometry.get("sha256") or stable_hash(geometry),
                "geometry": geometry,
                "measuredLengthKm": candidate.get("measuredLengthKm"),
                "componentCount": candidate.get("componentCount"),
                "componentIds": candidate.get("componentIds", []),
                "confidence": candidate.get("rating") or "unavailable",
                "countyMatch": candidate.get("countyMatch", {"status": "not_verified", "rationale": "No legal county proof."}),
                "topology": candidate.get("topology"),
            })
        records.append({
            "slug": row["slug"],
            "name": identity["name"],
            "county": identity["county"],
            "locality": identity.get("locality"),
            "association": identity.get("association", {}).get("name"),
            "associationSlug": identity.get("association", {}).get("slug"),
            "riverGroup": identity.get("riverGroup"),
            "subtype": identity.get("subtype"),
            "physicalCandidates": candidates,
            "legalStatus": "legal sector unverified",
            "disclosure": "Traseu fizic experimental; limitele sectorului contractual nu sunt verificate.",
            "canonicalMutation": False,
        })
    records.sort(key=lambda row: row["slug"])
    artifact = {
        "schemaVersion": 1,
        "artifact": "class2-physical-preview",
        "class": 2,
        "chunkId": chunk_id,
        "slugs": selected_slugs,
        "recordCount": len(records),
        "candidateCount": sum(len(r["physicalCandidates"]) for r in records),
        "sourceInventorySha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "records": records,
    }
    if selected_slugs is not None:
        artifact["chunkSlugsSha256"] = stable_hash(selected_slugs)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-id")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    artifact = build(chunk_id=args.chunk_id)
    expected = len(chunk_slugs(args.chunk_id)) if args.chunk_id else 163
    if artifact["recordCount"] != expected:
        raise SystemExit(f"expected {expected} Class-2 records, got {artifact['recordCount']}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({artifact['recordCount']} records, {artifact['candidateCount']} physical candidates)")


if __name__ == "__main__":
    main()
