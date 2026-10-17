"""Sector assembly, status and validation (plan T3.4).

``resolve_sector`` turns (water, parsed limit, matched course) into a
``SectorRecord`` dict (plan §3.5); ``flag_overlaps`` adds the cross-sector
overlap check; ``cli`` is ``python -m rivernet resolve``.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from .matcher import contract_km
from .resolvers import Candidate, Context, resolve_endpoint
from .textnorm import fold

SAME_POINT_M = 200.0
AMBIGUOUS_GAP = 0.1
AMBIGUOUS_M = 200.0
# A rivernet course joins OSM ways only at shared nodes and records every gap
# bridge as a synthetic span, so a long segment outside those spans is a
# coarsely mapped OSM way, not a chord across a gap. Over COARSE_SEGMENT_M it
# is reported (non-blocking); over MAX_SEGMENT_M it is a blocking invariant.
COARSE_SEGMENT_M = 1000.0
MAX_SEGMENT_M = 5000.0
COUNTY_BUFFER_M = 500.0
BAND_RESOLVED = (0.6, 1.6)
BAND_HIGH = (0.8, 1.25)
MIN_CONF_RESOLVED = 0.6
MIN_CONF_HIGH = 0.8
OVERLAP_REVIEW_SHARE = 0.5


# ---------------------------------------------------------------- endpoint dicts


def _ep(kind: str, c: Candidate) -> dict[str, Any]:
    return {"m": round(c.m, 1), "kind": kind, "anchor": c.anchor, "confidence": c.confidence,
            "method": c.method, "dist_m": None if c.dist_m is None else round(c.dist_m, 1)}


def _override_candidate(ov: Mapping[str, Any], course: Mapping[str, Any], ctx: Context, role: str) -> Candidate | None:
    a = ov["anchor"]
    line = ctx.line(course)
    t = a["type"]
    if t == "measure":
        m = float(a["m"])
        if m > course["length_m"]:
            return None
        return Candidate(m, 1.0, "override", {"type": "measure"})
    if t == "node":
        pt = ctx.node_coords.get(a["id"])
        if pt is None:
            return None
        m, d = line.locate(*pt)
        return Candidate(m, 1.0, "override", {"type": "node", "id": a["id"]}, d)
    if t == "way":
        pts = ctx.way_coords.get(a["id"])
        if not pts:
            return None
        m, d = min((line.locate(*p) for p in pts), key=lambda x: x[1])
        return Candidate(m, 1.0, "override", {"type": "way", "id": a["id"]}, d)
    area = ctx.area_by_id.get(str(a["id"]))
    if area is None:
        return None
    from .courses import county_intervals

    iv = county_intervals(line, area.poly)
    if not iv:
        return None
    return Candidate(iv[0][0] if role == "from" else iv[-1][1], 1.0, "override", {"type": "area", "id": a["id"]})


def _pick(cands: list[Candidate]) -> tuple[Candidate | None, list[str]]:
    if not cands:
        return None, []
    reasons = []
    if len(cands) > 1 and cands[0].confidence - cands[1].confidence < AMBIGUOUS_GAP \
            and abs(cands[0].m - cands[1].m) > AMBIGUOUS_M:
        reasons.append("ambiguous")
    return cands[0], reasons


# ------------------------------------------------------------------- the record


def _base(water: Mapping[str, Any], spec: Mapping[str, Any], match: Mapping[str, Any], network_version: str) -> dict[str, Any]:
    km = contract_km(water.get("dimensiune"))
    return {
        "slug": water["slug"], "name": water.get("name"), "judet": water.get("judet"),
        "limite": water.get("limite") or "", "contract_km": km,
        "includes_tributaries": bool(spec.get("includes_tributaries")),
        "parse": {"scope": spec.get("scope"), "from": spec.get("from"), "to": spec.get("to")},
        "course": {"course_id": match.get("course_id"), "match_score": match.get("score"), "method": match.get("method")},
        "from": None, "to": None, "length_m": None, "km_ratio": None,
        "status": "unresolved", "confidence": "low", "reasons": [], "override_ids": [],
        "network_version": network_version,
    }


def _unresolved(rec: dict[str, Any], *reasons: str) -> dict[str, Any]:
    rec["status"], rec["confidence"] = "unresolved", "low"
    rec["reasons"] = sorted(set(rec["reasons"]) | set(reasons))
    return rec


def _band(ratio: float | None, band: tuple[float, float], tribs: bool) -> bool:
    if ratio is None:
        return True
    if tribs:
        return ratio <= band[1]
    return band[0] <= ratio <= band[1]


def classify(rec: dict[str, Any]) -> None:
    """Set ``status`` and ``confidence`` from endpoint confidences and km_ratio (§3.5)."""
    lo = min(rec["from"]["confidence"], rec["to"]["confidence"])
    ratio, tribs = rec["km_ratio"], rec["includes_tributaries"]
    known = ratio is not None
    if lo >= MIN_CONF_HIGH and known and _band(ratio, BAND_HIGH, tribs):
        conf = "high"
    elif lo >= MIN_CONF_RESOLVED and _band(ratio, BAND_RESOLVED, tribs):
        conf = "medium"
    else:
        conf = "low"
    rec["confidence"] = conf
    rec["status"] = "resolved" if conf in ("high", "medium") else "review"
    if lo < MIN_CONF_RESOLVED:
        rec["reasons"].append("endpoint_confidence_low")
    if known and not _band(ratio, BAND_RESOLVED, tribs):
        rec["reasons"].append("km_ratio_out_of_band")


def validate(rec: dict[str, Any], course: Mapping[str, Any], ctx: Context) -> list[str]:
    """Invariants of §3.5; returns the names of the failed ones."""
    bad: list[str] = []
    f, t = rec["from"]["m"], rec["to"]["m"]
    if not (0 <= f < t <= course["length_m"] + 0.5) or abs(rec["length_m"] - (t - f)) > 0.2:
        bad.append("measure_order")
        return bad
    for end in ("from", "to"):
        e = rec[end]
        if e["kind"] == "CONFLUENCE" and e["method"] in ("tributary_junction", "outlet_into_named"):
            ok = abs(e["m"] - course["length_m"]) <= 1.0 or any(abs(e["m"] - j["m"]) <= 1.0 for j in course.get("junctions") or [])
            if not ok:
                bad.append(f"confluence_not_on_junction:{end}")
    line = ctx.line(course)
    pts = line.substring(f, t)
    spans = [(s["m_from"] - 1, s["m_to"] + 1) for s in course.get("synthetic") or []]
    from .geodesy import vincenty_m

    worst = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = vincenty_m(a[0], a[1], b[0], b[1])
        if seg > COARSE_SEGMENT_M:
            mid = line.locate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)[0]
            if not any(lo <= mid <= hi for lo, hi in spans):
                worst = max(worst, seg)
    if worst > MAX_SEGMENT_M:
        bad.append("segment_gt_5km")
    elif worst > COARSE_SEGMENT_M:
        rec["reasons"].append("coarse_osm_segment")
    poly = ctx.county_polys.get(fold(rec.get("judet")))
    if poly is not None and "COUNTY_LIMIT" not in (rec["from"]["kind"], rec["to"]["kind"]):
        samples = [pts[0], pts[len(pts) // 2], pts[-1]]
        if all(poly.distance_m(x, y, COUNTY_BUFFER_M) > COUNTY_BUFFER_M for x, y in samples):
            bad.append("outside_county")
    return bad


def _finish(rec, course, ctx) -> dict[str, Any]:
    rec["length_m"] = round(rec["to"]["m"] - rec["from"]["m"], 1)
    km = rec["contract_km"]
    rec["km_ratio"] = round(rec["length_m"] / (km * 1000), 3) if km else None
    classify(rec)
    if course.get("source") == "anar":  # fallback geometry is never high confidence
        rec["reasons"].append("fallback_source:anar")
        if rec["confidence"] == "high":
            rec["confidence"] = "medium"
        if (rec["course"].get("method") or "").startswith("anar_fuzzy") and rec["status"] == "resolved":
            rec["status"] = "review"
            rec["reasons"].append("fallback_fuzzy_match")
    bad = validate(rec, course, ctx)
    if bad:
        rec["reasons"] += [f"invariant:{b}" for b in bad]
        if rec["status"] == "resolved":
            rec["status"] = "review"
        rec["confidence"] = "low"
    rec["reasons"] = sorted(set(rec["reasons"]))
    return rec


def resolve_sector(
    water: Mapping[str, Any],
    spec: Mapping[str, Any],
    match: Mapping[str, Any],
    ctx: Context,
    endpoint_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    network_version: str = "",
) -> dict[str, Any]:
    rec = _base(water, spec, match, network_version)
    dim = (water.get("dimensiune") or "").lower()
    if " ha" in dim or dim.strip().endswith("ha"):
        rec["contract_km"] = None
        rec["reasons"].append("contract_unit_ha")
    elif rec["contract_km"] is None:
        rec["reasons"].append("contract_km_missing")
    scope = spec.get("scope")
    cid = match.get("course_id")
    course = ctx.courses.get(cid) if cid else None
    ovs = endpoint_overrides or {}
    if scope in ("empty", "unparsed", None):
        # Reviewed overrides for BOTH ends define the sector even when the limite
        # text is unusable (e.g. cadastral river-km markers: "Jirlău km 183 -
        # Voinești km 309").
        ends = {e: ovs.get((water["slug"], e)) for e in ("from", "to")}
        if course is None or not all(ends.values()):
            return _unresolved(rec, "limite_unusable")
        picked = {e: _override_candidate(ends[e], course, ctx, e) for e in ends}
        if not all(picked.values()):
            return _unresolved(rec, "limite_unusable", "override_anchor_unresolvable")
        f, t = picked["from"], picked["to"]
        if f.m > t.m:
            f, t = t, f
            rec["reasons"].append("swapped_order")
        rec["override_ids"] += [f"{water['slug']}:from", f"{water['slug']}:to"]
        rec["reasons"].append("limite_unusable_overridden")
        rec["from"], rec["to"] = _ep("OVERRIDE", f), _ep("OVERRIDE", t)
        if rec["to"]["m"] - rec["from"]["m"] <= 0:
            return _unresolved(rec, "empty_sector")
        return _finish(rec, course, ctx)
    if course is None:
        return _unresolved(rec, "course_" + (match.get("method") or "missing") if not cid else "course_record_missing")
    judet = water.get("judet")
    length = course["length_m"]

    if scope == "whole_course":
        c0, c1 = Candidate(0.0, 0.95, "whole_course"), Candidate(length, 0.95, "whole_course")
        rec["from"], rec["to"] = _ep("SOURCE", c0), _ep("MOUTH", c1)
    elif scope == "whole_county":
        want = fold(spec.get("county") or "")
        ivs = [(c["m_from"], c["m_to"]) for c in course.get("counties") or [] if fold(c.get("county")) == want]
        if not ivs:
            return _unresolved(rec, "county_not_on_course")
        a, b = max(ivs, key=lambda x: x[1] - x[0])
        if len(ivs) > 1:
            rec["reasons"].append("county_interval_multiple")
            # A border river leaves and re-enters the county; its stretch is
            # the span from first entry to last exit when that fits the
            # contract length better than the longest single interval.
            span = (min(x[0] for x in ivs), max(x[1] for x in ivs))
            km = rec["contract_km"]
            if km and abs((span[1] - span[0]) - km * 1000) < abs((b - a) - km * 1000):
                a, b = span
                rec["reasons"].append("county_interval_span")
        rec["from"] = _ep("COUNTY", Candidate(a, 0.9, "county_interval"))
        rec["to"] = _ep("COUNTY", Candidate(b, 0.9, "county_interval"))
    elif scope == "locality_list":
        found: list[Candidate] = []
        for name in spec.get("localities") or []:
            cs = resolve_endpoint({"kind": "LOCALITY", "target": name, "qualifier": "at"}, course, ctx, role="from", judet=judet)
            if cs:
                found.append(cs[0])
        if len(found) < 2:
            return _unresolved(rec, "locality_list_unresolved")
        lo, hi = min(found, key=lambda c: c.m), max(found, key=lambda c: c.m)
        rec["from"], rec["to"] = _ep("LOCALITY", lo), _ep("LOCALITY", hi)
    elif scope == "interval":
        specs = {"from": spec.get("from"), "to": spec.get("to")}
        picked: dict[str, Candidate | None] = {}
        allc: dict[str, list[Candidate]] = {}
        order = sorted(("from", "to"), key=lambda e: (specs[e] or {}).get("kind") == "BRIDGE")
        km = rec["contract_km"]
        for end in order:
            es = specs[end]
            if es is None:
                picked[end], allc[end] = None, []
                continue
            if (slug_end := (water["slug"], end)) in ovs:
                oc = _override_candidate(ovs[slug_end], course, ctx, end)
                if oc is not None:
                    rec["override_ids"].append(f"{water['slug']}:{end}")
                    picked[end], allc[end] = oc, [oc]
                    continue
            other = picked.get("to" if end == "from" else "from")
            window = None
            if other is not None:
                span = km * 1000 * BAND_RESOLVED[1] if km else length
                window = (max(0.0, other.m - span), other.m) if end == "from" else (other.m, min(length, other.m + span))
            cs = resolve_endpoint(es, course, ctx, role=end, judet=judet, window=window)
            allc[end] = cs
            p, why = _pick(cs)
            picked[end] = p
            rec["reasons"] += [f"endpoint_{w}:{end}" for w in why]
        for end in ("from", "to"):
            if picked.get(end) is None:
                rec["reasons"].append(f"endpoint_unresolved:{end}")
        if picked["from"] is None or picked["to"] is None:
            return _unresolved(rec)
        f, t = picked["from"], picked["to"]
        if abs(f.m - t.m) < SAME_POINT_M:
            weak = "from" if f.confidence <= t.confidence else "to"
            alt = [c for c in allc[weak][1:] if abs(c.m - (t if weak == "from" else f).m) >= SAME_POINT_M]
            if alt:
                if weak == "from":
                    f = alt[0]
                else:
                    t = alt[0]
                rec["reasons"].append(f"second_best:{weak}")
        kf, kt = specs["from"]["kind"], specs["to"]["kind"]
        if f.m > t.m:
            f, t, kf, kt = t, f, kt, kf
            rec["reasons"].append("swapped_order")
        rec["from"], rec["to"] = _ep(kf, f), _ep(kt, t)
    else:
        return _unresolved(rec, "scope_unsupported")
    if rec["to"]["m"] - rec["from"]["m"] <= 0:
        return _unresolved(rec, "empty_sector")
    return _finish(rec, course, ctx)


# ------------------------------------------------------------ alternative courses

ALT_MAX = 4  # match candidates tried after the chosen course
_RANK = {"resolved": 2, "review": 1, "unresolved": 0}
_CONF = {"high": 2, "medium": 1, "low": 0}


def _rank(rec: Mapping[str, Any]) -> tuple[int, int]:
    return _RANK[rec["status"]], _CONF[rec["confidence"]]


def resolve_best(
    water: Mapping[str, Any],
    spec: Mapping[str, Any],
    match: Mapping[str, Any],
    ctx: Context,
    endpoint_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    network_version: str = "",
) -> dict[str, Any]:
    """``resolve_sector`` plus endpoint evidence across the match candidates.

    * chosen course not ``resolved``: the other candidates (up to ``ALT_MAX``)
      are tried and one replaces it only with a strictly better status
      (reason ``alt_course``) - e.g. an OSM fragment beats a fallback course
      whose endpoints cannot be found, and vice versa;
    * ``ambiguous`` match: a candidate is taken only when it is the single
      one that resolves (else the single one reaching ``review``); reason
      ``ambiguity_resolved_by_endpoints``.
    Overrides are never second-guessed.
    """
    rec = resolve_sector(water, spec, match, ctx, endpoint_overrides, network_version)
    method = match.get("method") or ""
    if rec["status"] == "resolved" or method == "override" or spec.get("scope") in ("empty", "unparsed", None):
        return rec
    cands = [c[0] for c in match.get("candidates") or [] if c[0] != match.get("course_id") and c[0] in ctx.courses]
    alts = []
    for cid in cands[:ALT_MAX]:
        m2 = {**match, "course_id": cid, "method": method}
        alts.append(resolve_sector(water, spec, m2, ctx, endpoint_overrides, network_version))
    if not alts:
        return rec
    if match.get("course_id") is None:  # ambiguous
        for status in ("resolved", "review"):
            hit = [a for a in alts if a["status"] == status]
            if len(hit) == 1:
                best = hit[0]
                best["reasons"] = sorted(set(best["reasons"]) | {"ambiguity_resolved_by_endpoints"})
                best["course"]["method"] = "ambiguous+endpoints"
                return best
            if len(hit) > 1:
                break
        return rec
    best = max(alts, key=_rank)
    if _rank(best) > _rank(rec) and best["status"] != rec["status"]:
        best["reasons"] = sorted(set(best["reasons"]) | {"alt_course"})
        best["course"]["method"] = method + "|alt"
        return best
    return rec


# --------------------------------------------------------------------- overlaps


def _plausible(rec: Mapping[str, Any]) -> bool:
    return _band(rec.get("km_ratio"), BAND_RESOLVED, bool(rec.get("includes_tributaries")))


def flag_overlaps(records: list[dict[str, Any]]) -> None:
    """Flag ``overlap:<slug>`` on both sides; > 50% of the shorter sector (and
    neither is whole_county) downgrades ``resolved`` to ``review``."""
    by_course: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        if r["from"] and r["to"] and r["course"]["course_id"]:
            by_course.setdefault(r["course"]["course_id"], []).append(r)
    for recs in by_course.values():
        recs.sort(key=lambda r: r["slug"])
        for i, a in enumerate(recs):
            for b in recs[i + 1:]:
                lo = max(a["from"]["m"], b["from"]["m"])
                hi = min(a["to"]["m"], b["to"]["m"])
                if hi - lo <= 1.0:
                    continue
                for x, y in ((a, b), (b, a)):
                    x["reasons"] = sorted(set(x["reasons"]) | {f"overlap:{y['slug']}"})
                shorter = min(a["length_m"], b["length_m"])
                county = "whole_county" in (a["parse"]["scope"], b["parse"]["scope"])
                if shorter > 0 and (hi - lo) / shorter > OVERLAP_REVIEW_SHARE and not county:
                    for x, y in ((a, b), (b, a)):
                        x["reasons"] = sorted(set(x["reasons"]) | {"overlap_gt_50pct"})
                        # an implausible partner (its own km_ratio outside the resolved
                        # band, so it is already in review) cannot demote x; nor can a
                        # contract from another county (border rivers are leased per bank)
                        if x["status"] == "resolved" and _plausible(y) and fold(x.get("judet")) == fold(y.get("judet")):
                            x["status"] = "review"


# -------------------------------------------------------------------------- CLI


def cli(argv: list[str]) -> int:
    """`python -m rivernet resolve`: write data/sectors/sectors.jsonl."""
    import argparse
    import gzip
    import sys
    from collections import Counter
    from pathlib import Path

    from .extract_schema import load_extract
    from .overrides import load_endpoint_overrides
    from .resolvers import build_context

    ap = argparse.ArgumentParser(prog="rivernet resolve")
    ap.add_argument("--extract", required=True)
    ap.add_argument("--courses", default="data/rivernet/courses.jsonl.gz")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--parsed", default="data/sectors/limits_parsed.jsonl")
    ap.add_argument("--matches", default="data/sectors/matches.jsonl")
    ap.add_argument("--overrides", default="data/sectors/endpoint_overrides.json")
    ap.add_argument("--counties", default="public/data/counties.geojson")
    ap.add_argument("--course-index", default="data/rivernet/course_index.json")
    ap.add_argument("--out", default="data/sectors/sectors.jsonl")
    ns = ap.parse_args(argv)

    for p in (ns.courses, ns.parsed, ns.matches):
        if not Path(p).exists():
            print(f"rivernet resolve: {p} missing - run build/parse/match first", file=sys.stderr)
            return 1
    ex = load_extract(ns.extract)
    with gzip.open(ns.courses, "rt", encoding="utf-8") as f:
        courses = [json.loads(x) for x in f if x.strip()]
    cj = json.loads(Path(ns.counties).read_text(encoding="utf-8")) if Path(ns.counties).exists() else None
    ctx = build_context(ex, courses, cj)
    if Path(ns.course_index).exists():
        ctx.names = json.loads(Path(ns.course_index).read_text(encoding="utf-8"))
    ts = (ex.meta.osm_timestamp or "")[:10].replace("-", "")
    version = f"ro-water-{ts}" if ts else "ro-water-unknown"
    parsed = {r["slug"]: r["spec"] for r in map(json.loads, Path(ns.parsed).read_text(encoding="utf-8").splitlines())}
    matches = {r["slug"]: r for r in map(json.loads, Path(ns.matches).read_text(encoding="utf-8").splitlines())}
    ovs = load_endpoint_overrides(ns.overrides)
    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    recs = []
    for w in sorted((w for w in waters if w.get("subtype") == "rau"), key=lambda w: w["slug"]):
        recs.append(resolve_best(w, parsed.get(w["slug"], {"scope": "empty"}), matches.get(w["slug"], {}), ctx, ovs, version))
    flag_overlaps(recs)
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(dict(sorted(Counter(r["status"] for r in recs).items()))))
    return 0
