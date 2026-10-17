from __future__ import annotations

import gzip
import json

import pytest

from _factory import box, make_extract
from test_resolvers import LAT, LEN, LINE, bridge, county, course, ctx_for, ep, m_at, place, uat
from rivernet import sectors as S
from rivernet.extract_schema import Node


def water(name="Test", judet="Alba", km="30 km", limite="x", slug="w1"):
    return {"slug": slug, "name": name, "judet": judet, "dimensiune": km, "limite": limite, "subtype": "rau"}


def interval(f, t, **kw):
    d = {"scope": "interval", "from": f, "to": t, "localities": [], "county": None, "includes_tributaries": False}
    d.update(kw)
    return d


MATCH = {"course_id": "name:test:n1", "score": 0.9, "method": "name+county"}
KM = LEN / 1000  # contract km equal to the course => km_ratio 1.0 for the full course


def rs(spec, ctx=None, w=None, ovs=None, match=MATCH):
    return S.resolve_sector(w or water(km=f"{KM:.2f} km"), spec, match, ctx or ctx_for(), ovs, "ro-water-20260101")


def test_interval_source_to_mouth_high_confidence():
    r = rs(interval(ep("SOURCE"), ep("MOUTH")))
    assert r["status"] == "resolved" and r["confidence"] == "high"
    assert r["from"]["m"] == 0 and r["to"]["m"] == round(LEN, 1)
    assert r["length_m"] == round(LEN, 1) and r["km_ratio"] == pytest.approx(1.0, abs=0.01)
    assert r["network_version"] == "ro-water-20260101" and r["course"]["course_id"] == "name:test:n1"


def test_swap_when_text_is_downstream_first():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.1, LAT + 0.002), place(2, "Bbb", 24.3, LAT + 0.002)])
    r = rs(interval(ep("LOCALITY", target="Bbb"), ep("LOCALITY", target="Aaa")), ctx)
    assert "swapped_order" in r["reasons"]
    assert r["from"]["anchor"]["name"] == "Aaa" and r["to"]["anchor"]["name"] == "Bbb"
    assert r["from"]["m"] < r["to"]["m"]


def test_same_point_uses_second_best_for_weaker_end():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.1, LAT + 0.002), place(2, "Aaa", 24.3, LAT + 0.02)])
    r = rs(interval(ep("LOCALITY", target="Aaa"), ep("LOCALITY", target="Aaa")), ctx)
    assert "second_best:to" in r["reasons"] or "second_best:from" in r["reasons"]
    assert r["to"]["m"] - r["from"]["m"] > 200


def test_ambiguous_endpoint_flagged():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.1, LAT + 0.002), place(2, "Aaa", 24.3, LAT + 0.002)])
    r = rs(interval(ep("SOURCE"), ep("LOCALITY", target="Aaa")), ctx)
    assert "endpoint_ambiguous:to" in r["reasons"]


def test_unresolved_endpoint():
    r = rs(interval(ep("SOURCE"), ep("LOCALITY", target="Nowhere")))
    assert r["status"] == "unresolved" and "endpoint_unresolved:to" in r["reasons"]
    assert r["from"] is None


def test_unknown_endpoint_kind_unresolved():
    r = rs(interval(ep("UNKNOWN"), ep("MOUTH")))
    assert r["status"] == "unresolved"


def test_whole_course():
    r = rs({"scope": "whole_course"})
    assert (r["from"]["m"], r["to"]["m"]) == (0, round(LEN, 1)) and r["status"] == "resolved"


def test_whole_county_single_and_multiple():
    c = course(counties=[{"county": "Alba", "m_from": 1000.0, "m_to": 9000.0}])
    r = rs({"scope": "whole_county", "county": "Alba"}, ctx_for([c]))
    assert (r["from"]["m"], r["to"]["m"]) == (1000.0, 9000.0)
    c2 = course(counties=[{"county": "Alba", "m_from": 0.0, "m_to": 1000.0},
                          {"county": "Alba", "m_from": 5000.0, "m_to": 9000.0}])
    r2 = rs({"scope": "whole_county", "county": "Alba"}, ctx_for([c2]), w=water(km="4 km"))
    assert "county_interval_multiple" in r2["reasons"] and (r2["from"]["m"], r2["to"]["m"]) == (5000.0, 9000.0)
    r3 = rs({"scope": "whole_county", "county": "Cluj"}, ctx_for([c]))
    assert r3["status"] == "unresolved" and "county_not_on_course" in r3["reasons"]


def test_locality_list_min_max():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.3, LAT + 0.002), place(2, "Bbb", 24.1, LAT + 0.002),
                         place(3, "Ccc", 24.2, LAT + 0.002)])
    r = rs({"scope": "locality_list", "localities": ["Aaa", "Bbb", "Ccc"], "county": None}, ctx)
    assert r["from"]["anchor"]["name"] == "Bbb" and r["to"]["anchor"]["name"] == "Aaa"
    r2 = rs({"scope": "locality_list", "localities": ["Aaa", "Zzz"], "county": None}, ctx)
    assert r2["status"] == "unresolved"


@pytest.mark.parametrize("scope", ["empty", "unparsed"])
def test_unusable_limits(scope):
    r = rs({"scope": scope})
    assert r["status"] == "unresolved" and "limite_unusable" in r["reasons"]


def test_no_course():
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), match={"course_id": None, "method": "ambiguous", "score": 0.5})
    assert r["status"] == "unresolved" and "course_ambiguous" in r["reasons"]
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), match={"course_id": "rel:404", "method": "override", "score": 1.0})
    assert "course_record_missing" in r["reasons"]


@pytest.mark.parametrize("ratio,status,conf", [
    (0.59, "review", "low"), (0.6, "resolved", "medium"), (0.79, "resolved", "medium"),
    (0.8, "resolved", "high"), (1.25, "resolved", "high"), (1.26, "resolved", "medium"),
    (1.6, "resolved", "medium"), (1.61, "review", "low"),
])
def test_km_band_edges(ratio, status, conf):
    rec = {"from": {"confidence": 0.9}, "to": {"confidence": 0.9}, "km_ratio": ratio,
           "includes_tributaries": False, "reasons": []}
    S.classify(rec)
    assert (rec["status"], rec["confidence"]) == (status, conf)


def test_tributaries_only_upper_bound():
    rec = {"from": {"confidence": 0.9}, "to": {"confidence": 0.9}, "km_ratio": 0.2,
           "includes_tributaries": True, "reasons": []}
    S.classify(rec)
    assert rec["status"] == "resolved"
    rec["km_ratio"] = 1.7
    rec["reasons"] = []
    S.classify(rec)
    assert rec["status"] == "review" and "km_ratio_out_of_band" in rec["reasons"]


def test_low_endpoint_confidence_is_review():
    rec = {"from": {"confidence": 0.55}, "to": {"confidence": 0.95}, "km_ratio": 1.0,
           "includes_tributaries": False, "reasons": []}
    S.classify(rec)
    assert rec["status"] == "review" and "endpoint_confidence_low" in rec["reasons"]


def test_missing_km_never_high_but_can_be_medium():
    r = S.resolve_sector(water(km=""), interval(ep("SOURCE"), ep("MOUTH")), MATCH, ctx_for(), None, "v")
    assert "contract_km_missing" in r["reasons"] and r["km_ratio"] is None
    assert (r["status"], r["confidence"]) == ("resolved", "medium")


def test_ha_unit_skips_km_check():
    r = S.resolve_sector(water(km="50 ha"), interval(ep("SOURCE"), ep("MOUTH")), MATCH, ctx_for(), None, "v")
    assert "contract_unit_ha" in r["reasons"] and r["contract_km"] is None and r["km_ratio"] is None


def test_endpoint_override_measure_and_node():
    ctx = ctx_for(nodes=[place(7, "Zzz", 24.1, LAT + 0.001)])
    ovs = {("w1", "to"): {"anchor": {"type": "measure", "m": 20000.0}},
           ("w1", "from"): {"anchor": {"type": "node", "id": 7}}}
    r = rs(interval(ep("LOCALITY", target="Nowhere"), ep("LOCALITY", target="Nowhere")), ctx, ovs=ovs)
    assert r["to"]["m"] == 20000.0 and r["to"]["confidence"] == 1.0 and r["to"]["method"] == "override"
    assert abs(r["from"]["m"] - m_at(24.1)) < 5 and sorted(r["override_ids"]) == ["w1:from", "w1:to"]


def test_endpoint_override_beyond_course_ignored():
    ovs = {("w1", "to"): {"anchor": {"type": "measure", "m": LEN + 5000}}}
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ovs=ovs)
    assert r["override_ids"] == [] and r["to"]["method"] == "mouth"


def test_endpoint_override_way_and_area():
    ctx = ctx_for(ways=[bridge(5, 24.2)], areas=[uat("r9", "Zlatna", 24.1, 24.3)])
    ovs = {("w1", "from"): {"anchor": {"type": "way", "id": 5}}, ("w1", "to"): {"anchor": {"type": "area", "id": "r9"}}}
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx, ovs=ovs)
    assert abs(r["from"]["m"] - m_at(24.2)) < 5 and abs(r["to"]["m"] - m_at(24.3)) < 5


def test_validation_flags_long_segment_and_review():
    coords = [[24.0, LAT], [24.4, LAT]]  # one ~30 km segment: chord-scale, blocking
    c = course(geometry={"type": "LineString", "coordinates": coords})
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx_for([c]))
    assert r["status"] == "review" and "invariant:segment_gt_5km" in r["reasons"]


def test_coarse_osm_segment_is_reported_but_not_blocking():
    coords = [[24.0, LAT], [24.015, LAT], [24.03, LAT]]  # two ~1.16 km segments of one OSM way
    c = course(geometry={"type": "LineString", "coordinates": coords})
    km = c["length_m"] / 1000
    from rivernet.lr import Line
    c["length_m"] = Line.from_coords([tuple(x) for x in coords]).length_m
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx_for([c]), w=water(km=f"{c['length_m'] / 1000:.2f} km"))
    assert r["status"] == "resolved" and "coarse_osm_segment" in r["reasons"]
    assert not any(x.startswith("invariant:") for x in r["reasons"])


def test_synthetic_span_excuses_long_segment():
    coords = [[24.0, LAT], [24.4, LAT]]
    c = course(geometry={"type": "LineString", "coordinates": coords},
               synthetic=[{"m_from": 0.0, "m_to": LEN, "kind": "gap_bridge", "gap_m": LEN}])
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx_for([c]))
    assert not any(x.startswith("invariant:segment") for x in r["reasons"])


def test_validation_outside_county():
    ctx = ctx_for(areas=[county("Cluj", 20.0, 21.0)])
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx, w=water(judet="Cluj", km=f"{KM:.2f} km"))
    assert "invariant:outside_county" in r["reasons"] and r["status"] == "review"
    ctx2 = ctx_for(areas=[county("Alba", 23.0, 25.0)])
    assert "invariant:outside_county" not in rs(interval(ep("SOURCE"), ep("MOUTH")), ctx2)["reasons"]


def test_validation_confluence_must_sit_on_junction():
    c = course(junctions=[{"node": 1, "m": 5000.0, "tributary_course_id": "name:x:n1", "side": "in"}])
    rec = {"from": {"m": 0.0, "kind": "SOURCE", "method": "source"},
           "to": {"m": 5003.0, "kind": "CONFLUENCE", "method": "tributary_junction"},
           "length_m": 5003.0, "judet": None}
    assert "confluence_not_on_junction:to" in S.validate(rec, c, ctx_for([c]))
    rec["to"]["m"] = 5000.4
    rec["length_m"] = 5000.4
    assert S.validate(rec, c, ctx_for([c])) == []


def test_validation_measure_order():
    rec = {"from": {"m": 10.0, "kind": "SOURCE", "method": "x"}, "to": {"m": 5.0, "kind": "MOUTH", "method": "x"},
           "length_m": -5.0, "judet": None}
    assert S.validate(rec, course(), ctx_for()) == ["measure_order"]


# --------------------------------------------------------------------- overlaps


def mk(slug, f, t, scope="interval", status="resolved"):
    return {"slug": slug, "from": {"m": f}, "to": {"m": t}, "length_m": t - f, "status": status,
            "course": {"course_id": "c"}, "parse": {"scope": scope}, "reasons": []}


def test_overlap_flags_both_sides_without_status_change_if_small():
    a, b = mk("a", 0, 1000), mk("b", 900, 5000)
    S.flag_overlaps([a, b])
    assert "overlap:b" in a["reasons"] and "overlap:a" in b["reasons"]
    assert a["status"] == b["status"] == "resolved"


def test_overlap_over_half_downgrades():
    a, b = mk("a", 0, 1000), mk("b", 400, 5000)
    S.flag_overlaps([a, b])
    assert a["status"] == b["status"] == "review" and "overlap_gt_50pct" in a["reasons"]


def test_overlap_whole_county_exempt_and_other_course_ignored():
    a, b = mk("a", 0, 1000, scope="whole_county"), mk("b", 0, 1000)
    S.flag_overlaps([a, b])
    assert a["status"] == b["status"] == "resolved" and "overlap:b" in a["reasons"]
    c = mk("c", 0, 1000)
    c["course"]["course_id"] = "other"
    d = mk("d", 0, 1000)
    S.flag_overlaps([c, d])
    assert c["reasons"] == []


def test_touching_sectors_do_not_overlap():
    a, b = mk("a", 0, 1000), mk("b", 1000, 2000)
    S.flag_overlaps([a, b])
    assert a["reasons"] == []


def test_determinism():
    ctx = ctx_for(nodes=[place(1, "Aaa", 24.1, LAT + 0.002)])
    spec = interval(ep("SOURCE"), ep("LOCALITY", target="Aaa"))
    a = json.dumps(rs(spec, ctx), sort_keys=True)
    b = json.dumps(rs(spec, ctx), sort_keys=True)
    assert a == b


# -------------------------------------------------------------------------- CLI


def test_cli_end_to_end(tmp_path):
    ex_path = tmp_path / "ex.jsonl"
    recs = [{"t": "meta", "schema": 1, "source": "t", "osm_timestamp": "2026-10-15T00:00:00Z"}]
    ex_path.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    cp = tmp_path / "courses.jsonl.gz"
    with gzip.open(cp, "wt", encoding="utf-8") as f:
        f.write(json.dumps(course()) + "\n")
    wp = tmp_path / "w.json"
    wp.write_text(json.dumps([water(km=f"{KM:.2f} km"), {**water(slug="w2"), "subtype": "lac"}]))
    pp = tmp_path / "p.jsonl"
    pp.write_text(json.dumps({"slug": "w1", "spec": interval(ep("SOURCE"), ep("MOUTH"))}) + "\n")
    mp = tmp_path / "m.jsonl"
    mp.write_text(json.dumps({"slug": "w1", **MATCH}) + "\n")
    out = tmp_path / "s.jsonl"
    args = ["--extract", str(ex_path), "--courses", str(cp), "--waters", str(wp), "--parsed", str(pp),
            "--matches", str(mp), "--overrides", str(tmp_path / "none.json"),
            "--counties", str(tmp_path / "none.geojson"), "--out", str(out)]
    assert S.cli(args) == 0
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["status"] == "resolved" and rows[0]["network_version"] == "ro-water-20261015"
    assert S.cli(["--extract", str(ex_path), "--courses", str(tmp_path / "missing.gz")]) == 1


# ------------------------------------------------- fallback source cap (T6.5)


def test_anar_course_is_never_high_confidence():
    c = course(source="anar")
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx_for([c]))
    assert r["status"] == "resolved" and r["confidence"] == "medium"
    assert "fallback_source:anar" in r["reasons"]


def test_anar_fuzzy_match_goes_to_review():
    c = course(source="anar")
    m = {**MATCH, "method": "anar_fuzzy+county"}
    r = rs(interval(ep("SOURCE"), ep("MOUTH")), ctx_for([c]), match=m)
    assert r["status"] == "review" and "fallback_fuzzy_match" in r["reasons"]


# ---------------------------------------------------- alternative courses


def short_course(cid="name:test:n2"):
    coords = [(round(24.0 + 0.005 * i, 6), LAT) for i in range(11)]  # first ~3.9 km only
    from rivernet.lr import Line as _L
    ln = _L.from_coords(coords)
    return course(cid=cid, length_m=ln.length_m, geometry={"type": "LineString", "coordinates": [list(c) for c in coords]})


def rb(spec, ctx, match, w=None):
    return S.resolve_best(w or water(km=f"{KM:.2f} km"), spec, match, ctx, None, "v")


def test_alternative_course_replaces_an_unresolved_choice():
    ctx = ctx_for([short_course(), course()], nodes=[place(1, "Aaa", 24.35, LAT + 0.002)])
    m = {"course_id": "name:test:n2", "score": 0.8, "method": "name+county",
         "candidates": [["name:test:n2", 0.8, ""], ["name:test:n1", 0.7, ""]]}
    r = rb(interval(ep("SOURCE"), ep("LOCALITY", target="Aaa")), ctx, m)
    assert r["course"]["course_id"] == "name:test:n1" and "alt_course" in r["reasons"]
    assert r["course"]["method"] == "name+county|alt" and r["status"] in ("resolved", "review")


def test_alternative_never_downgrades_and_resolved_is_kept():
    ctx = ctx_for([short_course(), course()])
    m = {"course_id": "name:test:n1", "score": 0.8, "method": "name+county",
         "candidates": [["name:test:n1", 0.8, ""], ["name:test:n2", 0.7, ""]]}
    r = rb(interval(ep("SOURCE"), ep("MOUTH")), ctx, m)
    assert r["course"]["course_id"] == "name:test:n1" and "alt_course" not in r["reasons"]


def test_ambiguous_match_resolved_by_the_single_resolving_candidate():
    ctx = ctx_for([short_course(), course()], nodes=[place(1, "Aaa", 24.35, LAT + 0.002)])
    m = {"course_id": None, "score": 0.8, "method": "ambiguous",
         "candidates": [["name:test:n2", 0.8, ""], ["name:test:n1", 0.78, ""]]}
    r = rb(interval(ep("SOURCE"), ep("LOCALITY", target="Aaa")), ctx, m)
    assert r["course"]["course_id"] == "name:test:n1"
    assert r["course"]["method"] == "ambiguous+endpoints" and "ambiguity_resolved_by_endpoints" in r["reasons"]


def test_ambiguous_with_two_resolving_candidates_stays_unresolved():
    ctx = ctx_for([course(cid="name:test:n2"), course()])
    m = {"course_id": None, "score": 0.8, "method": "ambiguous",
         "candidates": [["name:test:n2", 0.8, ""], ["name:test:n1", 0.78, ""]]}
    r = rb(interval(ep("SOURCE"), ep("MOUTH")), ctx, m)
    assert r["status"] == "unresolved" and r["course"]["course_id"] is None


def test_override_and_unusable_limite_skip_alternatives():
    ctx = ctx_for([short_course(), course()])
    m = {"course_id": "name:test:n2", "score": 1.0, "method": "override",
         "candidates": [["name:test:n2", 1.0, "override"], ["name:test:n1", 0.7, ""]]}
    r = rb(interval(ep("SOURCE"), ep("LOCALITY", target="Nowhere")), ctx, m)
    assert r["course"]["course_id"] == "name:test:n2"
    r2 = rb({"scope": "unparsed"}, ctx, {**m, "method": "name+county"})
    assert r2["status"] == "unresolved" and "limite_unusable" in r2["reasons"]


# ------------------------------- unusable limite + overrides; plausible overlaps


def ov(m):
    return {"anchor": {"type": "measure", "m": m}, "reason": "r", "reviewer": "x", "date": "2026-10-17"}


def test_unusable_limite_with_both_endpoint_overrides_is_resolved():
    w = water(km=f"{(12000 - 2000) / 1000:.1f} km", limite="Jirlău km 183- Voinești km 309")
    ovs = {("w1", "from"): ov(12000.0), ("w1", "to"): ov(2000.0)}  # given downstream-first: swapped
    r = rs({"scope": "unparsed"}, w=w, ovs=ovs)
    assert (r["from"]["m"], r["to"]["m"]) == (2000.0, 12000.0)
    assert r["from"]["kind"] == "OVERRIDE" and r["status"] == "resolved"
    assert {"limite_unusable_overridden", "swapped_order"} <= set(r["reasons"])
    assert r["override_ids"] == ["w1:from", "w1:to"]


def test_unusable_limite_needs_both_overrides_and_a_valid_anchor():
    r = rs({"scope": "unparsed"}, ovs={("w1", "from"): ov(1000.0)})
    assert r["status"] == "unresolved" and r["reasons"] == ["limite_unusable"]
    r = rs({"scope": "empty"}, ovs={("w1", "from"): ov(1000.0), ("w1", "to"): ov(LEN + 5000)})
    assert r["status"] == "unresolved" and "override_anchor_unresolvable" in r["reasons"]


def rec_on(slug, f, t, ratio, status="resolved"):
    return {"slug": slug, "course": {"course_id": "c"}, "parse": {"scope": "interval"}, "includes_tributaries": False,
            "from": {"m": f}, "to": {"m": t}, "length_m": t - f, "km_ratio": ratio, "status": status, "reasons": []}


def test_implausible_partner_cannot_demote_a_plausible_sector():
    good = rec_on("good", 80_000, 187_000, 0.98)
    bad = rec_on("bad", 0, 296_000, 9.27, status="review")  # 'cursul principal' read as the whole river
    S.flag_overlaps([good, bad])
    assert good["status"] == "resolved" and "overlap_gt_50pct" in good["reasons"] and "overlap:bad" in good["reasons"]
    assert bad["status"] == "review"


def test_two_plausible_overlapping_sectors_still_demote_each_other():
    a, b = rec_on("a", 0, 10_000, 1.0), rec_on("b", 1_000, 11_000, 1.0)
    S.flag_overlaps([a, b])
    assert a["status"] == b["status"] == "review"


def test_whole_county_on_a_border_river_uses_the_span_when_it_fits_better():
    ivs = [{"county": "Vrancea", "m_from": 1000.0, "m_to": 3000.0},
           {"county": "Vrancea", "m_from": 5000.0, "m_to": 6000.0},
           {"county": "Vrancea", "m_from": 7000.0, "m_to": 9500.0}]
    c = course(counties=ivs)
    r = rs({"scope": "whole_county", "county": "Vrancea"}, ctx_for([c]), w=water(km="8.2 km"))
    assert (r["from"]["m"], r["to"]["m"]) == (1000.0, 9500.0)
    assert {"county_interval_multiple", "county_interval_span"} <= set(r["reasons"])
    r2 = rs({"scope": "whole_county", "county": "Vrancea"}, ctx_for([c]), w=water(km="2.5 km"))
    assert (r2["from"]["m"], r2["to"]["m"]) == (7000.0, 9500.0) and "county_interval_span" not in r2["reasons"]


def test_overlap_across_counties_does_not_demote():
    a, b = rec_on("a", 0, 10_000, 1.0), rec_on("b", 1_000, 11_000, 1.0)
    a["judet"], b["judet"] = "Suceava", "Botoșani"  # the Siret is their border
    S.flag_overlaps([a, b])
    assert a["status"] == b["status"] == "resolved"
    assert "overlap:b" in a["reasons"] and "overlap_gt_50pct" in a["reasons"]
