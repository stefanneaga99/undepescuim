import hashlib
import json
from pathlib import Path


ARTIFACT = Path(__file__).parents[1] / "public/data/preview_class2_physical.json"


def test_class2_preview_aggregate_schema_and_scope():
    payload = json.loads(ARTIFACT.read_text())
    assert payload["schemaVersion"] == 1
    assert payload["previewOnly"] is True
    assert payload["canonicalMutation"] is False
    assert payload["excludedChunks"] == ["CLASS2-01"]
    assert payload["recordCount"] == 148
    assert payload["candidateCount"] == 168
    assert len({record["slug"] for record in payload["records"]}) == 148
    for record in payload["records"]:
        assert record["legalStatus"] == "legal sector unverified"
        assert record["physicalCandidates"]
        for candidate in record["physicalCandidates"]:
            assert candidate["geometry"]["type"] in {"LineString", "MultiLineString", "Polygon", "MultiPolygon"}
            assert candidate["geometry"]["coordinates"]
            assert candidate["sourceBranch"].startswith("local/class2-")
            assert candidate["sourceCommit"]


def test_class2_preview_hash_is_stable_for_checked_in_artifact():
    digest = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    assert digest == "8e5a548340d59187b5c02233889541375661f846cf9da2cb53a026bff37a4576"
