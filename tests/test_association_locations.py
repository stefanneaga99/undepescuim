import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_curated_locations_validate():
    result = subprocess.run(
        [sys.executable, "scripts/validate_association_locations.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "11 records" in result.stdout


def test_public_projection_matches_curated_source():
    source = json.loads((ROOT / "data/processed/association_locations.json").read_text())
    public = json.loads((ROOT / "public/data/association_locations.json").read_text())
    assert public == source
    assert all(row["public"] and row["review"]["status"] == "approved" for row in public["locations"])


def test_patarlagele_is_not_pickup_or_branch():
    data = json.loads((ROOT / "public/data/association_locations.json").read_text())
    row = next(item for item in data["locations"] if item["locality"] == "Pătârlagele")
    assert row["type"] == "club_contact_point"
    assert "pickup" not in row["label"].lower()
    assert row["freshness"] == "needs_confirmation"
