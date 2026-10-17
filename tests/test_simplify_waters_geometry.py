"""simplify_waters_geometry: pre-cut sector waters are left as published (plan T4.2)."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("simplify_waters_geometry", ROOT / "scripts/simplify_waters_geometry.py")
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)

# dense, nearly straight line: DP at 0.001 deg collapses it to its end points
DENSE = [[24.0 + i * 0.0001, 46.0 + (i % 2) * 0.00001] for i in range(200)]


def water(**kw):
    w = {"slug": "w", "subtype": "rau", "coordinates": [24.01, 46.0],
         "geometry": {"type": "LineString", "coordinates": copy.deepcopy(DENSE)}}
    w.update(kw)
    return w


def test_sector_water_geometry_and_length_are_untouched():
    sector = water(slug="s", geometryKind="sector", lengthKm=1.6,
                   geometryByCounty={"alba": {"type": "LineString", "coordinates": [[24.123456789, 46.0], [24.2, 46.0]]}})
    legacy = water(slug="l")
    before = copy.deepcopy(sector["geometry"])
    sw.process_pool([sector, legacy], simplify=True)
    assert sector["geometry"] == before and sector["lengthKm"] == 1.6
    assert sector["geometryByCounty"]["alba"]["coordinates"][0] == [24.12346, 46.0]  # clips still rounded
    assert len(legacy["geometry"]["coordinates"]) < 10 and "lengthKm" in legacy
    assert sw.stats["sector_skipped"] >= 1


def test_uncontracted_pool_ignores_geometry_kind():
    w = water(geometryKind="sector")
    sw.process_pool([w], simplify=False)
    assert w["geometry"]["coordinates"][0] == [24.0, 46.0]
