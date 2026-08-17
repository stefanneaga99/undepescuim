import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useMapStore } from '@/stores/map-store';
import { useFilteredWaters } from '@/hooks/use-filtered-waters';
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
    asociatie: { name: 'AJVPS Cluj', slug: 'ajvps-cluj' },
    ...over,
  } as Water;
}

const waters: Water[] = [
  water({ slug: 'cluj-river', name: 'Râul Someșul Mic', judet: 'Cluj', subtype: 'rau', locality: 'Cluj-Napoca' }),
  water({ slug: 'cluj-lake', name: 'Lacul Tarnița', judet: 'Cluj', subtype: 'lac', locality: 'Gilău' }),
  water({ slug: 'bihor-river', name: 'Crișul Repede', judet: 'Bihor', subtype: 'rau', locality: 'Oradea' }),
];

beforeEach(() => {
  useMapStore.setState({
    waters,
    uncontracted: [],
    countyFilter: [],
    localityFilter: [],
    waterTypeFilter: 'all',
    contractFilter: 'all',
  });
});

describe('useFilteredWaters', () => {
  it('returns everything when no filters are active', () => {
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current.map((w) => w.slug)).toEqual(['cluj-river', 'cluj-lake', 'bihor-river']);
  });

  it('filters by county (AND) and hides county-clip-null waters', () => {
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [
        waters[0],
        waters[1],
        // Bihor water with a geometryByCounty entry of null for Cluj: would be
        // pulled in by county filter? No — its judet is Bihor, so it's
        // excluded by the county check before the clip step. This one tests
        // the clip-null path with a Cluj-judet water:
        water({ slug: 'cluj-misattributed', name: 'Râul Greșit', judet: 'Cluj', geometryByCounty: { cluj: null } }),
      ],
    });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current.map((w) => w.slug)).toEqual(['cluj-river', 'cluj-lake']);
  });

  it('keeps geometry-less (bbox-fallback) waters under a county filter (t_9529e678)', () => {
    // ANPA/Romsilva entries ship `geometry: null` (JSON null) — previously
    // countyRenderGeometry returned that null as the hide-signal, so every
    // bbox-fallback dot vanished under ANY county filter. They must survive
    // and render as point dots (t_cdb614de).
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [
        water({
          slug: 'cluj-dot',
          name: 'Lacul Fără Geometrie',
          judet: 'Cluj',
          geometry: null as never,
          bbox: [23.0, 46.0, 23.1, 46.1],
        }),
      ],
    });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current.map((w) => w.slug)).toEqual(['cluj-dot']);
    // A genuinely misattributed water (geometryByCounty entry null) is STILL
    // hidden — the two cases must not be conflated.
    useMapStore.setState({
      waters: [
        water({
          slug: 'cluj-dot-2',
          name: 'Lacul Fără Geometrie 2',
          judet: 'Cluj',
          geometry: null as never,
          geometryByCounty: { cluj: null },
        }),
      ],
    });
    const { result: result2 } = renderHook(() => useFilteredWaters());
    expect(result2.current).toEqual([]);
  });

  it('replaces the full geometry with the per-county clip when one exists', () => {
    const clip = { type: 'LineString' as const, coordinates: [[23.0, 46.5], [23.5, 46.6]] };
    useMapStore.setState({
      countyFilter: ['Cluj'],
      waters: [water({ slug: 'clipped', name: 'Râul Tăiat', judet: 'Cluj', geometryByCounty: { cluj: clip } })],
    });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current[0].geometry).toEqual(clip);
  });

  it('filters by locality', () => {
    useMapStore.setState({ countyFilter: ['Cluj'], localityFilter: ['Gilău'] });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current.map((w) => w.slug)).toEqual(['cluj-lake']);
  });

  it('filters by water type', () => {
    useMapStore.setState({ waterTypeFilter: 'lac' });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current.map((w) => w.slug)).toEqual(['cluj-lake']);
  });

  it('returns [] when contractFilter is necontractate', () => {
    useMapStore.setState({ contractFilter: 'necontractate' });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current).toEqual([]);
  });

  it('keeps everything when contractFilter is contractate', () => {
    useMapStore.setState({ contractFilter: 'contractate' });
    const { result } = renderHook(() => useFilteredWaters());
    expect(result.current).toHaveLength(3);
  });
});
