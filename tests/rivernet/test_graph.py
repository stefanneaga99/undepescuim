from rivernet.extract_schema import Extract, Meta, Way
from rivernet.geodesy import line_length_m, vincenty_m
from rivernet.graph import build_graph


def make_extract(ways):
    """ways: list of (way_id, [(node_id, lon, lat), ...], tags)."""
    meta = Meta(1, "test", None, None, None, None, None)
    ex = Extract(meta=meta)
    for wid, pts, tags in ways:
        ex.ways[wid] = Way(
            id=wid,
            nodes=tuple(p[0] for p in pts),
            coords=tuple((p[1], p[2]) for p in pts),
            tags=tags,
        )
    return ex


RIVER = {"waterway": "river", "name": "Râul Mare"}


def test_vincenty_known_distances():
    # one degree of longitude on the equator = 2*pi*a/360
    assert abs(vincenty_m(0, 0, 1, 0) - 111319.49) < 0.05
    # one degree of latitude near 45 deg ~ 111131.7 m
    assert abs(vincenty_m(25, 44.5, 25, 45.5) - 111131.7) < 5
    assert vincenty_m(25, 45, 25, 45) == 0.0
    # symmetric, and the polyline length is the sum of its parts
    pts = [(25.0, 45.0), (25.1, 45.0), (25.1, 45.1)]
    assert abs(vincenty_m(*pts[0], *pts[1]) - vincenty_m(*pts[1], *pts[0])) < 1e-6
    assert abs(line_length_m(pts) - vincenty_m(*pts[0], *pts[1]) - vincenty_m(*pts[1], *pts[2])) < 1e-6


def test_y_confluence_degrees_and_directions():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (2, 25.1, 45.1)], RIVER),          # left tributary -> 2
        (2, [(3, 25.2, 45.0), (2, 25.1, 45.1)], RIVER),          # right tributary -> 2
        (3, [(2, 25.1, 45.1), (4, 25.1, 45.2)], RIVER),          # main stem 2 -> 4
    ])
    wg = build_graph(ex)
    assert wg.node_count == 4 and wg.edge_count == 3
    assert wg.g.degree(2) == 3
    assert [e[0] for e in wg.in_edges(2)] == [1, 3]
    assert [e[1] for e in wg.out_edges(2)] == [4]
    assert wg.out_edges(1)[0][1] == 2  # direction follows the way


def test_shared_inner_node_splits_both_ways():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (5, 25.1, 45.1), (2, 25.2, 45.2)], RIVER),
        (2, [(3, 25.0, 45.2), (5, 25.1, 45.1), (4, 25.2, 45.0)], RIVER),
    ])
    wg = build_graph(ex)
    assert wg.edge_count == 4
    assert set(wg.edge_ids()) == {"1:0", "1:1", "2:0", "2:1"}
    assert wg.g.degree(5) == 4


def test_crossing_without_shared_node_is_not_a_junction():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (2, 25.2, 45.2)], RIVER),
        (2, [(3, 25.0, 45.2), (4, 25.2, 45.0)], RIVER),  # geometrically crosses way 1
    ])
    wg = build_graph(ex)
    assert wg.edge_count == 2 and wg.node_count == 4
    assert all(wg.g.degree(n) == 1 for n in wg.g.nodes)


def test_only_flow_waterways_are_included():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (2, 25.1, 45.0)], {"waterway": "dam"}),
        (2, [(2, 25.1, 45.0), (3, 25.2, 45.0)], {"waterway": "stream"}),
        (3, [(3, 25.2, 45.0), (4, 25.3, 45.0)], {"highway": "path"}),
    ])
    wg = build_graph(ex)
    assert list(wg.edge_ids()) == ["2:0"]


def test_edge_attributes_and_length():
    ex = make_extract([(7, [(1, 25.0, 45.0), (2, 25.1, 45.0)],
                        {"waterway": "river", "name": "Râul Mare", "wikidata": "Q1",
                         "intermittent": "yes", "tunnel": "culvert"})])
    wg = build_graph(ex)
    (u, v, k, d), = wg.out_edges(1)
    assert (u, v, k) == (1, 2, "7:0")
    assert d["name"] == "Râul Mare" and d["name_key"] == "mare"
    assert d["wikidata"] == "Q1" and d["intermittent"] is True and d["tunnel"] == "culvert"
    assert d["way_id"] == 7 and d["seq"] == 0
    expected = vincenty_m(25.0, 45.0, 25.1, 45.0)
    assert abs(d["length_m"] - expected) / expected < 0.001
    assert wg.node_coord(2) == (25.1, 45.0)


def test_edges_by_name_key():
    ex = make_extract([
        (1, [(1, 25.0, 45.0), (2, 25.1, 45.0)], {"waterway": "river", "name": "Râul Olt"}),
        (2, [(2, 25.1, 45.0), (3, 25.2, 45.0)], {"waterway": "river", "name": "Olt"}),
        (3, [(4, 26.0, 45.0), (5, 26.1, 45.0)], {"waterway": "river", "name": "Jiu"}),
    ])
    wg = build_graph(ex)
    assert sorted(e[2] for e in wg.edges_by_name_key("olt")) == ["1:0", "2:0"]
    assert wg.edges_by_name_key("nope") == []


def test_construction_is_deterministic_regardless_of_insertion_order():
    a = [(2, [(2, 25.1, 45.0), (3, 25.2, 45.0)], RIVER), (1, [(1, 25.0, 45.0), (2, 25.1, 45.0)], RIVER)]
    g1 = build_graph(make_extract(a))
    g2 = build_graph(make_extract(list(reversed(a))))
    assert list(g1.g.edges(keys=True)) == list(g2.g.edges(keys=True))
    assert list(g1.g.nodes) == list(g2.g.nodes)


def test_ways_with_mismatched_coords_are_skipped():
    ex = make_extract([(1, [(1, 25.0, 45.0), (2, 25.1, 45.0)], RIVER)])
    ex.ways[1] = Way(id=1, nodes=(1, 2), coords=((25.0, 45.0),), tags=RIVER)
    assert build_graph(ex).edge_count == 0
