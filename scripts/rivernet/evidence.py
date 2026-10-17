"""``public/data/sector-evidence.json`` for switched waters (plan T4.3).

One entry per pre-cut sector: each endpoint's kind, a short Romanian label
("confluența cu Mureș", "podul DN 1 la Băcăinți", "izvoare"), its anchor
(type + id only) and confidence, plus drawn vs contract km. Labels come from
``LABELS`` - a template per endpoint kind - filled from the resolved anchor
name, else the parsed ``limite`` target.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Mapping, Sequence

from .textnorm import fix_diacritics

SCHEMA = 1

_PREFIX = {
    "lake": re.compile(r"^(lacul|lac|acumularea|acumulare)\s+", re.I),
    "dam": re.compile(r"^(barajul|baraj)\s+", re.I),
}


def _strip(kind: str, name: str) -> str:
    return _PREFIX[kind].sub("", name).strip()


def _name(ep: Mapping[str, Any], spec: Mapping[str, Any]) -> str:
    """Anchor name when the resolver kept one, else the parsed target."""
    anchor = ep.get("anchor") or {}
    return fix_diacritics(anchor.get("name") or spec.get("target") or anchor.get("place") or "").strip()


def _bridge(ep: Mapping[str, Any], spec: Mapping[str, Any]) -> str:
    ref = (spec.get("road_ref") or "").strip()
    place = fix_diacritics(spec.get("locality_hint") or spec.get("target") or "").strip()
    head = f"podul {ref}" if ref else "podul"
    return f"{head} la {place}" if place else head


def _dam(ep: Mapping[str, Any], spec: Mapping[str, Any]) -> str:
    name = _name(ep, spec)
    return f"barajul {_strip('dam', name)}" if name else "baraj"


# kind -> label template (ep = resolved endpoint dict, spec = parsed EndpointSpec dict, judet)
LABELS: dict[str, Callable[[Mapping[str, Any], Mapping[str, Any], str], str]] = {
    "SOURCE": lambda ep, spec, judet: "izvoare",
    "MOUTH": lambda ep, spec, judet: "vărsare",
    "CONFLUENCE": lambda ep, spec, judet: f"confluența cu {_name(ep, spec)}" if _name(ep, spec) else "confluență",
    "DAM": lambda ep, spec, judet: _dam(ep, spec),
    "LAKE_UPSTREAM": lambda ep, spec, judet: f"coada lacului {_strip('lake', _name(ep, spec))}".strip(),
    "LAKE_DOWNSTREAM": lambda ep, spec, judet: f"aval de lacul {_strip('lake', _name(ep, spec))}".strip(),
    "BRIDGE": lambda ep, spec, judet: _bridge(ep, spec),
    "ROAD": lambda ep, spec, judet: f"drumul {spec.get('road_ref')}" if spec.get("road_ref") else "drum",
    "LOCALITY": lambda ep, spec, judet: _name(ep, spec) or "localitate",
    "COUNTY_LIMIT": lambda ep, spec, judet: f"limita județului {_name(ep, spec) or judet}",
    "COUNTY": lambda ep, spec, judet: f"limita județului {judet}",
    "BORDER": lambda ep, spec, judet: f"frontiera cu {_name(ep, spec)}" if _name(ep, spec) else "frontieră",
    "WATERFALL": lambda ep, spec, judet: _name(ep, spec) or "cascadă",
}


def label(kind: str, ep: Mapping[str, Any], spec: Mapping[str, Any] | None, judet: str = "") -> str:
    fn = LABELS.get(kind)
    spec = spec or {}
    text = fn(ep, spec, judet) if fn else ""
    return text or fix_diacritics(spec.get("raw") or "").strip() or kind.lower()


def _end(ep: Mapping[str, Any], spec: Mapping[str, Any] | None, judet: str) -> dict[str, Any]:
    anchor = ep.get("anchor") or {}
    return {
        "kind": ep["kind"],
        "label": label(ep["kind"], ep, spec, judet),
        "anchor": {"type": anchor.get("type"), "id": anchor.get("id")} if anchor.get("type") else None,
        "confidence": ep.get("confidence"),
    }


def build_evidence(
    new_waters: Sequence[Mapping[str, Any]],
    sectors: Mapping[str, Mapping[str, Any]],
    *,
    network_version: str,
    osm_timestamp: str | None,
) -> dict[str, Any]:
    """Evidence for every water `publish` switched (``geometryKind == "sector"``)."""
    out: dict[str, Any] = {}
    for w in sorted(new_waters, key=lambda x: x["slug"]):
        if w.get("geometryKind") != "sector":
            continue
        s = sectors.get(w["slug"])
        if not s or not s.get("from") or not s.get("to"):
            continue
        parse = s.get("parse") or {}
        judet = w.get("judet") or s.get("judet") or ""
        out[w["slug"]] = {
            "from": _end(s["from"], parse.get("from"), judet),
            "to": _end(s["to"], parse.get("to"), judet),
            "lengthKm": w.get("lengthKm"),
            "contractKm": s.get("contract_km"),
            "status": s.get("status"),
            "confidence": s.get("confidence"),
        }
    return {"schema": SCHEMA, "network_version": network_version, "osm_timestamp": osm_timestamp, "sectors": out}


def dumps(evidence: Mapping[str, Any]) -> str:
    return json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cli(argv: list[str]) -> int:
    """`python -m rivernet evidence`: write the evidence for a published waters file."""
    import argparse
    import sys
    from pathlib import Path

    ap = argparse.ArgumentParser(prog="rivernet evidence")
    ap.add_argument("--waters", required=True, help="waters.json after `publish` (or waters.shadow.json)")
    ap.add_argument("--sectors", default="data/sectors/sectors.jsonl")
    ap.add_argument("--manifest", default="data/rivernet/input_manifest.json")
    ap.add_argument("--out", required=True, help="e.g. public/data/sector-evidence.json at cutover")
    ns = ap.parse_args(argv)
    for p in (ns.waters, ns.sectors):
        if not Path(p).exists():
            print(f"rivernet evidence: {p} missing", file=sys.stderr)
            return 1
    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    sectors = {r["slug"]: r for r in map(json.loads, Path(ns.sectors).read_text(encoding="utf-8").splitlines()) if r}
    ts = None
    if Path(ns.manifest).exists():
        ts = (json.loads(Path(ns.manifest).read_text(encoding="utf-8")).get("pbf") or {}).get("osm_timestamp")
    versions = sorted({s.get("network_version") or "" for s in sectors.values()} - {""})
    ev = build_evidence(waters, sectors, network_version=versions[-1] if versions else "", osm_timestamp=ts)
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(dumps(ev), encoding="utf-8", newline="\n")
    print(json.dumps({"sectors": len(ev["sectors"]), "out": ns.out}))
    return 0
