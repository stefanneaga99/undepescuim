// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { boundedFocusInterval, measureContractSector } from '@/utils/contract-sector';
import type { Water } from '@/types/data';

function water(over: Partial<Water>): Water {
  return {
    slug: 'water',
    name: 'Râul Test',
    judet: 'Harghita',
    type: 'ape',
    subtype: 'rau',
    coordinates: [25, 46],
    bbox: [24, 45, 26, 47],
    asociatie: null,
    ...over,
  } as Water;
}

describe('measureContractSector', () => {
  it('reports the current Târnava Mare fallback as inferred, not source-backed', () => {
    const waters = JSON.parse(readFileSync('public/data/waters.json', 'utf8')) as Water[];
    const selected = waters.find((w) => w.slug === 'anpa-anpa-0333');
    expect(selected).toBeTruthy();

    const result = measureContractSector(selected!, waters);

    expect(result).toMatchObject({
      selectedSlug: 'anpa-anpa-0333',
      ownerSlug: 'ks2vsbaf',
      interval: [0, 0.1343],
      method: 'voronoi-fallback',
    });
    expect(result.renderedKm).toBeGreaterThan(29);
    expect(result.renderedKm).toBeLessThan(31);
  });

  it('provides a bounded diagnostic focus around a located fallback contract', () => {
    expect(boundedFocusInterval({ course_frac: 0.1072 } as Water)).toEqual([0.0972, 0.1172]);
    expect(boundedFocusInterval({ course_frac: 0.004 } as Water)).toEqual([0, 0.014]);
    expect(boundedFocusInterval({ course_frac: null } as unknown as Water)).toBeNull();
  });

  it('uses an explicit interval instead of the Voronoi position', () => {
    const owner = water({
      slug: 'owner',
      name: 'Râul X',
      riverGroup: 'x',
      geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46], [25, 45]] },
    });
    const selected = water({
      slug: 'selected',
      name: 'Râul X mijlociu',
      riverGroup: 'x',
      course_frac: 0.9,
      sectorStart: 0.25,
      sectorEnd: 0.5,
    });

    expect(measureContractSector(selected, [owner, selected])).toMatchObject({
      selectedSlug: 'selected',
      ownerSlug: 'owner',
      interval: [0.25, 0.5],
      method: 'explicit-interval',
    });
  });

  it('returns a structured non-measurement when no geometry owner exists', () => {
    const selected = water({ slug: 'missing', riverGroup: 'missing', course_frac: 0.4 });
    expect(measureContractSector(selected, [selected])).toEqual({
      selectedSlug: 'missing',
      ownerSlug: null,
      interval: null,
      renderedKm: null,
      method: 'unmeasurable',
    });
  });
});
