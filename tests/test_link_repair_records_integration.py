"""Integration coverage for the source-backed repair-record pipeline.

These tests deliberately execute the command-line validator and inventory
builder instead of replacing either component with a test double.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from scripts.build_link_review_inventory import build


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/fixtures/link_validation/repair_records_cases.json"


def run_validator(tmp_path: Path) -> tuple[dict, list[dict]]:
    report_path = tmp_path / "report.json"
    repairs_path = tmp_path / "repairs.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/link_validation.py",
            "--mode",
            "fixtures",
            "--report",
            str(report_path),
            "--repairs",
            str(repairs_path),
            "--fail-on",
            "none",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(report_path.read_text()), [
        json.loads(line) for line in repairs_path.read_text().splitlines() if line
    ]


def test_real_validator_and_inventory_preserve_inputs_and_emit_schema(tmp_path):
    tracked = [
        ROOT / "tests/fixtures/link_validation/targets.json",
        ROOT / "public/data/associations.json",
        ROOT / "public/data/waters.json",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}

    report, repairs = run_validator(tmp_path)
    report_before = deepcopy(report)
    repairs_before = deepcopy(repairs)
    report_path = tmp_path / "report.json"
    repairs_path = tmp_path / "repairs.jsonl"
    output_path = tmp_path / "inventory.jsonl"
    summary_path = tmp_path / "summary.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_link_review_inventory.py",
            "--report",
            str(report_path),
            "--repairs",
            str(repairs_path),
            "--output",
            str(output_path),
            "--summary",
            str(summary_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    rows = [json.loads(line) for line in output_path.read_text().splitlines() if line]
    summary = json.loads(summary_path.read_text())
    assert len(rows) == report["summary"]["total"] == summary["reportTotal"]
    assert summary["schemaVersion"] == 2
    assert all(
        {
            "schemaVersion",
            "recordKey",
            "originalUrl",
            "attemptHistory",
            "validationResults",
            "repairHistory",
            "candidateUrl",
            "actionability",
            "duplicate",
        }
        <= row.keys()
        for row in rows
    )
    assert all(row["candidateUrl"] is None for row in rows)
    assert all(row["actionability"] != "actionable" for row in rows)
    assert report == report_before
    assert repairs == repairs_before
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}


def test_common_fixture_review_gate_and_zero_applicable_output():
    bundle = json.loads(CASES.read_text())
    report = {"records": deepcopy(bundle["records"]), "summary": {"total": len(bundle["records"])}}
    repairs = deepcopy(bundle["repairs"])
    report_before = deepcopy(report)
    repairs_before = deepcopy(repairs)

    rows, summary = build(report, repairs)
    assert len(rows) == 6
    assert summary["repairProposalTotal"] == 5
    assert summary["candidateUrlCount"] == 1
    assert sum(row["actionability"] == "actionable" for row in rows) == 1

    reviewed = next(row for row in rows if row["observedStatus"] == "redirected")
    assert reviewed["candidateUrl"] == "https://ajvpsarges.ro/"
    assert reviewed["firstPartyEvidence"]["reviewed"] is True
    assert reviewed["candidateUrl"] in reviewed["firstPartyEvidence"]["urls"]

    rejected = next(row for row in rows if row["observedStatus"] == "client_error")
    assert rejected["candidateUrl"] is None
    assert rejected["actionability"] == "non_actionable"
    assert rejected["reviewStatus"] == "needs_first_party_review"
    assert report == report_before
    assert repairs == repairs_before

    zero_rows, zero_summary = build(
        {"records": [deepcopy(bundle["records"][0])], "summary": {"total": 1}},
        [],
    )
    assert len(zero_rows) == 1
    assert zero_summary["repairProposalTotal"] == 0
    assert zero_summary["candidateUrlCount"] == 0
    assert zero_rows[0]["actionability"] == "not_applicable"
    assert zero_rows[0]["repairHistory"] == []
    assert zero_rows[0]["originalUrl"] == bundle["records"][0]["originalUrl"]


def test_duplicate_and_failed_histories_survive_real_inventory_builder():
    bundle = json.loads(CASES.read_text())
    rows, summary = build(
        {"records": deepcopy(bundle["records"]), "summary": {"total": 6}},
        deepcopy(bundle["repairs"]),
    )
    duplicates = [
        row
        for row in rows
        if row["originalUrl"] == "https://permise.anpa.ro:12443/portal-public/permis"
    ]
    assert len(duplicates) == 2
    assert [row["duplicate"]["occurrence"] for row in duplicates] == [1, 2]
    assert summary["duplicateOriginalUrlGroups"] == 1
    assert all(row["attemptHistory"]["retry"]["exhausted"] for row in duplicates)
    assert all(row["validationResults"][0]["originalUrl"] == row["originalUrl"] for row in rows)
    assert all(row["repairHistory"] for row in rows if row["observedStatus"] != "ok")
