"""Endpoint resolvers (plan T3.3): ``EndpointSpec`` -> candidate measures on a course.

``resolve_endpoint(spec, course, ctx, role=...)`` returns candidates sorted by
confidence (highest first). Confidences are the module constants below; tests
assert them. Pure Python (no shapely): spatial work uses ``Line.locate``,
``PolygonIndex`` and a small cell grid.

Deviations from the plan (documented in the PR):

* ``course`` is a course *record* dict (as in ``courses.jsonl.gz``);
* ROAD only sees bridge ways (the extract keeps no plain highway ways), so a
  ``DN``/``DJ`` endpoint resolves where that road crosses the water on a bridge;
* an extra ``role`` ("from"/"to") and ``judet`` argument; the assembler (T3.4)
  passes them.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping

from .courses import county_intervals
from .extract_schema import Extract
from .lr import Line
from .planar import PolygonIndex, metres_per_degree
from .textnorm import fold, river_keys

# ------------------------------------------------------------ fixed confidences
C_SOURCE = 0.9
C_SOURCE_BRAIDED = 0.75
C_MOUTH = 0.95
C_CONF_OUTLET_INTO = 0.95
C_CONF_JUNCTION = 0.95
C_CONF_NEAR_OUTLET = 0.8
C_LAKE_NAMED = 0.9
C_LAKE_UNNAMED = 0.7
C_DAM_NAMED = 0.9
C_DAM_BY_PLACE = 0.7
C_BRIDGE_REF_PLACE = 0.85
C_BRIDGE_ONE = 0.75
C_BRIDGE_ONLY = 0.5
C_ROAD = 0.7
C_LOC_UAT = 0.8
C_LOC_NEAR = 0.7  # projection <= 1 km
C_LOC_FAR = 0.55  # projection <= 3 km
C_COUNTY_SINGLE = 0.9
C_COUNTY_MULTI = 0.65
C_BORDER = 0.85
C_WATERFALL = 0.85
OTHER_COUNTY_PENALTY = 0.1

BRAID_SHARE = 0.10
NEAR_OUTLET_M = 50.0
LAKE_FUZZY = 0.85
PLACE_FUZZY = 0.9
LAKE_UNNAMED_PLACE_M = 10_000.0
DAM_COURSE_M = 100.0
DAM_PLACE_M = 1_000.0
BRIDGE_COURSE_M = 30.0
BRIDGE_PLACE_M = 3_000.0
PLACE_MAX_M = 3_000.0
PLACE_NEAR_M = 1_000.0
WATERFALL_M = 200.0

GENERIC = re.compile(
    r"^(?:(?:baraj(?:ul)?|lac(?:ul)?|acumulare(?:a)?|pod(?:ul)?|cascada|localitatea|comuna|satul|sat|"
    r"orasul|municipiul|loc|com|jud|judetul|de|din|la|cu)\s+)+"
)
PLACE_TAGS = {"city", "town", "village", "hamlet", "suburb", "locality", "isolated_dwelling"}


@dataclass
class Candidate:
    m: float
    confidence: float
    method: str
    anchor: dict[str, Any] = field(default_factory=dict)
    dist_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"m": round(self.m, 1), "confidence": self.confidence, "method": self.method,
                "anchor": self.anchor, "dist_m": None if self.dist_m is None else round(self.dist_m, 1)}


def core(name: str | None) -> str:
    """Folded name without leading generic words (baraj, lac, pod, comuna, ...)."""
    s = fold(name)
    prev = None
    while prev != s:
        prev = s
        s = GENERIC.sub("", s).strip()
    return s


def name_sim(a: str | None, b: str | None) -> float:
    ca, cb = core(a), core(b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    return SequenceMatcher(None, ca, cb).ratio()


def norm_ref(ref: str | None) -> str:
    return re.sub(r"[\s\-]+", "", (ref or "").upper())


def ref_match(want: str, have: str) -> bool:
    """DN67 matches DN67 and DN67D (one trailing letter) but not DN6 / DN670."""
    if not want or not have:
        return False
    if want == have:
        return True
    a, b = (want, have) if len(want) < len(have) else (have, want)
    return b.startswith(a) and len(b) == len(a) + 1 and b[-1].isalpha()


# ------------------------------------------------------------------ spatial grid


class Grid:
    CELL = 0.05

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], list[Any]] = {}

    def add(self, item: Any, lon: float, lat: float) -> None:
        self.cells.setdefault((math.floor(lon / self.CELL), math.floor(lat / self.CELL)), []).append(item)

    def near(self, lon: float, lat: float, radius_m: float) -> Iterable[Any]:
        m_lon, m_lat = metres_per_degree(lat)
        rx = int(radius_m / (self.CELL * m_lon)) + 1
        ry = int(radius_m / (self.CELL * m_lat)) + 1
        cx, cy = math.floor(lon / self.CELL), math.floor(lat / self.CELL)
        for i in range(cx - rx, cx + rx + 1):
            for j in range(cy - ry, cy + ry + 1):
                yield from self.cells.get((i, j), ())


def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    m_lon, m_lat = metres_per_degree((a[1] + b[1]) / 2)
    return math.hypot((a[0] - b[0]) * m_lon, (a[1] - b[1]) * m_lat)


# ---------------------------------------------------------------------- context


@dataclass
class Place:
    id: int
    name: str
    coord: tuple[float, float]


@dataclass
class Feature:  # dam / weir / waterfall
    id: Any
    kind: str
    name: str | None
    coords: list[tuple[float, float]]


@dataclass
class Bridge:
    id: int
    tags: Mapping[str, str]
    coords: list[tuple[float, float]]

    @property
    def refs(self) -> set[str]:
        return {norm_ref(r) for r in re.split(r"[;,]", self.tags.get("ref", "")) if r.strip()}

    @property
    def names(self) -> list[str]:
        return [self.tags[k] for k in ("name", "bridge:name") if self.tags.get(k)]


@dataclass
class Area:
    id: str
    tags: Mapping[str, str]
    poly: PolygonIndex

    @property
    def name(self) -> str | None:
        return self.tags.get("name")


@dataclass
class Context:
    courses: dict[str, Mapping[str, Any]]
    places: Grid = field(default_factory=Grid)
    place_names: dict[str, list[Place]] = field(default_factory=dict)
    features: Grid = field(default_factory=Grid)
    bridges: Grid = field(default_factory=Grid)
    water_areas: list[Area] = field(default_factory=list)
    uat_areas: list[Area] = field(default_factory=list)
    county_polys: dict[str, PolygonIndex] = field(default_factory=dict)
    country_poly: PolygonIndex | None = None
    node_coords: dict[int, tuple[float, float]] = field(default_factory=dict)
    way_coords: dict[int, list[tuple[float, float]]] = field(default_factory=dict)
    area_by_id: dict[str, "Area"] = field(default_factory=dict)
    names: dict[str, list[str]] = field(default_factory=dict)  # course_id -> keys (all courses)
    _lines: dict[str, Line] = field(default_factory=dict)
    _by_key: dict[str, list[str]] = field(default_factory=dict)

    def line(self, course: Mapping[str, Any]) -> Line:
        cid = course["course_id"]
        if cid not in self._lines:
            coords = [tuple(c) for c in course["geometry"]["coordinates"]]
            self._lines[cid] = Line.from_coords(coords)  # recomputes vertex_m (same metric as the build)
        return self._lines[cid]

    def courses_named(self, keys: Iterable[str]) -> list[Mapping[str, Any]]:
        if not self._by_key:
            for cid, c in self.courses.items():
                self._by_key.setdefault(c.get("name_key") or "", []).append(cid)
                for a in c.get("aliases") or []:
                    for k in river_keys(a):
                        self._by_key.setdefault(k, []).append(cid)
        out, seen = [], set()
        for k in keys:
            for cid in self._by_key.get(k, ()):
                if cid not in seen:
                    seen.add(cid)
                    out.append(self.courses[cid])
        return out

    def county_of(self, lon: float, lat: float) -> str | None:
        for name, poly in self.county_polys.items():
            if poly.contains(lon, lat):
                return name
        return None


def _county_key(name: str | None) -> str:
    s = fold(name)
    for p in ("judetul ", "jud ", "county "):
        if s.startswith(p):
            s = s[len(p):]
    return s


def build_context(
    extract: Extract,
    courses: Iterable[Mapping[str, Any]],
    counties_geojson: Mapping[str, Any] | None = None,
) -> Context:
    ctx = Context(courses={c["course_id"]: c for c in courses})
    for n in extract.nodes.values():
        t = n.tags
        if t.get("place") in PLACE_TAGS and t.get("name"):
            ctx.node_coords[n.id] = n.coord
            p = Place(n.id, t["name"], n.coord)
            ctx.places.add(p, *n.coord)
            ctx.place_names.setdefault(core(t["name"]), []).append(p)
        wt = t.get("waterway")
        if wt in ("dam", "weir", "waterfall"):
            ctx.node_coords[n.id] = n.coord
            ctx.features.add(Feature(n.id, wt, t.get("name"), [n.coord]), *n.coord)
    for w in extract.ways.values():
        t = w.tags
        wt = t.get("waterway")
        if wt in ("dam", "weir", "waterfall") or (t.get("bridge") and (t.get("highway") or t.get("railway"))):
            ctx.way_coords[w.id] = list(w.coords)
        if wt in ("dam", "weir", "waterfall"):
            mid = w.coords[len(w.coords) // 2]
            ctx.features.add(Feature(w.id, wt, t.get("name"), list(w.coords)), *mid)
        if t.get("bridge") and (t.get("highway") or t.get("railway")):
            mid = w.coords[len(w.coords) // 2]
            ctx.bridges.add(Bridge(w.id, t, list(w.coords)), *mid)
    for a in extract.areas.values():
        t = a.tags
        if t.get("boundary") == "administrative":
            lvl = t.get("admin_level")
            poly = PolygonIndex(dict(a.geometry))
            if lvl == "2" and ctx.country_poly is None:
                ctx.country_poly = poly
            elif lvl == "4":
                ctx.county_polys[_county_key(t.get("name"))] = poly
            elif lvl == "8":
                ctx.uat_areas.append(Area(a.id, t, poly))
                ctx.area_by_id[a.id] = ctx.uat_areas[-1]
        elif t.get("natural") == "water" or t.get("landuse") == "reservoir":
            ctx.water_areas.append(Area(a.id, t, PolygonIndex(dict(a.geometry))))
            ctx.area_by_id[a.id] = ctx.water_areas[-1]
    if counties_geojson and not ctx.county_polys:
        for f in counties_geojson.get("features", []):
            ctx.county_polys[_county_key(f["properties"].get("name"))] = PolygonIndex(f["geometry"])
    return ctx


# ------------------------------------------------------------- shared helpers


def _tag(c: Candidate, spec: Mapping[str, Any]) -> Candidate:
    q = spec.get("qualifier") or "at"
    if q != "at":
        c.method += f"|{q}"
    return c


def _intervals(ctx: Context, course: Mapping[str, Any], poly: PolygonIndex) -> list[tuple[float, float]]:
    return county_intervals(ctx.line(course), poly)


def _find_places(ctx: Context, name: str, cutoff: float = PLACE_FUZZY) -> list[Place]:
    c = core(name)
    if not c:
        return []
    if c in ctx.place_names:
        return list(ctx.place_names[c])
    out: list[Place] = []
    for k, ps in ctx.place_names.items():
        if abs(len(k) - len(c)) > 3 or k[:1] != c[:1]:
            continue
        if SequenceMatcher(None, c, k).ratio() >= cutoff:
            out.extend(ps)
    return out


def _course_keys_of(ctx: Context, cid: str | None) -> set[str]:
    if not cid:
        return set()
    c = ctx.courses.get(cid)
    if c is not None:
        keys = {c.get("name_key") or ""}
        for a in c.get("aliases") or []:
            keys.update(river_keys(a))
        return keys - {""}
    if cid in ctx.names:
        return set(ctx.names[cid])
    parts = cid.split(":")
    return {parts[1]} if len(parts) >= 3 and parts[0] == "name" else set()


# ------------------------------------------------------------------- resolvers


def _source(spec, course, ctx, **_):
    braided = course.get("braids_dropped_m", 0.0) > BRAID_SHARE * course["length_m"]
    return [Candidate(0.0, C_SOURCE_BRAIDED if braided else C_SOURCE, "source" + ("_braided" if braided else ""))]


def _mouth(spec, course, ctx, **_):
    return [Candidate(course["length_m"], C_MOUTH, "mouth")]


def _confluence(spec, course, ctx, **_):
    target = spec.get("target")
    keys = set(river_keys(target))
    if not keys:
        return []
    out: list[Candidate] = []
    if _course_keys_of(ctx, course.get("receives_into")) & keys:
        out.append(Candidate(course["length_m"], C_CONF_OUTLET_INTO, "outlet_into_named",
                             {"type": "course", "id": course["receives_into"]}))
    for j in course.get("junctions") or []:
        if _course_keys_of(ctx, j.get("tributary_course_id")) & keys:
            out.append(Candidate(j["m"], C_CONF_JUNCTION, "tributary_junction",
                                 {"type": "node", "id": j.get("node"), "name": target}))
    if not out:
        line = ctx.line(course)
        for other in ctx.courses_named(keys):
            if other["course_id"] == course["course_id"]:
                continue
            ox, oy = other["geometry"]["coordinates"][-1]
            m, d = line.locate(ox, oy)
            if d <= NEAR_OUTLET_M:
                out.append(Candidate(m, C_CONF_NEAR_OUTLET, "near_outlet",
                                     {"type": "course", "id": other["course_id"]}, d))
    return out


def _lake(spec, course, ctx, kind, **_):
    target = spec.get("target") or ""
    pick = min if kind == "LAKE_UPSTREAM" else max
    out: list[Candidate] = []
    line_bbox = _bbox(course)
    named = []
    for a in ctx.water_areas:
        if a.name and name_sim(a.name, target) >= LAKE_FUZZY and _bbox_hit(a.poly.bbox, line_bbox):
            iv = _intervals(ctx, course, a.poly)
            if iv:
                named.append((a, iv))
    for a, iv in named:
        m = pick(i[0] for i in iv) if kind == "LAKE_UPSTREAM" else pick(i[1] for i in iv)
        out.append(Candidate(m, C_LAKE_NAMED, "lake_named", {"type": "area", "id": a.id, "name": a.name}))
    if out:
        return out
    places = _find_places(ctx, target, 0.9)
    if not places:
        return out
    crossed = []
    for a in ctx.water_areas:
        if a.name or not _bbox_hit(a.poly.bbox, line_bbox):
            continue
        iv = _intervals(ctx, course, a.poly)
        if iv:
            crossed.append((a, iv))
    near = []
    line = ctx.line(course)
    for a, iv in crossed:
        mid = line.point_at((iv[0][0] + iv[-1][1]) / 2)
        if any(dist_m(mid, p.coord) <= LAKE_UNNAMED_PLACE_M for p in places):
            near.append((a, iv))
    if len(near) == 1:
        a, iv = near[0]
        m = iv[0][0] if kind == "LAKE_UPSTREAM" else iv[-1][1]
        out.append(Candidate(m, C_LAKE_UNNAMED, "lake_unnamed_near_place", {"type": "area", "id": a.id}))
    return out


def _bbox(course):
    xs = [c[0] for c in course["geometry"]["coordinates"]]
    ys = [c[1] for c in course["geometry"]["coordinates"]]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_hit(a, b) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _features_near_course(ctx, course, kinds, name, cutoff=0.85):
    line = ctx.line(course)
    out = []
    seen = set()
    cells = ctx.features.cells.values()
    for cell in cells:
        for f in cell:
            if id(f) in seen or f.kind not in kinds:
                continue
            seen.add(id(f))
            out.append(f)
    return line, out


def _dam(spec, course, ctx, **_):
    target = spec.get("target") or ""
    line, feats = _features_near_course(ctx, course, ("dam", "weir"), target)
    out: list[Candidate] = []
    best_named: list[tuple[float, float, Feature]] = []
    for f in feats:
        if f.name and name_sim(f.name, target) >= LAKE_FUZZY:
            m, d = min((line.locate(*c) for c in f.coords), key=lambda t: t[1])
            if d <= DAM_COURSE_M:
                best_named.append((m, d, f))
    for m, d, f in best_named:
        out.append(Candidate(m, C_DAM_NAMED, "dam_named", {"type": "node" if len(f.coords) == 1 else "way", "id": f.id, "name": f.name}, d))
    if out:
        return out
    for p in _find_places(ctx, target):
        for f in ctx.features.near(*p.coord, DAM_PLACE_M):
            if f.kind not in ("dam", "weir") or min(dist_m(c, p.coord) for c in f.coords) > DAM_PLACE_M:
                continue
            m, d = min((line.locate(*c) for c in f.coords), key=lambda t: t[1])
            if d <= DAM_COURSE_M:
                out.append(Candidate(m, C_DAM_BY_PLACE, "dam_by_place", {"type": "way", "id": f.id, "place": p.name}, d))
    return out


def _waterfall(spec, course, ctx, **_):
    target = spec.get("target") or ""
    line, feats = _features_near_course(ctx, course, ("waterfall",), target)
    out = []
    for f in feats:
        if f.name and name_sim(f.name, target) >= LAKE_FUZZY:
            m, d = min((line.locate(*c) for c in f.coords), key=lambda t: t[1])
            if d <= WATERFALL_M:
                out.append(Candidate(m, C_WATERFALL, "waterfall_named", {"type": "node", "id": f.id, "name": f.name}, d))
    return out


def _densify(coords, step_m=10.0):
    out = [coords[0]]
    for a, b in zip(coords, coords[1:]):
        n = max(1, int(dist_m(a, b) / step_m))
        out.extend((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1))
    return out


def _bridge_crossings(ctx, course, bridges):
    """Bridges whose way passes within BRIDGE_COURSE_M of the course (sampled every 10 m)."""
    line = ctx.line(course)
    for b in bridges:
        m, d = min((line.locate(*c) for c in _densify(b.coords)), key=lambda t: t[1])
        if d <= BRIDGE_COURSE_M:
            yield b, m, d


def _bridge(spec, course, ctx, window=None, **_):
    ref = norm_ref(spec.get("road_ref"))
    raw_ref = (spec.get("road_ref") or "").upper()
    railway = "CFR" in raw_ref or raw_ref.strip() == "CF"
    if railway and ref in ("CFR", "CF"):
        ref = ""  # a bare railway marker is not a road number
    target = spec.get("target")
    hint = spec.get("locality_hint")
    anchors: list[Place] = []
    for nm in (hint, target):
        if nm and not anchors:
            anchors = _find_places(ctx, nm)
    cand_bridges: dict[int, Bridge] = {}
    if anchors:
        for p in anchors:
            for b in ctx.bridges.near(*p.coord, BRIDGE_PLACE_M):
                cand_bridges[b.id] = b
    elif ref or railway:
        for cell in ctx.bridges.cells.values():
            for b in cell:
                cand_bridges[b.id] = b
    elif window is not None:
        for cell in ctx.bridges.cells.values():
            for b in cell:
                cand_bridges[b.id] = b
    else:
        return []
    out: list[Candidate] = []
    pool = list(cand_bridges.values())
    if ref:
        pool = [b for b in pool if any(ref_match(ref, r) for r in b.refs)]
    if railway:
        pool = [b for b in pool if b.tags.get("railway")]
    crossings = list(_bridge_crossings(ctx, course, pool))
    if window is not None:
        lo, hi = window
        crossings = [x for x in crossings if lo <= x[1] <= hi]
    for b, m, d in crossings:
        pdist = min((min(dist_m(c, p.coord) for c in b.coords) for p in anchors), default=None)
        if anchors and pdist is not None and pdist > BRIDGE_PLACE_M:
            continue
        name_hit = bool(target) and any(name_sim(n, target) >= LAKE_FUZZY for n in b.names)
        has_ref = bool(ref) or railway
        has_place = bool(anchors)
        if has_ref and has_place:
            conf = C_BRIDGE_REF_PLACE
        elif has_ref or has_place or name_hit:
            conf = C_BRIDGE_ONE
        else:
            conf = C_BRIDGE_ONLY
        if name_hit and has_place and conf < C_BRIDGE_REF_PLACE:
            conf = C_BRIDGE_REF_PLACE if has_ref else C_BRIDGE_ONE
        out.append(Candidate(m, conf, "bridge", {"type": "way", "id": b.id, "name": (b.names or [None])[0]},
                             pdist if pdist is not None else d))
    out.sort(key=lambda c: (-c.confidence, c.dist_m if c.dist_m is not None else 1e12, c.m))
    return out


def _road(spec, course, ctx, **kw):
    if not spec.get("road_ref"):
        return []
    res = _bridge(spec, course, ctx, **kw)
    for c in res:
        c.confidence = C_ROAD if c.confidence >= C_ROAD else c.confidence
        c.method = "road_bridge"
    return res


def _locality(spec, course, ctx, role=None, judet=None, **_):
    target = spec.get("target") or ""
    c_t = core(target)
    if not c_t:
        return []
    line = ctx.line(course)
    q = spec.get("qualifier") or "at"
    side = role if role in ("from", "to") else "from"
    if q == "upstream":
        side = "from"
    elif q == "downstream":
        side = "to"
    out: list[Candidate] = []
    lb = _bbox(course)
    for a in ctx.uat_areas:
        if a.name and core(a.name) == c_t and _bbox_hit(a.poly.bbox, lb):
            iv = _intervals(ctx, course, a.poly)
            if iv:
                m = iv[0][0] if side == "from" else iv[-1][1]
                out.append(Candidate(m, C_LOC_UAT, "uat_intersection", {"type": "area", "id": a.id, "name": a.name}))
    if out:
        return out
    want = _county_key(judet) if judet else None
    for p in _find_places(ctx, target):
        m, d = line.locate(*p.coord)
        if d > PLACE_MAX_M:
            continue
        conf = C_LOC_NEAR if d <= PLACE_NEAR_M else C_LOC_FAR
        if want and ctx.county_polys:
            pc = ctx.county_of(*p.coord)
            if pc is not None and pc != want:
                if d > PLACE_NEAR_M:
                    continue
                conf = round(conf - OTHER_COUNTY_PENALTY, 2)
        out.append(Candidate(m, conf, "place_projection", {"type": "node", "id": p.id, "name": p.name}, d))
    out.sort(key=lambda c: (-c.confidence, c.dist_m or 0.0))
    return out


def _county_limit(spec, course, ctx, judet=None, role=None, **_):
    name = spec.get("target") or judet
    if not name:
        return []
    poly = ctx.county_polys.get(_county_key(name))
    if poly is None:
        return []
    return _crossings(ctx, course, poly, "county_limit", C_COUNTY_SINGLE, C_COUNTY_MULTI, name)


def _crossings(ctx, course, poly, method, c_single, c_multi, name):
    iv = _intervals(ctx, course, poly)
    length = course["length_m"]
    pts = []
    for a, b in iv:
        if a > 1.0:
            pts.append(a)
        if b < length - 1.0:
            pts.append(b)
    conf = c_single if len(pts) == 1 else c_multi
    return [Candidate(m, conf, method, {"type": "area", "name": name}) for m in pts]


def _border(spec, course, ctx, **_):
    if ctx.country_poly is None:
        return []
    return _crossings(ctx, course, ctx.country_poly, "border", C_BORDER, C_BORDER, spec.get("target"))


_DISPATCH = {
    "SOURCE": _source,
    "MOUTH": _mouth,
    "CONFLUENCE": _confluence,
    "DAM": _dam,
    "BRIDGE": _bridge,
    "ROAD": _road,
    "LOCALITY": _locality,
    "COUNTY_LIMIT": _county_limit,
    "BORDER": _border,
    "WATERFALL": _waterfall,
}


def resolve_endpoint(
    spec: Mapping[str, Any],
    course: Mapping[str, Any],
    ctx: Context,
    role: str | None = None,
    judet: str | None = None,
    window: tuple[float, float] | None = None,
) -> list[Candidate]:
    """Candidates for one endpoint, highest confidence first. ``spec`` is an
    ``EndpointSpec.to_dict()``; UNKNOWN (or an unsupported kind) gives ``[]``."""
    kind = spec.get("kind")
    if kind in ("LAKE_UPSTREAM", "LAKE_DOWNSTREAM"):
        cands = _lake(spec, course, ctx, kind=kind)
    else:
        fn = _DISPATCH.get(kind or "")
        cands = fn(spec, course, ctx, role=role, judet=judet, window=window) if fn else []
    for c in cands:
        _tag(c, spec)
    cands.sort(key=lambda c: (-c.confidence, c.m))
    return cands
