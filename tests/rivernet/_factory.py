"""Synthetic extract builders shared by the rivernet tests."""
from rivernet.extract_schema import Area, Extract, Member, Meta, Rel, Way


def make_extract(ways, rels=(), areas=()):
    """ways: [(way_id, [(node_id, lon, lat), ...], tags)];
    rels: [(rel_id, tags, [(way_id, role), ...])];
    areas: [(area_id, tags, geojson_geometry)]."""
    ex = Extract(meta=Meta(1, "test", None, None, None, None, None))
    for wid, pts, tags in ways:
        ex.ways[wid] = Way(
            id=wid,
            nodes=tuple(p[0] for p in pts),
            coords=tuple((p[1], p[2]) for p in pts),
            tags=tags,
        )
    for rid, tags, members in rels:
        ex.rels[rid] = Rel(id=rid, tags=tags, members=tuple(Member("w", w, role) for w, role in members))
    for aid, tags, geom in areas:
        ex.areas[aid] = Area(id=aid, tags=tags, geometry=geom)
    return ex


def box(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


REL = {"type": "waterway", "waterway": "river", "name": "Râul Test"}
RIVER = {"waterway": "river", "name": "Râul Test"}
