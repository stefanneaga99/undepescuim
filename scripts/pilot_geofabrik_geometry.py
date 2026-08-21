#!/usr/bin/env python3
"""Pilot-only Geofabrik geometry extractor and conservative matcher.

This script never writes canonical public/data files.  It reads a pinned PBF,
extracts named OSM waterway ways in the Covasna pilot bbox, and writes only
pilot/geofabrik/artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilot" / "geofabrik"
ARTIFACTS = PILOT / "artifacts"
PBF = PILOT / "data" / "romania-latest.osm.pbf"
COUNTY = "Covasna"
# County bbox with a small margin; source matching remains county/name gated.
BBOX = (25.43, 45.75, 26.20, 46.35)
BATCH = [
    {"slug": "anpa-anpa-0252", "class": "bbox-fallback", "known": False},
    {"slug": "anpa-anpa-0261", "class": "geometry-less-child", "known": False},
    {"slug": "anpa-anpa-0264", "class": "same-name-collision", "known": True},
    {"slug": "basca-mare-covasna", "class": "real-geometry-gap", "known": True},
    {"slug": "anpa-anpa-0253", "class": "unresolved-negative-control", "known": False},
]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(raul|raului|parau|paraul|river|riverul|pirau|piraiul)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_waters() -> list[dict]:
    with (ROOT / "public/data/waters.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def inventory() -> dict:
    waters = load_waters()
    selected = []
    for item in BATCH:
        water = next(w for w in waters if w["slug"] == item["slug"])
        selected.append({
            **item,
            "slug": water["slug"], "name": water["name"], "judet": water.get("judet"),
            "riverGroup": water.get("riverGroup"),
            "before": {"geometry": water.get("geometry"), "bbox": water.get("bbox")},
        })
    return {"county": COUNTY, "batch": selected, "batchCount": len(selected),
            "sourceCanonicalFilesRead": ["public/data/waters.json"]}


def extract() -> dict:
    try:
        import osmium  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyosmium is required: python -m pip install osmium") from exc
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "covasna_named_waterways.jsonl"
    started = time.monotonic()
    records: list[dict] = []

    class Handler(osmium.SimpleHandler):
        def way(self, obj):  # noqa: N802
            tags = obj.tags
            if tags.get("waterway") not in {"river", "stream", "canal", "drain", "wadi"}:
                return
            name = tags.get("name") or tags.get("name:ro")
            if not name or not obj.nodes:
                return
            coords = [[round(float(n.lon), 7), round(float(n.lat), 7)] for n in obj.nodes]
            if not coords:
                return
            minx = min(p[0] for p in coords); maxx = max(p[0] for p in coords)
            miny = min(p[1] for p in coords); maxy = max(p[1] for p in coords)
            if maxx < BBOX[0] or minx > BBOX[2] or maxy < BBOX[1] or miny > BBOX[3]:
                return
            records.append({"osmType": "way", "osmId": int(obj.id), "name": name,
                            "nameNorm": norm(name), "waterway": tags.get("waterway"),
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "tags": {k: tags[k] for k in ("waterway", "wikidata", "ref") if k in tags}})

    Handler().apply_file(str(PBF), locations=True)
    records.sort(key=lambda r: (r["nameNorm"], r["osmId"]))
    with out.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"records": len(records), "path": str(out), "runtimeSeconds": round(time.monotonic() - started, 3)}


def match() -> dict:
    inventory_data = inventory()
    source = ARTIFACTS / "covasna_named_waterways.jsonl"
    candidates = [json.loads(line) for line in source.open(encoding="utf-8")]
    by_name: dict[str, list[dict]] = {}
    for c in candidates:
        by_name.setdefault(c["nameNorm"], []).append(c)
    ledger = []
    cases = inventory_data["batch"] + [{"slug": "romsilva-covasna-aita", "class": "known-positive", "known": True}]
    for row in cases:
        water = next(w for w in load_waters() if w["slug"] == row["slug"])
        water_norm = norm(water["name"])
        exact = by_name.get(water_norm, [])
        # Conservative: a candidate is accepted only with an exact normalized
        # name and a unique source way. Ambiguity remains REVIEW, never guessed.
        classification = "ACCEPTED_DETERMINISTIC" if len(exact) == 1 else (
            "REVIEW_AMBIGUOUS" if exact else "UNRESOLVED_NO_EXACT_NAME")
        source_ids = [{"type": c["osmType"], "id": c["osmId"]} for c in exact]
        geometry = exact[0]["geometry"] if classification == "ACCEPTED_DETERMINISTIC" else None
        geometry_hash = hashlib.sha256(json.dumps(geometry, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest() if geometry else None
        ledger.append({
            "slug": row["slug"], "sourceIds": source_ids, "geometryHash": geometry_hash,
            "geometryType": geometry["type"] if geometry else None,
            "matchMethod": "normalized-exact-name", "confidence": 1.0 if geometry else 0.0,
            "endpointEvidence": {"nodeCount": len(geometry["coordinates"]) if geometry else 0},
            "distanceKm": None, "coverage": None, "classification": classification,
            "checkedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "batchClass": row["class"], "knownPositive": row.get("known", False),
        })
    accepted = sum(r["classification"] == "ACCEPTED_DETERMINISTIC" for r in ledger)
    validation = [r for r in ledger if r["slug"] == "romsilva-covasna-aita"]
    known_positives = sum(1 for r in validation if r["classification"] == "ACCEPTED_DETERMINISTIC")
    path = ARTIFACTS / "pilot_ledger.json"
    accepted_features = []
    for record, case in zip(ledger, cases):
        if record["classification"] != "ACCEPTED_DETERMINISTIC":
            continue
        candidate = by_name[norm(next(w for w in load_waters() if w["slug"] == case["slug"])["name"])][0]
        accepted_features.append({"type": "Feature", "geometry": candidate["geometry"],
                                 "properties": {"slug": record["slug"], "sourceIds": record["sourceIds"],
                                                 "geometryHash": record["geometryHash"]}})
    (ARTIFACTS / "accepted_geometry.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": accepted_features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    path = ARTIFACTS / "pilot_ledger.json"
    path.write_text(json.dumps({"source": source_meta(), "inventory": inventory_data,
                                "records": ledger,
                                "metrics": {"batchRecords": len(inventory_data["batch"]),
                                    "batchAccepted": accepted - known_positives,
                                    "knownPositiveControls": len(validation),
                                    "knownPositiveTruePositives": known_positives,
                                    "precision": 1.0 if known_positives else None,
                                    "recall": 1.0 if known_positives == len(validation) else 0.0}},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "records": len(ledger), "accepted": accepted,
            "batchRecords": len(inventory_data["batch"]), "knownPositiveControls": len(validation)}


def source_meta() -> dict:
    stat = PBF.stat()
    return {"url": "https://download.geofabrik.de/europe/romania-latest.osm.pbf",
            "retrievedAt": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat().replace("+00:00", "Z"),
            "sha256": sha256(PBF), "sizeBytes": stat.st_size,
            "license": "OpenStreetMap data, ODbL 1.0; Geofabrik download terms apply",
            "pbf": PBF.name}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inventory", "source", "extract", "match"])
    args = parser.parse_args()
    if args.command == "inventory": result = inventory()
    elif args.command == "source": result = source_meta()
    elif args.command == "extract": result = extract()
    else: result = match()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
