"""``rivernet publish``: switch waters to pre-cut sector geometry (plan T4.2).

Only the keys in ``ALLOWED`` may change; a test enforces it. Deviation: the
5 m simplification is a plain Douglas-Peucker in degrees (shapely is not
available to the authoring sandbox); on a single river line the result is the
same up to vertex choice.

D8 as amended by the owner on 2026-10-17: a multi-contract group still switches
as a whole only when every member is eligible, except that an eligible member
with no line geometry of its own switches on its own ("partial"). Such a member
was only ever drawn as a slice of the group owner's line; the owner and every
member with a legacy line stay untouched, and the partial member keeps its
owner-relative fraction fields (course_frac, sectorStart/End).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .geodesy import line_length_m
from .lr import Line

SIMPLIFY_DEG = 0.00005
DECIMALS = 5
SET_KEYS = {"geometry", "bbox", "lengthKm", "geometryKind", "sectorStatus", "sectorConfidence",
            "sectorStart", "sectorEnd", "source", "source_detail", "coordinates", "driving"}
REMOVE_KEYS = {"course_frac", "bbox_render", "fallback"}
ALLOWED = SET_KEYS | REMOVE_KEYS
BLOCKING_PREFIXES = ("invariant:",)
BLOCKING_REASONS = {"overlap_gt_50pct", "limite_unusable"}


# ------------------------------------------------------------------ geometry


def simplify_dp(coords: Sequence[Sequence[float]], tol: float = SIMPLIFY_DEG) -> list[list[float]]:
    """Douglas-Peucker (iterative); always keeps the end points."""
    pts = [list(c) for c in coords]
    if len(pts) <= 2:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a][:2], pts[b][:2]
        dx, dy = bx - ax, by - ay
        seg2 = dx * dx + dy * dy
        worst, wi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i][:2]
            if seg2 == 0:
                d = ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
                d = ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5
            if d > worst:
                worst, wi = d, i
        if worst > tol:
            keep[wi] = True
            stack += [(a, wi), (wi, b)]
    return [p for p, k in zip(pts, keep) if k]


def _round(coords: Sequence[Sequence[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for c in coords:
        r = [round(c[0], DECIMALS), round(c[1], DECIMALS)]
        if not out or r != out[-1]:
            out.append(r)
    return out


def sector_pieces(course: Mapping[str, Any], m_from: float, m_to: float) -> list[list[tuple[float, float]]]:
    """Sub-lines of [m_from, m_to], split at the course's synthetic spans."""
    line = Line.from_coords([tuple(c) for c in course["geometry"]["coordinates"]])
    cuts = sorted((s["m_from"], s["m_to"]) for s in course.get("synthetic") or []
                  if s["m_to"] > m_from and s["m_from"] < m_to)
    pieces, cur = [], m_from
    for a, b in cuts:
        if a > cur:
            pieces.append((cur, min(a, m_to)))
        cur = max(cur, b)
    if cur < m_to:
        pieces.append((cur, m_to))
    return [line.substring(a, b) for a, b in pieces if b - a > 0.5] or [line.substring(m_from, m_to)]


def build_geometry(course: Mapping[str, Any], m_from: float, m_to: float) -> dict[str, Any]:
    parts = [_round(simplify_dp(p)) for p in sector_pieces(course, m_from, m_to)]
    parts = [p for p in parts if len(p) >= 2]
    if len(parts) == 1:
        return {"type": "LineString", "coordinates": parts[0]}
    return {"type": "MultiLineString", "coordinates": parts}


def _lines(geom: Mapping[str, Any]) -> list[list[list[float]]]:
    return [geom["coordinates"]] if geom["type"] == "LineString" else list(geom["coordinates"])


# ----------------------------------------------------------------- selection


def eligible(water: Mapping[str, Any], sector: Mapping[str, Any] | None) -> tuple[bool, str]:
    if sector is None:
        return False, "no_sector_record"
    if water.get("subtype") != "rau":
        return False, "not_a_river"
    st = sector.get("status")
    if st == "resolved":
        return True, ""
    if st == "review":
        if not sector.get("override_ids"):
            return False, "review_without_override"
        bad = [r for r in sector.get("reasons", []) if r.startswith(BLOCKING_PREFIXES) or r in BLOCKING_REASONS]
        if bad:
            return False, "review_blocking_reason:" + bad[0]
        return True, ""
    return False, f"status_{st}"


def has_legacy_line(water: Mapping[str, Any]) -> bool:
    """A legacy (not pre-cut) line geometry of the water's own."""
    g = water.get("geometry") or {}
    return water.get("geometryKind") != "sector" and g.get("type") in ("LineString", "MultiLineString")


def publish(
    waters: Sequence[Mapping[str, Any]],
    sectors: Mapping[str, Mapping[str, Any]],
    courses: Mapping[str, Mapping[str, Any]],
    *,
    mode: str = "shadow",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if mode not in ("shadow", "write"):
        raise ValueError("mode must be 'shadow' or 'write'")
    ok: dict[str, bool] = {}
    why: dict[str, str] = {}
    for w in waters:
        s = sectors.get(w["slug"])
        e, r = eligible(w, s)
        if e and courses.get(s["course"]["course_id"]) is None:
            e, r = False, "course_missing"
        ok[w["slug"]], why[w["slug"]] = e, r
    groups: dict[str, list[str]] = defaultdict(list)
    for w in waters:
        if w.get("riverGroup"):
            groups[w["riverGroup"]].append(w["slug"])
    by_slug = {w["slug"]: w for w in waters}
    blocked: dict[str, list[str]] = {}
    partial: set[str] = set()
    for g, members in groups.items():
        bad = [m for m in members if not ok[m]]
        if bad and len(bad) < len(members):
            blocked[g] = sorted(bad)
            for m in members:
                if not ok[m]:
                    continue
                if has_legacy_line(by_slug[m]):
                    ok[m], why[m] = False, "d8_group_blocked"
                else:
                    # D8 amendment (owner, 2026-10-17): a member with no line of its
                    # own is only ever drawn as a slice of the group owner; giving it
                    # its own sector cuts nothing the legacy members rely on.
                    partial.add(m)
        # a group where nobody is eligible simply stays legacy for its own reasons

    new_waters: list[dict[str, Any]] = []
    switched, kept = [], []
    for w in waters:
        slug = w["slug"]
        if not ok[slug]:
            new_waters.append(dict(w))
            if w.get("subtype") == "rau":
                kept.append({"slug": slug, "reason": why[slug]})
            continue
        s = sectors[slug]
        c = courses[s["course"]["course_id"]]
        geom = build_geometry(c, s["from"]["m"], s["to"]["m"])
        lines = _lines(geom)
        xs = [p[0] for ln in lines for p in ln]
        ys = [p[1] for ln in lines for p in ln]
        out = dict(w)
        if slug not in partial:
            for k in REMOVE_KEYS:
                out.pop(k, None)
        out.update({
            "geometry": geom,
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "lengthKm": round(sum(line_length_m(ln) for ln in lines) / 1000, 1),
            "geometryKind": "sector",
            "sectorStatus": s["status"],
            "sectorConfidence": s["confidence"],
            "sectorStart": round(s["from"]["m"] / c["length_m"], 4),
            "sectorEnd": round(s["to"]["m"] / c["length_m"], 4),
            "source": "rivernet",
            "source_detail": f"rivernet:{s.get('network_version', '')}"
            + (";geometry:anar-hidrografie" if c.get("source") == "anar" else ""),
        })
        if slug in partial:
            # The legacy group members still resolve clicks on the owner's line
            # by owner-relative fractions; keep this water's legacy fraction fields
            # (course_frac stays, sectorStart/End as they were or absent).
            for k in ("sectorStart", "sectorEnd"):
                if k in w:
                    out[k] = w[k]
                else:
                    out.pop(k, None)
        if not out.get("coordinates"):
            whole = Line.from_coords([tuple(p) for ln in lines for p in ln])
            mid = whole.point_at(whole.length_m / 2)
            out["coordinates"] = [round(mid[0], 7), round(mid[1], 7)]
        if not out.get("driving"):
            out["driving"] = out["coordinates"]
        new_waters.append(out)
        switched.append({"slug": slug, "riverGroup": w.get("riverGroup"), "status": s["status"],
                         **({"d8": "partial"} if slug in partial else {})})
    report = {
        "mode": mode, "switched": switched, "switched_count": len(switched),
        "kept_legacy": kept, "kept_legacy_count": len(kept),
        "blocked_groups": [{"riverGroup": g, "blockers": b, "members": sorted(groups[g])} for g, b in sorted(blocked.items())],
    }
    return new_waters, report


def dumps_waters(waters: Sequence[Mapping[str, Any]]) -> str:
    """Same serialisation as scripts/merge_anpa_waters.py (indent=1, UTF-8, no newline)."""
    return json.dumps(list(waters), ensure_ascii=False, indent=1)


def cli(argv: list[str]) -> int:
    import argparse
    import gzip
    import sys

    ap = argparse.ArgumentParser(prog="rivernet publish")
    ap.add_argument("--mode", choices=("shadow", "write"), default="shadow")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--sectors", default="data/sectors/sectors.jsonl")
    ap.add_argument("--courses", default="data/rivernet/courses.jsonl.gz")
    ap.add_argument("--out-dir", default="data/sectors")
    ap.add_argument("--preview", default=None,
                    help="class-2 preview aggregate (default: preview_class2_physical.json beside --waters); "
                         "switched groups get their rivernet course ('' to skip)")
    ns = ap.parse_args(argv)
    if ns.preview is None:
        ns.preview = str(Path(ns.waters).parent / "preview_class2_physical.json")
    for p in (ns.waters, ns.sectors, ns.courses):
        if not Path(p).exists():
            print(f"rivernet publish: {p} missing", file=sys.stderr)
            return 1
    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    sectors = {r["slug"]: r for r in map(json.loads, Path(ns.sectors).read_text(encoding="utf-8").splitlines()) if r}
    with gzip.open(ns.courses, "rt", encoding="utf-8") as f:
        courses = {c["course_id"]: c for c in (json.loads(x) for x in f if x.strip())}
    new, report = publish(waters, sectors, courses, mode=ns.mode)
    out = Path(ns.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    preview_text = None
    if ns.preview and Path(ns.preview).exists():
        from .preview import rivernet_preview

        payload = json.loads(Path(ns.preview).read_text(encoding="utf-8"))
        new_preview, replaced = rivernet_preview(payload, new, sectors, courses)
        report["preview_groups_replaced"] = replaced
        # same serialisation as scripts/build_class2_aggregate.py
        preview_text = json.dumps(new_preview, ensure_ascii=False, separators=(",", ":"))
    (out / "publish_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if ns.mode == "write":
        Path(ns.waters).write_text(dumps_waters(new), encoding="utf-8", newline="\n")
        if preview_text is not None:
            Path(ns.preview).write_text(preview_text, encoding="utf-8", newline="\n")
    else:
        (out / "waters.shadow.json").write_text(dumps_waters(new), encoding="utf-8", newline="\n")
        if preview_text is not None:
            (out / "preview_class2_physical.shadow.json").write_text(preview_text, encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("mode", "switched_count", "kept_legacy_count")}))
    return 0
