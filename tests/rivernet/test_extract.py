import gzip
import json
from pathlib import Path

from rivernet import extract as ex
from rivernet import __main__ as cli
from rivernet.extract_schema import SCHEMA_VERSION, iter_records, load_extract

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "rivernet"
OPL = FIX / "mini.opl"
AREAS = FIX / "mini-areas.geojsonseq"


def test_unescape_opl():
    assert ex.unescape_opl("R%e2%ul%20%Mic") == "Râul Mic"
    assert ex.unescape_opl("a%2c%b%3d%c%25%") == "a,b=c%"
    assert ex.unescape_opl("plain") == "plain"


def test_parse_tags_handles_escapes_and_empty():
    assert ex.parse_tags("") == {}
    assert ex.parse_tags("a=1,b=x%20%y,c=") == {"a": "1", "b": "x y", "c": ""}


def test_parse_opl_node_way_relation():
    n = ex.parse_opl_line("n9 v1 dV x25.01 y45.02 Tplace=village")
    assert (n["kind"], n["id"], n["lon"], n["lat"], n["tags"]) == ("n", 9, 25.01, 45.02, {"place": "village"})
    w = ex.parse_opl_line("w10 v1 dV Twaterway=river Nn1,n2,n3")
    assert w["nodes"] == [1, 2, 3] and w["tags"] == {"waterway": "river"}
    r = ex.parse_opl_line("r20 v1 dV Ttype=waterway Mw10@main_stream,n3@weir,w14@")
    assert r["members"] == [("w", 10, "main_stream"), ("n", 3, "weir"), ("w", 14, "")]


def test_parse_opl_skips_blank_deleted_and_unlocated():
    assert ex.parse_opl_line("") is None
    assert ex.parse_opl_line("# comment") is None
    assert ex.parse_opl_line("w1 v1 dD Twaterway=river Nn1,n2") is None
    assert ex.parse_opl_line("n1 v1 dV T") is None


def test_filter_tags_whitelist_and_prefix():
    tags = {"name": "A", "name:en": "B", "source": "bing", "waterway": "river", "foo": "x"}
    assert ex.filter_tags(tags) == {"name": "A", "name:en": "B", "waterway": "river"}


def test_build_records_keeps_waterways_relations_and_nearby_bridges():
    records, stats = ex.build_records(OPL, AREAS)
    ways = {r["id"]: r for r in records if r["t"] == "way"}
    # w10 waterway, w14 relation member (untagged), w11 bridge next to the river
    assert set(ways) == {10, 11, 14}
    assert stats["ways"] == 3
    # w12 bridge far away and w13 plain road are dropped
    assert 12 not in ways and 13 not in ways
    w10 = ways[10]
    assert w10["nodes"] == [1, 2, 3, 4]
    assert w10["coords"][0] == [25.0, 45.0]
    assert w10["tags"] == {"name": "Râul Mic", "name:en": "Small river", "waterway": "river"}


def test_build_records_relations_nodes_and_areas():
    records, stats = ex.build_records(OPL, AREAS)
    rels = [r for r in records if r["t"] == "rel"]
    assert [r["id"] for r in rels] == [20]  # route relation and deleted one dropped
    assert rels[0]["members"][0] == {"type": "w", "ref": 10, "role": "main_stream"}
    nodes = {r["id"]: r for r in records if r["t"] == "node"}
    assert set(nodes) == {3, 9}
    assert nodes[3]["tags"] == {"name": "Prag", "waterway": "weir"}
    assert nodes[9]["tags"] == {"name": "Plopeni", "place": "village"}
    areas = {r["id"]: r for r in records if r["t"] == "area"}
    assert set(areas) == {"w100", "r101"}  # building and LineString dropped
    ring = areas["w100"]["geometry"]["coordinates"][0]
    assert ring[1] == [25.0012346, 45.0]
    assert stats == {"rels": 1, "ways": 3, "nodes": 2, "areas": 2}


def test_records_are_sorted_by_type_then_id():
    records, _ = ex.build_records(OPL, AREAS)
    order = {"rel": 0, "way": 1, "node": 2, "area": 3}
    keys = [(order[r["t"]], r["id"]) for r in records]
    assert keys == sorted(keys)


def test_write_and_load_round_trip(tmp_path):
    out = tmp_path / "x.jsonl.gz"
    stats = ex.extract(OPL, AREAS, out, osm_timestamp="2026-10-01T00:00:00Z",
                       pbf_sha256="ab" * 32, filters="w/waterway", bbox=[20, 43, 30, 48])
    assert stats["ways"] == 3
    data = load_extract(out)
    assert data.meta.schema == SCHEMA_VERSION
    assert data.meta.pbf_sha256 == "ab" * 32
    assert data.meta.bbox == (20.0, 43.0, 30.0, 48.0)
    assert data.meta.extractor_version
    assert set(data.ways) == {10, 11, 14}
    assert data.ways[10].coords[1] == (25.001, 45.001)
    assert data.rels[20].members[0].role == "main_stream"
    assert data.nodes[9].tags["place"] == "village"
    assert set(data.areas) == {"w100", "r101"}


def test_output_is_deterministic(tmp_path):
    a, b = tmp_path / "a.jsonl.gz", tmp_path / "b.jsonl.gz"
    ex.extract(OPL, AREAS, a, osm_timestamp="t")
    ex.extract(OPL, AREAS, b, osm_timestamp="t")
    assert a.read_bytes() == b.read_bytes()


def test_plain_jsonl_output_and_no_areas(tmp_path):
    out = tmp_path / "x.jsonl"
    ex.extract(OPL, None, out)
    recs = list(iter_records(out))
    assert recs[0]["t"] == "meta"
    assert not [r for r in recs if r["t"] == "area"]


def test_loader_rejects_bad_files(tmp_path):
    import pytest

    def write(name, lines):
        p = tmp_path / name
        p.write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
        return p

    with pytest.raises(ValueError):
        load_extract(write("a.jsonl", [{"t": "way", "id": 1}]))  # no meta first
    with pytest.raises(ValueError):
        load_extract(write("b.jsonl", [{"t": "meta", "schema": 99}]))
    with pytest.raises(ValueError):
        load_extract(write("c.jsonl", [{"t": "meta", "schema": 1}, {"t": "meta", "schema": 1}]))
    with pytest.raises(ValueError):
        load_extract(write("d.jsonl", [{"t": "meta", "schema": 1}, {"t": "zzz"}]))
    empty = tmp_path / "e.jsonl"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_extract(empty)


def test_grid_index_near():
    idx = ex.GridIndex()
    idx.add(25.0, 45.0)
    assert idx.near(25.0001, 45.0001, 40)  # ~14 m
    assert not idx.near(25.01, 45.0, 40)  # ~780 m


def test_geojsonseq_record_separator_prefix(tmp_path):
    p = tmp_path / "a.geojsonseq"
    feat = {"type": "Feature", "id": "w1", "properties": {"natural": "water"},
            "geometry": {"type": "Polygon", "coordinates": [[[1, 2], [3, 4], [5, 6], [1, 2]]]}}
    p.write_text("\x1e" + json.dumps(feat) + "\n", encoding="utf-8")
    assert [a["id"] for a in ex.iter_areas(p)] == ["w1"]


def test_cli_extract_end_to_end(tmp_path):
    out = tmp_path / "o.jsonl.gz"
    rc = cli.main(["extract", "--opl", str(OPL), "--areas", str(AREAS), "--out", str(out),
                   "--pbf-sha256", "cd" * 32])
    assert rc == 0
    assert load_extract(out).meta.pbf_sha256 == "cd" * 32
    with gzip.open(out, "rt", encoding="utf-8") as fh:
        assert json.loads(fh.readline())["t"] == "meta"
