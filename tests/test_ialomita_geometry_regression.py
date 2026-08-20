import hashlib
import json
from pathlib import Path

from river_segment_audit_lib import max_geometry_edge_m


ROOT = Path(__file__).parents[1]
SLUG = "3ek8e82l"
EXPECTED_SHA = "6023865f5a9de2b9c14980b292f4987803771cf3be965fb08ea24efdddc4cf08"
BAD_SHA = "0fd8e49df786a43316dc2e323eef15b35981880c5fd6f279c05ab311e1d86b45"


def water():
    return next(w for w in json.loads((ROOT / "public/data/waters.json").read_text()) if w["slug"] == SLUG)


def geometry_sha(geometry):
    return hashlib.sha256(json.dumps(geometry, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_ialomita_restores_hash_verified_multipart_geometry_and_topology():
    w = water()
    assert geometry_sha(w["geometry"]) == EXPECTED_SHA
    assert EXPECTED_SHA != BAD_SHA
    assert w["geometry"]["type"] == "MultiLineString"
    assert max_geometry_edge_m(w["geometry"]) < 20_000


def test_ialomita_dambovita_clip_is_derived_and_present():
    clips = json.loads((ROOT / "public/data/waters_county_clips.json").read_text())
    clip = clips[SLUG]["dambovita"]
    assert clip["type"] == "MultiLineString"
    assert len(clip["coordinates"]) > 1