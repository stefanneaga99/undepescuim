"""Small pure-Python planar helpers on lon/lat (polygon tests, point-to-polygon
distance). Local equirectangular scaling is used for distances; at the scales
involved (tens of metres to a few km) its error is far below the data's.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

_CELL_DEG = 0.01


def metres_per_degree(lat: float) -> tuple[float, float]:
    """(metres per degree of longitude, metres per degree of latitude) at ``lat``."""
    p = math.radians(lat)
    m_lat = 111132.954 - 559.822 * math.cos(2 * p) + 1.175 * math.cos(4 * p)
    m_lon = 111412.84 * math.cos(p) - 93.5 * math.cos(3 * p) + 0.118 * math.cos(5 * p)
    return m_lon, m_lat


def _point_segment_dist_m(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    m_lon, m_lat = metres_per_degree(py)
    x, y = (px - ax) * m_lon, (py - ay) * m_lat
    dx, dy = (bx - ax) * m_lon, (by - ay) * m_lat
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, (x * dx + y * dy) / seg2))
    return math.hypot(x - t * dx, y - t * dy)


class PolygonIndex:
    """Even-odd point-in-polygon over a GeoJSON Polygon/MultiPolygon, with a
    latitude-bucketed edge index so a test costs O(edges in one latitude band)."""

    def __init__(self, geometry: dict[str, Any]):
        kind = geometry["type"]
        if kind == "Polygon":
            polygons = [geometry["coordinates"]]
        elif kind == "MultiPolygon":
            polygons = geometry["coordinates"]
        else:
            raise ValueError(f"unsupported geometry type {kind!r}")
        self._edges: list[tuple[float, float, float, float]] = []
        self._cells: dict[int, list[int]] = {}
        xs: list[float] = []
        ys: list[float] = []
        for polygon in polygons:
            for ring in polygon:
                for i in range(len(ring) - 1):
                    (x1, y1), (x2, y2) = ring[i][:2], ring[i + 1][:2]
                    idx = len(self._edges)
                    self._edges.append((x1, y1, x2, y2))
                    lo, hi = sorted((math.floor(y1 / _CELL_DEG), math.floor(y2 / _CELL_DEG)))
                    for c in range(lo, hi + 1):
                        self._cells.setdefault(c, []).append(idx)
                xs.extend(p[0] for p in ring)
                ys.extend(p[1] for p in ring)
        if not xs:
            raise ValueError("empty polygon")
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    def contains(self, lon: float, lat: float) -> bool:
        x0, y0, x1, y1 = self.bbox
        if lon < x0 or lon > x1 or lat < y0 or lat > y1:
            return False
        inside = False
        for idx in self._cells.get(math.floor(lat / _CELL_DEG), ()):
            ax, ay, bx, by = self._edges[idx]
            if (ay > lat) != (by > lat):
                if lon < ax + (lat - ay) * (bx - ax) / (by - ay):
                    inside = not inside
        return inside

    def distance_m(self, lon: float, lat: float, max_m: float = math.inf) -> float:
        """Distance to the polygon in metres (0 inside). Returns early with any
        value <= ``max_m`` once an edge that close is found."""
        if self.contains(lon, lat):
            return 0.0
        best = math.inf
        for ax, ay, bx, by in self._edges:
            d = _point_segment_dist_m(lon, lat, ax, ay, bx, by)
            if d < best:
                best = d
                if best <= max_m:
                    break
        return best


def bisect_boundary(
    a: Sequence[float], b: Sequence[float], poly: PolygonIndex, iterations: int = 40
) -> float:
    """Fraction t in [0,1] along a->b where inside/outside flips (a and b differ)."""
    inside_a = poly.contains(a[0], a[1])
    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = (lo + hi) / 2
        pt = (a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid)
        if poly.contains(pt[0], pt[1]) == inside_a:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
