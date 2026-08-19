import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_inventory_accounts_for_report_and_repairs(tmp_path):
    output = tmp_path / "inventory.jsonl"
    summary = tmp_path / "summary.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_link_review_inventory.py",
            "--output",
            str(output),
            "--summary",
            str(summary),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    report = json.loads((ROOT / "data/processed/link_validation_report.json").read_text())
    repairs = (ROOT / "data/processed/link_validation_repairs.jsonl").read_text().splitlines()
    info = json.loads(summary.read_text())
    assert len(rows) == report["summary"]["total"] == 730
    assert info["repairProposalTotal"] == len(repairs) == 292
    assert sum(row["repairProposal"] for row in rows) == 292
    assert info["candidateUrlCount"] == 0
    assert all(row["candidateUrl"] is None for row in rows)
    assert all(
        row["firstPartyEvidence"]["status"] == "missing"
        for row in rows
        if row["reviewStatus"] == "needs_first_party_review"
    )
    assert json.loads(result.stdout)["failedTotal"] == 292


def test_redirects_are_observations_not_accepted_replacements():
    rows = [
        json.loads(line)
        for line in (ROOT / "data/processed/link_review_inventory.jsonl").read_text().splitlines()
    ]
    redirects = [row for row in rows if row["observedStatus"] == "redirected"]
    assert len(redirects) == 47
    assert all(row["errorCategory"] == "redirect" for row in redirects)
    assert all(row["candidateUrl"] is None for row in redirects)
    assert all(row["reviewStatus"] == "needs_first_party_review" for row in redirects)
    assert all(row["actionability"] == "non_actionable" for row in redirects)


def test_inventory_retains_validator_and_repair_audit_trails():
    rows = [
        json.loads(line)
        for line in (ROOT / "data/processed/link_review_inventory.jsonl").read_text().splitlines()
    ]
    report = json.loads((ROOT / "data/processed/link_validation_report.json").read_text())
    repairs = {
        item["repairKey"]: item
        for item in (
            json.loads(line)
            for line in (ROOT / "data/processed/link_validation_repairs.jsonl").read_text().splitlines()
        )
    }
    for row, source in zip(rows, report["records"]):
        assert row["validationResults"] == [source]
        if row["repairProposal"]:
            repair = repairs[row["repairHistory"][0]["repairKey"]]
            assert row["repairHistory"] == [repair]
        else:
            assert row["repairHistory"] == []
        if row["actionability"] == "non_actionable":
            assert row["candidateUrl"] is None
            assert row["firstPartyEvidence"]["reviewed"] is False
