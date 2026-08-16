"""Cross-language parity golden tests (plan §3.6).

The SAME geometry math exists twice:
  - TypeScript: src/utils/river-course.ts (orderParts / fractionAtPoint)
  - Python:     scripts/_mapping_common.py (ordered_parts / fraction_at_point)

Both read the SHARED fixture tests/fixtures/winding_river.geojson and must
produce the golden numbers in tests/fixtures/parity_expectations.json —
computed from the reference Python implementation and asserted on the vitest
side too (src/utils/river-course.test.ts). If one side drifts, one of the two
suites fails. This directly guards the course_frac ordering bugs
(t_9a7cf783 'Pârâu Buzăul Mijlociu', t_f4ff3853 Doftana).
"""
import json
from pathlib import Path

import pytest

from _mapping_common import (
    ordered_parts,
    order_course_linestring,
    km_to_frac,
    fraction_at_point,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GEOM_FILE = FIXTURES / "winding_river.geojson"
GOLDEN_FILE = FIXTURES / "parity_expectations.json"


@pytest.fixture(scope="module")
def winding_geom():
    fc = json.loads(GEOM_FILE.read_text(encoding="utf-8"))
    return fc["features"][0]["geometry"]


@pytest.fixture(scope="module")
def golden():
    return json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))


class TestParity:
    def test_ordered_course_endpoints(self, winding_geom, golden):
        ordered = ordered_parts(winding_geom)
        assert ordered[0][0] == golden["ordered_course"]["first_point"]
        assert ordered[-1][-1] == golden["ordered_course"]["last_point"]
        assert [len(p) for p in ordered] == golden["ordered_course"]["part_point_counts"]

    def test_fraction_at_point_matches_golden(self, winding_geom, golden):
        for case in golden["fraction_at_point"]:
            frac = fraction_at_point(winding_geom, case["point"])
            assert frac == pytest.approx(case["fraction"], abs=1e-6), case

    def test_km_to_frac_matches_golden(self, winding_geom, golden):
        for case in golden["km_to_frac"]:
            assert km_to_frac(winding_geom, case["km"]) == pytest.approx(case["fraction"], abs=1e-6), case

    def test_deduped_chain_matches_golden(self, winding_geom, golden):
        ls = order_course_linestring(winding_geom)
        assert len(ls["coordinates"]) == golden["deduped_chain"]["point_count"]
        assert ls["coordinates"][0] == golden["deduped_chain"]["first_point"]
        assert ls["coordinates"][-1] == golden["deduped_chain"]["last_point"]