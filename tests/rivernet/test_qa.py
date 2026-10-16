import json

from _factory import REL, RIVER, box, make_extract
from rivernet.courses import build_courses
from rivernet.graph import build_graph
from rivernet.planar import PolygonIndex
from rivernet.qa import qa_report, write_qa


def run(ex):
    wg = build_graph(ex)
    cs = build_courses(wg, ex)
    return wg, cs, qa_report(wg, cs, ex)


def test_counts_and_km_totals():
    ex = make_extract([(1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER)])
    wg, cs, rep = run(ex)
    assert rep["courses_total"] == 1
    assert rep["km_total"] == round(cs[0].length_m / 1000, 1)
    assert rep["graph"] == {"nodes": 2, "edges": 1}
    assert rep["synthetic_connectors"] == {"count": 0, "total_km": 0.0, "max_gap_m": 0.0}


def test_cycles_are_reported():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
        (2, [(2, 25.01, 45.0), (3, 25.02, 45.0)], RIVER),
        (3, [(3, 25.02, 45.0), (2, 25.01, 45.0)], RIVER),
    ])
    _wg, _cs, rep = run(ex)
    assert rep["cycles_total"] == 1 and rep["cycles"][0]["size"] == 2


def test_synthetic_gaps_are_summarised_and_excluded_from_max_segment():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.01127, 45.0), (4, 25.02, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
    )
    _wg, _cs, rep = run(ex)
    assert rep["synthetic_connectors"]["count"] == 1
    assert 95 < rep["synthetic_connectors"]["max_gap_m"] < 105
    assert rep["max_segment_m_overall"] > 700  # the real 787 m segments, not the 100 m gap
    assert rep["courses_with_qa_flags"]["has_synthetic"] == 1


def test_relation_splits_listed():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.05, 45.0), (4, 25.06, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
    )
    _wg, _cs, rep = run(ex)
    assert rep["relation_splits"] == ["rel:10:1", "rel:10:2"]


def test_inland_sink_vs_border_vs_danube():
    # country polygon whose eastern edge passes 1 km east of the first outlet
    country = {"boundary": "administrative", "admin_level": "2"}
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], {"waterway": "river", "name": "Râul A"}),
            (2, [(3, 25.0, 46.0), (4, 25.01, 46.0)], {"waterway": "river", "name": "Râul B"}),
        ],
        areas=[("r1", country, box(24.0, 44.0, 25.0213, 47.0))],  # ~1 km east of node 2/4... not of node 4's lat? same lon
    )
    _wg, _cs, rep = run(ex)
    # both outlets are ~1 km from the border -> not inland
    assert rep["sinks_inland_total"] == 0
    # without a country polygon both are reported
    wg = build_graph(ex)
    assert qa_report(wg, build_courses(wg, ex))["sinks_inland_total"] == 2
    # a river ending on the Danube course is not an inland sink
    ex2 = make_extract([
        (1, [(1, 24.0, 44.0), (2, 25.0, 44.0)], {"waterway": "river", "name": "Dunărea"}),
        (2, [(3, 24.5, 44.01), (4, 24.5, 44.001)], {"waterway": "river", "name": "Râul C"}),
    ])
    wg2 = build_graph(ex2)
    rep2 = qa_report(wg2, build_courses(wg2, ex2))
    assert [s["course_id"].split(":")[1] for s in rep2["sinks_inland"]] == ["dunarea"]


def test_write_qa_is_deterministic_json(tmp_path):
    ex = make_extract([(1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER)])
    wg = build_graph(ex)
    rep = qa_report(wg, build_courses(wg, ex))
    p = tmp_path / "d" / "qa.json"
    write_qa(p, rep)
    first = p.read_text(encoding="utf-8")
    write_qa(p, rep)
    assert p.read_text(encoding="utf-8") == first
    assert json.loads(first)["courses_total"] == 1


def test_boundary_distance():
    poly = PolygonIndex(box(25.0, 45.0, 25.1, 45.1))
    inside_near = poly.boundary_distance_m(25.0005, 45.05, 2000)
    assert 30 < inside_near < 50
    assert poly.boundary_distance_m(25.05, 45.05, 2000) == float("inf")
