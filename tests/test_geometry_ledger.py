import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/build_geometry_ledger.py"
AUTHORITATIVE = ROOT / "data/processed/geometry_ledger.json"
PUBLIC = ROOT / "public/data/geometry-ledger.json"
MANIFEST = ROOT / "public/data/geometry-ledger-manifest.json"
REPORT = ROOT / "docs/geometry-ledger-report.md"
WATERS = ROOT / "public/data/waters.json"
LEGAL_SURFACES = [
    WATERS,
    ROOT / "public/data/associations.json",
    ROOT / "public/data/association_locations.json",
    ROOT / "public/data/waters_county_clips.json",
    ROOT / "data/processed/anpa_waters.jsonl",
    ROOT / "data/processed/anpa_contracts.jsonl",
    ROOT / "data/processed/anpa_romsilva_waters.jsonl",
    ROOT / "data/processed/arebaltapeste_waters.jsonl",
    ROOT / "data/processed/arebaltapeste_associations.jsonl",
    ROOT / "data/processed/mures_harghita_covasna_endpoint_audit.json",
    ROOT / "data/processed/river_segment_audit.json",
    ROOT / "data/processed/permit_enrichment.json",
    ROOT / "data/processed/permit_overrides.json",
]
_MODULE = None


def load_module():
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    spec = importlib.util.spec_from_file_location("build_geometry_ledger", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _MODULE = module
    return _MODULE


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nested_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def run_generator(output_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--output-root", str(output_root)],
        cwd=ROOT,
        check=True,
    )


def test_canonical_geometry_hash_and_segment_identity_reject_nonfinite_values():
    ledger = load_module()
    geometry = {"coordinates": [[25.0, 45.0], [25.5, 45.5]], "type": "LineString"}
    expected_hash = hashlib.sha256(
        json.dumps(
            geometry,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    assert ledger.geometry_summary(geometry)["geometryHash"] == expected_hash
    expected_segment = hashlib.sha256(
        f"water-a\0{expected_hash}\0commit:path#water-a\0null\0null".encode()
    ).hexdigest()
    assert ledger.segment_id("water-a", expected_hash, "commit:path#water-a", None, None) == expected_segment
    with pytest.raises(ValueError, match="finite"):
        ledger.geometry_summary({"type": "Point", "coordinates": [math.inf, 45.0]})


def test_checked_in_ledger_is_complete_deterministic_and_public_projection_is_redacted(tmp_path):
    before = {str(path.relative_to(ROOT)): sha256(path) for path in LEGAL_SURFACES}
    run_generator(tmp_path / "first")
    run_generator(tmp_path / "second")
    for relative in [
        "data/processed/geometry_ledger.json",
        "public/data/geometry-ledger.json",
        "public/data/geometry-ledger-manifest.json",
        "docs/geometry-ledger-report.md",
    ]:
        first = tmp_path / "first" / relative
        second = tmp_path / "second" / relative
        # Compare fixed-size byte digests so a mismatch does not make pytest
        # construct a multi-megabyte bytes diff.
        assert sha256(first) == sha256(second)
        assert sha256(first) == sha256(ROOT / relative)
    after = {str(path.relative_to(ROOT)): sha256(path) for path in LEGAL_SURFACES}
    assert after == before

    authoritative = json.loads(AUTHORITATIVE.read_text())
    public = json.loads(PUBLIC.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert authoritative["totals"]["canonicalWaters"] == 1013
    assert authoritative["totals"]["rivers"] == 761
    assert authoritative["totals"]["lakes"] == 252
    assert authoritative["totals"]["unresolvedInventory"] == 312
    assert authoritative["totals"]["physicalPreviewRuntimeRepresentatives"] == 69
    assert len(authoritative["records"]) == 1013
    assert len({record["sourceSlug"] for record in authoritative["records"]}) == 1013
    assert len(public["records"]) == 1013
    assert "coordinates" not in set(nested_keys(public))
    assert "geojson" not in set(nested_keys(public))
    assert manifest["canonicalNoMutation"]["status"] == "PASS"
    assert manifest["staleManifestReconciliation"]["status"] == "STALE_RECORDED"


def test_aliases_groups_states_and_historical_candidates_are_explicit():
    ledger = json.loads(AUTHORITATIVE.read_text())
    records = {record["sourceSlug"]: record for record in ledger["records"]}
    buzau = records["anpa-anpa-0207"]
    assert buzau["riverGroup"] == "buzau"
    assert buzau["aliases"] == sorted(
        [
            "anpa-anpa-0207",
            "anpa-anpa-0210",
            "anpa-anpa-0211",
            "anpa-anpa-0214",
            "anpa-anpa-0261",
            "romsilva-brasov-buzaul-superior",
        ]
    )
    assert buzau["classification"] == "preview-only"
    assert {variant["state"] for variant in buzau["geometryVariants"]} == {
        "physical-full-course-preview"
    }
    assert buzau["endpointEvidence"]["status"] == "not-verified"
    assert "course_frac" not in set(nested_keys(buzau["endpointEvidence"]))

    explicit = records["anpa-anpa-0261"]
    assert "explicit-physical-segment" in {
        variant["state"] for variant in explicit["geometryVariants"]
    }
    assert explicit["endpointEvidence"]["status"] == "source-backed-explicit"

    expected_classification = {
        "romsilva-bacau-barzauta": "unresolved",
        "romsilva-covasna-sugo": "repaired",
        "romsilva-maramures-crasna-frumusaua": "unresolved",
        "vb2p0152": "repaired",
    }
    for slug, classification in expected_classification.items():
        record = records[slug]
        assert record["classification"] == classification
        assert record["historicalAudit"]["candidate"] is True
        assert record["historicalAudit"]["reproduction"] == "NOT_REPRODUCED"
        assert record["browserObservations"]


def test_every_geometry_variant_has_required_evidence_and_valid_identity():
    ledger = json.loads(AUTHORITATIVE.read_text())
    valid_states = {
        "canonical-legal-sector",
        "physical-full-course-preview",
        "explicit-physical-segment",
        "unresolved",
    }
    valid_classifications = {"repaired", "preview-only", "unresolved"}
    for record in ledger["records"]:
        assert record["aliases"] == sorted(set(record["aliases"]))
        assert record["sourceSlug"] in record["aliases"]
        assert record["classification"] in valid_classifications
        assert record["rawSources"]
        assert record["countyConsistencyEvidence"]
        assert record["endpointEvidence"]["citations"] is not None
        for variant in record["geometryVariants"]:
            assert variant["state"] in valid_states
            if variant["state"] == "unresolved":
                assert variant["geometry"] is None
                assert variant["reason"]
                continue
            assert variant["segmentId"] == load_module().segment_id(
                record["sourceSlug"],
                variant["geometry"]["geometryHash"],
                variant["evidenceSourceId"],
                variant["start"],
                variant["end"],
            )
            assert variant["geometry"]["valid"] is True
            assert variant["geometry"]["coordinateCount"] > 0
            assert len(variant["geometry"]["bbox"]) == 4
