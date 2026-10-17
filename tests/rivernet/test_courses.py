from _factory import REL, RIVER, box, make_extract
from rivernet.courses import build_courses, county_intervals
from rivernet.geodesy import vincenty_m
from rivernet.graph import build_graph
from rivernet.lr import Line
from rivernet.planar import PolygonIndex


def courses_for(ex):
    return build_courses(build_graph(ex), ex)


def by_id(courses):
    return {c.course_id: c for c in courses}


def d(lon1, lat1, lon2, lat2):
    return vincenty_m(lon1, lat1, lon2, lat2)


def test_relation_with_braid_takes_longest_path_and_reports_dropped_length():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(2, 25.01, 45.0), (4, 25.02, 45.0)], RIVER),  # short arm
            (3, [(2, 25.01, 45.0), (3, 25.015, 45.003), (4, 25.02, 45.0)], RIVER),  # long arm
        ],
        rels=[(10, REL, [(1, ""), (2, ""), (3, "")])],
    )
    (c,) = courses_for(ex)
    assert c.course_id == "rel:10"
    assert c.way_ids == [1, 3]
    assert abs(c.braids_dropped_m - d(25.01, 45.0, 25.02, 45.0)) < 0.5
    assert c.relation_id == 10 and c.name == "Râul Test" and c.name_key == "test"
    assert c.qa == []


def test_relation_with_small_gap_gets_one_gap_bridge():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.01127, 45.0), (4, 25.02, 45.0)], RIVER),  # ~100 m downstream of way 1
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
    )
    (c,) = courses_for(ex)
    assert len(c.synthetic) == 1
    s = c.synthetic[0]
    assert s["kind"] == "gap_bridge" and 95 < s["gap_m"] < 105
    assert "has_synthetic" in c.qa
    assert abs((s["m_to"] - s["m_from"]) - s["gap_m"]) < 0.2
    assert c.way_ids == [1, 2]


def test_relation_with_big_gap_through_a_reservoir_is_bridged():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.05, 45.0), (4, 25.06, 45.0)], RIVER),  # ~3.1 km gap
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
        areas=[("w9", {"natural": "water", "water": "reservoir"}, box(25.005, 44.99, 25.055, 45.01))],
    )
    (c,) = courses_for(ex)
    assert [s["kind"] for s in c.synthetic] == ["reservoir_crossing"]
    assert c.synthetic[0]["gap_m"] > 3000


def test_relation_with_big_gap_and_no_reservoir_is_split():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.05, 45.0), (4, 25.06, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
    )
    cs = courses_for(ex)
    assert [c.course_id for c in cs] == ["rel:10:1", "rel:10:2"]
    assert all("relation_split" in c.qa for c in cs)
    assert all(not c.synthetic for c in cs)


def test_reservoir_must_touch_both_ends():
    ex = make_extract(
        [
            (1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(3, 25.05, 45.0), (4, 25.06, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, ""), (2, "")])],
        areas=[("w9", {"water": "lake"}, box(24.99, 44.99, 25.012, 45.01))],  # covers only the upstream end
    )
    assert len(courses_for(ex)) == 2


def test_name_course_with_tributary_has_one_junction_at_the_right_measure():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0), (3, 25.02, 45.0)], {"waterway": "river", "name": "Râul Mare"}),
            (2, [(5, 25.01, 45.01), (2, 25.01, 45.0)], {"waterway": "stream", "name": "Pârâul Mic"}),
        ]
    )
    cs = by_id(courses_for(ex))
    assert set(cs) == {"name:mare:n3", "name:mic:n2"}
    main, trib = cs["name:mare:n3"], cs["name:mic:n2"]
    assert [j["node"] for j in main.junctions] == [2]
    j = main.junctions[0]
    assert j["tributary_course_id"] == "name:mic:n2" and j["side"] == "in"
    assert abs(j["m"] - d(25.0, 45.0, 25.01, 45.0)) < 0.2
    assert trib.receives_into == "name:mare:n3"
    assert main.receives_into is None


def test_unnamed_inflow_gives_a_junction_with_null_tributary():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0), (3, 25.02, 45.0)], {"waterway": "river", "name": "Râul Mare"}),
            (2, [(5, 25.01, 45.01), (2, 25.01, 45.0)], {"waterway": "stream"}),
        ]
    )
    (c,) = courses_for(ex)
    assert c.junctions[0]["tributary_course_id"] is None


def test_measures_are_monotonic_and_end_at_length():
    ex = make_extract(
        [(1, [(1, 25.0, 45.0), (2, 25.01, 45.002), (3, 25.02, 45.0), (4, 25.03, 45.004)], RIVER)]
    )
    (c,) = courses_for(ex)
    rec = c.to_record()
    vm = rec["vertex_m"]
    assert vm[0] == 0.0 and all(b >= a for a, b in zip(vm, vm[1:]))
    assert vm[-1] == rec["length_m"]
    assert len(vm) == len(rec["geometry"]["coordinates"])
    assert rec["course_id"] == "name:test:n4"
    # record coordinates are 6-decimal numbers
    assert all(round(x, 6) == x for pt in rec["geometry"]["coordinates"] for x in pt)


def test_cycle_is_broken_and_flagged():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(2, 25.01, 45.0), (8, 25.012, 45.004), (3, 25.015, 45.001)], RIVER),  # longer arc
            (3, [(3, 25.015, 45.001), (2, 25.01, 45.0)], RIVER),  # short edge loops back
            (4, [(3, 25.015, 45.001), (4, 25.03, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, ""), (2, ""), (3, ""), (4, "")])],
    )
    (c,) = courses_for(ex)
    assert "cycle_broken" in c.qa
    assert c.nodes[0] == 1 and c.nodes[-1] == 4


def test_side_stream_members_are_not_part_of_the_relation_course():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], RIVER),
            (2, [(2, 25.01, 45.0), (3, 25.02, 45.0)], RIVER),
        ],
        rels=[(10, REL, [(1, "main_stream"), (2, "side_stream")])],
    )
    cs = courses_for(ex)
    rel = [c for c in cs if c.relation_id == 10][0]
    assert rel.way_ids == [1]
    # the side stream falls back to a name course
    assert any(c.course_id.startswith("name:test:") for c in cs)


def test_missing_relation_member_is_flagged():
    ex = make_extract(
        [(1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], RIVER)],
        rels=[(10, REL, [(1, ""), (999, "")])],
    )
    (c,) = courses_for(ex)
    assert "relation_member_missing" in c.qa


def test_counties_are_intervals_of_the_course():
    ex = make_extract(
        [(1, [(1, 25.0, 45.0), (2, 25.02, 45.0), (3, 25.04, 45.0)], RIVER)],
        areas=[
            ("r1", {"boundary": "administrative", "admin_level": "4", "name": "Județul Alba"}, box(24.9, 44.9, 25.02, 45.1)),
            ("r2", {"boundary": "administrative", "admin_level": "4", "name": "Județul Sibiu"}, box(25.02, 44.9, 25.2, 45.1)),
            ("r3", {"boundary": "administrative", "admin_level": "8", "name": "Comuna X"}, box(24.9, 44.9, 25.2, 45.1)),
        ],
    )
    (c,) = courses_for(ex)
    assert [x["county"] for x in c.counties] == ["Alba", "Sibiu"]
    half = c.length_m / 2
    assert c.counties[0]["m_from"] == 0.0 and abs(c.counties[0]["m_to"] - half) < 0.5
    assert abs(c.counties[1]["m_from"] - half) < 0.5 and abs(c.counties[1]["m_to"] - c.length_m) < 0.2


def test_county_intervals_handles_leaving_and_reentering():
    line = Line.from_coords([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)])
    poly = PolygonIndex({"type": "MultiPolygon", "coordinates": [
        box(-0.5, -1, 0.5, 1)["coordinates"], box(2.5, -1, 3.5, 1)["coordinates"]]})
    iv = county_intervals(line, poly)
    assert len(iv) == 2
    assert iv[0][0] == 0.0 and abs(iv[0][1] - line.length_m / 6) < 1
    assert abs(iv[1][1] - line.length_m) < 1e-6
    assert county_intervals(line, PolygonIndex(box(10, 10, 11, 11))) == []


def test_unnamed_ways_do_not_become_courses():
    ex = make_extract([(1, [(1, 25.0, 45.0), (2, 25.01, 45.0)], {"waterway": "stream"})])
    assert courses_for(ex) == []


def test_output_is_deterministic_under_input_order():
    ways = [
        (3, [(2, 25.01, 45.0), (3, 25.015, 45.003), (4, 25.02, 45.0)], RIVER),
        (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], RIVER),
        (2, [(2, 25.01, 45.0), (4, 25.02, 45.0)], RIVER),
    ]
    rels = [(10, REL, [(1, ""), (2, ""), (3, "")])]
    a = [c.to_record() for c in courses_for(make_extract(ways, rels))]
    b = [c.to_record() for c in courses_for(make_extract(list(reversed(ways)), rels))]
    assert a == b


def test_partial_wikidata_does_not_split_a_river():
    # upper ways untagged, lower ways carry wikidata (Teleajen): one course
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], {"waterway": "river", "name": "Teleajen"}),
            (2, [(2, 25.01, 45.0), (3, 25.02, 45.0)], {"waterway": "river", "name": "Teleajen", "wikidata": "Q1"}),
            # a same-named river far away keeps its own course
            (3, [(7, 26.00, 46.0), (8, 26.01, 46.0)], {"waterway": "river", "name": "Teleajen"}),
        ]
    )
    cs = by_id(courses_for(ex))
    assert set(cs) == {"name:teleajen:n3", "name:teleajen:n8"}
    assert cs["name:teleajen:n3"].way_ids == [1, 2] and cs["name:teleajen:n3"].wikidata == "Q1"


def test_two_wikidata_groups_with_one_name_leave_untagged_ways_alone():
    ex = make_extract(
        [
            (1, [(1, 25.00, 45.0), (2, 25.01, 45.0)], {"waterway": "river", "name": "Bistra", "wikidata": "Q1"}),
            (2, [(5, 26.00, 46.0), (6, 26.01, 46.0)], {"waterway": "river", "name": "Bistra", "wikidata": "Q2"}),
            (3, [(2, 25.01, 45.0), (3, 25.02, 45.0)], {"waterway": "river", "name": "Bistra"}),
        ]
    )
    cs = by_id(courses_for(ex))
    assert set(cs) == {"name:bistra:n2", "name:bistra:n3", "name:bistra:n6"}
