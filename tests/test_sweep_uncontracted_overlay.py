"""Unit tests for scripts/sweep_uncontracted_overlay.py — overlay sweep classification."""
import pytest

from sweep_uncontracted_overlay import (
    river_core_name,
    name_match,
    classify_river_hit,
    classify_lake_hit,
)
from shapely.geometry import LineString, MultiLineString, Point, Polygon, shape


def _w(name="Râul Siriu"):
    return {"slug": "w", "name": name, "judet": "Buzău"}


class TestRiverCoreName:
    def test_strips_prefixes(self):
        assert river_core_name("Râul Siriu") == "siriu"
        assert river_core_name("Siriul") == "siriul"  # definite-article form kept as-is
        assert river_core_name("Valea Pojorâtei") == "pojoratei"
        assert river_core_name("Recea") == "recea"  # no prefix


class TestNameMatch:
    def test_exact_normalized(self):
        assert name_match("Râul Siriu", "Siriu")
        assert name_match("Siriul", "Siriul")

    def test_core_equality(self):
        assert name_match("Râul Bâsca", "Bâsca")
        assert name_match("Valea Pojorâtei", "Pojorâtei")

    def test_lake_core(self):
        assert name_match("Lacul Vidraru", "acumularea Vidraru")

    def test_no_match(self):
        assert not name_match("Râul Olt", "Râul Mureș")
        # 'siriu' vs 'siriul' do NOT match — definite-article forms are not merged
        assert not name_match("Râul Siriu", "Siriul")


class TestClassifyRiverHit:
    def test_2pt_chord_is_ambiguous(self):
        # a simplified 2-pt chord that lies ON the contracted course — the
        # Valea Brustuletului class (t_963f40e4): cannot judge by proximity.
        unc_geom = LineString([[0, 0], [1, 1]])
        w_geom = LineString([[0, 0], [1, 1]])
        label, conf, note = classify_river_hit(
            {"name": "Valea X"}, unc_geom, _w(), w_geom, 0.0, 1.0, True, True
        )
        assert label == "AMBIGUOUS"
        assert "2-pt chord" in note

    def test_duplicate_when_name_and_course_overlap(self):
        unc_geom = LineString([[0, 0], [1, 0], [2, 0]])
        w_geom = LineString([[0, 0], [2, 0]])
        label, conf, _ = classify_river_hit(
            {"name": "Râul X"}, unc_geom, _w("Râul X"), w_geom, 0.0, 1.0, True, True
        )
        assert label == "DUPLICATE"

    def test_tributary_mouth_only(self):
        # one end touches; course then moves away
        unc_geom = LineString([[0, 0], [1, 0], [2, 1]])
        w_geom = LineString([[0, 0], [0, 1]])
        label, conf, note = classify_river_hit(
            {"name": "Pârâul X"}, unc_geom, _w(), w_geom, 0.0001, 0.3, False, False
        )
        assert label == "TRIBUTARY"
        assert "mouth" in note

    def test_name_collision_far_apart(self):
        unc_geom = LineString([[0, 0], [0.5, 0], [1, 0]])  # 3-pt: real course, not a 2-pt chord
        w_geom = LineString([[5, 5], [6, 5]])
        label, conf, note = classify_river_hit(
            {"name": "Crasna"}, unc_geom, _w("Crasna"), w_geom, 0.5, 0.1, False, True
        )
        assert label == "NAME_COLLISION"
        assert "m away" in note

    def test_partial_duplicate_via_long_part_on_course(self):
        # one part of a MultiLineString lies >90% on the contracted course and
        # is >1 km long → PARTIAL_DUPLICATE (the Doftana class, t_f4ff3853)
        unc_geom = MultiLineString([LineString([[0, 0], [1, 0]]), LineString([[4, 4], [5, 5]])])
        w_geom = LineString([[0, 0], [2, 0]])
        part_fracs = [(0, 1.0, 111.0), (1, 0.0, 150.0)]
        label, conf, note = classify_river_hit(
            {"name": "Doftana"}, unc_geom, _w("Râul Doftana"), w_geom,
            0.0, 0.35, False, False, part_fracs=part_fracs,
        )
        assert label == "PARTIAL_DUPLICATE"
        assert "part 0" in note

    def test_tiny_part_does_not_trigger_partial(self):
        # a 2-pt connector fragment (< 1 km) at the confluence is NOT a
        # partial duplicate even at 100% course-nearness
        unc_geom = MultiLineString([LineString([[0, 0], [1, 0]])])
        w_geom = LineString([[0, 0], [2, 0]])
        part_fracs = [(0, 1.0, 0.5)]  # only 0.5 km
        label, conf, _ = classify_river_hit(
            {"name": "X"}, unc_geom, _w(), w_geom, 0.0, 1.0, True, True, part_fracs=part_fracs
        )
        assert label == "DUPLICATE"  # falls through to the name+frac_near rule

    def test_no_classification_returned(self):
        unc_geom = LineString([[0, 0], [0.5, 0], [1, 0]])  # 3-pt: real course
        w_geom = LineString([[5, 5], [6, 5]])
        cls = classify_river_hit(
            {"name": "Altul"}, unc_geom, _w(), w_geom, 7.0, 0.0, False, False
        )
        assert cls is None


class TestClassifyLakeHit:
    def _lake_geom(self):
        return Polygon([[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]])

    def test_duplicate_by_area(self):
        w_geom = Polygon([[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]])
        label, conf, note = classify_lake_hit(
            {"name": "Lacul X"}, self._lake_geom(), _w("Lacul X"), w_geom, 0.9, True, 0.0, True
        )
        assert label == "DUPLICATE"

    def test_duplicate_by_name_and_centroid(self):
        w_geom = Polygon([[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]])
        label, conf, _ = classify_lake_hit(
            {"name": "Lacul Vidraru"}, self._lake_geom(), _w("Lacul Vidraru"), w_geom,
            0.0, True, 0.0, True,
        )
        assert label == "DUPLICATE"

    def test_ambiguous_by_area(self):
        w_geom = Polygon([[1.5, 0], [4, 0], [4, 2], [1.5, 2], [1.5, 0]])
        label, conf, note = classify_lake_hit(
            {"name": "Lacul X"}, self._lake_geom(), _w(), w_geom, 0.3, False, 0.0, False
        )
        assert label == "AMBIGUOUS"
        assert "overlap" in note

    def test_name_collision_far(self):
        w_geom = Polygon([[10, 10], [12, 10], [12, 12], [10, 12], [10, 10]])
        label, conf, note = classify_lake_hit(
            {"name": "Lacul Crasna"}, self._lake_geom(), _w("Lacul Crasna"), w_geom,
            0.0, False, 0.5, True,
        )
        assert label == "NAME_COLLISION"

    def test_no_classification(self):
        w_geom = Polygon([[10, 10], [12, 10], [12, 12], [10, 12], [10, 10]])
        cls = classify_lake_hit(
            {"name": "Lacul Altul"}, self._lake_geom(), _w(), w_geom, 0.0, False, 0.5, False
        )
        assert cls is None


class TestLoadGeoms:
    def test_loads_and_skips_invalid(self):
        from sweep_uncontracted_overlay import load_geoms
        entries = [
            {"slug": "ok", "geometry": {"type": "Point", "coordinates": [0, 0]}},
            {"slug": "no-geom"},
            {"slug": "bad", "geometry": {"type": "Bogus", "coordinates": []}},
        ]
        out = load_geoms(entries)
        assert [e["slug"] for e, _ in out] == ["ok"]