"""Table-driven tests for the rule-based `limite` parser (plan T3.1).

Cases live in tests/fixtures/rivernet/limits_cases.json and are hand-labelled
from real strings; they must never be regenerated from parser output.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rivernet.limits_parser import parse_limits
from rivernet.textnorm import fold

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "rivernet" / "limits_cases.json")
    .read_text(encoding="utf-8")
)["cases"]

# Cases the rule-based parser knowingly gets wrong; kept in the table so a fix
# flips them to XPASS (strict) and forces removal from this dict.
KNOWN_FAILURES: dict[str, str] = {}


def _ep_diff(exp: dict, got: dict | None) -> list[str]:
    if got is None:
        return ["endpoint missing"]
    errs = []
    if exp["kind"] != got["kind"]:
        errs.append(f"kind {got['kind']} != {exp['kind']}")
    if exp["qualifier"] != got["qualifier"]:
        errs.append(f"qualifier {got['qualifier']} != {exp['qualifier']}")
    for k in ("target", "locality_hint", "road_ref"):
        e, g = exp.get(k), got.get(k)
        if (fold(e) if e else None) != (fold(g) if g else None):
            errs.append(f"{k} {g!r} != {e!r}")
    return errs


def diff(case: dict) -> list[str]:
    got = parse_limits(case["raw"]).to_dict()
    errs = []
    if got["scope"] != case["scope"]:
        return [f"scope {got['scope']} != {case['scope']}"]
    if case["scope"] == "interval":
        for side in ("from", "to"):
            errs += [f"{side}: {e}" for e in _ep_diff(case[side], got[side])]
    elif case["scope"] == "whole_county":
        if fold(got["county"] or "") != fold(case["county"]):
            errs.append(f"county {got['county']!r} != {case['county']!r}")
    elif case["scope"] == "locality_list":
        if [fold(x) for x in got["localities"]] != [fold(x) for x in case["localities"]]:
            errs.append(f"localities {got['localities']!r}")
    if case.get("includes_tributaries") and not got["includes_tributaries"]:
        errs.append("tributaries flag missing")
    return errs


def test_table_size():
    assert len(CASES) >= 150


def test_pass_rate():
    failures = [(c["raw"], diff(c)) for c in CASES if diff(c)]
    rate = 1 - len(failures) / len(CASES)
    assert rate >= 0.95, f"{rate:.1%} passing; failures: {failures}"


@pytest.mark.parametrize("case", CASES)
def test_case(case):
    if case["raw"] in KNOWN_FAILURES:
        pytest.xfail(KNOWN_FAILURES[case["raw"]])
    assert diff(case) == []


def test_never_raises_on_garbage():
    for s in ["", " ", "—", "((", "–", "a-b-c-d-e", "izvoare -", "- conf.", "\u0000"]:
        spec = parse_limits(s)
        assert spec.scope in {"empty", "whole_course", "whole_county", "locality_list", "interval", "unparsed"}


def test_cli_writes_outputs(tmp_path):
    from rivernet.limits_parser import cli

    waters = [
        {"slug": "b", "name": "B", "subtype": "rau", "limite": "Izvoare - conf. râul Olt"},
        {"slug": "a", "name": "A", "subtype": "rau", "limite": "Pe raza județului Arad"},
        {"slug": "l", "name": "L", "subtype": "lac", "limite": "x"},
        {"slug": "c", "name": "C", "subtype": "rau", "limite": "Bălan"},
    ]
    w = tmp_path / "w.json"
    w.write_text(json.dumps(waters), encoding="utf-8")
    assert cli(["--waters", str(w), "--out-dir", str(tmp_path / "o")]) == 0
    rows = [json.loads(x) for x in (tmp_path / "o" / "limits_parsed.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["slug"] for r in rows] == ["a", "b", "c"]
    summ = json.loads((tmp_path / "o" / "limits_parsed_summary.json").read_text(encoding="utf-8"))
    assert summ["total"] == 3 and summ["unparsedOrUnknown"] == 1
    assert summ["scopes"] == {"interval": 1, "unparsed": 1, "whole_county": 1}


def test_committed_parse_output_is_current():
    from rivernet.limits_parser import parse_limits as p

    root = Path(__file__).resolve().parents[2]
    rows = [json.loads(x) for x in (root / "data/sectors/limits_parsed.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows and all(p(r["raw"]).to_dict()["scope"] == r["spec"]["scope"] for r in rows[:200])
    summ = json.loads((root / "data/sectors/limits_parsed_summary.json").read_text(encoding="utf-8"))
    assert summ["unparsedOrUnknownShare"] < 0.12
