import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "pilot/geofabrik"
ART = PILOT / "artifacts"


def test_source_snapshot_hash_and_provenance():
    source = json.loads((ART / "source.json").read_text())
    assert source["url"].endswith("romania-latest.osm.pbf")
    assert source["license"].startswith("OpenStreetMap data, ODbL")
    assert len(source["sha256"]) == 64


def test_inventory_is_exact_and_canonical_data_unchanged():
    inventory = json.loads((ART / "inventory.json").read_text())
    assert [(row["slug"], row["class"]) for row in inventory["batch"]] == [
        ("anpa-anpa-0252", "bbox-fallback"), ("anpa-anpa-0261", "geometry-less-child"),
        ("anpa-anpa-0264", "same-name-collision"), ("basca-mare-covasna", "real-geometry-gap"),
        ("anpa-anpa-0253", "unresolved-negative-control")]
    assert not subprocess.run(["git", "diff", "--quiet", "--", "public/data/waters.json"]).returncode


def test_discovery_and_ledger_are_review_gated():
    discovery = ART / "candidate_discovery.jsonl"
    assert discovery.exists()
    for line in discovery.read_text().splitlines():
        row = json.loads(line)
        assert row["classification"] == "CANDIDATE_REVIEW_REQUIRED"
        assert row["osm"]["snapshotSha256"]
        assert row["geometryHash"]
    ledger = json.loads((ART / "pilot_ledger.json").read_text())
    assert ledger["metrics"]["batchRecords"] == 5
    assert ledger["metrics"]["batchAccepted"] == 0
    negative = [r for r in ledger["records"] if r["slug"] == "anpa-anpa-0253"]
    assert negative and negative[0]["review"]["status"] != "ACCEPTED_REVIEWED"


def test_rebuild_does_not_touch_canonical_data():
    before = hashlib.sha256((ROOT / "public/data/waters.json").read_bytes()).hexdigest()
    result = subprocess.run([sys.executable, "scripts/pilot_geofabrik_geometry.py", "match"], cwd=ROOT, check=True, capture_output=True, text=True)
    assert json.loads(result.stdout)["batchAccepted"] == 0
    assert hashlib.sha256((ROOT / "public/data/waters.json").read_bytes()).hexdigest() == before


def test_accepted_geometry_provenance_and_render_contract():
    geo = json.loads((ART / "accepted_geometry.geojson").read_text())
    assert geo["type"] == "FeatureCollection"
    for feature in geo["features"]:
        props = feature["properties"]
        assert props["pilotStatus"] == "accepted-reviewed"
        assert props["legalContractGeometry"] is False
        assert props["sourceUrl"].startswith("https://")
    assert not any(f["properties"]["slug"] == "anpa-anpa-0253" for f in geo["features"])
