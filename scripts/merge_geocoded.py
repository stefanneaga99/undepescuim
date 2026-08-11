#!/usr/bin/env python3
"""Merge Tier 1 premaps + Tier 2/3 batch results + private lakes into ONE GeoJSON.

Reads:
  - data/premapped/*.geojson  (Tier 1, 28 features)
  - data/geocoded_public.geojson  (Tier 2/3 batch output, non-premapped waters)
  - data/geocoded_private.geojson (private lakes, 201 features)
Writes (proposal s7.1):
  - data/waters_geocoded.geojson
  - public/data/waters_geocoded.geojson

Usage: python3 scripts/merge_geocoded.py
"""
import json
import os
from collections import Counter
from datetime import datetime, timezone

import geocode_common as gc

PIPELINE_VERSION = "1.0"


def premap_metadata(p, water):
    """Base properties for a Tier 1 feature, joined with arebaltapeste metadata."""
    props = dict(p["feature"]["properties"])
    props["arebaltapeste_slug"] = water["slug"] if water else None
    props["judet"] = water.get("judet") if water else None
    props["asociatie"] = (water.get("asociatie") or {}).get("name") if water else None
    props["dimensiune"] = water.get("dimensiune") if water else None
    props.setdefault("importance", None)  # s7.1: field present even for manual premaps
    return props


def main():
    premaps = gc.load_premaps()
    waters = gc.load_waters()
    with open(gc.OUT_PUBLIC, encoding="utf-8") as fh:
        batch_fc = json.load(fh)
    with open(gc.OUT_PRIVATE, encoding="utf-8") as fh:
        private_fc = json.load(fh)

    # --- Tier 1: matched waters carry premap geometry; unmatched premaps are extras
    matched_waters, extras = [], []
    matched_premaps = set()
    for w in waters:
        m = gc.premap_match(w, premaps)
        if m:
            matched_waters.append((w, m))
            matched_premaps.add(m["file"])
    for p in premaps:
        if p["file"] not in matched_premaps:
            extras.append(p)

    features = []
    for w, p in matched_waters:
        feat = json.loads(json.dumps(p["feature"]))  # deep copy
        feat["id"] = w["slug"]
        feat["properties"] = premap_metadata(p, w)
        features.append(feat)
    for p in extras:
        feat = json.loads(json.dumps(p["feature"]))
        feat["properties"] = premap_metadata(p, None)
        features.append(feat)

    # --- Tier 2/3 batch features
    for feat in batch_fc["features"]:
        features.append(feat)

    # --- Private lakes
    for feat in private_fc["features"]:
        features.append(feat)

    # --- Coverage breakdown by tier (public waters only: premap + batch)
    public_features = [f for f in features if not f["id"].startswith("private-")]
    private_features = [f for f in features if f["id"].startswith("private-")]
    tiers = Counter(f.get("properties", {}).get("geocode_tier") for f in public_features)
    sources = Counter(f.get("properties", {}).get("source") for f in public_features)
    with_geom = sum(1 for f in features if f.get("geometry"))
    batch_counts = batch_fc.get("metadata", {}).get("counts", {})
    tier2_miss = batch_counts.get("tier2_miss", 0)
    priv_tiers = Counter(f.get("properties", {}).get("geocode_tier") for f in private_features)

    coverage = {
        "tier1_manual": tiers.get("tier1", 0),
        "tier2_nominatim_hit": tiers.get("tier2", 0),
        "tier2_nominatim_miss": tier2_miss,
        "tier3_overpass_hit": tiers.get("tier3_overpass", 0),
        "tier3_ne_hit": tiers.get("tier3_ne", 0),
        "tier3_bbox_only": tiers.get("tier3_bbox", 0),
        "tier4_failed": tiers.get("failed", 0),
        "private_overpass_hit": priv_tiers.get("tier3_overpass", 0),
        "private_bbox_only": priv_tiers.get("tier3_bbox", 0),
        "sources": dict(sources),
    }
    total_public = len(public_features)

    fc = {
        "type": "FeatureCollection",
        "metadata": {
            "pipeline_version": PIPELINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_input_waters": len(waters),
            "total_output_features": len(features),
            "public_features": total_public,
            "private_lakes_separate": len(private_fc["features"]),
            "features_with_geometry": with_geom,
            "coverage": coverage,
            "notes": [
                "tier1 features = premapped waters (matched) + premap extras without a waters.json record (Danube, Prut, major lakes)",
                "tier2_miss counts batch waters that fell through to tier3 (they also appear in tier3_* counts)",
            ],
        },
        "features": features,
    }

    for out in (gc.OUT_MERGED, gc.OUT_PUBLIC_DATA):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(fc, fh, ensure_ascii=False)
        print(f"[merge] wrote {out} ({len(features)} features)")
    print(f"[merge] coverage={json.dumps(coverage, ensure_ascii=False)}")
    print(f"[merge] features_with_geometry={with_geom}/{len(features)}")


if __name__ == "__main__":
    main()
