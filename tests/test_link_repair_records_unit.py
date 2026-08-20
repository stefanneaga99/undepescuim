import json
from copy import deepcopy
from pathlib import Path

from scripts.build_link_review_inventory import build


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/link_validation/repair_records_cases.json"


def cases():
    return json.loads(FIXTURE.read_text())


def report_from_fixture(bundle):
    return {"records": deepcopy(bundle["records"]), "summary": {"total": len(bundle["records"])}}


def repairs_from_fixture(bundle):
    return deepcopy(bundle["repairs"])


def test_fixture_has_each_supported_error_category_and_expected_counts():
    bundle = cases()
    rows, summary = build(report_from_fixture(bundle), repairs_from_fixture(bundle))

    assert len(rows) == bundle["expected"]["recordTotal"] == 6
    assert len(bundle["repairs"]) == bundle["expected"]["repairRecordTotal"] == 5
    assert {row["errorCategory"] for row in rows} == {
        "ok",
        "client_error",
        "redirect",
        "transient_error",
        "blocked/policy",
    }
    assert summary["byCategory"] == {
        "blocked/policy": 1,
        "client_error": 1,
        "ok": 1,
        "redirect": 1,
        "transient_error": 2,
    }
    assert summary["repairProposalTotal"] == 5


def test_redirect_transient_and_policy_rows_are_classified_separately():
    bundle = cases()
    rows, _summary = build(report_from_fixture(bundle), repairs_from_fixture(bundle))

    redirect = next(row for row in rows if row["observedStatus"] == "redirected")
    transient = [row for row in rows if row["observedStatus"] == "transient_error"]
    policy = next(row for row in rows if row["observedStatus"] == "blocked")

    assert redirect["errorCategory"] == "redirect"
    assert redirect["attemptHistory"]["redirect"]["chain"]
    assert redirect["candidateUrl"] == "https://ajvpsarges.ro/"
    assert redirect["actionability"] == "actionable"

    assert len(transient) == 2
    assert all(row["errorCategory"] == "transient_error" for row in transient)
    assert all(row["candidateUrl"] is None for row in transient)
    assert all(row["actionability"] == "non_actionable" for row in transient)
    assert all(row["attemptHistory"]["retry"]["exhausted"] is True for row in transient)

    assert policy["errorCategory"] == "blocked/policy"
    assert policy["candidateUrl"] is None
    assert policy["actionability"] == "non_actionable"
    assert policy["attemptHistory"]["failureReason"] == "http_not_approved"


def test_only_reviewed_candidate_backed_by_first_party_url_is_applicable():
    bundle = cases()
    rows, _summary = build(report_from_fixture(bundle), repairs_from_fixture(bundle))

    applicable = [row for row in rows if row["actionability"] == "actionable"]
    assert len(applicable) == bundle["expected"]["actionableReviewedCandidates"] == 1
    assert applicable[0]["firstPartyEvidence"] == {
        "status": "reviewed",
        "urls": ["https://ajvpsarges.ro/"],
        "reviewed": True,
        "note": "No first-party evidence is attached; do not invent or accept a destination.",
    }

    unconfirmed = next(row for row in rows if row["observedStatus"] == "client_error")
    assert unconfirmed["candidateUrl"] is None
    assert unconfirmed["reviewStatus"] == "needs_first_party_review"
    assert unconfirmed["actionability"] == "non_actionable"
    assert unconfirmed["firstPartyEvidence"]["urls"] == []


def test_correct_url_and_duplicates_are_preserved_without_invented_destinations():
    bundle = cases()
    rows, summary = build(report_from_fixture(bundle), repairs_from_fixture(bundle))

    correct = next(row for row in rows if row["observedStatus"] == "ok")
    assert correct["candidateUrl"] is None
    assert correct["reviewStatus"] == "not_in_repair_scope"
    assert correct["actionability"] == "not_applicable"
    assert correct["repairHistory"] == []
    assert correct["originalUrl"] == "https://www.ajvpsbuzau.ro/ro/contact/"

    duplicates = [
        row
        for row in rows
        if row["originalUrl"] == "https://permise.anpa.ro:12443/portal-public/permis"
    ]
    assert len(duplicates) == 2
    assert summary["duplicateOriginalUrlGroups"] == 1
    assert summary["duplicateOriginalUrlRows"] == 2
    assert [row["duplicate"]["occurrence"] for row in duplicates] == [1, 2]
    assert all(row["duplicate"]["isDuplicate"] for row in duplicates)
    assert all(row["candidateUrl"] is None for row in duplicates)


def test_source_records_and_histories_are_not_mutated_by_build():
    bundle = cases()
    report = report_from_fixture(bundle)
    repairs = repairs_from_fixture(bundle)
    before_report = deepcopy(report)
    before_repairs = deepcopy(repairs)

    build(report, repairs)

    assert report == before_report
    assert repairs == before_repairs
    assert all(row["validationResults"] == [source] for row, source in zip(build(report, repairs)[0], report["records"]))
