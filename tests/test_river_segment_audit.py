import gzip
import json
from pathlib import Path

from build_osm_river_segment_index import build
from river_segment_audit_lib import connected_components, coverage, line_length_m, main_stem, topology


def test_index_is_sorted_and_marks_truncated_relation(tmp_path):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"elements": [
        {"type": "node", "id": 2, "lon": 1, "lat": 0},
        {"type": "node", "id": 1, "lon": 0, "lat": 0},
        {"type": "way", "id": 20, "nodes": [1, 2], "tags": {"name": "Test"}},
        {"type": "relation", "id": 3, "members": [{"type": "way", "ref": 20}, {"type": "way", "ref": 99}], "tags": {"name": "Test"}},
    ]}), encoding="utf-8")
    out, manifest = tmp_path / "index.jsonl.gz", tmp_path / "manifest.json"
    result = build(snapshot, out, manifest)
    with gzip.open(out, "rt", encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh]
    assert [r["osm_id"] for r in records] == [20, 3]
    assert records[1]["missing_way_ids"] == [99]
    assert result["counts"] == {"nodes": 2, "ways": 1, "relations": 1}


def way(osm_id, coords):
    return {"osm_id": osm_id, "coordinates": coords}


def test_topology_components_branch_and_main_stem():
    ways = [way(2, [[1, 0], [2, 0]]), way(1, [[0, 0], [1, 0]]), way(3, [[1, 0], [1, 1]])]
    assert connected_components(ways) == [[1, 2, 3]]
    assert topology(ways)["branch_nodes"]
    stem = main_stem(ways)
    assert len(stem) == 2 and 2 in stem
    assert len(connected_components(ways + [way(9, [[5, 0], [6, 0]])])) == 2


def test_coverage_detects_gap_without_mutating_geometry():
    published = [[0, 0], [0.01, 0]]
    osm = [[0, 0], [0.005, 0.003], [0.01, 0]]
    result = coverage(published, osm, tolerance_m=1)
    assert result["published_to_osm"] < 1
    assert result["osm_to_published"] < 1
    assert published == [[0, 0], [0.01, 0]]
    assert line_length_m(published) > 1000
