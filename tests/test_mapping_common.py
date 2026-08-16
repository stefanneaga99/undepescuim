"""Unit tests for scripts/_mapping_common.py — the shared pipeline helpers."""
import json

import pytest

from _mapping_common import (
    CANONICAL_COUNTIES,
    _county_key,
    canonical_county,
    slugify,
    assoc_slug,
    geom_bbox,
    merge_geoms,
    set_geometry,
    ordered_parts,
    order_course_linestring,
    ordered_fractions,
    km_to_frac,
    fraction_at_point,
    haversine_km,
    pick_cluster,
)


# ---------------------------------------------------------------------------
# canonical_county / _county_key
# ---------------------------------------------------------------------------
class TestCanonicalCounty:
    def test_all_42_counties_mapped(self):
        assert len(CANONICAL_COUNTIES) == 42

    def test_diacritics_and_separators_normalized(self):
        assert canonical_county("BISTRIȚA - NĂSĂUD") == "Bistrița-Năsăud"
        assert canonical_county("Bistrița-Năsăud") == "Bistrița-Năsăud"
        assert canonical_county("Bistrita-Nasaud") == "Bistrița-Năsăud"

    def test_plain_counties(self):
        assert canonical_county("cluj") == "Cluj"
        assert canonical_county("CĂLĂRAȘI") == "Călărași"
        assert canonical_county("București") == "București"

    def test_empty_string_passthrough(self):
        assert canonical_county("") == ""

    def test_county_key(self):
        assert _county_key("Bistrița - Năsăud") == "bistritanasaud"
        assert _county_key("Cluj") == "cluj"


class TestSlugify:
    def test_strips_diacritics_and_punctuation(self):
        assert slugify("Râul Bistrița Aurie") == "raul-bistrita-aurie"
        assert slugify("Lacul Vidraru") == "lacul-vidraru"

    def test_empty(self):
        assert slugify("") == ""
        assert slugify(None) == ""


class TestAssocSlug:
    def test_exact_name_match(self):
        assocs = [{"name": "AJVPS Cluj", "slug": "ajvps-cluj"}]
        waters = []
        assert assoc_slug("AJVPS Cluj", waters, assocs) == "ajvps-cluj"

    def test_case_insensitive_fallback_via_waters(self):
        assocs = [{"name": "AJVPS Cluj", "slug": "ajvps-cluj"}]
        waters = [
            {"asociatie": {"name": "ajvps cluj", "slug": "ajvps-cluj"}},
            {"asociatie": {"name": "ajvps cluj", "slug": "ajvps-cluj"}},
        ]
        assert assoc_slug("Ajvps Cluj", waters, assocs) == "ajvps-cluj"

    def test_unknown_name_slugified(self):
        assert assoc_slug("AJVPS Satu Mare", [], []) == "ajvps-satu-mare"


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------
class TestGeomBbox:
    def test_linestring(self):
        g = {"type": "LineString", "coordinates": [[23.0, 46.0], [23.5, 46.5], [23.2, 45.9]]}
        assert geom_bbox(g) == [23.0, 45.9, 23.5, 46.5]

    def test_multilinestring_flattens_parts(self):
        g = {"type": "MultiLineString", "coordinates": [[[23.0, 46.0], [23.5, 46.5]], [[24.0, 45.0]]]}
        assert geom_bbox(g) == [23.0, 45.0, 24.0, 46.5]

    def test_rounds_to_6_dp(self):
        g = {"type": "LineString", "coordinates": [[23.123456789, 46.0]]}
        assert geom_bbox(g) == [23.123457, 46.0, 23.123457, 46.0]

    def test_none_and_empty(self):
        assert geom_bbox(None) is None
        assert geom_bbox({"type": "LineString", "coordinates": []}) is None


class TestMergeGeoms:
    def test_single_linestring_stays_linestring(self):
        g1 = {"type": "LineString", "coordinates": [[1, 2], [3, 4]]}
        out = merge_geoms([g1])
        assert out == {"type": "LineString", "coordinates": [[1, 2], [3, 4]]}

    def test_multiple_parts_become_multilinestring(self):
        g1 = {"type": "LineString", "coordinates": [[1, 2], [3, 4]]}
        g2 = {"type": "LineString", "coordinates": [[5, 6], [7, 8]]}
        out = merge_geoms([g1, g2])
        assert out["type"] == "MultiLineString"
        assert out["coordinates"] == [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]

    def test_empty_inputs(self):
        assert merge_geoms([]) == {"type": "LineString", "coordinates": []}
        assert merge_geoms([None, None]) == {"type": "LineString", "coordinates": []}


class TestSetGeometry:
    def test_attaches_geometry_and_bbox(self):
        w = {}
        g = {"type": "LineString", "coordinates": [[23.0, 46.0], [23.5, 46.5]]}
        set_geometry(w, g)
        assert w["geometry"] == g
        assert w["bbox"] == [23.0, 46.0, 23.5, 46.5]

    def test_does_not_overwrite_when_geom_none(self):
        w = {"geometry": "keep"}
        set_geometry(w, None)
        assert w == {"geometry": "keep"}

    def test_skips_degenerate_bbox(self):
        w = {}
        set_geometry(w, {"type": "LineString", "coordinates": []})
        assert "bbox" not in w


# ---------------------------------------------------------------------------
# course ordering + fractions
# ---------------------------------------------------------------------------
WINDING = {
    "type": "MultiLineString",
    "coordinates": [
        [[26.0360, 45.3000], [26.0420, 45.2850], [26.0500, 45.2700]],
        [[26.0240, 45.3300], [26.0300, 45.3150], [26.0360, 45.3000]],
        [[26.0740, 45.2100], [26.0780, 45.1950], [26.0800, 45.1800]],
        [[26.0640, 45.2400], [26.0700, 45.2250], [26.0740, 45.2100]],
        [[26.0360, 45.3000], [26.0420, 45.2850], [26.0500, 45.2700]],
    ],
}


class TestOrderedParts:
    def test_single_part_passthrough(self):
        g = {"type": "LineString", "coordinates": [[1, 2], [3, 4]]}
        assert ordered_parts(g) == [[[1, 2], [3, 4]]]

    def test_scrambled_parts_ordered_source_to_mouth(self):
        ordered = ordered_parts(WINDING)
        assert ordered[0][0] == [26.024, 45.33]  # source
        assert ordered[-1][-1] == [26.08, 45.18]  # mouth


class TestOrderCourseLinestring:
    def test_chains_and_dedupes_duplicate_parts(self):
        ls = order_course_linestring(WINDING)
        assert ls["type"] == "LineString"
        assert ls["coordinates"][0] == [26.024, 45.33]
        assert ls["coordinates"][-1] == [26.08, 45.18]
        # 4 unique parts, chained (shared junction points not repeated)
        assert len(ls["coordinates"]) == 10


class TestOrderedFractions:
    def test_fractions_are_cumulative_and_end_at_1(self):
        fracs = ordered_fractions(WINDING)
        assert len(fracs) == 5
        assert fracs[0][0] == pytest.approx(0.0)
        assert fracs[-1][1] == pytest.approx(1.0)
        for f0, f1, *_ in fracs:
            assert 0.0 <= f0 <= f1 <= 1.0
        # each consecutive part starts where the previous ended
        for (_, e0, _, _), (s1, _, _, _) in zip(fracs, fracs[1:]):
            assert e0 == pytest.approx(s1)

    def test_empty_geometry(self):
        assert ordered_fractions({"type": "LineString", "coordinates": []}) == []


class TestKmToFrac:
    def test_zero_and_clamp(self):
        assert km_to_frac(WINDING, 0.0) == 0.0
        assert km_to_frac(WINDING, 999.0) == 1.0

    def test_mid_course(self):
        assert km_to_frac(WINDING, 10.0) == pytest.approx(0.981699, abs=1e-5)

    def test_unmeasurable(self):
        assert km_to_frac({"type": "LineString", "coordinates": []}, 5.0) == 0.0


class TestFractionAtPoint:
    def test_source_and_mouth(self):
        assert fraction_at_point(WINDING, [26.0240, 45.3300]) == pytest.approx(0.0, abs=1e-6)
        assert fraction_at_point(WINDING, [26.0800, 45.1800]) == pytest.approx(1.0, abs=1e-6)

    def test_mid_junctions(self):
        assert fraction_at_point(WINDING, [26.0360, 45.3000]) == pytest.approx(0.200352, abs=1e-5)
        assert fraction_at_point(WINDING, [26.0500, 45.2700]) == pytest.approx(0.403533, abs=1e-5)
        assert fraction_at_point(WINDING, [26.0640, 45.2400]) == pytest.approx(0.606713, abs=1e-5)

    def test_unmeasurable_returns_none(self):
        assert fraction_at_point({"type": "LineString", "coordinates": []}, [0, 0]) is None


class TestHaversineKm:
    def test_zero(self):
        assert haversine_km((23.0, 46.0), (23.0, 46.0)) == 0.0

    def test_one_degree_lat(self):
        assert haversine_km((23.0, 46.0), (23.0, 47.0)) == pytest.approx(111.19, abs=0.1)


class TestPickCluster:
    def test_picks_cluster_by_county_proximity(self):
        county_centroids = {"Cluj": (23.6, 46.7)}
        osm_geo_by_norm = {
            "bistrita": [
                {"type": "LineString", "coordinates": [[24.5, 47.1], [24.6, 47.2]]},  # Bistrița-Năsăud (far)
            ],
            "crisul": [
                {"type": "LineString", "coordinates": [[23.4, 46.6], [23.5, 46.7]]},  # Cluj (near)
            ],
        }
        g, name, score = pick_cluster(["crisul", "bistrita"], "Cluj", osm_geo_by_norm, county_centroids)
        assert name == "crisul"
        assert g is not None

    def test_no_candidates(self):
        g, name, score = pick_cluster(["nimeni"], "Cluj", {}, {})
        assert g is None
        assert name == ""
        assert score == -1.0