"""Linear referencing along a course polyline (T2.2).

Measures are cumulative geodesic metres along the line (WGS84 ellipsoid). The
plan names EPSG:3844 + shapely; this pure-Python equivalent is used instead so
the module is dependency-free and testable offline (the two differ by < 0.03 %,
EPSG:3844's own scale error). Between two vertices, positions are interpolated
linearly in lon/lat, which is exact to well under a millimetre at segment scale.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from .geodesy import vincenty_m
from .planar import metres_per_degree

Coord = tuple[float, float]


def vertex_measures(coords: list[Coord]) -> list[float]:
    out = [0.0]
    for i in range(len(coords) - 1):
        out.append(out[-1] + vincenty_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]))
    return out


@dataclass(frozen=True)
class Line:
    coords: tuple[Coord, ...]
    vertex_m: tuple[float, ...]

    @classmethod
    def from_coords(cls, coords: list[Coord]) -> "Line":
        if len(coords) < 2:
            raise ValueError("a line needs at least two vertices")
        return cls(tuple((float(x), float(y)) for x, y in coords), tuple(vertex_measures(list(coords))))

    @property
    def length_m(self) -> float:
        return self.vertex_m[-1]

    def point_at(self, m: float) -> Coord:
        m = min(max(m, 0.0), self.length_m)
        i = min(bisect.bisect_right(self.vertex_m, m) - 1, len(self.coords) - 2)
        seg = self.vertex_m[i + 1] - self.vertex_m[i]
        t = 0.0 if seg == 0 else (m - self.vertex_m[i]) / seg
        (x1, y1), (x2, y2) = self.coords[i], self.coords[i + 1]
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    def substring(self, m_from: float, m_to: float) -> list[Coord]:
        """Vertices of the sub-line between two measures (exact end points)."""
        if m_from > m_to:
            raise ValueError("m_from must be <= m_to")
        m_from = min(max(m_from, 0.0), self.length_m)
        m_to = min(max(m_to, 0.0), self.length_m)
        out = [self.point_at(m_from)]
        lo = bisect.bisect_right(self.vertex_m, m_from)
        hi = bisect.bisect_left(self.vertex_m, m_to)
        out.extend(self.coords[lo:hi])
        end = self.point_at(m_to)
        if end != out[-1]:
            out.append(end)
        if len(out) == 1:
            out.append(end)
        return out

    def locate(self, lon: float, lat: float) -> tuple[float, float]:
        """(measure, distance in metres) of the nearest point on the line."""
        m_lon, m_lat = metres_per_degree(lat)
        best_d2 = float("inf")
        best_m = 0.0
        best_pt = self.coords[0]
        for i in range(len(self.coords) - 1):
            (ax, ay), (bx, by) = self.coords[i], self.coords[i + 1]
            dx, dy = (bx - ax) * m_lon, (by - ay) * m_lat
            px, py = (lon - ax) * m_lon, (lat - ay) * m_lat
            seg2 = dx * dx + dy * dy
            t = 0.0 if seg2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / seg2))
            d2 = (px - t * dx) ** 2 + (py - t * dy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best_m = self.vertex_m[i] + t * (self.vertex_m[i + 1] - self.vertex_m[i])
                best_pt = (ax + (bx - ax) * t, ay + (by - ay) * t)
        return best_m, vincenty_m(lon, lat, best_pt[0], best_pt[1])
