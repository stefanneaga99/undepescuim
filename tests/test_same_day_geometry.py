"""P0 regression contract for the same-day geometry mappings.

Keep this fixture independent of the browser so data-only CI catches a slug
being moved to the wrong water, county, or bbox-only fallback.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_same_day_geometry_mappings_are_real_and_exact():
    waters = {water["slug"]: water for water in _load("public/data/waters.json")}
    probes = _load("tests/fixtures/same_day_geometry_contract.json")

    for probe in probes:
        slug = probe["slug"]
        water = waters.get(slug)
        assert water is not None, f"{probe['id']}: missing slug {slug}"
        assert water["name"] == probe["name"], f"{probe['id']}: wrong water for {slug}"
        assert water["judet"] == probe["county"], f"{probe['id']}: wrong county for {slug}"
        geometry = water.get("geometry")
        assert geometry and geometry.get("type") in probe["geometry_types"], (
            f"{probe['id']}: {slug} must have {probe['geometry_types']}, got {geometry!r}"
        )
        coordinates = geometry.get("coordinates")
        assert isinstance(coordinates, list) and coordinates, (
            f"{probe['id']}: {slug} geometry coordinates are empty"
        )
        assert water.get("_bboxFallback") is not True, (
            f"{probe['id']}: {slug} unexpectedly uses bbox-only fallback"
        )
