"""Pure, read-only topology and coverage primitives for the segment audit.

All public functions accept ordinary JSON-compatible dictionaries/lists.  No
function mutates its input, reads a cache, or performs network access.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Iterable, Sequence

Coord = Sequence[float]  # [longitude, latitude]
EARTH_M = 6_371_000.0

def haversine_m(a: Coord, b: Coord) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlon, dlat = lon2 - lon1, lat2 - lat1
    q = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_M * math.asin(min(1.0, math.sqrt(q)))

def line_length_m(line: Sequence[Coord]) -> float:
    return sum(haversine_m(a, b) for a, b in zip(line, line[1:]))

def _edge_graph(ways: Iterable[dict], snap_eps_m: float = 0) -> tuple[dict, dict]:
    """Return adjacency and edge metadata, joining endpoint coordinates."""
    graph: dict[object, set] = defaultdict(set)
    edges: dict[tuple[object, object], dict] = {}
    keys: list[tuple[object, Coord]] = []
    def key(coord: Coord):
        if snap_eps_m <= 0:
            return tuple(coord)
        for old, point in keys:
            if haversine_m(coord, point) <= snap_eps_m:
                return old
        value = len(keys)
        keys.append((value, coord))
        return value
    for way in sorted(ways, key=lambda w: int(w.get("osm_id", w.get("id", 0)))):
        coords = way.get("coordinates") or way.get("geometry") or []
        if len(coords) < 2:
            continue
        first, last = key(coords[0]), key(coords[-1])
        graph[first].add(last); graph[last].add(first)
        edge = (first, last) if repr(first) <= repr(last) else (last, first)
        edges[edge] = {"way_id": way.get("osm_id", way.get("id")), "length_m": line_length_m(coords), "coordinates": [list(p) for p in coords]}
    return graph, edges

def connected_components(ways: Iterable[dict], snap_eps_m: float = 0) -> list[list[int]]:
    graph, edges = _edge_graph(ways, snap_eps_m)
    seen = set(); result = []
    for start in sorted(graph, key=repr):
        if start in seen: continue
        stack = [start]; seen.add(start); ids = []
        while stack:
            node = stack.pop()
            for nxt in sorted(graph[node], key=repr):
                edge = (node, nxt) if repr(node) <= repr(nxt) else (nxt, node)
                if edge in edges: ids.append(edges[edge]["way_id"])
                if nxt not in seen: seen.add(nxt); stack.append(nxt)
        result.append(sorted(set(i for i in ids if i is not None)))
    return sorted(result, key=lambda x: (x[0] if x else -1, len(x)))

def topology(ways: Iterable[dict], snap_eps_m: float = 0) -> dict:
    graph, edges = _edge_graph(ways, snap_eps_m)
    degrees = {str(k): len(v) for k, v in sorted(graph.items(), key=lambda kv: repr(kv[0]))}
    return {"components": len(connected_components(ways, snap_eps_m)), "node_degree": degrees,
            "branch_nodes": sorted(k for k, v in degrees.items() if v > 2),
            "ways": sorted(edges)}

def main_stem(ways: Iterable[dict], snap_eps_m: float = 0) -> list[int]:
    """Choose the longest terminal-to-terminal path deterministically.

    This intentionally returns way IDs only; callers retain the original
    coordinates and can report branch evidence without concatenating branches.
    """
    graph, edges = _edge_graph(ways, snap_eps_m)
    terminals = [n for n, adj in graph.items() if len(adj) == 1]
    if len(terminals) < 2: return []
    best = None
    for source in sorted(terminals, key=repr):
        stack = [(source, None, 0.0, [])]
        while stack:
            node, parent, dist, ids = stack.pop()
            if node != source and node in terminals:
                candidate = (dist, tuple(sorted(ids)), tuple(ids))
                if best is None or candidate[:2] > best[:2]: best = candidate
            for nxt in graph[node]:
                if nxt == parent: continue
                edge = (node, nxt) if repr(node) <= repr(nxt) else (nxt, node)
                meta = edges[edge]
                stack.append((nxt, node, dist + meta["length_m"], ids + [meta["way_id"]]))
    return list(best[2]) if best else []

def _nearest_distance(point: Coord, line: Sequence[Coord]) -> float:
    # Local equirectangular projection is ample for the <=250 m tolerances and
    # avoids treating sparse OSM vertices as gaps in an otherwise continuous way.
    if not line:
        return float("inf")
    scale = math.cos(math.radians(point[1]))
    best = float("inf")
    for a, b in zip(line, line[1:]):
        ax, ay = (a[0] - point[0]) * scale, a[1] - point[1]
        bx, by = (b[0] - point[0]) * scale, b[1] - point[1]
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        t = max(0.0, min(1.0, -(ax * dx + ay * dy) / denom)) if denom else 0.0
        candidate = [point[0] + (ax + t * dx) / scale, point[1] + ay + t * dy]
        best = min(best, haversine_m(point, candidate))
    return best if len(line) > 1 else haversine_m(point, line[0])

def sample_line(line: Sequence[Coord], spacing_m: float = 100.0) -> list[dict]:
    if len(line) < 2: return []
    total = line_length_m(line)
    count = max(2, int(math.ceil(total / spacing_m)) + 1)
    out = []
    for i in range(count):
        fraction = i / (count - 1)
        target = total * fraction; walked = 0.0
        for a, b in zip(line, line[1:]):
            seg = haversine_m(a, b)
            if walked + seg >= target or b == line[-1]:
                t = 0 if seg == 0 else (target - walked) / seg
                out.append({"fraction": fraction, "cumulative_m": target, "coordinate": [a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t]})
                break
            walked += seg
    return out

def uncovered_intervals(samples: Sequence[dict], tolerance_m: float = 125.0, min_length_m: float = 250.0) -> list[dict]:
    """Collapse consecutive uncovered samples into deterministic intervals."""
    bad = [s for s in samples if s.get("distance_m", float("inf")) > tolerance_m]
    out = []
    for a, b in zip(bad, bad[1:]):
        if b["fraction"] - a["fraction"] <= 0: continue
        length = b.get("cumulative_m", 0) - a.get("cumulative_m", 0)
        if length >= min_length_m:
            out.append({"start_fraction": a["fraction"], "end_fraction": b["fraction"], "length_m": length,
                        "midpoint": b.get("coordinate")})
    return out

def coverage(published: Sequence[Coord], osm: Sequence[Coord], tolerance_m: float = 125.0) -> dict:
    pub = sample_line(published, max(100.0, line_length_m(published) / 100))
    raw = sample_line(osm, max(100.0, line_length_m(osm) / 100))
    for sample in pub: sample["distance_m"] = _nearest_distance(sample["coordinate"], osm)
    for sample in raw: sample["distance_m"] = _nearest_distance(sample["coordinate"], published)
    return {"published_to_osm": sum(s["distance_m"] <= tolerance_m for s in pub) / len(pub) if pub else 0.0,
            "osm_to_published": sum(s["distance_m"] <= tolerance_m for s in raw) / len(raw) if raw else 0.0,
            "published_samples": pub, "osm_samples": raw}

def distance_m(a: Coord, b: Coord) -> float:
    return haversine_m(a, b)

def line_length(coords: Sequence[Coord]) -> float:
    return line_length_m(coords)

def coverage_fraction(points: Sequence[Coord], published: Sequence[Coord], tolerance_m: float = 125.0) -> float:
    if not points:
        return 0.0
    return sum(_nearest_distance(p, published) <= tolerance_m for p in points) / len(points)

def uncovered_runs(source: Sequence[Coord], published: Sequence[Coord], tolerance_m: float = 125.0, min_report_m: float = 250.0) -> list[dict]:
    samples = sample_line(source, max(100.0, line_length_m(source) / 100))
    for sample in samples:
        sample["distance_m"] = _nearest_distance(sample["coordinate"], published)
    return uncovered_intervals(samples, tolerance_m, min_report_m)

def terminal_findings(osm: Sequence[Coord], published: Sequence[Coord], terminal_gap_m: float = 250.0) -> list[str]:
    if not osm or not published:
        return []
    findings = []
    if _nearest_distance(published[0], osm) > terminal_gap_m:
        findings.append("truncated_head")
    if _nearest_distance(published[-1], osm) > terminal_gap_m:
        findings.append("truncated_mouth")
    return findings

def canonical_county(value: str) -> str:
    import unicodedata
    s = " ".join((value or "").replace("Ţ", "Ț").replace("ţ", "ț").split()).strip()
    return s[:1].upper() + s[1:].lower() if s else s

def duplicate_way_ids(way_ids: Sequence[int | str]) -> list[int]:
    seen, repeated = set(), set()
    for value in way_ids:
        try:
            wid = int(value)
        except (TypeError, ValueError):
            continue
        if wid in seen:
            repeated.add(wid)
        seen.add(wid)
    return sorted(repeated)

def sector_findings(contracts: Sequence[dict]) -> list[dict]:
    findings = []
    for water in contracts:
        start, end = water.get("sectorStart"), water.get("sectorEnd")
        if start is None and end is None:
            continue
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not (0 <= start < end <= 1):
            findings.append({"code": "sector_mismatch", "slug": water.get("slug"), "reason": "invalid_interval"})
    ordered = sorted((w for w in contracts if isinstance(w.get("sectorStart"), (int, float)) and isinstance(w.get("sectorEnd"), (int, float))), key=lambda w: (w["sectorStart"], w["sectorEnd"], w.get("slug", "")))
    for left, right in zip(ordered, ordered[1:]):
        if right["sectorStart"] < left["sectorEnd"]:
            findings.append({"code": "sector_mismatch", "slug": right.get("slug"), "reason": "overlap"})
    return findings

def stable_report(report: dict) -> dict:
    report["rivers"] = sorted(report.get("rivers", []), key=lambda r: (str(r.get("river_group") or ""), str(r.get("osm", {}).get("osm_id") or "")))
    report["cells"] = sorted(report.get("cells", []), key=lambda c: (c.get("cell_id", ""), c.get("county", "")))
    return report
