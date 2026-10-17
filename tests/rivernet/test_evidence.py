from __future__ import annotations

import json

import pytest

from rivernet import evidence as E
from rivernet.__main__ import main


def ep(kind, name=None, conf=0.9, atype="node", aid=1, **kw):
    anchor = {"type": atype, "id": aid}
    if name:
        anchor["name"] = name
    return {"kind": kind, "m": 0.0, "confidence": conf, "anchor": anchor if atype else {}, **kw}


@pytest.mark.parametrize("kind,endpoint,spec,judet,want", [
    ("SOURCE", ep("SOURCE", atype=None), {}, "Alba", "izvoare"),
    ("MOUTH", ep("MOUTH", atype=None), {}, "Alba", "vărsare"),
    ("CONFLUENCE", ep("CONFLUENCE", atype="course", aid="rel:1"), {"target": "Mureș"}, "Alba", "confluența cu Mureș"),
    ("CONFLUENCE", ep("CONFLUENCE", "Lotrului"), {"target": "Lotru"}, "Vâlcea", "confluența cu Lotrului"),
    ("CONFLUENCE", ep("CONFLUENCE", atype="course"), {}, "Alba", "confluență"),
    ("DAM", ep("DAM", "Barajul Măneciu", atype="way"), {"target": "Măneciu"}, "Prahova", "barajul Măneciu"),
    ("DAM", {"kind": "DAM", "anchor": {"type": "way", "id": 3, "place": "Vadu Crișului"}}, {}, "Bihor", "barajul Vadu Crișului"),
    ("DAM", ep("DAM", atype="way"), {}, "Bihor", "baraj"),
    ("LAKE_UPSTREAM", ep("LAKE_UPSTREAM", "Lacul Mălaia", atype="area"), {}, "Vâlcea", "coada lacului Mălaia"),
    ("LAKE_DOWNSTREAM", ep("LAKE_DOWNSTREAM", "Lacul Gura Râului", atype="area"), {}, "Sibiu", "aval de lacul Gura Râului"),
    ("BRIDGE", ep("BRIDGE", atype="way"), {"road_ref": "DN 1", "locality_hint": "Băcăinți"}, "Alba", "podul DN 1 la Băcăinți"),
    ("BRIDGE", ep("BRIDGE", atype="way"), {"locality_hint": "Cristian"}, "Sibiu", "podul la Cristian"),
    ("BRIDGE", ep("BRIDGE", atype="way"), {}, "Sibiu", "podul"),
    ("ROAD", ep("ROAD", atype="way"), {"road_ref": "DN 67D"}, "Gorj", "drumul DN 67D"),
    ("ROAD", ep("ROAD", atype="way"), {}, "Gorj", "drum"),
    ("LOCALITY", ep("LOCALITY", "Tarcea", atype="area"), {"target": "Tarcea"}, "Bihor", "Tarcea"),
    ("LOCALITY", ep("LOCALITY", atype="node"), {}, "Bihor", "localitate"),
    ("COUNTY_LIMIT", ep("COUNTY_LIMIT", "Prahova", atype="area"), {}, "Buzău", "limita județului Prahova"),
    ("COUNTY_LIMIT", ep("COUNTY_LIMIT", atype="area"), {}, "Buzău", "limita județului Buzău"),
    ("COUNTY", ep("COUNTY", atype=None), {}, "Arad", "limita județului Arad"),
    ("BORDER", ep("BORDER", "Ungaria", atype="area"), {}, "Bihor", "frontiera cu Ungaria"),
    ("BORDER", ep("BORDER", atype="area"), {}, "Bihor", "frontieră"),
    ("WATERFALL", ep("WATERFALL", "Cascada Putnei"), {}, "Vrancea", "Cascada Putnei"),
    ("WATERFALL", ep("WATERFALL"), {}, "Vrancea", "cascadă"),
])
def test_label_table(kind, endpoint, spec, judet, want):
    assert E.label(kind, endpoint, spec, judet) == want


def test_label_falls_back_to_raw_text_then_kind():
    assert E.label("UNKNOWN", {}, {"raw": "Cheile Râmeţ"}) == "Cheile Râmeț"
    assert E.label("UNKNOWN", {}, None) == "unknown"
    assert set(E.LABELS) >= {"SOURCE", "MOUTH", "CONFLUENCE", "DAM", "LAKE_UPSTREAM", "LAKE_DOWNSTREAM", "BRIDGE",
                             "ROAD", "LOCALITY", "COUNTY_LIMIT", "BORDER", "WATERFALL"}


def sector(slug, **kw):
    s = {"slug": slug, "status": "resolved", "confidence": "high", "contract_km": 12.0, "judet": "Alba",
         "parse": {"from": {"kind": "SOURCE"}, "to": {"kind": "CONFLUENCE", "target": "Mureș"}},
         "from": ep("SOURCE", atype=None, conf=0.9),
         "to": ep("CONFLUENCE", "Mureș", atype="course", aid="rel:9", conf=0.95),
         "network_version": "ro-water-20261016"}
    s.update(kw)
    return s


def test_build_evidence_only_switched_waters_sorted():
    waters = [{"slug": "b", "geometryKind": "sector", "lengthKm": 11.4, "judet": "Alba"},
              {"slug": "a", "geometryKind": "sector", "lengthKm": 3.0, "judet": "Alba"},
              {"slug": "legacy", "judet": "Alba"},
              {"slug": "nosector", "geometryKind": "sector"}]
    ev = E.build_evidence(waters, {"a": sector("a"), "b": sector("b"), "legacy": sector("legacy")},
                          network_version="ro-water-20261016", osm_timestamp="2026-10-16T20:21:21Z")
    assert ev["schema"] == 1 and ev["osm_timestamp"] == "2026-10-16T20:21:21Z"
    assert list(ev["sectors"]) == ["a", "b"]
    b = ev["sectors"]["b"]
    assert b["from"] == {"kind": "SOURCE", "label": "izvoare", "anchor": None, "confidence": 0.9}
    assert b["to"] == {"kind": "CONFLUENCE", "label": "confluența cu Mureș", "anchor": {"type": "course", "id": "rel:9"},
                       "confidence": 0.95}
    assert (b["lengthKm"], b["contractKm"], b["status"], b["confidence"]) == (11.4, 12.0, "resolved", "high")
    assert E.dumps(ev) == E.dumps(json.loads(E.dumps(ev)))  # deterministic, round-trips


def test_cli(tmp_path):
    w = tmp_path / "waters.json"
    w.write_text(json.dumps([{"slug": "a", "geometryKind": "sector", "lengthKm": 3.0, "judet": "Alba"}]), encoding="utf-8")
    s = tmp_path / "s.jsonl"
    s.write_text(json.dumps(sector("a")) + "\n", encoding="utf-8")
    m = tmp_path / "m.json"
    m.write_text(json.dumps({"pbf": {"osm_timestamp": "2026-10-16T20:21:21Z"}}), encoding="utf-8")
    out = tmp_path / "o" / "sector-evidence.json"
    args = ["evidence", "--waters", str(w), "--sectors", str(s), "--manifest", str(m), "--out", str(out)]
    assert main(args) == 0
    first = out.read_bytes()
    ev = json.loads(first)
    assert ev["network_version"] == "ro-water-20261016" and list(ev["sectors"]) == ["a"]
    assert main(args) == 0 and out.read_bytes() == first
    assert main(["evidence", "--waters", str(tmp_path / "none"), "--out", str(out)]) == 1
