"""Directed waterway graph built from the normalised OSM extract (T2.1).

Topology comes only from shared OSM node ids (decision D2): two ways that merely
cross or touch geometrically are NOT connected. Nodes are way endpoints and
junction nodes (shared by >= 2 flow ways); every way is split at its junctions
into directed edges following the OSM way direction.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterator

import networkx as nx

from .extract_schema import Extract, Way
from .geodesy import line_length_m
from .textnorm import river_key

# waterway=* values that carry flowing water and take part in the network
FLOW_WATERWAYS = frozenset({"river", "stream", "canal", "drain", "ditch", "brook"})


@dataclass
class WaterGraph:
    g: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)
    _by_key: dict[str, list[tuple[int, int, str]]] = field(default_factory=dict)

    def node_coord(self, node_id: int) -> tuple[float, float]:
        return self.g.nodes[node_id]["coord"]

    def out_edges(self, node_id: int) -> list[tuple[int, int, str, dict[str, Any]]]:
        return sorted(self.g.out_edges(node_id, keys=True, data=True), key=lambda e: e[2])

    def in_edges(self, node_id: int) -> list[tuple[int, int, str, dict[str, Any]]]:
        return sorted(self.g.in_edges(node_id, keys=True, data=True), key=lambda e: e[2])

    def edges_by_name_key(self, key: str) -> list[tuple[int, int, str, dict[str, Any]]]:
        return [(u, v, k, self.g.edges[u, v, k]) for (u, v, k) in self._by_key.get(key, [])]

    def edge_ids(self) -> Iterator[str]:
        for _u, _v, k in self.g.edges(keys=True):
            yield k

    @property
    def node_count(self) -> int:
        return self.g.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.g.number_of_edges()


def _flow_ways(extract: Extract) -> list[Way]:
    ways = [
        w
        for w in extract.ways.values()
        if w.tags.get("waterway") in FLOW_WATERWAYS and len(w.nodes) >= 2 and len(w.nodes) == len(w.coords)
    ]
    ways.sort(key=lambda w: w.id)
    return ways


def build_graph(extract: Extract) -> WaterGraph:
    ways = _flow_ways(extract)

    # a node is a junction when it belongs to >= 2 distinct flow ways
    membership: Counter[int] = Counter()
    for w in ways:
        for nid in set(w.nodes):
            membership[nid] += 1

    wg = WaterGraph()
    for w in ways:
        last = len(w.nodes) - 1
        cut = [i for i, nid in enumerate(w.nodes) if i in (0, last) or membership[nid] >= 2]
        name = w.tags.get("name", "")
        attrs = {
            "way_id": w.id,
            "waterway": w.tags.get("waterway", ""),
            "name": name,
            "name_key": river_key(name),
            "wikidata": w.tags.get("wikidata", ""),
            "intermittent": w.tags.get("intermittent", "") == "yes",
            "tunnel": w.tags.get("tunnel", ""),
        }
        for seq, (a, b) in enumerate(zip(cut, cut[1:])):
            u, v = w.nodes[a], w.nodes[b]
            coords = [list(c) for c in w.coords[a : b + 1]]
            key = f"{w.id}:{seq}"
            for nid, idx in ((u, a), (v, b)):
                if nid not in wg.g:
                    wg.g.add_node(nid, coord=w.coords[idx])
            wg.g.add_edge(
                u, v, key=key, seq=seq, coords=coords,
                length_m=round(line_length_m(coords), 3), **attrs,
            )
            if attrs["name_key"]:
                wg._by_key.setdefault(attrs["name_key"], []).append((u, v, key))
    return wg
