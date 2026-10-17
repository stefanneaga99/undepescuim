from __future__ import annotations

import gzip
import json

import pytest

from _factory import box, make_extract
from rivernet import hidrografie as H
from rivernet.extract_schema import load_extract
from rivernet.fetch_input import sha256_file

# ---------------------------------------------------------------- names/codes


@pytest.mark.parametrize("code,parent", [
    ("RO12-1-17-24-3-0-0", "RO12-1-17-24-0-0-0"),
    ("RO12-1-17-24-0-0-0", "RO12-1-17-0-0-0-0"),
    ("RO8-1-97-0-0-0-0", "RO8-1-0-0-0-0-0"),
    ("RO1-1-1-0a-0-0-0", "RO1-1-1-0-0-0-0"),  # lettered side branch is a level of its own
    ("RO8-1-0-0-0-0-0", None),  # main river of the basin
    ("RO14-1-0-0-0-0-0", None),
])
def test_parent_code(code, parent):
    assert H.parent_code(code) == parent


def test_split_names_parenthetical_aliases_and_dupes():
    assert H.split_names("Baboia (Eruga, Baboias)", "", None) == ["Baboia", "Eruga", "Baboias"]
    assert H.split_names("Viseu (Borsa)", "VISEU") == ["Viseu", "Borsa"]
    assert H.split_names("Pârâul Şes", "Topa") == ["Pârâul Șes", "Topa"]  # cedilla repaired
    assert H.split_names("", None) == []


def test_join_parts_bridges_small_gaps_and_drops_far_parts():
    a = [(0.0, 0.0), (100.0, 0.0)]
    b = [(150.0, 0.0), (400.0, 0.0)]  # 50 m gap -> joined
    far = [(5000.0, 0.0), (5100.0, 0.0)]
    coords, dropped = H._join_parts([a, b])
    assert coords == [(0.0, 0.0), (100.0, 0.0), (150.0, 0.0), (400.0, 0.0)] and not dropped
    coords, dropped = H._join_parts([a, b, far])
    assert coords[-1] == (400.0, 0.0) and dropped
    touching, _ = H._join_parts([a, [(100.0, 0.0), (200.0, 0.0)]])
    assert touching == [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]  # shared vertex not repeated
    assert H._join_parts([[(1.0, 1.0)]]) == ([], False)


# -------------------------------------------------------------- normalisation

# EPSG:3844 false origin (500000, 500000) is lon 25, lat 46
ATTRS = {"objectid_1": 7, "codcadas_1": "RO8-1-97-0-0-0-0", "denumire": "Sâmbata", "denumire2": "",
         "denumirein": "", "canal": 0}


def test_normalise_rows_tags_rounding_and_skips():
    straight = [[(500000.0 + 10 * i, 500000.0) for i in range(101)]]  # 1 km, colinear
    rows = [
        (ATTRS, straight),
        ({**ATTRS, "objectid_1": 8, "codcadas_1": "RO8-1-98-0-0-0-0", "denumire": "Canal X (Y)", "canal": 1}, straight),
        ({**ATTRS, "objectid_1": 9, "denumire": ""}, straight),  # nameless -> skipped
        ({**ATTRS, "objectid_1": 10, "codcadas_1": ""}, straight),  # no code -> skipped
        ({**ATTRS, "objectid_1": 11}, [[(500000.0, 500000.0)]]),  # degenerate -> skipped
    ]
    out = list(H.normalise_rows(rows))
    assert [r["id"] for r in out] == [7, 8]
    r = out[0]
    assert r["t"] == "way" and r["nodes"] == []
    assert r["tags"] == {"waterway": "river", "name": "Sâmbata", "ref": "RO8-1-97-0-0-0-0"}
    assert len(r["coords"]) == 2  # colinear vertices simplified away
    assert r["coords"][0] == pytest.approx([25.0, 46.0], abs=3e-3)  # incl. the Pulkovo->WGS84 datum shift
    assert all(len(str(v).split(".")[-1]) <= H.COORD_DP for c in r["coords"] for v in c)
    assert out[1]["tags"]["waterway"] == "canal" and out[1]["tags"]["alt_name"] == "Y"


def test_write_extract_is_deterministic_and_loadable(tmp_path):
    meta = {"t": "meta", "schema": 1, "source": "anar-hidrografie", "osm_timestamp": "2025-02-12"}
    ways = [
        {"t": "way", "id": 2, "nodes": [], "coords": [[25.0, 46.0], [25.1, 46.0]], "tags": {"name": "B", "ref": "RO1-1-2-0-0-0-0"}},
        {"t": "way", "id": 1, "nodes": [], "coords": [[25.0, 46.1], [25.1, 46.1]], "tags": {"name": "A", "ref": "RO1-1-1-0-0-0-0"}},
    ]
    a, b = tmp_path / "a.jsonl.gz", tmp_path / "b.jsonl.gz"
    assert H.write_extract(a, meta, ways) == 2
    H.write_extract(b, meta, list(reversed(ways)))
    assert a.read_bytes() == b.read_bytes()
    ex = load_extract(a)
    assert sorted(ex.ways) == [1, 2] and ex.meta.source == "anar-hidrografie"


def test_shapefile_roundtrip_through_cli(tmp_path):
    shapefile = pytest.importorskip("shapefile")
    shp = tmp_path / "CursuriApaRauri"
    w = shapefile.Writer(str(shp), shapeType=shapefile.POLYLINE, encoding="utf-8")
    for name, typ, size in [("objectid_1", "N", 10), ("codcadas_1", "C", 40), ("denumire", "C", 80),
                            ("denumire2", "C", 80), ("denumirein", "C", 80), ("canal", "N", 5)]:
        w.field(name, typ, size=size)
    w.line([[(500000.0, 500000.0), (500500.0, 500300.0), (501000.0, 500000.0)]])
    w.record(3, "RO8-1-97-0-0-0-0", "Sâmbata (Sambata Mare)", "", "", 0)
    w.close()
    zipf = tmp_path / "res.zip"
    zipf.write_bytes(b"zip")
    out = tmp_path / "anar.jsonl.gz"
    from rivernet.__main__ import main

    assert main(["normalise-hidrografie", "--shp", str(shp) + ".shp", "--zip", str(zipf),
                 "--modified", "2025-02-12", "--out", str(out)]) == 0
    ex = load_extract(out)
    assert ex.meta.pbf_sha256 == sha256_file(zipf) and ex.meta.osm_timestamp == "2025-02-12"
    (way,) = ex.ways.values()
    assert way.tags["name"] == "Sâmbata" and way.tags["alt_name"] == "Sambata Mare"
    assert len(way.coords) == 3


# ------------------------------------------------------------- course records

LAT = 46.0
PARENT = "RO8-1-0-0-0-0-0"
CHILD = "RO8-1-5-0-0-0-0"
GRAND = "RO8-1-5-2-0-0-0"


def anar_extract():
    # parent flows west -> east along LAT; child joins it at lon 24.2 from the north
    # but is digitised mouth -> source (must be flipped); grandchild joins the child.
    parent = [(i, round(24.0 + 0.01 * i, 4), LAT) for i in range(41)]
    child = [(i, 24.2, round(LAT + 0.01 * (i), 4)) for i in range(11)]  # starts AT the parent
    grand = [(i, round(24.1 + 0.01 * i, 4), LAT + 0.05) for i in range(11)]  # ends at the child (24.2, 46.05)
    return make_extract([
        (1, parent, {"waterway": "river", "name": "Mureș", "ref": PARENT}),
        (2, child, {"waterway": "river", "name": "Sâmbata", "alt_name": "Sâmbăta Mare", "ref": CHILD}),
        (3, grand, {"waterway": "river", "name": "Valea Lisei", "ref": GRAND, "fixme": "multipart"}),
    ])


COUNTIES = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"name": "Alba"}, "geometry": box(23.9, 45.9, 24.25, 46.2)},
    {"type": "Feature", "properties": {"name": "Sibiu"}, "geometry": box(24.25, 45.9, 24.5, 46.2)},
]}


def test_build_records_orientation_topology_and_counties():
    recs = {r["course_id"]: r for r in H.build_records(anar_extract(), COUNTIES)}
    assert list(recs) == sorted(recs)
    child = recs["anar:" + CHILD]
    # flipped: the outlet (last vertex) is the one on the parent
    assert child["geometry"]["coordinates"][-1] == [24.2, LAT]
    assert child["receives_into"] == "anar:" + PARENT and child["source"] == "anar"
    assert child["aliases"] == ["Sâmbăta Mare"] and child["stem_key"] == "sambat"
    assert child["vertex_m"][0] == 0.0 and child["vertex_m"][-1] == child["length_m"]
    (j,) = child["junctions"]  # grandchild outlet on the child
    assert j["tributary_course_id"] == "anar:" + GRAND and j["m"] == pytest.approx(child["length_m"] * 0.5, rel=0.02)
    parent = recs["anar:" + PARENT]
    assert parent["receives_into"] is None
    (pj,) = parent["junctions"]
    assert pj["tributary_course_id"] == "anar:" + CHILD
    assert pj["m"] == pytest.approx(parent["length_m"] * 0.5, rel=0.01)
    assert [c["county"] for c in parent["counties"]] == ["Alba", "Sibiu"]
    assert recs["anar:" + GRAND]["qa"] == ["fallback_source", "multipart_dropped"]


def test_build_records_keep_filter_and_far_tributary():
    ex = anar_extract()
    only = H.build_records(ex, COUNTIES, keep=lambda names, counties: "Mureș" in names)
    assert [r["course_id"] for r in only] == ["anar:" + PARENT]
    assert only[0]["junctions"][0]["tributary_course_id"] == "anar:" + CHILD  # junctions see every course
    # a tributary whose outlet is far from its parent is not a junction
    far = make_extract([
        (1, [(i, 24.0 + 0.01 * i, LAT) for i in range(11)], {"name": "Mureș", "ref": PARENT}),
        (2, [(i, 24.05, LAT + 0.1 + 0.01 * i) for i in range(5)], {"name": "Departe", "ref": CHILD}),
    ])
    recs = {r["course_id"]: r for r in H.build_records(far, None)}
    assert recs["anar:" + PARENT]["junctions"] == [] and recs["anar:" + CHILD]["counties"] == []


def test_index_entries_cover_every_course():
    idx = H.index_entries(anar_extract())
    assert idx["anar:" + CHILD] == ["sambata", "sambata mare"]
    assert idx["anar:" + GRAND] == ["valea lisei", "lisei"]


def test_wanted_by_county_and_osm_coverage():
    waters = [
        {"slug": "a", "name": "Valea Sâmbetei", "judet": "Brașov", "subtype": "rau"},
        {"slug": "b", "name": "Râul Lisa", "judet": "Alba", "subtype": "rau"},
        {"slug": "c", "name": "Lacul X", "judet": "Alba", "subtype": "lac"},  # not a river
        {"slug": "d", "name": "Râul Cibin", "judet": "Sibiu", "subtype": "rau"},
    ]
    parsed = {"b": {"from": {"kind": "SOURCE"}, "to": {"kind": "CONFLUENCE", "target": "Pârâul Tărcăița"}}}
    osm = [{"course_id": "name:cibin:n1", "name": "Cibin", "aliases": [], "counties": [{"county": "Sibiu"}]},
           {"course_id": "anar:x", "source": "anar", "name": "Lisa", "counties": [{"county": "Alba"}]}]
    covered = H.osm_coverage(osm)
    assert covered == {("cibin", "sibiu"): 0.0}
    keep = H.wanted(waters, parsed, covered)
    assert keep(["Lisa"], set()) and keep(["Lisa"], {"Alba"}) and not keep(["Lisa"], {"Cluj"})
    assert keep(["Tarcaita"], {"Alba"})  # a confluence target of an Alba water
    assert keep(["Valea Sâmbetei"], {"Brașov"})
    assert not keep(["Cibin"], {"Sibiu"})  # OSM already answers it there
    assert not keep(["X"], {"Alba"}) and not keep(["Nimic"], set())


# ----------------------------------------------------------------------- merge


def write_gz(path, recs):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def test_merge_courses_replaces_old_fallback_records(tmp_path):
    p = tmp_path / "courses.jsonl.gz"
    write_gz(p, [{"course_id": "name:b:n1"}, {"course_id": "anar:OLD"}, {"course_id": "rel:5"}])
    H.merge_courses(p, [{"course_id": "anar:RO2"}, {"course_id": "anar:RO1"}])
    assert [r["course_id"] for r in read_gz(p)] == ["name:b:n1", "rel:5", "anar:RO1", "anar:RO2"]
    first = p.read_bytes()
    H.merge_courses(p, [{"course_id": "anar:RO1"}, {"course_id": "anar:RO2"}])
    assert p.read_bytes() == first


def test_merge_index(tmp_path):
    p = tmp_path / "course_index.json"
    H.merge_index(p, {"anar:A": ["a"]})  # creates the file
    p.write_text(json.dumps({"name:x:n1": ["x"], "anar:OLD": ["old"]}), encoding="utf-8")
    H.merge_index(p, {"anar:A": ["a"]})
    assert json.loads(p.read_text(encoding="utf-8")) == {"anar:A": ["a"], "name:x:n1": ["x"]}


# ------------------------------------------------------------------------- CLI


def fallback_env(tmp_path):
    ex = tmp_path / "anar.jsonl.gz"
    meta = {"t": "meta", "schema": 1, "source": "anar-hidrografie"}
    ways = [{"t": "way", "id": w.id, "nodes": [], "coords": [list(c) for c in w.coords], "tags": dict(w.tags)}
            for w in anar_extract().ways.values()]
    H.write_extract(ex, meta, ways)
    courses = tmp_path / "courses.jsonl.gz"
    write_gz(courses, [{"course_id": "name:olt:n1", "name": "Olt", "aliases": [], "counties": [{"county": "Sibiu"}]}])
    waters = tmp_path / "waters.json"
    waters.write_text(json.dumps([{"slug": "w", "name": "Pârâul Sâmbatei", "judet": "Alba", "subtype": "rau"}]), encoding="utf-8")
    parsed = tmp_path / "parsed.jsonl"
    parsed.write_text(json.dumps({"slug": "w", "spec": {"from": {"kind": "SOURCE"},
                                                        "to": {"kind": "CONFLUENCE", "target": "Mureș"}}}) + "\n", encoding="utf-8")
    counties = tmp_path / "counties.geojson"
    counties.write_text(json.dumps(COUNTIES), encoding="utf-8")
    args = ["--extract", str(ex), "--courses", str(courses), "--course-index", str(tmp_path / "ci.json"),
            "--waters", str(waters), "--parsed", str(parsed), "--counties", str(counties),
            "--manifest", str(tmp_path / "manifest.json")]
    return args, ex, courses


def test_cli_fallback_end_to_end(tmp_path, capsys):
    from rivernet.__main__ import main

    args, _, courses = fallback_env(tmp_path)
    assert main(["fallback", *args]) == 0
    ids = [r["course_id"] for r in read_gz(courses)]
    assert ids == ["name:olt:n1", "anar:" + PARENT, "anar:" + CHILD]  # Lisa is not wanted
    idx = json.loads((tmp_path / "ci.json").read_text(encoding="utf-8"))
    assert set(idx) == {"anar:" + PARENT, "anar:" + CHILD, "anar:" + GRAND}
    assert json.loads(capsys.readouterr().out)["anar_courses"] == 2


def test_cli_fallback_missing_inputs(tmp_path):
    args, ex, courses = fallback_env(tmp_path)
    courses.unlink()
    assert H.cli_fallback(args) == 1
    ex.unlink()
    (tmp_path / "src.jsonl.gz").write_bytes(b"not it")
    (tmp_path / "manifest.json").write_text(json.dumps({"asset": {
        "url": (tmp_path / "src.jsonl.gz").as_uri(), "sha256": "0" * 64}}), encoding="utf-8")
    assert H.cli_fallback(args) == 1  # sha mismatch refused, nothing downloaded
    assert not ex.exists()


def test_cli_fallback_downloads_pinned_asset(tmp_path):
    args, ex, _ = fallback_env(tmp_path)
    src = tmp_path / "src.jsonl.gz"
    src.write_bytes(ex.read_bytes())
    ex.unlink()
    (tmp_path / "manifest.json").write_text(json.dumps({"asset": {
        "url": src.as_uri(), "sha256": sha256_file(src)}}), encoding="utf-8")
    assert H.cli_fallback(args) == 0 and ex.exists()


def test_committed_fallback_manifest_is_pinned():
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / "data/rivernet/fallback_manifest.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    assert m["schema"] == 1 and m["licence"] == "CC-BY-4.0"
    for sec in ("resource", "asset"):
        assert m[sec]["url"].startswith("https://") and len(m[sec]["sha256"]) == 64
