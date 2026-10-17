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


def test_ialomita_is_a_precut_sector_without_the_bad_chords():
    # River geometry v2: the hash-verified legacy MultiLineString (EXPECTED_SHA)
    # was replaced by the contract's own pre-cut sector (Fieni -> Dâmbovița exit).
    w = water()
    assert w["geometryKind"] == "sector" and w["source"] == "rivernet"
    assert geometry_sha(w["geometry"]) not in (BAD_SHA, EXPECTED_SHA)
    assert max_geometry_edge_m(w["geometry"]) < 1_000  # stricter than the legacy 20 km bound


def test_ialomita_dambovita_sector_needs_no_county_clip():
    # the sector lies inside Dâmbovița, so no per-county clip is stored for it
    clips = json.loads((ROOT / "public/data/waters_county_clips.json").read_text())
    assert SLUG not in clips