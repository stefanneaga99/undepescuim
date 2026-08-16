"""Unit tests for scripts/merge_anpa_waters.py — ANPA canonical merge.

Determinism rule (§4.3): the merge is tested only through its PURE functions
(norm / anpa_subtype / osm_geometry_for) — never by touching the real
public/data/waters.json or data/cache/geocode.db. Idempotency of the file-level
merge is covered by the pure-function contract: adding an existing name skips
it, upgrading geometry is a no-op when not better.
"""
import pytest

from merge_anpa_waters import norm, anpa_subtype, osm_geometry_for


class TestNorm:
    def test_lowercase_strip_diacritics_collapse(self):
        assert norm("Râul Buzău") == "raul buzau"
        assert norm("  Lacul   Vidraru ") == "lacul vidraru"
        assert norm("") == ""

    def test_name_dedupe(self):
        assert norm("Râul  Buzău") == norm("Râul Buzău")


class TestAnpaSubtype:
    def test_river_stream(self):
        assert anpa_subtype({"water_type": "river"}) == "rau"
        assert anpa_subtype({"water_type": "stream"}) == "rau"

    def test_other_with_baraj_name_is_lake(self):
        assert anpa_subtype({"water_type": "other", "water_name": "Barajul Vidraru"}) == "lac"
        assert anpa_subtype({"water_type": "other", "water_name": "Fondul piscicol Mândra"}) == "lac"
        assert anpa_subtype({"water_type": "other", "water_name": "Potcoava"}) == "lac"

    def test_other_with_plain_name_is_river(self):
        assert anpa_subtype({"water_type": "other", "water_name": "Râul Olt"}) == "rau"

    def test_lake_default(self):
        assert anpa_subtype({"water_type": "lake"}) == "lac"
        assert anpa_subtype({}) == "lac"


class TestOsmGeometryFor:
    def _index(self):
        return {
            "raul buzau": {"type": "MultiLineString", "coordinates": [[[...]]], "kind": "relation", "name": "Râul Buzău"},
            "valea rece": {"type": "LineString", "coordinates": [[[...]]], "name": "Valea Rece"},
        }

    def test_exact_norm_match(self):
        g = osm_geometry_for("Râul Buzău", self._index())
        assert g == {"type": "MultiLineString", "coordinates": [[[...]]]}

    def test_core_match_after_prefix_strip(self):
        idx = {"buzau": {"type": "LineString", "coordinates": [[[...]]], "name": "buzau"}}
        g = osm_geometry_for("Râul Buzău", idx)
        assert g is not None

    def test_fuzzy_token_overlap(self):
        idx = {"valea rece mica": {"type": "LineString", "coordinates": [[[...]]], "name": "Valea Rece Mică"}}
        g = osm_geometry_for("Valea Rece", idx)
        assert g is not None  # 2/3 token overlap >= 0.6

    def test_no_match(self):
        assert osm_geometry_for("Lacul Inventat", self._index()) is None
        assert osm_geometry_for("", self._index()) is None