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
        # 'baraj ' (with space) matches the OTHER_LAKE_RE guard; 'Barajul' does
        # not (it is the river-name prefix 'barajul' in the ANPA list)
        assert anpa_subtype({"water_type": "other", "water_name": "Baraj Vidraru"}) == "lac"
        assert anpa_subtype({"water_type": "other", "water_name": "Fondul piscicol Mândra"}) == "lac"
        assert anpa_subtype({"water_type": "other", "water_name": "Potcoava"}) == "lac"
        assert anpa_subtype({"water_type": "other", "water_name": "Barajul Vidraru"}) == "rau"

    def test_other_with_plain_name_is_river(self):
        assert anpa_subtype({"water_type": "other", "water_name": "Râul Olt"}) == "rau"

    def test_lake_default(self):
        assert anpa_subtype({"water_type": "lake"}) == "lac"
        assert anpa_subtype({}) == "lac"


class TestOsmGeometryFor:
    def _index(self):
        return {
            "raul buzau": {"type": "MultiLineString", "coordinates": [[[0, 0]]], "kind": "relation", "name": "Râul Buzău"},
            "valea rece": {"type": "LineString", "coordinates": [[[0, 0]]], "name": "Valea Rece"},
        }

    def test_exact_norm_match(self):
        g = osm_geometry_for("Râul Buzău", self._index())
        assert g == {"type": "MultiLineString", "coordinates": [[[0, 0]]]}

    def test_core_match_after_prefix_strip(self):
        idx = {"buzau": {"type": "LineString", "coordinates": [[[0, 0]]], "name": "buzau"}}
        g = osm_geometry_for("Râul Buzău", idx)
        assert g is not None

    def test_fuzzy_token_overlap(self):
        # 2 of the water's 3 core tokens match the 3-token index entry → 2/3
        idx = {"valea rece mare": {"type": "LineString", "coordinates": [[[0, 0]]], "name": "Valea Rece Mare"}}
        g = osm_geometry_for("Râul Rece Mare", idx)
        assert g is not None

    def test_no_match(self):
        assert osm_geometry_for("Lacul Inventat", self._index()) is None
        assert osm_geometry_for("", self._index()) is None


class TestMergeIdempotency:
    """Run-twice → identical result (§4.3). The merge loop is deterministic:
    run 1 adds new names, run 2 (already merged input) skips every entry —
    output bytes are unchanged."""

    def _merge_once(self, fe, anpa, osm_index):
        """Faithful port of merge_anpa_waters.main()'s loop over in-memory
        lists — no file I/O (determinism rule)."""
        from merge_anpa_waters import anpa_subtype, norm as m_norm, osm_geometry_for as osm_for
        fe_by_name = {m_norm(x["name"]): x for x in fe}
        added = skipped = 0
        for w in anpa:
            name = w["water_name"]
            n = m_norm(name)
            geom = osm_for(name, osm_index)
            existing = fe_by_name.get(n)
            if existing is not None:
                if geom and (
                    existing.get("geometry") is None
                    or (geom["type"] == "MultiLineString" and existing["geometry"].get("type") != "MultiLineString")
                ):
                    existing["geometry"] = geom
                skipped += 1
                continue
            entry = {
                "slug": f"anpa-{w['id']}",
                "name": name,
                "type": "ape",
                "subtype": anpa_subtype(w),
                "asociatie": {"name": "X", "slug": "x"},
                "geometry": geom,
            }
            fe.append(entry)
            fe_by_name[n] = entry
            added += 1
        return added, skipped

    def test_rebuild_is_stable(self):
        fe = [{"slug": "w1", "name": "Râul Există", "geometry": None}]
        anpa = [
            {"id": "1", "water_name": "Râul Există", "water_type": "river"},   # dup → skip
            {"id": "2", "water_name": "Râul Nou", "water_type": "river"},      # add
            {"id": "3", "water_name": "Lacul Nou", "water_type": "lake"},      # add
        ]
        osm_index = {"raul nou": {"type": "LineString", "coordinates": [[[0, 0]]], "name": "Râul Nou"}}

        import json as _json
        run1 = {"added": self._merge_once(fe, anpa, osm_index)[0],
                "serialized": _json.dumps(fe, sort_keys=True)}
        fc = _json.loads(run1["serialized"])
        # Second run over the MERGED list: same input ANPA → nothing added,
        # output must be byte-identical.
        run2_added, _ = self._merge_once(fc, anpa, osm_index)
        assert run1["added"] == 2
        assert run2_added == 0
        assert _json.dumps(fc, sort_keys=True) == run1["serialized"]

    def test_geometry_upgrade_is_noop_when_not_better(self):
        fe = [{"slug": "w1", "name": "Râul X", "geometry": {"type": "MultiLineString", "coordinates": [[[1, 2]]]}}]
        anpa = [{"id": "1", "water_name": "Râul X", "water_type": "river"}]
        osm_index = {"raul x": {"type": "LineString", "coordinates": [[[3, 4]]], "name": "Râul X"}}
        added, skipped = self._merge_once(fe, anpa, osm_index)
        assert added == 0 and skipped == 1
        assert fe[0]["geometry"]["type"] == "MultiLineString"  # kept the better one