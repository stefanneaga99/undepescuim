// @vitest-environment node
import { describe, it, expect } from 'vitest';
import {
  haversineKm,
  distanceToWaterKm,
  waterToGeoJSON,
  nearestWaters,
  geometryParts,
  nearestWaterPoint,
  countyOfPoint,
  nearbyCounty,
  watersToFeatureCollection,
} from '@/utils/geo';
import type { CountyFeature, Water } from '@/types/data';

function water(over: Partial<Water> = {}): Water {
  return {
    slug: 'w1',
    name: 'Râul Test',
    judet: 'Cluj',
    type: 'ape',
    subtype: 'rau',
    coordinates: [23.6, 46.77],
    bbox: [23.0, 46.0, 24.0, 47.0],
    asociatie: null,
    ...over,
  } as Water;
}

describe('haversineKm', () => {
  it('returns 0 for identical points', () => {
    expect(haversineKm(46.0, 23.0, 46.0, 23.0)).toBe(0);
  });

  it('approximates 1 degree of latitude as ~111.2 km', () => {
    expect(haversineKm(46.0, 23.0, 47.0, 23.0)).toBeCloseTo(111.19, 1);
  });

  it('is symmetric', () => {
    const a = haversineKm(45.0, 25.0, 46.5, 26.5);
    const b = haversineKm(46.5, 26.5, 45.0, 25.0);
    expect(a).toBeCloseTo(b, 9);
  });

  it('matches a known Bucharest–Cluj-Napoca distance (~325 km)', () => {
    // Bucharest 44.43, 26.10 — Cluj-Napoca 46.77, 23.60
    expect(haversineKm(44.43, 26.1, 46.77, 23.6)).toBeGreaterThan(300);
    expect(haversineKm(44.43, 26.1, 46.77, 23.6)).toBeLessThan(350);
  });
});

describe('distanceToWaterKm', () => {
  it('is 0 when the user is inside the bbox', () => {
    const w = water({ bbox: [23.0, 46.0, 24.0, 47.0] });
    expect(distanceToWaterKm(46.5, 23.5, w)).toBe(0);
  });

  it('measures to the bbox rectangle when one exists (111.32 km/deg lat)', () => {
    const w = water({ bbox: [23.0, 46.0, 24.0, 47.0] });
    // 1 degree north of the bbox top edge
    expect(distanceToWaterKm(48.0, 23.5, w)).toBeCloseTo(111.32, 1);
  });

  it('falls back to haversine to stored coordinates when no bbox', () => {
    const w = water({ bbox: undefined as never, coordinates: [23.6, 46.77] });
    const d = distanceToWaterKm(47.77, 23.6, w); // 1 degree north
    expect(d).toBeCloseTo(111.19, 1);
  });

  it('returns Infinity when neither bbox nor coordinates exist', () => {
    const w = water({ bbox: undefined as never, coordinates: undefined as never });
    expect(distanceToWaterKm(46.5, 23.5, w)).toBe(Infinity);
  });

  it('handles a NaN bbox as missing (falls back to coordinates)', () => {
    const w = water({ bbox: [Number.NaN, Number.NaN, Number.NaN, Number.NaN] as never, coordinates: [23.6, 46.77] });
    expect(Number.isFinite(distanceToWaterKm(46.77, 23.6, w))).toBe(true);
  });
});

describe('waterToGeoJSON', () => {
  it('uses real geometry when present', () => {
    const geom = { type: 'LineString' as const, coordinates: [[23.0, 46.0], [23.5, 46.5]] };
    const f = waterToGeoJSON(water({ geometry: geom }));
    expect(f.geometry).toEqual(geom);
    expect((f.properties as { _bboxFallback?: boolean })._bboxFallback).toBeUndefined();
    expect((f.properties as { _hidden?: boolean })._hidden).toBeUndefined();
  });

  it('renders a bbox-fallback POINT at the bbox center when no geometry', () => {
    const f = waterToGeoJSON(water({ bbox: [23.0, 46.0, 24.0, 47.0], coordinates: undefined as never }));
    expect(f.geometry.type).toBe('Point');
    expect((f.geometry as GeoJSON.Point).coordinates).toEqual([23.5, 46.5]);
    expect((f.properties as { _bboxFallback?: boolean })._bboxFallback).toBe(true);
  });

  it('prefers stored coordinates over the bbox center for the fallback point', () => {
    const f = waterToGeoJSON(water({ bbox: [23.0, 46.0, 24.0, 47.0], coordinates: [23.9, 46.9] }));
    expect((f.geometry as GeoJSON.Point).coordinates).toEqual([23.9, 46.9]);
  });

  it('marks a water with neither geometry nor bbox as hidden', () => {
    const f = waterToGeoJSON(water({ bbox: undefined as never, coordinates: [25, 45.8] }));
    expect((f.properties as { _hidden?: boolean })._hidden).toBe(true);
    expect(f.geometry.type).toBe('Point');
  });
});

describe('geometryParts', () => {
  it('returns a single part for LineString', () => {
    const parts = geometryParts({ type: 'LineString', coordinates: [[1, 2], [3, 4]] });
    expect(parts).toEqual([[[1, 2], [3, 4]]]);
  });

  it('returns parts for MultiLineString', () => {
    const parts = geometryParts({
      type: 'MultiLineString',
      coordinates: [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
    });
    expect(parts).toHaveLength(2);
  });

  it('flattens Polygon rings into one part list', () => {
    const parts = geometryParts({
      type: 'Polygon',
      coordinates: [[[1, 2], [3, 4], [1, 2]]],
    });
    expect(parts).toEqual([[1, 2], [3, 4], [1, 2]]);
  });

  it('returns [] for unknown geometry types', () => {
    expect(geometryParts({ type: 'MultiLineString', coordinates: [] })).toEqual([]);
  });
});

describe('nearestWaters', () => {
  const waters = [
    water({ slug: 'a', bbox: [23.0, 46.0, 23.5, 46.5] }),   // ~0 km from (23.4, 46.3)
    water({ slug: 'b', bbox: [23.6, 46.6, 24.0, 47.0] }),   // ~0.5 deg NE
    water({ slug: 'far', bbox: [26.0, 45.0, 27.0, 46.0] }), // ~200+ km away
    water({ slug: 'noloc', bbox: undefined as never, coordinates: undefined as never }), // Infinity
  ];

  it('returns finite distances sorted nearest-first, within maxKm', () => {
    const out = nearestWaters(46.3, 23.4, waters, { limit: 10, maxKm: 300 });
    expect(out.map((e) => e.slug)).toEqual(['a', 'b', 'far']);
    expect(out[0].km).toBe(0);
    expect(out.every((e) => Number.isFinite(e.km))).toBe(true);
  });

  it('skips unlocatable (Infinity) waters', () => {
    const slugs = nearestWaters(46.3, 23.4, waters, { limit: 10, maxKm: 300 }).map((e) => e.slug);
    expect(slugs).not.toContain('noloc');
  });

  it('respects limit and maxKm', () => {
    const one = nearestWaters(46.3, 23.4, waters, { limit: 1, maxKm: 300 });
    expect(one).toHaveLength(1);
    expect(one[0].slug).toBe('a');
    const none = nearestWaters(46.3, 23.4, waters, { limit: 10, maxKm: -1 });
    expect(none).toHaveLength(0);
  });
});

describe('nearestWaterPoint', () => {
  it('picks the nearest geometry vertex', () => {
    const w = water({
      geometry: { type: 'MultiLineString', coordinates: [[[23.0, 46.0], [23.5, 46.5], [24.0, 46.0]]] },
    });
    expect(nearestWaterPoint(46.6, 23.5, w)).toEqual([23.5, 46.5]);
  });

  it('falls back to the nearest bbox point', () => {
    const w = water({ bbox: [23.0, 46.0, 24.0, 47.0], coordinates: [99, 99] });
    // user at 23.5, 45.0 → clamp lat to 46.0, lon unchanged
    expect(nearestWaterPoint(45.0, 23.5, w)).toEqual([23.5, 46.0]);
  });

  it('falls back to stored coordinates when no geometry and no bbox', () => {
    const w = water({ bbox: undefined as never, coordinates: [23.6, 46.77] });
    expect(nearestWaterPoint(45.0, 22.0, w)).toEqual([23.6, 46.77]);
  });

  it('returns null when the water has none of the three', () => {
    const w = water({ bbox: undefined as never, coordinates: undefined as never });
    expect(nearestWaterPoint(45.0, 22.0, w)).toBeNull();
  });
});

describe('countyOfPoint / nearbyCounty', () => {
  const counties: CountyFeature[] = [
    {
      type: 'Feature',
      properties: { name: 'Cluj' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[23.0, 46.0], [24.0, 46.0], [24.0, 47.0], [23.0, 47.0], [23.0, 46.0]]],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Bihor' },
      geometry: {
        type: 'MultiPolygon',
        coordinates: [
          [[[21.0, 46.5], [22.0, 46.5], [22.0, 47.5], [21.0, 47.5], [21.0, 46.5]]],
        ],
      },
    },
  ];

  it('returns the county containing the point (Polygon)', () => {
    expect(countyOfPoint(46.5, 23.5, counties)).toBe('Cluj');
  });

  it('returns the county for a MultiPolygon feature', () => {
    expect(countyOfPoint(47.0, 21.5, counties)).toBe('Bihor');
  });

  it('returns null outside every county', () => {
    expect(countyOfPoint(45.0, 20.0, counties)).toBeNull();
  });

  it('nearbyCounty attributes via the nearest water point', () => {
    const w = water({
      geometry: { type: 'LineString', coordinates: [[23.4, 46.5], [23.6, 46.6]] },
    });
    expect(nearbyCounty(46.55, 23.5, w, counties)).toBe('Cluj');
  });

  it('nearbyCounty returns null for an unlocatable water', () => {
    const w = water({ bbox: undefined as never, coordinates: undefined as never });
    expect(nearbyCounty(46.5, 23.5, w, counties)).toBeNull();
  });
});

describe('watersToFeatureCollection', () => {
  it('drops hidden waters and keeps the rest', () => {
    const visible = water({ slug: 'v', geometry: { type: 'Point', coordinates: [1, 2] } as never });
    const hidden = water({ slug: 'h', bbox: undefined as never, coordinates: undefined as never });
    const fc = watersToFeatureCollection([visible, hidden]);
    expect(fc.type).toBe('FeatureCollection');
    expect(fc.features.map((f) => f.properties.slug)).toEqual(['v']);
  });
});
