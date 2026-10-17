"""build_county_clip_geoms: pre-cut sector clips (plan T4.2)."""
import importlib.util
from pathlib import Path

from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_county_clip_geoms", ROOT / "scripts/build_county_clip_geoms.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)

# county "alba" covers lon < 24.5; the line runs 24.0 -> 25.0 with fine wiggles
POLYS = {"alba": box(23.0, 45.0, 24.5, 47.0), "sibiu": box(24.5, 45.0, 26.0, 47.0)}
BUFFERED = {k: v.buffer(bc.BUFFER_DEG) for k, v in POLYS.items()}
LINE = [[24.0 + i * 0.001, 46.0 + (0.0003 if i % 2 else 0.0)] for i in range(1001)]


def water(**kw):
    w = {"slug": "w", "judet": "Alba", "subtype": "rau", "geometry": {"type": "LineString", "coordinates": LINE}}
    w.update(kw)
    return w


def test_precut_sector_is_clipped_not_resliced_and_keeps_detail():
    w = water(geometryKind="sector", sectorStart=0.6, sectorEnd=0.9)  # compat fields relative to the course
    key, gj = bc.build_clip_for_water(w, w["geometry"], POLYS, BUFFERED, skip_if_inside=True)
    assert key == "alba"
    xs = [c[0] for c in gj["coordinates"]] if gj["type"] == "LineString" else [c[0] for p in gj["coordinates"] for c in p]
    # the Alba part of the line itself (24.0 .. 24.502), not 60-90 % of it
    assert min(xs) == 24.0 and 24.49 < max(xs) < 24.51
    # 0.0001 deg tolerance keeps the 0.0003 deg wiggles that 0.002 would flatten
    assert len(xs) > 400


def test_legacy_sector_interval_still_slices_with_coarse_tolerance():
    w = water(sectorStart=0.0, sectorEnd=0.3)
    key, gj = bc.build_clip_for_water(w, w["geometry"], POLYS, BUFFERED, skip_if_inside=False)
    xs = [c[0] for c in gj["coordinates"]] if gj["type"] == "LineString" else [c[0] for p in gj["coordinates"] for c in p]
    assert max(xs) <= 24.31 and len(xs) < 10


def test_precut_sector_fully_inside_its_county_needs_no_clip():
    inside = [[24.0 + i * 0.001, 46.0] for i in range(100)]
    w = water(geometryKind="sector", geometry={"type": "LineString", "coordinates": inside})
    assert bc.build_clip_for_water(w, w["geometry"], POLYS, BUFFERED, skip_if_inside=True) is None
