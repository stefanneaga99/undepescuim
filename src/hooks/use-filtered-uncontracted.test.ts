import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useMapStore } from '@/stores/map-store';
import { useFilteredUncontracted } from '@/hooks/use-filtered-uncontracted';
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

const uncontracted: Water[] = [
  water({ slug: 'unc-river', name: 'Râul Sălbatic', judet: 'Harghita', subtype: 'rau', uncontracted: true, locality: 'Gheorgheni' }),
  water({ slug: 'unc-lake', name: 'Lacul Verde', judet: 'Covasna', subtype: 'lac', uncontracted: true, locality: 'Bățani' }),
];

beforeEach(() => {
  useMapStore.setState({
    waters: [],
    uncontracted,
    countyFilter: [],
    localityFilter: [],
    waterTypeFilter: 'all',
    contractFilter: 'all',
  });
});

describe('useFilteredUncontracted', () => {
  it('returns everything when no filters are active', () => {
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current.map((w) => w.slug)).toEqual(['unc-river', 'unc-lake']);
  });

  it('returns [] when contractFilter is contractate', () => {
    useMapStore.setState({ contractFilter: 'contractate' });
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current).toEqual([]);
  });

  it('filters by county and hides clip-null waters', () => {
    useMapStore.setState({
      countyFilter: ['Harghita'],
      uncontracted: [
        uncontracted[0],
        water({ slug: 'clip-null', name: 'Râul Inexistent', judet: 'Harghita', uncontracted: true, geometryByCounty: { harghita: null } }),
      ],
    });
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current.map((w) => w.slug)).toEqual(['unc-river']);
  });

  it('replaces geometry with the county clip', () => {
    const clip = { type: 'LineString' as const, coordinates: [[25.5, 46.5], [25.6, 46.6]] };
    useMapStore.setState({
      countyFilter: ['Harghita'],
      uncontracted: [water({ slug: 'clipped', name: 'Râul Tăiat', judet: 'Harghita', uncontracted: true, geometryByCounty: { harghita: clip } })],
    });
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current[0].geometry).toEqual(clip);
  });

  it('filters by type and locality', () => {
    useMapStore.setState({ waterTypeFilter: 'lac' });
    expect(renderHook(() => useFilteredUncontracted()).result.current.map((w) => w.slug)).toEqual(['unc-lake']);

    useMapStore.setState({ countyFilter: ['Covasna'], localityFilter: ['Bățani'], waterTypeFilter: 'all' });
    expect(renderHook(() => useFilteredUncontracted()).result.current.map((w) => w.slug)).toEqual(['unc-lake']);
  });

  it('PINs the selected uncontracted water through a locality filter that hides it (t_21d2f68d)', () => {
    useMapStore.setState({
      countyFilter: ['Harghita'],
      localityFilter: ['Bățani'],
      selectedWaterSlug: 'unc-river', // in Harghita / Gheorgheni — not in Bățani
    });
    const { result } = renderHook(() => useFilteredUncontracted());
    // unc-lake is Covasna (excluded by the county filter); unc-river is pinned
    // through the locality filter.
    expect(result.current.map((w) => w.slug)).toEqual(['unc-river']);
  });

  it('does NOT pin an uncontracted selection outside the county filter (t_21d2f68d)', () => {
    useMapStore.setState({
      countyFilter: ['Harghita'],
      selectedWaterSlug: 'unc-lake', // Covasna — outside the county filter
    });
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current.map((w) => w.slug)).toEqual(['unc-river']);
  });

  it('does NOT pin a contracted selection into the uncontracted pool (t_21d2f68d)', () => {
    useMapStore.setState({
      waters: [{ slug: 'contracted-selected', judet: 'Harghita', subtype: 'rau', locality: 'Gheorgheni', asociatie: { name: 'X', slug: 'x' } } as Water],
      countyFilter: ['Harghita'],
      localityFilter: ['Bățani'],
      selectedWaterSlug: 'contracted-selected',
    });
    const { result } = renderHook(() => useFilteredUncontracted());
    expect(result.current.some((w) => w.slug === 'contracted-selected')).toBe(false);
  });
});
