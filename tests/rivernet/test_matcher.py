from __future__ import annotations

import gzip
import json

import pytest

from rivernet import matcher
from rivernet.matcher import contract_km, index_courses, match
from rivernet.overrides import (
    load_course_overrides,
    load_endpoint_overrides,
    validate_course_overrides,
    validate_endpoint_overrides,
)
from rivernet.textnorm import river_key


def course(cid, name, counties, length_km=50.0, aliases=(), junctions=(), receives_into=None):
    return {
        "course_id": cid,
        "name": name,
        "name_key": river_key(name),
        "aliases": list(aliases),
        "length_m": length_km * 1000,
        "counties": [{"county": c, "m_from": 0.0, "m_to": 1.0} for c in counties],
        "junctions": list(junctions),
        "receives_into": receives_into,
    }


def water(name, judet, km="40 km", slug="w1"):
    return {"slug": slug, "name": name, "judet": judet, "dimensiune": km, "subtype": "rau"}


def test_contract_km():
    assert contract_km("47km") == 47
    assert contract_km("61 Km") == 61
    assert contract_km("12,5 km") == 12.5
    assert contract_km("50 ha") is None
    assert contract_km("") is None and contract_km(None) is None


def test_siret_vs_siretel_exact_wins():
    cs = [course("a", "Siret", ["Suceava"]), course("b", "Sirețel", ["Suceava"])]
    r = match(water("Siret", "Suceava"), cs)
    assert r.course_id == "a" and r.method == "name+county"


def test_somes_vs_somesul_mic():
    cs = [course("a", "Someș", ["Cluj"]), course("b", "Someșul Mic", ["Cluj"])]
    assert match(water("Someșul Mic", "Cluj"), cs).course_id == "b"
    assert match(water("Râul Someș", "Cluj"), cs).course_id == "a"


def test_bistrita_three_counties():
    cs = [
        course("bn", "Bistrița", ["Neamț", "Bacău"]),
        course("bm", "Bistrița", ["Maramureș"]),
        course("bb", "Bistrița", ["Bistrița-Năsăud"]),
    ]
    assert match(water("Bistrița", "Maramureș"), cs).course_id == "bm"
    assert match(water("Bistrița", "Bacău"), cs).course_id == "bn"
    assert match(water("Bistrița", "Bistrița-Năsăud"), cs).course_id == "bb"


def test_jiu_vs_jiul_de_vest():
    cs = [course("j", "Jiu", ["Gorj"]), course("jv", "Jiul de Vest", ["Hunedoara"])]
    assert match(water("Jiul de Vest", "Hunedoara"), cs).course_id == "jv"
    assert match(water("Râul Jiu", "Gorj"), cs).course_id == "j"


def test_county_filter_blocks_namesake_elsewhere():
    cs = [course("a", "Valea Mare", ["Cluj"])]
    r = match(water("Valea Mare", "Alba"), cs)
    assert r.course_id is None and r.method == "no_county_match"


def test_county_hook_allows_near_border():
    cs = [course("a", "Valea Mare", ["Cluj"])]
    r = match(water("Valea Mare", "Alba"), cs, county_ok=lambda c, j: True)
    assert r.course_id == "a"


def test_course_without_counties_is_not_filtered():
    cs = [course("a", "Olt", [])]
    r = match(water("Olt", "Covasna"), cs)
    assert r.course_id == "a" and "county_unknown" in r.candidates[0][2]


def test_no_candidate():
    assert match(water("Zzzzz", "Alba"), [course("a", "Olt", ["Alba"])]).method == "no_candidate"


def test_fuzzy_match_when_no_exact():
    cs = [course("a", "Ialomița", ["Dâmbovița"])]
    r = match(water("Ialomiţza", "Dâmbovița"), cs)
    assert r.course_id == "a" and r.method == "fuzzy+county"


def test_ambiguous_two_equal_courses_same_county():
    cs = [course("a", "Valea Rea", ["Alba"]), course("b", "Valea Rea", ["Alba"])]
    r = match(water("Valea Rea", "Alba"), cs)
    assert r.course_id is None and r.method == "ambiguous"
    assert {c[0] for c in r.candidates} == {"a", "b"}


def test_length_fit_disambiguates():
    cs = [course("short", "Valea Rea", ["Alba"], length_km=5), course("long", "Valea Rea", ["Alba"], length_km=45)]
    r = match(water("Valea Rea", "Alba", km="40 km"), cs)
    assert r.course_id == "long"


def test_includes_tributaries_ignores_length_fit():
    cs = [course("short", "Valea Rea", ["Alba"], length_km=5)]
    spec = {"includes_tributaries": True}
    r = match(water("Valea Rea", "Alba", km="40 km"), cs, spec=spec)
    assert r.score == pytest.approx(0.6 + 0.2)


def test_mention_term_breaks_tie():
    j = [{"node": 1, "m": 10.0, "tributary_course_id": "name:trotus:n5", "side": "in"}]
    cs = [course("a", "Valea Rea", ["Alba"], junctions=j), course("b", "Valea Rea", ["Alba"])]
    spec = {"from": None, "to": {"kind": "CONFLUENCE", "target": "Râul Trotuș"}}
    r = match(water("Valea Rea", "Alba"), cs, spec=spec)
    assert r.course_id == "a"


def test_override_wins_even_if_name_differs():
    r = match(water("Qwerty", "Alba", slug="s"), [], {"s": {"course_id": "rel:9"}})
    assert (r.course_id, r.method, r.score) == ("rel:9", "override", 1.0)


def test_alias_matches_with_lower_name_score():
    cs = [course("a", "Maros", ["Alba"], aliases=["Mureș"])]
    r = match(water("Mureș", "Alba"), cs)
    assert r.course_id == "a" and r.score < 1.0


def test_indexed_lookup_equals_scan():
    cs = [course("a", "Siret", ["Suceava"]), course("b", "Sirețel", ["Suceava"])]
    idx = index_courses(cs)
    assert match(water("Siret", "Suceava"), [], by_key=idx).course_id == "a"
    assert match(water("Ialomiţza", "Dâmbovița"), [], by_key=index_courses([course("z", "Ialomița", ["Dâmbovița"])])).course_id == "z"


# ------------------------------------------------------------------ registries

GOOD = {"slug": "s", "reason": "r", "reviewer": "me", "date": "2026-10-17"}


def test_committed_registries_valid_and_empty():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "data" / "sectors"
    c = json.loads((root / "course_overrides.json").read_text(encoding="utf-8"))
    e = json.loads((root / "endpoint_overrides.json").read_text(encoding="utf-8"))
    assert validate_course_overrides(c) == [] and c["overrides"] == []
    assert validate_endpoint_overrides(e) == [] and e["overrides"] == []


def test_course_override_schema():
    ok = {"schema": 1, "overrides": [{**GOOD, "course_id": "rel:1"}]}
    assert validate_course_overrides(ok) == []
    assert validate_course_overrides([]) != []
    assert validate_course_overrides({"schema": 2, "overrides": []}) != []
    assert validate_course_overrides({"schema": 1, "overrides": [{**GOOD}]}) != []
    assert validate_course_overrides({"schema": 1, "overrides": [{**GOOD, "course_id": "x", "date": "17/10/2026"}]}) != []
    assert validate_course_overrides({"schema": 1, "overrides": [{**GOOD, "course_id": "x", "extra": 1}]}) != []
    dup = {"schema": 1, "overrides": [{**GOOD, "course_id": "x"}, {**GOOD, "course_id": "y"}]}
    assert any("duplicate" in e for e in validate_course_overrides(dup))


def test_endpoint_override_schema():
    def doc(**kw):
        return {"schema": 1, "overrides": [{**GOOD, "end": "from", "anchor": {"type": "measure", "m": 5}, **kw}]}

    assert validate_endpoint_overrides(doc()) == []
    assert validate_endpoint_overrides(doc(anchor={"type": "node", "id": 5})) == []
    assert validate_endpoint_overrides(doc(end="middle")) != []
    assert validate_endpoint_overrides(doc(anchor={"type": "node"})) != []
    assert validate_endpoint_overrides(doc(anchor={"type": "measure", "m": -1})) != []
    assert validate_endpoint_overrides(doc(anchor={"type": "bogus"})) != []
    assert validate_endpoint_overrides(doc(anchor="x")) != []
    assert validate_endpoint_overrides({"schema": 1, "overrides": [doc()["overrides"][0]] * 2}) != []


def test_loaders(tmp_path):
    assert load_course_overrides(tmp_path / "nope.json") == {}
    assert load_endpoint_overrides(tmp_path / "nope.json") == {}
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema": 1, "overrides": [{**GOOD, "course_id": "rel:1"}]}))
    assert load_course_overrides(p)["s"]["course_id"] == "rel:1"
    q = tmp_path / "e.json"
    q.write_text(json.dumps({"schema": 1, "overrides": [{**GOOD, "end": "to", "anchor": {"type": "measure", "m": 1}}]}))
    assert ("s", "to") in load_endpoint_overrides(q)
    p.write_text("{\"schema\": 9, \"overrides\": []}")
    with pytest.raises(ValueError):
        load_course_overrides(p)


def test_cli(tmp_path):
    cs = [course("a", "Siret", ["Suceava"]), course("b", "Valea Rea", ["Alba"]), course("c", "Valea Rea", ["Alba"])]
    cp = tmp_path / "courses.jsonl.gz"
    with gzip.open(cp, "wt", encoding="utf-8") as f:
        for c in cs:
            f.write(json.dumps(c) + "\n")
    waters = [
        water("Siret", "Suceava", slug="s1"),
        water("Valea Rea", "Alba", slug="s2"),
        water("Nimic", "Alba", slug="s3"),
        {"slug": "lac", "name": "Siret", "judet": "Suceava", "subtype": "lac"},
    ]
    wp = tmp_path / "w.json"
    wp.write_text(json.dumps(waters))
    out = tmp_path / "m.jsonl"
    args = ["--courses", str(cp), "--waters", str(wp), "--parsed", str(tmp_path / "none"),
            "--overrides", str(tmp_path / "none2"), "--out", str(out)]
    assert matcher.cli(args) == 0
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert [(r["slug"], r["method"]) for r in rows] == [
        ("s1", "name+county"), ("s2", "ambiguous"), ("s3", "no_candidate")]
    assert matcher.cli(["--courses", str(tmp_path / "missing.gz")]) == 1


def test_definite_article_variant_matches():
    cs = [course("a", "Gurghiu", ["Mureș"])]
    r = match(water("Râul Gurghiul mijlociu", "Mureș"), cs)
    assert r.course_id == "a" and r.score < 1.0
    assert match(water("Râul Gurghiu", "Mureș"), [course("b", "Gurghiul", ["Mureș"])], by_key=None).course_id == "b"
    assert match(water("Gurghiu", "Mureș"), [], by_key=index_courses([course("b", "Gurghiul", ["Mureș"])])).course_id == "b"


# ------------------------------------------------- fallback tiers (T6.5)

from rivernet.matcher import index_stems  # noqa: E402


def anar(cid, name, counties, **kw):
    return {**course(cid, name, counties, **kw), "source": "anar"}


def tiered(w, cs):
    return match(w, [], by_key=index_courses(cs), by_stem=index_stems(cs))


def test_tier1_osm_name_beats_fallback():
    cs = [course("osm", "Lisa", ["Brașov"]), anar("anar:RO1", "Lisa", ["Brașov"])]
    r = tiered(water("Râul Lisa", "Brașov"), cs)
    assert r.course_id == "osm" and r.method == "name+county"
    assert all(c[0] != "anar:RO1" for c in r.candidates)


def test_tier2_osm_by_stem():
    cs = [course("osm", "Pojorâta", ["Brașov"]), anar("anar:RO1", "Pojorâta", ["Brașov"])]
    r = tiered(water("Valea Pojorâtei", "Brașov"), cs)
    assert r.course_id == "osm" and r.method == "stem+county"


def test_tier3_fallback_by_stem_and_county():
    cs = [anar("anar:RO1", "Pojorâta", ["Brașov"]), anar("anar:RO2", "Pojorâta", ["Suceava"])]
    r = tiered(water("Valea Pojorâtei", "Brașov"), cs)
    assert r.course_id == "anar:RO1" and r.method == "anar+county"


def test_tier3_fuzzy_stem():
    cs = [anar("anar:RO1", "Sighisel", ["Bihor"])]
    r = tiered(water("Valea Sighiștelului", "Bihor"), cs)
    assert r.course_id == "anar:RO1" and r.method == "anar_fuzzy+county"


def test_tiers_report_county_mismatch_and_no_candidate():
    cs = [anar("anar:RO1", "Pojorâta", ["Suceava"])]
    assert tiered(water("Valea Pojorâtei", "Brașov"), cs).method == "no_county_match"
    assert tiered(water("Râul Nimic", "Brașov"), cs).method == "no_candidate"


def test_ambiguous_tier1_is_final():
    cs = [course("a", "Lisa", ["Brașov"]), course("b", "Lisa", ["Brașov"]), anar("anar:RO1", "Lisa", ["Brașov"])]
    assert tiered(water("Valea Lisei", "Brașov"), cs).method == "ambiguous"


def test_fallback_courses_are_ignored_without_stem_index():
    cs = [anar("anar:RO1", "Lisa", ["Brașov"])]
    assert match(water("Lisa", "Brașov"), cs).method == "no_candidate"
    assert index_courses(cs) == {}
    assert set(index_stems(cs + [course("x", "Lisa", ["Alba"], aliases=["Lisa Mare"])])) == {"lis", "lis mar"}


def test_osm_fragment_is_replaced_by_longer_fallback_course():
    cs = [course("osm", "Jolotca", ["Harghita"], length_km=5.2), anar("anar:RO1", "Jolotca", ["Harghita"], length_km=15.9)]
    r = tiered(water("Râul Jolotca", "Harghita", km="15 km"), cs)
    assert r.course_id == "anar:RO1" and r.method == "anar_longer+county"
    assert [c[0] for c in r.candidates] == ["anar:RO1", "osm"]  # the OSM fragment stays an alternative


def test_fragment_swap_needs_a_fitting_or_much_longer_course():
    w = water("Râul Siriu", "Buzău", km="38 km")
    short = [course("osm", "Siriu", ["Buzău"], length_km=8.5), anar("anar:RO1", "Siriu", ["Buzău"], length_km=12.0)]
    assert tiered(w, short).course_id == "osm"  # 12 km: neither >= 0.8 x 38 nor >= 2 x 8.5
    double = [course("osm", "Siriu", ["Buzău"], length_km=8.5), anar("anar:RO1", "Siriu", ["Buzău"], length_km=18.0)]
    assert tiered(w, double).course_id == "anar:RO1"


def test_no_fragment_swap_when_osm_fits_or_contract_unknown_or_tributaries():
    cs = [course("osm", "Jolotca", ["Harghita"], length_km=12.0), anar("anar:RO1", "Jolotca", ["Harghita"], length_km=15.9)]
    assert tiered(water("Râul Jolotca", "Harghita", km="15 km"), cs).course_id == "osm"
    frag = [course("osm", "Jolotca", ["Harghita"], length_km=2.0), anar("anar:RO1", "Jolotca", ["Harghita"], length_km=15.9)]
    assert tiered(water("Râul Jolotca", "Harghita", km=""), frag).course_id == "osm"
    r = match(water("Râul Jolotca", "Harghita", km="15 km"), [], spec={"includes_tributaries": True},
              by_key=index_courses(frag), by_stem=index_stems(frag))
    assert r.course_id == "osm"
    other_county = [course("osm", "Jolotca", ["Harghita"], length_km=2.0), anar("anar:RO1", "Jolotca", ["Mureș"], length_km=15.9)]
    assert tiered(water("Râul Jolotca", "Harghita", km="15 km"), other_county).course_id == "osm"


def test_stem_tier_fragment_is_also_replaced():
    cs = [course("osm", "Pojorâta", ["Brașov"], length_km=2.0), anar("anar:RO1", "Pojorâta", ["Brașov"], length_km=10.0)]
    r = tiered(water("Valea Pojorâtei", "Brașov", km="10 km"), cs)
    assert r.course_id == "anar:RO1" and r.method == "anar_longer+county"
