import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useMapStore } from '@/stores/map-store';
import { useCounties } from '@/hooks/use-counties';
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
  useMapStore.setState({
    waters: [
      water({ slug: 'a', name: 'Râul A', judet: 'Cluj' }),
      water({ slug: 'b', name: 'Râul B', judet: 'Bihor' }),
      water({ slug: 'c', name: 'Râul C', judet: 'Cluj' }), // dup county → dedupe
    ],
    uncontracted: [
      water({ slug: 'u1', name: 'Râul U', judet: 'Covasna', uncontracted: true }),
    ],
  });
});

describe('useCounties', () => {
  it('dedupes and RO-sorts counties from both pools, independent of filters', () => {
    const { result } = renderHook(() => useCounties());
    expect(result.current).toEqual(['Bihor', 'Cluj', 'Covasna']);
  });

  it('updates when the pools change', () => {
    useMapStore.setState({ uncontracted: [] });
    const { result } = renderHook(() => useCounties());
    expect(result.current).toEqual(['Bihor', 'Cluj']);
  });
});
