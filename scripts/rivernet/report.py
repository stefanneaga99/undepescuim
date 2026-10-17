"""Progress report and shadow comparison (plan T3.5).

``python -m rivernet report`` reads ``data/sectors/sectors.jsonl`` (and, when
available, the courses and ``public/data/waters.json``) and writes
``data/sectors/progress.json`` plus a markdown summary on stdout.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .geodesy import line_length_m
from .lr import Line
from .planar import metres_per_degree

RATIO_BUCKETS = [("<0.5", 0.0, 0.5), ("0.5-0.8", 0.5, 0.8), ("0.8-1.25", 0.8, 1.25), ("1.25-2", 1.25, 2.0), (">2", 2.0, math.inf)]
DENSIFY_M = 50.0
TOP_REASONS = 15


# ------------------------------------------------------------------- geometry


def sector_coords(course: Mapping[str, Any], m_from: float, m_to: float) -> list[tuple[float, float]]:
    """Vertices of the course between two measures (same metric as the build)."""
    line = Line.from_coords([tuple(c) for c in course["geometry"]["coordinates"]])
    return line.substring(m_from, m_to)


def max_segment_m(coords: Sequence[Sequence[float]]) -> float:
    from .geodesy import vincenty_m

    return max((vincenty_m(a[0], a[1], b[0], b[1]) for a, b in zip(coords, coords[1:])), default=0.0)


def flatten_lines(geom: Mapping[str, Any] | None) -> list[list[tuple[float, float]]]:
    if not geom:
        return []
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "LineString":
        return [[(p[0], p[1]) for p in c]]
    if t == "MultiLineString":
        return [[(p[0], p[1]) for p in part] for part in c]
    return []


def densify(coords: Sequence[tuple[float, float]], step_m: float = DENSIFY_M) -> list[tuple[float, float]]:
    out = [coords[0]]
    for a, b in zip(coords, coords[1:]):
        m_lon, m_lat = metres_per_degree((a[1] + b[1]) / 2)
        n = max(1, int(math.hypot((b[0] - a[0]) * m_lon, (b[1] - a[1]) * m_lat) / step_m))
        out.extend((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1))
    return out


def hausdorff_m(a_lines: Iterable[Sequence[tuple[float, float]]], b_lines: Iterable[Sequence[tuple[float, float]]]) -> float | None:
    """Symmetric Hausdorff distance (metres) between two sets of lines, after
    densifying to 50 m, in a local equirectangular frame. None if either is empty."""
    import numpy as np

    pa = [p for ln in a_lines for p in densify(ln)] if a_lines else []
    pb = [p for ln in b_lines for p in densify(ln)] if b_lines else []
    if not pa or not pb:
        return None
    lat0 = sum(p[1] for p in pa + pb) / len(pa + pb)
    m_lon, m_lat = metres_per_degree(lat0)
    A = np.array([(p[0] * m_lon, p[1] * m_lat) for p in pa])
    B = np.array([(p[0] * m_lon, p[1] * m_lat) for p in pb])

    def directed(X, Y):
        worst = 0.0
        for i in range(0, len(X), 512):
            d = np.sqrt(((X[i:i + 512, None, :] - Y[None, :, :]) ** 2).sum(-1)).min(axis=1)
            worst = max(worst, float(d.max()))
        return worst

    return max(directed(A, B), directed(B, A))


def legacy_lines(water: Mapping[str, Any]) -> tuple[list[list[tuple[float, float]]], bool]:
    """(old drawn lines, approximated). With sectorStart/End on a single line the
    slice of that line is used and flagged approximate."""
    lines = flatten_lines(water.get("geometry"))
    if not lines:
        return [], False
    s, e = water.get("sectorStart"), water.get("sectorEnd")
    if s is not None and e is not None and len(lines) == 1:
        line = Line.from_coords(lines[0])
        return [line.substring(s * line.length_m, e * line.length_m)], True
    return lines, False


# --------------------------------------------------------------------- report


def build_progress(
    sectors: Sequence[Mapping[str, Any]],
    waters: Mapping[str, Mapping[str, Any]] | None = None,
    courses: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    status = Counter(s["status"] for s in sectors)
    conf = Counter(f"{s['status']}/{s['confidence']}" for s in sectors)
    hist = Counter()
    for s in sectors:
        r = s.get("km_ratio")
        if r is None:
            hist["unknown"] += 1
            continue
        for name, lo, hi in RATIO_BUCKETS:
            if lo <= r < hi:
                hist[name] += 1
                break
    reasons = Counter(r.split(":")[0] if r.startswith(("overlap:", "endpoint_")) else r for s in sectors for r in s["reasons"])
    per_county: dict[str, dict[str, int]] = {}
    for s in sectors:
        c = per_county.setdefault(s.get("judet") or "?", {"total": 0, "resolved": 0})
        c["total"] += 1
        c["resolved"] += s["status"] == "resolved"
    out: dict[str, Any] = {
        "total": len(sectors),
        "by_status": dict(sorted(status.items())),
        "by_status_confidence": dict(sorted(conf.items())),
        "km_ratio_histogram": {name: hist.get(name, 0) for name, _, _ in RATIO_BUCKETS} | ({"unknown": hist["unknown"]} if hist["unknown"] else {}),
        "top_reasons": [[k, v] for k, v in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_REASONS]],
        "per_county": dict(sorted(per_county.items())),
    }
    if courses is not None:
        chords = []
        for s in sectors:
            if s["status"] == "resolved" and s["from"] and s["to"]:
                c = courses.get(s["course"]["course_id"])
                if c:
                    chords.append((round(max_segment_m(sector_coords(c, s["from"]["m"], s["to"]["m"])), 1), s["slug"]))
        chords.sort(reverse=True)
        out["chord_check"] = {"checked": len(chords), "max_segment_m": chords[0][0] if chords else 0.0,
                              "worst": [[slug, m] for m, slug in chords[:10]]}
    if waters is not None and courses is not None:
        rows = []
        for s in sectors:
            if s["status"] == "unresolved" or not s["from"]:
                continue
            w, c = waters.get(s["slug"]), courses.get(s["course"]["course_id"])
            if not w or not c:
                continue
            old, approx = legacy_lines(w)
            new = [sector_coords(c, s["from"]["m"], s["to"]["m"])]
            old_km = sum(line_length_m(ln) for ln in old) / 1000
            rows.append({"slug": s["slug"], "old_km": round(old_km, 2), "new_km": round(s["length_m"] / 1000, 2),
                         "hausdorff_m": None if not old else round(hausdorff_m(old, new) or 0.0, 1),
                         "legacy_approx": approx})
        out["shadow"] = {"compared": len(rows), "rows": rows}
    return out


def markdown(p: Mapping[str, Any]) -> str:
    lines = [f"# Sector progress ({p['total']} waters)", "", "| status | count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in p["by_status"].items()]
    lines += ["", "| km_ratio | count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in p["km_ratio_histogram"].items()]
    lines += ["", "| reason | count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in p["top_reasons"]]
    lines += ["", "| county | resolved/total |", "|---|---|"]
    lines += [f"| {k} | {v['resolved']}/{v['total']} |" for k, v in p["per_county"].items()]
    if "chord_check" in p:
        lines += ["", f"Chord check: max segment {p['chord_check']['max_segment_m']} m over {p['chord_check']['checked']} resolved sectors."]
    if "shadow" in p:
        h = sorted(r["hausdorff_m"] for r in p["shadow"]["rows"] if r["hausdorff_m"] is not None)
        if h:
            lines += ["", f"Shadow: {len(h)} compared, Hausdorff median {h[len(h) // 2]} m, max {h[-1]} m."]
    return "\n".join(lines) + "\n"


def cli(argv: list[str]) -> int:
    import argparse
    import gzip
    import sys

    ap = argparse.ArgumentParser(prog="rivernet report")
    ap.add_argument("--sectors", default="data/sectors/sectors.jsonl")
    ap.add_argument("--courses", default=None, help="courses.jsonl.gz (enables chord check and shadow comparison)")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--out", default="data/sectors/progress.json")
    ns = ap.parse_args(argv)
    sp = Path(ns.sectors)
    if not sp.exists():
        print(f"rivernet report: {sp} missing - run resolve first", file=sys.stderr)
        return 1
    sectors = [json.loads(x) for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()]
    courses = waters = None
    if ns.courses and Path(ns.courses).exists():
        with gzip.open(ns.courses, "rt", encoding="utf-8") as f:
            courses = {c["course_id"]: c for c in (json.loads(x) for x in f if x.strip())}
        if Path(ns.waters).exists():
            waters = {w["slug"]: w for w in json.loads(Path(ns.waters).read_text(encoding="utf-8"))}
    prog = build_progress(sectors, waters, courses)
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(json.dumps(prog, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(markdown(prog))
    return 0
