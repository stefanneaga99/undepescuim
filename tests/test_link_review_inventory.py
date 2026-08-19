import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_inventory(tmp_path):
    report = tmp_path / "report.json"
    repairs = tmp_path / "repairs.jsonl"
    output = tmp_path / "inventory.jsonl"
    summary = tmp_path / "summary.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/link_validation.py",
            "--mode",
            "fixtures",
            "--fail-on",
            "none",
            "--report",
            str(report),
            "--repairs",
            str(repairs),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_link_review_inventory.py",
            "--report",
            str(report),
            "--repairs",
            str(repairs),
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
    source_report = json.loads(report.read_text())
    source_repairs = {
        item["repairKey"]: item
        for item in (json.loads(line) for line in repairs.read_text().splitlines())
    }
    return rows, source_report, source_repairs, json.loads(summary.read_text()), json.loads(result.stdout)


def test_review_inventory_accounts_for_report_and_repairs(tmp_path):
    rows, report, repairs, info, stdout = build_inventory(tmp_path)
    assert len(rows) == report["summary"]["total"] == 9
    assert info["repairProposalTotal"] == len(repairs) == 7
    assert sum(row["repairProposal"] for row in rows) == 7
    assert info["candidateUrlCount"] == 0
    assert all(row["candidateUrl"] is None for row in rows)
    assert all(
        row["firstPartyEvidence"]["status"] == "missing"
        for row in rows
        if row["reviewStatus"] == "needs_first_party_review"
    )
    assert stdout["failedTotal"] == 7


def test_redirects_are_observations_not_accepted_replacements(tmp_path):
    rows, _report, _repairs, _info, _stdout = build_inventory(tmp_path)
    redirects = [row for row in rows if row["observedStatus"] == "redirected"]
    assert len(redirects) == 1
    assert all(row["errorCategory"] == "redirect" for row in redirects)
    assert all(row["candidateUrl"] is None for row in redirects)
    assert all(row["reviewStatus"] == "needs_first_party_review" for row in redirects)
    assert all(row["actionability"] == "non_actionable" for row in redirects)


def test_inventory_retains_validator_and_repair_audit_trails(tmp_path):
    rows, report, repairs, _info, _stdout = build_inventory(tmp_path)
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
