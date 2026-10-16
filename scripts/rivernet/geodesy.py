"""Pure-Python WGS84 geodesic distance (Vincenty inverse).

Used for edge lengths so graph construction needs neither pyproj nor any
compiled dependency and stays bit-for-bit deterministic. Accurate to well under
1 mm for the distances in a river network; not for near-antipodal points.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

_A = 6378137.0
_F = 1 / 298.257223563
_B = _A * (1 - _F)


def vincenty_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Geodesic distance in metres between two WGS84 lon/lat points."""
    if lon1 == lon2 and lat1 == lat2:
        return 0.0
    u1 = math.atan((1 - _F) * math.tan(math.radians(lat1)))
    u2 = math.atan((1 - _F) * math.tan(math.radians(lat2)))
    big_l = math.radians(lon2 - lon1)
    lam = big_l
    sin_u1, cos_u1 = math.sin(u1), math.cos(u1)
    sin_u2, cos_u2 = math.sin(u2), math.cos(u2)
    for _ in range(200):
        sin_lam, cos_lam = math.sin(lam), math.cos(lam)
        sin_sigma = math.hypot(cos_u2 * sin_lam, cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lam)
        if sin_sigma == 0:
            return 0.0
        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cos_u1 * cos_u2 * sin_lam / sin_sigma
        cos2_alpha = 1 - sin_alpha**2
        cos_2sm = cos_sigma - 2 * sin_u1 * sin_u2 / cos2_alpha if cos2_alpha else 0.0
        c = _F / 16 * cos2_alpha * (4 + _F * (4 - 3 * cos2_alpha))
        prev = lam
        lam = big_l + (1 - c) * _F * sin_alpha * (
            sigma + c * sin_sigma * (cos_2sm + c * cos_sigma * (-1 + 2 * cos_2sm**2))
        )
        if abs(lam - prev) < 1e-12:
            break
    u_sq = cos2_alpha * (_A**2 - _B**2) / _B**2
    big_a = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    big_b = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    d_sigma = big_b * sin_sigma * (
        cos_2sm
        + big_b / 4 * (
            cos_sigma * (-1 + 2 * cos_2sm**2)
            - big_b / 6 * cos_2sm * (-3 + 4 * sin_sigma**2) * (-3 + 4 * cos_2sm**2)
        )
    )
    return _B * big_a * (sigma - d_sigma)


def line_length_m(coords: Sequence[Sequence[float]] | Iterable[Sequence[float]]) -> float:
    """Geodesic length in metres of a lon/lat polyline."""
    pts = list(coords)
    return sum(
        vincenty_m(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for i in range(len(pts) - 1)
    )
