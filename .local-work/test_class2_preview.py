import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".local-work"))
from build_class2_preview import build  # noqa: E402


def test_class2_preview_is_deterministic_and_complete(tmp_path):
    source = ROOT.parent.parent / ".local-work" / "unresolved-geometry-inventory.json"
    first = build(source, "CLASS2-02")
    second = build(source, "CLASS2-02")
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(second, ensure_ascii=False, sort_keys=True)
    expected_slugs = json.loads((ROOT.parent.parent / ".local-work" / "class2-chunks.json").read_text(encoding="utf-8"))["chunks"][1]["slugs"]
    assert first["chunkId"] == "CLASS2-02"
    assert first["slugs"] == expected_slugs
    assert first["recordCount"] == 15
    assert len(first["records"]) == 15
    assert {row["slug"] for row in first["records"]} == set(expected_slugs)
    assert all(row["legalStatus"] == "legal sector unverified" for row in first["records"])
    assert all(row["canonicalMutation"] is False for row in first["records"])
    assert all(row["physicalCandidates"] for row in first["records"])


def test_preview_contains_provenance_and_does_not_claim_legal_fields():
    artifact = build(ROOT.parent.parent / ".local-work" / "unresolved-geometry-inventory.json", "CLASS2-02")
    for row in artifact["records"]:
        for candidate in row["physicalCandidates"]:
            assert "geometryHash" in candidate
            assert "physicalSourceUrl" in candidate
            assert "osmId" in candidate
            assert "geofabrikId" in candidate
            assert candidate["geometry"]["type"] in {"LineString", "MultiLineString", "Polygon", "MultiPolygon"}
        assert "sectorStart" not in row and "sectorEnd" not in row and "courseFrac" not in row


def test_generation_does_not_change_canonical_input():
    waters = ROOT / "public" / "data" / "waters.json"
    before = hashlib.sha256(waters.read_bytes()).hexdigest()
    build(ROOT.parent.parent / ".local-work" / "unresolved-geometry-inventory.json", "CLASS2-02")
    assert hashlib.sha256(waters.read_bytes()).hexdigest() == before
