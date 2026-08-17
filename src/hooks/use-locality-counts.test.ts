import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useMapStore } from '@/stores/map-store';
import { useLocalityCounts } from '@/hooks/use-locality-counts';
import type { Water } from '@/types/data';

function water(over: Partial<Water>): Water {
  return {
    slug: 'w',
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

beforeEach(() => {
  useMapStore.setState({ waters: [], uncontracted: [], countyFilter: [] });
});

describe('useLocalityCounts', () => {
  it('returns an empty map when no county is selected', () => {
    const { result } = renderHook(() => useLocalityCounts());
    expect(result.current.size).toBe(0);
  });

  it('counts waters from both pools scoped to the selected county', () => {
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [
        water({ slug: 'a', judet: 'Cluj', locality: 'Gilău' }),
        water({ slug: 'b', judet: 'Cluj', locality: 'Gilău' }),
        water({ slug: 'c', judet: 'Cluj', locality: 'Cluj-Napoca' }),
        water({ slug: 'd', judet: 'Bihor', locality: 'Oradea' }), // other county → excluded
        water({ slug: 'e', judet: 'Cluj', locality: null }), // no locality → excluded
      ],
      uncontracted: [
        water({ slug: 'u1', judet: 'Cluj', locality: 'Gilău', uncontracted: true }),
        water({ slug: 'u2', judet: 'Ilfov', locality: 'Brașov', uncontracted: true }), // other county
      ],
    });
    const { result } = renderHook(() => useLocalityCounts());
    const m = result.current;
    // keyed by the SAME normalized key as useLocalities (localityKey), which
    // LocalityFilter uses to look up each option's count.
    expect(Array.from(m.keys()).sort()).toEqual(['cluj-napoca', 'gilau']);
    expect(m.get('gilau')).toBe(3); // 2 contracted + 1 uncontracted
    expect(m.get('cluj-napoca')).toBe(1);
  });

  it('collapses visually-identical locality variants into one count (t_e70099a9)', () => {
    useMapStore.setState({
      countyFilter: ['Brașov'],
      waters: [
        water({ slug: 'a', judet: 'Brașov', locality: 'Brașov' }),
        water({ slug: 'b', judet: 'Brașov', locality: 'Brașov ' }), // trailing space
        water({ slug: 'c', judet: 'Brașov', locality: 'BRASOV' }), // uppercase
        water({ slug: 'd', judet: 'Brașov', locality: 'Brasov' }), // missing diacritic
      ],
      uncontracted: [
        water({ slug: 'u1', judet: 'Brașov', locality: 'Brașov', uncontracted: true }),
      ],
    });
    const { result } = renderHook(() => useLocalityCounts());
    const m = result.current;
    expect(Array.from(m.keys())).toEqual(['brasov']);
    expect(m.get('brasov')).toBe(5);
  });
});
