"""Permanent offline wiring checks for the river-segment data contract."""
import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/processed/pipeline_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_pins_segment_audit_inputs_and_outputs():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    inputs = manifest["inputs"]
    outputs = manifest["outputs"]
    for rel in (
        "data/cache/osm_river_segments_v1.jsonl.gz",
        "data/processed/river_name_aliases.json",
        "data/processed/river_segment_exceptions.json",
        "data/processed/river_segment_audit_baseline.json",
    ):
        assert rel in inputs, f"manifest must pin audit input {rel}"
        assert inputs[rel] == sha256(ROOT / rel)
    for rel in ("data/processed/river_segment_audit.json", "data/processed/river_segment_audit.md"):
        assert rel in outputs, f"manifest must pin audit output {rel}"
        assert outputs[rel] == sha256(ROOT / rel)


def test_report_is_tied_to_pinned_index_and_gate_is_not_auto_remediated():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = json.loads((ROOT / "data/processed/river_segment_audit.json").read_text(encoding="utf-8"))
    index = ROOT / "data/cache/osm_river_segments_v1.jsonl.gz"
    assert report["snapshot_sha256"] == manifest["inputs"][str(index.relative_to(ROOT))]
    assert report["gate"]["status"] == "BLOCKED"
    assert report["gate"]["blocking_findings"]
    # The offline gate only writes its report; it must not mutate contract data.
    assert manifest["outputs"]["public/data/waters.json"] == sha256(ROOT / "public/data/waters.json")


def test_review_registries_are_expirable_and_auditable():
    for rel, key in (
        ("data/processed/river_name_aliases.json", "aliases"),
        ("data/processed/river_segment_exceptions.json", "exceptions"),
    ):
        entries = json.loads((ROOT / rel).read_text(encoding="utf-8"))[key]
        for entry in entries:
            assert entry.get("justification")
            assert entry.get("source")
            expiry = date.fromisoformat(entry["expires_on"])
            assert expiry >= date(2026, 1, 1)
