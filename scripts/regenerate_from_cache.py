#!/usr/bin/env python3
"""Regenerate geocoded_public.geojson from the geocode cache DB.

The batch geocoder (geocode_batch.py) keeps crashing before writing its
output (SIGTERM around 100/397 in this environment), but the SQLite cache
ends up complete. This script reconstructs the output file from the cache,
matching the batch writer's feature shape.

Usage: python3 scripts/regenerate_from_cache.py
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cache" / "geocode.db"
OUT = ROOT / "data" / "geocoded_public.geojson"

# Waters to geocode (non-premapped) — same source list the batch uses
WATERS = ROOT / "data" / "sources" / "waters.jsonl"


def load_waters() -> list[dict]:
    if WATERS.exists():
        return [json.loads(l) for l in WATERS.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Fallback: derive from the snapshot
    snap = json.loads((ROOT / "data" / "raw" / "arebaltapeste_probe" / "snapshot_waters.json").read_text(encoding="utf-8"))
    return snap if isinstance(snap, list) else snap.get("waters", [])


def main() -> None:
    waters = load_waters()
    db = sqlite3.connect(DB)

    # Slugs already covered by Tier 1 premaps
    premapped = set()
    for p in (ROOT / "data" / "premapped").glob("*.geojson"):
        if p.name == "README.md":
            continue
        fc = json.loads(p.read_text(encoding="utf-8"))
        for f in fc.get("features", []):
            slug = (f.get("properties") or {}).get("arebaltapeste_slug")
            if slug:
                premapped.add(slug)

    features = []
    counts = {"tier2_hit": 0, "tier2_miss": 0, "t3_overpass": 0, "t3_ne": 0, "t3_bbox": 0, "failed": 0}

    for w in waters:
        slug = w.get("slug")
        if not slug or slug in premapped:
            continue

        # Prefer the row that actually has geometry (negative-cache rows from
        # later re-runs would otherwise shadow the good hit)
        row = db.execute(
            "SELECT result_json, osm_id, tier, source, confidence, geojson FROM geocode_cache "
            "WHERE arebaltapeste_slug=? AND (geojson IS NOT NULL OR bbox IS NOT NULL) "
            "ORDER BY (geojson IS NOT NULL) DESC, last_accessed DESC LIMIT 1",
            (slug,),
        ).fetchone()

        if row is None:
            counts["failed"] += 1
            continue

        result_json, osm_id, tier, source, confidence, geojson = row

        geometry = None
        if geojson:
            geometry = json.loads(geojson)
        elif result_json:
            try:
                rj = json.loads(result_json)
                if isinstance(rj, dict) and rj.get("geojson"):
                    geometry = rj["geojson"]
            except (TypeError, json.JSONDecodeError):
                pass

        if geometry is None:
            counts["failed"] += 1
            continue

        if tier == "tier2":
            counts["tier2_hit"] += 1
        elif tier == "tier3_overpass":
            counts["t3_overpass"] += 1
        elif tier == "tier3_ne":
            counts["t3_ne"] += 1
        else:
            counts["t3_bbox"] += 1

        features.append({
            "type": "Feature",
            "id": slug,
            "properties": {
                "arebaltapeste_slug": slug,
                "name": w.get("name"),
                "name_ro": w.get("name"),
                "type": w.get("type", "ape"),
                "source": source,
                "source_detail": f"geocode cache (tier={tier})",
                "osm_id": osm_id,
                "geocode_tier": tier,
                "confidence": confidence,
                "judet": w.get("judet"),
            },
            "geometry": geometry,
        })

    fc = {
        "type": "FeatureCollection",
        "metadata": {
            "pipeline": "tier2_tier3_batch",
            "pipeline_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "processed": len(features),
            "counts": counts,
        },
        "features": features,
    }
    OUT.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"[regen] wrote {OUT} ({len(features)} features)")
    print(f"[regen] counts={counts}")


if __name__ == "__main__":
    main()
