"""Unit tests for scripts/match_small_rivers.py — OSM bulk-matching of small rivers."""
import pytest

from match_small_rivers import norm, build_name_index, similarity, match_water, make_feature


class TestNorm:
    def test_lowercase_strip_diacritics_collapse(self):
        assert norm("Pârâul Buzăielului") == "paraul buzaielului"
        assert norm("Râul  Bistrița!!") == "raul bistrita"
        assert norm("Valea (Pojorâtei)") == "valea pojoratei"

    def test_empty(self):
        assert norm("") == ""
        assert norm(None) == ""


class TestSimilarity:
    def test_token_overlap(self):
        assert similarity("paraul buzaielului", "buzaielului") == pytest.approx(0.5)
        assert similarity("a b c", "a b c d") == pytest.approx(3 / 4)

    def test_no_overlap(self):
        assert similarity("a b", "c d") == 0.0

    def test_empty(self):
        assert similarity("", "x") == 0.0


class TestBuildNameIndex:
    def test_ways_and_relations_indexed(self):
        data = {
            "elements": [
                {"type": "node", "id": 1, "lat": 46.0, "lon": 23.0},
                {"type": "node", "id": 2, "lat": 46.1, "lon": 23.1},
                {"type": "way", "id": 101, "nodes": [1, 2], "tags": {"name": "Valea Rece", "waterway": "stream"}},
                {"type": "relation", "id": 201, "members": [{"type": "way", "ref": 101}], "tags": {"name": "Valea Rece", "waterway": "river"}},
            ]
        }
        index, geoms = build_name_index(data)
        assert "valea rece" in index
        # relation preferred in name_index entries order (201 listed after 101)
        assert set(index["valea rece"]) == {101, 201}
        assert geoms[201]["kind"] == "relation"
        assert geoms[101]["geometry"]["type"] == "LineString"

    def test_short_way_dropped(self):
        data = {"elements": [{"type": "node", "id": 1, "lat": 46.0, "lon": 23.0},
                             {"type": "way", "id": 101, "nodes": [1], "tags": {"name": "X", "waterway": "stream"}}]}
        index, geoms = build_name_index(data)
        assert 101 not in geoms


class TestMatchWater:
    def _waters(self):
        return {"name": "Valea Rece", "slug": "valea-rece", "judet": "Cluj"}

    def _index(self):
        data = {
            "elements": [
                {"type": "node", "id": 1, "lat": 46.0, "lon": 23.0},
                {"type": "node", "id": 2, "lat": 46.1, "lon": 23.1},
                {"type": "node", "id": 3, "lat": 46.2, "lon": 23.2},
                {"type": "way", "id": 101, "nodes": [1, 2], "tags": {"name": "Valea Rece", "waterway": "stream"}},
                {"type": "way", "id": 102, "nodes": [2, 3], "tags": {"name": "Valea Rece", "waterway": "stream"}},
            ]
        }
        return build_name_index(data)

    def test_exact_match_merges_ways(self):
        idx, geoms = self._index()
        f = match_water(self._waters(), idx, geoms)
        assert f is not None
        assert f["geometry"]["type"] == "MultiLineString"  # two ways merged
        assert f["properties"]["source_detail"] == "osm_exact"

    def test_fuzzy_match_within_threshold(self):
        # index entry has 3 tokens, water core shares 2 → 2/3 >= 0.6 fuzzy hit
        data = {
            "elements": [
                {"type": "node", "id": 1, "lat": 46.0, "lon": 23.0},
                {"type": "node", "id": 2, "lat": 46.1, "lon": 23.1},
                {"type": "way", "id": 101, "nodes": [1, 2], "tags": {"name": "Valea Rece Mare", "waterway": "stream"}},
            ]
        }
        idx, geoms = build_name_index(data)
        w = {"name": "Valea Rece Mare Mică", "slug": "vrm-mica", "judet": "Cluj"}
        f = match_water(w, idx, geoms)
        assert f is not None
        assert f["properties"]["source_detail"].startswith("osm_fuzzy_")

    def test_no_match_returns_none(self):
        idx, geoms = self._index()
        f = match_water({"name": "Lacul Nu Exista", "slug": "ne"}, idx, geoms)
        assert f is None

    def test_empty_name_returns_none(self):
        idx, geoms = self._index()
        assert match_water({"name": "Râul"}, idx, geoms) is None


class TestMakeFeature:
    def test_shape(self):
        f = make_feature(
            {"slug": "s", "name": "Râul X", "judet": "Cluj"},
            {"geometry": {"type": "LineString", "coordinates": [[1, 2], [3, 4]]}, "name": "X"},
            "osm_exact",
        )
        assert f["type"] == "Feature"
        assert f["id"] == "s"
        assert f["properties"]["confidence"] == "medium"  # exact match
        assert f["geometry"]["coordinates"] == [[1, 2], [3, 4]]

    def test_fuzzy_is_low_confidence(self):
        f = make_feature({"slug": "s", "name": "Râul X"}, {"geometry": {"type": "LineString", "coordinates": []}}, "osm_fuzzy_0.61")
        assert f["properties"]["confidence"] == "low"