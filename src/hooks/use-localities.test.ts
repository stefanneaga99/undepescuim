import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useMapStore } from '@/stores/map-store';
import { useLocalities } from '@/hooks/use-localities';
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

const waters: Water[] = [
  water({ slug: 'a', name: 'Râul A', judet: 'Cluj', locality: 'Gilău' }),
  water({ slug: 'b', name: 'Râul B', judet: 'Cluj', locality: 'Cluj-Napoca' }),
  water({ slug: 'c', name: 'Râul C', judet: 'Cluj', locality: 'Gilău' }), // dup → dedupe
  water({ slug: 'd', name: 'Râul D', judet: 'Bihor', locality: 'Oradea' }),
  water({ slug: 'e', name: 'Râul E', judet: 'Bihor', locality: null }),  // no locality
];

const uncontracted: Water[] = [
  water({ slug: 'u1', name: 'Râul U', judet: 'Cluj', locality: 'Huedin', uncontracted: true }),
];

beforeEach(() => {
  useMapStore.setState({ waters, uncontracted, countyFilter: [] });
});

describe('useLocalities', () => {
  it('returns [] when no county is selected', () => {
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual([]);
  });

  it('dedupes and RO-sorts localities scoped to the selected county (both pools)', () => {
    useMapStore.setState({ countyFilter: ['Cluj'] });
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual(['Cluj-Napoca', 'Gilău', 'Huedin']);
  });

  it('ignores waters without a locality', () => {
    useMapStore.setState({ countyFilter: ['Bihor'] });
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual(['Oradea']);
  });

  it('collapses visually-identical locality variants into one option (t_f6445fda)', () => {
    // The reported bug: 'Brașov' appeared TWICE in the LOCALITATE dropdown.
    // Distinct raw values that render the same (trailing space, case,
    // missing diacritics) must collapse to a single option — the exact-string
    // Set dedup kept them separate.
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
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual(['Brașov']);
  });

  it('skips whitespace-only locality values (t_f6445fda)', () => {
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [water({ slug: 'a', judet: 'Cluj', locality: '   ' })],
      uncontracted: [],
    });
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual([]);
  });

  it('keeps genuinely distinct same-prefix localities (t_f6445fda)', () => {
    // Normalization must NOT over-merge: different real UATs stay separate.
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [
        water({ slug: 'a', judet: 'Cluj', locality: 'Jucu' }),
        water({ slug: 'b', judet: 'Cluj', locality: 'Jucu de Mijloc' }),
      ],
      uncontracted: [],
    });
    const { result } = renderHook(() => useLocalities());
    expect(result.current).toEqual(['Jucu', 'Jucu de Mijloc']);
  });
});
