import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  useMapStore,
  DEFAULT_RADIUS_KM,
  EXPANDED_RADIUS_KM,
  NEARBY_LIMIT,
} from '@/stores/map-store';
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
  water({ slug: 'cluj-river', name: 'Râul Someșul Mic', judet: 'Cluj', subtype: 'rau', asociatie: { name: 'AJVPS Cluj', slug: 'ajvps-cluj' } }),
  water({ slug: 'cluj-lake', name: 'Lacul Tarnița', judet: 'Cluj', subtype: 'lac', asociatie: { name: 'AJVPS Cluj', slug: 'ajvps-cluj' } }),
  water({ slug: 'bihor-river', name: 'Crișul Repede', judet: 'Bihor', subtype: 'rau', asociatie: { name: 'AJVPS Bihor', slug: 'ajvps-bihor' }, locality: 'Oradea' }),
  water({ slug: 'bihor-lake', name: 'Lacul Pețea', judet: 'Bihor', subtype: 'lac', asociatie: { name: 'AJVPS Bihor', slug: 'ajvps-bihor' }, locality: 'Oradea' }),
];

const uncontracted: Water[] = [
  water({ slug: 'unc-river', name: 'Râul Sălbatic', judet: 'Harghita', subtype: 'rau', uncontracted: true, asociatie: null }),
];

function resetStore(extra: Partial<ReturnType<typeof useMapStore.getState>> = {}) {
  useMapStore.setState({
    associations: [],
    waters: [],
    uncontracted: [],
    counties: [],
    dataLoaded: false,
    selectedAssociationSlug: null,
    selectedWaterSlug: null,
    waterSheetOpen: false,
    countyFilter: [],
    localityFilter: [],
    waterTypeFilter: 'all',
    contractFilter: 'all',
    suppressAssociationFlyTo: false,
    associationSheetOpen: false,
    userPosition: null,
    nearbyWaters: [],
    nearbyRadiusKm: DEFAULT_RADIUS_KM,
    ...extra,
  });
}

beforeEach(() => {
  resetStore();
  vi.restoreAllMocks();
});

describe('selection basics', () => {
  it('selectAssociation sets the slug and closes the association sheet', () => {
    useMapStore.setState({ associationSheetOpen: true });
    useMapStore.getState().selectAssociation('ajvps-cluj');
    expect(useMapStore.getState().selectedAssociationSlug).toBe('ajvps-cluj');
    expect(useMapStore.getState().associationSheetOpen).toBe(false);
  });

  it('selectAssociation closes the water sheet but keeps the water selection (t_21d2f68d)', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-river', waterSheetOpen: true });
    useMapStore.getState().selectAssociation('ajvps-cluj');
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river'); // orange focus stays
    expect(useMapStore.getState().waterSheetOpen).toBe(false); // panel closes
  });

  it('openAssociationSheet opens the sheet and dismisses the selected water', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-river' });
    useMapStore.getState().openAssociationSheet();
    expect(useMapStore.getState().associationSheetOpen).toBe(true);
    expect(useMapStore.getState().selectedWaterSlug).toBeNull();
    expect(useMapStore.getState().waterSheetOpen).toBe(false);
  });

  it('closeAssociationSheet closes it', () => {
    useMapStore.setState({ associationSheetOpen: true });
    useMapStore.getState().closeAssociationSheet();
    expect(useMapStore.getState().associationSheetOpen).toBe(false);
  });

  it('selectWater(null) clears the selection without touching filters', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-river', countyFilter: ['Cluj'] });
    useMapStore.getState().selectWater(null);
    expect(useMapStore.getState().selectedWaterSlug).toBeNull();
    expect(useMapStore.getState().waterSheetOpen).toBe(false);
    expect(useMapStore.getState().countyFilter).toEqual(['Cluj']);
  });

  it('selectWater(slug) opens the sheet; closeWaterSheet keeps the selection (t_21d2f68d)', () => {
    useMapStore.setState({ waters });
    useMapStore.getState().selectWater('cluj-river');
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
    expect(useMapStore.getState().waterSheetOpen).toBe(true);
    // Closing the card (Escape / × / drag) must NOT clear the orange focus —
    // the reported bug was the card close wiping every highlight before the
    // user could pick a locality.
    useMapStore.getState().closeWaterSheet();
    expect(useMapStore.getState().waterSheetOpen).toBe(false);
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
  });
});

describe('selectWater association-clear semantics (t_7a7192ea / t_abccfd6c / t_697ba939)', () => {
  beforeEach(() => {
    resetStore({ waters, uncontracted });
  });

  it('a click on a water OUTSIDE the selected association clears the association + arms fly-to suppression', () => {
    useMapStore.setState({ selectedAssociationSlug: 'ajvps-cluj', suppressAssociationFlyTo: false });
    useMapStore.getState().selectWater('bihor-river');
    const s = useMapStore.getState();
    expect(s.selectedAssociationSlug).toBeNull();
    expect(s.selectedWaterSlug).toBe('bihor-river');
    expect(s.suppressAssociationFlyTo).toBe(true);
  });

  it('a click on a water BELONGING to the association keeps the association + no suppression', () => {
    useMapStore.setState({ selectedAssociationSlug: 'ajvps-cluj' });
    useMapStore.getState().selectWater('cluj-river');
    const s = useMapStore.getState();
    expect(s.selectedAssociationSlug).toBe('ajvps-cluj');
    expect(s.selectedWaterSlug).toBe('cluj-river');
    expect(s.suppressAssociationFlyTo).toBe(false);
  });

  it('an uncontracted water always clears the association', () => {
    useMapStore.setState({ selectedAssociationSlug: 'ajvps-cluj' });
    useMapStore.getState().selectWater('unc-river');
    expect(useMapStore.getState().selectedAssociationSlug).toBeNull();
  });

  it('consumeAssociationFlyToSuppression clears the one-shot flag', () => {
    useMapStore.setState({ suppressAssociationFlyTo: true });
    useMapStore.getState().consumeAssociationFlyToSuppression();
    expect(useMapStore.getState().suppressAssociationFlyTo).toBe(false);
  });

  it('drops a county/type/locality filter that would hide the clicked water', () => {
    useMapStore.setState({ countyFilter: ['Cluj'], waterTypeFilter: 'rau', localityFilter: ['Oradea'] });
    useMapStore.getState().selectWater('bihor-lake'); // Bihor + lac; locality Oradea matches
    const s = useMapStore.getState();
    expect(s.countyFilter).toEqual([]);
    expect(s.waterTypeFilter).toBe('all');
    expect(s.localityFilter).toEqual(['Oradea']); // clicked water's locality matches → kept
  });
});

describe('filters (t_21d2f68d: selection survives every filter change)', () => {
  beforeEach(() => {
    resetStore({ waters, uncontracted });
  });

  it('toggleCounty adds and removes counties, clears locality filter', () => {
    useMapStore.getState().toggleCounty('Cluj');
    expect(useMapStore.getState().countyFilter).toEqual(['Cluj']);
    useMapStore.setState({ localityFilter: ['Oradea'] });
    useMapStore.getState().toggleCounty('Bihor');
    expect(useMapStore.getState().countyFilter).toEqual(['Cluj', 'Bihor']);
    expect(useMapStore.getState().localityFilter).toEqual([]);
    useMapStore.getState().toggleCounty('Cluj');
    expect(useMapStore.getState().countyFilter).toEqual(['Bihor']);
  });

  it('a county change that hides the selected water KEEPS the selection (t_21d2f68d, R9 removed)', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-river', countyFilter: ['Cluj', 'Bihor'] });
    useMapStore.getState().toggleCounty('Cluj'); // remove Cluj → cluj-river hidden
    expect(useMapStore.getState().countyFilter).toEqual(['Bihor']);
    // Selection + card must NOT be dismissed: the filter narrows the visible
    // waters only (the selected water stays pinned in the rendered set).
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
  });

  it('toggleLocality adds/removes and never dismisses a hidden selection (t_21d2f68d)', () => {
    useMapStore.setState({ countyFilter: ['Bihor'], selectedWaterSlug: 'bihor-river' });
    useMapStore.getState().toggleLocality('Oradea');
    expect(useMapStore.getState().localityFilter).toEqual(['Oradea']);
    expect(useMapStore.getState().selectedWaterSlug).toBe('bihor-river'); // matches → kept
    useMapStore.getState().toggleLocality('Oradea');
    expect(useMapStore.getState().localityFilter).toEqual([]);
    // a water WITHOUT the active locality is NOT dismissed either — the
    // locality only narrows the map, the click focus + card survive (the
    // water is pinned into the rendered set by use-filtered-waters).
    useMapStore.setState({ selectedWaterSlug: 'cluj-river' }); // no locality
    useMapStore.getState().toggleLocality('Oradea');
    expect(useMapStore.getState().localityFilter).toEqual(['Oradea']);
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
  });

  it('clearLocalities empties the locality filter', () => {
    useMapStore.setState({ localityFilter: ['Oradea'], selectedWaterSlug: 'cluj-river' });
    useMapStore.getState().clearLocalities();
    expect(useMapStore.getState().localityFilter).toEqual([]);
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
  });

  it('setWaterTypeFilter filters but never dismisses a hidden selection (t_21d2f68d)', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-lake' });
    useMapStore.getState().setWaterTypeFilter('rau');
    expect(useMapStore.getState().waterTypeFilter).toBe('rau');
    // lake hidden by 'rau' — selection stays (card + orange focus survive)
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-lake');
    useMapStore.setState({ selectedWaterSlug: 'cluj-river' });
    useMapStore.getState().setWaterTypeFilter('rau');
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');
  });

  it('setContractFilter changes the filter but never dismisses the selection (t_21d2f68d)', () => {
    useMapStore.setState({ selectedWaterSlug: 'cluj-river' });
    useMapStore.getState().setContractFilter('contractate');
    expect(useMapStore.getState().contractFilter).toBe('contractate');
    expect(useMapStore.getState().selectedWaterSlug).toBe('cluj-river');

    useMapStore.setState({ selectedWaterSlug: 'unc-river', uncontracted });
    useMapStore.getState().setContractFilter('contractate');
    expect(useMapStore.getState().selectedWaterSlug).toBe('unc-river'); // NOT dismissed
    useMapStore.getState().setContractFilter('necontractate');
    expect(useMapStore.getState().selectedWaterSlug).toBe('unc-river'); // still kept
  });
});

describe('geolocation (applyUserPosition / clearUserPosition)', () => {
  it('computes nearby waters at the default radius and attaches county', () => {
    resetStore({ waters, counties: [] });
    useMapStore.getState().applyUserPosition({ lat: 46.5, lon: 23.5, accuracy: 50 });
    const s = useMapStore.getState();
    expect(s.userPosition).toEqual({ lat: 46.5, lon: 23.5, accuracy: 50 });
    expect(s.nearbyRadiusKm).toBe(DEFAULT_RADIUS_KM);
    expect(s.nearbyWaters.length).toBeGreaterThan(0);
    expect(s.nearbyWaters[0].slug).toBe('cluj-river'); // inside bbox → 0 km
    // county: no counties loaded → null (falls back to contract county downstream)
    expect(s.nearbyWaters[0].county).toBeNull();
  });

  it('expands the radius to 50 km when fewer than 3 are nearby', () => {
    const sparse = [
      water({ slug: 'one', bbox: [23.4, 46.4, 23.5, 46.5] }),
      water({ slug: 'two', bbox: [24.5, 47.0, 24.6, 47.1] }),
      water({ slug: 'three', bbox: [26.0, 45.0, 27.0, 46.0] }),
      water({ slug: 'noloc', bbox: undefined as never, coordinates: undefined as never }),
    ];
    resetStore({ waters: sparse });
    useMapStore.getState().applyUserPosition({ lat: 46.45, lon: 23.45, accuracy: 50 });
    const s = useMapStore.getState();
    // fewer than 3 → radius expands to 50 km, then the nearest-few fallback
    // GROWS the drawn radius to cover the farthest entry shown.
    expect(s.nearbyRadiusKm).toBeGreaterThanOrEqual(EXPANDED_RADIUS_KM);
    // still < MIN_NEARBY_COUNT → nearest-few fallback kicks in
    expect(s.nearbyWaters.length).toBeGreaterThanOrEqual(1);
    expect(s.nearbyWaters.every((n) => Number.isFinite(n.km))).toBe(true);
    expect(s.nearbyWaters.map((n) => n.slug)).not.toContain('noloc');
  });

  it('grows the drawn radius to cover the farthest shown entry in the fallback', () => {
    const sparse = [
      water({ slug: 'near', bbox: [23.0, 46.0, 23.5, 46.5] }),
      water({ slug: 'far', bbox: [26.0, 44.0, 27.0, 45.0] }),
    ];
    resetStore({ waters: sparse });
    useMapStore.getState().applyUserPosition({ lat: 46.3, lon: 23.4, accuracy: 100 });
    const s = useMapStore.getState();
    expect(s.nearbyWaters).toHaveLength(2);
    expect(s.nearbyRadiusKm).toBeGreaterThanOrEqual(DEFAULT_RADIUS_KM);
    const farthest = s.nearbyWaters[s.nearbyWaters.length - 1].km;
    expect(s.nearbyRadiusKm).toBeGreaterThanOrEqual(farthest);
    expect(s.nearbyRadiusKm).toBeLessThan(NEARBY_LIMIT * 1000); // sane bound
  });

  it('clearUserPosition resets the position, list and radius', () => {
    resetStore({ waters });
    useMapStore.getState().applyUserPosition({ lat: 46.3, lon: 23.4, accuracy: 50 });
    useMapStore.getState().clearUserPosition();
    const s = useMapStore.getState();
    expect(s.userPosition).toBeNull();
    expect(s.nearbyWaters).toEqual([]);
    expect(s.nearbyRadiusKm).toBe(DEFAULT_RADIUS_KM);
  });
});

describe('loadData', () => {
  function jsonResponse(data: unknown, ok = true, status = 200) {
    return {
      ok,
      status,
      json: async () => data,
    } as Response;
  }

  it('loads associations, waters, uncontracted rivers + lakes, counties, and freshness meta', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([{ slug: 'ajvps-cluj', name: 'AJVPS Cluj' }]))
      .mockResolvedValueOnce(jsonResponse(waters))
      .mockResolvedValueOnce(jsonResponse(uncontracted))
      .mockResolvedValueOnce(jsonResponse([water({ slug: 'unc-lake', uncontracted: true, asociatie: null })]))
      .mockResolvedValueOnce(jsonResponse({ type: 'FeatureCollection', features: [] }))
      .mockResolvedValueOnce(jsonResponse({ dataUpdatedAt: '2026-08-16T00:00:00Z' }));
    vi.stubGlobal('fetch', fetchMock);

    await useMapStore.getState().loadData();
    const s = useMapStore.getState();
    expect(s.dataLoaded).toBe(true);
    expect(s.associations).toHaveLength(1);
    expect(s.waters).toHaveLength(4);
    expect(s.uncontracted).toHaveLength(2); // rivers + lakes merged
    expect(s.counties).toEqual([]);
    expect(s.dataUpdatedAt).toBe('2026-08-16T00:00:00Z');
    expect(fetchMock).toHaveBeenCalledTimes(6);
    vi.unstubAllGlobals();
  });

  it('marks dataLoaded even when a fetch fails (empty map, no skeleton spin)', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'));
    vi.stubGlobal('fetch', fetchMock);
    await useMapStore.getState().loadData();
    expect(useMapStore.getState().dataLoaded).toBe(true);
    vi.unstubAllGlobals();
  });
});
