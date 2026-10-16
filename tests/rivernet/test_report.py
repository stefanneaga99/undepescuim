from __future__ import annotations

import gzip
import json

import pytest

from rivernet import report as RP
from rivernet import review_page as RV
from test_resolvers import LAT, LEN, course


def sec(slug, status="resolved", conf="high", ratio=1.0, judet="Alba", f=0.0, t=10000.0, reasons=(), cid="name:test:n1"):
    return {"slug": slug, "name": slug.upper(), "judet": judet, "limite": "x", "contract_km": 10.0,
            "status": status, "confidence": conf, "km_ratio": ratio, "reasons": list(reasons),
            "from": {"m": f, "kind": "SOURCE", "method": "source", "confidence": 0.9},
            "to": {"m": t, "kind": "MOUTH", "method": "mouth", "confidence": 0.9},
            "length_m": t - f, "course": {"course_id": cid}}


SECTORS = [
    sec("a", ratio=0.4, reasons=["overlap:b", "swapped_order"]),
    sec("b", "review", "low", ratio=0.9, judet="Cluj", reasons=["overlap:a", "endpoint_ambiguous:to"]),
    sec("c", ratio=1.0, f=2000, t=9000),
    sec("d", ratio=1.4), sec("e", ratio=2.5), sec("u", "unresolved", "low", ratio=None, reasons=["limite_unusable"]),
]
SECTORS[-1]["from"] = SECTORS[-1]["to"] = None


def test_progress_counts():
    p = RP.build_progress(SECTORS)
    assert p["total"] == 6 and p["by_status"] == {"resolved": 4, "review": 1, "unresolved": 1}
    assert p["by_status_confidence"]["resolved/high"] == 4
    assert p["km_ratio_histogram"] == {"<0.5": 1, "0.5-0.8": 0, "0.8-1.25": 2, "1.25-2": 1, ">2": 1, "unknown": 1}
    assert p["per_county"]["Alba"] == {"total": 5, "resolved": 4} and p["per_county"]["Cluj"] == {"total": 1, "resolved": 0}
    reasons = dict(map(tuple, p["top_reasons"]))
    assert reasons["overlap"] == 2 and reasons["limite_unusable"] == 1 and reasons["endpoint_ambiguous"] == 1


def test_top_reasons_capped_and_sorted():
    many = [sec(f"s{i}", reasons=[f"r{i}"] * 1) for i in range(30)] + [sec("z", reasons=["common"]), sec("y", reasons=["common"])]
    p = RP.build_progress(many)
    assert len(p["top_reasons"]) == 15 and p["top_reasons"][0] == ["common", 2]


def test_bucket_edges():
    p = RP.build_progress([sec("x", ratio=0.5), sec("y", ratio=0.8), sec("z", ratio=1.25), sec("w", ratio=2.0)])
    assert p["km_ratio_histogram"] == {"<0.5": 0, "0.5-0.8": 1, "0.8-1.25": 1, "1.25-2": 1, ">2": 1}


def test_chord_check_and_shadow():
    c = course()
    water = {"slug": "a", "geometry": {"type": "LineString", "coordinates": c["geometry"]["coordinates"]}}
    shifted = {"slug": "c", "geometry": {"type": "LineString",
                                         "coordinates": [[x, y + 0.001] for x, y in c["geometry"]["coordinates"]]}}
    p = RP.build_progress(SECTORS[:3] + SECTORS[-1:], {"a": water, "c": shifted}, {c["course_id"]: c})
    assert p["chord_check"]["checked"] == 2 and 300 < p["chord_check"]["max_segment_m"] < 500
    rows = {r["slug"]: r for r in p["shadow"]["rows"]}
    assert set(rows) == {"a", "c"}  # b has no legacy geometry entry, u is unresolved
    # symmetric Hausdorff: the legacy line extends past the 10 km sector by LEN - 10 km
    assert rows["a"]["hausdorff_m"] == pytest.approx(LEN - 10000, abs=200)
    assert rows["c"]["hausdorff_m"] == pytest.approx(LEN - 9000, abs=300)
    assert rows["a"]["new_km"] == 10.0 and rows["a"]["old_km"] > 30


def test_hausdorff_known_values():
    a = [[(24.0, LAT), (24.01, LAT)]]
    assert RP.hausdorff_m(a, a) == pytest.approx(0.0, abs=0.01)
    b = [[(24.0, LAT + 0.001), (24.01, LAT + 0.001)]]
    assert RP.hausdorff_m(a, b) == pytest.approx(111.2, abs=1.5)
    assert RP.hausdorff_m([], a) is None


def test_legacy_lines_slice_flagged_approximate():
    w = {"geometry": {"type": "LineString", "coordinates": [[24.0, LAT], [24.1, LAT]]}, "sectorStart": 0.0, "sectorEnd": 0.5}
    lines, approx = RP.legacy_lines(w)
    assert approx and lines[0][-1][0] == pytest.approx(24.05, abs=1e-4)
    lines, approx = RP.legacy_lines({"geometry": {"type": "MultiLineString", "coordinates": [[[1, 1], [2, 2]], [[3, 3], [4, 4]]]}})
    assert not approx and len(lines) == 2
    assert RP.legacy_lines({}) == ([], False)
    assert RP.flatten_lines({"type": "Polygon", "coordinates": []}) == []


def test_markdown_renders_tables():
    md = RP.markdown(RP.build_progress(SECTORS))
    assert "| resolved | 4 |" in md and "| Alba | 4/5 |" in md and "km_ratio" in md


def test_review_page_contains_every_slug_and_escapes():
    c = course()
    secs = [sec("a"), sec("b", "review", "low", judet="Cluj"), sec("evil", judet="Alba")]
    secs[2]["name"] = "</script><script>alert(1)</script>"
    html_all = RV.render(secs, {}, {c["course_id"]: c})
    assert html_all.startswith("<!doctype html>") and "leaflet/1.9.4/leaflet.min.js" in html_all
    for slug in ("a", "b", "evil"):
        assert f'"slug":"{slug}"' in html_all
    assert "</script><script>alert(1)" not in html_all
    only = RV.render(secs, {}, {c["course_id"]: c}, county="Cluj")
    assert '"slug":"b"' in only and '"slug":"a"' not in only


def test_cli_report_and_review(tmp_path):
    c = course()
    cp = tmp_path / "courses.jsonl.gz"
    with gzip.open(cp, "wt", encoding="utf-8") as f:
        f.write(json.dumps(c) + "\n")
    sp = tmp_path / "s.jsonl"
    sp.write_text("\n".join(json.dumps(s) for s in SECTORS[:3]) + "\n")
    wp = tmp_path / "w.json"
    wp.write_text("[]")
    out = tmp_path / "progress.json"
    assert RP.cli(["--sectors", str(sp), "--courses", str(cp), "--waters", str(wp), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["total"] == 3
    assert RP.cli(["--sectors", str(tmp_path / "none")]) == 1
    rd = tmp_path / "review"
    assert RV.cli(["--all", "--sectors", str(sp), "--courses", str(cp), "--waters", str(wp), "--out-dir", str(rd)]) == 0
    assert sorted(p.name for p in rd.iterdir()) == ["alba.html", "cluj.html"]
    assert RV.cli(["--county", "Alba", "--sectors", str(tmp_path / "none"), "--courses", str(cp)]) == 1
