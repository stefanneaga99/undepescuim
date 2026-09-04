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
    assert digest == "d12da466430d51237dd9266e234188949b18e62d2720005956b72bfd31fe6468"


def test_buzau_preview_keeps_physical_course_separate_from_unverified_contracts():
    payload = json.loads(ARTIFACT.read_text())
    records = [record for record in payload["records"] if record.get("riverGroup") == "buzau"]
    assert len(records) >= 6
    candidates = [record["physicalCandidates"][0] for record in records]
    assert len({candidate["geometryHash"] for candidate in candidates}) == 1
    # The source artifact has no legally supported endpoints for these rows;
    # the UI must not manufacture a clipped contractual segment.
    for record in records:
        assert "sectorStart" not in record
        assert "sectorEnd" not in record
        assert record["legalStatus"] == "legal sector unverified"
