from __future__ import annotations

import pytest

from _factory import box, make_extract
from rivernet import resolvers as R
from rivernet.extract_schema import Node
from rivernet.lr import Line
from rivernet.textnorm import river_key

LAT = 46.0
LONS = [24.0 + 0.05 * i for i in range(9)]  # 24.00 .. 24.40
COORDS = [(round(24.0 + 0.005 * i, 6), LAT) for i in range(81)]  # vertices every ~386 m
LINE = Line.from_coords(COORDS)
LEN = LINE.length_m


def m_at(lon):  # measure of the course at a longitude
    return LINE.locate(lon, LAT)[0]


def course(cid="name:test:n1", name="Test", **kw):
    rec = {
        "course_id": cid, "name": name, "name_key": river_key(name), "aliases": [],
        "length_m": LEN, "geometry": {"type": "LineString", "coordinates": [list(c) for c in COORDS]},
        "junctions": [], "receives_into": None, "braids_dropped_m": 0.0, "counties": [],
    }
    rec.update(kw)
    return rec


def ctx_for(courses=(), nodes=(), ways=(), areas=(), extra=None):
    ex = make_extract(list(ways), areas=list(areas))
    for n in nodes:
        ex.nodes[n.id] = n
    cs = list(courses) or [course()]
    return R.build_context(ex, cs + list(extra or []))


def place(i, name, lon, lat=LAT, kind="village"):
    return Node(i, (lon, lat), {"place": kind, "name": name})


def ep(kind, **kw):
    d = {"kind": kind, "target": None, "qualifier": "at", "locality_hint": None, "road_ref": None, "raw": ""}
    d.update(kw)
    return d


def res(spec, ctx, c=None, **kw):
    return R.resolve_endpoint(spec, c or course(), ctx, **kw)


def meas(c):
    return round(c.m)


# -------------------------------------------------------------------- helpers


def test_core_strips_generic_words():
    assert R.core("Barajul Baciu") == "baciu"
    assert R.core("Lacul de acumulare Vidraru") == "acumulare vidraru" or R.core("Lacul Vidraru") == "vidraru"
    assert R.core("Comuna Țânțăreni") == "tantareni"
    assert R.core(None) == ""


def test_ref_match():
    assert R.ref_match("DN67", "DN67D")
    assert R.ref_match("DN67D", "DN67")
    assert not R.ref_match("DN6", "DN67")
    assert not R.ref_match("DN67", "DN670")
    assert not R.ref_match("", "DN1")


# ------------------------------------------------------------ SOURCE and MOUTH


def test_source_and_mouth():
    ctx = ctx_for()
    s = res(ep("SOURCE"), ctx)
    assert (s[0].m, s[0].confidence) == (0.0, R.C_SOURCE) and R.C_SOURCE == 0.9
    mth = res(ep("MOUTH"), ctx)
    assert (mth[0].m, mth[0].confidence) == (LEN, 0.95)


def test_source_braided_lowers_confidence():
    c = course(braids_dropped_m=LEN * 0.2)
    assert res(ep("SOURCE"), ctx_for([c]), c)[0].confidence == 0.75


def test_qualifier_recorded_in_method():
    out = res(ep("SOURCE", qualifier="upstream"), ctx_for())
    assert out[0].method.endswith("|upstream") and out[0].m == 0.0


def test_unknown_and_unsupported_kinds_empty():
    ctx = ctx_for()
    assert res(ep("UNKNOWN"), ctx) == []
    assert res(ep("WHATEVER"), ctx) == []


# ----------------------------------------------------------------- CONFLUENCE


def test_confluence_outlet_into_named():
    parent = course("name:mures:n9", "Mureș")
    c = course(receives_into="name:mures:n9")
    out = res(ep("CONFLUENCE", target="Râul Mureș"), ctx_for([c], extra=[parent]), c)
    assert (out[0].m, out[0].confidence, out[0].method) == (LEN, 0.95, "outlet_into_named")


def test_confluence_outlet_into_named_without_parent_record():
    c = course(receives_into="name:mures:n9")
    out = res(ep("CONFLUENCE", target="Mureș"), ctx_for([c]), c)
    assert out and out[0].method == "outlet_into_named"


def test_confluence_tributary_junction():
    c = course(junctions=[{"node": 7, "m": 1234.5, "tributary_course_id": "name:trotus:n3", "side": "in"}])
    out = res(ep("CONFLUENCE", target="Pârâul Trotuș"), ctx_for([c]), c)
    assert (out[0].m, out[0].confidence, out[0].method) == (1234.5, 0.95, "tributary_junction")


def test_confluence_near_outlet():
    x = LONS[4]
    trib = course("name:valea:n5", "Valea",)
    trib["geometry"] = {"type": "LineString", "coordinates": [[x, LAT + 0.01], [x, LAT + 0.0003]]}
    c = course()
    out = res(ep("CONFLUENCE", target="Valea"), ctx_for([c], extra=[trib]), c)
    assert out and out[0].method == "near_outlet" and out[0].confidence == 0.8
    assert abs(out[0].m - m_at(x)) < 5 and out[0].dist_m < 50


def test_confluence_outlet_too_far():
    x = LONS[4]
    trib = course("name:valea:n5", "Valea")
    trib["geometry"] = {"type": "LineString", "coordinates": [[x, LAT + 0.01], [x, LAT + 0.01 - 0.0009]]}
    assert res(ep("CONFLUENCE", target="Valea"), ctx_for([course()], extra=[trib])) == []


def test_confluence_no_match():
    assert res(ep("CONFLUENCE", target="Nimic"), ctx_for()) == []
    assert res(ep("CONFLUENCE", target=None), ctx_for()) == []


# ------------------------------------------------------------------- LAKE / DAM


def lake(aid, name, x0, x1, tags=None):
    t = {"natural": "water", "water": "reservoir"}
    if name:
        t["name"] = name
    t.update(tags or {})
    return (aid, t, box(x0, LAT - 0.01, x1, LAT + 0.01))


def test_lake_upstream_and_downstream_named():
    ctx = ctx_for(areas=[lake("w1", "Lacul Vidraru", 24.10, 24.20)])
    up = res(ep("LAKE_UPSTREAM", target="Vidraru"), ctx)
    dn = res(ep("LAKE_DOWNSTREAM", target="Lacul Vidraru"), ctx)
    assert up[0].confidence == dn[0].confidence == 0.9
    assert abs(up[0].m - m_at(24.10)) < 5 and abs(dn[0].m - m_at(24.20)) < 5
    assert up[0].m < dn[0].m


def test_lake_unnamed_with_place():
    ctx = ctx_for(areas=[lake("w2", None, 24.10, 24.20)], nodes=[place(1, "Vidraru", 24.15, LAT + 0.02)])
    out = res(ep("LAKE_UPSTREAM", target="Vidraru"), ctx)
    assert out and out[0].confidence == 0.7


def test_lake_unnamed_two_reservoirs_is_ambiguous():
    ctx = ctx_for(areas=[lake("w2", None, 24.10, 24.15), lake("w3", None, 24.20, 24.25)],
                  nodes=[place(1, "Vidraru", 24.15, LAT + 0.02)])
    assert res(ep("LAKE_UPSTREAM", target="Vidraru"), ctx) == []


def test_lake_not_crossed():
    ctx = ctx_for(areas=[("w9", {"natural": "water", "name": "Lacul X"}, box(24.1, 47.0, 24.2, 47.1))])
    assert res(ep("LAKE_UPSTREAM", target="X"), ctx) == []


def dam_node(i, name, lon, lat=LAT):
    return Node(i, (lon, lat), {"waterway": "dam", "name": name} if name else {"waterway": "dam"})


def test_dam_named():
    ctx = ctx_for(nodes=[dam_node(1, "Barajul Baciu", 24.1)])
    out = res(ep("DAM", target="Baciu"), ctx)
    assert (out[0].confidence, out[0].method) == (0.9, "dam_named")
    assert abs(out[0].m - m_at(24.1)) < 5


def test_dam_by_place():
    ctx = ctx_for(nodes=[dam_node(1, None, 24.1), place(2, "Baciu", 24.1, LAT + 0.005)])
    out = res(ep("DAM", target="Baciu"), ctx)
    assert (out[0].confidence, out[0].method) == (0.7, "dam_by_place")


def test_dam_too_far_from_course():
    ctx = ctx_for(nodes=[dam_node(1, "Baraj Baciu", 24.1, LAT + 0.01)])
    assert res(ep("DAM", target="Baciu"), ctx) == []


# ---------------------------------------------------------------------- BRIDGE


def bridge(i, lon, ref=None, name=None, railway=False, lat0=LAT - 0.0004, lat1=LAT + 0.0004):
    tags = {"bridge": "yes"}
    tags["railway" if railway else "highway"] = "rail" if railway else "primary"
    if ref:
        tags["ref"] = ref
    if name:
        tags["name"] = name
    return (i, [(i * 10, lon, lat0), (i * 10 + 1, lon, lat1)], tags)


def test_bridge_ref_and_place():
    ctx = ctx_for(nodes=[place(1, "Novaci", 24.1, LAT + 0.01)],
                  ways=[bridge(1, 24.1, ref="DN67"), bridge(2, 24.3, ref="DN67")])
    out = res(ep("BRIDGE", road_ref="DN 67", locality_hint="Novaci"), ctx)
    assert len(out) == 1 and out[0].confidence == 0.85 and abs(out[0].m - m_at(24.1)) < 5


def test_bridge_two_bridges_nearest_hint_wins():
    ctx = ctx_for(nodes=[place(1, "Novaci", 24.10, LAT + 0.01)],
                  ways=[bridge(1, 24.10), bridge(2, 24.12)])
    out = res(ep("BRIDGE", locality_hint="Novaci"), ctx)
    assert [round(c.confidence, 2) for c in out] == [0.75, 0.75]
    assert abs(out[0].m - m_at(24.10)) < 5 and out[0].dist_m < out[1].dist_m


def test_bridge_place_five_km_away_no_candidate():
    ctx = ctx_for(nodes=[place(1, "Novaci", 24.10, LAT + 0.05)], ways=[bridge(1, 24.10)])
    assert res(ep("BRIDGE", locality_hint="Novaci"), ctx) == []


def test_bridge_only_crossing_in_window():
    ctx = ctx_for(ways=[bridge(1, 24.10), bridge(2, 24.35)])
    out = res(ep("BRIDGE", target="Zzz"), ctx, window=(m_at(24.3), LEN))
    assert len(out) == 1 and out[0].confidence == 0.5 and abs(out[0].m - m_at(24.35)) < 5


def test_bridge_without_anchor_or_window_empty():
    assert res(ep("BRIDGE"), ctx_for(ways=[bridge(1, 24.1)])) == []


def test_bridge_railway():
    ctx = ctx_for(nodes=[place(1, "Leordina", 24.2, LAT + 0.005)],
                  ways=[bridge(1, 24.2, railway=True), bridge(2, 24.2005)])
    out = res(ep("BRIDGE", road_ref="CFR", locality_hint="Leordina"), ctx)
    assert len(out) == 1 and out[0].confidence == 0.85


def test_bridge_not_crossing_course_ignored():
    ctx = ctx_for(nodes=[place(1, "Novaci", 24.1, LAT + 0.01)],
                  ways=[bridge(1, 24.1, lat0=LAT + 0.005, lat1=LAT + 0.006)])
    assert res(ep("BRIDGE", locality_hint="Novaci"), ctx) == []


def test_road_ref_resolves_via_bridge_with_cap():
    ctx = ctx_for(nodes=[place(1, "Novaci", 24.1, LAT + 0.01)], ways=[bridge(1, 24.1, ref="DN67")])
    out = res(ep("ROAD", road_ref="DN 67", locality_hint="Novaci"), ctx)
    assert out and out[0].confidence == 0.7 and out[0].method == "road_bridge"
    assert res(ep("ROAD", road_ref=None), ctx) == []


# -------------------------------------------------------------------- LOCALITY


def uat(aid, name, x0, x1):
    return (aid, {"boundary": "administrative", "admin_level": "8", "name": name}, box(x0, LAT - 0.01, x1, LAT + 0.01))


def test_locality_uat_entry_and_exit_by_role():
    ctx = ctx_for(areas=[uat("r1", "Zlatna", 24.10, 24.20)])
    f = res(ep("LOCALITY", target="Zlatna"), ctx, role="from")
    t = res(ep("LOCALITY", target="Zlatna"), ctx, role="to")
    assert f[0].confidence == t[0].confidence == 0.8
    assert abs(f[0].m - m_at(24.10)) < 5 and abs(t[0].m - m_at(24.20)) < 5


def test_locality_qualifier_overrides_role():
    ctx = ctx_for(areas=[uat("r1", "Zlatna", 24.10, 24.20)])
    out = res(ep("LOCALITY", target="Zlatna", qualifier="downstream"), ctx, role="from")
    assert abs(out[0].m - m_at(24.20)) < 5


def test_locality_projection_tiers():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.1, LAT + 0.004), place(2, "Bbb", 24.2, LAT + 0.02),
                         place(3, "Ccc", 24.3, LAT + 0.04)])
    assert res(ep("LOCALITY", target="Aaa"), ctx)[0].confidence == 0.7
    assert res(ep("LOCALITY", target="Bbb"), ctx)[0].confidence == 0.55
    assert res(ep("LOCALITY", target="Ccc"), ctx) == []  # ~4.4 km away


def test_locality_fuzzy_name():
    ctx = ctx_for(nodes=[place(1, "Săliștea", 24.1, LAT + 0.002)])
    assert res(ep("LOCALITY", target="Saliștea"), ctx)


def test_locality_namesake_in_other_county_filtered():
    ctx = ctx_for(nodes=[place(1, "Valea", 24.1, LAT + 0.02)])
    ctx.county_polys["alba"] = R.PolygonIndex(box(23.0, 45.0, 25.0, 47.0))
    ctx.county_polys["cluj"] = R.PolygonIndex(box(25.0, 45.0, 26.0, 47.0))
    assert res(ep("LOCALITY", target="Valea"), ctx, judet="Cluj") == []
    assert res(ep("LOCALITY", target="Valea"), ctx, judet="Alba")


def test_locality_other_county_close_keeps_penalty():
    ctx = ctx_for(nodes=[place(1, "Valea", 24.1, LAT + 0.004)])
    ctx.county_polys["alba"] = R.PolygonIndex(box(23.0, 45.0, 25.0, 47.0))
    ctx.county_polys["cluj"] = R.PolygonIndex(box(25.0, 45.0, 26.0, 47.0))
    assert res(ep("LOCALITY", target="Valea"), ctx, judet="Cluj")[0].confidence == pytest.approx(0.6)


# ---------------------------------------------------------------- COUNTY / BORDER


def county(name, x0, x1, level="4"):
    return (f"c{name}", {"boundary": "administrative", "admin_level": level, "name": name},
            box(x0, LAT - 1, x1, LAT + 1))


def test_county_limit_single_crossing():
    ctx = ctx_for(areas=[county("Județul Alba", 23.0, 24.2)])
    out = res(ep("COUNTY_LIMIT", target="Alba"), ctx)
    assert len(out) == 1 and out[0].confidence == 0.9 and abs(out[0].m - m_at(24.2)) < 5


def test_county_limit_uses_water_county_when_untargeted():
    ctx = ctx_for(areas=[county("Alba", 24.15, 25.0)])
    out = res(ep("COUNTY_LIMIT"), ctx, judet="Alba")
    assert len(out) == 1 and abs(out[0].m - m_at(24.15)) < 5


def test_county_limit_two_crossings_lower_confidence():
    ctx = ctx_for(areas=[county("Alba", 24.1, 24.2)])
    out = res(ep("COUNTY_LIMIT", target="Alba"), ctx)
    assert [c.confidence for c in out] == [0.65, 0.65] and len(out) == 2


def test_county_limit_unknown_county_or_none():
    ctx = ctx_for(areas=[county("Alba", 24.15, 25.0)])
    assert res(ep("COUNTY_LIMIT", target="Cluj"), ctx) == []
    assert res(ep("COUNTY_LIMIT"), ctx) == []


def test_county_limit_course_entirely_inside_has_no_crossing():
    ctx = ctx_for(areas=[county("Alba", 23.0, 25.0)])
    assert res(ep("COUNTY_LIMIT", target="Alba"), ctx) == []


def test_border_crossing():
    ctx = ctx_for(areas=[county("România", 23.0, 24.3, level="2")])
    out = res(ep("BORDER", target="Ungaria"), ctx)
    assert len(out) == 1 and out[0].confidence == 0.85 and abs(out[0].m - m_at(24.3)) < 5


def test_border_without_country_polygon():
    assert res(ep("BORDER"), ctx_for()) == []


# -------------------------------------------------------------------- WATERFALL


def test_waterfall_named_within_200m():
    near = Node(1, (24.1, LAT + 0.0009), {"waterway": "waterfall", "name": "Cascada Putna"})
    far = Node(2, (24.2, LAT + 0.004), {"waterway": "waterfall", "name": "Cascada Putna"})
    out = res(ep("WATERFALL", target="Putna"), ctx_for(nodes=[near, far]))
    assert len(out) == 1 and out[0].confidence == 0.85 and abs(out[0].m - m_at(24.1)) < 5


# ------------------------------------------------------------------ build_context


def test_build_context_counties_geojson_fallback():
    gj = {"features": [{"properties": {"name": "Alba"}, "geometry": box(23.0, 45.0, 25.0, 47.0)}]}
    ctx = R.build_context(make_extract([]), [course()], gj)
    assert ctx.county_of(24.0, 46.0) == "alba" and ctx.county_of(10.0, 10.0) is None


def test_candidate_to_dict():
    d = R.Candidate(12.34, 0.9, "x", {"type": "node"}, 5.55).to_dict()
    assert d["m"] == 12.3 and d["dist_m"] == 5.5 or d["dist_m"] == 5.6


def test_confluence_uses_course_index_for_courses_outside_the_subset():
    c = course(receives_into="rel:424242")
    ctx = ctx_for([c])
    assert res(ep("CONFLUENCE", target="Mureș"), ctx, c) == []
    ctx.names = {"rel:424242": ["mures"]}
    out = res(ep("CONFLUENCE", target="Mureș"), ctx, c)
    assert out and out[0].method == "outlet_into_named"


def test_confluence_base_name_lower_confidence():
    c = course(receives_into="name:aries:n9")
    ctx = ctx_for([c], extra=[course("name:aries:n9", "Arieș")])
    out = res(ep("CONFLUENCE", target="Arieșul Mare"), ctx, c)
    assert out and out[0].method == "outlet_into_base_name" and out[0].confidence == 0.7
    # an unrelated parent is still rejected
    c2 = course(receives_into="name:mures:n9")
    assert res(ep("CONFLUENCE", target="Arieșul Mare"), ctx_for([c2], extra=[course("name:mures:n9", "Mureș")]), c2) == []
    # 'Valea X' never collapses to 'valea'
    assert R._base_keys({"valea mare"}) == set()
