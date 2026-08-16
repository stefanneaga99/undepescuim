"""Unit tests for scripts/assign_course_frac.py — course_frac assignment.

Network rule (§4.3): geocode()/geocode_any() are never called against real
Nominatim — geocode_any is tested with a mocked geocode().
"""
import pytest

from assign_course_frac import (
    norm,
    haversine,
    order_parts,
    fraction_at,
    build_queries,
    geocode_any,
    county_seat,
)

COURSE = [
    [[26.0240, 45.3300], [26.0300, 45.3150], [26.0360, 45.3000]],
    [[26.0360, 45.3000], [26.0420, 45.2850], [26.0500, 45.2700]],
]


class TestNorm:
    def test_strip_diacritics(self):
        assert norm("Bistrița-Năsăud") == "bistrita nasaud"
        assert norm("Râul Buzău") == "raul buzau"


class TestHaversine:
    def test_zero(self):
        assert haversine((23.0, 46.0), (23.0, 46.0)) == 0.0

    def test_one_degree_lat(self):
        assert haversine((23.0, 46.0), (23.0, 47.0)) == pytest.approx(111.19, abs=0.1)


class TestOrderParts:
    def test_source_to_mouth(self):
        parts = [
            [[26.0360, 45.3000], [26.0420, 45.2850], [26.0500, 45.2700]],  # input scrambled
            [[26.0240, 45.3300], [26.0300, 45.3150], [26.0360, 45.3000]],
        ]
        ordered = order_parts(parts)
        assert ordered[0][0] == [26.024, 45.33]
        assert ordered[-1][-1] == [26.05, 45.27]


class TestFractionAt:
    def test_source_mouth(self):
        assert fraction_at(COURSE, [26.0240, 45.3300]) == pytest.approx(0.0, abs=1e-6)
        assert fraction_at(COURSE, [26.0500, 45.2700]) == pytest.approx(1.0, abs=1e-6)

    def test_unmeasurable(self):
        assert fraction_at([], [0, 0]) is None


class TestBuildQueries:
    def test_limits_first_county_then_river_then_seat(self):
        w = {"name": "Râul Olt", "judet": "Brașov", "limite": "De la Barajul Vidraru până la ieșire din județ"}
        queries = build_queries(w)
        # place names from limits lead (Barajul Vidraru is skipped by stopwords? — check the list)
        assert queries, "expected at least the name+county query"
        # the river-name+county query is present
        assert "Râul Olt, județul Brașov, România" in queries
        # the county-seat query is LAST
        assert queries[-1] == "Brașov, România"

    def test_dedupes(self):
        w = {"name": "Râul Olt", "judet": "Brașov", "limite": ""}
        qs = build_queries(w)
        assert len(qs) == len(set(norm(q) for q in qs))

    def test_no_county(self):
        qs = build_queries({"name": "Râul X", "judet": "", "limite": ""})
        assert qs == ["Râul X, România"]


class TestGeocodeAny:
    def test_returns_first_hit(self):
        calls = []

        def fake_geocode(q):
            calls.append(q)
            if "river" in q:
                return [25.0, 46.0]
            return None

        out = geocode_any(["brașov, românia", "river, românia"])
        assert out == [25.0, 46.0]
        assert calls == ["brașov, românia", "river, românia"]

    def test_returns_none_when_all_miss(self):
        out = geocode_any(["a", "b"])
        assert out is None


class TestCountySeat:
    def test_known_county(self):
        assert county_seat("Cluj") == [23.62, 46.77]

    def test_diacritics_normalized(self):
        assert county_seat("Bistrița-Năsăud") == [24.50, 47.13]
        assert county_seat("bistrita nasaud") == [24.50, 47.13]

    def test_unknown(self):
        assert county_seat("Atlantis") is None