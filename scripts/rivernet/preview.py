"""Class-2 physical preview for switched river groups (plan T4.2).

When a multi-contract ``riverGroup`` switches to pre-cut sectors (D8), the
legacy owner geometry that the Preview overlay drew as the group's physical
full course is gone. ``rivernet_preview`` replaces the physical candidates of
that group's records in ``public/data/preview_class2_physical.json`` with the
group's rivernet course, simplified at ``PREVIEW_SIMPLIFY_DEG``. Everything
else in the aggregate - the records' disclosure and legal status included -
is kept as is.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

from .publish import _round, simplify_dp

PREVIEW_SIMPLIFY_DEG = 0.0005


def switched_group_courses(
    new_waters: Sequence[Mapping[str, Any]],
    sectors: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    """riverGroup -> course_id for groups whose every member switched to a
    pre-cut sector on one and the same course."""
    members: dict[str, list[Mapping[str, Any]]] = {}
    for w in new_waters:
        if w.get("riverGroup"):
            members.setdefault(w["riverGroup"], []).append(w)
    out: dict[str, str] = {}
    for group, ws in sorted(members.items()):
        if len(ws) < 2 or any(w.get("geometryKind") != "sector" for w in ws):
            continue
        cids = {((sectors.get(w["slug"]) or {}).get("course") or {}).get("course_id") for w in ws}
        if len(cids) == 1 and None not in cids:
            out[group] = cids.pop()
    return out


def course_candidate(course: Mapping[str, Any], network_version: str) -> dict[str, Any]:
    from build_geometry_ledger import geometry_summary  # scripts/ is on the path

    coords = _round(simplify_dp(course["geometry"]["coordinates"], PREVIEW_SIMPLIFY_DEG))
    geometry = {"type": "LineString", "coordinates": coords}
    return {
        "componentCount": 1,
        "componentIds": [],
        "confidence": "source_backed_physical",
        "countyMatch": {"rationale": "rivernet course; county intervals are not legal proof", "status": "not_verified"},
        "geofabrikId": None,
        "geometry": geometry,
        "geometryHash": geometry_summary(geometry)["geometryHash"],
        "id": course["course_id"],
        "kind": "rivernet-course",
        "measuredLengthKm": round(course["length_m"] / 1000, 1),
        "osmId": f"relation/{course['relation_id']}" if course.get("relation_id") else None,
        "physicalSourceUrl": None,
        "rating": "source_backed_physical",
        "source": f"rivernet:{network_version}",
        "sourceBranch": "rivernet",
        "sourceCommit": network_version,
        "sourceId": course["course_id"],
        "topology": {"findings": [], "status": "not_applicable"},
    }


def rivernet_preview(
    payload: Mapping[str, Any],
    new_waters: Sequence[Mapping[str, Any]],
    sectors: Mapping[str, Mapping[str, Any]],
    courses: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """(new aggregate, replaced riverGroups). The input is not modified."""
    groups = switched_group_courses(new_waters, sectors)
    out = copy.deepcopy(dict(payload))
    replaced: set[str] = set()
    for record in out.get("records", []):
        cid = groups.get(record.get("riverGroup") or "")
        course = courses.get(cid or "")
        if course is None:
            continue
        version = (sectors.get(record.get("slug")) or {}).get("network_version") or ""
        record["physicalCandidates"] = [course_candidate(course, version)]
        replaced.add(record["riverGroup"])
    out["candidateCount"] = sum(len(r.get("physicalCandidates", [])) for r in out.get("records", []))
    return out, sorted(replaced)
