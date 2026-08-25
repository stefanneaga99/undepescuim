#!/usr/bin/env python3
"""Tests for the deterministic local geometry aggregate."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local-work"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    canonical = (ROOT / "public/data/waters.json", ROOT / "public/data/waters_county_clips.json")
    canonical_before = {p.name: sha(p) for p in canonical}
    subprocess.run(["python3", str(OUT / "geometry-final-aggregate.py")], check=True, cwd=ROOT)
    assert canonical_before == {p.name: sha(p) for p in canonical}
    first = {p.name: sha(p) for p in (OUT / "geometry-final-aggregate.json", OUT / "geometry-final-aggregate.md")}
    subprocess.run(["python3", str(OUT / "geometry-final-aggregate.py")], check=True, cwd=ROOT)
    assert canonical_before == {p.name: sha(p) for p in canonical}
    assert first == {p.name: sha(p) for p in (OUT / "geometry-final-aggregate.json", OUT / "geometry-final-aggregate.md")}
    doc = json.loads((OUT / "geometry-final-aggregate.json").read_text(encoding="utf-8"))
    assert doc["scope"]["batches"] == 190
    assert doc["scope"]["class_1_target_coverage"] == 701
    assert doc["scope"]["unresolved_class_2_to_6"] == 312
    assert doc["validation"]["unique_target_coverage"] is True
    assert doc["validation"]["canonical_data_mutation"] is False
    assert len(doc["batches"]) == 190
    assert len({b["batch_id"] for b in doc["batches"]}) == 190
    assert doc["external_actions"]["github_push"] is False
    assert doc["external_actions"]["production_promotion"] is False

if __name__ == "__main__":
    run()
    print("geometry final aggregate tests passed")
