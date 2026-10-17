from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import pytest

from rivernet import publish as P
from test_resolvers import LAT, LEN, course

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "rivernet" / "waters_mini.json"
WATERS = json.loads(FIX.read_text(encoding="utf-8"))
COURSE = course()


def sec(slug, status="resolved", conf="high", f=2000.0, t=12000.0, reasons=(), overrides=()):
    return {"slug": slug, "status": status, "confidence": conf, "reasons": list(reasons),
            "override_ids": list(overrides), "network_version": "ro-water-20261015",
            "course": {"course_id": COURSE["course_id"]},
            "from": {"m": f, "kind": "SOURCE"}, "to": {"m": t, "kind": "MOUTH"}}


def run(sectors, waters=None, mode="shadow", courses=None):
    return P.publish(copy.deepcopy(waters or WATERS), {s["slug"]: s for s in sectors},
                     courses if courses is not None else {COURSE["course_id"]: COURSE}, mode=mode)


def by_slug(ws):
    return {w["slug"]: w for w in ws}


ALL_RIVERS = ["1xqpi6rz", "aoja7n5d", "anpa-anpa-0379", "anpa-anpa-0134", "anpa-anpa-0135"]


def test_switched_single_gets_sector_fields_and_loses_legacy_keys():
    new, rep = run([sec("1xqpi6rz")])
    w = by_slug(new)["1xqpi6rz"]
    assert w["geometryKind"] == "sector" and w["sectorStatus"] == "resolved" and w["sectorConfidence"] == "high"
    assert w["source"] == "rivernet" and w["source_detail"] == "rivernet:ro-water-20261015"
    assert "course_frac" not in w and "bbox_render" not in w and "fallback" not in w
    assert w["sectorStart"] == round(2000 / LEN, 4) and w["sectorEnd"] == round(12000 / LEN, 4)
    assert w["lengthKm"] == pytest.approx(10.0, abs=0.1)
    x0, y0, x1, y1 = w["bbox"]
    assert y0 == y1 == round(LAT, 5) and x0 < x1
    assert [s["slug"] for s in rep["switched"]] == ["1xqpi6rz"]


def test_geometry_is_simplified_and_rounded():
    new, _ = run([sec("1xqpi6rz")])
    g = by_slug(new)["1xqpi6rz"]["geometry"]
    assert g["type"] == "LineString"
    assert len(g["coordinates"]) == 2  # straight line collapses to its end points
    assert all(len(str(v).split(".")[-1]) <= 5 for p in g["coordinates"] for v in p)


def test_blocked_group_keeps_every_member_legacy():
    sectors = [sec("1xqpi6rz"), sec("aoja7n5d"), sec("anpa-anpa-0379", "unresolved", "low")]
    new, rep = run(sectors)
    d = by_slug(new)
    assert "geometryKind" not in d["aoja7n5d"] and "geometryKind" not in d["anpa-anpa-0379"]
    assert rep["blocked_groups"] == [{"riverGroup": "crisul-alb", "blockers": ["anpa-anpa-0379"],
                                      "members": ["anpa-anpa-0379", "aoja7n5d"]}]
    assert {k["slug"]: k["reason"] for k in rep["kept_legacy"]}["aoja7n5d"] == "d8_group_blocked"


def test_group_switches_when_every_member_resolves():
    new, rep = run([sec("anpa-anpa-0134", f=0, t=5000), sec("anpa-anpa-0135", f=5000, t=15000)])
    d = by_slug(new)
    assert d["anpa-anpa-0134"]["geometryKind"] == d["anpa-anpa-0135"]["geometryKind"] == "sector"
    assert rep["blocked_groups"] == [] and rep["switched_count"] == 2


def test_review_needs_override_and_no_blocking_reason():
    base = [sec("1xqpi6rz", "review", "low", reasons=["km_ratio_out_of_band"])]
    assert "geometryKind" not in by_slug(run(base)[0])["1xqpi6rz"]
    assert run(base)[1]["kept_legacy"][0]["reason"] == "review_without_override"
    ok = [sec("1xqpi6rz", "review", "low", reasons=["km_ratio_out_of_band"], overrides=["1xqpi6rz:to"])]
    assert by_slug(run(ok)[0])["1xqpi6rz"]["sectorStatus"] == "review"
    bad = [sec("1xqpi6rz", "review", "low", reasons=["invariant:segment_gt_1km"], overrides=["1xqpi6rz:to"])]
    assert run(bad)[1]["kept_legacy"][0]["reason"].startswith("review_blocking_reason")


def test_lake_and_missing_sector_stay_legacy():
    new, rep = run([sec("1xqpi6rz"), sec("jrlgyh2h")])
    assert "geometryKind" not in by_slug(new)["jrlgyh2h"]
    reasons = {k["slug"]: k["reason"] for k in rep["kept_legacy"]}
    assert reasons["gxjd56ii"] == "no_sector_record" and "jrlgyh2h" not in reasons  # lakes are not reported


def test_course_missing_keeps_legacy():
    new, rep = run([sec("1xqpi6rz")], courses={})
    assert rep["switched_count"] == 0
    assert {k["slug"]: k["reason"] for k in rep["kept_legacy"]}["1xqpi6rz"] == "course_missing"


def test_synthetic_span_splits_into_multilinestring():
    c = course(synthetic=[{"m_from": 5000.0, "m_to": 6000.0, "kind": "gap_bridge", "gap_m": 1000.0}])
    new, _ = run([sec("1xqpi6rz")], courses={c["course_id"]: c})
    g = by_slug(new)["1xqpi6rz"]["geometry"]
    assert g["type"] == "MultiLineString" and len(g["coordinates"]) == 2


def test_coordinates_filled_only_when_null():
    ws = copy.deepcopy(WATERS)
    ws[0]["coordinates"] = None
    ws[0]["driving"] = None
    new, _ = run([sec("1xqpi6rz")], ws)
    w = by_slug(new)["1xqpi6rz"]
    assert w["coordinates"] == w["driving"] and LAT - 1e-4 < w["coordinates"][1] < LAT + 1e-4
    keep, _ = run([sec("1xqpi6rz")])
    assert by_slug(keep)["1xqpi6rz"]["coordinates"] == WATERS[0]["coordinates"]


def test_publish_only_touches_geometry_fields():
    sectors = [sec(s) for s in ALL_RIVERS]
    new, _ = run(sectors)
    for old, n in zip(WATERS, new):
        changed = {k for k in set(old) | set(n) if old.get(k) != n.get(k) or (k in old) != (k in n)}
        assert changed <= P.ALLOWED, (old["slug"], changed - P.ALLOWED)
        for k in set(old) - P.ALLOWED:
            assert json.dumps(old[k], sort_keys=True) == json.dumps(n[k], sort_keys=True)
        assert old["slug"] == n["slug"] and old["subtype"] == n["subtype"]


def test_unswitched_waters_are_byte_equal():
    new, _ = run([sec("1xqpi6rz")])
    for old, n in zip(WATERS, new):
        if n["slug"] != "1xqpi6rz":
            assert json.dumps(old, sort_keys=True) == json.dumps(n, sort_keys=True)


def test_determinism_and_input_not_mutated():
    ws = copy.deepcopy(WATERS)
    sectors = {s["slug"]: s for s in [sec("1xqpi6rz")]}
    a = P.publish(ws, sectors, {COURSE["course_id"]: COURSE})
    b = P.publish(ws, sectors, {COURSE["course_id"]: COURSE})
    assert P.dumps_waters(a[0]) == P.dumps_waters(b[0]) and a[1] == b[1]
    assert ws == WATERS


def test_bad_mode():
    with pytest.raises(ValueError):
        P.publish([], {}, {}, mode="nope")


def test_simplify_dp():
    assert P.simplify_dp([[0, 0], [1, 0.00001], [2, 0]], 0.00005) == [[0, 0], [2, 0]]
    assert len(P.simplify_dp([[0, 0], [1, 0.001], [2, 0]], 0.00005)) == 3
    assert P.simplify_dp([[0, 0], [1, 1]]) == [[0, 0], [1, 1]]
    assert P.simplify_dp([[0, 0], [0, 0], [0, 0]], 0.1) == [[0, 0], [0, 0]]


def test_dumps_waters_matches_existing_format():
    raw = FIX.read_text(encoding="utf-8")
    assert P.dumps_waters(json.loads(raw)) == raw.rstrip("\n") or P.dumps_waters(json.loads(raw)).startswith("[\n {")


def test_cli_shadow_and_write(tmp_path):
    wp = tmp_path / "waters.json"
    wp.write_text(P.dumps_waters(WATERS), encoding="utf-8")
    sp = tmp_path / "s.jsonl"
    sp.write_text(json.dumps(sec("1xqpi6rz")) + "\n")
    cp = tmp_path / "c.jsonl.gz"
    with gzip.open(cp, "wt", encoding="utf-8") as f:
        f.write(json.dumps(COURSE) + "\n")
    args = ["--waters", str(wp), "--sectors", str(sp), "--courses", str(cp), "--out-dir", str(tmp_path / "o")]
    before = wp.read_text(encoding="utf-8")
    assert P.cli(args) == 0
    assert wp.read_text(encoding="utf-8") == before  # shadow never touches the input
    shadow = json.loads((tmp_path / "o" / "waters.shadow.json").read_text(encoding="utf-8"))
    assert shadow[0]["geometryKind"] == "sector"
    assert json.loads((tmp_path / "o" / "publish_report.json").read_text())["switched_count"] == 1
    assert P.cli(args + ["--mode", "write"]) == 0
    assert json.loads(wp.read_text(encoding="utf-8"))[0]["geometryKind"] == "sector"
    assert P.cli(["--waters", str(tmp_path / "none")]) == 1


# ------------------------------------------------- class-2 preview (T4.2)

from rivernet import preview as PV  # noqa: E402


def preview_payload():
    rec = lambda slug, group: {"slug": slug, "riverGroup": group, "legalStatus": "legal sector unverified",
                               "disclosure": "Traseu fizic experimental", "physicalCandidates": [{"id": "old", "geometry": None}]}
    return {"artifact": "class2-physical-preview-aggregate", "candidateCount": 3,
            "records": [rec("anpa-anpa-0134", "colibita"), rec("anpa-anpa-0135", "colibita"), rec("aoja7n5d", "crisul-alb")]}


def test_switched_group_preview_is_the_rivernet_course():
    sectors = [sec("anpa-anpa-0134", f=0, t=5000), sec("anpa-anpa-0135", f=5000, t=15000)]
    new, _ = run(sectors)
    payload = preview_payload()
    out, replaced = PV.rivernet_preview(payload, new, {s["slug"]: s for s in sectors}, {COURSE["course_id"]: COURSE})
    assert replaced == ["colibita"]
    a, b, other = out["records"]
    (cand,) = a["physicalCandidates"]
    assert cand["kind"] == "rivernet-course" and cand["id"] == COURSE["course_id"]
    assert cand["source"] == "rivernet:ro-water-20261015" and cand["geometry"]["type"] == "LineString"
    assert len(cand["geometryHash"]) == 64 and b["physicalCandidates"] == [cand]
    assert a["disclosure"] == "Traseu fizic experimental" and a["legalStatus"] == "legal sector unverified"
    assert other["physicalCandidates"] == [{"id": "old", "geometry": None}]  # not switched
    assert out["candidateCount"] == 3 and payload["records"][0]["physicalCandidates"][0]["id"] == "old"


def test_preview_needs_every_member_switched_on_one_course():
    sectors = [sec("anpa-anpa-0134", f=0, t=5000), sec("anpa-anpa-0135", f=5000, t=15000)]
    new, _ = run(sectors)
    by = {s["slug"]: s for s in sectors}
    assert PV.switched_group_courses(new, by) == {"colibita": COURSE["course_id"]}
    split = {**by, "anpa-anpa-0135": {**by["anpa-anpa-0135"], "course": {"course_id": "other"}}}
    assert PV.switched_group_courses(new, split) == {}
    legacy, _ = run([sec("1xqpi6rz")])
    assert PV.switched_group_courses(legacy, by) == {}


def test_anar_course_is_named_in_source_detail():
    anar = {**COURSE, "source": "anar"}
    new, _ = run([sec("1xqpi6rz")], courses={COURSE["course_id"]: anar})
    assert by_slug(new)["1xqpi6rz"]["source_detail"] == "rivernet:ro-water-20261015;geometry:anar-hidrografie"


def test_cli_preview_shadow_and_write(tmp_path):
    wp = tmp_path / "waters.json"
    wp.write_text(P.dumps_waters(WATERS), encoding="utf-8")
    pv = tmp_path / "preview_class2_physical.json"
    pv.write_text(json.dumps(preview_payload()), encoding="utf-8")
    sp = tmp_path / "s.jsonl"
    sp.write_text("\n".join(json.dumps(s) for s in [sec("anpa-anpa-0134", f=0, t=5000), sec("anpa-anpa-0135", f=5000, t=15000)]) + "\n")
    cp = tmp_path / "c.jsonl.gz"
    with gzip.open(cp, "wt", encoding="utf-8") as f:
        f.write(json.dumps(COURSE) + "\n")
    args = ["--waters", str(wp), "--sectors", str(sp), "--courses", str(cp), "--out-dir", str(tmp_path / "o")]
    before = pv.read_text(encoding="utf-8")
    assert P.cli(args) == 0  # default preview path = beside --waters
    assert pv.read_text(encoding="utf-8") == before
    shadow = json.loads((tmp_path / "o" / "preview_class2_physical.shadow.json").read_text(encoding="utf-8"))
    assert shadow["records"][0]["physicalCandidates"][0]["kind"] == "rivernet-course"
    assert json.loads((tmp_path / "o" / "publish_report.json").read_text())["preview_groups_replaced"] == ["colibita"]
    assert P.cli(args + ["--mode", "write"]) == 0
    assert json.loads(pv.read_text(encoding="utf-8"))["records"][0]["physicalCandidates"][0]["kind"] == "rivernet-course"
    assert P.cli(args + ["--preview", ""]) == 0
    assert "preview_groups_replaced" not in json.loads((tmp_path / "o" / "publish_report.json").read_text())


# ------------------------------------------- D8 amendment: partial switch


def test_geometryless_member_switches_alone_when_the_owner_is_blocked():
    # crisul-alb: aoja7n5d owns the line; anpa-anpa-0379 has no geometry of its own
    waters = copy.deepcopy(WATERS)
    by = {w["slug"]: w for w in waters}
    by["anpa-anpa-0379"].update({"course_frac": 0.42, "sectorStart": 0.3, "sectorEnd": 0.5})
    new, rep = run([sec("aoja7n5d", "unresolved", "low"), sec("anpa-anpa-0379")], waters=waters)
    d = by_slug(new)
    assert "geometryKind" not in d["aoja7n5d"] and d["aoja7n5d"] == by["aoja7n5d"]  # owner untouched
    part = d["anpa-anpa-0379"]
    assert part["geometryKind"] == "sector" and part["geometry"]["type"] == "LineString"
    assert (part["course_frac"], part["sectorStart"], part["sectorEnd"]) == (0.42, 0.3, 0.5)  # owner-relative kept
    assert {"slug": "anpa-anpa-0379", "riverGroup": "crisul-alb", "status": "resolved", "d8": "partial"} in rep["switched"]
    assert rep["blocked_groups"][0]["riverGroup"] == "crisul-alb"


def test_partial_switch_adds_no_fraction_fields_the_water_did_not_have():
    new, _ = run([sec("aoja7n5d", "unresolved", "low"), sec("anpa-anpa-0379")])
    part = by_slug(new)["anpa-anpa-0379"]
    assert "sectorStart" not in part and "sectorEnd" not in part


def test_member_with_its_own_legacy_line_still_waits_for_the_group():
    new, rep = run([sec("aoja7n5d"), sec("anpa-anpa-0379", "unresolved", "low")])
    assert "geometryKind" not in by_slug(new)["aoja7n5d"]
    assert {k["slug"]: k["reason"] for k in rep["kept_legacy"]}["aoja7n5d"] == "d8_group_blocked"
    assert P.has_legacy_line({"geometry": {"type": "LineString"}})
    assert not P.has_legacy_line({"geometryKind": "sector", "geometry": {"type": "LineString"}})
    assert not P.has_legacy_line({"geometry": None})
