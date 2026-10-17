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
    # 168 before river geometry v2; switched groups preview one rivernet course each
    assert payload["candidateCount"] == 161
    assert payload["candidateCount"] == sum(len(r["physicalCandidates"]) for r in payload["records"])
    assert len({record["slug"] for record in payload["records"]}) == 148
    for record in payload["records"]:
        assert record["legalStatus"] == "legal sector unverified"
        assert record["physicalCandidates"]
        for candidate in record["physicalCandidates"]:
            assert candidate["geometry"]["type"] in {"LineString", "MultiLineString", "Polygon", "MultiPolygon"}
            assert candidate["geometry"]["coordinates"]
            if candidate.get("kind") == "rivernet-course":
                # river geometry v2 (T4.2/T4.4): a switched river group previews its rivernet course
                assert candidate["sourceBranch"] == "rivernet" and candidate["source"].startswith("rivernet:")
            else:
                assert candidate["sourceBranch"].startswith("local/class2-")
            assert candidate["sourceCommit"]


def test_class2_preview_hash_is_stable_for_checked_in_artifact():
    digest = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    # re-pinned at the river geometry v2 cutover (T4.4): switched groups preview their rivernet course
    assert digest == "95e4f72d3f8bf2e22d6298f1807d7fda8c24ca3e55e4417c3f3f9da6f1bbea64"


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
