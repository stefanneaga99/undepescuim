// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { countyClipKey, countyRenderGeometry, CLASS4_RENDERING_REPAIR_SLUGS } from '@/utils/county-clip';
import type { Water } from '@/types/data';

function water(over: Partial<Water> = {}): Water {
  return {
    slug: 'w1',
    name: 'Râul Test',
    judet: 'Bistrița-Năsăud',
    type: 'ape',
    subtype: 'rau',
    coordinates: [24.5, 47.13],
    bbox: [24.0, 46.5, 25.0, 47.5],
    asociatie: null,
    ...over,
  } as Water;
}

const fullGeom = { type: 'LineString' as const, coordinates: [[24.0, 47.0], [24.5, 47.2]] };
const clipGeom = { type: 'LineString' as const, coordinates: [[24.2, 47.05], [24.3, 47.1]] };

describe('countyClipKey', () => {
  it('lowercases, strips diacritics and removes separators', () => {
    expect(countyClipKey('Bistrița-Năsăud')).toBe('bistritanasaud');
    expect(countyClipKey('Bistrița - Năsăud')).toBe('bistritanasaud');
    expect(countyClipKey('Bistrița Năsăud')).toBe('bistritanasaud');
  });

  it('handles simple counties and diacritics', () => {
    expect(countyClipKey('Cluj')).toBe('cluj');
    expect(countyClipKey('Călărași')).toBe('calarasi');
    expect(countyClipKey('București')).toBe('bucuresti');
  });
});

describe('countyRenderGeometry', () => {
  it('allowlists exactly the six audited Class 4 candidates', () => {
    expect([...CLASS4_RENDERING_REPAIR_SLUGS].sort()).toEqual([
      'anpa-anpa-0202',
      'anpa-anpa-0204',
      'romsilva-bacau-barzauta',
      'romsilva-covasna-sugo',
      'romsilva-maramures-crasna-frumusaua',
      'vb2p0152',
    ]);
  });

  it('matches the audited lazy-clip sentinels without changing the data artifact', () => {
    const clips = JSON.parse(readFileSync('public/data/waters_county_clips.json', 'utf8')) as Record<string, Record<string, unknown>>;
    for (const slug of CLASS4_RENDERING_REPAIR_SLUGS) {
      expect(Object.values(clips[slug] ?? {})).toEqual([null]);
    }
  });

  it('returns full geometry when geometryByCounty is absent', () => {
    const w = water({ geometry: fullGeom });
    expect(countyRenderGeometry(w)).toBe(fullGeom);
  });

  it('returns full geometry when the water county key is not in geometryByCounty', () => {
    const w = water({
      judet: 'Brașov',
      geometry: fullGeom,
      geometryByCounty: { bistritanasaud: clipGeom },
    });
    expect(countyRenderGeometry(w)).toBe(fullGeom);
  });

  it('returns null when the clip entry is null (geometry outside its county → hide)', () => {
    const w = water({
      geometry: fullGeom,
      geometryByCounty: { bistritanasaud: null },
    });
    expect(countyRenderGeometry(w)).toBeNull();
  });

  it('returns the per-county clip when present', () => {
    const w = water({
      geometry: fullGeom,
      geometryByCounty: { bistritanasaud: clipGeom },
    });
    expect(countyRenderGeometry(w)).toBe(clipGeom);
  });

  it.each([
    ['romsilva-bacau-barzauta', 'Bacău'],
    ['anpa-anpa-0202', 'Brăila'],
    ['anpa-anpa-0204', 'Brăila'],
    ['romsilva-covasna-sugo', 'Covasna'],
    ['romsilva-maramures-crasna-frumusaua', 'Maramureș'],
    ['vb2p0152', 'Olt'],
  ])('keeps source-backed Class 4 geometry renderable for %s', (slug, county) => {
    const w = water({ slug, judet: county, geometry: fullGeom, geometryByCounty: { [countyClipKey(county)]: null } });
    expect(countyRenderGeometry(w)).toBe(fullGeom);
  });
});