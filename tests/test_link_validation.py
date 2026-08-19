import hashlib
import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).parents[1]

def run(tmp_path):
    report = tmp_path / "report.json"
    repairs = tmp_path / "repairs.jsonl"
    result = subprocess.run([sys.executable, "scripts/link_validation.py", "--mode", "fixtures", "--report", str(report), "--repairs", str(repairs), "--fail-on", "none"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(report.read_text()), repairs.read_text().splitlines()

def test_fixture_report_schema_and_classifications(tmp_path):
    report, repairs = run(tmp_path)
    assert report["schemaVersion"] == 1
    assert report["summary"]["total"] == 9
    assert {r["status"] for r in report["records"]} >= {"ok", "redirected", "client_error", "server_error", "blocked"}
    redirected = next(r for r in report["records"] if r["associationSlug"] == "redirect")
    assert redirected["originalUrl"] == "https://example.com/old?token=REDACTED"
    assert redirected["finalUrl"] == "https://example.com/new"
    assert all("secret" not in line and "person@example.com" not in line for line in repairs)

def test_registered_field_coverage_is_explicit():
    from scripts.link_validation_lib import ALLOWED_FIELDS
    fixture = json.loads((ROOT / "tests/fixtures/link_validation/coverage.json").read_text())
    assert set(fixture["fields"]) == ALLOWED_FIELDS


def test_policy_blocks_without_transport():
    from scripts.link_validation_lib import LinkTarget, result_for
    target = LinkTarget("x", "association.siteUrl", "fixture", "test", "http://localhost:8080/a")
    record = result_for(target, now="2026-01-01T00:00:00Z")
    assert record["status"] == "blocked"
    assert record["failureReason"] == "private_target"

def test_existing_source_data_is_not_modified(tmp_path):
    tracked = [ROOT / "public/data/waters.json", ROOT / "public/data/associations.json", ROOT / "data/processed/association_locations.json"]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    run(tmp_path)
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}


def test_content_classification_is_safe_and_body_free():
    from scripts.link_validation import content_reason
    html = SimpleNamespace(headers={"Content-Type": "text/html; charset=utf-8"}, _validator_sample=b"Welcome")
    assert content_reason(html, "association.siteUrl") is None
    parked = SimpleNamespace(headers={"Content-Type": "text/html"}, _validator_sample=b"Domain is for sale")
    assert content_reason(parked, "association.siteUrl") == "parked_domain"
    binary = SimpleNamespace(headers={"Content-Type": "application/octet-stream"}, _validator_sample=b"")
    assert content_reason(binary, "association.siteUrl") == "wrong_content_type"


def test_retryable_statuses_are_explicit():
    from scripts.link_validation import RETRYABLE
    assert {408, 425, 429, 500, 502, 503, 504}.issubset(RETRYABLE)
    assert 404 not in RETRYABLE
