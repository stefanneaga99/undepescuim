"""Turn a selection from the committed v1 river-segment index into a
normalised extract fixture (schema v1). Offline, standard library only.

The v1 index (``data/cache/osm_river_segments_v1.jsonl.gz``) holds OSM ways with
``node_ids`` + ``coordinates`` and name-matched relations whose members are only
``outer``/``inner`` (water-area multipolygons, not ``type=waterway``), so
fixtures contain ways only, tagged ``waterway=river``.

Usage::

    PYTHONPATH=scripts python -m rivernet.fixtures_from_v1 --out-dir tests/fixtures/rivernet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from .extract import make_meta, write_extract
from .extract_schema import open_text
from .textnorm import river_key

INDEX = Path("data/cache/osm_river_segments_v1.jsonl.gz")

BBox = tuple[float, float, float, float]  # west, south, east, north

# fixture name -> (river key, optional bbox). A way is kept when it has the key
# and at least one vertex inside the bbox.
SELECTIONS: dict[str, tuple[str, BBox | None]] = {
    "ialomita": ("ialomita", None),
    "barcau": ("barcau", None),
    "bistrita": ("bistrita", (24.9, 46.4, 27.1, 47.6)),  # Moldavian Bistrita
    "olt_reach": ("olt", (24.0, 45.0, 24.5, 46.2)),
}


def load_ways(index: Path = INDEX) -> list[dict[str, Any]]:
    out = []
    with open_text(index) as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("kind") == "way" and rec.get("node_ids") and rec.get("coordinates"):
                out.append(rec)
    return out


def _in_bbox(coords: Iterable[Iterable[float]], bbox: BBox) -> bool:
    w, s, e, n = bbox
    return any(w <= c[0] <= e and s <= c[1] <= n for c in coords)


def select_ways(ways: list[dict[str, Any]], key: str, bbox: BBox | None) -> list[dict[str, Any]]:
    sel = [
        w
        for w in ways
        if river_key(w.get("name")) == key
        and len(w["node_ids"]) == len(w["coordinates"])
        and (bbox is None or _in_bbox(w["coordinates"], bbox))
    ]
    return sorted(sel, key=lambda w: w["osm_id"])


def way_records(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "t": "way",
            "id": w["osm_id"],
            "nodes": list(w["node_ids"]),
            "coords": [[round(c[0], 7), round(c[1], 7)] for c in w["coordinates"]],
            "tags": {"name": w["name"], "waterway": "river"},
        }
        for w in selected
    ]


def build_fixture(ways: list[dict[str, Any]], name: str, out_dir: Path) -> Path:
    key, bbox = SELECTIONS[name]
    selected = select_ways(ways, key, bbox)
    if not selected:
        raise SystemExit(f"fixture {name}: no ways selected")
    path = out_dir / f"{name}.jsonl.gz"
    write_extract(
        path,
        make_meta(source="v1-index", filters=f"name_key={key} bbox={bbox}"),
        way_records(selected),
    )
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--index", default=str(INDEX))
    p.add_argument("--out-dir", default="tests/fixtures/rivernet")
    p.add_argument("names", nargs="*", default=sorted(SELECTIONS))
    ns = p.parse_args(argv)
    ways = load_ways(Path(ns.index))
    out_dir = Path(ns.out_dir)
    for name in ns.names:
        path = build_fixture(ways, name, out_dir)
        print(f"{path} {path.stat().st_size / 1024:.0f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
