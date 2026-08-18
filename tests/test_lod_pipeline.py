"""Deterministic coverage for the map LOD data builders."""

import json

import build_uncontracted_majors as majors
from simplify_waters_geometry import annotate_size


def test_annotate_size_adds_line_length_and_polygon_area():
    river = {"coordinates": [25.0, 45.0]}
    annotate_size(
        river,
        {"type": "LineString", "coordinates": [[25.0, 45.0], [25.0, 46.0]]},
    )
    assert 111.1 <= river["lengthKm"] <= 111.3

    lake = {"coordinates": [25.0, 45.0]}
    annotate_size(
        lake,
        {
            "type": "Polygon",
            "coordinates": [[[25.0, 45.0], [25.01, 45.0], [25.01, 45.01], [25.0, 45.01], [25.0, 45.0]]],
        },
    )
    assert 87 <= lake["areaHa"] <= 88


def test_annotate_size_leaves_point_fallback_without_size():
    water = {"coordinates": [25.0, 45.0]}
    annotate_size(water, {"type": "Point", "coordinates": [25.0, 45.0]})
    assert "lengthKm" not in water
    assert "areaHa" not in water


def test_build_majors_uses_exact_national_lod_thresholds(tmp_path, monkeypatch):
    rivers = tmp_path / "rivers.json"
    lakes = tmp_path / "lakes.json"
    output = tmp_path / "majors.json"
    rivers.write_text(json.dumps([
        {"slug": "short", "lengthKm": 29.99},
        {"slug": "river-threshold", "lengthKm": 30},
        {"slug": "river-large", "lengthKm": 90},
        {"slug": "river-missing"},
    ]), encoding="utf-8")
    lakes.write_text(json.dumps([
        {"slug": "small-lake", "areaHa": 99.99},
        {"slug": "lake-threshold", "areaHa": 100},
        {"slug": "lake-large", "areaHa": 500},
        {"slug": "lake-missing"},
    ]), encoding="utf-8")
    monkeypatch.setattr(majors, "RIVERS", rivers)
    monkeypatch.setattr(majors, "LAKES", lakes)
    monkeypatch.setattr(majors, "OUT", output)

    majors.main()

    assert [water["slug"] for water in json.loads(output.read_text(encoding="utf-8"))] == [
        "river-threshold",
        "river-large",
        "lake-threshold",
        "lake-large",
    ]
