import { create } from 'zustand';
import type { Association, ContractFilter, CountyFeature, Water, WaterTypeFilter } from '@/types/data';
import { distanceToWaterKm, nearbyCounty, nearestWaters, type NearbyWater } from '@/utils/geo';

/** Geolocation MVP constants (docs/geolocation-feasibility.md §5). */
export const DEFAULT_RADIUS_KM = 25;
export const EXPANDED_RADIUS_KM = 50;
export const MIN_NEARBY_COUNT = 3;
export const NEARBY_LIMIT = 10;

/**
 * Single source of truth for all cross-component map UI state.
 * Contract: docs/component_structure_plan.md §5.1 + docs/map-state-data-flow.md §1.
 *
 * Rules:
 * - Selection and filters are INDEPENDENT (R10) — no action clears another's state.
 * - R9: if a filter change removes the selected water, the sheet auto-dismisses.
 *
 * t_471dad64: `waters` are the CONTRACTED waters (association cards);
 * `uncontracted` are the OSM rivers with NO contract (teal overlay,
 * 'Necontractat' cards). They stay separate so contract-resolution logic
 * (contractAtFraction over `waters`) never sees the uncontracted entries.
 */

interface MapStore {
  // Data layer (loaded once, never mutated after load)
  associations: Association[];
  waters: Water[];
  uncontracted: Water[];
  /** County boundary polygons (/data/counties.geojson) — nearby chip attribution (t_6c2ac870). */
  counties: CountyFeature[];
  dataLoaded: boolean;

  // Selection layer (mutually independent)
  selectedAssociationSlug: string | null; // null = no association selected
  selectedWaterSlug: string | null; // null = detail sheet closed

  // Filter layer
  countyFilter: string[]; // empty [] = all counties
  localityFilter: string[]; // empty [] = all localities (t_dd918db7)
  waterTypeFilter: WaterTypeFilter; // 'all' | 'lac' | 'rau'
  contractFilter: ContractFilter; // 'all' | 'contractate' | 'necontractate'

  // FlyTo gating (t_697ba939): one-shot flag — the association was cleared
  // as a side effect of CLICKING a water outside it, so the next
  // FlyToController pass must NOT re-fit / zoom out to the full dataset.
  suppressAssociationFlyTo: boolean;

  // F2a: association detail sheet visibility (opened from the association
  // chip on the map). Mirrors the water sheet's one-at-a-time rule: opening
  // it clears the selected water, selecting a water closes it.
  associationSheetOpen: boolean;

  // Geolocation MVP (docs/geolocation-feasibility.md): one-shot user fix +
  // the nearest contracted waters computed client-side from the loaded pool.
  // `nearbyRadiusKm` is the ADAPTIVE radius actually used (25 → 50 when too
  // few results; grows to cover the nearest-few fallback) — the map draws
  // the circle with this value and the sheet labels it.
  userPosition: { lat: number; lon: number; accuracy: number } | null;
  nearbyWaters: NearbyWater[];
  nearbyRadiusKm: number;

  // Actions
  loadData: () => Promise<void>;
  selectAssociation: (slug: string | null) => void;
  selectWater: (slug: string | null) => void;
  consumeAssociationFlyToSuppression: () => void;
  openAssociationSheet: () => void;
  closeAssociationSheet: () => void;
  toggleCounty: (county: string) => void;
  toggleLocality: (locality: string) => void;
  clearLocalities: () => void;
  setWaterTypeFilter: (type: WaterTypeFilter) => void;
  setContractFilter: (filter: ContractFilter) => void;
  /** Geolocation MVP: store a one-shot position fix + recompute nearest waters. */
  applyUserPosition: (pos: { lat: number; lon: number; accuracy: number }) => void;
  /** Geolocation MVP: clear the user marker / circle / nearby list. */
  clearUserPosition: () => void;
}

/** R9: would `slug` survive the given filters? (checked across both pools) */
function isFilteredOut(
  slug: string | null,
  allWaters: Water[],
  countyFilter: string[],
  waterTypeFilter: WaterTypeFilter,
  localityFilter: string[],
): boolean {
  if (!slug) return false;
  const water = allWaters.find((w) => w.slug === slug);
  if (!water) return true;
  if (countyFilter.length > 0 && !countyFilter.includes(water.judet)) return true;
  if (waterTypeFilter !== 'all' && water.subtype !== waterTypeFilter) return true;
  // A water without a locality is hidden by any active locality filter.
  if (localityFilter.length > 0 && !localityFilter.includes(water.locality ?? '')) return true;
  return false;
}

export const useMapStore = create<MapStore>((set, get) => ({
  associations: [],
  waters: [],
  uncontracted: [],
  counties: [],
  dataLoaded: false,

  selectedAssociationSlug: null,
  selectedWaterSlug: null,

  countyFilter: [],
  localityFilter: [],
  waterTypeFilter: 'all',
  contractFilter: 'all',
  suppressAssociationFlyTo: false,
  associationSheetOpen: false,

  userPosition: null,
  nearbyWaters: [],
  nearbyRadiusKm: DEFAULT_RADIUS_KM,

  loadData: async () => {
    try {
      const [assocRes, watersRes, uncRes, uncLakesRes, countiesRes] = await Promise.all([
        fetch('/data/associations.json'),
        fetch('/data/waters.json'),
        fetch('/data/uncontracted_rivers.json'),
        fetch('/data/uncontracted_lakes.json'),
        fetch('/data/counties.geojson'),
      ]);
      if (!assocRes.ok || !watersRes.ok) throw new Error(`fetch failed: ${assocRes.status} / ${watersRes.status}`);
      const [associations, waters] = (await Promise.all([
        assocRes.json(),
        watersRes.json(),
      ])) as [Association[], Water[]];
      let uncontracted: Water[] = [];
      if (uncRes.ok) {
        uncontracted = (await uncRes.json()) as Water[];
      }
      // t_51e028c4: ponds/lakes with no contract join the same uncontracted
      // pool — county/type/contract filters and the 'Necontractat' card UX
      // apply to them automatically.
      if (uncLakesRes.ok) {
        const lakes = (await uncLakesRes.json()) as Water[];
        uncontracted = [...uncontracted, ...lakes];
      }
      // t_6c2ac870: county polygons for the nearby-waters chip. Optional —
      // the chip falls back to the contract county when missing.
      let counties: CountyFeature[] = [];
      if (countiesRes.ok) {
        const fc = (await countiesRes.json()) as { type: string; features: CountyFeature[] };
        counties = Array.isArray(fc.features) ? fc.features : [];
      }
      set({ associations, waters, uncontracted, counties, dataLoaded: true });
    } catch (err) {
      // Never leave the skeleton spinning forever — render an empty map instead.
      console.error('[map-store] loadData failed:', err);
      set({ dataLoaded: true });
    }
  },

  selectAssociation: (slug) =>
    set({ selectedAssociationSlug: slug, associationSheetOpen: false }),

  // F2a: the chip opens the association detail sheet; opening it dismisses
  // the water sheet (one-at-a-time, mirrors the existing selection rules).
  openAssociationSheet: () =>
    set({ associationSheetOpen: true, selectedWaterSlug: null }),
  closeAssociationSheet: () => set({ associationSheetOpen: false }),

  selectWater: (slug) => {
    // t_7a7192ea Bug 2: clicking a river/lake takes over from any active
    // association filter — clear selectedAssociationSlug so the map stops
    // showing the association's green/grey coverage, then select the clicked
    // water (existing orange focus + detail card behavior takes over).
    // t_abccfd6c: EXCEPT when the clicked water BELONGS to the selected
    // association — then the association filter stays (coverage keeps
    // highlighting the association's waters) and the map does NOT re-fit /
    // zoom out (FlyToController only reacts to selectedAssociationSlug
    // changes). Only a click on a water OUTSIDE the association clears it.
    // Also drop a county/type filter that would hide the clicked water (a
    // defensive "as needed" — normally only waters that pass the filters are
    // rendered/clickable, but never leave a selection invisible).
    if (slug === null) {
      set({ selectedWaterSlug: null });
      return;
    }
    const { countyFilter, localityFilter, waterTypeFilter, waters, uncontracted, selectedAssociationSlug } = get();
    const water =
      waters.find((w) => w.slug === slug) ??
      uncontracted.find((w) => w.slug === slug) ??
      null;
    // Same equality the coverage styling uses (colors.ts getFeatureStyle),
    // so a green-highlighted water keeps the association and a grey/dimmed
    // one clears it — visually consistent. Uncontracted waters have no
    // asociatie, so they always clear.
    const belongsToAssociation =
      selectedAssociationSlug !== null &&
      water !== null &&
      water.asociatie?.slug === selectedAssociationSlug;
    // t_697ba939: a click on a water OUTSIDE the association clears the
    // filter (t_7a7192ea), but that clear is a SIDE EFFECT of the click,
    // not the user leaving the association — FlyToController must NOT
    // re-fit / zoom out to the full dataset. Arm the one-shot suppression;
    // only set it when an association is actually being cleared (never
    // leave a stale flag that could swallow a later explicit clear).
    const clearingAssociationByClick = !belongsToAssociation && selectedAssociationSlug !== null;
    set({
      selectedWaterSlug: slug,
      selectedAssociationSlug: belongsToAssociation ? selectedAssociationSlug : null,
      associationSheetOpen: false,
      suppressAssociationFlyTo: clearingAssociationByClick,
      countyFilter:
        water && countyFilter.length > 0 && !countyFilter.includes(water.judet)
          ? []
          : countyFilter,
      waterTypeFilter:
        water && waterTypeFilter !== 'all' && water.subtype !== waterTypeFilter
          ? 'all'
          : waterTypeFilter,
      localityFilter:
        water && localityFilter.length > 0 && !localityFilter.includes(water.locality ?? '')
          ? []
          : localityFilter,
    });
  },

  // t_697ba939: consumed by FlyToController — the association was cleared by
  // a water click, so the map stays put (no zoom-out to the national view).
  consumeAssociationFlyToSuppression: () => set({ suppressAssociationFlyTo: false }),

  toggleCounty: (county) => {
    const { countyFilter, waters, uncontracted, selectedWaterSlug, waterTypeFilter } = get();
    const next = countyFilter.includes(county)
      ? countyFilter.filter((c) => c !== county)
      : [...countyFilter, county];
    set({
      countyFilter: next,
      // t_dd918db7: locality is a REFINEMENT of the county selection — a
      // locality list only exists for the currently selected counties, so a
      // county change invalidates any active locality filter (plan §7.4 /
      // risk 2: same-name UATs across counties must never leak).
      localityFilter: [],
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, [...waters, ...uncontracted], next, waterTypeFilter, [])
        ? null
        : selectedWaterSlug,
    });
  },

  toggleLocality: (locality) => {
    const { localityFilter, waters, uncontracted, selectedWaterSlug, countyFilter, waterTypeFilter } = get();
    const next = localityFilter.includes(locality)
      ? localityFilter.filter((l) => l !== locality)
      : [...localityFilter, locality];
    set({
      localityFilter: next,
      // R9: a locality change that hides the selected water dismisses the sheet.
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, [...waters, ...uncontracted], countyFilter, waterTypeFilter, next)
        ? null
        : selectedWaterSlug,
    });
  },

  clearLocalities: () => set({ localityFilter: [] }),

  setWaterTypeFilter: (type) => {
    const { countyFilter, localityFilter, waters, uncontracted, selectedWaterSlug } = get();
    set({
      waterTypeFilter: type,
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, [...waters, ...uncontracted], countyFilter, type, localityFilter)
        ? null
        : selectedWaterSlug,
    });
  },

  setContractFilter: (filter) => {
    // R9: a filter change that hides the selected water dismisses the sheet.
    const { selectedWaterSlug, uncontracted } = get();
    let nextSlug = selectedWaterSlug;
    if (selectedWaterSlug) {
      const isUnc = uncontracted.some((w) => w.slug === selectedWaterSlug);
      if (filter === 'contractate' && isUnc) nextSlug = null;
      if (filter === 'necontractate' && !isUnc) nextSlug = null;
    }
    set({ contractFilter: filter, selectedWaterSlug: nextSlug });
  },

  // Geolocation MVP (docs/geolocation-feasibility.md §5 AC4): adaptive radius
  // — 25 km default; if fewer than 3 contracted waters are within it, expand
  // to 50 km; always show at least the nearest few regardless of radius (and
  // grow the drawn radius to cover the farthest shown entry so the circle
  // never under-states what the list claims).
  applyUserPosition: (pos) => {
    const { waters, counties } = get();
    // t_6c2ac870: attach the water's OWN county (of the segment nearest the
    // user) so the nearby card doesn't show the association's seat county
    // (e.g. 'Ilfov' for the Dâmbovița headwaters near Brașov).
    const withCounty = (nearby: NearbyWater[]): NearbyWater[] =>
      nearby.map((n) => {
        const water = waters.find((w) => w.slug === n.slug);
        return { ...n, county: water ? nearbyCounty(pos.lat, pos.lon, water, counties) : null };
      });
    let radius = DEFAULT_RADIUS_KM;
    let nearby = withCounty(nearestWaters(pos.lat, pos.lon, waters, { limit: NEARBY_LIMIT, maxKm: radius }));
    if (nearby.length < MIN_NEARBY_COUNT) {
      radius = EXPANDED_RADIUS_KM;
      nearby = withCounty(nearestWaters(pos.lat, pos.lon, waters, { limit: NEARBY_LIMIT, maxKm: radius }));
    }
    if (nearby.length < MIN_NEARBY_COUNT) {
      // Nearest-few fallback, no radius cap (e.g. deep wilderness).
      nearby = withCounty(
        waters
          .map((w) => ({ slug: w.slug, km: distanceToWaterKm(pos.lat, pos.lon, w), county: null }))
          .filter((e) => Number.isFinite(e.km))
          .sort((a, b) => a.km - b.km)
          .slice(0, NEARBY_LIMIT),
      );
      if (nearby.length > 0) {
        radius = Math.max(radius, Math.ceil(nearby[nearby.length - 1].km / 10) * 10);
      }
    }
    set({ userPosition: pos, nearbyWaters: nearby, nearbyRadiusKm: radius });
  },

  clearUserPosition: () =>
    set({ userPosition: null, nearbyWaters: [], nearbyRadiusKm: DEFAULT_RADIUS_KM }),
}));
