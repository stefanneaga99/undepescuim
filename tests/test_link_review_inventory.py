import json
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def review_cases():
    return json.loads((ROOT / "tests/fixtures/link_validation/review_cases.json").read_text())


def as_report(records):
    return {"records": records, "summary": {"total": len(records)}}


def repair_for(record, **extra):
    raw = "|".join(
        str(record.get(key) or "")
        for key in ("sourceKind", "associationSlug", "field", "sourcePath", "originalUrl")
    )
    repair = {
        "schemaVersion": 1,
        "repairKey": hashlib.sha256(raw.encode()).hexdigest(),
        "associationSlug": record["associationSlug"],
        "field": record["field"],
        "sourcePath": record["sourcePath"],
        "originalUrl": record["originalUrl"],
        "observedStatus": record["status"],
        "evidence": {
            "checkedAt": record["checkedAt"],
            "failureReason": record["failureReason"],
            "finalUrl": record["finalUrl"],
            "redirect": record["redirect"],
        },
        "action": "review_and_manually_repair",
        "state": "open",
    }
    repair.update(extra)
    return repair


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


def test_review_fixture_covers_all_error_categories_and_output_schema():
    from scripts.build_link_review_inventory import build

    records = review_cases()
    rows, summary = build(as_report(records), [repair_for(records[0])])

    assert len(rows) == summary["reportTotal"] == 5
    assert {row["errorCategory"] for row in rows} == {
        "ok",
        "client_error",
        "redirect",
        "transient_error",
        "blocked/policy",
    }
    assert summary["schemaVersion"] == 2
    assert summary["repairProposalTotal"] == 1
    assert all(
        {"schemaVersion", "recordKey", "originalUrl", "attemptHistory", "repairHistory"}
        <= row.keys()
        for row in rows
    )


def test_original_urls_and_attempt_history_are_immutable_and_no_destination_is_invented():
    from scripts.build_link_review_inventory import build

    records = review_cases()
    repairs = [repair_for(record) for record in records if record["status"] != "ok"]
    rows, _summary = build(as_report(records), repairs)

    for source, row in zip(records, rows):
        assert row["originalUrl"] == source["originalUrl"]
        assert row["validationResults"] == [source]
        assert row["attemptHistory"]["redirect"] == source["redirect"]
        assert row["candidateUrl"] is None
        assert row["actionability"] == ("not_applicable" if source["status"] == "ok" else "non_actionable")


def test_duplicate_urls_are_counted_without_collapsing_records():
    from scripts.build_link_review_inventory import build

    records = review_cases() + [dict(review_cases()[0], sourcePath="data/processed/locuri_associations.jsonl[4].permit_url")]
    rows, summary = build(as_report(records), [repair_for(record) for record in records if record["status"] != "ok"])

    duplicate_rows = [row for row in rows if row["originalUrl"] == records[0]["originalUrl"]]
    assert len(duplicate_rows) == 2
    assert all(row["duplicate"]["isDuplicate"] for row in duplicate_rows)
    assert summary["duplicateOriginalUrlGroups"] == 1
    assert summary["duplicateOriginalUrlRows"] == 2


def test_only_reviewed_first_party_candidate_is_actionable():
    from scripts.build_link_review_inventory import build

    records = review_cases()[:2]
    reviewed_candidate = "https://new.example/permit"
    repairs = [
        repair_for(
            records[0],
            candidateUrl=reviewed_candidate,
            firstPartyEvidence={"reviewed": True, "urls": [reviewed_candidate]},
        ),
        repair_for(
            records[1],
            candidateUrl="https://invented.example/",
            firstPartyEvidence={"reviewed": False, "urls": []},
        ),
    ]
    rows, _summary = build(as_report(records), repairs)

    assert rows[0]["candidateUrl"] == reviewed_candidate
    assert rows[0]["reviewStatus"] == "reviewed_repair_ready"
    assert rows[0]["actionability"] == "actionable"
    assert rows[1]["candidateUrl"] is None
    assert rows[1]["reviewStatus"] == "needs_first_party_review"
    assert rows[1]["actionability"] == "non_actionable"
