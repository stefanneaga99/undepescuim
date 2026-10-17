"""Water -> course matcher (plan T3.2).

Works on course *records* (the dicts in ``courses.jsonl.gz``), not on ``Course``
objects, so it can run from the committed data alone.

Deviations from the plan, by design:

* the "wikidata label key" candidate source is skipped (records carry only the
  wikidata id, no label);
* the 2 km county buffer is applied through the course's ``counties`` intervals
  (exact polygon containment) plus an optional ``county_ok`` hook; a course
  without any county intervals is not filtered (reason ``county_unknown``);
* the "endpoint mentions a locality on this course" term only checks
  tributaries / the receiving course (no place index exists at this stage).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Callable, Iterable, Mapping

from .textnorm import article_variants, fold, river_key, river_keys, river_match_keys, stem_key

W_NAME, W_MENTION, W_LENGTH = 0.6, 0.2, 0.2
FUZZY_MIN = 0.88
AMBIGUITY_GAP = 0.1
NAME_EXACT, NAME_ALT_KEY = 1.0, 0.9
NAME_STEM = 0.85  # tiers 2/3: inflection-insensitive stem equality
FALLBACK_SOURCE = "anar"  # course records from rivernet.hidrografie
# An OSM course shorter than FRAGMENT_FIT x contract km is a fragment (OSM
# name-courses break at unnamed stretches); a fallback course of the same stem
# replaces it when it fits (>= LONGER_FIT x contract) or is LONGER_FACTOR x longer.
FRAGMENT_FIT, LONGER_FIT, LONGER_FACTOR = 0.6, 0.8, 2.0

KM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*km", re.I)


@dataclass
class MatchResult:
    course_id: str | None
    score: float
    # override | name+county | fuzzy+county | stem+county | anar+county | anar_fuzzy+county
    # | anar_longer+county | ambiguous | no_candidate | no_county_match
    method: str
    candidates: list[tuple[str, float, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "course_id": self.course_id,
            "score": round(self.score, 4),
            "method": self.method,
            "candidates": [[c, round(s, 4), r] for c, s, r in self.candidates],
        }


def contract_km(dimensiune: str | None) -> float | None:
    m = KM_RE.search(dimensiune or "")
    return float(m.group(1).replace(",", ".")) if m else None


def _course_keys(c: Mapping[str, Any]) -> tuple[str, set[str]]:
    primary = c.get("name_key") or river_key(c.get("name"))
    alt: set[str] = set(article_variants(primary))
    for a in c.get("aliases") or []:
        alt.update(river_match_keys(a))
    return primary, alt


def _in_county(c: Mapping[str, Any], judet: str | None, ok: Callable[..., bool] | None) -> tuple[bool, str]:
    if not judet:
        return True, "no_water_county"
    counties = c.get("counties") or []
    if not counties:
        return True, "county_unknown"
    want = fold(judet)
    if any(fold(x.get("county")) == want for x in counties):
        return True, "county"
    if ok is not None and ok(c, judet):
        return True, "county_near"
    return False, "county_mismatch"


def _tributary_keys(c: Mapping[str, Any]) -> set[str]:
    keys: set[str] = set()
    for j in c.get("junctions") or []:
        tid = j.get("tributary_course_id") or ""
        parts = tid.split(":")
        if len(parts) >= 2 and parts[0] == "name":
            keys.add(parts[1])
    ri = c.get("receives_into") or ""
    parts = ri.split(":")
    if len(parts) >= 2 and parts[0] == "name":
        keys.add(parts[1])
    return keys


def _endpoint_targets(spec: Mapping[str, Any] | None) -> set[str]:
    out: set[str] = set()
    if not spec:
        return out
    for side in ("from", "to"):
        ep = spec.get(side)
        if ep and ep.get("kind") == "CONFLUENCE" and ep.get("target"):
            out.update(river_keys(ep["target"]))
    return out


def is_fallback(c: Mapping[str, Any]) -> bool:
    return c.get("source") == FALLBACK_SOURCE


def match(
    water: Mapping[str, Any],
    courses: Iterable[Mapping[str, Any]],
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
    spec: Mapping[str, Any] | None = None,
    county_ok: Callable[..., bool] | None = None,
    mention_hook: Callable[[Mapping[str, Any], Mapping[str, Any]], bool] | None = None,
    by_key: Mapping[str, list[Mapping[str, Any]]] | None = None,
    by_stem: Mapping[str, list[Mapping[str, Any]]] | None = None,
) -> MatchResult:
    """Pick the course for one water; see the module docstring for the rules.

    Tiers, each tried only when the previous one finds no course in the
    water's county (``no_candidate`` / ``no_county_match``; ``ambiguous`` is
    final):

    1. OSM courses by name key (exact, then fuzzy) - the plan's T3.2 rule;
    2. OSM courses by ``stem_key`` ("Valea Pojorâtei" = "Pojorâta");
    3. fallback-source courses (ANAR cadastre) by stem, then fuzzy stem.

    Tiers 2-3 need ``by_stem`` (see ``index_stems``).
    """
    courses = [c for c in courses if not is_fallback(c)] if by_key is None else []
    slug = water.get("slug")
    if overrides and slug in overrides:
        return MatchResult(overrides[slug]["course_id"], 1.0, "override", [(overrides[slug]["course_id"], 1.0, "override")])

    keys = river_match_keys(water.get("name"))
    if not keys:
        return MatchResult(None, 0.0, "no_candidate")

    # candidate generation: exact key / alias key hits
    hits: dict[str, tuple[Mapping[str, Any], float, str]] = {}
    if by_key is not None:
        for rank, k in enumerate(keys):
            for c in by_key.get(k, ()):
                sc = NAME_EXACT if rank == 0 else NAME_ALT_KEY
                old = hits.get(c["course_id"])
                if old is None or sc > old[1]:
                    hits[c["course_id"]] = (c, sc, "name")
    else:
        for c in courses:
            primary, alt = _course_keys(c)
            if primary == keys[0]:
                hits[c["course_id"]] = (c, NAME_EXACT, "name")
            elif primary in keys or alt & set(keys):
                hits[c["course_id"]] = (c, NAME_ALT_KEY, "name")
    method_prefix = "name"
    if not hits:
        pool = list(by_key_values(by_key)) if by_key is not None else courses
        for c in pool:
            primary, _ = _course_keys(c)
            r = max(SequenceMatcher(None, k, primary).ratio() for k in keys)
            if r >= FUZZY_MIN:
                hits[c["course_id"]] = (c, r, "fuzzy")
        method_prefix = "fuzzy"
    res = _score(hits, water, spec, county_ok, mention_hook, method_prefix)
    if by_stem is None:
        return res
    st = stem_key(water.get("name"))
    stem_hits = list(by_stem.get(st, ())) if st else []
    if res.course_id is not None:
        return _prefer_longer(res, hits, stem_hits, water, spec, county_ok, mention_hook)
    if res.method not in _MISSES:
        return res

    osm = {c["course_id"]: (c, NAME_STEM, "stem") for c in stem_hits if not is_fallback(c)}
    res2 = _score(osm, water, spec, county_ok, mention_hook, "stem")
    if res2.course_id is not None:
        return _prefer_longer(res2, osm, stem_hits, water, spec, county_ok, mention_hook)
    if res2.method not in _MISSES:
        return res2
    anar = {c["course_id"]: (c, NAME_STEM, "anar") for c in stem_hits if is_fallback(c)}
    prefix = "anar"
    if not anar and st:
        for k in sorted(by_stem):
            r = SequenceMatcher(None, st, k).ratio()
            if r >= FUZZY_MIN:
                for c in by_stem[k]:
                    if is_fallback(c):
                        anar[c["course_id"]] = (c, NAME_STEM * r, "anar_fuzzy")
        prefix = "anar_fuzzy"
    res3 = _score(anar, water, spec, county_ok, mention_hook, prefix)
    if res3.method not in _MISSES:
        return res3
    # report the most informative miss: a county mismatch beats "no candidate"
    return next((r for r in (res, res2, res3) if r.method == "no_county_match"), res)


_MISSES = ("no_candidate", "no_county_match")


def _prefer_longer(
    res: MatchResult,
    hits: Mapping[str, tuple[Mapping[str, Any], float, str]],
    stem_hits: list[Mapping[str, Any]],
    water: Mapping[str, Any],
    spec: Mapping[str, Any] | None,
    county_ok: Callable[..., bool] | None,
    mention_hook: Callable[[Mapping[str, Any], Mapping[str, Any]], bool] | None,
) -> MatchResult:
    """Swap an OSM fragment for a same-stem fallback course that covers the contract."""
    km = contract_km(water.get("dimensiune"))
    if not km or (spec or {}).get("includes_tributaries"):
        return res
    osm_len = float(hits[res.course_id][0].get("length_m") or 0.0)
    if osm_len >= FRAGMENT_FIT * km * 1000:
        return res
    longer = {c["course_id"]: (c, NAME_STEM, "anar_longer") for c in stem_hits if is_fallback(c)
              and (float(c.get("length_m") or 0) >= LONGER_FIT * km * 1000
                   or float(c.get("length_m") or 0) >= LONGER_FACTOR * osm_len)}
    alt = _score(longer, water, spec, county_ok, mention_hook, "anar_longer")
    if alt.course_id is None:
        return res
    return MatchResult(alt.course_id, alt.score, alt.method, alt.candidates + res.candidates[:2])


def _score(
    hits: Mapping[str, tuple[Mapping[str, Any], float, str]],
    water: Mapping[str, Any],
    spec: Mapping[str, Any] | None,
    county_ok: Callable[..., bool] | None,
    mention_hook: Callable[[Mapping[str, Any], Mapping[str, Any]], bool] | None,
    method_prefix: str,
) -> MatchResult:
    if not hits:
        return MatchResult(None, 0.0, "no_candidate")
    km = contract_km(water.get("dimensiune"))
    tribs = bool((spec or {}).get("includes_tributaries"))
    targets = _endpoint_targets(spec)
    scored: list[tuple[str, float, str]] = []
    for cid, (c, name_score, how) in hits.items():
        ok, why = _in_county(c, water.get("judet"), county_ok)
        if not ok:
            continue
        mention = 1.0 if targets and (_tributary_keys(c) & targets) else 0.0
        if not mention and mention_hook is not None and spec:
            mention = 1.0 if mention_hook(c, spec) else 0.0
        length_m = float(c.get("length_m") or 0.0)
        if km is None or km <= 0 or tribs:
            fit = 1.0
        else:
            fit = 1.0 if length_m >= 0.8 * km * 1000 else min(1.0, length_m / (km * 1000))
        s = W_NAME * name_score + W_MENTION * mention + W_LENGTH * fit
        scored.append((cid, s, f"{how}+{why};mention={int(mention)};fit={fit:.2f}"))
    if not scored:
        return MatchResult(None, 0.0, "no_county_match")
    scored.sort(key=lambda t: (-t[1], t[0]))
    top = scored[0]
    if len(scored) > 1 and top[1] - scored[1][1] < AMBIGUITY_GAP:
        return MatchResult(None, top[1], "ambiguous", scored[:5])
    return MatchResult(top[0], top[1], f"{method_prefix}+county", scored[:5])


def by_key_values(by_key: Mapping[str, list[Mapping[str, Any]]]) -> Iterable[Mapping[str, Any]]:
    seen: set[str] = set()
    for lst in by_key.values():
        for c in lst:
            if c["course_id"] not in seen:
                seen.add(c["course_id"])
                yield c


def index_courses(courses: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    """key (primary + alias keys) -> OSM courses, for O(1) candidate lookup.
    Fallback-source courses are left out (they only answer tier 3)."""
    idx: dict[str, list[Mapping[str, Any]]] = {}
    for c in courses:
        if is_fallback(c):
            continue
        primary, alt = _course_keys(c)
        for k in {primary} | alt:
            idx.setdefault(k, []).append(c)
    return idx


def index_stems(courses: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    """stem_key (name + aliases) -> courses of every source (tiers 2-3)."""
    idx: dict[str, list[Mapping[str, Any]]] = {}
    for c in courses:
        for st in sorted({stem_key(c.get("name"))} | {stem_key(a) for a in c.get("aliases") or []}):
            if st:
                idx.setdefault(st, []).append(c)
    return idx


# ------------------------------------------------------------------------ CLI


def cli(argv: list[str]) -> int:
    """`python -m rivernet match`: write data/sectors/matches.jsonl."""
    import argparse
    import gzip
    import json
    import sys
    from pathlib import Path

    from .overrides import load_course_overrides

    ap = argparse.ArgumentParser(prog="rivernet match")
    ap.add_argument("--courses", default="data/rivernet/courses.jsonl.gz")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--parsed", default="data/sectors/limits_parsed.jsonl")
    ap.add_argument("--overrides", default="data/sectors/course_overrides.json")
    ap.add_argument("--out", default="data/sectors/matches.jsonl")
    ap.add_argument("--extract", default=None, help="OSM extract; enables the endpoint-evidence term")
    ap.add_argument("--counties", default="public/data/counties.geojson")
    ns = ap.parse_args(argv)

    cp = Path(ns.courses)
    if not cp.exists():
        print(f"rivernet match: {cp} missing - run `rivernet build` first", file=sys.stderr)
        return 1
    with gzip.open(cp, "rt", encoding="utf-8") as f:
        courses = [json.loads(line) for line in f if line.strip()]
    idx = index_courses(courses)
    sidx = index_stems(courses)
    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    parsed = {}
    pp = Path(ns.parsed)
    if pp.exists():
        for line in pp.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            parsed[r["slug"]] = r["spec"]
    ov = load_course_overrides(ns.overrides)
    hook = None
    if ns.extract:
        from .extract_schema import load_extract
        from .resolvers import build_context, resolve_endpoint

        cj = json.loads(Path(ns.counties).read_text(encoding="utf-8")) if Path(ns.counties).exists() else None
        ctx = build_context(load_extract(ns.extract), courses, cj)

        def hook(course, spec):  # noqa: E306
            for end in ("from", "to"):
                e = spec.get(end)
                if e and e.get("kind") in ("LOCALITY", "DAM", "BRIDGE", "WATERFALL") and e.get("target"):
                    if resolve_endpoint(e, course, ctx, role=end):
                        return True
            return False

    counts: dict[str, int] = {}
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for w in sorted((w for w in waters if w.get("subtype") == "rau"), key=lambda w: w["slug"]):
            r = match(w, [], ov, parsed.get(w["slug"]), mention_hook=hook, by_key=idx, by_stem=sidx)
            counts[r.method] = counts.get(r.method, 0) + 1
            f.write(json.dumps({"slug": w["slug"], **r.to_dict()}, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(dict(sorted(counts.items())), ensure_ascii=False))
    return 0
