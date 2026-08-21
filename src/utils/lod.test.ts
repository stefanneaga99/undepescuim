// @vitest-environment node
import { describe, expect, it } from 'vitest';
import type { LatLngBounds } from 'leaflet';
import { bboxInBounds, geometryBbox, lodThresholds, passesLod, renderBbox, viewSuffix } from '@/utils/lod';

function bounds(west: number, south: number, east: number, north: number): LatLngBounds {
  const make = (w: number, s: number, e: number, n: number): LatLngBounds => ({
    pad: (ratio: number) => {
      const dx = (e - w) * ratio;
      const dy = (n - s) * ratio;
      return make(w - dx, s - dy, e + dx, n + dy);
    },
    getWest: () => w,
    getSouth: () => s,
    getEast: () => e,
    getNorth: () => n,
  } as LatLngBounds);
  return make(west, south, east, north);
}

describe('lodThresholds', () => {
  it('uses the national, regional, and detail tiers at their exact boundaries', () => {
    expect(lodThresholds(7.99)).toEqual({ minLengthKm: 30, minAreaHa: 100 });
    expect(lodThresholds(8)).toEqual({ minLengthKm: 10, minAreaHa: 10 });
    expect(lodThresholds(9.99)).toEqual({ minLengthKm: 10, minAreaHa: 10 });
    expect(lodThresholds(10)).toEqual({ minLengthKm: 0, minAreaHa: 0 });
  });

  it('disables LOD for an active locality filter', () => {
    expect(lodThresholds(7, true)).toEqual({ minLengthKm: 0, minAreaHa: 0 });
  });
});

describe('passesLod', () => {
  const national = lodThresholds(7);

  it('gates rivers by length and polygons by area, including exact thresholds', () => {
    expect(passesLod({ lengthKm: 29.9 }, national)).toBe(false);
    expect(passesLod({ lengthKm: 30 }, national)).toBe(true);
    expect(passesLod({ areaHa: 99.9 }, national)).toBe(false);
    expect(passesLod({ areaHa: 100 }, national)).toBe(true);
  });

  it('keeps cheap fallback points without size metadata', () => {
    expect(passesLod({}, national)).toBe(true);
  });
});

describe('viewport helpers', () => {
  const viewport = bounds(24, 45, 26, 47);

  it('keeps intersecting and padded-edge bboxes while rejecting distant ones', () => {
    expect(bboxInBounds([24.5, 45.5, 25.5, 46.5], viewport)).toBe(true);
    expect(bboxInBounds([26.2, 45.5, 26.4, 46.5], viewport)).toBe(true);
    expect(bboxInBounds([27, 45.5, 28, 46.5], viewport)).toBe(false);
    expect(bboxInBounds(undefined, viewport)).toBe(true);
  });

  it('builds a stable, rounded layer-key suffix', () => {
    expect(viewSuffix(8, bounds(24.004, 45.005, 25.996, 47.004))).toBe(
      '8|24.00,45.01,26.00,47.00',
    );
  });

  it('derives render bounds from geometry instead of a stale stored bbox', () => {
    const geometry = {
      type: 'MultiLineString' as const,
      coordinates: [[[25.8, 46.04], [25.84, 46.02]]],
    };
    const water = { bbox: [25.18, 45.87, 25.54, 46.05] as [number, number, number, number], geometry };

    expect(geometryBbox(geometry)).toEqual([25.8, 46.02, 25.84, 46.04]);
    expect(renderBbox(water)).toEqual([25.8, 46.02, 25.84, 46.04]);
    expect(bboxInBounds(renderBbox(water), bounds(25.7, 45.9, 25.9, 46.1))).toBe(true);
    expect(bboxInBounds(water.bbox, bounds(25.7, 45.9, 25.9, 46.1))).toBe(false);
  });

  it('falls back to stored bounds for absent or malformed geometry', () => {
    const bbox = [25.18, 45.87, 25.54, 46.05] as [number, number, number, number];
    expect(renderBbox({ bbox })).toEqual(bbox);
    expect(renderBbox({ bbox, geometry: { type: 'LineString', coordinates: [[25.2, Number.NaN]] } })).toEqual(bbox);
    expect(renderBbox({ bbox, geometry: { type: 'MultiLineString', coordinates: [[[25.2, 46], [25.3]]] } })).toEqual(bbox);
    expect(geometryBbox({ type: 'Point', coordinates: [25.2, 46] })).toBeUndefined();
  });
});
