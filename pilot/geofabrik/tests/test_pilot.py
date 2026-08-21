import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "pilot/geofabrik"
ART = PILOT / "artifacts"


def test_source_snapshot_hash_and_provenance():
    source = json.loads((ART / "source.json").read_text())
    pbf = PILOT / "data/romania-latest.osm.pbf"
    assert source["url"].endswith("romania-latest.osm.pbf")
    assert source["license"].startswith("OpenStreetMap data, ODbL")
    assert source["sizeBytes"] == pbf.stat().st_size
    h = hashlib.sha256(pbf.read_bytes()).hexdigest()
    assert source["sha256"] == h


def test_inventory_is_exact_and_canonical_data_unchanged():
    inventory = json.loads((ART / "inventory.json").read_text())
    assert inventory["county"] == "Covasna"
    assert inventory["batchCount"] == 5
    assert len({r["slug"] for r in inventory["batch"]}) == 5
    assert {r["class"] for r in inventory["batch"]} == {
        "bbox-fallback", "geometry-less-child", "same-name-collision",
        "real-geometry-gap", "unresolved-negative-control"
    }
    assert not subprocess.run(["git", "diff", "--quiet", "--", "public/data/waters.json"]).returncode


def test_ledger_schema_and_no_guessed_geometry():
    ledger = json.loads((ART / "pilot_ledger.json").read_text())
    assert ledger["metrics"]["batchRecords"] == 5
    assert ledger["metrics"]["knownPositiveTruePositives"] == 1
    for row in ledger["records"]:
        for field in ("slug", "sourceIds", "geometryHash", "geometryType", "matchMethod",
                      "confidence", "endpointEvidence", "classification", "checkedAt"):
            assert field in row
        if row["classification"] != "ACCEPTED_DETERMINISTIC":
            assert row["geometryHash"] is None
            assert row["sourceIds"] == []


def test_deterministic_extraction_and_geometry_hashes():
    rows = (ART / "covasna_named_waterways.jsonl").read_bytes()
    rerun = subprocess.run(
        ["/tmp/geofabrik-venv/bin/python", "scripts/pilot_geofabrik_geometry.py", "extract"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert (ART / "covasna_named_waterways.jsonl").read_bytes() == rows
    assert json.loads(rerun.stdout)["records"] == 582


def test_accepted_geometry_provenance_and_render_contract():
    geo = json.loads((ART / "accepted_geometry.geojson").read_text())
    ledger = json.loads((ART / "pilot_ledger.json").read_text())
    accepted = [r for r in ledger["records"] if r["classification"] == "ACCEPTED_DETERMINISTIC"]
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == len(accepted) == 1
    feature = geo["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["sourceIds"]
    assert feature["properties"]["geometryHash"] == accepted[0]["geometryHash"]
