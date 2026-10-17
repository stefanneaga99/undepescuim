"""QA report over the graph and courses (T2.3). Pure functions; output is
deterministic JSON written to ``data/rivernet/qa.json`` by the build step."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from .courses import Course
from .extract_schema import Extract
from .graph import WaterGraph
from .planar import PolygonIndex

LIST_LIMIT = 200
BORDER_BUFFER_M = 2000.0
DANUBE_KEYS = frozenset({"dunarea", "danube"})
SEGMENT_TOLERANCE_M = 0.15


def _max_segment_m(course: Course) -> float:
    vm = course.line.vertex_m
    spans = [(s["m_from"], s["m_to"]) for s in course.synthetic]
    worst = 0.0
    for a, b in zip(vm, vm[1:]):
        if any(a >= lo - SEGMENT_TOLERANCE_M and b <= hi + SEGMENT_TOLERANCE_M for lo, hi in spans):
            continue
        worst = max(worst, b - a)
    return worst


def _country_polygons(extract: Extract | None) -> list[PolygonIndex]:
    if extract is None:
        return []
    out = []
    for aid in sorted(extract.areas):
        t = extract.areas[aid].tags
        if t.get("boundary") == "administrative" and t.get("admin_level") == "2":
            try:
                out.append(PolygonIndex(dict(extract.areas[aid].geometry)))
            except (ValueError, KeyError):
                continue
    return out


def qa_report(wg: WaterGraph, courses: list[Course], extract: Extract | None = None) -> dict[str, Any]:
    ordered = sorted(courses, key=lambda c: c.course_id)

    cycles = []
    for comp in nx.strongly_connected_components(wg.g):
        if len(comp) > 1:
            nodes = sorted(comp)
            cycles.append({"size": len(nodes), "nodes": nodes[:10]})
    cycles.sort(key=lambda c: (-c["size"], c["nodes"][0]))

    danube = [c for c in ordered if c.name_key in DANUBE_KEYS]
    countries = _country_polygons(extract)
    sinks = []
    for c in ordered:
        if c.receives_into is not None:
            continue
        lon, lat = wg.node_coord(c.outlet_node)
        if any(d.line.locate(lon, lat)[1] <= BORDER_BUFFER_M for d in danube if d.course_id != c.course_id):
            continue
        if any(poly.boundary_distance_m(lon, lat, BORDER_BUFFER_M) <= BORDER_BUFFER_M for poly in countries):
            continue
        sinks.append({"course_id": c.course_id, "node": c.outlet_node, "lon": lon, "lat": lat})

    synth = [s for c in ordered for s in c.synthetic]
    segs = sorted(
        ({"course_id": c.course_id, "max_segment_m": round(_max_segment_m(c), 1)} for c in ordered),
        key=lambda r: (-r["max_segment_m"], r["course_id"]),
    )
    return {
        "courses_total": len(ordered),
        "km_total": round(sum(c.length_m for c in ordered) / 1000.0, 1),
        "graph": {"nodes": wg.node_count, "edges": wg.edge_count},
        "cycles_total": len(cycles),
        "cycles": cycles[:LIST_LIMIT],
        "sinks_inland_total": len(sinks),
        "sinks_inland": sinks[:LIST_LIMIT],
        "relation_splits": [c.course_id for c in ordered if "relation_split" in c.qa][:LIST_LIMIT],
        "synthetic_connectors": {
            "count": len(synth),
            "total_km": round(sum(s["m_to"] - s["m_from"] for s in synth) / 1000.0, 3),
            "max_gap_m": round(max((s["gap_m"] for s in synth), default=0.0), 1),
        },
        "max_segment_m_overall": segs[0]["max_segment_m"] if segs else 0.0,
        "max_segment_m": segs[:LIST_LIMIT],
        "courses_with_qa_flags": {
            flag: sum(1 for c in ordered if flag in c.qa)
            for flag in sorted({q for c in ordered for q in c.qa})
        },
    }


def write_qa(path: str | Path, report: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
