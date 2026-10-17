"""River courses with linear referencing (T2.2, plan §3.4).

A *course* is one continuous upstream->downstream polyline for a named river:
either an OSM ``type=waterway`` relation or a group of same-named/wikidata ways.
Braids are dropped (longest path), small gaps are bridged by flagged synthetic
connectors, and every course carries cumulative metre measures so sectors can be
expressed as (course_id, m_from, m_to).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable

import networkx as nx

from .extract_schema import Area, Extract
from .geodesy import vincenty_m
from .graph import WaterGraph
from .lr import Line
from .planar import PolygonIndex, bisect_boundary
from .textnorm import fix_diacritics, river_key

GAP_BRIDGE_MAX_M = 250.0
RESERVOIR_CROSSING_MAX_M = 5000.0
RESERVOIR_NEAR_M = 50.0
RELATION_WATERWAYS = frozenset({"river", "stream", "canal"})
MAIN_ROLES = frozenset({"main_stream", ""})
COORD_DECIMALS = 6

EdgeRef = tuple[int, int, str]  # (u, v, key)


@dataclass
class Course:
    course_id: str
    name: str
    name_key: str
    aliases: list[str]
    wikidata: str | None
    relation_id: int | None
    way_ids: list[int]
    line: Line
    nodes: list[int]  # graph node ids along the course (synthetic hops included)
    node_vertex: list[int]  # vertex index of each entry in ``nodes``
    edges: list[EdgeRef]  # path edges, upstream -> downstream
    outlet_node: int
    receives_into: str | None = None
    junctions: list[dict[str, Any]] = field(default_factory=list)
    synthetic: list[dict[str, Any]] = field(default_factory=list)
    braids_dropped_m: float = 0.0
    braid_edges: list[EdgeRef] = field(default_factory=list)
    counties: list[dict[str, Any]] = field(default_factory=list)
    qa: list[str] = field(default_factory=list)

    @property
    def length_m(self) -> float:
        return self.line.length_m

    def to_record(self) -> dict[str, Any]:
        return {
            "course_id": self.course_id,
            "name": self.name,
            "name_key": self.name_key,
            "aliases": self.aliases,
            "wikidata": self.wikidata,
            "relation_id": self.relation_id,
            "way_ids": self.way_ids,
            "length_m": round(self.line.length_m, 1),
            "geometry": {"type": "LineString", "coordinates": [list(c) for c in self.line.coords]},
            "vertex_m": [round(m, 1) for m in self.line.vertex_m],
            "outlet_node": self.outlet_node,
            "receives_into": self.receives_into,
            "junctions": self.junctions,
            "synthetic": self.synthetic,
            "braids_dropped_m": round(self.braids_dropped_m, 1),
            "counties": self.counties,
            "qa": sorted(set(self.qa)),
        }


# ---------------------------------------------------------------- path finding


@dataclass
class _Path:
    nodes: list[int]
    edges: list[EdgeRef]
    dropped: list[EdgeRef]
    qa: list[str]


def _edge_len(wg: WaterGraph, e: EdgeRef) -> float:
    return wg.g.edges[e]["length_m"]


def _longest_path(wg: WaterGraph, edges: list[EdgeRef]) -> _Path | None:
    """Longest source->sink path of one weakly connected edge set.

    Returns ``None`` for a component without a usable edge (only self-loops).
    """
    qa: list[str] = []
    # collapse parallel edges to the longest one (ties: smallest key)
    best: dict[tuple[int, int], EdgeRef] = {}
    for e in sorted(edges, key=lambda e: (e[0], e[1], e[2])):
        k = (e[0], e[1])
        if k not in best or _edge_len(wg, e) > _edge_len(wg, best[k]):
            best[k] = e
    dg = nx.DiGraph()
    for (u, v), e in best.items():
        if u != v:
            dg.add_edge(u, v, ref=e, w=_edge_len(wg, e))
    if dg.number_of_edges() == 0:
        return None
    # break cycles by dropping the shortest edge of each cycle
    while True:
        try:
            cycle = nx.find_cycle(dg)
        except nx.NetworkXNoCycle:
            break
        victim = min(cycle, key=lambda uv: (dg.edges[uv]["w"], dg.edges[uv]["ref"][2]))[:2]
        dg.remove_edge(*victim)
        qa.append("cycle_broken")
    order = list(nx.lexicographical_topological_sort(dg))
    dist: dict[int, float] = {}
    prev: dict[int, int | None] = {}
    for n in order:
        preds = sorted(dg.predecessors(n))
        if not preds:
            dist[n], prev[n] = 0.0, None
            continue
        cand = [(dist[p] + dg.edges[p, n]["w"], -p) for p in preds]
        top = max(cand)
        dist[n], prev[n] = top[0], -top[1]
    sinks = sorted(n for n in dg.nodes if dg.out_degree(n) == 0)
    if len(sinks) > 1:
        qa.append("multiple_sinks")
    sink = max(sinks, key=lambda n: (dist[n], -n))
    nodes = [sink]
    while prev[nodes[-1]] is not None:
        nodes.append(prev[nodes[-1]])  # type: ignore[arg-type]
    nodes.reverse()
    path_edges = [dg.edges[a, b]["ref"] for a, b in zip(nodes, nodes[1:])]
    used = set(path_edges)
    dropped = sorted({e for e in edges if e not in used})
    return _Path(nodes=nodes, edges=path_edges, dropped=dropped, qa=qa)


def _components(edges: Iterable[EdgeRef]) -> list[list[EdgeRef]]:
    ug = nx.Graph()
    for e in edges:
        ug.add_edge(e[0], e[1])
    node_comp: dict[int, int] = {}
    comps = sorted((sorted(c) for c in nx.connected_components(ug)), key=lambda c: c[0])
    for i, c in enumerate(comps):
        for n in c:
            node_comp[n] = i
    out: list[list[EdgeRef]] = [[] for _ in comps]
    for e in sorted(edges):
        out[node_comp[e[0]]].append(e)
    return out


class _Reservoirs:
    def __init__(self, extract: Extract):
        self.items: list[tuple[str, PolygonIndex]] = []
        for aid in sorted(extract.areas):
            area = extract.areas[aid]
            t = area.tags
            if t.get("water") in ("reservoir", "lake") or t.get("landuse") == "reservoir":
                try:
                    self.items.append((aid, PolygonIndex(dict(area.geometry))))
                except (ValueError, KeyError):
                    continue

    def shared(self, p: tuple[float, float], q: tuple[float, float]) -> bool:
        for _aid, poly in self.items:
            if poly.distance_m(p[0], p[1], RESERVOIR_NEAR_M) <= RESERVOIR_NEAR_M and (
                poly.distance_m(q[0], q[1], RESERVOIR_NEAR_M) <= RESERVOIR_NEAR_M
            ):
                return True
        return False


@dataclass
class _Chain:
    """One or more component paths joined by synthetic connectors."""

    parts: list[_Path]
    links: list[dict[str, Any]]  # links[i] joins parts[i] -> parts[i+1]


def _chain_paths(wg: WaterGraph, paths: list[_Path], reservoirs: _Reservoirs) -> list[_Chain]:
    """Greedy chaining of component paths by smallest end->start gap."""
    n = len(paths)
    if n == 1:
        return [_Chain(paths, [])]
    cand = []
    for i, a in enumerate(paths):
        end = wg.node_coord(a.nodes[-1])
        for j, b in enumerate(paths):
            if i == j:
                continue
            start = wg.node_coord(b.nodes[0])
            gap = vincenty_m(end[0], end[1], start[0], start[1])
            if gap <= GAP_BRIDGE_MAX_M:
                kind = "gap_bridge"
            elif gap <= RESERVOIR_CROSSING_MAX_M and reservoirs.shared(end, start):
                kind = "reservoir_crossing"
            else:
                continue
            cand.append((gap, i, j, kind))
    cand.sort()
    nxt: dict[int, tuple[int, float, str]] = {}
    has_prev: set[int] = set()
    head_of = {i: i for i in range(n)}  # union-find over chains to avoid cycles

    def find(x: int) -> int:
        while head_of[x] != x:
            head_of[x] = head_of[head_of[x]]
            x = head_of[x]
        return x

    for gap, i, j, kind in cand:
        if i in nxt or j in has_prev or find(i) == find(j):
            continue
        nxt[i] = (j, gap, kind)
        has_prev.add(j)
        head_of[find(i)] = find(j)
    chains = []
    for start in range(n):
        if start in has_prev:
            continue
        parts, links, cur = [paths[start]], [], start
        while cur in nxt:
            j, gap, kind = nxt[cur]
            links.append({"gap_m": gap, "kind": kind})
            parts.append(paths[j])
            cur = j
        chains.append(_Chain(parts, links))
    return chains


# --------------------------------------------------------------- course build


def _assemble(
    wg: WaterGraph,
    chain: _Chain,
) -> tuple[Line, list[int], list[int], list[int], list[dict[str, Any]], list[EdgeRef]]:
    """Concatenate coordinates -> (line, nodes, node_vertex, way_ids, synthetic, edges)."""
    coords: list[tuple[float, float]] = []
    nodes: list[int] = []
    node_vertex: list[int] = []
    way_ids: list[int] = []
    edges: list[EdgeRef] = []
    synth_ranges: list[tuple[int, int, dict[str, Any]]] = []  # vertex index range

    def push(c: list[float] | tuple[float, float]) -> int:
        pt = (round(c[0], COORD_DECIMALS), round(c[1], COORD_DECIMALS))
        if not coords or coords[-1] != pt:
            coords.append(pt)
        return len(coords) - 1

    for pi, part in enumerate(chain.parts):
        if pi > 0:
            link = chain.links[pi - 1]
            before = len(coords) - 1
            first = wg.node_coord(part.nodes[0])
            idx = push(first)
            synth_ranges.append((before, idx, link))
        for ei, e in enumerate(part.edges):
            data = wg.g.edges[e]
            if ei == 0 and (pi == 0 or not nodes or nodes[-1] != e[0]):
                nodes.append(e[0])
                node_vertex.append(push(data["coords"][0]))
            for c in data["coords"][1:-1]:
                push(c)
            nodes.append(e[1])
            node_vertex.append(push(data["coords"][-1]))
            edges.append(e)
            if not way_ids or way_ids[-1] != data["way_id"]:
                way_ids.append(data["way_id"])
        if not part.edges:  # pragma: no cover - a path has >= 1 edge
            continue
    line = Line.from_coords(coords)
    synthetic = []
    for a, b, link in synth_ranges:
        synthetic.append(
            {
                "m_from": round(line.vertex_m[a], 1),
                "m_to": round(line.vertex_m[b], 1),
                "kind": link["kind"],
                "gap_m": round(link["gap_m"], 1),
            }
        )
    return line, nodes, node_vertex, way_ids, synthetic, edges


def _majority(values: list[str]) -> str:
    if not values:
        return ""
    counts = Counter(values)
    top = max(counts.values())
    return sorted(v for v, c in counts.items() if c == top)[0]


def _make_course(
    wg: WaterGraph,
    chain: _Chain,
    course_id: str,
    meta: dict[str, Any],
    qa: list[str],
) -> Course:
    line, nodes, node_vertex, way_ids, synthetic, edges = _assemble(wg, chain)
    dropped = [e for part in chain.parts for e in part.dropped]
    qa = list(qa) + [q for part in chain.parts for q in part.qa]
    if synthetic:
        qa.append("has_synthetic")
    return Course(
        course_id=course_id,
        name=meta["name"],
        name_key=meta["name_key"],
        aliases=meta.get("aliases", []),
        wikidata=meta.get("wikidata"),
        relation_id=meta.get("relation_id"),
        way_ids=way_ids,
        line=line,
        nodes=nodes,
        node_vertex=node_vertex,
        edges=edges,
        outlet_node=nodes[-1],
        synthetic=synthetic,
        braids_dropped_m=sum(_edge_len(wg, e) for e in dropped),
        braid_edges=dropped,
        qa=qa,
    )


def _aliases(tags: dict[str, str], name: str) -> list[str]:
    found: set[str] = set()
    for key, value in tags.items():
        if key in ("alt_name", "old_name", "official_name", "int_name") or key.startswith("name:"):
            for part in value.split(";"):
                part = fix_diacritics(part.strip())
                if part and part != name:
                    found.add(part)
    return sorted(found)


def _merge_partial_wikidata(wg: WaterGraph, groups: dict[str, list[EdgeRef]]) -> None:
    """Fold a name-only group (``nk:x``) into the wikidata group whose majority
    name key is ``x`` when exactly one such group exists.

    Wikidata is often tagged on part of a river's ways only (Teleajen: the
    lower 31 km), which split one river into consecutive courses. Same-named
    rivers elsewhere are unaffected: chaining still needs shared nodes or a
    gap of at most GAP_BRIDGE_MAX_M, so far-apart pieces stay separate courses.
    """
    by_key: dict[str, list[str]] = {}
    for gkey in sorted(groups):
        if gkey.startswith("wd:"):
            key = _majority([wg.g.edges[e]["name_key"] for e in groups[gkey]])
            by_key.setdefault(key, []).append(gkey)
    for key, wds in by_key.items():
        nk = f"nk:{key}"
        if len(wds) == 1 and nk in groups:
            groups[wds[0]] = sorted(groups[wds[0]] + groups.pop(nk), key=lambda e: (e[2], e[0], e[1]))


def build_courses(wg: WaterGraph, extract: Extract) -> list[Course]:
    reservoirs = _Reservoirs(extract)
    courses: list[Course] = []
    used_edges: set[EdgeRef] = set()

    edges_by_way: dict[int, list[EdgeRef]] = {}
    for u, v, k in sorted(wg.g.edges(keys=True), key=lambda e: (e[2], e[0], e[1])):
        edges_by_way.setdefault(wg.g.edges[u, v, k]["way_id"], []).append((u, v, k))

    # 1. relation courses
    for rid in sorted(extract.rels):
        rel = extract.rels[rid]
        if rel.tags.get("type") != "waterway" or rel.tags.get("waterway") not in RELATION_WATERWAYS:
            continue
        members = [m.ref for m in rel.members if m.type == "w" and m.role in MAIN_ROLES]
        edges: list[EdgeRef] = []
        missing = False
        for wid in members:
            if wid in edges_by_way:
                edges.extend(edges_by_way[wid])
            else:
                missing = True
        if not edges:
            continue
        used_edges.update(edges)
        name = fix_diacritics(rel.tags.get("name", ""))
        meta = {
            "name": name,
            "name_key": river_key(name),
            "aliases": _aliases(dict(rel.tags), name),
            "wikidata": rel.tags.get("wikidata") or None,
            "relation_id": rid,
        }
        paths = [p for p in (_longest_path(wg, comp) for comp in _components(edges)) if p]
        if not paths:
            continue
        chains = _chain_paths(wg, paths, reservoirs)
        chains.sort(key=lambda c: min(wg.g.edges[e]["way_id"] for p in c.parts for e in p.edges))
        for k, chain in enumerate(chains, start=1):
            cid = f"rel:{rid}" if len(chains) == 1 else f"rel:{rid}:{k}"
            qa = ["relation_member_missing"] if missing else []
            if len(chains) > 1:
                qa.append("relation_split")
            courses.append(_make_course(wg, chain, cid, meta, qa))

    # 2. name courses
    groups: dict[str, list[EdgeRef]] = {}
    for e in sorted(wg.g.edges(keys=True), key=lambda e: (e[2], e[0], e[1])):
        if e in used_edges:
            continue
        data = wg.g.edges[e]
        if not data["name_key"]:
            continue
        gkey = f"wd:{data['wikidata']}" if data["wikidata"] else f"nk:{data['name_key']}"
        groups.setdefault(gkey, []).append(e)
    _merge_partial_wikidata(wg, groups)
    for gkey in sorted(groups):
        gedges = groups[gkey]
        paths = [p for p in (_longest_path(wg, comp) for comp in _components(gedges)) if p]
        if not paths:
            continue
        chains = _chain_paths(wg, paths, reservoirs)
        for chain in chains:
            chain_edges = [e for p in chain.parts for e in p.edges]
            names = [wg.g.edges[e]["name"] for e in chain_edges if wg.g.edges[e]["name"]]
            keys = [wg.g.edges[e]["name_key"] for e in chain_edges]
            wds = [wg.g.edges[e]["wikidata"] for e in chain_edges if wg.g.edges[e]["wikidata"]]
            name_key = _majority(keys)
            meta = {
                "name": fix_diacritics(_majority(names)),
                "name_key": name_key,
                "aliases": [],
                "wikidata": _majority(wds) or None,
                "relation_id": None,
            }
            outlet = chain.parts[-1].nodes[-1]
            courses.append(_make_course(wg, chain, f"name:{name_key}:n{outlet}", meta, []))

    courses.sort(key=lambda c: c.course_id)
    _link_courses(wg, courses)
    _assign_counties(courses, extract)
    return courses


# ------------------------------------------------------- junctions & outlets


def _link_courses(wg: WaterGraph, courses: list[Course]) -> None:
    edge_course: dict[EdgeRef, str] = {}
    node_courses: dict[int, list[tuple[str, int]]] = {}
    for c in courses:
        for e in c.edges:
            edge_course[e] = c.course_id
        for pos, n in enumerate(c.nodes):
            node_courses.setdefault(n, []).append((c.course_id, pos))
    by_id = {c.course_id: c for c in courses}

    for c in courses:
        # 5. receiving course
        candidates: set[str] = set()
        for cid, pos in node_courses.get(c.outlet_node, []):
            other = by_id[cid]
            if cid != c.course_id and pos != len(other.nodes) - 1:
                candidates.add(cid)
        for _u, _v, key, _d in wg.out_edges(c.outlet_node):
            owner = edge_course.get((_u, _v, key))
            if owner and owner != c.course_id:
                candidates.add(owner)
        c.receives_into = sorted(candidates)[0] if candidates else None

        # 6. junctions at interior nodes
        own = set(c.edges) | set(c.braid_edges)
        junctions = []
        for pos in range(1, len(c.nodes) - 1):
            node = c.nodes[pos]
            for u, v, key, _d in wg.in_edges(node):
                e = (u, v, key)
                if e in own:
                    continue
                trib = edge_course.get(e)
                if trib == c.course_id:
                    continue
                junctions.append(
                    {
                        "node": node,
                        "m": round(c.line.vertex_m[c.node_vertex[pos]], 1),
                        "tributary_course_id": trib,
                        "side": "in",
                    }
                )
        junctions.sort(key=lambda j: (j["m"], j["node"], j["tributary_course_id"] or ""))
        c.junctions = junctions


# ----------------------------------------------------------------- counties


def _county_name(area: Area) -> str:
    name = fix_diacritics(area.tags.get("name", "")).strip()
    for prefix in ("Județul ", "Județ "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def county_intervals(line: Line, poly: PolygonIndex) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = poly.bbox
    coords = line.coords
    if not any(x0 <= c[0] <= x1 and y0 <= c[1] <= y1 for c in coords):
        return []
    state = [poly.contains(c[0], c[1]) for c in coords]
    out: list[tuple[float, float]] = []
    start: float | None = 0.0 if state[0] else None
    for i in range(len(coords) - 1):
        if state[i] == state[i + 1]:
            continue
        t = bisect_boundary(coords[i], coords[i + 1], poly)
        m = line.vertex_m[i] + t * (line.vertex_m[i + 1] - line.vertex_m[i])
        if state[i + 1]:
            start = m
        else:
            out.append((start if start is not None else 0.0, m))
            start = None
    if start is not None:
        out.append((start, line.length_m))
    merged: list[tuple[float, float]] = []
    for a, b in out:
        if merged and a - merged[-1][1] <= 0.5:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def _assign_counties(courses: list[Course], extract: Extract) -> None:
    counties = []
    for aid in sorted(extract.areas):
        area = extract.areas[aid]
        if area.tags.get("boundary") == "administrative" and area.tags.get("admin_level") == "4":
            try:
                counties.append((_county_name(area), PolygonIndex(dict(area.geometry))))
            except (ValueError, KeyError):
                continue
    counties.sort(key=lambda c: c[0])
    for c in courses:
        entries = []
        for name, poly in counties:
            for a, b in county_intervals(c.line, poly):
                entries.append({"county": name, "m_from": round(a, 1), "m_to": round(b, 1)})
        entries.sort(key=lambda e: (e["m_from"], e["county"]))
        c.counties = entries
