import pytest

from rivernet.geodesy import vincenty_m
from rivernet.lr import Line, vertex_measures

COORDS = [(25.0, 45.0), (25.01, 45.0), (25.01, 45.01), (25.02, 45.01)]


def test_vertex_measures_are_cumulative_and_monotonic():
    vm = vertex_measures(COORDS)
    assert vm[0] == 0.0
    assert all(b >= a for a, b in zip(vm, vm[1:]))
    assert abs(vm[1] - vincenty_m(25.0, 45.0, 25.01, 45.0)) < 1e-6


def test_line_needs_two_vertices():
    with pytest.raises(ValueError):
        Line.from_coords([(25.0, 45.0)])


def test_point_at_and_substring_hit_requested_measures():
    line = Line.from_coords(COORDS)
    m_from, m_to = line.length_m * 0.2, line.length_m * 0.8
    sub = line.substring(m_from, m_to)
    start, end = sub[0], sub[-1]
    # the sub-line's own length equals the requested span (<= 1 cm)
    total = sum(vincenty_m(sub[i][0], sub[i][1], sub[i + 1][0], sub[i + 1][1]) for i in range(len(sub) - 1))
    assert abs(total - (m_to - m_from)) < 0.01
    # end points sit exactly at the requested measures
    assert abs(line.locate(*start)[0] - m_from) < 0.01
    assert abs(line.locate(*end)[0] - m_to) < 0.01
    # interior vertices of the line between the measures are kept
    assert (25.01, 45.0) in sub and (25.01, 45.01) in sub


def test_substring_whole_line_and_clamping():
    line = Line.from_coords(COORDS)
    whole = line.substring(-5, line.length_m + 5)
    assert whole[0] == COORDS[0] and whole[-1] == COORDS[-1]
    assert len(whole) == len(COORDS)
    with pytest.raises(ValueError):
        line.substring(10, 5)


def test_substring_of_zero_span_has_two_points():
    line = Line.from_coords(COORDS)
    sub = line.substring(100.0, 100.0)
    assert len(sub) == 2 and sub[0] == sub[1]


def test_locate_off_line_returns_perpendicular_foot():
    line = Line.from_coords([(25.0, 45.0), (25.02, 45.0)])
    # a point 100 m north of the middle of an east-west line
    mid_lon = 25.01
    lat = 45.0 + 100.0 / 111141.0
    m, d = line.locate(mid_lon, lat)
    assert abs(m - line.length_m / 2) < 0.5
    assert abs(d - 100.0) < 0.5


def test_locate_clamps_beyond_the_ends():
    line = Line.from_coords([(25.0, 45.0), (25.02, 45.0)])
    m, d = line.locate(24.99, 45.0)
    assert m == 0.0 and d > 700
    m, d = line.locate(25.05, 45.0)
    assert abs(m - line.length_m) < 1e-6


def test_point_at_round_trips_with_locate():
    line = Line.from_coords(COORDS)
    for frac in (0.0, 0.13, 0.5, 0.77, 1.0):
        m = line.length_m * frac
        lon, lat = line.point_at(m)
        got, dist = line.locate(lon, lat)
        assert abs(got - m) < 0.01 and dist < 0.01
