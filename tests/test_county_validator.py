"""County-consistency invariants over the committed data snapshot.

Promotes the reusable assertions from the ad-hoc probe
scripts/_verify_county_clip.py + scripts/validate_geometry_county.py (§8 of
the QA test plan): schema + county-consistency smoke over public/data/*.json.
Pure functions are unit-tested here; the snapshot smoke runs over the
committed files (fast, no network).
"""
import json
import math
from pathlib import Path

import pytest

from validate_geometry_county import norm as vc_norm, water_points, centroid, seat_dist, COUNTY_SEATS

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"
UNCONTRACTED = ROOT / "public" / "data" / "uncontracted_rivers.json"


def _load(path):
    if not path.exists():
        pytest.skip(f"{path.name} not present in this checkout")
    return json.loads(path.read_text(encoding="utf-8"))


class TestValidateGeometryCountyPure:
    """Unit tests for the pure classifier helpers (no data files)."""

    def test_norm(self):
        assert vc_norm("Bistrița-Năsăud") == "bistrita nasaud"
        assert vc_norm("CĂLĂRAȘI") == "calarasi"

    def test_water_points_geometry(self):
        w = {"geometry": {"type": "MultiLineString", "coordinates": [[[23.0, 46.0], [23.5, 46.5]]]}}
        pts = water_points(w)
        assert pts == [[23.0, 46.0], [23.5, 46.5]]

    def test_water_points_fallback_bbox(self):
        w = {"bbox": [23.0, 46.0, 24.0, 47.0]}
        pts = water_points(w)
        # centroid + 4 corners
        assert [23.5, 46.5] in pts
        assert len(pts) == 5

    def test_water_points_empty(self):
        assert water_points({}) == []

    def test_centroid(self):
        assert centroid([(0, 0), (2, 4)]) == (1.0, 2.0)

    def test_seat_dist(self):
        d = seat_dist("Cluj", (23.62, 46.77))
        assert d == pytest.approx(0.0, abs=1e-9)
        assert seat_dist("Atlantis", (1, 1)) is None


class TestSnapshotInvariants:
    """Smoke over the committed snapshot — schema + county-consistency."""

    def test_waters_schema(self):
        waters = _load(WATERS)
        for w in waters:
            assert w["type"] == "ape"
            assert w["subtype"] in ("lac", "rau")
            assert isinstance(w["judet"], str) and w["judet"]
            # every geometry-carrying water has a plausible bbox or coordinates
            if w.get("geometry"):
                _ = w["geometry"]["type"] in ("LineString", "MultiLineString", "Polygon", "MultiPolygon")

    def test_uncontracted_schema(self):
        unc = _load(UNCONTRACTED)
        for w in unc:
            assert w.get("uncontracted") is True
            assert w.get("geometry"), "uncontracted entries must carry geometry"

    def test_geometry_within_declared_county_seat_range(self):
        """Every water with geometry sits within ~2.5° of its declared county
        seat (far away = same-name river in another county)."""
        waters = _load(WATERS)
        outliers = []
        for w in waters:
            g = w.get("geometry")
            if not g:
                continue
            declared = w.get("judet")
            if declared not in COUNTY_SEATS:
                continue
            pts = water_points(w, include_fallback=False)
            if not pts:
                continue
            cpt = centroid(pts)
            d = seat_dist(declared, cpt)
            if d is not None and d > 2.5:
                # multi-county group owners legitimately sit far from the seat
                group = w.get("riverGroup")
                members = [x for x in waters if x.get("riverGroup") == group and x.get("judet") != declared]
                if not members:
                    outliers.append((w["slug"], w["name"], declared, round(d, 2)))
        assert outliers == [], f"waters with geometry far from their county seat: {outliers[:10]}"

    def test_county_clip_keys_are_normalized(self):
        """geometryByCounty keys must equal countyClipKey(judet) so the FE
        lookup never misses (t_117f0b99)."""
        waters = _load(WATERS)
        bad = []
        for w in waters:
            by_county = w.get("geometryByCounty")
            if not by_county:
                continue
            key = vc_norm(w.get("judet") or "").replace(" ", "")
            if key not in by_county:
                bad.append((w["slug"], key, list(by_county.keys())[:3]))
        assert bad == [], f"geometryByCounty missing the water's own county key: {bad[:10]}"

    def test_county_clips_are_nonempty(self):
        waters = _load(WATERS)
        empty = []
        for w in waters:
            by_county = w.get("geometryByCounty") or {}
            for key, clip in by_county.items():
                if clip is not None:
                    coords = clip.get("coordinates") if isinstance(clip, dict) else None
                    if not coords:
                        empty.append((w["slug"], key))
        assert empty == [], f"empty clip geometries: {empty[:10]}"